#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Read pinned Core quota math/configuration on SSD, no build/image operation."""
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
GUEST=r'''import hashlib,json,pathlib,re,subprocess
base=pathlib.Path('/home/yocto/r61-build/factory42-475dc7c1ef3ac303/yocto/build-main/tmp/work')
roots=sorted(base.glob('*/*/*/service-update-deps/aos_core_lib_cpp'));assert roots,'PINNED_CORE_SOURCE_ABSENT'
source=roots[0];revision=subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()
assert revision=='5560291ba6914e36a5b841ade4d8fc54134a9e91','PINNED_CORE_SOURCE_CHANGED'
rows=[];pattern=re.compile('cpuQuota|cpu_quota|maxDmips|maxDMIPS|totalNumCores|totalNumThreads',re.I)
for path in sorted((source/'src').rglob('*')):
 if path.suffix not in ('.cpp','.hpp','.h') or not path.is_file() or path.stat().st_size>512*1024:continue
 lines=path.read_text().splitlines();indices=[i for i,row in enumerate(lines) if pattern.search(row)]
 if not indices:continue
 chosen=sorted({i for index in indices for i in range(max(0,index-3),min(len(lines),index+4))})
 rows.append(dict(path=str(path.relative_to(source)),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),lines=[dict(number=i+1,text=lines[i]) for i in chosen[:90]]))
 assert len(rows)<64
clean=list(base.glob('*/aos-image-vision/*/rootfs'));assert len(clean)==1
config=json.loads((clean[0]/'etc/aos/iam.cfg').read_bytes()).get('nodeInfo',{})
selected={key:value for key,value in config.items() if re.search('cpu|dmips|ram|memory',key,re.I)}
print(json.dumps(dict(revision=revision,coreQuotaSources=rows,nodeCapacityConfiguration=selected)))
'''

APPLICATION=r'''import hashlib,json,pathlib,re,subprocess
base=pathlib.Path('/home/yocto/r61-build/factory42-475dc7c1ef3ac303/yocto/build-main/tmp/work')
roots=sorted(p for p in base.glob('*/*/*/git') if p.parent.parent.name in ('aos-servicemanager','aos-iamanager'))
assert roots,'PINNED_APPLICATION_SOURCE_ABSENT'
rows=[];pattern=re.compile('cpuQuota|cpu_quota|maxDmips|maxDMIPS|totalNumCores|totalNumThreads|NumCores|NumThreads|_SC_NPROCESSORS|cpu cores|siblings',re.I)
for root in roots:
 revision=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()
 assert revision=='9d613a46df3c7f550062e2f19ae3406c57715694','PINNED_APPLICATION_SOURCE_CHANGED'
 for path in sorted(root.rglob('*')):
  if path.suffix not in ('.cpp','.hpp','.h') or not path.is_file() or path.stat().st_size>512*1024 or 'tests' in path.parts:continue
  lines=path.read_text().splitlines();indices=[i for i,row in enumerate(lines) if pattern.search(row)]
  if not indices:continue
  chosen=sorted({i for index in indices for i in range(max(0,index-6),min(len(lines),index+7))})
  rows.append(dict(recipe=root.parent.parent.name,path=str(path.relative_to(root)),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),lines=[dict(number=i+1,text=lines[i]) for i in chosen[:110]]))
  assert len(rows)<128
print(json.dumps(dict(applicationQuotaSources=rows)))
'''


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--application',action='store_true');args=parser.parse_args()
    output=Path('/Volumes/SDV-Dev/sdv/build/vision-services')/('capacity-source-02' if args.application else 'capacity-source-01');assert not output.exists();output.mkdir(mode=0o700)
    for key,value in dict(R61_BUILDER_ROOT='/Volumes/SDV-Dev/sdv/build/factory-builder',R61_BUILDER_VOLUME_UUID='F92AB578-22AA-4DAC-B8DD-7DC0EB831396',R61_BUILDER_SSH_PORT='10024',R61_BUILDER_DNS_PORT='18054').items():os.environ[key]=value
    sys.path.insert(0,str(ROOT/'scripts'));builder=runpy.run_path(str(ROOT/'scripts/r6-1-builder'),run_name='builder_library')
    result=dict(outcome='NOT_COMPLETE',imageTasks=False,sourceChanged=False);owned=False;started=time.monotonic()
    try:
        assert builder['resolve_running']() is None,'BUILDER_OTHER_OWNER_RUNNING';owned=True;builder['start'](False);builder['wait_ready']()
        done=subprocess.run(builder['ssh_base']()+['python3 -c '+shlex.quote(APPLICATION if args.application else GUEST)],capture_output=True,text=True,timeout=35)
        if done.returncode:
            result['diagnostic']=done.stderr[-4096:];raise ValueError('PINNED_QUOTA_SOURCE_READ_FAILED')
        result.update(outcome='PASS_READ_ONLY_PINNED_QUOTA_SOURCE',facts=json.loads(done.stdout))
    except Exception as error:result['code']=str(error) if str(error).isupper() else type(error).__name__
    finally:
        if owned:builder['stop']();result['builderStopped']=builder['resolve_running']() is None
        result['seconds']=round(time.monotonic()-started,2);(output/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
    return 0 if result['outcome'].startswith('PASS_') else 1


if __name__=='__main__':raise SystemExit(main())
