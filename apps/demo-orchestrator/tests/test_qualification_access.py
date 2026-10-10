# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
import contextlib
import json
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from aosedge_demo_orchestrator import qualification_access as q
from aosedge_demo_orchestrator.environment import JOURNAL, EnvironmentError
from aosedge_demo_orchestrator.native_access import NativeVMAccess
from aosedge_demo_orchestrator.status import load_configuration as actual_configuration


class QualificationAccessTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.path = self.root/q.PROFILE
        self.path.parent.mkdir(parents=True, mode=0o700)
        self.pin = 'a'*64
        self.value = dict(schemaVersion=1, kind='democtl.qualification-vm-access',
            instanceId='instance', domain=q.DOMAIN, factorySha256=self.pin, password='fixture-only')
        self.env = SimpleNamespace(root=self.root, _writer=contextlib.nullcontext,
            catalog=SimpleNamespace(resolve=Mock(return_value=SimpleNamespace(problems=[], sha256=self.pin))))
        self.patches = [patch.object(q.runtime_paths, 'installed', return_value=True),
            patch.object(q.runtime_paths, 'instance_id', return_value='instance'),
            patch('aosedge_demo_orchestrator.status.load_configuration', return_value=dict(
                cloudConnection=dict(domain=q.DOMAIN), vehicles=dict(test=dict(cloudHost=q.DOMAIN))))]
        for item in self.patches:
            item.start(); self.addCleanup(item.stop)

    def save(self, value=None):
        self.path.write_text(json.dumps(value or self.value)); self.path.chmod(0o600)

    def test_missing_is_ordinary_use_but_unattended_preflight_stops(self):
        self.assertIsNone(q.password(self.env, 'test', self.pin))
        with self.assertRaisesRegex(EnvironmentError, 'INPUT_REQUIRED'):
            q.preflight(self.env, 'factory')

    def test_first_and_repeat_prepare_private_bound_and_redacted(self):
        source = self.root/'fixture.json'
        source.write_text(json.dumps(dict(password='fixture-only'))); source.chmod(0o600)
        for _ in range(2):
            result = q.prepare(self.env, 'factory', source)
            self.assertTrue(result['available'])
            self.assertNotIn('fixture-only', json.dumps(result))
        self.assertEqual(self.path.stat().st_mode & 0o777, 0o600)
        self.assertEqual(q.password(self.env, 'test', self.pin), 'fixture-only')
        self.assertFalse((self.root/JOURNAL).exists())

    def test_real_fresh_configuration_uses_selected_domain_not_legacy_vehicle_defaults(self):
        config = self.root/'.local/demo-control/status.json'
        config.write_text(json.dumps(dict(schemaVersion=1, cloudProfiles={},
            cloudConnection=dict(domain=q.DOMAIN, source='OEM_CERTIFICATE_ORGANIZATION'))))
        source = self.root/'fixture.json'
        source.write_text(json.dumps(dict(password='fixture-only'))); source.chmod(0o600)
        with patch('aosedge_demo_orchestrator.status.load_configuration', side_effect=actual_configuration), \
             patch.object(q.runtime_paths, 'input_root', return_value=self.root/'inputs'):
            self.assertEqual(actual_configuration(self.root)['vehicles']['test']['cloudHost'], 'aoscloud.io')
            for _ in range(2):
                self.assertTrue(q.prepare(self.env, 'factory', source)['available'])
                self.assertTrue(q.preflight(self.env, 'factory')['available'])
            config.write_text(json.dumps(dict(schemaVersion=1, cloudProfiles={},
                cloudConnection=dict(domain='aoscloud.io', source='OEM_CERTIFICATE_ORGANIZATION'))))
            with self.assertRaisesRegex(EnvironmentError, 'STAGING_REQUIRED'):
                q.preflight(self.env, 'factory')

    def test_existing_journal_still_requires_staging_vehicle_binding(self):
        self.save()
        journal = self.root/JOURNAL; journal.parent.mkdir(parents=True); journal.write_text('{}')
        state = dict(vehicles=dict(test={}), selectedCloudDomain=q.DOMAIN)
        with patch('aosedge_demo_orchestrator.status.read_json', return_value=state), \
             patch('aosedge_demo_orchestrator.status.load_configuration', return_value=dict(
                cloudConnection=dict(domain=q.DOMAIN), vehicles=dict(test=None))):
            with self.assertRaisesRegex(EnvironmentError, 'TEST_FACTORY_MISMATCH'):
                q.preflight(self.env, 'factory')

    def test_production_wrong_factory_and_foreign_instance_rejected(self):
        self.save()
        for role, sha in [('production', self.pin), ('test', 'b'*64)]:
            with self.assertRaises(EnvironmentError): q.password(self.env, role, sha)
        self.save(dict(self.value, instanceId='other'))
        with self.assertRaises(EnvironmentError): q.preflight(self.env, 'factory')

    def test_unsafe_linked_pending_or_malformed_never_falls_back(self):
        self.save(); self.path.chmod(0o644)
        with self.assertRaisesRegex(EnvironmentError, 'PROFILE_INVALID'):
            q.password(self.env, 'test', self.pin)
        self.path.chmod(0o600)
        pending = self.path.with_name(self.path.name+'.pending')
        pending.touch()
        with self.assertRaisesRegex(EnvironmentError, 'WRITE_UNCONFIRMED'):
            q.password(self.env, 'test', self.pin)
        pending.unlink(); self.path.unlink(); self.path.symlink_to(self.root/'absent')
        with self.assertRaisesRegex(EnvironmentError, 'PROFILE_INVALID'):
            q.password(self.env, 'test', self.pin)

    def test_scope_and_password_validity_fail_closed(self):
        for value in ('', 'x\n', 'x\x00', 'x'*257, None):
            self.save(dict(self.value, password=value))
            with self.assertRaisesRegex(EnvironmentError, 'PROFILE_INVALID'):
                q.password(self.env, 'test', self.pin)
        self.save()
        with patch('aosedge_demo_orchestrator.status.load_configuration', return_value={}):
            with self.assertRaisesRegex(EnvironmentError, 'STAGING_REQUIRED'):
                q.preflight(self.env, 'factory')

    def test_existing_vm_requires_matching_journal_factory_and_test_only(self):
        self.save()
        journal = self.root/JOURNAL; journal.parent.mkdir(parents=True); journal.write_text('{}')
        state = dict(vehicles=dict(test={}), selectedCloudDomain=q.DOMAIN)
        with patch('aosedge_demo_orchestrator.status.read_json', return_value=state), \
             patch.object(q, 'factory_for', return_value=dict(sha256=self.pin)):
            self.assertEqual(q.password(self.env, 'test'), 'fixture-only')
            state['vehicles']['production'] = {}
            with self.assertRaisesRegex(EnvironmentError, 'TEST_FACTORY_MISMATCH'):
                q.password(self.env, 'test')

    def test_profile_uses_native_provider_without_keychain_or_dialog(self):
        runner, chain, progress = Mock(), Mock(), Mock()
        with patch.object(q, 'password', return_value='fixture-only'), \
             patch('aosedge_demo_orchestrator.environment.EnvironmentService', return_value=self.env):
            access = NativeVMAccess(progress, chain, runner)
            self.assertEqual(access('test'), 'fixture-only')
        chain.read.assert_not_called(); runner.assert_not_called()
        self.assertNotIn('fixture-only', str(progress.call_args_list))

    def test_invalid_profile_never_falls_back_to_dialog(self):
        runner, chain = Mock(), Mock()
        with patch.object(q, 'password', side_effect=EnvironmentError('QUALIFICATION_ACCESS_PROFILE_INVALID')), \
             patch('aosedge_demo_orchestrator.environment.EnvironmentService', return_value=self.env):
            with self.assertRaises(EnvironmentError): NativeVMAccess(keychain=chain, runner=runner)('test')
        runner.assert_not_called(); chain.read.assert_not_called()
