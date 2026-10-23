#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""One unattended native-controls campaign; normal owners, M1 only, no replay."""
import argparse
import contextlib
import hashlib
import io
import inspect
import json
import os
from pathlib import Path
import re
import shlex
import stat
import subprocess
import time
from types import SimpleNamespace
from uuid import UUID, uuid4

import campaign
import journey as j
import remote_harness as h
import ui_pilot

HERE = Path(__file__).resolve().parent
FIELDS = {'schemaVersion', 'scenario', 'mode', 'config', 'journey', 'nativeBuild',
          'nativeRunId', 'dmg', 'remoteDmg', 'mediaRecords', 'records', 'workspace',
          'test', 'versions'}
PATHS = {'config', 'journey', 'nativeBuild', 'dmg', 'mediaRecords', 'records', 'workspace'}
STAGES = ('preflight', 'prepare-baseline', 'native-ui', 'cleanup')


def source_pin():
    return hashlib.sha256(b''.join((HERE/name).read_bytes() for name in
        ('native_controls_campaign.py','journey.py','journey_plan.py','journey_worker.py',
         'remote_harness.py','campaign.py','ui_pilot.py','ui_m1.py','native_ui_live.py',
         'ui_native_gate.py','ui_journey.mjs','ui_pilot.mjs','ui_read_broker.mjs','ui_read_transport.py'))).hexdigest()


def code(error):
    value = str(error)
    return value if re.fullmatch(r'[A-Z][A-Z0-9_]{1,100}', value) else 'CAMPAIGN_OPERATION_UNAVAILABLE'


def configuration(path, scenario='native-controls'):
    path = h.unlinked(path)
    info = path.stat()
    h.require(info.st_uid == os.getuid() and stat.S_IMODE(info.st_mode) == 0o600
              and info.st_size < 16384, 'PRIVATE_CAMPAIGN_PLAN_REQUIRED')
    value = h.parse(path.read_bytes())
    h.require(isinstance(value, dict) and set(value) == FIELDS
              and type(value['schemaVersion']) is int and value['schemaVersion'] == 1
              and scenario in ('native-controls','continuous-campaign') and value['scenario'] == scenario
              and value['mode'] in ('fresh', 'retained'), 'CAMPAIGN_PLAN_INVALID')
    for key in PATHS:
        raw = value[key]
        h.require(isinstance(raw, str) and raw.startswith('/') and str(Path(raw)) == raw
                  and '..' not in Path(raw).parts and not any(ord(c) < 32 for c in raw),
                  'CAMPAIGN_PATH_INVALID')
        h.unlinked(Path(raw))
    h.require('/.local/remote-qualification/' in value['records']
              and not Path(value['records']).exists(), 'NEW_PRIVATE_CAMPAIGN_REQUIRED')
    h.require(Path(value['workspace']).is_dir(), 'SCRATCH_WORKSPACE_REQUIRED')
    h.require(isinstance(value['nativeRunId'], str)
              and re.fullmatch(r'native-ui-live-\d{8}(?:-[a-z0-9]+)?', value['nativeRunId']),
              'NATIVE_RUN_ID_INVALID')
    if value['mode'] == 'retained':
        h.require(isinstance(value['test'], str) and str(UUID(value['test'])) == value['test'],
                  'RETAINED_TEST_REQUIRED')
    else:
        h.require(value['test'] is None, 'FRESH_TEST_MUST_BE_UNBOUND')
    versions = value['versions']
    h.require(isinstance(versions, dict) and set(versions) == {'vdp', 'brake', 'tire'}
              and all(isinstance(v, str) and re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+', v)
                      for v in versions.values()), 'EXACT_BASELINE_VERSIONS_REQUIRED')
    return value


