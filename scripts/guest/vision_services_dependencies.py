#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Prepare only native Assessment build dependencies in the owned SSD Builder."""
import json
import argparse
import os
from pathlib import Path
import runpy
import shlex
import subprocess
import time

GUEST=r'''import json,pathlib,shutil,subprocess
root=pathlib.Path(GUEST_OUTPUT)
assert not root.exists();assert shutil.disk_usage('/home/yocto').free>60*1024**3
root.mkdir(mode=0o700)
names=['libopencv-core-dev','coinor-libipopt-dev','libeigen3-dev','libblas-dev','liblapack-dev']
def candidate(name):
 p=subprocess.run(['apt-cache','policy',name],text=True,capture_output=True,check=True)
 values=[line.split(':',1)[1].strip() for line in p.stdout.splitlines() if line.strip().startswith('Candidate:')]
 return values[0] if len(values)==1 and values[0]!='(none)' else None
cppad=next((name for name in ('libcppad-dev','cppad') if candidate(name)),None)
assert cppad,'CPPAD_BUILD_PACKAGE_ABSENT';names.append(cppad)
versions={name:candidate(name) for name in names};assert all(versions.values()),'BUILD_PACKAGE_CANDIDATE_ABSENT'
intent=dict(packages=versions,installOnlyBuildDependencies=True,imageTask=False)
(root/'intent.json').write_text(json.dumps(intent,indent=2)+'\n')
with (root/'install.log').open('wb') as log:
 p=subprocess.run(['sudo','env','DEBIAN_FRONTEND=noninteractive','apt-get','-y','--no-install-recommends','install',*[n+'='+v for n,v in versions.items()]],stdout=log,stderr=subprocess.STDOUT,timeout=600)
assert p.returncode==0,'ASSESSMENT_BUILD_DEPENDENCY_INSTALL_FAILED'
installed={name:subprocess.check_output(['dpkg-query','-W','-f=${Version}',name],text=True) for name in names}
assert installed==versions,'BUILD_DEPENDENCY_VERSION_CHANGED'
result=dict(outcome='PASS_PINNED_ASSESSMENT_BUILD_DEPENDENCIES',packages=installed,guestFreeGiB=round(shutil.disk_usage('/home/yocto').free/2**30,1),cppadHeader=pathlib.Path('/usr/include/cppad/cppad.hpp').is_file())
(root/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
'''


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,choices=(1,2),default=1);args=parser.parse_args()
    source=Path(__file__).resolve().parents[2];records=Path('/Volumes/SDV-Dev/sdv/build/vision-services')/('dependencies-'+str(args.attempt).zfill(2))
    assert not records.exists(),'DEPENDENCY_ATTEMPT_EXISTS_RECONCILE';records.mkdir(parents=True,mode=0o700)
    if args.attempt==2:
        compile=json.loads((records.parent/'native-03/campaign.json').read_bytes())
        assert compile['builderStopped'] and compile['code']=='TARGET_COMMAND_FAILED'
        assert 'cannot find -lblas' in (records.parent/'native-03/compile-1.log').read_text()
    prerequisite=json.loads((records.parent/'prerequisites-02/result.json').read_bytes());assert prerequisite['builderStopped']
    environment=dict(os.environ,R61_BUILDER_ROOT='/Volumes/SDV-Dev/sdv/build/factory-builder',R61_BUILDER_VOLUME_UUID='F92AB578-22AA-4DAC-B8DD-7DC0EB831396',R61_BUILDER_SSH_PORT='10024',R61_BUILDER_DNS_PORT='18054')
    builder=[os.sys.executable,'-B',str(source/'scripts/r6-1-builder')];began=time.monotonic();owned=False
    result=dict(scenario='VISION_SERVICES_BUILD_DEPENDENCIES',outcome='NOT_COMPLETE',imageTasks=False)
    def run(args,timeout=180):
        p=subprocess.run(builder+args,env=environment,capture_output=True,text=True,timeout=timeout)
        if p.returncode:
            result['failedCommand']=args[0];result['stderrPresent']=bool(p.stderr)
            raise ValueError('BUILDER_DEPENDENCY_COMMAND_FAILED')
        return p.stdout
    try:
        assert 'is running' not in run(['status']),'BUILDER_OTHER_OWNER_RUNNING';owned=True
        print('SSD_ASSESSMENT_DEPENDENCIES_START',flush=True);run(['start']);run(['wait'])
        code=GUEST.replace('GUEST_OUTPUT',repr('/home/yocto/r61-build/factory42-475dc7c1ef3ac303/vision-services-dependencies-'+str(args.attempt).zfill(2)))
        value=run(['run','python3 -c '+shlex.quote(code)],650)
        result.update(outcome='PASS_SSD_BUILD_DEPENDENCIES',inventory=json.loads(value))
    except Exception as error:result['code']=str(error) if str(error).isupper() else type(error).__name__
    finally:
        if owned:
            run(['stop']);result['builderStopped']='is running' not in run(['status'])
        result['seconds']=round(time.monotonic()-began,2);(records/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
    return 0 if result['outcome'].startswith('PASS') else 1


if __name__=='__main__':raise SystemExit(main())
