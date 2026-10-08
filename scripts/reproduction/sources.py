# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Exact, non-destructive source preparation. Never reset a user checkout."""
from .core import LabError, require, atomic_json, read_json, no_links, run_command

def git(path, args, env, timeout=30):
    result = run_command(['git', '--no-pager', '-C', str(path), '-c', 'core.hooksPath=/dev/null',
                          '-c', 'credential.helper=', *args], env=env, timeout=timeout)
    require(result.returncode == 0, 'Git operation failed; check source access or resume incomplete preparation')
    return result.stdout.decode('utf-8').strip()

def check_source(path, source, env):
    no_links(path)
    require((path / '.git').is_dir() and not (path / '.git').is_symlink(), 'Expected independent source checkout')
    require(git(path, ['rev-parse', '--show-toplevel'], env) == str(path.resolve()), 'Wrong source root')
    require(git(path, ['remote', 'get-url', 'origin'], env) == source['repository'], 'Wrong source remote')
    require(git(path, ['rev-parse', 'HEAD'], env) == source['revision'], 'Wrong source revision; no automatic reset')
    require(not git(path, ['status', '--porcelain', '--untracked-files=all'], env), 'Dirty source checkout; preserved unchanged')

def prepare_sources(storage, state, progress):
    env = storage.environment()
    for name, source in storage.release.selected_sources(storage.profile).items():
        storage.check(additional=2*2**30)
        require(source['access'] == 'public-git', 'Restricted source needs explicit entitlement preparation')
        path = storage.path('sources/' + name)
        marker = storage.path('sources/' + name + '.json')
        expected = {'repository': source['repository'], 'revision': source['revision']}
        if path.exists() and not marker.exists():
            raise LabError('Source path collision; existing data preserved')
        if marker.exists():
            require(read_json(marker) == expected, 'Source ownership marker differs')
        else:
            path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            atomic_json(marker, expected)
        if not path.exists():
            path.mkdir(mode=0o700)
        if not (path / '.git').exists():
            require(not any(path.iterdir()), 'Unowned files in incomplete source directory')
            git(path, ['init', '--quiet'], env)
        # A cancelled init may have completed before adding origin.
        remotes = git(path, ['remote'], env).splitlines()
        if not remotes:
            require(set(p.name for p in path.iterdir()) == {'.git'}, 'Incomplete source contains unowned files')
            git(path, ['remote', 'add', 'origin', source['repository']], env)
        require(git(path, ['remote', 'get-url', 'origin'], env) == source['repository'], 'Wrong source remote')
        # Missing HEAD is only resumable in our empty, marked initial checkout.
        head = run_command(['git', '-C', str(path), 'rev-parse', '--verify', 'HEAD'], env=env, timeout=10)
        if head.returncode:
            require(set(p.name for p in path.iterdir()) == {'.git'}, 'Partial checkout requires inspection; no overwrite')
            progress('FETCH_SOURCE', name)
            git(path, ['fetch', '--quiet', '--depth=1', '--no-tags', 'origin', source['revision']], env, timeout=180)
            storage.check()
            git(path, ['-c', 'submodule.recurse=false', 'checkout', '--quiet', '--detach', source['revision']], env)
        check_source(path, source, env)
        state['sources'][name] = expected
        storage.save(state)
        progress('SOURCE_READY', name)
    return state

def verify_sources(storage, state, complete=True):
    env = storage.environment(create=False)
    selected = storage.release.selected_sources(storage.profile)
    require(set(state['sources']).issubset(selected), 'Unexpected source receipt')
    if complete:
        require(set(state['sources']) == set(selected), 'Required sources are not all prepared')
    for name in state['sources']:
        source = selected[name]
        require(state['sources'][name] == {'repository': source['repository'], 'revision': source['revision']},
                'Source receipt differs from release')
        check_source(storage.path('sources/' + name), source, env)
    return len(state['sources'])
