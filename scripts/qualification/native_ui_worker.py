# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""M1-only mechanical native UI pilot. No product owner or vehicle connection."""
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import time
from uuid import uuid4

ACTIONS = ('driving.safe-stop','driving.autopilot','driving.brake-maneuver',
           'driving.tire-maneuver','driving.return-to-road')
APPS = {'DrivingControlPilot.app': ('ControlFixture','org.aosedge.sdv.qualification.control-fixture'),
        'Native UI Runner.app': ('NativeUIRunner','org.aosedge.sdv.qualification.native-ui-runner')}
SIGNER = '0514708CB8DA6BB8C26823D4F01C9F6869908008'


def require(value, code):
    if not value: raise ValueError(code)


def read(path):
    return json.loads(path.read_text())


def atomic(path, value):
    temporary=path.with_suffix('.pending')
    fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'w') as stream:
        json.dump(value,stream);stream.flush();os.fsync(stream.fileno())
    os.replace(temporary,path)


def wait(fn, code, seconds=8):
    until=time.monotonic()+seconds
    while True:
        value=fn()
        if value: return value
        require(time.monotonic()<until,code)
        time.sleep(.05)


def process_alive(pid):
    try: os.kill(pid,0);return True
    except ProcessLookupError: return False


def verify(root):
    require(root.parent==Path.home()/'SDV-Qualification'
        and re.fullmatch(r'native-ui-pilot-\d{8}(?:-[a-z0-9]+)?',root.name),'PILOT_ROOT_INVALID')
    for path in (root,root/'requests'):
        info=path.lstat()
        require(stat.S_ISDIR(info.st_mode) and info.st_uid==os.getuid()
            and stat.S_IMODE(info.st_mode)==0o700,'PILOT_ROOT_NOT_PRIVATE')
    manifest=read(root/'build-receipt.json')
    require(manifest['artifact']=='NATIVE_QUALIFICATION_PILOT'
        and manifest['productPayloadChanged'] is False and manifest['vehicleConnected'] is False
        and manifest['signatureIdentity']==SIGNER,'PILOT_ARTIFACT_INVALID')
    require(len(manifest['apps'])==2 and {r['app'] for r in manifest['apps']}==set(APPS),'PILOT_APPS_INVALID')
    for row in manifest['apps']:
        require((row['executable'],row['bundleId'])==APPS[row['app']], 'PILOT_APP_IDENTITY_INVALID')
        app=root/row['app']
        requirement='-R=anchor apple generic and certificate leaf = H"'+SIGNER+'" and identifier "'+row['bundleId']+'"'
        subprocess.run(['/usr/bin/codesign','--verify','--deep','--strict',requirement,str(app)],check=True,capture_output=True,timeout=10)
        exe=app/'Contents/MacOS'/row['executable']
        require(hashlib.sha256(exe.read_bytes()).hexdigest()==row['sha256'],'PILOT_EXECUTABLE_CHANGED')
    return manifest


