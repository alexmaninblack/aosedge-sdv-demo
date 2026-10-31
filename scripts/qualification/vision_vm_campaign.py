#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""One fixed-profile M4 VM campaign; installed owners retain lifecycle authority."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import stat
import subprocess
import sys
import time

import remote_harness as h
import journey as j

HERE=Path(__file__).resolve().parent
SOURCE=HERE.parents[1]/'apps/demo-orchestrator/src/aosedge_demo_orchestrator'


def configuration(path):
    path=h.unlinked(path);info=path.stat()
    h.require(info.st_uid==os.getuid() and stat.S_IMODE(info.st_mode)==0o600 and info.st_size<32768,'VISION_CONFIG_NOT_PRIVATE')
    c=h.parse(path.read_bytes())
    h.require(set(c)=={'transport','main','retainedTest','visionRoot','remoteRoot','records','baseFiles'},'VISION_CONFIG_FIELDS_INVALID')
    t=c['transport'];home=Path('/Users')/t['user']
    h.require(t['host']=='192.168.247.4' and t['source']=='192.168.247.1','M4_TARGET_REQUIRED')
    h.require(c['visionRoot']==str(home/'SDV-Vision-Lab-Data') and c['remoteRoot']==str(home/'SDV-Qualification/vision-vm-m4'),'VISION_SCOPE_INVALID')
    h.require(c['visionRoot']!=c['main']['instanceRoot'],'RETAINED_INSTANCE_OVERLAP')
    h.require(Path(c['records']).is_absolute() and '/.local/remote-qualification/' in c['records'],'EVIDENCE_SCOPE_INVALID')
    h.require(c['main']['manifestSha256'] in c['main']['packageRoot'] and re.fullmatch('[a-f0-9]{64}',c['main']['manifestSha256']),'CANDIDATE_PIN_INVALID')
    h.require(set(c['baseFiles'])=={'environment.py','vm.py'},'BASE_PINS_REQUIRED')
    for file in ('key','knownHosts'):h.unlinked(t[file])
    key=Path(t['key']).stat()
    h.require(key.st_uid==os.getuid() and stat.S_IMODE(key.st_mode)==0o600,'SSH_KEY_PERMISSIONS_INVALID')
    matches=[]
    for line in Path(t['knownHosts']).read_text().splitlines():
        if not line.strip() or line.lstrip().startswith('#'):continue
        fields=line.split()
        if fields[0]==t['host']:matches.append(fields)
    h.require(len(matches)==1 and len(matches[0])==3 and matches[0][1]=='ssh-ed25519','HOST_PIN_INVALID')
    fp='SHA256:'+base64.b64encode(hashlib.sha256(base64.b64decode(matches[0][2],validate=True)).digest()).decode().rstrip('=')
    h.require(fp==t['fingerprint'],'HOST_PIN_CHANGED')
    return c


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--config',type=Path,required=True)
    parser.add_argument('--resume-guest',action='store_true')
    parser.add_argument('--continuation',type=int,default=1)
    args=parser.parse_args();c=configuration(args.config);t=c['transport'];q=shlex.quote
    print(h.run([sys.executable,'-B',str(HERE.parent/'docs-check')],timeout=30).strip(),flush=True)
    console=h.parse(sys.stdin.read(8193))
    h.require(isinstance(console,dict) and set(console)=={'password'} and isinstance(console['password'],str)
              and 0<len(console['password'])<1024 and not any(ch in console['password'] for ch in '\r\n\x00'),'CONSOLE_INPUT_INVALID')
    h.require(1<=args.continuation<=10 and (args.resume_guest or args.continuation==1),'CONTINUATION_INVALID')
    records=Path(c['records']);base_remote=Path(c['remoteRoot']);previous_remote=base_remote
    if args.resume_guest:
        previous_name='guest-continuation' if args.continuation==2 else 'guest-continuation-'+str(args.continuation-1)
        previous_records=records if args.continuation==1 else records/previous_name
        previous_remote=base_remote if args.continuation==1 else base_remote/previous_name
        prior=json.loads((previous_records/'vm-result.json').read_bytes())
        h.require(prior['outcome']=='NOT_COMPLETE' and prior.get('code') in ('GUEST_PROOF_FAILED','GUEST_OCI_EXECUTION_FAILED','GUEST_TIME_OUTSIDE_HOST_ENVELOPE')
                  and prior['ownRuntimeStopped'] is True,'PREVIOUS_VM_ATTEMPT_NOT_RECONCILED')
        records=records/('guest-continuation' if args.continuation==1 else 'guest-continuation-'+str(args.continuation))
    remote=base_remote/records.name if args.resume_guest else base_remote
    records.mkdir(parents=True,mode=0o700,exist_ok=True)
    identity=hashlib.sha256(json.dumps(dict(config=c,resume=args.resume_guest,continuation=args.continuation),sort_keys=True).encode()).hexdigest()
    result=dict(scenario='VISION_VM_M4',outcome='NOT_COMPLETE',modelExecution='NOT_RUN',fullE2E='NOT_RUN',phases=[])
    began=time.monotonic()
    with h.Journal(records/'actions',identity) as journal:
        h.require(not h.read_attempts(journal.root),'EXISTING_VISION_CAMPAIGN_RECONCILE_REQUIRED')
        try:
            python=c['main']['packageRoot']+'/demo-artifacts/aosedge-sdv-demo/host-runtime/python/bin/python3.12'
            check='''import hashlib,json,pathlib,shutil,subprocess
c='''+repr(c)+'''
resume='''+repr(args.resume_guest)+'''
remote='''+repr(str(remote))+'''
assert subprocess.check_output(['/usr/sbin/sysctl','-n','hw.model'],text=True).strip()=='Mac16,8','M4_MODEL_CHANGED'
assert shutil.disk_usage(pathlib.Path.home()).free>60*1024**3,'M4_CAPACITY_REQUIRED'
assert resume or not pathlib.Path(c['visionRoot']).exists(),'VISION_INSTANCE_EXISTS_RECONCILE_REQUIRED'
assert not pathlib.Path(remote).exists(),'VISION_REMOTE_ATTEMPT_EXISTS'
p=pathlib.Path(c['main']['packageRoot'])
assert hashlib.sha256((p/'application-manifest.json').read_bytes()).hexdigest()==c['main']['manifestSha256'],'CANDIDATE_CHANGED'
for name,pin in c['baseFiles'].items():assert hashlib.sha256((p/'aosedge-sdv-demo/apps/demo-orchestrator/src/aosedge_demo_orchestrator'/name).read_bytes()).hexdigest()==pin,'BASE_CHANGED'
v=json.loads((pathlib.Path(c['main']['instanceRoot'])/'.run/demo-current/journal.json').read_bytes())
assert v['vehicles']['test']['localVmId']==c['retainedTest'],'RETAINED_TEST_CHANGED'
assert not v['vehicles']['test'].get('unitId'),'RETAINED_BASELINE_SCOPE_CHANGED'
print('M4_VISION_PREFLIGHT_PASS')
'''
            print(json.dumps(dict(stage='preflight',state='STARTED')),flush=True)
            h.remote(t,q(python)+' -I -B -c '+q(check),timeout=20)
            print(json.dumps(dict(stage='preflight',state='COMPLETE')),flush=True)
            if not args.resume_guest:
                runner=j.Runner(journal,j.Remote(t,c['main']),emit=lambda x:print(x,flush=True))
                stopped=runner.run_step(dict(id='retained-main-stop',kind='shutdown',args={},timeout=150),dict(runId=c['retainedTest']))
                h.require(stopped['outcome']=='PASS',stopped['code'])
                result['phases'].append(dict(stage='retained-main-stop',outcome='PASS',persistentStatePreserved=True))
            options=h.ssh_args(t)[1:-1];options.remove('-T');i=options.index('-b')
            options[i:i+2]=['-o','BindAddress='+options[i+1]]
            h.remote(t,'set -eu\numask 077\nmkdir '+q(str(remote))+'\nmkdir '+q(str(remote/'delta'))+'\n',timeout=10)
            files=[HERE/'vision_vm_worker.py',HERE/'vision_vm_guest.py']
            delta=[SOURCE/name for name in ('environment.py','vm.py','vm_profiles.py')]
            context=dict(c['main'],retainedRoot=c['main']['instanceRoot'],retainedTest=c['retainedTest'],
                visionRoot=c['visionRoot'],baseFiles=c['baseFiles'],
                proofFiles={**{f.name:h.digest(f) for f in files},**{'delta/'+f.name:h.digest(f) for f in delta}})
            h.atomic(records/'context.json',context)
            h.run(['/usr/bin/scp',*options,*map(str,files),str(records/'context.json'),t['user']+'@'+t['host']+':'+str(remote)+'/'],timeout=20)
            h.run(['/usr/bin/scp',*options,*map(str,delta),t['user']+'@'+t['host']+':'+str(remote/'delta')+'/'],timeout=20)
            attempt=journal.begin('vision-vm-worker');attempt['dispatched']=True
            h.atomic(journal.root/('attempt-'+str(attempt['attempt']).zfill(4)+'.json'),attempt)
            with (records/'progress.jsonl').open('w') as log:
                command=q(python)+' -I -B '+q(str(remote/'vision_vm_worker.py'))+' --context '+q(str(remote/'context.json'))
                if args.resume_guest:command+=' --resume-from '+q(str(previous_remote/'result.json'))
                p=subprocess.Popen(h.ssh_args(t)+[command],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
                # Explicit Factory console input travels only in this SSH
                # stdin, never argv, environment, files or evidence.
                p.stdin.write(json.dumps(console));p.stdin.close();console.clear()
                for line in p.stdout:
                    h.require(log.tell()<1024**2,'PROGRESS_LIMIT')
                    log.write(line);log.flush()
                    if line.startswith('{'):print(line.strip(),flush=True)
                diagnostic=p.stderr.read(16384);code=p.wait(timeout=15)
            collected=h.remote(t,'test -f '+q(str(remote/'result.json'))+'\n'+q(python)+' -I -B -c '+q('import pathlib;print(pathlib.Path('+repr(str(remote/'result.json'))+').read_text())'),timeout=10)
            observed=json.loads(collected);h.atomic(records/'vm-result.json',observed)
            state='PASS' if code==0 and observed['outcome']=='PASS_VM_ONLY' else 'UNCERTAIN'
            journal.finish(attempt,state,'VISION_VM_COMPLETE' if state=='PASS' else observed.get('code','VISION_VM_NOT_COMPLETE'),dict(facts=observed))
            result.update(outcome=observed['outcome'],vmResult='vm-result.json',ownRuntimeStopped=observed.get('ownRuntimeStopped',False))
        except Exception as error:
            message=str(error);result['code']=message if re.fullmatch('[A-Z][A-Z0-9_]{1,100}',message) else type(error).__name__
        finally:
            result['seconds']=round(time.monotonic()-began,2);h.atomic(records/'result.json',result)
            print(json.dumps(result),flush=True)
    return 0 if result['outcome']=='PASS_VM_ONLY' else 1


if __name__=='__main__':raise SystemExit(main())
