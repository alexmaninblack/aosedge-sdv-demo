#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""One permanent Source/Camera/native-Aos acceptance on the fresh .5 M4 VM."""
import base64
import hashlib
import json
from pathlib import Path
import re
import runpy
import shlex
import socket
import ssl
import subprocess
import sys
import time
import uuid


class FirstReselectProofComplete(Exception):pass


def require(ok,code):
    if not ok:raise ValueError(code)


def pairs(observation):
    """Only trusted native reader body hashes, current core and real metadata."""
    epoch=observation.get('health',{}).get('componentEpoch');out=[]
    for row in observation.get('messages',[]):
        if row.get('probe')!='LIVE_METADATA' or row.get('bytesVerified') is not True:continue
        value=row.get('value',{});frames=value.get('frames',[])
        if value.get('componentEpoch')!=epoch or len(frames)!=2:continue
        try:
            a,b=frames;uuid.UUID(a['sourceId']);uuid.UUID(a['sourceEpoch']);uuid.UUID(epoch)
            good=(all(a[k]==b[k] for k in ('sourceId','sourceEpoch','cameraId','calibrationId'))
                and a['frame']<b['frame'] and 80000000<=b['simulationTimeNs']-a['simulationTimeNs']<=120000000
                and all(re.fullmatch('[a-f0-9]{64}',v['sha256']) for v in frames))
            if good:out.append(value)
        except (KeyError,ValueError,TypeError,AttributeError):continue
    return out


