#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Rehearse retained stopped-VM recovery for the accepted Vision services packet."""
import argparse
import json
from pathlib import Path
import shlex
import subprocess
import remote_harness as h
from vision_vm_campaign import configuration


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--config',type=Path,required=True);args=parser.parse_args()
    c=configuration(args.config);name='vision-services-recovery-01';records=Path(c['records'])/name;remote=Path(c['remoteRoot'])/name
    h.require(not records.exists(),'VISION_SERVICES_RECOVERY_EXISTS_RECONCILE')
    previous=json.loads((Path(c['records'])/'vision-services-native-live-16/result.json').read_bytes())
    h.require(previous['outcome']=='PASS_NATIVE_INDEPENDENT_SOTA_AND_UNIX_ONLY_MAIN_PROCESSES' and all(previous['cleanup'].values()),'VISION_NATIVE_SUCCESSOR_GATE_REQUIRED')
    delivered=json.loads((Path(c['records'])/'vision-services-host-03/result.json').read_bytes())
    files=[Path(__file__).with_name(name) for name in ('vision_recovery_worker.py','vision_delivery_guest.py')]
    records.mkdir(mode=0o700)
    context=dict(main=c['main'],bundle=delivered['bundle'],bootstrapManifestSha256=delivered['manifestSha256'],servicesPacket=True,
        permanentDelivery=dict(authorized=True,recoveryFirst=True,rootfsVersion='6.1.1-vision-camera.6',cameraVersion='0.1.2',perceptionVersion='0.1.1',assessmentVersion='0.1.1'),
        files={path.name:h.digest(path) for path in files})
    h.atomic(records/'context.json',context);h.remote(c['transport'],'umask 077\nmkdir '+shlex.quote(str(remote)),timeout=15)
    options=h.ssh_args(c['transport'])[1:-1];options.remove('-T');index=options.index('-b');options[index:index+2]=['-o','BindAddress='+options[index+1]]
    h.run(['/usr/bin/scp',*options,*map(str,files),str(records/'context.json'),c['transport']['user']+'@'+c['transport']['host']+':'+str(remote)+'/'],timeout=30)
    python=c['main']['packageRoot']+'/demo-artifacts/aosedge-sdv-demo/host-runtime/python/bin/python3.12'
    process=subprocess.Popen(h.ssh_args(c['transport'])+[shlex.join([python,'-I','-B',str(remote/files[0].name),str(remote/'context.json')])],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    with (records/'progress.jsonl').open('x') as output:
        for line in process.stdout:
            h.require(output.tell()<1024**2,'VISION_RECOVERY_PROGRESS_LIMIT');output.write(line);output.flush();print(line.strip(),flush=True)
    code=process.wait(timeout=15);diagnostic=process.stderr.read(8192);h.atomic(records/'transport.json',dict(exit=code,stderrPresent=bool(diagnostic)))
    collect='import pathlib,json;root=pathlib.Path('+repr(str(remote))+');print(json.dumps({p.name:json.loads(p.read_bytes()) for p in root.glob("*.json") if p.name!="context.json" and p.stat().st_size<2*1024**2}))'
    values=json.loads(h.remote(c['transport'],shlex.join([python,'-I','-B','-c',collect]),timeout=20))
    for name,value in values.items():h.atomic(records/name,value)
    return code


if __name__=='__main__':raise SystemExit(main())
