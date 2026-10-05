# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Explicit installed-instance scope; no implicit activation or state migration."""

from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import plistlib
import re
import stat
import subprocess
from uuid import UUID, uuid4

CODE_ROOT = Path(__file__).resolve().parents[4]
MARKER = 'instance.json'
_active = None


def require(value, reason):
    if not value:
        raise ValueError('INSTALLED_' + reason)


def canonical(path):
    path = Path(path).absolute()
    require('..' not in path.parts and not any(c in str(path) for c in ('\x00', '\n', '\r', ',')), 'PATH_INVALID')
    require(not any(p.is_symlink() for p in (path, *path.parents)), 'PATH_LINKED')
    return path


def private(path, directory=False):
    canonical(path)
    info = path.lstat()
    require((stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode) and info.st_nlink == 1)
            and info.st_uid == os.getuid()
            and stat.S_IMODE(info.st_mode) == (0o700 if directory else 0o600), 'STATE_NOT_PRIVATE')


def small_json(path, limit=131072, owned=False):
    canonical(path)
    if owned:
        private(path)
    info = path.lstat()
    require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_size <= limit, 'METADATA_INVALID')
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, 'METADATA_INVALID')
            result[key] = value
        return result
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, 'rb') as stream:
        opened = os.fstat(stream.fileno())
        require((opened.st_dev, opened.st_ino) == (info.st_dev, info.st_ino), 'METADATA_CHANGED')
        raw = stream.read(limit+1)
        after = os.fstat(stream.fileno())
    fields = ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_ctime_ns', 'st_mode', 'st_uid', 'st_nlink')
    require(len(raw) == info.st_size and all(getattr(info, k) == getattr(after, k) == getattr(path.lstat(), k)
                                           for k in fields), 'METADATA_CHANGED')
    try:
        return json.loads(raw, object_pairs_hook=unique), raw
    except (UnicodeError, json.JSONDecodeError, RecursionError):
        raise ValueError('INSTALLED_METADATA_INVALID') from None


def instance(path):
    root = canonical(path)
    private(root, directory=True)
    require(len(os.fsencode(root / '.run/demo-current/control/control.sock')) < 104, 'SOCKET_PATH_TOO_LONG')
    require(root.stat().st_dev == Path.home().stat().st_dev, 'STATE_REQUIRES_INTERNAL_VOLUME')
    value, _ = small_json(root / MARKER, 4096, owned=True)
    require(isinstance(value, dict) and set(value) == {'schemaVersion', 'kind', 'instanceId'}
            and type(value['schemaVersion']) is int and value['schemaVersion'] == 1
            and value['kind'] == 'aosedge-demo-instance', 'STATE_SCHEMA_UNSUPPORTED')
    try:
        require(str(UUID(value['instanceId'])) == value['instanceId'], 'INSTANCE_ID_INVALID')
    except (ValueError, TypeError, AttributeError):
        raise ValueError('INSTALLED_INSTANCE_ID_INVALID') from None
    for name in ('.local', '.run', 'artifacts'):
        child = root / name
        if child.exists() or child.is_symlink():
            private(child, directory=True)
    return root, value['instanceId']


def create_instance(path):
    """Explicit fresh creation only; no foreign-directory adoption or credentials."""
    root = canonical(path)
    require(root.parent.is_dir(), 'STATE_PARENT_MISSING')
    if root.exists():
        checked, identity = instance(root)
        return dict(instanceId=identity, reused=True)
    require(len(os.fsencode(root / '.run/demo-current/control/control.sock')) < 104, 'SOCKET_PATH_TOO_LONG')
    require(root.parent.stat().st_dev == Path.home().stat().st_dev, 'STATE_REQUIRES_INTERNAL_VOLUME')
    root.mkdir(mode=0o700)
    value = dict(schemaVersion=1, kind='aosedge-demo-instance', instanceId=str(uuid4()))
    fd = os.open(root / MARKER, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'w') as stream:
        json.dump(value, stream, sort_keys=True)
        stream.flush(); os.fsync(stream.fileno())
    # Create the shared parent privately before any first-use consumer runs.
    # pathlib mkdir(parents=True) applies its mode only to the final directory.
    for name in ('.local', '.local/demo-control', '.run', 'artifacts'):
        (root / name).mkdir(mode=0o700)
    fd = os.open(root, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)
    return dict(instanceId=value['instanceId'], reused=False)


@dataclass(frozen=True)
class Layout:
    state: Path
    program: Path
    inputs: Path
    instance_id: str


def installed(root=None):
    if _active is None:
        return False
    require(root is None or Path(root).absolute() == _active.state, 'FOREIGN_STATE_ROOT')
    return True


def state_root():
    return _active.state if installed() else CODE_ROOT


def program_root(root=None):
    return _active.program if installed(root) else (Path(root) if root is not None else CODE_ROOT)


