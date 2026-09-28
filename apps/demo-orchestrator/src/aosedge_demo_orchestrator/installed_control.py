# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Private version-selection records and leases; never operates the demo."""

from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
import re
import stat
import subprocess

from .runtime_paths import canonical, private, require, small_json

CONTRACT = 'aosedge-demo-installed-state/1'
RECORD = 'installation.json'
LOCK = 'installation.lock'
SHA = re.compile(r'[0-9a-f]{64}')


def pin(value):
    require(isinstance(value, str) and SHA.fullmatch(value), 'VERSION_INVALID')
    return value


@contextmanager
def lease(path, exclusive=False, create=True):
    path = canonical(path)
    flags = (os.O_RDWR if exclusive else os.O_RDONLY) | os.O_NOFOLLOW | os.O_CLOEXEC
    fd = os.open(path, flags | (os.O_CREAT if create else 0), 0o600)
    try:
        info = os.fstat(fd)
        require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_uid == os.getuid()
                and stat.S_IMODE(info.st_mode) == 0o600, 'LEASE_UNSAFE')
        private(path)
        require((path.stat().st_dev, path.stat().st_ino) == (info.st_dev, info.st_ino), 'LEASE_CHANGED')
        try:
            fcntl.flock(fd, (fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH) | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError('INSTALLED_IN_USE') from None
        yield
        require((path.stat().st_dev, path.stat().st_ino) == (info.st_dev, info.st_ino), 'LEASE_CHANGED')
    finally:
        os.close(fd)


def selection(root, identity):
    path = root / RECORD
    if not path.exists() and not path.is_symlink():
        return None
    value, _ = small_json(path, 8192, owned=True)
    require(isinstance(value, dict) and set(value) == {'schemaVersion', 'instanceId', 'storePath',
        'volumeUUID', 'stateContract', 'revision', 'current', 'previous'}, 'SELECTION_INVALID')
    require(type(value['schemaVersion']) is int and value['schemaVersion'] == 1
            and value['instanceId'] == identity and value['stateContract'] == CONTRACT
            and type(value['revision']) is int and 0 < value['revision'] < 2**53
            and isinstance(value['storePath'], str) and Path(value['storePath']).is_absolute()
            and str(canonical(value['storePath'])) == value['storePath'], 'SELECTION_INVALID')
    from uuid import UUID
    try:
        require(str(UUID(value['volumeUUID'])).upper() == value['volumeUUID'], 'SELECTION_INVALID')
    except (ValueError, TypeError, AttributeError):
        raise ValueError('INSTALLED_SELECTION_INVALID') from None
    for field in ('current', 'previous'):
        if value[field] is not None:
            pin(value[field])
    require(value['current'] is None or value['current'] != value['previous'], 'SELECTION_INVALID')
    return value


def sync(path):
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def commit_selection(root, value):
    """Caller owns the exclusive lease; a failed rename leaves the old choice."""
    pending = root / (RECORD + '.pending')
    if pending.exists() or pending.is_symlink():
        private(pending)
        pending.unlink()  # Fixed private interrupted metadata only, never user data.
    fd = os.open(pending, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write((json.dumps(value, sort_keys=True) + '\n').encode())
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(pending, root / RECORD)
    sync(root)


def unused(paths):
    """Detached consumers also block. Failure to inspect is never evidence of idle."""
    roots = tuple(str(canonical(p)) for p in paths)
    try:
        result = subprocess.run(['/usr/sbin/lsof', '-nP', '-a', '-u', str(os.getuid()), '-Fpn'],
                                capture_output=True, timeout=30)
        require(result.returncode == 0 and not result.stderr and len(result.stdout) <= 16*2**20,
                'USAGE_UNKNOWN')
        owner, processes = None, 0
        for line in result.stdout.decode('utf-8').splitlines():
            if line.startswith('p'):
                require(line[1:].isdigit(), 'USAGE_UNKNOWN')
                owner = int(line[1:]); processes += 1
            elif line.startswith('n'):
                require(owner is not None, 'USAGE_UNKNOWN')
                name = line[1:]
                if owner != os.getpid() and any(name == p or name.startswith(p + '/') for p in roots):
                    raise ValueError('INSTALLED_NATIVE_CONSUMER_ACTIVE')
        require(processes > 0, 'USAGE_UNKNOWN')
    except (OSError, subprocess.SubprocessError, UnicodeError):
        raise ValueError('INSTALLED_USAGE_UNKNOWN') from None


def quiescent(root, store):
    # No inference from stale "stopped" statuses. Retained-run upgrades are a
    # separate qualification gate and must not be unblocked by deleting data.
    for name in ('.run/demo-current/journal.json', '.local/demo-current'):
        path = root / name
        require(not path.exists() and not path.is_symlink(), 'CURRENT_RUN_RETAINED')
    unused((root, store))


def repair_complete(store, digest):
    work = canonical(store / 'quarantine' / pin(digest))
    if work.exists():
        private(work, directory=True)
        path = work / 'transaction.json'
        require(path.exists() or path.is_symlink(), 'REPAIR_RECONCILIATION_REQUIRED')
        value, _ = small_json(path, 4096, owned=True)
        require(isinstance(value, dict) and value.get('schemaVersion') == 1
                and value.get('manifestSha256') == digest and value.get('status') == 'REPAIRED',
                'REPAIR_RECONCILIATION_REQUIRED')


@contextmanager
def runtime_leases(state, identity, store, digest, manifest):
    managed = manifest.get('installedStateContract')
    # Legacy kits are readable for existing engineering proof, not selectable
    # by the managed launcher. New kits require explicit selection.
    if managed is not None:
        require(managed == CONTRACT, 'STATE_COMPATIBILITY_UNSUPPORTED')
        require(selection(state, identity) is not None, 'VERSION_NOT_SELECTED')
    # Managed selection already created this lock. Runtime consumers must not
    # implicitly recreate missing ownership metadata during a read-only check.
    with lease(state / LOCK, create=managed is None):
        value = selection(state, identity)
        if managed is not None or value is not None:
            require(value is not None and value['current'] == digest
                    and value['storePath'] == str(store), 'VERSION_NOT_SELECTED')
            marker, _ = small_json(store / 'store.json', 4096, owned=True)
            require(value['volumeUUID'] == marker.get('volumeUUID'), 'VOLUME_CHANGED')
        repair_complete(store, digest)
        if managed is None:
            yield
        else:
            with lease(store / 'receipts' / (digest + '.use.lock'), create=False):
                repair_complete(store, digest)
                yield
