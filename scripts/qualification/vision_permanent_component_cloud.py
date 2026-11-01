#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Exact Vision rootfs.4 / Camera.1 OEM delivery through the official transport."""
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path,PurePosixPath
import re
import shutil
import sys
import tarfile
import tempfile

ROOTFS='aos-vision-vm-1.0.0-main-qemuarm64-rootfs'
CAMERA='aos-vision-vm-1.0.0-main-qemuarm64-camera-access'
VERSIONS={ROOTFS:'6.1.1-vision-camera.5',CAMERA:'0.1.1'}
LIMIT=8*1024**3


def require(ok,code):
    if not ok:raise ValueError('VISION_PERMANENT_'+code)


def configuration(kind, title='DEFAULT'):
    require(kind in VERSIONS,'COMPONENT_INVALID')
    root=kind==ROOTFS
    return dict(schemaVersion=2,publisher=dict(author='maninblack'),items=[dict(
        identity=dict(type='component',codename=kind,title=('Vision Rootfs' if root else 'Camera Access') if title=='DEFAULT' else title),
        version=VERSIONS[kind],sourceFolder='rootfs' if root else 'camera-access',
        configuration=dict(runtimes=[dict(codename=kind,type='runtime')]),
        images=[dict(path='image.squashfs' if root else 'payload.tar.gz',archInfo=dict(architecture='arm64'),
                     osInfo=dict(os='linux'),mediaType='application/vnd.aos.image.component.full.v1+'+('squashfs' if root else 'gzip'))])])


def sha(path):
    value=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(4*1024**2),b''):value.update(block)
    return value.hexdigest()


def entries(archive,allowed):
    names=set();total=0
    for member in archive:
        path=PurePosixPath(member.name);name=path.as_posix()
        require(not path.is_absolute() and '..' not in path.parts and '\\' not in name
                and len(name)<512 and not any(ord(c)<32 for c in name),'ARCHIVE_PATH_INVALID')
        if member.isdir():
            require(name=='.' or name in ('rootfs','camera-access'),'ARCHIVE_DIRECTORY_INVALID');continue
        require(member.isfile() and name in allowed and name not in names and 0<=member.size<=allowed[name],
                'ARCHIVE_ENTRY_INVALID')
        names.add(name);total+=member.size;require(total<=LIMIT+2**20,'ARCHIVE_EXPANSION_LIMIT')
        yield name,member.size,archive.extractfile(member)
    require(names==set(allowed),'ARCHIVE_CONTENTS_INVALID')


def verify(path,credential,kind,payload_sha,payload_bytes,expected=None,*,title='DEFAULT'):
    """Stream the large FOTA envelope; keep the Main 128-MiB parser unchanged."""
    import jwt
    from cryptography.hazmat.primitives.serialization.pkcs12 import load_key_and_certificates
    require(path.is_file() and not path.is_symlink() and 0<path.stat().st_size<=LIMIT,'BUNDLE_UNSAFE')
    outer_sha=sha(path);require(expected is None or outer_sha==expected,'SIGNED_DIGEST_CHANGED')
    config=configuration(kind,title);item=config['items'][0];payload_name=item['sourceFolder']+'/'+item['images'][0]['path']
    records=[];small={}
    with tempfile.TemporaryDirectory(prefix='.vision-verify-',dir=path.parent) as temporary:
        batch=Path(temporary)/'batch.tar.gz'
        with tarfile.open(path,mode='r|*') as archive:
            for name,size,stream in entries(archive,{'package.sign':65536,'config.yaml':1048576,'batch.tar.gz':LIMIT}):
                digest=hashlib.sha3_512();actual=0
                output=batch.open('xb') if name=='batch.tar.gz' else io.BytesIO()
                with output if name=='batch.tar.gz' else contextlib.nullcontext(output):
                    for block in iter(lambda:stream.read(4*1024**2),b''):
                        digest.update(block);actual+=len(block);require(actual<=size,'ARCHIVE_TRUNCATED');output.write(block)
                    require(actual==size,'ARCHIVE_TRUNCATED')
                    if name!='batch.tar.gz':small[name]=output.getvalue()
                if name!='package.sign':records.append(dict(name=name,size=size,hash=digest.hexdigest()))
        _,certificate,_=load_key_and_certificates(credential.read_bytes(),b'')
        claims=jwt.decode(small['package.sign'],certificate.public_key(),algorithms=['RS256'])
        require(claims.get('data')==sorted(records,key=lambda v:v['name']) or
                sorted(claims.get('data',[]),key=lambda v:v['name'])==sorted(records,key=lambda v:v['name']),'SIGNATURE_CONTENTS_INVALID')
        require(json.loads(small['config.yaml'])==config,'SIGNED_CONFIGURATION_CHANGED')
        with tarfile.open(batch,mode='r|*') as archive:
            for name,size,stream in entries(archive,{'config.yaml':1048576,payload_name:LIMIT}):
                if name=='config.yaml':require(stream.read()==small['config.yaml'],'INNER_CONFIGURATION_CHANGED');continue
                digest=hashlib.sha256();actual=0;magic=b''
                for block in iter(lambda:stream.read(4*1024**2),b''):
                    if not magic:magic=block[:4]
                    digest.update(block);actual+=len(block)
                require(actual==size==payload_bytes and digest.hexdigest()==payload_sha,'PAYLOAD_CHANGED')
                require(magic==b'hsqs' if kind==ROOTFS else magic[:2]==b'\x1f\x8b','PAYLOAD_FORMAT_INVALID')
    return dict(sha256=outer_sha,sizeBytes=path.stat().st_size,signatureVerification='VERIFIED_RS256',
                verificationTrust='CONFIGURED_OEM_SIGNING_CERTIFICATE',payloadSha256=payload_sha)


