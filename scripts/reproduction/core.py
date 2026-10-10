# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Pinned release, explicit-volume guards and build-only state."""
from __future__ import annotations
from contextlib import contextmanager
import fcntl
import hashlib
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import platform
import plistlib
import shutil
import signal
import stat
import subprocess

ROOT = Path(__file__).resolve().parents[2]
GIB = 2**30
# Read statically by the chain planner; old producers retain their own policy.
STORAGE_CAPABILITIES = ('internal-apfs', 'external-apfs', 'separate-docker-volume')

class LabError(RuntimeError):
    pass

def require(ok, message):
    if not ok:
        raise LabError(message)

def run_command(args, *, env, cwd=None, timeout=30):
    """Own the complete command group, including compiler/Git children."""
    try:
        process = subprocess.Popen(list(map(str, args)), cwd=cwd, env=env,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   start_new_session=True)
    except OSError:
        raise LabError('Required command is unavailable') from None
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except (subprocess.TimeoutExpired, KeyboardInterrupt) as exc:
        # No demo or shared infrastructure is in this newly created process group.
        for sig in (signal.SIGTERM, signal.SIGKILL):
            try:
                os.killpg(process.pid, sig)
            except ProcessLookupError:
                pass
            try:
                process.communicate(timeout=3)
                # Children may close inherited pipes before they exit.
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                break
            except subprocess.TimeoutExpired:
                continue
        if isinstance(exc, KeyboardInterrupt):
            raise
        raise LabError('Command timed out; owned processes stopped, partial work preserved') from None
    return subprocess.CompletedProcess(args, process.returncode, stdout, stderr)

def load_gate():
    loader = importlib.machinery.SourceFileLoader('lab_release_gate', str(ROOT / 'scripts/validate-release-definition'))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

def no_links(path):
    path = Path(os.path.abspath(path))
    require(not any(p.is_symlink() for p in (path, *path.parents)), 'Symlink in storage/input path')
    return path

def regular(path):
    path = no_links(path)
    info = path.stat()
    require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1, 'Expected an unlinked regular file')
    return path

def read_json(path):
    gate = load_gate()
    try:
        return gate.read_json(regular(path))
    except gate.DefinitionError as exc:
        raise LabError(str(exc)) from exc

def atomic_json(path, value):
    path = no_links(path)
    temporary = path.with_name(path.name + '.new')
    if temporary.exists():
        regular(temporary)
    with temporary.open('w', encoding='utf-8') as stream:
        os.chmod(temporary, 0o600)
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)

class Release:
    def __init__(self, path=None):
        gate = load_gate()
        self.path = path or ROOT / gate.DEFAULT
        try:
            self.value = gate.validate(gate.read_json(self.path))
        except gate.DefinitionError as exc:
            raise LabError(str(exc)) from exc
        self.key = digest(self.value)
        self.sources = {s['id']: s for s in self.value['sources']}
        self.components = {c['id']: c for c in self.value['components']}

    def selected_sources(self, profile):
        require(profile in ('operator', 'developer', 'full-source'), 'Unsupported profile')
        needed = {s for c in self.components.values() if c['actions'][profile] != 'reuse' for s in c['sourceIds']}
        return {s: self.sources[s] for s in sorted(needed)}

    def graph(self, profile):
        self.selected_sources(profile)
        result, keys = [], {}
        def visit(name):
            if name in keys:
                return
            c = self.components[name]
            for child in c['requires']:
                visit(child)
            key = digest({'component': c, 'sources': {s: self.sources[s]['revision'] for s in c['sourceIds']},
                          'dependencies': {d: keys[d] for d in c['requires']},
                          'manifests': [i for i in self.value['inputs'] if i['id'] in c['manifestIds']]})
            keys[name] = key
            result.append({'id': name, 'action': c['actions'][profile], 'key': key, 'requires': c['requires']})
        for name in self.components:
            visit(name)
        return result

    def gates(self, profile):
        return [{'id': g['id'], 'resolution': g['resolution']} for g in self.value['gates'] if profile in g['profiles']]

def native_mountpoint(path):
    """Darwin statfs mount identity (sys/mount.h, 64-bit Apple Silicon ABI).

    APFS firmlinks can give a mount and its parent the same st_dev, so the
    generic pathlib mount heuristic is insufficient on the system Data volume.
    """
    import ctypes
    class Statfs(ctypes.Structure):
        _fields_ = ([('bsize', ctypes.c_uint32), ('iosize', ctypes.c_int32)]
            + [(name, ctypes.c_uint64) for name in ('blocks', 'bfree', 'bavail', 'files', 'ffree')]
            + [('fsid', ctypes.c_int32 * 2)]
            + [(name, ctypes.c_uint32) for name in ('owner', 'type', 'flags', 'subtype')]
            + [('fstype', ctypes.c_char * 16), ('mount', ctypes.c_char * 1024),
               ('device', ctypes.c_char * 1024), ('flags_ext', ctypes.c_uint32),
               ('reserved', ctypes.c_uint32 * 7)])
    library = ctypes.CDLL('/usr/lib/libSystem.B.dylib', use_errno=True)
    probe = library.statfs
    probe.argtypes = [ctypes.c_char_p, ctypes.POINTER(Statfs)]
    probe.restype = ctypes.c_int
    value = Statfs()
    if probe(os.fsencode(path), ctypes.byref(value)) != 0:
        raise OSError(ctypes.get_errno(), 'Cannot inspect native mount')
    return Path(os.fsdecode(value.mount))

