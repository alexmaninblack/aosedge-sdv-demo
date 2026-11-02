#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Normal same-store Camera .1.2 delivery; no reset, rootfs write or Main access."""
import argparse
import gzip
import io
import json
from pathlib import Path
import shlex
import subprocess
import sys
import tarfile
import time
import traceback
from uuid import uuid4
import remote_harness as h


def worker(path):
    c=json.loads(path.read_bytes());records=path.parent;result=dict(outcome='NOT_COMPLETE',phases=[],cleanup={},cloudMutation=False)
    vm=app=native=None;attempted=confirmed=source_started=False;retained={};began=time.monotonic()
    def phase(name,action):
        print(json.dumps(dict(stage=name,state='STARTED')),flush=True);start=time.monotonic();value=action()
        h.atomic(records/(name+'.json'),dict(seconds=round(time.monotonic()-start,2),facts=value));result['phases'].append(dict(stage=name,seconds=round(time.monotonic()-start,2)))
        print(json.dumps(dict(stage=name,state='COMPLETE')),flush=True);return value
    try:
        for name,pin in c['files'].items():h.require(h.digest(records/name)==pin,'CAMERA_UPDATE_INPUT_CHANGED')
        package=Path(c['main']['packageRoot']);bundle=Path(c['host']['bundle']);h.require(h.digest(package/'application-manifest.json')==c['main']['manifestSha256'],'CAMERA_BASE_CHANGED')
        sys.path.insert(0,str(package/'aosedge-sdv-demo/apps/demo-orchestrator/src'))
        import aosedge_demo_orchestrator
        from aosedge_demo_orchestrator import runtime_paths
        tooling=bundle/'Contents/Resources/tooling/aosedge-sdv-demo/apps/demo-orchestrator/src';aosedge_demo_orchestrator.__path__.insert(0,str(tooling/'aosedge_demo_orchestrator'))
        from aosedge_demo_orchestrator import vision_bootstrap as v
        from aosedge_demo_orchestrator.environment import EnvironmentService,JOURNAL
        from aosedge_demo_orchestrator.application import DemoOrchestrator
        from aosedge_demo_orchestrator.vm import VMService,access_path
        from aosedge_demo_orchestrator.guest_access import ssh_command
        from aosedge_demo_orchestrator.status import load_configuration
        from aosedge_demo_orchestrator.cloud_runtime import launch
        from aosedge_demo_orchestrator.cloud_connection import selected_domain,cloud_binding
        from aosedge_demo_orchestrator.workspace import WorkspaceService
        bootstrap=v.verify(bundle,c['main']['manifestSha256']);h.require(bootstrap.manifest_sha256==c['host']['manifestSha256'],'CAMERA_HOST_CHANGED')
        native=Path.home()/v.INSTANCE_NAME;state=json.loads((native/JOURNAL).read_bytes());item=state['vehicles']['test']
        h.require(item['unitId']=='af6d074a-6ce1-49ba-b613-0476e7b6d1b5' and item['localVmId']=='89273f16-4be0-4b22-b4cb-58d08533c8bc'
            and item['runtime']['state']==state['source']['state']=='STOPPED','SAME_IDLE_VISION_REQUIRED')
        retained={Path.home()/n:(Path.home()/n/JOURNAL).read_bytes() for n in v.RETAINED_INSTANCE_NAMES}
        with runtime_paths.installed_session(native):
            env=EnvironmentService(catalog=v.SignedVisionCatalog(bootstrap),vm_profile=v.VM_PROFILE);vm=VMService(env);app=DemoOrchestrator(environment_service=env,vm_service=vm)
            config=load_configuration(native);sdk,sdk_env=launch(native,config['cloudPython'],'unit_cloud.py')
            payload=records/'camera-access-0.1.2.tar.gz'
            request=dict(servicesPacket=True,cloudDomain=selected_domain(state),oemOwner=cloud_binding(state)['ownerId'],
                oemCredential=str(config['cloudProfiles']['oem-delivery']['credential']),
                permanentDelivery=dict(authorized=True,recoveryFirst=True,rootfsVersion='6.1.1-vision-camera.6',cameraVersion='0.1.2',perceptionVersion='0.1.1',assessmentVersion='0.1.1'),
                componentType='aos-vision-vm-1.0.0-main-qemuarm64-camera-access',version='0.1.2',payload=str(payload),payloadSha256=c['camera']['sha256'],payloadBytes=c['camera']['bytes'],
                vehicles=dict(test={k:item[k] for k in ('unitId','systemUid','unitSetId','nodeId')}))
            request['vehicles']['test']['nodeHardwareId']=item['cloud']['identity']['nodeHardwareId']
            def component(action,**extra):
                done=subprocess.run([sdk[0],'-I','-B',str(records/'vision_permanent_component_cloud.py'),str(tooling)],input=json.dumps(dict(request,action=action,**extra)),capture_output=True,text=True,env=sdk_env,timeout=600)
                h.require(done.returncode==0 and len(done.stdout)<262144,'CAMERA_UPDATE_SDK_UNAVAILABLE');value=json.loads(done.stdout)
                h.require(value.get('ok') is True,value.get('reason','CAMERA_UPDATE_SDK_FAILED'));return value['data']
            def guest():
                code=(records/'vision_delivery_guest.py').read_text()+"\nprint(json.dumps(snapshot()))\n"
                done=subprocess.run(ssh_command(access_path(native,'test'),item['sshPort'],5),input='python3 -c '+shlex.quote(code)+'\n',capture_output=True,text=True,timeout=40)
                h.require(done.returncode==0,'CAMERA_NATIVE_STATUS_UNAVAILABLE');return json.loads(done.stdout)
            phase('same-retained-vision-start',lambda:vm.execute('start','test',timeout=150))
            before=phase('native-camera-before-update',guest)
            h.require(before['rootfsVersion']=='VERSION="6.1.1-vision-camera.6"' and before['camera']['version']=='0.1.1' and before['enforcing'],'CAMERA_NATIVE_BASELINE_CHANGED')
            source_started=True;phase('normal-source-start',lambda:app.source_service.simulation('start',target='test'))
            phase('normal-source-enrollment',app.source_service.initialize_test)
            def safe_stop():
                identity=str(uuid4())
                with env._writer(),app.source_service.driver.operation():
                    state=json.loads((native/JOURNAL).read_bytes());driver=app.source_service.driver;source=state['source']
                    driver.rpc(source,'safe_stop',identity);driver.wait(source,identity,'SAFE_STOP')
                    driver.rpc(source,'release',identity);frame=driver.ready(state)
                    h.require(frame.get('fresh') and not frame.get('held') and frame['frame'].get('activeMode')=='SAFE_STOP'
                        and frame['frame']['speedKmh']<=.5 and frame['frame']['brake']>=.99,'CAMERA_PHYSICAL_STOP_UNCONFIRMED')
                return dict(physicalSafeStop=True,held=False)
            phase('physical-safe-stop-for-native-update',safe_stop)
            catalog=phase('camera-publication-before',lambda:component('status'));h.require(catalog['publication']['stage']=='NOT_PUBLISHED' and not catalog['versions'],'CAMERA_PUBLICATION_EXISTS_RECONCILE')
            request['componentTitle']=catalog['componentTitle'];signed=phase('camera-oem-sign',lambda:component('sign',output=str(records/'camera-oem-0.1.2.tar.gz')))
            h.atomic(records/'camera-upload-intent.json',dict(attemptStarted=True,version='0.1.2',payloadSha256=c['camera']['sha256'],bundleSha256=signed['sha256']))
            attempted=True;result['cloudMutation']=True
            uploaded=phase('camera-upload',lambda:component('upload',bundle=str(records/'camera-oem-0.1.2.tar.gz'),expectedSha256=signed['sha256']));request['deploymentId']=uploaded['deploymentId']
            end=time.monotonic()+180
            while True:
                published=component('status');h.atomic(records/'camera-publication-latest.json',published)
                if published['publication']['stage']=='READY':break
                h.require(published['publication']['stage']=='PROCESSING' and time.monotonic()<end,'CAMERA_PUBLICATION_NOT_READY');time.sleep(2)
            h.atomic(records/'camera-send-intent.json',dict(attemptStarted=True,versionId=published['publication']['versionId']))
            phase('normal-camera-delivery',lambda:component('send'))
            end=time.monotonic()+150
            while True:
                after=guest();cloud=component('status');h.atomic(records/'camera-native-latest.json',after)
                if after['camera']['version']=='0.1.2' and any((r.get('installed_component') or {}).get('version')=='0.1.2' and not r.get('pending_component') for r in cloud['unit']['components'] or []):break
                h.require(time.monotonic()<end,'CAMERA_NATIVE_UPDATE_NOT_CONFIRMED');time.sleep(2)
            h.require(after['cameraPayloadSha256']==c['camera']['entrySha256'] and after['enforcing'],'CAMERA_NATIVE_BYTES_OR_POLICY_CHANGED')
            for key in ('machineId','rootfsVersion','cameraStoreUuid','provisioned','authorizedKeysPresent','rootHomeMount','sshHostKeyMounts'):
                h.require(after[key]==before[key],'CAMERA_RETAINED_DATA_CHANGED')
            confirmed=True;result.update(outcome='PASS_SAME_VISION_NATIVE_CAMERA_012_UPDATE',sameVm=True,sameCameraStore=True,dataPreserved=True,
                rootfsVersion='6.1.1-vision-camera.6',cameraVersion='0.1.2',rootfsCloudInventory='KNOWN_OMISSION_NOT_PASSED')
    except Exception as error:
        value=str(error);result.update(code=value if value.isupper() and len(value)<180 else type(error).__name__,failureLine=traceback.extract_tb(error.__traceback__)[-1].lineno)
    finally:
        if vm is not None:
            if attempted and not confirmed:result['cleanup']['activeUpdatePreservedForReconciliation']=True;result['cleanup']['sourceStopped']=False
            else:
                with runtime_paths.installed_session(native):
                    if source_started:app.source_service.simulation('stop',target='test');WorkspaceService(env,app.source_service.driver).execute('close')
                    result['cleanup']['visionStopped']=vm.execute('stop','test',timeout=150)['vehicles']['test']['state']=='COMPLETED'
                result['cleanup']['sourceStopped']=json.loads((native/JOURNAL).read_bytes())['source']['state']=='STOPPED'
            result['cleanup']['retainedJournalsUnchanged']=all((p/JOURNAL).read_bytes()==raw for p,raw in retained.items())
        result['seconds']=round(time.monotonic()-began,2)
        if 'code' in result or not result['cleanup'] or not all(result['cleanup'].values()):result['outcome']='NOT_COMPLETE'
        h.atomic(records/'result.json',result);print(json.dumps(result),flush=True)
    return 0 if result['outcome'].startswith('PASS_') else 1


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--config',type=Path);parser.add_argument('--worker',type=Path);a=parser.parse_args()
    if a.worker:return worker(a.worker)
    from vision_vm_campaign import configuration
    c=configuration(a.config);root=Path(__file__).resolve().parents[2];build=Path('/Volumes/SDV-Dev/sdv/build/vision-services/camera-oem-01')
    h.require(not build.exists(),'CAMERA_ARTIFACT_EXISTS_RECONCILE');build.mkdir(mode=0o700)
    platform=root.parent/'vision-camera-platform';revision=h.run(['git','-C',str(platform),'rev-parse','HEAD']).strip()
    h.require(revision=='9d540803bbebef1d1270471d5c4e5233301b6547' and not h.run(['git','-C',str(platform),'diff','HEAD','--name-only']),'FROZEN_CAMERA_SOURCE_REQUIRED')
    subprocess.run([sys.executable,'-B',str(platform/'tools/build_camera_access_payload.py'),'--version','0.1.2','--output',str(build/'payload.tar')],check=True,capture_output=True)
    raw=(build/'payload.tar').read_bytes()
    with tarfile.open(fileobj=io.BytesIO(raw)) as archive:entry=archive.extractfile('bin/camera-access').read()
    import hashlib
    payload=build/'camera-access-0.1.2.tar.gz';payload.write_bytes(gzip.compress(raw,mtime=0));payload.chmod(0o444)
    camera=dict(version='0.1.2',bytes=payload.stat().st_size,sha256=h.digest(payload),entrySha256=hashlib.sha256(entry).hexdigest(),platformRevision=revision)
    h.atomic(build/'artifact.json',camera)
    prior=json.loads((Path(c['records'])/'permanent-rootfs-close-01/result.json').read_bytes())
    h.require(prior['rootfsInstalled'] and prior['rootfsVersion']=='6.1.1-vision-camera.6' and all(prior['cleanup'].values()),'NATIVE_COMMITTED_IDLE_ROOTFS_REQUIRED')
    name='vision-services-camera-update-01';records=Path(c['records'])/name;remote=Path(c['remoteRoot'])/name
    h.require(not records.exists(),'CAMERA_UPDATE_EXISTS_RECONCILE');records.mkdir(mode=0o700)
    files=[Path(__file__).resolve(),Path(__file__).with_name('vision_permanent_component_cloud.py'),Path(__file__).with_name('vision_delivery_guest.py'),Path(__file__).with_name('remote_harness.py'),root/'scripts/distribution/installation_inputs.py',payload]
    context=dict(main=c['main'],host=json.loads((Path(c['records'])/'vision-services-host-04/result.json').read_bytes()),camera=camera,files={p.name:h.digest(p) for p in files})
    h.atomic(records/'context.json',context);h.remote(c['transport'],'umask 077\nmkdir '+shlex.quote(str(remote)),timeout=15)
    options=h.ssh_args(c['transport'])[1:-1];options.remove('-T');i=options.index('-b');options[i:i+2]=['-o','BindAddress='+options[i+1]]
    h.run(['/usr/bin/scp',*options,*map(str,files),str(records/'context.json'),c['transport']['user']+'@'+c['transport']['host']+':'+str(remote)+'/'],timeout=30)
    py=c['main']['packageRoot']+'/demo-artifacts/aosedge-sdv-demo/host-runtime/python/bin/python3.12'
    proc=subprocess.Popen(h.ssh_args(c['transport'])+[shlex.join([py,'-B',str(remote/files[0].name),'--worker',str(remote/'context.json')])],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    with (records/'progress.jsonl').open('x') as stream:
        for line in proc.stdout:h.require(stream.tell()<1024**2,'PROGRESS_LIMIT');stream.write(line);stream.flush();print(line.strip(),flush=True)
    exit_code=proc.wait(timeout=15);diagnostic=proc.stderr.read(8192)
    code='import pathlib,json;p=pathlib.Path('+repr(str(remote))+');print(json.dumps({f.name:json.loads(f.read_bytes()) for f in p.glob("*.json") if f.name!="context.json" and f.stat().st_size<2097152}))'
    for name,value in json.loads(h.remote(c['transport'],shlex.join([py,'-I','-B','-c',code]),timeout=20)).items():h.atomic(records/name,value)
    h.atomic(records/'transport.json',dict(exit=exit_code,stderrPresent=bool(diagnostic)));return exit_code


if __name__=='__main__':raise SystemExit(main())
