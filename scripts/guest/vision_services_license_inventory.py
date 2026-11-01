#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Read the actual warm Builder package/license layout; no compile/image task."""
import json
import argparse
import os
from pathlib import Path
import runpy
import shlex
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
GUEST='''import pathlib,json
base=pathlib.Path('/home/yocto/r61-build/factory42-475dc7c1ef3ac303/yocto/build-main/tmp')
root=base/'pkgdata/qemuarm64/runtime';rows=[]
for p in sorted(root.iterdir()):
 if p.name.startswith(('python3-core','glibc','libc6','libgcc','libstdc')):
  row=dict(name=p.name,file=p.is_file(),symlink=p.is_symlink())
  if p.is_file():
   lines=p.read_text().splitlines();row['keys']=[v.split(':',1)[0] for v in lines[:25]];row['prefixes']=[v[:100] for v in lines[:3]]
  rows.append(row)
print(json.dumps(dict(packages=rows[:24],licenseDirectories=[p.name for p in (base/'deploy/licenses').iterdir() if p.name.startswith(('python','glibc','gcc','zlib'))])))
'''


def main():
    p=argparse.ArgumentParser();group=p.add_mutually_exclusive_group();group.add_argument('--detail',action='store_true');group.add_argument('--headers',action='store_true');a=p.parse_args()
    output=Path('/Volumes/SDV-Dev/sdv/build/vision-services')/('license-inputs-03' if a.headers else ('license-inputs-02' if a.detail else 'license-inputs-01'));assert not output.exists();output.mkdir(mode=0o700)
    if a.headers:
        previous=json.loads((output.parent/'closure-07/campaign.json').read_bytes())
        assert previous['code']=='CLOSURE_TARGET_COMMAND_FAILED' and previous['builderStopped']
        assert 'HEADER_BUILD_NOTICE_ABSENT' in (output.parent/'closure-07/build.stderr').read_text()
    for key,value in dict(R61_BUILDER_ROOT='/Volumes/SDV-Dev/sdv/build/factory-builder',R61_BUILDER_VOLUME_UUID='F92AB578-22AA-4DAC-B8DD-7DC0EB831396',R61_BUILDER_SSH_PORT='10024',R61_BUILDER_DNS_PORT='18054').items():os.environ[key]=value
    sys.path.insert(0,str(ROOT/'scripts'));b=runpy.run_path(str(ROOT/'scripts/r6-1-builder'),run_name='builder_library')
    result=dict(scenario='VISION_SERVICES_LICENSE_LAYOUT',outcome='NOT_COMPLETE',imageTasks=False);owned=False;began=time.monotonic()
    try:
        assert b['resolve_running']() is None;owned=True;b['start'](False);b['wait_ready']()
        code=GUEST
        if a.detail:
            code='''import pathlib,json
base=pathlib.Path('/home/yocto/r61-build/factory42-475dc7c1ef3ac303/yocto/build-main/tmp')
rows=[]
for name in ('glibc','python3-core','libgcc','libstdc++'):
 p=base/'pkgdata/qemuarm64/runtime'/name
 if p.is_file():rows.append(dict(name=name,bytes=p.stat().st_size,fields=[l[:240] for l in p.read_text().splitlines() if l.startswith(('PN:','PV:','LICENSE:','FILES_INFO'))]))
licenses=base/'deploy/licenses'
print(json.dumps(dict(packages=rows,licenseRoot=[dict(name=p.name,directory=p.is_dir(),children=[v.name for v in list(p.iterdir())[:6]] if p.is_dir() else []) for p in list(licenses.iterdir())[:10]])))
'''
        if a.headers:
            code='''import pathlib,json,subprocess
rows=[]
for package in ('libeigen3-dev','libcppad-dev'):
 files=subprocess.check_output(['dpkg-query','-L',package],text=True).splitlines()
 notices=[pathlib.Path(name) for name in files if any(key in name.lower() for key in ('copyright','license','copying'))]
 expected=pathlib.Path('/usr/share/doc')/package/'copyright'
 rows.append(dict(package=package,version=subprocess.check_output(['dpkg-query','-W','-f=${Version}',package],text=True),
  expected=dict(path=str(expected),exists=expected.exists(),symlink=expected.is_symlink(),target=str(expected.resolve())),
  noticeFiles=[dict(path=str(p),exists=p.is_file(),symlink=p.is_symlink(),target=str(p.resolve()),bytes=p.stat().st_size if p.exists() else None) for p in notices[:16]]))
print(json.dumps(dict(headerPackages=rows)))
'''
        done=subprocess.run(b['ssh_base']()+['python3 -c '+shlex.quote(code)],capture_output=True,text=True,timeout=30)
        assert done.returncode==0;result.update(outcome='PASS_READ_ONLY_BUILD_LICENSE_LAYOUT',facts=json.loads(done.stdout))
    finally:
        if owned:b['stop']();result['builderStopped']=b['resolve_running']() is None
        result['seconds']=round(time.monotonic()-began,2);(output/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)


if __name__=='__main__':main()
