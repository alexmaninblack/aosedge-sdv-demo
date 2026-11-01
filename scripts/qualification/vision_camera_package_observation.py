#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Read-only M4 package/catalog diagnosis; no VM boot or Cloud mutation."""
import argparse
import json
from pathlib import Path
import shlex

import remote_harness as h
from vision_vm_campaign import configuration


REMOTE=r'''import json,pathlib,subprocess,sys
base=pathlib.Path(BASE);sys.path.insert(0,str(base/'aosedge-sdv-demo/apps/demo-orchestrator/src'))
from aosedge_demo_orchestrator import runtime_paths
from aosedge_demo_orchestrator.status import load_configuration
from aosedge_demo_orchestrator.cloud_connection import selected_domain,cloud_binding
from aosedge_demo_orchestrator.cloud_runtime import launch
home=pathlib.Path.home();root=home/'SDV-Vision-Camera-Image-Lab-Data'
state=json.loads((root/'.run/demo-current/journal.json').read_bytes())
assert state['vehicles']['test']['runtime']['state']=='STOPPED'
records=home/'SDV-Qualification/vision-vm-m4'
context=json.loads((records/'native-camera-14/context.json').read_bytes())
with runtime_paths.installed_session(root):
 config=load_configuration(root);sdk,env=launch(root,config['cloudPython'],'unit_cloud.py')
 request=dict(tooling=str(pathlib.Path(context['bundle'])/'Contents/Resources/tooling/aosedge-sdv-demo/apps/demo-orchestrator/src'),
  credential=str(config['cloudProfiles']['service-provider']['credential']),ownerId=config['cloudProfiles']['service-provider']['expectedOwnerId'],
  oemCredential=str(config['cloudProfiles']['oem-delivery']['credential']),oemOwner=cloud_binding(state)['ownerId'],
  cloudDomain=selected_domain(state),unitId=state['vehicles']['test']['unitId'],records=str(records),afterAcceptance=AFTER)
script=SDK
done=subprocess.run([sdk[0],'-I','-B','-c',script],input=json.dumps(request),env=env,capture_output=True,text=True,timeout=75)
assert done.returncode==0,'PACKAGE_OBSERVATION_FAILED'
print(done.stdout)
'''

