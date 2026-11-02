#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""One SSD-only compile campaign; no image tasks or prepared source edits."""
import hashlib
import json
import os
from pathlib import Path
import runpy
import shlex
import subprocess
import sys
import time
import argparse

ROOT=Path(__file__).resolve().parents[2]
PROJECT=Path('/home/yocto/r61-build/factory42-475dc7c1ef3ac303')


def main():
    p=argparse.ArgumentParser();p.add_argument('--attempt',type=int,choices=(1,2,3,4),default=1);a=p.parse_args();name='resource-capacity-'+str(a.attempt).zfill(2)
    if a.attempt>1:
        prior=json.loads((Path('/Volumes/SDV-Dev/sdv/build/vision-services')/('resource-capacity-'+str(a.attempt-1).zfill(2))/'result.json').read_bytes());assert prior['code']=='VISION_RESOURCE_CAPACITY_COMPILE_FAILED' and prior['builderStopped']
    output=Path('/Volumes/SDV-Dev/sdv/build/vision-services')/name;assert not output.exists();output.mkdir(mode=0o700)
    for k,v in dict(R61_BUILDER_ROOT='/Volumes/SDV-Dev/sdv/build/factory-builder',R61_BUILDER_VOLUME_UUID='F92AB578-22AA-4DAC-B8DD-7DC0EB831396',R61_BUILDER_SSH_PORT='10024',R61_BUILDER_DNS_PORT='18054').items():os.environ[k]=v
    sys.path.insert(0,str(ROOT/'scripts'));b=runpy.run_path(str(ROOT/'scripts/r6-1-builder'),run_name='builder_library')
    sys.path.insert(0,str(ROOT/'scripts/distribution'));from build_scratch import directory
    source=ROOT.parent/'vision-camera-platform/tools/vision_resource_capacity_compile_worker.py'
    result=dict(outcome='NOT_COMPLETE',imageBuilt=False);owned=False;start=time.monotonic()
    def run(args,timeout=60):
        p=subprocess.run(args,capture_output=True,text=True,timeout=timeout)
        if p.returncode:(output/'diagnostic.log').write_text((p.stdout+p.stderr)[-8192:]);raise ValueError('VISION_RESOURCE_CAPACITY_COMMAND_FAILED')
        return p.stdout
    try:
        assert b['resolve_running']() is None;owned=True;b['start'](False);b['wait_ready']()
        with directory(ROOT) as scratch:
            local=scratch/'worker.py';local.write_bytes(source.read_bytes());remote=PROJECT/'.tmp'/('vision-'+name+'-worker.py')
            run(b['scp_base']()+[str(local),'yocto@127.0.0.1:'+str(remote)],30)
        command='python3 -B '+shlex.quote(str(remote))+' --evidence '+shlex.quote(str(PROJECT/('vision-'+name)))
        done=subprocess.run(b['ssh_base']()+[command],capture_output=True,text=True,timeout=2500)
        print(done.stdout[-2000:],flush=True)
        for name in ('result.json','aos-servicemanager-configure-input.json','aos-servicemanager-configure.log','aos-servicemanager-compile.log','aos-communicationmanager-configure-input.json','aos-communicationmanager-configure.log','aos-communicationmanager-compile.log','aos_sm_app','aos_cm_app'):
            optional=subprocess.run(b['scp_base']()+['yocto@127.0.0.1:'+str(PROJECT/('vision-'+output.name)/name),str(output/name)],capture_output=True,timeout=30)
        if (output/'result.json').exists():result.update(json.loads((output/'result.json').read_bytes()))
        assert done.returncode==0,'VISION_RESOURCE_CAPACITY_COMPILE_FAILED'
        for name,pin in result['files'].items():assert hashlib.sha256((output/name).read_bytes()).hexdigest()==pin['sha256']
        run(b['ssh_base']()+['rm -- '+shlex.quote(str(remote))],15)
    except Exception as error:result['outcome']='NOT_COMPLETE';result['code']=str(error) if str(error).isupper() else type(error).__name__
    finally:
        if owned:b['stop']();result['builderStopped']=b['resolve_running']() is None
        result['seconds']=round(time.monotonic()-start,2);(output/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
    return 0 if result['outcome'].startswith('PASS_') else 1


if __name__=='__main__':raise SystemExit(main())
