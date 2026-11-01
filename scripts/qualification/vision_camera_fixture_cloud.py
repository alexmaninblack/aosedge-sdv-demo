#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""SDK worker for one diagnostic native-Aos Camera reader, never a product API."""
import contextlib
import io
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

CODENAME='vision-camera-image-probe'
TITLE='Vision Camera Image Probe'
LABEL='SDV Vision Camera Image Probe'


def require(ok, code):
    if not ok:raise ValueError('VISION_PROBE_'+code)


def terminal_retry(bundle, deployment_id, service_id, versions):
    """A failed build with no catalog effect permits one journalled resubmit."""
    require(bundle.get('id')==deployment_id and str(bundle.get('state')).lower()=='error'
            and service_id is None and not versions,'TERMINAL_BUILD_WITHOUT_EFFECT_REQUIRED')


def title_correction(before, after):
    import copy
    expected=copy.deepcopy(before)
    require(expected['items'][0]['identity']['codename']==CODENAME
            and expected['items'][0]['identity']['title']=='Vision Camera Access Probe','TITLE_CORRECTION_SOURCE_INVALID')
    expected['items'][0]['identity']['title']=TITLE
    require(after==expected,'TITLE_CORRECTION_MUST_BE_ONLY_CHANGE')


def configuration(version):
    require(version in ('0.1.0','0.1.1','0.1.2','0.1.3'),'VERSION_INVALID')
    return dict(schemaVersion=2,publisher=dict(author='maninblack'),items=[dict(
        identity=dict(type='service',codename=CODENAME,title=TITLE),
        version=version,sourceFolder='service',images=[dict(sourceFolder='arm64',archInfo=dict(architecture='arm64'))],
        configuration=dict(workingDir='/',cmd='/usr/bin/vision-camera-probe',instances=dict(minInstances=1,priority=10),
            offlineTTL='P7D',quotas=dict(cpuLimit=1000,ramLimit=134217728,storageLimit=16777216,
                stateLimit=1048576,tmpLimit=1048576,noFileLimit=1024,pidsLimit=32),alertRules=None,
            resources=[dict(name='vision-camera-read')] if version in ('0.1.0','0.1.2') else [],allowedConnections=[]),dependencies=[])] )


