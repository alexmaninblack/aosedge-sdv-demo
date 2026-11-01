# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Offline acceptance-report gates; never invokes a VM or Cloud."""
import copy
import ast
from pathlib import Path
import unittest
import hashlib
import subprocess
import sys
import tempfile

from vision_camera_native_worker import completion,fixture_helpers
from vision_camera_fixture_cloud import configuration,terminal_retry,title_correction,TITLE,successor_authority,SUCCESSOR_PACKET,FIXED_BINARY_SHA


class NativeFixtureIsolationTests(unittest.TestCase):
    def test_negative_exec_mount_is_private_bounded_and_does_not_remount_run(self):
        source=Path(__file__).with_name('vision_negative_probe.py').read_text()
        tree=ast.parse(source)
        commands=[n for n in ast.walk(tree) if isinstance(n,ast.List)
            and n.elts and isinstance(n.elts[0],ast.Constant) and n.elts[0].value=='mount']
        self.assertEqual(len(commands),1)
        self.assertEqual([ast.literal_eval(n) for n in commands[0].elts[:-1]],
            ['mount','-t','tmpfs','-o','size=4m,mode=0755,nodev,exec,suid','tmpfs'])
        self.assertEqual(ast.unparse(commands[0].elts[-1]),'str(executable)')
        self.assertIn("executable=root/'exec'",source)
        self.assertIn("['mount','-t','tmpfs','-o','size=4m,mode=0755,nodev,exec,suid','tmpfs',str(executable)]",source)
        self.assertNotIn('remount',source)
        self.assertIn("st_mode&0o7777==0o555",source)
        self.assertIn("st_uid==0",source)

    def test_negative_exec_cleanup_unmounts_normally_before_removing_owned_root(self):
        source=Path(__file__).with_name('vision_negative_probe.py').read_text()
        cleanup=source[source.index('def cleanup(files):'):]
        self.assertIn("json.loads((root/'.owner.json').read_bytes())==pins",cleanup)
        self.assertLess(cleanup.index("['umount',str(executable)]"),cleanup.index('executable.rmdir()'))
        self.assertIn('not executable.is_mount() and not any(executable.iterdir())',cleanup)
        self.assertNotIn('rmtree',source)
        self.assertNotIn("'-f'",cleanup)
        self.assertNotIn("'-l'",cleanup)

    def test_negative_prerequisites_never_open_credential_or_network(self):
        root=Path(__file__).resolve().parents[2]/'tests/fixtures'
        for name,operation in (('vision-ingress-boundary.c','int fd=socket('),('vision-camera-credential-deny.c','int fd=open(')):
            source=(root/name).read_text()
            self.assertIn('CONTEXT_OPEN',source);self.assertIn('CONTEXT_DOMAIN',source)
            self.assertLess(source.index('if(identity_only){'),source.index(operation))
        ast.parse(Path(__file__).with_name('vision_negative_probe.py').read_text())

    def test_hash_fixture_ignores_system_openssl_configuration_and_checks_result(self):
        source=(Path(__file__).resolve().parents[2]/'tests/fixtures/vision-camera-probe.c').read_text()
        self.assertLess(source.index('OPENSSL_init_crypto(OPENSSL_INIT_NO_LOAD_CONFIG,NULL)'),source.index('SHA256(body,sizes[i],hash)'))
        self.assertIn('if(SHA256(body,sizes[i],hash)==NULL)',source)

    def test_nested_diagnostic_guest_programs_are_syntax_checked_offline(self):
        for name in ('vision_fresh_diagnose.py','vision_reader_diagnostic.py'):
            source=Path(__file__).with_name(name).read_text();tree=ast.parse(source)
            programs=[n.value for n in ast.walk(tree) if isinstance(n,ast.Constant) and isinstance(n.value,str)
                and n.value.startswith(('import pathlib,','import json,sys,pathlib,')) and '\n' in n.value]
            self.assertTrue(programs)
            for program in programs:ast.parse(program)
            self.assertIn('ast.parse(guest)',source);self.assertIn('ast.parse(code)',source)


