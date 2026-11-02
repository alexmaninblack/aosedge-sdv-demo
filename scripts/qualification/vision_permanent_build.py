#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Named, recovery/account-gated SSD rootfs-FOTA build and immutable acquisition."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import runpy
import shlex
import shutil
import subprocess
import sys
import time

import remote_harness as h
from vision_vm_campaign import configuration

ROOT=Path(__file__).resolve().parents[2]
PLATFORM=ROOT.parent/'vision-camera-platform'
PROJECT=Path('/home/yocto/r61-build/factory42-475dc7c1ef3ac303')
BUILD=Path('/Volumes/SDV-Dev/sdv/build/vision-ingress')


def main():
    p=argparse.ArgumentParser();p.add_argument('--config',type=Path,required=True)
    p.add_argument('--name',required=True);p.add_argument('--cloud-proof',required=True)
    p.add_argument('--services-packet',action='store_true')
    reuse=p.add_mutually_exclusive_group()
    reuse.add_argument('--reuse-completed-rootfs-02',action='store_true')
    reuse.add_argument('--reuse-completed-rootfs-05',action='store_true');a=p.parse_args()
    c=configuration(a.config);q=shlex.quote
    h.require(a.name.startswith('rootfs-fota-') and a.name.removeprefix('rootfs-fota-').isdecimal(),'FOTA_NAME_INVALID')
    h.require(any(a.cloud_proof.startswith(prefix) and a.cloud_proof.removeprefix(prefix).isdecimal()
                  for prefix in (('vision-services-platform-preflight-',) if a.services_packet else ('ingress-verification-','ingress-cloud-'))),'CLOUD_PROOF_NAME_INVALID')
    cloud=Path(c['records'])/a.cloud_proof/'result.json';proof=json.loads(cloud.read_bytes())
    if a.services_packet:
        h.require(proof['outcome']=='PASS_VISION_SERVICES_PLATFORM_RECIPIENTS_AND_VERSIONS' and proof['cloudMutation'] is False
            and all(v['recipientScopeComplete'] and not v['publicationCollision'] for v in proof['components'].values()),'ACCOUNT_GATE_REQUIRED')
        h.require(not a.reuse_completed_rootfs_02 and not a.reuse_completed_rootfs_05,'SERVICES_BUILD_CANNOT_REUSE_LEGACY_ROOTFS')
    else:h.require(proof['outcome']=='PASS_NATIVE_PREREQUISITES' and proof['facts']['cloud']['ready']
              and all(proof['cleanup'].values()),'ACCOUNT_GATE_REQUIRED')
    h.require(shutil.disk_usage(BUILD).free>=60*1024**3,'SSD_FREE_SPACE_BELOW_60_GIB')
    h.require(not h.run(['git','-C',str(PLATFORM),'diff','HEAD','--name-only']),'COMMITTED_PLATFORM_REQUIRED')
    revision=h.run(['git','-C',str(PLATFORM),'rev-parse','HEAD']).strip()
    subprocess.run([sys.executable,'-B',str(PLATFORM/'tools'/('check_vision_services_delivery.py' if a.services_packet else 'check_camera_ingress_delivery.py'))],cwd=PLATFORM,check=True)
    for key,value in dict(R61_BUILDER_ROOT='/Volumes/SDV-Dev/sdv/build/factory-builder',
        R61_BUILDER_VOLUME_UUID='F92AB578-22AA-4DAC-B8DD-7DC0EB831396',R61_BUILDER_SSH_PORT='10024',R61_BUILDER_DNS_PORT='18054').items():os.environ[key]=value
    b=runpy.run_path(str(ROOT/'scripts/r6-1-builder'),run_name='builder_library')
    pid=b['resolve_running']();h.require(pid is not None,'OWNED_BUILDER_REQUIRED');b['verify_owned_process'](pid)
    ssh=b['ssh_base']();output=BUILD/a.name;h.require(not output.exists(),'FOTA_ATTEMPT_EXISTS_RECONCILE');output.mkdir(mode=0o700)
    source=PROJECT/'yocto'/('aos-vehicle-platform-'+revision);evidence=PROJECT/a.name
    archive=subprocess.check_output(['git','-C',str(PLATFORM),'archive',revision],timeout=30)
    export_sha=hashlib.sha256(archive).hexdigest()
    export='''import json,pathlib,sys,subprocess
p=pathlib.Path(__SOURCE_PATH__);receipt=p/'.vision-source-export.json'
if p.exists():
 assert receipt.is_file() and json.loads(receipt.read_bytes())==dict(revision=__SOURCE_REVISION__,archiveSha256=__ARCHIVE_SHA256__),'EXISTING_SOURCE_EXPORT_UNCONFIRMED'
else:
 p.mkdir(mode=0o700);data=sys.stdin.buffer.read();import hashlib
 assert hashlib.sha256(data).hexdigest()==__ARCHIVE_SHA256__
 subprocess.run(['tar','-xf','-','-C',str(p)],input=data,check=True)
 receipt.write_text(json.dumps(dict(revision=__SOURCE_REVISION__,archiveSha256=__ARCHIVE_SHA256__)));receipt.chmod(0o444)
print('SOURCE_EXPORT_READY')
'''.replace('__SOURCE_PATH__',repr(str(source))).replace('__SOURCE_REVISION__',repr(revision)).replace('__ARCHIVE_SHA256__',repr(export_sha))
    done=subprocess.run(ssh+['python3 -c '+q(export)],input=archive,capture_output=True,timeout=45)
    h.require(done.returncode==0,'PLATFORM_EXPORT_FAILED')
    inputs={
        'vision_ingress_rootfs_build.py':ROOT/'scripts/guest/vision_ingress_rootfs_build.py',
        'recovery.json':Path(c['records'])/('vision-services-recovery-01' if a.services_packet else 'ingress-recovery-01')/'result.json',
        'source-proof.json':Path(c['records'])/'vision-services-native-live-19/group-alias-acceptance.json' if a.services_packet else Path(c['records'])/'ingress-native-source-01/result.json',
        'cloud-proof.json':cloud,'boot-proof.json':Path(c['records'])/'vision-services-boot-02/boot-compatibility.json' if a.services_packet else BUILD/'native-primitives-01/boot-compatibility.json'}
    remote_inputs=PROJECT/'.tmp'/a.name
    h.run(ssh+['test ! -e '+q(str(evidence))+' && mkdir -m 700 '+q(str(remote_inputs))],timeout=15)
    for name,path in inputs.items():h.run(b['scp_base']()+[str(path),'yocto@127.0.0.1:'+str(remote_inputs/name)],timeout=20)
    command=['python3',str(remote_inputs/'vision_ingress_rootfs_build.py'),'--project',str(PROJECT),'--source',str(source),
             '--evidence',str(evidence),'--revision',revision]
    if a.services_packet:command+=['--services-packet']
    for flag,name in (('recovery','recovery.json'),('source-proof','source-proof.json'),('cloud-proof','cloud-proof.json'),('boot-proof','boot-proof.json')):
        command+=['--'+flag,str(remote_inputs/name)]
    if a.reuse_completed_rootfs_02:
        prior=json.loads((BUILD/'rootfs-fota-02/result.json').read_bytes())
        h.require(prior['code']=='ROOTFS_VERSION_MISMATCH' and prior['platformRevision']==revision
                  and prior['mainConfigurationRestored'],'EXACT_ROOTFS_RESUME_REQUIRED')
        command+=['--resume-rootfs-from',str(PROJECT/'rootfs-fota-02/result.json')]
    if a.reuse_completed_rootfs_05:
        prior=json.loads((BUILD/'rootfs-fota-05/result.json').read_bytes())
        h.require(prior['code']=='ROOTFS_BUILD_STAGE_FAILED:rootfs-envelope' and prior['platformRevision']==revision
                  and prior['mainConfigurationRestored'],'EXACT_ROOTFS_ENVELOPE_RESUME_REQUIRED')
        command+=['--resume-rootfs-from',str(PROJECT/'rootfs-fota-05/result.json')]
    h.atomic(output/'inputs.json',dict(platformRevision=revision,sourceExportSha256=export_sha,
                                      inputs={k:h.digest(v) for k,v in inputs.items()}))
    started=time.monotonic()
    process=subprocess.Popen(ssh+[shlex.join(command)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    with (output/'progress.jsonl').open('x') as log:
        for line in process.stdout:
            h.require(log.tell()<2**20,'BUILD_PROGRESS_LIMIT');log.write(line);log.flush()
            if line.startswith('{'):print(line.strip(),flush=True)
    code=process.wait(timeout=15);stderr=process.stderr.read(4096)
    h.atomic(output/'transport.json',dict(exit=code,stderrPresent=bool(stderr),seconds=round(time.monotonic()-started,2)))
    raw=h.run(ssh+['cat '+q(str(evidence/'result.json'))],timeout=15);result=json.loads(raw);h.atomic(output/'result.json',result)
    h.require(code==0 and result['outcome']=='ROOTFS_FOTA_BUILT_NOT_LIVE_QUALIFIED'
              and result['mainConfigurationRestored'],'ROOTFS_BUILD_NOT_COMPLETE')
    target=output/'vision-rootfs.squashfs'
    h.run(b['scp_base']()+['yocto@127.0.0.1:'+result['path'],str(target)],timeout=900)
    h.require(target.stat().st_size==result['bytes'] and h.digest(target)==result['sha256'],'FOTA_TRANSFER_CHANGED');target.chmod(0o444)
    h.atomic(output/'artifact.json',dict(path=str(target),bytes=result['bytes'],sha256=result['sha256'],
        rootfsVersion=result['rootfsVersion'],platformRevision=revision,status='UNSIGNED_ROOTFS_FOTA_NOT_INSTALLED'))
    h.run(ssh+['mv '+q(str(remote_inputs))+' '+q(str(evidence/'inputs'))],timeout=15)
    print(json.dumps(dict(outcome='ROOTFS_FOTA_FROZEN_NOT_INSTALLED',artifact=str(target))),flush=True)


if __name__=='__main__':main()