def is_mounted_volume(path):
    if path.is_mount():
        return True
    if platform.system() != 'Darwin' or platform.machine() != 'arm64':
        return False
    try:
        return path.is_dir() and native_mountpoint(path) == path
    except (OSError, ValueError, AttributeError):
        return False

def storage_volume(path):
    require(platform.system() == 'Darwin' and platform.machine() == 'arm64', 'Preparation requires macOS on Apple Silicon')
    path = no_links(path)
    existing = next(p for p in (path, *path.parents) if p.exists())
    try:
        # /Users is a firmlink into the Data volume: walking lexical parents
        # would select the sealed system volume. Ask df for the actual device.
        result = subprocess.run(['/bin/df', '-P', str(existing)], capture_output=True,
                                timeout=10, env={'LC_ALL':'C', 'PATH':'/usr/bin:/bin:/usr/sbin:/sbin'})
        require(result.returncode == 0, 'Cannot locate storage device')
        rows = result.stdout.decode('utf-8').splitlines()
        fields = rows[-1].split(None, 5) if len(rows) == 2 else []
        require(len(fields) == 6 and fields[0].startswith('/dev/disk'), 'Expected a local mounted disk')
        result = subprocess.run(['/usr/sbin/diskutil', 'info', '-plist', fields[0]], capture_output=True, timeout=10)
        require(result.returncode == 0, 'Cannot inspect selected storage')
        info = plistlib.loads(result.stdout)
    except (OSError, ValueError, UnicodeError, plistlib.InvalidFileException, subprocess.TimeoutExpired) as exc:
        raise LabError('Cannot inspect selected storage') from exc
    require(isinstance(info, dict) and isinstance(info.get('MountPoint'), str), 'Missing storage mount point')
    mount = no_links(info['MountPoint'])
    require(type(info.get('Internal')) is bool and info.get('WritableVolume') is True
            and isinstance(info.get('VolumeUUID'), str) and info['VolumeUUID']
            and info.get('FilesystemType') == 'apfs', 'A writable local APFS volume is required')
    require(is_mounted_volume(mount) and existing.stat().st_dev == mount.stat().st_dev,
            'Reported volume differs from selected storage')
    require(path not in (mount, Path('/')), 'Select a directory within the volume, not its root')
    # A stale/missing /Volumes/NAME directory can live on the internal Data
    # volume. Even a first preparation must not mistake it for a mounted disk.
    if path.is_relative_to('/Volumes'):
        require(mount.is_relative_to('/Volumes') and mount != Path('/Volumes')
                and path.is_relative_to(mount), 'Selected /Volumes disk is not mounted; no fallback')
    if not info['Internal']:
        require(path.is_relative_to(mount), 'External storage must remain inside its mounted volume')
    pool = info.get('APFSContainerReference')
    require(isinstance(pool, str) and pool.startswith('disk'), 'Missing APFS capacity pool identity')
    return {'uuid': info['VolumeUUID'], 'mount': str(mount), 'device': mount.stat().st_dev,
            'internal': info['Internal'], 'pool': pool}

def check_volume(path, volume):
    """Cheap in-operation checks; UUIDs are rebound/validated at command entry."""
    mount = Path(volume['mount'])
    require(is_mounted_volume(mount) and mount.stat().st_dev == volume['device'], 'Storage volume disconnected or replaced')
    path = no_links(path)
    existing = next(p for p in (path, *path.parents) if p.exists())
    require(existing.stat().st_dev == volume['device'], 'Storage escaped the selected volume')
    return existing

def capacity_report(requests):
    """Sum additional demand per APFS pool, retaining one largest reserve.

    Each request is (label, path, volume, additional bytes, reserve bytes).
    Per-volume checks also honor tighter volume quotas; free space is never
    summed across volumes in the same pool. This is admission, not a peak claim.
    """
    pools = {}
    for label, path, volume, additional, reserve in requests:
        require(type(additional) is int and additional >= 0 and type(reserve) is int and reserve >= 0,
                'Invalid capacity reservation')
        existing = check_volume(path, volume)
        free = shutil.disk_usage(existing).free
        key = volume.get('pool', volume['uuid'])
        row = pools.setdefault(key, {'pool':key, 'locations':[], 'freeBytes':free,
                                    'additionalBytes':0, 'reserveBytes':0})
        row['freeBytes'] = min(row['freeBytes'], free)
        row['additionalBytes'] += additional
        row['reserveBytes'] = max(row['reserveBytes'], reserve)
        row['locations'].append({'role':label, 'path':str(path), 'volumeUUID':volume['uuid'],
                                 'freeBytes':free, 'requiredBytes':additional+reserve})
    for row in pools.values():
        row['requiredBytes'] = row['additionalBytes'] + row['reserveBytes']
        row['fits'] = row['freeBytes'] >= row['requiredBytes']
    return list(pools.values())

