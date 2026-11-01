# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Offline acceptance-report gates; never invokes a VM or Cloud."""
import copy
import ast
from pathlib import Path
import unittest

from vision_camera_native_worker import completion
from vision_camera_fixture_cloud import configuration


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
    def test_read_versions_request_only_the_camera_read_resource(self):
        for version in ('0.1.0','0.1.2'):
            with self.subTest(version=version):
                item=configuration(version)['items'][0]
                self.assertEqual(item['version'],version)
                self.assertEqual(item['configuration']['resources'],[dict(name='vision-camera-read')])
                self.assertEqual(item['configuration']['allowedConnections'],[])

    def test_revoked_versions_request_neither_camera_nor_network(self):
        for version in ('0.1.1','0.1.3'):
            with self.subTest(version=version):
                item=configuration(version)['items'][0]
                self.assertEqual(item['configuration']['resources'],[])
                self.assertEqual(item['configuration']['allowedConnections'],[])

    def test_unknown_version_cannot_silently_omit_resource(self):
        for version in ('0.1.4','latest',None,1):
            with self.subTest(version=version),self.assertRaisesRegex(ValueError,'VERSION_INVALID'):
                configuration(version)


if __name__=='__main__':unittest.main()
