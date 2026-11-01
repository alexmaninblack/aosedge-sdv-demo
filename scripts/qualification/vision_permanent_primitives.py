#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Recovery-gated SSD native-policy/launcher compile and installed-boot pin."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import runpy
import shlex
import subprocess
import sys

import remote_harness as h
from vision_vm_campaign import configuration

ROOT=Path(__file__).resolve().parents[2]
PLATFORM=ROOT.parent/'vision-camera-platform'
BUILD=Path('/Volumes/SDV-Dev/sdv/build/vision-ingress')
PROJECT=Path('/home/yocto/r61-build/factory42-475dc7c1ef3ac303')


def main():
    p=argparse.ArgumentParser();p.add_argument('--config',type=Path,required=True);p.add_argument('--name',required=True)
    p.add_argument('--reuse-installed-boot-pin',action='store_true')
    a=p.parse_args();c=configuration(a.config)
    h.require(a.name.startswith('native-primitives-') and a.name.removeprefix('native-primitives-').isdecimal(),'PRIMITIVE_NAME_INVALID')
    recovery=json.loads((Path(c['records'])/'ingress-recovery-01/result.json').read_bytes())
    h.require(recovery['outcome']=='PASS_SAME_VM_CHECKPOINT_RECOVERY' and recovery['checkpointReady']
        and all(recovery['cleanup'].values()) and not recovery['updateAttempted'],'RECOVERY_GATE_REQUIRED')
    boot=json.loads((Path(c['records'])/'ingress-boot-01/result.json').read_bytes())
    h.require(boot['facts']['bootChanged'] is False and all(boot['cleanup'].values()),'READ_ONLY_BOOT_PIN_REQUIRED')
    boot_images=boot['facts']['initramfs'];h.require(len(boot_images)==1,'BOOT_IMAGE_AMBIGUOUS')
    for key,value in dict(R61_BUILDER_ROOT='/Volumes/SDV-Dev/sdv/build/factory-builder',
        R61_BUILDER_VOLUME_UUID='F92AB578-22AA-4DAC-B8DD-7DC0EB831396',R61_BUILDER_SSH_PORT='10024',R61_BUILDER_DNS_PORT='18054').items():os.environ[key]=value
    b=runpy.run_path(str(ROOT/'scripts/r6-1-builder'),run_name='builder_library')
    pid=b['resolve_running']();h.require(pid is not None,'OWNED_WARM_BUILDER_REQUIRED');b['verify_owned_process'](pid)
    ssh=b['ssh_base']();output=BUILD/a.name;h.require(not output.exists(),'PRIMITIVE_OUTPUT_EXISTS_RECONCILE')
    output.mkdir(mode=0o700)
    native=PLATFORM/'meta-aos-vehicle-platform'
    files={
        'camera_ingress.te':native/'recipes-security/refpolicy/files/camera_ingress.te',
        'aos-camera-ingress-launcher.c':native/'recipes-aos/aos-camera-access-platform/files/aos-camera-ingress-launcher.c',
        'camera_ingress_compile_worker.py':PLATFORM/'tools/camera_ingress_compile_worker.py',
        'vision_delivery_guest.py':ROOT/'scripts/qualification/vision_delivery_guest.py'}
    source=PROJECT/'.tmp'/a.name;remote_output=PROJECT/a.name
    h.run(ssh+['test ! -e '+shlex.quote(str(source))+' && test ! -e '+shlex.quote(str(remote_output))+' && mkdir -m 700 '+shlex.quote(str(source))],timeout=10)
    for name,path in files.items():h.run(b['scp_base']()+[str(path),'yocto@127.0.0.1:'+str(source/name)],timeout=15)
    pin=r'''import hashlib,json,pathlib,runpy,subprocess
p=pathlib.Path(PROJECT);tool=pathlib.Path(TOOL)
assert hashlib.sha256(tool.read_bytes()).hexdigest()==TOOL_SHA
ns=runpy.run_path(str(tool));image=p/'yocto/build-main/tmp/deploy/images/qemuarm64/aos-image-initramfs-qemuarm64.rootfs-20261101070727.cpio.gz'
raw=image.read_bytes();assert len(raw)==BOOT['bytes'] and hashlib.sha256(raw).hexdigest()==BOOT['sha256']
helpers=ns['archive_helpers'](raw);assert set(helpers)=={'aosupdate','machineid','opendisk','vardir'}
source=p/'yocto/meta-aos/recipes-core/initrdscripts/initramfs-framework'
matches={k:hashlib.sha256((source/k).read_bytes()).hexdigest()==v for k,v in helpers.items()};assert all(matches.values())
revision=subprocess.check_output(['git','-C',str(p/'yocto/meta-aos'),'rev-parse','HEAD'],text=True).strip()
assert revision=='176da6346b1199f854106dede4cc49604174619c'
print(json.dumps(dict(installedBootMatches=True,initramfsSha256=BOOT['sha256'],metaAosRevision=revision,helpers=helpers,sourceMatches=matches,bootUpdateRequired=False)))
'''.replace('PROJECT',repr(str(PROJECT))).replace('TOOL_SHA',repr(h.digest(files['vision_delivery_guest.py']))).replace('TOOL',repr(str(source/'vision_delivery_guest.py'))).replace('BOOT',repr(boot_images[0]))
    if a.reuse_installed_boot_pin:
        prior=json.loads((BUILD/'native-primitives-01/boot-compatibility.json').read_bytes())
        h.require(prior['installedBootMatches'] and not prior['bootUpdateRequired']
            and all(prior['sourceMatches'].values()),'EXISTING_INSTALLED_BOOT_PIN_REQUIRED')
        h.atomic(output/'boot-compatibility.json',prior)
    else:h.atomic(output/'boot-compatibility.json',json.loads(h.run(ssh+['python3 -'],data=pin,timeout=30)))
    print(json.dumps(dict(stage='targeted-native-policy-launcher',state='STARTED')),flush=True)
    result=h.run(ssh+[shlex.join(['python3',str(source/'camera_ingress_compile_worker.py'),'--input',str(source),'--evidence',str(remote_output),'--native-policy'])],timeout=120)
    value=json.loads(result);h.require(value['outcome']=='PASS_TARGETED_INGRESS_PRIMITIVES','NATIVE_PRIMITIVES_FAILED')
    for name in ('camera_ingress.pp','aos-camera-ingress-launcher','result.json'):
        h.run(b['scp_base']()+['yocto@127.0.0.1:'+str(remote_output/name),str(output/name)],timeout=20)
    for name,row in value['files'].items():h.require(h.digest(output/name)==row['sha256'],'PRIMITIVE_TRANSFER_CHANGED')
    h.run(ssh+['mv '+shlex.quote(str(source))+' '+shlex.quote(str(remote_output/'inputs'))],timeout=10)
    print(json.dumps(dict(outcome='PASS_NATIVE_PRIMITIVES_AND_INSTALLED_BOOT_PIN',output=str(output),imageBuilt=False)),flush=True)


if __name__=='__main__':main()
