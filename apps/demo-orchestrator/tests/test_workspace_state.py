# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Independent window-state regression; no live UI, Cloud or VM actions."""
import contextlib
import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import Mock, patch
from uuid import uuid4

from aosedge_demo_orchestrator import workspace
from aosedge_demo_orchestrator.environment import JOURNAL, atomic_json
from aosedge_demo_orchestrator.status import load_configuration
from aosedge_demo_orchestrator.presenter_operations import SessionOperations


class SeparateWorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='sdv-window-state-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.env = Mock(root=self.root)
        self.env._writer.side_effect = contextlib.nullcontext
        self.driver = Mock()
        self.driver.vm._processes.return_value = []
        self.driver.live_process.return_value = 30
        self.service = workspace.WorkspaceService(self.env, self.driver)
        self.service.directory.mkdir(parents=True, mode=0o700)
        self.service.binary.touch()
        self.journal = self.root / JOURNAL
        self.screen = dict(x=0, y=39, width=2056, height=1224, desktopState='UNLOCKED')
        self.layout = workspace.geometry(self.screen)
        self.service.save_configuration(dict(profile='builtin-v1', presenterBuild=self.service.binary.stat().st_mtime_ns))

    def restore(self, service=None, window_error=None, order_state='VERIFIED', **kwargs):
        service = service or self.service
        def window(pid, rectangle=None, title=None):
            if window_error:
                raise workspace.EnvironmentError(window_error)
            return self.layout[{'Demo Presenter — Header':'header', 'Demo Presenter — Platform':'browser',
                                'Demo Presenter — Background':'backdrop'}[title]]
        with patch.object(service, 'build'), patch.object(workspace.subprocess, 'run',
            return_value=Mock(returncode=0, stdout=json.dumps(self.screen))), \
            patch.object(workspace, 'window', side_effect=window), patch.object(workspace.os, 'kill'), \
            patch.object(service, 'ordering', return_value=dict(state=order_state)):
            return service.execute('restore', **kwargs)

    def test_empty_presenter_does_not_retry_absent_simulator_windows(self):
        for service in (self.service, self.service, workspace.WorkspaceService(self.env, self.driver)):
            result = self.restore(service)
            self.assertEqual('INCOMPLETE', result['state'])  # Not full demo readiness.
            self.assertFalse(result['retryPending'])
            self.assertEqual(0, service.configuration()['placement']['attempt'])
            self.assertEqual(3, len(result['problems']))
            with patch.object(workspace, 'window') as observed:
                service.execute('restore', recovery=True)
            observed.assert_not_called()
            self.assertFalse(self.journal.exists())

    def test_empty_presenter_still_retries_real_readiness_but_not_permission_errors(self):
        for error, retry in (('WORKSPACE_WINDOW_COUNT:0', True),
                             ('WORKSPACE_ACCESSIBILITY_REQUIRED', False),
                             ('WORKSPACE_WINDOW_COUNT:2', False)):
            with self.subTest(error=error):
                result = self.restore(window_error=error)
                self.assertEqual(retry, result['retryPending'])
                self.assertTrue(any('geometry observation unavailable' in p for p in result['problems']))
                for _ in range(3):
                    result = self.restore(window_error=error, recovery=True)
                self.assertFalse(result['retryPending'])
                self.assertFalse(self.journal.exists())

    def test_empty_presenter_still_requires_verified_z_order(self):
        result = self.restore(order_state='INCORRECT')
        self.assertTrue(result['retryPending'])
        self.assertIn('WORKSPACE_Z_ORDER_NOT_VERIFIED', result['problems'])
        self.assertFalse(self.journal.exists())

    def test_native_registration_display_change_settles_via_existing_recovery(self):
        initial = dict(self.screen, height=1220)
        settled = dict(self.screen, height=1225)
        self.layout = workspace.geometry(initial)
        def window(pid, rectangle=None, title=None):
            return self.layout[{'Demo Presenter — Header':'header', 'Demo Presenter — Platform':'browser',
                                'Demo Presenter — Background':'backdrop'}[title]]
        with patch.object(self.service, 'build'), patch.object(workspace.subprocess, 'run',
                side_effect=[Mock(returncode=0, stdout=json.dumps(row))
                             for row in (initial, settled, settled, settled, settled)]), \
                patch.object(workspace, 'window', side_effect=window), patch.object(workspace.os, 'kill'), \
                patch.object(self.service, 'ordering', return_value=dict(state='VERIFIED')):
            result = self.service.execute('restore')
            self.assertTrue(result['retryPending'])
            self.assertIn('WORKSPACE_DISPLAY_CHANGED', result['problems'])
            self.assertEqual(initial, result['display'])  # Applied geometry remains honest.
            self.layout = workspace.geometry(settled)
            result = self.service.execute('restore', recovery=True)
            self.assertFalse(result['retryPending'])
            self.assertEqual(1, self.service.configuration()['placement']['attempt'])
            self.assertEqual(3, len(result['problems']))  # Expected absences, not full demo ready.
            saved = (self.service.directory / 'state.json').read_bytes()
            observed = self.service.execute('status')
            self.assertEqual(saved, (self.service.directory / 'state.json').read_bytes())
            self.assertEqual(self.layout['browser'], observed['surfaces']['browser']['actual'])
        self.assertFalse(self.journal.exists())
        self.driver.start.assert_not_called()
        self.driver.vm.execute.assert_not_called()

    def test_repeated_display_changes_are_bounded_and_observation_failure_is_not_success(self):
        changing = dict(self.screen, height=self.screen['height'] + 5)
        screens = [self.screen, changing] * 4
        with patch.object(self.service, 'build'), patch.object(workspace.subprocess, 'run',
                side_effect=[Mock(returncode=0, stdout=json.dumps(row)) for row in screens]), \
                patch.object(workspace, 'window', return_value=self.layout['header']), \
                patch.object(workspace.os, 'kill'), \
                patch.object(self.service, 'ordering', return_value=dict(state='VERIFIED')):
            self.service.execute('restore')
            for _ in range(3):
                result = self.service.execute('restore', recovery=True)
            self.assertFalse(result['retryPending'])
            self.assertEqual('INCOMPLETE', result['state'])
            self.assertEqual(3, self.service.configuration()['placement']['attempt'])
        with patch.object(self.service, 'build'), patch.object(workspace.subprocess, 'run',
                side_effect=[Mock(returncode=0, stdout=json.dumps(self.screen)), Mock(returncode=1)]), \
                patch.object(workspace, 'window', return_value=self.layout['header']), \
                patch.object(workspace.os, 'kill'), \
                patch.object(self.service, 'ordering', return_value=dict(state='VERIFIED')):
            with self.assertRaisesRegex(workspace.EnvironmentError, 'BUILTIN_DISPLAY_UNAVAILABLE'):
                self.service.execute('restore')
        self.assertFalse(self.journal.exists())

    def test_first_repeat_restart_never_create_vehicle_journal(self):
        for service in (self.service, self.service, workspace.WorkspaceService(self.env, self.driver)):
            self.restore(service)
            self.assertFalse(self.journal.exists())
            load_configuration(self.root)
            self.assertEqual('builtin-v1', service.configuration()['profile'])
        self.driver.start.assert_not_called()
        self.driver.vm.execute.assert_not_called()

    def test_first_open_without_any_layout_record_then_repeat(self):
        (self.service.directory / 'state.json').unlink()
        self.driver.live_process.side_effect = [None, 30]
        with patch.object(workspace.subprocess, 'Popen', return_value=Mock(pid=30)) as launched:
            self.restore()
            self.restore()
        self.assertEqual(1, launched.call_count)
        self.assertFalse(self.journal.exists())
        load_configuration(self.root)

    def test_real_session_metadata_can_dispatch_after_window_restore(self):
        self.restore()
        operations = SessionOperations()
        identity = str(uuid4())
        operations.jobs[identity] = dict(id=identity, action='workspace-restore', progress=[], results=[])
        application = Mock(environment_service=self.env)
        with patch('aosedge_demo_orchestrator.presenter_operations.DemoOrchestrator', return_value=application), \
                patch('aosedge_demo_orchestrator.presenter_operations.VMService'), \
                patch('aosedge_demo_orchestrator.presenter_operations.execute_operation',
                    return_value=dict(operation='workspace.restore', state='COMPLETED', message='test', data={})) as dispatch:
            operations.run(identity, [dict(domain='workspace', action='restore')])
        self.assertEqual(1, dispatch.call_count)
        self.assertFalse(operations.uncertain)
        self.assertEqual('COMPLETED', operations.jobs[identity]['state'])

    def test_existing_vehicle_journal_and_old_workspace_are_preserved(self):
        self.journal.parent.mkdir(parents=True)
        value = dict(schemaVersion=1, kind='democtl.current-run', vehicles={'test':{'localVmId':'preserved'}},
                     workspace=dict(profile='builtin-v1', legacyField='preserved'))
        atomic_json(self.journal, value)
        before = self.journal.read_bytes()
        self.restore()
        self.assertEqual(before, self.journal.read_bytes())
        self.assertNotIn('legacyField', self.service.configuration())

    def test_legacy_layout_read_through_is_read_only(self):
        (self.service.directory / 'state.json').unlink()
        self.journal.parent.mkdir(parents=True)
        value = dict(workspace=dict(profile='builtin-v1', orderingGeneration=23))
        atomic_json(self.journal, value)
        before = self.journal.read_bytes()
        self.assertEqual(value['workspace'], self.service.configuration())
        self.assertFalse((self.service.directory / 'state.json').exists())
        self.assertEqual(before, self.journal.read_bytes())

    def test_invalid_lifecycle_journal_is_not_accepted_by_configuration(self):
        self.journal.parent.mkdir(parents=True)
        atomic_json(self.journal, dict(workspace={}))
        with self.assertRaisesRegex(ValueError, 'Unsupported current journal'):
            load_configuration(self.root)

    def test_read_only_status_does_not_modify_records(self):
        self.restore()
        path = self.service.directory / 'state.json'
        before = path.read_bytes(), path.stat().st_mtime_ns
        self.service.cached()
        self.assertEqual(before, (path.read_bytes(), path.stat().st_mtime_ns))
        self.assertFalse(self.journal.exists())

    def test_pending_state_fails_before_window_actions(self):
        path = self.service.directory / 'state.json.pending'
        path.touch(mode=0o600)
        with patch.object(self.service, 'build') as build, self.assertRaisesRegex(ValueError, 'WORKSPACE_STATE_RECOVERY_REQUIRED'):
            self.service.execute('restore')
        build.assert_not_called()
        self.assertTrue(path.exists())

    def test_bad_record_never_falls_back_to_legacy(self):
        path = self.service.directory / 'state.json'
        for value in ({}, dict(schemaVersion=True,kind='democtl.workspace',workspace={}),
                      dict(schemaVersion=2,kind='democtl.workspace',workspace={}),
                      dict(schemaVersion=1,kind='foreign',workspace={}),
                      dict(schemaVersion=1,kind='democtl.workspace',workspace={'vehicles':{}}),
                      dict(schemaVersion=1,kind='democtl.workspace',workspace={'placement':[]}),
                      dict(schemaVersion=1,kind='democtl.workspace',workspace=[])):
            atomic_json(path, value)
            with self.assertRaisesRegex(ValueError, 'WORKSPACE_STATE_INVALID'):
                self.service.configuration({'workspace':{'profile':'builtin-v1'}})

    def test_unsafe_file_mode_symlink_and_hardlink_rejected(self):
        path = self.service.directory / 'state.json'
        path.chmod(0o644)
        with self.assertRaises(ValueError): self.service.configuration()
        path.chmod(0o600)
        hard = path.with_name('linked')
        os.link(path, hard)
        with self.assertRaises(ValueError): self.service.configuration()
        hard.unlink()
        path.unlink()
        path.symlink_to(self.service.binary)
        with self.assertRaises(ValueError): self.service.configuration()

    def test_recovery_failure_without_vehicle_journal_is_recorded_separately(self):
        recovery = workspace.WorkspaceRecovery(self.service, Mock(lock=threading.RLock()))
        recovery.fail()
        self.assertFalse(self.journal.exists())
        self.assertEqual(['WORKSPACE_RECOVERY_FAILED'], self.service.cached()['problems'])

    def test_old_run_recovery_does_not_move_new_run_windows(self):
        self.restore()
        self.journal.parent.mkdir(parents=True)
        atomic_json(self.journal, {'source':{'runId':'new-run'}})
        with patch.object(workspace, 'window') as window:
            self.assertEqual({}, self.service.execute('restore', recovery=True))
        window.assert_not_called()


if __name__ == '__main__': unittest.main(verbosity=2)
