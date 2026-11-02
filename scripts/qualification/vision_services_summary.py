#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Bind immutable overnight receipts and actual M4 screenshots; never run models."""
import argparse
from html import escape
import json
import os
from pathlib import Path
import shlex
import sys
import remote_harness as h


def verdict(api,ui,root):
    h.require(api.get('apiPermanentPlatform')=='PASS_NO_TRANSIENT_PLATFORM_OVERRIDES'
        and api.get('code')=='ModuleNotFoundError' and all(api.get('cleanup',{}).values())
        and bool(api.get('cleanup')),'API_RECEIPT_NOT_ACCEPTABLE')
    h.require(ui.get('outcome')=='PASS_PERMANENT_VISION_HEADED_BROWSER_UI'
        and ui.get('cleanup') and all(ui['cleanup'].values()),'HEADED_UI_RECEIPT_NOT_ACCEPTABLE')
    if root.get('outcome') in ('PASS_ROOT6_CLOUD_INVENTORY_AFTER_EXACT_CACHE_RECONCILIATION',
            'PASS_ROOT6_CLOUD_INVENTORY_AFTER_NATIVE_CATALOG_RECONCILIATION'):
        h.require(root.get('rootfsCloudConfirmed') is True and root.get('cleanup')
            and all(root['cleanup'].values()),'ROOTFS_RECONCILIATION_CLEANUP_INCOMPLETE')
        return 'PASS_BOUNDED_NATIVE_API_AND_HEADED_VISION_UI'
    return 'NOT_COMPLETE_ROOTFS_CLOUD_INVENTORY_GATE_OPEN'


