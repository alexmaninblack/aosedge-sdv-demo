# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Private qualification correlation does not restore raw browser identities."""
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import journey_worker as worker
import ui_pilot


class BrowserIdentityTests(unittest.TestCase):
    def test_reset_reference_is_checked_against_both_current_protocol_views(self):
        identity = '01234567-89ab-cdef-0123-456789abcdef'
        native = dict(commandId=identity, issuedAt='2026-10-18T12:00:00Z', unitSystemUid='private', state='CLEARED')
        public = dict(native, commandId='ref_'+'a'*32, unitSystemUid='ref_'+'b'*32)
        self.assertEqual(worker.reset_command_binding(native, public, public['commandId']), identity)
        self.assertEqual(worker.reset_command_binding(dict(native,state='PENDING'), public, public['commandId']),identity)
        for changed in (dict(public,commandId='ref_'+'c'*32), dict(public,issuedAt='other'), dict(public,state='PENDING')):
            with self.assertRaises(ValueError):
                worker.reset_command_binding(native, changed, public['commandId'])

    def test_service_selector_uses_the_actual_top_level_local_receipt_projection(self):
        native=dict(serviceId='private-service',submitted=True,releaseHandle='brake/70.0.0')
        public=dict(serviceId='ref_'+'a'*32,releaseHandle='brake/70.0.0')
        value=object.__new__(worker.Worker)
        value.app=SimpleNamespace(environment_service=object())
        with patch('aosedge_demo_orchestrator.service_packages.ServicePackages') as packages, patch.object(worker,'exchange') as read:
            packages.return_value.receipts.return_value=dict(releases=[native])
            read.return_value=dict(serviceReleases=[public])
            self.assertEqual(value.service_reference('private-service'),public['serviceId'])
            read.assert_called_once_with('snapshot')
            read.return_value=dict(value=dict(serviceReleases=[public]))
            with self.assertRaisesRegex(ValueError,'BROWSER_SERVICE_BINDING_UNCONFIRMED'):
                value.service_reference('private-service')

    def test_browser_binding_requires_opaque_reference_and_same_vehicle_roles(self):
        native = dict(runId='01234567-89ab-cdef-0123-456789abcdef', vehicles={'test': {}})
        public = dict(runId='ref_'+'a'*32, vehicles={'test': {}})
        self.assertEqual(worker.browser_run_binding(native, public), public['runId'])
        for value in (native['runId'], 'test', '', None, 'ref_'+'a'*31):
            with self.assertRaisesRegex(ValueError, 'BROWSER_IDENTITY_NOT_OPAQUE'):
                worker.browser_run_binding(native, dict(public, runId=value))
        with self.assertRaisesRegex(ValueError, 'BROWSER_TEST_BINDING_CHANGED'):
            worker.browser_run_binding(native, dict(public, vehicles={'production': {}}))
        self.assertIsNone(worker.browser_run_binding(dict(runId=None), dict(runId=None)))
        with self.assertRaisesRegex(ValueError, 'PRESENTER_IDENTITY_CHANGED'):
            worker.browser_run_binding(dict(runId=None), public)

    def test_ui_backend_observer_explicitly_selects_public_projection(self):
        transport, config = {}, {}
        with patch.object(ui_pilot.j, 'Remote') as remote:
            remote.return_value.return_value = dict(outcome='PASS', code='POSTCONDITION_OBSERVED', facts={})
            ui_pilot.read_query(transport, config, 'private-test', 'backend', 'brake')
            args = remote.return_value.call_args.args[0]['args']
            self.assertEqual(args, dict(query='backend', team='brake', browserProjection=True))
            ui_pilot.read_query(transport, config, 'private-test', 'combined')
            self.assertTrue(remote.return_value.call_args.args[0]['args']['browserProjection'])


if __name__ == '__main__':
    unittest.main()
