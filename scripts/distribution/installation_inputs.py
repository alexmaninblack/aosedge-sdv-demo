# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Bounded complete-kit reader. Never imports or executes supplied payloads."""

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import unicodedata

LOCKS = {
    'host-runtime': 'portable-host-launch/host-runtime.lock.json',
    'preparation-inputs': 'portable-preparation-inputs/vehicle-inputs.lock.json',
    'vm-runtime': 'portable-vm-launch/vm-runtime.lock.json',
    'cloud-runtime': 'portable-cloud-backend-inputs/cloud-runtime.lock.json',
    'backend-inputs': 'portable-cloud-backend-inputs/backend-inputs.lock.json',
}
CATALOGUE = 'demo-artifacts/aosedge-sdv-demo'
SHA = re.compile(r'[0-9a-f]{64}')
MAX_FILES = 25000
MAX_BYTES = 48 * 2**30
MAX_JSON = 8 * 2**20


class InstallError(ValueError):
    """Fixed public failure code; no arbitrary input or secret in diagnostics."""


def require(value, code):
    if not value:
        raise InstallError(code)


def relative(value):
    require(isinstance(value, str) and 0 < len(value.encode('utf-8')) <= 1024,
            'INPUT_PATH_INVALID')
    require(not any(ord(c) < 32 or c in '\\:' for c in value), 'INPUT_PATH_INVALID')
    parts = value.split('/')
    require(len(parts) <= 32 and all(p not in ('', '.', '..') for p in parts), 'INPUT_PATH_INVALID')
    require(not PurePosixPath(value).is_absolute() and unicodedata.normalize('NFC', value) == value,
            'INPUT_PATH_INVALID')
    return value


def unlinked(path):
    path = Path(path).absolute()
    require(all(not p.is_symlink() for p in (path, *path.parents)), 'PATH_HAS_LINK')
    return path


def identity(path):
    info = path.lstat()
    return (info.st_dev, info.st_ino, info.st_mode, info.st_size,
            info.st_mtime_ns, info.st_ctime_ns, info.st_nlink)


def file_info(path):
    unlinked(path)
    info = path.lstat()
    require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1
            and not info.st_mode & 0o7022, 'INPUT_FILE_UNSAFE')
    return info


def no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'JSON_DUPLICATE_KEY')
        result[key] = value
    return result


def parse(raw):
    try:
        return json.loads(raw, object_pairs_hook=no_duplicates)
    except (UnicodeError, json.JSONDecodeError, RecursionError):
        raise InstallError('INPUT_JSON_INVALID') from None


def read_small(path, limit=MAX_JSON):
    info = file_info(path)
    require(info.st_size <= limit, 'INPUT_METADATA_TOO_LARGE')
    before = identity(path)
    with path.open('rb') as stream:
        raw = stream.read(limit + 1)
    require(len(raw) == info.st_size and identity(path) == before, 'SOURCE_CHANGED')
    return raw


def digest(path):
    file_info(path)
    before = identity(path)
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 2**20), b''):
            value.update(block)
    require(identity(path) == before, 'SOURCE_CHANGED')
    return value.hexdigest()


def inventory(root):
    root = unlinked(root)
    require(root.is_dir(), 'INPUT_DIRECTORY_MISSING')
    result, pending, directories = set(), [root], 0
    while pending:
        parent = pending.pop()
        info = parent.lstat()
        require(stat.S_ISDIR(info.st_mode) and not info.st_mode & 0o7022,
                'INPUT_DIRECTORY_UNSAFE')
        with os.scandir(parent) as entries:
            for entry in entries:
                path = Path(entry.path)
                info = entry.stat(follow_symlinks=False)
                name = relative(path.relative_to(root).as_posix())
                if stat.S_ISDIR(info.st_mode):
                    directories += 1
                    require(directories <= MAX_FILES, 'INPUT_INVENTORY_TOO_LARGE')
                    pending.append(path)
                else:
                    require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1
                            and not info.st_mode & 0o7022, 'INPUT_FILE_UNSAFE')
                    result.add(name)
                    require(len(result) <= MAX_FILES, 'INPUT_INVENTORY_TOO_LARGE')
    return result


@dataclass(frozen=True)
class Row:
    size: int
    sha256: str
    mode: int


