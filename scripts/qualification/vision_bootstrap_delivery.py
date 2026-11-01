#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Deliver signed Source-only tooling without manufacturing or rebasing a VM."""
import argparse
import json
from pathlib import Path
import shlex
import sys
import time

import remote_harness as h
from vision_vm_campaign import configuration

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'apps/demo-orchestrator/src'))
from aosedge_demo_orchestrator import vision_bootstrap as v


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config',type=Path,required=True);p.add_argument('--bundle',type=Path,required=True)
    p.add_argument('--name',choices=('source-enrollment-bootstrap-01',),required=True)
    a=p.parse_args();c=configuration(a.config);t=c['transport'];q=shlex.quote
    b=v.verify(a.bundle,c['main']['manifestSha256'])
    records=Path(c['records'])/a.name;target=Path(c['remoteRoot'])/a.name
    h.require(not records.exists(),'DELIVERY_ATTEMPT_EXISTS_RECONCILE');records.mkdir(mode=0o700)
    python=c['main']['packageRoot']+'/demo-artifacts/aosedge-sdv-demo/host-runtime/python/bin/python3.12'
    read=r'''import json,pathlib,subprocess
assert subprocess.check_output(['/usr/sbin/sysctl','-n','hw.model'],text=True).strip()=='Mac16,8'
p=pathlib.Path.home()/'SDV-Vision-Camera-Lab-Data'
s=json.loads((p/'.run/demo-current/journal.json').read_bytes());item=s['vehicles']['test']
assert s['vmProfile']=='aos-vision-main-qemuarm64-v1' and item['runtime']['state']=='STOPPED'
assert s['source']['state']=='STOPPED' and not s['source'].get('operation')
assert item['cloud']['identity']['model']=='aos-vision-vm' and item.get('unitId')
print(json.dumps(dict(localVmId=item['localVmId'],unitId=item['unitId'],nodeId=item['nodeId'],overlay=item['overlay'],factory=s['factory'])))
'''
    started=time.monotonic()
    before=json.loads(h.remote(t,q(python)+' -I -B -c '+q(read),timeout=15))
    h.atomic(records/'retained-scope.json',before)
    h.remote(t,'umask 077\nmkdir '+q(str(target)),timeout=15)
    options=h.ssh_args(t)[1:-1];options.remove('-T');i=options.index('-b');options[i:i+2]=['-o','BindAddress='+options[i+1]]
    print(json.dumps(dict(stage='transfer-signed-source-tooling',state='STARTED')),flush=True)
    h.run(['/usr/bin/scp','-C','-r',*options,str(a.bundle),t['user']+'@'+t['host']+':'+str(target)+'/'],timeout=900)
    remote_bundle=str(target/a.bundle.name)
    verify=r'''import pathlib,json,subprocess,hashlib
p=pathlib.Path(BUNDLE)
subprocess.run(['codesign','--verify','--deep','--strict','-R',
 '=identifier "org.aosedge.sdvlab.vision.bootstrap" and anchor apple generic and certificate leaf[subject.OU] = "3NF57VKB3V"',str(p)],check=True,capture_output=True,timeout=120)
raw=(p/'Contents/Resources/bootstrap.json').read_bytes();assert hashlib.sha256(raw).hexdigest()==MANIFEST
m=json.loads(raw);assert m['factory']['version']=='6.1.1-vision-camera.2'
assert m['baseProgramManifestSha256']==BASE
print(json.dumps(dict(signatureVerified=True,manifestVerified=True,vmNotRebuilt=True)))
'''.replace('BUNDLE',repr(remote_bundle)).replace('MANIFEST',repr(b.manifest_sha256)).replace('BASE',repr(c['main']['manifestSha256']))
    proof=json.loads(h.remote(t,q(python)+' -I -B -c '+q(verify),timeout=135))
    after=json.loads(h.remote(t,q(python)+' -I -B -c '+q(read),timeout=15))
    h.require(before==after,'RETAINED_INSTANCE_CHANGED')
    result=dict(outcome='SIGNED_TOOLING_DELIVERED_RETAINED_INSTANCE_UNCHANGED',bundle=remote_bundle,
        manifestSha256=b.manifest_sha256,sourceRevision=b.source_revision,proof=proof,
        seconds=round(time.monotonic()-started,2),manufacture=False,cloudMutation=False)
    h.atomic(records/'result.json',result);print(json.dumps(result),flush=True)
    return 0


if __name__=='__main__':raise SystemExit(main())
