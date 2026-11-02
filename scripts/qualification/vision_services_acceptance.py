#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""One permanent-platform API/visible-browser campaign on the retained Vision VM."""
import argparse
import json
from pathlib import Path
import shlex
import subprocess
import remote_harness as h
from vision_vm_campaign import configuration


def main():
    p=argparse.ArgumentParser();p.add_argument('--config',type=Path,required=True);p.add_argument('--ui-after-api',action='store_true')
    p.add_argument('--ui-case',type=int,choices=(2,3),default=2);a=p.parse_args();c=configuration(a.config)
    prior=Path(c['records'])/'vision-services-native-live-19'
    camera=json.loads((Path(c['records'])/'vision-services-camera-update-01/result.json').read_bytes())
    h.require(camera['outcome']=='PASS_SAME_VISION_NATIVE_CAMERA_012_UPDATE' and all(camera['cleanup'].values()),'PERMANENT_CAMERA_GATE_REQUIRED')
    name=('vision-services-permanent-api-ui-%02d'%a.ui_case) if a.ui_after_api else 'vision-services-permanent-api-ui-01';records=Path(c['records'])/name;remote=Path(c['remoteRoot'])/name
    if a.ui_after_api and a.ui_case==3:
        failed=json.loads((Path(c['records'])/'vision-services-permanent-api-ui-02/result.json').read_bytes())
        h.require(failed['code']=='VISION_BROWSER_CLEANUP_UNCONFIRMED' and all(failed['cleanup'].values()),'BROWSER_PIPE_CLEANUP_FAILURE_NOT_RECONCILED')
    h.require(not records.exists(),'PERMANENT_ACCEPTANCE_EXISTS_RECONCILE');records.mkdir(mode=0o700)
    context=json.loads((prior/'context.json').read_bytes());host=json.loads((Path(c['records'])/'vision-services-host-05/result.json').read_bytes())
    here=Path(__file__).parent
    files=[here/'vision_services_live.py',here/'vision_services_primitives_guest.py',here/'vision_services_visual.py',here/'vision_services_browser.cjs']
    for key in ('groupAliasProof','communicationCacheProof','nativeAdversarialProof','nativeUnixOnlyProof'):context.pop(key,None)
    context.update(permanentSystem=True,bundle=host['bundle'],bootstrapManifest=host['manifestSha256'],workerSha256=h.digest(files[0]),
        uiRuntime=json.loads(Path('/Volumes/SDV-Dev/sdv/build/vision-services/ui-runtime-01/signed-delivery.json').read_bytes()))
    if a.ui_after_api:
        api=Path(c['records'])/'vision-services-permanent-api-ui-01';value=json.loads((api/'result.json').read_bytes())
        characterization=json.loads((api/'native-characterization.json').read_bytes())
        security=json.loads((api/'native-functional-security-after-characterization.json').read_bytes())['facts']
        h.require(value['code']=='ModuleNotFoundError' and value['apiPermanentPlatform']=='PASS_NO_TRANSIENT_PLATFORM_OVERRIDES'
            and all(value['cleanup'].values()) and characterization['seconds']>=180 and characterization['uniqueObservedResults']>=20
            and not security['scopedAvcs'] and security['nativeScopedAvcCount']==0,'COMPLETED_API_PROOF_REQUIRED')
        context['uiOnlyAfterApi']=dict(resultSha256=h.digest(api/'result.json'),characterizationSha256=h.digest(api/'native-characterization.json'),
            securitySha256=h.digest(api/'native-functional-security-after-characterization.json'),originalFailurePreserved=True)
    for path in files:
        if path.name!='vision_services_live.py':context['files'][path.name]=h.digest(path)
    context['guestFiles']={'vision_services_primitives_guest.py':h.digest(here/'vision_services_primitives_guest.py')}
    h.atomic(records/'context.json',context)
    # Verified APFS clones avoid retransferring already published service blobs.
    unchanged={n:v for n,v in context['files'].items() if n not in {f.name for f in files}}
    code='''import pathlib,hashlib,subprocess
p=pathlib.Path(REMOTE);old=pathlib.Path(OLD);pins=PINS;p.mkdir(mode=0o700)
for name,pin in pins.items():
 f=old/name;assert hashlib.sha256(f.read_bytes()).hexdigest()==pin
 subprocess.run(['/bin/cp','-c',str(f),str(p/name)],check=True,capture_output=True)
print('RETAINED_INPUTS_VERIFIED_AND_CLONED')
'''.replace('REMOTE',repr(str(remote))).replace('OLD',repr(str(Path(c['remoteRoot'])/prior.name))).replace('PINS',repr(unchanged))
    py=c['main']['packageRoot']+'/demo-artifacts/aosedge-sdv-demo/host-runtime/python/bin/python3.12'
    h.remote(c['transport'],shlex.join([py,'-I','-B','-c',code]),timeout=30)
    options=h.ssh_args(c['transport'])[1:-1];options.remove('-T');i=options.index('-b');options[i:i+2]=['-o','BindAddress='+options[i+1]]
    h.run(['/usr/bin/scp',*options,*map(str,files),str(records/'context.json'),c['transport']['user']+'@'+c['transport']['host']+':'+str(remote)+'/'],timeout=30)
    proc=subprocess.Popen(h.ssh_args(c['transport'])+[shlex.join([py,'-I','-B',str(remote/files[0].name),'--worker',str(remote/'context.json')])],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    with (records/'progress.jsonl').open('x') as stream:
        for line in proc.stdout:h.require(stream.tell()<1024**2,'PROGRESS_LIMIT');stream.write(line);stream.flush();print(line.strip(),flush=True)
    exit_code=proc.wait(timeout=15);diagnostic=proc.stderr.read(8192)
    code='import pathlib,json;p=pathlib.Path('+repr(str(remote))+');print(json.dumps({f.name:json.loads(f.read_bytes()) for f in p.glob("*.json") if f.name!="context.json" and f.stat().st_size<2097152}))'
    for name,value in json.loads(h.remote(c['transport'],shlex.join([py,'-I','-B','-c',code]),timeout=20)).items():h.atomic(records/name,value)
    h.atomic(records/'transport.json',dict(exit=exit_code,stderrPresent=bool(diagnostic)))
    # Screenshots are created by the real headed M4 browser, never reconstructed.
    code='import pathlib,json;p=pathlib.Path('+repr(str(remote/'visual'))+');print(json.dumps([f.name for f in p.glob("*.png") if f.is_file() and not f.is_symlink() and f.stat().st_size<8388608]))'
    images=json.loads(h.remote(c['transport'],shlex.join([py,'-I','-B','-c',code]),timeout=15))
    if images:
        target=records/'review';target.mkdir(mode=0o700)
        for name in images:
            h.require('/' not in name and name.endswith('.png'),'SCREENSHOT_NAME_INVALID')
            h.run(['/usr/bin/scp',*options,c['transport']['user']+'@'+c['transport']['host']+':'+str(remote/'visual'/name),str(target/name)],timeout=30)
        page='<!doctype html><meta charset="utf-8"><title>Vision API/UI evidence</title><style>body{font:16px system-ui;background:#eef3f8;color:#17324c;margin:32px}img{max-width:100%;border:1px solid #b8c9db}section{margin:30px 0}</style><h1>Retained M4 Vision — API / headed UI evidence</h1><p>Captured from the actual M4 browser. Rootfs Cloud inventory omission remains an open qualification defect; no release promotion.</p>'
        for name in sorted(images):page+='<section><h2>'+name.removesuffix('.png').replace('-',' ')+'</h2><img src="'+name+'"></section>'
        (target/'index.html').write_text(page)
    return exit_code


if __name__=='__main__':raise SystemExit(main())