def execute(r):
    from aosedge_demo_orchestrator.unit_cloud import Cloud
    from aosedge_demo_orchestrator.vision_camera_delivery import scope
    from aosedge_demo_orchestrator.vision_bootstrap import PROFILE
    from aosedge_demo_orchestrator.component_publication import Reads,recipients,publication,bundle_view
    from aosedge_demo_orchestrator.component_cloud import resolve_component,unit_view,upload_bundle
    from aosedge_demo_orchestrator.component_worker import credential_snapshot
    kind=r['componentType'];require(kind in VERSIONS and r['version']==VERSIONS[kind],'EXACT_COMPONENT_VERSION_REQUIRED')
    require(r.get('permanentDelivery')==dict(authorized=True,recoveryFirst=True,rootfsVersion=VERSIONS[ROOTFS],
        cameraVersion=VERSIONS[CAMERA],readVersion='0.1.4',revokeVersion='0.1.5'),'PACKET_AUTHORITY_REQUIRED')
    cloud=Cloud(dict(credential=r['oemCredential'],cloudDomain=r['cloudDomain'],ownerId=r['oemOwner']))
    action=r['action']
    if action=='status':
        # Native rootfs trial/apply reboots legitimately make this exact Unit
        # offline. Read-only observation keeps the full identity binding;
        # every write still requires the ordinary Online scope below.
        from aosedge_demo_orchestrator.vision_bootstrap import NODE_TYPE
        expected=r['vehicles']['test'];unit=cloud.unit(expected['unitId'],nodes=True)
        require(unit is not None and unit['system_uid']==expected['systemUid'] and unit['status']=='provisioned'
            and unit['unit_sets']==[expected['unitSetId']] and len(unit['nodes'])==1
            and unit['nodes'][0]['id']==expected['nodeId'] and unit['nodes'][0]['node_type']==NODE_TYPE
            and unit['nodes'][0]['node_id']==expected['nodeHardwareId'],'RETAINED_UNIT_BINDING_CHANGED')
    else:scope(cloud,dict(r,version='0.1.0',setupProfile=PROFILE))
    if action=='sign':
        from aos_signer.upload_config_v2.batch_configuration import UpdateBundleConfiguration
        from aos_signer.signer.signer import Signer
        source=Path(r['payload']);output=Path(r['output'])
        require(source.is_file() and not source.is_symlink() and source.stat().st_size==r['payloadBytes']
            and sha(source)==r['payloadSha256'] and not output.exists(),'SIGN_INPUT_CHANGED')
        current=resolve_component(cloud,component_type=kind)
        require(current is not None and current.get('title')==r['componentTitle'],'COMPONENT_TITLE_CHANGED')
        config=configuration(kind,r['componentTitle']);item=config['items'][0]
        with tempfile.TemporaryDirectory(prefix='.vision-sign-',dir=output.parent) as temporary:
            stage=Path(temporary);target=stage/item['sourceFolder']/item['images'][0]['path'];target.parent.mkdir()
            shutil.copyfile(source,target);p=stage/'config.yaml';p.write_text(json.dumps(config));old=Path.cwd()
            try:
                os.chdir(stage)
                with credential_snapshot(dict(credential=r['oemCredential'])) as private:
                    Signer(UpdateBundleConfiguration(p),p,pkcs12_path=private['credential']).process()
                    value=verify(stage/'batch.tar.gz',Path(private['credential']),kind,r['payloadSha256'],r['payloadBytes'],title=r['componentTitle'])
            finally:os.chdir(old)
            shutil.copyfile(stage/'batch.tar.gz',output);output.chmod(0o444)
        return value
    reads=Reads(cloud);component=resolve_component(cloud,reads,component_type=kind)
    require(component is not None,'COMPONENT_IDENTITY_MISSING')
    versions=reads.pages('components/'+component['id']+'/versions/')
    selected=[v for v in versions if v.get('version')==r['version']]
    require(len(selected)<=1,'VERSION_AMBIGUOUS')
    bundle_id=r.get('deploymentId');bundles=reads.pages('deployment-bundles/',bundle_id)
    if not bundle_id:bundles=[v for v in bundles if any(i.get('codename')==kind and i.get('version')==r['version'] for i in v.get('items') or [])]
    observed=publication(r['version'],bundle_id,[bundle_view(v) for v in bundles],selected,component_type=kind)
    unit=unit_view(reads,r['vehicles']['test'],strict=True,component_type=kind)
    result=dict(publication=observed,unit=unit,componentId=component['id'],componentTitle=component.get('title'),versions=selected)
    if action=='status':return result
    require(component.get('title')==r['componentTitle'],'COMPONENT_TITLE_CHANGED')
    coverage=recipients(reads,r);require(coverage['complete'],'RECIPIENT_SCOPE_UNPROVEN')
    if action=='upload':
        require(observed['stage']=='NOT_PUBLISHED' and not selected and not bundles,'PUBLICATION_EXISTS_RECONCILE')
        require(unit['components'] is not None and not any(v.get('pending_component') for v in unit['components']),'PENDING_COMPONENT_RECONCILE')
        path=Path(r['bundle']);verify(path,Path(r['oemCredential']),kind,r['payloadSha256'],r['payloadBytes'],r['expectedSha256'],title=r['componentTitle'])
        return upload_bundle(cloud,path,prefix='VISION_PERMANENT')
    require(action=='send' and observed['stage']=='READY','PUBLICATION_NOT_READY')
    version_id=observed['versionId'];unit_id=r['vehicles']['test']['unitId']
    sends=reads.call('units/'+unit_id+'/components/send-requests/')
    require(isinstance(sends,list),'SEND_REQUESTS_INVALID')
    queued=[v for v in sends if v.get('component_type')==kind]
    require(not queued or all(v.get('update_component')==version_id for v in queued),'SEND_EXISTS_RECONCILE')
    delivery=next((key for row in unit['components'] or [] for key in ('installed_component','pending_component')
                   if (row.get(key) or {}).get('id')==version_id),None)
    if delivery or queued:return dict(noOp=True,deliveryObserved=delivery or 'REQUEST_LISTED',versionId=version_id)
    cloud.require('units_components_send_requests_create')
    value=cloud.call('units/'+unit_id+'/components/send-requests/','POST',dict(update_component_ids=[version_id]),expected=201)
    require(isinstance(value,list) and len(value)==1 and value[0].get('update_component')==version_id
        and value[0].get('component_type')==kind,'SEND_RESPONSE_UNCERTAIN')
    return dict(httpStatus=201,requestId=value[0]['id'],versionId=version_id)


def main():
    try:
        sys.path.insert(0,sys.argv[1]);request=json.loads(sys.stdin.read(65537))
        with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):value=execute(request)
        result=dict(ok=True,data=value)
    except Exception as error:
        import traceback
        value=str(error);location=traceback.extract_tb(error.__traceback__)[-1]
        result=dict(ok=False,reason=value if re.fullmatch(r'(VISION_|COMPONENT_|CLOUD_|OEM_)[A-Z0-9_:,.-]{1,160}',value) else type(error).__name__,
                    failureFile=Path(location.filename).name,failureLine=location.lineno)
    print(json.dumps(result),flush=True)


if __name__=='__main__':main()
