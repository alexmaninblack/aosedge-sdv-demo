#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""One scoped Vision VM native-prerequisite inventory, with mandatory shutdown."""
import argparse
import hashlib
import json
from pathlib import Path
import shlex
import sys

import remote_harness as h
from vision_vm_campaign import configuration, SOURCE


GUEST = r'''
import ctypes.util,json,os,pathlib,pwd,grp,subprocess
def run(args):
 try:
  p=subprocess.run(args,capture_output=True,text=True,timeout=8)
  return p.returncode,p.stdout.strip()
 except FileNotFoundError:return 127,''
f={'selinux':run(['getenforce'])[1],'nssSystemd':ctypes.util.find_library('nss_systemd'),
   'systemd':run(['systemd','--version'])[1].splitlines()[:1],
   'provisioned':pathlib.Path('/var/aos/.provisionstate').exists(),
   'accounts':{n:False for n in ('aos-camera-access','aos-vdp')},'configs':{},'units':{}}
for n in f['accounts']:
 try:pwd.getpwnam(n);f['accounts'][n]=True
 except KeyError:pass
for n in ('aos-sm.service','aos-cm.service','aos-iam.service','aos-vehicle-data-provider.service'):
 code,out=run(['systemctl','show',n,'-p','ActiveState','-p','NRestarts','-p','FragmentPath'])
 f['units'][n]=dict(v.split('=',1) for v in out.splitlines() if '=' in v)
for name in ('sm.cfg','resources.cfg','resources-demo-services.cfg'):
 p=pathlib.Path('/etc/aos')/name
 if p.exists():
  v=json.loads(p.read_bytes())
  if isinstance(v,dict):f['configs'][name]={'runtimes':[{k:r.get(k) for k in ('plugin','type','isComponent')} for r in v.get('runtimes',[])]}
  elif isinstance(v,list):f['configs'][name]=[{k:r.get(k) for k in ('name','sharedCount','groups')} for r in v]
f['nssConfiguration']=next((l for l in pathlib.Path('/etc/nsswitch.conf').read_text().splitlines() if l.startswith('group:')),'') if pathlib.Path('/etc/nsswitch.conf').exists() else ''
f['tools']={n:__import__('shutil').which(n) is not None for n in ('crun','semodule','checkmodule','semodule_package','restorecon','systemd-run')}
f['ldconfigSystemd']=any('libnss_systemd' in str(p) for base in ('/lib','/usr/lib') for p in pathlib.Path(base).glob('libnss_systemd*'))
print(json.dumps(f))
'''


