# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Bounded camera characterization; no vehicle spawning, ticking or actuation."""
import io
import json
import math
import os
from pathlib import Path
import subprocess
import threading
import time
from uuid import uuid4


PHASES = (
    ('A-baseline', False, False, False),
    ('B-visible-rgb', True, False, True),
    ('B-rgb-measure', True, False, False),
    ('C-visible-jpeg', True, True, True),
    ('C-jpeg-measure', True, True, False),
    ('A-recovery', False, False, False),
)
DEPENDENCIES = {'Pillow': '13.0.0', 'psutil': '7.2.2', 'pygame': '2.6.1'}
REFERENCE = dict(width=1280,height=720,postprocess=True,rayTracing=True)


def phase_definitions(profile):
    if profile=='camera':
        return [(*phase,dict(REFERENCE)) for phase in PHASES]
    if profile=='profile-static':
        return [(name,*phase[1:],dict(REFERENCE)) for name,phase in zip(
            ('P0-baseline','P1-visible-rgb','P2-rgb-no-preview','P3-visible-jpeg','P4-jpeg-no-preview','P5-recovery'),PHASES)]
    if profile=='profile-motion':
        return [(name,capture,jpeg,visible,dict(REFERENCE)) for name,capture,jpeg,visible in (
            ('D0-baseline',False,False,False),('D1-visible-jpeg',True,True,True),('D2-recovery',False,False,False))]
    reduced=dict(REFERENCE,postprocess=False,rayTracing=False)
    if profile=='optimize-static':
        return [
            ('S0-baseline',False,False,False,dict(REFERENCE)),
            ('S1-reference-720',True,True,True,dict(REFERENCE)),
            ('S2-no-rt-720',True,True,True,dict(REFERENCE,rayTracing=False)),
            ('S3-no-post-720',True,True,True,reduced),
            ('S4-no-post-540',True,True,True,dict(reduced,width=960,height=540)),
            ('S5-no-post-360',True,True,True,dict(reduced,width=640,height=360)),
            ('S6-reference-repeat',True,True,True,dict(REFERENCE)),
            ('S7-recovery',False,False,False,dict(REFERENCE)),
        ]
    require(profile=='optimize-motion','CAMERA_PROFILE_INVALID')
    return [
        ('M0-baseline',False,False,False,dict(REFERENCE)),
        ('M1-reference-720',True,True,True,dict(REFERENCE)),
        ('M2-no-post-720',True,True,True,reduced),
    ]
WHEELS = (
    ('pillow-13.0.0-cp312-cp312-macosx_11_0_arm64.whl',
     'https://files.pythonhosted.org/packages/39/4b/f2ed53d83aa44ac19599ac0a54897f867fafb95f406980d1e24083f8cbe3/',
     'fc481f742ccda20e9ed760b8f978dff50f2a4e9bc253ac167fb0a05b0783ef52',4852329),
    ('psutil-7.2.2-cp36-abi3-macosx_11_0_arm64.whl',
     'https://files.pythonhosted.org/packages/80/c4/f5af4c1ca8c1eeb2e92ccca14ce8effdeec651d5ab6053c589b074eda6e1/',
     '1a7b04c10f32cc88ab39cbf606e117fd74721c831c98a27dc04578deb0c16979',129859),
    ('pygame-2.6.1-cp312-cp312-macosx_11_0_arm64.whl',
     'https://files.pythonhosted.org/packages/cd/53/77ccbc384b251c6e34bfd2e734c638233922449a7844e3c7a11ef91cee39/',
     'c8040ea2ab18c6b255af706ec01355c8a6b08dc48d77fd4ee783f8fc46a843bf',12384524),
)


def require(ok, code):
    if not ok:
        raise ValueError(code)


def distribution(values):
    values = sorted(v for v in values if math.isfinite(v))
    if not values:
        return dict(count=0, min=None, median=None, p95=None, p99=None, max=None)
    def percentile(p):
        index = (len(values)-1)*p
        low = int(index)
        return values[low]+(values[min(low+1,len(values)-1)]-values[low])*(index-low)
    return dict(count=len(values), min=values[0], median=percentile(.5),
                p95=percentile(.95), p99=percentile(.99), max=values[-1])


