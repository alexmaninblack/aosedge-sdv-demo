# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""One engineering replay/compute proof on the retained isolated Vision VM."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import tarfile
import threading
import time
from uuid import uuid4
import zipfile


def require(ok, code):
    if not ok:raise ValueError(code)


def atomic(path,value):
    temporary=path.with_suffix('.pending')
    fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'w') as stream:json.dump(value,stream);stream.flush();os.fsync(stream.fileno())
    os.replace(temporary,path)


class LoadObserver:
    """The complete observer protocol includes final close, even without a helper."""
    def __init__(self):self.samples=[]
    def phase_start(self,*args):pass
    def sample(self,value):self.samples.append(dict(at=time.monotonic(),**value))
    def phase_end(self):pass
    def close(self):pass


def main():
    p=argparse.ArgumentParser();p.add_argument('--context',type=Path,required=True)
    p.add_argument('--resume-from',type=Path)
    p.add_argument('--reuse-sequence',action='store_true')
    a=p.parse_args();c=json.loads(a.context.read_bytes());root=a.context.parent
    require(subprocess.check_output(['/usr/sbin/sysctl','-n','hw.model'],text=True).strip()=='Mac16,8','M4_REQUIRED')
    require('"CGSSessionScreenIsLocked"=Yes' not in subprocess.check_output(['/usr/sbin/ioreg','-n','Root','-d1'],text=True),'M4_DESKTOP_LOCKED')
    package=Path(c['packageRoot']);vision=Path(c['visionRoot']);retained=Path(c['retainedRoot'])
    require(vision==Path.home()/'SDV-Vision-Lab-Data' and vision!=retained,'STATE_SCOPE_INVALID')
    require(hashlib.sha256((package/'application-manifest.json').read_bytes()).hexdigest()==c['manifestSha256'],'PACKAGE_CHANGED')
    for name,pin in c['proofFiles'].items():require(hashlib.sha256((root/name).read_bytes()).hexdigest()==pin,'PROOF_TRANSFER_CHANGED')
    previous=None
    if a.resume_from:
        shape_resume=root.name=='compute-model-shape';steady_resume=root.name=='compute-steady'
        expected=root.parent/('compute-model-shape/result.json' if steady_resume else 'compute-replay/result.json' if shape_resume else 'compute-continuation/result.json' if a.reuse_sequence else 'result.json')
        require(root.name in ('compute-steady','compute-model-shape','compute-replay','compute-continuation') and
                a.reuse_sequence==(root.name!='compute-continuation') and a.resume_from==expected,'RESUME_SCOPE_INVALID')
        previous=json.loads(a.resume_from.read_bytes())
        require(all(previous['cleanup'].values()) and
                (previous['outcome']=='PASS_ENGINEERING_TENSOR_TIMING_ONLY' if steady_resume else
                 previous['outcome']=='NOT_COMPLETE' and previous.get('modelResult',{}).get('code')==('MODEL_EXECUTION_NOT_COMPLETE' if shape_resume else 'FRAME_PAIR_INTERVAL_INVALID')),'PREVIOUS_COMPUTE_NOT_RECONCILED')
        if shape_resume:
            history=[json.loads(v) for v in (a.resume_from.parent/'model-progress.jsonl').read_text().splitlines()]
            require(any(v.get('code')=='MODEL_INPUT_SHAPE_CHANGED' for v in history),'PREVIOUS_MODEL_SHAPE_NOT_OBSERVED')
    payload=(root.parent if previous else root)/'vision-pilot-cpu-fp32.tar.gz'
    require(payload.stat().st_size==c['inputs']['bytes'] and hashlib.sha256(payload.read_bytes()).hexdigest()==c['inputs']['sha256'],'MODEL_INPUT_CHANGED')
    app_root=package/'aosedge-sdv-demo/apps/demo-orchestrator/src'
    sys.path.insert(0,str(app_root))
    import aosedge_demo_orchestrator
    aosedge_demo_orchestrator.__path__.insert(0,str(root/'delta'))
    from aosedge_demo_orchestrator import runtime_paths
    from aosedge_demo_orchestrator.environment import EnvironmentService,JOURNAL
    from aosedge_demo_orchestrator.vm import VMService,access_path
    from aosedge_demo_orchestrator.vm_profiles import VISION
    from aosedge_demo_orchestrator.guest_access import ssh_command
    from aosedge_demo_orchestrator.application import DemoOrchestrator
    from aosedge_demo_orchestrator.workspace import WorkspaceService
    main_before=json.loads((retained/JOURNAL).read_bytes())['vehicles']['test']
    preserved={k:main_before.get(k) for k in ('localVmId','overlay','unitId','nodeId','mac','sshPort')}
    require(preserved['localVmId']==c['retainedTest'],'RETAINED_MAIN_CHANGED')
    for port in (10022,2000,16443,18053):
        with socket.socket() as probe:
            probe.settimeout(.2);require(probe.connect_ex(('127.0.0.1',port))!=0,'CONFLICTING_MAIN_OWNER')
    result=dict(scenario='VISION_VM_MODEL_COMPUTE',outcome='NOT_COMPLETE',phases=[],nativeAosDeployment='NOT_RUN',
                assessment='NOT_RUN',accuracy='NOT_QUALIFIED',liveServiceIngress='NOT_RUN',fullE2E='NOT_RUN',
                cloudMutation=False,carlaOrFactoryRebuilt=False,mode='EXPLICIT_UNCALIBRATED_TENSOR_TIMING')
    started=time.monotonic();model=None;model_thread=None;model_result={};model_window={};runtime=None;source_started=False;probe=None
    def step(name,action):
        print(json.dumps(dict(stage=name,state='STARTED')),flush=True);begin=time.monotonic()
        value=action();row=dict(stage=name,seconds=round(time.monotonic()-begin,2),facts=value)
        result['phases'].append(row);atomic(root/(name+'.json'),row)
        print(json.dumps(dict(stage=name,state='COMPLETE',seconds=row['seconds'])),flush=True)
        return value
    with runtime_paths.installed_session(vision):
        env=EnvironmentService(vm_profile=VISION.name);runtime=VMService(env,
            progress=lambda value:print(json.dumps(dict(stage='vm-owner',state=str(value)[:100])),flush=True))
        app=DemoOrchestrator(environment_service=env,vm_service=runtime)
        state=json.loads((vision/JOURNAL).read_bytes())
        require(state['vehicles']['test']['localVmId']==c['visionTest'] and state['vmProfile']==VISION.name,'VISION_BINDING_CHANGED')
        require(runtime.observe_readiness('test')['reason']=='VM_NOT_RUNNING','VISION_VM_ALREADY_RUNNING')
        def guest(script,timeout=30):
            value=subprocess.run(ssh_command(access_path(vision,'test'),12022,10),input=script,capture_output=True,text=True,timeout=timeout)
            require(value.returncode==0,'GUEST_COMMAND_FAILED')
            return value.stdout
        try:
            def boot():
                v=runtime.execute('start','test',timeout=100)
                require(v['vehicles']['test']['state']=='COMPLETED','VISION_START_UNCONFIRMED')
                t=runtime.sync_time();require(t['state']=='READY','VISION_TIME_UNCONFIRMED')
                return dict(state='READY',skewBoundSeconds=t['skewBoundSeconds'])
            step('vm-start',boot)
            guest_root='/home/sdv-vision-model-probe'
            if previous is None:
                guest('set -eu\ntest ! -e '+guest_root+'\ntest "$(df -Pk /home | awk \'NR==2 {print $4}\')" -gt 340000\nmkdir -m 700 '+guest_root+'\n')
            else:guest('test -f '+guest_root+'/payload/input-lock.json\n')
            with tarfile.open(payload) as archive:
                require(all(not Path(r.name).is_absolute() and '..' not in Path(r.name).parts and not r.issym() and not r.islnk() for r in archive),'ARCHIVE_PATH_INVALID')
            def transfer_payload():
                with payload.open('rb') as stream:
                    sent=subprocess.run(ssh_command(access_path(vision,'test'),12022,10)[:-2]+['tar','-C',guest_root,'-xzf','-'],stdin=stream,capture_output=True,timeout=60)
                require(sent.returncode==0,'GUEST_PAYLOAD_TRANSFER_FAILED')
                return dict(bytes=c['inputs']['bytes'],sourceSha256=c['inputs']['sha256'],nativeAosPackage=False)
            if previous is None:step('guest-inputs',transfer_payload)
            def check_imports():
                script='''import sys,json,re
sys.path.insert(0,''' + repr(guest_root+'/payload/libraries') + ''')
try:
 import numpy,cv2,onnxruntime
 print(json.dumps(dict(ok=True,numpy=numpy.__version__,opencv=cv2.__version__,onnxruntime=onnxruntime.__version__)))
except Exception as error:
 print(json.dumps(dict(ok=False,code='GUEST_MODEL_ABI_UNAVAILABLE',type=type(error).__name__,libraries=re.findall(r'lib[A-Za-z0-9_.+-]+\\.so(?:\\.[0-9]+)*',str(error))[:4])))
'''
                data=json.loads(guest('OPENBLAS_NUM_THREADS=1 python3 -I -B - <<\'CHECK_IMPORTS\'\n'+script+'\nCHECK_IMPORTS\n'))
                atomic(root/'library-imports.json',data)
                print(json.dumps(dict(stage='library-imports',facts=data)),flush=True)
                require(data['ok'],'GUEST_MODEL_ABI_UNAVAILABLE')
                return data
            step('library-imports',check_imports)
            # A reviewed driver can evolve independently of immutable model/library
            # inputs. Preserve both identities and never overwrite the old proof.
            active_probe=(root/'vision_model_probe.py').read_bytes()
            probe_name=guest_root+'/'+root.name+'-probe.py'
            sent=subprocess.run(ssh_command(access_path(vision,'test'),12022,10)[:-2]+['tee',probe_name],
                input=active_probe,capture_output=True,timeout=10)
            require(sent.returncode==0 and sent.stdout==active_probe,'ACTIVE_PROBE_TRANSFER_FAILED')
            def model_metadata():
                script='''import sys,json,importlib.util
sys.path.insert(0,''' + repr(guest_root+'/payload/libraries') + ''')
import onnxruntime as ort
spec=importlib.util.spec_from_file_location('probe', ''' + repr(probe_name) + ''');probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)
models={}
for name in ('autodrive','autosteer','autospeed'):
 options=ort.SessionOptions();options.intra_op_num_threads=1;options.inter_op_num_threads=1;options.graph_optimization_level=ort.GraphOptimizationLevel.ORT_DISABLE_ALL
 session=ort.InferenceSession(''' + repr(guest_root+'/payload/models/') + '''+name+'_fp32.onnx',options,providers=['CPUExecutionProvider'])
 rows=session.get_inputs()
 assert len(rows)==(2 if name=='autodrive' else 1) and probe.valid_input_shapes(rows),'MODEL_INPUT_SHAPE_CHANGED'
 models[name]=[dict(name=r.name,shape=r.shape,type=r.type) for r in rows]
print(json.dumps(dict(ok=True,models=models)))
'''
                return json.loads(guest('OPENBLAS_NUM_THREADS=1 python3 -I -B - <<\'MODEL_METADATA\'\n'+script+'\nMODEL_METADATA\n',timeout=30))
            step('model-metadata',model_metadata)
            # Reuse verified probe wheels, not a system/global pip installation.
            wheels=Path(c['cameraWheels']);tools=root/'tools';tools.mkdir(mode=0o700)
            sys.path.insert(0,str(root));from vision_camera import Probe,Latest,REFERENCE,WHEELS,DEPENDENCIES
            for name,url,pin,size in WHEELS:
                path=wheels/name
                require(path.stat().st_size==size and hashlib.sha256(path.read_bytes()).hexdigest()==pin,'CAMERA_WHEEL_CHANGED')
                with zipfile.ZipFile(path) as archive:
                    require(all(not Path(r.filename).is_absolute() and '..' not in Path(r.filename).parts for r in archive.infolist()),'CAMERA_WHEEL_PATH_INVALID')
                    archive.extractall(tools)
            sys.path.insert(0,str(tools))
            import importlib,importlib.metadata
            importlib.invalidate_caches()
            require({n:importlib.metadata.version(n) for n in DEPENDENCIES}==DEPENDENCIES,'CAMERA_TOOL_VERSION_CHANGED')
            step('simulator-start',lambda:app.source_service.simulation('start',target='test'))
            source_started=True
            state=json.loads((vision/JOURNAL).read_bytes());source=state['source'];driver=app.source_service.driver
            assets=driver.assets();sys.path.append(str(assets['python-api-root']))
            import carla
            def control():
                require(model_result.get('outcome')!='NOT_COMPLETE',model_result.get('code','MODEL_PROBE_FAILED'))
                v=driver.rpc(source,'status',str(uuid4()));frame=v.get('frame') or {}
                require(frame.get('runId')==source['runId'] and frame.get('activeMode')=='SAFE_STOP','SOURCE_MODE_CHANGED')
                return dict(egoActorId=frame['egoActorId'],fresh=v.get('fresh') is True,held=v.get('held') is True,
                    mode=frame['activeMode'],speedKmh=frame['speedKmh'])
            first=control();client=carla.Client('127.0.0.1',2000);client.set_timeout(8.)
            world=client.get_world();ego=world.get_actor(first['egoActorId'])
            require(ego and ego.type_id.startswith('vehicle.'),'EGO_UNAVAILABLE')
            sequence=root/'sequence';sequence.mkdir(mode=0o700);frames=[];recorded_bytes=[0];record_after=[None];retained_sequence=None
            if a.reuse_sequence:
                # Original acquisition manifest is authoritative. Earlier cost
                # probes mislabeled a reused recording with their later load run.
                # Preserve those records and reconcile JPEG/metadata equality.
                previous_sequence=root.parent/'compute-continuation/sequence'
                data=json.loads((previous_sequence/'sequence.json').read_bytes());retained_sequence=data
                from vision_model_probe import validate_sequence
                frames.extend(validate_sequence(data,tensor_timing_only=True))
                require(len(frames)==60,'BOUNDED_SEQUENCE_NOT_CAPTURED')
                for row in frames:
                    path=previous_sequence/row['file'];raw=path.read_bytes()
                    require(not path.is_symlink() and hashlib.sha256(raw).hexdigest()==row['sha256'],'RETAINED_FRAME_CHANGED')
                    require(sum(p.stat().st_size for p in sequence.iterdir())+len(raw)<=32*1024**2,'RECORDING_BYTE_LIMIT')
                    (sequence/row['file']).write_bytes(raw);recorded_bytes[0]+=len(raw)
                result['sequenceReused']=True
            class RecordingLatest(Latest):
                def offer(self,row):
                    if record_after[0] is None:record_after[0]=time.monotonic()+2.
                    if time.monotonic()<record_after[0]:
                        super().offer(row);return
                    if row.get('jpeg') and len(frames)<60:
                        data=row['jpeg'];recorded_bytes[0]+=len(data)
                        require(recorded_bytes[0]<=32*1024**2,'RECORDING_BYTE_LIMIT')
                        name=str(row['frame'])+'.jpg';(sequence/name).write_bytes(data)
                        frames.append(dict(frame=row['frame'],simulationTime=row['simulationTime'],file=name,
                                           sha256=hashlib.sha256(data).hexdigest()))
                    super().offer(row)
            def run_models():
                nonlocal model
                try:
                    from vision_model_probe import replay_manifest
                    data=replay_manifest(source['runId'],frames,retained_sequence)
                    # Validate pair intervals before spending time on model execution.
                    from vision_model_probe import validate_sequence
                    atomic(sequence/'sequence.json',data);validate_sequence(data,tensor_timing_only=True)
                    archive=root/'sequence.tar'
                    with tarfile.open(archive,'w') as tar:
                        for f in sequence.iterdir():tar.add(f,arcname=str(Path('sequence')/f.name),recursive=False)
                    with archive.open('rb') as stream:
                        sent=subprocess.run(ssh_command(access_path(vision,'test'),12022,10)[:-2]+['tar','-C',guest_root,'-xf','-'],stdin=stream,capture_output=True,timeout=20)
                    require(sent.returncode==0,'SEQUENCE_REPLAY_TRANSFER_FAILED')
                    command='OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 -I -B '+probe_name+' --payload '+guest_root+'/payload --sequence '+guest_root+'/sequence --tensor-timing-only --steady-seconds 60'
                    model=subprocess.Popen(ssh_command(access_path(vision,'test'),12022,10)[:-2]+[command],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
                    with (root/'model-progress.jsonl').open('w') as log:
                        for line in model.stdout:
                            require(log.tell()<512*1024,'MODEL_OUTPUT_LIMIT');log.write(line);log.flush()
                            if line.startswith('{'):
                                value=json.loads(line)
                                if 'outcome' in value:
                                    model_result.clear();model_result.update(value)
                                if value.get('stage') in ('steady-start','steady-end'):
                                    model_window[value['stage']]=time.monotonic()
                                    atomic(root/'model-observation-window.json',model_window)
                                print(json.dumps(dict(stage='model',facts=value)),flush=True)
                        error=model.stderr.read(8192);code=model.wait(timeout=10)
                    require(code==0 and model_result.get('outcome')=='PASS_TENSOR_EXECUTION_ONLY','MODEL_EXECUTION_NOT_COMPLETE')
                except Exception as error:
                    if model_result.get('outcome')!='NOT_COMPLETE':
                        model_result.update(outcome='NOT_COMPLETE',code=str(error) if str(error).isupper() else type(error).__name__)
            output=root/'camera';output.mkdir(mode=0o700)
            class ComputeProbe(Probe):
                def phase_run(self,definition,psutil):
                    nonlocal model_thread
                    if definition[0]=='models-with-live-camera':
                        require(len(frames)==60,'BOUNDED_SEQUENCE_NOT_CAPTURED')
                        model_thread=threading.Thread(target=run_models,daemon=True);model_thread.start()
                        self.warmup=0.;self.seconds=90.
                    else:self.warmup=2.;self.seconds=10.
                    super().phase_run(definition,psutil)
                def start_preview(self):
                    super().start_preview()
                    self.pg.display.set_caption('Vision VM — bounded compute probe')
            observer=LoadObserver()
            probe=ComputeProbe(world,ego,carla,output,control,profile='camera',observer=observer)
            probe.display=RecordingLatest()
            probe.definitions=[(name,capture,True,visible,dict(REFERENCE)) for name,capture,visible in (
                ('replay-capture-baseline',True,True),('models-with-live-camera',True,True),('camera-removed-recovery',False,False))]
            for sig in (signal.SIGTERM,signal.SIGINT,signal.SIGHUP):
                signal.signal(sig,lambda *_:setattr(probe,'error','CAMPAIGN_INTERRUPTED'))
            camera=probe.run()
            camera.update(comparability='Stationary Safe Stop; real recorded replay and a separate live camera load',
                          aiInference='ENGINEERING_GUEST_REPLAY_ONLY; see model result',vmDelivery='REPLAY_OVER_SSH_ONLY')
            atomic(root/'compute-camera-report.json',camera)
            if model_thread:model_thread.join(timeout=5)
            require(model_thread and not model_thread.is_alive(),'MODEL_DEADLINE_EXCEEDED')
            require(model_result.get('outcome')=='PASS_TENSOR_EXECUTION_ONLY','MODEL_EXECUTION_NOT_COMPLETE')
            require(camera['outcome']=='PASS' and camera['ownSensorsRemoved'] and camera['worldSettingsUnchanged'],'CAMERA_RESULT_UNCONFIRMED')
            require(set(model_window)=={'steady-start','steady-end'},'STEADY_WINDOW_UNCONFIRMED')
            start,end=model_window['steady-start'],model_window['steady-end'];duration=end-start
            loaded=next(r for r in camera['phases'] if r['phase']=='models-with-live-camera')
            world_rows=[r for r in loaded['worldTimeline'] if start<=r['at']<=end]
            camera_rows=[r for r in loaded['cameraTimeline'] if start<=r['at']<=end]
            controls=[r for r in observer.samples if start<=r['at']<=end]
            resources=[r for r in loaded['resources'] if start<=r['at']<=end]
            require(duration>=59 and len(world_rows)>20 and len(camera_rows)>20 and len(resources)>20,'STEADY_LOAD_OBSERVATION_MISSING')
            result.update(outcome='PASS_ENGINEERING_TENSOR_TIMING_ONLY',modelResult=model_result,
                cameraPhases=[{k:r[k] for k in ('phase','worldFps','cameraFps','controllerStaleSamples')} for r in camera['phases']],
                recordedFrames=len(frames),recordedBytes=recorded_bytes[0],cameraMotion='STATIONARY_SAFE_STOP',
                activeProbeSha256=hashlib.sha256(active_probe).hexdigest(),
                replaySource=retained_sequence['source'] if a.reuse_sequence else source['runId'],liveCameraSource=source['runId'],
                sustainedLoad=dict(observedSeconds=duration,worldFps=(world_rows[-1]['frame']-world_rows[0]['frame'])/(world_rows[-1]['at']-world_rows[0]['at']),
                    cameraFps=(len(camera_rows)-1)/(camera_rows[-1]['at']-camera_rows[0]['at']),
                    staleControllerSamples=sum(not r['fresh'] for r in controls),controllerSamples=len(controls),
                    minimumAvailableBytes=min(r['availableBytes'] for r in resources),
                    swapGrowthBytes=resources[-1]['swapBytes']-resources[0]['swapBytes']),
                calibration='NOT_VALIDATED; AutoDrive BEV intentionally omitted in tensor-only profile',
                guestInput='Bounded replay copied over existing SSH, not a product live-image ingress')
        except Exception as error:
            result['code']=str(error) if str(error).isupper() else type(error).__name__
            if model_result:result['modelResult']=model_result
        finally:
            clean={}
            if source_started or json.loads((vision/JOURNAL).read_bytes()).get('source'):
                try:
                    app.source_service.simulation('stop',target='test')
                    WorkspaceService(env,app.source_service.driver).execute('close')
                    clean['sourceStopped']=True
                except Exception:clean['sourceStopped']=False
            try:
                stopped=runtime.execute('stop','test',timeout=60)
                clean['vmStopped']=stopped['vehicles']['test']['state']=='COMPLETED' and runtime.observe_readiness('test')['reason']=='VM_NOT_RUNNING'
            except Exception:clean['vmStopped']=False
            after=json.loads((retained/JOURNAL).read_bytes())['vehicles']['test']
            clean['mainIdentityPreserved']={k:after.get(k) for k in preserved}==preserved
            listeners=[]
            for port in (12022,2000,16443,18053):
                with socket.socket() as check:
                    check.settimeout(.2)
                    if check.connect_ex(('127.0.0.1',port))==0:listeners.append(port)
            clean['ownedListenersReleased']=not listeners
            result['cleanup']=clean
            if not all(clean.values()):result['outcome']='NOT_COMPLETE'
            result['seconds']=round(time.monotonic()-started,2);atomic(root/'result.json',result)
            print(json.dumps(result),flush=True)
    return 0 if result['outcome']=='PASS_ENGINEERING_TENSOR_TIMING_ONLY' else 1


if __name__=='__main__':raise SystemExit(main())
