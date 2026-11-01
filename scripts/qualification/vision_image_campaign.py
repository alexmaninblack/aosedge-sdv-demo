#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Separate signed-image acceptance; preserve all four retained M4 instances."""
import argparse
import hashlib
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time

import remote_harness as h
from vision_vm_campaign import configuration

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'apps/demo-orchestrator/src'))
from aosedge_demo_orchestrator import vision_bootstrap as v


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config',type=Path,required=True)
    p.add_argument('--identity',required=True)
    a=p.parse_args();c=configuration(a.config);q=shlex.quote
    records=Path(c['records'])/'image-policy-01'
    h.require(not records.exists(),'IMAGE_CAMPAIGN_EXISTS_RECONCILE');records.mkdir(mode=0o700)
    output=Path('/Volumes/SDV-Dev/sdv/build/vision-bootstrap/0.3.0')
    h.require(not output.exists(),'IMAGE_OUTPUT_EXISTS_RECONCILE')
    platform=Path('/Volumes/SDV-Dev/sdv/worktrees/vision-camera-platform')
    revision=h.run(['git','-C',str(platform),'rev-parse','HEAD']).strip()
    h.require(not h.run(['git','-C',str(platform),'diff','HEAD','--name-only']),'COMMITTED_PLATFORM_REQUIRED')
    loader=importlib.machinery.SourceFileLoader('vision_image_builder',str(ROOT/'scripts/r6-1-builder'))
    spec=importlib.util.spec_from_loader(loader.name,loader);builder=importlib.util.module_from_spec(spec)
    sys.modules[spec.name]=builder;loader.exec_module(builder)
    pid=builder.resolve_running();h.require(pid is not None,'OWNED_WARM_BUILDER_REQUIRED');builder.verify_owned_process(pid)
    ssh=builder.ssh_base();project=Path('/home/yocto/r61-build/factory42-475dc7c1ef3ac303')
    selected=project/'yocto'/('aos-vehicle-platform-'+revision)
    result=dict(scenario='VISION_SEPARATE_IMAGE_ACCEPTANCE',outcome='NOT_COMPLETE',phases=[],cleanup={})
    began=time.monotonic()
    def call(name,args,timeout=600):
        print(json.dumps(dict(stage=name,state='STARTED')),flush=True);start=time.monotonic()
        with (records/(name+'.log')).open('x') as log:
            done=subprocess.run(args,stdout=log,stderr=subprocess.STDOUT,text=True,timeout=timeout)
        result['phases'].append(dict(stage=name,exit=done.returncode,seconds=round(time.monotonic()-start,2)))
        h.atomic(records/'progress.json',result)
        h.require(done.returncode==0,'IMAGE_CAMPAIGN_STAGE_FAILED:'+name)
        print(json.dumps(dict(stage=name,state='COMPLETE')),flush=True)
    try:
        python=c['main']['packageRoot']+'/demo-artifacts/aosedge-sdv-demo/host-runtime/python/bin/python3.12'
        preflight=r'''import contextlib,io,json,pathlib,shutil,socket,subprocess,sys
home=pathlib.Path.home();assert shutil.disk_usage(home).free>80*1024**3
assert not (home/INSTANCE).exists()
for name in RETAINED:
 s=json.loads((home/name/'.run/demo-current/journal.json').read_bytes())
 assert all(v.get('runtime',{}).get('state')=='STOPPED' for v in s['vehicles'].values())
for port in (10022,12022,2000,18080,16443,18053):
 with socket.socket() as sock:
  sock.settimeout(.2);assert sock.connect_ex(('127.0.0.1',port))!=0,'CONFLICTING_RUNTIME_OWNER'
base=pathlib.Path(BASE);sys.path.insert(0,str(base/'aosedge-sdv-demo/apps/demo-orchestrator/src'))
from aosedge_demo_orchestrator import runtime_paths
from aosedge_demo_orchestrator.status import load_configuration
from aosedge_demo_orchestrator.cloud_runtime import launch
from aosedge_demo_orchestrator.cloud_connection import selected_domain,cloud_binding
root=home/'SDV-Vision-Camera-Lab-Data';s=json.loads((root/'.run/demo-current/journal.json').read_bytes())
with runtime_paths.installed_session(root):
 config=load_configuration(root);sdk,env=launch(root,config['cloudPython'],'unit_cloud.py')
 request=dict(cloudDomain=selected_domain(s),credential=str(config['cloudProfiles']['oem-delivery']['credential']),ownerId=cloud_binding(s)['ownerId'],unitId=s['vehicles']['test']['unitId'],spCredential=str(config['cloudProfiles']['service-provider']['credential']),spOwner=config['cloudProfiles']['service-provider']['expectedOwnerId'],tooling=str(base/'aosedge-sdv-demo/apps/demo-orchestrator/src'),setTitle=SET_LABEL)
code="""import contextlib,io,json,sys
r=json.load(sys.stdin);sys.path.insert(0,r['tooling'])
from aosedge_demo_orchestrator.unit_cloud import Cloud
with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
 o=Cloud(r);o.require('units_read','unit_sets_list','unit_sets_units_list','unit_sets_create')
 assert o.unit(r['unitId']) is not None
 assert not [v for v in o.pages('unit-sets/') if v.get('title')==r['setTitle']]
 sp=Cloud(dict(credential=r['spCredential'],cloudDomain=r['cloudDomain'],ownerId=r['spOwner']),expected_role='service provider')
 sp.require('services_list','services_read','deployment_bundles_create','deployment_bundles_list')
 assert not [v for v in sp.pages('services/') if v.get('codename')=='vision-camera-image-probe']
print(json.dumps(dict(rolesAndPermissions=True,newSetAbsent=True,newProbeAbsent=True,retainedUnitObserved=True)))
"""
done=subprocess.run([sdk[0],'-I','-B','-c',code],input=json.dumps(request),env=env,capture_output=True,text=True,timeout=60)
assert done.returncode==0,'ACCOUNT_PREFLIGHT_FAILED'
print(done.stdout)
'''.replace('INSTANCE',repr(v.INSTANCE_NAME)).replace('RETAINED',repr(v.RETAINED_INSTANCE_NAMES)).replace('BASE',repr(c['main']['packageRoot'])).replace('SET_LABEL',repr(v.SET_TITLE))
        # Only fixed codes/booleans leave the credential-owning SDK process.
        facts=json.loads(h.remote(c['transport'],q(python)+' -I -B -c '+q(preflight),timeout=75))
        h.atomic(records/'m4-preflight.json',facts)
        # The old exported image is a redundant Builder delivery copy, not a
        # backing disk/cache. The immutable host copy and old VM remain intact.
        old=json.loads(Path('/Volumes/SDV-Dev/sdv/build/vision-bootstrap/0.2.0/factory.json').read_bytes())
        h.require(tuple(old['verifiedStamp'])==v.stamp(Path(old['path'])),'RETAINED_IMAGE_CHANGED')
        clean=r'''import json,pathlib,subprocess
p=pathlib.Path(PROJECT);image=p/'main-qemuarm64-6.1.1-vision-camera.2.img'
r=json.loads((p/'vision-bootstrap-image-07/result.json').read_bytes())
assert image.is_file() and not image.is_symlink() and image.stat().st_size==EXPECTED['bytes']
assert r['sha256']==EXPECTED['sha256'] and r['bytes']==EXPECTED['bytes']
assert subprocess.run(['fuser',str(image)],capture_output=True).returncode==1
image.unlink()
print(json.dumps(dict(removedDuplicate=image.name,bytes=EXPECTED['bytes'],hostImagePreserved=True)))
'''.replace('PROJECT',repr(str(project))).replace('EXPECTED',repr({k:old[k] for k in ('bytes','sha256')}))
        h.atomic(records/'builder-duplicate-cleanup.json',json.loads(h.run(ssh+['python3 -'],data=clean,timeout=20)))
        archive=subprocess.check_output(['git','-C',str(platform),'archive',revision],timeout=20)
        exported=subprocess.run(ssh+['mkdir '+q(str(selected))+' && tar -xf - -C '+q(str(selected))],input=archive,capture_output=True,timeout=45)
        h.require(exported.returncode==0,'PLATFORM_EXPORT_FAILED')
        inputs={
            'vision_bootstrap_build_03.py':ROOT/'scripts/guest/vision_bootstrap_build.py',
            'camera-resource-transient-proof.json':Path(c['records'])/'native-camera-13/result.json'}
        for name,path in inputs.items():
            h.run(ssh+['umask 077; test ! -e '+q(str(project/name))+' && cp /dev/stdin '+q(str(project/name))],data=path.read_text(),timeout=15)
        evidence=project/'vision-bootstrap-image-08'
        command=['python3',str(project/'vision_bootstrap_build_03.py'),'--project',str(project),'--source',str(selected),
            '--evidence',str(evidence),'--manifest','/home/yocto/r61-input/factory42-475dc7c1ef3ac303/factory42.yaml',
            '--native-proof',str(project/'camera-archive-profile-proof/result.json'),
            '--store-proof',str(project/'camera-store-transient-proof.json'),
            '--resource-proof',str(project/'camera-resource-transient-proof.json'),'--revision',revision]
        call('warm-image-build',ssh+[shlex.join(command)],timeout=11000)
        call('freeze-image',[sys.executable,'-B',str(ROOT/'scripts/distribution/vision_bootstrap_acquire.py'),
            '--result',str(evidence/'result.json'),'--output',str(output)],timeout=600)
        bundle=output/'AosEdge Vision Bootstrap 0.3.0.bundle'
        call('sign-bootstrap',[sys.executable,'-B',str(ROOT/'scripts/distribution/vision_bootstrap.py'),
            '--factory',str(output/'factory.json'),'--camera-payload','/Volumes/SDV-Dev/sdv/build/vision-bootstrap/0.1.0/camera-access-payload.tar',
            '--base-manifest',c['main']['manifestSha256'],'--platform-revision',revision,'--identity',a.identity,'--output',str(bundle)],timeout=240)
        call('separate-manufacture-provision',[sys.executable,'-B',str(ROOT/'scripts/qualification/vision_bootstrap_campaign.py'),
            '--config',str(a.config),'--bundle',str(bundle),'--attempt','3'],timeout=1500)
        verified=v.verify(bundle,c['main']['manifestSha256'])
        call('native-image-acceptance',[sys.executable,'-B',str(ROOT/'scripts/qualification/vision_camera_native_campaign.py'),
            '--config',str(a.config),'--name','native-camera-14','--bundle-remote',str(Path(c['remoteRoot'])/'signed-bootstrap-03'/bundle.name),
            '--bootstrap-manifest',verified.manifest_sha256,'--probe','/Volumes/SDV-Dev/sdv/build/vision-bootstrap/0.1.0/vision-camera-probe',
            '--reuse-camera-publication'],timeout=1800)
        accepted=json.loads((Path(c['records'])/'native-camera-14/result.json').read_bytes())
        h.require(accepted['outcome']=='PASS_NATIVE_CAMERA_OEM_AND_AOS_READ','NATIVE_IMAGE_NOT_ACCEPTED')
        result.update(outcome='PASS_SEPARATE_NATIVE_IMAGE_CAMERA_ACCESS',bootstrapManifestSha256=verified.manifest_sha256)
    except Exception as error:
        result['code']=str(error) if isinstance(error,h.Error) else type(error).__name__
    finally:
        # This is the exact Builder started for this image campaign, not the
        # unrelated Raspberry Pi builder or shared Docker.
        try:subprocess.run(ssh+['sudo -n systemctl poweroff'],capture_output=True,timeout=20)
        except subprocess.TimeoutExpired:pass
        try:
            call('builder-stop',[sys.executable,str(ROOT/'scripts/r6-1-builder'),'stop'],timeout=180)
            result['cleanup']['builderStopped']=True
        except Exception:result['cleanup']['builderStopped']=False
        if not all(result['cleanup'].values()):result['outcome']='CLEANUP_INCOMPLETE'
        result['seconds']=round(time.monotonic()-began,2);h.atomic(records/'result.json',result)
        print(json.dumps(result),flush=True)
    return 0 if result['outcome']=='PASS_SEPARATE_NATIVE_IMAGE_CAMERA_ACCESS' else 1


if __name__=='__main__':raise SystemExit(main())