def local_inputs(plan, transport, config):
    """Small manifests/tool gates only. Do not hash/rebuild a large DMG here."""
    media = campaign.media_input(Path(plan['dmg']), config, plan['remoteDmg'], transport['user'])
    h.require(ui_pilot.verified_media(Path(plan['mediaRecords']), media) is not None,
              'VERIFIED_MEDIA_REQUIRED')
    build = Path(plan['nativeBuild'])
    receipt = h.parse((build/'build-receipt.json').read_bytes())
    from native_ui_live import BUNDLE, SIGNER
    apps = [v for v in receipt.get('apps', []) if v.get('bundleId') == BUNDLE]
    h.require(receipt.get('signatureIdentity') == SIGNER and len(apps) == 1,
              'NATIVE_RUNNER_BUILD_INVALID')
    row = apps[0]
    h.require(row.get('app') == 'Native UI Runner.app' and row.get('executable') == 'NativeUIRunner'
              and h.digest(build/row['app']/'Contents/MacOS'/row['executable']) == row.get('sha256'),
              'NATIVE_RUNNER_BUILD_CHANGED')
    sources = [v for k,v in receipt.get('inputs',{}).items() if k.endswith('/native/NativeUIRunner.swift')]
    h.require(sources == [h.digest(HERE/'native/NativeUIRunner.swift')], 'NATIVE_RUNNER_SOURCE_CHANGED')
    h.require((HERE.parent.parent/'apps/presenter-ui/node_modules/@playwright/test').is_dir(),
              'EXISTING_DEVELOPMENT_BROWSER_TOOLS_REQUIRED')
    return media


def inspect_preflight_pair(connection, oem, sp, retained):
    """Read through the existing fresh/same-OEM owner guards; never select/save."""
    if not retained:
        return connection.inspect_pair(oem, sp)
    before = connection._pair_stamp(oem, sp, connect=True)
    first, second = connection.inspect(oem), connection.inspect(sp)
    if first['domain'] != second['domain']:
        raise ValueError('CLOUD_OEM_SP_DOMAIN_MISMATCH')
    if before != connection._pair_stamp(oem, sp, connect=True):
        raise ValueError('CLOUD_CERTIFICATE_CHANGED_SINCE_PREVIEW')
    return dict(domain=first['domain'], rolesChecked=False)


