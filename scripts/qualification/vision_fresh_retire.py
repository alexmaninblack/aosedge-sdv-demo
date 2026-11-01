#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""The retirement stage of the authorized fresh-Vision campaign."""
import argparse
import json
from pathlib import Path
import shlex
import subprocess
import remote_harness as h
from vision_vm_campaign import configuration


def main():
    p=argparse.ArgumentParser();p.add_argument('--config',type=Path,required=True);p.add_argument('--name',required=True)
    p.add_argument('--bundle',type=Path,required=True)
    p.add_argument('--resume-local-after',choices=('vision-fresh-retire-01',));a=p.parse_args()
    h.require(a.name.startswith('vision-fresh-retire-') and a.name.removeprefix('vision-fresh-retire-').isdecimal(),'EXACT_FRESH_RETIREMENT_NAME_REQUIRED')
    c=configuration(a.config);t=c['transport'];q=shlex.quote;records=Path(c['records'])/a.name;remote=Path(c['remoteRoot'])/a.name
    import sys
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'apps/demo-orchestrator/src'))
    from aosedge_demo_orchestrator.vision_bootstrap import verify
    verified=verify(a.bundle,c['main']['manifestSha256'])
    h.require(not records.exists(),'RETIREMENT_EXISTS_RECONCILE');records.mkdir(mode=0o700)
    worker=Path(__file__).with_name('vision_fresh_retire_worker.py')
    context=dict(main=c['main'],bundle=str(remote/a.bundle.name),
        bootstrapManifestSha256=verified.manifest_sha256,remoteRoot=c['remoteRoot'])
    if a.resume_local_after:context['resumeLocalAfter']=str(Path(c['remoteRoot'])/a.resume_local_after)
    h.atomic(records/'context.json',context);h.remote(t,'umask 077\nmkdir '+q(str(remote)),timeout=15)
    options=h.ssh_args(t)[1:-1];options.remove('-T');i=options.index('-b');options[i:i+2]=['-o','BindAddress='+options[i+1]]
    h.run(['/usr/bin/scp','-C','-r',*options,str(a.bundle),str(worker),str(records/'context.json'),t['user']+'@'+t['host']+':'+str(remote)+'/'],timeout=600)
    python=c['main']['packageRoot']+'/demo-artifacts/aosedge-sdv-demo/host-runtime/python/bin/python3.12'
    verify='import hashlib,pathlib;assert hashlib.sha256(pathlib.Path('+repr(str(remote/worker.name))+').read_bytes()).hexdigest()=='+repr(h.digest(worker))
    h.remote(t,q(python)+' -I -B -c '+q(verify),timeout=15)
    process=subprocess.Popen(h.ssh_args(t)+[q(python)+' -I -B '+q(str(remote/worker.name))+' '+q(str(remote/'context.json'))],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    with (records/'progress.jsonl').open('x') as log:
        for line in process.stdout:
            h.require(log.tell()<2**20,'PROGRESS_LIMIT');log.write(line);log.flush()
            if line.startswith('{'):print(line.strip(),flush=True)
    code=process.wait(timeout=15);diagnostic=process.stderr.read(8192)
    h.atomic(records/'transport.json',dict(exit=code,stderrPresent=bool(diagnostic)))
    collect='import pathlib,json;p=pathlib.Path('+repr(str(remote))+');print(json.dumps({f.name:json.loads(f.read_bytes()) for f in p.glob("*.json") if f.name!="context.json" and f.stat().st_size<2097152}))'
    values=json.loads(h.remote(t,q(python)+' -I -B -c '+q(collect),timeout=20))
    for name,value in values.items():h.atomic(records/name,value)
    print(json.dumps(values.get('result.json',dict(outcome='UNCERTAIN'))));return code


if __name__=='__main__':raise SystemExit(main())
