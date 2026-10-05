# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Native launch contract; no real process, Cloud, VM or desktop mutation."""

from contextlib import nullcontext, contextmanager
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import test_distribution_setup as fixtures
with patch.object(sys, 'path', [str(fixtures.fixtures.SCRIPTS), *sys.path]):
    import setup_launch as launch


def snapshot(**changes):
    return dict(sessionId='session-1', active=None, uncertain=False, workspaceBusy=False,
                sourceRecoveryBusy=False, sourceRecovery=None, jobs=[], **changes)


def surfaces():
    return dict(state='PLACED_AWAITING_VISUAL_REVIEW', zOrder=dict(state='VERIFIED'),
        hostPid=17, surfaces={name: dict(pid=17, actual=[1, 2, 100, 200], expected=[1, 2, 100, 200])
                              for name in ('header', 'browser', 'backdrop')})


class ProtocolTests(unittest.TestCase):
    def test_package_access_feedback_precedes_the_first_package_open(self):
        events = []
        @contextmanager
        def package(*args, **kwargs):
            self.assertEqual('LAUNCH_PACKAGE_ACCESS', events[-1]['stage'])
            raise RuntimeError('proof stops before external file access')
            yield
        with patch.object(launch.runtime_paths, 'instance', return_value=(Path('/private/tmp/state'), 'instance')), \
                patch.object(launch.installed_control, 'selection', return_value={'current':'a'*64, 'storePath':'/private/tmp/store'}), \
                patch.object(launch.runtime_paths, 'installed_session', side_effect=package), \
                self.assertRaisesRegex(RuntimeError, 'proof stops'):
            launch.perform({'action':'launch', 'state':'/private/tmp/state'}, 'a'*64, events.append)
        self.assertNotIn('/private/tmp', json.dumps(events))

    def test_missing_instance_is_actionable_before_runtime(self):
        with patch.object(fixtures.bridge, 'supported_platform'), \
                patch.object(fixtures.bridge, 'state_check', side_effect=FileNotFoundError('must not echo')):
            with self.assertRaisesRegex(ValueError, '^SETUP_INSTANCE_NOT_FOUND$'):
                fixtures.bridge.perform({'action':'launch','state':'/private/tmp/absent'}, 'a'*64)

    def test_access_denial_is_redacted_and_does_not_suggest_a_broken_package(self):
        self.assertEqual('SETUP_FILE_ACCESS_DENIED', fixtures.bridge.error_code(PermissionError('private path must not echo')))

    def test_launch_request_has_no_commands_or_credentials(self):
        value = dict(action='launch', state='/private/tmp/sdv-launch-test')
        self.assertEqual(value, fixtures.bridge.request(json.dumps(value).encode()))
        for changed in (dict(command='anything'), dict(source='/tmp/source'), dict(pin='a'*64),
                        dict(state='relative'), dict(state='/tmp/../tmp/x'), dict(state='/tmp/x/'),
                        dict(state='/tmp/a\nb'), dict(state='//tmp/x')):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                fixtures.bridge.request(json.dumps(value | changed).encode())

    def test_missing_or_busy_session_fails_closed(self):
        launch.idle(snapshot())
        for key in ('sessionId', 'active', 'uncertain', 'workspaceBusy', 'sourceRecoveryBusy'):
            value = snapshot(); del value[key]
            with self.subTest(missing=key), self.assertRaises(ValueError):
                launch.idle(value)
        for changed in ({'active': 'job'}, {'uncertain': True}, {'workspaceBusy': True},
                        {'sourceRecoveryBusy': True}, {'sourceRecovery': {'state': 'FAILED'}}):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                launch.idle(snapshot() | changed)

    def test_surface_observation_is_not_full_demo_readiness(self):
        self.assertEqual(dict(status='PRESENTER_OPENED', presenterObserved=True, layoutComplete=True),
                         launch.surface_result(surfaces()))
        value = surfaces(); value['state'] = 'WAITING_FOR_WINDOWS'
        self.assertEqual(dict(status='PRESENTER_OPENED', presenterObserved=True, layoutComplete=False),
                         launch.surface_result(value))
        for change in ('missing', 'mixed-owner', 'geometry', 'zorder', 'locked'):
            value = surfaces()
            if change == 'missing': del value['surfaces']['header']
            if change == 'mixed-owner': value['surfaces']['header']['pid'] = 18
            if change == 'geometry': value['surfaces']['browser']['actual'][0] += 4
            if change == 'zorder': value['zOrder']['state'] = 'UNAVAILABLE'
            if change == 'locked': value = {'state': 'WAITING_FOR_UNLOCK'}
            with self.subTest(change=change):
                self.assertEqual('PRESENTER_NEEDS_ATTENTION', launch.surface_result(value)['status'])

    def test_minimal_spawn_environment_and_detached_lifetime(self):
        with patch.object(launch.subprocess, 'Popen') as spawn:
            launch.start(['pinned-python', '-I', '-B', 'fixed-entry', 'ui', 'serve'], Path('/private/tmp'))
        args = spawn.call_args.kwargs
        self.assertTrue(args['start_new_session'])
        self.assertEqual({'HOME', 'PATH', 'LC_ALL'}, set(args['env']))
        self.assertEqual(launch.subprocess.DEVNULL, args['stdin'])
        self.assertEqual(launch.subprocess.DEVNULL, args['stdout'])