class Pilot:
    def __init__(self,root,manifest):
        self.root=root;self.manifest=manifest;self.pid=None;self.runner=None
        self.digest=next(r['sha256'] for r in manifest['apps'] if r['executable']=='ControlFixture')
        self.stages=[]

    def request(self,operation,**extra):
        id=str(uuid4());path=self.root/'requests'/(id+'.json')
        value=dict(schemaVersion=1,requestId=id,operation=operation,pid=self.pid or 12345,executableSha256=self.digest,**extra)
        data=json.dumps(value).encode();fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        with os.fdopen(fd,'wb') as stream: stream.write(data);stream.flush();os.fsync(stream.fileno())
        receipt=wait(lambda:read(path.with_suffix('.receipt')) if path.with_suffix('.receipt').exists() else None,
                     'RUNNER_RESPONSE_UNCERTAIN',seconds=10)
        require(receipt.get('requestId')==id,'RUNNER_RECEIPT_MISMATCH')
        return value,receipt

    def events(self):
        path=self.root/'fixture-events.jsonl'
        return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []

    def mode(self,mode):
        id=str(uuid4());atomic(self.root/'fixture-command.json',dict(requestId=id,mode=mode))
        if mode=='quit': return
        wait(lambda:(self.root/'fixture-command-receipt.json').exists()
            and read(self.root/'fixture-command-receipt.json').get('requestId')==id,'FIXTURE_COMMAND_UNCONFIRMED')

    def stage(self,label,fn):
        start=time.monotonic()
        try: facts=fn()
        except Exception:
            self.stages.append(dict(stage=label,outcome='FAIL',seconds=round(time.monotonic()-start,3)))
            raise
        else:
            self.stages.append(dict(stage=label,outcome='PASS',seconds=round(time.monotonic()-start,3),facts=facts or {}))

    def inspect(self):
        _,receipt=self.request('inspect')
        require(receipt.get('outcome')=='PASS' and receipt.get('code')=='UI_CONTRACT_OBSERVED','UI_INSPECTION_UNCONFIRMED')
        rows=receipt.get('buttons',[])
        require(len(rows)==5 and {r['id'] for r in rows}==set(ACTIONS),'UI_SEMANTIC_CONTRACT_MISMATCH')
        return receipt

    def place(self):
        before=self.inspect()['buttons']
        _,receipt=self.request('place',frame=[650,180,700,470])
        require(receipt.get('outcome')=='PASS' and receipt.get('code')=='LAYOUT_REQUESTED','UI_LAYOUT_UNCONFIRMED')
        def changed():
            rows=self.inspect()['buttons']
            return rows if [r['frame'] for r in before]!=[r['frame'] for r in rows] else None
        after=wait(changed,'UI_GEOMETRY_DID_NOT_CHANGE')
        return dict(before=before,after=after)

    def click(self,action):
        before=len(self.events());value,receipt=self.request('click',action=action)
        require(receipt.get('outcome')=='INPUT_DISPATCHED' and receipt.get('inputDispatched') is True,
                receipt.get('code','INPUT_NOT_DISPATCHED'))
        def effect():
            current=self.events()
            if len(current)==before:return None
            require(len(current)==before+1 and current[-1]['action']==action
                and current[-1]['fixture'] is True and current[-1]['mouseDownObserved'] is True,'FIXTURE_EFFECT_MISMATCH')
            return current[-1]
        effect_started=time.monotonic();wait(effect,'MOUSE_EFFECT_UNCONFIRMED')
        return dict(requestId=value['requestId'],runnerSeconds=receipt['runnerSeconds'],
                    targetResolveSeconds=receipt['resolveSeconds'],
                    callbackObservationSeconds=round(time.monotonic()-effect_started,6),frame=receipt['resolvedFrame'])

    def negative(self,operation,code,**extra):
        before=len(self.events());_,receipt=self.request(operation,**extra)
        require(receipt.get('outcome')=='BLOCKED' and receipt.get('code')==code
            and receipt.get('inputDispatched') is False,'NEGATIVE_GUARD_MISMATCH')
        require(len(self.events())==before,'NEGATIVE_EMITTED_ACTION')
        return dict(code=code,inputDispatched=False)

    def execute(self):
        status=self.root/'runner-status.json'
        state=wait(lambda:read(status) if status.exists() else None,'RUNNER_NOT_STARTED')
        self.runner=state['pid']
        require(process_alive(self.runner),'RUNNER_PROCESS_MISSING')
        require(state['status']=='READY','ACCESSIBILITY_PERMISSION_REQUIRED')
        require(not (self.root/'fixture-status.json').exists(),'FIXTURE_REPLAY_FORBIDDEN')
        subprocess.run(['/usr/bin/open','-a',str(self.root/'DrivingControlPilot.app'),'--args',str(self.root)],check=True,capture_output=True,timeout=10)
        fixture=wait(lambda:read(self.root/'fixture-status.json') if (self.root/'fixture-status.json').exists() else None,'FIXTURE_NOT_STARTED')
        require(fixture['fixture'] is True,'FIXTURE_IDENTITY_INVALID');self.pid=fixture['pid']
        self.stage('semantic-elements',self.inspect)
        for action in ACTIONS:self.stage('original-'+action,lambda action=action:self.click(action))
        self.stage('move-and-resize',self.place)
        for action in ACTIONS:self.stage('transformed-'+action,lambda action=action:self.click(action))
        for mode,code in (('busy','UI_ELEMENT_DISABLED'),('missing','UI_ELEMENT_MISSING'),
                          ('duplicate','UI_ELEMENT_AMBIGUOUS'),('obstructed','UI_ELEMENT_OBSTRUCTED'),
                          ('minimized','TARGET_WINDOW_MINIMIZED')):
            self.mode(mode)
            self.stage(mode+'-refusal',lambda code=code:self.negative('click',code,action='driving.tire-maneuver'))
            self.mode('normal')
        self.stage('unsupported-action',lambda:self.negative('click','REQUEST_ACTION_INVALID',action='driving.delete-test'))
        original=self.digest;self.digest='0'*64
        try:self.stage('wrong-digest',lambda:self.negative('click','TARGET_DIGEST_MISMATCH',action='driving.safe-stop'))
        finally:self.digest=original
        original=self.pid;self.pid=self.runner
        try:self.stage('wrong-process',lambda:self.negative('click','TARGET_PROCESS_MISMATCH',action='driving.safe-stop'))
        finally:self.pid=original
        facts=self.click('driving.safe-stop');id=facts['requestId']
        receipt=read(self.root/'requests'/(id+'.receipt'))
        before=len(self.events());time.sleep(.2)
        require(read(self.root/'requests'/(id+'.receipt'))==receipt
            and len(self.events())==before,'RECORDED_REQUEST_REEXECUTED')
        self.stages.append(dict(stage='persistent-request-not-reexecuted',outcome='PASS',facts=dict(inputRepeated=False)))

    def close(self):
        if self.pid and process_alive(self.pid):
            self.mode('quit');wait(lambda:not process_alive(self.pid),'FIXTURE_EXIT_UNCONFIRMED')
        if self.runner and process_alive(self.runner):
            self.request('quit');wait(lambda:not process_alive(self.runner),'RUNNER_EXIT_UNCONFIRMED')
        return dict(fixtureClosed=True,runnerClosed=True,productOwnersChanged=False)


