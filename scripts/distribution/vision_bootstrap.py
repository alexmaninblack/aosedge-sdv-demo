#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Assemble a separate signed Vision resource bundle; never modify Main inputs."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import plistlib
import re
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'apps/demo-orchestrator/src'))
from aosedge_demo_orchestrator import vision_bootstrap as model
from build_scratch import directory
from setup_signing import select


def digest(path):
    value=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(4*2**20),b''):value.update(chunk)
    return value.hexdigest()


def authorized_identity():
    """Resolve the existing owner's OU, not the unrelated CN display suffix."""
    import warnings
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes
    from cryptography.x509.oid import NameOID
    listing=subprocess.check_output(['/usr/bin/security','find-identity','-v','-p','codesigning'],text=True)
    valid=dict(re.findall(r'^\s*\d+\) ([0-9A-Fa-f]{40}) "([^"\r\n]+)"\s*$',listing,re.M))
    certificates=subprocess.check_output(['/usr/bin/security','find-certificate','-a','-p'])
    matches=set()
    for pem in re.findall(b'-----BEGIN CERTIFICATE-----.*?-----END CERTIFICATE-----',certificates,re.S):
        try:
            with warnings.catch_warnings():
                warnings.simplefilter('ignore');certificate=x509.load_pem_x509_certificate(pem)
        except ValueError:continue  # Unrelated system certificates cannot match.
        identity=certificate.fingerprint(hashes.SHA1()).hex().upper()
        owners=[v.value for v in certificate.subject.get_attributes_for_oid(NameOID.ORGANIZATIONAL_UNIT_NAME)]
        if owners==[model.TEAM] and valid.get(identity,'').startswith('Apple Development: '):matches.add(identity)
    model.require(len(matches)==1,'AUTHORIZED_SIGNING_OWNER_UNAVAILABLE')
    return next(iter(matches))  # Private internal selector; never report it.


