# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Owned, disposable build scratch. Never a cache, output or credential store."""
from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
import re
import shutil
import signal
import stat
import subprocess
import tempfile
import threading
import warnings

MARKER = 'aosedge-build-scratch-v1'


class ScratchError(RuntimeError):
    pass


def safe(path):
    if not Path(path).is_absolute() or '..' in Path(path).parts:
        raise ScratchError('Scratch requires an absolute path without traversal')
    path = Path(os.path.abspath(path))
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ScratchError('Linked scratch path; preserved')
    return path


def private(path, directory=False):
    value = safe(path).stat()
    kind = stat.S_ISDIR if directory else stat.S_ISREG
    if (not kind(value.st_mode) or value.st_uid != os.getuid()
            or value.st_mode & 0o077 or (not directory and value.st_nlink != 1)):
        raise ScratchError('Unsafe scratch ownership or mode; preserved')
    return value


def root_for(anchor, root=None):
    anchor = safe(anchor)
    if not anchor.is_dir():
        raise ScratchError('Scratch anchor must already exist')
    selected = root or os.environ.get('SDV_SCRATCH_ROOT') or anchor / '.tmp'
    selected = safe(selected)
    if selected.name != '.tmp' or not selected.parent.is_dir():
        raise ScratchError('Scratch must use an existing workspace parent and its .tmp directory')
    if selected.parent.stat().st_dev != anchor.stat().st_dev:
        raise ScratchError('Scratch must stay on the selected volume; no fallback')
    try:
        selected.mkdir(mode=0o700)
    except FileExistsError:
        private(selected, True)
    private(selected, True)
    marker = selected / '.owner'
    # An empty/new directory can be adopted; unknown existing contents cannot.
    if not marker.exists():
        if any(selected.iterdir()):
            raise ScratchError('Unowned nonempty scratch directory; preserved')
        try:
            fd = os.open(marker, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            with os.fdopen(fd, 'w') as stream:
                stream.write(MARKER + '\n')
        except FileExistsError:
            pass
    if private(marker).st_size != len(MARKER) + 1 or marker.read_text() != MARKER + '\n':
        raise ScratchError('Unknown scratch marker; preserved')
    return selected


@contextmanager
def lock(path, nonblocking=False):
    fd = os.open(safe(path), os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        private(path)
        fcntl.flock(fd, fcntl.LOCK_EX | (fcntl.LOCK_NB if nonblocking else 0))
        yield fd
    finally:
        os.close(fd)


def alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def idle(path):
    """Crash recovery also checks children that outlived their recorded owner."""
    tool = shutil.which('lsof', path='/usr/sbin:/usr/bin:/sbin:/bin')
    if tool is None:
        return False
    result = subprocess.run([tool, '-t', '+D', str(path)], capture_output=True, timeout=15)
    if result.stderr or result.returncode not in (0, 1):
        return False
    return all(pid == str(os.getpid()).encode() for pid in result.stdout.splitlines())


def remove(path, device):
    private(path, True)
    if path.stat().st_dev != device:
        raise ScratchError('Scratch volume changed; preserved')
    # Never traverse a mount inserted beneath the owned directory. Symlinks
    # inside it are removed as links, not followed by rmtree.
    for parent, directories, _ in os.walk(path, followlinks=False):
        for name in directories:
            entry = Path(parent) / name
            if not entry.is_symlink() and entry.stat().st_dev != device:
                raise ScratchError('Nested mount in scratch; preserved')
    shutil.rmtree(path)


def reap(root):
    """Called under the registry lock. Only marked, idle owned runs qualify."""
    count = 0
    for path in root.iterdir():
        if not re.fullmatch(r'(?:run-|t)[a-z0-9_]{8}', path.name):
            continue
        try:
            private(path, True)
            metadata = path / '.run.json'
            info = private(metadata)
            if info.st_size > 1024:
                continue
            value = json.loads(metadata.read_bytes())
            if (set(value) != {'kind', 'pid', 'device'} or value['kind'] != MARKER
                    or type(value['pid']) is not int or value['pid'] <= 0
                    or value['device'] != root.stat().st_dev or alive(value['pid'])):
                continue
            private(path / '.lease')
            with lock(path / '.lease', True):
                if not idle(path):
                    continue
                remove(path, value['device'])
                count += 1
        except (ScratchError, OSError, ValueError, TypeError, subprocess.TimeoutExpired):
            # Foreign/active/uncertain directories are not automatically removed.
            continue
    return count


@contextmanager
def directory(anchor, *, root=None, compact=False):
    """Return a private payload directory; remove only this run on all exits."""
    root = root_for(anchor, root)
    device, inode = root.stat().st_dev, root.stat().st_ino
    with lock(root / '.registry'):
        recovered = reap(root)
        if recovered:
            warnings.warn(f'Removed {recovered} abandoned owned scratch run(s)', stacklevel=2)
        run = Path(tempfile.mkdtemp(prefix='t' if compact else 'run-', dir=root))
        metadata = run / '.run.json'
        metadata.write_text(json.dumps(dict(kind=MARKER, pid=os.getpid(), device=device)))
        metadata.chmod(0o600)
        lease = os.open(run / '.lease', os.O_CREAT | os.O_EXCL | os.O_RDWR, 0o600)
        fcntl.flock(lease, fcntl.LOCK_EX)
        payload = run if compact else run / 'data'
        if not compact:
            payload.mkdir(mode=0o700)
    try:
        previous = None
        if (threading.current_thread() is threading.main_thread()
                and signal.getsignal(signal.SIGTERM) == signal.SIG_DFL):
            def cancel(signum, frame):
                raise KeyboardInterrupt
            previous = signal.signal(signal.SIGTERM, cancel)
        try:
            yield payload
        finally:
            if previous is not None:
                signal.signal(signal.SIGTERM, previous)
    finally:
        try:
            safe(root)
            if (root.stat().st_dev, root.stat().st_ino) != (device, inode):
                raise ScratchError('Scratch volume/directory changed; preserved')
            with lock(root / '.registry'):
                remove(run, device)
        finally:
            os.close(lease)
