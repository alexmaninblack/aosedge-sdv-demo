#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Scenario-owned same-Vision-VM checks; never operate retained Main instances."""
import argparse
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import sys
import time

UNIT='af6d074a-6ce1-49ba-b613-0476e7b6d1b5'
VM='89273f16-4be0-4b22-b4cb-58d08533c8bc'
BOOTSTRAP='e10d77b648b664a8ae5cbe895c428d0ee37578f516c0a62b467161e055118a1c'


def require(ok,code):
    if not ok:raise ValueError(code)


def native_profile_valid(facts):
    # A shared Source projection helper is not VDP installation. Check the
    # actual VDP executable/projection and resource selection instead.
    return facts['cpuCount']==4 and facts['selinux']=='Enforcing' and not facts['mainServicesPresent']


def atomic(path,value):
    pending=path.with_suffix('.pending');pending.write_text(json.dumps(value,indent=2)+'\n');pending.chmod(0o600);pending.replace(path)


def worker(context):
    c=json.loads(context.read_bytes());records=context.parent;started=time.monotonic();vm=None;native=None;retained={}
    result=dict(scenario='VISION_SERVICES_SAME_VM_NATIVE_INVENTORY',outcome='NOT_COMPLETE',phases=[],cleanup={},
        servicesDeployed=False,modelExecution='NOT_RUN',cloudMutation=False,carlaRebuilt=False,mainFactoryRebuilt=False)
    def phase(name,action):
        print(json.dumps(dict(stage=name,state='STARTED')),flush=True);began=time.monotonic();value=action()
        atomic(records/(name+'.json'),dict(seconds=round(time.monotonic()-began,2),facts=value));result['phases'].append(dict(stage=name,seconds=round(time.monotonic()-began,2)))
        atomic(records/'progress.json',result);print(json.dumps(dict(stage=name,state='COMPLETE')),flush=True);return value
    try:
        require(hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==c['workerSha256'],'WORKER_CHANGED')
        package=Path(c['packageRoot']);bundle=Path(c['bundle'])
        require(subprocess.check_output(['/usr/sbin/sysctl','-n','hw.model'],text=True).strip()=='Mac16,8','M4_REQUIRED')
        require(hashlib.sha256((package/'application-manifest.json').read_bytes()).hexdigest()==c['baseManifest'],'BASE_CHANGED')
        subprocess.run(['codesign','--verify','--deep','--strict','-R',
            '=identifier "org.aosedge.sdvlab.vision.bootstrap" and anchor apple generic and certificate leaf[subject.OU] = "3NF57VKB3V"',str(bundle)],check=True,capture_output=True,timeout=120)
        sys.path.insert(0,str(package/'aosedge-sdv-demo/apps/demo-orchestrator/src'))
        import aosedge_demo_orchestrator
        from aosedge_demo_orchestrator import runtime_paths
        aosedge_demo_orchestrator.__path__.insert(0,str(bundle/'Contents/Resources/tooling/aosedge-sdv-demo/apps/demo-orchestrator/src/aosedge_demo_orchestrator'))
        from aosedge_demo_orchestrator import vision_bootstrap as v
        from aosedge_demo_orchestrator.environment import EnvironmentService,JOURNAL
        from aosedge_demo_orchestrator.vm import VMService,access_path
        from aosedge_demo_orchestrator.guest_access import ssh_command
        expected_bootstrap=c.get('bootstrapManifest',BOOTSTRAP)
        require(expected_bootstrap in (BOOTSTRAP,'c4694c1b440bb036b3df63a1b0adc573724d9371e11f98abb596d005ecc84ea9'),'VISION_BOOTSTRAP_SELECTION_INVALID')
        bootstrap=v.verify(bundle,c['baseManifest']);require(bootstrap.manifest_sha256==expected_bootstrap,'VISION_BOOTSTRAP_CHANGED')
        native=Path.home()/v.INSTANCE_NAME;retained={Path.home()/n:(Path.home()/n/JOURNAL).read_bytes() for n in v.RETAINED_INSTANCE_NAMES}
        before=json.loads((native/JOURNAL).read_bytes());item=before['vehicles']['test']
        require(item['unitId']==UNIT and item['localVmId']==VM and item['runtime']['state']==before['source']['state']=='STOPPED'
            and not before['source'].get('operation'),'SAME_IDLE_VISION_REQUIRED')
        with runtime_paths.installed_session(native):
            vm=VMService(EnvironmentService(catalog=v.SignedVisionCatalog(bootstrap),vm_profile=v.VM_PROFILE))
            def start():
                value=vm.execute('start','test',timeout=150);require(value['vehicles']['test']['state']=='COMPLETED','VM_START_UNCONFIRMED');return dict(started=True,sameVm=True)
            phase('normal-same-vm-start',start)
            def inventory():
                code='''import json,pathlib,subprocess,os
assert pathlib.Path('/etc/machine-id').read_text().strip()=='89273f164be04b22b4cb58d08533c8bc'
def numeric(value):
 out={}
 if isinstance(value,dict):
  for k,v in value.items():
   if 'dmips' in k.lower() and type(v) in (int,float):out[k]=v
   nested=numeric(v)
   if nested:out[k]=nested
 elif isinstance(value,list):
  for i,v in enumerate(value):
   nested=numeric(v)
   if nested:out[str(i)]=nested
 return out
dmips={}
for path in pathlib.Path('/etc/aos').glob('*.cfg'):
 if path.stat().st_size<1024**2:
  try:
   fields=numeric(json.loads(path.read_bytes()))
   if fields:dmips[path.name]=fields
  except (ValueError,UnicodeError):pass
resources=json.loads(pathlib.Path('/etc/aos/resources.cfg').read_bytes())
native=[]
for proc in pathlib.Path('/proc').iterdir():
 if not proc.name.isdigit():continue
 try:
  if (proc/'comm').read_text().strip()!='vision-camera-probe'[:15]:continue
  values=dict(row.split(':',1) for row in (proc/'status').read_text().splitlines() if ':' in row)
  if list(map(int,values['Uid'].split()))!=[5000]*4:continue
  groups=(proc/'cgroup').read_text().splitlines();unified=[row[3:] for row in groups if row.startswith('0::')]
  if len(unified)!=1:continue
  group=pathlib.Path('/sys/fs/cgroup'+unified[0]);cpu=(group/'cpu.max').read_text().split()
  native.append(dict(uid=5000,cpuMax=list(map(int,cpu)) if cpu[0]!='max' else cpu,memoryMax=(group/'memory.max').read_text().strip()))
 except (FileNotFoundError,ProcessLookupError):continue
print(json.dumps(dict(cpuCount=os.cpu_count(),memTotalKiB=int(next(v.split()[1] for v in pathlib.Path('/proc/meminfo').read_text().splitlines() if v.startswith('MemTotal:'))),
 pythonVersion=list(__import__('sys').version_info[:3]),selinux=subprocess.check_output(['getenforce'],text=True).strip(),
 nativeResourceNames=[r['name'] for r in resources],nodeDmipsConfiguration=dmips,nativeDiagnosticQuotas=native,rootfsVersion=pathlib.Path('/etc/aos/version').read_text().strip(),
 sharedSourceHelperPresent=pathlib.Path('/usr/libexec/aos-demo-service-inputs.py').exists(),
 mainServicesPresent=any(pathlib.Path(p).exists() for p in ('/usr/libexec/aos-vehicle-data-provider-launcher','/etc/systemd/system/aos-sm.service.d/40-aos-demo-service-inputs.conf')))))
'''
                active=json.loads((native/JOURNAL).read_bytes())['vehicles']['test']
                command=ssh_command(access_path(native,'test'),active['sshPort'],8)
                done=subprocess.run(command,input="python3 -I -B - <<'VISION_INVENTORY'\n"+code+"\nVISION_INVENTORY\n",capture_output=True,text=True,timeout=35)
                require(done.returncode==0,'GUEST_INVENTORY_FAILED');facts=json.loads(done.stdout)
                atomic(records/'native-capacity-observed.json',facts)
                require(native_profile_valid(facts),'PRESERVED_VISION_PROFILE_CHANGED');return facts
            phase('native-capacity-and-profile',inventory);result['outcome']='PASS_SAME_VM_NATIVE_INVENTORY_ONLY'
            if c.get('nativePrimitives'):
                def native_primitives():
                    proof=c['nativePrimitives'];base=Path('/run/aos-vision-services-input-01')
                    for name,pin in proof['files'].items():require(hashlib.sha256((records/name).read_bytes()).hexdigest()==pin,'VISION_PRIMITIVE_INPUT_CHANGED')
                    current=json.loads((native/JOURNAL).read_bytes())['vehicles']['test'];command=ssh_command(access_path(native,'test'),current['sshPort'],8)
                    prepare=subprocess.run(command,input='test ! -e '+shlex.quote(str(base))+'\nmkdir -m 755 '+shlex.quote(str(base))+'\n',capture_output=True,text=True,timeout=10)
                    require(prepare.returncode==0,'VISION_PRIMITIVE_STAGING_CONFLICT')
                    options=command[1:-3];options.remove('-T');options[options.index('-p')]='-P'
                    delivered=subprocess.run(['/usr/bin/scp','-O',*options,*[str(records/name) for name in proof['files']],'root@127.0.0.1:'+str(base)+'/'],capture_output=True,text=True,timeout=30)
                    require(delivered.returncode==0,'VISION_PRIMITIVE_STAGING_FAILED')
                    code='import pathlib,hashlib,json,shutil\nbase=pathlib.Path('+repr(str(base))+')\nfiles='+repr(proof['files'])+'\n'
                    code+='assert all(not (base/name).is_symlink() and hashlib.sha256((base/name).read_bytes()).hexdigest()==pin for name,pin in files.items())\n'
                    code+='ns={};exec((base/"vision_services_primitives_guest.py").read_text(),ns)\nresult=ns["run"](base)\n'
                    code+='if result["outcome"].startswith("PASS_"):shutil.rmtree(base);result["cleanup"]["stagedInputsRemoved"]=True\nprint(json.dumps(result))\n'
                    observed=subprocess.run(command,input="python3 -I -B - <<'VISION_NATIVE_PRIMITIVES'\n"+code+"\nVISION_NATIVE_PRIMITIVES\n",capture_output=True,text=True,timeout=280)
                    require(observed.returncode==0 and len(observed.stdout)<262144,'VISION_PRIMITIVE_OBSERVER_FAILED')
                    value=json.loads(observed.stdout);atomic(records/'native-primitives-observed.json',value)
                    require(value['outcome']=='PASS_REVERSIBLE_NATIVE_PRIMITIVES_PREPARATION',value.get('code',value.get('cleanupCode','VISION_PRIMITIVES_UNCONFIRMED')))
                    require(all(value['cleanup'].values()),'VISION_PRIMITIVE_RESTORATION_UNCONFIRMED');return value
                phase('reversible-native-exchange-primitives',native_primitives);result['outcome']='PASS_NATIVE_EXCHANGE_PRIMITIVES_AND_STOCK_RESTORATION'
            if c.get('nativeExchangePreflight'):
                def exchange_preflight():
                    code='''import json,pathlib,shutil,pwd,grp,subprocess
assert pathlib.Path('/etc/machine-id').read_text().strip()=='89273f164be04b22b4cb58d08533c8bc'
paths=('/run','/var/aos/workdirs','/var/aos/storages','/var/aos/states','/var/aos/images','/var/aos')
storage={}
for name in paths:
 p=pathlib.Path(name)
 if p.exists():
  d=shutil.disk_usage(p);storage[name]=dict(bytes=d.total,free=d.free,used=d.used,device=p.stat().st_dev)
resource=json.loads(pathlib.Path('/etc/aos/resources.cfg').read_bytes())
names=('aos-vision-exchange','aos-vision-perception-publish','aos-vision-perception-read','aos-vision-context-read','aos-vision-assessment-publish')
groups={name:bool([g for g in grp.getgrall() if g.gr_name==name]) for name in names}
configs={}
for name in ('sm','cm'):
 value=json.loads((pathlib.Path('/etc/aos')/(name+'.cfg')).read_bytes())
 configs[name]=dict(fields=sorted(value),paths={k:v for k,v in value.items() if type(v) is str and v.startswith('/var/aos/')})
measurement=pathlib.Path('/var/aos/workdirs/vision-services-measure-inputs')
ownedInputs=[dict(name=p.name,bytes=p.stat().st_size) for p in sorted(measurement.iterdir()) if p.is_file() and not p.is_symlink()] if measurement.is_dir() else []
for config in configs.values():
 for path in config['paths'].values():
  p=pathlib.Path(path)
  if p.exists():
   d=shutil.disk_usage(p);storage[path]=dict(bytes=d.total,free=d.free,used=d.used,device=p.stat().st_dev)
print(json.dumps(dict(storage=storage,resourceNames=[r['name'] for r in resource],exchangeGroupsPresent=groups,
 exchangeUserPresent=any(u.pw_name=='aos-vision-exchange' for u in pwd.getpwall()),
 nativeStorageConfiguration=configs,ownedMeasurementInputs=ownedInputs,
 stockPolicyBytes=pathlib.Path('/sys/fs/selinux/policy').stat().st_size,
 stoppedProofPathsAbsent=all(not pathlib.Path(p).exists() for p in ('/run/aos-vision-services-proof','/run/vision-camera-store-proof')),
 rootfsWritable=False,selinux=subprocess.check_output(['getenforce'],text=True).strip())))
'''
                    current=json.loads((native/JOURNAL).read_bytes())['vehicles']['test'];command=ssh_command(access_path(native,'test'),current['sshPort'],8)
                    observed=subprocess.run(command,input="python3 -I -B - <<'VISION_EXCHANGE_PREFLIGHT'\n"+code+"\nVISION_EXCHANGE_PREFLIGHT\n",capture_output=True,text=True,timeout=25)
                    require(observed.returncode==0 and len(observed.stdout)<16384,'VISION_EXCHANGE_PREFLIGHT_FAILED');facts=json.loads(observed.stdout)
                    require(facts['resourceNames']==['vision-camera-read'] and not any(facts['exchangeGroupsPresent'].values())
                        and facts['exchangeUserPresent'] is False and facts['stoppedProofPathsAbsent'] and facts['selinux']=='Enforcing','VISION_EXCHANGE_BASELINE_CHANGED')
                    return facts
                phase('native-exchange-storage-preflight',exchange_preflight);result['outcome']='PASS_READ_ONLY_NATIVE_EXCHANGE_PREFLIGHT'
            if c.get('cpuTopologyProof'):
                def prove_cpu_topology():
                    proof=c['cpuTopologyProof']
                    for name,pin in proof['files'].items():require(hashlib.sha256((records/name).read_bytes()).hexdigest()==pin,'CPU_TOPOLOGY_PROOF_SOURCE_CHANGED')
                    current=json.loads((native/JOURNAL).read_bytes())['vehicles']['test']
                    command=ssh_command(access_path(native,'test'),current['sshPort'],8)
                    source_text=(records/'vision_cpuinfo_projection.py').read_text()
                    code='import json\nprojection={};exec('+repr(source_text)+',projection)\nprojection["__proofSource"]='+repr(source_text)+'\n'
                    code+='proof={};exec('+repr((records/'vision_services_cpu_guest.py').read_text())+',proof)\nprint(json.dumps(proof["run"](projection,canonical='+repr(proof.get('canonical',False))+',writer='+repr(proof.get('writer',False))+')))\n'
                    observed=subprocess.run(command,input="python3 -I -B - <<'VISION_CPU_PROOF'\n"+code+"\nVISION_CPU_PROOF\n",capture_output=True,text=True,timeout=150)
                    if observed.returncode:
                        # The wrapper contains no request secrets/config text.
                        atomic(records/'cpu-proof-command-diagnostics.json',dict(exit=observed.returncode,stdout=observed.stdout[-8192:],stderr=observed.stderr[-8192:]))
                    require(observed.returncode==0 and len(observed.stdout)<65536,'CPU_TOPOLOGY_PROOF_OBSERVER_FAILED')
                    value=json.loads(observed.stdout);atomic(records/'cpu-topology-observed.json',value)
                    require(value['outcome']=='PASS_TRANSIENT_FOUR_CPU_NATIVE_QUOTA_MAPPING',value.get('code','CPU_TOPOLOGY_NOT_CONFIRMED'))
                    require(value['cleanup'] and all(value['cleanup'].values()),'CPU_TOPOLOGY_RESTORATION_NOT_CONFIRMED');return value
                result['cloudMutation']='NATIVE_CAPACITY_REPORT_ONLY'
                phase('native-cpu-topology-projection',prove_cpu_topology);result['outcome']='PASS_NATIVE_QUOTA_MAPPING_AND_STOCK_RESTORATION'
            if c.get('diagnoseMeasurement'):
                def diagnose():
                    current=json.loads((native/JOURNAL).read_bytes())['vehicles']['test']
                    command=ssh_command(access_path(native,'test'),current['sshPort'],8)
                    code='''import hashlib,json,pathlib,shutil,subprocess
base=pathlib.Path('/var/aos/workdirs/vision-services-measure-inputs')
info=dict(machineMatches=pathlib.Path('/etc/machine-id').read_text().strip()=='89273f164be04b22b4cb58d08533c8bc',baseExists=base.is_dir(),baseSymlink=base.is_symlink(),freeBytes=shutil.disk_usage(base).free,files={},units={})
for name in ('runtime_measurement.py','vision_services_measure_guest.py','perception-rootfs.tar.gz','assessment-rootfs.tar.gz','perception-closure.json','assessment-closure.json'):
 path=base/name;info['files'][name]=dict(exists=path.is_file(),bytes=path.stat().st_size if path.exists() else None)
for role in ('perception','assessment'):
 info['units'][role]=subprocess.run(['systemctl','show','aos-vision-closure-measure-'+role,'--property=LoadState,ActiveState,Result,ExecMainStatus,MemoryPeak,CPUUsageNSec'],capture_output=True,text=True,timeout=5).stdout
info['scratchChildren']=len(list((base/'.tmp').iterdir())) if (base/'.tmp').is_dir() else None
print(json.dumps(info))
'''
                    observed=subprocess.run(command,input="python3 -I -B - <<'VISION_DIAGNOSE'\n"+code+"\nVISION_DIAGNOSE\n",capture_output=True,text=True,timeout=25)
                    require(observed.returncode==0 and len(observed.stdout)<16384,'MEASUREMENT_DIAGNOSIS_FAILED');return json.loads(observed.stdout)
                phase('read-only-measurement-diagnosis',diagnose);result['outcome']='PASS_READ_ONLY_MEASUREMENT_DIAGNOSIS'
            if c.get('measurements'):
                def measure():
                    files=c['measurements']['files']
                    base=Path('/run/aos-vision-services-measure/inputs-06') if c['measurements'].get('inputProfile')=='tmpfs-current-06' else Path('/var/aos/workdirs/vision-services-measure-inputs')
                    current=json.loads((native/JOURNAL).read_bytes())['vehicles']['test']
                    command=ssh_command(access_path(native,'test'),current['sshPort'],8)
                    for name,pin in files.items():
                        origin=records.parent/'vision-services-closure-01' if c['measurements'].get('reuseGuestInputs') and name.endswith('.tar.gz') else records
                        require(hashlib.sha256((origin/name).read_bytes()).hexdigest()==pin,'MEASUREMENT_STAGED_INPUT_CHANGED')
                    if not c['measurements'].get('reuseGuestInputs'):
                        if c['measurements'].get('inputProfile')=='tmpfs-current-06':
                            prefix="python3 -I -B - <<'MEASUREMENT_PARENT'\nimport pathlib,stat\np=pathlib.Path('/run/aos-vision-services-measure')\nif not p.exists():p.mkdir(mode=0o755)\ns=p.lstat();assert stat.S_ISDIR(s.st_mode) and s.st_uid==0 and not s.st_mode&0o022\nMEASUREMENT_PARENT\n"
                            parent=subprocess.run(command,input=prefix,capture_output=True,text=True,timeout=10)
                            require(parent.returncode==0,'MEASUREMENT_TMPFS_PARENT_INVALID')
                        prepared=subprocess.run(command,input='set -eu\numask 022\ntest ! -e '+shlex.quote(str(base))+'\nmkdir -m 755 '+shlex.quote(str(base))+'\n',capture_output=True,text=True,timeout=15)
                        require(prepared.returncode==0,'MEASUREMENT_INPUT_OWNER_CONFLICT')
                        options=command[1:-3];options.remove('-T');options[options.index('-p')]='-P'
                        delivered=subprocess.run(['/usr/bin/scp','-O',*options,*[str(records/name) for name in files],'root@127.0.0.1:'+str(base)+'/'],capture_output=True,text=True,timeout=60)
                        require(delivered.returncode==0,'MEASUREMENT_GUEST_TRANSFER_FAILED')
                    request=c['measurements']['request']
                    # Preserve previous harness source. Only a new digest-named
                    # measurement probe is delivered; cached models are reused.
                    probe=base/('runtime_measurement-'+request['probeSha256'][:16]+'.py')
                    checked=subprocess.run(command,input='test ! -e '+shlex.quote(str(probe))+'\n',capture_output=True,text=True,timeout=10)
                    require(checked.returncode==0,'MEASUREMENT_PROBE_EXISTS_RECONCILE')
                    options=command[1:-3];options.remove('-T');options[options.index('-p')]='-P'
                    delivered=subprocess.run(['/usr/bin/scp','-O',*options,str(records/'runtime_measurement.py'),'root@127.0.0.1:'+str(probe)],capture_output=True,text=True,timeout=15)
                    require(delivered.returncode==0,'MEASUREMENT_PROBE_TRANSFER_FAILED')
                    code='import json,pathlib\nns={};exec('+repr((records/'vision_services_measure_guest.py').read_text())+',ns)\nns["BASE"]=pathlib.Path('+repr(str(base))+')\nprint(json.dumps(ns["run"]('+repr(request)+')))\n'
                    observed=subprocess.run(command,input="python3 -I -B - <<'VISION_MEASURE'\n"+code+"\nVISION_MEASURE\n",capture_output=True,text=True,timeout=195)
                    if observed.returncode:
                        atomic(records/'measurement-command-diagnostics.json',dict(exit=observed.returncode,stdout=observed.stdout[-8192:],stderr=observed.stderr[-8192:]))
                    require(observed.returncode==0 and len(observed.stdout)<262144,'MEASUREMENT_GUEST_OBSERVER_FAILED')
                    value=json.loads(observed.stdout);atomic(records/'closure-measurements-observed.json',value)
                    require(value['outcome']=='PASS_ISOLATED_ARM64_CLOSURE_MEASUREMENTS',value.get('code','MEASUREMENT_UNCONFIRMED'))
                    require(all(value['cleanup'].values()),'MEASUREMENT_CLEANUP_UNCONFIRMED');return value
                result['modelExecution']='ATTEMPTED_UNCONFIRMED'
                phase('isolated-closure-characterization',measure);result.update(outcome='PASS_SAME_VM_ISOLATED_CLOSURE_MEASUREMENTS',modelExecution='PASS_SYNTHETIC_CLOSURE_ONLY',nativeAos='NOT_RUN',liveCamera='NOT_RUN')
    except Exception as error:
        result['outcome']='NOT_COMPLETE';result['code']=str(error) if str(error).isupper() else type(error).__name__
    finally:
        if vm is not None and native is not None:
            try:
                from aosedge_demo_orchestrator import runtime_paths
                with runtime_paths.installed_session(native):
                    value=vm.execute('stop','test',timeout=150);result['cleanup']['vmStopped']=value['vehicles']['test']['state']=='COMPLETED' and vm.observe_readiness('test')['reason']=='VM_NOT_RUNNING'
                state=json.loads((native/'.run/demo-current/journal.json').read_bytes());item=state['vehicles']['test']
                result['cleanup'].update(sameVmAndUnit=item['unitId']==UNIT and item['localVmId']==VM,sourceStopped=state['source']['state']=='STOPPED',
                    retainedJournalsUnchanged=all((p/'.run/demo-current/journal.json').read_bytes()==raw for p,raw in retained.items()))
            except Exception:result['cleanup']['vmStopped']=False
        result['seconds']=round(time.monotonic()-started,2);atomic(records/'result.json',result);print(json.dumps(result),flush=True)
    return 0 if result['outcome'].startswith('PASS_') and 'code' not in result and result['cleanup'] and all(result['cleanup'].values()) else 1