def preflight(transport, config, expected, native_run_id, versions=None):
    """Single bounded M1 read: installed selection, stopped owners, desktop and Cloud."""
    request = dict(config=config, kind='observe', args={}, phase='observe',
                   requestId=str(uuid4()), expectedRun=expected)
    program = j.WORKER.read_text() + '\n'+inspect.getsource(inspect_preflight_pair)+'\nREQUEST=' + repr(request) + '\nNATIVE_RUN_ID='+repr(native_run_id)+'\nVERSIONS='+repr(versions)+'''
answer=None;facts={}
try:
 with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
  worker=Worker(REQUEST)
  with worker.imports():
   state=worker.binding(allow_empty=True)
   require((state is not None)==(REQUEST['expectedRun'] is not None),'CAMPAIGN_BASELINE_MODE_CONFLICT')
   require(subprocess.check_output(['/usr/bin/uname','-m'],text=True).strip()=='arm64','M1_ARM64_REQUIRED')
   require(Path('/dev/console').stat().st_uid==os.getuid(),'TARGET_CONSOLE_CHANGED')
   require(not (Path.home()/'SDV-Qualification'/NATIVE_RUN_ID).exists(),'NATIVE_CAMPAIGN_REPLAY_FORBIDDEN')
   owners=wait_for_exit(timeout=1)
   engine=docker_info();require(engine is not None,'DOCKER_ENGINE_UNAVAILABLE')
   require(engine['runningContainers']==0,'IDLE_SHARED_DOCKER_REQUIRED')
   facts=dict(candidate=worker.pin,test=REQUEST['expectedRun'],**owners,
    dockerEngineId=engine['engineId'],cloudMutation=False,normalOwnersStarted=False)
   from aosedge_demo_orchestrator.host_runtime import selected
   runtime=selected(worker.state)
   screen=subprocess.run([str(runtime.entry('presenter')),'screen'],capture_output=True,text=True,timeout=5)
   desktop=json.loads(screen.stdout).get('desktopState') if screen.returncode==0 else 'UNKNOWN'
   desktop=desktop if desktop in ('UNLOCKED','LOCKED','UNKNOWN') else 'UNKNOWN'
   facts['desktopState']=desktop
   local_checks=[dict(key='desktop',state='READY' if desktop=='UNLOCKED' else 'BLOCKED',
    code=None if desktop=='UNLOCKED' else 'TARGET_DESKTOP_NOT_UNLOCKED')]
   from aosedge_demo_orchestrator.cloud_connection import CloudConnection
   from aosedge_demo_orchestrator.cloud_setup import CloudSetup
   from aosedge_demo_orchestrator.environment import EnvironmentService
   from aosedge_demo_orchestrator.units import UnitService
   from aosedge_demo_orchestrator.vm import VMService
   environment=EnvironmentService(root=worker.state)
   # A Cloud version alone cannot authorize assignment. Require the normal
   # same-owner local publication proof before creating any vehicle.
   if VERSIONS is not None:
    from aosedge_demo_orchestrator.service_assignment import ServiceAssignment
    assignment=ServiceAssignment(environment,worker.app.unit_service)
    publications=[]
    for reference in worker.config.get('subjectReferences',[]):
     row=assignment._publication(reference['serviceId'])
     require(row['team']==reference['team'] and row['serviceProviderId']==reference['serviceProviderId']
       and row['publishedVersion']==VERSIONS[reference['team']],'BASELINE_PUBLICATION_BINDING_CHANGED')
     publications.append(dict(team=row['team'],version=row['publishedVersion']))
    require({r['team'] for r in publications}=={'brake','tire'},'BASELINE_PUBLICATION_RECEIPTS_REQUIRED')
    facts['publicationReceipts']=publications
   from aosedge_demo_orchestrator.qualification_access import input_password,preflight as vm_access_check
   if worker.config.get('vmPasswordFile'):input_password(Path(worker.config['vmPasswordFile']))
   else:vm_access_check(environment,worker.config['image'])
   candidate=environment.catalog.resolve(worker.config['image'])
   require(not candidate.problems,'DEMO_FACTORY_IMAGE_UNAVAILABLE')
   from aosedge_demo_orchestrator.backends import BackendService
   backends=BackendService(environment)
   if state is not None:
    retained_backend_images(state,backends)
   else:
    for team in ('brake','tire'):backends._image(backends._candidate(team)['imageId'])
   connection=CloudConnection(environment)
   pair=inspect_preflight_pair(connection,worker.config['oemCertificate'],worker.config['spCertificate'],state is not None)
   require(pair['domain']==worker.domain,'QUALIFICATION_CLOUD_CHANGED')
   saved=connection._configuration().get('cloudProfiles',{})
   require(all(saved.get(role,{}).get('credential')==worker.config[key] for role,key in
    [('oem-delivery','oemCertificate'),('service-provider','spCertificate')]),'SETUP_SAVE_PAIR_FIRST')
   report=CloudSetup(UnitService(VMService(environment=environment))).check(first_use=True)
   checks=local_checks+[dict(key=r['key'],state=r['state'],code=fixed_code(r.get('detail'))) for r in report['checks']]
   require(report['domain']==worker.domain,'QUALIFICATION_CLOUD_CHANGED')
   if worker.owners is not None:
    require(report['owners']==worker.owners,'QUALIFICATION_CLOUD_OWNERS_CHANGED')
   blockers=[r for r in checks if r['state'] in ('BLOCKED','CONFLICT','MISSING')]
   facts.update(cloudStage=report['stage'],checks=checks)
   answer=result(facts) if report['stage']=='READY' and not blockers else result(facts,outcome='BLOCKED',
    code=next((r['code'] for r in blockers if r['code']),'CLOUD_PREREQUISITES_NOT_READY'))
except Exception as error:
 answer=result(facts,outcome='BLOCKED',code=fixed_code(str(error)) or 'PREFLIGHT_OBSERVATION_UNAVAILABLE')
print(json.dumps(answer),flush=True)
'''
    python = config['packageRoot'] + '/demo-artifacts/aosedge-sdv-demo/host-runtime/python/bin/python3.12'
    with j.Progress('campaign-preflight', emit=print):
        return h.parse(h.remote(transport, shlex.quote(python) +
            " -I -B - <<'SDV_CAMPAIGN_PREFLIGHT'\n" + program + '\nSDV_CAMPAIGN_PREFLIGHT\n', timeout=70))


