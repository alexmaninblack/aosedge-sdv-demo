#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Fresh campaign's empty-recipient gate and one immutable .5 publication."""
import argparse
import json
from pathlib import Path
import shlex
import subprocess
import remote_harness as h
from vision_vm_campaign import configuration


def main():
    p=argparse.ArgumentParser();p.add_argument('--config',type=Path,required=True);p.add_argument('--name',required=True)
    p.add_argument('--mode',choices=('gate','publish'),required=True);p.add_argument('--artifact',type=Path);a=p.parse_args()
    c=configuration(a.config);t=c['transport'];q=shlex.quote
    h.require(a.name.startswith('vision-fresh-oem-') and a.name.removeprefix('vision-fresh-oem-').isdecimal(),'FRESH_OEM_NAME_INVALID')
    records=Path(c['records'])/a.name;remote=Path(c['remoteRoot'])/a.name
    h.require(not records.exists(),'FRESH_OEM_ATTEMPT_EXISTS_RECONCILE');records.mkdir(mode=0o700)
    here=Path(__file__).parent;files=[here/n for n in ('vision_fresh_oem_worker.py','vision_fresh_cloud.py','vision_permanent_component_cloud.py')]
    context=dict(main=c['main'],mode=a.mode,retirement=str(Path(c['remoteRoot'])/'vision-fresh-retire-02'),
        bundle=str(Path(c['remoteRoot'])/'vision-fresh-retire-02/AosEdge Vision Retirement.bundle'),files={f.name:h.digest(f) for f in files})
    if a.mode=='publish':
        artifact=json.loads(a.artifact.read_bytes());h.require(artifact['rootfsVersion']=='6.1.1-vision-camera.5','EXACT_FIFTH_ARTIFACT_REQUIRED')
        context['artifact']=artifact
    h.atomic(records/'context.json',context);h.remote(t,'umask 077\nmkdir '+q(str(remote)),timeout=15)
    options=h.ssh_args(t)[1:-1];options.remove('-T');i=options.index('-b');options[i:i+2]=['-o','BindAddress='+options[i+1]]
    h.run(['/usr/bin/scp',*options,*map(str,files),str(records/'context.json'),t['user']+'@'+t['host']+':'+str(remote)+'/'],timeout=30)
    if a.mode=='publish':h.run(['/usr/bin/scp',*options,artifact['path'],t['user']+'@'+t['host']+':'+str(remote/'vision-rootfs.squashfs')],timeout=120)
    python=c['main']['packageRoot']+'/demo-artifacts/aosedge-sdv-demo/host-runtime/python/bin/python3.12'
    process=subprocess.Popen(h.ssh_args(t)+[q(python)+' -I -B '+q(str(remote/files[0].name))+' '+q(str(remote/'context.json'))],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    stdout,stderr=process.communicate(timeout=900);h.atomic(records/'transport.json',dict(exit=process.returncode,stderrPresent=bool(stderr)))
    collect='import pathlib,json;p=pathlib.Path('+repr(str(remote))+');print(json.dumps({f.name:json.loads(f.read_bytes()) for f in p.glob("*.json") if f.name!="context.json" and f.stat().st_size<2097152}))'
    values=json.loads(h.remote(t,q(python)+' -I -B -c '+q(collect),timeout=20))
    for name,value in values.items():h.atomic(records/name,value)
    print(json.dumps(values.get('result.json',dict(outcome='UNCERTAIN'))),flush=True);return process.returncode


if __name__=='__main__':raise SystemExit(main())