WORKER = r'''
import hashlib,json,pathlib,socket,subprocess,sys,time,uuid
c=CONTEXT
package=pathlib.Path(c['packageRoot']);root=pathlib.Path(c['remoteRecords']);vision=pathlib.Path(c['visionRoot'])
assert not root.exists(),'INVENTORY_ATTEMPT_EXISTS'
root.mkdir(mode=0o700)
assert subprocess.check_output(['/usr/sbin/sysctl','-n','hw.model'],text=True).strip()=='Mac16,8','M4_REQUIRED'
assert hashlib.sha256((package/'application-manifest.json').read_bytes()).hexdigest()==c['manifestSha256'],'PACKAGE_CHANGED'
for port in (10022,12022,2000,16443,18053):
 with socket.socket() as s:
  s.settimeout(.15);assert s.connect_ex(('127.0.0.1',port))!=0,'CONFLICTING_OWNER'
sys.path.insert(0,str(package/'aosedge-sdv-demo/apps/demo-orchestrator/src'))
import aosedge_demo_orchestrator
aosedge_demo_orchestrator.__path__.insert(0,str(root/'delta'))
for name,content in c['delta'].items():
 d=root/'delta';d.mkdir(mode=0o700,exist_ok=True);(d/name).write_text(content)
from aosedge_demo_orchestrator import runtime_paths
from aosedge_demo_orchestrator.environment import EnvironmentService,JOURNAL
from aosedge_demo_orchestrator.vm import VMService,access_path
from aosedge_demo_orchestrator.guest_access import ssh_command
retained=pathlib.Path(c['retainedRoot'])/JOURNAL
before=retained.read_bytes()
main=json.loads(before)['vehicles']['test']
assert main['localVmId']==c['retainedTest'] and main['runtime']['state']=='STOPPED','MAIN_NOT_PRESERVED'
v=json.loads((vision/JOURNAL).read_bytes())
assert v['vmProfile']=='aos-vision-main-qemuarm64-v1' and v['vehicles']['test']['localVmId']==c['visionTest'],'VISION_CHANGED'
result={'scenario':'CAMERA_ACCESS_NATIVE_INVENTORY','outcome':'NOT_COMPLETE','nativeActivation':'NOT_RUN'}
started=time.monotonic()
with runtime_paths.installed_session(vision):
 env=EnvironmentService(vm_profile='aos-vision-main-qemuarm64-v1')
 vm=VMService(env,progress=lambda v:print(json.dumps({'stage':'vm-owner','state':str(v)[:110]}),flush=True))
 try:
  print(json.dumps({'stage':'vision-boot','state':'STARTED'}),flush=True)
  value=vm.execute('start','test',timeout=100)
  assert value['vehicles']['test']['state']=='COMPLETED','VISION_START_FAILED'
  command=ssh_command(access_path(vision,'test'),12022,10)
  p=subprocess.run(command,input="python3 - <<'CAMERA_INVENTORY'\n"+c['guest']+"\nCAMERA_INVENTORY\n",capture_output=True,text=True,timeout=50)
  assert p.returncode==0 and len(p.stdout)<32768,'GUEST_INVENTORY_FAILED'
  result['guest']=json.loads(p.stdout);result['outcome']='PASS_INVENTORY_ONLY'
 except Exception as e:
  msg=str(e);result['code']=msg if msg.isupper() and msg.replace('_','').isalnum() else type(e).__name__
 finally:
  try:
   value=vm.execute('stop','test',timeout=60)
   result['vmStopped']=value['vehicles']['test']['state']=='COMPLETED' and vm.observe_readiness('test')['reason']=='VM_NOT_RUNNING'
  except Exception:result['vmStopped']=False
  result['mainBytesUnchanged']=retained.read_bytes()==before
  result['listenersReleased']=True
  for port in (12022,2000,16443,18053):
   with socket.socket() as s:s.settimeout(.15);result['listenersReleased']&=s.connect_ex(('127.0.0.1',port))!=0
  if not all(result.get(k) for k in ('vmStopped','mainBytesUnchanged','listenersReleased')):result['outcome']='NOT_COMPLETE'
  result['seconds']=round(time.monotonic()-started,2)
  (root/'result.json').write_text(json.dumps(result))
  print(json.dumps(result),flush=True)
'''


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--config',type=Path,required=True)
    p.add_argument('--resume-inventory',action='store_true');a=p.parse_args()
    c=configuration(a.config);records=Path(c['records'])/('camera-native-inventory-02' if a.resume_inventory else 'camera-native-inventory-01')
    if a.resume_inventory:
        old=json.loads((Path(c['records'])/'camera-native-inventory-01/result.json').read_bytes())
        h.require(old.get('code')=='GUEST_INVENTORY_FAILED' and all(old[k] for k in ('vmStopped','mainBytesUnchanged','listenersReleased')),'INVENTORY_FAILURE_NOT_RECONCILED')
    h.require(not records.exists(),'INVENTORY_ATTEMPT_EXISTS');records.mkdir(mode=0o700)
    previous=json.loads((Path(c['records'])/'moving-camera-02/live-result.json').read_bytes())
    h.require(previous['outcome']=='PASS_LIVE_ENGINEERING_PREVIEW' and all(previous['cleanup'].values()),'PREVIOUS_LIVE_NOT_RECONCILED')
    proof=json.loads((Path(c['records'])/'guest-continuation-3/vm-result.json').read_bytes())
    vision_test=proof.get('resumedExistingVm')
    h.require(proof.get('ownRuntimeStopped') is True and proof.get('visionRoot')==c['visionRoot']
              and isinstance(vision_test,str) and vision_test!=c['retainedTest'],'VISION_PROOF_NOT_RECONCILED')
    context=dict(c['main'],retainedRoot=c['main']['instanceRoot'],retainedTest=c['retainedTest'],visionRoot=c['visionRoot'],
                 visionTest=vision_test,remoteRecords=str(Path(c['remoteRoot'])/records.name),
                 guest=GUEST,delta={name:(SOURCE/name).read_text() for name in ('environment.py','vm.py','vm_profiles.py')})
    script=WORKER.replace('CONTEXT',repr(context),1)
    pin=hashlib.sha256(script.encode()).hexdigest()
    with h.Journal(records/'actions',pin) as journal:
        attempt=journal.begin('vision-native-inventory')
        attempt['dispatched']=True;h.atomic(journal.root/('attempt-'+str(attempt['attempt']).zfill(4)+'.json'),attempt)
        python=c['main']['packageRoot']+'/demo-artifacts/aosedge-sdv-demo/host-runtime/python/bin/python3.12'
        try:
            raw=h.remote(c['transport'],shlex.quote(python)+" -I -B - <<'VISION_CAMERA_INVENTORY'\n"+script+"\nVISION_CAMERA_INVENTORY",timeout=180)
            for line in raw.splitlines():
                if line.startswith('{'):print(line,flush=True)
            result=json.loads(raw.splitlines()[-1]);h.atomic(records/'result.json',result)
            ok=result['outcome']=='PASS_INVENTORY_ONLY'
            journal.finish(attempt,'PASS' if ok else 'UNCERTAIN',result.get('code','INVENTORY_COMPLETE'),dict(facts=result))
            return 0 if ok else 1
        except h.Error as error:
            h.atomic(records/'transport-failure.json',{'code':str(error),'replay':'RECONCILE_REQUIRED'})
            raise


if __name__=='__main__':raise SystemExit(main())
