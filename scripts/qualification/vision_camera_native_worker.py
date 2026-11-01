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


def completion(result):
    """An action pass never hides failed cleanup or unexecuted acceptance gates."""
    if result['outcome'].startswith('PASS_') and not all(result['cleanup'].values()):
        result['outcome']='NOT_COMPLETE'
        result['code']='CAMERA_CLEANUP_NOT_CONFIRMED'
    return result


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
    resume=Path(c['resumeFrom']) if c.get('resumeFrom') else None
    if resume:
        require(resume.parent==records.parent and resume.name=='native-camera-02','RESUME_SCOPE_INVALID')
        previous=json.loads((resume/'result.json').read_bytes())
        require(previous.get('code')=='VISION_CAMERA_UPDATE_EXISTS_RECONCILE'
                and previous['cleanup']['retainedJournalsUnchanged'] is True,'PREVIOUS_CAMERA_ATTEMPT_NOT_RECONCILED')
        upload=initial.get('componentOperations',{}).get('0.1.0',{})
        require(upload.get('deploymentId')==(upload.get('upload',{}).get('response') or {}).get('deploymentId')
                and upload['upload']['response']['httpStatus']==201,'RECORDED_PUBLICATION_REQUIRED')
    result=dict(scenario='VISION_NATIVE_CAMERA_ACCESS',outcome='NOT_COMPLETE',phases=[],
        fullVisionE2E='NOT_RUN',gatewayCameraIngress='NOT_RUN',cameraRestart='NOT_RUN',
        nativeColdRestart='NOT_RUN',input='OEM_LOCAL_RECORDED_JPEG_FIXTURE',cleanup={})
    began=time.monotonic();source_started=False;producer=None;app=None;transient=False
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
            phase('isolate-native-unit-memberships',units.isolate_vision_test)
            boot=phase('native-start',lambda:vm.execute('start','test',timeout=150))
            require(boot['vehicles']['test']['state']=='COMPLETED','VM_START_INCOMPLETE')
            if c.get('transientSm'):
                import base64
                binary=(records/'aos-sm-profile-proof').read_bytes()
                require(len(binary)<8*1024**2 and hashlib.sha256(binary).hexdigest()==c['transientSm']['sha256'],
                        'TRANSIENT_SM_BINARY_CHANGED')
                transient=True
                code=r'''import base64,hashlib,json,pathlib,subprocess
root=pathlib.Path('/run/vision-camera-sm-proof');assert not root.exists();root.mkdir(mode=0o700)
binary=root/'aos-sm';raw=base64.b64decode(BINARY)
assert hashlib.sha256(raw).hexdigest()==DIGEST
binary.write_bytes(raw);binary.chmod(0o500)
subprocess.run(['chcon','--reference=/usr/bin/aos_sm_app',str(binary)],check=True,capture_output=True)
drop=pathlib.Path('/run/systemd/system/aos-sm.service.d/99-camera-profile-proof.conf')
drop.parent.mkdir(exist_ok=True);assert not drop.exists()
drop.write_text('[Service]\nExecStart=\nExecStart=/run/vision-camera-sm-proof/aos-sm -c /etc/aos/sm.cfg -v debug -j\n')
drop.chmod(0o600)
if REPAIR_LABELS:
 conf=root/'camera-store.conf'
 conf.write_text('Z /var/aos/workdirs/sm/runtimes/systemd-slot-camera-access - - - -\n')
 unit=pathlib.Path('/run/systemd/system/vision-camera-store-proof.service')
 assert not unit.exists()
 unit.write_text('[Unit]\nRequiresMountsFor=/var/aos/workdirs\n[Service]\nType=oneshot\nExecStart=/usr/bin/systemd-tmpfiles --create /run/vision-camera-sm-proof/camera-store.conf\n')
 subprocess.run(['systemctl','daemon-reload'],check=True,capture_output=True)
 subprocess.run(['systemctl','start','vision-camera-store-proof.service'],check=True,capture_output=True,timeout=15)
rollback=root/'rollback.py'
rollback.write_text("import pathlib,subprocess\np=pathlib.Path('/run/systemd/system/aos-sm.service.d/99-camera-profile-proof.conf')\np.unlink(missing_ok=True)\nsubprocess.run(['systemctl','daemon-reload'],check=True)\nsubprocess.run(['systemctl','restart','aos-sm'],check=True)\n")
subprocess.run(['systemd-run','--unit=vision-camera-sm-proof-rollback','--on-active=20m','/usr/bin/python3',str(rollback)],check=True,capture_output=True)
subprocess.run(['systemctl','daemon-reload'],check=True,capture_output=True)
subprocess.run(['systemctl','restart','aos-sm'],check=True,capture_output=True,timeout=40)
print(json.dumps(dict(transient=True,stockRootfsUnchanged=True,rollbackArmed=True)))
'''.replace('BINARY',repr(base64.b64encode(binary).decode())).replace('DIGEST',repr(c['transientSm']['sha256'])).replace('REPAIR_LABELS',repr(bool(c.get('repairStoreLabels'))))
                phase('transient-sm-profile-proof',lambda:guest(code,timeout=55))
                result['bootstrapAcceptance']='NOT_FACTORY_ACCEPTANCE_TRANSIENT_TARGET'
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
            if resume:
                scope['deploymentId']=initial['componentOperations']['0.1.0']['deploymentId']
            before=phase('camera-publication-preflight',lambda:units._cloud('vision-camera-status',purpose='status' if resume else 'upload',**scope))
            require(before['publication']['stage']==('READY' if resume else 'NOT_PUBLISHED')
                    and (bool(before['versions']) if resume else not before['versions']),'CAMERA_PUBLICATION_EXISTS_RECONCILE')
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
            if transient:
                # Classify known offline failures before paying CARLA startup.
                deadline=time.monotonic()+15
                while time.monotonic()<deadline:
                    offline=guest("""import json,subprocess
p=subprocess.run(['systemctl','show','aos-camera-access-selftest@a','-p','Result','-p','ExecMainStatus','-p','ExecMainStartTimestampMonotonic'],capture_output=True,text=True)
print(json.dumps(dict(line.split('=',1) for line in p.stdout.splitlines() if '=' in line)))
""")
                    require(offline.get('Result')!='exit-code','CAMERA_OFFLINE_SELFTEST_FAILED')
                    if int(offline.get('ExecMainStartTimestampMonotonic','0'))>0 and offline.get('ExecMainStatus')=='0':break
                    time.sleep(1)
                atomic(records/'camera-offline-selftest.json',offline)
            # The existing Source owner, not this diagnostic, owns all CARLA
            # ticks and physical Safe Stop. Inference/fixture never actuates it.
            app=DemoOrchestrator(environment_service=env,vm_service=vm)
            source_started=True
            phase('source-start',lambda:app.source_service.simulation('start',target='test'))
            phase('source-native-authentication',app.source_service.initialize_test)
            component=ComponentService(env)
            if not resume:
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
            if not resume:
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
            if not resume:
                phase('camera-native-send',lambda:mutation('send',lambda:units._cloud('vision-camera-send',**scope)))
            else:
                atomic(records/'automatic-delivery-reconciled.json',dict(deploymentId=scope['deploymentId'],
                    versionId=scope['updateComponentId'],noUpload=True,noSend=True,
                    reason='EXACT_PUBLICATION_AND_AUTOMATIC_VERIFICATION_PENDING_OBSERVED'))
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
            require(health['installed'].get('Version')=='0.1.0','CAMERA_NATIVE_VERSION_MISMATCH')
            result['nativeActivation']='PASS'
            def external(name,action):
                intent=records/(name+'-intent.json')
                require(not intent.exists(),'FIXTURE_MUTATION_EXISTS_RECONCILE')
                atomic(intent,dict(attemptStarted=True,action=name,unitId=item['unitId'],startedAt=now()))
                value=action();atomic(records/(name+'-response.json'),value)
                return value
            def publish_probe(version):
                output=records/('probe-'+version+'.tar.gz')
                signed=phase('probe-sign-'+version,lambda:fixture('sign',probeVersion=version,output=str(output)))
                response=phase('probe-upload-'+version,lambda:external('probe-upload-'+version,
                    lambda:fixture('upload',probeVersion=version,bundle=str(output),expectedSha256=signed['sha256'])))
                deadline=time.monotonic()+150;value=None
                while time.monotonic()<deadline:
                    value=fixture('publication',probeVersion=version,deploymentId=response['deploymentId'])
                    if value['stage']=='READY':return value
                    require(value['stage']=='PROCESSING','PROBE_PUBLICATION_FAILED');time.sleep(2)
                raise ValueError('PROBE_PUBLICATION_TIMEOUT')
            published=publish_probe('0.1.0');service_id=published['serviceId']
            created=phase('probe-subject-create',lambda:external('probe-subject-create',
                lambda:fixture('subject-create',serviceId=service_id)))
            subject=created['subject']
            phase('probe-subject-bind',lambda:external('probe-subject-bind',
                lambda:fixture('subject-bind',serviceId=service_id,subject=subject)))
            phase('probe-subject-assign',lambda:external('probe-subject-assign',
                lambda:fixture('subject-assign',serviceId=service_id,subject=subject)))
            # Retained recording, explicit OEM-local replay. Preserve original
            # frame/time/bytes; a new fixture epoch is selected for each replay.
            # This proves IPC/identity, not live ingress/calibration or models.
            sequence=Path.home()/'SDV-Qualification/vision-vm-m4/model-compute/compute-continuation/sequence'
            manifest=json.loads((sequence/'sequence.json').read_bytes());frames=manifest['frames']
            pair=next((frames[i:i+2] for i in range(len(frames)-1)
                if 80_000_000<=round((frames[i+1]['simulationTime']-frames[i]['simulationTime'])*1e9)<=120_000_000),None)
            require(pair is not None,'RECORDED_FIXTURE_PAIR_REQUIRED')
            import base64
            images=[]
            for row in pair:
                name=row['file'];require(Path(name).name==name,'FIXTURE_PATH_INVALID')
                raw=(sequence/name).read_bytes()
                require(0<len(raw)<=4*1024**2 and hashlib.sha256(raw).hexdigest()==row['sha256'],'FIXTURE_FRAME_CHANGED')
                images.append(dict(row,jpeg=base64.b64encode(raw).decode()))
            producer_code=r'''import base64,hashlib,json,os,pathlib,signal,socket,sys,time,uuid
root=pathlib.Path('/run/vision-camera-probe-fixture')
assert not root.exists();root.mkdir(mode=0o700)
(root/'pid').write_text(json.dumps(dict(pid=os.getpid(),start=pathlib.Path('/proc/self/stat').read_text().split()[21])))
stopping=[False]
for name in (signal.SIGTERM,signal.SIGHUP):signal.signal(name,lambda *_:stopping.__setitem__(0,True))
payload=pathlib.Path('/var/aos/workdirs/sm/runtimes/systemd-slot-camera-access/active/bin/camera-access')
sys.path.insert(0,str(payload))
from aos_camera_access import ipc
def call(value,data=b''):
 with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as stream:
  stream.settimeout(2);stream.connect('/run/aos-camera-access/oem/producer.sock');deadline=time.monotonic()+2
  ipc.write(stream,(ipc.header(value),data),deadline);return ipc.receive(stream,deadline)
frames=IMAGES
epoch=call(dict(schemaVersion=1,operation='hello'))['componentEpoch']
calibration=hashlib.sha256(b'uncalibrated OEM-local recorded JPEG IPC fixture').hexdigest()
print('VISION_CAMERA_FIXTURE_STARTED',flush=True)
end=time.monotonic()+75
try:
 while time.monotonic()<end and not stopping[0]:
  binding=dict(sourceId='00000000-0000-0000-0000-000000000003',sourceEpoch=str(uuid.uuid4()),cameraId='front',calibrationId=calibration)
  call(dict(schemaVersion=1,operation='select',componentEpoch=epoch,binding=binding))
  for row in frames:
   raw=base64.b64decode(row['jpeg']);stamp=round(row['simulationTime']*1e9)
   metadata=dict(schemaVersion=1,profile='front-rgb-jpeg-720p-v1',**binding,frame=row['frame'],
    simulationTimeNs=stamp,sensorSimulationTimeNs=stamp,clock='CARLA_WORLD_SNAPSHOT_FRAME_MATCH',
    encoding='JPEG',width=1280,height=720,payloadBytes=len(raw),sha256=row['sha256'])
   call(dict(schemaVersion=1,operation='frame',componentEpoch=epoch,metadata=metadata),raw)
  time.sleep(.25)
finally:
 try:call(dict(schemaVersion=1,operation='disconnect',componentEpoch=epoch))
 except Exception:pass
 (root/'pid').unlink();root.rmdir()
'''.replace('IMAGES',repr(images))
            state=read_json(native/JOURNAL);command=ssh_command(access_path(native,'test'),item['sshPort'],5)
            script="python3 -u - <<'VISION_CAMERA_FIXTURE'\n"+producer_code+"\nVISION_CAMERA_FIXTURE\n"
            producer=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            producer.stdin.write(script);producer.stdin.close()
            require(producer.stdout.readline().strip()=='VISION_CAMERA_FIXTURE_STARTED','OEM_FIXTURE_START_FAILED')
            def native_reader():
                return guest("""import hashlib,json,pathlib,pwd,grp,subprocess
rows=[]
for path in pathlib.Path('/proc').iterdir():
 if not path.name.isdecimal():continue
 try:
  exe=(path/'exe').resolve(strict=True)
  if exe.name!='vision-camera-probe':continue
  status=dict(line.split(':',1) for line in (path/'status').read_text().splitlines() if ':' in line)
  mount=[line.split() for line in (path/'mountinfo').read_text().splitlines() if ' /run/aosedge/platform/camera ' in line]
  rows.append(dict(pid=int(path.name),uid=int(status['Uid'].split()[0]),groups=[int(v) for v in status['Groups'].split()],
   capEff=status['CapEff'].strip(),noNewPrivs=status.get('NoNewPrivs','').strip(),
   binarySha256=hashlib.sha256((path/'exe').read_bytes()).hexdigest(),context=(path/'attr/current').read_text().strip(),
   mountReadonly=bool(mount) and all('ro' in line[5].split(',') for line in mount)))
 except (OSError,KeyError,ValueError):pass
p=subprocess.run(['journalctl','-b','-n','500','--no-pager','-o','cat'],capture_output=True,text=True)
messages=[]
for line in p.stdout.splitlines():
 at=line.find('{"probe":')
 if at>=0:
  try:messages.append(json.JSONDecoder().raw_decode(line[at:])[0])
  except ValueError:pass
print(json.dumps(dict(processes=rows,messages=messages[-80:],readerGid=grp.getgrnam('aos-camera-read').gr_gid,
 enforcing=pathlib.Path('/sys/fs/selinux/enforce').read_text().strip()=='1')))
""")
            deadline=time.monotonic()+60;reader=None
            while time.monotonic()<deadline:
                reader=native_reader()
                if any(row.get('probe')=='READ' and row.get('pair') and row.get('bytesVerified') for row in reader['messages']):break
                time.sleep(2)
            atomic(records/'native-reader.json',reader)
            require(reader['enforcing'] and len(reader['processes'])==1,'NATIVE_READER_NOT_OBSERVED')
            process=reader['processes'][0]
            require(process['uid']>0 and reader['readerGid'] in process['groups'] and process['mountReadonly']
                    and int(process['capEff'],16)==0 and process['binarySha256']==c['probeSha256'],'NATIVE_READER_IDENTITY_OR_MOUNT_FAILED')
            require(any(row.get('probe')=='READ' and row.get('pair') and row.get('bytesVerified') for row in reader['messages']), 'NATIVE_READER_BYTES_NOT_PROVEN')
            require(any(row.get('probe')=='READER_MUTATION_DENIED' for row in reader['messages']),'NATIVE_READER_DENIAL_NOT_PROVEN')
            before_pid=process['pid'];result['aosConsumer']='PASS_READ_ONLY_NATIVE_RESOURCE'
            updated=publish_probe('0.1.1');require(updated['serviceId']==service_id,'PROBE_SERVICE_CHANGED')
            deadline=time.monotonic()+60;revoked=None
            while time.monotonic()<deadline:
                revoked=native_reader()
                if len(revoked['processes'])==1 and revoked['processes'][0]['pid']!=before_pid and not revoked['processes'][0]['mountReadonly']:break
                time.sleep(2)
            atomic(records/'native-revocation.json',revoked)
            require(len(revoked['processes'])==1 and revoked['processes'][0]['pid']!=before_pid
                    and not revoked['processes'][0]['mountReadonly'],'NATIVE_RESOURCE_REVOCATION_NOT_PROVEN')
            result.update(outcome='PASS_TRANSIENT_CAMERA_OEM_AND_AOS_READ' if transient else 'PASS_NATIVE_CAMERA_OEM_AND_AOS_READ',resourceRevocation='PASS',
                          diagnosticService='NOT_PERCEPTION',captureClockAccuracy='NOT_QUALIFIED')
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
                try:
                    guest("""import json,os,pathlib,signal,time
p=pathlib.Path('/run/vision-camera-probe-fixture/pid')
if p.exists():
 value=json.loads(p.read_bytes());proc=pathlib.Path('/proc')/str(value['pid'])
 if proc.exists():
  assert (proc/'stat').read_text().split()[21]==value['start']
  assert (proc/'cmdline').read_bytes().startswith(b'python3\\0-u\\0-\\0')
  os.kill(value['pid'],signal.SIGTERM)
  end=time.monotonic()+4
  while proc.exists() and time.monotonic()<end:time.sleep(.1)
  assert not proc.exists()
print(json.dumps(dict(stopped=True)))
""")
                    producer.wait(timeout=8);result['cleanup']['producerStopped']=True
                except Exception:result['cleanup']['producerStopped']=False
            if source_started and app is not None:
                try:
                    app.source_service.simulation('stop',target='test')
                    WorkspaceService(env,app.source_service.driver).execute('close')
                    result['cleanup']['sourceStopped']=True
                except Exception:result['cleanup']['sourceStopped']=False
            else:result['cleanup']['sourceStopped']=True
            if transient:
                try:
                    guest("""import json,pathlib,subprocess
p=pathlib.Path('/run/vision-camera-sm-proof');drop=pathlib.Path('/run/systemd/system/aos-sm.service.d/99-camera-profile-proof.conf')
subprocess.run(['systemctl','stop','vision-camera-sm-proof-rollback.timer'],check=True,capture_output=True)
drop.unlink(missing_ok=True)
subprocess.run(['systemctl','daemon-reload'],check=True,capture_output=True)
subprocess.run(['systemctl','restart','aos-sm'],check=True,capture_output=True,timeout=40)
unit=pathlib.Path('/run/systemd/system/vision-camera-store-proof.service')
if unit.exists():
 subprocess.run(['systemctl','stop','vision-camera-store-proof.service'],check=True,capture_output=True)
 unit.unlink()
 subprocess.run(['systemctl','daemon-reload'],check=True,capture_output=True)
for name in ('aos-sm','rollback.py','camera-store.conf'):(p/name).unlink(missing_ok=True)
p.rmdir()
print(json.dumps(dict(stockSmRestored=True)))
""",timeout=50)
                    result['cleanup']['stockSmRestored']=True
                except Exception:result['cleanup']['stockSmRestored']=False
            try:
                stopped=vm.execute('stop','test',timeout=150)
                result['cleanup']['nativeVmStopped']=stopped['vehicles']['test']['state']=='COMPLETED'
            except Exception:result['cleanup']['nativeVmStopped']=False
            result['cleanup']['retainedJournalsUnchanged']=all((root/JOURNAL).read_bytes()==raw for root,raw in retained.items())
            result['seconds']=round(time.monotonic()-began,2)
            completion(result)
            atomic(records/'result.json',result);print(json.dumps(result),flush=True)
    return 0 if result['outcome'] in ('PASS_NATIVE_CAMERA_OEM_AND_AOS_READ','PASS_TRANSIENT_CAMERA_OEM_AND_AOS_READ') else 1


if __name__=='__main__':raise SystemExit(main())
