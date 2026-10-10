# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Reviewed streamed adapter, using only the selected installed product owners."""

import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import time
import urllib.request
from uuid import UUID

DOMAIN = 'aws-stage.epmp-aos.projects.epam.com'
BASE = 'http://127.0.0.1:18080'
OPERATIONS = {'create', 'start-vms', 'provision', 'start-simulation', 'connect-test',
              'prepare', 'publish', 'service-prepare', 'service-publish', 'service-assign', 'backend-reset'}
QUERIES = {'installed', 'component', 'component-idle', 'service', 'backend', 'local', 'combined', 'platform', 'snapshot', 'publication'}
DOCKER = '/Applications/Docker.app/Contents/Resources/bin/docker'
PORTS = (18080,18600,2000,2001,2002,10022,10023)


def fixed_code(value):
    return value if isinstance(value, str) and re.fullmatch('[A-Z][A-Z0-9_]{1,100}', value) else None


def fixed_reason(value):
    # Source guest failures append the fixed role, not arbitrary diagnostics.
    # Preserve the reason while still excluding free text and secret suffixes.
    if isinstance(value, str):
        match = re.fullmatch(r'([A-Z][A-Z0-9_]{1,100}):(test|production)', value)
        if match:
            return match.group(1)
    return fixed_code(value)


def job_projection(job):
    """Bounded product fields only; exclude arbitrary progress/text/logs."""
    return dict(productState=fixed_code(job.get('state')), results=[
        dict(state=fixed_code(row.get('state')),
             code=fixed_reason(row.get('message')) or fixed_reason((row.get('facts') or {}).get('reason')))
        for row in job.get('results', [])[-12:]])


def component_idle_projection(value):
    section = value.get('components') or {}
    rows = section.get('value')
    current = (section.get('state') == 'CURRENT' and isinstance(rows, list)
               and all(isinstance(row, dict) for row in rows))
    return dict(idle=current and not any(row.get('pending_component') or
        row.get('pending_component_error') for row in rows), cloudCurrent=current)


def wait_for_exit(timeout=10):
    # ui.stop sends an ordinary signal; its return precedes actual socket exit.
    # A bounded read-only wait is not a repeated shutdown or forced termination.
    deadline = time.monotonic() + timeout
    while True:
        ports = []
        for port in PORTS:
            try:
                with socket.create_connection(('127.0.0.1',port),timeout=.3): ports.append(port)
            except ConnectionRefusedError: pass
        if not ports: break
        require(time.monotonic() < deadline, 'LISTENERS_REMAIN')
        time.sleep(.25)
    names = subprocess.run(['/bin/ps','-axo','comm='], capture_output=True, text=True,
                           check=True, timeout=5).stdout.splitlines()
    require(not any(any(key in name for key in ('CarlaUnreal-Mac-', 'carla-ego-service',
        'carla-viss-client', 'CARLA Keyboard', 'Demo Presenter', 'qemu-system-aarch64')) for name in names),
        'DEMO_PROCESSES_REMAIN')
    return dict(ownedDemoListeners=0, ownedDemoProcesses=0)


def validate_binding(state, expected):
    require(state.get('schemaVersion') == 1 and state.get('kind') == 'democtl.current-run', 'JOURNAL_INVALID')
    require(set(state['vehicles']) == {'test'}, 'EXACT_TEST_ONLY_REQUIRED')
    require(state['vehicles']['test']['localVmId'] == expected, 'TEST_IDENTITY_CHANGED')
    require(state.get('selectedCloudDomain') == DOMAIN, 'STAGING_REQUIRED')


def docker_info():
    require(Path(DOCKER).is_file(), 'DOCKER_APPLICATION_REQUIRED')
    endpoint = 'unix://' + str(Path.home()/'.docker/run/docker.sock')
    proc = subprocess.run([DOCKER, '--host', endpoint, 'info', '--format', '{{json .}}'],
                          capture_output=True, text=True, timeout=8)
    if proc.returncode:
        return None
    value = json.loads(proc.stdout)
    require(value['OSType'] == 'linux' and value['Architecture'] in ('aarch64','arm64')
            and 'Docker Desktop' in value['OperatingSystem'], 'DOCKER_ENGINE_WRONG_IDENTITY')
    return dict(engineId=value['ID'], runningContainers=value['ContainersRunning'])


def docker_backend_present():
    proc = subprocess.run(['/bin/ps','-axo','comm='],capture_output=True,text=True,check=True,timeout=5)
    return any(name.strip() == '/Applications/Docker.app/Contents/MacOS/com.docker.backend'
               for name in proc.stdout.splitlines())


def require(ok, code):
    if not ok:
        raise ValueError(code)


def result(facts=None, outcome='PASS', code='POSTCONDITION_OBSERVED'):
    return dict(outcome=outcome, code=code, facts=facts or {})


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise ValueError('REDIRECT_FORBIDDEN')


def exchange(path, payload=None):
    require(path in ('operations', 'snapshot', 'platform', 'backend/brake', 'backend/tire'), 'QUERY_NOT_ALLOWED')
    request = urllib.request.Request(BASE + '/api/presenter/' + path,
        data=None if payload is None else json.dumps(payload).encode(),
        headers={'Origin': BASE, 'Content-Type': 'application/json'})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    with opener.open(request, timeout=20) as response:
        require(response.status == (200 if payload is None else 202), 'HTTP_STATUS_INVALID')
        raw = response.read(2**20 + 1)
    require(len(raw) <= 2**20, 'HTTP_RESPONSE_TOO_LARGE')
    value = json.loads(raw)
    require(isinstance(value, dict), 'HTTP_RESPONSE_INVALID')
    return value