def main(root):
    os.umask(0o077);began=time.monotonic();pilot=None
    result=dict(outcome='FAIL',fixtureOnly=True,vehicleConnected=False,fullE2E='NOT_COMPLETE')
    # Only a verified, exclusively claimed campaign may write evidence or close apps.
    try:
        manifest=verify(root)
        require(not (root/'campaign.intent').exists() and not (root/'pilot-report.json').exists(),'CAMPAIGN_REPLAY_FORBIDDEN')
        fd=os.open(root/'campaign.intent',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        with os.fdopen(fd,'w') as stream:
            json.dump(dict(pid=os.getpid(),fixtureOnly=True),stream);stream.flush();os.fsync(stream.fileno())
    except Exception as error:
        code=str(error)
        result['code']=code if re.fullmatch('[A-Z][A-Z0-9_]{1,100}',code) else 'CAMPAIGN_CLAIM_REFUSED'
        print(json.dumps(result));return 2
    try:
        pilot=Pilot(root,manifest);pilot.execute()
        result['outcome']='PASS'
    except Exception as error:
        message=str(error)
        result['code']=message if re.fullmatch('[A-Z][A-Z0-9_]{1,100}',message) else 'NATIVE_PILOT_FAILED'
    finally:
        if pilot:
            result['stages']=pilot.stages
            try:result['cleanup']=pilot.close()
            except Exception:result.update(outcome='FAIL',cleanup=dict(code='PILOT_CLEANUP_UNCONFIRMED'))
        result['seconds']=round(time.monotonic()-began,3)
        atomic(root/'pilot-report.json',result)
    print(json.dumps(result))
    return 0 if result['outcome']=='PASS' else 1


if __name__=='__main__': raise SystemExit(main(Path(sys.argv[1]).absolute()))
