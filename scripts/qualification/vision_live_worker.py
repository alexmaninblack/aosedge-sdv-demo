# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""One visible M4 live-camera -> Linux VM -> matched prediction scenario."""
import argparse
import hashlib
import io
import json
import math
import os
from pathlib import Path
import selectors
import signal
import socket
import subprocess
import sys
import tarfile
import threading
import time
from uuid import uuid4
import zipfile

sys.path.insert(0,str(Path(__file__).resolve().parent))
from vision_live_contract import calibration,encode_packet,model_to_raw,require,usable_capture_pair,write_all,validate_result,FrameClock,frame_reference,WIRE_SCHEMA


def atomic(path,value):
    part=path.with_suffix('.pending')
    fd=os.open(part,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'w') as f:json.dump(value,f,allow_nan=False);f.flush();os.fsync(f.fileno())
    os.replace(part,path)


def response(process,pending,timeout):
    if b'\n' in pending:
        line,remaining=pending.split(b'\n',1)
        return json.loads(line),remaining
    end=time.monotonic()+timeout
    with selectors.DefaultSelector() as selector:
        selector.register(process.stdout,selectors.EVENT_READ)
        while b'\n' not in pending:
            require(time.monotonic()<end,'GUEST_RESULT_DEADLINE')
            require(selector.select(max(0,end-time.monotonic())),'GUEST_RESULT_DEADLINE')
            data=os.read(process.stdout.fileno(),4096);require(data,'GUEST_RESULT_EOF')
            pending+=data;require(len(pending)<=65536,'GUEST_RESULT_LIMIT')
    line,remaining=pending.split(b'\n',1)
    return json.loads(line),remaining


def vector(value):return [value.x,value.y,value.z]
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def unit(a):
    length=math.sqrt(dot(a,a));require(length>1e-6,'CALIBRATION_BASIS_INVALID')
    return [v/length for v in a]
def cross(a,b):return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]


