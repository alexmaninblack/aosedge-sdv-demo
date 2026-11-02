#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Same-VM stopped-checkpoint rehearsal before any permanent update."""
import ctypes
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import textwrap
import time


def require(ok,code):
    if not ok:raise ValueError(code)


def atomic(path,value):
    temporary=path.with_suffix('.pending')
    fd=os.open(temporary,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    with os.fdopen(fd,'w') as stream:json.dump(value,stream);stream.flush();os.fsync(stream.fileno())
    os.replace(temporary,path)


def swap(source,target):
    # Darwin RENAME_SWAP is one atomic operation and preserves both old inodes.
    # No overwrite/delete fallback; an unsupported filesystem fails closed.
    libc=ctypes.CDLL('/usr/lib/libSystem.B.dylib',use_errno=True)
    function=libc.renameatx_np
    function.argtypes=[ctypes.c_int,ctypes.c_char_p,ctypes.c_int,ctypes.c_char_p,ctypes.c_uint]
    if function(-2,os.fsencode(source),-2,os.fsencode(target),2):
        raise OSError(ctypes.get_errno(),'RECOVERY_ATOMIC_SWAP_FAILED')


def main():
    context=Path(sys.argv[1]);c=json.loads(context.read_bytes());records=context.parent
    require(not (records/'result.json').exists(),'RECOVERY_ATTEMPT_EXISTS_RECONCILE')
    authority=(dict(authorized=True,recoveryFirst=True,rootfsVersion='6.1.1-vision-camera.6',cameraVersion='0.1.2',perceptionVersion='0.1.1',assessmentVersion='0.1.1')
        if c.get('servicesPacket') else dict(authorized=True,recoveryFirst=True,rootfsVersion='6.1.1-vision-camera.4',cameraVersion='0.1.1',readVersion='0.1.4',revokeVersion='0.1.5'))
    require(c.get('permanentDelivery')==authority,'PERMANENT_PACKET_AUTHORITY_REQUIRED')
    package=Path(c['main']['packageRoot']);bundle=Path(c['bundle'])
    require(hashlib.sha256((package/'application-manifest.json').read_bytes()).hexdigest()==c['main']['manifestSha256'],'BASE_PROGRAM_CHANGED')
    for name,digest in c['files'].items():require(hashlib.sha256((records/name).read_bytes()).hexdigest()==digest,'RECOVERY_TRANSFER_CHANGED')
    subprocess.run(['codesign','--verify','--deep','--strict','-R',
        '=identifier "org.aosedge.sdvlab.vision.bootstrap" and anchor apple generic and certificate leaf[subject.OU] = "3NF57VKB3V"',str(bundle)],check=True,capture_output=True,timeout=120)
    sys.path.insert(0,str(package/'aosedge-sdv-demo/apps/demo-orchestrator/src'))
    import aosedge_demo_orchestrator
    from aosedge_demo_orchestrator import runtime_paths
    aosedge_demo_orchestrator.__path__.insert(0,str(bundle/'Contents/Resources/tooling/aosedge-sdv-demo/apps/demo-orchestrator/src/aosedge_demo_orchestrator'))
    from aosedge_demo_orchestrator import vision_bootstrap as v
    from aosedge_demo_orchestrator.environment import EnvironmentService,JOURNAL
    from aosedge_demo_orchestrator.vm import VMService,access_path
    from aosedge_demo_orchestrator.guest_access import ssh_command
    bootstrap=v.verify(bundle,c['main']['manifestSha256']);require(bootstrap.manifest_sha256==c['bootstrapManifestSha256'],'BOOTSTRAP_CHANGED')
    native=Path.home()/v.INSTANCE_NAME
    retained={Path.home()/n:(Path.home()/n/JOURNAL).read_bytes() for n in v.RETAINED_INSTANCE_NAMES}
    initial=json.loads((native/JOURNAL).read_bytes());item=initial['vehicles']['test']
    if c.get('servicesPacket'):
        require(item['unitId']=='af6d074a-6ce1-49ba-b613-0476e7b6d1b5' and item['localVmId']=='89273f16-4be0-4b22-b4cb-58d08533c8bc','SERVICES_RECOVERY_TARGET_CHANGED')
    require(item['runtime']['state']=='STOPPED' and initial['source']['state']=='STOPPED' and not initial['source'].get('operation'),'RECOVERY_IDLE_VISION_REQUIRED')
    identity={k:item[k] for k in ('localVmId','unitId','nodeId','overlay','mac','sshPort')}
    result=dict(scenario='VISION_STOPPED_CHECKPOINT_RECOVERY',outcome='NOT_COMPLETE',phases=[],cleanup={},cloudMutation=False,updateAttempted=False)
    began=time.monotonic();vm=None;backup=None;candidate=None;swapped=False;restored=False
    def phase(name,action):
        print(json.dumps(dict(stage=name,state='STARTED')),flush=True);start=time.monotonic();facts=action()
        atomic(records/(name+'.json'),dict(facts=facts,seconds=round(time.monotonic()-start,2)))
        result['phases'].append(dict(stage=name,seconds=round(time.monotonic()-start,2)))
        print(json.dumps(dict(stage=name,state='COMPLETE')),flush=True);return facts
    with runtime_paths.installed_session(native):
        env=EnvironmentService(catalog=v.SignedVisionCatalog(bootstrap),vm_profile=v.VM_PROFILE)
        vm=VMService(env,progress=lambda msg:print(json.dumps(dict(stage='native-owner',message=str(msg)[:110])),flush=True))
        def start():
            value=vm.execute('start','test',timeout=150);require(value['vehicles']['test']['state']=='COMPLETED','RECOVERY_VM_START_INCOMPLETE')
            return dict(started=True)
        def stop():
            value=vm.execute('stop','test',timeout=150);require(value['vehicles']['test']['state']=='COMPLETED','RECOVERY_VM_STOP_INCOMPLETE')
            return dict(stopped=True)
        def guest(action):
            code=(records/'vision_delivery_guest.py').read_text()+'\nprint(json.dumps(run('+repr(action)+')))\n'
            wrapper='import json,traceback\ntry:\n'+textwrap.indent(code,' ')+'\nexcept Exception as error:\n print(json.dumps(dict(probeError=type(error).__name__,line=traceback.extract_tb(error.__traceback__)[-1].lineno)))\n'
            done=subprocess.run(ssh_command(access_path(native,'test'),item['sshPort'],5),input="python3 - <<'RECOVERY_PROOF'\n"+wrapper+"\nRECOVERY_PROOF\n",capture_output=True,text=True,timeout=45)
            require(done.returncode==0,'RECOVERY_GUEST_PROBE_FAILED');value=json.loads(done.stdout)
            if 'probeError' in value:
                atomic(records/'probe-error.json',value);raise ValueError('RECOVERY_GUEST_PROBE_ERROR')
            return value
        try:
            phase('baseline-native-start',start);baseline=phase('baseline-native-identity',lambda:guest('snapshot'))
            require(baseline['machineId']==item['localVmId'].replace('-','') and baseline['provisioned'] and baseline['enforcing'] and not baseline['markerPresent'],'RECOVERY_BASELINE_INVALID')
            phase('baseline-native-stop',stop)
            overlay=native/item['overlay'];checkpoint=records/'checkpoint';checkpoint.mkdir(mode=0o700)
            backup=checkpoint/'before-update.qcow2';candidate=overlay.with_name('vision-recovery-promotion.pending')
            def stopped():
                state=json.loads((native/JOURNAL).read_bytes())
                require(state['vehicles']['test']['runtime']['state']=='STOPPED' and state['source']['state']=='STOPPED'
                    and all(state['vehicles']['test'][k]==val for k,val in identity.items()),'RECOVERY_IDENTITY_OR_OWNER_CHANGED')
                env._owned_file(overlay);env._assert_unheld(overlay)
                require(vm._owned_pid(vm._command(state,'test'),str(overlay)) is None,'RECOVERY_VM_PROCESS_REMAINS')
                return state
            def clone():
                with env._writer():
                    stopped();require(not backup.exists() and not candidate.exists(),'RECOVERY_CHECKPOINT_COLLISION')
                    require(shutil.disk_usage(native).free>3*overlay.stat().st_size+8*1024**3,'RECOVERY_CHECKPOINT_CAPACITY')
                    subprocess.run(['/bin/cp','-c',str(overlay),str(backup)],check=True,capture_output=True,timeout=45);backup.chmod(0o400)
                    subprocess.run(['/usr/bin/cmp','-s',str(overlay),str(backup)],check=True,capture_output=True,timeout=45)
                    require(env._info(overlay)['backing-filename']==env._info(backup)['backing-filename'],'RECOVERY_BACKING_CHANGED')
                    checked=json.loads(env._command(['check','--output=json',str(backup)]));require(checked.get('check-errors',0)==0,'RECOVERY_DISK_CHECK_FAILED')
                    atomic(checkpoint/'binding.json',dict(identity=identity,baseline=baseline,overlay=str(overlay),backup=str(backup)))
                return dict(checkpointCreated=True,byteComparison=True,diskCheck=True,sameBacking=True,privateMode=True)
            phase('stopped-private-checkpoint',clone)
            phase('rehearsal-native-start',start);phase('rehearsal-owned-marker',lambda:guest('marker-create'))
            changed=phase('rehearsal-marker-confirmed',lambda:guest('snapshot'));require(changed['markerPresent'],'RECOVERY_MARKER_NOT_PERSISTED')
            phase('rehearsal-native-stop',stop)
            def restore():
                nonlocal swapped,restored
                with env._writer():
                    stopped();require(not candidate.exists(),'RECOVERY_PROMOTION_COLLISION')
                    subprocess.run(['/bin/cp','-c',str(backup),str(candidate)],check=True,capture_output=True,timeout=45);candidate.chmod(0o600)
                    env._assert_unheld(candidate)
                    atomic(checkpoint/'restore-intent.json',dict(state='PREPARED',identity=identity))
                    swap(overlay,candidate);swapped=True
                    # The pre-restore disk is retained, never overwritten/deleted.
                    candidate.rename(checkpoint/'before-rehearsal-restore.qcow2')
                    atomic(checkpoint/'restore-applied.json',dict(state='APPLIED',sameVm=True,originalPreserved=True))
                    subprocess.run(['/usr/bin/cmp','-s',str(overlay),str(backup)],check=True,capture_output=True,timeout=45)
                    restored=True
                return dict(restored=True,atomicSwap=True,originalDiskPreserved=True,byteComparison=True,journalNotRewritten=True)
            phase('same-vm-checkpoint-restore',restore)
            phase('restored-native-start',start);after=phase('restored-native-identity',lambda:guest('snapshot'))
            fields=('machineId','rootfsVersion','camera','cameraStoreUuid','provisioned','enforcing','authorizedKeysPresent','rootHomeMount','sshHostKeyMounts')
            require(not after['markerPresent'] and all(after[k]==baseline[k] for k in fields),'RECOVERY_GUEST_STATE_CHANGED')
            require(after['cameraUnit']['NRestarts']=='0','RECOVERY_CAMERA_RESTART_STORM')
            atomic(checkpoint/'restore-verified.json',dict(state='VERIFIED',sameVm=True,markerAbsent=True,sshContinuity=True,dataPreserved=True))
            result.update(outcome='PASS_SAME_VM_CHECKPOINT_RECOVERY',sameVm=True,dataPreserved=True,sshContinuity=True,checkpointReady=True)
        except Exception as error:
            message=str(error)
            result['code']=message if isinstance(error,ValueError) and re.fullmatch('[A-Z0-9_]{1,150}',message) else type(error).__name__
        finally:
            try:stop();result['cleanup']['visionStopped']=True
            except Exception:result['cleanup']['visionStopped']=False
            current=json.loads((native/JOURNAL).read_bytes())
            result['cleanup']['sourceStopped']=current['source']['state']=='STOPPED'
            result['cleanup']['sameVisionIdentity']=all(current['vehicles']['test'][k]==val for k,val in identity.items())
            result['cleanup']['retainedJournalsUnchanged']=all((p/JOURNAL).read_bytes()==raw for p,raw in retained.items())
            result['checkpointPreserved']=backup is not None and backup.exists()
            result['restoreApplied']=swapped;result['restoreVerified']=restored
            result['seconds']=round(time.monotonic()-began,2)
            if not all(result['cleanup'].values()):result['outcome']='NOT_COMPLETE'
            atomic(records/'result.json',result)
            print(json.dumps(result),flush=True)
    return 0 if result['outcome'].startswith('PASS_') else 1


if __name__=='__main__':raise SystemExit(main())
