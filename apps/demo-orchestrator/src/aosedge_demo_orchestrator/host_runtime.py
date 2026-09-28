# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Fixed, independently locked host inputs; no build or developer fallback."""
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat

from .environment import EnvironmentError
from .status import project_root, read_json

LOCK = 'contracts/portable-host-launch/host-runtime.lock.json'
MANIFEST = 'host-runtime-manifest.json'
ENTRY = {
    'presenter': 'ui/native/Demo Presenter',
    'keyboard': 'ui/native/Driving Control.app/Contents/MacOS/KeyboardControl',
    'python': 'python/bin/python3.12',
    'runtime': 'native/bin/carla-ego-runtime',
    'client': 'native/bin/carla-viss-client',
    'simulator': 'simulator/CarlaUnreal.app/Contents/MacOS/CarlaUnreal',
    'openssl': 'openssl/bin/openssl',
    'openssl-config': 'openssl/openssl.cnf',
    'config': 'ui/gateway/config/m6_2_town10hd_handover.json',
    'runner': 'ui/gateway/tools/run_m6_interactive.py',
    'web': 'ui/demo/apps/presenter-ui/dist/index.html',
}


def require(condition, reason):
    if not condition:
        raise EnvironmentError('HOST_RUNTIME_' + reason)


def identity(path):
    info = path.lstat()
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns, info.st_mode, info.st_nlink)


def safe(root, name):
    parts = PurePosixPath(name).parts if isinstance(name, str) else ()
    require(parts and 0 < len(name) <= 768 and name == '/'.join(parts) and not name.startswith('/') and
            '..' not in parts and '\\' not in name and not any(ord(c) < 32 for c in name), 'PATH_UNSAFE')
    path = root.joinpath(*parts)
    require(not any(p.is_symlink() for p in (path, *path.parents) if p.is_relative_to(root.parent)), 'PATH_UNSAFE')
    return path


@lru_cache(maxsize=4)
def manifest_rows(raw):
    value = json.loads(raw)
    require(isinstance(value, dict) and value.get('schemaVersion') == 1 and
            value.get('status') == 'ASSEMBLED_HOST_LAUNCH_NOT_DISTRIBUTION_QUALIFIED', 'MANIFEST_INVALID')
    rows = value.get('files')
    require(isinstance(rows, list) and 1 <= len(rows) <= 20000, 'MANIFEST_INVALID')
    files, size = {}, 0
    for row in rows:
        require(isinstance(row, dict) and set(row) == {'path', 'bytes', 'sha256', 'mode'}, 'MANIFEST_INVALID')
        name = row['path']
        safe(Path('/__host_input_validation__'), name)
        require(name not in files and name.split('/')[0] in ('ui', 'native', 'python', 'simulator', 'openssl'), 'MANIFEST_INVALID')
        require(type(row['bytes']) is int and 0 <= row['bytes'] <= 16*2**30 and
                type(row['mode']) is int and row['mode'] in (0o444, 0o644, 0o555, 0o755) and
                isinstance(row['sha256'], str) and re.fullmatch('[a-f0-9]{64}', row['sha256']), 'MANIFEST_INVALID')
        size += row['bytes']
        require(size <= 32*2**30, 'SIZE_LIMIT')
        files[name] = row
    require(all(name in files for name in ENTRY.values()), 'ENTRY_MISSING')
    return files


# Per-process only. Every use rechecks the exact regular-file identity.
_verified = {}


