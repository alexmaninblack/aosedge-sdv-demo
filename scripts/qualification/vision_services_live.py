#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Scenario-owned same-VM Source/exchange proof, not an engineering model worker."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import queue
import select
import shlex
import subprocess
import sys
import time
import traceback
import threading

UNIT='af6d074a-6ce1-49ba-b613-0476e7b6d1b5'
VM='89273f16-4be0-4b22-b4cb-58d08533c8bc'
MANIFEST='c4694c1b440bb036b3df63a1b0adc573724d9371e11f98abb596d005ecc84ea9'


def require(ok,code):
    if not ok:raise ValueError(code)


def atomic(path,value):
    pending=path.with_suffix('.pending');pending.write_text(json.dumps(value,indent=2)+'\n');pending.chmod(0o600);pending.replace(path)


def evidence(value):
    """Owner return values are private; retain only safe diagnostic fields."""
    if isinstance(value,dict):
        return {key:evidence(item) for key,item in value.items() if not any(word in key.lower() for word in
            ('fingerprint','certificate','privatekey','private_key','secret','token','material','runnercommand','simulatorcommand','signerid'))}
    if isinstance(value,(list,tuple)):return [evidence(item) for item in value]
    if isinstance(value,str) and '-----BEGIN ' in value:return '<redacted>'
    return value


def clean_error(error):
    value=str(error);return value if re.fullmatch('[A-Z][A-Z0-9_:.-]{1,160}',value) else type(error).__name__


def final_outcome(result):
    """A partial PASS must never survive a later failed gate or cleanup."""
    if result.get('code') or not result.get('cleanup') or not all(result['cleanup'].values()):return 'NOT_COMPLETE'
    return result['outcome']


class ConfigProofComplete(Exception):
    pass


def camera_pose_diagnosis(app,records,native):
    """Read existing actors only; no tick, attachment, settings or vehicle writes."""
    assets=app.source_service.driver.assets();sys.path.append(str(assets['python-api-root']))
    import carla
    client=carla.Client('127.0.0.1',2000);client.set_timeout(5.)
    from uuid import uuid4
    from aosedge_demo_orchestrator.environment import JOURNAL
    source=json.loads((native/JOURNAL).read_bytes())['source']
    status=app.source_service.driver.rpc(source,'status',str(uuid4()));frame=status.get('frame') or {}
    require(frame.get('runId')==source['runId'] and status.get('fresh') is True,'VISION_POSE_SOURCE_NOT_FRESH')
    world=client.get_world();parent=world.get_actor(frame['egoActorId'])
    require(parent is not None and parent.type_id.startswith('vehicle.'),'VISION_POSE_EXISTING_EGO_REQUIRED')
    # A newly connected LibCarla client receives its actor cache asynchronously.
    # A successful get_world()/vehicle RPC is not evidence that this cache is ready.
    deadline=time.monotonic()+3
    while True:
        world.get_snapshot();actors=list(world.get_actors());all_cameras=[a for a in actors if a.type_id=='sensor.camera.rgb']
        if all_cameras or time.monotonic()>=deadline:break
        time.sleep(.05)
    atomic(records/'read-only-camera-inventory.json',dict(actorTypes={kind:sum(a.type_id==kind for a in actors) for kind in sorted({a.type_id for a in actors})},cameras=[dict(hasParent=s.parent is not None,
        ownedParent=s.parent is not None and s.parent.id==parent.id,
        attributes={k:v for k,v in s.attributes.items() if k in ('image_size_x','image_size_y','fov','sensor_tick')}) for s in all_cameras]))
    cameras=[s for s in all_cameras if s.parent is not None and s.parent.id==parent.id
        and s.attributes.get('image_size_x')=='1280' and s.attributes.get('image_size_y')=='720' and float(s.attributes.get('fov','0'))==50.]
    require(len(cameras)==1,'VISION_POSE_EXISTING_CAMERA_REQUIRED')
    camera=cameras[0];rows=[]
    for _ in range(12):
        snapshot=world.get_snapshot();vehicle=snapshot.find(parent.id);sensor=snapshot.find(camera.id)
        require(vehicle is not None and sensor is not None,'VISION_POSE_SAME_SNAPSHOT_REQUIRED')
        vp=vehicle.get_transform();cp=sensor.get_transform()
        p,y,r=map(math.radians,(vp.rotation.pitch,vp.rotation.yaw,vp.rotation.roll))
        sp,cpitch,sy,cy,sr,cr=math.sin(p),math.cos(p),math.sin(y),math.cos(y),math.sin(r),math.cos(r)
        corrected=[[cpitch*cy,cy*sp*sr-sy*cr,cy*sp*cr+sy*sr],
                   [cpitch*sy,sy*sp*sr+cy*cr,sy*sp*cr-cy*sr],[-sp,cpitch*sr,cpitch*cr]]
        unreal=[[cpitch*cy,cy*sp*sr-sy*cr,-cy*sp*cr-sy*sr],
                [cpitch*sy,sy*sp*sr+cy*cr,-sy*sp*cr+cy*sr],[sp,-cpitch*sr,cpitch*cr]]
        observed=[cp.location.x-vp.location.x,cp.location.y-vp.location.y,cp.location.z-vp.location.z]
        mount=[1.6,0.,1.5]
        def prediction(matrix):return [sum(matrix[i][j]*mount[j] for j in range(3)) for i in range(3)]
        def error(matrix):return math.sqrt(sum((a-b)**2 for a,b in zip(prediction(matrix),observed)))
        rows.append(dict(frame=snapshot.frame,parentRotation=[vp.rotation.pitch,vp.rotation.yaw,vp.rotation.roll],
            cameraRotation=[cp.rotation.pitch,cp.rotation.yaw,cp.rotation.roll],observedMountWorld=observed,
            correctedMountWorld=prediction(corrected),unrealMountWorld=prediction(unreal),
            correctedErrorMetres=error(corrected),unrealErrorMetres=error(unreal)))
        time.sleep(.1)
    return dict(readOnly=True,existingActorsOnly=True,sameSnapshot=True,samples=rows)