def preparation_steps(plan, config):
    """Fixed normal API preparation; never publication, retirement or native acceptance."""
    steps = [dict(id='vm-access', kind='vm-access', timeout=30)]
    if plan['mode'] == 'retained':
        return steps
    steps += [dict(id='subjects',kind='setup',args=dict(action='cloud-subjects'),timeout=150),
              dict(id='presenter',kind='presenter-start',timeout=90)]
    for label,action in [('create','create'),('start','start-vms'),('simulator','start-simulation'),
                         ('provision','provision')]:
        args = dict(action=action)
        if action == 'create': args['image'] = config['image']
        steps.append(dict(id=label,kind='presenter',args=args,timeout=360))
    steps.append(dict(id='safe-stop',kind='mode',args=dict(mode='safe_stop'),timeout=30))
    steps.append(dict(id='update-idle',kind='observe',args=dict(query='component-idle'),timeout=180,
                      until=dict(test='equals',actual='$sample.idle',expected=True)))
    steps.append(dict(id='connect',kind='presenter',args=dict(action='connect-test'),timeout=360))
    steps.append(dict(id='vdp-ready',kind='observe',args=dict(query='component'),timeout=180,
                      until=dict(test='ready-vdp',actual='$sample',version=plan['versions']['vdp'])))
    for team in ('brake','tire'):
        refs = [r for r in config.get('subjectReferences', []) if r['team'] == team]
        h.require(len(refs) == 1, 'EXACT_SUBJECT_REFERENCE_REQUIRED')
        steps.append(dict(id=team+'-assign',kind='presenter',timeout=360,
                          args=dict(action='service-assign',serviceId=refs[0]['serviceId'])))
        steps.append(dict(id=team+'-ready',kind='observe',timeout=180,args=dict(query='service',team=team),
                          until=dict(test='ready-service',actual='$sample',version=plan['versions'][team])))
    return steps


