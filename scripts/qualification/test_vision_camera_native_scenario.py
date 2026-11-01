# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Offline acceptance-report gates; never invokes a VM or Cloud."""
import copy
import unittest

from vision_camera_native_worker import completion


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


if __name__=='__main__':unittest.main()
