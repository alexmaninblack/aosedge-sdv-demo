#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Reject only the accepted failed batch while the recovered VM stays stopped."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import time


def require(ok,code):
    if not ok:raise ValueError(code)


def main():
    context=Path(sys.argv[1]);c=json.loads(context.read_bytes());records=context.parent
    require(not (records/'result.json').exists(),'ATTEMPT_EXISTS_RECONCILE')
    def record(name,value):
        p=records/name;p.write_text(json.dumps(value,indent=2)+'\n');p.chmod(0o600)
    result=dict(scenario='VISION_FAILED_ROOTFS_BATCH_REJECTION',outcome='NOT_COMPLETE',cleanup={},
                runtimeStarted=False,rejectionAttempted=False)
    began=time.monotonic();retained={};native=None
    try:
        package=Path(c['main']['packageRoot']);bundle=Path(c['bundle'])
        require(hashlib.sha256((package/'application-manifest.json').read_bytes()).hexdigest()==c['main']['manifestSha256'],'BASE_CHANGED')
        for name,pin in c['files'].items():require(hashlib.sha256((records/name).read_bytes()).hexdigest()==pin,'REJECTION_INPUT_CHANGED')
        subprocess.run(['codesign','--verify','--deep','--strict','-R',
            '=identifier "org.aosedge.sdvlab.vision.bootstrap" and anchor apple generic and certificate leaf[subject.OU] = "3NF57VKB3V"',
            str(bundle)],check=True,capture_output=True,timeout=120)
        sys.path.insert(0,str(package/'aosedge-sdv-demo/apps/demo-orchestrator/src'))
        import aosedge_demo_orchestrator
        from aosedge_demo_orchestrator import runtime_paths
        tooling=bundle/'Contents/Resources/tooling/aosedge-sdv-demo/apps/demo-orchestrator/src'
        aosedge_demo_orchestrator.__path__.insert(0,str(tooling/'aosedge_demo_orchestrator'))
        from aosedge_demo_orchestrator import vision_bootstrap as v
        from aosedge_demo_orchestrator.environment import JOURNAL
        from aosedge_demo_orchestrator.status import load_configuration,read_json
        from aosedge_demo_orchestrator.cloud_connection import cloud_binding,selected_domain
        from aosedge_demo_orchestrator.cloud_runtime import launch
        verified=v.verify(bundle,c['main']['manifestSha256']);require(verified.manifest_sha256==c['bootstrapManifestSha256'],'BOOTSTRAP_CHANGED')
        native=Path.home()/v.INSTANCE_NAME;before=(native/JOURNAL).read_bytes();j=json.loads(before);item=j['vehicles']['test']
        require(item['runtime']['state']==j['source']['state']=='STOPPED','RECOVERED_IDLE_VISION_REQUIRED')
        retained={Path.home()/name:(Path.home()/name/JOURNAL).read_bytes() for name in v.RETAINED_INSTANCE_NAMES}
        recovered=read_json(Path(c['recoveredAttempt'])/'result.json')
        require(recovered['outcome']=='PASS_NATIVE_UNCONFIRMED_TRIAL_REVERT' and all(recovered['cleanup'].values()),'NATIVE_RECOVERY_REQUIRED')
        with runtime_paths.installed_session(native):
            config=load_configuration(native);sdk,sdk_env=launch(native,config['cloudPython'],'unit_cloud.py')
            request=dict(oemCredential=str(config['cloudProfiles']['oem-delivery']['credential']),
                oemOwner=cloud_binding(j)['ownerId'],cloudDomain=selected_domain(j),operationDirectory=str(records),
                rejectFailedRootfs=c['rejectFailedRootfs'],vehicles=dict(test={k:item[k] for k in ('unitId','nodeId','systemUid','unitSetId')}))
            request['vehicles']['test']['nodeHardwareId']=item['cloud']['identity']['nodeHardwareId']
            result['rejectionAttempted']=True
            done=subprocess.run([sdk[0],'-I','-B',str(records/'vision_permanent_cloud.py'),str(tooling)],
                input=json.dumps(request),env=sdk_env,text=True,capture_output=True,timeout=90)
            require(done.returncode==0,'REJECTION_SDK_FAILED');value=json.loads(done.stdout);record('sdk-result.json',value)
            require(value.get('ok') and value['data']['confirmed'],'REJECTION_NOT_CONFIRMED_NO_REPLAY')
        result['outcome']='PASS_FAILED_ROOTFS_BATCH_REJECTED';result['batch']=value['data']['batch']
        result['cleanup']['visionJournalUnchanged']=(native/JOURNAL).read_bytes()==before
    except Exception as error:
        value=str(error);result['code']=value if re.fullmatch('[A-Z][A-Z0-9_:,.-]{1,160}',value) else type(error).__name__
    finally:
        if native is not None:
            state=json.loads((native/JOURNAL).read_bytes())
            result['cleanup'].update(visionStopped=state['vehicles']['test']['runtime']['state']=='STOPPED',
                sourceStopped=state['source']['state']=='STOPPED',
                retainedJournalsUnchanged=all((p/JOURNAL).read_bytes()==raw for p,raw in retained.items()))
        if not result['cleanup'] or not all(result['cleanup'].values()):result['outcome']='NOT_COMPLETE'
        result['seconds']=round(time.monotonic()-began,2);record('result.json',result);print(json.dumps(result),flush=True)
    return 0 if result['outcome']=='PASS_FAILED_ROOTFS_BATCH_REJECTED' else 1


if __name__=='__main__':raise SystemExit(main())
