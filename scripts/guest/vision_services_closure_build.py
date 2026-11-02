#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""One offline SSD closure build/measurement; no image, models or M4 execution."""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import runpy
import re
import shlex
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
SERVICES=ROOT.parent/'vision-pilot-services'
PROJECT=Path('/home/yocto/r61-build/factory42-475dc7c1ef3ac303')
MODEL_SHA='96de1b49b4efb1e733f30fcde65d7e22d3848a3895ef3662e04dc2af35d193f0'
MODELS=Path('/Volumes/SDV-Dev/sdv/build/inputs/vision-pilot-cpu/vision-pilot-cpu-fp32.tar.gz')


def file_digest(path):
    # The macOS system interpreter is Python 3.9; file_digest arrived in 3.11.
    result=hashlib.sha256()
    with path.open('rb') as data:
        for block in iter(lambda:data.read(4*1024**2),b''):result.update(block)
    return result.hexdigest()


def recover_delivery(records):
    """Resume only verified immutable output transfer, never rerun the build."""
    prior=json.loads((records/'campaign.json').read_bytes())
    assert prior['code']=='AttributeError' and prior['builderStopped'] and prior['outcome']=='MEASURED_ARM64_CLOSURES_NOT_DEPLOYED'
    assert records.name=='closure-06' and not (records/'delivery.json').exists(),'DELIVERY_RECONCILE_REQUIRED'
    artifacts=prior['closure']['artifacts'];assert set(artifacts)=={'perception','assessment'}
    for key,value in dict(R61_BUILDER_ROOT='/Volumes/SDV-Dev/sdv/build/factory-builder',R61_BUILDER_VOLUME_UUID='F92AB578-22AA-4DAC-B8DD-7DC0EB831396',R61_BUILDER_SSH_PORT='10024',R61_BUILDER_DNS_PORT='18054').items():os.environ[key]=value
    sys.path.insert(0,str(ROOT/'scripts'));b=runpy.run_path(str(ROOT/'scripts/r6-1-builder'),run_name='builder_library')
    owned=False;started=time.monotonic();result=dict(outcome='NOT_COMPLETE',buildRepeated=False,transfers={})
    try:
        assert b['resolve_running']() is None,'BUILDER_OTHER_OWNER_RUNNING';owned=True;b['start'](False);b['wait_ready']()
        for role,artifact in artifacts.items():
            remote=PROJECT/'vision-services-inputs/closure-06'/(role+'-rootfs.tar.gz')
            assert artifact['path']==str(remote)
            target=records/remote.name
            if target.exists():
                assert not target.is_symlink() and target.stat().st_size==artifact['bytes'] and file_digest(target)==artifact['sha256'],'LOCAL_DELIVERY_CHANGED'
                reused=True
            else:
                # This is the same immutable consumer delivery interrupted by
                # the host digest API, not a provider round-trip test.
                subprocess.run(b['scp_base']()+['yocto@127.0.0.1:'+str(remote),str(target)],check=True,capture_output=True,timeout=90)
                assert target.stat().st_size==artifact['bytes'] and file_digest(target)==artifact['sha256'],'DELIVERY_CHANGED';reused=False
            target.chmod(0o444);result['transfers'][role]=dict(bytes=artifact['bytes'],sha256=artifact['sha256'],reused=reused)
        result['outcome']='PASS_VERIFIED_CLOSURE_DELIVERY'
    except Exception as error:result['code']=str(error) if str(error).isupper() else type(error).__name__
    finally:
        if owned:b['stop']();result['builderStopped']=b['resolve_running']() is None
        result['seconds']=round(time.monotonic()-started,2);(records/'delivery.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
    return 0 if result['outcome'].startswith('PASS_') and result.get('builderStopped') else 1

GUEST='''import gzip,hashlib,json,pathlib,shutil,subprocess,sys,tarfile
workspace=pathlib.Path(WORKSPACE);source_archive=workspace/(NAME+'.source.tar')
assert hashlib.sha256(source_archive.read_bytes()).hexdigest()==SOURCE_SHA
assert shutil.disk_usage(workspace).free>=60*1024**3,'BUILDER_FREE_SPACE_BELOW_60_GIB'
sys.path.insert(0,str(workspace));from build_scratch import directory
with directory(workspace) as scratch:
 source=scratch/'source';source.mkdir()
 with tarfile.open(source_archive) as archive:
  for member in archive:
   rel=pathlib.PurePosixPath(member.name)
   assert not rel.is_absolute() and '..' not in rel.parts and (member.isdir() or member.isfile()) and member.size<2*1024**2
   if member.isdir():continue
   path=source/rel;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(archive.extractfile(member).read())
 if QUARANTINE_INCOMPLETE_ASSESSMENT:
  base=pathlib.Path(OUTPUT_PATH);partial=base/'assessment';retained=base/'assessment-incomplete-header-notice'
  assert partial.is_dir() and not partial.is_symlink() and (partial/'rootfs/app/service-manifest.json').is_file() and not (partial/'closure.json').exists() and not retained.exists()
  assert json.loads((partial/'rootfs/app/service-manifest.json').read_bytes())['sourceRevision']==SOURCE_REVISION
  partial.rename(retained)
 command=['python3','-B',str(source/'tools/build_closure.py'),'--clean-rootfs',CLEAN_ROOTFS,
  '--models',str(workspace/'vision-pilot-cpu-fp32.tar.gz'),'--models-sha256',MODEL_DIGEST,
  '--assessment-library',LIBRARY,'--assessment-sha256',LIBRARY_SHA,'--output',OUTPUT_PATH,'--source-revision',SOURCE_REVISION,
  '--service-version',SERVICE_VERSION]+(['--resume-owned'] if RESUME_OWNED else [])
 if INCLUDE_LICENSES:command+=['--pkgdata-root',PKGDATA_ROOT,'--license-root',LICENSE_ROOT]
 run=subprocess.run(command,capture_output=True,text=True,timeout=240)
 (workspace/(NAME+'.stdout')).write_text(run.stdout);(workspace/(NAME+'.stderr')).write_text(run.stderr)
 assert run.returncode==0,'ARM64_CLOSURE_COMMAND_FAILED'
 result=json.loads(run.stdout)
 if INCLUDE_LICENSES:
  artifacts={}
  for role in ('perception','assessment'):
   root=pathlib.Path(OUTPUT_PATH)/role/'rootfs';target=pathlib.Path(OUTPUT_PATH)/(role+'-rootfs.tar.gz')
   assert not target.exists()
   with target.open('xb') as stream,gzip.GzipFile(fileobj=stream,mode='wb',mtime=0,filename='') as compressed,tarfile.open(fileobj=compressed,mode='w',format=tarfile.USTAR_FORMAT) as archive:
    for path in sorted(root.rglob('*')):
     assert not path.is_symlink()
     if not path.is_file():continue
     entry=archive.gettarinfo(str(path),arcname=str(path.relative_to(root)));entry.uid=entry.gid=0;entry.uname=entry.gname='';entry.mtime=0
     with path.open('rb') as data:archive.addfile(entry,data)
   h=hashlib.sha256()
   with target.open('rb') as data:
    for block in iter(lambda:data.read(4*1024**2),b''):h.update(block)
   artifacts[role]=dict(path=str(target),bytes=target.stat().st_size,sha256=h.hexdigest())
  result['artifacts']=artifacts
 print(json.dumps(result))
source_archive.unlink()
'''


def guest_code(values):
    # Substitute whole placeholder tokens, never LIBRARY inside LIBRARY_SHA.
    code=re.sub(r'\b('+'|'.join(sorted(values,key=len,reverse=True))+r')\b',lambda match:repr(values[match[0]]),GUEST)
    ast.parse(code);return code


def main():
    p=argparse.ArgumentParser();p.add_argument('--name',choices=('closure-01','closure-02','closure-03','closure-04','closure-05','closure-06','closure-07','closure-08','closure-09'),default='closure-01');p.add_argument('--resume-delivery',action='store_true');a=p.parse_args()
    records=Path('/Volumes/SDV-Dev/sdv/build/vision-services')/a.name
    if a.resume_delivery:return recover_delivery(records)
    assert not records.exists(),'CLOSURE_ATTEMPT_EXISTS_RECONCILE';records.mkdir(mode=0o700)
    if a.name=='closure-02':
        old=json.loads((records.parent/'closure-01/campaign.json').read_bytes())
        assert old['code']=='CLOSURE_TARGET_COMMAND_FAILED' and old['builderStopped']
        broken=GUEST.replace('LIBRARY',repr('/library.so')).replace('LIBRARY_SHA',repr('a'*64))
        try:ast.parse(broken)
        except SyntaxError:pass
        else:raise ValueError('EXACT_PLACEHOLDER_FAILURE_REQUIRED')
    if a.name in ('closure-03','closure-04'):
        previous='closure-02' if a.name=='closure-03' else 'closure-03'
        old=json.loads((records.parent/previous/'campaign.json').read_bytes())
        assert old['code']=='CLOSURE_TARGET_COMMAND_FAILED' and old['builderStopped']
        error=(records.parent/previous/'build.stderr').read_text()
        assert ('dpkg-query: no path found matching pattern '+('/lib/aarch64-linux-gnu/libopencv_core.so.4.5d' if a.name=='closure-03' else '/usr/lib/aarch64-linux-gnu/libbz2.so.1.0.4')) in error
        assert not subprocess.check_output(['git','-C',str(SERVICES),'diff',old['sourceRevision'],'HEAD','--','common','apps','contracts','dependencies'],text=True),'COMPLETED_RUNTIME_SOURCE_CHANGED'
    if a.name=='closure-05':
        prior_closure=json.loads((records.parent/'closure-04/campaign.json').read_bytes())
        assert prior_closure['outcome']=='MEASURED_ARM64_CLOSURES_NOT_DEPLOYED' and prior_closure['builderStopped']
        assert not subprocess.check_output(['git','-C',str(SERVICES),'diff',prior_closure['sourceRevision'],'HEAD','--','apps/assessment/native','third_party/vision_pilot/VisionPilot/modules'],text=True),'NATIVE_LIBRARY_SOURCE_CHANGED'
    if a.name=='closure-06':
        previous=json.loads((records.parent/'closure-05/campaign.json').read_bytes())
        assert previous['code']=='CLOSURE_TARGET_COMMAND_FAILED' and previous['builderStopped']
        assert 'PKGDATA_OWNERS_EMPTY' in (records.parent/'closure-05/build.stderr').read_text(),'EXACT_LICENSE_PARSER_FAILURE_REQUIRED'
        assert not subprocess.check_output(['git','-C',str(SERVICES),'diff',previous['sourceRevision'],'HEAD','--','apps/assessment/native','third_party/vision_pilot/VisionPilot/modules'],text=True),'NATIVE_LIBRARY_SOURCE_CHANGED'
    if a.name=='closure-07':
        previous=json.loads((records.parent/'closure-06/delivery.json').read_bytes())
        assert previous['outcome']=='PASS_VERIFIED_CLOSURE_DELIVERY' and previous['builderStopped'],'PREVIOUS_IMMUTABLE_CLOSURES_UNRECONCILED'
        assert 'for (float v:in.confidence) if (!std::isfinite(v)) return false;' in (SERVICES/'apps/assessment/native/assessment.cpp').read_text()
    if a.name=='closure-08':
        previous=json.loads((records.parent/'closure-07/campaign.json').read_bytes())
        observed=json.loads((records.parent/'license-inputs-03/result.json').read_bytes())
        assert previous['code']=='CLOSURE_TARGET_COMMAND_FAILED' and previous['builderStopped'] and observed['builderStopped']
        assert 'HEADER_BUILD_NOTICE_ABSENT' in (records.parent/'closure-07/build.stderr').read_text()
        assert observed['outcome']=='PASS_READ_ONLY_BUILD_LICENSE_LAYOUT' and all(row['expected']['exists'] and not row['expected']['symlink'] for row in observed['facts']['headerPackages'])
        assert not subprocess.check_output(['git','-C',str(SERVICES),'diff',previous['sourceRevision'],'HEAD','--','common','apps','contracts','dependencies','third_party'],text=True),'COMPLETED_RUNTIME_SOURCE_CHANGED'
    if a.name=='closure-09':
        proof=json.loads((ROOT/'.local/remote-qualification/vision-vm-m4/vision-services-native-live-15/result.json').read_bytes())
        assert proof['outcome']=='PASS_TRANSIENT_NATIVE_UNIX_ONLY_AND_INPUT_RECOVERY' and all(proof['cleanup'].values()),'UNIX_ONLY_NATIVE_TRANSIENT_PROOF_REQUIRED'
        assert 'close_range(3,UINT_MAX,0) || unix_only()' in (SERVICES/'apps/common/launcher.c').read_text()
    native='native-06' if a.name in ('closure-07','closure-08','closure-09') else 'native-05'
    prior=json.loads((records.parent/native/'campaign.json').read_bytes())
    assert prior['outcome']=='PASS_SSD_NATIVE_ASSESSMENT' and prior['builderStopped']
    if a.name=='closure-09':
        assert not subprocess.check_output(['git','-C',str(SERVICES),'diff',prior['sourceRevision'],'HEAD','--',
            'common','apps/perception','apps/assessment','third_party','dependencies','contracts'],text=True),'SUCCESSOR_ALGORITHM_OR_PROTOCOL_CHANGED'
    assert not subprocess.check_output(['git','-C',str(SERVICES),'status','--porcelain'],text=True)
    revision=subprocess.check_output(['git','-C',str(SERVICES),'rev-parse','HEAD'],text=True).strip()
    if a.name=='closure-07':assert prior['sourceRevision']==revision,'NATIVE_LIBRARY_SOURCE_CHANGED'
    for key,value in dict(R61_BUILDER_ROOT='/Volumes/SDV-Dev/sdv/build/factory-builder',R61_BUILDER_VOLUME_UUID='F92AB578-22AA-4DAC-B8DD-7DC0EB831396',R61_BUILDER_SSH_PORT='10024',R61_BUILDER_DNS_PORT='18054').items():os.environ[key]=value
    sys.path.insert(0,str(ROOT/'scripts'));b=runpy.run_path(str(ROOT/'scripts/r6-1-builder'),run_name='builder_library')
    sys.path.insert(0,str(ROOT/'scripts/distribution'));from build_scratch import directory
    application_revision=prior['sourceRevision'] if a.name=='closure-08' else revision
    started=time.monotonic();owned=False;result=dict(scenario='VISION_SERVICES_ARM64_CLOSURES',outcome='NOT_COMPLETE',sourceRevision=revision,applicationSourceRevision=application_revision,imageTasks=False,modelsExecuted=False)
    def run(args,timeout=60):
        done=subprocess.run(args,capture_output=True,text=True,timeout=timeout)
        if done.returncode:raise ValueError('CLOSURE_TARGET_COMMAND_FAILED')
        return done.stdout
    workspace=PROJECT/'vision-services-inputs'
    try:
        assert b['resolve_running']() is None,'BUILDER_OTHER_OWNER_RUNNING';owned=True;b['start'](False);b['wait_ready']()
        ssh=b['ssh_base']();scp=b['scp_base']();run(ssh+['mkdir -m 700 -p '+shlex.quote(str(workspace))])
        inventory=json.loads(run(ssh+['python3 -c '+shlex.quote('import pathlib,json; p=pathlib.Path('+repr(str(workspace/'vision-pilot-cpu-fp32.tar.gz'))+');print(json.dumps(dict(exists=p.exists(),bytes=p.stat().st_size if p.exists() else None)))')]))
        if inventory['exists']:assert inventory['bytes']==145774349,'MODEL_INPUT_COLLISION'
        else:
            print('COPY_VERIFIED_MODEL_INPUT_TO_SSD_BUILDER',flush=True)
            run(scp+[str(MODELS),'yocto@127.0.0.1:'+str(workspace/'vision-pilot-cpu-fp32.tar.gz')],90)
        with directory(ROOT) as scratch:
            archive=scratch/'source.tar'
            with archive.open('wb') as stream:subprocess.run(['git','-C',str(SERVICES),'archive','--format=tar',revision],stdout=stream,check=True)
            source_sha=hashlib.sha256(archive.read_bytes()).hexdigest()
            run(scp+[str(archive),'yocto@127.0.0.1:'+str(workspace/(a.name+'.source.tar'))])
            run(scp+[str(ROOT/'scripts/distribution/build_scratch.py'),'yocto@127.0.0.1:'+str(workspace/'build_scratch.py')])
        values=dict(WORKSPACE=str(workspace),NAME=a.name,SOURCE_SHA=source_sha,SOURCE_REVISION=application_revision,CLEAN_ROOTFS=prior['runtimeInputInventory']['cleanRootfs'],MODEL_DIGEST=MODEL_SHA,
            LIBRARY=str(PROJECT/'vision-services-build'/native/'libvision_assessment.so'),LIBRARY_SHA=prior['build']['library']['sha256'],
            OUTPUT_PATH=str(workspace/('closure-07' if a.name=='closure-08' else ('closure-02' if a.name in ('closure-03','closure-04') else a.name))),RESUME_OWNED=a.name in ('closure-03','closure-04','closure-08'),
            QUARANTINE_INCOMPLETE_ASSESSMENT=a.name=='closure-08',
            INCLUDE_LICENSES=a.name in ('closure-05','closure-06','closure-07','closure-08','closure-09'),SERVICE_VERSION='0.1.1' if a.name=='closure-09' else '0.1.0',
            PKGDATA_ROOT=str(PROJECT/'yocto/build-main/tmp/pkgdata/qemuarm64'),LICENSE_ROOT=str(PROJECT/'yocto/build-main/tmp/deploy/licenses'))
        code=guest_code(values)
        print('MEASURE_ARM64_RUNTIME_CLOSURES',flush=True);observed=json.loads(run(ssh+['python3 -c '+shlex.quote(code)],300));result.update(outcome=observed['outcome'],closure=observed)
        for part in ('perception','assessment'):
            (records/part).mkdir()
            run(scp+['yocto@127.0.0.1:'+str(Path(values['OUTPUT_PATH'])/part/'closure.json'),str(records/part/'closure.json')])
        if a.name in ('closure-05','closure-06','closure-07','closure-08','closure-09'):
            for role,artifact in observed['artifacts'].items():
                target=records/(role+'-rootfs.tar.gz');run(scp+['yocto@127.0.0.1:'+artifact['path'],str(target)],90)
                assert target.stat().st_size==artifact['bytes']
                assert file_digest(target)==artifact['sha256'];target.chmod(0o444)
            result['verifiedDeliveryComplete']=True
    except Exception as error:
        result['code']=str(error) if str(error).isupper() else type(error).__name__
        if owned:
            for suffix in ('stdout','stderr'):
                try:run(b['scp_base']()+['yocto@127.0.0.1:'+str(workspace/(a.name+'.'+suffix)),str(records/('build.'+suffix))],15)
                except Exception:pass
    finally:
        if owned:b['stop']();result['builderStopped']=b['resolve_running']() is None
        result['seconds']=round(time.monotonic()-started,2);(records/'campaign.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
    return 0 if result['outcome'].startswith('MEASURED_') and 'code' not in result else 1


if __name__=='__main__':raise SystemExit(main())