class Operations:
    def __init__(self, plan, transport, config, root):
        self.plan, self.transport, self.config, self.root = plan, transport, config, root
        self.media = None
        self.mount_owned = self.bootstrap = False
        self.test = plan['test']
        self.runner = None
        self.ui_report = None
        self.permission_root = None
        self.permission_request = None
        self.source = source_pin()

    def permission_close(self):
        if self.permission_root is None: return
        python = self.config['packageRoot']+'/demo-artifacts/aosedge-sdv-demo/host-runtime/python/bin/python3.12'
        value = dict(schemaVersion=1,requestId=self.permission_request,operation='quit',pid=12345,
                     executableSha256='0'*64)
        program = 'ROOT='+repr(self.permission_root)+'\nVALUE='+repr(value)+'''
import json,os,pathlib,stat,subprocess,time
root=pathlib.Path(ROOT);path=root/'requests'/(VALUE['requestId']+'.json')
if root.exists():
 for p in (root,root/'requests'):
  info=p.lstat();assert stat.S_ISDIR(info.st_mode) and info.st_uid==os.getuid() and stat.S_IMODE(info.st_mode)==0o700
 marker=root/'probe-owner.json';info=marker.lstat()
 assert stat.S_ISREG(info.st_mode) and info.st_uid==os.getuid() and stat.S_IMODE(info.st_mode)==0o600
 assert json.loads(marker.read_bytes())==dict(quitRequestId=VALUE['requestId'],inputAllowed=False),'PERMISSION_PROBE_OWNER_CHANGED'
def alive():
 names=subprocess.run(['/bin/ps','-axo','comm='],capture_output=True,text=True,check=True).stdout.splitlines()
 return any(n.startswith(str(root)+'/Native UI Runner.app/') for n in names)
if alive() and not path.exists():
 fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 os.write(fd,json.dumps(VALUE).encode());os.fsync(fd);os.close(fd)
deadline=time.monotonic()+8
while alive() and time.monotonic()<deadline:time.sleep(.05)
assert not alive(),'PERMISSION_CLIENT_CLOSE_UNCONFIRMED'
print(json.dumps(dict(permissionClientClosed=True,inputDispatched=False)))
'''
        h.parse(h.remote(self.transport,shlex.quote(python)+" -I -B - <<'SDV_PERMISSION_CLOSE'\n"+
                        program+'\nSDV_PERMISSION_CLOSE\n',timeout=15))
        self.permission_root=None

    def permission_probe(self):
        """Same signed client reports its own grant; no fixture/target/input."""
        from native_ui_live import BUNDLE,SIGNER
        receipt=h.parse((Path(self.plan['nativeBuild'])/'build-receipt.json').read_bytes())
        row=next(r for r in receipt['apps'] if r['bundleId']==BUNDLE)
        date=self.plan['nativeRunId'].split('-')[3]
        name='native-ui-pilot-'+date+'-p'+hashlib.sha256(str(self.root).encode()).hexdigest()[:10]
        self.permission_root='/Users/'+self.transport['user']+'/SDV-Qualification/'+name
        self.permission_request=str(uuid4())
        h.atomic(self.root/'permission-probe.intent.json',dict(quitRequestId=self.permission_request,
            bundleId=BUNDLE,executableSha256=row['sha256'],inputAllowed=False))
        python=self.config['packageRoot']+'/demo-artifacts/aosedge-sdv-demo/host-runtime/python/bin/python3.12'
        marker=json.dumps(dict(quitRequestId=self.permission_request,inputAllowed=False)).encode()
        create='import os,pathlib; os.umask(0o077); p=pathlib.Path('+repr(self.permission_root)+'); '+\
            'assert not p.exists(),"PERMISSION_PROBE_REPLAY_REFUSED"; p.mkdir(mode=0o700); (p/"requests").mkdir(mode=0o700); '+\
            'fd=os.open(p/"probe-owner.json",os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600); '+\
            'os.write(fd,'+repr(marker)+'); os.fsync(fd); os.close(fd)'
        h.remote(self.transport,shlex.quote(python)+' -I -B -c '+shlex.quote(create),timeout=10)
        shell=shlex.join(h.ssh_args(self.transport)[:-1])
        subprocess.run(['/usr/bin/rsync','-rpt','-e',shell,str(Path(self.plan['nativeBuild'])/'Native UI Runner.app'),
            self.transport['user']+'@'+self.transport['host']+':'+shlex.quote(self.permission_root+'/')],
            check=True,capture_output=True,timeout=30)
        requirement='-R=anchor apple generic and certificate leaf = H"'+SIGNER+'" and identifier "'+BUNDLE+'"'
        program='ROOT='+repr(self.permission_root)+'\nDIGEST='+repr(row['sha256'])+'\nREQUIREMENT='+repr(requirement)+'''
import hashlib,json,pathlib,subprocess,time
root=pathlib.Path(ROOT);app=root/'Native UI Runner.app'
subprocess.run(['/usr/bin/codesign','--verify','--deep','--strict',REQUIREMENT,str(app)],check=True,capture_output=True,timeout=10)
assert hashlib.sha256((app/'Contents/MacOS/NativeUIRunner').read_bytes()).hexdigest()==DIGEST,'PERMISSION_CLIENT_CHANGED'
names=subprocess.run(['/bin/ps','-axo','comm='],capture_output=True,text=True,check=True).stdout.splitlines()
assert not any(n.endswith('/Native UI Runner.app/Contents/MacOS/NativeUIRunner') for n in names),'NATIVE_CLIENT_ALREADY_ACTIVE'
subprocess.run(['/usr/bin/open','-a',str(app),'--args',str(root)],check=True,capture_output=True,timeout=10)
status=root/'runner-status.json';deadline=time.monotonic()+8
while not status.exists() and time.monotonic()<deadline:time.sleep(.05)
assert status.exists(),'PERMISSION_PROBE_UNCONFIRMED'
value=json.loads(status.read_bytes());assert value.get('bundleId')=='org.aosedge.sdv.qualification.native-ui-runner'
assert value.get('status') in ('READY','ACCESSIBILITY_PERMISSION_REQUIRED')
print(json.dumps(dict(nativePermission=value['status'],inputDispatched=False,fixtureStarted=False)))
'''
        try:
            value=h.parse(h.remote(self.transport,shlex.quote(python)+" -I -B - <<'SDV_PERMISSION_PROBE'\n"+
                                  program+'\nSDV_PERMISSION_PROBE\n',timeout=35))
            h.require(value['nativePermission']=='READY','ACCESSIBILITY_PERMISSION_REQUIRED')
            return value
        finally:self.permission_close()

    def preflight(self):
        h.require(source_pin()==self.source,'CAMPAIGN_SOURCE_CHANGED')
        media = local_inputs(self.plan, self.transport, self.config)
        self.media = campaign.Media(self.transport, self.config, media)
        result = preflight(self.transport, self.config, self.test, self.plan['nativeRunId'], self.plan['versions'])
        self.initial = result['facts']
        if result['outcome']=='PASS':result['facts'].update(self.permission_probe())
        return result

    def prepare(self):
        h.require(source_pin()==self.source,'CAMPAIGN_SOURCE_CHANGED')
        self.mount_owned = not self.media.attached()
        self.media.mount()
        baseline = self.root/'baseline'
        config = dict(self.config,records=str(baseline))
        with h.Journal(baseline,j.identity(config,self.transport)) as journal:
            self.runner = j.Runner(journal,j.Remote(self.transport,config),emit=print)
            try:
                for step in preparation_steps(self.plan,config):
                    context = dict(runId=self.test) if self.test else j.context_from(h.read_attempts(baseline))
                    if step['id'] == 'presenter': self.bootstrap = True
                    row = self.runner.run_step(step,context)
                    self.test = j.context_from(h.read_attempts(baseline)).get('runId',self.test)
                    if row['outcome'] != 'PASS':
                        return dict(outcome=row['outcome'],code=row['code'],facts=dict(step=step['id'],test=self.test))
                return dict(outcome='PASS',code='BASELINE_PREPARED',facts=dict(test=self.test,
                    publication='NOT_REQUESTED',nativeAcceptance='NOT_RUN'))
            finally:
                # This profile deliberately qualifies cold UI startup. API
                # preparation is not a substitute for those actual UI clicks.
                if self.bootstrap:
                    self._stop_baseline(self.runner,baseline)

    def stop_baseline(self):
        # Reopen the same baseline lease if a failed close escaped preparation.
        # An existing uncertain close is reconciled, never dispatched again.
        root = self.root/'baseline'
        config = dict(self.config,records=str(root))
        with h.Journal(root,j.identity(config,self.transport)) as journal:
            runner = j.Runner(journal,j.Remote(self.transport,config),emit=print)
            return self._stop_baseline(runner,root)

    def _stop_baseline(self,runner,root):
        step = dict(id='baseline-close',kind='shutdown',timeout=120)
        rows = h.read_attempts(root)
        previous = j.rows_by_step(rows).get(step['id'])
        context = dict(runId=self.test) if self.test else j.context_from(rows)
        if previous and previous['outcome']=='PASS':
            self.bootstrap=False
            return
        h.require(previous is None or previous['outcome']=='UNCERTAIN','BASELINE_CLOSE_NEEDS_DIAGNOSIS')
        row = runner.run_step(step,context,previous=previous)
        if row['outcome'] == 'UNCERTAIN':
            row = runner.run_step(step,context,previous=row)
        h.require(row['outcome'] == 'PASS', 'BASELINE_CLOSE_UNCONFIRMED')
        self.bootstrap = False

    def ui(self):
        h.require(source_pin()==self.source,'CAMPAIGN_SOURCE_CHANGED')
        h.require(self.test is not None, 'PREPARED_TEST_REQUIRED')
        args = SimpleNamespace(scenario='native-controls',display='m1',test=self.test,
            cards_from_release_records=None,continue_from=None,node=None,
            config=Path(self.plan['config']),journey=Path(self.plan['journey']),
            records=self.root/'ui',workspace=Path(self.plan['workspace']),dmg=Path(self.plan['dmg']),
            remote_dmg=self.plan['remoteDmg'],media_records=Path(self.plan['mediaRecords']),
            native_build=Path(self.plan['nativeBuild']),native_run_id=self.plan['nativeRunId'],
            native_versions=self.plan['versions'])
        status = ui_pilot.run(args,self.transport,self.config)
        self.ui_report = h.parse((args.records/'pilot-report.json').read_bytes())
        passed = status == 0 and self.ui_report.get('nativeControls') == 'PASS'
        return dict(outcome='PASS' if passed else 'FAIL',code='NATIVE_CONTROLS_PASSED' if passed
                    else 'NATIVE_CONTROLS_NOT_QUALIFIED',facts=dict(nativeControls=self.ui_report.get('nativeControls'),
                    ownersClosed=self.ui_report.get('ownersClosed'),test=self.test))

    def cleanup(self):
        self.permission_close()
        if self.bootstrap: self.stop_baseline()
        # Historical startup belongs to phase receipts. Cleanup preserves the
        # campaign's prepared Test, not a wrapper's separately retired old Test.
        facts = dict(sharedDocker='PRESERVED',currentPreparedTestPreserved=self.test is not None)
        if self.test and self.runner:
            result = j.Remote(self.transport,self.config)(dict(id='campaign-close-observe',kind='shutdown',timeout=35),
                'reconcile',dict(runId=self.test),str(uuid4()))
            h.require(result['outcome'] == 'PASS','CAMPAIGN_CLOSE_UNCONFIRMED')
            facts.update(result['facts'])
            if self.ui_report:
                h.require(self.ui_report.get('ownersClosed') is True
                    and self.ui_report.get('nativeRunnerClosed') is True,'UI_OWNERS_CLOSE_UNCONFIRMED')
        if self.mount_owned:
            self.media.remote('/usr/bin/hdiutil detach '+shlex.quote(str(Path(self.config['setupApp']).parent))+' >/dev/null')
            h.require(not self.media.attached(),'OWNED_MEDIA_DETACH_UNCONFIRMED')
        facts['ownedMediaDetached'] = True
        return dict(outcome='PASS',code='CAMPAIGN_OWNERS_CLOSED',facts=facts)


