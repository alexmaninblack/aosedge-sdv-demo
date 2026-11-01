# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Hermetic signed-catalog fixtures; no signature, image or live-VM claim."""
import hashlib
import json
from pathlib import Path
import plistlib
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from aosedge_demo_orchestrator import vision_bootstrap as v
from aosedge_demo_orchestrator.environment import EnvironmentService,EnvironmentError
from aosedge_demo_orchestrator.images import ImageError

BASE='a'*64


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve();self.bundle=self.root/'Vision.bundle'
        self.resources=self.bundle/'Contents/Resources';self.resources.mkdir(parents=True)
        (self.bundle/'Contents/Info.plist').write_bytes(plistlib.dumps(dict(CFBundleIdentifier=v.IDENTIFIER,CFBundlePackageType='BNDL')))
        entries={'images/main-qemuarm64.img':b'unit-image-not-a-VM',
                 'camera-access/payload.tar':b'unit-payload',
                 'tooling/aosedge-sdv-demo/apps/demo-orchestrator/src/aosedge_demo_orchestrator/vision_bootstrap.py':b'# unit fixture\n',
                 'tooling/aosedge-sdv-demo/config/fixture.json':b'{}'}
        files=[]
        for name,raw in entries.items():
            path=self.resources/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw);path.chmod(0o444)
            files.append(dict(path=name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
        self.manifest=dict(schemaVersion=1,kind='signed-vision-bootstrap',profile=v.PROFILE,bundleIdentifier=v.IDENTIFIER,
            teamIdentifier=v.TEAM,baseProgramManifestSha256=BASE,sources=dict(integration='a'*40,platform='b'*40),
            factory=dict(files[0],version=v.VERSION,architecture='main-qemuarm64',format='raw',unitModel=v.MODEL,
                         nodeType=v.NODE_TYPE,componentType=v.COMPONENT),cameraPayload=dict(files[1],version='0.1.0'),files=files)
        self.save()
        self.sig=patch.object(v,'_signature');self.signature=self.sig.start();self.addCleanup(self.sig.stop)

    def save(self):
        p=self.resources/'bootstrap.json'
        if p.exists():p.chmod(0o644)
        p.write_text(json.dumps(self.manifest));p.chmod(0o444)

    def test_verified_catalog_exposes_only_exact_vision_selector(self):
        checked=v.verify(self.bundle,BASE)
        base=SimpleNamespace(**{n:self.root/n for n in ('root','workspace','project','input_root','input_project')})
        catalog=v.SignedVisionCatalog(checked,base)
        self.assertEqual(v.COMPONENT,self.manifest['factory']['componentType'])
        self.assertEqual(v.VM_PROFILE,catalog.resolve(v.SELECTOR).runtime_profile)
        self.assertEqual(base.input_root,catalog.input_root)
        self.assertEqual(v.NODE_TYPE,catalog.unit_configuration['nodes'][0]['nodeType'])
        for selector in ('latest','6.1.1-maninblack.42/main-qemuarm64',None):
            with self.assertRaises(ImageError):catalog.resolve(selector)
        with self.assertRaises(ImageError):catalog.resolve(v.SELECTOR,self.resources/'images/main-qemuarm64.img')
        with self.assertRaises(ImageError):catalog.component_support('anything')
        self.signature.assert_called_once_with(self.bundle)

    def test_main_environment_cannot_adopt_vision_input(self):
        checked=v.verify(self.bundle,BASE)
        base=SimpleNamespace(**{n:self.root/n for n in ('root','workspace','project','input_root','input_project')})
        catalog=v.SignedVisionCatalog(checked,base)
        with self.assertRaisesRegex(EnvironmentError,'PROFILE_BINDING'):
            EnvironmentService(self.root,catalog=catalog,qemu_img='unused')
        env=EnvironmentService(self.root,catalog=catalog,qemu_img='unused',vm_profile=v.VM_PROFILE)
        self.assertEqual(v.VM_PROFILE,env.vm_profile)

    def test_foreign_program_or_bundle_identity_fail_closed(self):
        with self.assertRaisesRegex(ImageError,'BASE_PROGRAM'):v.verify(self.bundle,'b'*64)
        for key,value in (('profile','main'),('teamIdentifier','OTHERTEAM00'),('bundleIdentifier','main.setup')):
            previous=self.manifest[key];self.manifest[key]=value;self.save()
            with self.assertRaises(ImageError):v.verify(self.bundle,BASE)
            self.manifest[key]=previous

    def test_image_successor_is_distinct_and_retains_all_previous_instances(self):
        contract=json.loads((Path(__file__).resolve().parents[3]/'contracts/vision-vm/bootstrap.v1.json').read_bytes())
        self.assertEqual(contract['nativeInstanceName'],v.INSTANCE_NAME)
        self.assertEqual(contract['verificationSetTitle'],v.SET_TITLE)
        self.assertEqual(contract['factoryVersion'],v.VERSION)
        self.assertEqual(tuple(contract['retainedInstanceNames']),v.RETAINED_INSTANCE_NAMES)
        self.assertIn('SDV-Vision-Camera-Lab-Data',v.RETAINED_INSTANCE_NAMES)
        self.assertNotIn(v.INSTANCE_NAME,v.RETAINED_INSTANCE_NAMES)
        self.manifest['factory']['version']='6.1.1-vision-camera.2';self.save()
        with self.assertRaisesRegex(ImageError,'FACTORY_PROFILE'):v.verify(self.bundle,BASE)

    def test_vdp_model_or_component_are_not_vision_bootstrap(self):
        for key,value in (('componentType','aos-vm-1.0.0-main-qemuarm64-vehicle-data-provider'),
                          ('unitModel',{'name':'aos-vm','version':'1.0.0'}),('nodeType','aos-vm-main')):
            previous=self.manifest['factory'][key];self.manifest['factory'][key]=value;self.save()
            with self.assertRaisesRegex(ImageError,'FACTORY_PROFILE'):v.verify(self.bundle,BASE)
            self.manifest['factory'][key]=previous

    def test_changed_source_or_unsigned_extra_file_are_rejected(self):
        source=self.resources/self.manifest['files'][2]['path'];source.chmod(0o644);source.write_bytes(b'changed');source.chmod(0o444)
        with self.assertRaises(ImageError):v.verify(self.bundle,BASE)

    def test_verified_handle_detects_subsequent_change(self):
        checked=v.verify(self.bundle,BASE)
        p=self.resources/'camera-access/payload.tar';p.chmod(0o644);p.write_bytes(b'changed');p.chmod(0o444)
        with self.assertRaisesRegex(ImageError,'CHANGED'):checked.unchanged()

    def test_undeclared_resource_and_path_escape_and_link_are_rejected(self):
        (self.resources/'extra.json').write_text('{}')
        with self.assertRaisesRegex(ImageError,'UNDECLARED'):v.verify(self.bundle,BASE)
        for path in ('../image','/image','a/../b','a\\b','a//b'):
            with self.assertRaises(ImageError):v.resource(self.resources,path)
        link=self.resources/'linked';link.symlink_to(self.root)
        with self.assertRaises(ImageError):v.resource(self.resources,'linked/file')

    def test_signature_failure_is_not_an_ad_hoc_fallback(self):
        self.signature.side_effect=ImageError('VISION_BOOTSTRAP_SIGNATURE_INVALID')
        with self.assertRaisesRegex(ImageError,'SIGNATURE_INVALID'):v.verify(self.bundle,BASE)

    def test_codesign_receives_inline_requirement_not_a_filename(self):
        self.sig.stop()
        signed=SimpleNamespace(returncode=0,stdout='',stderr='Identifier='+v.IDENTIFIER+'\nTeamIdentifier='+v.TEAM+'\nAuthority=Apple Development: fixture\n')
        with patch.object(v.subprocess,'run',return_value=signed) as run:
            v._signature(self.bundle)
        arguments=run.call_args_list[0].args[0]
        self.assertTrue(arguments[arguments.index('-R')+1].startswith('=identifier '))


if __name__=='__main__':unittest.main()