def main():
    p=argparse.ArgumentParser();p.add_argument('--context',type=Path,required=True);a=p.parse_args()
    root=a.context.parent;c=json.loads(a.context.read_bytes());vision=Path(c['visionRoot']);package=Path(c['packageRoot'])
    diagnostic=root.name=='live-diagnostic-01';moving=c.get('moving') is True
    require(root.name in ('live-camera-01','live-camera-02','live-camera-03','live-diagnostic-01','moving-camera-01','moving-camera-02') and vision==Path.home()/'SDV-Vision-Lab-Data','LIVE_SCOPE_INVALID')
    require(moving==root.name.startswith('moving-camera-'),'MOTION_SCOPE_INVALID')
    if moving:
        prior=json.loads((root.parent/'live-camera-03/result.json').read_bytes())
        require(prior['outcome']=='PASS_LIVE_ENGINEERING_PREVIEW' and all(prior['cleanup'].values()),'STATIONARY_PROOF_REQUIRED')
    if root.name=='moving-camera-02':
        prior=json.loads((root.parent/'moving-camera-01/result.json').read_bytes())
        require(prior.get('code')=='NATIVE_AUTOPILOT_NOT_OBSERVED' and all(prior['cleanup'].values()),'NATIVE_INPUT_ATTEMPT_NOT_RECONCILED')
    if root.name=='live-camera-02':
        prior=json.loads((root.parent/'live-camera-01/result.json').read_bytes())
        require(prior.get('code')=='CALIBRATION_SINGULAR' and all(prior['cleanup'][v] for v in
            ('sourceStopped','vmStopped','awakeHelperClosed','mainIdentityPreserved','listenersReleased','inferenceThreadExited')),'CALIBRATION_ATTEMPT_NOT_RECONCILED')
    if diagnostic or root.name=='live-camera-03':
        prior=json.loads((root.parent/'live-camera-02/result.json').read_bytes())
        require(prior.get('code')=='RESULT_BINDING_INVALID' and all(prior['cleanup'][v] for v in
            ('sourceStopped','vmStopped','awakeHelperClosed','mainIdentityPreserved','listenersReleased','inferenceThreadExited','cameraRemoved')),'LIVE_ATTEMPT_NOT_RECONCILED')
    if root.name=='live-camera-03':
        proof=json.loads((root.parent/'live-diagnostic-01/result.json').read_bytes())
        require(proof['outcome']=='PASS_REPLAY_DIAGNOSTIC' and all(proof['cleanup'].values()),'LIVE_REPLAY_PROOF_REQUIRED')
    require(subprocess.check_output(['/usr/sbin/sysctl','-n','hw.model'],text=True).strip()=='Mac16,8','M4_REQUIRED')
    require('"CGSSessionScreenIsLocked"=Yes' not in subprocess.check_output(['/usr/sbin/ioreg','-n','Root','-d1'],text=True),'M4_DESKTOP_LOCKED')
    require(hashlib.sha256((package/'application-manifest.json').read_bytes()).hexdigest()==c['manifestSha256'],'PACKAGE_CHANGED')
    for name,pin in c['proofFiles'].items():require(hashlib.sha256((root/name).read_bytes()).hexdigest()==pin,'PROOF_CHANGED')
    for port in (10022,12022,2000,16443,18053):
        with socket.socket() as s:s.settimeout(.2);require(s.connect_ex(('127.0.0.1',port))!=0,'CONFLICTING_OWNER')
    sys.path.insert(0,str(package/'aosedge-sdv-demo/apps/demo-orchestrator/src'))
    import aosedge_demo_orchestrator
    aosedge_demo_orchestrator.__path__.insert(0,str(root/'delta'))
    from aosedge_demo_orchestrator import runtime_paths
    from aosedge_demo_orchestrator.environment import EnvironmentService,JOURNAL
    from aosedge_demo_orchestrator.vm import VMService,access_path
    from aosedge_demo_orchestrator.vm_profiles import VISION
    from aosedge_demo_orchestrator.guest_access import ssh_command
    from aosedge_demo_orchestrator.application import DemoOrchestrator
    from aosedge_demo_orchestrator.workspace import WorkspaceService
    retained=Path(c['retainedRoot']);main_before=json.loads((retained/JOURNAL).read_bytes())['vehicles']['test']
    identity={k:main_before.get(k) for k in ('localVmId','overlay','unitId','nodeId','mac','sshPort')}
    require(identity['localVmId']==c['retainedTest'],'MAIN_CHANGED')
    before=json.loads((vision/JOURNAL).read_bytes())
    require(before['vmProfile']==VISION.name and before['vehicles']['test']['localVmId']==c['visionTest'],'VISION_CHANGED')
    result=dict(scenario='VISION_LIVE_CPU_PREVIEW',outcome='NOT_COMPLETE',phases=[],accuracy='NOT_QUALIFIED',
        assessment='NOT_RUN',nativeAosDeployment='NOT_RUN',fullE2E='NOT_RUN',cloudMutation=False,
        motionAuthority=False,drivingMode='NATIVE_AUTOPILOT' if moving else 'SAFE_STOP',carlaOrFactoryRebuilt=False,
        frameClock='CARLA_WORLD_SNAPSHOT_FRAME_MATCH',wireSchema=WIRE_SCHEMA)
    started=time.monotonic();stop=threading.Event();model_error=[];model=None;thread=None;probe=None;awake=None;source_started=False
    tick_subscription=None;frame_clock=FrameClock();measurement_active=[not moving]
    counters=dict(results=0,autodriveResults=0,invalidPairs=0,droppedPairs=0,skippedInvalidPairs=0);metrics=[];samples=[]
    def emit(value):print(json.dumps(value),flush=True)
    def step(name,action):
        emit(dict(stage=name,state='STARTED'));begin=time.monotonic();value=action()
        row=dict(stage=name,seconds=round(time.monotonic()-begin,2),facts=value)
        result['phases'].append(row);atomic(root/(name+'.json'),row);emit(dict(stage=name,state='COMPLETE',seconds=row['seconds']))
        return value
    with runtime_paths.installed_session(vision):
        env=EnvironmentService(vm_profile=VISION.name)
        runtime=VMService(env,progress=lambda v:emit(dict(stage='owner',state=str(v)[:110])))
        app=DemoOrchestrator(environment_service=env,vm_service=runtime)
        require(runtime.observe_readiness('test')['reason']=='VM_NOT_RUNNING','VISION_ALREADY_RUNNING')
        def guest(script,timeout=30):
            v=subprocess.run(ssh_command(access_path(vision,'test'),12022,10),input=script,capture_output=True,text=True,timeout=timeout)
            require(v.returncode==0,'GUEST_PREPARATION_FAILED');return v.stdout
        try:
            awake=subprocess.Popen(['/usr/bin/caffeinate','-d','-i','-u','-t','600'])
            def boot():
                value=runtime.execute('start','test',timeout=100)
                require(value['vehicles']['test']['state']=='COMPLETED','VISION_START_UNCONFIRMED')
                timed=runtime.sync_time();require(timed['state']=='READY','VISION_TIME_UNCONFIRMED')
                return dict(state='READY')
            step('vm-start',boot)
            payload='/home/sdv-vision-model-probe/payload';guest('test -f '+payload+'/input-lock.json\n')
            if diagnostic:
                cal=json.loads((root.parent/'live-camera-02/calibration.json').read_bytes());atomic(root/'calibration.json',cal)
                old=root.parent/'model-compute/compute-continuation/sequence'
                sequence=json.loads((old/'sequence.json').read_bytes());refs=sequence['frames'][3:5]
                frames=[dict(frame=v['frame'],simulationTime=v['simulationTime']) for v in refs]
                guest_dir='/home/sdv-vision-model-probe/'+root.name
                guest('set -eu\ntest ! -e '+guest_dir+'\nmkdir -m 700 '+guest_dir+'\n')
                archive=io.BytesIO()
                with tarfile.open(fileobj=archive,mode='w') as tar:
                    for name in ('vision_live_guest.py','vision_live_contract.py','vision_model_probe.py','calibration.json'):
                        tar.add(root/name,arcname=name,recursive=False)
                sent=subprocess.run(ssh_command(access_path(vision,'test'),12022,10)[:-2]+['tar','-C',guest_dir,'-xf','-'],input=archive.getvalue(),capture_output=True,timeout=15)
                require(sent.returncode==0,'GUEST_CODE_TRANSFER_FAILED')
                session=str(uuid4());command='OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 -I -B '+guest_dir+'/vision_live_guest.py --payload '+payload+' --session '+session+' --source '+sequence['source']+' --calibration '+guest_dir+'/calibration.json'
                with (root/'guest-diagnostic.log').open('wb') as error:
                    model=subprocess.Popen(ssh_command(access_path(vision,'test'),12022,10)[:-2]+[command],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=error,bufsize=0)
                ready,pending=response(model,b'',30);require(ready.get('state')=='READY','MODEL_START_UNCONFIRMED')
                packet=encode_packet(dict(schemaVersion=1,session=session,source=sequence['source'],calibration=cal['id'],frames=frames),[(old/v['file']).read_bytes() for v in refs])
                write_all(model.stdin,packet);value,pending=response(model,pending,15)
                atomic(root/'diagnostic-response.json',value);emit(dict(stage='REPLAY_DIAGNOSTIC',response=value))
                result.update(scenario='VISION_REPLAY_DIAGNOSTIC',outcome='PASS_REPLAY_DIAGNOSTIC' if value.get('state')=='RESULT' else 'NOT_COMPLETE',
                    code=value.get('code','DIAGNOSTIC_RESULT'),diagnosticResponse=value,liveCamera='NOT_RUN')
                return 0 if value.get('state')=='RESULT' else 1
            wheels=Path(c['cameraWheels']);tools=root/'tools';tools.mkdir(mode=0o700)
            from vision_camera import Probe,Latest,WHEELS,DEPENDENCIES,initial_snapshot,settings_projection
            for name,url,pin,size in WHEELS:
                path=wheels/name;require(path.stat().st_size==size and hashlib.sha256(path.read_bytes()).hexdigest()==pin,'CAMERA_WHEEL_CHANGED')
                with zipfile.ZipFile(path) as z:
                    require(all(not Path(v.filename).is_absolute() and '..' not in Path(v.filename).parts for v in z.infolist()),'WHEEL_PATH_INVALID')
                    z.extractall(tools)
            sys.path.insert(0,str(tools))
            import importlib,importlib.metadata
            importlib.invalidate_caches();require({n:importlib.metadata.version(n) for n in DEPENDENCIES}==DEPENDENCIES,'TOOLS_CHANGED')
            step('simulator-start',lambda:app.source_service.simulation('start',target='test'));source_started=True
            state=json.loads((vision/JOURNAL).read_bytes());source=state['source'];driver=app.source_service.driver
            assets=driver.assets();sys.path.append(str(assets['python-api-root']));import carla
            def control():
                value=driver.rpc(source,'status',str(uuid4()));frame=value.get('frame') or {}
                require(frame.get('runId')==source['runId'] and frame.get('activeMode') in (('SAFE_STOP','AUTOPILOT') if moving else ('SAFE_STOP',)),'SOURCE_MODE_CHANGED')
                require(not value.get('held'),'NATIVE_SOURCE_HELD_NO_MOTION_OVERRIDE')
                return dict(egoActorId=frame['egoActorId'],fresh=value.get('fresh') is True,speedKmh=frame['speedKmh'],mode=frame['activeMode'])
            first=control();client=carla.Client('127.0.0.1',2000);client.set_timeout(8.)
            world=client.get_world();ego=world.get_actor(first['egoActorId']);require(ego and ego.is_alive,'EGO_UNAVAILABLE')
            class CapturedPoseProbe(Probe):
                def callback(self,image,configuration=None):
                    if not hasattr(self,'capture_pose'):
                        self.capture_pose=dict(frame=image.frame,simulationTime=image.timestamp,
                                               inverse=image.transform.get_inverse_matrix())
                    super().callback(image,configuration)
            snapshot=initial_snapshot(world,ego)
            settings=world.get_settings()
            require(settings.synchronous_mode and abs(settings.fixed_delta_seconds-.05)<1e-8,'EXPECTED_SOURCE_TIMEBASE_REQUIRED')
            frame_clock.note(snapshot.frame,snapshot.timestamp.elapsed_seconds)
            tick_subscription=world.on_tick(lambda snap:frame_clock.note(snap.frame,snap.timestamp.elapsed_seconds))
            probe=CapturedPoseProbe(world,ego,carla,root,control);probe.jpeg=True
            probe.camera(True)
            deadline=time.monotonic()+8
            while not hasattr(probe,'capture_pose'):
                require(time.monotonic()<deadline and not probe.error,'CAMERA_CAPTURE_POSE_UNAVAILABLE');time.sleep(.025)
            road=world.get_map().get_waypoint(ego.get_location()).transform
            normal=unit(vector(road.get_up_vector()));forward=vector(ego.get_transform().get_forward_vector())
            forward=unit([v-dot(forward,normal)*n for v,n in zip(forward,normal)]);left=unit(cross(forward,normal))
            location=ego.get_location();origin=[location.x,location.y,road.location.z]
            camera_transform=probe.capture_pose['inverse']
            atomic(root/'calibration-inputs.json',dict(capture=probe.capture_pose,origin=origin,forward=forward,left=left))
            cal=calibration(camera_transform,origin,forward,left)
            # Independently check actual CARLA point/transform projection against H.
            from vision_live_contract import project
            errors=[]
            focal=1280/(2*math.tan(math.radians(50)/2))
            for x,y in ((15,5),(30,-3),(75,2),(150,-5)):
                point=[origin[i]+x*forward[i]+y*left[i] for i in range(3)]
                camera=[sum(camera_transform[i][j]*point[j] for j in range(3))+camera_transform[i][3] for i in range(3)]
                expected=[640+focal*camera[1]/camera[0],360-focal*camera[2]/camera[0]]
                actual=project(cal['rawToGround'],expected);errors.append(math.dist(actual,[x,y]))
            require(max(errors)<1e-5,'CARLA_CALIBRATION_CHECK_FAILED');cal['carlaProjectionCheckMetres']=max(errors)
            atomic(root/'calibration.json',cal);result['calibration']=dict(id=cal['id'],geometryCheckMetres=max(errors),accuracy='NOT_QUALIFIED')
            guest_dir='/home/sdv-vision-model-probe/'+root.name
            guest('set -eu\ntest ! -e '+guest_dir+'\nmkdir -m 700 '+guest_dir+'\n')
            archive=io.BytesIO()
            with tarfile.open(fileobj=archive,mode='w') as tar:
                for name in ('vision_live_guest.py','vision_live_contract.py','vision_model_probe.py','calibration.json'):
                    tar.add(root/name,arcname=name,recursive=False)
            transfer=subprocess.run(ssh_command(access_path(vision,'test'),12022,10)[:-2]+['tar','-C',guest_dir,'-xf','-'],input=archive.getvalue(),capture_output=True,timeout=15)
            require(transfer.returncode==0,'GUEST_CODE_TRANSFER_FAILED')
            session=str(uuid4());command='OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 -I -B '+guest_dir+'/vision_live_guest.py --payload '+payload+' --session '+session+' --source '+source['runId']+' --calibration '+guest_dir+'/calibration.json'
            with (root/'guest-diagnostic.log').open('wb') as diagnostic:
                model=subprocess.Popen(ssh_command(access_path(vision,'test'),12022,10)[:-2]+[command],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=diagnostic,bufsize=0)
            ready,pending=response(model,b'',30)
            require(ready==dict(state='READY',session=session,source=source['runId'],calibration=cal['id'],provider='CPUExecutionProvider'),'MODEL_START_UNCONFIRMED')
            latest=Latest();pairs=Latest();predicted=Latest();previous=[None]
            class LiveFrames(Latest):
                def offer(self,row):
                    require(row.get('jpeg') and len(row['jpeg'])<=4*1024**2,'CAMERA_JPEG_INVALID')
                    row=frame_clock.bind(row)
                    if row is None:return
                    older=previous[0];previous[0]=row;latest.offer(row)
                    if older:
                        interval=row['simulationTime']-older['simulationTime']
                        if usable_capture_pair(older,row) and .08<=interval<=.12:pairs.offer((older,row))
                        else:counters['skippedInvalidPairs']+=1
                    super().offer(row)
            probe.display=LiveFrames();probe.thread=threading.Thread(target=probe.worker,daemon=True);probe.thread.start()
            def infer_loop():
                nonlocal pending
                try:
                    while not stop.is_set():
                        pair=pairs.take()
                        if pair is None:stop.wait(.01);continue
                        require(time.monotonic()-pair[1]['received']<1,'STALE_CAMERA_PAIR')
                        refs=[frame_reference(v) for v in pair]
                        meta=dict(schemaVersion=WIRE_SCHEMA,session=session,source=source['runId'],calibration=cal['id'],frames=refs)
                        begin=time.monotonic();write_all(model.stdin,encode_packet(meta,[v['jpeg'] for v in pair]))
                        value,pending=response(model,pending,15)
                        if value.get('state')=='FAILED':
                            atomic(root/'guest-failure.json',value)
                            atomic(root/'failure-frame-metadata.json',refs)
                            require(False,value.get('code','GUEST_INFERENCE_FAILED'))
                        validate_result(value,meta)
                        age=(time.monotonic()-pair[1]['received'])*1000
                        if measurement_active[0]:
                            counters['results']+=1;counters['autodriveResults']+=value['autodrive']['valid'];counters['invalidPairs']+=not value['autodrive']['valid']
                            metrics.append(dict(frame=refs[1]['frame'],frames=refs,guestPipelineMs=value['guestPipelineMs'],arrivalToResultMs=age,
                                pairSeconds=refs[1]['simulationTime']-refs[0]['simulationTime'],
                                sensorPairSeconds=refs[1]['sensorSimulationTime']-refs[0]['sensorSimulationTime'],
                                transportRoundtripMs=(time.monotonic()-begin)*1000,pathPoints=len(value['autosteer']['path']),
                                detections=len(value['autospeed']['detections']),autodriveValid=value['autodrive']['valid']))
                        require(len(metrics)<=1800,'METRIC_RETENTION_LIMIT');predicted.offer(dict(row=pair[1],result=value,age=age))
                except Exception as error:
                    if 'pair' in locals() and pair:
                        atomic(root/'failure-frame-metadata.json',[dict(frame=v['frame'],simulationTime=v['simulationTime']) for v in pair])
                        for index,row in enumerate(pair):(root/f'failure-input-{index}.jpg').write_bytes(row['jpeg'])
                    if 'value' in locals():atomic(root/'last-guest-response.json',value)
                    message=str(error);model_error.append(message if message.isupper() else type(error).__name__);stop.set()
            thread=threading.Thread(target=infer_loop,daemon=True);thread.start()
            os.environ['PYGAME_HIDE_SUPPORT_PROMPT']='1';os.environ['SDL_VIDEO_WINDOW_POS']='20,60'
            import pygame as pg
            from PIL import Image,ImageDraw
            pg.display.init();pg.font.init();screen=pg.display.set_mode((1000,620));pg.display.set_caption('Vision Pilot — LIVE Linux VM CPU — Analysis only')
            font=pg.font.Font(None,23);small=pg.font.Font(None,19)
            for sig in (signal.SIGTERM,signal.SIGINT,signal.SIGHUP):signal.signal(sig,lambda *_:stop.set())
            def image(row,output=None):
                picture=Image.open(io.BytesIO(row['jpeg'])).convert('RGB')
                if output:
                    draw=ImageDraw.Draw(picture)
                    points=[model_to_raw(*v) for v in output['autosteer']['path']]
                    if len(points)>1:draw.line(points,fill=(50,255,120),width=5)
                    for d in output['autospeed']['detections']:
                        x1,y1=model_to_raw(*d['box'][:2]);x2,y2=model_to_raw(*d['box'][2:])
                        x1,x2=max(0,min(1279,x1)),max(0,min(1279,x2));y1,y2=max(0,min(719,y1)),max(0,min(719,y2))
                        if x2>x1 and y2>y1:
                            draw.rectangle((x1,y1,x2,y2),outline=(255,195,60),width=4)
                            draw.text((x1+3,y1+3),f"L{d['level']} {d['score']:.0%}",fill=(255,230,160),stroke_width=2,stroke_fill=(0,0,0))
                picture=picture.resize((480,270));return pg.image.fromstring(picture.tobytes(),picture.size,'RGB')
            begin=time.monotonic();waiting=moving;motion_deadline=begin+90;next_control=begin
            last_position=None;distance_metres=0.;moving_samples=0;mode_observation=dict(mode='SAFE_STOP',speedKmh=0.)
            last_ui=None;last_result=None;live_surface=None;result_surface=None;next_status=begin;next_sample=begin+10
            emit(dict(stage='WAIT_FOR_NATIVE_AUTOPILOT' if moving else 'LIVE_VISIBLE',seconds=c['liveSeconds'],mode='SAFE_STOP',provider='CPUExecutionProvider'))
            while not stop.is_set() and (waiting or time.monotonic()-begin<c['liveSeconds']):
                require(not probe.error,probe.error or 'CAMERA_FAILED')
                for event in pg.event.get():
                    if event.type==pg.QUIT or event.type==pg.KEYDOWN and event.key==pg.K_ESCAPE:stop.set()
                row=latest.take()
                if row:last_ui=row;live_surface=image(row)
                computed=predicted.take()
                if computed:last_result=computed;result_surface=image(computed['row'],computed['result'])
                now=time.monotonic()
                if now>=next_control:
                    mode_observation=control();require(mode_observation['egoActorId']==ego.id,'SOURCE_CHANGED');next_control=now+1
                    if waiting:
                        require(now<motion_deadline,'NATIVE_AUTOPILOT_NOT_OBSERVED')
                        if mode_observation['mode']=='AUTOPILOT' and mode_observation['speedKmh']>.5:
                            waiting=False;measurement_active[0]=True;begin=now;next_status=now;next_sample=now+10
                            emit(dict(stage='MOVING_CONFIRMED',mode='AUTOPILOT',speedKmh=mode_observation['speedKmh']))
                    if measurement_active[0]:
                        if moving:require(mode_observation['mode']=='AUTOPILOT','NATIVE_AUTOPILOT_INTERRUPTED')
                        location=ego.get_location();position=[location.x,location.y,location.z]
                        if last_position:distance_metres+=math.dist(position,last_position)
                        last_position=position;moving_samples+=mode_observation['speedKmh']>.5
                        samples.append(mode_observation)
                screen.fill((16,23,34))
                def text(value,pos,color=(220,229,240),tiny=False):screen.blit((small if tiny else font).render(str(value),True,color),pos)
                text('Vision Pilot | Linux ARM64 VM / 4 CPU / FP32 | ANALYSIS ONLY',(16,16))
                text(('Select Autopilot in native Driving Control — no hold or Cloud bypass' if waiting else
                      f"Native {mode_observation['mode']} | {mode_observation['speedKmh']:.1f} km/h | Vision is read-only"),(16,44),(255,199,100),True)
                text('Live camera — no model overlay',(16,82));text('Processed frame — matching model predictions',(510,82))
                if live_surface:screen.blit(live_surface,(16,112))
                stale=not last_result or now-last_result['row']['received']>1
                if result_surface and not stale:screen.blit(result_surface,(510,112))
                else:text('Waiting / stale result — overlay hidden',(535,220),(255,199,100))
                text(f"Camera frame: {last_ui['frame'] if last_ui else 'warming'}",(16,392),tiny=True)
                text(f"Result frame: {last_result['row']['frame'] if last_result else 'warming'}",(510,392),tiny=True)
                if last_result and not stale:
                    v=last_result['result'];lead=v['autodrive'];ad='Waiting for a valid frame pair'
                    if lead['valid']:
                        distance=lead['distanceEstimateMetres'];ad=f"Lead p={lead['probability']:.0%}; "+('no confirmed distance' if distance is None else f'est. {distance:.1f} m')
                    text('AutoDrive',(16,440));text(ad,(16,470),tiny=True)
                    text('AutoSteer',(355,440));text(f"{len(v['autosteer']['path'])} model-path points",(355,470),tiny=True)
                    text('AutoSpeed',(690,440));text(f"{len(v['autospeed']['detections'])} boxes / path-relative L0–L3",(690,470),tiny=True)
                    text(f"Guest pipeline: {v['guestPipelineMs']:.0f} ms | Image arrival age: {(now-last_result['row']['received'])*1000:.0f} ms",(16,514),tiny=True)
                text('Green = predicted ego path, not lane markings. Amber = model detections, not simulator labels.',(16,551),tiny=True)
                text('World-frame time + original sensor time retained. Accuracy NOT QUALIFIED. Esc stops scenario.',(16,578),(255,199,100),True)
                pg.display.flip()
                if now>=next_status:
                    counters['droppedPairs']=pairs.counters()['replaced']
                    emit(dict(stage='WAITING_NATIVE_INPUT' if waiting else 'LIVE_PROGRESS',seconds=round(now-begin),mode=mode_observation['mode'],speedKmh=mode_observation['speedKmh'],**counters));next_status=now+15
                if not waiting and now>=next_sample and last_result and not stale and len(result.get('screenshots',[]))<4:
                    name=f"live-{len(result.get('screenshots',[]))+1:02d}.png";pg.image.save(screen,root/name)
                    require((root/name).stat().st_size<=4*1024**2,'SCREENSHOT_LIMIT');result.setdefault('screenshots',[]).append(name);next_sample=now+30
                time.sleep(.025)
            stop.set();thread.join(timeout=18)
            require(not thread.is_alive(),'INFERENCE_THREAD_EXIT_UNCONFIRMED')
            require(not model_error,model_error[0] if model_error else 'MODEL_FAILED')
            require(counters['results']>=30 and counters['autodriveResults']>=10,'LIVE_MODEL_RESULTS_INSUFFICIENT')
            require(counters['results']==counters['autodriveResults'],'NOT_ALL_THREE_MODELS_VALID')
            if moving:require(moving_samples>=10 and distance_metres>5,'ACTUAL_MOTION_NOT_PROVEN')
            from vision_camera import distribution
            counters['droppedPairs']=pairs.counters()['replaced']
            result.update(outcome='PASS_LIVE_ENGINEERING_PREVIEW',counters=dict(counters),liveSeconds=time.monotonic()-begin,
                guestPipelineMs=distribution([v['guestPipelineMs'] for v in metrics]),
                arrivalToResultMs=distribution([v['arrivalToResultMs'] for v in metrics]),
                maximumPathPoints=max(v['pathPoints'] for v in metrics),maximumDetections=max(v['detections'] for v in metrics),
                staleControllerSamples=sum(not v['fresh'] for v in samples),movingSamples=moving_samples,distanceMetres=distance_metres,
                clock=frame_clock.facts(),recording='Four bounded UI snapshots; no raw video history')
            atomic(root/'frame-metrics.json',metrics)
            atomic(root/'motion-observations.json',samples)
        except Exception as error:
            message=str(error);result['code']=message if message.isupper() and message.replace('_','').isalnum() else type(error).__name__
            emit(dict(stage='FAILED',code=result['code']))
        finally:
            stop.set();clean={}
            if tick_subscription is not None:
                try:world.remove_on_tick(tick_subscription);clean['worldTickObserverRemoved']=True
                except Exception:clean['worldTickObserverRemoved']=False
            if probe:
                probe.stop.set()
                try:
                    probe.camera(False)
                    if probe.thread:probe.thread.join(timeout=5)
                    deadline=time.monotonic()+2
                    while True:
                        remaining=[v for v in world.get_actors().filter('sensor.camera.rgb') if v.id in probe.sensor_ids]
                        if not remaining or time.monotonic()>=deadline:break
                        time.sleep(.05)
                    clean['cameraRemoved']=not remaining and settings_projection(world.get_settings())==probe.original
                except Exception:clean['cameraRemoved']=False
            if thread:thread.join(timeout=18)
            if model:
                try:model.stdin.close();model.wait(timeout=10);clean['guestProcessExited']=model.returncode==0
                except Exception:clean['guestProcessExited']=False
            if 'pg' in locals():pg.quit()
            if awake:
                try:awake.terminate();awake.wait(timeout=5);clean['awakeHelperClosed']=True
                except Exception:clean['awakeHelperClosed']=False
            if source_started:
                try:app.source_service.simulation('stop',target='test');WorkspaceService(env,driver).execute('close');clean['sourceStopped']=True
                except Exception:clean['sourceStopped']=False
            try:
                stopped=runtime.execute('stop','test',timeout=60)
                clean['vmStopped']=stopped['vehicles']['test']['state']=='COMPLETED' and runtime.observe_readiness('test')['reason']=='VM_NOT_RUNNING'
            except Exception:clean['vmStopped']=False
            if thread and thread.is_alive():thread.join(timeout=3)
            clean['inferenceThreadExited']=not thread or not thread.is_alive()
            after=json.loads((retained/JOURNAL).read_bytes())['vehicles']['test']
            clean['mainIdentityPreserved']={k:after.get(k) for k in identity}==identity
            clean['listenersReleased']=True
            for port in (12022,2000,16443,18053):
                with socket.socket() as s:s.settimeout(.2);clean['listenersReleased']&=s.connect_ex(('127.0.0.1',port))!=0
            result['cleanup']=clean
            if not all(clean.values()):result['outcome']='NOT_COMPLETE'
            result['seconds']=round(time.monotonic()-started,2);atomic(root/'result.json',result);emit(result)
    return 0 if result['outcome'] in ('PASS_LIVE_ENGINEERING_PREVIEW','PASS_REPLAY_DIAGNOSTIC') else 1


if __name__=='__main__':raise SystemExit(main())