def frame_metadata(frame, width, height):
    require(type(frame.frame) is int and frame.frame >= 0, 'CAMERA_FRAME_INVALID')
    require(math.isfinite(frame.timestamp) and frame.timestamp >= 0, 'CAMERA_TIME_INVALID')
    require((frame.width, frame.height) == (width, height), 'CAMERA_DIMENSIONS_CHANGED')
    require(len(frame.raw_data) == width*height*4, 'CAMERA_BUFFER_INVALID')
    data = bytes(frame.raw_data)
    return dict(frame=frame.frame, simulationTime=frame.timestamp, received=time.monotonic(), raw=data)


class Latest:
    """Exactly one owned pending value; replacing a value counts a drop."""
    def __init__(self):
        self.lock = threading.Lock()
        self.value = None
        self.offered = self.replaced = self.taken = 0

    def offer(self, value):
        with self.lock:
            self.offered += 1
            self.replaced += self.value is not None
            self.value = value

    def take(self):
        with self.lock:
            value, self.value = self.value, None
            self.taken += value is not None
            return value

    def counters(self):
        with self.lock:
            return dict(offered=self.offered, replaced=self.replaced,
                        taken=self.taken, pending=int(self.value is not None), capacity=1)


def delta(after, before):
    return {key:after[key]-before[key] for key in ('offered','replaced','taken')}


def settings_projection(settings):
    names = ('synchronous_mode','fixed_delta_seconds','no_rendering_mode',
             'substepping','max_substep_delta_time','max_substeps')
    return {name:getattr(settings,name,None) for name in names}


def sample_matches_format(row,jpeg):
    # The previous phase can leave one raw value while the encoder switches.
    return bool(row.get('jpeg'))==bool(jpeg)


def initial_snapshot(world,ego,timeout=5.,clock=time.monotonic,sleep=time.sleep):
    """A newly subscribed client can initially hold the empty episode state."""
    end=clock()+timeout
    while True:
        snapshot=world.get_snapshot()
        if snapshot.frame>0 and snapshot.find(ego.id) is not None:
            require(ego.is_alive,'SELECTED_EGO_DISAPPEARED')
            return snapshot
        require(clock()<end,'EGO_NOT_IN_CURRENT_WORLD')
        sleep(.025)


