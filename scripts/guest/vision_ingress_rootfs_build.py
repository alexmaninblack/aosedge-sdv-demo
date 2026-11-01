#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Offline rootfs FOTA artifact only; no boot/manufacturing image assembly."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import time

VERSION='6.1.1-vision-camera.4'


def require(ok, code):
    if not ok: raise RuntimeError(code)


def sha(path):
    value=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(4*1024**2),b''):value.update(block)
    return value.hexdigest()


def main():
    p=argparse.ArgumentParser()
    for name in ('project','source','evidence','recovery','source-proof','cloud-proof','boot-proof'):
        p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--revision',required=True)
    p.add_argument('--resume-rootfs-from',type=Path);a=p.parse_args()
    require(os.uname().machine=='aarch64' and os.uname().sysname=='Linux','ARM64_BUILDER_REQUIRED')
    require(re.fullmatch('[a-f0-9]{40}',a.revision),'REVISION_REQUIRED')
    for path in (a.project,a.source,a.evidence,a.recovery,a.source_proof,a.cloud_proof,a.boot_proof):
        require(path.is_absolute() and '..' not in path.parts and not any(v.is_symlink() for v in (path,*path.parents)),'PATH_UNSAFE')
    require(a.project==Path('/home/yocto/r61-build/factory42-475dc7c1ef3ac303'),'WARM_PROJECT_REQUIRED')
    require(a.source.name=='aos-vehicle-platform-'+a.revision and not a.evidence.exists(),'SOURCE_OR_ATTEMPT_INVALID')
    recovery=json.loads(a.recovery.read_bytes());source=json.loads(a.source_proof.read_bytes())
    cloud=json.loads(a.cloud_proof.read_bytes());boot=json.loads(a.boot_proof.read_bytes())
    require(recovery['outcome']=='PASS_SAME_VM_CHECKPOINT_RECOVERY' and all(recovery['cleanup'].values()),'RECOVERY_GATE_REQUIRED')
    require(source['outcome']=='PASS_TRANSIENT_NATIVE_STORE_INGRESS_POLICY' and all(source['cleanup'].values()),'NATIVE_SOURCE_GATE_REQUIRED')
    require(cloud['outcome']=='PASS_NATIVE_PREREQUISITES' and cloud['facts']['cloud']['ready']
            and all(cloud['cleanup'].values()),'ACCOUNT_RECIPIENT_GATE_REQUIRED')
    require(boot['installedBootMatches'] and not boot['bootUpdateRequired'] and all(boot['sourceMatches'].values()),'INSTALLED_BOOT_GATE_REQUIRED')
    a.evidence.mkdir(mode=0o700)
    lock=(a.project/'.vision-bootstrap-build.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    config=a.project/'yocto/build-main/conf/bblayers.conf';before=config.read_bytes()
    old=str(a.project/'yocto/aos-vehicle-platform/meta-aos-vehicle-platform').encode()
    require(before.count(old)==1,'MAIN_LAYER_BINDING_UNEXPECTED')
    selected=before.replace(old,str(a.source/'meta-aos-vehicle-platform').encode())
    prefix='cd '+shlex.quote(str(a.project/'yocto'))+'; . poky/oe-init-build-env build-main >/dev/null; '
    flags=['-R',str(a.source/'qualification/vision-ingress-1.conf')]
    result=dict(scenario='VISION_NATIVE_ROOTFS_FOTA_BUILD',outcome='NOT_COMPLETE',platformRevision=a.revision,
                phases=[],carlaRebuilt=False,manufacturingImageBuilt=False,bootBuilt=False,mainConfigurationRestored=False)
    began=time.monotonic()
    def save():
        path=a.evidence/'result.json';temporary=path.with_suffix('.pending')
        temporary.write_text(json.dumps(result,indent=2)+'\n');os.replace(temporary,path)
    def run(name,args,timeout):
        require(shutil.disk_usage(a.project).free>=60*1024**3,'BUILDER_FREE_SPACE_BELOW_60_GIB')
        print(json.dumps(dict(stage=name,state='STARTED')),flush=True);start=time.monotonic()
        with (a.evidence/(name+'.log')).open('wb') as output:
            done=subprocess.run(['bash','-e','-c',prefix+shlex.join(['bitbake',*flags,*args])],
                                cwd=a.project,stdout=output,stderr=subprocess.STDOUT,timeout=timeout)
        result['phases'].append(dict(stage=name,exit=done.returncode,seconds=round(time.monotonic()-start,2)));save()
        require(done.returncode==0,'ROOTFS_BUILD_STAGE_FAILED:'+name)
        print(json.dumps(dict(stage=name,state='COMPLETE')),flush=True)
    try:
        config.write_bytes(selected)
        run('configuration',['-e','aos-image-vision'],300)
        text=(a.evidence/'configuration.log').read_text()
        def variable(name):
            rows=re.findall('^'+re.escape(name)+'="(.*)"$',text,re.M)
            require(len(rows)==1,'CONFIG_VARIABLE_MISSING:'+name);return rows[0]
        for name,value in dict(BB_NO_NETWORK='1',AOS_UNIT_MODEL='aos-vision-vm',AOS_NODE_TYPE='aos-vision-vm-main',
            AOS_ROOTFS_IMAGE_VERSION=VERSION,AOS_VISION_CAMERA_INGRESS='1',
            AOS_COMPONENT_RUNTIME_PREFIX='aos-vision-vm-1.0.0-main-qemuarm64-').items():
            require(variable(name)==value,'CONFIG_MISMATCH:'+name)
        rootfs=Path(variable('IMAGE_ROOTFS'))
        require(rootfs.is_relative_to(a.project/'yocto/build-main/tmp'),'ROOTFS_SCOPE_INVALID')
        if a.resume_rootfs_from:
            require(a.resume_rootfs_from==a.project/'rootfs-fota-02/result.json','EXACT_COMPLETED_ROOTFS_RECEIPT_REQUIRED')
            previous=json.loads(a.resume_rootfs_from.read_bytes())
            require(previous['platformRevision']==a.revision and previous['mainConfigurationRestored']
                and previous['code']=='ROOTFS_VERSION_MISMATCH'
                and [(v['stage'],v['exit']) for v in previous['phases']]==[
                    ('configuration',0),('compile',0),('package-qa',0),('rootfs',0)],'ROOTFS_RESUME_NOT_RECONCILED')
            result['completedRootfsReused']='rootfs-fota-02'
        else:
            run('compile',['-c','compile','refpolicy-aos','aos-camera-access-platform'],3600)
            run('package-qa',['refpolicy-aos','aos-camera-access-platform'],3600)
            modules=list((a.project/'yocto/build-main/tmp/work/qemuarm64-aos-linux/refpolicy-aos').glob('*/packages-split/refpolicy-aos/usr/share/selinux/aos/camera_ingress.pp'))
            require(len(modules)==1 and modules[0].is_file(),'NATIVE_POLICY_MODULE_NOT_PACKAGED')
            run('rootfs',['-c','rootfs','aos-image-vision'],5400)
        require((rootfs/'etc/aos/version').read_text().strip()=='VERSION="'+VERSION+'"','ROOTFS_VERSION_MISMATCH')
        sm=json.loads((rootfs/'etc/aos/sm.cfg').read_bytes())
        require({r['type'] for r in sm['runtimes'] if r['plugin'] in ('rootfs','boot')}=={
            'aos-vision-vm-1.0.0-main-qemuarm64-rootfs','aos-vision-vm-1.0.0-main-qemuarm64-boot'},'RUNTIME_TYPES_CHANGED')
        require([r['name'] for r in json.loads((rootfs/'etc/aos/resources.cfg').read_bytes())]==['vision-camera-read'],'RESOURCE_CHANGED')
        require(not (rootfs/'usr/libexec/aos-vehicle-data-provider-launcher').exists(),'VDP_INCLUDED')
        passwd=[v.split(':') for v in (rootfs/'etc/passwd').read_text().splitlines()]
        require(any(v[0]=='aos-camera-access' and v[2:4]==['992','990'] for v in passwd),'CAMERA_STATIC_IDENTITY_CHANGED')
        for name in ('usr/libexec/aos-camera-ingress-launcher','usr/lib/systemd/system/aos-camera-ingress.service',
                     'etc/selinux/aos/contexts/files/file_contexts'):
            require((rootfs/name).is_file(),'NATIVE_INGRESS_FILE_MISSING')
        require('camera_ingress_exec_t' in (rootfs/'etc/selinux/aos/contexts/files/file_contexts').read_text(),'NATIVE_LABEL_MISSING')
        for path in (rootfs/'etc/systemd/system').rglob('aos-camera-ingress.service'):
            require(not path.parent.name.endswith(('.wants','.requires')),'INGRESS_BOOT_ENABLED')
        require(not (rootfs/'etc/machine-id').read_bytes().strip(),'MACHINE_ID_SHIPPED')
        for pattern in ('etc/ssh/ssh_host_*_key','etc/ssl/private/*'):
            require(not any(p.is_file() and not p.is_symlink() and p.stat().st_size for p in rootfs.glob(pattern)),'PRIVATE_KEY_SHIPPED')
        run('rootfs-envelope',['aos-rootfs-vision'],3600)
        artifact=a.project/'yocto/build-main/tmp/deploy/images/qemuarm64/update'/('aos-vision-rootfs-'+VERSION+'.squashfs')
        require(artifact.is_file() and not artifact.is_symlink() and 0<artifact.stat().st_size<8*1024**3,'FOTA_ARTIFACT_INVALID')
        with artifact.open('rb') as stream:require(stream.read(4)==b'hsqs','FOTA_NOT_RAW_SQUASHFS')
        result.update(outcome='ROOTFS_FOTA_BUILT_NOT_LIVE_QUALIFIED',rootfsVersion=VERSION,path=str(artifact),
            bytes=artifact.stat().st_size,sha256=sha(artifact),rootfsQa='PASS',offline=True)
    except Exception as error:
        result['code']=str(error) if isinstance(error,RuntimeError) else type(error).__name__
    finally:
        require(config.read_bytes()==selected,'LAYER_CONFIGURATION_CONCURRENT_CHANGE')
        config.write_bytes(before);result.update(mainConfigurationRestored=config.read_bytes()==before,
                                                seconds=round(time.monotonic()-began,2));save()
        print(json.dumps(result),flush=True);lock.close()
    return 0 if result['outcome']=='ROOTFS_FOTA_BUILT_NOT_LIVE_QUALIFIED' else 1


if __name__=='__main__':raise SystemExit(main())
