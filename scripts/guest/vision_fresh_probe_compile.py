#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Target only the native diagnostic reader and its parser unit fixture."""
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import argparse

PROJECT=Path('/home/yocto/r61-build/factory42-475dc7c1ef3ac303')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--attempt',choices=('01','03'),default='01');args=parser.parse_args()
    assert os.uname().machine=='aarch64' and os.uname().sysname=='Linux'
    source=PROJECT/'.tmp'/('vision-fresh-probe-'+args.attempt);output=PROJECT/('vision-fresh-probe-'+args.attempt)
    assert not output.exists();output.mkdir(mode=0o700)
    work=PROJECT/'yocto/build-main/tmp/work/cortexa57-aos-linux/aos-servicemanager/git'
    values={s.split('=',1)[0].removeprefix('export '):shlex.split(s)[1].split('=',1)[1]
        for s in (work/'temp/run.do_compile').read_text().splitlines() if s.startswith(('export PATH=','export CC=','export STRIP='))}
    environment=dict(os.environ,PATH=values['PATH']);rows={}
    for name in ('vision-camera-probe','vision-camera-probe-test'):
        target=output/name
        done=subprocess.run([*shlex.split(values['CC']),'-O2','-static','-Wall','-Wextra','-Werror',str(source/(name+'.c')),
            '-o',str(target),'-lcrypto','-pthread','-ldl'],env=environment,capture_output=True,timeout=60)
        (output/(name+'.compile.log')).write_bytes(done.stderr);assert done.returncode==0,'DIAGNOSTIC_COMPILE_FAILED'
        subprocess.run([*shlex.split(values['STRIP']),str(target)],env=environment,check=True,capture_output=True,timeout=15)
        raw=target.read_bytes();assert raw[:5]==b'\x7fELF\x02' and raw[18:20]==b'\xb7\x00'
        assert len(raw)<8*1024**2,'DIAGNOSTIC_BINARY_LIMIT'
        rows[name]=dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
    test=subprocess.run([str(output/'vision-camera-probe-test')],capture_output=True,text=True,timeout=10)
    assert test.returncode==0 and 'NATIVE_CAMERA_PROBE_PARSER_PASS' in test.stdout,'DIAGNOSTIC_UNIT_FAILED'
    source.rename(output/'inputs')
    value=dict(outcome='PASS_FRESH_DIAGNOSTIC_READER_COMPILE_AND_UNIT',files=rows,sourceSha256=hashlib.sha256((output/'inputs/vision-camera-probe.c').read_bytes()).hexdigest())
    (output/'result.json').write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(value))


if __name__=='__main__':main()
