# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Source-locked SDK inputs for the existing bounded workers; no Cloud I/O."""

from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys

from .environment import EnvironmentError
from .host_runtime import identity, safe
from .status import read_json

LOCK = 'contracts/portable-cloud-backend-inputs/cloud-runtime.lock.json'
MANIFEST = 'cloud-runtime-manifest.json'
CONTRACT = 'aosedge-demo-portable-cloud-inputs'
HINT = 'AOSEDGE_CLOUD_RUNTIME'
PYTHON = 'bin/python3.12'
ADAPTERS = ('aos-prov-5-4-2-compat', 'aos_prov_5_4_2_guard.py', 'aos-prov-5.4.2-source-lock.json')
WORKERS = {'cloud.py', 'cloud_connection_worker.py', 'component_worker.py', 'unit_cloud.py', 'service_cloud.py'}
_verified = {}


def require(condition, reason):
    if not condition:
        raise EnvironmentError('CLOUD_RUNTIME_' + reason)


@lru_cache(maxsize=4)
def rows(raw):
    value = json.loads(raw)
    require(isinstance(value, dict) and value.get('schemaVersion') == 1 and
            value.get('status') == 'ASSEMBLED_NOT_INTEGRATED' and
            value.get('operatorCredentialsCopied') is False, 'MANIFEST_INVALID')
    records = value.get('files')
    require(isinstance(records, list) and 1 <= len(records) <= 10000, 'MANIFEST_INVALID')
    result, total = {}, 0
    for row in records:
        require(isinstance(row, dict) and set(row) == {'path', 'bytes', 'sha256'}, 'MANIFEST_INVALID')
        name = row['path']
        safe(Path('/__cloud_input_validation__'), name)
        require(name not in result and name != MANIFEST and
                name.split('/')[0] in ('bin', 'lib', 'demo', 'notices', 'cloud-wheels.lock.json',
                                       'python-runtime-manifest.json', 'native-manifest.json'), 'MANIFEST_INVALID')
        require(type(row['bytes']) is int and 0 <= row['bytes'] <= 128 * 2**20 and
                isinstance(row['sha256'], str) and re.fullmatch('[a-f0-9]{64}', row['sha256']), 'MANIFEST_INVALID')
        total += row['bytes']
        require(total <= 512 * 2**20, 'SIZE_LIMIT')
        result[name] = row
    require(PYTHON in result and all('demo/scripts/host/' + name in result for name in ADAPTERS), 'ENTRY_MISSING')
    return result


class CloudRuntime:
    def __init__(self, root, lock):
        self.root = root
        try:
            require(root.is_dir() and not root.is_symlink(), 'PATH_UNSAFE')
            expected = read_json(lock)
            require(expected.get('schemaVersion') == 1 and expected.get('contractId') == CONTRACT, 'LOCK_INVALID')
            pin = expected['manifest']
            require(pin['path'] == MANIFEST and type(pin['bytes']) is int and 0 < pin['bytes'] <= 2**21, 'LOCK_INVALID')
            path = safe(root, MANIFEST)
            stamp = identity(path)
            require(stat.S_ISREG(stamp[5]) and stamp[6] == 1 and not stamp[5] & 0o7022 and stamp[2] == pin['bytes'], 'MANIFEST_INVALID')
            with path.open('rb') as stream:
                raw = stream.read(pin['bytes'] + 1)
            require(len(raw) == pin['bytes'] and hashlib.sha256(raw).hexdigest() == pin['sha256'] and
                    identity(path) == stamp, 'MANIFEST_CHANGED')
            self.files = rows(raw)
        except EnvironmentError:
            raise
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            raise EnvironmentError('CLOUD_RUNTIME_UNAVAILABLE_OR_INVALID') from None

    def file(self, name):
        try:
            require(name in self.files, 'FILE_UNDECLARED')
            row = self.files[name]
            path = safe(self.root, name)
            stamp = identity(path)
            require(stat.S_ISREG(stamp[5]) and stamp[6] == 1 and not stamp[5] & 0o7022 and
                    stamp[2] == row['bytes'], 'FILE_CHANGED')
            if _verified.get((path, row['sha256'])) != stamp:
                digest = hashlib.sha256()
                with path.open('rb') as stream:
                    for block in iter(lambda: stream.read(2**20), b''):
                        digest.update(block)
                require(digest.hexdigest() == row['sha256'] and identity(path) == stamp, 'FILE_CHANGED')
                _verified[path, row['sha256']] = stamp
            return path
        except EnvironmentError:
            raise
        except OSError:
            raise EnvironmentError('CLOUD_RUNTIME_FILE_UNAVAILABLE') from None

    def verify(self):
        try:
            declared = {*self.files, MANIFEST}
            for path in self.root.rglob('*'):
                require(not path.is_symlink(), 'PATH_UNSAFE')
                if path.is_dir():
                    require(not path.stat().st_mode & 0o022, 'PATH_UNSAFE')
                else:
                    require(path.relative_to(self.root).as_posix() in declared, 'UNDECLARED_FILE')
            for name in self.files:
                self.file(name)
            require(self.file(PYTHON).stat().st_mode & 0o100, 'INTERPRETER_NOT_EXECUTABLE')
        except OSError:
            raise EnvironmentError('CLOUD_RUNTIME_FILE_UNAVAILABLE') from None


def selected(root, catalog=None):
    from .images import ImageCatalog
    from .runtime_paths import catalogue_inputs, installed, program_root, required_group
    catalog = catalog or ImageCatalog(workspace=root.parent)
    path = catalogue_inputs(catalog) / 'cloud-runtime'
    if not path.exists() and not path.is_symlink():
        required_group(root, False)
        return None
    return CloudRuntime(path, program_root(root) / LOCK)


def launch(root, interpreter, worker):
    """Only input selection changes; caller retains request, deadline and IPC."""
    require(worker in WORKERS, 'WORKER_INVALID')
    runtime = selected(root)
    environment = {'PATH': os.defpath}
    if runtime is not None:
        runtime.verify()
        interpreter = runtime.file(PYTHON)
        environment[HINT] = str(runtime.root)
    return ([str(interpreter), '-I', '-B', str(Path(__file__).with_name(worker))], environment)


def adapter_directory(root):
    hint = os.environ.get(HINT)
    if hint is None:
        return root / 'scripts/host'
    runtime = CloudRuntime(Path(hint), root / LOCK)
    require(Path(sys.executable).absolute() == runtime.file(PYTHON).absolute(), 'INTERPRETER_MISMATCH')
    runtime.verify()
    return runtime.root / 'demo/scripts/host'
