#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Own one offline Vision-services rootfs build, with the warm Builder lifecycle."""
import argparse
import json
import os
from pathlib import Path
import runpy
import shlex
import subprocess
import sys

import remote_harness as h

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts/distribution'))
sys.path.insert(0,str(ROOT/'scripts'))


def main():
    p=argparse.ArgumentParser();p.add_argument('--config',type=Path,required=True)
    p.add_argument('--name',required=True);a=p.parse_args()
    h.require(not (Path('/Volumes/SDV-Dev/sdv/build/vision-ingress')/a.name).exists(),'BUILD_RECEIPT_ALREADY_EXISTS')
    for key,value in dict(R61_BUILDER_ROOT='/Volumes/SDV-Dev/sdv/build/factory-builder',
        R61_BUILDER_VOLUME_UUID='F92AB578-22AA-4DAC-B8DD-7DC0EB831396',R61_BUILDER_SSH_PORT='10024',R61_BUILDER_DNS_PORT='18054').items():os.environ[key]=value
    b=runpy.run_path(str(ROOT/'scripts/r6-1-builder'),run_name='builder_library')
    h.require(b['resolve_running']() is None,'BUILDER_ALREADY_IN_USE')
    try:
        b['start'](False);b['wait_ready']()
        from vision_vm_campaign import configuration
        c=configuration(a.config)
        boot_records=Path(c['records'])/'vision-services-boot-02'
        inventory=json.loads((boot_records/'boot-inventory.json').read_bytes())
        prior=json.loads(Path('/Volumes/SDV-Dev/sdv/build/vision-ingress/native-primitives-01/boot-compatibility.json').read_bytes())
        h.require(inventory['readOnlyInspection'] and inventory['bootChanged'] is False and len(inventory['initramfs'])==1,'CURRENT_INSTALLED_BOOT_REQUIRED')
        current=inventory['initramfs'][0]
        h.require(current['helpers']==prior['helpers'] and len(current['helpers'])==4,'INSTALLED_UPDATE_HELPERS_CHANGED')
        boot=dict(prior,initramfsSha256=current['sha256'],currentBootRechecked=True,
            previousArchiveSha256=prior['initramfsSha256'],archiveIdentityChanged=current['sha256']!=prior['initramfsSha256'],
            archiveComparison='ALL_FOUR_INSTALLED_UPDATE_HELPERS_EQUAL_PINNED_SOURCE',bootUpdateRequired=False)
        py=c['main']['packageRoot']+'/demo-artifacts/aosedge-sdv-demo/host-runtime/python/bin/python3.12'
        idle="import json,pathlib;s=json.loads((pathlib.Path.home()/'SDV-Vision-Camera-Image-Lab-Data/.run/demo-current/journal.json').read_bytes());i=s['vehicles']['test'];assert i['localVmId']=='89273f16-4be0-4b22-b4cb-58d08533c8bc' and i['unitId']=='af6d074a-6ce1-49ba-b613-0476e7b6d1b5';assert i['runtime']['state']==s['source']['state']=='STOPPED';print('SAME_VISION_IDLE')"
        h.require(h.remote(c['transport'],shlex.join([py,'-I','-B','-c',idle]),timeout=15).strip()=='SAME_VISION_IDLE','VISION_IDLE_REQUIRED')
        # The installed boot receipt is from this retained VM. No boot update is
        # part of this packet; revalidate its immutable upstream inputs as well.
        code='''import hashlib,json,pathlib,subprocess
p=pathlib.Path('/home/yocto/r61-build/factory42-475dc7c1ef3ac303/yocto')
b=__BOOT__
assert b['installedBootMatches'] and not b['bootUpdateRequired'] and all(b['sourceMatches'].values())
checks=dict(metaAosRevisionMatches=subprocess.check_output(['git','-C',str(p/'meta-aos'),'rev-parse','HEAD'],text=True).strip()==b['metaAosRevision'])
s=p/'meta-aos/recipes-core/initrdscripts/initramfs-framework'
checks['sourceHelpersMatch']=all(hashlib.sha256((s/k).read_bytes()).hexdigest()==v for k,v in b['helpers'].items())
print(json.dumps(checks),flush=True)
assert all(checks.values())
print('INSTALLED_BOOT_INPUTS_UNCHANGED')
'''.replace('__BOOT__',repr(boot))
        checked=subprocess.run(b['ssh_base']()+['python3 -c '+shlex.quote(code)],capture_output=True,text=True,timeout=30)
        print(checked.stdout[:4096],flush=True)
        h.require(checked.returncode==0,'INSTALLED_BOOT_INPUTS_REQUIRE_RECONCILIATION')
        boot['cleanup']=dict(visionStopped=True,sourceStopped=True)
        h.atomic(boot_records/'boot-compatibility.json',boot)
        return subprocess.run([sys.executable,'-B',str(ROOT/'scripts/qualification/vision_permanent_build.py'),
            '--config',str(a.config),'--name',a.name,'--cloud-proof','vision-services-platform-preflight-01','--services-packet'],cwd=ROOT).returncode
    finally:
        if b['resolve_running']() is not None:b['stop']()
        h.require(b['resolve_running']() is None,'BUILDER_NOT_STOPPED')


if __name__=='__main__':raise SystemExit(main())
