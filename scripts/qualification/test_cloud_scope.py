# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Offline domain/owner guards; no authentication or live target required."""
import unittest
from unittest.mock import patch
import journey_worker as worker
import remote_harness as h

OWNERS={'oem':'60266780-a6e3-4998-a7b1-b39f246cf81d',
        'sp':'fa2c914f-dfc8-48e8-9888-1671c2c9c8c4'}


class CloudScopeTests(unittest.TestCase):
    def test_staging_default_is_unchanged(self):
        self.assertEqual(worker.cloud_scope({}),(worker.DOMAIN,None))

    def test_production_requires_both_explicit_owner_pins(self):
        with self.assertRaisesRegex(ValueError,'PRODUCTION_OWNER_PINS_REQUIRED'):
            worker.cloud_scope({'cloudDomain':'aoscloud.io'})
        self.assertEqual(worker.cloud_scope(dict(cloudDomain='aoscloud.io',cloudOwners=OWNERS)),
                         ('aoscloud.io',OWNERS))

    def test_invalid_domain_and_owner_inputs_fail_closed(self):
        for domain in ('other.example','https://aoscloud.io',None):
            with self.assertRaises(ValueError):worker.cloud_scope({'cloudDomain':domain})
        for owners in ({},dict(oem=OWNERS['oem']),dict(OWNERS,admin=OWNERS['oem']),
                       dict(OWNERS,sp='bad'),dict(OWNERS,sp=3),[]):
            with self.assertRaises(ValueError):
                worker.cloud_scope(dict(cloudDomain='aoscloud.io',cloudOwners=owners))

    def test_production_still_requires_exact_test_only_and_domain(self):
        state=dict(schemaVersion=1,kind='democtl.current-run',vehicles={'test':{'localVmId':'test'}},
                   selectedCloudDomain='aoscloud.io')
        worker.validate_binding(state,'test','aoscloud.io')
        with self.assertRaisesRegex(ValueError,'QUALIFICATION_CLOUD_CHANGED'):
            worker.validate_binding(state,'test')
        with self.assertRaisesRegex(ValueError,'EXACT_TEST_ONLY_REQUIRED'):
            worker.validate_binding(dict(state,vehicles=dict(state['vehicles'],production={})),
                                    'test','aoscloud.io')

    def test_network_probe_uses_only_selected_allowlisted_cloud(self):
        config=dict(model='M1',os='test',user='operator')
        facts=dict(arch='arm64',model='M1',os='test',user='operator')
        with patch.object(h,'remote',return_value=b'facts') as remote,patch.object(h,'parse_probe',return_value=facts):
            h.probe(config,cloud_domain='aoscloud.io')
            self.assertIn('https://aoscloud.io/',remote.call_args.args[1])
            self.assertNotIn('https://aws-stage.epmp-aos.projects.epam.com/',remote.call_args.args[1])
        with patch.object(h,'remote') as remote:
            with self.assertRaises(ValueError):h.probe(config,cloud_domain='other.example')
            remote.assert_not_called()


if __name__=='__main__':unittest.main()
