#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Named retained-Vision ingress campaign; transport never prints secrets."""
import argparse
import json
from pathlib import Path
import shlex
import subprocess

import remote_harness as h
from vision_vm_campaign import configuration


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config',type=Path,required=True);p.add_argument('--name',required=True)
    mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument('--preflight',action='store_true');mode.add_argument('--live',action='store_true');mode.add_argument('--credentials',action='store_true');mode.add_argument('--network',action='store_true')
    p.add_argument('--candidate',type=Path)
    p.add_argument('--resume-read-from',help='Reconcile an existing 0.1.2 publication; never upload it again')
    a=p.parse_args();c=configuration(a.config);t=c['transport'];q=shlex.quote
    prefix='ingress-live-' if a.live else 'ingress-projection-' if a.credentials else 'ingress-network-' if a.network else 'ingress-preflight-'
    h.require(a.name.startswith(prefix) and a.name.removeprefix(prefix).isdecimal(),'CAMPAIGN_NAME_INVALID')
    records=Path(c['records'])/a.name;remote=Path(c['remoteRoot'])/a.name
    h.require(not records.exists(),'ATTEMPT_EXISTS_RECONCILE');records.mkdir(mode=0o700)
    bundle=Path(c['remoteRoot'])/'signed-bootstrap-03/AosEdge Vision Bootstrap 0.3.0.bundle'
    context=dict(main=c['main'],bundle=str(bundle),bootstrapManifestSha256='d782737eff7ddf6c69f59a36c806b2428129d83b70e6e2deb097939990006612')
    if a.credentials:context['projectionProbe']=True
    if a.network:context['networkSource']=(Path(__file__).resolve().parents[2]/'apps/demo-orchestrator/src/aosedge_demo_orchestrator/vision_source_guest.py').read_text()
    worker=Path(__file__).with_name('vision_ingress_live_worker.py' if a.live else 'vision_ingress_preflight_worker.py')
    files=[worker]
    if a.live:
        h.require(a.candidate is not None and a.candidate.is_dir() and not a.candidate.is_symlink(),'LIVE_CANDIDATE_REQUIRED')
        import shutil
        for path in (Path(__file__).with_name('vision_camera_fixture_cloud.py'),Path(__file__).with_name('vision_ingress_observation.py'),
                Path('/Volumes/SDV-Dev/sdv/build/vision-ingress/reader-01/vision-camera-probe'),
                Path('/Volumes/SDV-Dev/sdv/build/vision-ingress/reader-01/vision-camera-credential-deny')):
            files.append(path)
        context.update(candidateManifestSha256=h.digest(a.candidate/'manifest.json'),
            previousNative=str(Path(c['remoteRoot'])/'native-camera-17'),files={p.name:h.digest(p) for p in files},
            diagnosticCycle=dict(codename='vision-camera-image-probe',readVersion='0.1.2',revokeVersion='0.1.3',authorized=True))
        if a.resume_read_from:
            h.require(a.resume_read_from.startswith('ingress-live-') and a.resume_read_from.removeprefix('ingress-live-').isdecimal(), 'RESUME_NAME_INVALID')
            previous=Path(c['records'])/a.resume_read_from
            old=json.loads((previous/'context.json').read_bytes());result=json.loads((previous/'result.json').read_bytes())
            intent=json.loads((previous/'diagnostic-upload-0.1.2-intent.json').read_bytes())
            response=json.loads((previous/'diagnostic-upload-0.1.2-response.json').read_bytes())
            before=json.loads((previous/'nonroot-live-ingress.json').read_bytes())['facts']['consumers']
            h.require(result.get('cloudMutation') is True and result.get('code')=='NATIVE_READER_IDENTITY_FAILED'
                and all(result['cleanup'].values()) and not (previous/'diagnostic-upload-0.1.3-intent.json').exists()
                and old['candidateManifestSha256']==context['candidateManifestSha256']
                and old['files']['vision-camera-probe']==context['files']['vision-camera-probe']==intent['binarySha256']
                and old['diagnosticCycle']==context['diagnosticCycle'] and intent['version']=='0.1.2'
                and intent['attemptStarted'] is True and response['httpStatus']==201 and len(before)==1,'RESUME_RECEIPT_INVALID')
            context['readCycleResume']=dict(attempt=a.resume_read_from,**intent,
                deploymentId=response['deploymentId'],serviceId=json.loads((previous/'diagnostic-catalog-before.json').read_bytes())['facts']['serviceId'],
                nativeReaderBoundingSet=before[0]['capabilities']['CapBnd'])
    h.atomic(records/'context.json',context);files.append(records/'context.json')
    h.remote(t,'umask 077\nmkdir '+q(str(remote)),timeout=15)
    options=h.ssh_args(t)[1:-1];options.remove('-T');i=options.index('-b');options[i:i+2]=['-o','BindAddress='+options[i+1]]
    h.run(['/usr/bin/scp',*options,*map(str,files),t['user']+'@'+t['host']+':'+str(remote)+'/'],timeout=30)
    if a.live:h.run(['/usr/bin/scp',*options,'-r',str(a.candidate),t['user']+'@'+t['host']+':'+str(remote/'candidate')],timeout=90)
    python=c['main']['packageRoot']+'/demo-artifacts/aosedge-sdv-demo/host-runtime/python/bin/python3.12'
    command=q(python)+' -I -B '+q(str(remote/worker.name))+(' --context ' if a.live else ' ')+q(str(remote/'context.json'))
    process=subprocess.Popen(h.ssh_args(t)+[command],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    with (records/'progress.jsonl').open('x') as log:
        for line in process.stdout:
            h.require(log.tell()<2**20,'PROGRESS_LIMIT');log.write(line);log.flush()
            if line.startswith('{'):print(line.strip(),flush=True)
    code=process.wait(timeout=10);diagnostic=process.stderr.read(8192)
    # Retain only fixed exception class/line diagnostics, never raw stderr.
    h.atomic(records/'transport.json',dict(exit=code,stderrPresent=bool(diagnostic)))
    collect='import pathlib,json; p=pathlib.Path('+repr(str(remote))+'); print(json.dumps({f.name:json.loads(f.read_bytes()) for f in p.glob("*.json") if f.name!="context.json" and f.stat().st_size<2097152}))'
    values=json.loads(h.remote(t,q(python)+' -I -B -c '+q(collect),timeout=20))
    for name,value in values.items():h.atomic(records/name,value)
    value=values.get('result.json',dict(outcome='UNCERTAIN',code='WORKER_RESULT_MISSING'))
    print(json.dumps({k:v for k,v in value.items() if k!='facts'}),flush=True)
    return code


if __name__=='__main__':raise SystemExit(main())
