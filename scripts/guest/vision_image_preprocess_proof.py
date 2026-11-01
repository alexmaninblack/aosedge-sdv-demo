#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Prove image presets on SSD without rebuilding a disk/FOTA or touching M4."""
import fcntl
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import time


def preset_links(root, name):
    # Enumerate entries before matching: Python 3.10 literal glob can omit
    # an absolute guest symlink that is dangling on the Builder host.
    return [str(path.relative_to(root)) for path in (root/'etc/systemd/system').rglob('*')
            if path.name==name and path.is_symlink()
            and path.parent.name.endswith(('.wants','.requires'))]


def main():
    project=Path('/home/yocto/r61-build/factory42-475dc7c1ef3ac303');source=Path(sys.argv[1])
    assert os.uname().machine=='aarch64' and source.parent==project/'yocto'
    name=sys.argv[2] if len(sys.argv)>2 else 'vision-image-preprocess-01'
    assert re.fullmatch('vision-image-preprocess-[0-9]{2}',name)
    output=project/name;assert not output.exists();output.mkdir(mode=0o700)
    config=project/'yocto/build-main/conf/bblayers.conf';before=config.read_bytes()
    old=str(project/'yocto/aos-vehicle-platform/meta-aos-vehicle-platform').encode();assert before.count(old)==1
    selected=before.replace(old,str(source/'meta-aos-vehicle-platform').encode())
    lock=(project/'.vision-bootstrap-build.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    flags=['-R',str(source/'qualification/vision-ingress-1.conf')]
    prefix='cd '+shlex.quote(str(project/'yocto'))+'; . poky/oe-init-build-env build-main >/dev/null; '
    result=dict(outcome='NOT_COMPLETE',fotaBuilt=False,manufacturingDiskBuilt=False,bootBuilt=False,cloudMutation=False)
    began=time.monotonic()
    try:
        config.write_bytes(selected)
        for name,args in (('configuration',['-e','aos-image-vision']),
                          ('image-preprocess',['-c','prepare_vision_rootfs_fota','aos-image-vision']),
                          ('idempotent-repeat',['-c','prepare_vision_rootfs_fota','aos-image-vision'])):
            with (output/(name+'.log')).open('wb') as log:
                done=subprocess.run(['bash','-e','-c',prefix+shlex.join(['bitbake',*flags,*args])],stdout=log,stderr=subprocess.STDOUT,timeout=300)
            assert done.returncode==0,'IMAGE_PREPROCESS_STEP_FAILED'
        text=(output/'configuration.log').read_text()
        def variable(name):return re.findall('^'+re.escape(name)+'="(.*)"$',text,re.M)[0]
        assert variable('BB_NO_NETWORK')=='1'
        assert all(value in variable('IMAGE_PREPROCESS_COMMAND') for value in ('systemd_preset_all','selinux_set_labels'))
        root=Path(variable('IMAGE_ROOTFS'));assert root.is_relative_to(project/'yocto/build-main/tmp')
        def links(name):return preset_links(root,name)
        network=links('systemd-networkd.service')+links('systemd-networkd.socket');ssh=links('sshd.socket')
        assert network and ssh,'IMAGE_BOOTSTRAP_PRESETS_MISSING'
        exported=project/'yocto/build-main/tmp/work-shared/aos-vision-fota-qemuarm64/rootfs'
        assert exported.is_symlink() and exported.resolve()==root.resolve(),'INDEPENDENT_FOTA_SOURCE_MISSING'
        for log in ('image-preprocess.log','idempotent-repeat.log'):
            assert not re.search(r'Running task[^\n]*:do_(image_ext4|image_wic|create_rw_parts|create_shared_links)\)',
                                 (output/log).read_text()),'MANUFACTURING_TASK_EXECUTED'
        result.update(outcome='PASS_OFFLINE_IMAGE_PREPROCESS',networkPresetLinks=network,sshPresetLinks=ssh,
                      networkGuardPreserved=True,independentFotaInput=True,idempotentRepeat=True,
                      sourceRevision=source.name.removeprefix('aos-vehicle-platform-'))
    except Exception as error:result['code']=str(error) if isinstance(error,AssertionError) else type(error).__name__
    finally:
        assert config.read_bytes()==selected;config.write_bytes(before)
        result.update(mainConfigurationRestored=config.read_bytes()==before,seconds=round(time.monotonic()-began,2))
        (output/'result.json').write_text(json.dumps(result,indent=2)+'\n');lock.close();print(json.dumps(result))
    return 0 if result['outcome']=='PASS_OFFLINE_IMAGE_PREPROCESS' else 1


if __name__=='__main__':raise SystemExit(main())
