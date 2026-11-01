#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""One owned SSD primitive compile; preserve warm Builder, never image-build."""
import hashlib
import json
import os
from pathlib import Path
import runpy
import shlex
import subprocess
import sys
import tarfile
import time

ROOT=Path(__file__).resolve().parents[2]
PLATFORM=ROOT.parent/'vision-camera-platform'
PROJECT=Path('/home/yocto/r61-build/factory42-475dc7c1ef3ac303')


def main():
    output=Path('/Volumes/SDV-Dev/sdv/build/vision-services/exchange-primitives-01');assert not output.exists();output.mkdir(mode=0o700)
    for key,value in dict(R61_BUILDER_ROOT='/Volumes/SDV-Dev/sdv/build/factory-builder',R61_BUILDER_VOLUME_UUID='F92AB578-22AA-4DAC-B8DD-7DC0EB831396',R61_BUILDER_SSH_PORT='10024',R61_BUILDER_DNS_PORT='18054').items():os.environ[key]=value
    sys.path.insert(0,str(ROOT/'scripts'));b=runpy.run_path(str(ROOT/'scripts/r6-1-builder'),run_name='builder_library')
    sys.path.insert(0,str(ROOT/'scripts/distribution'));from build_scratch import directory
    result=dict(outcome='NOT_COMPLETE',imageBuilt=False);owned=False;started=time.monotonic()
    def run(args,timeout=120):
        p=subprocess.run(args,capture_output=True,text=True,timeout=timeout)
        if p.returncode:
            (output/'target-diagnostics.log').write_text((p.stdout+p.stderr)[-8192:]);raise ValueError('VISION_EXCHANGE_TARGET_COMPILE_FAILED')
        return p.stdout
    try:
        assert b['resolve_running']() is None,'BUILDER_OTHER_OWNER_RUNNING';owned=True;b['start'](False);b['wait_ready']()
        with directory(ROOT) as scratch:
            archive=scratch/'exchange.tar'
            paths=list((PLATFORM/'tests/fixtures/vision-native-exchange').iterdir())+[PLATFORM/'tools/vision_exchange_compile_worker.py']
            with tarfile.open(archive,'w') as tar:
                for path in paths:
                    assert path.is_file() and not path.is_symlink();tar.add(path,arcname=path.name)
            pin=hashlib.sha256(archive.read_bytes()).hexdigest()
            remote=PROJECT/'.tmp/vision-exchange-input-01.tar'
            run(b['scp_base']()+[str(archive),'yocto@127.0.0.1:'+str(remote)],30)
        code='''import hashlib,json,pathlib,subprocess,tempfile,tarfile
project=pathlib.Path(PROJECT);archive=project/'.tmp/vision-exchange-input-01.tar'
assert hashlib.sha256(archive.read_bytes()).hexdigest()==PIN
with tempfile.TemporaryDirectory(prefix='vision-exchange-input-',dir=project/'.tmp') as temporary:
 source=pathlib.Path(temporary)
 with tarfile.open(archive) as tar:
  for row in tar:
   assert row.isfile() and '/' not in row.name and '..' not in row.name and row.size<65536
   (source/row.name).write_bytes(tar.extractfile(row).read())
 subprocess.run(['python3','-B',str(source/'vision_exchange_compile_worker.py'),'--input',str(source),'--evidence',str(project/'vision-exchange-primitives-01')],check=True,timeout=90)
archive.unlink()
'''.replace('PROJECT',repr(str(PROJECT))).replace('PIN',repr(pin))
        result.update(json.loads(run(b['ssh_base']()+['python3 -B -c '+shlex.quote(code)],120)))
        for name,pin in result['files'].items():
            run(b['scp_base']()+['yocto@127.0.0.1:'+str(PROJECT/'vision-exchange-primitives-01'/name),str(output/name)],20)
            assert hashlib.sha256((output/name).read_bytes()).hexdigest()==pin['sha256'],'VISION_EXCHANGE_DELIVERY_CHANGED'
    except Exception as error:result['code']=str(error) if str(error).isupper() else type(error).__name__
    finally:
        if owned:b['stop']();result['builderStopped']=b['resolve_running']() is None
        result['seconds']=round(time.monotonic()-started,2);(output/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
    return 0 if result['outcome'].startswith('PASS_') and result.get('builderStopped') else 1


if __name__=='__main__':raise SystemExit(main())
