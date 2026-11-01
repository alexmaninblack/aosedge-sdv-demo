#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Normal manufacture and bounded reversible storage proof; no Cloud Unit."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def atomic(p,value):
    t=p.with_suffix('.pending');t.write_text(json.dumps(value,indent=2));t.chmod(0o600);os.replace(t,p)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--context',type=Path,required=True);a=p.parse_args()
    c=json.loads(a.context.read_bytes());records=a.context.parent;assert not (records/'result.json').exists()
    console=json.loads(sys.stdin.read(8193));assert set(console)=={'password'}
    package=Path(c['main']['packageRoot']);bundle=Path(c['bundle'])
    assert hashlib.sha256((package/'application-manifest.json').read_bytes()).hexdigest()==c['main']['manifestSha256']
    requirement='=identifier "org.aosedge.sdvlab.vision.bootstrap" and anchor apple generic and certificate leaf[subject.OU] = "3NF57VKB3V"'
    subprocess.run(['codesign','--verify','--deep','--strict','-R',requirement,str(bundle)],capture_output=True,check=True,timeout=120)
    sys.path.insert(0,str(package/'aosedge-sdv-demo/apps/demo-orchestrator/src'))
    import aosedge_demo_orchestrator
    from aosedge_demo_orchestrator import runtime_paths,installed_control
    aosedge_demo_orchestrator.__path__.insert(0,str(bundle/'Contents/Resources/tooling/aosedge-sdv-demo/apps/demo-orchestrator/src/aosedge_demo_orchestrator'))
    from aosedge_demo_orchestrator import vision_bootstrap as v
    from aosedge_demo_orchestrator.environment import EnvironmentService,JOURNAL
    from aosedge_demo_orchestrator.vm import VMService,access_path
    from aosedge_demo_orchestrator.guest_access import ssh_command
    b=v.verify(bundle,c['main']['manifestSha256']);assert b.manifest_sha256==c['bootstrapManifestSha256']
    retained_native=c.get('retainedNative') is True
    root=Path.home()/('SDV-Vision-Native-Lab-Data' if retained_native else 'SDV-Vision-Store-Proof-Data')
    names=('SDV-Lab-Data','SDV-Vision-Lab-Data') if retained_native else ('SDV-Lab-Data','SDV-Vision-Lab-Data','SDV-Vision-Native-Lab-Data')
    retained={Path.home()/n:(Path.home()/n/JOURNAL).read_bytes() for n in names}
    assert all(all(i.get('runtime',{}).get('state')=='STOPPED' for i in json.loads(raw)['vehicles'].values()) for raw in retained.values())
    result=dict(scenario='VISION_CAMERA_STORE_M4',outcome='NOT_COMPLETE',phases=[],cleanup={},cloudMutations=False)
    started=time.monotonic();vm=None
    def phase(name,action):
        print(json.dumps(dict(stage=name,state='STARTED')),flush=True);begin=time.monotonic();value=action()
        result['phases'].append(dict(name=name,seconds=round(time.monotonic()-begin,2)))
        atomic(records/(name+'.json'),value);print(json.dumps(dict(stage=name,state='COMPLETE')),flush=True)
        return value
    try:
        sys.path.insert(0,str(Path(c['main']['setupApp'])/'Contents/Resources/tooling/scripts/distribution'))
        from installation import Store
        from version_management import Versions
        _,old_id=runtime_paths.instance(Path.home()/'SDV-Lab-Data')
        selected=installed_control.selection(Path.home()/'SDV-Lab-Data',old_id)
        store=Store(Path(selected['storePath']),selected['volumeUUID'])
        if retained_native:
            state=json.loads((root/JOURNAL).read_bytes());old=state['vehicles']['test']
            assert old.get('unitId') and old['cloud']['identity']['model']=='aos-vision-vm' and old['runtime']['state']=='STOPPED'
        else:
            assert not root.exists(),'PROOF_INSTANCE_EXISTS_RECONCILE'
            phase('proof-instance',lambda:runtime_paths.create_instance(root))
            phase('base-selection',lambda:Versions(store,root).change('select',0,c['main']['manifestSha256']))
        with runtime_paths.installed_session(root):
            env=EnvironmentService(catalog=v.SignedVisionCatalog(b),vm_profile=v.VM_PROFILE)
            vm=VMService(env,password_provider=lambda role:console['password'],progress=lambda message:print(json.dumps(dict(stage='vm-owner',state=str(message)[:110])),flush=True))
            if not retained_native:phase('normal-manufacture',lambda:env.create('test',selector=v.SELECTOR))
            boot=phase('proof-boot',lambda:vm.execute('start','test',timeout=180))
            assert boot['vehicles']['test']['state']=='COMPLETED'
            console.clear();vm.password_provider=None
            state=json.loads((root/JOURNAL).read_bytes())
            assert (state['vehicles']['test'].get('unitId')==old['unitId']) if retained_native else not state['vehicles']['test'].get('unitId')
            command=ssh_command(access_path(root,'test'),state['vehicles']['test']['sshPort'],5)
            raw=(records/'payload.tar.gz').read_bytes();assert hashlib.sha256(raw).hexdigest()==c['payloadSha256'] and len(raw)<4*1024**2
            code="""import base64,hashlib,io,pathlib,tarfile
r=pathlib.Path('/run/vision-camera-store-proof');assert not r.exists();r.mkdir(mode=0o700)
raw=base64.b64decode(PAYLOAD);assert hashlib.sha256(raw).hexdigest()==DIGEST
with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as t:t.extractall(r,filter='data')
""".replace('PAYLOAD',repr(base64.b64encode(raw).decode())).replace('DIGEST',repr(c['payloadSha256']))
            script="python3 - <<'PREPARE_STORE_PROOF'\n"+code+"\nPREPARE_STORE_PROOF\npython3 /run/vision-camera-store-proof/guest.py\n"
            def proof():
                r=subprocess.run(command,input=script,text=True,capture_output=True,timeout=240)
                lines=[line for line in r.stdout.splitlines() if line.startswith('{')]
                if not lines:
                    atomic(records/'guest-command.json',dict(exit=r.returncode,diagnostic=r.stderr[-2000:]))
                    raise RuntimeError('STORE_PROOF_RESULT_MISSING')
                value=json.loads(lines[-1]);atomic(records/'guest-result.json',value)
                assert r.returncode==0 and value['outcome']=='PASS_TRANSIENT_STORE_ONLY','STORE_TRANSIENT_PROOF_FAILED'
                return value
            phase('storage-functional-security-recovery',proof)
            result['outcome']='PASS_TRANSIENT_STORE_ONLY'
    except Exception as error:
        result['code']=str(error)[:150] if isinstance(error,(RuntimeError,AssertionError)) else type(error).__name__
    finally:
        console.clear()
        if vm is not None:
            try:
                with runtime_paths.installed_session(root):
                    stop=vm.execute('stop','test',timeout=150)
                    result['cleanup']['proofVmStopped']=stop['vehicles']['test']['state']=='COMPLETED'
            except Exception:result['cleanup']['proofVmStopped']=False
        result['cleanup']['retainedJournalsUnchanged']=all((p/JOURNAL).read_bytes()==raw for p,raw in retained.items())
        if not all(result['cleanup'].values()):result['outcome']='NOT_COMPLETE'
        result['seconds']=round(time.monotonic()-started,2);atomic(records/'result.json',result);print(json.dumps(result),flush=True)
    return 0 if result['outcome']=='PASS_TRANSIENT_STORE_ONLY' else 1


if __name__=='__main__':raise SystemExit(main())
