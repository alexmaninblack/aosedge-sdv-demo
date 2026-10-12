# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Pinned M1 native mouse adapter. No vehicle/Cloud mutation or RPC fallback."""
import contextlib
import io
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
from uuid import uuid4

import journey as j
import remote_harness as h
from ui_native_gate import ACTION_IDS, LIVE_STAGES, native_receipt, validate

SIGNER = '0514708CB8DA6BB8C26823D4F01C9F6869908008'
BUNDLE = 'org.aosedge.sdv.qualification.native-ui-runner'


def target(transport, config, gate):
    """Read normal installed selection/source journal; never guess a process."""
    payload = dict(config=config, kind='observe', args=dict(query='snapshot'),
                   phase='observe', requestId=str(uuid4()), expectedRun=gate['test'])
    program = j.WORKER.read_text() + '\nREQUEST=' + repr(payload) + '\nSESSION=' + repr(gate['sessionId']) + '''
answer=None
try:
 with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
  worker=Worker(REQUEST)
  with worker.imports():
   state=worker.binding();ops=worker.idle()
   require(ops['sessionId']==SESSION,'NATIVE_SESSION_CHANGED')
   source=state['source']; view=worker.app.source_service.observe()
   require(state.get('currentVehicle')=='test' and view.get('selectedVehicle')=='test'
    and view.get('state')=='CONNECTED' and source.get('runId')==REQUEST['expectedRun'],'NATIVE_SOURCE_NOT_CONNECTED')
   from aosedge_demo_orchestrator.host_runtime import selected
   runtime=selected(worker.state);exe=runtime.entry('keyboard')
   runner=source.get('runnerCommand') or []
   require('--keyboard-ui' in runner and runner[runner.index('--keyboard-ui')+1]==str(exe),'NATIVE_OWNER_PATH_CHANGED')
   control=str(worker.state/source['controlDirectory'])
   pids=[pid for pid,args in worker.app.source_service.driver.vm._processes()
    if args.startswith(str(exe)+' ') and control in args]
   require(len(pids)==1,'NATIVE_OWNER_NOT_UNIQUE')
   answer=dict(candidate=worker.pin,test=REQUEST['expectedRun'],sessionId=SESSION,pid=pids[0],
    executable=str(exe),executableSha256=hashlib.sha256(exe.read_bytes()).hexdigest())
except Exception as error:
 answer=dict(error=fixed_code(str(error)) or 'NATIVE_OWNER_UNAVAILABLE')
print(json.dumps(answer),flush=True)
'''
    python = config['packageRoot'] + '/demo-artifacts/aosedge-sdv-demo/host-runtime/python/bin/python3.12'
    output = h.remote(transport, shlex.quote(python)+" -I -B - <<'SDV_NATIVE_OWNER_READ'\n"+
                      program+'\nSDV_NATIVE_OWNER_READ\n', timeout=50)
    value = h.parse(output)
    h.require(isinstance(value,dict) and 'error' not in value, value.get('error','NATIVE_OWNER_UNAVAILABLE'))
    h.require(value['candidate']==config['manifestSha256'] and value['test']==gate['test']
              and value['sessionId']==gate['sessionId'], 'NATIVE_OWNER_BINDING_CHANGED')
    return value


