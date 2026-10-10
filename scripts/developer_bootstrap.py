# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Small pre-clone owner. Embedded in the downloadable macOS launcher."""
import hashlib
import fcntl
import json
import os
from pathlib import Path
import re
import signal
import stat
import subprocess
import sys
import tempfile

REMOTE = 'https://github.com/alexmaninblack/aosedge-sdv-demo.git'


class WorkflowError(RuntimeError):
    pass


def require(ok, message):
    if not ok:
        raise WorkflowError(message)


def safe(path):
    path = Path(path)
    require(path.is_absolute() and '..' not in path.parts
            and not any(p.is_symlink() for p in (path, *path.parents)),
            'Unsafe or linked workflow path; existing files were preserved.')
    return path


def read(path):
    path = safe(path)
    info = path.stat()
    require(stat.S_ISREG(info.st_mode) and info.st_uid == os.getuid()
            and info.st_nlink == 1 and info.st_size <= 1024 * 1024,
            'Unsafe workflow metadata; existing files were preserved.')
    return json.loads(path.read_text())


def save(path, value):
    path = safe(path)
    fd, temporary = tempfile.mkstemp(prefix='.workflow-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump(value, stream, sort_keys=True)
            stream.write('\n')
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def git(directory, *args, timeout=60, optional=False):
    # No interactive credentials, inherited repository overrides or local hooks.
    env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
    env.update(GIT_TERMINAL_PROMPT='0', GIT_CONFIG_NOSYSTEM='1',
               GIT_CONFIG_GLOBAL='/dev/null', GIT_LFS_SKIP_SMUDGE='1')
    process = subprocess.Popen(['git', '-c', 'core.hooksPath=/dev/null',
                                '-c', 'protocol.file.allow=never', *args],
                               cwd=directory, env=env, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, text=True, start_new_session=True)
    try:
        output, _ = process.communicate(timeout=timeout)
    except (subprocess.TimeoutExpired, KeyboardInterrupt) as error:
        for sig in (signal.SIGTERM, signal.SIGKILL):
            try:
                os.killpg(process.pid, sig)
            except ProcessLookupError:
                pass
            try:
                process.communicate(timeout=3)
                break
            except subprocess.TimeoutExpired:
                continue
        if isinstance(error, KeyboardInterrupt):
            raise
        raise WorkflowError('Source operation timed out. The selected commit and partial checkout were preserved; rerun after checking connectivity.') from None
    if optional and process.returncode != 0:
        return ''
    require(process.returncode == 0,
            'Source operation failed. Check connectivity/repository access; existing sources and the selected commit were preserved.')
    return output.strip()


def validate_checkout(path, revision=None):
    safe(path)
    require((path/'.git').is_dir() and not (path/'.git').is_symlink(),
            'Expected an independent source checkout, not a linked worktree.')
    require(git(path, 'rev-parse', '--show-toplevel') == str(path)
            and git(path, 'remote') == 'origin'
            and git(path, 'remote', 'get-url', '--all', 'origin') == REMOTE,
            'Existing source belongs to a different repository; it was not changed.')
    require(not git(path, 'status', '--porcelain', '--untracked-files=all'),
            'Existing source has local changes. Preserve/review them before continuing; no reset or overwrite was performed.')
    actual = git(path, 'rev-parse', 'HEAD')
    require(re.fullmatch('[a-f0-9]{40}', actual) and (revision is None or actual == revision),
            'Source revision changed since this build was selected; no update was adopted.')
    return actual


def source_matches(source, requirements):
    pins = requirements.get('sourceFiles')
    require(isinstance(pins, dict) and pins, 'Prepared source requirements are missing.')
    for name, expected in pins.items():
        require(isinstance(name, str) and not Path(name).is_absolute()
                and '..' not in Path(name).parts and re.fullmatch('[a-f0-9]{64}', expected),
                'Invalid prepared source requirement.')
        path = safe(source/name)
        require(path.is_file() and path.stat().st_size <= 1024*1024
                and hashlib.sha256(path.read_bytes()).hexdigest() == expected,
                'Cloned source requirements differ from the prepared release. Obtain matching preparation/source; no inputs were downloaded or built.')
    require((source/'scripts/developer_build.py').is_file(),
            'The selected repository revision does not yet contain the one-run workflow. Publish the reviewed source before the joint walkthrough.')


def checkout(root, volume, requirements_path):
    lock = safe(Path(root)/'.developer-preparation/workflow.lock')
    fd = os.open(lock, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'w') as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise WorkflowError('Another source/build workflow is using this workspace.') from None
        return _checkout(root, volume, requirements_path)


def _checkout(root, volume, requirements_path):
    root = safe(root)
    control = safe(root/'.developer-preparation')
    require(control.is_dir() and (control/'.aosedge-preparation').read_text().strip()
            == 'aosedge-developer-preparation-v1', 'Prepared workspace ownership is missing.')
    requirements = read(requirements_path)
    requirements_key = hashlib.sha256(json.dumps(requirements, sort_keys=True,
                                                separators=(',', ':')).encode()).hexdigest()
    source = safe(root/'source')
    partial = safe(control/'source.partial')
    receipt = safe(control/'root-source.json')
    binding = dict(schemaVersion=1, remote=REMOTE, root=str(root), volumeUUID=volume,
                   requirementsSha256=requirements_key)
    if receipt.exists():
        selected = read(receipt)
        require(set(selected) == set(binding) | {'revision'}
                and all(selected[k] == v for k, v in binding.items())
                and re.fullmatch('[a-f0-9]{40}', selected['revision']),
                'Saved source selection belongs to another volume/release. Use a separate workspace; nothing was replaced.')
    else:
        require(not partial.exists(), 'Unowned partial checkout preserved; inspect it before continuing.')
        if source.exists():
            revision = validate_checkout(source)
            source_matches(source, requirements)
        else:
            print('Selecting the current main revision…', flush=True)
            rows = git(root, 'ls-remote', '--exit-code', REMOTE, 'refs/heads/main').splitlines()
            require(len(rows) == 1 and re.fullmatch('[a-f0-9]{40}\trefs/heads/main', rows[0]),
                    'Cannot resolve one main revision; no source was selected.')
            revision = rows[0].split()[0]
        selected = {**binding, 'revision': revision}
        # Persist before fetching: a resumed run never follows a moving main.
        save(receipt, selected)
    revision = selected['revision']
    if not source.exists():
        partial.mkdir(exist_ok=True, mode=0o700)
        if not (partial/'.git').exists():
            require(not any(partial.iterdir()), 'Unexpected partial checkout contents preserved.')
            git(partial, 'init', '--quiet')
        require((partial/'.git').is_dir() and not (partial/'.git').is_symlink(), 'Unsafe partial Git directory.')
        remotes = git(partial, 'remote')
        if not remotes:
            git(partial, 'remote', 'add', 'origin', REMOTE)
        require(git(partial, 'remote') == 'origin'
                and git(partial, 'remote', 'get-url', '--all', 'origin') == REMOTE,
                'Partial checkout remote changed; preserved without fetching.')
        # A checkout interrupted after materialization is reused only if clean.
        probe = git(partial, 'rev-parse', '--verify', '--quiet', '--end-of-options', revision+'^{commit}', optional=True)
        if not probe:
            print('Downloading root source (large binary inputs are not included)…', flush=True)
            git(partial, 'fetch', '--quiet', '--no-tags', 'origin', revision, timeout=900)
        # Do not force/reset an interrupted or modified worktree.
        require(not git(partial, 'status', '--porcelain', '--untracked-files=all'),
                'Partial source checkout has changes; inspect it before resuming.')
        git(partial, 'checkout', '--quiet', '--detach', revision)
        validate_checkout(partial, revision)
        source_matches(partial, requirements)
        require(not source.exists(), 'Source destination appeared during preparation; both copies preserved.')
        os.rename(partial, source)
    validate_checkout(source, revision)
    source_matches(source, requirements)
    print('Root source ready at ' + revision + ' (fixed for repeats).', flush=True)
    return selected


if __name__ == '__main__':
    def cancel(signum, frame):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, cancel)
    signal.signal(signal.SIGINT, cancel)
    try:
        require(len(sys.argv) == 4, 'Invalid bootstrap invocation.')
        checkout(*sys.argv[1:])
    except KeyboardInterrupt:
        print('Source preparation stopped; selection and partial work preserved.', file=sys.stderr)
        sys.exit(130)
    except (WorkflowError, OSError, ValueError, KeyError, TypeError) as error:
        print('STOP: ' + (str(error) if isinstance(error, WorkflowError) else
                         'Source preparation metadata is unavailable or malformed; existing files preserved.'), file=sys.stderr)
        sys.exit(1)
