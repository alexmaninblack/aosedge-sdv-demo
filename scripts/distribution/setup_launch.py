# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Open the selected Presenter using existing Demo Control, never a new lifecycle."""

import json
import os
from pathlib import Path
import subprocess
import time
import urllib.error
import urllib.request
from uuid import uuid4

from installation_inputs import Bundle, require, unlinked
from aosedge_demo_orchestrator import runtime_paths, installed_control
from aosedge_demo_orchestrator.environment import EnvironmentService
from aosedge_demo_orchestrator.host_runtime import selected as selected_runtime

URL = 'http://127.0.0.1:18080'
OPERATIONS = '/api/presenter/operations'
MAX_REPLY = 2 * 2**20


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise ValueError('SETUP_LAUNCH_REDIRECT_FORBIDDEN')


def request(value):
    require(set(value) == {'action', 'state'} and value['action'] == 'launch', 'SETUP_REQUEST_INVALID')
    raw = value['state']
    require(isinstance(raw, str) and 1 < len(os.fsencode(raw)) <= 1024
            and raw.startswith('/') and not raw.startswith('//') and str(Path(raw)) == raw
            and not any(ord(c) < 32 or c == ',' for c in raw)
            and '..' not in Path(raw).parts, 'SETUP_PATH_INVALID')
    unlinked(raw)
    return value


def listener(port):
    result = subprocess.run(['/usr/sbin/lsof', '-t', '-nP', '-iTCP:' + str(port), '-sTCP:LISTEN'],
                            capture_output=True, text=True, timeout=3)
    require(not result.stderr and len(result.stdout) <= 4096, 'SETUP_LAUNCH_OWNER_UNAVAILABLE')
    rows = set(result.stdout.split())
    if result.returncode == 1 and not rows:
        return None
    require(result.returncode == 0 and len(rows) == 1 and all(x.isdigit() for x in rows),
            'SETUP_LAUNCH_PORT_CONFLICT')
    return int(rows.pop())


def owner(command):
    ports = [listener(port) for port in (18080, 18600)]
    if ports == [None, None]:
        return None
    require(ports[0] is not None and ports[0] == ports[1], 'SETUP_LAUNCH_PORT_CONFLICT')
    result = subprocess.run(['/bin/ps', '-p', str(ports[0]), '-o', 'uid=,command='],
                            capture_output=True, text=True, timeout=3)
    row = result.stdout.strip().split(None, 1)
    require(result.returncode == 0 and not result.stderr and len(row) == 2
            and row[0] == str(os.getuid()) and row[1] == ' '.join(command),
            'SETUP_LAUNCH_FOREIGN_OWNER')
    stamp = subprocess.run(['/bin/ps', '-p', str(ports[0]), '-o', 'lstart='],
                           capture_output=True, text=True, timeout=3)
    require(stamp.returncode == 0 and not stamp.stderr and 10 < len(stamp.stdout.strip()) < 80,
            'SETUP_LAUNCH_OWNER_UNAVAILABLE')
    return ports[0], stamp.stdout.strip()


def exchange(path, payload=None):
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    headers = {'Origin': URL, 'Content-Type': 'application/json'}
    request = urllib.request.Request(URL + path, headers=headers,
        data=None if payload is None else json.dumps(payload).encode())
    with opener.open(request, timeout=3) as response:
        require(response.status == (202 if payload is not None else 200), 'SETUP_LAUNCH_RESPONSE_INVALID')
        raw = response.read(MAX_REPLY + 1)
    require(len(raw) <= MAX_REPLY, 'SETUP_LAUNCH_RESPONSE_INVALID')
    value = json.loads(raw)
    require(isinstance(value, dict), 'SETUP_LAUNCH_RESPONSE_INVALID')
    return value


def idle(snapshot):
    require(isinstance(snapshot.get('sessionId'), str) and 1 <= len(snapshot['sessionId']) <= 100,
            'SETUP_LAUNCH_SESSION_INVALID')
    require('active' in snapshot and snapshot['active'] is None
            and all(snapshot.get(k) is False for k in ('uncertain', 'workspaceBusy', 'sourceRecoveryBusy'))
            and (snapshot.get('sourceRecovery') or {}).get('state') not in ('ATTEMPTED', 'FAILED'),
            'SETUP_LAUNCH_SESSION_BUSY')


