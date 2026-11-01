#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Read native ingress prerequisites on the retained Vision VM, then stop it.

No Source, simulator, Cloud mutation, key/certificate read or policy change.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time


def main():
    context=json.loads(Path(sys.argv[1]).read_bytes());records=Path(sys.argv[1]).parent
    package=Path(context['main']['packageRoot']);bundle=Path(context['bundle'])
    assert not (records/'result.json').exists(),'EXISTING_ATTEMPT_RECONCILE'
    assert hashlib.sha256((package/'application-manifest.json').read_bytes()).hexdigest()==context['main']['manifestSha256']
    subprocess.run(['codesign','--verify','--deep','--strict','-R',
        '=identifier "org.aosedge.sdvlab.vision.bootstrap" and anchor apple generic and certificate leaf[subject.OU] = "3NF57VKB3V"',
        str(bundle)],check=True,capture_output=True,timeout=120)
    sys.path.insert(0,str(package/'aosedge-sdv-demo/apps/demo-orchestrator/src'))
    import aosedge_demo_orchestrator
    # Installed scope must be the trusted base package, not bootstrap tooling.
    # Its CODE_ROOT is captured at import; load it before the verified overlay.
    from aosedge_demo_orchestrator import runtime_paths
    aosedge_demo_orchestrator.__path__.insert(0,str(bundle/'Contents/Resources/tooling/aosedge-sdv-demo/apps/demo-orchestrator/src/aosedge_demo_orchestrator'))
    from aosedge_demo_orchestrator import vision_bootstrap as v
    from aosedge_demo_orchestrator.environment import EnvironmentService,JOURNAL
    from aosedge_demo_orchestrator.vm import VMService,access_path
    from aosedge_demo_orchestrator.guest_access import ssh_command
    bootstrap=v.verify(bundle,context['main']['manifestSha256']);assert bootstrap.manifest_sha256==context['bootstrapManifestSha256']
    native=Path.home()/v.INSTANCE_NAME
    retained={Path.home()/name:(Path.home()/name/JOURNAL).read_bytes() for name in v.RETAINED_INSTANCE_NAMES}
    before=json.loads((native/JOURNAL).read_bytes());item=before['vehicles']['test']
    assert item['runtime']['state']=='STOPPED' and before['source']['state']=='STOPPED'
    result=dict(scenario='VISION_INGRESS_NATIVE_PREFLIGHT',outcome='NOT_COMPLETE',cleanup={})
    start=time.monotonic()
    with runtime_paths.installed_session(native):
        env=EnvironmentService(catalog=v.SignedVisionCatalog(bootstrap),vm_profile=v.VM_PROFILE)
        vm=VMService(env,progress=lambda message:print(json.dumps(dict(stage='native-owner',message=str(message)[:100])),flush=True))
        try:
            print(json.dumps(dict(stage='native-preflight-start')),flush=True)
            value=vm.execute('start','test',timeout=150);assert value['vehicles']['test']['state']=='COMPLETED'
            current=json.loads((native/JOURNAL).read_bytes());assert current['vehicles']['test']['unitId']==item['unitId']
            command=ssh_command(access_path(native,'test'),item['sshPort'],5)
            script=r'''import grp,json,os,pathlib,pwd,subprocess,time
def call(args):return subprocess.check_output(args,text=True,stderr=subprocess.DEVNULL,timeout=10)
end=time.monotonic()+20
while True:
 unit=dict(v.split('=',1) for v in call(['systemctl','show','aos-camera-access','-p','ActiveState','-p','Result','-p','NRestarts','-p','MainPID']).splitlines())
 if unit['ActiveState']=='active' or time.monotonic()>=end:break
 time.sleep(.25)
names=['/run/credentials','/run/credentials/aos-sm.service','/run/aos-camera-access/oem/producer.sock','/usr/bin/python3','/usr/libexec/aos-camera-access-launcher']
facts=[]
for name in names:
 p=pathlib.Path(name)
 if p.exists():
  s=p.stat();facts.append(dict(kind=p.name,uid=s.st_uid,gid=s.st_gid,mode=oct(s.st_mode&0o777),context=os.getxattr(p,'security.selinux').decode().rstrip('\0')))
pid=int(unit['MainPID']);p=pathlib.Path('/proc')/str(pid)
status=dict(v.split(':',1) for v in (p/'status').read_text().splitlines() if ':' in v) if pid else {}
print(json.dumps(dict(enforcing=pathlib.Path('/sys/fs/selinux/enforce').read_text().strip()=='1',unit=unit,
 uid=pwd.getpwnam('aos-camera-access').pw_uid,gid=grp.getgrnam('aos-camera-read').gr_gid,
 nativeContext=(p/'attr/current').read_text().strip() if pid else None,nativeCaps=status.get('CapEff','').strip(),
 labels=facts,credentialMounts=[v for v in pathlib.Path('/proc/1/mountinfo').read_text().splitlines() if ' /run/credentials/' in v],
 pythonVersion=call(['python3','-V']).strip(),systemdVersion=call(['systemctl','--version']).splitlines()[0])))
'''
            import textwrap
            wrapped='import json,traceback\ntry:\n'+textwrap.indent(script,' ')+'\nexcept Exception as error:\n print(json.dumps(dict(probeError=type(error).__name__,line=traceback.extract_tb(error.__traceback__)[-1].lineno)))\n'
            done=subprocess.run(command,input="python3 - <<'VISION_PREFLIGHT'\n"+wrapped+"\nVISION_PREFLIGHT\n",capture_output=True,text=True,timeout=50)
            assert done.returncode==0,'NATIVE_PREFLIGHT_OBSERVATION_FAILED'
            result['facts']=json.loads(done.stdout)
            assert 'probeError' not in result['facts'],'NATIVE_PREFLIGHT_PROBE_ERROR'
            assert result['facts']['unit']['ActiveState']=='active','NATIVE_CAMERA_NOT_ACTIVE'
            result['outcome']='PASS_NATIVE_PREREQUISITES'
        except Exception as error:
            result['code']=str(error) if isinstance(error,AssertionError) else type(error).__name__
        finally:
            try:
                stopped=vm.execute('stop','test',timeout=150)
                result['cleanup']['visionStopped']=stopped['vehicles']['test']['state']=='COMPLETED'
            except Exception:result['cleanup']['visionStopped']=False
            result['cleanup']['retainedUnchanged']=all((path/JOURNAL).read_bytes()==raw for path,raw in retained.items())
            result['seconds']=round(time.monotonic()-start,2)
            if not all(result['cleanup'].values()):result['outcome']='NOT_COMPLETE'
            (records/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:val for k,val in result.items() if k!='facts'}),flush=True)
    return 0 if result['outcome']=='PASS_NATIVE_PREREQUISITES' else 1


if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as error:
        # Early verification/import failures must also leave a bounded result.
        # No guessed cleanup claim: these booleans remain false until observed.
        path=Path(sys.argv[1]).parent/'result.json'
        if not path.exists():
            value=dict(scenario='VISION_INGRESS_NATIVE_PREFLIGHT',outcome='NOT_COMPLETE',
                code=type(error).__name__,cleanupVerified=False)
            path.write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(value),flush=True)
        raise SystemExit(1)
