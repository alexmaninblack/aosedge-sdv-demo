# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Explicit local Setup signing; never silently replace a missing identity."""

import hashlib
from pathlib import Path
import re
import subprocess

from installation_inputs import file_info, require, unlinked

IDENTIFIER = 'org.aosedge.sdvlab.setup.preview'
FINGERPRINT = re.compile(r'[0-9A-Fa-f]{40}')


def run(arguments, code):
    try:
        result = subprocess.run(arguments, capture_output=True, text=True, timeout=60,
                                env={'PATH': '/usr/bin:/bin:/usr/sbin:/sbin', 'LC_ALL': 'C'})
    except (OSError, subprocess.SubprocessError):
        raise ValueError(code) from None
    require(result.returncode == 0, code)
    return result.stdout + result.stderr


def select(identity=None, ad_hoc=False, *, distribution=False):
    # An engineering build must explicitly acknowledge its unstable identity.
    require(type(ad_hoc) is bool and ((identity is not None) != ad_hoc),
            'SETUP_SIGNING_MODE_REQUIRED')
    require(type(distribution) is bool and not (distribution and ad_hoc),
            'SETUP_SIGNING_DISTRIBUTION_MODE_INVALID')
    if ad_hoc:
        return '-'
    require(isinstance(identity, str) and FINGERPRINT.fullmatch(identity),
            'SETUP_SIGNING_IDENTITY_INVALID')
    observed = run(['/usr/bin/security', 'find-identity', '-v', '-p', 'codesigning'],
                   'SETUP_SIGNING_DISCOVERY_FAILED')
    matches = re.findall(r'^\s*\d+\) ([0-9A-Fa-f]{40}) "([^"\r\n]+)"\s*$', observed, re.M)
    names = {name for fingerprint, name in matches if fingerprint.upper() == identity.upper()}
    require(len(names) == 1, 'SETUP_SIGNING_IDENTITY_UNAVAILABLE')
    prefix = 'Developer ID Application: ' if distribution else 'Apple Development: '
    require(next(iter(names)).startswith(prefix),
            'SETUP_SIGNING_DEVELOPER_ID_REQUIRED' if distribution else 'SETUP_SIGNING_DEVELOPMENT_REQUIRED')
    return identity.upper()


def native_bootstrap(app):
    """Only the previously authenticated copied Python closure; never kit code."""
    root = unlinked(Path(app) / 'Contents/Resources/python')
    require(root.is_dir(), 'SETUP_SIGNING_BOOTSTRAP_MISSING')
    files = sorted(root.rglob('*'))
    require(len(files) <= 12000, 'SETUP_SIGNING_BOOTSTRAP_TOO_LARGE')
    native = []
    magics = {bytes.fromhex(value) for value in
              ('feedface', 'feedfacf', 'cefaedfe', 'cffaedfe',
               'cafebabe', 'bebafeca', 'cafebabf', 'bfbafeca')}
    for path in files:
        require(not path.is_symlink(), 'SETUP_SIGNING_BOOTSTRAP_LINK')
        if path.is_dir():
            continue
        file_info(path)
        with path.open('rb') as stream:
            if stream.read(4) in magics:
                native.append(path)
    require(root / 'bin/python3.12' in native and len(native) <= 1000,
            'SETUP_SIGNING_BOOTSTRAP_INVALID')
    return sorted(native, key=lambda p: (-len(p.parts), str(p)))


def inspect_hardened(path, prefix, expected_team, distribution):
    details = run(['/usr/bin/codesign', '-dvv', str(path)], 'SETUP_SIGNATURE_INSPECTION_FAILED')
    require('(runtime)' in details and 'TeamIdentifier=' + expected_team in details.splitlines()
            and any(line.startswith('Authority=' + prefix) for line in details.splitlines()),
            'SETUP_SIGNATURE_HARDENED_INVALID')
    require(not distribution or any(line.startswith('Timestamp=') for line in details.splitlines()),
            'SETUP_SIGNATURE_TIMESTAMP_REQUIRED')


def sign(app, identity, *, hardened=False, distribution=False):
    require(identity == '-' or (isinstance(identity, str) and FINGERPRINT.fullmatch(identity)),
            'SETUP_SIGNING_IDENTITY_INVALID')
    require(type(hardened) is bool and type(distribution) is bool
            and (not distribution or hardened) and (not hardened or identity != '-'),
            'SETUP_SIGNING_HARDENED_MODE_INVALID')
    nested = native_bootstrap(app) if hardened else []
    options = ['--options', 'runtime'] if hardened else []
    timestamp = '--timestamp' if distribution else '--timestamp=none'
    for path in nested:
        run(['/usr/bin/codesign', '--force', '--sign', identity, *options, timestamp, str(path)],
            'SETUP_NESTED_SIGNING_FAILED')
    # Never use deep signing, custom requirements or permission exceptions.
    run(['/usr/bin/codesign', '--force', '--sign', identity, *options, timestamp, str(app)],
        'SETUP_SIGNING_FAILED')
    run(['/usr/bin/codesign', '--verify', '--deep', '--strict', str(app)],
        'SETUP_SIGNATURE_INVALID')
    details = run(['/usr/bin/codesign', '-dvv', str(app)], 'SETUP_SIGNATURE_INSPECTION_FAILED')
    requirement = run(['/usr/bin/codesign', '-d', '-r-', str(app)],
                      'SETUP_SIGNATURE_INSPECTION_FAILED')
    require('Identifier=' + IDENTIFIER in details.splitlines(), 'SETUP_SIGNATURE_IDENTIFIER_MISMATCH')
    rows = [line.split('designated => ', 1)[1] for line in requirement.splitlines()
            if 'designated => ' in line]
    require(len(rows) == 1, 'SETUP_SIGNATURE_REQUIREMENT_MISSING')
    team = None
    if identity == '-':
        require('Signature=adhoc' in details.splitlines(), 'SETUP_SIGNATURE_MODE_MISMATCH')
    else:
        teams = re.findall(r'^TeamIdentifier=([A-Z0-9]{10})$', details, re.M)
        prefix = 'Developer ID Application: ' if distribution else 'Apple Development: '
        require(len(teams) == 1 and 'Signature=adhoc' not in details.splitlines()
                and any(line.startswith('Authority=' + prefix) for line in details.splitlines())
                and 'anchor apple' in rows[0] and 'cdhash' not in rows[0],
                'SETUP_SIGNATURE_IDENTITY_UNSTABLE')
        team = teams[0]
        if hardened:
            for path in [*nested, app]:
                inspect_hardened(path, prefix, team, distribution)
    mode = ('developer-id-application-unnotarized' if distribution else
            'ad-hoc-local-only' if identity == '-' else 'apple-development-local-only')
    return dict(signing=mode, hardenedRuntime=hardened,
                signedNativeFiles=len(nested) + 1, secureTimestamp=distribution,
                teamIdentifier=team, stableSigningIdentity=identity != '-',
                designatedRequirementSha256=hashlib.sha256(rows[0].encode()).hexdigest(),
                consentPersistenceQualified=False)
