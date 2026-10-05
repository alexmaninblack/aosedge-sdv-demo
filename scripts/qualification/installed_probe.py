# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Streamed test adapter. Uses installed owners, never installs product code."""

import contextlib
import hashlib
import io
import json
from pathlib import Path
import socket
import sys
import time
import urllib.request

ACTIONS = ('vm-start', 'vm-stop', 'brake-start', 'tire-start', 'backends-stop')


def require(ok, code):
    if not ok:
        raise ValueError(code)


def public_http(path):
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *args, **kwargs):
            raise ValueError('PRESENTER_REDIRECT_FORBIDDEN')
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    with opener.open('http://127.0.0.1:18080/api/presenter/' + path, timeout=5) as response:
        raw = response.read(1048577)
    require(len(raw) <= 1048576, 'PRESENTER_RESPONSE_TOO_LARGE')
    value = json.loads(raw)
    require(isinstance(value, dict), 'PRESENTER_RESPONSE_INVALID')
    return value


def presenter_idle(identity):
    # Refusal proves no listener; all other failures leave operation state unknown.
    try:
        with socket.create_connection(('127.0.0.1', 18080), timeout=2):
            pass
    except ConnectionRefusedError:
        return
    value = public_http('operations')
    require('active' in value and 'uncertain' in value
            and not value['active'] and not value['uncertain'], 'PRESENTER_OPERATION_UNRESOLVED')
    require(public_http('snapshot').get('runId') == identity, 'PRESENTER_IDENTITY_CHANGED')


def entry(request):
    started = time.monotonic()
    attempted = False
    facts = {}
    operation_seconds = 0.0
    stage = 'PACKAGE_BINDING'
    try:
        target = request['target']
        package, root = Path(target['packageRoot']), Path(target['instanceRoot'])
        require(hashlib.sha256((package / 'application-manifest.json').read_bytes()).hexdigest()
                == target['manifestSha256'], 'CANDIDATE_CHANGED')
        require(not any(p.is_symlink() for p in (package, *package.parents, root, *root.parents)),
                'TARGET_PATH_UNSAFE')
        sys.path.insert(0, str(package / 'aosedge-sdv-demo/apps/demo-orchestrator/src'))
        from aosedge_demo_orchestrator import runtime_paths
        from aosedge_demo_orchestrator.status import StatusService, load_configuration
        from aosedge_demo_orchestrator.environment import EnvironmentService
        from aosedge_demo_orchestrator.backends import BackendService
        from aosedge_demo_orchestrator.probes import qmp_status

        with runtime_paths.installed_session(root):
            stage = 'TEST_BINDING'
            def binding():
                config = load_configuration(root)
                require((config['journal'].get('value') or {}).get('runId') == target['localVmId'],
                        'TEST_IDENTITY_CHANGED')
                require(config['vehicles'].get('production') is None, 'PRODUCTION_PRESENT')
                require(config['vehicles']['test']['cloudHost'] == 'aws-stage.epmp-aos.projects.epam.com',
                        'STAGING_REQUIRED')
                return config

            binding()
            facts['installed'] = True
            kind, name = request['kind'], request['name']
            environment = EnvironmentService()
            if kind == 'action':
                require(name in ACTIONS, 'ACTION_NOT_ALLOWED')
                from aosedge_demo_orchestrator.application import DemoOrchestrator
                from aosedge_demo_orchestrator.models import OperationRequest, VehicleTarget
                # Same environment writer is reentrant in existing product owners.
                with environment._writer():
                    binding()
                    stage = 'OPERATION_INTERLOCK'
                    presenter_idle(target['localVmId'])
                    app = DemoOrchestrator(environment_service=environment)
                    action_start = time.monotonic()
                    attempted = True
                    stage = 'OWNER_OPERATION'
                    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                        if name == 'backends-stop':
                            result = BackendService(environment).stop_stack()
                            complete = result['state'] == 'STOPPED'
                        else:
                            domain, action = ('vm', name[3:]) if name.startswith('vm-') else ('backend', 'start')
                            args = dict(target=VehicleTarget.TEST, timeout=90) if domain == 'vm' else dict(team=name.split('-')[0])
                            result = app.execute(OperationRequest(domain, action, **args))
                            complete = result.state.value == 'COMPLETED'
                    operation_seconds = time.monotonic() - action_start
                    require(complete, 'OWNER_OPERATION_NOT_COMPLETED')
                binding()
            stage = 'CONTROLLER_OBSERVATION'
            if name != 'installed':
                snapshot = StatusService().collect(target='test', timeout=3)
                local = snapshot['vehicles']['test']['local']
                facts['controller'] = (local.get('value') or {}).get('processState') if local['state'] == 'CURRENT' else 'UNKNOWN'
                monitor = root / '.run/demo-current/test.qmp'
                facts['qmpRunning'] = None
                if monitor.exists() and not monitor.is_symlink():
                    try:
                        facts['qmpRunning'] = qmp_status(monitor, 2)['running']
                    except (OSError, ValueError):
                        pass
            if name in ('backends-running', 'backends-stopped', 'brake-running', 'tire-running',
                        'stopped', 'brake-start', 'tire-start', 'backends-stop'):
                stage = 'BACKEND_OBSERVATION'
                stack = BackendService(environment).observe_stack()
                for team in ('brake', 'tire'):
                    row = stack['teams'][team]
                    facts[team] = row['state']
                    facts[team + 'Healthy'] = row.get('processHealth') == 'healthy'
            if name == 'presenter-consistency':
                stage = 'PRESENTER_OBSERVATION'
                view = public_http('snapshot')
                require(view.get('runId') == target['localVmId'], 'PRESENTER_IDENTITY_CHANGED')
                row = view['vehicles']['test']
                facts['presenter'] = row.get('process') if row.get('state') == 'CURRENT' else 'UNKNOWN'
                presenter_idle(target['localVmId'])
        code = 'OBSERVED'
    except Exception:
        # Arbitrary exception details may contain paths, API responses or secrets.
        code = 'ACTION_UNCERTAIN' if attempted else 'INSTALLED_PROBE_BLOCKED'
    return dict(schemaVersion=1, code=code, stage=stage, actionAttempted=attempted, facts=facts,
                operationSeconds=round(operation_seconds, 3),
                observationSeconds=round(max(0, time.monotonic() - started - operation_seconds), 3))