def backend_projection(value):
    require(value.get('state') == 'OBSERVED', 'BACKEND_NOT_OBSERVED')
    observations = value['observations']
    rows = []
    for resource in ('assessments', 'productData'):
        envelope = observations.get(resource, {})
        for item in (envelope.get('data') or {}).get('items', []):
            item = item.get('message', item)
            identifier = item.get('assessmentId') or item.get('eventId')
            if not identifier or not item.get('serviceVersion'):
                continue
            # Brake V1 is complete only when every chunk is durably received.
            if resource == 'productData' and item.get('terminalState') is not None:
                if not (item['terminalState'] == 'COMPLETE' and item.get('deliveryState') == 'DURABLY_RECEIVED'
                        and item.get('receivedChunkCount') == item.get('expectedChunkCount')):
                    continue
            row = dict(id=identifier, version=item['serviceVersion'])
            if resource == 'assessments':
                content = item.get('content') or {}
                row.update({key: content[key] for key in ('quality', 'currentBand') if key in content})
            rows.append(row)
    command = (observations.get('demoReset', {}).get('data') or {}).get('command') or {}
    advisory = []
    for item in (observations.get('advisories', {}).get('data') or {}).get('items', []):
        item = item.get('message', item)
        advisory.append(dict(version=item.get('serviceVersion'), state=item.get('gatewayState'),
                             assessmentId=item.get('assessmentId') or (item.get('content') or {}).get('decisionId')
                             or (item.get('content') or {}).get('assessmentId')))
    function_data = observations.get('functionObservations', {}).get('data') or {}
    functions = []
    for envelope in function_data.get('items', []):
        item = envelope.get('message') or {}
        content = item.get('content') or {}
        native = item.get('serviceInstance') or {}
        functions.append(dict(version=item.get('serviceVersion'), generation=item.get('generation'),
            instance={key:native.get(key) for key in ('serviceId','subjectId','instanceIndex','instanceId')},
            fresh=(function_data.get('truncated') is False and envelope.get('stale') is False
                and envelope.get('clockSkew') is False and envelope.get('deliveryState') == 'DURABLY_RECEIVED'
                and envelope.get('authority') == 'FUNCTION_TEAM_REPORTED_OBSERVATION'),
            connection=content.get('connection'),
            input=(content.get('input') or {}).get('state'), inputReason=(content.get('input') or {}).get('reason')))
    return dict(products=rows, productIds=sorted(set(r['id'] for r in rows)),
                resetId=command.get('commandId'), resetState=command.get('state'), advisories=advisory,
                functions=functions)


def service_projection(value, team):
    require(value.get('state') == 'CURRENT', 'PLATFORM_NOT_CURRENT')
    inventory = (value.get('value') or {}).get('inventory') or {}
    sid = inventory.get('teamServiceIds', {}).get(team)
    if sid is None:
        return dict(instances=[])
    rows = inventory.get('serviceDetails', {}).get(sid, {}).get('value') or []
    instances = []
    for row in rows:
        installed = (row.get('service_versions') or {}).get('installed_service_version') or {}
        for item in (row.get('instances') or {}).get('value') or []:
            instances.append(dict(version=item.get('version') if item.get('version') == installed.get('version') else None,
                run_state=item.get('run_state'), error_message=bool(item.get('error_message')),
                error_exit_code=item.get('error_exit_code')))
    return dict(instances=instances)


def control_projection(value):
    frame = value.get('frame') or {}
    return dict(fresh=value.get('fresh') is True, held=value.get('held') is True,
                mode=frame.get('activeMode'), speed=frame.get('speedKmh'), brake=frame.get('brake'))


# Fixed read-only guest projection. Never reads certificates, tokens, process
# environments or command arguments. No telemetry or model mutation/injection.
GUEST = r'''
import hashlib,json,os,subprocess
from pathlib import Path
out={'bootId':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'teams':{}}
for proc in Path('/proc').iterdir() if COLLECT_TEAMS else ():
 if not proc.name.isdigit():continue
 try:name=Path(os.readlink(proc/'exe')).name
 except OSError:continue
 teams=[t for t in ('brake','tire') if name==t+'-health-service']
 if not teams:continue
 team=teams[0];assert team not in out['teams']
 root=proc/'root/storage'/(team+'-health');assert root.is_dir()
 models=[];queued=[];assessments=[];count=0
 def project(data):
  if not isinstance(data,dict):return {}
  return {k:(project(v) if k in ('model','state') else v) for k,v in data.items()
   if k in ('model','state','generation','conditionBand','conditionScore','producerEpoch','assessmentId','lastAssessmentId','recentSourceEventIds','recentSourceExerciseIds')}
 for path in root.rglob('*.json'):
  count+=1;assert count<=2048
  parts=path.relative_to(root).parts
  if len(parts)>5 or path.is_symlink() or path.stat().st_size>1048576:continue
  if path.name=='state.json' and any('state' in p for p in parts):
   models.append(project(json.loads(path.read_text())))
  if 'outbox' in parts:
   data=json.loads(path.read_text())
   if isinstance(data,dict) and 'messageType' in data:
    key=data.get('assessmentId') or data.get('eventId') or data.get('requestId') or data.get('statusId')
    assert key is not None;queued.append(key)
    if data['messageType'] in ('BRAKE_HEALTH_ASSESSMENT','TIRE_HEALTH_ASSESSMENT'):assessments.append(data['assessmentId'])
 assert models and len(queued)<=512
 out['teams'][team]={'model':hashlib.sha256(json.dumps(models,sort_keys=True).encode()).hexdigest(),
  'queuedIds':sorted(queued),'queuedAssessmentIds':sorted(assessments)}
out['services']={}
for unit in ('aos-iam.service','aos-cm.service','aos-sm.service','aos-vehicle-data-provider.service'):
 p=subprocess.run(['systemctl','show',unit,'-p','ActiveState','-p','NRestarts','-p','Result'],capture_output=True,text=True,check=True)
 out['services'][unit]=dict(line.split('=',1) for line in p.stdout.splitlines() if '=' in line)
print(json.dumps(out))
'''


