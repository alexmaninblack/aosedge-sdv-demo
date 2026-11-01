#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Bounded stopped-state continuation; no manufacture, provisioning or cleanup."""
import argparse
import hashlib
import json
import re
from pathlib import Path
import subprocess
import sys


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--context',type=Path,required=True)
    p.add_argument('--output-name',default='native-inventory.json')
    a=p.parse_args();assert re.fullmatch(r'native-inventory(?:-[0-9]{2})?\.json',a.output_name)
    c=json.loads(a.context.read_bytes())
    package=Path(c['main']['packageRoot']);bundle=Path(c['bundle'])
    assert hashlib.sha256((package/'application-manifest.json').read_bytes()).hexdigest()==c['main']['manifestSha256']
    requirement='=identifier "org.aosedge.sdvlab.vision.bootstrap" and anchor apple generic and certificate leaf[subject.OU] = "3NF57VKB3V"'
    subprocess.run(['codesign','--verify','--deep','--strict','-R',requirement,str(bundle)],check=True,capture_output=True,timeout=120)
    sys.path.insert(0,str(package/'aosedge-sdv-demo/apps/demo-orchestrator/src'))
    import aosedge_demo_orchestrator
    from aosedge_demo_orchestrator import runtime_paths
    aosedge_demo_orchestrator.__path__.insert(0,str(bundle/'Contents/Resources/tooling/aosedge-sdv-demo/apps/demo-orchestrator/src/aosedge_demo_orchestrator'))
    from aosedge_demo_orchestrator import vision_bootstrap as v
    from aosedge_demo_orchestrator.environment import EnvironmentService,JOURNAL
    from aosedge_demo_orchestrator.vm import VMService,access_path
    from aosedge_demo_orchestrator.guest_access import ssh_command
    bootstrap=v.verify(bundle,c['main']['manifestSha256']);assert bootstrap.manifest_sha256==c['bootstrapManifestSha256']
    native=Path.home()/v.INSTANCE_NAME
    retained={Path.home()/n:(Path.home()/n/JOURNAL).read_bytes() for n in ('SDV-Lab-Data','SDV-Vision-Lab-Data')}
    old=json.loads((native/JOURNAL).read_bytes())['vehicles']['test']
    assert old['cloud']['lifecycle']=='ONLINE' and old['runtime']['state']=='STOPPED'
    with runtime_paths.installed_session(native):
        env=EnvironmentService(catalog=v.SignedVisionCatalog(bootstrap),vm_profile=v.VM_PROFILE)
        vm=VMService(env,progress=lambda message:print(json.dumps(dict(stage='native-owner',state=str(message)[:110])),flush=True))
        result=dict(scenario='VISION_NATIVE_BOOTSTRAP_INVENTORY',outcome='NOT_COMPLETE')
        try:
            boot=vm.execute('start','test',timeout=150)
            assert boot['vehicles']['test']['state']=='COMPLETED'
            state=json.loads((native/JOURNAL).read_bytes());item=state['vehicles']['test']
            assert item['localVmId']==old['localVmId'] and item['unitId']==old['unitId']
            code='''import json,os,pathlib,pwd,grp,shutil,subprocess
def account(kind,name):
 try:
  v=pwd.getpwnam(name) if kind=='user' else grp.getgrnam(name)
  return dict(present=True,id=v.pw_uid if kind=='user' else v.gr_gid)
 except KeyError:return dict(present=False)
sm=json.loads(pathlib.Path('/etc/aos/sm.cfg').read_bytes())
directories={}
for name in ('/var/aos/workdirs','/var/aos/workdirs/sm','/var/aos/workdirs/sm/runtimes/systemd-slot-component','/var/aos/workdirs/sm/runtimes/systemd-slot-camera-access'):
 p=pathlib.Path(name)
 directories[name]=dict(present=p.is_dir(),mounted=os.path.ismount(p),uid=p.stat().st_uid if p.exists() else None,mode=oct(p.stat().st_mode & 0o777) if p.exists() else None)
props=subprocess.run(['systemctl','show','aos-sm','--property=ActiveState,Result,NRestarts,MainPID'],capture_output=True,text=True)
j=subprocess.run(['journalctl','-u','aos-sm','-b','-n','30','--no-pager','-o','cat'],capture_output=True,text=True)
stages=[line[:200] for line in j.stdout.splitlines() if any(w in line for w in ('Failed','failed','Dependency','dependency','not found','No such','invalid','permission'))]
print(json.dumps(dict(enforcing=pathlib.Path('/sys/fs/selinux/enforce').read_text().strip(),
 user=account('user','aos-camera-access'),group=account('group','aos-camera-read'),getentAvailable=shutil.which('getent') is not None,
 sm=dict(line.split('=',1) for line in props.stdout.splitlines() if '=' in line),failures=stages,
 cameraLauncherPresent=pathlib.Path('/usr/libexec/aos-camera-access-launcher').is_file(),
 vdpLauncherPresent=pathlib.Path('/usr/libexec/aos-vehicle-data-provider-launcher').exists(),
 target=[v for v in sm['runtimes'] if v['plugin']=='systemd-slot-component'],
 resources=json.loads(pathlib.Path('/etc/aos/resources.cfg').read_bytes()),directories=directories,
 mounts=[line.split()[:3] for line in pathlib.Path('/proc/mounts').read_text().splitlines() if line.split()[1].startswith('/var/aos')],
 storeMounted=os.path.ismount('/var/aos/workdirs/sm/runtimes/systemd-slot-camera-access'))))
'''
            command=ssh_command(access_path(native,'test'),item['sshPort'],5)
            script="python3 - <<'VISION_INVENTORY'\n"+code+"\nVISION_INVENTORY\n"
            done=subprocess.run(command,input=script,capture_output=True,text=True,timeout=15)
            assert done.returncode==0,'GUEST_OBSERVATION_FAILED'
            result.update(outcome='OBSERVED',facts=json.loads(done.stdout))
        finally:
            stop=vm.execute('stop','test',timeout=90)
            result['cleanup']=dict(nativeVmStopped=stop['vehicles']['test']['state']=='COMPLETED',
                retainedJournalsUnchanged=all((root/JOURNAL).read_bytes()==raw for root,raw in retained.items()))
            target=a.context.parent/a.output_name
            assert not target.exists()
            target.write_text(json.dumps(result,indent=2)+'\n');target.chmod(0o600)
            print(json.dumps(result),flush=True)


if __name__=='__main__':main()
