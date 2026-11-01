#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""One SSD ARM64 Assessment target compile/unit campaign, never an image task."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import runpy
import shlex
import subprocess
import sys
import tarfile
import time

ROOT=Path(__file__).resolve().parents[2]
SERVICES=ROOT.parent/'vision-pilot-services'
PROJECT=Path('/home/yocto/r61-build/factory42-475dc7c1ef3ac303')

GUEST=r'''import hashlib,json,os,pathlib,shutil,subprocess,sys,tarfile,time
workspace=pathlib.Path(WORKSPACE);workspace.mkdir(mode=0o700,exist_ok=True)
output=workspace/NAME;assert not output.exists();output.mkdir(mode=0o700)
archive=workspace/(NAME+'.tar');assert hashlib.sha256(archive.read_bytes()).hexdigest()==ARCHIVE_SHA
sys.path.insert(0,str(workspace));from build_scratch import directory
started=time.monotonic()
with directory(workspace) as scratch:
 source=scratch/'source';source.mkdir()
 with tarfile.open(archive) as tar:
  for row in tar:
   relative=pathlib.PurePosixPath(row.name)
   assert not relative.is_absolute() and '..' not in relative.parts and (row.isfile() or row.isdir()) and row.size<2*1024**2
   if row.isdir():continue
   path=source/relative;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(tar.extractfile(row).read());path.chmod(row.mode&0o755)
 build=scratch/'compile'
 commands=[['cmake','-S',str(source/'apps/assessment/native'),'-B',str(build),'-G','Ninja','-DCMAKE_BUILD_TYPE=Release'],['cmake','--build',str(build),'-j','4']]
 for index,args in enumerate(commands):
  with (output/('compile-'+str(index)+'.log')).open('wb') as log:p=subprocess.run(args,stdout=log,stderr=subprocess.STDOUT,timeout=180)
  assert p.returncode==0,'ASSESSMENT_TARGET_COMPILE_FAILED_'+str(index)
 library=build/'libvision_assessment.so';raw=library.read_bytes();assert raw[:5]==b'\x7fELF\x02' and raw[18:20]==b'\xb7\x00'
 test=subprocess.run(['python3','-B',str(source/'tools/native_smoke.py'),'--library',str(library)],capture_output=True,text=True,timeout=30)
 (output/'unit.stdout').write_text(test.stdout);(output/'unit.stderr').write_text(test.stderr)
 assert test.returncode==0,'ASSESSMENT_TARGET_UNIT_FAILED'
 units=json.loads(test.stdout)
 shutil.copy2(library,output/library.name)
 dependencies=subprocess.check_output(['ldd',str(library)],text=True)
 rows=[r.strip().split(' => ') for r in dependencies.splitlines() if ' => ' in r]
 closure={r[0]:r[1].split(' (')[0] for r in rows};assert all(pathlib.Path(p).is_file() for p in closure.values())
 result=dict(outcome='PASS_SSD_ARM64_ASSESSMENT_TARGET',sourceRevision=SOURCE_REVISION,sourceArchiveSha256=ARCHIVE_SHA,
  library=dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()),dependencies=closure,units=units,imageTasks=False,seconds=round(time.monotonic()-started,2))
 (output/'result.json').write_text(json.dumps(result,indent=2)+'\n')
archive.unlink();print(json.dumps(result))
'''


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--name',default='native-01',choices=('native-01','native-02','native-03','native-04','native-05','native-06'));args=parser.parse_args()
    result_root=Path('/Volumes/SDV-Dev/sdv/build/vision-services');output=result_root/args.name
    assert not output.exists(),'TARGET_OUTPUT_EXISTS_RECONCILE';output.mkdir(parents=True,mode=0o700)
    if args.name=='native-02':
        prior=json.loads((result_root/'native-01/campaign.json').read_bytes())
        assert prior['code']=='ModuleNotFoundError' and prior['builderStopped'],'PREVIOUS_COMPILE_ATTEMPT_UNRECONCILED'
    if args.name=='native-03':
        prior=json.loads((result_root/'native-02/campaign.json').read_bytes())
        assert prior['code']=='TARGET_COMMAND_FAILED' and prior['builderStopped']
        assert 'fatal error: coin-or/IpIpoptApplication.hpp: No such file or directory' in (result_root/'native-02/compile-1.log').read_text(),'EXACT_HEADER_COMPATIBILITY_FAULT_REQUIRED'
    if args.name=='native-04':
        prior=json.loads((result_root/'native-03/campaign.json').read_bytes())
        assert prior['code']=='TARGET_COMMAND_FAILED' and prior['builderStopped']
        assert 'cannot find -lblas' in (result_root/'native-03/compile-1.log').read_text(),'EXACT_LINK_DEPENDENCY_FAULT_REQUIRED'
    if args.name=='native-05':
        prior=json.loads((result_root/'native-04/campaign.json').read_bytes())
        assert prior['outcome']=='PASS_SSD_NATIVE_ASSESSMENT' and prior['builderStopped'],'PREVIOUS_BUILD_UNRECONCILED'
        # This is an explicit algorithm-validity/input-mask delta, not a retry
        # of a completed compile or an observer/evidence failure.
        text=(SERVICES/'apps/assessment/native/assessment.cpp').read_text()
        assert 'in.flags==7 && output->lead_valid' in text and 'in.flags&~7' in text
        solver=(SERVICES/'third_party/vision_pilot/VisionPilot/modules/safety_guardian/planning/src/lateral_planning.cpp').read_text()
        assert 'if (solution.status != CppAD::ipopt::solve_result<Dvector>::success) return {};' in solver
    if args.name=='native-06':
        prior=json.loads((result_root/'native-05/campaign.json').read_bytes())
        assert prior['outcome']=='PASS_SSD_NATIVE_ASSESSMENT' and prior['builderStopped'],'PREVIOUS_BUILD_UNRECONCILED'
        text=(SERVICES/'apps/assessment/native/assessment.cpp').read_text()
        assert 'for (float v:in.confidence) if (!std::isfinite(v)) return false;' in text
        assert 'RAW_AUTOSTEER_HEIGHT_MASK_IS_NOT_PROBABILITY' in (SERVICES/'tools/native_smoke.py').read_text()
    dependencies=json.loads((result_root/('dependencies-02' if args.name in ('native-04','native-05','native-06') else 'dependencies-01')/'result.json').read_bytes());assert dependencies['outcome']=='PASS_SSD_BUILD_DEPENDENCIES' and dependencies['builderStopped']
    assert not subprocess.check_output(['git','-C',str(SERVICES),'status','--porcelain'],text=True),'SERVICES_SOURCE_DIRTY'
    revision=subprocess.check_output(['git','-C',str(SERVICES),'rev-parse','HEAD'],text=True).strip()
    environment=dict(os.environ,R61_BUILDER_ROOT='/Volumes/SDV-Dev/sdv/build/factory-builder',R61_BUILDER_VOLUME_UUID='F92AB578-22AA-4DAC-B8DD-7DC0EB831396',R61_BUILDER_SSH_PORT='10024',R61_BUILDER_DNS_PORT='18054')
    for key in ('R61_BUILDER_ROOT','R61_BUILDER_VOLUME_UUID','R61_BUILDER_SSH_PORT','R61_BUILDER_DNS_PORT'):os.environ[key]=environment[key]
    sys.path.insert(0,str(ROOT/'scripts'))
    b=runpy.run_path(str(ROOT/'scripts/r6-1-builder'),run_name='builder_library')
    sys.path.insert(0,str(ROOT/'scripts/distribution'));from build_scratch import directory
    began=time.monotonic();owned=False;result=dict(scenario='VISION_SERVICES_TARGET_COMPILE',outcome='NOT_COMPLETE',sourceRevision=revision,imageTasks=False)
    def run(command,timeout=180):
        p=subprocess.run(command,capture_output=True,text=True,timeout=timeout)
        if p.returncode:raise ValueError('TARGET_COMMAND_FAILED')
        return p.stdout
    try:
        assert b['resolve_running']() is None,'BUILDER_OTHER_OWNER_RUNNING';owned=True;b['start'](False);b['wait_ready']()
        workspace=PROJECT/'vision-services-build';ssh=b['ssh_base']();scp=b['scp_base']()
        run(ssh+['mkdir -m 700 -p '+shlex.quote(str(workspace))])
        with directory(ROOT) as scratch:
            archive=scratch/'source.tar'
            with archive.open('wb') as stream:subprocess.run(['git','-C',str(SERVICES),'archive','--format=tar',revision],stdout=stream,check=True)
            digest=hashlib.sha256(archive.read_bytes()).hexdigest()
            run(scp+[str(archive),'yocto@127.0.0.1:'+str(workspace/(args.name+'.tar'))],60)
            run(scp+[str(ROOT/'scripts/distribution/build_scratch.py'),'yocto@127.0.0.1:'+str(workspace/'build_scratch.py')],20)
        code=GUEST.replace('WORKSPACE',repr(str(workspace))).replace('NAME',repr(args.name)).replace('ARCHIVE_SHA',repr(digest)).replace('SOURCE_REVISION',repr(revision))
        print('ARM64_ASSESSMENT_TARGET_COMPILE',flush=True)
        value=run(ssh+['python3 -c '+shlex.quote(code)],420);result.update(outcome='PASS_SSD_NATIVE_ASSESSMENT',build=json.loads(value))
        for name in ('result.json','libvision_assessment.so','compile-0.log','compile-1.log','unit.stdout','unit.stderr'):
            run(scp+['yocto@127.0.0.1:'+str(workspace/args.name/name),str(output/name)],30)
        assert hashlib.sha256((output/'libvision_assessment.so').read_bytes()).hexdigest()==result['build']['library']['sha256']
        if args.name in ('native-05','native-06'):
            # Read-only clean build-image inventory. Never use a provisioned VM
            # or its trust/store as a runtime packaging input.
            inventory='''import json,pathlib,subprocess
project=pathlib.Path('/home/yocto/r61-build/factory42-475dc7c1ef3ac303')
roots=list((project/'yocto/build-main/tmp/work').glob('*/aos-image-vision/*/rootfs'))
assert len(roots)==1
root=roots[0];assert (root/'etc/aos/version').read_text().strip()=='VERSION="6.1.1-vision-camera.5"'
assert not list(root.rglob('*.p12')) and not list(root.rglob('client-key.pem'))
python=root/'usr/bin/python3.12';assert python.is_file()
library=root/'usr/lib/python3.12';files=[p for p in library.rglob('*') if p.is_file() and not p.is_symlink()]
print(json.dumps(dict(cleanRootfs=str(root),pythonBytes=python.stat().st_size,pythonStdlibFiles=len(files),pythonStdlibBytes=sum(p.stat().st_size for p in files),
 pythonNeeded=subprocess.check_output(['readelf','-d',str(python)],text=True),modelsExecuted=False,imageTasks=False)))
'''
            observed=json.loads(run(ssh+['python3 -c '+shlex.quote(inventory)],30));result['runtimeInputInventory']=observed
            (output/'runtime-input-inventory.json').write_text(json.dumps(observed,indent=2)+'\n')
    except Exception as error:
        result['code']=str(error) if str(error).isupper() else type(error).__name__
        if owned:
            try:
                for name in ('compile-0.log','compile-1.log','unit.stdout','unit.stderr'):
                    run(b['scp_base']()+['yocto@127.0.0.1:'+str(PROJECT/'vision-services-build'/args.name/name),str(output/name)],15)
            except Exception:pass
    finally:
        if owned:b['stop']();result['builderStopped']=b['resolve_running']() is None
        result['seconds']=round(time.monotonic()-began,2);(output/'campaign.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
    return 0 if result['outcome'].startswith('PASS') else 1


if __name__=='__main__':raise SystemExit(main())
