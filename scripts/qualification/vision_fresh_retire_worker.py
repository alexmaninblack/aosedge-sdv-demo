#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Retire only the explicitly discarded Vision experiment, never a peer VM."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

OLD_UNIT='4374bcb2-0613-419c-8ac9-e8458358c91c'
OLD_NODE='d22dca91-5746-4218-ac1a-cc9bd489023c'
OLD_VM='2a624dfd-8745-476b-8a5e-890baae119e3'
INSTANCE='SDV-Vision-Camera-Image-Lab-Data'


def require(ok,code):
    if not ok:raise ValueError(code)


def target(root,state):
    require(root==Path('/Users/alexagizim')/INSTANCE and not root.is_symlink(),'EXACT_DISPOSABLE_ROOT_REQUIRED')
    item=state['vehicles']['test']
    require(set(state['vehicles'])=={'test'} and item['unitId']==OLD_UNIT and item['nodeId']==OLD_NODE
        and item['localVmId']==OLD_VM and state['vmProfile']=='aos-vision-main-qemuarm64-v1','DISPOSABLE_IDENTITY_CHANGED')
    require(item['runtime']['state']==state['source']['state']=='STOPPED' and state.get('currentVehicle') is None
        and not state['source'].get('operation') and not state['source'].get('stopOperation'),'DISPOSABLE_NOT_IDLE')
    return item


