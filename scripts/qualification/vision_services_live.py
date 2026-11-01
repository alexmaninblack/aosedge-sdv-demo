#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Scenario-owned same-VM Source/exchange proof, not an engineering model worker."""
import argparse
import hashlib
import json
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
        require(not re.search('CGSSessionScreenIsLocked[^\r\n]{0,16}Yes',desktop),'M4_DESKTOP_LOCKED')
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
        bootstrap=v.verify(bundle,c['baseManifest']);require(bootstrap.manifest_sha256==MANIFEST,'VISION_LIVE_BOOTSTRAP_CHANGED')
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
            transfer=subprocess.run(['/usr/bin/scp','-O',*options,*[str(records/name) for name in c['files']],'root@127.0.0.1:'+str(base)+'/'],capture_output=True,text=True,timeout=30)
            require(transfer.returncode==0,'VISION_LIVE_INPUT_TRANSFER_FAILED')
            code='''import hashlib,json,pathlib,select,sys,time,traceback
base=pathlib.Path(BASE);pins=PINS
assert all(not (base/name).is_symlink() and hashlib.sha256((base/name).read_bytes()).hexdigest()==pin for name,pin in pins.items())
ns={};exec((base/'vision_services_primitives_guest.py').read_text(),ns);transaction=ns['Transaction'](base)
def emit(phase,data):print(json.dumps(dict(phase=phase,data=data)),flush=True)
try:
 emit('READY',transaction.open());deadline=time.monotonic()+900
 while time.monotonic()<deadline:
  if not select.select([sys.stdin],[],[],max(0,deadline-time.monotonic()))[0]:break
  operation=sys.stdin.readline(65).strip()
  if operation in ('','STOP'):break
  try:
   if operation=='OBSERVE':emit(operation,transaction.observe())
   elif operation=='DENY_ROOT':emit(operation,transaction.root_denial())
   elif operation=='RESTART':
    ns['call'](['systemctl','restart','aos-vision-exchange.service']);emit(operation,transaction.observe())
   else:raise ValueError('VISION_LIVE_GUEST_OPERATION_DENIED')
  except Exception as error:
   value=str(error);emit('ERROR',dict(code=value if value.isupper() and len(value)<160 else type(error).__name__))
except Exception as error:
 value=str(error);emit('ERROR',dict(code=value if value.isupper() and len(value)<160 else type(error).__name__,frames=[dict(file=pathlib.Path(f.filename).name,line=f.lineno) for f in traceback.extract_tb(error.__traceback__)[-3:]]))
finally:
 try:emit('CLOSED',transaction.close())
 except Exception as error:
  value=str(error);emit('CLEANUP_ERROR',dict(code=value if value.isupper() and len(value)<160 else type(error).__name__))
'''
            code=re.sub(r'\b(BASE|PINS)\b',lambda match:repr(str(base)) if match[0]=='BASE' else repr(c['files']),code)
            session=subprocess.Popen(command[:-2]+['python3 -I -B -c '+shlex.quote(code)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
            def read_responses():
                for row in session.stdout:lines.put(row)
                lines.put('')
            reader=threading.Thread(target=read_responses,daemon=True);reader.start()
            ready=receive(170);require(ready['phase']=='READY','VISION_LIVE_GUEST_NOT_READY');atomic(records/'native-primitives-ready.json',ready['data'])
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
    except Exception as error:
        result['code']=clean_error(error);result['errorFrames']=[dict(file=Path(f.filename).name,line=f.lineno) for f in traceback.extract_tb(error.__traceback__)[-4:]]
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
                        result['cleanup']['nativeConfigAndPolicyRestored']=session.returncode==0
                        if reader is not None:reader.join(timeout=2)
                    except Exception as error:result['cleanup']['nativeConfigAndPolicyRestored']=False;result['guestCleanupCode']=clean_error(error)
                try:result['cleanup']['vmStopped']=vm.execute('stop','test',timeout=150)['vehicles']['test']['state']=='COMPLETED'
                except Exception:result['cleanup']['vmStopped']=False
                state=json.loads((native/JOURNAL).read_bytes());result['cleanup'].update(sameVmAndUnit=state['vehicles']['test']['unitId']==UNIT and state['vehicles']['test']['localVmId']==VM,
                    retainedJournalsUnchanged=all((p/JOURNAL).read_bytes()==raw for p,raw in retained.items()))
        if awake is not None:awake.terminate();awake.wait(timeout=5);result['cleanup']['awakeHelperStopped']=True
        if not result['cleanup'] or not all(result['cleanup'].values()):result['outcome']='NOT_COMPLETE'
        result['seconds']=round(time.monotonic()-started,2);atomic(records/'result.json',result);print(json.dumps(result),flush=True)
    return 0 if result['outcome'].startswith('PASS_') and 'code' not in result else 1


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--worker',type=Path);parser.add_argument('--config',type=Path);parser.add_argument('--resume-nosuid-proof',action='store_true');parser.add_argument('--diagnose-peer-denial',action='store_true');a=parser.parse_args()
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
    delivered=json.loads((Path(c['records'])/'vision-services-host-01/result.json').read_bytes())
    source=Path(__file__).resolve();context=dict(packageRoot=c['main']['packageRoot'],baseManifest=c['main']['manifestSha256'],
        bundle=delivered['bundle'],workerSha256=h.digest(source),files={path.name:h.digest(path) for path in files})
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
