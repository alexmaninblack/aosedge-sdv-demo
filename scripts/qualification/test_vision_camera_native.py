# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Pure outcome fixtures; no VM, Cloud or native deployment acceptance."""
import unittest
from vision_camera_native_worker import completion


class CompletionTests(unittest.TestCase):
    def test_cleanup_failure_prevents_native_or_transient_pass(self):
        for outcome in ('PASS_NATIVE_CAMERA_OEM_AND_AOS_READ','PASS_TRANSIENT_CAMERA_OEM_AND_AOS_READ'):
            value=completion(dict(outcome=outcome,cleanup=dict(sourceStopped=True,nativeVmStopped=False)))
            self.assertEqual('NOT_COMPLETE',value['outcome'])
            self.assertEqual('CAMERA_CLEANUP_NOT_CONFIRMED',value['code'])

    def test_preserve_failure_and_its_cause(self):
        value=dict(outcome='NOT_COMPLETE',code='CAMERA_OFFLINE_SELFTEST_FAILED',cleanup=dict(nativeVmStopped=False))
        self.assertEqual(value,completion(dict(value)))

    def test_completed_cleanup_does_not_upgrade_transient_proof(self):
        value=dict(outcome='PASS_TRANSIENT_CAMERA_OEM_AND_AOS_READ',cleanup=dict(nativeVmStopped=True))
        self.assertEqual(value,completion(dict(value)))


if __name__=='__main__':unittest.main()