class Live:
    def __init__(self, transport, config, test, build, records, run_id):
        h.require(re.fullmatch(r'native-ui-live-\d{8}(?:-[a-z0-9]+)?',run_id), 'NATIVE_LIVE_ROOT_INVALID')
        self.transport,self.config,self.test,self.records=transport,config,test,records
        self.root='/Users/'+transport['user']+'/SDV-Qualification/'+run_id
        self.python=config['packageRoot']+'/demo-artifacts/aosedge-sdv-demo/host-runtime/python/bin/python3.12'
        self.profile=None;self.started=False;self.stages=set()
        build=h.unlinked(build.resolve(strict=True));receipt=h.parse((build/'build-receipt.json').read_bytes())
        rows=[r for r in receipt['apps'] if r['bundleId']==BUNDLE]
        h.require(len(rows)==1 and receipt['signatureIdentity']==SIGNER, 'NATIVE_RUNNER_BUILD_INVALID')
        row=rows[0];app=build/row['app']
        h.require(row['app']=='Native UI Runner.app' and row['executable']=='NativeUIRunner'
                  and h.digest(app/'Contents/MacOS/NativeUIRunner')==row['sha256'], 'NATIVE_RUNNER_BUILD_CHANGED')
        self.runner_digest=row['sha256']
        self.remote('import os,pathlib; os.umask(0o077); r=pathlib.Path('+repr(self.root)+'); '
            'assert not r.exists(),"NATIVE_CAMPAIGN_REPLAY_FORBIDDEN"; '
            'r.mkdir(mode=0o700); (r/"requests").mkdir(mode=0o700)')
        shell=shlex.join(h.ssh_args(transport)[:-1])
        subprocess.run(['/usr/bin/rsync','-rpt','-e',shell,str(app),transport['user']+'@'+transport['host']+':'+
                        shlex.quote(self.root+'/')],check=True,capture_output=True,timeout=30)
        requirement='-R=anchor apple generic and certificate leaf = H"'+SIGNER+'" and identifier "'+BUNDLE+'"'
        self.remote('import hashlib,pathlib,subprocess; app=pathlib.Path('+repr(self.root+'/Native UI Runner.app')+'); '
            'subprocess.run(["/usr/bin/codesign","--verify","--deep","--strict",'+repr(requirement)+
            ',str(app)],check=True,capture_output=True,timeout=10); '
            'assert hashlib.sha256((app/"Contents/MacOS/NativeUIRunner").read_bytes()).hexdigest()=='+repr(self.runner_digest))

    def remote(self, program, timeout=15):
        return h.remote(self.transport,shlex.quote(self.python)+" -I -B - <<'SDV_NATIVE_LIVE'\n"+
                        program+'\nSDV_NATIVE_LIVE\n',timeout=timeout)

    def launch(self, profile):
        self.profile=profile
        self.remote('import json,os,pathlib,subprocess; r=pathlib.Path('+repr(self.root)+'); '
            'names=subprocess.run(["/bin/ps","-axo","comm="],capture_output=True,text=True,check=True).stdout.splitlines(); '
            'assert not any(n.endswith("/Native UI Runner.app/Contents/MacOS/NativeUIRunner") for n in names),"NATIVE_RUNNER_ALREADY_ACTIVE"; '
            'fd=os.open(r/"live-profile.json",os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600); '
            'os.write(fd,'+repr(json.dumps(profile).encode())+'); os.fsync(fd); os.close(fd)')
        self.started=True
        h.remote(self.transport,shlex.join(['/usr/bin/open','-a',self.root+'/Native UI Runner.app','--args',self.root]),timeout=10)
        result=self.remote('import pathlib,json,time; p=pathlib.Path('+repr(self.root+'/runner-status.json')+'); '
            'end=time.monotonic()+8\nwhile not p.exists() and time.monotonic()<end: time.sleep(.05)\n'
            'assert p.exists(),"NATIVE_RUNNER_START_UNCONFIRMED"\nprint(p.read_text())',timeout=12)
        status=h.parse(result)
        h.require(status.get('status')=='READY' and status.get('bundleId')==BUNDLE,'ACCESSIBILITY_PERMISSION_REQUIRED')
        self.runner_pid=status['pid']

    def request(self, operation, stage, action=None):
        identity=str(uuid4());profile=self.profile
        binding={k:profile[k] for k in ('candidate','test','sessionId')};binding['stage']=stage
        value=dict(schemaVersion=1,requestId=identity,operation=operation,pid=profile['pid'],
                   executableSha256=profile['executableSha256'],binding=binding)
        if action is not None:value['action']=action
        path=self.root+'/requests/'+identity+'.json'
        # Record before dispatch. An interrupted transport is reconciled by a
        # receipt read only, never by resubmitting or choosing another request ID.
        h.atomic(self.records/('native-'+stage+'.intent.json'),value)
        program='import os,pathlib,time; p=pathlib.Path('+repr(path)+'); '
        program+='fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600); '
        program+='os.write(fd,'+repr(json.dumps(value).encode())+'); os.fsync(fd); os.close(fd); '
        program+='r=p.with_suffix(".receipt"); end=time.monotonic()+8\n'
        program+='while not r.exists() and time.monotonic()<end: time.sleep(.05)\n'
        program+='assert r.exists(),"NATIVE_INPUT_UNCERTAIN"\nprint(r.read_text())'
        try:raw=self.remote(program,timeout=12)
        except h.Error:
            raw=self.remote('import pathlib; print(pathlib.Path('+repr(str(Path(path).with_suffix('.receipt')))+').read_text())')
        result=h.parse(raw);h.require(result.get('requestId')==identity,'NATIVE_RECEIPT_ID_CHANGED')
        h.atomic(self.records/('native-'+stage+'.receipt.json'),result)
        return result

    def __call__(self, gate):
        validate(gate,gate.get('stage'),gate.get('action'))
        h.require(gate['test']==self.test and LIVE_STAGES.get(gate['stage'])==gate['action']
                  and gate['stage'] not in self.stages, 'NATIVE_LIVE_STAGE_REFUSED')
        self.stages.add(gate['stage'])
        h.require(not (self.records/('native-'+gate['stage']+'.intent.json')).exists(),'NATIVE_INPUT_ALREADY_ATTEMPTED')
        current=target(self.transport,self.config,gate)
        if self.profile is None:self.launch(current)
        h.require(current==self.profile,'NATIVE_LIVE_TARGET_CHANGED')
        return native_receipt(gate,self.request('click',gate['stage'],ACTION_IDS[gate['action']]),self.config['manifestSha256'])

    def close(self):
        if not self.started:return True
        result=self.request('quit','native-controls-close')
        h.require(result.get('code')=='RUNNER_CLOSED','NATIVE_RUNNER_CLOSE_UNCONFIRMED')
        self.remote('import os,time,subprocess; end=time.monotonic()+8\n'
            'while time.monotonic()<end:\n'
            ' names=subprocess.run(["/bin/ps","-axo","comm="],capture_output=True,text=True,check=True).stdout.splitlines()\n'
            ' if not any(n.startswith('+repr(self.root+'/')+') for n in names): break\n'
            ' time.sleep(.05)\nelse: raise ValueError("NATIVE_RUNNER_EXIT_UNCONFIRMED")',timeout=12)
        self.started=False
        return True
