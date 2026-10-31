# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Pinned engineering delta over immutable installed owners, not a new product."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import stat
import subprocess
import sys
import time


def check(ok, code):
    if not ok:raise ValueError(code)


def atomic(path, value):
    part=path.with_suffix('.pending')
    fd=os.open(part,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'w') as stream:json.dump(value,stream);stream.flush();os.fsync(stream.fileno())
    os.replace(part,path)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--context',required=True,type=Path)
    parser.add_argument('--resume-from',type=Path)
    args=parser.parse_args();c=json.loads(args.context.read_bytes());records=args.context.parent
    console=json.loads(sys.stdin.read(8193))
    check(set(console)=={'password'} and isinstance(console['password'],str) and 0<len(console['password'])<1024
          and not any(ch in console['password'] for ch in '\r\n\x00'),'CONSOLE_INPUT_INVALID')
    check(args.context.stat().st_uid==os.getuid() and stat.S_IMODE(args.context.stat().st_mode)==0o600,'CONTEXT_NOT_PRIVATE')
    check(subprocess.check_output(['/usr/sbin/sysctl','-n','hw.model'],text=True).strip()=='Mac16,8','M4_MODEL_CHANGED')
    package=Path(c['packageRoot']);retained=Path(c['retainedRoot']);vision=Path(c['visionRoot'])
    check(vision==Path.home()/'SDV-Vision-Lab-Data' and vision!=retained,'VISION_STATE_SCOPE_INVALID')
    previous=None
    if args.resume_from:
        match=re.fullmatch('guest-continuation(?:-([2-9][0-9]*))?',records.name)
        check(match is not None,'RESUME_SCOPE_INVALID')
        number=int(match.group(1) or '1')
        previous_root=records.parent if number==1 else records.parent/('guest-continuation' if number==2 else 'guest-continuation-'+str(number-1))
        check(args.resume_from==previous_root/'result.json','RESUME_SCOPE_INVALID')
        previous=json.loads(args.resume_from.read_bytes())
        check(previous['outcome']=='NOT_COMPLETE' and previous.get('code') in ('GUEST_PROOF_FAILED','GUEST_OCI_EXECUTION_FAILED','GUEST_TIME_OUTSIDE_HOST_ENVELOPE')
              and previous['ownRuntimeStopped'] is True,'PREVIOUS_ATTEMPT_NOT_RECONCILED')
    else:
        check(not vision.exists() and not vision.is_symlink(),'VISION_INSTANCE_EXISTS_RECONCILE_REQUIRED')
    check(hashlib.sha256((package/'application-manifest.json').read_bytes()).hexdigest()==c['manifestSha256'],'CANDIDATE_CHANGED')
    for name,pin in c['proofFiles'].items():
        check(hashlib.sha256((records/name).read_bytes()).hexdigest()==pin,'PROOF_TRANSFER_CHANGED')
    app=package/'aosedge-sdv-demo/apps/demo-orchestrator/src'
    for name,pin in c['baseFiles'].items():
        check(hashlib.sha256((app/'aosedge_demo_orchestrator'/name).read_bytes()).hexdigest()==pin,'INSTALLED_BASE_CHANGED')
    sys.path.insert(0,str(app))
    import aosedge_demo_orchestrator
    aosedge_demo_orchestrator.__path__.insert(0,str(records/'delta'))
    from aosedge_demo_orchestrator import runtime_paths,installed_control
    from aosedge_demo_orchestrator.environment import EnvironmentService,JOURNAL
    from aosedge_demo_orchestrator.vm import VMService,access_path
    from aosedge_demo_orchestrator.vm_profiles import VISION
    from aosedge_demo_orchestrator.guest_access import ssh_command
    check(runtime_paths.CODE_ROOT==package/'aosedge-sdv-demo','BASE_RUNTIME_SCOPE_CHANGED')
    for port in (10022,12022,18080,2000,18053):
        with socket.socket() as probe:
            probe.settimeout(.2)
            check(probe.connect_ex(('127.0.0.1',port))!=0,'CONFLICTING_RUNTIME_OWNER')
    before=json.loads((retained/JOURNAL).read_bytes())
    old=before['vehicles']['test']
    check(old['localVmId']==c['retainedTest'] and not old.get('unitId'),'RETAINED_TEST_CHANGED')
    preserved={k:old.get(k) for k in ('localVmId','overlay','unitId','nodeId','mac','sshPort')}
    result=dict(scenario='VISION_VM_M4',outcome='NOT_COMPLETE',phases=[],modelExecution='NOT_RUN',
        nativeAosDeployment='NOT_RUN',liveCameraDelivery='NOT_RUN',fullE2E='NOT_RUN',cloudMutation=False,
        carlaOrFactoryRebuilt=False,engineeringDelta=True)
    started=time.monotonic();runtime=None;created=False;cleanup=False
    def step(name,action):
        print(json.dumps(dict(stage=name,state='STARTED')),flush=True);begin=time.monotonic()
        data=action();row=dict(stage=name,seconds=round(time.monotonic()-begin,2),facts=data)
        result['phases'].append(row);atomic(records/(name+'.json'),row)
        print(json.dumps(dict(stage=name,state='COMPLETE',seconds=row['seconds'])),flush=True)
        return data
    try:
        # Use the existing installed selection transaction, never forge a receipt.
        sys.path.insert(0,str(Path(c['setupApp'])/'Contents/Resources/tooling/scripts/distribution'))
        from installation import Store
        from version_management import Versions
        _,identity=runtime_paths.instance(retained)
        selection=installed_control.selection(retained,identity)
        store=Store(Path(selection['storePath']),selection['volumeUUID'])
        if previous is None:
            step('instance',lambda:runtime_paths.create_instance(vision))
            step('select-verified-inputs',lambda:Versions(store,vision).change('select',0,c['manifestSha256']))
        else:
            _,vision_id=runtime_paths.instance(vision)
            check(installed_control.selection(vision,vision_id)['current']==c['manifestSha256'],'VISION_SELECTION_CHANGED')
            existing=json.loads((vision/JOURNAL).read_bytes())
            previous_id=previous.get('resumedExistingVm') or next(p['facts']['localVmId'] for p in previous['phases'] if p['stage']=='manufacture')
            check(existing['vehicles']['test']['localVmId']==previous_id and
                  existing['vmProfile']==VISION.name and existing['vehicles']['test']['runtime']['state']=='STOPPED','RESUME_VM_BINDING_CHANGED')
            created=True;result['resumedExistingVm']=previous_id
        with runtime_paths.installed_session(vision):
            env=EnvironmentService(vm_profile=VISION.name)
            def provider(role):
                check(role=='test','VISION_VM_REQUIRES_TEST_ONLY')
                return console['password']
            runtime=VMService(env,password_provider=provider,progress=lambda msg:print(json.dumps(dict(stage='vm-owner',state=str(msg)[:100])),flush=True))
            def manufacture():
                nonlocal created
                state=env.create('test',selector=c['image']);created=True
                check(state['vmProfile']==VISION.name,'PROFILE_NOT_RECORDED')
                return dict(profile=state['vmProfile'],localVmId=state['vehicles']['test']['localVmId'],cloudUnit=None)
            if previous is None:step('manufacture',manufacture)
            def start_vm():
                response=runtime.execute('start','test',timeout=150)
                check(response['vehicles']['test']['state']=='COMPLETED' and response['infrastructure']['state']=='COMPLETED','VISION_VM_START_UNCONFIRMED')
                return dict(state='COMPLETED',profile=VISION.name)
            def stop_vm():
                response=runtime.execute('stop','test',timeout=60)
                check(response['vehicles']['test']['state']=='COMPLETED' and response['infrastructure']['state']=='COMPLETED','VISION_VM_STOP_UNCONFIRMED')
                return dict(state='COMPLETED')
            step('first-boot',start_vm)
            console.clear();runtime.password_provider=None
            def synchronize():
                value=runtime.sync_time()
                atomic(records/'native-time-observation.json',value)
                check(value['state']=='READY','GUEST_NATIVE_TIME_UNCONFIRMED')
                return dict(state=value['state'],skewBoundSeconds=value['skewBoundSeconds'])
            step('native-time',synchronize)
            def guest():
                begin=time.time()
                response=subprocess.run(ssh_command(access_path(vision,'test'),12022,15),
                    input='python3 - <<\'VISION_GUEST\'\n'+(records/'vision_vm_guest.py').read_text()+'\nVISION_GUEST\n',
                    capture_output=True,text=True,timeout=40)
                check(len(response.stdout)<32768,'GUEST_PROOF_RESPONSE_TOO_LARGE')
                data=json.loads(response.stdout)
                atomic(records/'guest-last-observation.json',data)
                if response.returncode:
                    atomic(records/'guest-failure.json',data)
                    print(json.dumps(dict(stage='guest-diagnostic',state='FAILED',facts=data)),flush=True)
                    check(False,data.get('code','GUEST_PROOF_FAILED'))
                check(begin-10<=data['guestEpoch']<=time.time()+10,'GUEST_TIME_OUTSIDE_HOST_ENVELOPE')
                return data
            step('guest-container-proof',guest)
            step('first-stop',stop_vm)
            step('retained-restart',start_vm)
            step('restart-native-time',synchronize)
            step('restart-guest-proof',guest)
            step('final-stop',stop_vm)
            check(runtime.observe_readiness('test')['reason']=='VM_NOT_RUNNING','VM_EXIT_UNCONFIRMED')
            for port in (12022,18053):
                with socket.socket() as probe:
                    probe.settimeout(.2);check(probe.connect_ex(('127.0.0.1',port))!=0,'LISTENER_EXIT_UNCONFIRMED')
            cleanup=True
        after=json.loads((retained/JOURNAL).read_bytes())['vehicles']['test']
        check({k:after.get(k) for k in preserved}==preserved,'RETAINED_MAIN_IDENTITY_CHANGED')
        result.update(outcome='PASS_VM_ONLY',ownRuntimeStopped=True,mainIdentityPreserved=True,profile=VISION.name,
            visionRoot=str(vision),next='Real-model compute characterization; not yet executed')
    except Exception as error:
        message=str(error);result['code']=message if re.fullmatch('[A-Z][A-Z0-9_]{1,100}',message) else type(error).__name__
        if created and runtime and not cleanup:
            try:
                with runtime_paths.installed_session(vision):
                    response=runtime.execute('stop','test',timeout=60)
                    cleanup=response['vehicles']['test']['state']=='COMPLETED' and response['infrastructure']['state']=='COMPLETED' and runtime.observe_readiness('test')['reason']=='VM_NOT_RUNNING'
            except Exception:cleanup=False
        result['ownRuntimeStopped']=cleanup
    finally:
        result['seconds']=round(time.monotonic()-started,2)
        atomic(records/'result.json',result)
        print(json.dumps(result),flush=True)
    return 0 if result['outcome']=='PASS_VM_ONLY' else 1


if __name__=='__main__':raise SystemExit(main())
