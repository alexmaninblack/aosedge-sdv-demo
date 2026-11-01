#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Bounded read-only guest inventory after the exact fresh Source boot fault."""
import argparse
import json
from pathlib import Path
import shlex
import remote_harness as h
from vision_vm_campaign import configuration


def main():
    p=argparse.ArgumentParser();p.add_argument('--config',type=Path,required=True);a=p.parse_args()
    c=configuration(a.config);python=c['main']['packageRoot']+'/demo-artifacts/aosedge-sdv-demo/host-runtime/python/bin/python3.12'
    records=Path(c['records'])/'vision-fresh-diagnose-01';h.require(not records.exists(),'DIAGNOSTIC_EXISTS_RECONCILE');records.mkdir(mode=0o700)
    code=r'''import json,sys,pathlib,subprocess,stat
main=MAIN
bundle=pathlib.Path(BUNDLE)
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
verified=v.verify(bundle,main['manifestSha256']);native=pathlib.Path.home()/v.INSTANCE_NAME
retained={pathlib.Path.home()/n:(pathlib.Path.home()/n/JOURNAL).read_bytes() for n in v.RETAINED_INSTANCE_NAMES}
result={}
with runtime_paths.installed_session(native):
 env=EnvironmentService(catalog=v.SignedVisionCatalog(verified),vm_profile=v.VM_PROFILE);vm=VMService(env)
 try:
  result['start']=vm.execute('start','test',timeout=150)
  code=GUEST
  state=read_json(native/JOURNAL);item=state['vehicles']['test']
  done=subprocess.run(ssh_command(access_path(native,'test'),item['sshPort'],5),input="python3 - <<'DIAG'\n"+code+"\nDIAG\n",capture_output=True,text=True,timeout=35)
  assert done.returncode==0 and len(done.stdout)<131072
  result['inventory']=json.loads(done.stdout)
 finally:
  result['stop']=vm.execute('stop','test',timeout=150)
  result['retainedJournalsUnchanged']=all((p/JOURNAL).read_bytes()==raw for p,raw in retained.items())
print(json.dumps(result))
'''
    guest=r'''import pathlib,json,subprocess,stat
root=pathlib.Path('/var/aos/workdirs/sm/runtimes/systemd-slot-camera-access')
names=['aos-sm','aos-camera-access','aos-camera-access-bootstrap','aos-camera-access-store-layout','aos-camera-access-store-prepare','aos-camera-access-store-attach']
units={n:dict(v.split('=',1) for v in subprocess.check_output(['systemctl','show',n,'-p','ActiveState','-p','Result','-p','ExecMainStatus','-p','NRestarts'],text=True).splitlines() if '=' in v) for n in names}
files={}
for relative in ('state/installed.json','state/transaction.json','demo-inputs/selected.json','demo-inputs/viss-update-binding','demo-inputs/viss-update-ca'):
 p=root/relative;files[relative]=dict(exists=p.exists(),linked=p.is_symlink())
 if p.exists():
  s=p.stat();files[relative].update(mode=oct(stat.S_IMODE(s.st_mode)),uid=s.st_uid,bytes=s.st_size,context=subprocess.check_output(['ls','-Zd',str(p)],text=True).split()[0])
for role in ('selected-platform-unit','platform-update-runtime'):
 for name in ('client.pem','client-key.pem'):
  p=pathlib.Path('/var/aos/iam/vehicle-state')/role/name
  files[role+'/'+name]=dict(exists=p.exists(),mode=oct(stat.S_IMODE(p.stat().st_mode)) if p.exists() else None)
check=subprocess.run(['/usr/libexec/aos-camera-access-store-check','verify'],capture_output=True,text=True)
metadata=json.loads((root/'state/installed.json').read_bytes()) if (root/'state/installed.json').is_file() else None
transaction=json.loads((root/'state/transaction.json').read_bytes()) if (root/'state/transaction.json').is_file() else None
print(json.dumps(dict(units=units,files=files,storeVerified=check.returncode==0,installed=metadata,transaction=transaction,
 mounts=[s.split()[:4] for s in pathlib.Path('/proc/mounts').read_text().splitlines() if str(root) in s])))
'''
    code=code.replace('MAIN',repr(c['main'])).replace('BUNDLE',repr(str(Path(c['remoteRoot'])/'signed-bootstrap-04/AosEdge Vision Bootstrap 0.5.0.bundle'))).replace('GUEST',repr(guest))
    value=json.loads(h.remote(c['transport'],shlex.quote(python)+' -I -B -c '+shlex.quote(code),timeout=240))
    h.atomic(records/'result.json',value);print(json.dumps(value,indent=2))


if __name__=='__main__':main()
