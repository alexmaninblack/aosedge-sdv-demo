# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Bounded read-only capacity process; never initializes or locks build state."""
import json
import os
from pathlib import Path
import selectors
import signal
import subprocess
import sys
import time

from .core import ROOT, LabError, Release, Storage, read_json, require
from .space import report

DEADLINE = 45
LIMIT = 4*2**20
FIELDS = ('storage', 'manifest', 'profile', 'target', 'build_plan', 'cache_from', 'docker')
STAGES = {'metadata', 'cache', 'plan', 'docker', 'capacity-pools', 'producer-policy',
          *('inventory-'+name for name in ('sources','cache','inputs','builds','.tmp','tmp'))}


def inspect_request(request, progress):
    require(isinstance(request, dict) and set(request) == set(FIELDS)
            and all(v is None or isinstance(v, str) for v in request.values()),
            'Invalid capacity request')
    progress('SPACE_STAGE', 'metadata')
    require(request['storage'] is not None, 'Specify explicit capacity storage')
    path = Path(request['storage'])
    profile = request['profile']
    if profile is None and (path/'preparation.json').exists():
        profile = read_json(path/'preparation.json')['binding']['profile']
    storage = Storage(path, Release(Path(request['manifest']) if request['manifest'] else None),
                      profile or 'developer')
    state = storage.state() if storage.state_path.exists() else {
        'binding':storage.binding, 'sources':{}, 'artifacts':{}, 'builds':{}}
    require(storage.state_path.exists() or not storage.root.exists() or not any(storage.root.iterdir()),
            'Refusing an unowned nonempty workspace')
    return report(storage, state, request['target'],
                  Path(request['build_plan']) if request['build_plan'] else None,
                  Path(request['cache_from']) if request['cache_from'] else None,
                  Path(request['docker']) if request['docker'] else None, progress=progress)


def stop(process):
    for sig in (signal.SIGTERM, signal.SIGKILL):
        exited = process.poll() is not None  # Reap a Darwin zombie before killpg.
        try:
            os.killpg(process.pid, sig)
        except ProcessLookupError:
            pass
        except PermissionError:
            require(exited, 'Cannot stop the capacity reader; no completed result')
        try:
            process.wait(timeout=7 if sig == signal.SIGTERM else 3)
            # A reader may exit while one of its ordinary children still owns
            # the pipe. This process group contains only this read-only probe.
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            except PermissionError:
                require(process.poll() is not None, 'Cannot stop the capacity reader; no completed result')
            return
        except subprocess.TimeoutExpired:
            continue
    raise LabError('Capacity reader did not exit; no completed result')


def probe(args, progress, *, deadline=DEADLINE, worker=None):
    request = {key: str(getattr(args, key)) if getattr(args, key) is not None else None for key in FIELDS}
    raw = json.dumps(request).encode()
    require(len(raw) < 8192, 'Capacity request is too large')
    env = {k:v for k,v in os.environ.items() if k in ('PATH', 'LC_ALL', 'LANG', 'TERM')}
    env.update(PYTHONDONTWRITEBYTECODE='1', GIT_TERMINAL_PROMPT='0', GIT_NO_LAZY_FETCH='1')
    process = subprocess.Popen([sys.executable, '-I', '-B', str(worker or ROOT/'scripts/reproduction/space_worker.py')],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        start_new_session=True, env=env, cwd=ROOT)
    started = time.monotonic()
    last, buffer, count, result, error = 'metadata', b'', 0, None, None
    selector = selectors.DefaultSelector()
    try:
        process.stdin.write(raw); process.stdin.close()
        selector.register(process.stdout, selectors.EVENT_READ)
        while selector.get_map():
            remaining = deadline-(time.monotonic()-started)
            require(remaining > 0, 'Capacity check deadline exceeded at '+last+'; no completed capacity result')
            for key, _ in selector.select(min(remaining, .2)):
                chunk = os.read(key.fd, 65536)
                if not chunk:
                    selector.unregister(key.fileobj)
                    continue
                count += len(chunk); buffer += chunk
                require(count <= LIMIT, 'Capacity reader output exceeded its limit')
                while b'\n' in buffer:
                    line, buffer = buffer.split(b'\n', 1)
                    try:
                        value = json.loads(line)
                    except (ValueError, UnicodeError):
                        raise LabError('Invalid capacity reader response') from None
                    require(isinstance(value, dict), 'Invalid capacity reader response')
                    if set(value) == {'event', 'detail'} and value['event'] == 'SPACE_STAGE':
                        require(isinstance(value['detail'], str) and value['detail'] in STAGES
                                and result is None and error is None,
                                'Invalid capacity stage')
                        last = value['detail']; progress('SPACE_STAGE', last)
                    elif set(value) == {'result'} and result is None and error is None:
                        result = value['result']
                    elif set(value) == {'error'} and error is None and result is None:
                        require(isinstance(value['error'], str) and len(value['error']) <= 2000,
                                'Invalid capacity failure')
                        error = value['error']
                    else:
                        raise LabError('Invalid capacity reader response')
        require(not buffer, 'Incomplete capacity reader response')
        remaining = deadline-(time.monotonic()-started)
        require(remaining > 0, 'Capacity check deadline exceeded at '+last+'; no completed capacity result')
        try:
            code = process.wait(timeout=remaining)
        except subprocess.TimeoutExpired:
            raise LabError('Capacity check deadline exceeded at '+last+'; no completed capacity result') from None
        if error is not None:
            raise LabError(error)
        require(code == 0 and isinstance(result, dict) and result.get('status') == 'SPACE_REPORT'
                and type(result.get('fitsCheckedPools')) is bool
                and type(result.get('storagePreflightComplete')) is bool,
                'Capacity reader did not complete successfully')
        result['inspectionSeconds'] = round(time.monotonic()-started, 3)
        return result
    finally:
        selector.close()
        try:
            stop(process)
        finally:
            process.stdout.close()
            if not process.stdin.closed:
                process.stdin.close()