def execute(r):
    from aosedge_demo_orchestrator.unit_cloud import Cloud
    from aosedge_demo_orchestrator.vision_camera_delivery import scope
    from aosedge_demo_orchestrator.vision_bootstrap import PROFILE
    from aosedge_demo_orchestrator.component_cloud import upload_bundle
    from aosedge_demo_orchestrator.component_publication import Reads,bundle_view
    from aosedge_demo_orchestrator.component_worker import credential_snapshot,verify
    from aosedge_demo_orchestrator.service_cloud import service_view,version_view,unit_view
    from aosedge_demo_orchestrator.status import object_id
    action=r['action'];version=r.get('probeVersion','0.1.0');configuration(version)
    oem=Cloud(dict(credential=r['oemCredential'],cloudDomain=r['cloudDomain'],ownerId=r['oemOwner']))
    scope(oem,dict(r,version='0.1.0',setupProfile=PROFILE))
    provider=Cloud(dict(credential=r['spCredential'],cloudDomain=r['cloudDomain'],ownerId=r['spOwner']),expected_role='service provider')
    if action=='preflight':
        provider.require('services_list','services_read','services_service_versions_list','services_units_list',
                         'deployment_bundles_create','deployment_bundles_list')
        oem.require('subjects_list','subjects_read','subjects_create','subjects_units_create',
                    'subjects_units_list','subjects_services_list','subjects_services_create','units_subjects_services_list')
        services=provider.pages('services/')
        require(not any(v.get('title')==TITLE and v.get('codename')!=CODENAME for v in services),'TITLE_OWNED_BY_ANOTHER_SERVICE')
        if not any(v.get('codename')==CODENAME for v in services):provider.require('services_create')
        return dict(ready=True)
    if action=='sign':
        from aos_signer.upload_config_v2.batch_configuration import UpdateBundleConfiguration
        from aos_signer.signer.signer import Signer
        import hashlib
        binary=Path(r['binary']);raw=binary.read_bytes()
        require(binary.is_file() and not binary.is_symlink() and len(raw)<8*1024**2 and raw[:5]==b'\x7fELF\x02'
                and raw[18:20]==b'\xb7\x00' and hashlib.sha256(raw).hexdigest()==r['binarySha256'],'BINARY_CHANGED')
        output=Path(r['output']);require(not output.exists(),'SIGN_OUTPUT_EXISTS')
        with tempfile.TemporaryDirectory(prefix='.probe-sign-',dir=output.parent) as temporary:
            root=Path(temporary);p=root/'service/arm64/usr/bin/vision-camera-probe';p.parent.mkdir(parents=True);p.write_bytes(raw);p.chmod(0o555)
            config=root/'config.yaml';config.write_text(json.dumps(configuration(version)))
            old=Path.cwd()
            try:
                os.chdir(root)
                with credential_snapshot(dict(credential=r['spCredential'])) as private:
                    Signer(UpdateBundleConfiguration(config),config,pkcs12_path=private['credential']).process()
                    observed=verify(root/'batch.tar.gz',Path(private['credential']))
            finally:os.chdir(old)
            shutil.copyfile(root/'batch.tar.gz',output);output.chmod(0o444)
        return dict(observed,verificationTrust='CONFIGURED_SP_SIGNING_CERTIFICATE')
    reads=Reads(provider)
    service_rows=reads.pages('services/')
    require(not any(v.get('title')==TITLE and v.get('codename')!=CODENAME for v in service_rows),'TITLE_OWNED_BY_ANOTHER_SERVICE')
    matches=[service_view(row,provider.user) for row in service_rows if row.get('codename')==CODENAME]
    require(len(matches)<=1,'SERVICE_AMBIGUOUS')
    require(not matches or matches[0]['title']==TITLE,'SERVICE_TITLE_CHANGED')
    service_id=matches[0]['id'] if matches else None
    if r.get('serviceId'):require(service_id==r['serviceId'],'SERVICE_CHANGED')
    versions=[version_view(row) for row in reads.pages('services/'+service_id+'/service-versions/')] if service_id else []
    selected=[row for row in versions if row['version']==version]
    require(len(selected)<=1,'VERSION_AMBIGUOUS')
    if service_id:
        recipients=[unit_view(row) for row in reads.pages('services/'+service_id+'/units/')]
        current=r['vehicles']['test']
        require(all(row['id']==current['unitId'] and row['system_uid']==current['systemUid'] for row in recipients),'FOREIGN_RECIPIENT')
    if action=='catalog':
        return dict(serviceId=service_id,versions=[dict(version=v['version'],versionId=v['id'],state=v['container_state']) for v in versions])
    if action=='upload':
        require(not selected,'VERSION_EXISTS_RECONCILE')
        if service_id is None:provider.require('services_create')
        if r.get('failedDeploymentId'):
            rows=reads.pages('deployment-bundles/',r['failedDeploymentId'])
            require(len(rows)==1,'FAILED_BUILD_NOT_OBSERVED')
            terminal_retry(rows[0],r['failedDeploymentId'],service_id,versions)
        path=Path(r['bundle']);verify(path,Path(r['spCredential']),r['expectedSha256'])
        from aosedge_demo_orchestrator.components import archive_files
        outer=archive_files(path.read_bytes());inner=archive_files(outer['batch.tar.gz'])
        require(json.loads(inner['config.yaml'])==configuration(version),'SIGNED_CONFIG_CHANGED')
        return upload_bundle(provider,path,prefix='VISION_PROBE')
    if action=='publication':
        deployment=object_id(r['deploymentId']);bundles=Reads(provider).pages('deployment-bundles/',deployment)
        require(len(bundles)==1 and bundles[0]['id']==deployment,'BUNDLE_NOT_OBSERVED')
        bundle=bundle_view(bundles[0]);state=str(bundle['state']).lower()
        if state=='error':return dict(stage='ERROR',serviceId=service_id,catalogVersionCount=len(versions))
        if state!='done' or not selected:return dict(stage='PROCESSING',serviceId=service_id)
        require(len(bundle['items'])==1 and bundle['items'][0]['type']=='service'
                and bundle['items'][0]['codename']==CODENAME and bundle['items'][0]['version']==version,'BUNDLE_CONTENT_CHANGED')
        return dict(stage='READY' if str(selected[0]['container_state']).lower()=='ready' else 'PROCESSING',
                    serviceId=service_id,versionId=selected[0]['id'])
    require(service_id is not None,'SERVICE_REQUIRED')
    from aosedge_demo_orchestrator.service_assignment import _pages,_subject
    subjects=_pages(oem,'subjects/',lambda row:object_id(row['id']))
    candidates=[row for row in subjects if row.get('label')==LABEL]
    if action=='subject-create':
        require(not candidates,'SUBJECT_COLLISION_RECONCILE')
        oem.require('subjects_create')
        value=oem.call('subjects/','POST',dict(label=LABEL,is_group=True),expected=201)
        return dict(subject=_subject(value,LABEL,created_by=oem.user['userId']),httpStatus=201)
    subject=r['subject'];subject_id=object_id(subject['id'])
    require(len(candidates)==1 and candidates[0]['id']==subject_id,'SUBJECT_CHANGED')
    _subject(oem.call('subjects/'+subject_id+'/'),LABEL,subject_id,subject['createdBy'])
    members=_pages(oem,'subjects/'+subject_id+'/units/',lambda row:object_id(row['id']))
    current=r['vehicles']['test']
    require(all(row['id']==current['unitId'] and row['system_uid']==current['systemUid'] for row in members),'FOREIGN_SUBJECT_UNIT')
    services=_pages(oem,'subjects/'+subject_id+'/services/',lambda row:object_id(row['service']['id']))
    require(all(row['service']['id']==service_id for row in services),'FOREIGN_SUBJECT_SERVICE')
    if action=='subject-status':
        from aosedge_demo_orchestrator.cloud_observation import service
        rows=_pages(oem,'units/'+current['unitId']+'/subjects-services/',
                    lambda row:(str(row.get('subject')),row['service']['id']))
        return dict(unitBound=bool(members),serviceBound=bool(services),
                    runtime=[service(row) for row in rows if row['service']['id']==service_id])
    require(action in ('subject-bind','subject-assign'),'ACTION_INVALID')
    bind=action=='subject-bind'
    require(not (members if bind else services),'ASSIGNMENT_EXISTS_RECONCILE')
    require(bind or bool(members),'BIND_FIRST')
    oem.require('subjects_units_create' if bind else 'subjects_services_create')
    key='system_uids' if bind else 'service_ids';value=current['systemUid'] if bind else service_id
    response=oem.call('subjects/'+subject_id+('/units/' if bind else '/services/'),'POST',{key:[value]},expected=201)
    require(response['subject_id']==subject_id and response[key]==[value],'ASSIGNMENT_RESPONSE_UNCERTAIN')
    return dict(httpStatus=201,accepted=True)


def main():
    try:
        tooling=Path(sys.argv[1]);require(tooling.is_absolute() and tooling.is_dir(),'TOOLING_REQUIRED')
        sys.path.insert(0,str(tooling))
        request=json.loads(sys.stdin.read(65537))
        with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
            data=execute(request)
        result=dict(ok=True,data=data)
    except Exception as error:
        value=str(error)
        import re
        result=dict(ok=False,reason=value if re.fullmatch(r'(VISION_PROBE_|VISION_CAMERA_|CLOUD_|OEM_|SP_)[A-Z0-9_:,.-]{1,160}',value) else type(error).__name__)
    print(json.dumps(result),flush=True)


if __name__=='__main__':main()