def main():
    context=Path(sys.argv[1]);c=json.loads(context.read_bytes());records=context.parent
    require(not (records/'result.json').exists(),'RETIREMENT_EXISTS_RECONCILE')
    def record(name,value):
        p=records/name;p.write_text(json.dumps(value,indent=2)+'\n');p.chmod(0o600)
    result=dict(scenario='VISION_DISPOSABLE_FRESH_RETIREMENT',outcome='NOT_COMPLETE',cleanup={},phases=[],removed=[])
    began=time.monotonic();retained={};native=Path.home()/INSTANCE
    def phase(name,action):
        print(json.dumps(dict(stage=name,state='STARTED')),flush=True);start=time.monotonic();value=action()
        record(name+'.json',value);result['phases'].append(dict(stage=name,seconds=round(time.monotonic()-start,2)))
        print(json.dumps(dict(stage=name,state='COMPLETE')),flush=True);return value
    try:
        package=Path(c['main']['packageRoot']);bundle=Path(c['bundle'])
        require(hashlib.sha256((package/'application-manifest.json').read_bytes()).hexdigest()==c['main']['manifestSha256'],'BASE_CHANGED')
        subprocess.run(['codesign','--verify','--deep','--strict','-R',
            '=identifier "org.aosedge.sdvlab.vision.bootstrap" and anchor apple generic and certificate leaf[subject.OU] = "3NF57VKB3V"',
            str(bundle)],check=True,capture_output=True,timeout=120)
        sys.path.insert(0,str(package/'aosedge-sdv-demo/apps/demo-orchestrator/src'))
        import aosedge_demo_orchestrator
        from aosedge_demo_orchestrator import runtime_paths
        aosedge_demo_orchestrator.__path__.insert(0,str(bundle/'Contents/Resources/tooling/aosedge-sdv-demo/apps/demo-orchestrator/src/aosedge_demo_orchestrator'))
        from aosedge_demo_orchestrator import vision_bootstrap as v
        from aosedge_demo_orchestrator.environment import EnvironmentService,JOURNAL
        from aosedge_demo_orchestrator.vm import VMService
        from aosedge_demo_orchestrator.units import UnitService
        from aosedge_demo_orchestrator.status import load_configuration,read_json
        verified=v.verify(bundle,c['main']['manifestSha256']);require(verified.manifest_sha256==c['bootstrapManifestSha256'],'BASELINE_BOOTSTRAP_CHANGED')
        before=read_json(native/JOURNAL);item=target(native,before)
        retained={Path.home()/name:(Path.home()/name/JOURNAL).read_bytes() for name in v.RETAINED_INSTANCE_NAMES}
        with runtime_paths.installed_session(native):
            env=EnvironmentService(catalog=v.SignedVisionCatalog(verified),vm_profile=v.VM_PROFILE);vm=VMService(env)
            units=UnitService(vm);config=load_configuration(native)
            shared=[Path(config['cloudProfiles'][name]['credential']) for name in ('oem-delivery','service-provider')]
            require(all(p.is_file() and not p.is_symlink() and not p.is_relative_to(native) for p in shared),'SHARED_CREDENTIAL_MUST_BE_PRESERVED_OUTSIDE_DISPOSABLE_ROOT')
            shared_stamps={p:(p.stat().st_ino,p.stat().st_size,p.stat().st_mtime_ns) for p in shared}
            observed=units._cloud('read',unitId=OLD_UNIT)['unit']
            require(observed and observed['system_uid']==item['systemUid'] and observed['online_status']=='Offline'
                and observed['unit_sets']==[item['unitSetId']] and len(observed['nodes'])==1
                and observed['nodes'][0]['id']==OLD_NODE,'OLD_CLOUD_SCOPE_CHANGED')
            # Only checkpoint children of this exact disposable factory may go.
            factory=native/before['factory']['path'];checkpoints=[]
            for path in sorted(Path(c['remoteRoot']).rglob('*.qcow2')):
                require(not path.is_symlink(),'CHECKPOINT_LINKED')
                info=env._info(path)
                if info.get('full-backing-filename')==str(factory):
                    require(path.is_file() and path.stat().st_uid==os.getuid(),'CHECKPOINT_NOT_OWNED')
                    env._assert_unheld(path);checkpoints.append(path)
            env._assert_unheld(native/item['overlay']);env._assert_unheld(factory)
            record('retirement-scope.json',dict(unitId=OLD_UNIT,nodeId=OLD_NODE,vmId=OLD_VM,instance=str(native),
                checkpointChildren=[str(p) for p in checkpoints],sharedCredentialsOutsideTarget=True,retainedInstances=list(v.RETAINED_INSTANCE_NAMES)))
            phase('deprovision',lambda:units.execute('deprovision','test'))
            phase('delete-unit',lambda:units.execute('delete','test'))
            state=read_json(native/JOURNAL);require(units.confirm_retired(state,roles=('test',)),'RETIREMENT_ABSENCE_REQUIRED')
            record('checkpoint-removal-intent.json',dict(paths=[str(p) for p in checkpoints],irreversible=True))
            for path in checkpoints:
                env._assert_unheld(path);path.unlink();result['removed'].append(str(path))
            phase('retire-local-run',lambda:env.retire(lambda state:units.confirm_retired(state,roles=('test',))))
        # All native lifecycle owners have completed. Remove only the remaining
        # disposable selection/config/Source state, not its external package.
        require(native==Path('/Users/alexagizim')/INSTANCE and not native.is_symlink(),'ROOT_CHANGED')
        held=subprocess.run(['/usr/sbin/lsof','-t','+D',str(native)],capture_output=True,text=True,timeout=20)
        require(held.returncode==1 and not held.stdout,'DISPOSABLE_ROOT_HAS_OPEN_HANDLE')
        entries=list(native.rglob('*'))
        require(all(not p.is_mount() and p.lstat().st_uid==os.getuid() for p in entries),'FOREIGN_OR_MOUNTED_DISPOSABLE_CONTENT')
        record('instance-removal-intent.json',dict(path=str(native),oldUnitAbsent=True,entryCount=len(entries),irreversible=True))
        shutil.rmtree(native);result['removed'].append(str(native))
        result['cleanup']['sharedCredentialsPreserved']=all(p.is_file() and (p.stat().st_ino,p.stat().st_size,p.stat().st_mtime_ns)==stamp for p,stamp in shared_stamps.items())
        result['cleanup']['oldInstanceAbsent']=not native.exists()
        result['outcome']='PASS_DISPOSABLE_VISION_RETIRED'
    except Exception as error:
        import traceback
        value=str(error);frame=traceback.extract_tb(error.__traceback__)[-1]
        result.update(code=value if re.fullmatch('[A-Z][A-Z0-9_:,.-]{1,160}',value) else type(error).__name__,failureFile=Path(frame.filename).name,failureLine=frame.lineno)
    finally:
        result['cleanup']['retainedJournalsUnchanged']=bool(retained) and all((p/'.run/demo-current/journal.json').read_bytes()==raw for p,raw in retained.items())
        if native.exists():
            journal=native/'.run/demo-current/journal.json'
            result['cleanup']['oldVmStopped']=not journal.exists() or read_json(journal)['vehicles']['test']['runtime']['state']=='STOPPED'
        else:result['cleanup']['oldVmStopped']=True
        if not all(result['cleanup'].values()):result['outcome']='NOT_COMPLETE'
        result['seconds']=round(time.monotonic()-began,2);record('result.json',result);print(json.dumps(result),flush=True)
    return 0 if result['outcome']=='PASS_DISPOSABLE_VISION_RETIRED' else 1


if __name__=='__main__':raise SystemExit(main())
