#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Freeze one exact completed Vision image from the owned SSD Builder."""
import argparse
import hashlib
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
sys.path.insert(0,str(ROOT/'apps/demo-orchestrator/src'))
from aosedge_demo_orchestrator.vision_bootstrap import stamp,VERSION


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--result',required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    assert a.output.is_absolute() and not a.output.exists() and a.output.parent.is_dir()
    assert a.output.parent.stat().st_dev==ROOT.stat().st_dev
    path=ROOT/'scripts/r6-1-builder'
    loader=importlib.machinery.SourceFileLoader('vision_owned_builder',str(path))
    spec=importlib.util.spec_from_loader(loader.name,loader)
    builder=importlib.util.module_from_spec(spec);sys.modules[spec.name]=builder;loader.exec_module(builder)
    pid=builder.resolve_running();assert pid is not None,'OWNED_BUILDER_REQUIRED'
    builder.verify_owned_process(pid)
    ssh=builder.ssh_base()
    prefix='/home/yocto/r61-build/factory42-475dc7c1ef3ac303/'
    assert a.result.startswith(prefix) and re.fullmatch(r'vision-bootstrap-image-[0-9]{2}/result.json',a.result[len(prefix):])
    raw=subprocess.check_output(ssh+['cat '+shlex.quote(a.result)],timeout=15)
    assert len(raw)<32768
    receipt=json.loads(raw)
    assert receipt['outcome']=='IMAGE_BUILT_NOT_LIVE_QUALIFIED' and receipt['mainConfigurationRestored'] is True
    assert receipt['factoryVersion']==VERSION and receipt['rootfsQa']=='PASS' and receipt['offline'] is True
    assert receipt['path']==prefix+'main-qemuarm64-'+VERSION+'.img' and 0<receipt['bytes']<=16*1024**3
    assert re.fullmatch('[a-f0-9]{64}',receipt['sha256'])
    a.output.mkdir(mode=0o700);image=a.output/'main-qemuarm64.img'
    h=hashlib.sha256();total=0
    process=subprocess.Popen(ssh+['cat '+shlex.quote(receipt['path'])],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    with image.open('xb') as output:
        for block in iter(lambda:process.stdout.read(4*2**20),b''):
            total+=len(block);assert total<=receipt['bytes'],'IMAGE_TRANSFER_LIMIT'
            output.write(block);h.update(block)
        output.flush();os.fsync(output.fileno())
    assert process.wait(timeout=15)==0 and total==receipt['bytes'] and h.hexdigest()==receipt['sha256'],'TRANSFER_DIGEST_MISMATCH'
    image.chmod(0o444)
    receipt.update(path=str(image),verifiedStamp=stamp(image),builderReceipt=a.result,hostTransferSha256Matched=True)
    target=a.output/'factory.json'
    with target.open('x') as stream:
        os.fchmod(stream.fileno(),0o600);json.dump(receipt,stream,indent=2);stream.write('\n')
    print(json.dumps(dict(outcome='VISION_FACTORY_TRANSFER_VERIFIED',receipt=str(target),bytes=total)))


if __name__=='__main__':main()