def require_capacity(requests):
    rows = capacity_report(requests)
    for row in rows:
        locations = ', '.join(f"{r['role']}: {r['path']}" for r in row['locations'])
        require(row['fits'], f"Insufficient disk space ({locations}): {row['freeBytes']/GIB:.2f} GiB available, "
                f"{row['requiredBytes']/GIB:.2f} GiB required including reserve")
    return rows

class Storage:
    def __init__(self, path, release, profile):
        self.root = no_links(path)
        self.release, self.profile = release, profile
        release.selected_sources(profile)
        self.volume = storage_volume(self.root)
        self.binding = {'schemaVersion': 1, 'release': release.key, 'releaseId': release.value['id'],
                        'profile': profile, 'volumeUUID': self.volume['uuid']}
        self.state_path = self.root / 'preparation.json'

    def check(self, additional=0, reserve=60*GIB):
        require_capacity([('workspace', self.root, self.volume, additional, reserve)])

    def path(self, relative):
        p = Path(relative)
        require(not p.is_absolute() and '..' not in p.parts, 'Path escapes preparation storage')
        self.check(reserve=0)
        return no_links(self.root / p)

    def state(self):
        value = read_json(self.state_path)
        require(type(value) is dict, 'Invalid preparation state')
        require(value.get('binding') == self.binding, 'Prepared release/profile/volume differs; use another storage directory')
        require(set(value) == {'binding', 'sources', 'artifacts', 'builds'}, 'Invalid preparation state')
        require(all(type(value[k]) is dict for k in ('sources', 'artifacts', 'builds')), 'Invalid preparation state sections')
        return value

    def initialize(self):
        self.check()
        if self.state_path.exists():
            self.state()
            return
        require(not self.root.exists() or not any(self.root.iterdir()), 'Refusing an unowned nonempty storage directory')
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        atomic_json(self.state_path, {'binding': self.binding, 'sources': {}, 'artifacts': {}, 'builds': {}})

    def save(self, state):
        self.check(reserve=0)
        require(state['binding'] == self.binding, 'Invalid state binding')
        atomic_json(self.state_path, state)

    @contextmanager
    def locked(self):
        # Serialize first initialization and subsequent updates in the parent.
        self.check()
        require(self.root.parent.is_dir(), 'Create the explicit storage parent first')
        lock = no_links(self.root.parent / ('.' + self.root.name + '.lab.lock'))
        descriptor = os.open(lock, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        try:
            info = os.fstat(descriptor)
            require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1, 'Unsafe lock file')
            try:
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise LabError('Another preparation/build is active') from exc
            self.initialize()
            from distribution.build_scratch import directory
            with directory(self.root) as scratch:
                self._scratch = scratch
                try:
                    yield self.state()
                finally:
                    del self._scratch
        finally:
            os.close(descriptor)

    def environment(self, create=True):
        env = {k: v for k, v in os.environ.items() if k in ('PATH', 'LANG', 'LC_ALL', 'TERM')}
        scratch_root = no_links(os.environ.get('SDV_SCRATCH_ROOT', self.root / '.tmp'))
        require(scratch_root.name == '.tmp', 'Scratch must use the workspace .tmp directory')
        existing = next(p for p in (scratch_root, *scratch_root.parents) if p.exists())
        require(existing.stat().st_dev == self.volume['device'], 'Scratch escaped selected volume')
        inherited = Path(os.environ.get('TMPDIR', str(scratch_root)))
        scratch = getattr(self, '_scratch', inherited if inherited.is_relative_to(scratch_root) else scratch_root)
        no_links(scratch)
        if create:
            scratch.mkdir(parents=True, exist_ok=True, mode=0o700)
        env['TMPDIR'] = str(scratch)
        env['SDV_SCRATCH_ROOT'] = str(scratch_root)
        for name, relative in [('XDG_CACHE_HOME', 'cache/tools'),
                               ('npm_config_cache', 'cache/npm'), ('PIP_CACHE_DIR', 'cache/pip'),
                               ('CMAKE_BUILD_PARALLEL_LEVEL', None)]:
            if relative is None:
                env[name] = '4'
            else:
                directory = self.path(relative)
                if create:
                    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
                env[name] = str(directory)
        env['PYTHONDONTWRITEBYTECODE'] = '1'
        env['GIT_CONFIG_NOSYSTEM'] = '1'
        env['GIT_CONFIG_GLOBAL'] = os.devnull
        env['GIT_TERMINAL_PROMPT'] = '0'
        env['GIT_NO_LAZY_FETCH'] = '1'
        return env
