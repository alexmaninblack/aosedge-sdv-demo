#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Targeted non-secret negative-fixture diagnostics, never a policy build."""
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess

PROJECT=Path('/home/yocto/r61-build/factory42-475dc7c1ef3ac303')


def main():
    assert os.uname().machine=='aarch64' and os.uname().sysname=='Linux'
    source=PROJECT/'.tmp/vision-negative-fixtures-01';output=PROJECT/'vision-negative-fixtures-01'
    assert not output.exists();output.mkdir(mode=0o700)
    work=PROJECT/'yocto/build-main/tmp/work/cortexa57-aos-linux/aos-servicemanager/git'
    values={s.split('=',1)[0].removeprefix('export '):shlex.split(s)[1].split('=',1)[1]
        for s in (work/'temp/run.do_compile').read_text().splitlines() if s.startswith(('export PATH=','export CC=','export STRIP='))}
    environment=dict(os.environ,PATH=values['PATH']);rows={}
    for name in ('vision-ingress-boundary','vision-camera-credential-deny'):
        target=output/name
        done=subprocess.run([*shlex.split(values['CC']),'-O2','-static','-Wall','-Wextra','-Werror',str(source/(name+'.c')),'-o',str(target)],
            env=environment,capture_output=True,timeout=60)
        (output/(name+'.compile.log')).write_bytes(done.stderr);assert done.returncode==0,'NEGATIVE_FIXTURE_COMPILE_FAILED'
        subprocess.run([*shlex.split(values['STRIP']),str(target)],env=environment,check=True,capture_output=True,timeout=15)
        raw=target.read_bytes();assert raw[:5]==b'\x7fELF\x02' and raw[18:20]==b'\xb7\x00' and len(raw)<8*1024**2
        # Wrong/absent identity never reaches a socket, credential or policy.
        test=subprocess.run([str(target)],capture_output=True,text=True,timeout=5)
        assert test.returncode==2 and json.loads(test.stdout)['fixtureError']=='ARGUMENT_COUNT'
        rows[name]=dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),sourceSha256=hashlib.sha256((source/(name+'.c')).read_bytes()).hexdigest())
    source.rename(output/'inputs')
    result=dict(outcome='PASS_TARGETED_NEGATIVE_FIXTURE_DIAGNOSTICS',files=rows)
    (output/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))


if __name__=='__main__':main()
