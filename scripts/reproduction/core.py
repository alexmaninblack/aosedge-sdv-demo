# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Pinned release, external-volume guard and build-only state."""
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

def external_volume(path):
    require(platform.system() == 'Darwin' and platform.machine() == 'arm64', 'Preparation requires macOS on Apple Silicon')
    path = no_links(path)
    existing = next(p for p in (path, *path.parents) if p.exists())
    # diskutil accepts a device or mount point, not an arbitrary child directory.
    selected_mount = next(p for p in (existing, *existing.parents) if p.is_mount())
    try:
        result = subprocess.run(['/usr/sbin/diskutil', 'info', '-plist', str(selected_mount)], capture_output=True, timeout=10)
        require(result.returncode == 0, 'Cannot inspect external storage')
        info = plistlib.loads(result.stdout)
    except (OSError, ValueError, plistlib.InvalidFileException, subprocess.TimeoutExpired) as exc:
        raise LabError('Cannot inspect external storage') from exc
    mount = no_links(info.get('MountPoint', '/'))
    require(mount == selected_mount, 'Reported volume differs from selected mount')
    require(info.get('Internal') is False and info.get('WritableVolume') is True and info.get('VolumeUUID'),
            'A writable external volume is required; no internal fallback')
    require(mount != Path('/') and mount.is_mount() and path != mount and path.is_relative_to(mount),
            'Storage must be a directory inside a mounted external volume')
    return {'uuid': info['VolumeUUID'], 'mount': str(mount), 'device': mount.stat().st_dev}

class Storage:
    def __init__(self, path, release, profile):
        self.root = no_links(path)
        self.release, self.profile = release, profile
        release.selected_sources(profile)
        self.volume = external_volume(self.root)
        self.binding = {'schemaVersion': 1, 'release': release.key, 'releaseId': release.value['id'],
                        'profile': profile, 'volumeUUID': self.volume['uuid']}
        self.state_path = self.root / 'preparation.json'

    def check(self, additional=0, reserve=60*GIB):
        mount = Path(self.volume['mount'])
        require(mount.is_mount() and mount.stat().st_dev == self.volume['device'], 'External volume disconnected or replaced')
        no_links(self.root)
        existing = next(p for p in (self.root, *self.root.parents) if p.exists())
        require(existing.stat().st_dev == self.volume['device'], 'Storage escaped the selected volume')
        require(shutil.disk_usage(existing).free >= reserve + additional, 'Insufficient external disk space including reserve')

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
            yield self.state()
        finally:
            os.close(descriptor)

    def environment(self, create=True):
        env = {k: v for k, v in os.environ.items() if k in ('PATH', 'LANG', 'LC_ALL', 'TERM')}
        for name, relative in [('TMPDIR', 'tmp'), ('XDG_CACHE_HOME', 'cache/tools'),
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