class Bundle:
    def __init__(self, root, expected_sha256):
        require(isinstance(expected_sha256, str) and SHA.fullmatch(expected_sha256), 'RELEASE_PIN_INVALID')
        self.root = unlinked(root)
        self.pin = expected_sha256
        self.rows, self.identities, self._folded = {}, {}, set()
        raw = read_small(self.root/'application-manifest.json', 2**20)
        require(hashlib.sha256(raw).hexdigest() == self.pin, 'APPLICATION_MANIFEST_MISMATCH')
        manifest = parse(raw)
        require(isinstance(manifest, dict) and manifest.get('schemaVersion') == 1
                and manifest.get('operatorStateCopied') is False, 'APPLICATION_MANIFEST_INVALID')
        require(isinstance(manifest.get('inputs'), dict) and set(manifest['inputs']) == set(LOCKS),
                'REQUIRED_INPUT_GROUP_MISSING')
        self._add('application-manifest.json', dict(bytes=len(raw), sha256=self.pin))
        rows = manifest.get('applicationFiles')
        require(isinstance(rows, list) and 0 < len(rows) <= 1000, 'APPLICATION_INVENTORY_INVALID')
        for row in rows:
            require(isinstance(row, dict), 'INPUT_ROW_INVALID')
            name = relative(row.get('path'))
            require(name in ('LICENSE', 'workspace/repositories.json', 'config/aosvm-single-node-unitconfig.json') or name.startswith(
                ('apps/demo-orchestrator/src/', 'contracts/')), 'APPLICATION_PATH_UNDECLARED')
            self._add('aosedge-sdv-demo/' + name, row)
        required = {'aosedge-sdv-demo/apps/demo-orchestrator/src/aosedge_demo_orchestrator/' + name
                    for name in ('__init__.py', 'cli.py', 'presenter.py', 'host_entry.py')}
        require(required <= self.rows.keys(), 'APPLICATION_ENTRY_MISSING')
        for group, lock_name in LOCKS.items():
            name = 'aosedge-sdv-demo/contracts/' + lock_name
            require(name in self.rows, 'INPUT_LOCK_MISSING')
            self.verify_file(name)
            lock = parse(read_small(self.root/name))
            require(isinstance(lock, dict) and lock.get('manifest') == manifest['inputs'][group],
                    'INPUT_LOCK_MISMATCH')
            pin = lock['manifest']
            require(isinstance(pin, dict), 'INPUT_PIN_INVALID')
            group_path = CATALOGUE + '/' + group + '/'
            name = group_path + relative(pin.get('path'))
            self._add(name, pin)
            self.verify_file(name)
            value = parse(read_small(self.root/name))
            require(isinstance(value, dict), 'INPUT_MANIFEST_INVALID')
            if group == 'vm-runtime':
                require(value.get('hostManifest') == manifest['inputs']['host-runtime'],
                        'VM_HOST_MANIFEST_MISMATCH')
            if group == 'backend-inputs':
                rows = [dict(path='backends.tar', bytes=value.get('archiveBytes'), sha256=value.get('archiveSha256'))]
            else:
                rows = value.get('files')
            require(isinstance(rows, list) and 0 < len(rows) <= 20000, 'INPUT_INVENTORY_INVALID')
            for row in rows:
                require(isinstance(row, dict), 'INPUT_ROW_INVALID')
                self._add(group_path + relative(row.get('path')), row)
            if group == 'preparation-inputs':
                factory = value.get('factory')
        require(isinstance(factory, dict), 'FACTORY_REFERENCE_INVALID')
        version = relative(factory.get('version'))
        image = relative(factory.get('image'))
        require('/' not in version and '/' not in image and image != 'manifest.json', 'FACTORY_REFERENCE_INVALID')
        for leaf in ('manifest.json', image):
            source = CATALOGUE + '/preparation-inputs/factory/' + version + '/' + leaf
            target = CATALOGUE + '/factory-images/' + version + '/' + leaf
            require(source in self.rows, 'FACTORY_REFERENCE_MISSING')
            row = self.rows[source]
            self._add(target, dict(bytes=row.size, sha256=row.sha256, mode=row.mode))
        self.check_inventory()
        self.total_bytes = sum(row.size for row in self.rows.values())
        require(self.total_bytes <= MAX_BYTES, 'INPUT_SIZE_BUDGET_EXCEEDED')

    def _add(self, name, row):
        name = relative(name)
        folded = name.casefold()
        require(folded not in self._folded, 'INPUT_PATH_DUPLICATE')
        self._folded.add(folded)
        size, sha = row.get('bytes'), row.get('sha256')
        require(type(size) is int and 0 <= size <= 16*2**30
                and isinstance(sha, str) and SHA.fullmatch(sha), 'INPUT_ROW_INVALID')
        path = self.root/name
        info = file_info(path)
        mode = stat.S_IMODE(info.st_mode)
        require(info.st_size == size, 'INPUT_FILE_SIZE_MISMATCH')
        require('mode' not in row or type(row['mode']) is int and row['mode'] == mode,
                'INPUT_FILE_MODE_MISMATCH')
        self.rows[name] = Row(size, sha, mode)
        self.identities[name] = identity(path)
        require(len(self.rows) <= MAX_FILES, 'INPUT_INVENTORY_TOO_LARGE')

    def check_inventory(self):
        require(inventory(self.root) == set(self.rows), 'INPUT_INVENTORY_MISMATCH')

    def unchanged(self, name):
        require(identity(self.root/name) == self.identities[name], 'SOURCE_CHANGED')

    def verify_file(self, name):
        self.unchanged(name)
        require(digest(self.root/name) == self.rows[name].sha256, 'INPUT_DIGEST_MISMATCH')

    def verify(self):
        self.check_inventory()
        for name in self.rows:
            self.verify_file(name)
        self.check_inventory()
        for name in self.rows:
            self.unchanged(name)