class OwnershipTests(unittest.TestCase):
    def test_readiness_wait_never_restarts_or_submits(self):
        with patch.object(launch, 'owner', return_value=(3, 'start')), patch.object(launch, 'exchange',
                side_effect=[OSError('not yet serving'), {'buildId': 'expected'}]) as exchange, \
                patch.object(launch.time, 'sleep'), patch.object(launch, 'start') as start:
            self.assertEqual({'buildId': 'expected'}, launch.ready_client(['fixed'], (3, 'start')))
            start.assert_not_called()
            self.assertTrue(all(c.args == ('/api/presenter/client-state',) for c in exchange.call_args_list))
        with patch.object(launch, 'owner', return_value=(3, 'start')), patch.object(launch, 'exchange', side_effect=OSError()), \
                patch.object(launch.time, 'monotonic', side_effect=[0, 21]):
            with self.assertRaisesRegex(ValueError, 'START_UNCONFIRMED'):
                launch.ready_client(['fixed'], (3, 'start'))

    def test_no_redirect_to_another_endpoint(self):
        with self.assertRaisesRegex(ValueError, 'REDIRECT_FORBIDDEN'):
            launch.NoRedirect().redirect_request(None, None, 302, '', {}, 'https://elsewhere.invalid')

    def test_writer_covers_child_bind_gap_and_timeout_preserves_child(self):
        held = [False]
        @contextmanager
        def writer():
            held[0] = True
            try: yield
            finally: held[0] = False
        child = Mock(pid=19); child.poll.return_value = None
        def listener(port):
            self.assertTrue(held[0])
            return None
        with patch.object(launch, 'EnvironmentService') as env, patch.object(launch, 'owner', return_value=None), \
                patch.object(launch, 'listener', side_effect=listener), patch.object(launch, 'start', return_value=child) as start, \
                patch.object(launch.time, 'monotonic', side_effect=[0, 31]):
            env.return_value._writer.return_value = writer()
            with self.assertRaisesRegex(ValueError, 'START_UNCONFIRMED'):
                launch.ensure_server(['fixed'], Path('/tmp'), lambda _: None)
            start.assert_called_once(); child.terminate.assert_not_called(); child.kill.assert_not_called()
        self.assertFalse(held[0])

    def test_fixed_ports_absent_partial_different_and_exact(self):
        with patch.object(launch, 'listener', side_effect=[None, None]):
            self.assertIsNone(launch.owner(['fixed']))
        for ports in ([3, None], [None, 3], [3, 4]):
            with self.subTest(ports=ports), patch.object(launch, 'listener', side_effect=ports), \
                    self.assertRaisesRegex(ValueError, 'PORT_CONFLICT'):
                launch.owner(['fixed'])
        for uid, command in ((os.getuid()+1, 'fixed'), (os.getuid(), 'foreign')):
            with patch.object(launch, 'listener', return_value=3), patch.object(launch.subprocess, 'run',
                    return_value=SimpleNamespace(returncode=0, stderr='', stdout=f'{uid} {command}')):
                with self.assertRaisesRegex(ValueError, 'FOREIGN_OWNER'):
                    launch.owner(['fixed'])
        with patch.object(launch, 'listener', return_value=3), patch.object(launch.subprocess, 'run',
                side_effect=[SimpleNamespace(returncode=0, stderr='', stdout=f'{os.getuid()} fixed'),
                             SimpleNamespace(returncode=0, stderr='', stdout='Mon Sep 28 10:00:00 2026')]):
            self.assertEqual((3, 'Mon Sep 28 10:00:00 2026'), launch.owner(['fixed']))

    def test_unobservable_listener_does_not_mean_free(self):
        for code, out, err in ((0, '', ''), (1, '', 'denied'), (0, '2 3', ''), (0, 'not-pid', '')):
            with patch.object(launch.subprocess, 'run', return_value=SimpleNamespace(returncode=code, stdout=out, stderr=err)):
                with self.assertRaises(ValueError): launch.listener(18080)

    def test_first_repeat_and_foreign_start_are_bounded(self):
        child = Mock(pid=19); child.poll.return_value = None
        with patch.object(launch, 'EnvironmentService') as environment, patch.object(launch, 'owner',
                side_effect=[None, (19, 'start'), (19, 'start')]), \
                patch.object(launch, 'listener', return_value=19), patch.object(launch, 'start', return_value=child) as start:
            environment.return_value._writer.return_value = nullcontext()
            self.assertEqual(((19, 'start'), True), launch.ensure_server(['fixed'], Path('/tmp'), lambda _: None))
            start.assert_called_once()
        with patch.object(launch, 'EnvironmentService') as environment, patch.object(launch, 'owner', return_value=(19, 'start')), \
                patch.object(launch, 'start') as start:
            environment.return_value._writer.return_value = nullcontext()
            self.assertEqual(((19, 'start'), False), launch.ensure_server(['fixed'], Path('/tmp'), lambda _: None))
            start.assert_not_called()
        with patch.object(launch, 'EnvironmentService') as environment, patch.object(launch, 'owner', side_effect=ValueError('FOREIGN')), \
                patch.object(launch, 'start') as start:
            environment.return_value._writer.return_value = nullcontext()
            with self.assertRaisesRegex(ValueError, 'FOREIGN'):
                launch.ensure_server(['fixed'], Path('/tmp'), lambda _: None)
            start.assert_not_called()


