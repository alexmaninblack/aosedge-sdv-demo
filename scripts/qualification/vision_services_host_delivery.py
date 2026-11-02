#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Deliver sealed Vision host delta; clone retained image, never rebase a VM."""
import argparse
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import tarfile
import time

import remote_harness as h
from vision_vm_campaign import configuration

BASE=Path('/Volumes/SDV-Dev/sdv/build/vision-bootstrap/0.6.0-services-host')
NAME='AosEdge Vision Bootstrap 0.6.0.bundle'


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--config',type=Path,required=True);choice=p.add_mutually_exclusive_group();choice.add_argument('--observation-successor',action='store_true');choice.add_argument('--calibration-successor',action='store_true');choice.add_argument('--ui-successor',action='store_true');choice.add_argument('--reader-isolation-successor',action='store_true');a=p.parse_args();c=configuration(a.config)
    version='0.6.4' if a.reader_isolation_successor else '0.6.3' if a.ui_successor else '0.6.2' if a.calibration_successor else '0.6.1' if a.observation_successor else '0.6.0'
    base=BASE.parent/('0.6.4-services-ui-isolated' if a.reader_isolation_successor else '0.6.3-services-ui' if a.ui_successor else '0.6.2-services-calibration' if a.calibration_successor else '0.6.1-services-observe') if version!='0.6.0' else BASE
    name='AosEdge Vision Bootstrap '+version+'.bundle'
    records=Path(c['records'])/('vision-services-host-05' if a.reader_isolation_successor else 'vision-services-host-04' if a.ui_successor else 'vision-services-host-03' if a.calibration_successor else 'vision-services-host-02' if a.observation_successor else 'vision-services-host-01');remote=Path(c['remoteRoot'])/records.name
    h.require(not records.exists(),'VISION_HOST_DELIVERY_EXISTS_RECONCILE');records.mkdir(mode=0o700)
    result=json.loads((base/'result.json').read_bytes());bundle=base/name;archive=base/'host-files.tar'
    h.require(result['manifestSha256']==hashlib.sha256((bundle/'Contents/Resources/bootstrap.json').read_bytes()).hexdigest(),'VISION_HOST_MANIFEST_CHANGED')
    h.require(not archive.exists(),'VISION_HOST_TRANSFER_INPUT_EXISTS')
    with tarfile.open(archive,'w') as output:
        for path in sorted(bundle.rglob('*')):
            h.require(not path.is_symlink(),'VISION_HOST_LINK_FORBIDDEN')
            if path.is_file() and path.relative_to(bundle).as_posix()!='Contents/Resources/images/main-qemuarm64.img':
                output.add(path,arcname=path.relative_to(bundle).as_posix(),recursive=False)
    archive.chmod(0o444);pin=h.digest(archive);t=c['transport'];q=shlex.quote;started=time.monotonic()
    h.remote(t,'umask 077\nmkdir '+q(str(remote)),timeout=10)
    options=h.ssh_args(t)[1:-1];options.remove('-T');i=options.index('-b');options[i:i+2]=['-o','BindAddress='+options[i+1]]
    h.run(['/usr/bin/scp',*options,str(archive),t['user']+'@'+t['host']+':'+str(remote)+'/'],timeout=90)
    code='''import hashlib,json,pathlib,subprocess,tarfile,sys,stat
root=pathlib.Path(REMOTE);bundle=root/NAME;old=pathlib.Path(OLD);archive=root/'host-files.tar'
assert not bundle.exists() and hashlib.sha256(archive.read_bytes()).hexdigest()==PIN
native=pathlib.Path.home()/'SDV-Vision-Camera-Image-Lab-Data';journal=pathlib.Path('.run/demo-current/journal.json')
names=('SDV-Lab-Data','SDV-Vision-Lab-Data','SDV-Vision-Native-Lab-Data','SDV-Vision-Camera-Lab-Data')
retained={pathlib.Path.home()/name:(pathlib.Path.home()/name/journal).read_bytes() for name in names}
before=(native/journal).read_bytes();state=json.loads(before);item=state['vehicles']['test']
assert item['unitId']=='af6d074a-6ce1-49ba-b613-0476e7b6d1b5' and item['localVmId']=='89273f16-4be0-4b22-b4cb-58d08533c8bc'
assert state['source']['state']==item['runtime']['state']=='STOPPED'
assert hashlib.sha256((old/'Contents/Resources/bootstrap.json').read_bytes()).hexdigest()=='e10d77b648b664a8ae5cbe895c428d0ee37578f516c0a62b467161e055118a1c'
requirement='=identifier "org.aosedge.sdvlab.vision.bootstrap" and anchor apple generic and certificate leaf[subject.OU] = "3NF57VKB3V"'
subprocess.run(['codesign','--verify','--deep','--strict','-R',requirement,str(old)],check=True,capture_output=True,timeout=120)
bundle.mkdir(mode=0o755)
with tarfile.open(archive) as source:
 seen=set()
 for row in source:
  path=pathlib.PurePosixPath(row.name)
  assert row.isfile() and not row.issym() and not row.islnk() and not path.is_absolute() and '..' not in path.parts and row.name not in seen
  assert row.name.startswith('Contents/') and row.size<32*1024**2 and not row.mode&0o7000
  if row.name.startswith('Contents/Resources/'):assert row.mode&0o222==0
  seen.add(row.name);target=bundle/path;target.parent.mkdir(parents=True,exist_ok=True)
  with target.open('xb') as stream:stream.write(source.extractfile(row).read())
  target.chmod(stat.S_IMODE(row.mode))
image=bundle/'Contents/Resources/images/main-qemuarm64.img';image.parent.mkdir()
subprocess.run(['/bin/cp','-c',str(old/'Contents/Resources/images/main-qemuarm64.img'),str(image)],check=True,capture_output=True,timeout=30)
subprocess.run(['codesign','--verify','--deep','--strict','-R',requirement,str(bundle)],check=True,capture_output=True,timeout=120)
assert hashlib.sha256((bundle/'Contents/Resources/bootstrap.json').read_bytes()).hexdigest()==MANIFEST
sys.path.insert(0,str(pathlib.Path(PACKAGE)/'aosedge-sdv-demo/apps/demo-orchestrator/src'))
import aosedge_demo_orchestrator
from aosedge_demo_orchestrator import runtime_paths
aosedge_demo_orchestrator.__path__.insert(0,str(bundle/'Contents/Resources/tooling/aosedge-sdv-demo/apps/demo-orchestrator/src/aosedge_demo_orchestrator'))
from aosedge_demo_orchestrator import vision_bootstrap as v
b=v.verify(bundle,BASE_MANIFEST);assert b.manifest_sha256==MANIFEST
with runtime_paths.installed_session(native):
 catalog=v.SignedVisionCatalog(b);assert catalog.vision_exchange_scopes==('vision-context-read','vision-assessment-publish')
assert (native/journal).read_bytes()==before and all((p/journal).read_bytes()==raw for p,raw in retained.items())
print(json.dumps(dict(outcome='PASS_SIGNED_VISION_HOST_DELIVERY',signatureVerified=True,exactScopesVerified=True,
 retainedJournalsUnchanged=True,sameVmAndUnit=True,vmRebased=False,cloudMutation=False,bundle=str(bundle),manifestSha256=MANIFEST)))
'''
    values=dict(REMOTE=str(remote),NAME=name,OLD=str(Path(c['remoteRoot'])/'vision-fresh-accept-11/AosEdge Vision Bootstrap 0.5.0.bundle'),
        PIN=pin,MANIFEST=result['manifestSha256'],BASE_MANIFEST=c['main']['manifestSha256'],PACKAGE=c['main']['packageRoot'])
    import re
    code=re.sub(r'\b('+'|'.join(sorted(values,key=len,reverse=True))+r')\b',lambda m:repr(values[m[0]]),code)
    python=c['main']['packageRoot']+'/demo-artifacts/aosedge-sdv-demo/host-runtime/python/bin/python3.12'
    observed=json.loads(h.remote(t,shlex.join([python,'-I','-B','-c',code]),timeout=300))
    observed['seconds']=round(time.monotonic()-started,2);h.atomic(records/'result.json',observed);print(json.dumps(observed));return 0


if __name__=='__main__':raise SystemExit(main())
