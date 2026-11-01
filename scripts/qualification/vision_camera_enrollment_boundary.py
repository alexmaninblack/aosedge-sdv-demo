#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Observe and normally stop only the failed first Vision enrollment campaign.

No credential projection, transaction edit, component cancellation, Cloud
mutation, rootfs change, new VM or new camera publication is permitted here.
"""
import argparse
import json
from pathlib import Path
import shlex
import subprocess
import sys
import time


def remote(context,preserve_unfinished=False,collect_stopped=False):
    c=json.loads(context.read_bytes());records=context.parent
    if not collect_stopped:assert not (records/'enrollment-boundary-result.json').exists()
    package=Path(c['main']['packageRoot']);bundle=Path(c['bundle'])
    subprocess.run(['codesign','--verify','--deep','--strict','-R',
        '=identifier "org.aosedge.sdvlab.vision.bootstrap" and anchor apple generic and certificate leaf[subject.OU] = "3NF57VKB3V"',
        str(bundle)],check=True,capture_output=True,timeout=120)
    sys.path.insert(0,str(package/'aosedge-sdv-demo/apps/demo-orchestrator/src'))
    import aosedge_demo_orchestrator
    from aosedge_demo_orchestrator import runtime_paths
    aosedge_demo_orchestrator.__path__.insert(0,str(bundle/'Contents/Resources/tooling/aosedge-sdv-demo/apps/demo-orchestrator/src/aosedge_demo_orchestrator'))
    from aosedge_demo_orchestrator import vision_bootstrap as v
    from aosedge_demo_orchestrator.environment import EnvironmentService,JOURNAL
    from aosedge_demo_orchestrator.vm import VMService,access_path
    from aosedge_demo_orchestrator.application import DemoOrchestrator
    from aosedge_demo_orchestrator.workspace import WorkspaceService
    from aosedge_demo_orchestrator.guest_access import ssh_command
    from aosedge_demo_orchestrator.status import read_json
    native=Path.home()/v.INSTANCE_NAME
    retained={Path.home()/n:(Path.home()/n/JOURNAL).read_bytes() for n in
        ('SDV-Lab-Data','SDV-Vision-Lab-Data','SDV-Vision-Native-Lab-Data')}
    b=v.verify(bundle,c['main']['manifestSha256']);assert b.manifest_sha256==c['bootstrapManifestSha256']
    result=dict(scenario='VISION_CAMERA_FIRST_ENROLLMENT_BOUNDARY',outcome='NOT_COMPLETE',cleanup={})
    began=time.monotonic()
    with runtime_paths.installed_session(native):
        env=EnvironmentService(catalog=v.SignedVisionCatalog(b),vm_profile=v.VM_PROFILE)
        vm=VMService(env);app=DemoOrchestrator(environment_service=env,vm_service=vm)
        state=read_json(native/JOURNAL);item=state['vehicles']['test'];source=state['source'];pending=source['operation']
        if collect_stopped:
            previous=json.loads((records/'enrollment-boundary-result.json').read_bytes())
            assert previous['code']=='KeyError' and previous['cleanup']['sourceProcessesStopped'] is True
            assert item['runtime']['state']=='STOPPED' and previous['unfinishedSourceIntentPreserved'] is True
            assert not any(app.source_service.driver.live_process(source[n]) for n in ('runnerCommand','simulatorCommand'))
            assert pending['initialManual'] is True and pending['phase']=='RESET_CONFIRMED'
            assert vm._owned_pid(vm._command(state,'test'),str(native/item['overlay'])) is None
            # The VM's normal per-guest stop completed before the receipt
            # shape error; its separate DNS-owner close had not yet run.
            assert all(i['runtime']['state']=='STOPPED' for i in state['vehicles'].values())
            with env._writer():
                vm._stop_dns(state)
            import socket,os
            for port in (12022,2000,18080,16443,18053):
                with socket.socket() as s:
                    s.settimeout(.2);assert s.connect_ex(('127.0.0.1',port))!=0
            result=dict(scenario='VISION_CAMERA_FIRST_ENROLLMENT_STOP_RECONCILIATION',outcome='OWNED_PROCESSES_STOPPED_INTENT_PRESERVED',
                sourceProcessesStopped=True,nativeVmStopped=True,listenersReleased=True,unfinishedSourceIntentPreserved=True,
                noVmOrSourceActionsReplayed=True,dnsOwnerStoppedNormally=True,sourceJournalReconciliation='PENDING',nativeAcceptance='NOT_PASSED')
            output=records/'enrollment-boundary-stop-reconciled.json'
            with output.open('x') as stream:
                os.fchmod(stream.fileno(),0o600);json.dump(result,stream)
            print(json.dumps(result),flush=True)
            return 0
        assert pending['initialManual'] is True and pending['target']=='test' and pending['previous'] is None
        assert pending['phase']=='RESET_CONFIRMED' and state['currentVehicle'] is None
        assert source['trust']['onboarding']['state']=='PENDING'
        guest=r'''import json,pathlib,subprocess
p=pathlib.Path('/var/aos/workdirs/sm/runtimes/systemd-slot-camera-access')
tx=p/'state/transaction.json';raw=tx.read_bytes();transaction=json.loads(raw)
assert transaction['schemaVersion']==2 and transaction['phase']=='waiting-for-safe-stop'
assert transaction['operation']=='install-or-replace' and transaction['hasPrevious'] is False
assert not (p/'state/installed.json').exists() and not (p/'active').is_symlink()
assert not (p/'demo-inputs/viss-update-binding').exists()
assert not pathlib.Path('/run/systemd/system/aos-sm.service.d/85-democtl-viss-mtls.conf').exists()
subprocess.run(['/usr/libexec/aos-camera-access-store-check','verify'],check=True,capture_output=True,timeout=10)
assert tx.read_bytes()==raw
print(json.dumps(dict(componentPhase='waiting-for-safe-stop',firstInstall=True,installedComponentAbsent=True,
 runtimeEnrollmentAbsent=True,storeVerified=True,transactionUnchanged=True)))
'''
        done=subprocess.run(ssh_command(access_path(native,'test'),item['sshPort'],5),
            input="python3 - <<'BOUNDARY'\n"+guest+"\nBOUNDARY\n",text=True,capture_output=True,timeout=25)
        assert done.returncode==0
        result['boundary']=json.loads(done.stdout)
        # Same journaled initialization operation, normal physical Safe Stop.
        # The Source cancellation owner requires SAFE_STOP, not MANUAL_READY.
        intent=records/'enrollment-boundary-stop-intent.json'
        if preserve_unfinished:
            before_intent=json.loads(intent.read_bytes())
            assert before_intent==dict(action='NORMAL_SAFE_STOP_AND_SOURCE_CANCEL',operationId=pending['id'],unitId=item['unitId'])
        else:
            assert not intent.exists()
            with intent.open('x') as stream:
                import os
                os.fchmod(stream.fileno(),0o600)
                json.dump(dict(action='NORMAL_SAFE_STOP_AND_SOURCE_CANCEL',operationId=pending['id'],unitId=item['unitId']),stream)
        try:
            if preserve_unfinished:
                # A stationary MANUAL_READY enrollment cannot satisfy the
                # existing Source cancellation's SAFE_STOP phase. Do not forge
                # completion or erase the pending intent. Close only its exact
                # process owners, retaining the journal for the design repair.
                with env._writer(),app.source_service.driver.operation():
                    frame=app.source_service.driver.rpc(source,'status',pending['id'])
                    assert frame['operationId']==pending['id'] and frame['held'] and frame['fresh']
                    assert frame['phase']=='MANUAL_READY' and frame['frame']['speedKmh']<=.5 and frame['frame']['brake']>=.99
                    app.source_service.driver.stop(source)
                    assert not any(app.source_service.driver.live_process(source[n]) for n in ('runnerCommand','simulatorCommand'))
                    current=read_json(native/JOURNAL)
                    assert current['source']==source
                    stopped=vm._stop(current,'test',150)
                    vm._save(current)
                result['cleanup']['sourceProcessesStopped']=True
                result['sourceJournalReconciliation']='PENDING_INITIALIZATION_PRESERVED_NOT_STOPPED_STATE'
                result['unfinishedSourceIntentPreserved']=read_json(native/JOURNAL)['source']==source
            else:
                with env._writer(),app.source_service.driver.operation():
                    frame=app.source_service.driver.rpc(source,'status',pending['id'])
                    assert frame['operationId']==pending['id'] and frame['held'] and frame['fresh']
                    assert frame['phase']=='MANUAL_READY' and frame['frame']['speedKmh']<=.5 and frame['frame']['brake']>=.99
                    app.source_service.driver.rpc(source,'safe_stop',pending['id'])
                    app.source_service.driver.wait(source,pending['id'],'SAFE_STOP')
                app.source_service.simulation('stop',target='test')
                WorkspaceService(env,app.source_service.driver).execute('close')
                result['cleanup']['sourceStopped']=True
                stopped=vm.execute('stop','test',timeout=150)
            result['cleanup']['nativeVmStopped']=(stopped.get('vehicles',{}).get('test') or stopped)['state']=='COMPLETED'
            import socket
            released=True
            for port in (12022,2000,18080,16443,18053):
                with socket.socket() as s:
                    s.settimeout(.2);released &= s.connect_ex(('127.0.0.1',port))!=0
            result['cleanup']['listenersReleased']=released
            result['cleanup']['retainedJournalsUnchanged']=all((root/JOURNAL).read_bytes()==raw for root,raw in retained.items())
            if all(result['cleanup'].values()):result['outcome']='BOUNDARY_CONFIRMED_PROCESSES_STOPPED' if preserve_unfinished else 'BOUNDARY_CONFIRMED_OWNERS_STOPPED'
        except Exception as error:
            import re
            code=re.match('[A-Z][A-Z0-9_]*',str(error))
            result['code']=code.group(0) if code else type(error).__name__
        finally:
            result['seconds']=round(time.monotonic()-began,2)
            import os
            output=records/'enrollment-boundary-result.json';temporary=output.with_suffix('.pending')
            with temporary.open('x') as stream:
                os.fchmod(stream.fileno(),0o600);json.dump(result,stream);stream.flush();os.fsync(stream.fileno())
            os.replace(temporary,output)
            print(json.dumps(result),flush=True)
    return 0 if result['outcome'].startswith('BOUNDARY_CONFIRMED_') else 1


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config',type=Path);p.add_argument('--remote-context',type=Path)
    p.add_argument('--preserve-unfinished',action='store_true')
    p.add_argument('--collect-stopped',action='store_true')
    a=p.parse_args()
    if a.remote_context:return remote(a.remote_context,a.preserve_unfinished,a.collect_stopped)
    assert a.config
    from vision_vm_campaign import configuration
    import remote_harness as h
    c=configuration(a.config);t=c['transport'];q=shlex.quote
    records=Path(c['records'])/'native-camera-06';target=Path(c['remoteRoot'])/records.name
    previous=json.loads((records/'result.json').read_bytes())
    assert previous['outcome']=='NOT_COMPLETE' and previous['code']=='EnvironmentError'
    assert previous['cleanup']['retainedJournalsUnchanged'] is True
    output='enrollment-boundary-stop-reconciled.json' if a.collect_stopped else 'enrollment-boundary-result.json'
    assert not (records/output).exists()
    files=[Path(__file__).resolve()]
    options=h.ssh_args(t)[1:-1];options.remove('-T');i=options.index('-b');options[i:i+2]=['-o','BindAddress='+options[i+1]]
    h.run(['/usr/bin/scp',*options,*map(str,files),t['user']+'@'+t['host']+':'+str(target)+'/'],timeout=30)
    python=c['main']['packageRoot']+'/demo-artifacts/aosedge-sdv-demo/host-runtime/python/bin/python3.12'
    value=h.remote(t,q(python)+' -B '+q(str(target/files[0].name))+' --remote-context '+q(str(target/'context.json'))+
        (' --preserve-unfinished' if a.preserve_unfinished else '')+(' --collect-stopped' if a.collect_stopped else ''),timeout=220)
    result=json.loads(value);h.atomic(records/output,result);print(json.dumps(result))
    return 0 if result['outcome'].startswith(('BOUNDARY_CONFIRMED_','OWNED_PROCESSES_STOPPED_')) else 1


if __name__=='__main__':raise SystemExit(main())