def input_root():
    require(installed(), 'INSTANCE_NOT_SELECTED')
    return _active.inputs


def catalogue_inputs(catalog):
    """Keep the developer catalogue protocol unchanged, including test doubles."""
    return input_root() / 'aosedge-sdv-demo' if installed() else catalog.project


def instance_id():
    return _active.instance_id if installed() else None


def cli_arguments(root):
    return ['--instance-root', str(root)] if installed(root) else []


def required_group(root, present):
    require(not installed(root) or present, 'PACKAGED_INPUT_REQUIRED')


def credential_defaults(root):
    prefix = '.local/demo-control/credentials/' if installed(root) else '~/.aos/security/'
    return {'oem-delivery': dict(credential=prefix+'aos-user-oem.p12', expectedRole='oem'),
            'service-provider': dict(credential=prefix+'aos-user-sp.p12', expectedRole='service provider')}


def volume_uuid(path):
    """Bind mounted package bytes to the installer's volume, not its mount name."""
    device_id = path.stat().st_dev
    try:
        result = subprocess.run(['/bin/df', '-P', str(path)], capture_output=True, timeout=15,
                                env={'PATH': '/usr/bin:/bin:/usr/sbin:/sbin', 'LC_ALL': 'C'})
        lines = result.stdout.decode().splitlines()
        require(result.returncode == 0 and len(lines) == 2 and lines[1].split(), 'VOLUME_UNAVAILABLE')
        device = lines[1].split()[0]
        require(re.fullmatch(r'/dev/disk\d+(?:s\d+)+', device), 'VOLUME_INVALID')
        result = subprocess.run(['/usr/sbin/diskutil', 'info', '-plist', device], capture_output=True, timeout=15)
        require(result.returncode == 0, 'VOLUME_UNAVAILABLE')
        info = plistlib.loads(result.stdout)
        require(info.get('GlobalPermissionsEnabled') is True and info.get('DeviceNode') == device
                and path.stat().st_dev == device_id
                and Path(info['MountPoint']).stat().st_dev == device_id, 'VOLUME_CHANGED')
        return str(UUID(info['VolumeUUID'])).upper()
    except (OSError, subprocess.TimeoutExpired, UnicodeError, plistlib.InvalidFileException,
            KeyError, TypeError, AttributeError):
        raise ValueError('INSTALLED_VOLUME_UNAVAILABLE') from None


@contextmanager
def installed_session(root, *, _program=None):
    """One explicit scope for shared CLI/API; workers retain their existing IPC."""
    global _active
    require(_active is None, 'INSTANCE_ALREADY_SELECTED')
    state, identity = instance(root)
    program = canonical(_program if _program is not None else CODE_ROOT)
    kit = program.parent
    pin = kit.name
    require(program.name == 'aosedge-sdv-demo' and kit.parent.name == 'versions'
            and re.fullmatch(r'[0-9a-f]{64}', pin), 'PACKAGE_REQUIRED')
    require(not state.is_relative_to(kit) and not kit.is_relative_to(state), 'STATE_PACKAGE_OVERLAP')
    require(not os.environ.get('DEMO_ARTIFACT_ROOT'), 'ARTIFACT_OVERRIDE_FORBIDDEN')
    for directory in (kit.parent.parent, kit.parent, kit.parent.parent / 'receipts'):
        private(directory, directory=True)
    store, _ = small_json(kit.parent.parent / 'store.json', 4096, owned=True)
    receipt, _ = small_json(kit.parent.parent / 'receipts' / (pin+'.json'), 4096, owned=True)
    manifest, raw = small_json(kit / 'application-manifest.json', 2**20)
    require(isinstance(store, dict) and set(store) == {'schemaVersion', 'kind', 'volumeUUID'}
            and type(store['schemaVersion']) is int and store['schemaVersion'] == 1
            and store.get('kind') == 'aosedge-package-store'
            and isinstance(receipt, dict) and type(receipt.get('schemaVersion')) is int
            and receipt['schemaVersion'] == 1 and receipt.get('status') == 'INSTALLED_NOT_ACTIVATED'
            and receipt.get('manifestSha256') == pin and receipt.get('volumeUUID') == store.get('volumeUUID')
            and all(receipt.get(k) is False for k in ('runtimeChanged', 'operatorStateCopied', 'cloudAccessed', 'activeVersionSelected'))
            and hashlib.sha256(raw).hexdigest() == pin
            and isinstance(manifest, dict) and manifest.get('operatorStateCopied') is False,
            'PACKAGE_RECEIPT_INVALID')
    require(volume_uuid(kit) == store['volumeUUID'], 'VOLUME_CHANGED')
    from .installed_control import runtime_leases
    with runtime_leases(state, identity, kit.parent.parent, pin, manifest):
        _active = Layout(state, program, kit/'demo-artifacts', identity)
        try:
            yield _active
        finally:
            _active = None
