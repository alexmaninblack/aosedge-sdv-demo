# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Private installed-instance Gateway server identity; never Cloud authority.

Call prepare only inside the existing environment writer during explicit start.
Inspection never creates material. A failed publication is retained for review.
"""

import ctypes
import json
import os
from pathlib import Path
import sys

from aosedge_demo_orchestrator import runtime_paths as paths, source_trust as crypto
from aosedge_demo_orchestrator.environment import EnvironmentError, sync_directory

PROFILE = 'LOCAL_DEMO_SERVER_TLS'
RELATIVE = '.local/demo-control/tls'
FILES = {'server-cert.pem', 'server-key.pem', 'identity.json'}


def require(condition, reason):
    if not condition:
        raise EnvironmentError('SOURCE_SERVER_TLS_' + reason)


def context(root):
    require(paths.installed(root), 'INSTALLED_INSTANCE_REQUIRED')
    checked, identity = paths.instance(root)
    require(identity == paths.instance_id(), 'INSTANCE_CONFLICT')
    return checked / RELATIVE, dict(schemaVersion=1, instanceId=identity, profile=PROFILE)


def stamp(path):
    paths.private(path)
    info = path.lstat()
    require(0 < info.st_size <= (4096 if path.name == 'identity.json' else 16384), 'FILE_SIZE_INVALID')
    return tuple(getattr(info, k) for k in ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns',
                 'st_ctime_ns', 'st_mode', 'st_uid', 'st_nlink'))


def inspect_directory(directory, expected):
    paths.private(directory, directory=True)
    require({p.name for p in directory.iterdir()} == FILES, 'MATERIAL_INCOMPLETE')
    before = {name: stamp(directory/name) for name in FILES}
    value, _ = paths.small_json(directory/'identity.json', 4096, owned=True)
    require(value == expected and type(value.get('schemaVersion')) is int, 'INSTANCE_CONFLICT')
    cert, key = directory/'server-cert.pem', directory/'server-key.pem'
    require(crypto.openssl(['x509', '-in', cert, '-noout', '-pubkey']) ==
            crypto.openssl(['pkey', '-in', key, '-pubout']), 'KEY_MISMATCH')
    subject = 'OU=' + expected['instanceId'] + ',CN=localhost'
    names = crypto.openssl(['x509', '-in', cert, '-noout', '-subject', '-issuer',
                            '-nameopt', 'RFC2253']).decode().splitlines()
    require([line.split('=', 1)[-1].strip() for line in names] == [subject, subject], 'CERTIFICATE_IDENTITY_INVALID')
    extensions = {
        'basicConstraints': ('X509v3 Basic Constraints: critical', 'CA:FALSE'),
        'keyUsage': ('X509v3 Key Usage: critical', 'Digital Signature, Key Encipherment'),
        'extendedKeyUsage': ('X509v3 Extended Key Usage:', 'TLS Web Server Authentication'),
        'subjectAltName': ('X509v3 Subject Alternative Name:', 'DNS:localhost, IP Address:127.0.0.1'),
    }
    for name, wanted in extensions.items():
        lines = crypto.openssl(['x509', '-in', cert, '-noout', '-ext', name]).decode().splitlines()
        require(tuple(line.strip() for line in lines) == wanted, 'CERTIFICATE_PROFILE_INVALID')
    # Explicit trust only; verify validity, self-signature, purpose and both names.
    for flag, name in (('-verify_hostname', 'localhost'), ('-verify_ip', '127.0.0.1')):
        crypto.openssl(['verify', '-no-CApath', '-no-CAstore', '-CAfile', cert,
                        '-check_ss_sig', '-purpose', 'sslserver', flag, name, cert])
    require(before == {name: stamp(directory/name) for name in FILES}, 'MATERIAL_CHANGED')
    return dict(state='VERIFIED', profile=PROFILE, systemTrustChanged=False)


def inspect(root):
    try:
        directory, expected = context(root)
        if not directory.exists() and not directory.is_symlink():
            raise EnvironmentError('SOURCE_OPERATOR_TLS_REQUIRED')
        paths.private(directory.parent, directory=True)
        return inspect_directory(directory, expected)
    except EnvironmentError:
        raise
    except (OSError, ValueError, TypeError, AttributeError, UnicodeError):
        raise EnvironmentError('SOURCE_SERVER_TLS_MATERIAL_INVALID') from None


def publish(stage, directory):
    # macOS renamex_np(RENAME_EXCL): even an empty concurrent destination blocks.
    require(sys.platform == 'darwin', 'PLATFORM_UNSUPPORTED')
    rename = ctypes.CDLL(None, use_errno=True).renamex_np
    rename.argtypes = (ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint)
    rename.restype = ctypes.c_int
    require(rename(os.fsencode(stage), os.fsencode(directory), 0x00000004) == 0,
            'PUBLICATION_CONFLICT')


def prepare(root, state):
    try:
        directory, expected = context(root)
        parent = directory.parent
        if not parent.exists() and not parent.is_symlink():
            parent.mkdir(mode=0o700)
        paths.private(parent, directory=True)
        stage = parent / '.gateway-tls.pending'
        require(not stage.exists() and not stage.is_symlink(), 'RECONCILIATION_REQUIRED')
        if directory.exists() or directory.is_symlink():
            return dict(inspect(root), reused=True)
        require(not state.get('source'), 'RETAINED_SOURCE_TRUST_MISSING')
        stage.mkdir(mode=0o700)  # Exclusive; never remove partial foreign/stale work.
        crypto.openssl(['req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-sha256', '-days', '365',
            '-subj', '/CN=localhost/OU=' + expected['instanceId'],
            '-keyout', stage/'server-key.pem', '-out', stage/'server-cert.pem',
            '-addext', 'basicConstraints=critical,CA:FALSE',
            '-addext', 'keyUsage=critical,digitalSignature,keyEncipherment',
            '-addext', 'extendedKeyUsage=serverAuth',
            '-addext', 'subjectAltName=DNS:localhost,IP:127.0.0.1'])
        crypto.write_private(stage/'identity.json', (json.dumps(expected, sort_keys=True)+'\n').encode())
        result = inspect_directory(stage, expected)
        for name in FILES:
            sync_directory(stage/name)
        sync_directory(stage)
        publish(stage, directory)
        sync_directory(parent)
        return dict(result, reused=False)
    except EnvironmentError:
        raise
    except (OSError, ValueError, TypeError, AttributeError, UnicodeError):
        raise EnvironmentError('SOURCE_SERVER_TLS_INITIALIZATION_FAILED') from None
