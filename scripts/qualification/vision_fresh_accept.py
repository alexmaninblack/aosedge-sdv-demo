#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Run the remaining accepted permanent-ingress packet once on fresh M4 .5."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import runpy
import shlex
import subprocess
import sys
import tarfile
import time

import remote_harness as h
from vision_vm_campaign import configuration


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,required=True)
    parser.add_argument('--name',required=True)
    parser.add_argument('--bundle',type=Path)
    args=parser.parse_args();c=configuration(args.config);t=c['transport'];q=shlex.quote
    h.require(args.name in ('vision-fresh-accept-01','vision-fresh-accept-02','vision-fresh-accept-03','vision-fresh-accept-04','vision-fresh-accept-05'),'EXACT_FRESH_ACCEPTANCE_REQUIRED')
    records=Path(c['records'])/args.name;remote=Path(c['remoteRoot'])/args.name
    h.require(not records.exists(),'ACCEPTANCE_EXISTS_RECONCILE');records.mkdir(mode=0o700)
    source=Path(__file__).resolve().parents[2];here=Path(__file__).parent
    platform=Path('/Volumes/SDV-Dev/sdv/worktrees/vision-camera-platform')
    platform_pin='64df0da36c845dc28d50a9e5a60d006acd222643'
    h.require(h.run(['git','-C',str(platform),'rev-parse','HEAD']).strip()==platform_pin
              and not h.run(['git','-C',str(platform),'status','--porcelain']).strip(),'PLATFORM_INPUT_CHANGED')
    provision=json.loads((Path(c['records'])/'signed-bootstrap-04/result.json').read_bytes())
    h.require(provision['outcome']=='PASS_BOOTSTRAP_PROVISION_ONLY','FRESH_PROVISION_PROOF_REQUIRED')
    published=json.loads((Path(c['records'])/'vision-fresh-oem-02/result.json').read_bytes())
    h.require(published['outcome']=='PASS_FRESH_FIFTH_PUBLISHED_EMPTY_COHORT','FIFTH_PUBLICATION_PROOF_REQUIRED')
    # The owning platform producer creates deterministic component bytes only;
    # it does not compile CARLA, manufacture another VM or publish anything.
    payload=records/'camera-access-0.1.1.tar.gz'
    raw=runpy.run_path(str(platform/'tools/build_camera_access_payload.py'))['payload']('0.1.1')
    with payload.open('xb') as output:
        with gzip.GzipFile(filename='',mode='wb',fileobj=output,mtime=0) as stream:stream.write(raw)
    payload.chmod(0o444)
    files=[here/name for name in ('vision_fresh_accept_worker.py','vision_ingress_live_worker.py',
        'vision_ingress_observation.py','vision_delivery_guest.py','vision_camera_fixture_cloud.py','vision_permanent_component_cloud.py')]
    build=Path('/Volumes/SDV-Dev/sdv/build/vision-ingress')
    files += [build/'fresh-reader-02/vision-camera-probe',build/'reader-01/vision-camera-credential-deny',
              build/'boundary-01/vision-ingress-boundary']
    h.require(all(p.is_file() and not p.is_symlink() for p in files),'FIXTURE_INPUT_MISSING')
    context=dict(main=c['main'],bundle=str(Path(c['remoteRoot'])/'signed-bootstrap-04/AosEdge Vision Bootstrap 0.5.0.bundle'),
        bootstrapManifestSha256='bea5e3fd9ed899430122f0b0c49cec312cd516eff2159a6d9cdfd0427e4fb6fe',
        previousNative=str(Path(c['remoteRoot'])/'native-camera-17'),
        files={f.name:h.digest(f) for f in files},camera=dict(bytes=payload.stat().st_size,sha256=h.digest(payload),platformRevision=platform_pin))
    context['existingPublication']=json.loads((Path(c['records'])/'native-camera-17/context.json').read_bytes())['existingPublication']
    if args.bundle:
        sys.path.insert(0,str(source/'apps/demo-orchestrator/src'))
        from aosedge_demo_orchestrator import vision_bootstrap as v
        verified=v.verify(args.bundle,c['main']['manifestSha256'])
        context.update(bundle=str(remote/args.bundle.name),bootstrapManifestSha256=verified.manifest_sha256)
    h.atomic(records/'context.json',context)
    python=c['main']['packageRoot']+'/demo-artifacts/aosedge-sdv-demo/host-runtime/python/bin/python3.12'
    preflight='''import pathlib,subprocess,json
assert not pathlib.Path(REMOTE).exists()
assert '"CGSSessionScreenIsLocked"=Yes' not in subprocess.check_output(['/usr/sbin/ioreg','-n','Root','-d1'],text=True),'M4_DESKTOP_LOCKED'
state=json.loads((pathlib.Path.home()/'SDV-Vision-Camera-Image-Lab-Data/.run/demo-current/journal.json').read_bytes())
assert state.get('source',{}).get('state','STOPPED')==state['vehicles']['test']['runtime']['state']=='STOPPED'
assert state['vehicles']['test']['unitId']!='4374bcb2-0613-419c-8ac9-e8458358c91c'
print('FRESH_PERMANENT_ACCEPTANCE_PREFLIGHT_PASS')
'''.replace('REMOTE',repr(str(remote)))
    print(h.remote(t,q(python)+' -I -B -c '+q(preflight),timeout=20).strip(),flush=True)
    h.remote(t,'umask 077\nmkdir '+q(str(remote)),timeout=15)
    options=h.ssh_args(t)[1:-1];options.remove('-T');i=options.index('-b');options[i:i+2]=['-o','BindAddress='+options[i+1]]
    h.run(['/usr/bin/scp',*options,*map(str,files),str(payload),str(records/'context.json'),t['user']+'@'+t['host']+':'+str(remote)+'/'],timeout=90)
    if args.bundle:
        from build_scratch import directory
        with directory(source) as scratch:
            archive=scratch/'signed-host-refresh.tar'
            with tarfile.open(archive,'w') as tar:
                for path in sorted(args.bundle.rglob('*')):
                    relative=path.relative_to(args.bundle).as_posix()
                    if path.is_file() and relative!='Contents/Resources/images/main-qemuarm64.img':
                        h.require(not path.is_symlink(),'LINKED_BUNDLE_RESOURCE');tar.add(path,arcname=relative,recursive=False)
            archive_sha=h.digest(archive)
            h.run(['/usr/bin/scp',*options,str(archive),t['user']+'@'+t['host']+':'+str(remote/archive.name)],timeout=90)
            refresh='''import pathlib,hashlib,tarfile,subprocess,shutil
p=pathlib.Path(ARCHIVE);assert hashlib.sha256(p.read_bytes()).hexdigest()==DIGEST
target=pathlib.Path(TARGET);assert not target.exists();target.mkdir(mode=0o700)
with tarfile.open(p) as tar:
 for member in tar:
  relative=pathlib.PurePosixPath(member.name)
  assert member.isfile() and not relative.is_absolute() and '..' not in relative.parts and member.size<64*1024**2
  destination=target/relative;destination.parent.mkdir(parents=True,exist_ok=True)
  with destination.open('xb') as output:shutil.copyfileobj(tar.extractfile(member),output)
  destination.chmod(member.mode)
old=pathlib.Path(OLD)/'Contents/Resources/images/main-qemuarm64.img'
destination=target/'Contents/Resources/images/main-qemuarm64.img';destination.parent.mkdir()
assert old.is_file() and not old.is_symlink() and old.stat().st_size==IMAGEBYTES
subprocess.run(['/bin/cp','-c',str(old),str(destination)],check=True,capture_output=True)
subprocess.run(['codesign','--verify','--deep','--strict','-R','=identifier "org.aosedge.sdvlab.vision.bootstrap" and anchor apple generic and certificate leaf[subject.OU] = "3NF57VKB3V"',str(target)],check=True,capture_output=True,timeout=120)
p.unlink();print('SIGNED_HOST_REFRESH_VERIFIED_REUSED_SEALED_IMAGE')
'''.replace('ARCHIVE',repr(str(remote/archive.name))).replace('DIGEST',repr(archive_sha)).replace('TARGET',repr(context['bundle'])).replace('OLD',repr(str(Path(c['remoteRoot'])/'signed-bootstrap-04/AosEdge Vision Bootstrap 0.5.0.bundle'))).replace('IMAGEBYTES',str(json.loads((verified.resources/'bootstrap.json').read_bytes())['factory']['bytes']))
            print(h.remote(t,q(python)+' -I -B -c '+q(refresh),timeout=150).strip(),flush=True)
    identity=hashlib.sha256(json.dumps(context,sort_keys=True).encode()).hexdigest();began=time.monotonic()
    with h.Journal(records/'actions',identity) as journal:
        attempt=journal.begin('permanent-fresh-acceptance-worker');attempt['dispatched']=True
        h.atomic(journal.root/('attempt-'+str(attempt['attempt']).zfill(4)+'.json'),attempt)
        process=subprocess.Popen(h.ssh_args(t)+[q(python)+' -I -B '+q(str(remote/'vision_fresh_accept_worker.py'))+' '+q(str(remote/'context.json'))],
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        with (records/'progress.jsonl').open('x') as log:
            for line in process.stdout:
                h.require(log.tell()<2**20,'PROGRESS_LIMIT');log.write(line);log.flush()
                if line.startswith('{'):print(line.strip(),flush=True)
        stderr=process.stderr.read(8192);code=process.wait(timeout=20)
        h.atomic(records/'transport.json',dict(exit=code,stderrPresent=bool(stderr)))
        collect='import pathlib,json;p=pathlib.Path('+repr(str(remote))+');print(json.dumps({f.name:json.loads(f.read_bytes()) for f in p.glob("*.json") if f.name!="context.json" and f.stat().st_size<2097152}))'
        values=json.loads(h.remote(t,q(python)+' -I -B -c '+q(collect),timeout=20))
        for name,value in values.items():h.atomic(records/name,value)
        result=values.get('result.json',dict(outcome='UNCERTAIN'));result['totalSeconds']=round(time.monotonic()-began,2)
        journal.finish(attempt,'PASS' if code==0 and result['outcome'].startswith('PASS_') else 'UNCERTAIN',result.get('code','FRESH_ACCEPTANCE_OBSERVED'),dict(facts=result))
        h.atomic(records/'result.json',result);print(json.dumps(result),flush=True)
    return code


if __name__=='__main__':raise SystemExit(main())
