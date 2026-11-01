#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Named retained-Vision ingress campaign; transport never prints secrets."""
import argparse
import json
from pathlib import Path
import shlex
import subprocess

import remote_harness as h
from vision_vm_campaign import configuration


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config',type=Path,required=True);p.add_argument('--name',required=True)
    p.add_argument('--preflight',action='store_true',required=True)
    a=p.parse_args();c=configuration(a.config);t=c['transport'];q=shlex.quote
    h.require(a.name.startswith('ingress-preflight-') and a.name.removeprefix('ingress-preflight-').isdecimal(),'CAMPAIGN_NAME_INVALID')
    records=Path(c['records'])/a.name;remote=Path(c['remoteRoot'])/a.name
    h.require(not records.exists(),'ATTEMPT_EXISTS_RECONCILE');records.mkdir(mode=0o700)
    bundle=Path(c['remoteRoot'])/'signed-bootstrap-03/AosEdge Vision Bootstrap 0.3.0.bundle'
    context=dict(main=c['main'],bundle=str(bundle),bootstrapManifestSha256='d782737eff7ddf6c69f59a36c806b2428129d83b70e6e2deb097939990006612')
    h.atomic(records/'context.json',context)
    worker=Path(__file__).with_name('vision_ingress_preflight_worker.py')
    h.remote(t,'umask 077\nmkdir '+q(str(remote)),timeout=15)
    options=h.ssh_args(t)[1:-1];options.remove('-T');i=options.index('-b');options[i:i+2]=['-o','BindAddress='+options[i+1]]
    h.run(['/usr/bin/scp',*options,str(worker),str(records/'context.json'),t['user']+'@'+t['host']+':'+str(remote)+'/'],timeout=30)
    python=c['main']['packageRoot']+'/demo-artifacts/aosedge-sdv-demo/host-runtime/python/bin/python3.12'
    command=q(python)+' -I -B '+q(str(remote/worker.name))+' '+q(str(remote/'context.json'))
    process=subprocess.Popen(h.ssh_args(t)+[command],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    for line in process.stdout:
        if line.startswith('{'):print(line.strip(),flush=True)
    code=process.wait(timeout=10);diagnostic=process.stderr.read(8192)
    # Retain only fixed exception class/line diagnostics, never raw stderr.
    h.atomic(records/'transport.json',dict(exit=code,stderrPresent=bool(diagnostic)))
    collect='import pathlib; print((pathlib.Path('+repr(str(remote))+')/"result.json").read_text())'
    value=json.loads(h.remote(t,q(python)+' -I -B -c '+q(collect),timeout=15))
    h.atomic(records/'result.json',value)
    print(json.dumps({k:v for k,v in value.items() if k!='facts'}),flush=True)
    return code


if __name__=='__main__':raise SystemExit(main())
