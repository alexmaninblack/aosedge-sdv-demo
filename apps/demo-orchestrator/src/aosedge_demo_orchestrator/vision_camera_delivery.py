# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Fixed Vision Camera Test adapter over the existing signed bundle transport."""
import json
from pathlib import Path

from .vision_bootstrap import PROFILE, COMPONENT, SET_TITLE, NODE_TYPE
from .unit_cloud import CloudFailure
from .status import object_id
from .component_cloud import upload_bundle, unit_view
from .component_publication import snapshot

VERSION='0.1.0'


def package_configuration():
    return dict(schemaVersion=2,publisher=dict(author='maninblack'),items=[dict(
        identity=dict(type='component',codename=COMPONENT,title='Camera Access'),
        version=VERSION,sourceFolder='camera-access',
        configuration=dict(runtimes=[dict(codename=COMPONENT,type='runtime')]),
        images=[dict(path='payload.tar.gz',archInfo=dict(architecture='arm64'),osInfo=dict(os='linux'),
                     mediaType='application/vnd.aos.image.component.full.v1+gzip')])])


def require(ok, code):
    if not ok:
        raise CloudFailure('VISION_CAMERA_'+code)


def scope(cloud, request):
    require(request.get('setupProfile') == PROFILE and request.get('version') == VERSION, 'PROFILE_REQUIRED')
    require(set(request.get('vehicles',{})) == {'test'}, 'TEST_ONLY')
    vehicle=request['vehicles']['test']
    cloud.require('units_read','units_nodes_list','unit_sets_units_list')
    unit=cloud.unit(object_id(vehicle['unitId']),nodes=True)
    require(unit is not None and unit['system_uid']==vehicle['systemUid']
            and unit['status']=='provisioned' and unit['online_status']=='Online'
            and unit['unit_sets']==[object_id(vehicle['unitSetId'])], 'UNIT_BINDING_CHANGED')
    require(len(unit['nodes'])==1 and unit['nodes'][0]['id']==vehicle['nodeId']
            and unit['nodes'][0]['node_type']==NODE_TYPE and unit['nodes'][0]['node_id']==vehicle['nodeHardwareId']
            and unit['nodes'][0].get('is_main') in (None,True),'NODE_BINDING_CHANGED')
    selected=cloud.call('unit-sets/'+object_id(vehicle['unitSetId'])+'/')
    require(selected.get('title')==SET_TITLE and selected.get('is_validation_set') is True
            and selected.get('allow_unknown_components') is False and selected.get('fleet')==unit['fleet'],'SET_BINDING_CHANGED')
    members=cloud.pages('unit-sets/'+vehicle['unitSetId']+'/units/')
    require(len(members)==1 and members[0]['id']==vehicle['unitId']
            and members[0]['system_uid']==vehicle['systemUid'],'FOREIGN_RECIPIENT')
    return vehicle


def execute(cloud, request):
    vehicle=scope(cloud,request)
    action=request['action']
    if action=='vision-camera-status':
        return snapshot(cloud,request,component_type=COMPONENT)
    if action=='vision-camera-upload':
        from .component_worker import verify
        from .components import archive_files,sha
        path=Path(request['bundle'])
        require(path.is_file() and not path.is_symlink() and path.stat().st_size<8*1024**2,'BUNDLE_UNSAFE')
        verify(path,Path(request['credential']),request['expectedSha256'])
        outer=archive_files(path.read_bytes())
        inner=archive_files(outer['batch.tar.gz'])
        config=json.loads(inner['config.yaml']);items=config.get('items')
        require(config.get('schemaVersion')==2 and isinstance(items,list) and len(items)==1,'ENVELOPE_INVALID')
        item=items[0]
        require(config==package_configuration(),'PACKAGE_BINDING_CHANGED')
        require(set(inner)=={'config.yaml','camera-access/payload.tar.gz'}
                and sha(inner['camera-access/payload.tar.gz'])==request['payloadSha256'],'PAYLOAD_CHANGED')
        payload=archive_files(inner['camera-access/payload.tar.gz'])
        metadata=json.loads(payload['component.json'])
        require(metadata.get('component')=='camera-access' and metadata.get('version')==VERSION
                and set(payload)=={'component.json','bin/camera-access','config/camera.json'},'CAMERA_PAYLOAD_INVALID')
        before=snapshot(cloud,dict(request,purpose='upload'),component_type=COMPONENT)
        require(before['publication']['stage']=='NOT_PUBLISHED' and not before['versions']
                and not before['deploymentBundles'],'ALREADY_PUBLISHED_RECONCILE')
        return upload_bundle(cloud,path,prefix='VISION_CAMERA')
    require(action=='vision-camera-send','ACTION_INVALID')
    cloud.require('units_components_send_requests_create','units_components_send_requests_list')
    observed=snapshot(cloud,request,component_type=COMPONENT)
    publication=observed['publication']
    require(publication['stage']=='READY' and publication['versionId']==request['updateComponentId'],'PUBLICATION_NOT_READY')
    current=unit_view(cloud,vehicle,strict=True,component_type=COMPONENT)
    version_id=object_id(request['updateComponentId'])
    existing=cloud.call('units/'+vehicle['unitId']+'/components/send-requests/')
    observed=next((k for v in current['components'] or [] for k in ('installed_component','pending_component')
                   if (v.get(k) or {}).get('id')==version_id),None)
    queued=[v for v in existing if v.get('component_type')==COMPONENT]
    require(not queued or all(v.get('update_component')==version_id for v in queued),'SEND_EXISTS_RECONCILE')
    if observed or queued:
        # Verification sets can enqueue the exact uploaded candidate themselves.
        # This is authoritative observation, not a second send or installation
        # success. Native commit/health still have their independent gate.
        return dict(noOp=True,requestAccepted=False,unitId=vehicle['unitId'],updateComponentId=version_id,
                    deliveryObserved=observed or 'REQUEST_LISTED',origin='EXISTING_VERIFICATION_DELIVERY')
    response=cloud.call('units/'+vehicle['unitId']+'/components/send-requests/','POST',
                        {'update_component_ids':[version_id]},expected=201)
    require(isinstance(response,list) and len(response)==1 and response[0].get('component_type')==COMPONENT
            and response[0].get('update_component')==version_id,'SEND_RESPONSE_UNCERTAIN')
    return dict(requestId=object_id(response[0]['id']),requestAccepted=True,httpStatus=201)