class Probe:
    def __init__(self, world, ego, carla, output, control, warmup=10., seconds=45.,profile='camera',observer=None):
        self.world, self.ego, self.carla = world, ego, carla
        self.output, self.control = Path(output), control
        self.warmup, self.seconds = warmup, seconds
        self.width, self.height = 1280, 720
        self.profile=profile
        self.observer=observer
        self.definitions=phase_definitions(profile)
        self.camera_profile=dict(REFERENCE)
        self.raw, self.display = Latest(), Latest()
        self.stop = threading.Event()
        self.sensor = None
        self.sensor_ids = []
        self.destroyed_ids = set()
        self.thread = None
        self.pg = self.screen = self.font = None
        self.error = None
        self.jpeg = False
        self.phase = None
        self.rows = []
        self.callback_rows = []
        self.codec_rows = []
        self.lock = threading.Lock()
        self.sensor_role = 'sdv-camera-probe-'+uuid4().hex[:16]
        self.original = settings_projection(world.get_settings())
        self.original_sensors = {a.id for a in world.get_actors().filter('sensor.*')}

    def callback(self, image, configuration=None):
        start = time.monotonic()
        try:
            configuration=configuration or self.camera_profile
            row = frame_metadata(image, configuration['width'], configuration['height'])
            row.update(width=configuration['width'],height=configuration['height'],
                       cameraProfile=configuration,encodeJpeg=self.jpeg)
            self.raw.offer(row)
            with self.lock:
                self.callback_rows.append((start,row['frame'],row['simulationTime'],time.monotonic()-start))
                require(len(self.callback_rows) < 12000, 'CALLBACK_RETENTION_LIMIT')
        except Exception as exc:
            self.error = str(exc) if isinstance(exc,ValueError) else 'CAMERA_CALLBACK_FAILED'

    def worker(self):
        from PIL import Image
        while not self.stop.wait(.001):
            row = self.raw.take()
            if row is None:
                continue
            try:
                started = time.monotonic()
                if row['encodeJpeg']:
                    image = Image.frombytes('RGB',(row['width'],row['height']),row['raw'],'raw','BGRX')
                    stream = io.BytesIO()
                    image.save(stream,format='JPEG',quality=85,subsampling=2,optimize=False)
                    payload = stream.getvalue()
                    require(len(payload) <= 4*1024**2, 'JPEG_SIZE_LIMIT')
                    row = dict(row,jpeg=payload)
                else:
                    payload = None
                finished = time.monotonic()
                with self.lock:
                    self.codec_rows.append((started,row['frame'],finished-started,
                                            len(payload) if payload else 0,finished-row['received']))
                    require(len(self.codec_rows)<12000,'CODEC_RETENTION_LIMIT')
                self.display.offer(row)
            except Exception as exc:
                self.error = str(exc) if isinstance(exc,ValueError) else 'CAMERA_CODEC_FAILED'
                return

    def camera(self, enabled, configuration=None):
        configuration=dict(configuration or REFERENCE)
        if enabled and self.sensor is not None and configuration!=self.camera_profile:
            self.camera(False)
        if enabled and self.sensor is None:
            self.camera_profile=configuration
            self.width,self.height=configuration['width'],configuration['height']
            bp = self.world.get_blueprint_library().find('sensor.camera.rgb')
            attributes=dict(image_size_x=str(self.width),image_size_y=str(self.height),fov='50',sensor_tick='0.1')
            if self.profile.startswith('optimize-'):
                attributes.update(enable_postprocess_effects=str(configuration['postprocess']).lower(),
                                  use_ray_tracing=str(configuration['rayTracing']).lower())
            for name,value in attributes.items():
                require(bp.has_attribute(name),'CAMERA_ATTRIBUTE_UNAVAILABLE')
                bp.set_attribute(name,value)
            require(bp.has_attribute('role_name'),'CAMERA_ROLE_ATTRIBUTE_REQUIRED')
            bp.set_attribute('role_name',self.sensor_role)
            self.sensor = self.world.spawn_actor(bp,self.carla.Transform(self.carla.Location(x=1.6,z=1.5)),
                                                attach_to=self.ego)
            self.sensor_ids.append(self.sensor.id)
            self.sensor.listen(lambda image:self.callback(image,configuration))
            self.attributes = dict(self.sensor.attributes)
        elif not enabled and self.sensor is not None:
            sensor = self.sensor
            sensor.stop()
            require(sensor.destroy() is True,'OWNED_CAMERA_DESTROY_FAILED')
            self.destroyed_ids.add(sensor.id)
            self.sensor = None
            self.raw.take(); self.display.take()

    def start_preview(self):
        os.environ['PYGAME_HIDE_SUPPORT_PROMPT']='1'
        import pygame
        self.pg = pygame
        pygame.display.init();pygame.font.init()
        w,h = pygame.display.get_desktop_sizes()[0]
        os.environ['SDL_VIDEO_WINDOW_POS']=f'20,{max(40,h-420)}'
        self.screen=pygame.display.set_mode((560,370))
        pygame.display.set_caption('SDV front camera - measurement')
        self.font=pygame.font.Font(None,23)

    def paint(self, phase, visible, remaining):
        from PIL import Image
        pg=self.pg
        start=time.monotonic()
        for event in pg.event.get():
            if event.type==pg.QUIT or event.type==pg.KEYDOWN and event.key==pg.K_ESCAPE:
                raise ValueError('OPERATOR_STOPPED_CAMERA_PROBE')
        self.screen.fill((18,25,34))
        title=f'{phase} | {remaining:.0f}s | '+('LIVE' if visible else 'preview paused for measurement')
        self.screen.blit(self.font.render(title,True,(225,235,245)),(10,8))
        row=self.display.take()
        if row and row['cameraProfile']!=self.camera_profile:
            row=None
        decode=0.
        if visible and row:
            begin=time.monotonic()
            if row.get('jpeg'):
                image=Image.open(io.BytesIO(row['jpeg'])).convert('RGB')
                surface=pg.image.frombuffer(image.tobytes(),(row['width'],row['height']),'RGB')
            else:
                surface=pg.image.frombuffer(row['raw'],(row['width'],row['height']),'BGRA')
            decode=time.monotonic()-begin
            self.last_surface=pg.transform.smoothscale(surface,(540,304))
            self.last_frame=row['frame']
            self.last_received=row['received']
            if phase not in self.samples and sample_matches_format(row,self.jpeg):
                image=Image.frombytes('RGB',(row['width'],row['height']),row['raw'],'raw','BGRX')
                from PIL import ImageStat
                st=ImageStat.Stat(image)
                require(max(st.stddev)>1.,'CAMERA_IMAGE_EMPTY_OR_UNIFORM')
                image.thumbnail((640,360))
                name=phase+'.'+('jpg' if row.get('jpeg') else 'png')
                if row.get('jpeg'):
                    (self.output/name).write_bytes(row['jpeg'])
                else:
                    image.save(self.output/name)
                self.samples[phase]=dict(file=name,frame=row['frame'],simulationTime=row['simulationTime'],
                                         channelMean=st.mean,channelStddev=st.stddev)
        if visible and getattr(self,'last_surface',None) is not None:
            self.screen.blit(self.last_surface,(10,36))
            text=f'CARLA frame {self.last_frame} | image age {(time.monotonic()-self.last_received)*1000:.0f} ms'
            self.screen.blit(self.font.render(text,True,(150,210,180)),(10,345))
        else:
            text='No added camera' if phase.startswith('A-') else 'Capture is active; display isolated from the measurement'
            self.screen.blit(self.font.render(text,True,(160,175,190)),(10,120))
        pg.display.flip()
        return (time.monotonic()-start)*1000,decode*1000

    def resources(self, psutil):
        groups={k:dict(cpu=0.,rss=0,pids=[]) for k in ('carla','vm','gateway','presenter','probe')}
        for p in psutil.process_iter(['pid','name','cpu_times','memory_info']):
            try:
                a=p.info;name=(a.get('name') or '').lower()
                group=('probe' if a['pid']==os.getpid() else 'carla' if 'carlaunreal' in name else
                       'vm' if 'qemu-system' in name else 'gateway' if name in ('carla-ego-runtime','keyboardcontrol')
                       else 'presenter' if 'presenter' in name else None)
                if group and a['cpu_times'] and a['memory_info']:
                    g=groups[group];g['cpu']+=a['cpu_times'].user+a['cpu_times'].system
                    g['rss']+=a['memory_info'].rss;g['pids'].append(a['pid'])
            except (psutil.NoSuchProcess,psutil.AccessDenied):pass
        vm=psutil.virtual_memory();swap=psutil.swap_memory()
        return dict(at=time.monotonic(),cpuPercent=psutil.cpu_percent(),availableBytes=vm.available,
                    usedBytes=vm.used,swapBytes=swap.used,groups=groups)

    def phase_run(self, definition, psutil):
        name,capture,jpeg,visible,configuration=definition
        print(json.dumps(dict(stage=name,state='STARTED',visible=visible,configuration=configuration)),flush=True)
        self.jpeg=jpeg;self.camera(capture,configuration)
        self.last_surface=None
        started=time.monotonic();begin=started+self.warmup;end=begin+self.seconds
        if self.observer:self.observer.phase_start(name,started,self.warmup,self.seconds)
        paints=[];decodes=[];snapshots=[];resources=[];controls=[];positions=[]
        sample_next=started;reference=None;raw_before=None;last_frame=None;last_tick=None;intervals=[]
        while time.monotonic()<end:
            now=time.monotonic()
            require(self.error is None,self.error or 'CAMERA_WORKER_FAILED')
            snapshot=self.world.get_snapshot()
            require(self.ego.is_alive,'SELECTED_EGO_DISAPPEARED')
            if now>=begin:
                if reference is None:
                    reference=(now,snapshot.timestamp.elapsed_seconds,snapshot.frame)
                    raw_before=self.raw.counters()
                if snapshot.frame!=last_frame:
                    snapshots.append((now,snapshot.frame,snapshot.timestamp.elapsed_seconds))
                    if last_tick is not None:intervals.append((now-last_tick)*1000)
                    last_tick=now;last_frame=snapshot.frame
            paint,decode=self.paint(name,visible,max(0,end-now))
            if now>=begin:paints.append(paint);decodes.append(decode)
            if now>=sample_next:
                sample_next=now+1
                observed=self.control()
                require(observed['egoActorId']==self.ego.id,'SELECTED_SOURCE_CHANGED')
                if self.profile.endswith('-static'):
                    require(observed['mode']=='MANUAL' and observed['speedKmh']<=.5,'STATIC_COMPARISON_MOVED')
                if self.observer:self.observer.sample(observed)
                if now>=begin:
                    resources.append(self.resources(psutil));controls.append(observed)
                    t=self.ego.get_location();positions.append((t.x,t.y,t.z))
            time.sleep(.015)
        require(reference is not None and len(snapshots)>1,'SIMULATION_DID_NOT_ADVANCE')
        elapsed=time.monotonic()-reference[0]
        with self.lock:
            frames=[r for r in self.callback_rows if begin<=r[0]<=end]
            codecs=[r for r in self.codec_rows if begin<=r[0]<=end]
        require(not capture or len(frames)>=10,'CAMERA_FRAMES_MISSING')
        sim_elapsed=snapshots[-1][2]-reference[1]
        raw_delta=delta(self.raw.counters(),raw_before)
        row=dict(phase=name,capture=capture,jpeg=jpeg,visible=visible,measurementSeconds=elapsed,
            cameraConfiguration=configuration,sensorAttributes=dict(self.attributes) if capture else None,
            simulationSeconds=sim_elapsed,realTimeFactor=sim_elapsed/elapsed,
            worldFps=(snapshots[-1][1]-reference[2])/elapsed,
            cameraFrames=len(frames),cameraFps=len(frames)/elapsed,
            cameraPerSimSecond=len(frames)/sim_elapsed if sim_elapsed else None,
            cameraIntervalMs=distribution([(b[0]-a[0])*1000 for a,b in zip(frames,frames[1:])]),
            simulationObservationIntervalMs=distribution(intervals),
            callbackMs=distribution([r[3]*1000 for r in frames]),
            encodeMs=distribution([r[2]*1000 for r in codecs]) if jpeg else None,
            encodedBytes=distribution([r[3] for r in codecs]) if jpeg else None,
            encodedMbps=sum(r[3] for r in codecs)*8/elapsed/1e6 if jpeg else None,
            callbackToEncodedMs=distribution([r[4]*1000 for r in codecs]) if jpeg else None,
            previewPaintMs=distribution(paints),previewDecodeMs=distribution([v for v in decodes if v]),
            pendingRaw=raw_delta,queueCapacity=1,resources=resources,
            controllerSamples=controls,
            movingSamples=sum(c['speedKmh']>.5 for c in controls),
            controllerFreshSamples=sum(c['fresh'] for c in controls),
            controllerStaleSamples=sum(not c['fresh'] for c in controls),
            controllerReadSamplingHz=1,
            distanceMetres=sum(math.dist(a,b) for a,b in zip(positions,positions[1:])),
            contentSample=self.samples.get(name),settingsUnchanged=settings_projection(self.world.get_settings())==self.original)
        require(row['settingsUnchanged'],'WORLD_SETTINGS_CHANGED')
        require(all(b[1]>a[1] and b[2]>a[2] for a,b in zip(frames,frames[1:])),'CAMERA_ORDER_REGRESSION')
        if self.observer:
            row['worldTimeline']=[dict(at=r[0],frame=r[1],simulationTime=r[2]) for r in snapshots]
            row['cameraTimeline']=[dict(at=r[0],frame=r[1],simulationTime=r[2]) for r in frames]
            self.observer.phase_end()
        self.rows.append(row)
        (self.output/(name+'.json')).write_text(json.dumps(row,indent=2)+'\n')
        print(json.dumps(dict(stage=name,state='COMPLETE',worldFps=row['worldFps'],
                             cameraFps=row['cameraFps'],realTimeFactor=row['realTimeFactor'],
                             staleControlSamples=row['controllerStaleSamples'])),flush=True)

    def run(self):
        import psutil
        self.samples={};started=time.monotonic();completed=False;cleanup=False
        awake=None;cleanup_errors=[]
        try:
            require(self.original['no_rendering_mode'] is not True,'RENDERING_IS_DISABLED')
            awake=subprocess.Popen(['/usr/bin/caffeinate','-d','-i','-u','-t','900'],
                                    stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            self.start_preview();psutil.cpu_percent()
            self.thread=threading.Thread(target=self.worker,daemon=True);self.thread.start()
            for definition in self.definitions:self.phase_run(definition,psutil)
            require(len(self.samples)==sum(d[3] for d in self.definitions),'VISIBLE_CAMERA_SAMPLES_REQUIRED')
            completed=True
        finally:
            self.stop.set()
            def finish(action,code):
                try:action()
                except Exception:cleanup_errors.append(code)
            finish(lambda:self.camera(False),'CAMERA_STOP_FAILED')
            # Reconcile a lost spawn response by exact probe role and parent;
            # never adopt or destroy another sensor.
            def reconcile():
                for actor in self.world.get_actors().filter('sensor.camera.rgb'):
                    if (actor.id not in self.destroyed_ids and actor.attributes.get('role_name')==self.sensor_role
                            and actor.parent and actor.parent.id==self.ego.id):
                        actor.stop()
                        require(actor.destroy() is True,'OWNED_CAMERA_DESTROY_FAILED')
                        self.destroyed_ids.add(actor.id)
            finish(reconcile,'CAMERA_RECONCILIATION_FAILED')
            if self.thread:
                finish(lambda:self.thread.join(5),'CODEC_JOIN_FAILED')
                if self.thread.is_alive():cleanup_errors.append('CODEC_WORKER_DID_NOT_EXIT')
            if self.observer:finish(self.observer.close,'PROFILE_HELPER_EXIT_UNCONFIRMED')
            self.raw.take();self.display.take()
            if self.pg:finish(self.pg.quit,'PREVIEW_CLOSE_FAILED')
            if awake:finish(lambda:(awake.terminate(),awake.wait(timeout=5)),'AWAKE_HELPER_CLOSE_FAILED')
            remaining=set();unchanged=False
            def observe_cleanup():
                nonlocal remaining,unchanged
                end=time.monotonic()+2
                while True:
                    remaining={a.id for a in self.world.get_actors().filter('sensor.*')}
                    if not remaining.intersection(self.sensor_ids) or time.monotonic()>=end:break
                    time.sleep(.05)
                unchanged=settings_projection(self.world.get_settings())==self.original
            finish(observe_cleanup,'CLEANUP_OBSERVATION_FAILED')
            cleanup=(not cleanup_errors and not remaining.intersection(self.sensor_ids)
                     and self.original_sensors<=remaining and unchanged)
            report=dict(outcome='PASS' if completed and cleanup else 'NOT_COMPLETE',
                elapsedSeconds=time.monotonic()-started,phases=self.rows,ownSensorsRemoved=cleanup,
                worldSettingsUnchanged=unchanged,cleanupErrors=cleanup_errors,
                profile=dict(name=self.profile,fov=50,sensorTick=.1,jpegQuality=85,
                             warmupSeconds=self.warmup,observationSeconds=self.seconds),
                sensorAttributes=getattr(self,'attributes',{}),samples=self.samples,
                gpuUtilization='NOT_MEASURED',performanceQualification='CHARACTERIZATION_ONLY',
                comparability=('Stationary same selected ego/view; dynamic town and warm-up can still vary' if self.profile.endswith('-static')
                               else 'Continuous Autopilot route, not identical-frame scene replay'),
                carlaRebuilt=False,factoryRebuilt=False,aiInference='NOT_RUN',vmDelivery='NOT_RUN')
            (self.output/'camera-report.json').write_text(json.dumps(report,indent=2)+'\n')
        require(cleanup,'CAMERA_CLEANUP_UNCONFIRMED')
        return report
