#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""One authenticated, visible M4 camera/CPU-VM engineering scenario."""
import argparse
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import sys
import time

import remote_harness as h
from vision_vm_campaign import configuration,HERE,SOURCE


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--config',type=Path,required=True)
    p.add_argument('--vm-proof',type=Path,required=True);p.add_argument('--seconds',type=int,default=120)
    p.add_argument('--resume-calibration',action='store_true')
    p.add_argument('--diagnose-replay',action='store_true')
    p.add_argument('--resume-input',action='store_true')
    a=p.parse_args();c=configuration(a.config);t=c['transport'];q=shlex.quote
    h.require(60<=a.seconds<=180,'LIVE_DURATION_INVALID')
    h.require(sum((a.resume_calibration,a.diagnose_replay,a.resume_input))<=1,'LIVE_MODE_INVALID')
    proof=json.loads(a.vm_proof.read_bytes())
    h.require(a.vm_proof.is_relative_to(Path(c['records'])) and proof['outcome']=='PASS_VM_ONLY'
              and proof['mainIdentityPreserved'] and proof['ownRuntimeStopped'] and proof['visionRoot']==c['visionRoot'],'VM_PROOF_REQUIRED')
    vm_id=proof.get('resumedExistingVm') or next(v['facts']['localVmId'] for v in proof['phases'] if v['stage']=='manufacture')
    print(h.run([sys.executable,'-B',str(HERE.parent/'docs-check')],timeout=30).strip(),flush=True)
    if a.resume_calibration:
        previous=json.loads((Path(c['records'])/'live-camera-01/live-result.json').read_bytes())
        h.require(previous.get('code')=='CALIBRATION_SINGULAR' and all(previous['cleanup'][v] for v in
            ('sourceStopped','vmStopped','awakeHelperClosed','mainIdentityPreserved','listenersReleased','inferenceThreadExited')),'CALIBRATION_ATTEMPT_NOT_RECONCILED')
    if a.resume_input:
        prior=json.loads((Path(c['records'])/'live-diagnostic-01/live-result.json').read_bytes())
        h.require(prior['outcome']=='PASS_REPLAY_DIAGNOSTIC' and all(prior['cleanup'].values()),'LIVE_REPLAY_PROOF_REQUIRED')
    name='live-camera-03' if a.resume_input else 'live-diagnostic-01' if a.diagnose_replay else 'live-camera-02' if a.resume_calibration else 'live-camera-01'
    records=Path(c['records'])/name;remote=Path(c['remoteRoot'])/name
    records.mkdir(mode=0o700,parents=True,exist_ok=True)
    files=[HERE/name for name in ('vision_live_worker.py','vision_live_guest.py','vision_live_contract.py','vision_model_probe.py','vision_camera.py')]
    delta=[SOURCE/name for name in ('environment.py','vm.py','vm_profiles.py')]
    context=dict(c['main'],retainedRoot=c['main']['instanceRoot'],retainedTest=c['retainedTest'],
        visionRoot=c['visionRoot'],visionTest=vm_id,liveSeconds=a.seconds,
        cameraWheels='/Users/'+t['user']+'/SDV-Qualification/m4-camera-baseline-20261030/wheels',
        proofFiles={**{f.name:h.digest(f) for f in files},**{'delta/'+f.name:h.digest(f) for f in delta}})
    identity=hashlib.sha256(json.dumps(context,sort_keys=True).encode()).hexdigest()
    started=time.monotonic();result=dict(scenario='VISION_LIVE_CPU_PREVIEW',outcome='NOT_COMPLETE',fullE2E='NOT_RUN')
    with h.Journal(records/'actions',identity) as journal:
        h.require(not h.read_attempts(journal.root),'LIVE_ATTEMPT_EXISTS_RECONCILE_REQUIRED')
        attempt=journal.begin('vision-live-preview')
        try:
            options=h.ssh_args(t)[1:-1];options.remove('-T');i=options.index('-b');options[i:i+2]=['-o','BindAddress='+options[i+1]]
            h.remote(t,'set -eu\numask 077\nmkdir '+q(str(remote))+'\nmkdir '+q(str(remote/'delta'))+'\n',timeout=10)
            h.atomic(records/'context.json',context)
            h.run(['/usr/bin/scp',*options,*map(str,files),str(records/'context.json'),t['user']+'@'+t['host']+':'+str(remote)+'/'],timeout=20)
            h.run(['/usr/bin/scp',*options,*map(str,delta),t['user']+'@'+t['host']+':'+str(remote/'delta')+'/'],timeout=15)
            python=c['main']['packageRoot']+'/demo-artifacts/aosedge-sdv-demo/host-runtime/python/bin/python3.12'
            verify='import hashlib,pathlib;assert hashlib.sha256(pathlib.Path('+repr(str(remote/'vision_live_worker.py'))+').read_bytes()).hexdigest()=='+repr(context['proofFiles']['vision_live_worker.py'])
            h.remote(t,q(python)+' -I -B -c '+q(verify),timeout=10)
            attempt['dispatched']=True;h.atomic(journal.root/'attempt-0001.json',attempt)
            with (records/'progress.jsonl').open('w') as log,(records/'worker-diagnostic.log').open('w') as error:
                command=q(python)+' -I -B '+q(str(remote/'vision_live_worker.py'))+' --context '+q(str(remote/'context.json'))
                process=subprocess.Popen(h.ssh_args(t)+[command],stdout=subprocess.PIPE,stderr=error,text=True)
                for line in process.stdout:
                    h.require(log.tell()<2*1024**2,'LIVE_PROGRESS_LIMIT');log.write(line);log.flush()
                    if line.startswith('{'):print(line.strip(),flush=True)
                code=process.wait(timeout=15)
            raw=h.remote(t,q(python)+' -I -B -c '+q('import pathlib;print(pathlib.Path('+repr(str(remote/'result.json'))+').read_text())'),timeout=10)
            value=json.loads(raw);h.atomic(records/'live-result.json',value);result.update(value)
            outcome='PASS' if code==0 and value['outcome'] in ('PASS_LIVE_ENGINEERING_PREVIEW','PASS_REPLAY_DIAGNOSTIC') else 'UNCERTAIN'
            journal.finish(attempt,outcome,'LIVE_PREVIEW_COMPLETE' if outcome=='PASS' else value.get('code','LIVE_PREVIEW_NOT_COMPLETE'),dict(facts=value))
            names=['result.json','calibration.json','frame-metrics.json','diagnostic-response.json',*value.get('screenshots',[])]
            safe=[name for name in names if Path(name).name==name]
            for name in safe:
                try:h.run(['/usr/bin/scp',*options,t['user']+'@'+t['host']+':'+str(remote/name),str(records/name)],timeout=10)
                except h.Error:pass
        except Exception as error:
            message=str(error);result['code']=message if message.isupper() and message.replace('_','').isalnum() else type(error).__name__
        finally:
            result['campaignSeconds']=round(time.monotonic()-started,2);h.atomic(records/'campaign-result.json',result);print(json.dumps(result),flush=True)
    return 0 if result['outcome'] in ('PASS_LIVE_ENGINEERING_PREVIEW','PASS_REPLAY_DIAGNOSTIC') else 1


if __name__=='__main__':raise SystemExit(main())
