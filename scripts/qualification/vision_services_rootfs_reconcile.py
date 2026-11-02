#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Read-only reconciliation of the already published .6; never uploads/sends."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import shlex
import subprocess
import sys
import time
import traceback
import remote_harness as h


def worker(path):
    c=json.loads(path.read_bytes());records=path.parent;old=Path(c['original'])
    h.require(h.digest(old/'context.json')==c['originalContextSha256'],'ORIGINAL_ROOTFS_CONTEXT_CHANGED')
    original=json.loads((old/'context.json').read_bytes());failure=json.loads((old/'result.json').read_bytes())
    h.require(failure['code']=='CLOUD_HTTP_503' and original['servicesPacket'] is True
        and original['rootfs']['rootfsVersion']=='6.1.1-vision-camera.6','EXACT_ROOTFS_OBSERVATION_FAILURE_REQUIRED')
    for name,pin in original['files'].items():h.require(h.digest(old/name)==pin,'ORIGINAL_ROOTFS_TOOL_CHANGED')
    package=Path(original['main']['packageRoot']);bundle=Path(original['bundle']);native=Path.home()/'SDV-Vision-Camera-Image-Lab-Data'
    h.require(h.digest(package/'application-manifest.json')==original['main']['manifestSha256'],'BASE_CHANGED')
    sys.path.insert(0,str(package/'aosedge-sdv-demo/apps/demo-orchestrator/src'))
    import aosedge_demo_orchestrator
    from aosedge_demo_orchestrator import runtime_paths
    tooling=bundle/'Contents/Resources/tooling/aosedge-sdv-demo/apps/demo-orchestrator/src'
    aosedge_demo_orchestrator.__path__.insert(0,str(tooling/'aosedge_demo_orchestrator'))
    from aosedge_demo_orchestrator import vision_bootstrap as v
    from aosedge_demo_orchestrator.environment import EnvironmentService,JOURNAL
    from aosedge_demo_orchestrator.vm import VMService,access_path
    from aosedge_demo_orchestrator.guest_access import ssh_command
    from aosedge_demo_orchestrator.status import load_configuration
    from aosedge_demo_orchestrator.cloud_runtime import launch
    from aosedge_demo_orchestrator.cloud_connection import selected_domain,cloud_binding
    bootstrap=v.verify(bundle,original['main']['manifestSha256']);h.require(bootstrap.manifest_sha256==original['bootstrapManifestSha256'],'HOST_CHANGED')
    state=json.loads((native/JOURNAL).read_bytes());item=state['vehicles']['test']
    h.require(item['unitId']=='af6d074a-6ce1-49ba-b613-0476e7b6d1b5' and item['localVmId']=='89273f16-4be0-4b22-b4cb-58d08533c8bc'
        and item['runtime']['state']=='RUNNING' and state['source']['state']=='STOPPED','SAME_ACTIVE_VISION_REQUIRED')
    retained={Path.home()/n:(Path.home()/n/JOURNAL).read_bytes() for n in v.RETAINED_INSTANCE_NAMES}
    ns=runpy.run_path(str(old/'vision_permanent_rootfs_worker.py'));code=(old/'vision_delivery_guest.py').read_text()+'\nimport re\n'+ns['OBSERVE']
    with runtime_paths.installed_session(native):
        done=subprocess.run(ssh_command(access_path(native,'test'),item['sshPort'],5),input='python3 -c '+shlex.quote(code)+'\n',capture_output=True,text=True,timeout=45)
        h.require(done.returncode==0,'NATIVE_ROOTFS_READ_UNAVAILABLE');guest=json.loads(done.stdout);h.atomic(records/'guest.json',guest)
        h.require(guest['rootfsVersion']==guest['nativeInstalledVersion']=='6.1.1-vision-camera.6' and not guest['rootfsPending']
            and not guest['updateFlags'] and guest['rootMount']==dict(source='/dev/sda3',filesystem='ext4',readOnly=True)
            and guest['enforcing'] and guest['coreActive'] and guest['ingressShipped'] and not guest['transientProofPresent'],'ROOTFS_NOT_NATIVELY_COMMITTED')
        baseline=json.loads((old/'native-before-update.json').read_bytes())['facts']
        for key in ('machineId','camera','cameraInstalledMetadataSha256','cameraPayloadSha256','cameraStoreUuid','provisioned','authorizedKeysPresent','rootHomeMount','sshHostKeyMounts'):
            h.require(guest[key]==baseline[key],'ROOTFS_RETAINED_DATA_CHANGED')
        config=load_configuration(native);sdk,environment=launch(native,config['cloudPython'],'unit_cloud.py')
        request=dict(action='status',servicesPacket=True,cloudDomain=selected_domain(state),oemOwner=cloud_binding(state)['ownerId'],
            oemCredential=str(config['cloudProfiles']['oem-delivery']['credential']),permanentDelivery=original['permanentDelivery'],
            componentType='aos-vision-vm-1.0.0-main-qemuarm64-rootfs',version='6.1.1-vision-camera.6',
            deploymentId=json.loads((old/'rootfs-upload.json').read_bytes())['facts']['deploymentId'],
            vehicles=dict(test={k:item[k] for k in ('unitId','systemUid','unitSetId','nodeId')}))
        request['vehicles']['test']['nodeHardwareId']=item['cloud']['identity']['nodeHardwareId']
        end=time.monotonic()+180;last=None;confirmed=False
        while time.monotonic()<end:
            done=subprocess.run([sdk[0],'-I','-B',str(old/'vision_permanent_component_cloud.py'),str(tooling)],input=json.dumps(request),capture_output=True,text=True,env=environment,timeout=60)
            h.require(done.returncode==0 and len(done.stdout)<262144,'ROOTFS_STATUS_SDK_UNAVAILABLE');last=json.loads(done.stdout)
            if last.get('ok'):
                h.atomic(records/'cloud.json',last['data'])
                if any((r.get('installed_component') or {}).get('version')=='6.1.1-vision-camera.6' and not r.get('pending_component') for r in last['data']['unit']['components'] or []):confirmed=True;break
                if c.get('closeNativeCommitted'):
                    h.require(last['data']['publication']['stage']=='READY' and last['data']['unit']['online_status']=='Online'
                        and last['data']['unit']['components']==[],'EXACT_ROOTFS_INVENTORY_OMISSION_REQUIRED')
                    break
            else:h.require(last.get('reason') in ('CLOUD_HTTP_503','CLOUD_HTTP_502','CLOUD_HTTP_504'),'ROOTFS_STATUS_UNEXPECTED_FAILURE')
            print(json.dumps(dict(stage='already-published-rootfs-status',state='OBSERVING',guestCommitted=True)),flush=True);time.sleep(5)
        else:raise ValueError('ROOTFS_CLOUD_CONFIRMATION_UNAVAILABLE')
        env=EnvironmentService(catalog=v.SignedVisionCatalog(bootstrap),vm_profile=v.VM_PROFILE);stopped=VMService(env).execute('stop','test',timeout=150)
        h.require(stopped['vehicles']['test']['state']=='COMPLETED','ROOTFS_RECONCILE_STOP_UNCONFIRMED')
    h.require(all((p/JOURNAL).read_bytes()==raw for p,raw in retained.items()),'RETAINED_JOURNALS_CHANGED')
    value=dict(outcome='PASS_RETAINED_NATIVE_ROOTFS_FOTA_RECONCILED' if confirmed else 'NATIVE_ROOTFS_COMMITTED_CLOUD_INVENTORY_MISSING',
        cloudRootfsConfirmed=confirmed,rootfsVersion='6.1.1-vision-camera.6',rootfsInstalled=True,sameVm=True,dataPreserved=True,
        cloudMutation=False,uploadRepeated=False,originalFailurePreserved=True,cleanup=dict(visionStopped=True,sourceStopped=True,retainedJournalsUnchanged=True))
    h.atomic(records/'result.json',value);print(json.dumps(value));return 0