def execute(operations, root, clock=time.monotonic):
    """One entry executes all fixed phases. Failure never calls a later mutation."""
    started = clock()
    stages = []
    outcome, failure = 'PASS', None
    input_stage = False
    def stage(label, fn):
        began = clock()
        h.atomic(root/(label+'.intent.json'),dict(stage=label,startedAt=h.utc()))
        print(json.dumps(dict(stage=label,state='STARTED')),flush=True)
        try:
            answer = fn()
            h.require(isinstance(answer,dict) and set(answer) == {'outcome','code','facts'}
                      and answer['outcome'] in ('PASS','BLOCKED','FAIL','UNCERTAIN')
                      and isinstance(answer['facts'],dict) and isinstance(answer['code'],str)
                      and re.fullmatch(r'[A-Z][A-Z0-9_]{1,100}',answer['code']),
                      'CAMPAIGN_STAGE_RESPONSE_INVALID')
        except KeyboardInterrupt:
            answer=dict(outcome='UNCERTAIN',code='CAMPAIGN_INTERRUPTED',facts={})
        except Exception as error:
            answer = dict(outcome='FAIL' if label=='cleanup' else 'UNCERTAIN' if label in
                          ('prepare-baseline','native-ui') else 'BLOCKED',code=code(error),facts={})
        row = dict(stage=label,seconds=round(clock()-began,3),**answer)
        stages.append(row)
        h.atomic(root/(label+'.result.json'),row)
        print(json.dumps(dict(stage=label,outcome=row['outcome'],seconds=row['seconds'],code=row['code'])),flush=True)
        return row
    try:
        for label,fn in [('preflight',operations.preflight),('prepare-baseline',operations.prepare),('native-ui',operations.ui)]:
            input_stage |= label=='native-ui'
            row = stage(label,fn)
            if row['outcome'] != 'PASS':
                outcome,failure = row['outcome'],row['code']
                break
    except KeyboardInterrupt:
        outcome,failure='UNCERTAIN','CAMPAIGN_INTERRUPTED'
    finally:
        closed = stage('cleanup',operations.cleanup)
        if closed['outcome'] != 'PASS': outcome,failure = 'FAIL',closed['code']
        by_stage = {row['stage']:row for row in stages}
        report = dict(scenario='native-controls',outcome=outcome,code=failure or 'CAMPAIGN_PASSED',
            seconds=round(clock()-started,3),candidate=operations.config['manifestSha256'],test=operations.test,
            nativeControls='PASS' if outcome=='PASS' else 'NOT_QUALIFIED',fullE2E='NOT_COMPLETE',
            stages=[by_stage.get(s,dict(stage=s,outcome='NOT_RUN',seconds=None)) for s in STAGES],
            nativeStageStarted=input_stage,cleanupConfirmed=closed['outcome']=='PASS',
            previousTestPolicy='PRESERVE',newReleasePublication=False,agentStepScheduling=False)
        h.atomic(root/'campaign-report.json',report)
        lines=[f"Native controls: {outcome}",f"Reason: {report['code']}",f"Elapsed: {report['seconds']:.3f} s"]
        lines += [f"{r['stage']}: {r['outcome']}" +
                  (f" ({r['seconds']:.3f} s)" if r['seconds'] is not None else '') for r in report['stages']]
        # Small human summary contains no arbitrary diagnostics or credentials.
        with (root/'summary.txt').open('x') as stream:stream.write('\n'.join(lines)+'\n')
        print('\n'.join(lines),flush=True)
    return 0 if outcome=='PASS' else 2 if outcome=='BLOCKED' else 1


def main():
    os.umask(0o077)
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan',type=Path,required=True)
    args=parser.parse_args()
    plan=configuration(args.plan)
    transport,_=h.configuration(Path(plan['config']))
    config=j.configuration(Path(plan['journey']),transport['user'])
    root=Path(plan['records'])
    source=source_pin()
    pin=hashlib.sha256(json.dumps(dict(plan=plan,source=source,
        connection=j.identity(config,transport)),sort_keys=True).encode()).hexdigest()
    with h.Journal(root,pin):
        h.atomic(root/'campaign.intent.json',dict(scenario='native-controls',candidate=config['manifestSha256'],
            startedAt=h.utc(),sourceSha256=source,planSha256=h.digest(args.plan)))
        return execute(Operations(plan,transport,config,root),root)


if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as error:
        print(json.dumps(dict(outcome='BLOCKED',code=code(error),agentStepScheduling=False)),flush=True)
        raise SystemExit(2)