class HostRuntime:
    def __init__(self, root, lock):
        self.root = root
        try:
            require(root.is_dir() and not root.is_symlink(), 'PATH_UNSAFE')
            expected = read_json(lock)
            require(expected.get('schemaVersion') == 1 and expected.get('contractId') == 'aosedge-demo-portable-host-launch', 'LOCK_INVALID')
            pin = expected['manifest']
            require(pin['path'] == MANIFEST and type(pin['bytes']) is int and 0 < pin['bytes'] <= 8*2**20, 'LOCK_INVALID')
            path = safe(root, MANIFEST)
            info = path.lstat()
            require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and not info.st_mode & 0o022 and info.st_size == pin['bytes'], 'MANIFEST_INVALID')
            with path.open('rb') as stream:
                raw = stream.read(pin['bytes'] + 1)
            require(len(raw) == pin['bytes'] and hashlib.sha256(raw).hexdigest() == pin['sha256'], 'MANIFEST_CHANGED')
            self.files = manifest_rows(raw)
        except EnvironmentError:
            raise
        except (OSError, ValueError, TypeError, KeyError, AttributeError):
            raise EnvironmentError('HOST_RUNTIME_UNAVAILABLE_OR_INVALID') from None

    def file(self, name):
        try:
            require(name in self.files, 'FILE_NOT_DECLARED')
            row = self.files[name]
            path = safe(self.root, name)
            stamp = identity(path)
            require(stat.S_ISREG(stamp[5]) and stamp[6] == 1 and stamp[2] == row['bytes'] and
                    stat.S_IMODE(stamp[5]) == row['mode'], 'FILE_CHANGED')
            if _verified.get((path, row['sha256'])) != stamp:
                h = hashlib.sha256()
                with path.open('rb') as stream:
                    for part in iter(lambda: stream.read(2**20), b''):
                        h.update(part)
                require(h.hexdigest() == row['sha256'] and identity(path) == stamp, 'FILE_CHANGED')
                _verified[path, row['sha256']] = stamp
            return path
        except EnvironmentError:
            raise
        except OSError:
            raise EnvironmentError('HOST_RUNTIME_FILE_UNAVAILABLE') from None

    def verify(self, *groups):
        # A valid manifest must not hide extra importable modules/providers.
        # Verify the dependency directory inventory before running any entry.
        for group in groups:
            require(group in ('ui', 'python', 'native', 'simulator', 'openssl'), 'GROUP_INVALID')
            directory = safe(self.root, group)
            require(directory.is_dir(), 'GROUP_UNAVAILABLE')
            for path in directory.rglob('*'):
                require(not path.is_symlink(), 'PATH_UNSAFE')
                if not path.is_dir():
                    require(path.relative_to(self.root).as_posix() in self.files, 'UNDECLARED_FILE')
        for name in self.files:
            if name.split('/')[0] in groups:
                self.file(name)

    def entry(self, name):
        return self.file(ENTRY[name])

    def cli(self, root):
        from .runtime_paths import program_root, cli_arguments
        self.verify('python')
        return [str(self.entry('python')), '-I', '-B',
                str(program_root(root) / 'apps/demo-orchestrator/src/aosedge_demo_orchestrator/host_entry.py'),
                *cli_arguments(root)]

    def source_assets(self):
        # Cheap preflight; full consumed groups are verified at explicit Start.
        result = {name: self.entry(name) for name in ('python', 'runtime', 'client', 'simulator', 'config', 'runner', 'keyboard')}
        result.update({'runtime-root': self.root / 'ui/gateway',
                       'keyboard-app': self.root / 'ui/native/Driving Control.app',
                       'python-api-root': self.root / 'python/lib/python3.12/site-packages',
                       'packaged-runtime': self})
        return result


def selected(root=None, catalog=None):
    from .images import ImageCatalog
    from .runtime_paths import catalogue_inputs, installed, program_root, required_group
    root = root or project_root()
    catalog = catalog or ImageCatalog(workspace=root.parent)
    path = catalogue_inputs(catalog) / 'host-runtime'
    if not path.exists() and not path.is_symlink():
        required_group(root, False)
        return None
    return HostRuntime(path, program_root(root) / LOCK)


def simulator_command(paths, screen):
    from .workspace import geometry
    x, y, width, height = geometry(screen, combined=True)['carla']
    return [str(paths['simulator']), '/Game/Carla/Maps/Town10HD_Opt', '-windowed',
            '-ResX=' + str(width), '-ResY=' + str(height - 32), '-WinX=' + str(x), '-WinY=' + str(y),
            # Desktop Restore owns the outer rectangle. Unreal's default
            # aspect lock otherwise changes width when only height changes.
            '-ini:Game:[/Script/EngineSettings.GeneralProjectSettings]:bShouldWindowPreserveAspectRatio=False',
            '-quality-level=Low', '-nosound', '-unattended', '-nosplash', '-carla-rpc-port=2000']
