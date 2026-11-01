#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""One retained M4 live ingress/read/revoke scenario, with owned rollback."""
import argparse
import base64
import hashlib
import io
import json
import os
from pathlib import Path
import re
import socket
import ssl
import subprocess
import sys
import tarfile
import time
import traceback


def require(ok,code):
    if not ok:raise ValueError(code)


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic(path,value):
    temporary=path.with_suffix('.pending')
    fd=os.open(temporary,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    with os.fdopen(fd,'w') as stream:json.dump(value,stream,indent=2);stream.flush();os.fsync(stream.fileno())
    os.replace(temporary,path)


def evidence(value):
    """Owner results may contain enrolled fingerprints; never retain those."""
    if isinstance(value,dict):
        return {k:evidence(v) for k,v in value.items() if not any(word in k.lower() for word in
            ('fingerprint','certificate','privatekey','secret','token','material','runnercommand','simulatorcommand','signerid'))}
    if isinstance(value,(tuple,list)):return [evidence(v) for v in value]
    return value


def correlated(observation):
    frames={(v['ingressFrame'],v['sha256']) for v in observation.get('ingressFrames',[])}
    pairs=[v for v in observation.get('messages',[]) if v.get('probe')=='LIVE_PAIR' and v.get('bytesVerified') is True]
    return [v for v in pairs if len(v['frames'])==len(v['sha256'])==2
        and all((frame,digest) in frames for frame,digest in zip(v['frames'],v['sha256']))]


def expected_bind_denial(line):
    """Only the deliberate no-listener probe, never arbitrary AVC noise."""
    return ('avc:  denied  { bind } ' in line and 'comm="python3" ' in line
        and 'scontext=system_u:system_r:camera_ingress_t:s0 ' in line
        and 'tcontext=system_u:system_r:camera_ingress_t:s0 ' in line
        and 'tclass=tcp_socket permissive=0' in line)


def inactive_native_capabilities(process,bounding):
    """Native Aos retains its pre-existing bounding set, not active grants.

    The ingress daemon's stricter all-zero requirement is separate. Never
    change native OCI capabilities to satisfy a diagnostic harness assumption.
    """
    caps=process['capabilities']
    return (process['nnp']=='1' and int(caps['CapBnd'],16)==int(bounding,16)
        and all(int(caps[k],16)==0 for k in ('CapEff','CapPrm','CapInh','CapAmb')))


class NativeSourceProofComplete(Exception):pass


def main():
    p=argparse.ArgumentParser();p.add_argument('--context',type=Path,required=True);a=p.parse_args()
    c=json.loads(a.context.read_bytes());records=a.context.parent;candidate=records/'candidate'
    require(not (records/'result.json').exists(),'ATTEMPT_EXISTS_RECONCILE')
    result=dict(scenario='VISION_GATEWAY_NATIVE_INGRESS_READ_REVOKE',outcome='NOT_COMPLETE',phases=[],cleanup={},
        permanentImage='NOT_RUN',perception='NOT_RUN',assessment='NOT_RUN',fullVisionE2E='NOT_RUN',cloudMutation=False)
    start=time.monotonic();app=None;vm=None;env=None;source_started=False;policy_attempted=False;caffeinate=None
    retained={};native=None;proof_deadline=None
    def phase(name,action):
        print(json.dumps(dict(stage=name,state='STARTED')),flush=True);began=time.monotonic()
        value=action();atomic(records/(name+'.json'),dict(seconds=round(time.monotonic()-began,2),facts=evidence(value)))
        result['phases'].append(dict(stage=name,seconds=round(time.monotonic()-began,2),state='COMPLETE'))
        atomic(records/'progress.json',result);print(json.dumps(dict(stage=name,state='COMPLETE')),flush=True)
        return value
    try:
        native_source=c.get('nativeSourceProof') is True
        if native_source:
            require(c.get('permanentDelivery')==dict(authorized=True,recoveryFirst=True,rootfsVersion='6.1.1-vision-camera.4',cameraVersion='0.1.1',readVersion='0.1.4',revokeVersion='0.1.5'),'PERMANENT_PACKET_AUTHORITY_REQUIRED')
        else:
            require(c.get('diagnosticCycle')==dict(codename='vision-camera-image-probe',readVersion='0.1.2',revokeVersion='0.1.3',authorized=True),
                'EXACT_DIAGNOSTIC_CYCLE_AUTHORITY_REQUIRED')
        require(subprocess.check_output(['/usr/sbin/sysctl','-n','hw.model'],text=True).strip()=='Mac16,8','M4_REQUIRED')
        require('"CGSSessionScreenIsLocked"=Yes' not in subprocess.check_output(['/usr/sbin/ioreg','-n','Root','-d1'],text=True),'M4_DESKTOP_LOCKED')
        package=Path(c['main']['packageRoot']);bundle=Path(c['bundle'])
        require(sha(package/'application-manifest.json')==c['main']['manifestSha256'],'BASE_CHANGED')
        requirement='=identifier "org.aosedge.sdvlab.vision.bootstrap" and anchor apple generic and certificate leaf[subject.OU] = "3NF57VKB3V"'
        subprocess.run(['codesign','--verify','--deep','--strict','-R',requirement,str(bundle)],check=True,capture_output=True,timeout=120)
        require(sha(candidate/'manifest.json')==c['candidateManifestSha256'],'CANDIDATE_MANIFEST_CHANGED')
        manifest=json.loads((candidate/'manifest.json').read_bytes())
        require(manifest['kind']=='REVERSIBLE_VISION_INGRESS_PROOF' and manifest['releaseImage'] is False,'PROOF_CANDIDATE_REQUIRED')
        if native_source:require(manifest.get('nativePolicy') is True,'NATIVE_POLICY_CANDIDATE_REQUIRED')
        for name,row in manifest['files'].items():
            path=candidate/name;require(path.is_relative_to(candidate) and '..' not in Path(name).parts
                and not path.is_symlink() and path.stat().st_size==row['bytes'] and sha(path)==row['sha256'],'CANDIDATE_FILE_CHANGED')
        for name,digest in c['files'].items():require(sha(records/name)==digest,'WORKER_INPUT_CHANGED')
        subprocess.run(['codesign','--verify','--strict',str(candidate/'native/carla-ego-runtime')],check=True,capture_output=True,timeout=10)
        subprocess.run([str(candidate/'native/carla-ego-runtime'),'--version'],check=True,capture_output=True,timeout=10)
        sys.path.insert(0,str(package/'aosedge-sdv-demo/apps/demo-orchestrator/src'))
        import aosedge_demo_orchestrator
        from aosedge_demo_orchestrator import runtime_paths
        tooling=bundle/'Contents/Resources/tooling/aosedge-sdv-demo/apps/demo-orchestrator/src'
        aosedge_demo_orchestrator.__path__.insert(0,str(tooling/'aosedge_demo_orchestrator'))
        aosedge_demo_orchestrator.__path__.insert(0,str(candidate/'source-proof'))
        from aosedge_demo_orchestrator import vision_bootstrap as v
        from aosedge_demo_orchestrator.environment import EnvironmentService,JOURNAL
        from aosedge_demo_orchestrator.vm import VMService,access_path
        from aosedge_demo_orchestrator.units import UnitService
        from aosedge_demo_orchestrator.guest_access import ssh_command
        from aosedge_demo_orchestrator.status import read_json,load_configuration
        from aosedge_demo_orchestrator.cloud_runtime import launch
        from aosedge_demo_orchestrator.cloud_connection import selected_domain,cloud_binding
        from aosedge_demo_orchestrator.application import DemoOrchestrator
        from aosedge_demo_orchestrator.workspace import WorkspaceService
        from aosedge_demo_orchestrator import source_authentication as authentication
        bootstrap=v.verify(bundle,c['main']['manifestSha256'])
        require(bootstrap.manifest_sha256==c['bootstrapManifestSha256'],'BOOTSTRAP_CHANGED')
        native=Path.home()/v.INSTANCE_NAME
        retained={Path.home()/n:(Path.home()/n/JOURNAL).read_bytes() for n in v.RETAINED_INSTANCE_NAMES}
        before=read_json(native/JOURNAL);item=before['vehicles']['test']
        require(item['runtime']['state']=='STOPPED' and before['source']['state']=='STOPPED'
            and not before['source'].get('operation'),'RETAINED_IDLE_VISION_REQUIRED')
        identity={k:item[k] for k in ('localVmId','unitId','nodeId','overlay')}
        previous=Path(c['previousNative'])
        subject=json.loads((previous/'probe-subject-create-response.json').read_bytes())['subject']
        caffeinate=subprocess.Popen(['/usr/bin/caffeinate','-d','-i','-w',str(os.getpid())],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        with runtime_paths.installed_session(native):
            env=EnvironmentService(catalog=v.SignedVisionCatalog(bootstrap),vm_profile=v.VM_PROFILE)
            vm=VMService(env,progress=lambda value:print(json.dumps(dict(stage='native-owner',message=str(value)[:110])),flush=True))
            units=UnitService(vm);config=load_configuration(native)
            sdk,sdk_environment=launch(native,config['cloudPython'],'unit_cloud.py')
            request=dict(setupProfile=v.PROFILE,version='0.1.0',cloudDomain=selected_domain(before),
                oemOwner=cloud_binding(before)['ownerId'],ownerId=cloud_binding(before)['ownerId'],
                spOwner=config['cloudProfiles']['service-provider']['expectedOwnerId'],
                oemCredential=str(config['cloudProfiles']['oem-delivery']['credential']),
                spCredential=str(config['cloudProfiles']['service-provider']['credential']),
                vehicles={'test':{k:item[k] for k in ('unitId','systemUid','unitSetId','nodeId')}},
                binary=str(records/'vision-camera-probe'),binarySha256=c['files']['vision-camera-probe'])
            request['vehicles']['test']['nodeHardwareId']=item['cloud']['identity']['nodeHardwareId']
            def fixture(action,**extra):
                done=subprocess.run([sdk[0],'-I','-B',str(records/'vision_camera_fixture_cloud.py'),str(tooling)],
                    input=json.dumps(dict(request,action=action,**extra)),text=True,capture_output=True,env=sdk_environment,timeout=100)
                require(done.returncode==0 and len(done.stdout)<131072,'DIAGNOSTIC_SDK_UNAVAILABLE')
                value=json.loads(done.stdout);require(value.get('ok'),value.get('reason','DIAGNOSTIC_SDK_FAILED'));return value['data']
            boot=phase('retained-native-start',lambda:vm.execute('start','test',timeout=150))
            require(boot['vehicles']['test']['state']=='COMPLETED','NATIVE_START_INCOMPLETE')
            def online():
                with env._writer():
                    state=read_json(native/JOURNAL)
                    return units._wait(state,'test',lambda v:v and v['online_status']=='Online','CLOUD_ONLINE',timeout=60)
            phase('existing-unit-online',online)
            phase('cloud-read-preflight',lambda:fixture('preflight'))
            catalog=phase('diagnostic-catalog-before',lambda:fixture('catalog'))
            resume=c.get('readCycleResume')
            expected_versions={'0.1.0','0.1.1','0.1.2','0.1.3'} if native_source else {'0.1.0','0.1.1','0.1.2'} if resume else {'0.1.0','0.1.1'}
            require(catalog['serviceId'] and {v['version'] for v in catalog['versions']}==expected_versions,'DIAGNOSTIC_VERSIONS_EXIST_RECONCILE')
            service=catalog['serviceId']
            if resume:
                require(resume['unitId']==item['unitId'] and resume['subjectId']==subject['id']
                    and resume['serviceId']==service and resume['binarySha256']==c['files']['vision-camera-probe'],'RESUME_SCOPE_CHANGED')
                reconciled=phase('existing-read-publication-reconciled',lambda:fixture('publication',probeVersion='0.1.2',deploymentId=resume['deploymentId']))
                require(reconciled['stage']=='READY' and reconciled['serviceId']==service,'RESUME_PUBLICATION_UNCONFIRMED')
                result['readCycleResumed']=resume['attempt']
            bound=phase('existing-subject-before',lambda:fixture('subject-status',serviceId=service,subject=subject))
            require(bound['unitBound'] and bound['serviceBound'],'RETAINED_SUBJECT_BINDING_CHANGED')
            def guest(code,timeout=30):
                state=read_json(native/JOURNAL);current=state['vehicles']['test']
                command=ssh_command(access_path(native,'test'),current['sshPort'],5)
                wrapper="import json,traceback\ntry:\n"+'\n'.join(' '+v for v in code.splitlines())+"\nexcept Exception as error:\n print(json.dumps(dict(guestError=type(error).__name__,line=traceback.extract_tb(error.__traceback__)[-1].lineno)))\n"
                done=subprocess.run(command,input="python3 - <<'INGRESS_PROOF'\n"+wrapper+"\nINGRESS_PROOF\n",text=True,capture_output=True,timeout=timeout)
                require(done.returncode==0 and len(done.stdout)<2*1024**2,'GUEST_OBSERVATION_FAILED')
                value=json.loads(done.stdout)
                if 'guestError' in value:
                    atomic(records/'guest-error.json',value);raise ValueError('GUEST_'+value['guestError'].upper()+'_LINE_'+str(value['line']))
                return value
            observe_code=(records/'vision_ingress_observation.py').read_text().replace("if __name__=='__main__':print(json.dumps(observe()))",'print(json.dumps(observe()))')
            def observe():return guest(observe_code)
            def until(predicate,timeout=30):
                end=min(time.monotonic()+timeout,proof_deadline or float('inf'));last=None
                while time.monotonic()<end:
                    last=observe()
                    if predicate(last):return last
                    require(last['ingress']['ActiveState'] not in ('failed',),'INGRESS_PROCESS_FAILED')
                    time.sleep(.5)
                atomic(records/'last-observation.json',last);raise ValueError('INGRESS_OBSERVATION_TIMEOUT')
            # Only reversible guest files/policy. Native slot/rootfs stay intact.
            files=[p for p in (candidate/'guest').iterdir() if p.is_file()]+[records/'vision-camera-credential-deny']
            buffer=io.BytesIO()
            with tarfile.open(fileobj=buffer,mode='w:gz') as archive:
                for path in files:archive.add(path,arcname=path.name)
            raw=buffer.getvalue();require(len(raw)<1024**2,'GUEST_PROOF_PAYLOAD_LIMIT')
            prepare=r'''import base64,hashlib,io,json,pathlib,subprocess,tarfile
p=pathlib.Path('/run/vision-camera-store-proof');assert not p.exists();p.mkdir(mode=0o700)
raw=base64.b64decode(DATA);assert hashlib.sha256(raw).hexdigest()==DIGEST
with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as archive:archive.extractall(p,filter='data')
done=subprocess.run(['python3',str(p/'vision_camera_ingress_guest.py'),'start'],capture_output=True,text=True,timeout=150)
if done.returncode:print(json.dumps(dict(policyStart=False,errorClass=done.stderr.splitlines()[-1].split(':')[0] if done.stderr else 'NO_DIAGNOSTIC')))
else:print(done.stdout)
'''.replace('DATA',repr(base64.b64encode(raw).decode())).replace('DIGEST',repr(hashlib.sha256(raw).hexdigest()))
            policy_attempted=True
            prepared=phase('transient-ingress-prepare',lambda:guest(prepare,timeout=160));require(prepared.get('prepared'),'TRANSIENT_INGRESS_PREPARE_FAILED')
            proof_deadline=time.monotonic()+510
            app=DemoOrchestrator(environment_service=env,vm_service=vm)
            original_assets=app.source_service.driver.assets
            def proof_assets():
                paths=original_assets()
                for relative in ('native/carla-ego-runtime','tools/run_m6_interactive.py','tools/run_m5.py'):
                    require(sha(candidate/relative)==manifest['files'][relative]['sha256'],'PROOF_SOURCE_CHANGED')
                paths.update(runtime=candidate/'native/carla-ego-runtime',runner=candidate/'tools/run_m6_interactive.py')
                return paths
            app.source_service.driver.assets=proof_assets
            source_started=True
            phase('normal-source-start',lambda:app.source_service.simulation('start',target='test'))
            phase('normal-source-enrollment',app.source_service.initialize_test)
            phase('source-ingress-start',lambda:app.source_service.camera_ingress('start'))
            first=phase('nonroot-live-ingress',lambda:until(lambda v:len(v['ingressFrames'])>=3 and v.get('health',{}).get('status',{}).get('deliveryState')=='AVAILABLE',timeout=35))
            require(len(first['consumers'])==1,'EXISTING_NATIVE_READER_REQUIRED')
            native_bounding=resume['nativeReaderBoundingSet'] if resume else first['consumers'][0]['capabilities']['CapBnd']
            require(inactive_native_capabilities(first['consumers'][0],native_bounding),'EXISTING_NATIVE_PRIVILEGES_CHANGED')
            process=first.get('ingressProcess',{})
            require(process.get('uid')==first['producerUid']>0 and process.get('context','').split(':')[2]=='camera_ingress_t'
                and process.get('nnp')=='1' and all(int(v,16)==0 for v in process['capabilities'].values())
                and process['credentialMountReadonly'],'INGRESS_NATIVE_IDENTITY_FAILED')
            core=first['cameraProcess']
            require(core['uid']==first['producerUid'] and core['context'].split(':')[2]=='camera_access_t'
                and not core['credentialEnvironment'],'CAMERA_CORE_CREDENTIAL_ASSIGNMENT_INVALID')
            # systemd's read-only credential mount can propagate into the old
            # core namespace. Mount visibility is not a read grant: require the
            # same-UID/core-domain actual open-denial below, under Enforcing.
            require({v['networkProof'] for v in first['networkProofs'] if v.get('denied')}=={'outside-peer','bind'},'INGRESS_NETWORK_BOUNDARY_FAILED')
            require(first['egressDropPackets']>0,'INGRESS_NATIVE_EGRESS_DROP_NOT_OBSERVED')
            phase('source-ingress-idempotent-repeat',lambda:app.source_service.camera_ingress('start'))
            result['nonrootLiveIngress']='PASS'
            # Reject a foreign generation before any projection/credential write.
            def wrong_generation():
                with env._writer(),app.source_service.driver.operation():
                    state=read_json(native/JOURNAL)
                    try:app.source_service.driver.guest(state,'test','camera-start',sourceId=state['source']['runId'],generation=state['source']['assignmentGeneration']+1)
                    except ValueError as error:
                        require('CAMERA_SELECTION_MISMATCH' in str(error),'WRONG_GENERATION_UNEXPECTED_RESULT');return dict(denied=True)
                    raise ValueError('WRONG_GENERATION_ACCEPTED')
            phase('wrong-source-generation-denied',wrong_generation)
            def media_status(role):
                state=read_json(native/JOURNAL);driver=app.source_service.driver
                paths=driver.assets();context=ssl.create_default_context(cafile=str(paths['ca']))
                if role:
                    directory=native/authentication.DIRECTORY
                    context.load_cert_chain(str(directory/(role+'.pem')),str(directory/(role+'-key.pem')))
                try:
                    with socket.create_connection(('127.0.0.1',16443),timeout=2) as tcp:
                        with context.wrap_socket(tcp,server_hostname='127.0.0.1') as tls:
                            tls.settimeout(2);tls.sendall(b'GET /vision/v1/camera/front.mjpeg HTTP/1.1\r\nHost: 127.0.0.1\r\nConnection: close\r\n\r\n')
                            raw=tls.recv(8192);require(raw.startswith(b'HTTP/1.1 '),'MEDIA_DENIAL_RESPONSE_INVALID')
                            return int(raw.split(b' ',2)[1])
                except ssl.SSLError as error:
                    require(role is None and 'CERTIFICATE_REQUIRED' in str(error.reason),'MEDIA_TLS_FAILURE_NOT_AUTH_DENIAL')
                    return 'CLIENT_CERTIFICATE_REQUIRED'
            def deny_roles():
                values={role:media_status(role) for role in ('dashboard','runtime')}
                require(all(v==403 for v in values.values()),'WRONG_MEDIA_ROLE_ACCEPTED')
                require(media_status(None)=='CLIENT_CERTIFICATE_REQUIRED','ANONYMOUS_MEDIA_ACCEPTED')
                require(media_status('vdp')==403,'SECOND_MEDIA_SLOT_ACCEPTED')
                return dict(wrongRolesDenied=True,anonymousTlsDenied=True,secondMediaSlotDenied=True)
            phase('live-media-role-and-quota-denial',deny_roles)
            # Same nonroot UID as Camera core, but the core SELinux domain may
            # not open ingress credentials. The probe never reads their bytes.
            deny=r'''import grp,json,pathlib,pwd,subprocess
p=pathlib.Path('/run/vision-camera-store-proof/exec/core-credential-deny')
import shutil
shutil.copyfile('/run/vision-camera-store-proof/vision-camera-credential-deny',p);p.chmod(0o555)
subprocess.run(['chcon','--reference=/usr/libexec/aos-camera-access-launcher',str(p)],check=True,capture_output=True)
done=subprocess.run(['systemd-run','--quiet','--wait','--unit=vision-core-credential-deny','-p','User=aos-camera-access','-p','Group=aos-camera-read','-p','CapabilityBoundingSet=','-p','AmbientCapabilities=',str(p),str(pwd.getpwnam('aos-camera-access').pw_uid),str(grp.getgrnam('aos-camera-read').gr_gid)],text=True,capture_output=True,timeout=15)
unit=dict(v.split('=',1) for v in subprocess.check_output(['systemctl','show','vision-core-credential-deny','-p','ExecMainStatus','-p','Result'],text=True).splitlines() if '=' in v)
raw=subprocess.check_output(['journalctl','-u','vision-core-credential-deny','-n','30','-o','cat','--no-pager'],text=True)
probes=[json.loads(v) for v in raw.splitlines() if v.startswith('{"coreCredentialDenied":')]
print(json.dumps(dict(exit=done.returncode,unit=unit,probes=probes)))
'''
            isolation=phase('core-credential-isolation',lambda:guest(deny,timeout=20))
            require(isolation['exit']==0 and isolation['probes'] and all(v.get('coreCredentialDenied') is True
                and v.get('nonroot') is True and v.get('coreDomainVerified') is True for v in isolation['probes']),'CORE_CREDENTIAL_ISOLATION_NOT_PROVED')
            # Negative probes precede the functional audit cursor; preserve
            # their explicit denials separately rather than erasing evidence.
            phase('negative-proof-audit',lambda:guest("import json,pathlib\np=pathlib.Path('/var/log/audit/audit.log')\nraw=p.read_bytes()[-262144:].decode(errors='replace')\nprint(json.dumps(dict(scopedAvcs=[v[:1600] for v in raw.splitlines() if 'avc:' in v and ('camera_ingress' in v or 'camera_access_t' in v)],cursor=p.stat().st_size)))"))
            if native_source:
                epoch=first['health']['componentEpoch'];old_source=first['ingressFrames'][-1]['sourceEpoch']
                phase('native-policy-ingress-stop',lambda:app.source_service.camera_ingress('stop'))
                phase('native-policy-pixels-cleared',lambda:until(lambda v:v['health']['status']['deliveryState']=='UNAVAILABLE' and v['health']['status']['retainedFrames']==0,timeout=5))
                phase('native-policy-ingress-repeat',lambda:app.source_service.camera_ingress('start'))
                repeated=phase('native-policy-fresh-stream',lambda:until(lambda v:v['ingressFrames'] and v['ingressFrames'][-1]['sourceEpoch']!=old_source and v['health']['status']['deliveryState']=='AVAILABLE',timeout=20))
                source_epoch=repeated['ingressFrames'][-1]['sourceEpoch']
                phase('native-policy-core-restart',lambda:guest("import json,subprocess\nsubprocess.run(['systemctl','restart','aos-camera-access.service'],check=True,capture_output=True,timeout=20)\nprint(json.dumps(dict(restarted=True)))",timeout=25))
                phase('native-policy-source-after-restart',lambda:app.source_service.camera_ingress('start'))
                phase('native-policy-fresh-core-and-stream',lambda:until(lambda v:v['health']['componentEpoch']!=epoch and v['health']['status']['deliveryState']=='AVAILABLE'
                    and v['ingressFrames'][-1]['sourceEpoch']!=source_epoch,timeout=25))
                audit=guest("import json,pathlib\np=pathlib.Path('/var/log/audit/audit.log');cursor=CURSOR\nwith p.open('rb') as f:f.seek(cursor);raw=f.read(1048577)\nassert len(raw)<=1048576\nprint(json.dumps(dict(enforcing=pathlib.Path('/sys/fs/selinux/enforce').read_text().strip()=='1',scopedAvcs=[v[:1600] for v in raw.decode(errors='replace').splitlines() if 'avc:' in v and ('camera_ingress' in v or 'camera_access_t' in v)])))".replace('CURSOR',str(json.loads((records/'negative-proof-audit.json').read_bytes())['facts']['cursor'])))
                atomic(records/'functional-audit.json',audit)
                require(audit['enforcing'] and all(expected_bind_denial(v) for v in audit['scopedAvcs']),'NATIVE_POLICY_UNEXPECTED_FUNCTIONAL_AVC')
                phase('native-policy-normal-source-stop',lambda:app.source_service.simulation('stop',target='test'))
                WorkspaceService(env,app.source_service.driver).execute('close');source_started=False
                result.update(outcome='PASS_TRANSIENT_NATIVE_STORE_INGRESS_POLICY',nativeAosLiveFrames='NOT_RUN_RESOURCE_REMAINS_REVOKED',nativePolicy=True)
                raise NativeSourceProofComplete()
            require(proof_deadline-time.monotonic()>300,'INSUFFICIENT_PUBLICATION_AND_REVOKE_BUDGET')
            def publish(version):
                if version=='0.1.2' and resume:return reconciled
                output=records/('probe-'+version+'.tar.gz')
                signed=phase('diagnostic-sign-'+version,lambda:fixture('sign',probeVersion=version,output=str(output)))
                intent=records/('diagnostic-upload-'+version+'-intent.json')
                require(not intent.exists(),'DIAGNOSTIC_MUTATION_EXISTS_RECONCILE')
                atomic(intent,dict(attemptStarted=True,version=version,unitId=item['unitId'],subjectId=subject['id'],binarySha256=c['files']['vision-camera-probe']))
                result['cloudMutation']=True
                response=phase('diagnostic-upload-'+version,lambda:fixture('upload',probeVersion=version,bundle=str(output),expectedSha256=signed['sha256']))
                atomic(records/('diagnostic-upload-'+version+'-response.json'),response)
                end=min(time.monotonic()+150,proof_deadline)
                while time.monotonic()<end:
                    value=fixture('publication',probeVersion=version,deploymentId=response['deploymentId'])
                    if value['stage']=='READY':return value
                    require(value['stage']=='PROCESSING','DIAGNOSTIC_PUBLICATION_FAILED');time.sleep(2)
                raise ValueError('DIAGNOSTIC_PUBLICATION_TIMEOUT')
            read=publish('0.1.2');require(read['serviceId']==service,'DIAGNOSTIC_SERVICE_CHANGED')
            reader=phase('native-aos-live-pair',lambda:until(lambda v:bool(correlated(v)),timeout=60))
            require(len(reader['consumers'])==1,'NATIVE_READER_COUNT_INVALID');consumer=reader['consumers'][0]
            require(consumer['uid']>0 and reader['readerGid'] in consumer['groups'] and consumer['readMountReadonly']
                and consumer['context'].split(':')[2]=='container_engine_t'
                and inactive_native_capabilities(consumer,native_bounding)
                and consumer['binarySha256']==c['files']['vision-camera-probe'] and not consumer['credentialMount'],'NATIVE_READER_IDENTITY_FAILED')
            require(any(v.get('probe')=='READER_MUTATION_DENIED' for v in reader['messages']),'NATIVE_READER_MUTATION_NOT_DENIED')
            atomic(records/'correlated-live-pairs.json',dict(pairs=correlated(reader)[-8:],sameGatewayMetadataAndReaderBytes=True))
            result['nativeAosLiveFrames']='PASS_MATCHING_FRAME_IDS_AND_SHA256'
            old_epoch=reader['health']['componentEpoch'];old_source=reader['ingressFrames'][-1]['sourceEpoch'];old_frame=reader['ingressFrames'][-1]['ingressFrame']
            phase('source-media-disconnect',lambda:app.source_service.camera_ingress('stop'))
            phase('pixels-cleared-on-disconnect',lambda:until(lambda v:v['health']['status']['deliveryState']=='UNAVAILABLE' and v['health']['status']['retainedFrames']==0,timeout=5))
            phase('source-media-reconnect',lambda:app.source_service.camera_ingress('start'))
            reconnection=phase('fresh-source-epoch',lambda:until(lambda v:bool(v['ingressFrames']) and v['ingressFrames'][-1]['sourceEpoch']!=old_source
                and any(row['frames'][-1]>old_frame for row in correlated(v)),timeout=20))
            restart_frame=reconnection['ingressFrames'][-1]['ingressFrame']
            restart="import json,subprocess\nsubprocess.run(['systemctl','restart','aos-camera-access.service'],check=True,capture_output=True,timeout=20)\nprint(json.dumps(dict(restarted=True)))"
            phase('native-camera-restart',lambda:guest(restart,timeout=25))
            phase('source-after-camera-restart',lambda:app.source_service.camera_ingress('start'))
            after=phase('fresh-camera-and-source-epochs',lambda:until(lambda v:v.get('health',{}).get('componentEpoch')!=old_epoch
                and v.get('health',{}).get('status',{}).get('deliveryState')=='AVAILABLE'
                and any(row['frames'][-1]>restart_frame for row in correlated(v)),timeout=25))
            require(after['camera']['NRestarts']=='0','CAMERA_RESTART_STORM')
            result['disconnectReconnectAndCameraRestart']='PASS'
            # Revoke last, after every functional check; never downgrade/replay.
            revoked=publish('0.1.3');require(revoked['serviceId']==service,'DIAGNOSTIC_SERVICE_CHANGED')
            revoke=phase('native-aos-resource-revoked',lambda:until(lambda v:len(v['consumers'])==1 and v['consumers'][0]['pid']!=consumer['pid']
                and not v['consumers'][0]['readMount'] and v['readerGid'] not in v['consumers'][0]['groups'],timeout=60))
            result['resourceRevocation']='PASS'
            bound=phase('existing-subject-after',lambda:fixture('subject-status',serviceId=service,subject=subject))
            require(bound['unitBound'] and bound['serviceBound'],'SUBJECT_MEMBERSHIP_CHANGED')
            audit=guest("import json,pathlib\np=pathlib.Path('/var/log/audit/audit.log');cursor=CURSOR\nwith p.open('rb') as f:f.seek(cursor);raw=f.read(1048577)\nassert len(raw)<=1048576\nprint(json.dumps(dict(enforcing=pathlib.Path('/sys/fs/selinux/enforce').read_text().strip()=='1',scopedAvcs=[v[:1600] for v in raw.decode(errors='replace').splitlines() if 'avc:' in v and ('camera_ingress' in v or 'camera_access_t' in v)])))".replace('CURSOR',str(json.loads((records/'negative-proof-audit.json').read_bytes())['facts']['cursor'])))
            atomic(records/'functional-audit.json',audit)
            require(audit['enforcing'] and all(expected_bind_denial(v) for v in audit['scopedAvcs']),'UNEXPECTED_FUNCTIONAL_AVC')
            original_detach=authentication.detach
            def observed_detach(driver,state):
                value=original_detach(driver,state)
                observed=authentication.observe(driver)
                require(observed['state']=='DETACHED' and all(observed['activeRoleCounts'][k]==0 for k in ('selectedPlatformUnit','platformUpdateRuntime')),
                    'SOURCE_MEDIA_DRAIN_INCOMPLETE')
                require(media_status('vdp')==403,'DETACHED_SOURCE_IDENTITY_RECONNECTED')
                atomic(records/'source-detach-media-denial.json',dict(mediaDrained=True,oldSelectedIdentityDenied=True))
                return value
            authentication.detach=observed_detach
            phase('normal-source-stop-with-media-drain',lambda:app.source_service.simulation('stop',target='test'))
            WorkspaceService(env,app.source_service.driver).execute('close');source_started=False
            result['outcome']='PASS_REVERSIBLE_NATIVE_LIVE_INGRESS_READ_REVOKE'
    except NativeSourceProofComplete:pass
    except Exception as error:
        message=str(error)
        fixed=message.removesuffix(':test')
        result['code']=fixed if isinstance(error,ValueError) and re.fullmatch('[A-Z0-9_:,.-]{1,180}',fixed) else type(error).__name__
        result['errorFrames']=[dict(file=Path(v.filename).name,line=v.lineno) for v in traceback.extract_tb(error.__traceback__)[-4:]]
        if vm is not None:
            try:atomic(records/'failure-observation.json',observe())
            except Exception:pass
    finally:
        if vm is not None:
            # Re-enter the trusted installed scope for cleanup after any error.
            with runtime_paths.installed_session(native):
                try:
                    if source_started and app is not None:
                        app.source_service.simulation('stop',target='test')
                        WorkspaceService(env,app.source_service.driver).execute('close')
                    result['cleanup']['sourceStopped']=not source_started or read_json(native/JOURNAL)['source']['state']=='STOPPED'
                except Exception:result['cleanup']['sourceStopped']=False
                try:
                    if policy_attempted:
                        code="import json,pathlib,subprocess\np=pathlib.Path('/run/vision-camera-store-proof')\nif (p/'policy-state.json').exists():\n done=subprocess.run(['python3',str(p/'vision_camera_ingress_guest.py'),'stop'],text=True,capture_output=True,timeout=90)\n assert done.returncode==0\n print(done.stdout)\nelse:print(json.dumps(dict(noPolicyState=True)))"
                        restored=guest(code,timeout=100);atomic(records/'policy-restoration.json',restored)
                        require(restored.get('stockPolicyRestored') or restored.get('noPolicyState'),'POLICY_RESTORE_NOT_CONFIRMED')
                    result['cleanup']['stockPolicyRestored']=True
                except Exception:result['cleanup']['stockPolicyRestored']=False
                try:
                    stopped=vm.execute('stop','test',timeout=150);result['cleanup']['visionStopped']=stopped['vehicles']['test']['state']=='COMPLETED'
                except Exception:result['cleanup']['visionStopped']=False
                result['cleanup']['retainedJournalsUnchanged']=all((path/JOURNAL).read_bytes()==raw for path,raw in retained.items())
                state=read_json(native/JOURNAL)
                result['cleanup']['sameVisionIdentity']=all(state['vehicles']['test'][k]==value for k,value in identity.items())
        if caffeinate is not None:
            caffeinate.terminate();caffeinate.wait(timeout=5)
        result['seconds']=round(time.monotonic()-start,2)
        if result['outcome'].startswith('PASS_') and not all(result['cleanup'].values()):result['outcome']='NOT_COMPLETE';result['code']='CLEANUP_NOT_CONFIRMED'
        atomic(records/'result.json',result);print(json.dumps(result),flush=True)
    return 0 if result['outcome'].startswith('PASS_') else 1


if __name__=='__main__':raise SystemExit(main())