def worker(context):
    c=json.loads(context.read_bytes());records=context.parent;result=dict(outcome='NOT_COMPLETE',phases=[],cleanup={},cloudMutation=False,servicesDeployed=False)
    started=time.monotonic();vm=None;app=None;native=None;retained={};session=None;awake=None;source_attempted=False;lines=queue.Queue(maxsize=64);reader=None
    def phase(name,action):
        print(json.dumps(dict(stage=name,state='STARTED')),flush=True);began=time.monotonic();value=action()
        atomic(records/(name+'.json'),dict(seconds=round(time.monotonic()-began,2),facts=evidence(value)));result['phases'].append(dict(stage=name,seconds=round(time.monotonic()-began,2)))
        print(json.dumps(dict(stage=name,state='COMPLETE')),flush=True);return value
    def receive(timeout=30):
        try:raw=lines.get(timeout=timeout)
        except queue.Empty:raise ValueError('VISION_LIVE_GUEST_RESPONSE_TIMEOUT') from None
        require(raw and len(raw)<=262144,'VISION_LIVE_GUEST_RESPONSE_LIMIT');return json.loads(raw)
    def request(operation,timeout=30):
        session.stdin.write(operation+'\n');session.stdin.flush();value=receive(timeout)
        if value.get('phase')!=operation:atomic(records/'guest-error-response.json',value)
        require(value.get('phase')==operation,value.get('data',{}).get('code','VISION_LIVE_GUEST_PROTOCOL_FAILED'));return value['data']
    try:
        require(hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==c['workerSha256'],'VISION_LIVE_WORKER_CHANGED')
        require(subprocess.check_output(['/usr/sbin/sysctl','-n','hw.model'],text=True).strip()=='Mac16,8','M4_REQUIRED')
        desktop=subprocess.check_output(['/usr/sbin/ioreg','-n','Root','-d1'],text=True)
        locked=bool(re.search('CGSSessionScreenIsLocked[^\r\n]{0,16}Yes',desktop))
        require(not locked or c.get('nativeServices'),'M4_DESKTOP_LOCKED')
        result['visualDesktop']='LOCKED_UI_NOT_RUN' if locked else 'UNLOCKED'
        package=Path(c['packageRoot']);bundle=Path(c['bundle'])
        require(hashlib.sha256((package/'application-manifest.json').read_bytes()).hexdigest()==c['baseManifest'],'VISION_LIVE_BASE_CHANGED')
        subprocess.run(['codesign','--verify','--deep','--strict','-R','=identifier "org.aosedge.sdvlab.vision.bootstrap" and anchor apple generic and certificate leaf[subject.OU] = "3NF57VKB3V"',str(bundle)],check=True,capture_output=True,timeout=120)
        sys.path.insert(0,str(package/'aosedge-sdv-demo/apps/demo-orchestrator/src'))
        import aosedge_demo_orchestrator
        from aosedge_demo_orchestrator import runtime_paths
        aosedge_demo_orchestrator.__path__.insert(0,str(bundle/'Contents/Resources/tooling/aosedge-sdv-demo/apps/demo-orchestrator/src/aosedge_demo_orchestrator'))
        from aosedge_demo_orchestrator import vision_bootstrap as v
        from aosedge_demo_orchestrator.environment import EnvironmentService,JOURNAL
        from aosedge_demo_orchestrator.vm import VMService,access_path
        from aosedge_demo_orchestrator.guest_access import ssh_command
        from aosedge_demo_orchestrator.application import DemoOrchestrator
        from aosedge_demo_orchestrator.workspace import WorkspaceService
        bootstrap=v.verify(bundle,c['baseManifest']);require(bootstrap.manifest_sha256==c.get('bootstrapManifest',MANIFEST),'VISION_LIVE_BOOTSTRAP_CHANGED')
        native=Path.home()/v.INSTANCE_NAME;before=json.loads((native/JOURNAL).read_bytes());item=before['vehicles']['test']
        retained={Path.home()/n:(Path.home()/n/JOURNAL).read_bytes() for n in v.RETAINED_INSTANCE_NAMES}
        require(item['unitId']==UNIT and item['localVmId']==VM and item['runtime']['state']==before['source']['state']=='STOPPED' and not before['source'].get('operation'),'SAME_IDLE_VISION_REQUIRED')
        awake=subprocess.Popen(['/usr/bin/caffeinate','-d','-i','-w',str(__import__('os').getpid())],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        with runtime_paths.installed_session(native):
            env=EnvironmentService(catalog=v.SignedVisionCatalog(bootstrap),vm_profile=v.VM_PROFILE);vm=VMService(env);app=DemoOrchestrator(environment_service=env,vm_service=vm)
            phase('normal-same-vm-start',lambda:vm.execute('start','test',timeout=150))
            current=json.loads((native/JOURNAL).read_bytes())['vehicles']['test'];command=ssh_command(access_path(native,'test'),current['sshPort'],8)
            base=Path('/run/aos-vision-services-input-02')
            for name,pin in c['files'].items():require(hashlib.sha256((records/name).read_bytes()).hexdigest()==pin,'VISION_LIVE_INPUT_CHANGED')
            setup=subprocess.run(command,input='set -eu\ntest ! -e '+shlex.quote(str(base))+'\nmkdir -m 755 '+shlex.quote(str(base))+'\n',capture_output=True,text=True,timeout=15)
            require(setup.returncode==0,'VISION_LIVE_STAGING_CONFLICT')
            options=command[1:-3];options.remove('-T');options[options.index('-p')]='-P'
            guest_files=c.get('guestFiles',c['files'])
            require(set(guest_files)<=set(c['files']) and all(c['files'][name]==pin for name,pin in guest_files.items()),'VISION_GUEST_FILE_SCOPE_CHANGED')
            transfer=subprocess.run(['/usr/bin/scp','-O',*options,*[str(records/name) for name in guest_files],'root@127.0.0.1:'+str(base)+'/'],capture_output=True,text=True,timeout=30)
            require(transfer.returncode==0,'VISION_LIVE_INPUT_TRANSFER_FAILED')
            code='''import hashlib,json,pathlib,select,sys,time,traceback
base=pathlib.Path(BASE);pins=PINS
assert all(not (base/name).is_symlink() and hashlib.sha256((base/name).read_bytes()).hexdigest()==pin for name,pin in pins.items())
ns={};exec((base/'vision_services_primitives_guest.py').read_text(),ns);transaction=ns['PermanentObservation' if PERMANENT else 'Transaction'](base)
def emit(phase,data):print(json.dumps(dict(phase=phase,data=data)),flush=True)
try:
 emit('READY',transaction.open());deadline=time.monotonic()+1800
 while time.monotonic()<deadline:
  if not select.select([sys.stdin],[],[],max(0,deadline-time.monotonic()))[0]:break
  operation=sys.stdin.readline(65).strip()
  if operation in ('','STOP'):break
  try:
   if operation=='OBSERVE':emit(operation,transaction.observe())
   elif operation=='NATIVE':emit(operation,transaction.native())
   elif operation=='STORAGE':emit(operation,transaction.storage())
   elif operation=='DIAGNOSE':emit(operation,transaction.diagnose())
   elif operation=='CALIBRATION_DIAGNOSE':emit(operation,transaction.native_calibration_diagnosis())
   elif operation=='NATIVE_ROLE_PROOF':emit(operation,transaction.native_calibration_diagnosis('unix-only' if UNIX_ONLY else 'roles'))
   elif operation=='NATIVE_NETWORK_DIAGNOSE':emit(operation,transaction.native_network_diagnosis())
   elif operation=='RETIRE_MEASUREMENT':emit(operation,transaction.retire_measurement_duplicates(MEASUREMENT_INPUTS))
   elif operation=='DENY_ROOT':emit(operation,transaction.root_denial())
   elif operation=='RESTART':
    ns['call'](['systemctl','restart','aos-vision-exchange.service']);emit(operation,transaction.observe())
   else:raise ValueError('VISION_LIVE_GUEST_OPERATION_DENIED')
  except Exception as error:
   value=str(error);emit('ERROR',dict(code=value if value.isupper() and len(value)<160 else type(error).__name__,frames=[dict(file=pathlib.Path(f.filename).name,line=f.lineno) for f in traceback.extract_tb(error.__traceback__)[-3:]]))
except Exception as error:
 value=str(error);emit('ERROR',dict(code=value if value.isupper() and len(value)<160 else type(error).__name__,frames=[dict(file=pathlib.Path(f.filename).name,line=f.lineno) for f in traceback.extract_tb(error.__traceback__)[-3:]]))
finally:
 try:emit('CLOSED',transaction.close())
 except Exception as error:
  value=str(error);emit('CLEANUP_ERROR',dict(code=value if value.isupper() and len(value)<160 else type(error).__name__))
'''
            replacements=dict(BASE=str(base),PINS=guest_files,MEASUREMENT_INPUTS=c.get('measurementInputs',{}),UNIX_ONLY=c.get('nativeUnixOnlyProof',False),PERMANENT=c.get('permanentSystem',False))
            code=re.sub(r'\b(BASE|PINS|MEASUREMENT_INPUTS|UNIX_ONLY|PERMANENT)\b',lambda match:repr(replacements[match[0]]),code)
            session=subprocess.Popen(command[:-2]+['python3 -I -B -c '+shlex.quote(code)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
            def read_responses():
                for row in session.stdout:lines.put(row)
                lines.put('')
            reader=threading.Thread(target=read_responses,daemon=True);reader.start()
            ready=receive(170);require(ready['phase']=='READY','VISION_LIVE_GUEST_NOT_READY');atomic(records/'native-primitives-ready.json',ready['data'])
            if c.get('nativeOwnerCapacityFive'):phase('five-resource-native-owners-configuration',lambda:request('DIAGNOSE'))
            if c.get('nativeConfigProof'):
                phase('effective-native-resource-configuration',lambda:request('DIAGNOSE'));result['outcome']='PASS_READ_ONLY_NATIVE_CONFIGURATION_OBSERVATION';raise ConfigProofComplete
            source_attempted=True
            phase('normal-source-start',lambda:app.source_service.simulation('start',target='test'))
            phase('normal-source-enrollment',app.source_service.initialize_test)
            phase('normal-source-camera-and-exchange-start',lambda:app.source_service.camera_ingress('start'))
            def healthy():
                end=time.monotonic()+5
                while True:
                    value=request('OBSERVE');atomic(records/'latest-broker-observation.json',value)
                    if value['unit']['ActiveState']!='active' or value['socketCount']==4 or value['scopedAvcs'] or time.monotonic()>=end:break
                    time.sleep(.05)
                require(value['unit']['ActiveState']=='active' and value['unit']['NRestarts']=='0' and value['socketCount']==4,'VISION_LIVE_BROKER_NOT_HEALTHY')
                require(len(set(value['uid']))==1 and value['uid'][0]>0 and value['nnp']=='1' and all(int(v,16)==0 for v in value['capabilities'].values())
                    and value['context'].split(':')[2]=='vision_exchange_t' and value['credentialMountReadonly']
                    and all(row['isSocket'] and row['ownerCorrect'] and row['groupCorrect'] and row['mode']==0o660 for row in value['sockets']),'VISION_LIVE_BROKER_IDENTITY_FAILED')
                return value
            first=phase('nonroot-source-owned-broker',healthy)
            phase('idempotent-source-exchange-start',lambda:app.source_service.camera_ingress('start'))
            repeated=phase('same-broker-after-repeat',healthy);require(first['unit']['MainPID']==repeated['unit']['MainPID'],'VISION_LIVE_REPEAT_RESTARTED_BROKER')
            denied=phase('wrong-root-peer-denials',lambda:request('DENY_ROOT'));require(denied['outcome']=='PASS_WRONG_ROOT_PEER_DENIED','VISION_LIVE_ROOT_NOT_DENIED')
            after_denial=phase('same-healthy-broker-after-denials',healthy);require(after_denial['unit']['MainPID']==first['unit']['MainPID'],'VISION_LIVE_DENIAL_CRASHED_OWNER')
            restarted=phase('broker-restart',lambda:request('RESTART'));require(restarted['unit']['MainPID']!=first['unit']['MainPID'],'VISION_LIVE_RESTART_NOT_OBSERVED')
            phase('healthy-broker-after-restart',healthy)
            phase('normal-source-exchange-stop',lambda:app.source_service.camera_ingress('stop'))
            stopped=phase('broker-process-exited',lambda:request('OBSERVE'));require(stopped['unit']['MainPID']=='0','VISION_LIVE_BROKER_REMAINS')
            phase('normal-source-exchange-reconnect',lambda:app.source_service.camera_ingress('start'))
            final=phase('healthy-broker-after-reconnect',healthy);require(not final['scopedAvcs'],'VISION_LIVE_FUNCTIONAL_AVC')
            result['outcome']='PASS_SOURCE_OWNED_NATIVE_BROKER_LIFECYCLE_ONLY'
            if c.get('nativeServices'):
                phase('native-storage-before-delivery',lambda:request('STORAGE'))
                if c.get('measurementInputs'):phase('retire-verified-measurement-duplicates',lambda:request('RETIRE_MEASUREMENT'))
                from aosedge_demo_orchestrator.status import load_configuration
                from aosedge_demo_orchestrator.cloud_runtime import launch
                from aosedge_demo_orchestrator.cloud_connection import selected_domain,cloud_binding
                config=load_configuration(native);sdk,sdk_env=launch(native,config['cloudPython'],'unit_cloud.py')
                payload=c['nativeServices'];tooling=bundle/'Contents/Resources/tooling/aosedge-sdv-demo/apps/demo-orchestrator/src'
                cloud_request=dict(cloudDomain=selected_domain(before),oemOwner=cloud_binding(before)['ownerId'],spOwner=config['cloudProfiles']['service-provider']['expectedOwnerId'],
                    oemCredential=str(config['cloudProfiles']['oem-delivery']['credential']),spCredential=str(config['cloudProfiles']['service-provider']['credential']),
                    vehicle={key:item[key] for key in ('unitId','systemUid','unitSetId','nodeId')})
                cloud_request['vehicle']['nodeHardwareId']=item['cloud']['identity']['nodeHardwareId']
                if c.get('nativeSota') or c.get('currentNative'):cloud_request['unixOnlySuccessor']=True
                def cloud(action,**extra):
                    if action in ('upload','subject-create','subject-bind','subject-assign'):result['cloudMutation']=True
                    done=subprocess.run([sdk[0],'-I','-B',str(records/'vision_services_cloud.py'),str(tooling)],input=json.dumps(dict(cloud_request,action=action,**extra)),
                        capture_output=True,text=True,env=sdk_env,timeout=105)
                    require(done.returncode==0 and len(done.stdout)<262144,'VISION_NATIVE_CLOUD_WORKER_UNAVAILABLE')
                    value=json.loads(done.stdout);require(value.get('ok') is True,value.get('reason','VISION_NATIVE_CLOUD_UNCONFIRMED'));return value['data']
                preflight=phase('two-service-cloud-preflight',lambda:cloud('preflight'))
                require(c.get('resumeNative') or (not preflight['subjectCandidates'] and all(not row['versions'] for row in preflight['services'].values())),'VISION_NATIVE_INITIAL_VERSION_OR_SUBJECT_EXISTS_RECONCILE')
                published={}
                for role in (() if c.get('resumeNative') else ('perception','assessment')):
                    pin=payload['services'][role];filename='vision-'+role+'-0.1.0.tar.gz'
                    intent=records/('upload-'+role+'-intent.json');require(not intent.exists(),'VISION_NATIVE_UPLOAD_EXISTS_RECONCILE')
                    atomic(intent,dict(attemptStarted=True,unitId=UNIT,codename='vision-'+role,version='0.1.0',sha256=pin['sha256']))
                    result['cloudMutation']=True
                    response=phase('publish-'+role,lambda role=role,pin=pin,filename=filename:cloud('upload',role=role,bundle=str(records/filename),expectedSha256=pin['sha256'],
                        prepared=str(records/(role+'-prepared.json')),preparedSha256=pin['preparedSha256'],packageModule=str(records/'aos_package.py'),packageModuleSha256=payload['packageModuleSha256']))
                    atomic(records/('upload-'+role+'-response.json'),response);deadline=time.monotonic()+180
                    while True:
                        value=cloud('publication',role=role,deploymentId=response['deploymentId']);atomic(records/('publication-'+role+'-latest.json'),value)
                        if value['stage']=='READY':published[role]=value;break
                        require(time.monotonic()<deadline,'VISION_NATIVE_PUBLICATION_TIMEOUT');time.sleep(2)
                if c.get('resumeNative'):
                    resume=c['resumeNative'];ids=resume['serviceIds'];subject=resume['subject']
                    require(preflight['subjectCandidates']==[subject['id']] and all(preflight['services'][role]['serviceId']==ids[role]
                        and {row['id'] for row in preflight['services'][role]['versions']}==({resume['versionIds'][role],c['currentNative']['versionIds'][role]} if c.get('currentNative') else {resume['versionIds'][role]})
                        for role in ('perception','assessment')),'VISION_NATIVE_RECONCILIATION_CHANGED')
                    reconciled=phase('existing-native-subject-reconciliation',lambda:cloud('subject-status',serviceIds=ids,subject=subject))
                    require(reconciled['unitBound'] and reconciled['assignedRoles']==c.get('expectedAssignedRoles',['perception']),'VISION_NATIVE_EXISTING_ASSIGNMENT_CHANGED')
                else:
                    ids={role:row['serviceId'] for role,row in published.items()}
                    atomic(records/'subject-create-intent.json',dict(attemptStarted=True,unitId=UNIT,serviceIds=ids,label='SDV Vision Pilot'))
                    subject=phase('create-isolated-vision-subject',lambda:cloud('subject-create',serviceIds=ids))['subject'];atomic(records/'vision-subject.json',subject)
                    atomic(records/'subject-bind-intent.json',dict(attemptStarted=True,unitId=UNIT,subjectId=subject['id']))
                    phase('bind-same-vision-unit',lambda:cloud('subject-bind',serviceIds=ids,subject=subject))
                for role in ('perception','assessment'):
                    if not c.get('resumeNative') or role not in c.get('expectedAssignedRoles',['perception']):
                        atomic(records/('subject-assign-'+role+'-intent.json'),dict(attemptStarted=True,unitId=UNIT,subjectId=subject['id'],serviceId=ids[role]))
                        phase('assign-native-'+role,lambda role=role:cloud('subject-assign',role=role,serviceIds=ids,subject=subject))
                    if c.get('nativeDeliveryReconcile'):continue
                    deadline=time.monotonic()+120
                    while True:
                        actual=request('NATIVE');atomic(records/'native-instances-latest.json',actual)
                        if 'vision-'+role in actual['instances']:break
                        require(time.monotonic()<deadline,'VISION_NATIVE_INSTANCE_START_UNCONFIRMED');time.sleep(.5)
                if c.get('nativeDeliveryReconcile'):
                    deadline=time.monotonic()+120
                    while True:
                        actual=request('NATIVE');atomic(records/'native-instances-latest.json',actual)
                        if set(actual['instances'])=={'vision-perception','vision-assessment'}:break
                        require(time.monotonic()<deadline,'VISION_NATIVE_INSTANCE_START_UNCONFIRMED');time.sleep(.5)
                actual=phase('actual-native-service-identities',lambda:request('NATIVE'));instances=actual['instances']
                for role in ('perception','assessment'):
                    value=instances['vision-'+role];allocation=payload['allocation'][role]
                    require(value['identity']['version']==('0.1.1' if c.get('currentNative') else '0.1.0') and value['identity']['sourceRevision']==(c['currentNative']['sourceRevision'] if c.get('currentNative') else payload['applicationSourceRevision'])
                        and len(set(value['uid']))==1 and value['uid'][0]>0 and min(value['gid'])>0 and value['nnp']=='1'
                        and value['context'].split(':')[2]=='container_engine_t'
                        and all(int(value['capabilities'][key],16)==0 for key in ('CapEff','CapPrm','CapInh','CapAmb')),'VISION_NATIVE_IDENTITY_OR_SOURCE_MISMATCH')
                    require(value['cpuMax']==('280000 100000' if role=='perception' else '10000 100000') and value['memoryMax']==str(allocation['ramLimit']),'VISION_NATIVE_CPU_OR_MEMORY_QUOTA_NOT_APPLIED')
                    require(value['pidsMax']==str(allocation['pidsLimit']),'VISION_NATIVE_PID_QUOTA_NOT_APPLIED')
                    require(value['noFileLimits']==[str(allocation['noFileLimit'])]*2 and value['tmpFilesystemBytes']==allocation['tmpLimit'],
                        'VISION_NATIVE_FD_OR_TMP_QUOTA_NOT_APPLIED')
                    expected={'/run/aosedge/vision/'+name for name in (('perception-publish',) if role=='perception' else ('perception-read','context-read','assessment-publish'))}
                    if role=='perception':expected.add('/run/aosedge/platform/camera')
                    require(set(value['resourceMounts'])==expected and all(all(options.values()) for options in value['resourceMounts'].values())
                        and not value['credentialMountPresent'] and not value['forbiddenRolePathsPresent'],'VISION_NATIVE_ROLE_OR_MOUNT_ISOLATION_FAILED')
                result['servicesDeployed']=True
                if c.get('cameraPoseDiagnosis'):
                    phase('read-only-existing-camera-parent-pose',lambda:camera_pose_diagnosis(app,records,native))
                    phase('read-only-actual-native-calibration-diagnosis',lambda:request('CALIBRATION_DIAGNOSE'))
                    result['outcome']='PASS_READ_ONLY_NATIVE_CAMERA_POSE_DIAGNOSIS';raise ConfigProofComplete
                if c.get('nativeCalibrationDiagnosis'):
                    phase('read-only-actual-native-calibration-diagnosis',lambda:request('CALIBRATION_DIAGNOSE'))
                    result['outcome']='PASS_READ_ONLY_NATIVE_RESOURCE_CALIBRATION_DIAGNOSIS';raise ConfigProofComplete
                def observation():return app.source_service.observe(guest=False,timeout=5).get('vision')
                deadline=time.monotonic()+90
                while True:
                    view=observation();atomic(records/'latest-vision-observation.json',view)
                    if view and view.get('reference') and view['state']=='AVAILABLE':break
                    require(time.monotonic()<deadline,'VISION_NATIVE_FUNCTIONAL_RESULT_NOT_CONFIRMED');time.sleep(.1)
                if c.get('communicationCacheProof'):
                    facts=phase('native-communication-cache-path-functional',lambda:request('NATIVE'))
                    require(facts['storage']['imageManager']['installPath']=='/var/aos/downloads/vision-services/cm-images'
                        and all(row['seccomp']=='2' for row in facts['instances'].values()),'VISION_COMMUNICATION_CACHE_EFFECTIVE_CONFIG_CHANGED')
                    security=phase('native-security-after-communication-cache-path',lambda:request('OBSERVE'))
                    require(not security['scopedAvcs'] and security['nativeScopedAvcCount']==0,'VISION_NATIVE_FUNCTIONAL_AVC')
                    if c.get('groupAliasProof'):
                        configuration=phase('native-short-role-group-configuration',lambda:request('DIAGNOSE'))
                        require({r['name'].removeprefix('vision-'):r['groups'][0] for r in configuration['resourceFile'][1:]}==c['groupAliasProof']
                            and configuration['smVisibleResourceFile']==configuration['resourceFile'],'VISION_ROLE_GROUP_ALIASES_NOT_APPLIED')
                    result['outcome']='PASS_NATIVE_SHORT_ROLE_GROUPS_AND_RETAINED_SUCCESSORS' if c.get('groupAliasProof') else 'PASS_NATIVE_COMMUNICATION_CACHE_PATH_AND_RETAINED_SUCCESSORS';raise ConfigProofComplete
                if c.get('nativeNetworkDiagnosis'):
                    phase('read-only-native-network-configuration',lambda:request('NATIVE_NETWORK_DIAGNOSE',timeout=50))
                    result['outcome']='PASS_READ_ONLY_NATIVE_NETWORK_DIAGNOSIS';raise ConfigProofComplete
                if c.get('nativeSota'):
                    successor=c['nativeSota'];version='0.1.1'
                    storage=phase('independent-sota-capacity-preflight',lambda:request('STORAGE'))['space']
                    peak=max(2*successor['services']['perception']['bytes'],successor['services']['perception']['bytes']+2*successor['services']['assessment']['bytes'])+32*1024**2
                    require(storage['/var/aos/workdirs']['free']>=peak and storage['/var/aos/downloads']['free']>=successor['expandedBytes']+32*1024**2,
                        'VISION_NATIVE_SOTA_MEASURED_CAPACITY_REQUIRED')
                    current=instances
                    for role in ('perception','assessment'):
                        other='assessment' if role=='perception' else 'perception';pin=successor['services'][role]
                        require(not any(row['version']==version for row in preflight['services'][role]['versions']),'VISION_NATIVE_SOTA_VERSION_EXISTS_RECONCILE')
                        atomic(records/('sota-'+role+'-intent.json'),dict(attemptStarted=True,unitId=UNIT,serviceId=ids[role],version=version,sha256=pin['sha256']))
                        response=phase('publish-independent-'+role+'-successor',lambda role=role,pin=pin:cloud('upload',role=role,
                            bundle=str(records/('vision-'+role+'-'+version+'.tar.gz')),expectedSha256=pin['sha256'],
                            prepared=str(records/(role+'-successor-prepared.json')),preparedSha256=pin['preparedSha256'],
                            packageModule=str(records/'aos_package.py'),packageModuleSha256=payload['packageModuleSha256']))
                        atomic(records/('sota-'+role+'-response.json'),response);deadline=time.monotonic()+180
                        while True:
                            published=cloud('publication',role=role,deploymentId=response['deploymentId']);atomic(records/('sota-'+role+'-publication.json'),published)
                            if published['stage']=='READY':break
                            require(time.monotonic()<deadline,'VISION_NATIVE_SOTA_PUBLICATION_TIMEOUT');time.sleep(2)
                        deadline=time.monotonic()+150
                        while True:
                            after=request('NATIVE')['instances'];atomic(records/('sota-'+role+'-native-latest.json'),after)
                            value=after.get('vision-'+role)
                            if value and value['identity'].get('version')==version:break
                            require(time.monotonic()<deadline,'VISION_NATIVE_SOTA_INSTANCE_NOT_OBSERVED');time.sleep(.3)
                        require(value['identity']['sourceRevision']==successor['sourceRevision'] and value['identity'].get('processProfile')=='unix-only-seccomp-v1'
                            and value['seccomp']=='2' and value['nnp']=='1' and value['pid']!=current['vision-'+role]['pid']
                            and value['uid']==current['vision-'+role]['uid'] and value['groups']==current['vision-'+role]['groups']
                            and value['cpuMax']==current['vision-'+role]['cpuMax'] and value['memoryMax']==current['vision-'+role]['memoryMax']
                            and value['pidsMax']==current['vision-'+role]['pidsMax'] and value['noFileLimits']==current['vision-'+role]['noFileLimits']
                            and value['tmpFilesystemBytes']==current['vision-'+role]['tmpFilesystemBytes']
                            and value['resourceMounts']==current['vision-'+role]['resourceMounts']
                            and not value['credentialMountPresent'] and not value['forbiddenRolePathsPresent']
                            and all(int(value['capabilities'][key],16)==0 for key in ('CapEff','CapPrm','CapInh','CapAmb')),'VISION_NATIVE_SOTA_IDENTITY_SANDBOX_OR_QUOTA_CHANGED')
                        preserved=after.get('vision-'+other,{})
                        require(preserved.get('identity')==current['vision-'+other]['identity'] and preserved.get('uid')==current['vision-'+other]['uid']
                            and preserved.get('resourceMounts')==current['vision-'+other]['resourceMounts'],'VISION_NATIVE_SOTA_CHANGED_OTHER_SERVICE')
                        atomic(records/('sota-'+role+'-independence.json'),dict(otherVersionUnchanged=True,otherSourceAndResourcesUnchanged=True,
                            otherPidUnchanged=preserved['pid']==current['vision-'+other]['pid']))
                        deadline=time.monotonic()+20
                        while True:
                            visible=observation()
                            if visible and visible['state']=='AVAILABLE' and visible[role+'Version']==version:break
                            require(time.monotonic()<deadline,'VISION_NATIVE_SOTA_FUNCTIONAL_RESULT_NOT_CONFIRMED');time.sleep(.05)
                        atomic(records/('sota-'+role+'-functional.json'),visible);current=after
                    security=phase('native-functional-security-after-independent-sota',lambda:request('OBSERVE'))
                    require(not security['scopedAvcs'] and security['nativeScopedAvcCount']==0,'VISION_NATIVE_FUNCTIONAL_AVC')
                    phase('subject-after-independent-sota',lambda:cloud('subject-status',serviceIds=ids,subject=subject))
                    result['outcome']='PASS_NATIVE_INDEPENDENT_SOTA_AND_UNIX_ONLY_MAIN_PROCESSES'
                    result['fullVisionE2E']='PENDING_PERMANENT_IMAGE_AND_UI';raise ConfigProofComplete
                if c.get('nativeAdversarialProof'):
                    phase('actual-native-role-and-network-negatives',lambda:request('NATIVE_ROLE_PROOF',timeout=45))
                    before_loss=view;before_native=instances
                    phase('normal-camera-and-broker-input-loss',lambda:app.source_service.camera_ingress('stop'))
                    deadline=time.monotonic()+4
                    while True:
                        lost=observation()
                        if lost is not None and lost['reference'] is None and all(lost[k] is None for k in ('lead','path','plan')):break
                        require(time.monotonic()<deadline,'VISION_NATIVE_LOSS_DID_NOT_CLEAR_OUTPUT');time.sleep(.05)
                    atomic(records/'unavailable-after-real-input-loss.json',lost)
                    phase('normal-camera-and-broker-input-recovery',lambda:app.source_service.camera_ingress('start'))
                    deadline=time.monotonic()+20
                    while True:
                        recovered=observation()
                        if recovered and recovered['state']=='AVAILABLE' and recovered['reference'] and recovered['reference']!=before_loss['reference']:break
                        require(time.monotonic()<deadline,'VISION_NATIVE_INPUT_RECOVERY_NOT_CONFIRMED');time.sleep(.05)
                    atomic(records/'available-after-real-input-recovery.json',recovered)
                    after_native=phase('native-identities-after-input-recovery',lambda:request('NATIVE'))['instances']
                    require(all(after_native[name]['pid']==before_native[name]['pid'] for name in before_native),'VISION_NATIVE_INPUT_LOSS_RESTARTED_APPLICATION')
                    security=phase('native-functional-security-after-negatives-and-recovery',lambda:request('OBSERVE'))
                    require(not security['scopedAvcs'] and security['nativeScopedAvcCount']==0,'VISION_NATIVE_FUNCTIONAL_AVC')
                    result['outcome']='PASS_TRANSIENT_NATIVE_UNIX_ONLY_AND_INPUT_RECOVERY' if c.get('nativeUnixOnlyProof') else 'PASS_NATIVE_ROLE_NETWORK_LOSS_AND_RECOVERY'
                    result['applicationProcessFilter']='NOT_PACKAGED' if c.get('nativeUnixOnlyProof') else 'NOT_TESTED'
                    result['fullVisionE2E']='PENDING_INDEPENDENT_SOTA_PERMANENT_IMAGE_AND_UI';raise ConfigProofComplete
                samples=[];seen=set();began=time.monotonic()
                while time.monotonic()-began<180:
                    view=observation()
                    if view:
                        row={key:view[key] for key in ('reference','sequence','frame','cameraFrame','captureAgeMs','state','reason','imageMatched')}
                        row['elapsedSeconds']=round(time.monotonic()-began,3);samples.append(row)
                        if row['reference']:seen.add(row['reference'])
                    time.sleep(.15)
                ages=sorted(row['captureAgeMs'] for row in samples if row['captureAgeMs'] is not None)
                characterization=dict(seconds=round(time.monotonic()-began,2),uniqueObservedResults=len(seen),observedResultsPerSecond=len(seen)/(time.monotonic()-began),
                    captureToObservationAgeMs=dict(median=ages[len(ages)//2],p95=ages[min(len(ages)-1,int(len(ages)*.95))],maximum=max(ages)) if ages else None,
                    samples=samples,modelAccuracyQualified=False,soak=False)
                atomic(records/'native-characterization.json',characterization)
                require(len(seen)>=20,'VISION_NATIVE_CHARACTERIZATION_NO_CONTINUOUS_RESULTS')
                security=phase('native-functional-security-after-characterization',lambda:request('OBSERVE'))
                require(not security['scopedAvcs'] and security['nativeScopedAvcCount']==0,'VISION_NATIVE_FUNCTIONAL_AVC')
                phase('native-current-subject-after-characterization',lambda:cloud('subject-status',serviceIds=ids,subject=subject))
                if c.get('permanentSystem'):
                    result['apiPermanentPlatform']='PASS_NO_TRANSIENT_PLATFORM_OVERRIDES'
                    from vision_services_visual import visual
                    phase('headed-vision-ui-loss-and-recovery',lambda:visual(app,env,records,c,observation,request))
                    result.update(outcome='PASS_PERMANENT_VISION_API_AND_HEADED_BROWSER_UI',fullVisionE2E='ROOTFS_CLOUD_INVENTORY_DEFECT_OPEN',
                        rootfsCloudInventory='KNOWN_OMISSION_NOT_PASSED');raise ConfigProofComplete
                result['outcome']='PASS_NATIVE_TWO_SERVICE_CAMERA_CHARACTERIZATION_ONLY';result['fullVisionE2E']='PENDING_INDEPENDENT_SOTA_PERMANENT_IMAGE_AND_UI'
    except ConfigProofComplete:
        pass
    except Exception as error:
        result['outcome']='NOT_COMPLETE';result['code']=clean_error(error);result['errorFrames']=[dict(file=Path(f.filename).name,line=f.lineno) for f in traceback.extract_tb(error.__traceback__)[-4:]]
        if session is not None and session.poll() is None:
            try:atomic(records/'failure-native-diagnostics.json',request('DIAGNOSE'))
            except Exception as diagnostic_error:result['diagnosticCode']=clean_error(diagnostic_error)
    finally:
        if vm is not None and native is not None:
            with runtime_paths.installed_session(native):
                try:
                    if source_attempted:app.source_service.simulation('stop',target='test');WorkspaceService(env,app.source_service.driver).execute('close')
                    result['cleanup']['sourceStopped']=json.loads((native/JOURNAL).read_bytes())['source']['state']=='STOPPED'
                except Exception as error:result['cleanup']['sourceStopped']=False;result['sourceCleanupCode']=clean_error(error)
                if session is not None:
                    try:
                        if session.poll() is None:session.stdin.write('STOP\n');session.stdin.flush()
                        closed=receive(100);require(closed['phase']=='CLOSED','VISION_LIVE_GUEST_RESTORE_NOT_CONFIRMED');atomic(records/'native-restoration.json',closed['data'])
                        require(closed['data'] and all(closed['data'].values()),'VISION_LIVE_RESTORE_NOT_COMPLETE');session.stdin.close();session.wait(timeout=10)
                        result['cleanup']['permanentConfigAndPolicyUnchanged' if c.get('permanentSystem') else 'nativeConfigAndPolicyRestored']=session.returncode==0
                        if reader is not None:reader.join(timeout=2)
                    except Exception as error:result['cleanup']['nativeConfigAndPolicyRestored']=False;result['guestCleanupCode']=clean_error(error)
                try:result['cleanup']['vmStopped']=vm.execute('stop','test',timeout=150)['vehicles']['test']['state']=='COMPLETED'
                except Exception:result['cleanup']['vmStopped']=False
                state=json.loads((native/JOURNAL).read_bytes());result['cleanup'].update(sameVmAndUnit=state['vehicles']['test']['unitId']==UNIT and state['vehicles']['test']['localVmId']==VM,
                    retainedJournalsUnchanged=all((p/JOURNAL).read_bytes()==raw for p,raw in retained.items()))
        if awake is not None:awake.terminate();awake.wait(timeout=5);result['cleanup']['awakeHelperStopped']=True
        result['outcome']=final_outcome(result)
        result['seconds']=round(time.monotonic()-started,2);atomic(records/'result.json',result);print(json.dumps(result),flush=True)
    return 0 if result['outcome'].startswith('PASS_') and 'code' not in result else 1


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker',type=Path);parser.add_argument('--config',type=Path)
    for flag in ('resume-nosuid-proof','diagnose-peer-denial','native-services','resume-native','native-config-proof',
                 'native-delivery-reconcile','native-image-path-proof','native-calibration-diagnosis','calibrated-camera-proof','adversarial-proof','native-network-diagnosis','network-tools-proof','unix-only-proof','native-sota','communication-cache-proof'):
        parser.add_argument('--'+flag,action='store_true')
    parser.add_argument('--resume-native-exec',nargs='?',const=1,type=int,choices=(1,2))
    parser.add_argument('--camera-pose-diagnosis',nargs='?',const=1,type=int,choices=(1,2,3))
    a=parser.parse_args()
    if a.communication_cache_proof:a.native_sota=True
    if a.native_sota:a.unix_only_proof=True
    if a.unix_only_proof:a.network_tools_proof=True
    if a.network_tools_proof:a.native_network_diagnosis=True
    if a.native_network_diagnosis:a.adversarial_proof=True
    if a.adversarial_proof:a.calibrated_camera_proof=True
    if a.calibrated_camera_proof:a.camera_pose_diagnosis=3
    if a.camera_pose_diagnosis:a.resume_native_exec=2
    if a.resume_native_exec:a.native_calibration_diagnosis=True
    if a.native_calibration_diagnosis:a.native_image_path_proof=True
    if a.native_image_path_proof:a.native_delivery_reconcile=True
    if a.native_delivery_reconcile:a.resume_native=True
    if a.native_config_proof:a.resume_native=True
    if a.resume_native:a.native_services=True
    if a.worker:return worker(a.worker)
    import remote_harness as h
    from vision_vm_campaign import configuration
    c=configuration(a.config);name='vision-services-broker-live-02' if a.resume_nosuid_proof else 'vision-services-broker-live-01';records=Path(c['records'])/name;remote=Path(c['remoteRoot'])/name
    if a.diagnose_peer_denial:
        old_path=Path(c['records'])/'vision-services-broker-live-02';old_result=json.loads((old_path/'result.json').read_bytes());old_observed=json.loads((old_path/'latest-broker-observation.json').read_bytes())
        require(old_result['code']=='VISION_LIVE_GUEST_PROTOCOL_FAILED' and all(old_result['cleanup'].values())
            and old_observed['socketCount']==4 and old_observed['context'].rstrip('\x00').split(':')[2]=='vision_exchange_t'
            and not old_observed['scopedAvcs'],'VISION_PEER_DENIAL_OBSERVER_FAILURE_NOT_RECONCILED')
        name='vision-services-broker-live-03';records=Path(c['records'])/name;remote=Path(c['remoteRoot'])/name
    if a.native_services:
        previous=json.loads((Path(c['records'])/'vision-services-broker-live-03/result.json').read_bytes())
        require(previous['outcome']=='PASS_SOURCE_OWNED_NATIVE_BROKER_LIFECYCLE_ONLY' and all(previous['cleanup'].values()),'VISION_NATIVE_BROKER_LIFECYCLE_REQUIRED')
        name='vision-services-native-live-01';records=Path(c['records'])/name;remote=Path(c['remoteRoot'])/name
        if a.resume_native:
            failed=json.loads((records/'result.json').read_bytes())
            require(failed.get('code')=='VISION_NATIVE_INSTANCE_START_UNCONFIRMED' and all(failed['cleanup'].values()),'VISION_NATIVE_FAILED_ASSIGNMENT_RECONCILIATION_REQUIRED')
            name='vision-services-native-live-02';records=Path(c['records'])/name;remote=Path(c['remoteRoot'])/name
            if a.native_delivery_reconcile:
                prior_result=json.loads((records/'result.json').read_bytes());diagnostic=json.loads((records/'failure-native-diagnostics.json').read_bytes())
                require(prior_result.get('code')=='VISION_NATIVE_INSTANCE_START_UNCONFIRMED' and all(prior_result['cleanup'].values())
                    and any('not found (imagemanager.cpp:281)' in row for row in diagnostic['logs']['aos-sm.service']),'VISION_NATIVE_MISSING_SM_IMAGE_NOT_RECONCILED')
                name='vision-services-native-live-03';records=Path(c['records'])/name;remote=Path(c['remoteRoot'])/name
                if a.native_image_path_proof:
                    failed=json.loads((records/'result.json').read_bytes());diagnostic=json.loads((records/'failure-native-diagnostics.json').read_bytes())
                    require(failed.get('code')=='VISION_NATIVE_INSTANCE_START_UNCONFIRMED' and all(failed['cleanup'].values())
                        and any('Failed to unpack layer' in row and 'not enough space' in row for row in diagnostic['logs']['aos-sm.service']),'VISION_NATIVE_IMAGE_CAPACITY_FAULT_REQUIRED')
                    name='vision-services-native-live-04';records=Path(c['records'])/name;remote=Path(c['remoteRoot'])/name
                    if a.native_calibration_diagnosis:
                        prior=json.loads((records/'result.json').read_bytes());require(prior.get('code')=='VISION_NATIVE_FUNCTIONAL_RESULT_NOT_CONFIRMED' and prior['servicesDeployed'] and all(prior['cleanup'].values()),'VISION_NATIVE_CALIBRATION_FAULT_NOT_RECONCILED')
                        name='vision-services-native-live-05';records=Path(c['records'])/name;remote=Path(c['remoteRoot'])/name
                        if a.resume_native_exec:
                            failed=json.loads((records/'result.json').read_bytes());require(failed.get('code')=='VISION_CALIBRATION_EXISTING_OCI_ID_REQUIRED' and all(failed['cleanup'].values()),'VISION_NATIVE_OCI_DISCOVERY_FAULT_NOT_RECONCILED')
                            name='vision-services-native-live-06';records=Path(c['records'])/name;remote=Path(c['remoteRoot'])/name
                            if a.resume_native_exec==2:
                                prior=json.loads((records/'result.json').read_bytes());discovery=json.loads((records/'failure-native-diagnostics.json').read_bytes())['readOnlyExecDiscovery']
                                require(prior.get('code')=='VISION_CALIBRATION_NATIVE_READ_ONLY_EXEC_FAILED' and all(prior['cleanup'].values())
                                    and discovery['lastExec']['stderr']=='fchown std stream 0: Permission denied\n','VISION_NATIVE_EXEC_STDIO_DENIAL_NOT_RECONCILED')
                                name='vision-services-native-live-07';records=Path(c['records'])/name;remote=Path(c['remoteRoot'])/name
                                if a.camera_pose_diagnosis:
                                    last=json.loads((records/'result.json').read_bytes());cal=json.loads((records/'read-only-actual-native-calibration-diagnosis.json').read_bytes())['facts']
                                    require(last['outcome']=='PASS_READ_ONLY_NATIVE_RESOURCE_CALIBRATION_DIAGNOSIS' and all(last['cleanup'].values()) and cal['reason']=='MOUNT_INCOMPATIBLE','VISION_NATIVE_MOUNT_DIAGNOSIS_REQUIRED')
                                    name='vision-services-native-live-08';records=Path(c['records'])/name;remote=Path(c['remoteRoot'])/name
                                    if a.camera_pose_diagnosis>=2:
                                        failed=json.loads((records/'result.json').read_bytes())
                                        require(failed.get('code')=='VISION_POSE_EXISTING_CAMERA_REQUIRED' and all(failed['cleanup'].values()),'VISION_POSE_SELECTOR_FAILURE_NOT_RECONCILED')
                                        name='vision-services-native-live-09';records=Path(c['records'])/name;remote=Path(c['remoteRoot'])/name
                                        if a.camera_pose_diagnosis==3:
                                            failed=json.loads((records/'result.json').read_bytes());inventory=json.loads((records/'read-only-camera-inventory.json').read_bytes())
                                            require(failed.get('code')=='VISION_POSE_EXISTING_CAMERA_REQUIRED' and all(failed['cleanup'].values()) and inventory['cameras']==[],'VISION_POSE_EMPTY_CACHE_FAULT_REQUIRED')
                                            name='vision-services-native-live-10';records=Path(c['records'])/name;remote=Path(c['remoteRoot'])/name
                                            if a.calibrated_camera_proof:
                                                done=json.loads((records/'result.json').read_bytes());pose=json.loads((records/'read-only-existing-camera-parent-pose.json').read_bytes())['facts']
                                                require(all(done['cleanup'].values()) and pose['sameSnapshot'] and len(pose['samples'])==12
                                                    and all(row['unrealErrorMetres']<.00002 and row['correctedErrorMetres']>.01 for row in pose['samples']),
                                                    'VISION_MEASURED_UNREAL_ATTACHMENT_PROOF_REQUIRED')
                                                name='vision-services-native-live-11';records=Path(c['records'])/name;remote=Path(c['remoteRoot'])/name
                                                if a.adversarial_proof:
                                                    prior=json.loads((records/'result.json').read_bytes())
                                                    require(prior['outcome']=='PASS_NATIVE_TWO_SERVICE_CAMERA_CHARACTERIZATION_ONLY' and all(prior['cleanup'].values()),'VISION_NATIVE_CALIBRATED_CHARACTERIZATION_REQUIRED')
                                                    name='vision-services-native-live-12';records=Path(c['records'])/name;remote=Path(c['remoteRoot'])/name
                                                    if a.native_network_diagnosis:
                                                        failed=json.loads((records/'result.json').read_bytes());last=json.loads((records/'failure-native-diagnostics.json').read_bytes())['readOnlyExecDiscovery']['lastExec']
                                                        require(failed.get('code')=='VISION_CALIBRATION_NATIVE_READ_ONLY_EXEC_FAILED' and all(failed['cleanup'].values())
                                                            and last['role']=='perception' and 'ConnectionRefusedError: [Errno 111] Connection refused' in last['stderr'],'VISION_NATIVE_NETWORK_REFUSAL_DIAGNOSIS_REQUIRED')
                                                        name='vision-services-native-live-13';records=Path(c['records'])/name;remote=Path(c['remoteRoot'])/name
                                                        if a.network_tools_proof:
                                                            previous=json.loads((records/'result.json').read_bytes());error=json.loads((records/'guest-error-response.json').read_bytes())
                                                            require(previous.get('code')=='ValueError' and all(previous['cleanup'].values()) and error['data']['code']=='FileNotFoundError',
                                                                'VISION_NATIVE_NETWORK_EVIDENCE_TOOL_FAILURE_REQUIRED')
                                                            name='vision-services-native-live-14';records=Path(c['records'])/name;remote=Path(c['remoteRoot'])/name
                                                            if a.unix_only_proof:
                                                                previous=json.loads((records/'result.json').read_bytes())
                                                                require(previous['outcome']=='PASS_READ_ONLY_NATIVE_NETWORK_DIAGNOSIS' and all(previous['cleanup'].values()),'VISION_NATIVE_EFFECTIVE_NETWORK_RULES_REQUIRED')
                                                                name='vision-services-native-live-15';records=Path(c['records'])/name;remote=Path(c['remoteRoot'])/name
                                                                if a.native_sota:
                                                                    previous=json.loads((records/'result.json').read_bytes())
                                                                    require(previous['outcome']=='PASS_TRANSIENT_NATIVE_UNIX_ONLY_AND_INPUT_RECOVERY' and all(previous['cleanup'].values()),'VISION_NATIVE_UNIX_ONLY_TRANSIENT_REQUIRED')
                                                                    name='vision-services-native-live-16';records=Path(c['records'])/name;remote=Path(c['remoteRoot'])/name
                                                                    if a.communication_cache_proof:
                                                                        previous=json.loads((records/'result.json').read_bytes());recovery=json.loads((Path(c['records'])/'vision-services-recovery-01/result.json').read_bytes())
                                                                        require(previous['outcome']=='PASS_NATIVE_INDEPENDENT_SOTA_AND_UNIX_ONLY_MAIN_PROCESSES' and all(previous['cleanup'].values())
                                                                            and recovery['outcome']=='PASS_SAME_VM_CHECKPOINT_RECOVERY' and all(recovery['cleanup'].values()),'VISION_SUCCESSOR_RECOVERY_REQUIRED')
                                                                        name='vision-services-native-live-17';records=Path(c['records'])/name;remote=Path(c['remoteRoot'])/name
            if a.native_config_proof:
                name='vision-services-native-config-02';records=Path(c['records'])/name;remote=Path(c['remoteRoot'])/name
                prior_diagnostic=json.loads((Path(c['records'])/'vision-services-native-config-01/result.json').read_bytes())
                require(prior_diagnostic.get('code')=='ValueError' and all(prior_diagnostic['cleanup'].values()),'VISION_NATIVE_CONFIG_OBSERVER_FAULT_RECONCILIATION_REQUIRED')
    if a.resume_nosuid_proof:
        old_path=Path(c['records'])/'vision-services-broker-live-01';old_result=json.loads((old_path/'result.json').read_bytes());old_observed=json.loads((old_path/'latest-broker-observation.json').read_bytes())
        require(old_result['code']=='VISION_LIVE_BROKER_NOT_HEALTHY' and all(old_result['cleanup'].values()) and old_observed['socketCount']==0
            and any('{ nosuid_transition }' in row and 'vision_exchange_t' in row for row in old_observed['scopedAvcs']),'VISION_NOSUID_PROOF_FAULT_NOT_RECONCILED')
    require(not records.exists(),'VISION_LIVE_ATTEMPT_EXISTS_RECONCILE');records.mkdir(mode=0o700)
    prior=Path(c['records'])/'vision-services-exchange-primitives-01';proof=json.loads((prior/'result.json').read_bytes())
    require(proof['outcome']=='PASS_NATIVE_EXCHANGE_PRIMITIVES_AND_STOCK_RESTORATION' and all(proof['cleanup'].values()),'VISION_LIVE_PRIMITIVE_PROOF_REQUIRED')
    files=[Path(__file__).with_name('vision_services_primitives_guest.py')]
    old=json.loads((prior/'context.json').read_bytes())
    platform=Path(__file__).resolve().parents[3]/'vision-camera-platform'
    primitive=Path('/Volumes/SDV-Dev/sdv/build/vision-services/exchange-primitives-01')
    files += [platform/'tools/vision_cpuinfo_projection.py',platform/'tests/fixtures/vision-native-exchange/aos-vision-exchange.service',
        primitive/'aos-vision-exchange-proof',primitive/'vision_exchange.pp',prior/'camera-access',
        Path('/Volumes/SDV-Dev/sdv/build/vision-bootstrap/0.1.0/evidence/camera-store-policy-loader-01/vision-policy-load')]
    for path in files:
        if path.name!='vision_services_primitives_guest.py':require(h.digest(path)==old['nativePrimitives']['files'][path.name],'VISION_LIVE_RETAINED_INPUT_CHANGED')
    delivered=json.loads((Path(c['records'])/('vision-services-host-03' if a.calibrated_camera_proof else 'vision-services-host-02' if a.native_services else 'vision-services-host-01')/'result.json').read_bytes())
    source=Path(__file__).resolve();context=dict(packageRoot=c['main']['packageRoot'],baseManifest=c['main']['manifestSha256'],
        bundle=delivered['bundle'],bootstrapManifest=delivered['manifestSha256'],workerSha256=h.digest(source),files={path.name:h.digest(path) for path in files})
    if a.native_config_proof:context['nativeConfigProof']=True
    if a.native_delivery_reconcile:context['nativeDeliveryReconcile']=True
    if a.native_image_path_proof:context['expectedAssignedRoles']=['perception','assessment']
    if a.native_calibration_diagnosis and not a.calibrated_camera_proof:context['nativeCalibrationDiagnosis']=True
    if a.camera_pose_diagnosis and not a.calibrated_camera_proof:context['cameraPoseDiagnosis']=True
    if a.adversarial_proof:context['nativeAdversarialProof']=True
    if a.native_network_diagnosis and not a.unix_only_proof:context['nativeNetworkDiagnosis']=True
    if a.unix_only_proof:context['nativeUnixOnlyProof']=True
    if a.native_services:
        import shutil
        build=Path('/Volumes/SDV-Dev/sdv/build/vision-services');signed=json.loads((build/'signed-03/result.json').read_bytes())
        require(signed['outcome']=='PASS_TWO_INDEPENDENT_OFFICIAL_VISION_SIGNATURES' and signed['scratchRemoved'],'VISION_NATIVE_SIGNED_INPUTS_REQUIRED')
        package=Path(__file__).resolve().parents[3]/'vision-pilot-services/tools/aos_package.py'
        files.extend([Path(__file__).with_name('vision_services_cloud.py'),package]);services={}
        for role,pin in signed['services'].items():
            archive=build/'signed-03'/('vision-'+role+'-0.1.0.tar.gz');require(archive.stat().st_size==pin['bytes'] and h.digest(archive)==pin['sha256'],'VISION_NATIVE_SIGNED_INPUT_CHANGED')
            prepared=records/(role+'-prepared.json');shutil.copyfile(build/'packages-01'/role/'prepared.json',prepared);prepared.chmod(0o600)
            files.extend([archive,prepared]);services[role]=dict(sha256=pin['sha256'],preparedSha256=h.digest(prepared))
        context['nativeServices']=dict(services=services,packageModuleSha256=h.digest(package),allocation=json.loads((Path(__file__).resolve().parents[2]/'contracts/vision-vm/services-allocation.v1.json').read_bytes()),applicationSourceRevision='cd924e2120dcd3578274829f68995366a7e042d1')
        old_context=json.loads((Path(c['records'])/'vision-services-closure-01/context.json').read_bytes())
        known=dict(old_context['measurements']['files'])
        for i in range(2,6):
            old_probe=json.loads((Path(c['records'])/('vision-services-closure-'+str(i).zfill(2))/'context.json').read_bytes())['measurements']['request']['probeSha256']
            known['runtime_measurement-'+old_probe[:16]+'.py']=old_probe
        inventory=json.loads((Path(c['records'])/'vision-services-exchange-preflight-02/native-exchange-storage-preflight.json').read_bytes())['facts']['ownedMeasurementInputs']
        for role in ('perception','assessment'):
            original=build/'closure-06'/(role+'-rootfs.tar.gz');require(h.digest(original)==known[original.name],'VISION_MEASUREMENT_RETAINED_ARCHIVE_CHANGED')
        if a.resume_native:
            prior=Path(c['records'])/'vision-services-native-live-01'
            published={role:json.loads((prior/('publication-'+role+'-latest.json')).read_bytes()) for role in ('perception','assessment')}
            retired=json.loads((prior/'retire-verified-measurement-duplicates.json').read_bytes())
            require(retired['facts']['outcome']=='PASS_OWNED_MEASUREMENT_DUPLICATES_RETIRED','VISION_NATIVE_MEASUREMENT_RETIREMENT_NOT_RECONCILED')
            context['resumeNative']=dict(serviceIds={role:row['serviceId'] for role,row in published.items()},versionIds={role:row['versionId'] for role,row in published.items()},subject=json.loads((prior/'vision-subject.json').read_bytes()))
            if not a.native_config_proof:
                observed=json.loads((Path(c['records'])/'vision-services-native-config-02/effective-native-resource-configuration.json').read_bytes())['facts']
                require(observed['smVisibleResourceFile']==observed['resourceFile'] and len(observed['resourceFile'])==5
                    and any("Can't get resources info: err=not enough memory" in row for row in observed['logs']['aos-sm.service']),'VISION_FIVE_RESOURCE_CAPACITY_FAULT_REQUIRED')
                compiled=Path('/Volumes/SDV-Dev/sdv/build/vision-services/resource-capacity-04');receipt=json.loads((compiled/'result.json').read_bytes())
                require(receipt['outcome']=='PASS_TARGETED_FIVE_RESOURCE_NATIVE_OWNER_COMPILE' and receipt['nodeResources']==5 and receipt['builderStopped'],'VISION_TARGETED_CAPACITY_COMPILE_REQUIRED')
                for name,pin in receipt['files'].items():
                    candidate=compiled/name;require(h.digest(candidate)==pin['sha256'],'VISION_CAPACITY_BINARY_CHANGED');files.append(candidate)
                context['nativeOwnerCapacityFive']=True
                if a.native_image_path_proof:
                    plan=records/'native-image-path-proof.json';atomic(plan,dict(schemaVersion=1,imagePath='/var/aos/downloads/vision-services/sm-images',preserveOriginal=True,
                        **({'reuseRecordedCache':True} if a.native_calibration_diagnosis else {}),
                        **(dict(communicationInstallPath='/var/aos/downloads/vision-services/cm-images',expectedServiceSourceRevision='a10c6f354866e5d3e839ee59a18344bb7cad96df') if a.communication_cache_proof else {})));files.append(plan)
        else:context['measurementInputs']={row['name']:dict(bytes=row['bytes'],sha256=known[row['name']]) for row in inventory}
        context['files']={path.name:h.digest(path) for path in files}
        if a.native_sota:
            signed_successor=json.loads((build/'signed-04/result.json').read_bytes())
            require(signed_successor['outcome']=='PASS_TWO_INDEPENDENT_OFFICIAL_VISION_SUCCESSOR_SIGNATURES' and signed_successor['scratchRemoved'],'VISION_NATIVE_SOTA_SIGNATURES_REQUIRED')
            successors={};expanded=0;source_revision=None
            for role,pin in signed_successor['services'].items():
                archive=build/'signed-04'/('vision-'+role+'-0.1.1.tar.gz')
                require(pin['version']=='0.1.1' and archive.stat().st_size==pin['bytes'] and h.digest(archive)==pin['sha256'],'VISION_NATIVE_SOTA_INPUT_CHANGED')
                prepared=records/(role+'-successor-prepared.json');shutil.copyfile(build/'packages-02'/role/'prepared.json',prepared);prepared.chmod(0o600)
                closure=json.loads((build/'closure-09'/role/'closure.json').read_bytes());expanded+=closure['bytes']
                require(source_revision in (None,pin['sourceRevision']),'VISION_NATIVE_SOTA_SOURCE_MISMATCH');source_revision=pin['sourceRevision']
                successors[role]=dict(sha256=pin['sha256'],bytes=pin['bytes'],preparedSha256=h.digest(prepared));files.extend([archive,prepared])
            if a.communication_cache_proof:
                context['currentNative']=dict(sourceRevision=source_revision,versionIds={role:json.loads((Path(c['records'])/'vision-services-native-live-16'/('sota-'+role+'-publication.json')).read_bytes())['versionId'] for role in successors})
                context['communicationCacheProof']=True
            else:context['nativeSota']=dict(services=successors,expandedBytes=expanded,sourceRevision=source_revision)
            context['files']={path.name:h.digest(path) for path in files}
    guest_names={'vision_services_primitives_guest.py','vision_cpuinfo_projection.py','aos-vision-exchange.service','aos-vision-exchange-proof',
        'vision_exchange.pp','camera-access','vision-policy-load','aos_sm_app','aos_cm_app','native-image-path-proof.json'}
    context['guestFiles']={name:pin for name,pin in context['files'].items() if name in guest_names}
    atomic(records/'context.json',context);t=c['transport'];h.remote(t,'umask 077\nmkdir '+shlex.quote(str(remote)),timeout=15)
    options=h.ssh_args(t)[1:-1];options.remove('-T');i=options.index('-b');options[i:i+2]=['-o','BindAddress='+options[i+1]]
    h.run(['/usr/bin/scp',*options,str(source),str(records/'context.json'),*map(str,files),t['user']+'@'+t['host']+':'+str(remote)+'/'],timeout=30)
    python=c['main']['packageRoot']+'/demo-artifacts/aosedge-sdv-demo/host-runtime/python/bin/python3.12'
    process=subprocess.Popen(h.ssh_args(t)+[shlex.join([python,'-I','-B',str(remote/source.name),'--worker',str(remote/'context.json')])],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    with (records/'progress.jsonl').open('w') as log:
        for line in process.stdout:require(log.tell()<1024**2,'VISION_LIVE_PROGRESS_LIMIT');log.write(line);log.flush();print(line.strip(),flush=True)
    exit_code=process.wait(timeout=10);diagnostic=process.stderr.read(8192)
    collect='import pathlib,json;root=pathlib.Path('+repr(str(remote))+');print(json.dumps({p.name:json.loads(p.read_bytes()) for p in root.glob("*.json") if p.name!="context.json" and p.stat().st_size<2*1024**2}))'
    values=json.loads(h.remote(t,shlex.join([python,'-I','-B','-c',collect]),timeout=20))
    for name,value in values.items():atomic(records/name,value)
    atomic(records/'transport.json',dict(exit=exit_code,stderrPresent=bool(diagnostic)));return exit_code


if __name__=='__main__':raise SystemExit(main())