class CompletionTests(unittest.TestCase):
    def setUp(self):
        self.complete=dict(outcome='PASS_NATIVE_CAMERA_OEM_AND_AOS_READ',
            cameraRestart='PASS_FRESH_EPOCH_WITHOUT_SOURCE',
            nativeColdRestart='PASS_SAME_UNIT_STORE_AND_REVOKED_RESOURCE',
            resourceRevocation='PASS',cleanup=dict(vmStopped=True,sourceStopped=True))

    def test_complete_native_report_is_retained(self):
        self.assertEqual(completion(copy.deepcopy(self.complete)),self.complete)

    def test_service_restart_does_not_replace_cold_boot(self):
        value=copy.deepcopy(self.complete);value['nativeColdRestart']='NOT_RUN'
        self.assertEqual(completion(value)['code'],'CAMERA_ACCEPTANCE_GATE_NOT_COMPLETE')

    def test_no_gate_can_be_omitted(self):
        for key in ('cameraRestart','nativeColdRestart','resourceRevocation'):
            with self.subTest(key=key):
                value=copy.deepcopy(self.complete);value.pop(key)
                self.assertEqual(completion(value)['outcome'],'NOT_COMPLETE')

    def test_failed_cleanup_cannot_pass(self):
        value=copy.deepcopy(self.complete);value['cleanup']['vmStopped']=False
        self.assertEqual(completion(value)['code'],'CAMERA_CLEANUP_NOT_CONFIRMED')

    def test_failed_report_cannot_be_promoted(self):
        value=dict(outcome='NOT_COMPLETE',code='NATIVE_FAILURE',cleanup={})
        self.assertEqual(completion(copy.deepcopy(value)),value)

    def test_embedded_guest_scripts_have_valid_python_syntax(self):
        tree=ast.parse(Path(__file__).with_name('vision_camera_native_worker.py').read_text())
        checked=0
        for value in ast.walk(tree):
            if isinstance(value,ast.Constant) and isinstance(value.value,str) and value.value.startswith('import ') and '\n' in value.value:
                compile(value.value,'native-camera-guest-fixture','exec');checked+=1
        self.assertGreaterEqual(checked,8)


class ProbeConfigurationTests(unittest.TestCase):
    def test_verified_fixture_loads_in_isolated_python_without_script_search_path(self):
        worker=Path(__file__).with_name('vision_camera_native_worker.py').resolve()
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary).resolve();fixture=root/'vision_camera_fixture_cloud.py'
            fixture.write_text('answer = 42\n');digest=hashlib.sha256(fixture.read_bytes()).hexdigest()
            code="import importlib.util,pathlib; s=importlib.util.spec_from_file_location('worker',"+repr(str(worker))+"); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); assert m.fixture_helpers(pathlib.Path("+repr(str(root))+"),"+repr(digest)+").answer==42"
            subprocess.run([sys.executable,'-I','-B','-c',code],check=True,capture_output=True,timeout=5)
            with self.assertRaisesRegex(ValueError,'FIXTURE_WORKER_CHANGED'):fixture_helpers(root,'0'*64)

    def test_new_service_has_a_distinct_title_and_only_that_field_may_be_corrected(self):
        after=configuration('0.1.0');before=copy.deepcopy(after)
        before['items'][0]['identity']['title']='Vision Camera Access Probe'
        self.assertEqual(TITLE,'Vision Camera Image Probe')
        title_correction(before,after)
        for mutate in (lambda c:c['items'][0].update(version='0.1.2'),
                lambda c:c['items'][0]['configuration'].update(resources=[]),
                lambda c:c['items'][0]['identity'].update(codename='other')):
            wrong=copy.deepcopy(after);mutate(wrong)
            with self.assertRaisesRegex(ValueError,'TITLE_CORRECTION_MUST_BE_ONLY_CHANGE'):title_correction(before,wrong)

    def test_terminal_retry_requires_exact_failed_job_and_no_catalog_effect(self):
        terminal_retry(dict(id='known',state='error'),'known',None,[])
        for bundle,identity,versions in ((dict(id='other',state='error'),None,[]),
                (dict(id='known',state='processing'),None,[]),
                (dict(id='known',state='error'),'existing-service',[]),
                (dict(id='known',state='error'),None,[dict(version='0.1.0')])):
            with self.subTest(bundle=bundle,identity=identity,versions=versions),self.assertRaisesRegex(ValueError,'TERMINAL_BUILD_WITHOUT_EFFECT_REQUIRED'):
                terminal_retry(bundle,'known',identity,versions)

    def test_read_versions_request_only_the_camera_read_resource(self):
        for version in ('0.1.0','0.1.2','0.1.4','0.1.6'):
            with self.subTest(version=version):
                item=configuration(version)['items'][0]
                self.assertEqual(item['version'],version)
                self.assertEqual(item['configuration']['resources'],[dict(name='vision-camera-read')])
                self.assertEqual(item['configuration']['allowedConnections'],[])

    def test_revoked_versions_request_neither_camera_nor_network(self):
        for version in ('0.1.1','0.1.3','0.1.5','0.1.7'):
            with self.subTest(version=version):
                item=configuration(version)['items'][0]
                self.assertEqual(item['configuration']['resources'],[])
                self.assertEqual(item['configuration']['allowedConnections'],[])

    def test_unknown_version_cannot_silently_omit_resource(self):
        for version in ('0.1.8','latest',None,1):
            with self.subTest(version=version),self.assertRaisesRegex(ValueError,'VERSION_INVALID'):
                configuration(version)

    def test_successors_require_exact_accepted_pair_and_fixed_binary(self):
        for version in ('0.1.6','0.1.7'):
            request=dict(probeVersion=version,diagnosticSuccessors=dict(SUCCESSOR_PACKET),binarySha256=FIXED_BINARY_SHA)
            successor_authority(request)
            for key,value in (('diagnosticSuccessors',{}),('binarySha256','older-binary')):
                with self.assertRaises(ValueError):successor_authority(dict(request,**{key:value}))
            with self.assertRaises(ValueError):successor_authority(dict(probeVersion=version,binarySha256=FIXED_BINARY_SHA))


if __name__=='__main__':unittest.main()
