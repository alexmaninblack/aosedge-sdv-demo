# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Locked portable inputs inside the existing catalogue; no build/fallback."""

import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import stat

from .environment import EnvironmentError
from .status import read_json

LOCK = 'contracts/portable-preparation-inputs/vehicle-inputs.lock.json'
MANIFEST = 'vehicle-input-manifest.json'


def require(condition, code):
    if not condition:
        raise EnvironmentError('PREPARATION_INPUTS_' + code)


def selected(environment):
    from .runtime_paths import catalogue_inputs, installed, program_root, required_group
    root = catalogue_inputs(environment.catalog) / 'preparation-inputs'
    if not root.exists() and not root.is_symlink():
        if installed():
            required_group(environment.root, False)
        return None
    return PreparationInputs(root, program_root(environment.root) / LOCK)


class PreparationInputs:
    def __init__(self, root, lock):
        self.root = root
        try:
            require(root.is_dir() and not root.is_symlink(), 'PATH_UNSAFE')
            expected = read_json(lock)
            require(isinstance(expected, dict) and expected.get('schemaVersion') == 1 and
                    expected.get('contractId') == 'aosedge-demo-portable-preparation-inputs' and
                    expected.get('contractVersion') == '1.0.0' and
                    isinstance(expected.get('manifest'), dict) and
                    expected['manifest'].get('path') == MANIFEST, 'LOCK_INVALID')
            pin = expected['manifest']
            require(type(pin.get('bytes')) is int and 0 < pin['bytes'] <= 262144, 'LOCK_INVALID')
            raw = self._raw(MANIFEST, pin['bytes'])
            require(hashlib.sha256(raw).hexdigest() == pin.get('sha256'), 'MANIFEST_DIGEST_MISMATCH')
            self.manifest = json.loads(raw)
            require(isinstance(self.manifest, dict), 'MANIFEST_INVALID')
            rows = self.manifest.get('files', [])
            require(self.manifest.get('schemaVersion') == 1 and
                    self.manifest.get('status') == 'ASSEMBLED_PREPARATION_INPUTS_NOT_UPLOAD_READY' and
                    isinstance(rows, list) and 1 <= len(rows) <= 512, 'MANIFEST_INVALID')
            self.files, size = {}, 0
            for row in rows:
                require(isinstance(row, dict) and set(row) == {'path', 'bytes', 'sha256'}, 'MANIFEST_INVALID')
                name = row['path']
                require(isinstance(name, str) and name not in self.files and name != MANIFEST, 'MANIFEST_INVALID')
                require(type(row['bytes']) is int and 0 <= row['bytes'] <= 8 * 2**30 and
                        isinstance(row['sha256'], str) and re.fullmatch(r'[0-9a-f]{64}', row['sha256']), 'MANIFEST_INVALID')
                size += row['bytes']
                require(size <= 9 * 2**30, 'SIZE_LIMIT')
                self._path(name, row['bytes'])
                self.files[name] = row
        except EnvironmentError:
            raise
        except (OSError, ValueError, TypeError, KeyError):
            raise EnvironmentError('PREPARATION_INPUTS_UNAVAILABLE_OR_INVALID') from None

    def _path(self, name, size):
        require(isinstance(name, str) and 0 < len(name) <= 512, 'PATH_UNSAFE')
        parts = PurePosixPath(name).parts
        require(parts and name == '/'.join(parts) and not name.startswith('/') and '..' not in parts and
                '\\' not in name and not any(ord(c) < 32 for c in name), 'PATH_UNSAFE')
        path = self.root.joinpath(*parts)
        require(not any(p.is_symlink() for p in (path, *path.parents) if p.is_relative_to(self.root.parent)), 'PATH_UNSAFE')
        info = path.lstat()
        require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and not info.st_mode & 0o022 and info.st_size == size,
                'FILE_MISMATCH')
        return path

    def _raw(self, name, size):
        with self._path(name, size).open('rb') as stream:
            raw = stream.read(size + 1)
        require(len(raw) == size, 'FILE_MISMATCH')
        return raw

    def read(self, name, limit=32 * 2**20):
        try:
            row = self.files.get(name)
            require(row is not None and row['bytes'] <= limit, 'FILE_NOT_DECLARED_OR_TOO_LARGE')
            raw = self._raw(name, row['bytes'])
            require(hashlib.sha256(raw).hexdigest() == row['sha256'], 'FILE_DIGEST_MISMATCH')
            return raw
        except EnvironmentError:
            raise
        except (OSError, ValueError, TypeError):
            raise EnvironmentError('PREPARATION_INPUTS_FILE_UNAVAILABLE') from None

    def contract(self, name):
        return json.loads(self.read('contracts/' + name, 2**20))

    def runtime(self):
        from .component_build import advisory_runtime_pin, ADVISORY_RUNTIME_MODULES, PACKAGE
        pin = advisory_runtime_pin()
        require(json.loads(self.read('vdp/reviewed-runtime/pin.json')) == pin, 'RUNTIME_PIN_MISMATCH')
        files = {}
        for name in ADVISORY_RUNTIME_MODULES:
            raw = self.read('vdp/reviewed-runtime/' + PACKAGE + name, 2**20)
            require(hashlib.sha256(raw).hexdigest() == pin['modules'][name], 'RUNTIME_DIGEST_MISMATCH')
            files[PACKAGE + name] = raw
        return files

    def vdp(self, service, version):
        from .component_build import PROFILE_BASES
        from .component_sources import UNSIGNED_SHA
        require(version in UNSIGNED_SHA, 'VDP_PROFILE_INVALID')
        profile = next(k for k, v in PROFILE_BASES.items() if v[0] == version)
        prefix = 'vdp/profiles/' + profile + '/'
        expected = dict(schemaVersion=1, version=version, legacyArchiveSha256=PROFILE_BASES[profile][1],
                        unsignedSha256=UNSIGNED_SHA[version], trust='REVIEWED_SOURCE_DIGESTS')
        require(json.loads(self.read(prefix + 'source.json')) == expected, 'VDP_RECEIPT_MISMATCH')
        require(hashlib.sha256(self.read(prefix + 'package.tar.gz')).hexdigest() == UNSIGNED_SHA[version], 'VDP_DIGEST_MISMATCH')
        info, payload = service._inspect(version, path=self.root / prefix / 'package.tar.gz')
        require(not info['problems'] and not info['signedEnvelope'] and info['sha256'] == UNSIGNED_SHA[version],
                'VDP_STRUCTURE_INVALID')
        return dict(info, source=expected, signatureVerification='NOT_APPLICABLE',
                    sourceIntegrity='VERIFIED_PINNED_DIGESTS'), payload

    def service(self, team, profile):
        matches = [r for r in self.manifest['serviceProfiles'] if r['team'] == team and r['profile'] == profile]
        require(len(matches) == 1, 'SERVICE_PROFILE_INVALID')
        pin = matches[0]
        prefix = 'services/' + team + '/' + profile + '/'
        for name in self.files:
            if name.startswith(prefix):
                self.read(name)
        product = json.loads(self.read(prefix + 'product-build.json'))
        expected = {'rootfs/usr/bin/' + team + '-health-' + role: pin[role + 'Sha256'] for role in ('bootstrap', 'service')}
        require(product.get('sourceRevision') == pin['source'] and product.get('functionalProfile') == profile and
                product.get('schemaVersion') == 1 and product.get('architecture') == 'arm64' and product.get('os') == 'linux' and
                product.get('kind') == team + '-health-linux-arm64-product' and len(product['binaries']) == 2 and
                {r['path']: r['sha256'] for r in product['binaries']} == expected, 'SERVICE_IDENTITY_MISMATCH')
        require(product['tests'].get('ctest') == 'passed' and product['tests'].get('count', 0) > 0 and
                hashlib.sha256(self.read(prefix + 'evidence/ctest-results.xml')).hexdigest() == product['tests'].get('reportSha256'),
                'SERVICE_TEST_RECEIPT_MISMATCH')
        # Configuration is read by the unchanged packager after allocation.
        # Check its complete selected contract set now, before any Cloud call.
        contracts = ('brake-telemetry-window/brake-telemetry-window-profile.v1.json',
                     'brake-health-model/brake-health-model-profile.v1.json',
                     'brake-health-runtime/brake-health-runtime-profile.v1.json') if team == 'brake' else (
                     'tire-health-model/tire-health-product-profile.v1.json',)
        for name in contracts:
            self.contract(name)
        return dict(schemaVersion=1, team=team, contentProfile=profile, state='BUILT', sourceRevision=pin['source'],
                    qualification='BUILT_NOT_LIVE_QUALIFIED', outputPath=str(self.root / prefix), binaries=expected,
                    preparationInputsRoot=str(self.root), noOp=True)