class Worker:
    def __init__(self, request):
        self.request = request
        self.config, self.args = request['config'], request['args']
        self.state, self.package = Path(self.config['instanceRoot']), Path(self.config['packageRoot'])
        self.pin = self.config['manifestSha256']
        self.app = None
        self.attempted = False
        require(request['phase'] in ('prepare', 'execute', 'observe', 'reconcile'), 'PHASE_INVALID')
        require(str(UUID(request['requestId'])) == request['requestId'], 'REQUEST_ID_INVALID')

    def imports(self):
        require(not any(p.is_symlink() for root in (self.state, self.package) for p in (root, *root.parents)), 'PATH_UNSAFE')
        require(hashlib.sha256((self.package/'application-manifest.json').read_bytes()).hexdigest() == self.pin,
                'CANDIDATE_CHANGED')
        sys.path.insert(0, str(self.package/'aosedge-sdv-demo/apps/demo-orchestrator/src'))
        from aosedge_demo_orchestrator import runtime_paths, installed_control
        state, identity = runtime_paths.instance(self.state)
        selected = installed_control.selection(state, identity)
        require(selected and selected['current'] == self.pin
            and Path(selected['storePath'])/'versions'/self.pin == self.package, 'SELECTION_CHANGED')
        return runtime_paths.installed_session(self.state)

    def binding(self, allow_empty=False):
        from aosedge_demo_orchestrator.application import DemoOrchestrator
        from aosedge_demo_orchestrator.environment import JOURNAL
        from aosedge_demo_orchestrator.status import read_json
        self.app = self.app or DemoOrchestrator()
        path = self.state / JOURNAL
        if not path.exists():
            require(allow_empty and self.request['expectedRun'] is None, 'TEST_JOURNAL_REQUIRED')
            return None
        state = read_json(path)
        validate_binding(state, self.request['expectedRun'])
        from aosedge_demo_orchestrator.status import load_configuration
        observed = load_configuration(self.state)  # ordinary product schema validation
        require(observed['vehicles']['test']['cloudHost'] == DOMAIN, 'STAGING_REQUIRED')
        return state

    def idle(self, allow_created=False):
        deadline, session = time.monotonic() + 35, None
        while True:
            snapshot, operations = exchange('snapshot'), exchange('operations')
            if not allow_created:
                require(snapshot.get('runId') == self.request['expectedRun'], 'PRESENTER_IDENTITY_CHANGED')
            require(operations['cloudDomain'] == DOMAIN, 'STAGING_REQUIRED')
            current = operations['sessionId']
            require(session in (None, current), 'SESSION_CHANGED_RECONCILE_REQUIRED')
            session = current
            require(not operations['uncertain'], 'OWNER_UNCERTAIN')
            require((operations.get('sourceRecovery') or {}).get('state') not in ('ATTEMPTED','FAILED'),
                    'SOURCE_RECOVERY_UNCONFIRMED')
            if (operations['active'] is None and not operations.get('sourceRecoveryBusy')
                    and not operations.get('workspaceBusy')):
                return operations
            # Layout and boot recovery have their own bounded work after the
            # foreground action completes. Observe them, never redispatch it.
            require(time.monotonic() < deadline, 'OWNER_BUSY')
            time.sleep(.5)

    def setup_call(self, action, **extra):
        resources = Path(self.config['setupApp'])/'Contents/Resources'
        process = subprocess.run([str(resources/'python/bin/python3.12'), '-I', '-B',
            str(resources/'tooling/scripts/distribution/setup_bridge.py')],
            input=json.dumps(dict(action=action, state=str(self.state), **extra)), capture_output=True, text=True,
            timeout=180, env=dict(HOME=str(Path.home()), PATH='/usr/bin:/bin:/usr/sbin:/sbin', LC_ALL='C'))
        require(len(process.stdout) <= 2**20, 'SETUP_RESPONSE_TOO_LARGE')
        rows = [json.loads(line) for line in process.stdout.splitlines()]
        if rows and rows[-1].get('kind') == 'error':
            code = rows[-1].get('code') or ''
            require(False, code if re.fullmatch('[A-Z][A-Z0-9_]{1,100}',code) else 'SETUP_OPERATION_NOT_CONFIRMED')
        require(rows and rows[-1].get('kind') == 'result' and process.returncode == 0, 'SETUP_OPERATION_NOT_CONFIRMED')
        return rows[-1]['result']

    def setup(self):
        action = self.args['action']
        require(set(self.args) == {'action'} and action in ('prepare-backends', 'cloud-pair', 'cloud-check', 'cloud-subjects', 'launch'), 'SETUP_ACTION_INVALID')
        app = Path(self.config['setupApp'])
        subprocess.run(['/usr/bin/codesign', '--verify', '--deep', '--strict', str(app)], check=True,
                       capture_output=True, timeout=30)
        require(hashlib.sha256((app/'Contents/MacOS/SDVLabSetup').read_bytes()).hexdigest() == self.config['setupSha256'], 'SETUP_CHANGED')
        resources = app/'Contents/Resources'
        require(json.loads((resources/'tooling/scripts/distribution/setup_release.json').read_bytes())['manifestSha256'] == self.pin, 'SETUP_PIN_MISMATCH')
        if action == 'launch':
            # An SSH child has different macOS TCC attribution from native
            # Setup. Never request sshd Accessibility or replay a GUI launch.
            if self.request['phase'] != 'reconcile':
                return result(outcome='BLOCKED', code='SETUP_NATIVE_GUI_REQUIRED')
            # Resolve a previous engineering launch only once its normal
            # cleanup has completed. shutdown/reconcile is strictly read-only;
            # stopped owners do not retroactively prove visual acceptance.
            stopped = self.shutdown()
            return result(stopped['facts'], outcome='FAIL',
                          code='SETUP_LAUNCH_STOPPED_WITHOUT_ACCEPTANCE')
        if self.request['phase'] == 'prepare':
            return result(dict(validated=True))
        if action == 'prepare-backends':
            # This owner inspects its durable attempt before any import on resume.
            self.attempted = True
            value = self.setup_call(action)
            require(value['status'] == 'BACKEND_IMAGES_AVAILABLE' and value['imagesVerified'] == 2, 'BACKEND_IMAGES_NOT_READY')
            return result({k:value[k] for k in ('status', 'imagesVerified', 'importAttempted')})
        pair = dict(oem=self.config['oemCertificate'], sp=self.config['spCertificate'])
        observed = self.setup_call('cloud-inspect', **pair)
        require(observed['domain'] == DOMAIN, 'STAGING_REQUIRED')
        pair['selectionToken'] = observed['selectionToken']  # memory only, never evidence
        if action == 'cloud-subjects':
            # Never choose by label/eligibility. The operator's exact public
            # references are part of this candidate's immutable test binding.
            requested = self.config.get('subjectReferences', [])
            available = self.setup_call('cloud-subjects-inspect', **pair)['subjects']
            require(len(available) == len(requested) and all(any(row.get('state') == 'ELIGIBLE'
                and row.get('reference') == ref for row in available) for ref in requested),
                'EXPLICIT_SUBJECT_SELECTION_REQUIRED')
            for ref in requested:
                self.attempted = True
                saved = self.setup_call('cloud-subjects-save', **pair, reference=ref)
                require(saved['status'] == 'CLOUD_SUBJECT_REFERENCE_SAVED', 'SUBJECT_SAVE_UNCONFIRMED')
                pair['selectionToken'] = saved['selectionToken']
            return result(dict(selectedTeams=sorted(ref['team'] for ref in requested), cloudMutation=False))
        if action == 'cloud-pair':
            if self.request['phase'] == 'reconcile':
                from aosedge_demo_orchestrator.cloud_connection import CloudConnection
                from aosedge_demo_orchestrator.environment import EnvironmentService
                current = CloudConnection(EnvironmentService(root=self.state))._configuration()
                profiles = current.get('cloudProfiles', {})
                require(all(profiles.get(role, {}).get('credential') == pair[key] for role, key in
                    (('oem-delivery','oem'), ('service-provider','sp'))), 'PAIR_SAVE_UNCONFIRMED')
                return result(dict(status='CLOUD_REFERENCES_SAVED'))
            self.attempted = True
            value = self.setup_call('cloud-save', **pair)
            require(value['status'] == 'CLOUD_REFERENCES_SAVED', 'PAIR_SAVE_UNCONFIRMED')
            return result(dict(status=value['status']))
        value = self.setup_call('cloud-check', **pair)
        require(value['rolesChecked'] and value['cloudStage'] == 'READY', 'CLOUD_PREREQUISITES_NOT_READY')
        return result(dict(status=value['status'], cloudStage=value['cloudStage'], rolesChecked=True))

    def installed(self):
        receipt = json.loads((Path(self.config['storeRoot'])/'receipts'/(self.pin+'.json')).read_bytes())
        require(receipt['manifestSha256'] == self.pin and receipt['status'] == 'INSTALLED_NOT_ACTIVATED', 'RECEIPT_INVALID')
        self.binding(allow_empty=True)
        return dict(manifestSha256=self.pin, selectionVerified=True, installationReceiptVerified=True,
                    runId=self.request['expectedRun'])

    def dependency(self):
        require(not self.args, 'DEPENDENCY_ARGUMENTS_FORBIDDEN')
        current = docker_info()
        if self.request['phase'] == 'prepare':
            return result(dict(wasRunning=current is not None))
        was_running = self.request['prepared']['wasRunning']
        # An unavailable API does not prove the backend is stopped. A starting,
        # sleeping or unhealthy backend is observed, never opened again.
        if current is None and self.request['phase'] == 'execute' and not docker_backend_present():
            self.attempted = True
            subprocess.run([DOCKER,'desktop','start','--detach'], check=True, capture_output=True, timeout=15)
        deadline = time.monotonic() + 90
        while current is None and time.monotonic() < deadline:
            time.sleep(2); current = docker_info()
        require(current is not None, 'DOCKER_START_OR_CONSENT_REQUIRED')
        return result(dict(current, startedByJourney=not was_running))

    def restore(self):
        """Fresh reads before fixed normal-owner startup; no deployments/resets."""
        owner = self.args.get('owner')
        require(set(self.args) == {'owner'} and owner in ('brake','tire','vm','source','connection'), 'RESTORE_OWNER_INVALID')
        self.binding(); self.idle()
        from aosedge_demo_orchestrator.models import OperationRequest, VehicleTarget
        from aosedge_demo_orchestrator.backends import BackendService
        def observed():
            if owner in ('brake','tire'):
                item = BackendService(self.app.environment_service).observe_stack()['teams'][owner]
                if item['state'] == 'RUNNING' and item.get('processHealth') == 'healthy': return True
                require(item['state'] == 'STOPPED', 'BACKEND_RESTORE_STATE_UNKNOWN')
            elif owner == 'vm':
                item = exchange('snapshot')['vehicles']['test']
                require(item['state'] == 'CURRENT' and item['process'] in ('RUNNING','STOPPED'), 'VM_RESTORE_STATE_UNKNOWN')
                return item['process'] == 'RUNNING'
            else:
                item = self.app.source_service.observe(guest=owner == 'connection')
                if owner == 'source':
                    if item['state'] in ('RUNNING_UNASSIGNED','SELECTED_NOT_PROBED'): return True
                    require(item['state'] == 'STOPPED', 'SOURCE_RESTORE_STATE_UNKNOWN')
                else:
                    if item['state'] == 'CONNECTED' and item.get('currentVehicle') == 'test': return True
                    require(item['state'] == 'DETACHED', 'CONNECTION_RESTORE_STATE_UNKNOWN')
            return False
        ready = observed()
        if self.request['phase'] == 'prepare': return result(dict(alreadyReady=ready))
        if not ready:
            require(self.request['phase'] != 'reconcile', 'RESTORE_OUTCOME_UNCONFIRMED')
            request = (OperationRequest('backend','start',team=owner) if owner in ('brake','tire') else
                OperationRequest('vm','start',target=VehicleTarget.TEST,timeout=90) if owner == 'vm' else
                OperationRequest('simulation','start',target=VehicleTarget.TEST) if owner == 'source' else
                OperationRequest('vehicle','select',target=VehicleTarget.TEST))
            self.attempted = True
            require(self.app.execute(request).state.value == 'COMPLETED', 'RESTORE_OUTCOME_UNCONFIRMED')
            require(observed(), 'RESTORE_POSTCONDITION_UNCONFIRMED')
        return result(dict(owner=owner, ready=True))

    def local(self, require_teams=True):
        from aosedge_demo_orchestrator.vm import access_path
        from aosedge_demo_orchestrator.guest_access import ssh_command
        state = self.binding()
        vehicle = state['vehicles']['test']
        process = subprocess.run(ssh_command(access_path(self.state, 'test'), vehicle['sshPort'], 5),
            input="python3 - <<'SDV_FIXED_READ'\nCOLLECT_TEAMS=" + repr(require_teams) + '\n' + GUEST + '\nSDV_FIXED_READ\n',
            capture_output=True, text=True, timeout=30)
        require(process.returncode == 0 and len(process.stdout) <= 262144, 'LOCAL_PROJECTION_UNAVAILABLE')
        value = json.loads(process.stdout)
        if require_teams: require(set(value['teams']) == {'brake','tire'}, 'SERVICE_PROJECTION_INCOMPLETE')
        value['controller'] = control_projection(self.app.source_service.driver.ready(state))
        value['identity'] = {key:vehicle.get(key) for key in ('localVmId', 'unitId', 'nodeId', 'systemUid')}
        return value

    def observe(self):
        query = self.args['query']
        require(query in QUERIES and set(self.args) <= {'query','team','release'}, 'OBSERVATION_NOT_ALLOWED')
        if query == 'installed': return self.installed()
        self.binding()
        if query == 'component-idle':
            return component_idle_projection(self.app.unit_service.observe('cloud-status', 'test'))
        if query == 'publication':
            require(set(self.args) == {'query','release'}, 'PUBLICATION_FIELDS_INVALID')
            from aosedge_demo_orchestrator.environment import EnvironmentError
            from aosedge_demo_orchestrator.service_packages import ServicePackages
            deadline = time.monotonic() + 20
            while True:
                self.idle()
                self.binding()
                try:
                    value = ServicePackages(self.app.environment_service).cloud_status(self.args['release'])
                    break
                except EnvironmentError as error:
                    # cloud_status raises this only before its read begins;
                    # an optional receipt-cache collision is handled by owner.
                    if str(error) != 'CURRENT_RUN_BUSY' or time.monotonic() >= deadline:
                        raise
                    time.sleep(.5)
            return {k:value.get(k) for k in ('stage','source','version','serviceId','deploymentId','versionId')}
        if query == 'local': return self.local(require_teams=False)
        if query == 'combined':
            return dict(local=self.local(), brake=backend_projection(exchange('backend/brake')),
                        tire=backend_projection(exchange('backend/tire')))
        if query == 'backend':
            require(self.args['team'] in ('brake','tire'), 'TEAM_INVALID')
            return backend_projection(exchange('backend/'+self.args['team']))
        if query == 'service':
            require(self.args['team'] in ('brake','tire'), 'TEAM_INVALID')
            return service_projection(exchange('platform'), self.args['team'])
        if query == 'platform':
            value = exchange('platform')
            require(value['state'] == 'CURRENT', 'PLATFORM_NOT_CURRENT')
            return dict(online=(value.get('value') or {}).get('online'))
        if query == 'snapshot':
            value = exchange('snapshot')
            require(value['runId'] == self.request['expectedRun'], 'TEST_IDENTITY_CHANGED')
            return dict(process=value['vehicles']['test'].get('process'))
        from aosedge_demo_orchestrator.models import OperationRequest, VehicleTarget
        from aosedge_demo_orchestrator.presenter_operations import public_result
        raw = self.app.execute(OperationRequest('component', 'status', target=VehicleTarget.TEST)).to_dict()
        return public_result(raw)['facts']

    def presenter_start(self):
        sys.path.insert(0, str(Path(self.config['setupApp'])/'Contents/Resources/tooling/scripts/distribution'))
        import setup_launch
        from aosedge_demo_orchestrator.host_runtime import selected
        self.binding(allow_empty=True)
        runtime = selected(self.state)
        require(runtime is not None, 'INSTALLED_RUNTIME_REQUIRED')
        runtime.verify('ui')
        command = [*runtime.cli(self.state), 'ui', 'serve']
        if self.request['phase'] == 'prepare': return result(dict(validated=True))
        if self.request['phase'] == 'reconcile':
            require(setup_launch.owner(command) is not None, 'PRESENTER_START_UNCONFIRMED')
        else:
            self.attempted = True
            setup_launch.ensure_server(command, self.state, lambda event: None)
        owner = setup_launch.owner(command)
        client = setup_launch.ready_client(command, owner)
        require(client['buildId'] == hashlib.sha256(runtime.entry('web').read_bytes()).hexdigest(), 'UI_BUILD_CHANGED')
        return result(dict(serverReady=True, nativeWindowsOpened=False))

    def vm_access(self):
        from aosedge_demo_orchestrator.qualification_access import prepare, preflight, input_password
        self.binding(allow_empty=True)
        if self.request['phase'] == 'prepare':
            if self.config.get('vmPasswordFile'):
                input_password(Path(self.config['vmPasswordFile']))
            else:
                preflight(self.app.environment_service, self.config['image'])
            return result(dict(validated=True))
        if self.request['phase'] == 'execute' and self.config.get('vmPasswordFile'):
            self.attempted = True
            prepare(self.app.environment_service, self.config['image'], Path(self.config['vmPasswordFile']))
        return result(preflight(self.app.environment_service, self.config['image']))

    def bind_created(self, job):
        identity = exchange('snapshot').get('runId')
        require(identity and str(UUID(identity)) == identity and job.get('runId') == identity,
                'CREATE_IDENTITY_UNCONFIRMED')
        require(self.request.get('expectedRun') in (None, identity), 'TEST_IDENTITY_CHANGED')
        self.request['expectedRun'] = identity
        state = self.binding()
        return identity, state

    def diagnostic(self):
        # One bounded observation before shutdown, even when enrollment failed.
        state = self.binding(allow_empty=True)
        value = dict(state='OBSERVED', expected='COMPLETED_OR_OBSERVED',
                     journalPresent=state is not None)
        if state:
            lifecycle = state.get('demoLifecycle') or {}
            vehicle = state['vehicles']['test']
            value.update(lifecycleState=fixed_code(lifecycle.get('state')),
                reason=fixed_code(lifecycle.get('reason')),
                provisioned=bool(vehicle.get('unitId')),
                vmState=fixed_code((vehicle.get('runtime') or {}).get('state')))
        try:
            operations = exchange('operations')
            value['activeOperation'] = operations.get('active') is not None
            rows = [row for row in operations.get('jobs', []) if row.get('id') == self.request['requestId']]
            if len(rows) == 1:
                value['job'] = job_projection(rows[0])
        except (OSError, ValueError, KeyError):
            value['presenterObservation'] = 'UNAVAILABLE'
        return result(value)

    def presenter(self):
        action = self.args['action']
        require(action in OPERATIONS, 'OPERATION_NOT_ALLOWED')
        from aosedge_demo_orchestrator.presenter_operations import operation_plan
        prepared = self.request['prepared']
        payload = dict(self.args, requestId=self.request['requestId'], sessionId=prepared.get('sessionId', 'preflight'))
        operation_plan(payload)  # Exact product field and action validation.
        if self.request['phase'] == 'prepare':
            self.binding(allow_empty=action == 'create')
            return result(dict(sessionId=self.idle()['sessionId']))
        # Create may already have changed the journal after a lost response.
        state = self.binding() if action != 'create' else None
        if self.request['phase'] == 'reconcile' and action == 'service-assign':
            # The assignment owner journals before any Cloud mutation. When
            # that record is absent, corroborate complete Unit inventory before
            # resolving non-submission after an expired Presenter session.
            operation = (state.get('serviceOperations') or {}).get(self.args['serviceId'])
            collision = operation and operation.get('reason') == 'SERVICE_SUBJECT_UNRECORDED_LABEL_COLLISION'
            if collision:
                from aosedge_demo_orchestrator.service_assignment import retirement_subjects
                require(retirement_subjects(state) == [], 'ASSIGNMENT_ABSENCE_UNCONFIRMED')
            if operation is None or collision:
                observed = self.app.unit_service.observe('cloud-status','test')['services']
                require(observed.get('state') == 'CURRENT' and observed.get('value') == []
                        and observed.get('coverage',{}).get('complete') is True,
                        'ASSIGNMENT_ABSENCE_UNCONFIRMED')
                return result(dict(assignmentNotSubmitted=True, cloudMutation=False), outcome='FAIL',
                              code='ASSIGNMENT_NOT_SUBMITTED')
        operations = exchange('operations')
        require(operations['sessionId'] == prepared['sessionId'], 'SESSION_CHANGED_RECONCILE_REQUIRED')
        if self.request['phase'] == 'execute':
            self.idle()
            self.attempted = True
            try: exchange('operations', payload)
            except OSError: pass  # Read the same request identity, never POST twice.
        deadline = time.monotonic() + 350
        while True:
            operations = exchange('operations')
            require(operations['sessionId'] == prepared['sessionId'], 'SESSION_CHANGED_RECONCILE_REQUIRED')
            jobs = [row for row in operations['jobs'] if row['id'] == self.request['requestId']]
            require(len(jobs) == 1, 'SUBMISSION_UNCONFIRMED')
            job = jobs[0]
            if operations['active'] != self.request['requestId']:
                if job['state'] not in ('COMPLETED','OBSERVED'):
                    rows = job.get('results',[])
                    facts = job_projection(job)
                    not_submitted = (action=='service-assign' and len(rows)==1
                        and rows[0].get('operation')=='service.runtime-prepare' and rows[0].get('state')=='BLOCKED')
                    partial_create = False
                    if action == 'create' and job.get('runId'):
                        identity, state = self.bind_created(job)
                        lifecycle = state.get('demoLifecycle') or {}
                        require(lifecycle.get('action') == 'create' and lifecycle.get('image') == self.config['image']
                                and not state['vehicles']['test'].get('unitId'), 'PARTIAL_CREATE_UNCONFIRMED')
                        partial_create = lifecycle.get('state') == 'PARTIAL' and job['state'] == 'PARTIAL'
                        if partial_create:
                            facts.update(runId=identity, partialRunBound=True,
                                         reason=fixed_code(lifecycle.get('reason')))
                    return result(dict(facts,assignmentNotSubmitted=not_submitted),
                        outcome='FAIL' if not_submitted or partial_create else 'UNCERTAIN',
                        code='PRODUCT_OPERATION_NOT_COMPLETED')
                facts = {key:job[key] for key in ('version','release','serviceId') if job.get(key)}
                for row in job.get('results', []):
                    if (row.get('facts') or {}).get('command'):
                        facts['commandId'] = row['facts']['command']['commandId']
                if action == 'create':
                    facts['runId'], _ = self.bind_created(job)
                return result(facts)
            require(time.monotonic() < deadline, 'OPERATION_DEADLINE_RECONCILE_REQUIRED')
            time.sleep(2)

    def control(self):
        action = self.args['action']
        require(action in ('exercise', 'return-to-road', 'connectivity-on', 'connectivity-off'), 'CONTROL_NOT_ALLOWED')
        require(set(self.args) == ({'action','team'} if action == 'exercise' else {'action'}), 'CONTROL_FIELDS_INVALID')
        if action == 'exercise': require(self.args['team'] in ('brake','tire'), 'TEAM_INVALID')
        state = self.binding()
        from aosedge_demo_orchestrator.models import OperationRequest, VehicleTarget
        domain = 'vehicle' if action.startswith('connectivity-') else 'simulation'
        if self.request['phase'] == 'prepare':
            self.idle()
            return result(dict(previousExercise=(state.get('source') or {}).get('exercise', {}).get('id')))
        if self.request['phase'] == 'reconcile':
            if domain == 'simulation':
                item = (state.get('source') or {}).get('exercise') or {}
                require(item.get('id') != self.request['prepared'].get('previousExercise')
                        and item.get('phase') == 'RELEASED' and item.get('result', {}).get('state') == 'COMPLETED', 'EXERCISE_UNCONFIRMED')
                return result(dict(operationId=item['id'], physicalStop=item['result']['physicalStop']))
            raw = self.app.execute(OperationRequest('vehicle', 'connectivity-status', target=VehicleTarget.TEST)).to_dict()
            require(raw.get('data', {}).get('state') == action.split('-')[-1].upper(), 'CONNECTIVITY_UNCONFIRMED')
            return result(dict(state=raw['data']['state']))
        self.idle()
        self.attempted = True
        raw = self.app.execute(OperationRequest(domain, action, target=VehicleTarget.TEST, team=self.args.get('team'))).to_dict()
        require(raw['state'] == 'COMPLETED', 'CONTROL_UNCONFIRMED')
        data = raw.get('data') or {}
        return result({k:data[k] for k in ('state','operationId','physicalStop','driveMode','autopilotStarted') if k in data})

    def mode(self):
        require(self.args == {'mode':'safe_stop'}, 'MODE_NOT_ALLOWED')
        state = self.binding()
        driver = self.app.source_service.driver
        if self.request['phase'] == 'prepare':
            self.idle(); driver.ready(state)
            return result(dict(validated=True))
        with self.app.environment_service._writer(), driver.operation(timeout=25):
            source = state['source']
            if self.request['phase'] != 'reconcile':
                self.attempted = True
                driver.rpc(source, 'safe_stop', self.request['requestId'])
            value = driver.rpc(source, 'status', self.request['requestId'])
            require(value.get('operationId') == self.request['requestId'], 'CONTROL_OPERATION_CHANGED')
            if value.get('phase') == 'STOPPING':
                value = driver.wait(source, self.request['requestId'], 'SAFE_STOP')
            require(value.get('phase') in ('SAFE_STOP','RELEASED'), 'SAFE_STOP_UNCONFIRMED')
            if value.get('held'):
                driver.rpc(source, 'release', self.request['requestId'])
            final = control_projection(driver.ready(state))
            require(final['fresh'] and not final['held'] and final['mode'] == 'SAFE_STOP'
                    and final['speed'] <= .5 and final['brake'] >= .99, 'SAFE_STOP_UNCONFIRMED')
            return result(dict(controller=final))

    def poweroff(self):
        from aosedge_demo_orchestrator.vm import access_path
        from aosedge_demo_orchestrator.guest_access import read_guest
        state = self.binding()
        if self.request['phase'] == 'reconcile':
            value = exchange('snapshot')
            require(value['runId'] == self.request['expectedRun'] and value['vehicles']['test']['process'] == 'STOPPED', 'POWEROFF_UNCONFIRMED')
            return result(dict(process='STOPPED'))
        self.idle()
        control = control_projection(self.app.source_service.driver.ready(state))
        require(control['fresh'] and not control['held'] and control['mode'] == 'SAFE_STOP'
            and control['speed'] <= .5 and control['brake'] >= .99, 'IGNITION_REQUIRES_PHYSICAL_STOP')
        if self.request['phase'] == 'prepare': return result(dict(safeStop=True))
        self.attempted = True
        read_guest(access_path(self.state,'test'), state['vehicles']['test']['sshPort'], 8, shutdown=True)
        return result(dict(poweroffRequested=True))

    def shutdown(self):
        from aosedge_demo_orchestrator import presenter
        from aosedge_demo_orchestrator.models import OperationRequest, VehicleTarget
        from aosedge_demo_orchestrator.backends import BackendService
        state = self.binding(allow_empty=True)
        from aosedge_demo_orchestrator.host_runtime import selected
        sys.path.insert(0, str(Path(self.config['setupApp'])/'Contents/Resources/tooling/scripts/distribution'))
        import setup_launch
        runtime = selected(self.state)
        command = [*runtime.cli(self.state), 'ui', 'serve']
        owner = setup_launch.owner(command)
        if owner: self.idle()
        if self.request['phase'] == 'prepare': return result(dict(ownedPresenter=owner is not None))
        if self.request['phase'] == 'reconcile':
            # The prior stop may have completed after its final read timed out.
            # Reconciliation only observes; never repeat lifecycle commands.
            require(owner is None, 'PRESENTER_STOP_UNCONFIRMED')
            exited = wait_for_exit()
            if state:
                teams = BackendService(self.app.environment_service).observe_stack()['teams']
                require(set(teams) == {'brake','tire'} and
                        all(row['state'] == 'STOPPED' for row in teams.values()), 'BACKEND_STOP_UNCONFIRMED')
            return result(dict(exited, persistentStatePreserved=True, finishExecuted=False,
                               dockerEnginePolicy='PRESERVED', reconciliationOnly=True))
        self.attempted = True
        if state:
            # Normal selected-source shutdown owns Safe Stop and detachment.
            if state.get('currentVehicle'):
                raw = self.app.execute(OperationRequest('vehicle','connectivity-status',target=VehicleTarget.TEST)).to_dict()
                require(raw.get('data',{}).get('state') in ('ON','OFF'), 'CONNECTIVITY_UNKNOWN_DURING_SHUTDOWN')
                if raw['data']['state'] == 'OFF':
                    raw = self.app.execute(OperationRequest('vehicle','connectivity-on',target=VehicleTarget.TEST)).to_dict()
                    require(raw['state'] == 'COMPLETED', 'NETWORK_RESTORE_UNCONFIRMED')
            for domain, action, target in (('simulation','stop',VehicleTarget.TEST), ('vm','stop',VehicleTarget.TEST)):
                raw = self.app.execute(OperationRequest(domain,action,target=target,timeout=60)).to_dict()
                require(raw['state'] == 'COMPLETED', 'OWNER_SHUTDOWN_UNCONFIRMED')
            require(BackendService(self.app.environment_service).stop_stack()['state'] == 'STOPPED', 'BACKEND_STOP_UNCONFIRMED')
        if owner:
            raw = self.app.execute(OperationRequest('workspace','close')).to_dict()
            require(raw['state'] == 'COMPLETED', 'WORKSPACE_CLOSE_UNCONFIRMED')
            require(presenter.stop() == 0, 'PRESENTER_STOP_UNCONFIRMED')
        exited = wait_for_exit()
        # Docker is shared background infrastructure, not a demo-owned process.
        # Never stop/restart/quit it, including when this journey started it.
        return result(dict(exited, persistentStatePreserved=True, finishExecuted=False,
                           dockerEnginePolicy='PRESERVED'))

    def execute(self):
        kind = self.request['kind']
        require(kind in ('dependency','setup','vm-access','diagnostic','presenter-start','presenter','control','mode','poweroff','shutdown','observe','hold','restore'), 'KIND_INVALID')
        with self.imports():
            if kind == 'setup': return self.setup()
            if kind in ('observe','hold'): return result(self.observe())
            return getattr(self, kind.replace('-','_'))()


def main(raw):
    worker = None
    try:
        worker = Worker(json.loads(raw))
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            answer = worker.execute()
    except Exception as error:
        code = str(error) if re.fullmatch('[A-Z][A-Z0-9_]{1,100}', str(error)) else 'WORKER_OBSERVATION_UNAVAILABLE'
        uncertain = worker is not None and (worker.attempted or worker.request['phase'] == 'reconcile')
        answer = result(outcome='UNCERTAIN' if uncertain else 'BLOCKED', code=code)
    print(json.dumps(answer), flush=True)
