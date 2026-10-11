# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Integrated intent composes existing engines without a second lifecycle."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, Mock

import test_distribution_setup as fixtures
with patch.object(fixtures.sys, 'path', [str(fixtures.fixtures.SCRIPTS), *fixtures.sys.path]):
    from setup_bridge import request, perform
    import setup_workflow as workflow


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.f = fixtures.SetupTests(); self.f.addCleanup = self.addCleanup; self.f.setUp()
        self.pin = self.f.f.pin

    def value(self, action='setup-install'):
        value = dict(action=action, state=str(self.f.state))
        if action == 'setup-install':
            value.update(source=str(self.f.f.source), store=str(self.f.f.target))
        return request(json.dumps(value).encode())

    def test_empty_status_and_protocol_are_read_only(self):
        result = perform(self.value('setup-status'), self.pin)
        self.assertFalse(result['localInstalled'])
        self.assertFalse(self.f.state.exists())
        for change in (dict(unknown=True), dict(state='relative'), dict(source='/tmp/extra')):
            with self.assertRaises(ValueError):
                request(json.dumps(dict(dict(action='setup-status', state=str(self.f.state)), **change)).encode())

    def test_docker_failure_before_install_or_state_creation(self):
        with patch.object(workflow, 'Docker', side_effect=ValueError('SETUP_BACKENDS_DOCKER_MISSING')):
            with self.assertRaisesRegex(ValueError, 'DOCKER_MISSING'):
                perform(self.value(), self.pin)
        self.assertFalse(self.f.state.exists()); self.assertFalse(self.f.f.target.exists())

    def test_one_intent_preserves_engine_sequence(self):
        events = []
        real = fixtures.bridge.perform
        calls = []
        def step(value, pin, emit=lambda x: None):
            calls.append(value['action'])
            if value['action'] == 'prepare-backends': return {'status': 'fixture'}
            return real(value, pin, emit)
        with patch.object(workflow, 'Docker'), patch.object(workflow, 'launcher') as launcher, \
                patch.object(fixtures.bridge, 'perform', side_effect=step):
            result = workflow.perform(self.value(), self.pin, events.append)
        self.assertEqual(['preflight', 'install', 'prepare', 'prepare-backends'], calls)
        launcher.assert_called_once_with(self.pin)
        self.assertEqual('SETUP_LOCAL_INSTALLED', result['status'])
        self.assertFalse(result['demoReady']); self.assertFalse(result['runtimeChanged'])

    def test_reopen_does_not_recopy_or_select_or_import(self):
        self.f.run_action('install'); self.f.run_action('prepare')
        observed = dict(localInstalled=True, backendsObserved=True)
        with patch.object(workflow, 'status', return_value=observed), patch.object(workflow, 'Docker'), \
                patch.object(workflow, 'launcher'), patch.object(fixtures.bridge, 'perform') as step:
            workflow.perform(self.value(), self.pin)
        step.assert_not_called()


class LauncherTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(dir='/private/tmp'); self.addCleanup(temp.cleanup)
        self.home = Path(temp.name)
        self.app = self.home/'Media/AosEdge SDV Lab Setup.app'
        self.leaf = 'Contents/Resources/tooling/scripts/distribution/setup_release.json'
        file = self.app/self.leaf; file.parent.mkdir(parents=True)
        file.write_text(json.dumps(dict(manifestSha256='a'*64)))
        (self.app/'team').write_text('authorized-team')
        self.target = self.home/'Applications/AosEdge SDV Lab.app'
        self.previous = self.home/'Applications/.AosEdge SDV Lab.previous.app'
        def signature(path):
            return (path/'team').read_text()
        for mock in (patch.object(Path, 'home', return_value=self.home),
                     patch.object(workflow, '__file__', str(self.app/self.leaf)),
                     patch.object(workflow, 'signature', side_effect=signature),
                     patch.object(workflow.installed_control, 'unused')):
            mock.start(); self.addCleanup(mock.stop)

    def test_first_copy_and_same_team_replacement_leave_no_scratch(self):
        workflow.launcher('a'*64)
        self.assertEqual('a'*64, json.loads((self.target/self.leaf).read_bytes())['manifestSha256'])
        workflow.launcher('a'*64)
        self.assertFalse(self.previous.exists())
        self.assertEqual([self.target], list(self.target.parent.iterdir()))

    def test_foreign_launcher_is_not_overwritten(self):
        workflow.launcher('a'*64); (self.target/'team').write_text('foreign-team')
        with self.assertRaisesRegex(ValueError, 'FOREIGN_APPLICATION'): workflow.launcher('a'*64)
        self.assertEqual('foreign-team', (self.target/'team').read_text())

    def test_interrupted_rename_recovers_only_authorized_predecessor(self):
        workflow.launcher('a'*64); self.target.rename(self.previous)
        workflow.launcher('a'*64)
        self.assertTrue(self.target.is_dir()); self.assertFalse(self.previous.exists())
        self.target.rename(self.previous); (self.previous/'team').write_text('foreign-team')
        with self.assertRaisesRegex(ValueError, 'RECONCILIATION_REQUIRED'): workflow.launcher('a'*64)
        self.assertTrue(self.previous.is_dir()); self.assertFalse(self.target.exists())

    def test_active_launcher_or_wrong_pin_preserved(self):
        workflow.launcher('a'*64)
        with patch.object(workflow.installed_control, 'unused', side_effect=ValueError('IN_USE')):
            with self.assertRaisesRegex(ValueError, 'IN_USE'): workflow.launcher('a'*64)
        with self.assertRaisesRegex(ValueError, 'PIN_MISMATCH'): workflow.launcher('b'*64)
        self.assertTrue(self.target.is_dir()); self.assertFalse(self.previous.exists())


if __name__ == '__main__': unittest.main()
