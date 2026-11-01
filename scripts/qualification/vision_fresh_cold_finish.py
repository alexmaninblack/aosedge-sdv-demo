#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Exact continuation of accept-11: reconcile Stop, cold read, revoke, cleanup."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import re
import runpy
import shlex
import subprocess
import sys
import time
import uuid


def require(ok,code):
    if not ok:raise ValueError(code)


WARM_STAGES=('native-aos-real-jpeg-pairs','native-network-and-credential-denials',
    'stalled-media-age-out','wrong-source-generation-denied','pixels-cleared',
    'fresh-stream-epoch','fresh-core-and-jpeg-pairs','warm-functional-avc-check',
    'normal-source-detach-media-denial')


def prior_gate(prior):
    require(prior['outcome']=='NOT_COMPLETE' and prior['code']=='SOURCE_CONTROL_REJECTED'
        and prior['cleanup']==dict(ownedRuntimesStopped=False,sameFreshIdentity=True,retainedJournalsUnchanged=True)
        and not prior['cloudMutation'] and set(WARM_STAGES)<={r['stage'] for r in prior['phases']},'EXACT_WARM_PROOF_REQUIRED')


def worker(context):
    c=json.loads(context.read_bytes());records=context.parent;prior=Path(c['prior'])
    require(not (records/'result.json').exists(),'CONTINUATION_EXISTS_RECONCILE')
    result=dict(scenario='VISION_FRESH_COLD_READ_REVOKE_CONTINUATION',outcome='NOT_COMPLETE',
        warmProof=prior.name,phases=[],cleanup={},cloudMutation=False,fullVisionE2E='NOT_RUN',perception='NOT_RUN',assessment='NOT_RUN')
    began=time.monotonic();vm=app=None;source_started=True;retained={};native=None;caffeinate=None
    def record(name,value):
        p=records/name;p.write_text(json.dumps(value,indent=2)+'\n');p.chmod(0o600)
    def phase(name,action):
        print(json.dumps(dict(stage=name,state='STARTED')),flush=True);start=time.monotonic();value=action()
        record(name+'.json',dict(seconds=round(time.monotonic()-start,2),facts=evidence(value)))
        result['phases'].append(dict(stage=name,seconds=round(time.monotonic()-start,2)))
        record('progress.json',result);print(json.dumps(dict(stage=name,state='COMPLETE')),flush=True);return value
    try:
        require(hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==c['workerSha256'],'CONTINUATION_WORKER_CHANGED')
        pc=json.loads((prior/'context.json').read_bytes());prior_gate(json.loads((prior/'result.json').read_bytes()))
        for name,digest in pc['files'].items():require(hashlib.sha256((prior/name).read_bytes()).hexdigest()==digest,'WARM_INPUT_CHANGED')
        helper=runpy.run_path(str(prior/'vision_ingress_live_worker.py'));evidence=helper['evidence']
        pair_reader=runpy.run_path(str(prior/'vision_fresh_accept_worker.py'))['pairs']
        fixture_helper=runpy.run_path(str(prior/'vision_camera_fixture_cloud.py'))
        require(pc['diagnosticSuccessors']==fixture_helper['SUCCESSOR_PACKET'],'SUCCESSOR_AUTHORITY_CHANGED')
        package=Path(pc['main']['packageRoot']);bundle=Path(pc['bundle'])
        require(subprocess.check_output(['/usr/sbin/sysctl','-n','hw.model'],text=True).strip()=='Mac16,8','M4_REQUIRED')
        require(hashlib.sha256((package/'application-manifest.json').read_bytes()).hexdigest()==pc['main']['manifestSha256'],'BASE_CHANGED')
        subprocess.run(['codesign','--verify','--deep','--strict','-R','=identifier "org.aosedge.sdvlab.vision.bootstrap" and anchor apple generic and certificate leaf[subject.OU] = "3NF57VKB3V"',str(bundle)],check=True,capture_output=True,timeout=120)
        sys.path.insert(0,str(package/'aosedge-sdv-demo/apps/demo-orchestrator/src'))
        import aosedge_demo_orchestrator
        from aosedge_demo_orchestrator import runtime_paths
        tooling=bundle/'Contents/Resources/tooling/aosedge-sdv-demo/apps/demo-orchestrator/src'
        aosedge_demo_orchestrator.__path__.insert(0,str(tooling/'aosedge_demo_orchestrator'))
        from aosedge_demo_orchestrator import vision_bootstrap as v,source_authentication as auth
        from aosedge_demo_orchestrator.environment import EnvironmentService,JOURNAL
        from aosedge_demo_orchestrator.vm import VMService,access_path
        from aosedge_demo_orchestrator.guest_access import ssh_command
        from aosedge_demo_orchestrator.status import read_json,load_configuration
        from aosedge_demo_orchestrator.application import DemoOrchestrator
        from aosedge_demo_orchestrator.workspace import WorkspaceService
        from aosedge_demo_orchestrator.units import UnitService
        from aosedge_demo_orchestrator.cloud_connection import selected_domain,cloud_binding
        from aosedge_demo_orchestrator.cloud_runtime import launch
        verified=v.verify(bundle,pc['main']['manifestSha256']);require(verified.manifest_sha256==pc['bootstrapManifestSha256'],'BOOTSTRAP_CHANGED')
        native=Path.home()/v.INSTANCE_NAME;state=read_json(native/JOURNAL);item=state['vehicles']['test']
        require(item['unitId']=='af6d074a-6ce1-49ba-b613-0476e7b6d1b5' and item['localVmId']=='89273f16-4be0-4b22-b4cb-58d08533c8bc','FRESH_IDENTITY_CHANGED')
        identity={k:item[k] for k in ('unitId','nodeId','localVmId','overlay')}
        retained={Path.home()/n:(Path.home()/n/JOURNAL).read_bytes() for n in v.RETAINED_INSTANCE_NAMES}
        caffeinate=subprocess.Popen(['/usr/bin/caffeinate','-d','-i','-w',str(__import__('os').getpid())],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        with runtime_paths.installed_session(native):
            env=EnvironmentService(catalog=v.SignedVisionCatalog(verified),vm_profile=v.VM_PROFILE);vm=VMService(env)
            app=DemoOrchestrator(environment_service=env,vm_service=vm);units=UnitService(vm);driver=app.source_service.driver
            def guest(code,timeout=35):
                current=read_json(native/JOURNAL)['vehicles']['test']
                done=subprocess.run(ssh_command(access_path(native,'test'),current['sshPort'],5),input="python3 - <<'COLD_FINISH'\n"+code+"\nCOLD_FINISH\n",capture_output=True,text=True,timeout=timeout)
                require(done.returncode==0 and len(done.stdout)<2**21,'CONTINUATION_GUEST_FAILED');return json.loads(done.stdout)
            observation=(prior/'vision_ingress_observation.py').read_text().replace("'2200'","'500'").replace("if __name__=='__main__':print(json.dumps(observe()))",'print(json.dumps(observe()))')
            def observe():return guest(observation)
            def pairs(value):
                sid=read_json(native/JOURNAL)['source']['runId']
                return [r for r in pair_reader(value) if r['frames'][0]['sourceId']==sid]
            def until(check,seconds=60):
                end=time.monotonic()+seconds
                while time.monotonic()<end:
                    value=observe()
                    if check(value):return value
                    time.sleep(1)
                record('last-observation.json',evidence(value));raise ValueError('COLD_OBSERVATION_TIMEOUT')
            def negative_cleanup():
                files={key:base64.b64encode((prior/name).read_bytes()).decode() for key,name in (('boundary','vision-ingress-boundary'),('core-deny','vision-camera-credential-deny'))}
                return guest('FILES='+repr(files)+'\nIDENTITY_ONLY=False\nCLEANUP=True\n'+(prior/'vision_negative_probe.py').read_text(),55)
            def restore_selected_session():
                with env._writer(),driver.operation():
                    s=read_json(native/JOURNAL);source=s['source'];assignment=auth.observe(driver)
                    require(source['state']=='RUNNING' and not source.get('operation') and source['stopOperation']['phase']=='SAFE_STOP_REQUESTED'
                        and assignment['state']=='SELECTED' and assignment['selectedSource']==auth.selection(s) and assignment['assignmentGeneration']==source['assignmentGeneration']
                        and not source['trust'].get('pending'),'DETACHED_STOP_STATE_CHANGED')
                    status=driver.rpc(source,'status',source['stopOperation']['id']);frame=status.get('frame') or{}
                    require(status.get('fresh') and status.get('held') and status.get('phase')=='SAFE_STOP'
                        and frame.get('activeMode')=='SAFE_STOP' and frame.get('speedKmh',999)<=.5 and frame.get('brake',0)>=.99,'DETACHED_PHYSICAL_STOP_NOT_CONFIRMED')
                    pair=json.loads((prior/'native-pair-proof.json').read_bytes())['metadata'][-1]
                    require(source['runId']==pair['frames'][0]['sourceId'] and status['operationId']!=source['stopOperation']['id'],'WARM_SCENARIO_HOLD_NOT_IDENTIFIED')
                    record('release-warm-safe-stop-intent.json',dict(action='NORMAL_OWNER_RELEASE',operationId=status['operationId'],sameUnit=True,attemptStarted=True))
                    released=driver.rpc(source,'release',status['operationId'])
                    require(not released['held'],'WARM_HOLD_NOT_RELEASED')
                    return dict(normalOwnerReleased=True,sameUnit=True,journalNotPatched=True)
            phase('reconcile-detached-stop',restore_selected_session)
            phase('normal-source-stop',lambda:app.source_service.simulation('stop',target='test'))
            source_started=False;WorkspaceService(env,driver).execute('close')
            phase('remove-warm-negative-fixtures',negative_cleanup)
            snapshot=(prior/'vision_delivery_guest.py').read_text()+"\nprint(json.dumps(run('snapshot')))\n"
            initial=phase('retained-camera-before-cold',lambda:guest(snapshot,45))
            phase('native-cold-stop',lambda:vm.execute('stop','test',timeout=150))
            started=phase('native-cold-start',lambda:vm.execute('start','test',timeout=150))
            require(started['vehicles']['test']['state']=='COMPLETED','COLD_START_FAILED')
            def online():
                with env._writer():return units._wait(read_json(native/JOURNAL),'test',lambda u:u and u['online_status']=='Online','CLOUD_ONLINE',timeout=60)
            phase('cold-unit-online',online)
            restored=phase('retained-camera-after-cold',lambda:guest(snapshot,45))
            require(initial['cameraStoreUuid']==restored['cameraStoreUuid'] and restored['camera']['version']=='0.1.1'
                and restored['rootfsVersion']=='VERSION="6.1.1-vision-camera.5"' and restored['enforcing'],'COLD_DATA_NOT_RETAINED')
            cursor=phase('cold-audit-cursor',lambda:guest("import json,pathlib;print(json.dumps(dict(cursor=pathlib.Path('/var/log/audit/audit.log').stat().st_size)))"))['cursor']
            source_started=True;phase('cold-normal-source-start',lambda:app.source_service.simulation('start',target='test'))
            phase('cold-normal-source-enrollment',app.source_service.initialize_test)
            def safe_stop():
                with env._writer(),driver.operation():
                    s=read_json(native/JOURNAL);op=str(uuid.uuid4());driver.rpc(s['source'],'safe_stop',op);value=driver.wait(s['source'],op,'SAFE_STOP')
                    if value.get('held'):driver.rpc(s['source'],'release',op)
                    value=driver.ready(s);f=value.get('frame')or{}
                    require(value.get('fresh') and not value.get('held') and f.get('activeMode')=='SAFE_STOP' and f.get('speedKmh',999)<=.5 and f.get('brake',0)>=.99,'COLD_PHYSICAL_STOP_FAILED')
                    return dict(physicalSafeStop=True)
            phase('cold-physical-safe-stop',safe_stop)
            phase('cold-ingress-start',lambda:app.source_service.camera_ingress('start'))
            cold=phase('cold-native-real-jpeg-pairs',lambda:until(lambda x:bool(pairs(x)),60));consumer=cold['consumers'][0]
            require(len(cold['consumers'])==1 and consumer['readMountReadonly'] and not consumer['credentialMount']
                and consumer['binarySha256']==fixture_helper['FIXED_BINARY_SHA'],'COLD_READER_IDENTITY_FAILED')
            record('cold-native-pair-proof.json',dict(metadata=pairs(cold)[-4:],bodyHashesVerifiedByNativeAosReader=True))
            config=load_configuration(native);sdk,sdk_env=launch(native,config['cloudPython'],'unit_cloud.py')
            before=read_json(native/JOURNAL);binding=cloud_binding(before)
            scope=dict(setupProfile=v.PROFILE,version='0.1.0',cloudDomain=selected_domain(before),ownerId=binding['ownerId'],oemOwner=binding['ownerId'],
                spOwner=config['cloudProfiles']['service-provider']['expectedOwnerId'],oemCredential=str(config['cloudProfiles']['oem-delivery']['credential']),
                spCredential=str(config['cloudProfiles']['service-provider']['credential']),vehicles=dict(test={k:item[k] for k in ('unitId','systemUid','unitSetId','nodeId')}),
                binary=str(prior/'vision-camera-probe'),binarySha256=pc['files']['vision-camera-probe'],diagnosticSuccessors=pc['diagnosticSuccessors'])
            scope['vehicles']['test']['nodeHardwareId']=item['cloud']['identity']['nodeHardwareId']
            def fixture(action,**extra):
                done=subprocess.run([sdk[0],'-I','-B',str(prior/'vision_camera_fixture_cloud.py'),str(tooling)],input=json.dumps(dict(scope,action=action,**extra)),capture_output=True,text=True,env=sdk_env,timeout=180)
                require(done.returncode==0 and len(done.stdout)<262144,'COLD_SDK_FAILED');value=json.loads(done.stdout)
                if not value.get('ok'):record('sdk-error.json',value);raise ValueError(value.get('reason','COLD_SDK_FAILED'))
                return value['data']
            phase('revocation-cloud-preflight',lambda:fixture('preflight'))
            catalog=phase('revocation-catalog',lambda:fixture('catalog'))
            require({v['version'] for v in catalog['versions']}=={'0.1.0','0.1.1','0.1.2','0.1.3','0.1.4','0.1.6'},'REVOKE_CATALOG_COLLISION')
            subject=json.loads((Path(pc['previousNative'])/'probe-subject-create-response.json').read_bytes())['subject']
            bound=phase('revocation-subject',lambda:fixture('subject-status',serviceId=catalog['serviceId'],subject=subject))
            require(bound['unitBound'] and bound['serviceBound'],'REVOKE_SUBJECT_CHANGED')
            version='0.1.7';bundle_path=records/'probe-0.1.7.tar.gz'
            signed=phase('probe-sign-0.1.7',lambda:fixture('sign',probeVersion=version,output=str(bundle_path)))
            record('probe-upload-0.1.7-intent.json',dict(attemptStarted=True,unitId=item['unitId'],subjectId=subject['id'],version=version,binarySha256=scope['binarySha256']))
            result['cloudMutation']=True
            uploaded=phase('probe-upload-0.1.7',lambda:fixture('upload',probeVersion=version,bundle=str(bundle_path),expectedSha256=signed['sha256']))
            def ready():
                end=time.monotonic()+150
                while time.monotonic()<end:
                    value=fixture('publication',probeVersion=version,deploymentId=uploaded['deploymentId'])
                    if value['stage']=='READY':return value
                    require(value['stage']=='PROCESSING','REVOCATION_PUBLICATION_FAILED');time.sleep(2)
                raise ValueError('REVOCATION_PUBLICATION_UNCERTAIN_RECONCILE')
            phase('revocation-publication-ready',ready)
            revoked=phase('native-read-resource-revoked',lambda:until(lambda x:len(x['consumers'])==1 and x['consumers'][0]['pid']!=consumer['pid']
                and not x['consumers'][0]['readMount'] and x['readerGid'] not in x['consumers'][0]['groups'],90))
            require(revoked['camera']['NRestarts']==revoked['ingress']['NRestarts']=='0','REVOCATION_RESTART_STORM')
            audit="import json,pathlib;p=pathlib.Path('/var/log/audit/audit.log');f=p.open('rb');f.seek("+str(cursor)+");raw=f.read(1048577);assert len(raw)<=1048576;print(json.dumps(dict(enforcing=pathlib.Path('/sys/fs/selinux/enforce').read_text().strip()=='1',avcs=[s[:1600] for s in raw.decode(errors='replace').splitlines() if 'avc:' in s and ('camera_ingress' in s or 'camera_access_t' in s)])))"
            avcs=phase('cold-functional-avc-check',lambda:guest(audit))
            require(avcs['enforcing'] and not avcs['avcs'],'UNEXPECTED_COLD_AVC')
            result.update(outcome='PASS_FRESH_PERMANENT_INGRESS_NATIVE_READ_REVOKE',sameFreshUnit=True,cameraVersion='0.1.1',rootfsVersion='6.1.1-vision-camera.5',
                readVersion='0.1.6',revokeVersion='0.1.7',actualJpegPairs=True,nativeColdBoot=True,resourceRevocation=True,warmGatesRetained=True)
    except Exception as error:
        import traceback
        frame=traceback.extract_tb(error.__traceback__)[-1];value=str(error).split(':',1)[0]
        result.update(code=value if re.fullmatch('[A-Z][A-Z0-9_:,.-]{1,160}',value) else type(error).__name__,failureFile=Path(frame.filename).name,failureLine=frame.lineno)
    finally:
        if vm is not None:
            with runtime_paths.installed_session(native):
                source_stopped=False
                try:
                    if source_started:app.source_service.simulation('stop',target='test')
                    WorkspaceService(env,app.source_service.driver).execute('close');source_stopped=True
                    result['cleanup']['sourceStopped']=True
                except Exception:result['cleanup']['sourceStopped']=False
                if source_stopped:
                    try:result['cleanup'].update(negative_cleanup())
                    except Exception:result['cleanup']['temporaryFixturesRemoved']=False
                    try:
                        stopped=vm.execute('stop','test',timeout=150);result['cleanup']['ownedVmStopped']=stopped['vehicles']['test']['state']=='COMPLETED'
                    except Exception:result['cleanup']['ownedVmStopped']=False
                else:result['cleanup']['ownedVmStopped']=False
                state=read_json(native/JOURNAL)
                result['cleanup']['sameFreshIdentity']=all(state['vehicles']['test'][k]==v for k,v in identity.items())
                result['cleanup']['retainedJournalsUnchanged']=all((p/JOURNAL).read_bytes()==raw for p,raw in retained.items())
        if caffeinate is not None:caffeinate.terminate();caffeinate.wait(timeout=5)
        if not result['cleanup'] or not all(result['cleanup'].values()):result['outcome']='NOT_COMPLETE'
        result['seconds']=round(time.monotonic()-began,2);record('result.json',result);print(json.dumps(result),flush=True)
    return 0 if result['outcome'].startswith('PASS_') else 1


def main():
    p=argparse.ArgumentParser();p.add_argument('--config',type=Path);p.add_argument('--worker',type=Path);args=p.parse_args()
    if args.worker:return worker(args.worker)
    import remote_harness as h
    from vision_vm_campaign import configuration
    c=configuration(args.config);t=c['transport'];name='vision-fresh-cold-finish-02';records=Path(c['records'])/name;remote=Path(c['remoteRoot'])/name
    require(not records.exists(),'CONTINUATION_EXISTS_RECONCILE');prior=Path(c['records'])/'vision-fresh-accept-11'
    prior_gate(json.loads((prior/'result.json').read_bytes()));diagnosis=json.loads((prior/'detached-stop-diagnosis.json').read_bytes())
    require(diagnosis['trustState']=='DETACHED' and diagnosis['generationMatches'] and diagnosis['control']==dict(phase='SAFE_STOP',fresh=True,mode='SAFE_STOP',speedKmh=0.,brake=1.),'DETACHED_STOP_DIAGNOSIS_REQUIRED')
    previous=json.loads((Path(c['records'])/'vision-fresh-cold-finish-01/result.json').read_bytes())
    require(previous['code']=='SOURCE_CONTROL_REJECTED' and not previous['cloudMutation']
        and [r['stage'] for r in previous['phases']]==['reconcile-detached-stop'] and previous['cleanup']['sameFreshIdentity']
        and previous['cleanup']['retainedJournalsUnchanged'],'EXACT_RESELECT_ATTEMPT_REQUIRED')
    records.mkdir(mode=0o700);source=Path(__file__).resolve();context=dict(prior=str(Path(c['remoteRoot'])/'vision-fresh-accept-11'),workerSha256=h.digest(source))
    h.atomic(records/'context.json',context);h.remote(t,'umask 077\nmkdir '+shlex.quote(str(remote)),timeout=15)
    options=h.ssh_args(t)[1:-1];options.remove('-T');i=options.index('-b');options[i:i+2]=['-o','BindAddress='+options[i+1]]
    h.run(['/usr/bin/scp',*options,str(source),str(records/'context.json'),t['user']+'@'+t['host']+':'+str(remote)+'/'],timeout=30)
    python=c['main']['packageRoot']+'/demo-artifacts/aosedge-sdv-demo/host-runtime/python/bin/python3.12'
    command=' '.join(map(shlex.quote,[python,'-I','-B',str(remote/source.name),'--worker',str(remote/'context.json')]))
    process=subprocess.Popen(h.ssh_args(t)+[command],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    with (records/'progress.jsonl').open('x') as log:
        for line in process.stdout:require(log.tell()<2**20,'PROGRESS_LIMIT');log.write(line);log.flush();print(line.strip(),flush=True)
    error=process.stderr.read(8192);code=process.wait(timeout=20);h.atomic(records/'transport.json',dict(exit=code,stderrPresent=bool(error)))
    collect='import pathlib,json;p=pathlib.Path('+repr(str(remote))+');print(json.dumps({f.name:json.loads(f.read_bytes()) for f in p.glob("*.json") if f.name!="context.json" and f.stat().st_size<2097152}))'
    values=json.loads(h.remote(t,shlex.quote(python)+' -I -B -c '+shlex.quote(collect),timeout=20))
    for name,value in values.items():h.atomic(records/name,value)
    print(json.dumps(values.get('result.json',dict(outcome='UNCERTAIN'))),flush=True);return code


if __name__=='__main__':raise SystemExit(main())
