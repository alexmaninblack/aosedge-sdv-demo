#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Bounded same-VM native-delivery diagnosis; no Cloud/config/cache mutation."""
import argparse
import json
from pathlib import Path
import re
import shlex
import subprocess
import sys
import time


def worker(context):
    c=json.loads(context.read_bytes());records=context.parent
    sys.path.insert(0,str(Path(c['packageRoot'])/'aosedge-sdv-demo/apps/demo-orchestrator/src'))
    import aosedge_demo_orchestrator
    from aosedge_demo_orchestrator import runtime_paths
    aosedge_demo_orchestrator.__path__.insert(0,str(Path(c['bundle'])/'Contents/Resources/tooling/aosedge-sdv-demo/apps/demo-orchestrator/src/aosedge_demo_orchestrator'))
    from aosedge_demo_orchestrator import vision_bootstrap as v
    from aosedge_demo_orchestrator.environment import EnvironmentService,JOURNAL
    from aosedge_demo_orchestrator.vm import VMService,access_path
    from aosedge_demo_orchestrator.guest_access import ssh_command
    from vision_services_live import atomic,evidence,require,clean_error
    native=Path.home()/v.INSTANCE_NAME;before=json.loads((native/JOURNAL).read_bytes())
    retained={Path.home()/name:(Path.home()/name/JOURNAL).read_bytes() for name in v.RETAINED_INSTANCE_NAMES}
    item=before['vehicles']['test'];require(item['unitId']==c['unitId'] and item['runtime']['state']=='STOPPED' and before['source']['state']=='STOPPED','SAME_STOPPED_VISION_REQUIRED')
    result=dict(outcome='NOT_COMPLETE',cleanup={});start=time.monotonic();vm=None
    try:
        bootstrap=v.verify(Path(c['bundle']),c['baseManifest'])
        with runtime_paths.installed_session(native):
            vm=VMService(EnvironmentService(catalog=v.SignedVisionCatalog(bootstrap),vm_profile=v.VM_PROFILE))
            vm.execute('start','test',timeout=150)
            current=json.loads((native/JOURNAL).read_bytes())['vehicles']['test'];command=ssh_command(access_path(native,'test'),current['sshPort'],8)
            code='''import json,pathlib,re,subprocess,shutil
def scrub(s):
 s=re.sub(r'https?://[^\\s\\"\\x27]+','<url>',s)
 s=re.sub(r'eyJ[A-Za-z0-9_-]+\\.[A-Za-z0-9_-]+\\.[A-Za-z0-9_-]+','<token>',s)
 if any(x in s.lower() for x in ('-----begin','privatekey','private_key','fingerprint','authorization:','password','pin=')):return '<private diagnostic omitted>'
 return s[:1800]
logs={}
for unit in ('aos-cm','aos-sm','aos-iam'):
 options=['--since','2026-11-01 23:18:00','--until','2026-11-01 23:22:30'] if HISTORY else []
 p=subprocess.run(['journalctl','-u',unit,'--no-pager','-n','4000','-o','short-iso',*options],capture_output=True,text=True,timeout=12)
 logs[unit]=[scrub(s) for s in p.stdout.splitlines() if 'message={' not in s and any(w in s.lower() for w in ('error','fail','denied','space','download','install','resource','image','quota'))][-200:]
inventory=[]
for parent in ('/var/aos/workdirs/cm','/var/aos/workdirs/sm'):
 root=pathlib.Path(parent)
 for p in sorted(root.rglob('*')):
  if len(inventory)>=160:break
  if p.is_file() and not p.is_symlink() and p.stat().st_size>1000000:inventory.append(dict(path=str(p),bytes=p.stat().st_size))
space={p:dict(total=shutil.disk_usage(p).total,free=shutil.disk_usage(p).free) for p in ('/var/aos','/var/aos/workdirs','/var/aos/storages','/var/aos/states')}
layout={}
if LAYOUT:
 for name,args in (('vg',['vgs','--reportformat','json','--units','b','--nosuffix','-o','vg_name,vg_size,vg_free']),('lv',['lvs','--reportformat','json','--units','b','--nosuffix','-o','vg_name,lv_name,lv_size']),('blocks',['lsblk','-b','-J','-o','NAME,SIZE,FSTYPE,MOUNTPOINT'])):
  p=subprocess.run(args,capture_output=True,text=True,timeout=12)
  layout[name]=json.loads(p.stdout) if p.returncode==0 else dict(available=False)
print(json.dumps(dict(logs=logs,inventory=inventory,space=space,layout=layout)))
'''.replace('HISTORY',repr(c.get('history',False))).replace('LAYOUT',repr(c.get('layout',False)))
            done=subprocess.run(command,input='python3 -I -B -c '+shlex.quote(code)+'\n',capture_output=True,text=True,timeout=60)
            require(done.returncode==0 and len(done.stdout)<262144,'NATIVE_DIAGNOSTIC_UNAVAILABLE')
            atomic(records/'diagnosis.json',evidence(json.loads(done.stdout)));result['outcome']='PASS_READ_ONLY_NATIVE_DELIVERY_DIAGNOSIS'
    except Exception as error:result['code']=clean_error(error)
    finally:
        if vm:
            with runtime_paths.installed_session(native):
                try:result['cleanup']['vmStopped']=vm.execute('stop','test',timeout=150)['vehicles']['test']['state']=='COMPLETED'
                except Exception:result['cleanup']['vmStopped']=False
        state=json.loads((native/JOURNAL).read_bytes());result['cleanup']['sameVmAndUnit']=state['vehicles']['test']['unitId']==item['unitId'] and state['vehicles']['test']['localVmId']==item['localVmId']
        result['cleanup']['retainedJournalsUnchanged']=all((p/JOURNAL).read_bytes()==raw for p,raw in retained.items())
        result['seconds']=round(time.monotonic()-start,2)
        if not all(result['cleanup'].values()) or 'code' in result:result['outcome']='NOT_COMPLETE'
        atomic(records/'result.json',result);print(json.dumps(result),flush=True)
    return 0 if result['outcome'].startswith('PASS_') else 1


