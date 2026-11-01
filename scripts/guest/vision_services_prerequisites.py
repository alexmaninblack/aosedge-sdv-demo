#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""One owned SSD Builder inventory, no image task or dependency installation."""
import json
import argparse
import os
from pathlib import Path
import subprocess
import shlex
import time


def main():
    source=Path(__file__).resolve().parents[2];root=Path('/Volumes/SDV-Dev/sdv/build/factory-builder')
    parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,choices=(1,2),default=1);args=parser.parse_args()
    parent=Path('/Volumes/SDV-Dev/sdv/build/vision-services')
    if args.attempt==2:
        previous=json.loads((parent/'prerequisites-01/result.json').read_bytes())
        assert previous['outcome']=='NOT_COMPLETE' and previous['builderStopped']
    records=parent/('prerequisites-'+str(args.attempt).zfill(2))
    assert not records.exists(),'PREREQUISITE_RECEIPT_EXISTS_RECONCILE';records.mkdir(parents=True,mode=0o700)
    environment=dict(os.environ,R61_BUILDER_ROOT=str(root),R61_BUILDER_VOLUME_UUID='F92AB578-22AA-4DAC-B8DD-7DC0EB831396',R61_BUILDER_SSH_PORT='10024',R61_BUILDER_DNS_PORT='18054')
    builder=[os.sys.executable,'-B',str(source/'scripts/r6-1-builder')];began=time.monotonic();owned=False
    result=dict(scenario='VISION_SERVICES_BUILD_PREREQUISITES',outcome='NOT_COMPLETE',imageTasks=False)
    def run(args,timeout=180):
        value=subprocess.run(builder+args,env=environment,capture_output=True,text=True,timeout=timeout)
        assert value.returncode==0,'BUILDER_COMMAND_FAILED';return value.stdout
    try:
        status=run(['status']);assert 'is running' not in status,'BUILDER_OTHER_OWNER_RUNNING'
        print('SSD_BUILDER_START',flush=True);owned=True;run(['start']);run(['wait'])
        code="import json,pathlib,shutil,subprocess; packages=['libopencv-dev','coinor-libipopt-dev','libcppad-dev','libeigen3-dev','g++','cmake','ninja-build']; rows={p:subprocess.run(['dpkg-query','-W','-f=${Version}',p],text=True,capture_output=True).stdout for p in packages}; print(json.dumps(dict(packages=rows,guestFreeGiB=round(shutil.disk_usage('/home/yocto').free/2**30,1),python=shutil.which('python3'),pkgConfig=shutil.which('pkg-config'))))"
        output=run(['run','python3 -c '+shlex.quote(code)],30)
        result.update(outcome='PASS_READONLY_BUILDER_INVENTORY',inventory=json.loads(output))
    finally:
        if owned:
            print('SSD_BUILDER_STOP',flush=True);run(['stop']);assert 'is running' not in run(['status']);result['builderStopped']=True
        result['seconds']=round(time.monotonic()-began,2);(records/'result.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(result),flush=True)


if __name__=='__main__':main()
