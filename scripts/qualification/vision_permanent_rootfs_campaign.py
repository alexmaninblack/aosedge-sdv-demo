#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Transfer the authorized immutable rootfs.5 to its retained M4 owner."""
import argparse
import json
from pathlib import Path
import shlex
import subprocess

import remote_harness as h
from vision_vm_campaign import configuration


def main():
    p=argparse.ArgumentParser();p.add_argument('--config',type=Path,required=True);p.add_argument('--name',required=True)
    p.add_argument('--artifact',type=Path,required=True);p.add_argument('--cloud-proof',required=True)
    p.add_argument('--services-packet',action='store_true');a=p.parse_args()
    c=configuration(a.config);t=c['transport'];q=shlex.quote
    h.require(a.name.startswith('permanent-rootfs-') and a.name.removeprefix('permanent-rootfs-').isdecimal(),'PERMANENT_NAME_INVALID')
    records=Path(c['records'])/a.name;remote=Path(c['remoteRoot'])/a.name
    h.require(not records.exists(),'PERMANENT_ATTEMPT_EXISTS_RECONCILE');records.mkdir(mode=0o700)
    artifact=json.loads(a.artifact.read_bytes())
    version='6.1.1-vision-camera.6' if a.services_packet else '6.1.1-vision-camera.5'
    h.require(artifact['rootfsVersion']==version and Path(artifact['path']).stat().st_size==artifact['bytes']
        and h.digest(Path(artifact['path']))==artifact['sha256'],'FROZEN_ROOTFS_REQUIRED')
    recovery_name='vision-services-recovery-01' if a.services_packet else 'ingress-recovery-01'
    recovery=json.loads((Path(c['records'])/recovery_name/'result.json').read_bytes())
    prefix='vision-services-platform-preflight-' if a.services_packet else 'ingress-cloud-'
    h.require(a.cloud_proof.startswith(prefix) and a.cloud_proof.removeprefix(prefix).isdecimal(),'CURRENT_ACCOUNT_GATE_REQUIRED')
    account=json.loads((Path(c['records'])/a.cloud_proof/'result.json').read_bytes())
    h.require(recovery['outcome']=='PASS_SAME_VM_CHECKPOINT_RECOVERY' and all(recovery['cleanup'].values()),'RECOVERY_GATE_REQUIRED')
    if a.services_packet:h.require(account['outcome']=='PASS_VISION_SERVICES_PLATFORM_RECIPIENTS_AND_VERSIONS'
        and account['cloudMutation'] is False and all(v['recipientScopeComplete'] and not v['publicationCollision'] for v in account['components'].values()),'ACCOUNT_GATE_REQUIRED')
    else:h.require(account['outcome']=='PASS_NATIVE_PREREQUISITES' and account['facts']['cloud']['ready'],'ACCOUNT_GATE_REQUIRED')
    files=[Path(__file__).with_name(n) for n in ('vision_permanent_rootfs_worker.py','vision_permanent_component_cloud.py','vision_delivery_guest.py')]
    context=dict(main=c['main'],bundle=str(Path(c['remoteRoot'])/'signed-bootstrap-03/AosEdge Vision Bootstrap 0.3.0.bundle'),
        bootstrapManifestSha256='d782737eff7ddf6c69f59a36c806b2428129d83b70e6e2deb097939990006612',rootfs=artifact,
        recovery=str(Path(c['remoteRoot'])/recovery_name),files={p.name:h.digest(p) for p in files},
        permanentDelivery=dict(authorized=True,recoveryFirst=True,rootfsVersion='6.1.1-vision-camera.5',cameraVersion='0.1.1',readVersion='0.1.4',revokeVersion='0.1.5'))
    if a.services_packet:
        host=json.loads((Path(c['records'])/'vision-services-host-03/result.json').read_bytes())
        context.update(servicesPacket=True,bundle=host['bundle'],bootstrapManifestSha256=host['manifestSha256'],
            permanentDelivery=dict(authorized=True,recoveryFirst=True,rootfsVersion=version,cameraVersion='0.1.2',perceptionVersion='0.1.1',assessmentVersion='0.1.1'))
    h.atomic(records/'context.json',context)
    h.remote(t,'umask 077\nmkdir '+q(str(remote)),timeout=15)
    options=h.ssh_args(t)[1:-1];options.remove('-T');i=options.index('-b');options[i:i+2]=['-o','BindAddress='+options[i+1]]
    h.run(['/usr/bin/scp',*options,*map(str,files),str(records/'context.json'),t['user']+'@'+t['host']+':'+str(remote)+'/'],timeout=30)
    h.run(['/usr/bin/scp',*options,artifact['path'],t['user']+'@'+t['host']+':'+str(remote/'vision-rootfs.squashfs')],timeout=120)
    python=c['main']['packageRoot']+'/demo-artifacts/aosedge-sdv-demo/host-runtime/python/bin/python3.12'
    process=subprocess.Popen(h.ssh_args(t)+[q(python)+' -I -B '+q(str(remote/files[0].name))+' '+q(str(remote/'context.json'))],
        stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    with (records/'progress.jsonl').open('x') as log:
        for line in process.stdout:
            h.require(log.tell()<2**20,'PROGRESS_LIMIT');log.write(line);log.flush()
            if line.startswith('{'):print(line.strip(),flush=True)
    code=process.wait(timeout=15);stderr=process.stderr.read(8192);h.atomic(records/'transport.json',dict(exit=code,stderrPresent=bool(stderr)))
    collect='import pathlib,json;p=pathlib.Path('+repr(str(remote))+');print(json.dumps({f.name:json.loads(f.read_bytes()) for f in p.glob("*.json") if f.name!="context.json" and f.stat().st_size<2097152}))'
    values=json.loads(h.remote(t,q(python)+' -I -B -c '+q(collect),timeout=20))
    for name,value in values.items():h.atomic(records/name,value)
    print(json.dumps(values.get('result.json',dict(outcome='UNCERTAIN'))),flush=True)
    return code


if __name__=='__main__':raise SystemExit(main())