def main():
    p=argparse.ArgumentParser();p.add_argument('--config',type=Path);p.add_argument('--worker',type=Path)
    p.add_argument('--close-native-committed',action='store_true');a=p.parse_args()
    if a.worker:return worker(a.worker)
    from vision_vm_campaign import configuration
    c=configuration(a.config);name='permanent-rootfs-close-01' if a.close_native_committed else 'permanent-rootfs-reconcile-01';records=Path(c['records'])/name;remote=Path(c['remoteRoot'])/name
    h.require(not records.exists(),'ROOTFS_RECONCILE_EXISTS');records.mkdir(mode=0o700)
    files=[Path(__file__).resolve(),Path(__file__).with_name('remote_harness.py'),Path(__file__).parent.parent/'distribution/installation_inputs.py']
    context=dict(original=str(Path(c['remoteRoot'])/'permanent-rootfs-02'),originalContextSha256=h.digest(Path(c['records'])/'permanent-rootfs-02/context.json'),closeNativeCommitted=a.close_native_committed)
    h.atomic(records/'context.json',context);h.remote(c['transport'],'umask 077\nmkdir '+shlex.quote(str(remote)),timeout=15)
    options=h.ssh_args(c['transport'])[1:-1];options.remove('-T');i=options.index('-b');options[i:i+2]=['-o','BindAddress='+options[i+1]]
    h.run(['/usr/bin/scp',*options,*map(str,files),str(records/'context.json'),c['transport']['user']+'@'+c['transport']['host']+':'+str(remote)+'/'],timeout=30)
    py=c['main']['packageRoot']+'/demo-artifacts/aosedge-sdv-demo/host-runtime/python/bin/python3.12'
    proc=subprocess.Popen(h.ssh_args(c['transport'])+[shlex.join([py,'-B',str(remote/files[0].name),'--worker',str(remote/'context.json')])],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    with (records/'progress.jsonl').open('x') as stream:
        for line in proc.stdout:stream.write(line);stream.flush();print(line.strip(),flush=True)
    exit_code=proc.wait(timeout=15);proc.stderr.read(8192)
    code='import pathlib,json;p=pathlib.Path('+repr(str(remote))+');print(json.dumps({f.name:json.loads(f.read_bytes()) for f in p.glob("*.json") if f.name!="context.json"}))'
    for name,value in json.loads(h.remote(c['transport'],shlex.join([py,'-I','-B','-c',code]),timeout=20)).items():h.atomic(records/name,value)
    return exit_code


if __name__=='__main__':raise SystemExit(main())