class RestoreTests(unittest.TestCase):
    def exercise(self, *, lost=False, present=True, changed=False, result='COMPLETED'):
        calls = []
        def exchange(path, payload=None):
            calls.append((path, payload))
            if payload is not None:
                if lost: raise OSError('response lost, must not echo')
                return {'id': 'job-1', 'state': 'ACCEPTED'}
            value = snapshot()
            if len(calls) > 1:
                if changed: value['sessionId'] = 'different'
                if present: value['jobs'] = [dict(id='job-1', action='workspace-restore', state=result)]
            return value
        with patch.object(launch, 'exchange', side_effect=exchange), patch.object(launch, 'uuid4', return_value='job-1'), \
                patch.object(launch, 'owner', return_value=(3, 'started')), patch.object(launch.time, 'sleep'):
            try: launch.restore(['fixed'], (3, 'started'), lambda _: None)
            finally: self.assertEqual(1, sum(payload is not None for _, payload in calls))
        return calls

    def test_one_submission_and_read_only_reconciliation_after_lost_response(self):
        self.exercise()
        self.exercise(lost=True)
        self.exercise(result='PARTIAL')

    def test_uncertain_absent_or_changed_session_never_replays(self):
        for options in (dict(lost=True, present=False), dict(changed=True), dict(result='UNCERTAIN')):
            with self.subTest(options=options), self.assertRaises(ValueError): self.exercise(**options)

    def test_busy_prevents_submission(self):
        with patch.object(launch, 'exchange', return_value=snapshot() | {'active': 'other'}) as request:
            with self.assertRaisesRegex(ValueError, 'BUSY'): launch.restore(['fixed'], (3, 'start'), lambda _: None)
            request.assert_called_once_with(launch.OPERATIONS)


