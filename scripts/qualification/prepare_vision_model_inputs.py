#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Assemble verified public Linux ARM64 wheels/models on the selected SSD."""
import argparse
import email
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tarfile
import urllib.request
import zipfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'distribution'))
from build_scratch import directory


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def require(ok,code):
    if not ok:raise ValueError(code)


def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True)
    p.add_argument('--cache',type=Path,required=True);a=p.parse_args()
    require(a.source.is_absolute() and a.cache.is_absolute() and a.source.stat().st_dev==a.cache.stat().st_dev,'INPUT_VOLUME_MISMATCH')
    require(a.cache.stat().st_dev!=Path.home().stat().st_dev,'BUILD_REQUIRES_SELECTED_SSD')
    pin='e7e5c614832f175f1f9f10a0d0c0df2559ff2c38'
    require(subprocess.check_output(['git','-C',str(a.source),'rev-parse','HEAD'],text=True).strip()==pin,'UPSTREAM_PIN_CHANGED')
    require(not subprocess.check_output(['git','-C',str(a.source),'status','--porcelain'],text=True),'UPSTREAM_SOURCE_DIRTY')
    final=a.cache/'vision-pilot-cpu-fp32.tar.gz';receipt=a.cache/'vision-pilot-cpu-fp32.json'
    require(not final.exists() and not receipt.exists(),'INPUT_BUNDLE_EXISTS_RECONCILE_REQUIRED')
    wheels=[]
    for path in sorted((a.cache/'wheels').glob('*.whl')):
        with zipfile.ZipFile(path) as z:
            md=email.message_from_bytes(z.read(next(n for n in z.namelist() if n.endswith('.dist-info/METADATA'))))
        name,version=md['Name'],md['Version']
        with urllib.request.urlopen('https://pypi.org/pypi/'+name+'/'+version+'/json',timeout=15) as response:metadata=json.load(response)
        remote=next(r for r in metadata['urls'] if r['filename']==path.name)
        sha=digest(path);require(sha==remote['digests']['sha256'] and path.stat().st_size==remote['size'],'WHEEL_CHECKSUM_CHANGED')
        wheels.append(dict(name=name,version=version,file=path.name,sha256=sha,bytes=path.stat().st_size))
    require({r['name']:r['version'] for r in wheels}=={'onnxruntime':'1.26.0','numpy':'2.4.4','opencv-python-headless':'4.13.0.92',
        'flatbuffers':'25.12.19','packaging':'26.3','protobuf':'7.36.2'},'WHEEL_SET_CHANGED')
    with directory(a.cache) as scratch:
        root=scratch/'payload';root.mkdir();libs=root/'libraries';libs.mkdir();(root/'models').mkdir()
        for row in wheels:
            with zipfile.ZipFile(a.cache/'wheels'/row['file']) as archive:
                for entry in archive.infolist():
                    name=Path(entry.filename);mode=entry.external_attr>>16
                    require(not name.is_absolute() and '..' not in name.parts and not stat.S_ISLNK(mode),'WHEEL_PATH_INVALID')
                    if entry.is_dir():continue
                    target=libs/name;require(not target.exists(),'WHEEL_FILE_COLLISION');target.parent.mkdir(parents=True,exist_ok=True)
                    target.write_bytes(archive.read(entry));target.chmod((mode&0o755) or 0o644)
        for name in ('autodrive','autosteer','autospeed'):
            src=a.source/'VisionPilot/modules/models/weights'/f'{name}_fp32.onnx'
            shutil.copyfile(src,root/'models'/src.name)
        shutil.copyfile(Path(__file__).with_name('vision_model_probe.py'),root/'probe.py')
        shutil.copyfile(a.source/'LICENSE',root/'UPSTREAM-LICENSE')
        files=[dict(path=str(path.relative_to(root)),bytes=path.stat().st_size,sha256=digest(path),mode=stat.S_IMODE(path.stat().st_mode))
               for path in sorted(root.rglob('*')) if path.is_file()]
        lock=dict(schemaVersion=1,kind='engineering-onnx-cpu-probe',upstream=pin,wheels=wheels,files=files,
                  models='FP32 only; no quantization/output-accuracy claim',nativeAosPackage=False)
        (root/'input-lock.json').write_text(json.dumps(lock,sort_keys=True,indent=2)+'\n')
        archive=scratch/'payload.tar.gz'
        with tarfile.open(archive,'w:gz') as tar:
            for path in sorted(root.rglob('*')):tar.add(path,arcname=str(Path('payload')/path.relative_to(root)),recursive=False)
        result=dict(schemaVersion=1,file=final.name,sha256=digest(archive),bytes=archive.stat().st_size,
                    extractedBytes=sum(r['bytes'] for r in files),upstream=pin,kind='ENGINEERING_MODEL_PROBE_NOT_AOS_PACKAGE')
        os.rename(archive,final)
        receipt.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__=='__main__':main()
