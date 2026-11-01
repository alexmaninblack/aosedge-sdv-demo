#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Exact two-service Vision Cloud worker; every mutation needs recorded intent.

No Main service APIs, OEM firmware operation, retry, arbitrary role, Unit or
version is accepted. Account credentials stay in the SDK worker's memory.
"""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import re
import runpy
import sys

UNIT='af6d074a-6ce1-49ba-b613-0476e7b6d1b5'
NODE='84a5e7db-f694-4124-a024-0f6ee1f35bf3'
HARDWARE='89273f164be04b22b4cb58d08533c8bc'
SET='09068ddf-7bb3-4454-bbe7-e24274d30dac'
LABEL='SDV Vision Pilot'
ROLES=('perception','assessment')


def require(ok,code):
    if not ok:raise ValueError('VISION_SERVICES_'+code)


def scope(cloud,r):
    v=r['vehicle'];require(r['cloudDomain']=='aoscloud.io' and v['unitId']==UNIT and v['nodeId']==NODE
        and v['unitSetId']==SET and v['nodeHardwareId']==HARDWARE,'TARGET_CHANGED')
    cloud.require('units_read','units_nodes_list','unit_sets_units_list')
    unit=cloud.unit(UNIT,nodes=False)
    require(unit and unit['id']==UNIT and unit['system_uid']==v['systemUid'] and unit['status']=='provisioned'
        and unit['online_status']=='Online' and unit['unit_sets']==[SET],'UNIT_BINDING_CHANGED')
    nodes=cloud.pages('units/'+UNIT+'/nodes/')
    require(len(nodes)==1 and nodes[0]['id']==NODE and nodes[0]['node_id']==HARDWARE
        and nodes[0]['node_type']=='aos-vision-vm-main' and nodes[0].get('is_main') in (None,True),'NODE_BINDING_CHANGED')
    selected=cloud.call('unit-sets/'+SET+'/');members=cloud.pages('unit-sets/'+SET+'/units/')
    require(selected['id']==SET and selected['is_validation_set'] is True and selected['fleet']==unit['fleet']
        and selected.get('allow_unknown_components') is False and len(members)==1
        and members[0]['id']==UNIT and members[0]['system_uid']==v['systemUid'],'VERIFICATION_SCOPE_CHANGED')


def execute(r):
    from aosedge_demo_orchestrator.unit_cloud import Cloud
    from aosedge_demo_orchestrator.service_cloud import service_view,version_view,unit_view
    from aosedge_demo_orchestrator.component_publication import Reads,bundle_view
    from aosedge_demo_orchestrator.service_assignment import _subject
    from aosedge_demo_orchestrator.status import object_id
    action=r['action'];role=r.get('role')
    require(action in ('preflight','catalog','upload','publication','subject-create','subject-status','subject-bind','subject-assign'),'ACTION_DENIED')
    require(role in ROLES or (role is None and action in ('preflight','subject-create','subject-status','subject-bind')),'ROLE_DENIED')
    oem=Cloud(dict(credential=r['oemCredential'],cloudDomain=r['cloudDomain'],ownerId=r['oemOwner']));scope(oem,r)
    provider=Cloud(dict(credential=r['spCredential'],cloudDomain=r['cloudDomain'],ownerId=r['spOwner']),expected_role='service provider')
    provider.require('services_list','services_read','services_service_versions_list','services_units_list','deployment_bundles_list')
    catalog=provider.pages('services/');services={};versions={}
    for name in ROLES:
        candidates=[row for row in catalog if row.get('codename')=='vision-'+name]
        require(len(candidates)<=1 and not any(row.get('title')=='Vision '+name.title() and row.get('codename')!='vision-'+name for row in catalog),'SERVICE_IDENTITY_CONFLICT')
        current=service_view(candidates[0],provider.user) if candidates else None
        require(current is None or current['title']=='Vision '+name.title(),'SERVICE_TITLE_CHANGED');services[name]=current
        rows=[version_view(row) for row in provider.pages('services/'+current['id']+'/service-versions/')] if current else []
        require(len(rows)<=1 and all(row['version']=='0.1.0' for row in rows),'UNEXPECTED_VERSION_RECONCILE');versions[name]=rows
        if current:
            recipients=[unit_view(row) for row in provider.pages('services/'+current['id']+'/units/')]
            require(all(row['id']==UNIT and row['system_uid']==r['vehicle']['systemUid'] for row in recipients),'FOREIGN_SERVICE_RECIPIENT')
    subjects=[row for row in oem.pages('subjects/') if row.get('label')==LABEL]
    require(len(subjects)<=1,'SUBJECT_LABEL_COLLISION')
    if action=='preflight':
        provider.require('deployment_bundles_create')
        oem.require('subjects_list','subjects_read','subjects_create','subjects_units_create','subjects_units_list','subjects_services_list','subjects_services_create','units_subjects_services_list')
        for name in ROLES:
            if services[name] is None:provider.require('services_create')
        return dict(ready=True,services={name:dict(serviceId=services[name]['id'] if services[name] else None,versions=versions[name]) for name in ROLES},subjectCandidates=[object_id(row['id']) for row in subjects])
    if action=='catalog':return dict(serviceId=services[role]['id'] if services[role] else None,versions=versions[role])
    if action=='upload':
        require(not versions[role],'VERSION_EXISTS_RECONCILE')
        package=Path(r['packageModule']);prepared_path=Path(r['prepared'])
        require(not package.is_symlink() and hashlib.sha256(package.read_bytes()).hexdigest()==r['packageModuleSha256']
            and not prepared_path.is_symlink() and hashlib.sha256(prepared_path.read_bytes()).hexdigest()==r['preparedSha256'],'PACKAGE_VERIFIER_CHANGED')
        module=runpy.run_path(str(package));prepared=json.loads(prepared_path.read_bytes())
        require(prepared['role']==role and prepared['version']=='0.1.0','PREPARED_IDENTITY_CHANGED')
        signed=module['verify_signed'](Path(r['bundle']),Path(r['spCredential']),role,prepared,r['expectedSha256'])
        from aosedge_demo_orchestrator.component_cloud import upload_bundle
        return dict(upload_bundle(provider,Path(r['bundle']),prefix='VISION_SERVICES'),signedSha256=signed['sha256'])
    if action=='publication':
        rows=Reads(provider).pages('deployment-bundles/',object_id(r['deploymentId']));require(len(rows)==1,'DEPLOYMENT_NOT_OBSERVED')
        bundle=bundle_view(rows[0]);state=str(bundle['state']).lower()
        require(state!='error','DEPLOYMENT_BUILD_FAILED')
        if state!='done' or not versions[role]:return dict(stage='PROCESSING',serviceId=services[role]['id'] if services[role] else None)
        require(len(bundle['items'])==1 and bundle['items'][0]['type']=='service'
            and bundle['items'][0]['codename']=='vision-'+role and bundle['items'][0]['version']=='0.1.0','DEPLOYMENT_ITEMS_CHANGED')
        version=versions[role][0]
        return dict(stage='READY' if str(version['container_state']).lower()=='ready' else 'PROCESSING',serviceId=services[role]['id'],versionId=version['id'],version='0.1.0')
    require(all(services[name] and len(versions[name])==1 and str(versions[name][0]['container_state']).lower()=='ready' for name in ROLES),'BOTH_READY_SERVICES_REQUIRED')
    planned={services[name]['id'] for name in ROLES}
    require(r.get('serviceIds')=={name:services[name]['id'] for name in ROLES},'PUBLISHED_SERVICE_BINDING_CHANGED')
    if action=='subject-create':
        require(not subjects,'SUBJECT_EXISTS_RECONCILE');oem.require('subjects_create')
        value=oem.call('subjects/','POST',dict(label=LABEL,is_group=True),expected=201)
        return dict(subject=_subject(value,LABEL,created_by=oem.user['userId']),httpStatus=201)
    subject=r['subject'];sid=object_id(subject['id']);require(len(subjects)==1 and subjects[0]['id']==sid,'SUBJECT_ID_CHANGED')
    _subject(oem.call('subjects/'+sid+'/'),LABEL,sid,subject['createdBy'])
    members=oem.pages('subjects/'+sid+'/units/');assigned=oem.pages('subjects/'+sid+'/services/')
    require(all(row['id']==UNIT and row['system_uid']==r['vehicle']['systemUid'] for row in members),'FOREIGN_SUBJECT_UNIT')
    require(all(row['service']['id'] in planned for row in assigned),'FOREIGN_SUBJECT_SERVICE')
    present={row['service']['id'] for row in assigned}
    if action=='subject-status':
        from aosedge_demo_orchestrator.cloud_observation import service
        runtime=[service(row) for row in oem.pages('units/'+UNIT+'/subjects-services/') if row['service']['id'] in planned]
        return dict(unitBound=bool(members),assignedRoles=[name for name in ROLES if services[name]['id'] in present],runtime=runtime)
    if action=='subject-bind':
        require(not members and not assigned,'SUBJECT_MEMBERSHIP_EXISTS_RECONCILE');oem.require('subjects_units_create')
        key='system_uids';value=r['vehicle']['systemUid'];endpoint='units/'
    else:
        require(members and services[role]['id'] not in present,'SUBJECT_ASSIGNMENT_EXISTS_RECONCILE');oem.require('subjects_services_create')
        key='service_ids';value=services[role]['id'];endpoint='services/'
    response=oem.call('subjects/'+sid+'/'+endpoint,'POST',{key:[value]},expected=201)
    require(response['subject_id']==sid and response[key]==[value],'SUBJECT_WRITE_RESPONSE_UNCERTAIN')
    return dict(httpStatus=201,accepted=True)


def main():
    try:
        tooling=Path(sys.argv[1]);require(tooling.is_absolute() and tooling.is_dir(),'TOOLING_REQUIRED');sys.path.insert(0,str(tooling))
        request=json.loads(sys.stdin.read(65537))
        with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):data=execute(request)
        result=dict(ok=True,data=data)
    except Exception as error:
        value=str(error);result=dict(ok=False,reason=value if re.fullmatch(r'(VISION_SERVICES_|CLOUD_|OEM_|SP_)[A-Z0-9_:,.-]{1,160}',value) else type(error).__name__)
    print(json.dumps(result),flush=True);return 0


if __name__=='__main__':raise SystemExit(main())
