# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Native existing-access protocol against a tiny installed fixture."""

import json
import sys
import unittest
from unittest.mock import patch

import test_distribution_setup as local_setup
from test_distribution_installation import SCRIPTS, UUID
with patch.object(sys, 'path', [str(SCRIPTS), *sys.path]):
    import setup_cloud
from aosedge_demo_orchestrator import runtime_paths
from aosedge_demo_orchestrator.cloud_connection import CloudConnection, CONFIG
from aosedge_demo_orchestrator.cloud_setup import CloudSetup


class CloudBridgeTests(unittest.TestCase):
    def setUp(self):
        self.f = local_setup.SetupTests(); self.f.addCleanup = self.addCleanup; self.f.setUp()
        self.f.run_action('install'); self.f.run_action('prepare')
        self.state = self.f.state
        self.oem, self.sp = self.state.parent/'oem.p12', self.state.parent/'sp.p12'
        for path in (self.oem, self.sp):
            path.write_bytes(b'not-a-real-credential'); path.chmod(0o600)
        for mock in (patch.object(runtime_paths, 'volume_uuid', return_value=UUID),
                     patch.object(CloudConnection, 'inspect', return_value=dict(domain='stage.example.test', validUntil='2030-01-01'))):
            mock.start(); self.addCleanup(mock.stop)

    def req(self, action, token=None, **extra):
        value = dict(action=action, state=str(self.state), oem=str(self.oem), sp=str(self.sp))
        if token is not None: value['selectionToken'] = token
        return local_setup.bridge.request(json.dumps(dict(value, **extra)).encode())

    def run_action(self, action='cloud-inspect', token=None):
        return local_setup.bridge.perform(self.req(action, token), self.f.f.pin)

    def test_preview_save_repeat_and_get_only_check(self):
        preview = self.run_action()
        self.assertFalse(preview['cloudAccessed'])
        self.assertFalse((self.state/CONFIG).exists())
        saved = self.run_action('cloud-save', preview['selectionToken'])
        repeated = self.run_action('cloud-save', saved['selectionToken'])
        self.assertEqual(saved, repeated)
        for stage in ('READY', 'MISSING', 'BLOCKED'):
            report = dict(domain='stage.example.test', stage=stage,
                          checks=[dict(key='oem', state='READY', detail='do-not-echo-private-detail')])
            with patch.object(CloudSetup, 'check', return_value=report) as check, patch.object(CloudSetup, 'prepare') as prepare:
                result = self.run_action('cloud-check', saved['selectionToken'])
                check.assert_called_once_with(first_use=True); prepare.assert_not_called()
            self.assertTrue(result['cloudAccessed']); self.assertFalse(result['demoReady'])
            self.assertEqual(stage, result['cloudStage'])
            self.assertNotIn('do-not-echo', json.dumps(result))
            self.assertNotIn(str(self.state), json.dumps(result))

    def test_no_check_before_save_or_after_changed_selection(self):
        preview = self.run_action()
        with patch.object(CloudSetup, 'check') as check:
            with self.assertRaisesRegex(ValueError, 'SAVE_PAIR_FIRST'):
                self.run_action('cloud-check', preview['selectionToken'])
            saved = self.run_action('cloud-save', preview['selectionToken'])
            self.sp.write_bytes(b'changed'); self.sp.chmod(0o600)
            with self.assertRaisesRegex(ValueError, 'CHANGED_SINCE_PREVIEW'):
                self.run_action('cloud-check', saved['selectionToken'])
            check.assert_not_called()
        with self.assertRaisesRegex(ValueError, 'LOCAL_PREPARATION_REQUIRED'):
            local_setup.bridge.perform(self.req('cloud-inspect'), 'f'*64)

    def test_report_change_or_raw_server_error_not_exposed(self):
        saved = self.run_action('cloud-save', self.run_action()['selectionToken'])
        with patch.object(CloudSetup, 'check', return_value=dict(domain='different.example.test', stage='READY')):
            with self.assertRaisesRegex(ValueError, 'REPORT_INVALID'):
                self.run_action('cloud-check', saved['selectionToken'])
        with patch.object(CloudSetup, 'check', side_effect=ValueError('SECRET server body')):
            try: self.run_action('cloud-check', saved['selectionToken'])
            except ValueError as error: self.assertEqual('SETUP_OPERATION_FAILED', local_setup.bridge.error_code(error))
            else: self.fail('expected failure')

    def test_strict_actions_and_paths(self):
        for action in ('cloud-prepare', 'cloud-enroll', 'cloud-publish', 'cloud-launch'):
            with self.assertRaisesRegex(ValueError, 'ACTION_INVALID'): self.req(action)
        for change in (dict(oem='relative'), dict(oem=str(self.oem)+'/'), dict(sp='//private/a.p12'),
                       dict(sp='/a\nb.p12'), dict(domain='other.test'), dict(token='secret')):
            with self.assertRaises(ValueError): self.req('cloud-inspect', **change)
        with self.assertRaises(ValueError): self.req('cloud-save')
        with self.assertRaises(ValueError): self.req('cloud-save', 'invalid')
