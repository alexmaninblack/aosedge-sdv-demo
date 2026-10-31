#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Engineering model replay under real M4 camera load; not Vision E2E."""
import argparse
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import time

import remote_harness as h
from vision_vm_campaign import configuration,SOURCE,HERE


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('config','inputs','receipt','vm-proof'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--resume-capture',action='store_true')
    p.add_argument('--resume-replay',action='store_true',help='Reuse the reconciled second attempt recording; no recapture')
    p.add_argument('--resume-model-shape',action='store_true',help='Reconcile the pinned export batch metadata mismatch')
    p.add_argument('--steady',action='store_true',help='Sustained load after successful bounded model execution')
    a=p.parse_args();c=configuration(a.config);t=c['transport'];q=shlex.quote
    h.require(sum((a.resume_capture,a.resume_replay,a.resume_model_shape,a.steady))<=1,'RESUME_MODE_INVALID')
    proof=json.loads(a.vm_proof.read_bytes())
    h.require(proof['outcome']=='PASS_VM_ONLY' and proof['ownRuntimeStopped'] and proof['mainIdentityPreserved']
              and proof['visionRoot']==c['visionRoot'],'PASSED_VM_PROOF_REQUIRED')
    h.require(a.vm_proof.is_relative_to(Path(c['records'])),'VM_PROOF_SCOPE_INVALID')
    vm_id=proof.get('resumedExistingVm') or next(r['facts']['localVmId'] for r in proof['phases'] if r['stage']=='manufacture')
    inputs=json.loads(a.receipt.read_bytes())
    h.require(inputs['kind']=='ENGINEERING_MODEL_PROBE_NOT_AOS_PACKAGE' and inputs['file']==a.inputs.name
              and a.inputs.stat().st_size==inputs['bytes'],'MODEL_INPUT_RECEIPT_INVALID')
    gate=h.run([__import__('sys').executable,'-B',str(HERE.parent/'docs-check')],timeout=30)
    print(gate.strip(),flush=True)
    records=Path(c['records'])/'model-compute';remote=Path(c['remoteRoot'])/'model-compute';previous_remote=remote
    if a.resume_capture or a.resume_replay or a.resume_model_shape or a.steady:
        previous_name='compute-model-shape' if a.steady else 'compute-replay' if a.resume_model_shape else 'compute-continuation' if a.resume_replay else ''
        previous_remote=remote/previous_name
        previous_root=records/previous_name
        previous=json.loads((previous_root/'result.json').read_bytes())
        expected='MODEL_EXECUTION_NOT_COMPLETE' if a.resume_model_shape else 'FRAME_PAIR_INTERVAL_INVALID'
        h.require(all(previous['cleanup'].values()) and
                  (previous['outcome']=='PASS_ENGINEERING_TENSOR_TIMING_ONLY' if a.steady else
                   previous['outcome']=='NOT_COMPLETE' and previous.get('modelResult',{}).get('code')==expected),'PREVIOUS_COMPUTE_NOT_RECONCILED')
        if a.resume_model_shape:
            observations=[json.loads(v) for v in (previous_root/'progress.jsonl').read_text().splitlines() if v.startswith('{')]
            h.require(any(v.get('facts',{}).get('code')=='MODEL_INPUT_SHAPE_CHANGED' for v in observations),'PREVIOUS_MODEL_SHAPE_NOT_OBSERVED')
        name='compute-steady' if a.steady else 'compute-model-shape' if a.resume_model_shape else 'compute-replay' if a.resume_replay else 'compute-continuation'
        records=records/name;remote=remote/name
    records.mkdir(mode=0o700,parents=True,exist_ok=True)
    files=[HERE/name for name in ('vision_compute_worker.py','vision_camera.py','vision_model_probe.py')]
    delta=[SOURCE/name for name in ('environment.py','vm.py','vm_profiles.py')]
    context=dict(c['main'],retainedRoot=c['main']['instanceRoot'],retainedTest=c['retainedTest'],
        visionRoot=c['visionRoot'],visionTest=vm_id,inputs=inputs,
        cameraWheels='/Users/'+t['user']+'/SDV-Qualification/m4-camera-baseline-20261030/wheels',
        proofFiles={**{f.name:h.digest(f) for f in files},**{'delta/'+f.name:h.digest(f) for f in delta}})
    identity=hashlib.sha256(json.dumps(dict(config=c,context=context,resumeCapture=a.resume_capture,resumeReplay=a.resume_replay,resumeModelShape=a.resume_model_shape,steady=a.steady),sort_keys=True).encode()).hexdigest()
    result=dict(scenario='VISION_VM_MODEL_COMPUTE',outcome='NOT_COMPLETE',nativeAosDeployment='NOT_RUN',fullE2E='NOT_RUN')
    begin=time.monotonic()
    with h.Journal(records/'actions',identity) as journal:
        h.require(not h.read_attempts(journal.root),'MODEL_CAMPAIGN_EXISTS_RECONCILE_REQUIRED')
        attempt=journal.begin('vision-model-compute')
        try:
            options=h.ssh_args(t)[1:-1];options.remove('-T');i=options.index('-b')
            options[i:i+2]=['-o','BindAddress='+options[i+1]]
            h.remote(t,'set -eu\numask 077\nmkdir '+q(str(remote))+'\nmkdir '+q(str(remote/'delta'))+'\n',timeout=10)
            h.atomic(records/'context.json',context)
            resume=a.resume_capture or a.resume_replay or a.resume_model_shape or a.steady
            print(json.dumps(dict(stage='compute-input-transfer',state='REUSING_VERIFIED_INPUTS' if resume else 'STARTED',bytesToTransfer=0 if resume else inputs['bytes'])),flush=True)
            sent_files=[*map(str,files),str(records/'context.json')]+([] if resume else [str(a.inputs)])
            h.run(['/usr/bin/scp',*options,*sent_files,t['user']+'@'+t['host']+':'+str(remote)+'/'],timeout=60)
            h.run(['/usr/bin/scp',*options,*map(str,delta),t['user']+'@'+t['host']+':'+str(remote/'delta')+'/'],timeout=15)
            python=c['main']['packageRoot']+'/demo-artifacts/aosedge-sdv-demo/host-runtime/python/bin/python3.12'
            verify='import hashlib,pathlib; assert hashlib.sha256(pathlib.Path('+repr(str(remote/'vision_compute_worker.py'))+').read_bytes()).hexdigest()=='+repr(context['proofFiles']['vision_compute_worker.py'])
            h.remote(t,q(python)+' -I -B -c '+q(verify),timeout=10)
            attempt['dispatched']=True;h.atomic(journal.root/'attempt-0001.json',attempt)
            with (records/'progress.jsonl').open('w') as log:
                command=q(python)+' -I -B '+q(str(remote/'vision_compute_worker.py'))+' --context '+q(str(remote/'context.json'))
                if resume:command+=' --resume-from '+q(str(previous_remote/'result.json'))
                if a.resume_replay or a.resume_model_shape or a.steady:command+=' --reuse-sequence'
                process=subprocess.Popen(h.ssh_args(t)+[command],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
                for line in process.stdout:
                    h.require(log.tell()<2*1024**2,'PROGRESS_LIMIT');log.write(line);log.flush()
                    if line.startswith('{'):print(line.strip(),flush=True)
                diagnostic=process.stderr.read(16384);code=process.wait(timeout=15)
            raw=h.remote(t,q(python)+' -I -B -c '+q('import pathlib;print(pathlib.Path('+repr(str(remote/'result.json'))+').read_text())'),timeout=10)
            value=json.loads(raw);h.atomic(records/'compute-result.json',value)
            outcome='PASS' if code==0 and value['outcome']=='PASS_ENGINEERING_TENSOR_TIMING_ONLY' else 'UNCERTAIN'
            journal.finish(attempt,outcome,'ENGINEERING_COMPUTE_COMPLETE' if outcome=='PASS' else value.get('code','MODEL_COMPUTE_NOT_COMPLETE'),dict(facts=value))
            result.update(value)
        except Exception as error:
            message=str(error);result['code']=message if message.isupper() and len(message)<100 else type(error).__name__
        finally:
            result['campaignSeconds']=round(time.monotonic()-begin,2);h.atomic(records/'result.json',result)
            print(json.dumps(result),flush=True)
    return 0 if result['outcome']=='PASS_ENGINEERING_TENSOR_TIMING_ONLY' else 1


if __name__=='__main__':raise SystemExit(main())
