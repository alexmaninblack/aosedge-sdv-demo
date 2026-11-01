#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""One monotonic owned-Builder capacity repair; preserve caches and checkpoint."""
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys

import remote_harness as h


def main():
    for k,v in dict(R61_BUILDER_ROOT='/Volumes/SDV-Dev/sdv/build/factory-builder',
        R61_BUILDER_VOLUME_UUID='F92AB578-22AA-4DAC-B8DD-7DC0EB831396',
        R61_BUILDER_SSH_PORT='10024',R61_BUILDER_DNS_PORT='18054').items():os.environ[k]=v
    root=Path(__file__).resolve().parents[2]
    sys.path.insert(0,str(root/'scripts'))
    b=runpy.run_path(str(root/'scripts/r6-1-builder'),run_name='builder_library')
    output=Path('/Volumes/SDV-Dev/sdv/build/vision-ingress/builder-capacity-01.json')
    disk=b['OVERLAY']
    checkpoint=disk.with_name('r61-yocto-builder-before-grow-320.qcow2')
    if output.exists():
        h.require(json.loads(output.read_bytes())==dict(state='GROWTH_INTENT',fromGiB=220,toGiB=320,checkpointPreserved=True)
            and b['resolve_running']() is None,'CAPACITY_RESUME_INTENT_REQUIRED')
        before=b['image_info'](checkpoint);after=b['image_info'](disk)
        h.require(before['virtual-size']==220*1024**3 and after['virtual-size']==320*1024**3
            and before['full-backing-filename']==after['full-backing-filename'],'CAPACITY_RESUME_NOT_RECONCILED')
    else:
        pid=b['resolve_running']();h.require(pid is not None,'OWNED_BUILDER_REQUIRED');b['verify_owned_process'](pid)
        p=subprocess.run(b['ssh_base']()+["pgrep -f '[b]itbake|[p]seudo'"],capture_output=True,timeout=15)
        h.require(p.returncode==1,'ACTIVE_BUILDER_TASK_BLOCKS_GROWTH')
        b['stop']();b['verify_prepared']();before=b['image_info'](disk)
        h.require(before['virtual-size']==220*1024**3,'EXACT_220_GIB_GROWTH_SOURCE_REQUIRED')
        h.require(not checkpoint.exists(),'CAPACITY_CHECKPOINT_EXISTS_RECONCILE')
        subprocess.run(['/bin/cp','-c',str(disk),str(checkpoint)],check=True,capture_output=True,timeout=60);checkpoint.chmod(0o400)
        h.atomic(output,dict(state='GROWTH_INTENT',fromGiB=220,toGiB=320,checkpointPreserved=True))
        subprocess.run([b['command_path'](b['QEMU_IMG']),'resize',str(disk),'320G'],check=True,capture_output=True,timeout=30)
        after=b['image_info'](disk)
        h.require(after['virtual-size']==320*1024**3 and after['full-backing-filename']==before['full-backing-filename'],'CAPACITY_GROWTH_UNCONFIRMED')
    b['verify_prepared']();b['start'](False);b['wait_ready']()
    code='''import json,pathlib,shutil,subprocess
assert subprocess.check_output(['findmnt','-n','-o','SOURCE','/'],text=True).strip()=='/dev/vda1'
assert subprocess.check_output(['findmnt','-n','-o','UUID','/'],text=True).strip()=='1748280c-69ff-4c85-8e0a-f34f6530c5a2'
if shutil.disk_usage('/').total<300*1024**3:
 subprocess.run(['sudo','-n','growpart','/dev/vda','1'],check=True,capture_output=True,timeout=30)
 subprocess.run(['sudo','-n','resize2fs','/dev/vda1'],check=True,capture_output=True,timeout=120)
usage=shutil.disk_usage('/');assert usage.total>300*1024**3 and usage.free>100*1024**3
assert pathlib.Path('/home/yocto/yocto-cache/downloads').is_dir() and pathlib.Path('/home/yocto/yocto-cache/sstate-cache').is_dir()
print(json.dumps(dict(outcome='PASS_OWNED_BUILDER_GROWTH',fromGiB=220,toGiB=320,rootFilesystemUuidPreserved=True,cachesPreserved=True,checkpointPreserved=True,availableGiB=round(usage.free/1024**3,2))))
'''
    result=json.loads(h.run(b['ssh_base']()+['python3 -'],data=code,timeout=180));h.atomic(output,result)
    print(json.dumps(result),flush=True)


if __name__=='__main__':main()
