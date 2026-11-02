#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""One reversible same-GID short-name proof, reusing the qualified native inputs."""
import argparse
import json
from pathlib import Path
import shlex
import subprocess
import tarfile
import remote_harness as h
from vision_vm_campaign import configuration


def main():
    p=argparse.ArgumentParser();p.add_argument('--config',type=Path,required=True);p.add_argument('--reconcile-ordering-evidence',action='store_true');a=p.parse_args();c=configuration(a.config)
    if a.reconcile_ordering_evidence:
        records=Path(c['records'])/'vision-services-native-live-19';original=json.loads((records/'result.json').read_bytes())
        configuration_record=records/'native-short-role-group-configuration.json';observed=json.loads(configuration_record.read_bytes())['facts']
        security_record=records/'native-security-after-communication-cache-path.json';security=json.loads(security_record.read_bytes())['facts']
        names=json.loads((records/'context.json').read_bytes())['groupAliasProof']
        actual={r['name'].removeprefix('vision-'):r['groups'][0] for r in observed['resourceFile'][1:]}
        h.require(original['code']=='VISION_ROLE_GROUP_ALIASES_NOT_APPLIED' and all(original['cleanup'].values())
            and original['servicesDeployed'] and original['cloudMutation'] is False and actual==names
            and observed['smVisibleResourceFile']==observed['resourceFile'] and not security['scopedAvcs']
            and security['nativeScopedAvcCount']==0,'ROLE_GROUP_EVIDENCE_NOT_RECONCILED')
        view=json.loads((records/'latest-vision-observation.json').read_bytes())
        h.require(view['state']=='AVAILABLE' and view['reference'] and view['perceptionVersion']==view['assessmentVersion']=='0.1.1','ROLE_GROUP_FUNCTIONAL_RESULT_REQUIRED')
        output=dict(outcome='PASS_NATIVE_SHORT_ROLE_GROUPS_AND_RETAINED_SUCCESSORS',cleanup=original['cleanup'],cloudMutation=False,
            reconciliation='JSON_OBJECT_ORDER_WAS_NOT_A_RESOURCE_MAPPING',originalResultSha256=h.digest(records/'result.json'),
            evidenceSha256={p.name:h.digest(p) for p in (configuration_record,security_record,records/'latest-vision-observation.json')},
            originalFailurePreserved=True,liveRunRepeated=False)
        h.atomic(records/'group-alias-acceptance.json',output);print(json.dumps(output));return 0
    previous=Path(c['records'])/'vision-services-native-live-17';prior=json.loads((previous/'result.json').read_bytes())
    h.require(prior['outcome']=='PASS_NATIVE_COMMUNICATION_CACHE_PATH_AND_RETAINED_SUCCESSORS' and all(prior['cleanup'].values()),'NATIVE_CACHE_GATE_REQUIRED')
    failure=json.loads((Path(c['records'])/'vision-services-native-live-18/result.json').read_bytes())
    h.require(failure['code']=='EnvironmentError' and all(failure['cleanup'].values()),'LEGACY_SOURCE_OBSERVER_FAULT_NOT_RECONCILED')
    name='vision-services-native-live-19';records=Path(c['records'])/name;remote=Path(c['remoteRoot'])/name
    h.require(not records.exists(),'GROUP_PROOF_EXISTS_RECONCILE');records.mkdir(mode=0o700)
    context=json.loads((previous/'context.json').read_bytes());here=Path(__file__).parent;platform=here.parents[2]/'vision-camera-platform'
    names=json.loads((platform/'contracts/camera-access/native-services-profile.json').read_bytes())['groupNames']
    payload=Path('/Volumes/SDV-Dev/sdv/build/vision-services/exchange-primitives-01/camera-access-groups.tar')
    with tarfile.open(payload) as archive:raw=archive.extractfile('bin/camera-access').read()
    camera=records/'camera-access';camera.write_bytes(raw);camera.chmod(0o444)
    plan=json.loads((previous/'native-image-path-proof.json').read_bytes());plan.update(reuseCommunicationCache=True,groupNames=names,legacyGroupAliases=True)
    h.atomic(records/'native-image-path-proof.json',plan)
    files=[here/'vision_services_live.py',here/'vision_services_primitives_guest.py',
        platform/'tests/fixtures/vision-native-exchange/aos-vision-exchange.service',camera,records/'native-image-path-proof.json']
    context.update(groupAliasProof=names,workerSha256=h.digest(here/'vision_services_live.py'))
    for path in files:
        if path.name!='vision_services_live.py':context['files'][path.name]=h.digest(path)
    context['guestFiles']={name:pin for name,pin in context['files'].items() if name in context['guestFiles']}
    h.atomic(records/'context.json',context)
    code='''import pathlib,hashlib,subprocess,json
p=pathlib.Path(REMOTE);old=pathlib.Path(OLD);pins=PINS;p.mkdir(mode=0o700)
for name,pin in pins.items():
 f=old/name;assert hashlib.sha256(f.read_bytes()).hexdigest()==pin
 subprocess.run(['/bin/cp','-c',str(f),str(p/name)],check=True,capture_output=True)
print('RETAINED_HOST_INPUTS_CLONED')
'''.replace('REMOTE',repr(str(remote))).replace('OLD',repr(str(Path(c['remoteRoot'])/previous.name))).replace('PINS',repr({n:v for n,v in context['files'].items() if n not in {f.name for f in files}}))
    py=c['main']['packageRoot']+'/demo-artifacts/aosedge-sdv-demo/host-runtime/python/bin/python3.12'
    h.remote(c['transport'],shlex.join([py,'-I','-B','-c',code]),timeout=30)
    options=h.ssh_args(c['transport'])[1:-1];options.remove('-T');i=options.index('-b');options[i:i+2]=['-o','BindAddress='+options[i+1]]
    h.run(['/usr/bin/scp',*options,*map(str,files),str(records/'context.json'),c['transport']['user']+'@'+c['transport']['host']+':'+str(remote)+'/'],timeout=30)
    proc=subprocess.Popen(h.ssh_args(c['transport'])+[shlex.join([py,'-I','-B',str(remote/'vision_services_live.py'),'--worker',str(remote/'context.json')])],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    with (records/'progress.jsonl').open('x') as stream:
        for line in proc.stdout:h.require(stream.tell()<1024**2,'PROGRESS_LIMIT');stream.write(line);stream.flush();print(line.strip(),flush=True)
    exit_code=proc.wait(timeout=15);diagnostic=proc.stderr.read(8192)
    code='import pathlib,json;p=pathlib.Path('+repr(str(remote))+');print(json.dumps({f.name:json.loads(f.read_bytes()) for f in p.glob("*.json") if f.name!="context.json" and f.stat().st_size<2097152}))'
    for name,value in json.loads(h.remote(c['transport'],shlex.join([py,'-I','-B','-c',code]),timeout=20)).items():h.atomic(records/name,value)
    h.atomic(records/'transport.json',dict(exit=exit_code,stderrPresent=bool(diagnostic)));return exit_code


if __name__=='__main__':raise SystemExit(main())
