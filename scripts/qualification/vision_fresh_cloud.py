#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""OEM pre-provision publication only when every verification cohort is empty."""
import contextlib
import io
import json
from pathlib import Path
import re
import sys

OLD='4374bcb2-0613-419c-8ac9-e8458358c91c'
SET='09068ddf-7bb3-4454-bbe7-e24274d30dac'
ROOTFS='aos-vision-vm-1.0.0-main-qemuarm64-rootfs'
VERSION='6.1.1-vision-camera.5'


def require(ok,code):
    if not ok:raise ValueError('VISION_FRESH_'+code)


def empty(cloud):
    from aosedge_demo_orchestrator.component_publication import Reads,recipients
    cloud.require('units_read','unit_sets_list','unit_sets_units_list','components_list',
        'components_versions_list','deployment_bundles_list','deployment_bundles_create')
    require(cloud.unit(OLD,nodes=False) is None,'OLD_UNIT_MUST_BE_ABSENT')
    selected=cloud.call('unit-sets/'+SET+'/')
    require(selected.get('title')=='SDV Vision Camera Image Verification'
        and selected.get('is_validation_set') is True and selected.get('allow_unknown_components') is False,'SELECTED_SET_CHANGED')
    coverage=recipients(Reads(cloud),{})
    batch=cloud.call('verification-batch/96a16904-0cfa-484c-ac70-0601ff90048d/')
    entries=batch.get('update_items') or []
    require(batch.get('oem_id')==cloud.user['ownerId'] and batch.get('architectures')==['arm64']
        and batch.get('state')=='Invalid' and (batch.get('approval_states') or {}).get('arm64',{}).get('is_approved') is False
        and len(entries)==1 and entries[0].get('codename')==ROOTFS
        and entries[0].get('version')=='6.1.1-vision-camera.4','FAILED_BATCH_NOT_REJECTED')
    return dict(ready=True,oldUnitAbsent=True,allVerificationMembersAbsent=True,recipientCoverage=coverage,
        selectedSetId=SET,failedFourthCandidateRejected=True)


def execute(r):
    from aosedge_demo_orchestrator.unit_cloud import Cloud
    from aosedge_demo_orchestrator.component_cloud import resolve_component,upload_bundle
    from aosedge_demo_orchestrator.component_publication import Reads,publication,bundle_view
    oem=Cloud(dict(credential=r['credential'],cloudDomain=r['cloudDomain'],ownerId=r['ownerId']))
    gate=empty(oem);component=resolve_component(oem,component_type=ROOTFS);require(component is not None,'COMPONENT_MISSING')
    reads=Reads(oem);versions=reads.pages('components/'+component['id']+'/versions/')
    selected=[v for v in versions if v.get('version')==VERSION]
    bundles=reads.pages('deployment-bundles/',r['deploymentId']) if r.get('deploymentId') else [
        v for v in reads.pages('deployment-bundles/') if any(i.get('codename')==ROOTFS and i.get('version')==VERSION for i in v.get('items') or [])]
    observed=publication(VERSION,r.get('deploymentId'),[bundle_view(v) for v in bundles],selected,component_type=ROOTFS)
    if r['action']=='gate':
        require(not selected and not bundles,'FIFTH_CANDIDATE_EXISTS_RECONCILE')
        provider=Cloud(dict(credential=r['spCredential'],cloudDomain=r['cloudDomain'],ownerId=r['spOwner']),expected_role='service provider')
        provider.require('services_list','services_read','services_service_versions_list','services_units_list','deployment_bundles_create')
        return dict(gate,publication=observed,componentTitle=component.get('title'),spAuthorityReady=True)
    if r['action']=='status':return dict(gate,publication=observed,componentTitle=component.get('title'))
    require(r['action'] in ('sign','upload') and not selected and not bundles,'EXACT_UNPUBLISHED_ACTION_REQUIRED')
    require(r['componentTitle']==component.get('title'),'COMPONENT_TITLE_CHANGED')
    # Verified qualification helper, not an alternate product trust owner.
    helper=Path(r['helperDirectory']);sys.path.insert(0,str(helper))
    from vision_permanent_component_cloud import configuration,verify,sha
    payload=Path(r['payload']);require(payload.is_file() and not payload.is_symlink()
        and payload.stat().st_size==r['payloadBytes'] and sha(payload)==r['payloadSha256'],'PAYLOAD_CHANGED')
    if r['action']=='upload':
        path=Path(r['bundle']);verify(path,Path(r['credential']),ROOTFS,r['payloadSha256'],r['payloadBytes'],r['expectedSha256'],title=r['componentTitle'])
        return upload_bundle(oem,path,prefix='VISION_FRESH')
    import os,shutil,tempfile
    from aos_signer.upload_config_v2.batch_configuration import UpdateBundleConfiguration
    from aos_signer.signer.signer import Signer
    from aosedge_demo_orchestrator.component_worker import credential_snapshot
    output=Path(r['output']);require(not output.exists(),'SIGNED_OUTPUT_EXISTS')
    with tempfile.TemporaryDirectory(prefix='.vision-fresh-sign-',dir=output.parent) as directory:
        stage=Path(directory);target=stage/'rootfs/image.squashfs';target.parent.mkdir();shutil.copyfile(payload,target)
        config=stage/'config.yaml';config.write_text(json.dumps(configuration(ROOTFS,r['componentTitle'])));before=Path.cwd()
        try:
            os.chdir(stage)
            with credential_snapshot(dict(credential=r['credential'])) as private:
                Signer(UpdateBundleConfiguration(config),config,pkcs12_path=private['credential']).process()
                result=verify(stage/'batch.tar.gz',Path(private['credential']),ROOTFS,r['payloadSha256'],r['payloadBytes'],title=r['componentTitle'])
        finally:os.chdir(before)
        shutil.copyfile(stage/'batch.tar.gz',output);output.chmod(0o444)
    return result


def main():
    try:
        sys.path.insert(0,sys.argv[1]);r=json.load(sys.stdin)
        with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):value=execute(r)
        result=dict(ok=True,data=value)
    except Exception as error:
        import traceback
        frame=traceback.extract_tb(error.__traceback__)[-1];value=str(error)
        result=dict(ok=False,reason=value if re.fullmatch('(VISION_|COMPONENT_|CLOUD_|OEM_|SP_)[A-Z0-9_:,.-]{1,160}',value) else type(error).__name__,
            failureFile=Path(frame.filename).name,failureLine=frame.lineno)
    print(json.dumps(result),flush=True)


if __name__=='__main__':main()
