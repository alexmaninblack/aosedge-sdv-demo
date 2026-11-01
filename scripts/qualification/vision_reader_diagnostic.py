#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Synthetic IPC/ELF fault isolation only; never live-camera acceptance."""
import argparse
import ast
import base64
import json
from pathlib import Path
import shlex
import remote_harness as h
from vision_vm_campaign import configuration


def main():
    p=argparse.ArgumentParser();p.add_argument('--config',type=Path,required=True);p.add_argument('--attempt',type=int,choices=(1,2,3,4),default=1);a=p.parse_args();c=configuration(a.config)
    records=Path(c['records'])/('vision-reader-diagnostic-'+str(a.attempt).zfill(2));h.require(not records.exists(),'READER_DIAGNOSTIC_EXISTS');records.mkdir(mode=0o700)
    binary=Path('/Volumes/SDV-Dev/sdv/build/vision-ingress')/('fresh-reader-03' if a.attempt==4 else 'fresh-reader-02')/'vision-camera-probe-test'
    guest=r'''import pathlib,subprocess,hashlib,base64,json,sys,socket,time,struct,uuid,shutil,os,signal
root=pathlib.Path('/run/vision-reader-diagnostic');assert not root.exists();root.mkdir(mode=0o700)
raw=base64.b64decode(BINARY);assert hashlib.sha256(raw).hexdigest()==DIGEST
target=root/'probe-test';target.write_bytes(raw);target.chmod(0o555)
subprocess.run(['chcon','--reference=/bin/true',str(target)],check=True,capture_output=True)
result=dict(scenario='SYNTHETIC_IPC_DIAGNOSTIC_NOT_LIVE',cases=[])
def process():
 out=[]
 for p in pathlib.Path('/proc').iterdir():
  if not p.name.isdecimal():continue
  try:
   if (p/'comm').read_text().strip()=='vision-camera-p':out.append(dict(pid=int(p.name),limits=(p/'limits').read_text(),status=(p/'status').read_text()[:1800]))
  except OSError:pass
 return out
sys.path.insert(0,'/var/aos/workdirs/sm/runtimes/systemd-slot-camera-access/active/bin/camera-access')
from aos_camera_access import ipc
def call(value,data=b''):
 with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as stream:
  stream.settimeout(2);stream.connect('/run/aos-camera-access/oem/producer.sock');deadline=time.monotonic()+2
  ipc.write(stream,(ipc.header(value),data),deadline);return ipc.receive(stream,deadline)
epoch=call(dict(schemaVersion=1,operation='hello'))['componentEpoch']
try:
 test=subprocess.run([str(target)],capture_output=True,text=True,timeout=15)
 result['standaloneParser']=dict(exit=test.returncode,passed='NATIVE_CAMERA_PROBE_PARSER_PASS' in test.stdout,stderrPresent=bool(test.stderr))
 result['before']=process()
 if result['before']:
  native_root=pathlib.Path('/proc')/str(result['before'][0]['pid'])/'root'
  result['containerFiles']={s:(native_root/s).exists() for s in ('dev/null','dev/urandom','etc/ssl/openssl.cnf','usr/lib/ssl/openssl.cnf','proc/self/auxv')}
  result['bareFilesystemUnits']=[]
  for disable_config in (False,True):
   fd=os.open(target,os.O_RDONLY);out,writer=os.pipe();pid=os.fork()
   if pid==0:
    os.close(out);os.dup2(writer,1);os.dup2(writer,2);os.close(writer)
    os.chroot(native_root);os.chdir('/')
    environment={'PATH':'/usr/bin:/bin'}
    if disable_config:environment['OPENSSL_CONF']=''
    os.execve(fd,['native-parser-unit'],environment)
   os.close(fd);os.close(writer);deadline=time.monotonic()+10;status=None
   while time.monotonic()<deadline:
    observed,code=os.waitpid(pid,os.WNOHANG)
    if observed:status=code;break
    time.sleep(.05)
   if status is None:os.kill(pid,signal.SIGKILL);_,status=os.waitpid(pid,0)
   output=os.read(out,16384);os.close(out)
   result['bareFilesystemUnits'].append(dict(disableConfig=disable_config,exit=os.waitstatus_to_exitcode(status),passed=b'NATIVE_CAMERA_PROBE_PARSER_PASS' in output))
 for size in TESTSIZES:
  binding=dict(sourceId='00000000-0000-0000-0000-000000000003',sourceEpoch=str(uuid.uuid4()),cameraId='front',calibrationId=hashlib.sha256(b'SYNTHETIC_IPC_DIAGNOSTIC_NOT_LIVE').hexdigest())
  call(dict(schemaVersion=1,operation='select',componentEpoch=epoch,binding=binding))
  jpeg=b'\xff\xd8\xff\xc0'+struct.pack('!HBHHB',8,8,720,1280,3)+b'x'*size+b'\xff\xd9'
  for pair in range(8):
   for n in (0,1):
    frame=10+pair*2+n;stamp=frame*100000000
    metadata=dict(schemaVersion=1,profile='front-rgb-jpeg-720p-v1',**binding,frame=frame,simulationTimeNs=stamp,sensorSimulationTimeNs=stamp,
      clock='CARLA_WORLD_SNAPSHOT_FRAME_MATCH',encoding='JPEG',width=1280,height=720,payloadBytes=len(jpeg),sha256=hashlib.sha256(jpeg).hexdigest())
    call(dict(schemaVersion=1,operation='frame',componentEpoch=epoch,metadata=metadata),jpeg)
   time.sleep(.25)
  raw=subprocess.check_output(['journalctl','-b','-n','350','--no-pager','-o','cat'],text=True)
  messages=[]
  for line in raw.splitlines():
   at=line.find('{"probe":')
   if at>=0:
    try:messages.append(json.JSONDecoder().raw_decode(line[at:])[0])
    except ValueError:pass
  result['cases'].append(dict(jpegBytes=len(jpeg),processes=process(),messages=messages[-12:]))
finally:
 call(dict(schemaVersion=1,operation='disconnect',componentEpoch=epoch));shutil.rmtree(root)
 result['scratchRemoved']=not root.exists()
print(json.dumps(result))
'''.replace('BINARY',repr(base64.b64encode(binary.read_bytes()).decode())).replace('DIGEST',repr(h.digest(binary))).replace('TESTSIZES','()' if a.attempt==4 else '(0,512000)')
    ast.parse(guest)
    code=r'''import pathlib,subprocess,sys,json
main=MAIN;bundle=pathlib.Path(BUNDLE)
subprocess.run(['codesign','--verify','--deep','--strict',str(bundle)],check=True,capture_output=True)
sys.path.insert(0,main['packageRoot']+'/aosedge-sdv-demo/apps/demo-orchestrator/src')
import aosedge_demo_orchestrator
from aosedge_demo_orchestrator import runtime_paths
aosedge_demo_orchestrator.__path__.insert(0,str(bundle/'Contents/Resources/tooling/aosedge-sdv-demo/apps/demo-orchestrator/src/aosedge_demo_orchestrator'))
from aosedge_demo_orchestrator import vision_bootstrap as v
from aosedge_demo_orchestrator.environment import EnvironmentService,JOURNAL
from aosedge_demo_orchestrator.vm import VMService,access_path
from aosedge_demo_orchestrator.guest_access import ssh_command
from aosedge_demo_orchestrator.status import read_json
from aosedge_demo_orchestrator.units import UnitService
verified=v.verify(bundle,main['manifestSha256']);native=pathlib.Path.home()/v.INSTANCE_NAME
retained={pathlib.Path.home()/n:(pathlib.Path.home()/n/JOURNAL).read_bytes() for n in v.RETAINED_INSTANCE_NAMES};result={}
with runtime_paths.installed_session(native):
 env=EnvironmentService(catalog=v.SignedVisionCatalog(verified),vm_profile=v.VM_PROFILE);vm=VMService(env)
 try:
  assert read_json(native/JOURNAL)['source']['state']=='STOPPED'
  result['start']=vm.execute('start','test',timeout=150);assert result['start']['vehicles']['test']['state']=='COMPLETED'
  state=read_json(native/JOURNAL);item=state['vehicles']['test']
  done=subprocess.run(ssh_command(access_path(native,'test'),item['sshPort'],5),input="python3 - <<'DIAG'\n"+GUEST+"\nDIAG\n",capture_output=True,text=True,timeout=60)
  if done.returncode or len(done.stdout)>131072:
   import re
   result['probeError']=dict(exit=done.returncode,errorTypes=re.findall(r'^([A-Za-z]+Error):',done.stderr,re.M),lines=re.findall(r'File "<stdin>", line (\d+)',done.stderr))
  else:result['diagnostic']=json.loads(done.stdout)
  result['cloudServices']=UnitService(vm).observe('cloud-status','test').get('services')
 finally:
  stopped=vm.execute('stop','test',timeout=150)
  result['cleanup']=dict(vmStopped=stopped['vehicles']['test']['state']=='COMPLETED',retainedJournalsUnchanged=all((p/JOURNAL).read_bytes()==raw for p,raw in retained.items()))
print(json.dumps(result))
'''.replace('MAIN',repr(c['main'])).replace('BUNDLE',repr(str(Path(c['remoteRoot'])/'vision-fresh-accept-07/AosEdge Vision Bootstrap 0.5.0.bundle'))).replace('GUEST',repr(guest))
    ast.parse(code)
    python=c['main']['packageRoot']+'/demo-artifacts/aosedge-sdv-demo/host-runtime/python/bin/python3.12'
    value=json.loads(h.remote(c['transport'],shlex.quote(python)+" -I -B <<'M4_READER_DIAG'\n"+code+"\nM4_READER_DIAG\n",timeout=240))
    h.atomic(records/'result.json',value);print(json.dumps(value,indent=2))


if __name__=='__main__':main()
