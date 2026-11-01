#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Fresh .5 image/FOTA from warm SSD caches after exact empty-cohort proof."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import runpy
import shlex
import subprocess
import sys
import time
import remote_harness as h
from vision_vm_campaign import configuration

ROOT=Path(__file__).resolve().parents[2]
PROJECT=Path('/home/yocto/r61-build/factory42-475dc7c1ef3ac303')
OUTPUT=Path('/Volumes/SDV-Dev/sdv/build/vision-bootstrap/0.5.0')


def main():
    p=argparse.ArgumentParser();p.add_argument('--config',type=Path,required=True);a=p.parse_args();c=configuration(a.config)
    subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','apps/demo-orchestrator/tests','-p','test_vision*.py'],
        cwd=ROOT,env=dict(os.environ,PYTHONPATH=str(ROOT/'apps/demo-orchestrator/src')),check=True)
    gate=Path(c['records'])/'vision-fresh-oem-01/result.json';proof=json.loads(gate.read_bytes())
    h.require(proof['outcome']=='PASS_EMPTY_VISION_PUBLICATION_GATE' and proof['facts']['ready']
        and all(proof['cleanup'].values()),'EMPTY_COHORT_GATE_REQUIRED')
    platform=ROOT.parent/'vision-camera-platform';revision=h.run(['git','-C',str(platform),'rev-parse','HEAD']).strip()
    h.require(not h.run(['git','-C',str(platform),'diff','HEAD','--name-only']),'COMMITTED_PLATFORM_REQUIRED')
    subprocess.run([sys.executable,'-B',str(platform/'tools/check_camera_ingress_delivery.py')],cwd=platform,check=True)
    records=Path(c['records'])/'vision-fresh-build-01';h.require(not records.exists() and not OUTPUT.exists(),'FRESH_BUILD_EXISTS_RECONCILE');records.mkdir(mode=0o700)
    for key,value in dict(R61_BUILDER_ROOT='/Volumes/SDV-Dev/sdv/build/factory-builder',R61_BUILDER_VOLUME_UUID='F92AB578-22AA-4DAC-B8DD-7DC0EB831396',R61_BUILDER_SSH_PORT='10024',R61_BUILDER_DNS_PORT='18054').items():os.environ[key]=value
    b=runpy.run_path(str(ROOT/'scripts/r6-1-builder'),run_name='builder_library');b['verify_owned_process'](b['resolve_running']());ssh=b['ssh_base']()
    source=PROJECT/'yocto'/('aos-vehicle-platform-'+revision);evidence=PROJECT/'vision-bootstrap-image-09';scratch=PROJECT/'.tmp/vision-fresh-build-01'
    result=dict(scenario='VISION_FRESH_IMAGE_SSD_BUILD',outcome='NOT_COMPLETE',cleanup={},carlaRebuilt=False)
    began=time.monotonic()
    try:
        archive=subprocess.check_output(['git','-C',str(platform),'archive',revision]);digest=hashlib.sha256(archive).hexdigest()
        code="import pathlib,sys,hashlib,subprocess,json;p=pathlib.Path("+repr(str(source))+");assert not p.exists();raw=sys.stdin.buffer.read();assert hashlib.sha256(raw).hexdigest()=="+repr(digest)+";p.mkdir(mode=0o700);subprocess.run(['tar','-xf','-','-C',str(p)],input=raw,check=True);(p/'.vision-source-export.json').write_text(json.dumps(dict(revision="+repr(revision)+",archiveSha256="+repr(digest)+")))"
        done=subprocess.run(ssh+['python3 -c '+shlex.quote(code)],input=archive,capture_output=True,timeout=45);h.require(done.returncode==0,'FRESH_SOURCE_EXPORT_FAILED')
        h.run(ssh+['mkdir -m 700 '+shlex.quote(str(scratch))],timeout=15)
        for path,name in ((ROOT/'scripts/guest/vision_bootstrap_build.py','vision_bootstrap_build.py'),(gate,'empty-cohort-proof.json')):
            h.run(b['scp_base']()+[str(path),'yocto@127.0.0.1:'+str(scratch/name)],timeout=20)
        command=['python3',str(scratch/'vision_bootstrap_build.py'),'--project',str(PROJECT),'--source',str(source),'--evidence',str(evidence),
            '--manifest','/home/yocto/r61-input/factory42-475dc7c1ef3ac303/factory42.yaml','--native-proof',str(PROJECT/'camera-archive-profile-proof/result.json'),
            '--store-proof',str(PROJECT/'camera-store-transient-proof.json'),'--resource-proof',str(PROJECT/'camera-resource-transient-proof.json'),
            '--revision',revision,'--fresh-empty-proof',str(scratch/'empty-cohort-proof.json')]
        process=subprocess.Popen(ssh+[shlex.join(command)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        with (records/'progress.jsonl').open('x') as log:
            for line in process.stdout:
                h.require(log.tell()<2**20,'BUILD_PROGRESS_LIMIT');log.write(line);log.flush()
                if line.startswith('{'):print(line.strip(),flush=True)
        code=process.wait(timeout=15);stderr=process.stderr.read(8192)
        h.atomic(records/'transport.json',dict(exit=code,stderrPresent=bool(stderr)))
        built=json.loads(h.run(ssh+['cat '+shlex.quote(str(evidence/'result.json'))],timeout=15));h.atomic(records/'builder-result.json',built)
        h.require(code==0 and built['outcome']=='IMAGE_BUILT_NOT_LIVE_QUALIFIED' and built['mainConfigurationRestored'],'FRESH_IMAGE_NOT_COMPLETE')
        subprocess.run([sys.executable,'-B',str(ROOT/'scripts/distribution/vision_bootstrap_acquire.py'),'--result',str(evidence/'result.json'),'--output',str(OUTPUT)],check=True,timeout=900)
        artifact=built['rootfsArtifact'];target=OUTPUT/'vision-rootfs.squashfs'
        h.run(b['scp_base']()+['yocto@127.0.0.1:'+artifact['path'],str(target)],timeout=120)
        h.require(target.stat().st_size==artifact['bytes'] and h.digest(target)==artifact['sha256'],'FRESH_FOTA_TRANSFER_CHANGED');target.chmod(0o444)
        artifact.update(path=str(target),platformRevision=revision);h.atomic(OUTPUT/'rootfs-artifact.json',artifact)
        h.run(ssh+['mv '+shlex.quote(str(scratch))+' '+shlex.quote(str(evidence/'inputs'))],timeout=15)
        result.update(outcome='PASS_FRESH_FIFTH_IMAGE_FROZEN_NOT_INSTALLED',factory=str(OUTPUT/'factory.json'),rootfsArtifact=str(OUTPUT/'rootfs-artifact.json'),platformRevision=revision)
    except Exception as error:result['code']=str(error) if isinstance(error,h.Error) else type(error).__name__
    finally:
        stop=subprocess.run([sys.executable,'-B',str(ROOT/'scripts/r6-1-builder'),'stop'],capture_output=True,text=True,timeout=180)
        result['cleanup']['builderStopped']=stop.returncode==0
        if not all(result['cleanup'].values()):result['outcome']='NOT_COMPLETE'
        result['seconds']=round(time.monotonic()-began,2);h.atomic(records/'result.json',result);print(json.dumps(result),flush=True)
    return 0 if result['outcome']=='PASS_FRESH_FIFTH_IMAGE_FROZEN_NOT_INSTALLED' else 1


if __name__=='__main__':raise SystemExit(main())