def main():
    p=argparse.ArgumentParser();p.add_argument('--config',type=Path);p.add_argument('--worker',type=Path);p.add_argument('--attempt',type=int,choices=(1,2,3),default=1);a=p.parse_args()
    if a.worker:return worker(a.worker)
    import remote_harness as h
    from vision_vm_campaign import configuration
    from vision_services_live import atomic,require
    c=configuration(a.config);name='vision-services-native-diagnose-'+str(a.attempt).zfill(2);records=Path(c['records'])/name;remote=Path(c['remoteRoot'])/name
    prior=json.loads((Path(c['records'])/('vision-services-native-live-'+str(a.attempt).zfill(2))/'result.json').read_bytes())
    require(prior.get('code')=='VISION_NATIVE_INSTANCE_START_UNCONFIRMED' and all(prior['cleanup'].values()),'NATIVE_FAILED_DELIVERY_REQUIRED')
    require(not records.exists(),'DIAGNOSIS_EXISTS_RECONCILE');records.mkdir(mode=0o700)
    old=json.loads((Path(c['records'])/'vision-services-native-live-01/context.json').read_bytes())
    context={key:old[key] for key in ('packageRoot','bundle','baseManifest')};context['history']=a.attempt==2;context['layout']=a.attempt==3;context['unitId']='af6d074a-6ce1-49ba-b613-0476e7b6d1b5';atomic(records/'context.json',context)
    h.remote(c['transport'],'umask 077\nmkdir '+shlex.quote(str(remote)),timeout=15)
    args=h.ssh_args(c['transport'])[1:-1];args.remove('-T');i=args.index('-b');args[i:i+2]=['-o','BindAddress='+args[i+1]]
    h.run(['/usr/bin/scp',*args,__file__,str(Path(__file__).with_name('vision_services_live.py')),str(records/'context.json'),c['transport']['user']+'@'+c['transport']['host']+':'+str(remote)+'/'],timeout=20)
    python=c['main']['packageRoot']+'/demo-artifacts/aosedge-sdv-demo/host-runtime/python/bin/python3.12'
    result=h.remote(c['transport'],shlex.join([python,'-B',str(remote/Path(__file__).name),'--worker',str(remote/'context.json')]),timeout=240);print(result,flush=True)
    collect='import json,pathlib;root=pathlib.Path('+repr(str(remote))+');print(json.dumps({p.name:json.loads(p.read_bytes()) for p in root.glob("*.json") if p.name!="context.json"}))'
    values=json.loads(h.remote(c['transport'],shlex.join([python,'-I','-B','-c',collect]),timeout=20))
    for name,value in values.items():atomic(records/name,value)
    return 0


if __name__=='__main__':raise SystemExit(main())
