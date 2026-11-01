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


def assemble(factory, camera_payload, base_manifest, platform_revision, identity, output):
    output=model.canonical(output)
    model.require(not output.exists() and output.suffix=='.bundle' and output.parent.is_dir(),'OUTPUT_EXISTS_OR_INVALID')
    model.require(output.parent.stat().st_dev==ROOT.stat().st_dev,'BUILD_REQUIRES_SELECTED_SSD')
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
        (contents/'Info.plist').write_bytes(plistlib.dumps(dict(CFBundleIdentifier=model.IDENTIFIER,
            CFBundleName='AosEdge Vision Bootstrap',CFBundlePackageType='BNDL',CFBundleVersion='0.3.0')))
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
        subprocess.run(['/usr/bin/codesign','--sign',identity,'--timestamp=none',str(bundle)],check=True,capture_output=True,timeout=120)
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
    a=p.parse_args();print(json.dumps(assemble(a.factory,a.camera_payload,a.base_manifest,a.platform_revision,a.identity,a.output)))


if __name__=='__main__':main()
