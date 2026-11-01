#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""One retained-Vision native OEM/reader campaign; no manufacture or SDK retry."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time


def require(ok,code):
    if not ok:raise ValueError(code)


def atomic(path,value):
    tmp=path.with_suffix('.pending')
    with tmp.open('x') as f:
        os.fchmod(f.fileno(),0o600);json.dump(value,f,indent=2);f.flush();os.fsync(f.fileno())
    os.replace(tmp,path)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--context',type=Path,required=True)
    a=p.parse_args();c=json.loads(a.context.read_bytes());records=a.context.parent
    require(not (records/'result.json').exists(),'CAMERA_ATTEMPT_EXISTS_RECONCILE')
    package=Path(c['main']['packageRoot']);bundle=Path(c['bundle'])
    require(hashlib.sha256((package/'application-manifest.json').read_bytes()).hexdigest()==c['main']['manifestSha256'],'BASE_CHANGED')
    requirement='=identifier "org.aosedge.sdvlab.vision.bootstrap" and anchor apple generic and certificate leaf[subject.OU] = "3NF57VKB3V"'
    subprocess.run(['codesign','--verify','--deep','--strict','-R',requirement,str(bundle)],check=True,capture_output=True,timeout=120)
    sys.path.insert(0,str(package/'aosedge-sdv-demo/apps/demo-orchestrator/src'))
    import aosedge_demo_orchestrator
    from aosedge_demo_orchestrator import runtime_paths
    tooling=bundle/'Contents/Resources/tooling/aosedge-sdv-demo/apps/demo-orchestrator/src'
    aosedge_demo_orchestrator.__path__.insert(0,str(tooling/'aosedge_demo_orchestrator'))
    from aosedge_demo_orchestrator import vision_bootstrap as v
    from aosedge_demo_orchestrator.environment import EnvironmentService,JOURNAL
    from aosedge_demo_orchestrator.vm import VMService,access_path
    from aosedge_demo_orchestrator.units import UnitService
    from aosedge_demo_orchestrator.components import ComponentService
    from aosedge_demo_orchestrator.vision_camera_delivery import package_configuration
    from aosedge_demo_orchestrator.status import load_configuration,read_json,now
    from aosedge_demo_orchestrator.cloud_connection import cloud_binding,selected_domain
    from aosedge_demo_orchestrator.cloud_runtime import launch
    from aosedge_demo_orchestrator.guest_access import ssh_command
    from aosedge_demo_orchestrator.application import DemoOrchestrator
    from aosedge_demo_orchestrator.workspace import WorkspaceService
    bootstrap=v.verify(bundle,c['main']['manifestSha256'])
    require(bootstrap.manifest_sha256==c['bootstrapManifestSha256'],'BOOTSTRAP_CHANGED')
    native=Path.home()/v.INSTANCE_NAME
    retained={Path.home()/n:(Path.home()/n/JOURNAL).read_bytes() for n in ('SDV-Lab-Data','SDV-Vision-Lab-Data')}
    initial=read_json(native/JOURNAL);old=initial['vehicles']['test']
    require(initial['vmProfile']==v.VM_PROFILE and old['runtime']['state']=='STOPPED'
            and old['cloud']['lifecycle']=='ONLINE' and old['cloud']['identity']['model']=='aos-vision-vm','RETAINED_VISION_REQUIRED')
    result=dict(scenario='VISION_NATIVE_CAMERA_ACCESS',outcome='NOT_COMPLETE',phases=[],
        fullVisionE2E='NOT_RUN',gatewayCameraIngress='NOT_RUN',input='OEM_LOCAL_RECORDED_JPEG_FIXTURE',cleanup={})
    began=time.monotonic();source_started=False;producer=None;app=None
    def phase(name,action):
        print(json.dumps(dict(stage=name,state='STARTED')),flush=True);start=time.monotonic()
        value=action();atomic(records/(name+'.json'),dict(seconds=round(time.monotonic()-start,2),facts=value))
        result['phases'].append(dict(stage=name,state='COMPLETE',seconds=round(time.monotonic()-start,2)))
        atomic(records/'progress.json',result);print(json.dumps(dict(stage=name,state='COMPLETE')),flush=True)
        return value
    with runtime_paths.installed_session(native):
        env=EnvironmentService(catalog=v.SignedVisionCatalog(bootstrap),vm_profile=v.VM_PROFILE)
        vm=VMService(env,progress=lambda message:print(json.dumps(dict(stage='native-owner',state=str(message)[:110])),flush=True))
        units=UnitService(vm)
        def guest(code,timeout=20):
            state=read_json(native/JOURNAL);item=state['vehicles']['test']
            command=ssh_command(access_path(native,'test'),item['sshPort'],5)
            script="python3 - <<'VISION_CAMERA_PY'\n"+code+"\nVISION_CAMERA_PY\n"
            done=subprocess.run(command,input=script,text=True,capture_output=True,timeout=timeout)
            require(done.returncode==0,'CAMERA_GUEST_WORKER_FAILED')
            return json.loads(done.stdout)
        try:
            boot=phase('native-start',lambda:vm.execute('start','test',timeout=150))
            require(boot['vehicles']['test']['state']=='COMPLETED','VM_START_INCOMPLETE')
            state=read_json(native/JOURNAL);item=state['vehicles']['test']
            require(item['localVmId']==old['localVmId'] and item['unitId']==old['unitId'],'NATIVE_IDENTITY_CHANGED')
            def online():
                with env._writer():
                    state=read_json(native/JOURNAL)
                    return units._wait(state,'test',lambda value:value and value['online_status']=='Online','CLOUD_ONLINE',timeout=60)
            phase('cloud-online',online)
            state=read_json(native/JOURNAL);item=state['vehicles']['test']
            scope=dict(setupProfile=v.PROFILE,version='0.1.0',vehicles={'test':{
                key:item[key] for key in ('unitId','systemUid','unitSetId','nodeId')}},ownerId=cloud_binding(state)['ownerId'])
            scope['vehicles']['test']['nodeHardwareId']=item['cloud']['identity']['nodeHardwareId']
            before=phase('camera-publication-preflight',lambda:units._cloud('vision-camera-status',purpose='upload',**scope))
            require(before['publication']['stage']=='NOT_PUBLISHED' and not before['versions'],'CAMERA_PUBLICATION_EXISTS_RECONCILE')
            config=load_configuration(native)
            sdk,environment=launch(native,config['cloudPython'],'unit_cloud.py')
            request=dict(scope,cloudDomain=selected_domain(state),oemOwner=cloud_binding(state)['ownerId'],
                spOwner=config['cloudProfiles']['service-provider']['expectedOwnerId'],
                oemCredential=str(config['cloudProfiles']['oem-delivery']['credential']),
                spCredential=str(config['cloudProfiles']['service-provider']['credential']),
                binary=str(records/'vision-camera-probe'),binarySha256=c['probeSha256'])
            require(hashlib.sha256((records/'vision_camera_fixture_cloud.py').read_bytes()).hexdigest()==c['fixtureWorkerSha256'],'FIXTURE_WORKER_CHANGED')
            def fixture(action,**extra):
                done=subprocess.run([sdk[0],'-I','-B',str(records/'vision_camera_fixture_cloud.py'),str(tooling)],
                    input=json.dumps(dict(request,action=action,**extra)),capture_output=True,text=True,env=environment,timeout=100)
                require(done.returncode==0 and len(done.stdout)<131072,'FIXTURE_SDK_UNAVAILABLE')
                value=json.loads(done.stdout);require(value.get('ok'),value.get('reason','FIXTURE_SDK_FAILED'))
                return value['data']
            phase('probe-cloud-preflight',lambda:fixture('preflight'))
            # The existing Source owner, not this diagnostic, owns all CARLA
            # ticks and physical Safe Stop. Inference/fixture never actuates it.
            app=DemoOrchestrator(environment_service=env,vm_service=vm)
            source_started=True
            phase('source-start',lambda:app.source_service.simulation('start',target='test'))
            phase('source-native-authentication',app.source_service.initialize_test)
            component=ComponentService(env)
            prepared=records/'camera-package';prepared.mkdir(mode=0o700)
            (prepared/'camera-access').mkdir()
            raw=(bootstrap.resources/'camera-access/payload.tar').read_bytes()
            compressed=gzip.compress(raw,compresslevel=6,mtime=0)
            (prepared/'camera-access/payload.tar.gz').write_bytes(compressed)
            (prepared/'config.yaml').write_text(json.dumps(package_configuration()))
            signed=prepared/'camera-access-signed.tar.gz'
            signing=phase('camera-oem-sign',lambda:component._worker('sign',directory=str(prepared),output=str(signed)))
            scope.update(bundle=str(signed),expectedSha256=signing['sha256'],payloadSha256=hashlib.sha256(compressed).hexdigest())
            def mutation(name,operation):
                with env._writer():
                    state=read_json(native/JOURNAL)
                    record=state.setdefault('componentOperations',{}).setdefault('0.1.0',dict(
                        version='0.1.0',componentType=v.COMPONENT,ownerId=scope['ownerId'],cloudDomain=selected_domain(state),publicationPath='VERIFICATION_TEST'))
                    require(name not in record,'CAMERA_MUTATION_EXISTS_RECONCILE')
                    record[name]=dict(state='ATTEMPTING',attemptStarted=True,startedAt=now());vm._save(state)
                    value=operation()
                    record[name].update(state='RESPONDED',response=value)
                    if name=='upload':record['deploymentId']=value['deploymentId']
                    vm._save(state)
                    return value
            upload=phase('camera-oem-upload',lambda:mutation('upload',lambda:units._cloud('vision-camera-upload',**scope)))
            scope['deploymentId']=upload['deploymentId']
            deadline=time.monotonic()+150;publication=None
            while time.monotonic()<deadline:
                publication=units._cloud('vision-camera-status',**scope)
                if publication['publication']['stage']=='READY':break
                require(publication['publication']['stage']=='PROCESSING','CAMERA_PUBLICATION_NOT_READY')
                time.sleep(2)
            require(publication['publication']['stage']=='READY','CAMERA_PUBLICATION_TIMEOUT')
            atomic(records/'camera-publication.json',publication)
            scope['updateComponentId']=publication['publication']['versionId']
            phase('camera-native-send',lambda:mutation('send',lambda:units._cloud('vision-camera-send',**scope)))
            # The native OEM owner commits the real A/B transaction. No direct
            # unit start, slot writes, Safe Stop injection or manual crun counts.
            deadline=time.monotonic()+180;health=None
            while time.monotonic()<deadline:
                health=guest("""import json,pathlib,subprocess
p=pathlib.Path('/var/aos/workdirs/sm/runtimes/systemd-slot-camera-access')
r=subprocess.run(['systemctl','show','aos-camera-access','-p','ActiveState','-p','Result','-p','NRestarts','-p','MainPID'],capture_output=True,text=True)
print(json.dumps(dict(unit=dict(line.split('=',1) for line in r.stdout.splitlines() if '=' in line),
 installed=json.loads((p/'state/installed.json').read_bytes()) if (p/'state/installed.json').exists() else None,
 transactionPresent=(p/'state/transaction.json').exists())))
""")
                if health['unit'].get('ActiveState')=='active' and health['installed'] and not health['transactionPresent']:break
                time.sleep(2)
            atomic(records/'camera-native-health.json',health)
            require(health['unit'].get('ActiveState')=='active' and health['installed'] and not health['transactionPresent'],'CAMERA_NATIVE_ACTIVATION_NOT_CONFIRMED')
            result.update(outcome='PASS_NATIVE_CAMERA_OEM_ONLY',nativeActivation='PASS',aosConsumer='NOT_RUN')
        except Exception as error:
            value=str(error);result['code']=value if re.fullmatch('[A-Z][A-Z0-9_:,.-]{1,180}',value) else type(error).__name__
            try:
                facts=guest("""import json,pathlib,subprocess
def run(args):
 p=subprocess.run(args,capture_output=True,text=True,timeout=8);return p.stdout
units={name:dict(line.split('=',1) for line in run(['systemctl','show',name,'-p','ActiveState','-p','Result','-p','NRestarts','-p','MainPID']).splitlines() if '=' in line) for name in ('aos-sm','aos-camera-access')}
paths={}
for name in ('/var/aos/workdirs/sm/runtimes/systemd-slot-camera-access','/run/aos-camera-access/read','/run/aos-camera-access/oem'):
 p=pathlib.Path(name)
 paths[name]=dict(present=p.exists(),label=run(['stat','-c','%C',name]).strip() if p.exists() else None)
kernel=run(['journalctl','-k','-b','-n','300','--no-pager','-o','cat'])
avcs=[line[:1200] for line in kernel.splitlines() if 'avc:  denied' in line or 'avc: denied' in line]
logs=run(['journalctl','-b','-u','aos-camera-access','-u','aos-sm','-n','80','--no-pager','-o','cat'])
errors=[line[:250] for line in logs.splitlines() if any(word in line for word in ('CAMERA_ACCESS_','Failed','failed','denied','SafeStop','safe stop','waiting-for-safe-stop'))]
print(json.dumps(dict(units=units,paths=paths,avcs=avcs[-20:],errors=errors[-20:])))
""")
                atomic(records/'failure-diagnostics.json',facts)
            except Exception:result['diagnostic']='BOUNDED_GUEST_OBSERVATION_UNAVAILABLE'
        finally:
            if producer is not None:
                producer.terminate();producer.wait(timeout=10)
            if source_started and app is not None:
                try:
                    app.source_service.simulation('stop',target='test')
                    WorkspaceService(env,app.source_service.driver).execute('close')
                    result['cleanup']['sourceStopped']=True
                except Exception:result['cleanup']['sourceStopped']=False
            else:result['cleanup']['sourceStopped']=True
            try:
                stopped=vm.execute('stop','test',timeout=90)
                result['cleanup']['nativeVmStopped']=stopped['vehicles']['test']['state']=='COMPLETED'
            except Exception:result['cleanup']['nativeVmStopped']=False
            result['cleanup']['retainedJournalsUnchanged']=all((root/JOURNAL).read_bytes()==raw for root,raw in retained.items())
            result['seconds']=round(time.monotonic()-began,2)
            atomic(records/'result.json',result);print(json.dumps(result),flush=True)
    return 0 if result['outcome']=='PASS_NATIVE_CAMERA_OEM_ONLY' else 1


if __name__=='__main__':raise SystemExit(main())