class ObservationTests(unittest.TestCase):
    def exercise(self, replies, statuses, *, clock=None):
        service = Mock()
        service.execute.side_effect = statuses
        with patch.object(launch, 'owner', return_value=(3, 'started')), \
                patch.object(launch, 'exchange', side_effect=replies) as exchange, \
                patch.object(launch.time, 'sleep'), \
                patch.object(launch.time, 'monotonic', side_effect=clock or [0] * 20):
            try:
                return launch.observe(service, ['fixed'], (3, 'started'), 'session-1')
            finally:
                self.assertTrue(all(c.args == (launch.OPERATIONS,) for c in exchange.call_args_list))
                self.assertTrue(all(c.args == ('status',) for c in service.execute.call_args_list))

    def test_layout_recovery_then_lock_race_only_repeats_observation(self):
        from aosedge_demo_orchestrator.environment import EnvironmentError
        result = self.exercise([snapshot() | {'workspaceBusy': True}, snapshot(), snapshot()],
                              [EnvironmentError('CURRENT_RUN_BUSY'), surfaces()])
        self.assertEqual(surfaces(), result)

    def test_new_operation_unknown_state_or_session_blocks_observation(self):
        for changes in ({'active': 'new'}, {'uncertain': True}, {'sourceRecoveryBusy': True},
                        {'workspaceBusy': None}, {'sessionId': 'another'}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.exercise([snapshot() | changes], [])

    def test_observation_wait_is_bounded(self):
        with self.assertRaisesRegex(ValueError, 'LAYOUT_UNCONFIRMED'):
            self.exercise([snapshot() | {'workspaceBusy': True}], [], clock=[0, 21])

    def test_first_incomplete_observation_can_settle_without_restore_replay(self):
        pending = surfaces(); pending['zOrder'] = {'state': 'UNAVAILABLE'}
        self.assertEqual(surfaces(), self.exercise([snapshot(), snapshot()], [pending, surfaces()]))

    def test_unconfirmed_geometry_stays_attention_at_deadline(self):
        pending = surfaces(); pending['surfaces']['browser']['actual'][0] += 20
        self.assertEqual(pending, self.exercise([snapshot()], [pending], clock=[0, 21]))

    def test_other_observation_errors_are_not_retried(self):
        from aosedge_demo_orchestrator.environment import EnvironmentError
        with self.assertRaisesRegex(EnvironmentError, 'WORKSPACE_ACCESSIBILITY_REQUIRED'):
            self.exercise([snapshot()], [EnvironmentError('WORKSPACE_ACCESSIBILITY_REQUIRED')])


class SelectedPackageTests(fixtures.SetupTests):
    # The inherited fixture tests continue to exercise the unchanged setup path.
    def test_real_absent_instance_is_actionable_without_creation(self):
        self.assertFalse(self.state.exists())
        with patch.object(fixtures.bridge, 'supported_platform'), \
                patch.object(fixtures.bridge, 'internal_volume'), \
                self.assertRaisesRegex(ValueError, '^SETUP_INSTANCE_NOT_FOUND$'):
            fixtures.bridge.perform(dict(action='launch', state=str(self.state)), self.f.pin)
        self.assertFalse(self.state.exists())

    def test_not_selected_cannot_launch_or_change_selection(self):
        self.run_action('install'); self.run_action('prepare')
        before = (self.state / fixtures.control.RECORD).read_bytes()
        with patch.object(launch, 'ensure_server') as server, self.assertRaisesRegex(ValueError, 'PREPARATION_REQUIRED'):
            launch.perform(dict(action='launch', state=str(self.state)), '0'*64)
        server.assert_not_called()
        self.assertEqual(before, (self.state / fixtures.control.RECORD).read_bytes())

    def test_corrupt_selected_code_blocks_before_execution(self):
        self.run_action('install'); self.run_action('prepare')
        program = self.f.target / 'versions' / self.f.pin / 'aosedge-sdv-demo'
        path = program / 'apps/demo-orchestrator/src/aosedge_demo_orchestrator/host_entry.py'
        raw = path.read_bytes(); path.chmod(0o644); path.write_bytes(b'X' + raw[1:]); path.chmod(0o444)
        with patch.object(launch.runtime_paths, 'volume_uuid', return_value=fixtures.fixtures.UUID), \
                patch.object(launch, 'ensure_server') as server, self.assertRaisesRegex(ValueError, 'DIGEST_MISMATCH'):
            launch.perform(dict(action='launch', state=str(self.state)), self.f.pin)
        server.assert_not_called()
