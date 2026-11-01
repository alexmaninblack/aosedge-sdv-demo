#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""One disposable M4 Camera-store scenario; SSD-built primitives only."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import shlex
import subprocess
import tarfile
import remote_harness as h
from vision_vm_campaign import configuration


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--config',type=Path,required=True)
    p.add_argument('--platform',type=Path,required=True);p.add_argument('--primitives',type=Path,required=True)
    p.add_argument('--policy-loader',type=Path,required=True)
    p.add_argument('--tools',type=Path,required=True)
    p.add_argument('--loop-module',type=Path,required=True)
    p.add_argument('--attempt',type=int,default=1);p.add_argument('--retained-native',action='store_true')
    a=p.parse_args();c=configuration(a.config);t=c['transport'];q=shlex.quote;here=Path(__file__).resolve().parent
    h.require(1<=a.attempt<=20,'ATTEMPT_INVALID')
    name='camera-store-proof-'+str(a.attempt).zfill(2);root=Path(c['records'])/name;remote=Path(c['remoteRoot'])/name
    h.require(not root.exists(),'ATTEMPT_EXISTS_RECONCILE');root.mkdir(mode=0o700)
    files=a.platform/'meta-aos-vehicle-platform/recipes-aos/aos-camera-access-platform/files'
    names=['aos-camera-access-store-layout','aos-camera-access-store-layout.service','aos-camera-access-store-prepare',
        'aos-camera-access-store-prepare.service','aos-camera-access-store-attach.service','aos-camera-access-store.mount',
        'aos-camera-access-store-check','camera-store.conf','aos-camera-access-bootstrap.service']
    proof=json.loads((a.primitives/'result.json').read_bytes());h.require(proof['outcome']=='PASS_TARGETED_PRIMITIVE_COMPILE','PRIMITIVE_GATE_REQUIRED')
    payload=io.BytesIO()
    with tarfile.open(fileobj=payload,mode='w:gz') as archive:
        for n in names:archive.add(files/n,arcname='files/'+n)
        for n in ('camera_access.pp','aos-camera-access-loop'):
            h.require(h.digest(a.primitives/n)==proof['files'][n]['sha256'],'PRIMITIVE_CHANGED')
            archive.add(a.primitives/n,arcname='files/'+n)
        loader=json.loads((a.policy_loader.parent/'result.json').read_bytes())
        h.require(loader['outcome']=='PASS_TARGETED_POLICY_LOADER_COMPILE' and h.digest(a.policy_loader)==loader['sha256'],'POLICY_LOADER_CHANGED')
        archive.add(a.policy_loader,arcname='files/vision-policy-load')
        tools=json.loads((a.tools/'result.json').read_bytes())
        h.require(tools['outcome']=='VERIFIED_EXISTING_TARGET_DEPENDENCIES','TARGET_TOOL_GATE_REQUIRED')
        for n,row in tools['files'].items():
            h.require(n in ('blkid','losetup') and h.digest(a.tools/n)==row['sha256'],'TARGET_TOOL_CHANGED')
            archive.add(a.tools/n,arcname='tools/'+n)
        kernel=json.loads((a.loop_module.parent/'result.json').read_bytes())
        h.require(kernel['kernelRelease']=='6.6.123-yocto-standard' and h.digest(a.loop_module)==kernel['sha256'],'LOOP_MODULE_CHANGED')
        archive.add(a.loop_module,arcname='kernel/loop.ko')
        archive.add(a.loop_module.parent/'result.json',arcname='kernel/result.json')
        archive.add(here/'vision_camera_store_guest.py',arcname='guest.py')
    raw=payload.getvalue();(root/'payload.tar.gz').write_bytes(raw)
    context=dict(main=c['main'],payloadSha256=hashlib.sha256(raw).hexdigest(),retainedNative=a.retained_native,
        bundle=str(Path(c['remoteRoot'])/'native-camera-02/AosEdge Vision Bootstrap 0.1.2.bundle'),
        bootstrapManifestSha256='fb857d8cd3579dc9ae56ba484921e029a17909e318a5cfdf2b99b2f1410f32cc')
    h.atomic(root/'context.json',context)
    h.remote(t,'umask 077\nmkdir '+q(str(remote)),timeout=15)
    options=h.ssh_args(t)[1:-1];options.remove('-T');i=options.index('-b');options[i:i+2]=['-o','BindAddress='+options[i+1]]
    h.run(['/usr/bin/scp',*options,str(here/'vision_camera_store_worker.py'),str(root/'payload.tar.gz'),str(root/'context.json'),t['user']+'@'+t['host']+':'+str(remote)+'/'],timeout=40)
    python=c['main']['packageRoot']+'/demo-artifacts/aosedge-sdv-demo/host-runtime/python/bin/python3.12'
    command=q(python)+' -I -B '+q(str(remote/'vision_camera_store_worker.py'))+' --context '+q(str(remote/'context.json'))
    process=subprocess.Popen(h.ssh_args(t)+[command],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    process.stdin.write(json.dumps(dict(password='Password1')));process.stdin.close()
    with (root/'progress.jsonl').open('x') as log:
        for line in process.stdout:
            log.write(line);log.flush()
            if line.startswith('{'):print(line.strip(),flush=True)
    code=process.wait(timeout=15);diagnostic=process.stderr.read(4000)
    collect="""import json,pathlib
p=pathlib.Path(REMOTE);names=['result.json','guest-result.json','guest-command.json']
print(json.dumps({n:json.loads((p/n).read_bytes()) for n in names if (p/n).is_file()}))
""".replace('REMOTE',repr(str(remote)))
    observed=json.loads(h.remote(t,q(python)+' -I -B -c '+q(collect),timeout=20))
    for n,v in observed.items():h.atomic(root/n,v)
    print(json.dumps(observed.get('guest-result.json',observed.get('guest-command.json',dict(exit=code,stderrPresent=bool(diagnostic))))),flush=True)
    return code


if __name__=='__main__':raise SystemExit(main())