def main():
    p=argparse.ArgumentParser();p.add_argument('--config',type=Path);p.add_argument('--worker',type=Path);group=p.add_mutually_exclusive_group();group.add_argument('--measure-closures',action='store_true');group.add_argument('--diagnose-measurement',action='store_true');group.add_argument('--prove-cpu-info',nargs='?',const=1,type=int,choices=(1,2,3,4));group.add_argument('--resume-measurement',nargs='?',const=2,type=int,choices=(2,3,4,5,6));group.add_argument('--exchange-preflight',nargs='?',const=1,type=int,choices=(1,2));group.add_argument('--exchange-primitives',action='store_true');a=p.parse_args()
    if a.worker:return worker(a.worker)
    require(a.config is not None,'PRIVATE_CONFIG_REQUIRED')
    import remote_harness as h
    from vision_vm_campaign import configuration
    c=configuration(a.config);t=c['transport'];q=shlex.quote;name='vision-services-cpu-'+str(a.prove_cpu_info).zfill(2) if a.prove_cpu_info else ('vision-services-closure-'+str(a.resume_measurement).zfill(2) if a.resume_measurement else ('vision-services-closure-diagnosis-01' if a.diagnose_measurement else ('vision-services-closure-01' if a.measure_closures else 'vision-services-native-01')))
    if a.exchange_preflight:name='vision-services-exchange-preflight-'+str(a.exchange_preflight).zfill(2)
    if a.exchange_primitives:name='vision-services-exchange-primitives-01'
    records=Path(c['records'])/name;remote=Path(c['remoteRoot'])/name
    require(not records.exists(),'ATTEMPT_EXISTS_RECONCILE');records.mkdir(mode=0o700)
    source=Path(__file__).resolve();context=dict(packageRoot=c['main']['packageRoot'],baseManifest=c['main']['manifestSha256'],
        bundle=str(Path(c['remoteRoot'])/'vision-fresh-accept-11/AosEdge Vision Bootstrap 0.5.0.bundle'),workerSha256=h.digest(source))
    inputs=[];extra_files=[]
    if a.exchange_preflight or a.exchange_primitives:
        delivered=json.loads((Path(c['records'])/'vision-services-host-01/result.json').read_bytes())
        require(delivered['outcome']=='PASS_SIGNED_VISION_HOST_DELIVERY' and delivered['retainedJournalsUnchanged'],'VISION_HOST_DELIVERY_PROOF_REQUIRED')
        context.update(bundle=delivered['bundle'],bootstrapManifest=delivered['manifestSha256'],nativeExchangePreflight=bool(a.exchange_preflight))
    if a.exchange_primitives:
        import runpy,tarfile,io
        platform=Path(__file__).resolve().parents[3]/'vision-camera-platform';build=Path('/Volumes/SDV-Dev/sdv/build/vision-services/exchange-primitives-01')
        primitive=json.loads((build/'result.json').read_bytes());require(primitive['outcome']=='PASS_VISION_EXCHANGE_TARGETED_PRIMITIVES' and primitive['builderStopped'],'VISION_PRIMITIVE_COMPILE_REQUIRED')
        for name in ('aos-vision-exchange-proof','vision_exchange.pp'):
            require(h.digest(build/name)==primitive['files'][name]['sha256'],'VISION_PRIMITIVE_COMPILE_CHANGED')
        payload=runpy.run_path(str(platform/'tools/build_camera_access_payload.py'))['payload']('0.1.2')
        with tarfile.open(fileobj=io.BytesIO(payload)) as archive:raw=archive.extractfile('bin/camera-access').read()
        zipfile=records/'camera-access';zipfile.write_bytes(raw);zipfile.chmod(0o555)
        extra_files=[Path(__file__).with_name('vision_services_primitives_guest.py'),platform/'tools/vision_cpuinfo_projection.py',
            platform/'tests/fixtures/vision-native-exchange/aos-vision-exchange.service',build/'aos-vision-exchange-proof',build/'vision_exchange.pp',
            Path('/Volumes/SDV-Dev/sdv/build/vision-bootstrap/0.1.0/evidence/camera-store-policy-loader-01/vision-policy-load')]
        context['nativePrimitives']=dict(files={path.name:h.digest(path) for path in [*extra_files,zipfile]})
        extra_files.append(zipfile)
    if a.prove_cpu_info:
        prior=json.loads((Path(c['records'])/'vision-services-closure-06/result.json').read_bytes())
        capacity=json.loads((Path(c['records'])/'vision-services-cloud-preflight-02/result.json').read_bytes())
        source_capacity=json.loads(Path('/Volumes/SDV-Dev/sdv/build/vision-services/capacity-source-02/result.json').read_bytes())
        require(prior['outcome']=='PASS_SAME_VM_ISOLATED_CLOSURE_MEASUREMENTS' and all(prior['cleanup'].values())
            and capacity['outcome']=='PASS_READ_ONLY_VISION_CLOUD_PREFLIGHT' and capacity['journalsUnchanged']
            and source_capacity['outcome']=='PASS_READ_ONLY_PINNED_QUOTA_SOURCE' and source_capacity['builderStopped'],'CPU_PROOF_MEASUREMENT_AND_SOURCE_GATES_REQUIRED')
        extra_files=[Path(__file__).with_name('vision_services_cpu_guest.py'),Path(__file__).resolve().parents[3]/'vision-camera-platform/tools/vision_cpuinfo_projection.py']
        context['cpuTopologyProof']=dict(files={path.name:h.digest(path) for path in extra_files},canonical=a.prove_cpu_info in (2,3),writer=a.prove_cpu_info==4)
        if a.prove_cpu_info>=2:
            prior_cpu=json.loads((Path(c['records'])/'vision-services-cpu-01/result.json').read_bytes())
            require(prior_cpu['outcome']=='PASS_NATIVE_QUOTA_MAPPING_AND_STOCK_RESTORATION' and all(prior_cpu['cleanup'].values()),'CPU_PROOF_TRANSIENT_MAPPING_REQUIRED')
        if a.prove_cpu_info==3:
            prior_cpu=json.loads((Path(c['records'])/'vision-services-cpu-02/result.json').read_bytes())
            diagnostic=json.loads((Path(c['records'])/'vision-services-cpu-02/cpu-proof-command-diagnostics.json').read_bytes())
            require(prior_cpu['code']=='CPU_TOPOLOGY_PROOF_OBSERVER_FAILED' and all(prior_cpu['cleanup'].values())
                and 'CPU_PROOF_PROJECTION_NOT_IDEMPOTENT' in diagnostic['stderr'],'CPU_PROOF_CANONICAL_PACKAGE_ID_OBSERVER_FAULT_REQUIRED')
        if a.prove_cpu_info==4:
            prior_cpu=json.loads((Path(c['records'])/'vision-services-cpu-03/result.json').read_bytes())
            native_cpu=json.loads((Path(c['records'])/'vision-services-cpu-03/cpu-topology-observed.json').read_bytes())
            require(prior_cpu['code']=='CPU_PROOF_QUOTA_NOT_CONFIRMED' and all(prior_cpu['cleanup'].values()) and all(native_cpu['cleanup'].values())
                and native_cpu['restoredNativeQuota']==[10000,100000],'CPU_PROOF_SHORTENED_PROFILE_REJECTED_AND_RESTORED_REQUIRED')
    if a.diagnose_measurement:
        previous=json.loads((Path(c['records'])/'vision-services-closure-01/result.json').read_bytes())
        require(previous.get('code')=='MEASUREMENT_GUEST_OBSERVER_FAILED' and all(previous['cleanup'].values()),'MEASUREMENT_ATTEMPT_RECONCILE_REQUIRED')
        context['diagnoseMeasurement']=True
    if a.resume_measurement==2:
        prior=json.loads((Path(c['records'])/'vision-services-closure-diagnosis-01/result.json').read_bytes())
        observed=json.loads((Path(c['records'])/'vision-services-closure-diagnosis-01/read-only-measurement-diagnosis.json').read_bytes())['facts']
        require(prior['outcome']=='PASS_READ_ONLY_MEASUREMENT_DIAGNOSIS' and all(prior['cleanup'].values()) and observed['machineMatches']
            and 0<observed['freeBytes']<2*1024**3 and observed['scratchChildren'] is None
            and all('LoadState=not-found' in row for row in observed['units'].values()),'EXACT_PREEXEC_WORKDIRS_CAPACITY_FAULT_REQUIRED')
    if a.resume_measurement==3:
        previous=json.loads((Path(c['records'])/'vision-services-closure-02/result.json').read_bytes())
        observed=json.loads((Path(c['records'])/'vision-services-closure-02/closure-measurements-observed.json').read_bytes())
        require(previous['code']=='ISOLATED_CLOSURE_EXECUTION_FAILED' and all(previous['cleanup'].values()) and all(observed['cleanup'].values())
            and observed['roles']['perception']['stderr']=='Failed to start transient service unit: Connection reset by peer\n'
            and observed['roles']['perception']['stdout']=='','EXACT_TRANSIENT_START_TRANSPORT_FAULT_REQUIRED')
    if a.resume_measurement==4:
        previous=json.loads((Path(c['records'])/'vision-services-closure-03/result.json').read_bytes())
        observed=json.loads((Path(c['records'])/'vision-services-closure-03/closure-measurements-observed.json').read_bytes())
        require(previous['code']=='ISOLATED_CLOSURE_EXECUTION_FAILED' and all(previous['cleanup'].values()) and all(observed['cleanup'].values())
            and 'ExecMainStatus=217\n' in observed['roles']['perception']['unit'] and not observed['roles']['perception']['stdout']
            and not observed['roles']['perception']['scopedAvc'],'EXACT_MEASUREMENT_HOST_NSS_IDENTITY_FAULT_REQUIRED')
    if a.resume_measurement==5:
        previous=json.loads((Path(c['records'])/'vision-services-closure-04/result.json').read_bytes())
        observed=json.loads((Path(c['records'])/'vision-services-closure-04/closure-measurements-observed.json').read_bytes())
        require(previous['code']=='ISOLATED_CLOSURE_EXECUTION_FAILED' and all(previous['cleanup'].values()) and all(observed['cleanup'].values())
            and 'os.setresuid(5000,5000,5000)' in observed['roles']['perception']['stderr']
            and 'PermissionError: [Errno 1] Operation not permitted' in observed['roles']['perception']['stderr'],
            'EXACT_PREMODEL_CREDENTIAL_DROP_FAILURE_REQUIRED')
    if a.resume_measurement==6:
        previous=json.loads((Path(c['records'])/'vision-services-closure-05/result.json').read_bytes())
        observed=json.loads((Path(c['records'])/'vision-services-closure-05/closure-measurements-observed.json').read_bytes())
        native=json.loads(Path('/Volumes/SDV-Dev/sdv/build/vision-services/native-06/campaign.json').read_bytes())
        require(previous['code']=='ISOLATED_CLOSURE_EXECUTION_FAILED' and all(previous['cleanup'].values()) and all(observed['cleanup'].values())
            and 'outputs.autosteer' in observed['roles']['perception']['stderr'] and 'NUMBER_INVALID' in observed['roles']['perception']['stderr']
            and native['outcome']=='PASS_SSD_NATIVE_ASSESSMENT' and native['builderStopped']
            and 'RAW_AUTOSTEER_HEIGHT_MASK_IS_NOT_PROBABILITY' in native['build']['units']['cases'],'EXACT_RAW_AUTOSTEER_MASK_FAILURE_AND_TARGETED_FIX_REQUIRED')
    if a.measure_closures or a.resume_measurement:
        closure=Path('/Volumes/SDV-Dev/sdv/build/vision-services')/('closure-08' if a.resume_measurement==6 else 'closure-06')
        if a.resume_measurement==6:
            built=json.loads((closure/'campaign.json').read_bytes())
            require(built['outcome']=='MEASURED_ARM64_CLOSURES_NOT_DEPLOYED' and built['builderStopped'] and built['verifiedDeliveryComplete'] and 'code' not in built,'VERIFIED_CLOSURE_DELIVERY_REQUIRED')
            delivery=dict(transfers=built['closure']['artifacts'])
        else:
            delivery=json.loads((closure/'delivery.json').read_bytes());require(delivery['outcome']=='PASS_VERIFIED_CLOSURE_DELIVERY' and delivery['builderStopped'],'VERIFIED_CLOSURE_DELIVERY_REQUIRED')
        inputs=[Path(__file__).with_name('vision_services_measure_guest.py'),Path(__file__).resolve().parents[3]/'vision-pilot-services/tools/runtime_measurement.py']
        artifacts={}
        for role,pin in delivery['transfers'].items():
            archive=closure/(role+'-rootfs.tar.gz');require(archive.stat().st_size==pin['bytes'] and h.digest(archive)==pin['sha256'],'CLOSURE_LOCAL_INPUT_CHANGED')
            target=records/(role+'-closure.json');target.write_bytes((closure/role/'closure.json').read_bytes());target.chmod(0o600)
            inputs.extend([archive,target]);artifacts[role]=dict(bytes=pin['bytes'],sha256=pin['sha256'],manifestSha256=h.digest(target))
        context['measurements']=dict(files={path.name:h.digest(path) for path in inputs},request=dict(artifacts=artifacts,probeSha256=h.digest(inputs[1])),
            reuseGuestInputs=a.resume_measurement in (2,3,4,5),inputProfile='tmpfs-current-06' if a.resume_measurement==6 else 'retained-inputs-v1')
    atomic(records/'context.json',context);h.remote(t,'umask 077\nmkdir '+q(str(remote)),timeout=15)
    options=h.ssh_args(t)[1:-1];options.remove('-T');i=options.index('-b');options[i:i+2]=['-o','BindAddress='+options[i+1]]
    h.run(['/usr/bin/scp',*options,str(source),str(records/'context.json'),t['user']+'@'+t['host']+':'+str(remote)+'/'],timeout=20)
    if extra_files:h.run(['/usr/bin/scp',*options,*map(str,extra_files),t['user']+'@'+t['host']+':'+str(remote)+'/'],timeout=20)
    if inputs:
        transfer=[path for path in inputs if not context['measurements']['reuseGuestInputs'] or path.suffix!='gz']
        h.run(['/usr/bin/scp',*options,*map(str,transfer),t['user']+'@'+t['host']+':'+str(remote)+'/'],timeout=90)
    python=c['main']['packageRoot']+'/demo-artifacts/aosedge-sdv-demo/host-runtime/python/bin/python3.12'
    process=subprocess.Popen(h.ssh_args(t)+[q(python)+' -I -B '+q(str(remote/source.name))+' --worker '+q(str(remote/'context.json'))],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    with (records/'progress.jsonl').open('w') as log:
        for line in process.stdout:
            require(log.tell()<1024**2,'PROGRESS_LIMIT');log.write(line);log.flush();print(line.strip(),flush=True)
    stderr=process.stderr.read(8192);exit_code=process.wait(timeout=10)
    # Errors from owners are not copied raw: they can carry credential paths.
    observed=json.loads(h.remote(t,'/bin/cat '+q(str(remote/'result.json')),timeout=10));atomic(records/'result.json',observed)
    for phase in observed['phases']:
        filename=phase['stage']+'.json';raw=h.remote(t,'/bin/cat '+q(str(remote/filename)),timeout=10);atomic(records/filename,json.loads(raw))
    if a.measure_closures or a.resume_measurement:
        for name in ('closure-measurements-observed.json','native-capacity-observed.json','measurement-command-diagnostics.json'):
            raw=h.remote(t,'if test -f '+q(str(remote/name))+'; then /bin/cat '+q(str(remote/name))+'; else printf null; fi',timeout=10)
            if json.loads(raw) is not None:atomic(records/name,json.loads(raw))
    if a.prove_cpu_info:
        for name in ('cpu-topology-observed.json','cpu-proof-command-diagnostics.json'):
            raw=h.remote(t,'if test -f '+q(str(remote/name))+'; then /bin/cat '+q(str(remote/name))+'; else printf null; fi',timeout=10)
            if json.loads(raw) is not None:atomic(records/name,json.loads(raw))
    if a.exchange_primitives:
        raw=h.remote(t,'if test -f '+q(str(remote/'native-primitives-observed.json'))+'; then /bin/cat '+q(str(remote/'native-primitives-observed.json'))+'; else printf null; fi',timeout=10)
        if json.loads(raw) is not None:atomic(records/'native-primitives-observed.json',json.loads(raw))
    atomic(records/'transport.json',dict(exit=exit_code,stderrPresent=bool(stderr)))
    return exit_code


if __name__=='__main__':raise SystemExit(main())
