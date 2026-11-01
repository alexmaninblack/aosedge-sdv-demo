#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""One M4 retained-Vision native Camera campaign, including bounded collection."""
import argparse
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import time

import remote_harness as h
from vision_vm_campaign import configuration


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config',type=Path,required=True)
    p.add_argument('--name',required=True)
    p.add_argument('--bundle-remote',required=True)
    p.add_argument('--bootstrap-manifest',required=True)
    p.add_argument('--probe',type=Path,required=True)
    p.add_argument('--resume',choices=('native-camera-02',))
    p.add_argument('--transient-sm',type=Path)
    p.add_argument('--repair-store-labels',action='store_true')
    p.add_argument('--reconcile-stop',choices=('native-camera-04',))
    p.add_argument('--reuse-camera-publication',action='store_true')
    p.add_argument('--source-proof',action='store_true')
    p.add_argument('--resource-policy',type=Path)
    p.add_argument('--probe-resume',choices=('native-camera-09',))
    p.add_argument('--probe-cycle',type=int,choices=(1,2),default=1)
    p.add_argument('--consumer-only',action='store_true')
    p.add_argument('--reuse-probe-read',choices=('native-camera-12',))
    p.add_argument('--retry-probe-build',choices=('native-camera-14',))
    p.add_argument('--correct-probe-title',choices=('native-camera-15',))
    a=p.parse_args();c=configuration(a.config);t=c['transport'];q=shlex.quote
    h.require(not a.repair_store_labels or a.transient_sm is not None,'LABEL_PROOF_REQUIRES_TRANSIENT_CONTEXT')
    h.require(a.name.startswith('native-camera-') and a.name.removeprefix('native-camera-').isdecimal(),'ATTEMPT_NAME_INVALID')
    root=Path(c['records'])/a.name;remote=Path(c['remoteRoot'])/a.name
    h.require(not root.exists(),'ATTEMPT_EXISTS_RECONCILE');root.mkdir(mode=0o700)
    here=Path(__file__).resolve().parent
    context=dict(main=c['main'],bundle=a.bundle_remote,bootstrapManifestSha256=a.bootstrap_manifest,
        probeSha256=h.digest(a.probe),fixtureWorkerSha256=h.digest(here/'vision_camera_fixture_cloud.py'),
        probeCycle=a.probe_cycle,consumerOnly=a.consumer_only)
    h.require(not a.consumer_only or (a.reuse_camera_publication and (a.probe_resume or a.retry_probe_build or a.correct_probe_title)),'CONSUMER_ONLY_RETAINED_SCOPE_REQUIRED')
    h.require(not a.retry_probe_build or (a.name=='native-camera-15' and a.consumer_only and not a.probe_resume
        and not a.resource_policy and not a.transient_sm and a.probe_cycle==1),'TERMINAL_RETRY_SCOPE_INVALID')
    h.require(not a.correct_probe_title or (a.name in ('native-camera-16','native-camera-17') and a.consumer_only and not a.probe_resume
        and not a.retry_probe_build and not a.resource_policy and not a.transient_sm and a.probe_cycle==1),'TITLE_CORRECTION_SCOPE_INVALID')
    if a.resume:context['resumeFrom']=str(remote.parent/a.resume)
    if a.probe_resume:context['probeResumeFrom']=str(remote.parent/a.probe_resume)
    if a.reuse_probe_read:context['probeReadReuseFrom']=str(remote.parent/a.reuse_probe_read)
    if a.retry_probe_build:context['probeBuildRetryFrom']=str(remote.parent/a.retry_probe_build)
    if a.correct_probe_title:
        diagnosis=json.loads((Path(c['records'])/'cloud-build-diagnostic-01.json').read_bytes())
        h.require(diagnosis['signaturesVerified'] and diagnosis['payloadFilesIdentical']
            and diagnosis['newTitleAlreadyUsedByRetainedService'] and diagnosis['newServiceAbsent']
            and diagnosis['visionUnitHasNoBrakeTireVdpAssignment'],'TITLE_DIAGNOSIS_REQUIRED')
        context['probeTitleCorrectionFrom']=str(remote.parent/a.correct_probe_title)
    files=[here/'vision_camera_native_worker.py',here/'vision_camera_fixture_cloud.py',a.probe]
    if a.resource_policy:
        record=json.loads((a.resource_policy.parent/'result.json').read_bytes())
        h.require(record['outcome']=='PASS_TARGETED_RESOURCE_POLICY_COMPILE' and h.digest(a.resource_policy)==record['sha256'],'RESOURCE_POLICY_GATE_REQUIRED')
        loader=Path('/Volumes/SDV-Dev/sdv/build/vision-bootstrap/0.1.0/evidence/camera-store-policy-loader-01/vision-policy-load')
        context['resourcePolicy']={f.name:h.digest(f) for f in (a.resource_policy,loader,here/'vision_camera_resource_guest.py')}
        files.extend([a.resource_policy,loader,here/'vision_camera_resource_guest.py'])
    proof_files=[]
    if a.source_proof:
        source=here.parents[1]/'apps/demo-orchestrator/src/aosedge_demo_orchestrator'
        proof_files=[source/n for n in ('vm.py','source.py','vision_source_guest.py','vision_first_enrollment.py')]
        context['sourceProof']={f.name:h.digest(f) for f in proof_files}
    if a.transient_sm:
        h.require(a.transient_sm.name=='aos-sm-profile-proof','TRANSIENT_BINARY_NAME_INVALID')
        context['transientSm']=dict(sha256=h.digest(a.transient_sm));files.append(a.transient_sm)
        context['repairStoreLabels']=a.repair_store_labels
    h.atomic(root/'context.json',context);files.append(root/'context.json')
    python=c['main']['packageRoot']+'/demo-artifacts/aosedge-sdv-demo/host-runtime/python/bin/python3.12'
    if a.correct_probe_title and a.name=='native-camera-17':
        check='''import json,pathlib
p=pathlib.Path(PREVIOUS);r=json.loads((p/'result.json').read_bytes());c=json.loads((p/'context.json').read_bytes())
assert r['code']=='ModuleNotFoundError' and all(r['cleanup'].values())
assert c['bootstrapManifestSha256']==MANIFEST and c['probeSha256']==PROBE
assert not (p/'probe-sign-0.1.0.json').exists() and not (p/'probe-upload-0.1.0-intent.json').exists()
print(json.dumps(dict(previousStopped=True,noCorrectedSigningOrUpload=True)))
'''.replace('PREVIOUS',repr(str(remote.parent/'native-camera-16'))).replace('MANIFEST',repr(a.bootstrap_manifest)).replace('PROBE',repr(context['probeSha256']))
        reconciled=json.loads(h.remote(t,q(python)+' -I -B -c '+q(check),timeout=15))
        h.atomic(root/'previous-tooling-failure-reconciled.json',reconciled)
    if a.reuse_camera_publication:
        h.require(not a.resume,'PUBLICATION_REUSE_SCOPE_INVALID')
        code="""import json,pathlib,subprocess
p=pathlib.Path.home()/'SDV-Vision-Native-Lab-Data/.run/demo-current/journal.json'
s=json.loads(p.read_bytes());r=s['componentOperations']['0.1.0'];u=r['upload']['response']
assert u['httpStatus']==201 and u['deploymentId']==r['deploymentId']
b=pathlib.Path(BUNDLE)
requirement='=identifier "org.aosedge.sdvlab.vision.bootstrap" and anchor apple generic and certificate leaf[subject.OU] = "3NF57VKB3V"'
subprocess.run(['codesign','--verify','--deep','--strict','-R',requirement,str(b)],check=True,capture_output=True,timeout=120)
m=json.loads((b/'Contents/Resources/bootstrap.json').read_bytes())
print(json.dumps(dict(deploymentId=u['deploymentId'],ownerId=r['ownerId'],cloudDomain=r['cloudDomain'],payloadSha256=m['cameraPayload']['sha256'])))
""".replace('BUNDLE',repr(str(Path(c['remoteRoot'])/'native-camera-02/AosEdge Vision Bootstrap 0.1.2.bundle')))
        context['existingPublication']=json.loads(h.remote(t,q(python)+' -I -B -c '+q(code),timeout=135))
        h.atomic(root/'context.json',context)
    if a.reconcile_stop:
        code="""import json,pathlib,sys
p=pathlib.Path(PREVIOUS);r=json.loads((p/'result.json').read_bytes());c=json.loads((p/'context.json').read_bytes())
assert r['cleanup']['sourceStopped'] is True and r['cleanup']['stockSmRestored'] is True and r['cleanup']['retainedJournalsUnchanged'] is True
package=pathlib.Path(c['main']['packageRoot']);bundle=pathlib.Path(c['bundle'])
sys.path.insert(0,str(package/'aosedge-sdv-demo/apps/demo-orchestrator/src'))
import aosedge_demo_orchestrator
from aosedge_demo_orchestrator import runtime_paths
aosedge_demo_orchestrator.__path__.insert(0,str(bundle/'Contents/Resources/tooling/aosedge-sdv-demo/apps/demo-orchestrator/src/aosedge_demo_orchestrator'))
from aosedge_demo_orchestrator import vision_bootstrap as v
from aosedge_demo_orchestrator.environment import EnvironmentService
from aosedge_demo_orchestrator.vm import VMService
b=v.verify(bundle,c['main']['manifestSha256'])
with runtime_paths.installed_session(pathlib.Path.home()/v.INSTANCE_NAME):
 vm=VMService(EnvironmentService(catalog=v.SignedVisionCatalog(b),vm_profile=v.VM_PROFILE))
 value=vm.execute('stop','test',timeout=150)
 assert value['vehicles']['test']['state']=='COMPLETED'
 print(json.dumps(dict(normalStopReconciled=True,facts=value['vehicles']['test'])))
""".replace('PREVIOUS',repr(str(remote.parent/a.reconcile_stop)))
        observed=json.loads(h.remote(t,q(python)+' -I -B -c '+q(code),timeout=165))
        h.atomic(root/'previous-normal-stop-reconciled.json',observed)
    h.remote(t,'umask 077\nmkdir '+q(str(remote)),timeout=15)
    options=h.ssh_args(t)[1:-1];options.remove('-T');i=options.index('-b')
    options[i:i+2]=['-o','BindAddress='+options[i+1]]
    h.run(['/usr/bin/scp',*options,*map(str,files),t['user']+'@'+t['host']+':'+str(remote)+'/'],timeout=90)
    if proof_files:
        h.remote(t,'umask 077\nmkdir '+q(str(remote/'source-proof')),timeout=10)
        h.run(['/usr/bin/scp',*options,*map(str,proof_files),t['user']+'@'+t['host']+':'+str(remote/'source-proof')+'/'],timeout=30)
    command=q(python)+' -I -B '+q(str(remote/'vision_camera_native_worker.py'))+' --context '+q(str(remote/'context.json'))
    started=time.monotonic();process=subprocess.Popen(h.ssh_args(t)+[command],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    with (root/'progress.jsonl').open('x') as log:
        for line in process.stdout:
            h.require(log.tell()<2**20,'PROGRESS_LIMIT');log.write(line);log.flush()
            if line.startswith('{'):print(line.strip(),flush=True)
    code=process.wait(timeout=10);diagnostic=process.stderr.read(8192)
    collect="""import json,pathlib
p=pathlib.Path(REMOTE)
names=['result.json','camera-native-health.json','failure-diagnostics.json','native-reader.json','native-revocation.json','resource-policy-rollback.json','native-cold-restart.json']
print(json.dumps({n:json.loads((p/n).read_bytes()) for n in names if (p/n).is_file()}))
""".replace('REMOTE',repr(str(remote)))
    observed=json.loads(h.remote(t,q(python)+' -I -B -c '+q(collect),timeout=20))
    for name,value in observed.items():h.atomic(root/name,value)
    result=observed.get('result.json',dict(outcome='UNCERTAIN',code='WORKER_RESULT_MISSING'))
    h.atomic(root/'transport.json',dict(exit=code,seconds=round(time.monotonic()-started,2),stderrPresent=bool(diagnostic)))
    print(json.dumps(result),flush=True)
    return code


if __name__=='__main__':raise SystemExit(main())
