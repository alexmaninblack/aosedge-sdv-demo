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
VERSIONS = {ROOTFS: '6.1.1-vision-camera.4', CAMERA: '0.1.1'}


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
    scope(cloud, dict(request, version='0.1.0', setupProfile=PROFILE))
    return inventory(cloud, request)


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
        value = str(error)
        result = dict(ok=False, reason=value if re.fullmatch(
            r'(VISION_|COMPONENT_|CLOUD_|OEM_)[A-Z0-9_:,.-]{1,160}', value) else type(error).__name__)
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