def start(command, state):
    # No credentials, developer environment, shell, inherited stdin or pipe that
    # would keep the native setup helper alive. The child owns its runtime lease.
    return subprocess.Popen(command, cwd=state, stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True,
        env={'HOME': str(Path.home()), 'PATH': '/usr/bin:/bin:/usr/sbin:/sbin', 'LC_ALL': 'C'})


def ensure_server(command, state, emit):
    child = None
    # Hold the existing writer until socket ownership is established, so a
    # concurrent helper cannot race the first child's bind and start another.
    # Release it before HTTP readiness/restore; those may need this writer.
    with EnvironmentService(root=state)._writer():
        current = owner(command)
        if current is None:
            emit(dict(kind='progress', stage='LAUNCH_STARTING_PRESENTER'))
            child = start(command, state)
        deadline = time.monotonic() + 30
        while True:
            if child is not None:
                require(child.poll() is None, 'SETUP_LAUNCH_SERVER_EXITED')
                # A new server opens its two sockets consecutively. Do not adopt
                # either socket until both are proven to belong to this child.
                ports = [listener(port) for port in (18080, 18600)]
                require(all(pid in (None, child.pid) for pid in ports), 'SETUP_LAUNCH_PORT_CONFLICT')
                if ports == [child.pid, child.pid]:
                    current = owner(command)
            if current is not None:
                require(owner(command) == current, 'SETUP_LAUNCH_OWNER_CHANGED')
                return current, child is not None
            require(time.monotonic() < deadline, 'SETUP_LAUNCH_START_UNCONFIRMED')
            time.sleep(.2)


def ready_client(command, expected):
    deadline = time.monotonic() + 20
    while True:
        require(owner(command) == expected, 'SETUP_LAUNCH_OWNER_CHANGED')
        try:
            return exchange('/api/presenter/client-state')
        except urllib.error.HTTPError as error:
            require(error.code == 503, 'SETUP_LAUNCH_RESPONSE_INVALID')
        except OSError:
            pass  # Bounded read-only readiness; no start or operation replay.
        require(time.monotonic() < deadline, 'SETUP_LAUNCH_START_UNCONFIRMED')
        time.sleep(.2)


def restore(command, expected, emit):
    snapshot = exchange(OPERATIONS)
    idle(snapshot)
    require(owner(command) == expected, 'SETUP_LAUNCH_OWNER_CHANGED')
    identity = str(uuid4())
    payload = dict(action='workspace-restore', requestId=identity, sessionId=snapshot['sessionId'])
    emit(dict(kind='progress', stage='LAUNCH_OPENING_WINDOWS'))
    try:
        exchange(OPERATIONS, payload)
    except (OSError, ValueError):
        # Lost/rejected submission is reconciled by this identity, never replayed.
        pass
    deadline = time.monotonic() + 45
    while True:
        require(owner(command) == expected, 'SETUP_LAUNCH_OWNER_CHANGED')
        state = exchange(OPERATIONS)
        require(state.get('sessionId') == payload['sessionId'], 'SETUP_LAUNCH_SESSION_CHANGED')
        jobs = state.get('jobs')
        require(isinstance(jobs, list) and len(jobs) <= 128, 'SETUP_LAUNCH_RESPONSE_INVALID')
        matches = [job for job in jobs if isinstance(job, dict) and job.get('id') == identity]
        require(len(matches) <= 1, 'SETUP_LAUNCH_RESPONSE_INVALID')
        if matches:
            job = matches[0]
            require(job.get('action') == 'workspace-restore', 'SETUP_LAUNCH_RESPONSE_INVALID')
            if job.get('state') not in ('ACCEPTED', 'RUNNING'):
                require(job.get('state') in ('COMPLETED', 'PARTIAL'), 'SETUP_LAUNCH_LAYOUT_UNCONFIRMED')
                return payload['sessionId']
        else:
            # Submit itself is synchronous: no identity after its response was
            # lost means no acceptance can be established, not permission to retry.
            raise ValueError('SETUP_LAUNCH_SUBMISSION_UNCONFIRMED')
        require(time.monotonic() < deadline, 'SETUP_LAUNCH_LAYOUT_UNCONFIRMED')
        time.sleep(.3)


