#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Read-only account-level gate for the accepted permanent Vision packet."""
import contextlib
import io
import json
from pathlib import Path
import re
import sys

ROOTFS = 'aos-vision-vm-1.0.0-main-qemuarm64-rootfs'
CAMERA = 'aos-vision-vm-1.0.0-main-qemuarm64-camera-access'
VERSIONS = {ROOTFS: '6.1.1-vision-camera.5', CAMERA: '0.1.1'}
FAILED_BATCH='96a16904-0cfa-484c-ac70-0601ff90048d'
FAILED_COMPONENT='40ed2e6e-2aee-45f5-af80-3ab6928771ff'
CURRENT_UNIT='4374bcb2-0613-419c-8ac9-e8458358c91c'
RETIRED_VERIFICATION = {
    '55e87ad2-9c8c-4e0f-ad3c-02bbd362acd9': (
        'SDV Vision Camera Verification', '5abf6a2b-ae53-4995-a58a-91d9253057f7'),
    '581d4776-9679-4c48-8021-194539f2a5d3': (
        'SDV Vision Verification', '2ac4b71a-2d06-4dd5-904f-7d2c24109f39')}


def reject_failed_rootfs(cloud, request):
    """One accepted rejection; no deletion, membership change or upload retry."""
    import os
    from aosedge_demo_orchestrator.unit_cloud import CloudFailure
    if request.get('rejectFailedRootfs')!=dict(authorized=True,batchId=FAILED_BATCH,
        failedVersion='6.1.1-vision-camera.4',successorVersion=VERSIONS[ROOTFS]):
        raise CloudFailure('VISION_ROOTFS_REJECTION_AUTHORITY_REQUIRED')
    if request['vehicles']['test']['unitId']!=CURRENT_UNIT:
        raise CloudFailure('VISION_ROOTFS_REJECTION_UNIT_CHANGED')
    cloud.require('verification_batch_approval')
    records=Path(request['operationDirectory'])
    if not records.is_absolute() or not records.is_dir() or records.is_symlink():
        raise CloudFailure('VISION_ROOTFS_REJECTION_RECORDS_INVALID')
    path='verification-batch/'+FAILED_BATCH+'/'
    def observe():
        value=cloud.call(path);entries=value.get('update_items') or []
        if (value.get('id')!=FAILED_BATCH or value.get('oem_id')!=cloud.user['ownerId']
            or value.get('architectures')!=['arm64'] or len(entries)!=1
            or entries[0].get('identity_id')!=FAILED_COMPONENT
            or entries[0].get('codename')!=ROOTFS or entries[0].get('version')!='6.1.1-vision-camera.4'):
            raise CloudFailure('VISION_ROOTFS_REJECTION_BATCH_CHANGED')
        return {k:value.get(k) for k in ('id','state','architectures','approval_states')}
    def record(name,value):
        fd=os.open(records/name,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
        with os.fdopen(fd,'w') as stream:
            json.dump(value,stream,indent=2);stream.flush();os.fsync(stream.fileno())
    before=observe();intent=records/'failed-rootfs-rejection-intent.json'
    body=[dict(architecture='arm64',is_approved=False)]
    if intent.exists():
        expected=dict(batchId=FAILED_BATCH,unitId=CURRENT_UNIT,body=body,attemptStarted=True)
        if json.loads(intent.read_bytes())!=expected:
            raise CloudFailure('VISION_ROOTFS_REJECTION_INTENT_CHANGED')
        if (before.get('approval_states') or {}).get('arm64',{}).get('is_approved') is not False:
            raise CloudFailure('VISION_ROOTFS_REJECTION_UNCERTAIN_NO_REPLAY')
        return dict(confirmed=True,replayed=False,resumed=True,batch=before)
    record('failed-rootfs-rejection-before.json',before)
    record(intent.name,dict(batchId=FAILED_BATCH,unitId=CURRENT_UNIT,body=body,attemptStarted=True))
    uncertain=False
    try:cloud.call(path,'PATCH',body)
    except Exception:uncertain=True
    after=observe()
    confirmed=(after.get('approval_states') or {}).get('arm64',{}).get('is_approved') is False
    record('failed-rootfs-rejection-response.json',dict(confirmed=confirmed,responseUncertain=uncertain,batch=after))
    if not confirmed:raise CloudFailure('VISION_ROOTFS_REJECTION_UNCONFIRMED_NO_REPLAY')
    return dict(confirmed=True,replayed=False,resumed=False,batch=after)


def retire_verification(cloud, request):
    """Exact authorized flag-only migration; no Unit/member/Subject write API."""
    import os
    from aosedge_demo_orchestrator.unit_cloud import CloudFailure
    if request.get('retireVerification') != dict(authorized=True, flagOnly=True,
                                               setIds=list(RETIRED_VERIFICATION)):
        raise CloudFailure('VISION_VERIFICATION_AUTHORITY_REQUIRED')
    # Live permission projection uses the plural collection name. The public
    # schema's operationId currently uses the inconsistent singular spelling.
    cloud.require('unit_sets_partial_update', 'unit_sets_read', 'unit_sets_units_list')
    records = Path(request['operationDirectory'])
    if not records.is_absolute() or not records.is_dir() or records.is_symlink():
        raise CloudFailure('VISION_VERIFICATION_RECORDS_INVALID')
    def record(name, value):
        path = records / name
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(fd, 'w') as stream:
            json.dump(value, stream, indent=2)
            stream.flush(); os.fsync(stream.fileno())
    resume=request.get('resumeRetirement')
    resume_id=None
    if resume:
        old=Path(resume['directory'])
        if (resume.get('attempt')!='ingress-verification-04' or old.name!=resume['attempt']
                or old.parent!=records.parent):
            raise CloudFailure('VISION_VERIFICATION_RESUME_SCOPE_INVALID')
        resume_id=next(iter(RETIRED_VERIFICATION))
        prior=json.loads((old/('verification-'+resume_id+'-intent.json')).read_bytes())
        if prior!=dict(setId=resume_id,body=dict(is_validation_set=False),
                       expectedMemberIds=[RETIRED_VERIFICATION[resume_id][1]],attemptStarted=True):
            raise CloudFailure('VISION_VERIFICATION_RESUME_INTENT_INVALID')
        if not (old/('verification-'+resume_id+'-unconfirmed.json')).is_file():
            raise CloudFailure('VISION_VERIFICATION_RESUME_RESULT_REQUIRED')
    before = {}
    for identity, (title, unit) in RETIRED_VERIFICATION.items():
        value = cloud.call('unit-sets/' + identity + '/')
        members = cloud.pages('unit-sets/' + identity + '/units/')
        if (value.get('id') != identity or value.get('title') != title
                or value.get('is_validation_set') is not (False if identity==resume_id else True)
                or len(members) != 1 or members[0].get('id') != unit):
            raise CloudFailure('VISION_VERIFICATION_SCOPE_CHANGED')
        before[identity] = (value, members)
    results = []
    for identity, (value, members) in before.items():
        if identity==resume_id:
            # Known exact intent has applied. Record the read reconciliation;
            # never issue a second PATCH to obtain a more convenient receipt.
            result=dict(setId=identity,flag=False,membersUnchanged=True,
                        previousAttemptReconciled=resume['attempt'],requestReplayed=False,
                        definitionPreimage='NOT_RETAINED_BY_PRIOR_OBSERVER')
            record('verification-'+identity+'-response.json',result);results.append(result)
            continue
        record('verification-'+identity+'-before.json',dict(definition=value,
               memberIds=[v['id'] for v in members]))
        intent = dict(setId=identity, body=dict(is_validation_set=False),
                      expectedMemberIds=[v['id'] for v in members], attemptStarted=True)
        record('verification-' + identity + '-intent.json', intent)
        # The intent exists before the only mutation. Never replay after a lost
        # response; subsequent actions are authoritative GETs only.
        uncertain = False
        try:
            cloud.call('unit-sets/' + identity + '/', 'PATCH', intent['body'])
        except Exception:
            uncertain = True
        after = cloud.call('unit-sets/' + identity + '/')
        after_members = cloud.pages('unit-sets/' + identity + '/units/')
        ignored = {'is_validation_set', 'updated_at'}
        # Unit detail projections embed the set's own flag. Its expected
        # reflection is not a membership change or an additional Unit write.
        import copy
        expected_members=copy.deepcopy(members)
        for member in expected_members:
            for bound in member.get('unit_sets') or []:
                if bound.get('id')==identity:bound['is_validation_set']=False
        if (after.get('is_validation_set') is not False
                or {k:v for k,v in after.items() if k not in ignored}
                != {k:v for k,v in value.items() if k not in ignored}
                or after_members != expected_members):
            record('verification-' + identity + '-unconfirmed.json',
                   dict(setId=identity, responseUncertain=uncertain, confirmed=False))
            raise CloudFailure('VISION_VERIFICATION_FLAG_CHANGE_UNCONFIRMED')
        result = dict(setId=identity, flag=False, membersUnchanged=True,
                      definitionOtherwiseUnchanged=True, responseReconciled=uncertain)
        record('verification-' + identity + '-response.json', result)
        results.append(result)
    return results


def inventory(cloud, request):
    from aosedge_demo_orchestrator.component_publication import Reads, recipients
    from aosedge_demo_orchestrator.component_cloud import resolve_component, unit_view
    from aosedge_demo_orchestrator.unit_cloud import CloudFailure
    from aosedge_demo_orchestrator.status import object_id
    cloud.require('components_list', 'components_versions_list', 'deployment_bundles_list',
                  'deployment_bundles_create', 'unit_sets_list', 'unit_sets_units_list',
                  'units_read', 'units_components_send_requests_list',
                  'units_components_send_requests_create')
    reads = Reads(cloud)
    target = request['vehicles']['test']
    sets = reads.pages('unit-sets/?is_validation_set=true')
    if len(sets) > 16 or any(v.get('is_validation_set') is not True for v in sets):
        raise CloudFailure('COMPONENT_VERIFICATION_SET_FILTER_NOT_PROVEN')
    memberships, member_rows = [], {}
    for row in sets:
        set_id = object_id(row['id'])
        members = reads.pages('unit-sets/' + set_id + '/units/')
        member_rows['unit-sets/' + set_id + '/units/'] = members
        memberships.append(dict(id=set_id, title=row.get('title'), members=[dict(
            id=object_id(v['id']), currentTarget=v['id'] == target['unitId']
            and v.get('system_uid') == target['systemUid']) for v in members]))
    # Reuse the product's exact recipient guard over the already observed data.
    # No permission is inferred from a separate directory, model or offline VM.
    class Observed:
        def pages(self, path):
            if path == 'unit-sets/?is_validation_set=true':
                return sets
            if path in member_rows:
                return member_rows[path]
            raise CloudFailure('COMPONENT_UNEXPECTED_RECIPIENT_READ')
    blockers = []
    try:
        coverage = recipients(Observed(), request)
    except CloudFailure as error:
        if str(error) != 'COMPONENT_UNRELATED_VERIFICATION_RECIPIENT':
            raise
        blockers.append(str(error))
        coverage = dict(complete=False)
    components = []
    for kind, version in VERSIONS.items():
        component = resolve_component(cloud, reads, component_type=kind)
        versions = reads.pages('components/' + component['id'] + '/versions/') if component else []
        selected = [v for v in versions if v.get('version') == version]
        if selected:
            blockers.append('VISION_TARGET_VERSION_EXISTS_RECONCILE')
        unit = unit_view(reads, target, strict=True, component_type=kind)
        if unit.get('components') is None or any(v.get('pending_component') for v in unit['components']):
            blockers.append('VISION_PENDING_COMPONENT_RECONCILE')
        components.append(dict(type=kind, candidateVersion=version,
            componentId=component['id'] if component else None,
            versions=[dict(id=object_id(v['id']), version=v.get('version'), state=v.get('state'),
                           isFake=v.get('is_fake')) for v in versions], unit=unit))
    sends = reads.call('units/' + object_id(target['unitId']) + '/components/send-requests/')
    if not isinstance(sends, list):
        raise CloudFailure('COMPONENT_SEND_REQUESTS_SCHEMA_INVALID')
    if any(v.get('component_type') in VERSIONS for v in sends):
        blockers.append('VISION_SEND_REQUEST_EXISTS_RECONCILE')
    bundles = reads.pages('deployment-bundles/')
    collisions = [dict(id=object_id(v['id']), state=v.get('state')) for v in bundles
        if any(i.get('codename') in VERSIONS and i.get('version') == VERSIONS[i['codename']]
               for i in v.get('items') or [])]
    if collisions:
        blockers.append('VISION_TARGET_BUNDLE_EXISTS_RECONCILE')
    return dict(ready=not blockers, blockers=sorted(set(blockers)), mutationAttempted=False,
        verificationSets=memberships, recipientCoverage=coverage, components=components,
        targetSendRequestCount=len(sends), candidateBundles=collisions)


def execute(request):
    from aosedge_demo_orchestrator.unit_cloud import Cloud
    from aosedge_demo_orchestrator.vision_camera_delivery import scope
    from aosedge_demo_orchestrator.vision_bootstrap import PROFILE
    cloud = Cloud(dict(credential=request['oemCredential'], cloudDomain=request['cloudDomain'],
                       ownerId=request['oemOwner']))
    if request.get('rejectFailedRootfs'):
        from aosedge_demo_orchestrator.vision_bootstrap import NODE_TYPE
        expected=request['vehicles']['test'];unit=cloud.unit(expected['unitId'],nodes=True)
        if not (unit is not None and unit['system_uid']==expected['systemUid'] and unit['status']=='provisioned'
            and unit['unit_sets']==[expected['unitSetId']] and len(unit['nodes'])==1
            and unit['nodes'][0]['id']==expected['nodeId'] and unit['nodes'][0]['node_type']==NODE_TYPE
            and unit['nodes'][0]['node_id']==expected['nodeHardwareId']):
            from aosedge_demo_orchestrator.unit_cloud import CloudFailure
            raise CloudFailure('VISION_ROOTFS_REJECTION_RETAINED_IDENTITY_CHANGED')
        return reject_failed_rootfs(cloud,request)
    scope(cloud, dict(request, version='0.1.0', setupProfile=PROFILE))
    changes = retire_verification(cloud, request) if request.get('retireVerification') else []
    result = inventory(cloud, request)
    result.update(mutationAttempted=bool(changes), verificationChanges=changes)
    return result


def main():
    try:
        tooling = Path(sys.argv[1])
        assert tooling.is_absolute() and tooling.is_dir()
        sys.path.insert(0, str(tooling))
        request = json.loads(sys.stdin.read(65537))
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            data = execute(request)
        result = dict(ok=True, data=data)
    except Exception as error:
        import traceback
        value = str(error)
        safe=re.fullmatch(r'(VISION_|COMPONENT_|CLOUD_|OEM_)[A-Z0-9_:,.-]{1,160}',value) or re.fullmatch(
            r'OEM_PERMISSION_MISSING:[a-z_,]{1,200}',value)
        result = dict(ok=False, reason=value if safe else type(error).__name__)
        location=traceback.extract_tb(error.__traceback__)[-1]
        result.update(failureFile=Path(location.filename).name,failureLine=location.lineno)
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