def main():
    p=argparse.ArgumentParser();p.add_argument('--config',type=Path,required=True);p.add_argument('--final',action='store_true');a=p.parse_args()
    from vision_vm_campaign import configuration
    c=configuration(a.config);base=Path(c['records']);out=base/('vision-services-overnight-summary-02' if a.final else 'vision-services-overnight-summary-01')
    h.require(not out.exists() or (out.is_dir() and not out.is_symlink() and out.stat().st_uid==os.getuid()
        and not any(out.iterdir())),'SUMMARY_EXISTS_RECONCILE');out.mkdir(mode=0o700,exist_ok=True)
    def read(case,name='result.json'):return json.loads((base/case/name).read_bytes())
    api_case='vision-services-permanent-api-ui-01';ui_case='vision-services-permanent-api-ui-03';root_case='vision-services-root-cache-10'
    api=read(api_case);ui=read(ui_case);root=read(root_case)
    for key,name in [('resultSha256','result.json'),('characterizationSha256','native-characterization.json'),
        ('securitySha256','native-functional-security-after-characterization.json')]:
        h.require(ui['apiProofReused'][key]==h.digest(base/api_case/name),'API_PROOF_CHANGED')
    h.require(read('vision-services-camera-update-01')['outcome']=='PASS_SAME_VISION_NATIVE_CAMERA_012_UPDATE'
        and read('vision-services-recovery-01')['outcome'].startswith('PASS_'),'CAMERA_OR_RECOVERY_GATE_MISSING')
    code='''import json,pathlib,subprocess,socket,os
p=pathlib.Path.home()/'SDV-Vision-Camera-Image-Lab-Data';j=json.loads((p/'.run/demo-current/journal.json').read_bytes())
item=j['vehicles']['test'];assert item['unitId']=='af6d074a-6ce1-49ba-b613-0476e7b6d1b5' and item['localVmId']=='89273f16-4be0-4b22-b4cb-58d08533c8bc'
rows=[line.split(None,1)[1] for line in subprocess.check_output(['/bin/ps','-axo','pid=,command='],text=True).splitlines()
 if len(line.split(None,1))==2 and int(line.split(None,1)[0]) not in (os.getpid(),os.getppid())]
facts=dict(sameVmAndUnit=True,sourceStopped=j['source']['state']=='STOPPED',vmStopped=item['runtime']['state']=='STOPPED',
 ownedBrowserStopped=not any('vision-services-permanent-api-ui-' in row and '--user-data-dir=' in row for row in rows),
 ownedQemuStopped=not any('qemu-system-' in row and '89273f16-4be0-4b22-b4cb-58d08533c8bc' in row for row in rows))
probe=socket.socket();probe.settimeout(1);facts['presenterListenerReleased']=probe.connect_ex(('127.0.0.1',18080))!=0;probe.close()
print(json.dumps(facts))
'''
    py=c['main']['packageRoot']+'/demo-artifacts/aosedge-sdv-demo/host-runtime/python/bin/python3.12'
    cleanup=json.loads(h.remote(c['transport'],shlex.join([py,'-I','-B','-c',code]),timeout=20))
    h.atomic(out/'final-target-idle.json',cleanup);h.require(all(cleanup.values()),'FINAL_OWNED_PROCESS_CLEANUP_INCOMPLETE')
    characterization={k:v for k,v in read(api_case,'native-characterization.json').items() if k!='samples'}
    visual=read(ui_case,'headed-vision-ui-loss-and-recovery.json')
    receipts={case:h.digest(base/case/'result.json') for case in (api_case,ui_case,root_case,
        'vision-services-camera-update-01','vision-services-recovery-01','vision-services-native-live-16','vision-services-root-cache-11')}
    audit=read('vision-services-root-cache-11','exact-native-cache-audit.json')
    root_native=read('vision-services-root-cache-11','native-committed-final-read-only.json')
    h.require(root_native['rootfsCommittedReadOnly'] and audit['pending']==[] and audit['cm']['NRestarts']=='0'
        and audit['readOnlyRootfsCatalog']==[dict(relativePath='cm.db',rootfsRows=[])],'FINAL_READONLY_ROOT_CAUSE_UNCONFIRMED')
    diagnosis=dict(nativeRootCommitted=True,rootfsRowsInNativeCatalog=0,originalCompleteOciClosureIntact=True,
        manualDatabaseChanges=False,normalSameVersionSendRejectedHttp=400,sendRepeated=False,
        sourceGuard='ROOTFS_NATIVE_CACHE_MIGRATION_REQUIRED_BEFORE_PUBLICATION',
        investigationScenarioSeconds=round(sum(read('vision-services-root-cache-%02d'%n)['seconds'] for n in range(1,12)),2))
    result=dict(outcome=verdict(api,ui,root),sourcePins=dict(
        integrationRuntime='48d31423e676f62356f132dcaeabfca6718cb05f',
        services='a10c6f354866e5d3e839ee59a18344bb7cad96df',
        gateway='34bdea3dfb254dc7aedf34c7915054a29898837e',
        platform='9d540803bbebef1d1270471d5c4e5233301b6547'),
        versions=dict(rootfs='6.1.1-vision-camera.6',camera='0.1.2',perception='0.1.1',assessment='0.1.1',host='0.6.4'),
        characterization=characterization,visual=visual['facts'],cleanup=cleanup,receiptSha256=receipts,rootfsDiagnosis=diagnosis,
        retainedDataPreserved=True,rootfsCloudConfirmed=root.get('rootfsCloudConfirmed',False),
        originalFailuresPreserved=True,publicRelease=False,mainChanged=False,
        limits=['Stationary calibrated engineering reference, not moving-route or learned-accuracy acceptance.',
            'Five results/s and 500-ms full capture-to-display goals are not qualified.',
            'Trusted vehicle geometry is unavailable; the dependent shadow plan is correctly withheld.',
            'Headed browser covers all three new Vision views. Native Driving Control buttons and camera overlays were not automated.',
            'No CARLA, Main Factory, boot or second Vision rootfs image build. No retained VDP/Brake/Tire changes.'],
        uiFindings=['Input-loss reason says SOURCE NOT SELECTED while the selected Source owner remains RUNNING: clarify diagnostic wording.',
            'Perception cards describe the three model roles, not separate raw outputs; no new browser transport was invented.',
            'Ground-plane plot is not an overlay on the newer live camera image. Full associations stay server-side.'])
    h.atomic(out/'result.json',result)
    images=['01-overview-available','02-perception','03-assessment','04-input-unavailable','05-input-recovered']
    page='''<!doctype html><html lang="en"><meta charset="utf-8"><title>Vision overnight API / UI</title>
<style>body{font:16px system-ui;max-width:1250px;margin:32px auto;padding:0 24px;background:#f1f5f9;color:#18334b}h1{font-size:30px}img{max-width:100%;border:1px solid #c0cfdd;border-radius:8px}section{margin:32px 0}li{margin:8px 0}pre{white-space:pre-wrap;background:white;padding:18px;border-radius:8px}</style><h1>Retained M4 Vision — overnight verification</h1>'''
    page+='<p><strong>'+escape(result['outcome'])+'</strong></p><p>Actual native services and real M4 headed-browser captures. No public release or Main promotion.</p>'
    page+='<h2>Measured stationary run</h2><pre>'+escape(json.dumps(characterization,indent=2))+'</pre>'
    page+='<h2>Scope and remaining limits</h2><ul>'+''.join('<li>'+escape(x)+'</li>' for x in result['limits'])+'</ul>'
    page+='<h2>Unresolved Rootfs gate</h2><p>The native root is committed and healthy, but its CM catalog row is absent and Cloud omits it. Original image blobs are intact. No manual database edit, fresh VM or second image was used. A supported catalog recovery or explicitly agreed data-preserving recovery plan is required before full acceptance.</p><pre>'+escape(json.dumps(diagnosis,indent=2))+'</pre>'
    page+='<h2>UI review observations</h2><ul>'+''.join('<li>'+escape(x)+'</li>' for x in result['uiFindings'])+'</ul>'
    page+='<h2>Execution time</h2><p>API campaign: '+str(api['seconds'])+' s (including 180-s sampling and preserved UI-import failure). Final UI campaign: '+str(ui['seconds'])+' s, of which visible semantic actions: '+str(visual['seconds'])+' s. These are scenario times, not total overnight implementation/debugging time.</p>'
    for image in images:
        target=base/ui_case/'review'/(image+'.png');h.require(target.is_file(),'ACTUAL_SCREENSHOT_MISSING')
        page+='<section><h2>'+escape(image.replace('-',' '))+'</h2><img alt="Actual M4 browser capture" src="../'+ui_case+'/review/'+image+'.png"></section>'
    page+='<h2>Preserved receipts</h2><pre>'+escape(json.dumps(receipts,indent=2))+'</pre></html>'
    (out/'index.html').write_text(page)
    print(json.dumps(dict(outcome=result['outcome'],report=str(out/'index.html'),cleanup=cleanup)))
    return 0 if result['outcome'].startswith('PASS_') else 2


if __name__=='__main__':raise SystemExit(main())
