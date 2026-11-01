#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Transfer a signed Vision bootstrap and run its isolated M4 scenario once."""
import argparse
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import sys
import time

import remote_harness as h
from vision_vm_campaign import configuration

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'apps/demo-orchestrator/src'))
from aosedge_demo_orchestrator import vision_bootstrap as v


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config',type=Path,required=True)
    p.add_argument('--bundle',type=Path,required=True)
    p.add_argument('--attempt',type=int,default=1)
    a=p.parse_args();c=configuration(a.config);t=c['transport'];q=shlex.quote
    verified=v.verify(a.bundle,c['main']['manifestSha256'])
    h.require(1<=a.attempt<=10,'ATTEMPT_INVALID')
    records=Path(c['records'])/('signed-bootstrap-'+str(a.attempt).zfill(2))
    remote=Path(c['remoteRoot'])/records.name
    h.require(not records.exists(),'LOCAL_ATTEMPT_EXISTS_RECONCILE')
    records.mkdir(mode=0o700)
    worker=Path(__file__).with_name('vision_bootstrap_worker.py')
    identity=h.digest(worker)+verified.manifest_sha256
    python=c['main']['packageRoot']+'/demo-artifacts/aosedge-sdv-demo/host-runtime/python/bin/python3.12'
    result=dict(scenario='VISION_SIGNED_BOOTSTRAP_M4',outcome='NOT_COMPLETE',phases=[])
    began=time.monotonic()
    def stage(name):
        print(json.dumps(dict(stage=name,state='STARTED')),flush=True)
    with h.Journal(records/'actions',hashlib.sha256(identity.encode()).hexdigest()) as journal:
        try:
            stage('m4-preflight')
            code='''import hashlib,pathlib,subprocess,shutil,json
c=CONTEXT
assert subprocess.check_output(['/usr/sbin/sysctl','-n','hw.model'],text=True).strip()=='Mac16,8'
assert shutil.disk_usage(pathlib.Path.home()).free>80*1024**3
p=pathlib.Path(c['main']['packageRoot'])
assert hashlib.sha256((p/'application-manifest.json').read_bytes()).hexdigest()==c['main']['manifestSha256']
assert not pathlib.Path(REMOTE).exists()
assert not (pathlib.Path.home()/'SDV-Vision-Camera-Lab-Data').exists()
for name in ('SDV-Lab-Data','SDV-Vision-Lab-Data','SDV-Vision-Native-Lab-Data'):
 state=json.loads((pathlib.Path.home()/name/'.run/demo-current/journal.json').read_bytes())
 assert all(i.get('runtime',{}).get('state')=='STOPPED' for i in state['vehicles'].values())
print('M4_SIGNED_BOOTSTRAP_PREFLIGHT_PASS')
'''.replace('CONTEXT',repr(c)).replace('REMOTE',repr(str(remote)))
            h.remote(t,q(python)+' -I -B -c '+q(code),timeout=20)
            h.remote(t,'umask 077\nmkdir '+q(str(remote)),timeout=10)
            context=dict(main=c['main'],bundle=str(remote/a.bundle.name),bootstrapManifestSha256=verified.manifest_sha256)
            h.atomic(records/'context.json',context)
            options=h.ssh_args(t)[1:-1];options.remove('-T');i=options.index('-b')
            options[i:i+2]=['-o','BindAddress='+options[i+1]]
            stage('transfer-signed-vision-bootstrap')
            h.run(['/usr/bin/scp','-C','-r',*options,str(a.bundle),str(worker),str(records/'context.json'),
                   t['user']+'@'+t['host']+':'+str(remote)+'/'],timeout=900)
            check='import hashlib,pathlib;assert hashlib.sha256(pathlib.Path('+repr(str(remote/worker.name))+').read_bytes()).hexdigest()=='+repr(h.digest(worker))
            h.remote(t,q(python)+' -I -B -c '+q(check),timeout=10)
            attempt=journal.begin('signed-bootstrap-worker');attempt['dispatched']=True
            h.atomic(journal.root/('attempt-'+str(attempt['attempt']).zfill(4)+'.json'),attempt)
            stage('m4-native-scenario')
            command=q(python)+' -I -B '+q(str(remote/worker.name))+' --context '+q(str(remote/'context.json'))
            process=subprocess.Popen(h.ssh_args(t)+[command],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            # Previously authorized, non-secret Factory console default. Never
            # an Apple/login password; not stored in a context, argv or report.
            process.stdin.write(json.dumps({'password':'Password1'}));process.stdin.close()
            with (records/'progress.jsonl').open('x') as log:
                for line in process.stdout:
                    h.require(log.tell()<2**20,'PROGRESS_LIMIT')
                    log.write(line);log.flush()
                    if line.startswith('{'):print(line.strip(),flush=True)
            diagnostic=process.stderr.read(8192);code=process.wait(timeout=20)
            raw=h.remote(t,q(python)+' -I -B -c '+q('import pathlib;print(pathlib.Path('+repr(str(remote/'result.json'))+').read_text())'),timeout=15)
            observed=json.loads(raw);h.atomic(records/'m4-result.json',observed)
            state='PASS' if code==0 and observed['outcome']=='PASS_BOOTSTRAP_PROVISION_ONLY' else 'UNCERTAIN'
            journal.finish(attempt,state,observed.get('code','VISION_BOOTSTRAP_OBSERVED'),dict(facts=observed))
            result.update(observed)
        except Exception as error:
            result['code']=str(error) if isinstance(error,h.Error) else type(error).__name__
        finally:
            result['totalSeconds']=round(time.monotonic()-began,2)
            h.atomic(records/'result.json',result)
            print(json.dumps(result),flush=True)
    return 0 if result['outcome']=='PASS_BOOTSTRAP_PROVISION_ONLY' else 1


if __name__=='__main__':raise SystemExit(main())
