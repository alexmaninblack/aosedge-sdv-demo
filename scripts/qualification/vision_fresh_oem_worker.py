#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Empty-cohort gate/sign/upload with normal configured SDK; no VM starts."""
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
    require(not (records/'result.json').exists(),'FRESH_OEM_ATTEMPT_EXISTS_RECONCILE')
    def record(name,value):
        p=records/name;p.write_text(json.dumps(value,indent=2)+'\n');p.chmod(0o600)
    result=dict(scenario='VISION_FRESH_EMPTY_COHORT_OEM',outcome='NOT_COMPLETE',cloudMutation=False,cleanup={})
    began=time.monotonic();retained={}
    try:
        package=Path(c['main']['packageRoot']);bundle=Path(c['bundle'])
        require(hashlib.sha256((package/'application-manifest.json').read_bytes()).hexdigest()==c['main']['manifestSha256'],'BASE_CHANGED')
        for name,pin in c['files'].items():require(hashlib.sha256((records/name).read_bytes()).hexdigest()==pin,'FRESH_OEM_HELPER_CHANGED')
        subprocess.run(['codesign','--verify','--deep','--strict','-R',
            '=identifier "org.aosedge.sdvlab.vision.bootstrap" and anchor apple generic and certificate leaf[subject.OU] = "3NF57VKB3V"',str(bundle)],check=True,capture_output=True,timeout=120)
        sys.path.insert(0,str(package/'aosedge-sdv-demo/apps/demo-orchestrator/src'))
        import aosedge_demo_orchestrator
        from aosedge_demo_orchestrator import runtime_paths
        tooling=bundle/'Contents/Resources/tooling/aosedge-sdv-demo/apps/demo-orchestrator/src'
        aosedge_demo_orchestrator.__path__.insert(0,str(tooling/'aosedge_demo_orchestrator'))
        from aosedge_demo_orchestrator.status import read_json,load_configuration
        from aosedge_demo_orchestrator.cloud_connection import cloud_binding,selected_domain
        from aosedge_demo_orchestrator.cloud_runtime import launch
        names=('SDV-Lab-Data','SDV-Vision-Lab-Data','SDV-Vision-Native-Lab-Data','SDV-Vision-Camera-Lab-Data')
        retained={Path.home()/n:(Path.home()/n/'.run/demo-current/journal.json').read_bytes() for n in names}
        require(not (Path.home()/'SDV-Vision-Camera-Image-Lab-Data').exists(),'DISPOSABLE_ROOT_NOT_REMOVED')
        old=read_json(Path(c['retirement'])/'result.json')
        require(old['outcome']=='PASS_DISPOSABLE_VISION_RETIRED' and all(old['cleanup'].values()),'EXACT_RETIREMENT_REQUIRED')
        root=Path(c['main']['instanceRoot']);state=read_json(root/'.run/demo-current/journal.json')
        with runtime_paths.installed_session(root):
            config=load_configuration(root);sdk,environment=launch(root,config['cloudPython'],'unit_cloud.py')
        profiles=config['cloudProfiles']
        request=dict(credential=str(profiles['oem-delivery']['credential']),cloudDomain=selected_domain(state),
            ownerId=profiles['oem-delivery']['expectedOwnerId'],spCredential=str(profiles['service-provider']['credential']),
            spOwner=profiles['service-provider']['expectedOwnerId'],helperDirectory=str(records))
        def call(action,**extra):
            done=subprocess.run([sdk[0],'-I','-B',str(records/'vision_fresh_cloud.py'),str(tooling)],input=json.dumps(dict(request,action=action,**extra)),
                text=True,capture_output=True,env=environment,timeout=600)
            require(done.returncode==0,'FRESH_OEM_SDK_FAILED');value=json.loads(done.stdout)
            if not value.get('ok'):record('sdk-error.json',value);raise ValueError(value.get('reason','FRESH_OEM_SDK_FAILED'))
            return value['data']
        gate=call('gate');record('empty-gate.json',gate)
        if c['mode']=='publish':
            artifact=c['artifact'];payload=records/'vision-rootfs.squashfs'
            require(payload.stat().st_size==artifact['bytes'] and hashlib.sha256(payload.read_bytes()).hexdigest()==artifact['sha256'],'FROZEN_FIFTH_PAYLOAD_CHANGED')
            request.update(payload=str(payload),payloadBytes=artifact['bytes'],payloadSha256=artifact['sha256'],componentTitle=gate['componentTitle'])
            output=records/'rootfs-6.1.1-vision-camera.5.tar.gz';signed=call('sign',output=str(output));record('signed.json',signed)
            record('upload-intent.json',dict(attemptStarted=True,version='6.1.1-vision-camera.5',payloadSha256=artifact['sha256'],bundleSha256=signed['sha256'],recipientPolicy='ALL_VERIFICATION_SETS_EMPTY'))
            result['cloudMutation']=True
            upload=call('upload',bundle=str(output),expectedSha256=signed['sha256']);record('upload-response.json',upload)
            end=time.monotonic()+180;observed=None
            while time.monotonic()<end:
                observed=call('status',deploymentId=upload['deploymentId'])
                if observed['publication']['stage']=='READY':break
                require(observed['publication']['stage']=='PROCESSING','FRESH_PUBLICATION_FAILED');time.sleep(2)
            require(observed and observed['publication']['stage']=='READY','FRESH_PUBLICATION_TIMEOUT_RECONCILE')
            record('publication.json',observed);result.update(outcome='PASS_FRESH_FIFTH_PUBLISHED_EMPTY_COHORT',publication=observed['publication'])
        else:result.update(outcome='PASS_EMPTY_VISION_PUBLICATION_GATE',facts=gate)
    except Exception as error:
        import traceback
        frame=traceback.extract_tb(error.__traceback__)[-1];value=str(error)
        result.update(code=value if re.fullmatch('[A-Z][A-Z0-9_:,.-]{1,160}',value) else type(error).__name__,failureFile=Path(frame.filename).name,failureLine=frame.lineno)
    finally:
        result['cleanup']['retainedJournalsUnchanged']=bool(retained) and all((p/'.run/demo-current/journal.json').read_bytes()==raw for p,raw in retained.items())
        result['cleanup']['disposableRootAbsent']=not (Path.home()/'SDV-Vision-Camera-Image-Lab-Data').exists()
        if not all(result['cleanup'].values()):result['outcome']='NOT_COMPLETE'
        result['seconds']=round(time.monotonic()-began,2);record('result.json',result);print(json.dumps(result),flush=True)
    return 0 if result['outcome'].startswith('PASS_') else 1


if __name__=='__main__':raise SystemExit(main())
