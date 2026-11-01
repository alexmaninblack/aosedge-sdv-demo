#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Compile only the fixed non-secret negative fixture in the SSD Builder."""
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess

PROJECT=Path('/home/yocto/r61-build/factory42-475dc7c1ef3ac303')


def main():
    assert os.uname().machine=='aarch64'
    source=PROJECT/'.tmp/vision-ingress-boundary.c'
    output=PROJECT/'vision-ingress-boundary-01';assert not output.exists();output.mkdir(mode=0o700)
    work=PROJECT/'yocto/build-main/tmp/work/cortexa57-aos-linux/aos-servicemanager/git'
    values={s.split('=',1)[0].removeprefix('export '):shlex.split(s)[1].split('=',1)[1]
            for s in (work/'temp/run.do_compile').read_text().splitlines() if s.startswith(('export PATH=','export CC='))}
    target=output/'vision-ingress-boundary'
    subprocess.run([*shlex.split(values['CC']),'-static','-Wall','-Wextra','-Werror',str(source),'-o',str(target)],
        env=dict(os.environ,PATH=values['PATH']),check=True,capture_output=True,timeout=60)
    raw=target.read_bytes();assert raw[:5]==b'\x7fELF\x02' and raw[18:20]==b'\xb7\x00'
    value=dict(outcome='PASS_TARGETED_BOUNDARY_FIXTURE',bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),
               sourceSha256=hashlib.sha256(source.read_bytes()).hexdigest())
    source.rename(output/source.name);(output/'result.json').write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(value))


if __name__=='__main__':main()
