#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""One fixed production first-use scenario: empty Setup, new keys, real UI, closure.

Only the already-qualified Test is retired. Prior installation/certificates are
parked by same-filesystem rename, never copied into the new setup. Issuance is
at-most-once; tokens pass from RAM over pinned SSH stdin to a 0600 FIFO and
native secure fields. No token appears in argv, environment, clipboard or logs.
"""
import argparse
import contextlib
import io
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time
from uuid import uuid4

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(HERE), str(ROOT / 'apps/demo-orchestrator/src')]
import journey as j
import remote_harness as h

TEST = '79adbc10-3f37-40f7-8642-b03968791734'
UNIT = 'e0f42f9e-bb33-4b39-aa58-c461b4d1e693'
PRESERVED = 'd87ba9cb-b21f-45db-8773-553e52d0353e'
REMOTE = '/Users/alexagizim/SDV-Qualification/native-first-use-production-20261015'
DMG = '/Users/alexagizim/SDV-Qualification/production-clock-20261015/AosEdge-SDV-Lab-Production-Clock-20261015.dmg'
SIGNER = '0514708CB8DA6BB8C26823D4F01C9F6869908008'


class Campaign:
    def __init__(self, build, records, reconcile=False, installed=False, media=None):
        os.umask(0o077)
        self.t, _ = h.configuration(ROOT / '.local/remote-qualification/m1-20261001.json')
        self.c = j.configuration(ROOT / '.local/remote-qualification/m1-production-clock-full-20261015/journey.json', self.t['user'])
        self.build, self.records = build, records
        if installed:
            prior=h.parse((records/'report.json').read_bytes())
            h.require(prior['outcome']=='FAIL' and prior['code'] in ('PRODUCTION_SELECTION_UNCONFIRMED','UI_WAIT_CONNECTEDTOPRODUCTION','SETUP_ENROLLMENT_ENVIRONMENT_INVALID')
                and any(r['stage']=='retire-and-park' and r['status']=='PASS' for r in prior['stages']),
                'INSTALLED_CONTINUATION_REFUSED')
            names={'PRODUCTION_SELECTION_UNCONFIRMED':'before-environment-selection-correction.json',
                   'UI_WAIT_CONNECTEDTOPRODUCTION':'before-native-error-diagnostics.json',
                   'SETUP_ENROLLMENT_ENVIRONMENT_INVALID':'before-setup-domain-fix.json'}
            h.atomic(records/names[prior['code']],prior)
        elif reconcile:
            prior=h.parse((records/'report.json').read_bytes())
            h.require(prior['outcome']=='FAIL' and prior['code']=='REMOTE_COMMAND_FAILED'
                and not (records/'native-launch.intent.json').exists(), 'FIRST_USE_CONTINUATION_REFUSED')
            h.atomic(records/'before-sharing-reconciliation.json',prior)
        else:
            h.require(not records.exists(), 'FIRST_USE_REPLAY_REQUIRES_RECONCILIATION')
            records.mkdir(mode=0o700)
        self.reconcile=reconcile
        self.installed=installed
        self.stages = []
        self.started = time.monotonic()
        self.parked = False
        self.mounted = False
        self.media=media
        self.remote_dmg=DMG
        if media:
            receipt=h.parse((media/'Setup/build-receipt.json').read_bytes())
            h.require(receipt['manifestSha256']==self.c['manifestSha256'],'RUNTIME_PRODUCT_CHANGED')
            self.c=dict(self.c,setupApp='/Volumes/SDV-First-Use-20261015/AosEdge SDV Lab Setup.app',
                sourceRoot='/Volumes/SDV-First-Use-20261015/Runtime Kit',setupSha256=receipt['binarySha256'])
            self.remote_dmg=REMOTE+'/AosEdge-SDV-Lab-1.2.0-rc.2.dmg'

    def remote(self, code, timeout=40):
        return h.remote(self.t, "/usr/bin/python3 -I -B - <<'FIRST_USE_SCENARIO'\n" + code + '\nFIRST_USE_SCENARIO\n', timeout=timeout)

    def stage(self, name, action):
        print(json.dumps(dict(stage=name, status='RUNNING')), flush=True)
        start = time.monotonic()
        h.atomic(self.records / (name + '.intent.json'), dict(startedAt=h.utc(), replayAllowed=False))
        result = action()
        row = dict(stage=name, status='PASS', seconds=round(time.monotonic()-start, 3), facts=result)
        self.stages.append(row)
        h.atomic(self.records / (name + '.result.json'), row)
        print(json.dumps(row), flush=True)
        return result

    def worker(self, body, *, fresh=False, timeout=150):
        request = dict(config=self.c, kind='observe', args={}, phase='execute', requestId=str(uuid4()),
                       expectedRun=None if fresh else TEST)
        program = j.WORKER.read_text() + '\nREQUEST=' + repr(request) + '\n' + body
        python = self.c['packageRoot'] + '/demo-artifacts/aosedge-sdv-demo/host-runtime/python/bin/python3.12'
        return h.parse(h.remote(self.t, shlex.quote(python) + " -I -B - <<'FIRST_USE_OWNER'\n" + program + '\nFIRST_USE_OWNER\n', timeout=timeout))

    def prepare(self):
        p = h.probe(self.t, cloud_domain='aoscloud.io')
        h.require(p['demoProcesses'] == 0 and p['busyPorts'] == 0, 'FIRST_USE_OWNERS_NOT_CLOSED')
        if self.installed:
            facts=self.worker('''
with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
 w=Worker(REQUEST)
 with w.imports():
  require(w.binding(allow_empty=True) is None,'UNEXPECTED_TEST_CREATED')
  for key in ('oemCertificate','spCertificate'):
   path=Path(w.config[key])
   require(not path.exists() and not (path.parent/'attempt.json').exists(),'ISSUANCE_ALREADY_STARTED')
print(json.dumps(dict(installedUnenrolled=True,retiredTest='''+repr(TEST)+''',retirementReplayed=False)))
''',fresh=True)
            self.parked=True
            for role in ('oem','sp'):
                intent=self.records/('token-'+role+'.intent.json')
                if intent.exists():
                    suffix='before-setup-domain-fix' if self.media else 'before-native-error-diagnostics'
                    destination=intent.with_name('token-'+role+'.'+suffix+'.intent.json')
                    h.require(not destination.exists(),'TOKEN_INTENT_ALREADY_ARCHIVED')
                    intent.rename(destination)
            return facts
        # Exact retired run, quiescent state and Cloud identity are checked by
        # the normal owner before its one retirement submission.
        if self.reconcile:
            from aosedge_demo_orchestrator.unit_cloud import Cloud
            with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
                cloud=Cloud(dict(credential='/Users/alexagizim/.aos/security prod/aos-user-oem.p12',cloudDomain='aoscloud.io'))
                h.require(cloud.user['ownerId']==self.c['cloudOwners']['oem'] and cloud.unit(UNIT,nodes=False) is None
                    and cloud.unit(PRESERVED,nodes=False) is not None,'RETIREMENT_RECONCILIATION_FAILED')
            self.remote('''
import pathlib,subprocess,time,json
assert not pathlib.Path('/Users/alexagizim/SDV-Lab-Data/.run/demo-current/journal.json').exists(),'RETIREMENT_JOURNAL_REMAINS'
docker='/Applications/Docker.app/Contents/Resources/bin/docker'
args=[docker,'--host','unix:///Users/alexagizim/.docker/run/docker.sock']
assert not subprocess.check_output(args+['ps','-q'],text=True).strip(),'RUNNING_CONTAINERS_BLOCK_MAINTENANCE'
subprocess.run([docker,'desktop','restart'],check=True,capture_output=True,timeout=120)
end=time.monotonic()+60
while time.monotonic()<end:
 p=subprocess.run(args+['info','--format','{{json .ID}}'],capture_output=True,text=True)
 if p.returncode==0:break
 time.sleep(1)
assert p.returncode==0,'DOCKER_MAINTENANCE_UNCONFIRMED'
''',timeout=200)
            facts=dict(retiredTest=TEST,retiredUnit=UNIT,reconciliationOnly=True,staleDockerSharingRestartedOnce=True)
        else:
            facts = self.worker('''
answer=None
with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
 w=Worker(REQUEST)
 with w.imports():
  state=w.binding()
  require(state['vehicles']['test']['unitId']==''' + repr(UNIT) + ''', 'RETIREMENT_UNIT_CHANGED')
  require(state.get('currentVehicle') is None and not state.get('source',{}).get('operation'),'RETIREMENT_NOT_QUIESCENT')
  from aosedge_demo_orchestrator.models import OperationRequest,VehicleTarget
  result=w.app.execute(OperationRequest('demo','retire',target=VehicleTarget.TEST)).to_dict()
  require(result['state']=='COMPLETED','RETIREMENT_UNCONFIRMED')
  answer=dict(retiredTest=REQUEST['expectedRun'],retiredUnit=''' + repr(UNIT) + ''')
print(json.dumps(answer))
''', timeout=220)
        # Recoverable parking, no recursive cleanup or shared Docker restart.
        self.remote('''
import os,pathlib,json,subprocess
r=pathlib.Path(''' + repr(REMOTE) + '''); backup=r/'previous-installation'
assert not backup.exists(),'BACKUP_ALREADY_EXISTS'
paths=[pathlib.Path('/Users/alexagizim/SDV-Lab-Data'),pathlib.Path('/Users/alexagizim/AosEdge SDV Packages'),pathlib.Path('/Users/alexagizim/Applications/AosEdge SDV Lab.app')]
assert all(p.exists() and not p.is_symlink() for p in paths),'PARKING_PATH_CHANGED'
assert all(p.stat().st_dev==r.stat().st_dev for p in paths),'PARKING_VOLUME_CHANGED'
for p in paths:
 proc=subprocess.run(['/usr/sbin/lsof','-t','+D',str(p)],capture_output=True,text=True,timeout=40)
 assert proc.returncode==1 and not proc.stdout,'PARKING_OPEN_HANDLES'
backup.mkdir(mode=0o700)
for p in paths: p.rename(backup/p.name)
assert all(not p.exists() for p in paths),'PARKING_UNCONFIRMED'
''', timeout=140)
        self.parked = True
        return dict(facts, previousInstallation='PARKED', sharedDocker='PRESERVED')

    def launch(self):
        if self.media:
            from campaign import Media,media_input
            path=self.media/'AosEdge-SDV-Lab-1.2.0-rc.2.dmg'
            selected=media_input(path,self.c,self.remote_dmg,self.t['user'])
            Media(self.t,self.c,selected,emit=lambda s:print(s,flush=True)).transfer()
        mount = str(Path(self.c['setupApp']).parent)
        h.remote(self.t, shlex.join(['/usr/bin/hdiutil', 'attach', self.remote_dmg, '-nobrowse', '-readonly', '-mountpoint', mount]) + ' >/dev/null\n', timeout=90)
        self.mounted = True
        app = self.build / 'Native UI Runner.app'
        receipt = json.loads((self.build / 'build-receipt.json').read_bytes())
        h.require(h.digest(app/'Contents/MacOS/NativeUIRunner') == receipt['executableSha256'] and receipt['signer']==SIGNER,
                  'FIRST_USE_RUNNER_CHANGED')
        subprocess.run(['/usr/bin/rsync', '-rpt', '-e', shlex.join(h.ssh_args(self.t)[:-1]),
            str(app), self.t['user']+'@'+self.t['host']+':'+shlex.quote(REMOTE+'/')], check=True, capture_output=True, timeout=40)
        self.remote('''
import pathlib,os,subprocess,time,json,hashlib
r=pathlib.Path(''' + repr(REMOTE) + '''); exe=pathlib.Path(''' + repr(self.c['setupApp'] + '/Contents/MacOS/Setup') + ''')
# Discover the executable from signed Info.plist instead of trusting its name.
import plistlib
app=pathlib.Path(''' + repr(self.c['setupApp']) + ''')
exe=app/'Contents/MacOS'/plistlib.loads((app/'Contents/Info.plist').read_bytes())['CFBundleExecutable']
assert hashlib.sha256(exe.read_bytes()).hexdigest()==''' + repr(self.c['setupSha256']) + ''','SETUP_EXECUTABLE_CHANGED'
subprocess.run(['/usr/bin/codesign','--verify','--deep','--strict',str(app)],check=True,capture_output=True)
runner=r/'Native UI Runner.app'
subprocess.run(['/usr/bin/codesign','--verify','--deep','--strict','-R=anchor apple generic and certificate leaf = H"''' + SIGNER + '''" and identifier "org.aosedge.sdv.qualification.native-ui-runner"',str(runner)],check=True,capture_output=True)
assert not (r/'tokens.fifo').exists(),'TOKEN_TRANSPORT_ALREADY_EXISTS'
os.mkfifo(r/'tokens.fifo',0o600)
subprocess.run(['/usr/bin/open','-a',str(app)],check=True,capture_output=True)
end=time.monotonic()+12
while time.monotonic()<end:
 rows=subprocess.run(['/bin/ps','-axo','pid=,comm='],capture_output=True,text=True,check=True).stdout.splitlines()
 pids=[int(row.strip().split(None,1)[0]) for row in rows if row.strip().split(None,1)[-1]==str(exe)]
 if len(pids)==1: break
 time.sleep(.1)
assert len(pids)==1,'SETUP_PROCESS_NOT_UNIQUE'
(r/'profile.json').write_text(json.dumps(dict(pid=pids[0],executable=str(exe),sha256=''' + repr(self.c['setupSha256']) + ''',installedUnenrolled='''+repr(self.installed)+''')))
os.chmod(r/'profile.json',0o600)
old=r/'progress.json'
if old.exists(): old.rename(r/('progress.before-'+str(int(time.time()))+'.json'))
owner=r/'display-owner.json'
if owner.exists():
 old=json.loads(owner.read_bytes())
 assert not subprocess.run(['/bin/ps','-p',str(old['pid']),'-o','comm='],capture_output=True,text=True).stdout.strip(),'DISPLAY_ASSERTION_ALREADY_ACTIVE'
awake=subprocess.Popen(['/usr/bin/caffeinate','-d','-i','-u','-t','7200'],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
owner.write_text(json.dumps(dict(pid=awake.pid)));os.chmod(owner,0o600)
subprocess.run(['/usr/bin/open','-a',str(runner),'--args',str(r)],check=True,capture_output=True)
''', timeout=45)
        return dict(setupSha256=self.c['setupSha256'], nativeSource=receipt['sourceSha256'], certificatesInitiallyAbsent=True)

    def progress(self):
        return h.parse(self.remote('import pathlib,json; p=pathlib.Path('+repr(REMOTE+'/progress.json')+'); print(p.read_text() if p.exists() else "{}")'))

    def run_ui(self):
        last = None
        end = time.monotonic() + 1200
        while time.monotonic() < end:
            progress = self.progress()
            stage = progress.get('stage')
            if stage != last:
                print(json.dumps(dict(nativeStage=stage)), flush=True)
                last = stage
            if stage == 'TOKENS_REQUIRED':
                self.issue_tokens()
            elif stage == 'PASS':
                h.atomic(self.records/'native-report.json', progress)
                return progress
            elif stage and stage not in ('EMPTY_SETUP_OBSERVED','INSTALLED_UNENROLLED_CONTINUATION','INSTALL_INPUT_DISPATCHED','INSTALL_COMPLETED','PAIR_ISSUANCE_INPUT_INTENT','NEW_CERTIFICATES_CONNECTED'):
                raise h.Error(stage)
            time.sleep(2)
        raise h.Error('NATIVE_FIRST_USE_DEADLINE')

    def issue_tokens(self):
        from aosedge_demo_orchestrator.unit_cloud import Cloud
        tokens = {}
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            for role in ('oem','sp'):
                intent = self.records/('token-'+role+'.intent.json')
                h.require(not intent.exists(), 'TOKEN_ALREADY_ISSUED_RECONCILE')
                client = Cloud(dict(credential='/Users/alexagizim/.aos/security prod/aos-user-'+role+'.p12', cloudDomain='aoscloud.io'),
                    expected_role='oem' if role=='oem' else 'service provider')
                h.require(client.user['ownerId']==self.c['cloudOwners'][role], 'TOKEN_OWNER_CHANGED')
                client.require('users_new_token', 'user_certificates_create')
                h.atomic(intent, dict(role=role, ownerId=client.user['ownerId'], method='POST', route='users/new-token/', replayAllowed=False))
                tokens[role] = client.call('users/new-token/','POST',expected=201)['token']
            # The remote program is fixed; only stdin carries the secret JSON.
            program = "import os,sys,stat; p="+repr(REMOTE+'/tokens.fifo')+"; s=os.lstat(p); assert stat.S_ISFIFO(s.st_mode) and stat.S_IMODE(s.st_mode)==0o600 and s.st_uid==os.getuid(); data=sys.stdin.buffer.read(16384); fd=os.open(p,os.O_WRONLY|os.O_NOFOLLOW|os.O_NONBLOCK); os.write(fd,data); os.close(fd)"
            proc = subprocess.run(h.ssh_args(self.t)+[shlex.join(['/usr/bin/python3','-I','-B','-c',program])],
                input=(json.dumps(tokens)+'\n').encode(), capture_output=True, timeout=20)
            tokens.clear()
            h.require(proc.returncode==0, 'TOKEN_SECURE_TRANSPORT_UNCONFIRMED')
        # Wait for a new stage; do not treat repeated TOKENS_REQUIRED polls as
        # permission to issue another token pair.
        end=time.monotonic()+15
        while self.progress().get('stage')=='TOKENS_REQUIRED':
            h.require(time.monotonic()<end, 'TOKEN_INPUT_UNCONFIRMED')
            time.sleep(.2)

    def verify(self):
        return self.worker('''
answer=None
with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
 w=Worker(REQUEST)
 with w.imports():
  require(w.binding(allow_empty=True) is None,'UNEXPECTED_TEST_CREATED')
  from aosedge_demo_orchestrator.cloud_connection import inspect_certificate
  certs=[inspect_certificate(w.config[key]) for key in ('oemCertificate','spCertificate')]
  require(all(row['domain']=='aoscloud.io' for row in certs),'ISSUED_CERTIFICATE_DOMAIN_CHANGED')
  connected=w.setup_call('cloud-observe',oem=w.config['oemCertificate'],sp=w.config['spCertificate'])
  require(connected['cloudStage']=='READY' and connected['rolesChecked'],'ISSUED_PAIR_NOT_READY')
  require(exchange('operations')['cloudDomain']=='aoscloud.io','PRESENTER_DOMAIN_CHANGED')
  answer=dict(newOemAndSpCertificates=True,domain='aoscloud.io',cloudStage='READY',noTestCreated=True,presenterObserved=True)
print(json.dumps(answer))
''', fresh=True)

    def cleanup(self):
        facts = {}
        if self.parked and self.mounted:
            # Normal product close, with no vehicle journal expected.
            facts = self.worker('''
with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
 w=Worker(REQUEST)
 with w.imports(): answer=w.shutdown()
print(json.dumps(answer))
''', fresh=True)
        self.remote('''
import pathlib,json,os,signal,subprocess,time
r=pathlib.Path('''+repr(REMOTE)+''')
profiles=[(r/'profile.json','pid'),(r/'progress.json','pid')]
for file,key in profiles:
 if not file.exists(): continue
 pid=json.loads(file.read_text())[key]
 comm=subprocess.run(['/bin/ps','-p',str(pid),'-o','comm='],capture_output=True,text=True).stdout.strip()
 if comm and (comm.startswith('''+repr(str(Path(self.c['setupApp']).parent)) + ''') or comm.startswith(str(r/'Native UI Runner.app'))):
  os.kill(pid,signal.SIGTERM)
p=r/'tokens.fifo'
if p.exists(): p.unlink()
owner=r/'display-owner.json'
if owner.exists():
 value=json.loads(owner.read_text());pid=value['pid']
 comm=subprocess.run(['/bin/ps','-p',str(pid),'-o','comm='],capture_output=True,text=True).stdout.strip()
 if comm=='/usr/bin/caffeinate':os.kill(pid,signal.SIGTERM)
''')
        if self.mounted:
            h.remote(self.t, shlex.join(['/usr/bin/hdiutil','detach',str(Path(self.c['setupApp']).parent)])+' >/dev/null\n', timeout=30)
        p = h.probe(self.t,cloud_domain='aoscloud.io')
        h.require(p['demoProcesses']==0 and p['busyPorts']==0, 'FIRST_USE_CLEANUP_UNCONFIRMED')
        return dict(product=facts, ownedDemoProcesses=0, ownedDemoListeners=0, mediaDetached=True, sharedDockerPreserved=True)

    def run(self):
        outcome, code = 'FAIL', 'NOT_RUN'
        try:
            self.stage('retire-and-park',self.prepare)
            self.stage('native-launch',self.launch)
            self.stage('native-first-use',self.run_ui)
            self.stage('independent-effects',self.verify)
            outcome, code = 'PASS', 'FIRST_USE_ACCEPTED'
        except Exception as error:
            code = str(error) if str(error).replace('_','').isalnum() else 'FIRST_USE_FAILED'
            print(json.dumps(dict(outcome='FAIL',code=code)),flush=True)
        finally:
            try:self.stage('closure',self.cleanup)
            except Exception as error:
                outcome, code = 'FAIL', 'CLOSURE_UNCONFIRMED'
                print(json.dumps(dict(outcome=outcome,code=code)),flush=True)
            h.atomic(self.records/'report.json',dict(outcome=outcome,code=code,stages=self.stages,
                seconds=round(time.monotonic()-self.started,3),candidate=self.c['manifestSha256'],
                tokensPersisted=False,workingKeysCopied=False))
        return 0 if outcome=='PASS' else 1


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build',type=Path,required=True)
    p.add_argument('--records',type=Path,required=True)
    p.add_argument('--reconcile-retired-docker-sharing',action='store_true')
    p.add_argument('--resume-installed-ui',action='store_true')
    p.add_argument('--media',type=Path)
    a=p.parse_args()
    sys.exit(Campaign(a.build,a.records,a.reconcile_retired_docker_sharing,a.resume_installed_ui,a.media).run())