def observe(service, command, expected, session):
    from aosedge_demo_orchestrator.environment import EnvironmentError
    # The accepted restore may still own bounded layout recovery after its job
    # completes. Wait only for observation; never replay restore or a lifecycle.
    deadline = time.monotonic() + 20
    last = None
    while True:
        require(owner(command) == expected, 'SETUP_LAUNCH_OWNER_CHANGED')
        snapshot = exchange(OPERATIONS)
        require(snapshot.get('sessionId') == session, 'SETUP_LAUNCH_SESSION_CHANGED')
        busy = snapshot.get('workspaceBusy')
        require(type(busy) is bool, 'SETUP_LAUNCH_SESSION_BUSY')
        idle(snapshot | {'workspaceBusy': False})
        if not busy:
            try:
                last = service.execute('status')
                if surface_result(last)['presenterObserved']:
                    return last
            except EnvironmentError as error:
                if str(error) != 'CURRENT_RUN_BUSY':
                    raise
        if time.monotonic() >= deadline:
            require(last is not None, 'SETUP_LAUNCH_LAYOUT_UNCONFIRMED')
            return last
        time.sleep(.2)


def surface_result(value):
    surfaces = value.get('surfaces') or {}
    valid = (value.get('zOrder') or {}).get('state') == 'VERIFIED'
    for name in ('header', 'browser', 'backdrop'):
        row = surfaces.get(name) or {}
        actual, expected = row.get('actual'), row.get('expected')
        valid = valid and type(row.get('pid')) is int and row['pid'] > 0 and row['pid'] == value.get('hostPid')
        valid = valid and isinstance(actual, list) and isinstance(expected, list) and len(actual) == len(expected) == 4
        valid = valid and all(type(a) is int and type(b) is int and abs(a - b) <= 3 for a, b in zip(actual, expected))
    return dict(status='PRESENTER_OPENED' if valid else 'PRESENTER_NEEDS_ATTENTION',
                presenterObserved=bool(valid),
                layoutComplete=bool(valid and value.get('state') == 'PLACED_AWAITING_VISUAL_REVIEW'))


def perform(value, pin, emit=lambda event: None):
    emit(dict(kind='progress', stage='LAUNCH_VERIFYING_SELECTION'))
    state, identity = runtime_paths.instance(value['state'])
    selection = installed_control.selection(state, identity)
    require(selection and selection['current'] == pin, 'SETUP_LOCAL_PREPARATION_REQUIRED')
    program = Path(selection['storePath']) / 'versions' / pin / 'aosedge-sdv-demo'
    emit(dict(kind='progress', stage='LAUNCH_PACKAGE_ACCESS'))
    with runtime_paths.installed_session(state, _program=program):
        emit(dict(kind='progress', stage='LAUNCH_VERIFYING_PROGRAM'))
        bundle = Bundle(program.parent, pin)
        for name in bundle.rows:
            if name.startswith('aosedge-sdv-demo/'):
                bundle.verify_file(name)
        runtime = selected_runtime(state)
        require(runtime is not None, 'SETUP_LAUNCH_RUNTIME_REQUIRED')
        runtime.verify('ui')
        command = [*runtime.cli(state), 'ui', 'serve']
        expected, started = ensure_server(command, state, emit)
        client = ready_client(command, expected)
        from hashlib import sha256
        require(client.get('buildId') == sha256(runtime.entry('web').read_bytes()).hexdigest(),
                'SETUP_LAUNCH_UI_MISMATCH')
        session = restore(command, expected, emit)
        from aosedge_demo_orchestrator.application import DemoOrchestrator
        from aosedge_demo_orchestrator.workspace import WorkspaceService
        app = DemoOrchestrator()
        workspace = WorkspaceService(app.environment_service, app.source_service.driver)
        observation = observe(workspace, command, expected, session)
        require(owner(command) == expected, 'SETUP_LAUNCH_OWNER_CHANGED')
        return dict(surface_result(observation), runtimeChanged=True, cloudAccessed=False,
                    demoReady=False, serverStarted=started)