SDK=r'''import contextlib,io,json,pathlib,sys
r=json.load(sys.stdin);sys.path.insert(0,r['tooling'])
from aosedge_demo_orchestrator.unit_cloud import Cloud
from aosedge_demo_orchestrator.component_publication import Reads
from aosedge_demo_orchestrator.component_worker import verify
from aosedge_demo_orchestrator.components import archive_files
records=pathlib.Path(r['records'])
def differences(a,b,p=''):
 if type(a)!=type(b):return [p]
 if isinstance(a,dict):
  return [v for k in sorted(set(a)|set(b)) for v in ([p+'/'+k] if k not in a or k not in b else differences(a[k],b[k],p+'/'+k))]
 if isinstance(a,list):
  if len(a)!=len(b):return [p]
  return [v for i,(x,y) in enumerate(zip(a,b)) for v in differences(x,y,p+'/'+str(i))]
 return [] if a==b else [p]
with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
 cloud=Cloud(r,expected_role='service provider');reads=Reads(cloud)
 paths=[records/'native-camera-12/probe-0.1.2.tar.gz',records/'native-camera-14/probe-0.1.0.tar.gz']
 configs=[];payloads=[]
 for path in paths:
  verify(path,pathlib.Path(r['credential']))
  files=archive_files(archive_files(path.read_bytes())['batch.tar.gz'])
  configs.append(json.loads(files.pop('config.yaml')));payloads.append(files)
 services=reads.pages('services/')
 old=[v for v in services if v.get('codename')=='vision-camera-access-probe']
 new=[v for v in services if v.get('codename')=='vision-camera-image-probe']
 assert len(old)==1
 if r['afterAcceptance']:assert len(new)==1 and new[0]['title']=='Vision Camera Image Probe'
 else:assert not new
 failed=[]
 for name in ('native-camera-14','native-camera-15'):
  response=json.loads((records/name/'probe-upload-0.1.0-response.json').read_bytes())
  bundle=reads.pages('deployment-bundles/',response['deploymentId'])[0]
  message=str(bundle.get('build_info')).strip().lower()
  generic=message in ('error: failed to build deployment bundle.','error: failed to build deployment bundle','error. failed to build deployment bundle.')
  failed.append(dict(state=bundle['state'],diagnosis='GENERIC_DEPLOYMENT_BUNDLE_BUILD_FAILURE' if generic else 'UNCLASSIFIED_BOUNDED_BUILD_STATUS'))
 oem=Cloud(dict(credential=r['oemCredential'],ownerId=r['oemOwner'],cloudDomain=r['cloudDomain']))
 assigned=oem.pages('units/'+r['unitId']+'/subjects-services/')
 own_unit_services=[v.get('service',{}).get('codename') for v in assigned]
 assert not any(v and any(k in v.lower() for k in ('brake','tire','vehicle-data-provider')) for v in own_unit_services)
 facts=dict(scenario='VISION_CAMERA_PACKAGE_READ_ONLY_DIAGNOSIS',signaturesVerified=True,
  configurationDifferenceFields=differences(*configs),payloadFilesIdentical=payloads[0]==payloads[1],
  oldTitleEqualsNewTitle=configs[0]['items'][0]['identity']['title']==configs[1]['items'][0]['identity']['title'],
  newTitleAlreadyUsedByRetainedService=old[0]['title']==configs[1]['items'][0]['identity']['title'],
  newServiceAbsent=True,failedBuilds=failed,visionUnitHasNoBrakeTireVdpAssignment=True,
  visionAssignedServiceCount=len(assigned),mutation=False,vmStarted=False)
 facts['serviceCreationPermitted']='services_create' in cloud.user['effectivePermissions']
 if r['afterAcceptance']:
  own=new[0]['id']
  assert len(assigned)==1 and assigned[0]['service']['id']==own
  receipt=json.loads((records/'native-camera-17/probe-subject-create-response.json').read_bytes())['subject']
  subject=oem.call('subjects/'+receipt['id']+'/')
  assert subject['label']=='SDV Vision Camera Image Probe'
  members=oem.pages('subjects/'+receipt['id']+'/units/')
  bindings=oem.pages('subjects/'+receipt['id']+'/services/')
  assert len(members)==1 and members[0]['id']==r['unitId']
  assert len(bindings)==1 and bindings[0]['service']['id']==own
  versions=reads.pages('services/'+own+'/service-versions/')
  assert {v['version']:str(v['container_state']).lower() for v in versions}=={'0.1.0':'ready','0.1.1':'ready'}
  states=[]
  for version in ('0.1.0','0.1.1'):
   response=json.loads((records/'native-camera-17'/('probe-upload-'+version+'-response.json')).read_bytes())
   states.append(reads.pages('deployment-bundles/',response['deploymentId'])[0]['state'])
  assert states==['done','done']
  facts.update(newServiceAbsent=False,correctedTitleAccepted=True,successfulBuildStates=states,
   visionSubjectHasOnlyThisUnit=True,visionSubjectHasOnlyThisService=True,visionUnitHasOnlyVisionAssignment=True,
   retainedServiceTitleUnchanged=old[0]['title']==configs[0]['items'][0]['identity']['title'])
print(json.dumps(facts))
'''


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--config',type=Path,required=True)
    p.add_argument('--attempt',type=int,choices=(1,2),default=1)
    p.add_argument('--after-acceptance',action='store_true')
    a=p.parse_args();c=configuration(a.config)
    python=c['main']['packageRoot']+'/demo-artifacts/aosedge-sdv-demo/host-runtime/python/bin/python3.12'
    code=REMOTE.replace('BASE',repr(c['main']['packageRoot'])).replace('SDK',repr(SDK)).replace('AFTER',repr(a.after_acceptance))
    result=json.loads(h.remote(c['transport'],shlex.quote(python)+' -I -B -c '+shlex.quote(code),timeout=85))
    target=Path(c['records'])/(('cloud-subject-acceptance-' if a.after_acceptance else 'cloud-build-diagnostic-')+str(a.attempt).zfill(2)+'.json')
    h.require(not target.exists(),'DIAGNOSTIC_EXISTS_RECONCILE');h.atomic(target,result)
    print(json.dumps(result),flush=True)


if __name__=='__main__':main()
