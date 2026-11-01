#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Prove missing image presets transiently, then native-revert unconfirmed trial."""
import json
import hashlib
import os
from pathlib import Path
import re
import shlex
import socket
import subprocess
import sys
import time


def require(ok,code):
    if not ok:raise ValueError(code)


def digest(path):
    value=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(4*1024**2),b''):value.update(block)
    return value.hexdigest()


def atomic(path,value):
    temporary=path.with_suffix('.pending');fd=os.open(temporary,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    with os.fdopen(fd,'w') as stream:json.dump(value,stream,indent=2);stream.flush();os.fsync(stream.fileno())
    os.replace(temporary,path)


def console(serial,password,script):
    result=dict(authenticated=False);stage='prompt';buffer='';end=time.monotonic()+35
    with socket.socket(socket.AF_UNIX) as connection:
        connection.settimeout(1);connection.connect(str(serial));connection.sendall(b'\r')
        while time.monotonic()<end:
            try:chunk=connection.recv(8192)
            except socket.timeout:continue
            if not chunk:break
            buffer=(buffer+chunk.decode(errors='replace'))[-65536:]
            prompt=re.sub(r'\x1b(?:\[[0-?]*[ -/]*[@-~]|[78])','',buffer)
            if stage=='prompt' and re.search(r'login: *$',prompt):
                connection.sendall(b'root\r');stage='password';buffer=''
            elif stage=='password' and re.search(r'[Pp]assword: *$',prompt):
                connection.sendall(password.encode()+b'\r');stage='shell';buffer=''
            elif stage in ('prompt','password','shell') and re.search(r'(?:^|[\r\n])root@[A-Za-z0-9_.-]+:(?:~|/)[^\r\n]*# *$',prompt):
                result['authenticated']=True
                connection.sendall(('HISTFILE=/dev/null; stty -echo; python3 -c '+shlex.quote(script)+'; stty echo; exit\r').encode())
                stage='read';buffer=''
            elif stage=='shell' and 'Login incorrect' in prompt:raise ValueError('CONSOLE_AUTH_DENIED')
            if stage=='read':
                for line in buffer.splitlines():
                    if line.startswith('VISION_RECOVERY_FACTS='):
                        try:return dict(result,facts=json.loads(line.split('=',1)[1]))
                        except json.JSONDecodeError:continue
    return dict(result,stage=stage,code='CONSOLE_RESULT_UNCONFIRMED')


GUARD=r'''
import json,pathlib,subprocess
assert pathlib.Path('/etc/machine-id').read_text().strip()==HARDWARE
root=next(line.split() for line in pathlib.Path('/proc/mounts').read_text().splitlines() if line.split()[1]=='/')
p=pathlib.Path('/var/aos/workdirs/sm/runtimes/rootfs')
assert root[2]=='squashfs' and pathlib.Path('/etc/aos/version').read_text().strip()=='VERSION="6.1.1-vision-camera.4"'
assert {n for n in ('do_update','updated','do_apply','failed') if (p/n).exists()}=={'do_update','updated'}
assert (p/'pending_instance.json').exists()
'''


def main():
    context=Path(sys.argv[1]);c=json.loads(context.read_bytes());records=context.parent
    password=json.loads(sys.stdin.read(8193))['password']
    require(isinstance(password,str) and not any(v in password for v in '\r\n\x00'),'CONSOLE_INPUT_INVALID')
    require(not (records/'result.json').exists(),'RECOVERY_ATTEMPT_EXISTS_RECONCILE')
    result=dict(scenario='VISION_UNCONFIRMED_ROOTFS_NATIVE_REVERT',outcome='NOT_COMPLETE',cleanup={},
        rootfsWrites=False,checkpointRestored=False,cloudMutation=False,requestReplayed=False)
    began=time.monotonic();native=None;vm=None;retained={};reverted=False
    try:
        package=Path(c['main']['packageRoot']);bundle=Path(c['bundle'])
        require(digest(package/'application-manifest.json')==c['main']['manifestSha256'],'BASE_CHANGED')
        for name,pin in c['files'].items():require(digest(records/name)==pin,'RECOVERY_INPUT_CHANGED')
        subprocess.run(['codesign','--verify','--deep','--strict','-R',
            '=identifier "org.aosedge.sdvlab.vision.bootstrap" and anchor apple generic and certificate leaf[subject.OU] = "3NF57VKB3V"',
            str(bundle)],check=True,capture_output=True,timeout=120)
        sys.path.insert(0,str(package/'aosedge-sdv-demo/apps/demo-orchestrator/src'))
        import aosedge_demo_orchestrator
        from aosedge_demo_orchestrator import runtime_paths
        tooling=bundle/'Contents/Resources/tooling/aosedge-sdv-demo/apps/demo-orchestrator/src'
        aosedge_demo_orchestrator.__path__.insert(0,str(tooling/'aosedge_demo_orchestrator'))
        from aosedge_demo_orchestrator import vision_bootstrap as v
        from aosedge_demo_orchestrator.environment import EnvironmentService,JOURNAL
        from aosedge_demo_orchestrator.vm import VMService,access_path
        from aosedge_demo_orchestrator.guest_access import ssh_command
        from aosedge_demo_orchestrator.status import load_configuration,read_json
        from aosedge_demo_orchestrator.cloud_connection import cloud_binding,selected_domain
        from aosedge_demo_orchestrator.cloud_runtime import launch
        verified=v.verify(bundle,c['main']['manifestSha256']);require(verified.manifest_sha256==c['bootstrapManifestSha256'],'BOOTSTRAP_CHANGED')
        native=Path.home()/v.INSTANCE_NAME;before=read_json(native/JOURNAL);item=before['vehicles']['test']
        require(item['runtime']['state']=='RUNNING' and before['source']['state']=='STOPPED','EXACT_ACTIVE_TRIAL_REQUIRED')
        identity={k:item[k] for k in ('unitId','nodeId','localVmId','overlay')}
        retained={Path.home()/n:(Path.home()/n/JOURNAL).read_bytes() for n in v.RETAINED_INSTANCE_NAMES}
        old=Path(c['failedAttempt']);failed=json.loads((old/'result.json').read_bytes())
        require(failed['code']=='NATIVE_ROOTFS_COMMIT_NOT_CONFIRMED' and failed['cloudMutation']
            and not failed['rootfsInstalled'],'EXACT_UNCONFIRMED_FOTA_REQUIRED')
        baseline=json.loads((old/'native-before-update.json').read_bytes())['facts']
        previous_context=json.loads((old/'context.json').read_bytes())
        require(digest(old/'vision_permanent_component_cloud.py')==previous_context['files']['vision_permanent_component_cloud.py'],'ORIGINAL_COMPONENT_ADAPTER_CHANGED')
        with runtime_paths.installed_session(native):
            env=EnvironmentService(catalog=v.SignedVisionCatalog(verified),vm_profile=v.VM_PROFILE);vm=VMService(env)
            config=load_configuration(native);sdk,sdk_env=launch(native,config['cloudPython'],'unit_cloud.py')
            request=dict(action='status',componentType='aos-vision-vm-1.0.0-main-qemuarm64-rootfs',version='6.1.1-vision-camera.4',
                oemCredential=str(config['cloudProfiles']['oem-delivery']['credential']),oemOwner=cloud_binding(before)['ownerId'],
                cloudDomain=selected_domain(before),permanentDelivery=previous_context['permanentDelivery'],
                deploymentId=json.loads((old/'rootfs-upload.json').read_bytes())['facts']['deploymentId'],
                vehicles=dict(test={k:item[k] for k in ('unitId','nodeId','systemUid','unitSetId')}))
            request['vehicles']['test']['nodeHardwareId']=item['cloud']['identity']['nodeHardwareId']
            def cloud_status():
                done=subprocess.run([sdk[0],'-I','-B',str(old/'vision_permanent_component_cloud.py'),str(tooling)],
                    input=json.dumps(request),text=True,capture_output=True,env=sdk_env,timeout=40)
                require(done.returncode==0,'RECOVERY_CLOUD_READ_FAILED');value=json.loads(done.stdout)
                require(value.get('ok'),'RECOVERY_CLOUD_IDENTITY_UNCONFIRMED');value=value['data']
                return dict(publicationStage=value['publication']['stage'],unitOnline=value['unit']['online_status'],
                    components=[dict(installedVersion=(r.get('installed_component') or {}).get('version'),
                        pendingVersion=(r.get('pending_component') or {}).get('version'),pendingStatus=r.get('pending_component_status'),
                        errorPresent=bool(r.get('pending_component_error'))) for r in value['unit']['components'] or []])
            atomic(records/'cloud-before-native-revert.json',cloud_status())
            guard=GUARD.replace('HARDWARE',repr(item['localVmId'].replace('-','')))
            # Prevent a diagnostic network start from accidentally confirming
            # the bad trial: hold SM/CM stopped through their normal owners.
            script=guard+r'''
subprocess.run(['systemctl','stop','aos-sm','aos-cm'],check=True,capture_output=True,timeout=30)
assert all(subprocess.run(['systemctl','is-active','--quiet',name],capture_output=True).returncode!=0 for name in ('aos-sm','aos-cm'))
starts={}
for name in ('systemd-networkd','sshd.socket'):
 d=subprocess.run(['systemctl','start',name],capture_output=True,timeout=20);starts[name]=d.returncode
print('VISION_RECOVERY_FACTS='+json.dumps(dict(coreHeldStopped=True,transientStarts=starts,rootfsStillReadOnly='ro' in root[3].split(','),noEnableOrPreset=True)),flush=True)
'''
            proof=console(native/'.run/demo-current/test.serial',password,script);atomic(records/'transient-network-owner-start.json',proof)
            require(proof.get('facts',{}).get('coreHeldStopped'),'TRIAL_HEALTH_OWNER_NOT_HELD')
            probe="python3 -c "+shlex.quote("import json,pathlib;print(json.dumps(dict(machineId=pathlib.Path('/etc/machine-id').read_text().strip(),version=pathlib.Path('/etc/aos/version').read_text().strip())))")+'\n'
            end=time.monotonic()+20;network=None
            while time.monotonic()<end:
                done=subprocess.run(ssh_command(access_path(native,'test'),item['sshPort'],3),input=probe,capture_output=True,text=True,timeout=8)
                if done.returncode==0:network=json.loads(done.stdout);break
                time.sleep(1)
            result['transientNetworkProof']=bool(network and network['machineId']==item['localVmId'].replace('-',''))
            atomic(records/'transient-ssh-continuity.json',dict(sshRestored=result['transientNetworkProof'],noEnrollment=True,noHostPinChange=True))
            atomic(records/'native-reboot-intent.json',dict(attemptStarted=True,unitId=item['unitId'],localVmId=item['localVmId'],
                action='NORMAL_REBOOT_UNCONFIRMED_TRIAL',requiredFlags=['do_update','updated'],doApplyAbsent=True,checkpointRestore=False))
            reboot=guard+r'''
subprocess.run(['systemctl','reboot'],check=True,capture_output=True,timeout=10)
print('VISION_RECOVERY_FACTS='+json.dumps(dict(rebootRequested=True)),flush=True)
'''
            ack=console(native/'.run/demo-current/test.serial',password,reboot);atomic(records/'native-reboot-response.json',ack)
            # A lost console response is observed, never a second reboot.
            guest_code=(records/'vision_delivery_guest.py').read_text()+"\nprint(json.dumps(run('snapshot')))\n"
            end=time.monotonic()+150;after=None
            while time.monotonic()<end:
                done=subprocess.run(ssh_command(access_path(native,'test'),item['sshPort'],4),
                    input="python3 - <<'READ_RECOVERY'\n"+guest_code+"\nREAD_RECOVERY\n",capture_output=True,text=True,timeout=40)
                if done.returncode==0:
                    try:after=json.loads(done.stdout)
                    except json.JSONDecodeError:pass
                    if after and after['rootfsVersion']=='VERSION="6.1.1-vision-camera.3"':break
                time.sleep(2)
            require(after is not None and after['rootfsVersion']==baseline['rootfsVersion'] or
                    after is not None and after['rootfsVersion']=='VERSION="6.1.1-vision-camera.3"','NATIVE_TRIAL_REVERT_NOT_CONFIRMED')
            for key in ('machineId','camera','cameraInstalledMetadataSha256','cameraPayloadSha256','cameraStoreUuid','provisioned',
                        'authorizedKeysPresent','rootHomeMount','sshHostKeyMounts'):
                require(after[key]==baseline[key],'NATIVE_REVERT_DATA_CHANGED')
            require(after['enforcing'] and after['cameraUnit']['ActiveState']=='active','NATIVE_REVERT_SECURITY_FAILED')
            atomic(records/'native-restored-snapshot.json',after)
            # The native owner must have cleared its failed trial transaction.
            check="python3 -c "+shlex.quote("import json,pathlib; p=pathlib.Path('/var/aos/workdirs/sm/runtimes/rootfs'); print(json.dumps(dict(flags=[n for n in ('do_update','updated','do_apply','failed') if (p/n).exists()],pending=(p/'pending_instance.json').exists())))")+'\n'
            end=time.monotonic()+45;state=None
            while time.monotonic()<end:
                done=subprocess.run(ssh_command(access_path(native,'test'),item['sshPort'],4),input=check,capture_output=True,text=True,timeout=10)
                if done.returncode==0:
                    state=json.loads(done.stdout)
                    if not state['flags'] and not state['pending']:break
                time.sleep(2)
            require(state is not None and not state['flags'] and not state['pending'],'NATIVE_REVERT_TRANSACTION_NOT_CLOSED')
            atomic(records/'native-transaction-closed.json',state);atomic(records/'cloud-after-native-revert.json',cloud_status())
            reverted=True;result.update(outcome='PASS_NATIVE_UNCONFIRMED_TRIAL_REVERT',sameVm=True,dataPreserved=True,
                rootfsVersion='6.1.1-vision-camera.3',sshContinuity=True,trialNeverApplied=True)
    except Exception as error:
        value=str(error);result['code']=value if re.fullmatch('[A-Z][A-Z0-9_:,.-]{1,160}',value) else type(error).__name__
    finally:
        password=''
        if vm is not None:
            if reverted:
                try:
                    with runtime_paths.installed_session(native):value=vm.execute('stop','test',timeout=150)
                    result['cleanup']['visionStopped']=value['vehicles']['test']['state']=='COMPLETED'
                except Exception:result['cleanup']['visionStopped']=False
            else:result['cleanup']['visionStopped']=False
            state=read_json(native/JOURNAL)
            result['cleanup']['sameVisionIdentity']=all(state['vehicles']['test'][k]==v for k,v in identity.items())
            result['cleanup']['retainedJournalsUnchanged']=all((p/JOURNAL).read_bytes()==raw for p,raw in retained.items())
            result['cleanup']['sourceStopped']=state['source']['state']=='STOPPED'
        result['seconds']=round(time.monotonic()-began,2)
        if not result['cleanup'] or not all(result['cleanup'].values()):result['outcome']='NOT_COMPLETE'
        atomic(records/'result.json',result);print(json.dumps(result),flush=True)
    return 0 if result['outcome']=='PASS_NATIVE_UNCONFIRMED_TRIAL_REVERT' else 1


if __name__=='__main__':raise SystemExit(main())
