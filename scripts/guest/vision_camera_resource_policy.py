#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Compile one diagnostic module with the retained Yocto native toolchain."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import time


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True);p.add_argument('--sha256',required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    project=Path('/home/yocto/r61-build/factory42-475dc7c1ef3ac303')
    tools=project/'yocto/build-main/tmp/work/qemuarm64-aos-linux/refpolicy-aos/2_20220106+git/recipe-sysroot-native/usr/bin'
    assert a.source.name=='vision_camera_resource_probe.te' and sha(a.source)==a.sha256
    assert a.output.parent==project and not a.output.exists()
    a.output.mkdir(mode=0o700);start=time.monotonic()
    with tempfile.TemporaryDirectory(prefix='camera-resource-',dir=project/'.tmp') as temporary:
        root=Path(temporary);source=root/a.source.name;shutil.copyfile(a.source,source)
        for command in ([str(tools/'checkmodule'),'-M','-m','-c','21','-o',str(root/'vision_camera_resource_probe.mod'),str(source)],
                        [str(tools/'semodule_package'),'-o',str(root/'vision_camera_resource_probe.pp'),'-m',str(root/'vision_camera_resource_probe.mod')]):
            subprocess.run(command,check=True,capture_output=True,timeout=30)
        output=a.output/'vision_camera_resource_probe.pp';shutil.copyfile(root/output.name,output);output.chmod(0o400)
        result=dict(outcome='PASS_TARGETED_RESOURCE_POLICY_COMPILE',sourceSha256=a.sha256,sha256=sha(output),bytes=output.stat().st_size,
            toolchainSha256={n:sha(tools/n) for n in ('checkmodule','semodule_package')},moduleVersion=21,seconds=round(time.monotonic()-start,2),scratchRemovedAfterExit=True)
        (a.output/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__=='__main__':main()