def assemble(factory, camera_payload, base_manifest, platform_revision, identity, output,
             ingress_candidate=None, ingress_proof=None, update_platform_revision=None,
             services_candidate=None, services_proof=None):
    output=model.canonical(output)
    model.require(not output.exists() and output.suffix=='.bundle' and output.parent.is_dir(),'OUTPUT_EXISTS_OR_INVALID')
    model.require(output.parent.stat().st_dev==ROOT.stat().st_dev,'BUILD_REQUIRES_SELECTED_SSD')
    if identity=='authorized-vision-owner':
        identity=authorized_identity()
    identity=select(identity)
    # Source must be a committed, reproducible snapshot. Untracked retained
    # research files are not inputs and are deliberately not copied wholesale.
    model.require(not subprocess.check_output(['git','diff','HEAD','--name-only'],cwd=ROOT),'COMMITTED_SOURCE_REQUIRED')
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    record=json.loads(factory.read_bytes())
    model.require(set(record)>={'path','bytes','sha256','platformRevision','factoryVersion'},'FACTORY_RECEIPT_INVALID')
    image=model.canonical(Path(record['path']))
    model.require(record['factoryVersion']==model.VERSION and record['platformRevision']==platform_revision
                  and 0<record['bytes']<=model.MAX_IMAGE and image.stat().st_size==record['bytes'],'FACTORY_BINDING_INVALID')
    source_stamp=model.stamp(image)
    if record.get('verifiedStamp') is not None:
        model.require(tuple(record['verifiedStamp'])==source_stamp,'FACTORY_RECEIPT_IDENTITY_CHANGED')
    else:
        model.require(digest(image)==record['sha256'] and model.stamp(image)==source_stamp,'FACTORY_DIGEST_MISMATCH')
    model.require(model.SHA.fullmatch(base_manifest) and model.REV.fullmatch(platform_revision),'SOURCE_BINDING_INVALID')
    with directory(output.parent) as scratch:
        bundle=scratch/output.name;resources=bundle/'Contents/Resources';resources.mkdir(parents=True)
        contents=bundle/'Contents'
        model.require(services_candidate is None or ingress_candidate is None,'HOST_CANDIDATE_MODE_AMBIGUOUS')
        services=services_candidate is not None
        (contents/'Info.plist').write_bytes(plistlib.dumps(dict(CFBundleIdentifier=model.IDENTIFIER,
            CFBundleName='AosEdge Vision Bootstrap',CFBundlePackageType='BNDL',CFBundleVersion='0.6.0' if services else '0.5.0')))
        target=resources/'images/main-qemuarm64.img';target.parent.mkdir()
        # APFS clone when available; the independent file is still signature-sealed.
        result=subprocess.run(['/bin/cp','-c',str(image),str(target)],capture_output=True)
        if result.returncode:
            model.require(not target.exists(),'PARTIAL_IMAGE_COPY_RECONCILE_REQUIRED')
            shutil.copyfile(image,target)
        target.chmod(0o444)
        model.require(model.stamp(image)==source_stamp and target.stat().st_size==record['bytes'],'FACTORY_COPY_CHANGED')
        target=resources/'camera-access/payload.tar';target.parent.mkdir();shutil.copyfile(camera_payload,target);target.chmod(0o444)
        tracked=subprocess.check_output(['git','ls-files','apps/demo-orchestrator/src','contracts','config'],cwd=ROOT,text=True).splitlines()
        for name in tracked:
            source=ROOT/name
            if source.suffix not in ('.py','.json') or not source.is_file():continue
            destination=resources/'tooling/aosedge-sdv-demo'/name;destination.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(source,destination);destination.chmod(0o444)
        if ingress_candidate is not None or services:
            selected_proof=services_proof if services else ingress_proof
            model.require(selected_proof is not None and isinstance(update_platform_revision,str)
                          and model.REV.fullmatch(update_platform_revision),'HOST_PROOF_REQUIRED')
            candidate=model.canonical(services_candidate if services else ingress_candidate);proof=model.canonical(selected_proof)
            observed=json.loads((proof/'result.json').read_bytes());context=json.loads((proof/'context.json').read_bytes())
            manifest=json.loads((candidate/'manifest.json').read_bytes())
            if services:
                # An early sealed Source/Gateway is an input to the native
                # exchange proof, never a claim that the new image passed it.
                model.require(observed['outcome']=='PASS_VISION_SERVICES_HOST_SOURCE_PREREQUISITES'
                    and observed['nativeExchange']=='NOT_RUN' and observed['imageBuild']=='NOT_RUN'
                    and observed['gatewayUnitTestsPassed']==5 and observed['cpuProofRestored'] is True
                    and manifest['kind']=='VISION_SERVICES_HOST_ENGINEERING_INPUT'
                    and manifest['releaseImage'] is False and manifest['nativeQualified'] is False
                    and set(manifest['source'])=={'integration','platform','gateway','services'}
                    and manifest['source']['integration']==revision and manifest['source']['platform']==update_platform_revision
                    and all(model.REV.fullmatch(v) for v in manifest['source'].values())
                    and manifest['contractSha256']==digest(ROOT/'contracts/vision-vm/services.v1.json')
                    and manifest['allocationSha256']==digest(ROOT/'contracts/vision-vm/services-allocation.v1.json'),
                    'HOST_SERVICES_PREREQUISITES_MISMATCH')
            else:
                model.require(observed['outcome']=='PASS_TRANSIENT_NATIVE_STORE_INGRESS_POLICY'
                              and all(observed['cleanup'].values()),'HOST_NATIVE_PROOF_MISMATCH')
                model.require(manifest['nativePolicy'] is True and manifest['releaseImage'] is False,'HOST_CANDIDATE_INVALID')
            model.require(digest(candidate/'manifest.json')==context['candidateManifestSha256'],'HOST_CANDIDATE_PROOF_CHANGED')
            host=resources/model.HOST_PREFIX;host.mkdir(parents=True)
            selected=[name for name in manifest['files'] if name.startswith(('native/','tools/'))]
            for name in selected:
                path=candidate/name;row=manifest['files'][name]
                model.require(not path.is_symlink() and path.is_file() and path.stat().st_size==row['bytes']
                              and digest(path)==row['sha256'],'HOST_INPUT_CHANGED')
                destination=host/name;destination.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(path,destination);destination.chmod(0o644 if name.startswith('tools/') else 0o755)
            for name in ('native/lib/libcrypto.3.dylib','native/lib/libssl.3.dylib','native/carla-ego-runtime'):
                path=host/name
                dependencies=subprocess.check_output(['/usr/bin/otool','-L',str(path)],text=True)
                model.require('/opt/homebrew/' not in dependencies,'HOST_NOT_PORTABLE')
                done=subprocess.run(['/usr/bin/codesign','--force','--sign',identity,'--timestamp=none',str(path)],capture_output=True,timeout=120)
                model.require(done.returncode==0,'HOST_NATIVE_SIGNING_FAILED')
                done=subprocess.run(['/usr/bin/codesign','--verify','--strict','-R',
                    '=anchor apple generic and certificate leaf[subject.OU] = "'+model.TEAM+'"',str(path)],capture_output=True,timeout=20)
                model.require(done.returncode==0,'HOST_NATIVE_SIGNATURE_INVALID')
                path.chmod(0o555)
            descriptor=dict(schemaVersion=1,kind='signed-vision-services-host' if services else 'signed-vision-ingress-host',profile=model.PROFILE,
                baseProgramManifestSha256=base_manifest,rootfsVersion='6.1.1-vision-camera.6' if services else '6.1.1-vision-camera.5',cameraVersion='0.1.2' if services else '0.1.1',
                sources=dict(integration=revision,platform=update_platform_revision,gateway=manifest['source']['gateway']),
                assets=dict(runtime=model.HOST_RUNTIME,runner=model.HOST_RUNNER))
            if services:
                descriptor['sources']['services']=manifest['source']['services']
                descriptor['exchangeScopes']=['vision-context-read','vision-assessment-publish']
            (host/'host-runtime.json').write_text(json.dumps(descriptor,indent=2)+'\n');(host/'host-runtime.json').chmod(0o444)
            for path in (host/'tools').rglob('*'):
                if path.is_file():path.chmod(0o444)
        files=[]
        for p in sorted(resources.rglob('*')):
            if p.is_file():
                relative=p.relative_to(resources).as_posix()
                files.append(dict(path=relative,bytes=p.stat().st_size,
                    sha256=record['sha256'] if relative=='images/main-qemuarm64.img' else digest(p)))
        rows={r['path']:r for r in files}
        manifest=dict(schemaVersion=1,kind='signed-vision-bootstrap',profile=model.PROFILE,bundleIdentifier=model.IDENTIFIER,
            teamIdentifier=model.TEAM,baseProgramManifestSha256=base_manifest,sources=dict(integration=revision,platform=platform_revision),
            factory=dict(rows['images/main-qemuarm64.img'],version=model.VERSION,architecture='main-qemuarm64',format='raw',
                         unitModel=model.MODEL,nodeType=model.NODE_TYPE,componentType=model.COMPONENT),
            cameraPayload=dict(rows['camera-access/payload.tar'],version='0.1.0'),files=files)
        p=resources/'bootstrap.json';p.write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n');p.chmod(0o444)
        done=subprocess.run(['/usr/bin/codesign','--sign',identity,'--timestamp=none',str(bundle)],capture_output=True,timeout=120)
        model.require(done.returncode==0,'BUNDLE_SIGNING_FAILED')
        # codesign just hashed the complete clone. Corroborate its sealed image
        # hash against the transfer receipt instead of reading gigabytes again.
        seal=plistlib.loads((contents/'_CodeSignature/CodeResources').read_bytes())
        model.require(seal['files2']['Resources/images/main-qemuarm64.img']['hash2'].hex()==record['sha256'],
                      'SEALED_FACTORY_DIGEST_MISMATCH')
        verified=model.verify(bundle,base_manifest)
        os.rename(bundle,output)
        return dict(outcome='SIGNED_VISION_BOOTSTRAP_NOT_LIVE_QUALIFIED',bundle=str(output),manifestSha256=verified.manifest_sha256,
                    sourceRevision=revision,platformRevision=platform_revision,teamIdentifier=model.TEAM)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('factory','camera-payload','output'):p.add_argument('--'+name,type=Path,required=True)
    for name in ('base-manifest','platform-revision','identity'):p.add_argument('--'+name,required=True)
    p.add_argument('--ingress-candidate',type=Path);p.add_argument('--ingress-proof',type=Path)
    p.add_argument('--update-platform-revision')
    p.add_argument('--services-candidate',type=Path);p.add_argument('--services-proof',type=Path)
    a=p.parse_args();print(json.dumps(assemble(a.factory,a.camera_payload,a.base_manifest,a.platform_revision,a.identity,a.output,
        a.ingress_candidate,a.ingress_proof,a.update_platform_revision,a.services_candidate,a.services_proof)))


if __name__=='__main__':main()
