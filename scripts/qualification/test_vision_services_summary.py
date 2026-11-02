# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
import copy
import unittest
from vision_services_summary import verdict


class SummaryTests(unittest.TestCase):
    def setUp(self):
        self.api=dict(apiPermanentPlatform='PASS_NO_TRANSIENT_PLATFORM_OVERRIDES',code='ModuleNotFoundError',cleanup=dict(stopped=True))
        self.ui=dict(outcome='PASS_PERMANENT_VISION_HEADED_BROWSER_UI',cleanup=dict(stopped=True))
        self.root=dict(outcome='PASS_ROOT6_CLOUD_INVENTORY_AFTER_EXACT_CACHE_RECONCILIATION',rootfsCloudConfirmed=True,cleanup=dict(stopped=True))

    def test_independent_api_and_ui_do_not_hide_rootfs_gate(self):
        self.assertEqual(verdict(self.api,self.ui,dict(outcome='NOT_COMPLETE')),'NOT_COMPLETE_ROOTFS_CLOUD_INVENTORY_GATE_OPEN')
        self.assertEqual(verdict(self.api,self.ui,self.root),'PASS_BOUNDED_NATIVE_API_AND_HEADED_VISION_UI')
        self.root['outcome']='PASS_ROOT6_CLOUD_INVENTORY_AFTER_NATIVE_CATALOG_RECONCILIATION'
        self.assertEqual(verdict(self.api,self.ui,self.root),'PASS_BOUNDED_NATIVE_API_AND_HEADED_VISION_UI')

    def test_a_later_cleanup_failure_cannot_be_aggregated_as_pass(self):
        for index in range(3):
            values=copy.deepcopy([self.api,self.ui,self.root]);values[index]['cleanup']['stopped']=False
            with self.assertRaises(ValueError):verdict(*values)

    def test_other_api_failures_cannot_reuse_characterization_as_full_api(self):
        self.api['code']='NATIVE_SERVICE_FAILED'
        with self.assertRaises(ValueError):verdict(self.api,self.ui,self.root)


if __name__=='__main__':unittest.main()