def main():
    context=Path(sys.argv[1]);c=json.loads(context.read_bytes());records=context.parent
    require(not (records/'result.json').exists(),'FRESH_ACCEPTANCE_EXISTS_RECONCILE')
    result=dict(scenario='VISION_FRESH_PERMANENT_INGRESS_ACCEPTANCE',outcome='NOT_COMPLETE',phases=[],cleanup={},
        fullVisionE2E='NOT_RUN',perception='NOT_RUN',assessment='NOT_RUN',cloudMutation=False)
    began=time.monotonic();vm=app=env=None;native=None;retained={};source_started=False;camera_attempted=False;camera_confirmed=False;caffeinate=None
    def record(name,value):
        p=records/name;p.write_text(json.dumps(value,indent=2)+'\n');p.chmod(0o600)
    try:
        package=Path(c['main']['packageRoot']);bundle=Path(c['bundle'])
        require(subprocess.check_output(['/usr/sbin/sysctl','-n','hw.model'],text=True).strip()=='Mac16,8','M4_REQUIRED')
        require('"CGSSessionScreenIsLocked"=Yes' not in subprocess.check_output(['/usr/sbin/ioreg','-n','Root','-d1'],text=True),'M4_DESKTOP_LOCKED')
        require(hashlib.sha256((package/'application-manifest.json').read_bytes()).hexdigest()==c['main']['manifestSha256'],'BASE_CHANGED')
        for name,pin in c['files'].items():require(hashlib.sha256((records/name).read_bytes()).hexdigest()==pin,'FRESH_ACCEPTANCE_INPUT_CHANGED')
        helpers=runpy.run_path(str(records/'vision_ingress_live_worker.py'))
        evidence=helpers['evidence'];inactive=helpers['inactive_native_capabilities']
        def phase(name,action):
            print(json.dumps(dict(stage=name,state='STARTED')),flush=True);start=time.monotonic();value=action()
            record(name+'.json',dict(seconds=round(time.monotonic()-start,2),facts=evidence(value)))
            result['phases'].append(dict(stage=name,seconds=round(time.monotonic()-start,2)));record('progress.json',result)
            print(json.dumps(dict(stage=name,state='COMPLETE')),flush=True);return value
        subprocess.run(['codesign','--verify','--deep','--strict','-R',
            '=identifier "org.aosedge.sdvlab.vision.bootstrap" and anchor apple generic and certificate leaf[subject.OU] = "3NF57VKB3V"',str(bundle)],check=True,capture_output=True,timeout=120)
        sys.path.insert(0,str(package/'aosedge-sdv-demo/apps/demo-orchestrator/src'))
        import aosedge_demo_orchestrator
        from aosedge_demo_orchestrator import runtime_paths
        tooling=bundle/'Contents/Resources/tooling/aosedge-sdv-demo/apps/demo-orchestrator/src'
        aosedge_demo_orchestrator.__path__.insert(0,str(tooling/'aosedge_demo_orchestrator'))
        from aosedge_demo_orchestrator import vision_bootstrap as v
        from aosedge_demo_orchestrator.environment import EnvironmentService,JOURNAL
        from aosedge_demo_orchestrator.vm import VMService,access_path
        from aosedge_demo_orchestrator.units import UnitService
        from aosedge_demo_orchestrator.status import load_configuration,read_json
        from aosedge_demo_orchestrator.guest_access import ssh_command
        from aosedge_demo_orchestrator.cloud_connection import selected_domain,cloud_binding
        from aosedge_demo_orchestrator.cloud_runtime import launch
        from aosedge_demo_orchestrator.application import DemoOrchestrator
        from aosedge_demo_orchestrator.workspace import WorkspaceService
        from aosedge_demo_orchestrator import source_authentication as authentication
        if c.get('transientFirstReselect'):
            from aosedge_demo_orchestrator import vision_source_guest as projection
            candidate=runpy.run_path(str(records/'vision_pending_reselect_proof.py'))['candidate']
            original_script=projection.script;original_source=Path(projection.__file__).read_text();updated=candidate(original_source)
            def transient_script(request,**kwargs):
                value=original_script(request,**kwargs);require(value.count(repr(original_source))==1,'PROJECTION_PROOF_BINDING_CHANGED')
                return value.replace(repr(original_source),repr(updated))
            projection.script=transient_script
        verified=v.verify(bundle,c['main']['manifestSha256']);require(verified.manifest_sha256==c['bootstrapManifestSha256'] and v.VERSION=='6.1.1-vision-camera.5','FRESH_BOOTSTRAP_CHANGED')
        native=Path.home()/v.INSTANCE_NAME;before=read_json(native/JOURNAL);item=before['vehicles']['test']
        require(item['unitId']!='4374bcb2-0613-419c-8ac9-e8458358c91c' and item['runtime']['state']==before.get('source',{}).get('state','STOPPED')=='STOPPED','FRESH_IDLE_UNIT_REQUIRED')
        identity={k:item[k] for k in ('unitId','nodeId','localVmId','overlay')}
        resume=Path(c['resumeFrom']) if c.get('resumeFrom') else None
        if resume:
            require(resume.parent==records.parent and resume.name=='vision-fresh-accept-07','READER_RESUME_SCOPE_INVALID')
            prior=json.loads((resume/'result.json').read_bytes())
            require(prior.get('code')=='PERMANENT_OBSERVATION_TIMEOUT' and prior.get('cameraUpgrade')=='PASS_SAME_STORE_NATIVE_OEM'
                and all(prior['cleanup'].values()),'READER_RESUME_NOT_RECONCILED')
            prior_context=json.loads((resume/'context.json').read_bytes())
            require(prior_context['files']['vision-camera-probe']==c['files']['vision-camera-probe'] and prior_context['camera']==c['camera'],'READER_RESUME_INPUT_CHANGED')
        retained={Path.home()/n:(Path.home()/n/JOURNAL).read_bytes() for n in v.RETAINED_INSTANCE_NAMES}
        caffeinate=subprocess.Popen(['/usr/bin/caffeinate','-d','-i','-w',str(__import__('os').getpid())],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        with runtime_paths.installed_session(native):
            env=EnvironmentService(catalog=v.SignedVisionCatalog(verified),vm_profile=v.VM_PROFILE)
            vm=VMService(env,progress=lambda text:print(json.dumps(dict(stage='native-owner',message=str(text)[:110])),flush=True));units=UnitService(vm)
            app=DemoOrchestrator(environment_service=env,vm_service=vm);config=load_configuration(native)
            sdk,sdk_env=launch(native,config['cloudPython'],'unit_cloud.py')
            scope=dict(setupProfile=v.PROFILE,version='0.1.0',cloudDomain=selected_domain(before),ownerId=cloud_binding(before)['ownerId'],
                oemOwner=cloud_binding(before)['ownerId'],spOwner=config['cloudProfiles']['service-provider']['expectedOwnerId'],
                oemCredential=str(config['cloudProfiles']['oem-delivery']['credential']),spCredential=str(config['cloudProfiles']['service-provider']['credential']),
                vehicles=dict(test={k:item[k] for k in ('unitId','systemUid','unitSetId','nodeId')}),
                binary=str(records/'vision-camera-probe'),binarySha256=c['files']['vision-camera-probe'])
            scope['vehicles']['test']['nodeHardwareId']=item['cloud']['identity']['nodeHardwareId']
            def sdk_call(filename,request,timeout=180):
                done=subprocess.run([sdk[0],'-I','-B',str(records/filename),str(tooling)],input=json.dumps(request),text=True,capture_output=True,env=sdk_env,timeout=timeout)
                require(done.returncode==0 and len(done.stdout)<262144,'ACCEPTANCE_SDK_UNAVAILABLE');value=json.loads(done.stdout)
                if not value.get('ok'):record('sdk-error.json',value);raise ValueError(value.get('reason','ACCEPTANCE_SDK_FAILED'))
                return value['data']
            def fixture(action,**extra):return sdk_call('vision_camera_fixture_cloud.py',dict(scope,action=action,**extra))
            packet=dict(authorized=True,recoveryFirst=True,rootfsVersion='6.1.1-vision-camera.5',cameraVersion='0.1.1',readVersion='0.1.4',revokeVersion='0.1.5')
            def component(action,kind='aos-vision-vm-1.0.0-main-qemuarm64-camera-access',**extra):
                version='6.1.1-vision-camera.5' if kind.endswith('-rootfs') else '0.1.1'
                if resume and kind.endswith('-camera-access') and action=='status':
                    extra.setdefault('deploymentId',json.loads((resume/'camera-upload.json').read_bytes())['facts']['deploymentId'])
                return sdk_call('vision_permanent_component_cloud.py',dict(scope,action=action,componentType=kind,version=version,permanentDelivery=packet,**extra),600)
            def guest(code,timeout=30):
                import textwrap
                wrapped='import json,traceback\ntry:\n'+textwrap.indent(code,' ')+'\nexcept Exception as e:\n print(json.dumps(dict(guestError=type(e).__name__,line=traceback.extract_tb(e.__traceback__)[-1].lineno)))\n'
                current=read_json(native/JOURNAL)['vehicles']['test']
                done=subprocess.run(ssh_command(access_path(native,'test'),current['sshPort'],5),input="python3 - <<'FRESH_ACCEPTANCE'\n"+wrapped+"\nFRESH_ACCEPTANCE\n",text=True,capture_output=True,timeout=timeout)
                require(done.returncode==0 and len(done.stdout)<2**21,'ACCEPTANCE_GUEST_UNAVAILABLE');value=json.loads(done.stdout)
                if 'guestError' in value:record('guest-error.json',value);raise ValueError('ACCEPTANCE_GUEST_PROBE_FAILED')
                return value
            observation=(records/'vision_ingress_observation.py').read_text().replace("'2200'","'500'").replace("if __name__=='__main__':print(json.dumps(observe()))",'print(json.dumps(observe()))')
            def observe():return guest(observation)
            def current_pairs(observed):
                source_id=read_json(native/JOURNAL)['source']['runId']
                return [p for p in pairs(observed) if p['frames'][0]['sourceId']==source_id]
            def until(predicate,timeout=60):
                end=time.monotonic()+timeout;last=None
                while time.monotonic()<end:
                    last=observe()
                    if predicate(last):return last
                    time.sleep(1)
                record('last-observation.json',evidence(last));raise ValueError('PERMANENT_OBSERVATION_TIMEOUT')
            boot=phase('fresh-retained-start',lambda:vm.execute('start','test',timeout=150));require(boot['vehicles']['test']['state']=='COMPLETED','FRESH_START_INCOMPLETE')
            def online():
                with env._writer():return units._wait(read_json(native/JOURNAL),'test',lambda u:u and u['online_status']=='Online','CLOUD_ONLINE',timeout=60)
            phase('fresh-unit-online',online)
            phase('reader-process-before-source',observe)
            root=phase('fifth-rootfs-cloud-status',lambda:component('status','aos-vision-vm-1.0.0-main-qemuarm64-rootfs'))
            require(any((r.get('installed_component') or {}).get('version')=='6.1.1-vision-camera.5' and not r.get('pending_component') for r in root['unit']['components'] or []),'FIFTH_ROOTFS_NOT_CONFIRMED')
            base_scope={k:value for k,value in scope.items() if k in ('setupProfile','version','vehicles','ownerId','cloudDomain')}
            reuse=c['existingPublication'];bootstrap=json.loads((verified.resources/'bootstrap.json').read_bytes())
            require(reuse['ownerId']==scope['ownerId'] and reuse['cloudDomain']==scope['cloudDomain']
                and reuse['payloadSha256']==bootstrap['cameraPayload']['sha256'],'INITIAL_CAMERA_INPUT_CHANGED')
            base_scope['deploymentId']=reuse['deploymentId']
            if not resume:
                baseline=phase('initial-camera-catalog',lambda:units._cloud('vision-camera-status',**base_scope))
                require(baseline['publication']['stage']=='READY','INITIAL_CAMERA_CATALOG_NOT_READY')
                record('initial-camera-send-intent.json',dict(unitId=item['unitId'],versionId=baseline['publication']['versionId'],attemptStarted=True))
                result['cloudMutation']=True
                phase('initial-camera-send',lambda:units._cloud('vision-camera-send',**base_scope,updateComponentId=baseline['publication']['versionId']))
            source_started=True
            phase('normal-source-start',lambda:app.source_service.simulation('start',target='test'))
            phase('normal-source-enrollment',app.source_service.initialize_test)
            def physical_safe_stop():
                operation=str(uuid.uuid4());record('physical-safe-stop-intent.json',dict(operationId=operation,action='SAFE_STOP'))
                with env._writer(),app.source_service.driver.operation():
                    state=read_json(native/JOURNAL);driver=app.source_service.driver;source=state['source']
                    driver.rpc(source,'safe_stop',operation);value=driver.wait(source,operation,'SAFE_STOP')
                    if value.get('held'):driver.rpc(source,'release',operation)
                    final=driver.ready(state);frame=final.get('frame') or {}
                    require(final.get('fresh') and not final.get('held') and frame.get('activeMode')=='SAFE_STOP'
                        and frame.get('speedKmh',float('inf'))<=.5 and frame.get('brake',0)>=.99,'PHYSICAL_SAFE_STOP_UNCONFIRMED')
                    return dict(physicalSafeStop=True,held=False)
            phase('initial-physical-safe-stop',physical_safe_stop)
            native_snapshot=(records/'vision_delivery_guest.py').read_text()+"\nprint(json.dumps(run('snapshot')))\n"
            initial=phase('initial-camera-activation',lambda:guest(native_snapshot,45))
            require(initial['rootfsVersion']=='VERSION="6.1.1-vision-camera.5"' and initial['camera']['version']==('0.1.1' if resume else '0.1.0') and initial['enforcing'],'INITIAL_CAMERA_NOT_ACTIVATED')
            if c.get('transientFirstReselect'):
                result.update(outcome='PASS_TRANSIENT_FIRST_RESELECT_NATIVE_ACTIVATION',nativeCameraActivated=True,immutableGuestFilesChanged=False,
                    permanentIngress='NOT_RUN');raise FirstReselectProofComplete()
            camera=phase('camera-successor-catalog',lambda:component('status'))
            if resume:
                previous_camera=json.loads((resume/'camera-native-upgrade.json').read_bytes())
                require(camera['publication']['stage']=='READY' and initial['cameraStoreUuid']==previous_camera['cameraStoreUuid']
                    and initial['machineId']==item['localVmId'].replace('-','')
                    and any((r.get('installed_component') or {}).get('version')=='0.1.1' and not r.get('pending_component') for r in camera['unit']['components'] or []),'RETAINED_CAMERA_UPGRADE_NOT_CONFIRMED')
                record('retained-camera-update-reconciled.json',dict(noUpload=True,noSend=True,sameStore=True,version='0.1.1'))
            else:
                require(camera['publication']['stage']=='NOT_PUBLISHED','CAMERA_SUCCESSOR_EXISTS_RECONCILE')
                camera_input=c['camera'];payload=records/'camera-access-0.1.1.tar.gz'
                require(hashlib.sha256(payload.read_bytes()).hexdigest()==camera_input['sha256'],'CAMERA_PAYLOAD_CHANGED')
                extra=dict(payload=str(payload),payloadBytes=camera_input['bytes'],payloadSha256=camera_input['sha256'],componentTitle=camera['componentTitle'])
                output=records/'camera-0.1.1.tar.gz';signed=phase('camera-oem-sign',lambda:component('sign',output=str(output),**extra))
                record('camera-upload-intent.json',dict(attemptStarted=True,unitId=item['unitId'],version='0.1.1',bundleSha256=signed['sha256']));camera_attempted=True
                uploaded=phase('camera-upload',lambda:component('upload',bundle=str(output),expectedSha256=signed['sha256'],**extra))
                end=time.monotonic()+150;ready=None;cloud_camera_confirmed=False
                while time.monotonic()<end:
                    ready=component('status',deploymentId=uploaded['deploymentId'])
                    if ready['publication']['stage']=='READY':break
                    require(ready['publication']['stage']=='PROCESSING','CAMERA_PUBLICATION_FAILED');time.sleep(2)
                require(ready and ready['publication']['stage']=='READY','CAMERA_PUBLICATION_TIMEOUT_RECONCILE')
                record('camera-send-intent.json',dict(attemptStarted=True,unitId=item['unitId'],versionId=ready['publication']['versionId']))
                phase('camera-delivery',lambda:component('send',deploymentId=uploaded['deploymentId'],componentTitle=camera['componentTitle']))
                end=time.monotonic()+120;after=None
                while time.monotonic()<end:
                    try:after=guest(native_snapshot,35)
                    except ValueError:time.sleep(1);continue
                    status=component('status',deploymentId=uploaded['deploymentId'])
                    if after['camera']['version']=='0.1.1' and any((r.get('installed_component') or {}).get('version')=='0.1.1' and not r.get('pending_component') for r in status['unit']['components'] or []):
                        cloud_camera_confirmed=True;break
                    time.sleep(2)
                require(cloud_camera_confirmed and after and after['camera']['version']=='0.1.1' and after['cameraStoreUuid']==initial['cameraStoreUuid'] and after['enforcing'],'CAMERA_UPGRADE_NOT_CONFIRMED')
                record('camera-native-upgrade.json',after)
            camera_confirmed=True;result['cameraUpgrade']='PASS_SAME_STORE_NATIVE_OEM'
            phase('native-ingress-start',lambda:app.source_service.camera_ingress('start'))
            first=phase('permanent-ingress-live',lambda:until(lambda x:x.get('health',{}).get('status',{}).get('deliveryState')=='AVAILABLE'))
            ingress=first['ingressProcess'];core=first['cameraProcess']
            require(first['enforcing'] and ingress['uid']==core['uid']==first['producerUid']>0
                and ingress['context'].split(':')[2]=='camera_ingress_t' and ingress['nnp']=='1'
                and all(int(v,16)==0 for v in ingress['capabilities'].values()) and ingress['credentialMountReadonly']
                and core['context'].split(':')[2]=='camera_access_t' and not core['credentialEnvironment'],'PERMANENT_INGRESS_IDENTITY_FAILED')
            phase('native-ingress-idempotent-repeat',lambda:app.source_service.camera_ingress('start'))
            def media_status(role):
                paths=app.source_service.driver.assets();tls_context=ssl.create_default_context(cafile=str(paths['ca']))
                if role:
                    directory=native/authentication.DIRECTORY
                    tls_context.load_cert_chain(str(directory/(role+'.pem')),str(directory/(role+'-key.pem')))
                try:
                    with socket.create_connection(('127.0.0.1',16443),timeout=2) as tcp:
                        with tls_context.wrap_socket(tcp,server_hostname='127.0.0.1') as tls:
                            tls.settimeout(2);tls.sendall(b'GET /vision/v1/camera/front.mjpeg HTTP/1.1\r\nHost: 127.0.0.1\r\nConnection: close\r\n\r\n')
                            raw=tls.recv(8192);require(raw.startswith(b'HTTP/1.1 '),'MEDIA_DENIAL_RESPONSE_INVALID')
                            return int(raw.split(b' ',2)[1])
                except ssl.SSLError as error:
                    require(role is None and 'CERTIFICATE_REQUIRED' in str(error.reason),'MEDIA_TLS_FAILURE_NOT_AUTH_DENIAL')
                    return 'CLIENT_CERTIFICATE_REQUIRED'
            def deny_roles():
                require(all(media_status(role)==403 for role in ('dashboard','runtime')),'WRONG_MEDIA_ROLE_ACCEPTED')
                require(media_status(None)=='CLIENT_CERTIFICATE_REQUIRED','ANONYMOUS_MEDIA_ACCEPTED')
                require(media_status('vdp')==403,'SECOND_MEDIA_SLOT_ACCEPTED')
                return dict(wrongRolesDenied=True,anonymousTlsDenied=True,secondMediaSlotDenied=True)
            phase('live-media-role-and-quota-denial',deny_roles)
            phase('diagnostic-cloud-preflight',lambda:fixture('preflight'))
            catalog=phase('diagnostic-catalog',lambda:fixture('catalog'));service=catalog['serviceId']
            require({v['version'] for v in catalog['versions']}==({'0.1.0','0.1.1','0.1.2','0.1.3','0.1.4'} if resume else {'0.1.0','0.1.1','0.1.2','0.1.3'}),'DIAGNOSTIC_CATALOG_COLLISION')
            subject=json.loads((Path(c['previousNative'])/'probe-subject-create-response.json').read_bytes())['subject']
            bound=phase('diagnostic-subject-before',lambda:fixture('subject-status',serviceId=service,subject=subject))
            if not bound['unitBound']:
                record('subject-bind-intent.json',dict(attemptStarted=True,subjectId=subject['id'],unitId=item['unitId']))
                phase('diagnostic-subject-bind',lambda:fixture('subject-bind',serviceId=service,subject=subject))
            if not bound['serviceBound']:
                record('subject-service-intent.json',dict(attemptStarted=True,subjectId=subject['id'],serviceId=service))
                phase('diagnostic-subject-service',lambda:fixture('subject-assign',serviceId=service,subject=subject))
            if resume:
                old=json.loads((resume/'native-revoked-baseline.json').read_bytes())['facts']
            else:old=phase('native-revoked-baseline',lambda:until(lambda x:len(x['consumers'])==1))
            bounding=old['consumers'][0]['capabilities']['CapBnd']
            def publish(version):
                path=records/('probe-'+version+'.tar.gz');signed=phase('probe-sign-'+version,lambda:fixture('sign',probeVersion=version,output=str(path)))
                record('probe-upload-'+version+'-intent.json',dict(attemptStarted=True,unitId=item['unitId'],subjectId=subject['id'],version=version,binarySha256=c['files']['vision-camera-probe']))
                uploaded=phase('probe-upload-'+version,lambda:fixture('upload',probeVersion=version,bundle=str(path),expectedSha256=signed['sha256']))
                end=time.monotonic()+150
                while time.monotonic()<end:
                    value=fixture('publication',probeVersion=version,deploymentId=uploaded['deploymentId'])
                    if value['stage']=='READY':return value
                    require(value['stage']=='PROCESSING','PROBE_PUBLICATION_FAILED');time.sleep(2)
                raise ValueError('PROBE_PUBLICATION_TIMEOUT_RECONCILE')
            if resume:
                previous_upload=json.loads((resume/'probe-upload-0.1.4.json').read_bytes())['facts']
                reconciled=phase('read-publication-reconciled',lambda:fixture('publication',probeVersion='0.1.4',deploymentId=previous_upload['deploymentId']))
                require(reconciled['stage']=='READY','EXISTING_READER_NOT_READY')
                record('retained-reader-publication.json',dict(noUpload=True,version='0.1.4',versionId=reconciled['versionId']))
            else:publish('0.1.4')
            live=phase('native-aos-real-jpeg-pairs',lambda:until(lambda x:bool(current_pairs(x)),90));consumer=live['consumers'][0]
            require(len(live['consumers'])==1 and consumer['uid']>0 and live['readerGid'] in consumer['groups'] and consumer['readMountReadonly']
                and consumer['context'].split(':')[2]=='container_engine_t' and inactive(consumer,bounding)
                and consumer['binarySha256']==c['files']['vision-camera-probe'] and not consumer['credentialMount'],'NATIVE_READER_PRIVILEGE_FAILED')
            require(any(m.get('probe')=='READER_MUTATION_DENIED' for m in live['messages']),'NATIVE_READER_MUTATION_NOT_DENIED')
            record('native-pair-proof.json',dict(metadata=current_pairs(live)[-4:],bodyHashesVerifiedByNativeAosReader=True,productObserverInstalled=False))
            epoch=current_pairs(live)[-1]['frames'][0]['sourceEpoch'];core_epoch=live['health']['componentEpoch']
            # Negative fixtures run under actual native domains, never load a
            # policy or replace a product binary. Root observes metadata only.
            negative=r'''import base64,json,pathlib,pwd,grp,subprocess,shutil
root=pathlib.Path('/run/vision-permanent-acceptance');assert not root.exists();root.mkdir(mode=0o755)
subprocess.run(['chcon','--reference=/var/aos/workdirs/sm/runtimes/systemd-slot-camera-access',str(root)],check=True,capture_output=True)
for name,data in FILES.items():
 p=root/name;p.write_bytes(base64.b64decode(data));p.chmod(0o555)
 reference='/usr/libexec/aos-camera-ingress-launcher' if name=='boundary' else '/usr/libexec/aos-camera-access-launcher'
 subprocess.run(['chcon','--reference='+reference,str(p)],check=True,capture_output=True)
uid=pwd.getpwnam('aos-camera-access').pw_uid;gid=grp.getgrnam('aos-camera-read').gr_gid
results={}
for name in ('boundary','core-deny'):
 command=['systemd-run','--quiet','--wait','--unit=vision-permanent-'+name,'-p','User=aos-camera-access','-p','Group=aos-camera-read','-p','CapabilityBoundingSet=','-p','AmbientCapabilities=']
 if name=='core-deny':
  pid=subprocess.check_output(['systemctl','show','aos-camera-ingress','--value','-p','MainPID'],text=True).strip();assert pid.isdecimal() and int(pid)>0
  source='/proc/'+pid+'/root/run/credentials/aos-camera-ingress.service';assert pathlib.Path(source,'camera-private-key').is_file()
  command+=['-p','BindReadOnlyPaths='+source+':/run/credentials/aos-camera-ingress.service']
 command += [str(root/name),str(uid),str(gid)]
 done=subprocess.run(command,text=True,capture_output=True,timeout=20)
 raw=subprocess.check_output(['journalctl','-u','vision-permanent-'+name,'-n','40','--no-pager','-o','cat'],text=True)
 messages=[]
 for line in raw.splitlines():
  if line.startswith('{'):
   try:messages.append(json.loads(line))
   except ValueError:pass
 results[name]=dict(exit=done.returncode,messages=messages)
print(json.dumps(results))
'''.replace('FILES',repr({key:base64.b64encode((records/name).read_bytes()).decode() for key,name in (('boundary','vision-ingress-boundary'),('core-deny','vision-camera-credential-deny'))}))
            denied=phase('native-network-and-credential-denials',lambda:guest(negative,55))
            require(all(row['exit']==0 for row in denied.values()),'NATIVE_NEGATIVE_FIXTURE_FAILED')
            require(any(m.get('coreCredentialDenied') and m.get('errno') in (1,13) for m in denied['core-deny']['messages']),'CREDENTIAL_DOMAIN_DENIAL_NOT_OBSERVED')
            require(observe()['egressDropPackets']>live['egressDropPackets'],'NATIVE_NETWORK_DROP_NOT_OBSERVED')
            audit_code="import json,pathlib;p=pathlib.Path('/var/log/audit/audit.log');print(json.dumps(dict(cursor=p.stat().st_size)))"
            cursor=phase('functional-audit-cursor',lambda:guest(audit_code))['cursor']
            def check_audit(cursor):
                audit="import json,pathlib;p=pathlib.Path('/var/log/audit/audit.log');f=p.open('rb');f.seek("+str(cursor)+");raw=f.read(1048577);assert len(raw)<=1048576;print(json.dumps(dict(enforcing=pathlib.Path('/sys/fs/selinux/enforce').read_text().strip()=='1',avcs=[s[:1600] for s in raw.decode(errors='replace').splitlines() if 'avc:' in s and ('camera_ingress' in s or 'camera_access_t' in s)])))"
                value=guest(audit);require(value['enforcing'] and not value['avcs'],'UNEXPECTED_PERMANENT_AVC');return value
            def stale_media():
                # Reversible process scheduling fault only; Source, Camera,
                # network policy and installed files are unchanged.
                try:
                    guest("import json,subprocess;subprocess.run(['systemctl','kill','--kill-whom=main','--signal=STOP','aos-camera-ingress'],check=True,capture_output=True);print(json.dumps(dict(paused=True)))")
                    value=until(lambda x:x['health']['status']['deliveryState']=='STALE',6)
                    count=value['health']['status']['counters']['admitted'];time.sleep(.3);later=observe()
                    require(later['health']['status']['deliveryState']=='STALE' and later['health']['status']['counters']['admitted']==count,'STALLED_MEDIA_NOT_AGED_OUT')
                    return dict(stale=True,noNewAdmission=True,replayedPixelsAvailable=False)
                finally:
                    guest("import json,subprocess;subprocess.run(['systemctl','kill','--kill-whom=main','--signal=CONT','aos-camera-ingress'],check=True,capture_output=True);print(json.dumps(dict(resumed=True)))")
            phase('stalled-media-age-out',stale_media)
            phase('live-after-media-resume',lambda:until(lambda x:x['health']['status']['deliveryState']=='AVAILABLE',15))
            def wrong_generation():
                with env._writer(),app.source_service.driver.operation():
                    state=read_json(native/JOURNAL)
                    try:app.source_service.driver.guest(state,'test','camera-start',sourceId=state['source']['runId'],generation=state['source']['assignmentGeneration']+1)
                    except ValueError as error:require('CAMERA_SELECTION_MISMATCH' in str(error),'WRONG_GENERATION_RESULT');return dict(denied=True)
                    raise ValueError('WRONG_GENERATION_ACCEPTED')
            phase('wrong-source-generation-denied',wrong_generation)
            phase('normal-ingress-stop',lambda:app.source_service.camera_ingress('stop'))
            phase('pixels-cleared',lambda:until(lambda x:x['health']['status']['deliveryState']=='UNAVAILABLE' and x['health']['status']['retainedFrames']==0,8))
            phase('normal-ingress-reconnect',lambda:app.source_service.camera_ingress('start'))
            phase('fresh-stream-epoch',lambda:until(lambda x:any(p['frames'][0]['sourceEpoch']!=epoch for p in current_pairs(x)),30))
            phase('native-camera-restart',lambda:guest("import json,subprocess;subprocess.run(['systemctl','restart','aos-camera-access'],check=True,capture_output=True,timeout=20);print(json.dumps(dict(restarted=True)))",30))
            phase('source-after-camera-restart',lambda:app.source_service.camera_ingress('start'))
            restarted=phase('fresh-core-and-jpeg-pairs',lambda:until(lambda x:x['health']['componentEpoch']!=core_epoch and bool(current_pairs(x)),45))
            require(restarted['camera']['NRestarts']=='0' and restarted['ingress']['NRestarts']=='0','PERMANENT_RESTART_STORM')
            phase('warm-functional-avc-check',lambda:check_audit(cursor))
            def detached_denial():
                with env._writer(),app.source_service.driver.operation():
                    state=read_json(native/JOURNAL);driver=app.source_service.driver;operation=str(uuid.uuid4())
                    driver.rpc(state['source'],'safe_stop',operation);driver.wait(state['source'],operation,'SAFE_STOP')
                    authentication.detach(driver,state)
                    status=authentication.observe(driver)
                    require(status['state']=='DETACHED' and all(status['activeRoleCounts'][k]==0 for k in ('selectedPlatformUnit','platformUpdateRuntime')),'SOURCE_MEDIA_DRAIN_INCOMPLETE')
                    require(media_status('vdp')==403,'DETACHED_IDENTITY_ACCEPTED')
                    return dict(normalOwnerDetached=True,mediaDrained=True,oldSelectedIdentityDenied=True)
            phase('normal-source-detach-media-denial',detached_denial)
            phase('source-stop-before-cold-boot',lambda:app.source_service.simulation('stop',target='test'))
            WorkspaceService(env,app.source_service.driver).execute('close');source_started=False
            phase('native-cold-stop',lambda:vm.execute('stop','test',timeout=150))
            cold=phase('native-cold-start',lambda:vm.execute('start','test',timeout=150));require(cold['vehicles']['test']['state']=='COMPLETED','COLD_START_FAILED')
            phase('cold-unit-online',online)
            restored=phase('retained-camera-after-cold-boot',lambda:guest(native_snapshot,40))
            require(restored['camera']['version']=='0.1.1' and restored['cameraStoreUuid']==initial['cameraStoreUuid'] and restored['enforcing'],'COLD_DATA_NOT_RETAINED')
            cursor=phase('cold-audit-cursor',lambda:guest(audit_code))['cursor']
            source_started=True;phase('cold-normal-source-start',lambda:app.source_service.simulation('start',target='test'))
            phase('cold-normal-source-enrollment',app.source_service.initialize_test)
            phase('cold-physical-safe-stop',physical_safe_stop)
            phase('cold-ingress-start',lambda:app.source_service.camera_ingress('start'))
            cold_live=phase('cold-native-real-jpeg-pairs',lambda:until(lambda x:bool(current_pairs(x)),60));consumer=cold_live['consumers'][0]
            publish('0.1.5')
            revoked=phase('native-read-resource-revoked',lambda:until(lambda x:len(x['consumers'])==1 and x['consumers'][0]['pid']!=consumer['pid']
                and not x['consumers'][0]['readMount'] and x['readerGid'] not in x['consumers'][0]['groups'],90))
            require(revoked['camera']['NRestarts']=='0' and revoked['ingress']['NRestarts']=='0','REVOCATION_RESTART_STORM')
            phase('cold-functional-avc-check',lambda:check_audit(cursor))
            result.update(outcome='PASS_FRESH_PERMANENT_INGRESS_NATIVE_READ_REVOKE',sameFreshUnit=True,cameraVersion='0.1.1',rootfsVersion='6.1.1-vision-camera.5',
                actualJpegPairs=True,disconnectClearing=True,stalledMediaAgeOut=True,mediaRoleQuotaDenial=True,sourceDetachDenial=True,cameraRestart=True,nativeColdBoot=True,resourceRevocation=True)
    except FirstReselectProofComplete:pass
    except Exception as error:
        import traceback
        frame=traceback.extract_tb(error.__traceback__)[-1];value=str(error).split(':',1)[0]
        result.update(code=value if re.fullmatch('[A-Z][A-Z0-9_:,.-]{1,160}',value) else type(error).__name__,failureFile=Path(frame.filename).name,failureLine=frame.lineno)
        if vm is not None:
            try:record('failure-observation.json',evidence(observe()))
            except Exception:pass
    finally:
        if vm is not None:
            with runtime_paths.installed_session(native):
                if camera_attempted and not camera_confirmed:
                    result['cleanup']['activeCameraUpdatePreservedForReconciliation']=True;result['cleanup']['ownedRuntimesStopped']=False
                else:
                    try:
                        if source_started:app.source_service.simulation('stop',target='test');WorkspaceService(env,app.source_service.driver).execute('close')
                        try:
                            removed=guest("import json,pathlib,shutil,subprocess;p=pathlib.Path('/run/vision-permanent-acceptance');\nfor u in ('vision-permanent-boundary','vision-permanent-core-deny'):\n subprocess.run(['systemctl','stop',u],capture_output=True);subprocess.run(['systemctl','reset-failed',u],capture_output=True)\nif p.exists():shutil.rmtree(p)\nprint(json.dumps(dict(temporaryFixturesRemoved=not p.exists())))")
                            result['cleanup'].update(removed)
                        except Exception:result['cleanup']['temporaryFixturesRemoved']=False
                        stopped=vm.execute('stop','test',timeout=150);result['cleanup']['ownedRuntimesStopped']=stopped['vehicles']['test']['state']=='COMPLETED'
                    except Exception:result['cleanup']['ownedRuntimesStopped']=False
                state=read_json(native/JOURNAL);result['cleanup']['sameFreshIdentity']=all(state['vehicles']['test'][k]==value for k,value in identity.items())
                result['cleanup']['retainedJournalsUnchanged']=all((p/JOURNAL).read_bytes()==raw for p,raw in retained.items())
        if caffeinate is not None:caffeinate.terminate();caffeinate.wait(timeout=5)
        if not result['cleanup'] or not all(result['cleanup'].values()):result['outcome']='NOT_COMPLETE'
        result['seconds']=round(time.monotonic()-began,2);record('result.json',result);print(json.dumps(result),flush=True)
    return 0 if result['outcome'].startswith('PASS_') else 1


if __name__=='__main__':raise SystemExit(main())
