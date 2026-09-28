# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Locked backend candidates; no Docker command, archive import or state write."""

import hashlib
import json
from pathlib import Path
import re
import stat

from .environment import EnvironmentError
from .host_runtime import identity, safe
from .status import read_json

LOCK = 'contracts/portable-cloud-backend-inputs/backend-inputs.lock.json'
MANIFEST = 'backend-image-manifest.json'
CONTRACT = 'aosedge-demo-portable-backend-inputs'
_verified = {}


def require(condition, reason):
    if not condition:
        raise EnvironmentError('BACKEND_INPUTS_' + reason)


class BackendInputs:
    def __init__(self, root, lock):
        self.root = root
        try:
            require(root.is_dir() and not root.is_symlink(), 'PATH_UNSAFE')
            expected = read_json(lock)
            require(expected.get('schemaVersion') == 1 and expected.get('contractId') == CONTRACT, 'LOCK_INVALID')
            pin = expected['manifest']
            require(pin['path'] == MANIFEST and type(pin['bytes']) is int and 0 < pin['bytes'] <= 16384, 'LOCK_INVALID')
            path = self._file(MANIFEST, pin['bytes'])
            with path.open('rb') as stream:
                raw = stream.read(pin['bytes'] + 1)
            require(len(raw) == pin['bytes'] and hashlib.sha256(raw).hexdigest() == pin['sha256'], 'MANIFEST_CHANGED')
            value = json.loads(raw)
            require(value.get('schemaVersion') == 1 and value.get('status') ==
                    'OFFLINE_INTEGRITY_VERIFIED_NOT_CLEAN_ENGINE_QUALIFIED' and
                    value.get('operatorDataIncluded') is False, 'MANIFEST_INVALID')
            records = value['images']
            require(isinstance(records, list) and len(records) == 2, 'MANIFEST_INVALID')
            self.candidates = {}
            for row in records:
                team = row['team']
                require(team in ('brake', 'tire') and team not in self.candidates and
                        re.fullmatch('sha256:[0-9a-f]{64}', row['imageId']) and
                        re.fullmatch('[0-9a-f]{40}', row['source']) and row['architecture'] == 'linux/arm64', 'MANIFEST_INVALID')
                protocols = expected['protocols'][team]
                require(protocols == (dict(mockCleanupProtocol='isolated-mock-v1') if team == 'brake' else
                        dict(mockCleanupProtocol='isolated-mock-v1', privateCleanupProtocol='tire-product-v1')), 'PROTOCOL_INVALID')
                self.candidates[team] = dict(schemaVersion=1, team=team, imageId=row['imageId'],
                    sourceRevision=row['source'], **protocols)
            self.size, self.digest = value['archiveBytes'], value['archiveSha256']
            require(type(self.size) is int and 0 < self.size <= 512 * 2**20 and
                    re.fullmatch('[0-9a-f]{64}', self.digest), 'MANIFEST_INVALID')
            require({p.name for p in root.iterdir()} == {MANIFEST, 'backends.tar'}, 'UNDECLARED_FILE')
            self._file('backends.tar', self.size)
        except EnvironmentError:
            raise
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            raise EnvironmentError('BACKEND_INPUTS_UNAVAILABLE_OR_INVALID') from None

    def _file(self, name, size):
        path = safe(self.root, name)
        info = path.lstat()
        require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and not info.st_mode & 0o7022 and
                info.st_size == size, 'FILE_CHANGED')
        return path

    def archive(self):
        """Explicit setup integrity gate; selection/status never reread 78 MiB."""
        try:
            path = self._file('backends.tar', self.size)
            stamp = identity(path)
            if _verified.get((path, self.digest)) != stamp:
                digest = hashlib.sha256()
                with path.open('rb') as stream:
                    for block in iter(lambda: stream.read(2**20), b''):
                        digest.update(block)
                require(digest.hexdigest() == self.digest and identity(path) == stamp, 'ARCHIVE_CHANGED')
                _verified[path, self.digest] = stamp
            return path
        except OSError:
            raise EnvironmentError('BACKEND_INPUTS_FILE_UNAVAILABLE') from None

    def candidate(self, team):
        require(team in self.candidates, 'TEAM_INVALID')
        return dict(self.candidates[team])


def selected(environment):
    from .runtime_paths import catalogue_inputs, installed, program_root, required_group
    path = catalogue_inputs(environment.catalog) / 'backend-inputs'
    if not path.exists() and not path.is_symlink():
        if installed():
            required_group(environment.root, False)
        return None
    return BackendInputs(path, program_root(environment.root) / LOCK)
