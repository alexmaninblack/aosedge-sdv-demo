# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts/qualification'))
import installed_scenarios as s
import remote_harness as h


def observed(**facts):
    return dict(schemaVersion=1, code='OBSERVED', stage='CONTROLLER_OBSERVATION',
                actionAttempted=False, facts=dict(installed=True, **facts),
                operationSeconds=0, observationSeconds=0.01)


class ScenarioTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve() / 'records'
        self.addCleanup(self.tmp.cleanup)
        self.target = dict(schemaVersion=1, manifestSha256='a' * 64,
            packageRoot='/Users/tester/AosEdge SDV Packages/versions/' + 'a' * 64,
            instanceRoot='/Users/tester/SDV-Lab-Data', localVmId='b449b383-8137-4086-a4bd-04075a3a3ef5')

    def test_bindings_private_and_paths_with_spaces(self):
        path = self.root.parent / 'target.json'
        path.write_text(json.dumps(self.target)); path.chmod(0o600)
        target, pin = s.target_configuration(path, dict(user='tester'))
        self.assertEqual(target, self.target)
        self.assertEqual(len(pin), 64)
        path.chmod(0o644)
        with self.assertRaises(h.Error):
            s.target_configuration(path, dict(user='tester'))

    def test_reject_target_traversal_overlap_or_wrong_digest(self):
        for key, value in (('instanceRoot', '/Users/tester/../other'),
                           ('instanceRoot', '/Users/tester/AosEdge SDV Packages'),
                           ('packageRoot', '/Users/tester/versions/' + 'b' * 64)):
            path = self.root.parent / 'target.json'
            path.write_text(json.dumps(dict(self.target, **{key: value}))); path.chmod(0o600)
            with self.assertRaises(h.Error):
                s.target_configuration(path, dict(user='tester'))

    def test_false_stopped_regression_is_detected(self):
        facts = dict(installed=True, controller='STOPPED', qmpRunning=True)
        self.assertFalse(s.satisfied('controller-running', facts))
        self.assertFalse(s.satisfied('controller-stopped', facts))
        self.assertFalse(s.satisfied('presenter-consistency', dict(facts, presenter='STOPPED')))

    def test_unknown_is_never_ready_or_stopped(self):
        for name in s.CHECKS[1:]:
            self.assertFalse(s.satisfied(name, dict(installed=True, controller='UNKNOWN')))

    def test_running_requires_qmp_and_backend_health(self):
        self.assertTrue(s.satisfied('controller-running', dict(installed=True, controller='RUNNING', qmpRunning=True)))
        self.assertFalse(s.satisfied('backends-running', dict(installed=True, brake='RUNNING', tire='RUNNING')))

    def test_baseline_stops_at_first_failure_and_preserves_prior_pass(self):
        with h.Journal(self.root, 'config') as journal:
            with patch.object(s, 'remote_observe') as observer:
                observer.side_effect = [observed(), observed(controller='STOPPED', qmpRunning=True)]
                rows = s.execute(journal, {}, self.target, 'target', 'verify', 'local-baseline', observer)
                self.assertEqual(len(rows), 2)
                self.assertEqual([r['outcome'] for r in rows], ['PASS', 'FAIL'])
                self.assertEqual(observer.call_count, 2)
        self.assertEqual(len(h.read_attempts(self.root)), 2)

    def test_uncertain_mutation_is_not_replayed_then_read_reconciles(self):
        with h.Journal(self.root, 'config') as journal:
            def lost(*args):
                raise h.Error('COMMAND_TIMEOUT')
            row = s.execute(journal, {}, self.target, 'target', 'action', 'vm-start', lost)[0]
            self.assertEqual(row['outcome'], 'UNCERTAIN')
            with self.assertRaisesRegex(h.Error, 'ACTION_RECONCILIATION_REQUIRED'):
                s.execute(journal, {}, self.target, 'target', 'action', 'vm-start', lost)
            calls = []
            def read(*args):
                calls.append(args[-2:])
                return observed(controller='RUNNING', qmpRunning=True)
            result = s.execute(journal, {}, self.target, 'target', 'reconcile', None, read)[0]
            self.assertEqual(result['outcome'], 'PASS')
            self.assertEqual(calls, [('verify', 'controller-powered')])
            self.assertFalse(s.unresolved(h.read_attempts(self.root)))
            self.assertEqual(h.read_attempts(self.root)[0]['outcome'], 'UNCERTAIN')

    def test_failed_reconciliation_does_not_clear_uncertainty(self):
        with h.Journal(self.root, 'config') as journal:
            s.attempt(journal, {}, self.target, 'target', 'action', 'vm-start',
                      lambda *a: dict(observed(), code='ACTION_UNCERTAIN', actionAttempted=True))
            s.execute(journal, {}, self.target, 'target', 'reconcile', None, lambda *a: observed(controller='UNKNOWN'))
            self.assertEqual(len(s.unresolved(h.read_attempts(self.root))), 1)
            with self.assertRaises(h.Error):
                s.execute(journal, {}, self.target, 'different', 'reconcile', None)

    def test_changed_candidate_or_harness_does_not_inherit_pass(self):
        with h.Journal(self.root, 'config') as journal:
            s.attempt(journal, {}, self.target, 'target', 'verify', 'installed', lambda *a: observed())
        rows = h.read_attempts(self.root)
        self.assertEqual(s.checkpoint(rows, 'target')['engineeringChecks']['installed'], 'PASS')
        self.assertEqual(s.checkpoint(rows, 'other')['engineeringChecks']['installed'], 'NOT_RUN')
        with patch.object(s, 'source_digest', return_value='changed'):
            self.assertEqual(s.checkpoint(rows, 'target')['engineeringChecks']['installed'], 'NOT_RUN')
        self.assertEqual(s.checkpoint(rows, 'target')['nativeAcceptance'], 'NOT_RUN')

    def test_unfinished_action_blocks_after_restart(self):
        with h.Journal(self.root, 'config') as journal:
            journal.begin('action:vm-start')
        with h.Journal(self.root, 'config') as journal:
            with self.assertRaises(h.Error):
                s.execute(journal, {}, self.target, 'target', 'action', 'vm-stop')

    def test_remote_uses_private_python_without_bytecode_and_rejects_extra_data(self):
        with patch.object(h, 'remote', return_value=json.dumps(observed())) as remote:
            s.remote_observe({}, self.target, 'verify', 'installed')
            self.assertIn(' -I -B - ', remote.call_args.args[1])
            self.assertIn("'" + self.target['packageRoot'], remote.call_args.args[1])
        for value in (dict(observed(), secret='do-not-log'), dict(observed(), facts={'secret': 'x'}),
                      dict(observed(), observationSeconds=float('nan'))):
            with patch.object(h, 'remote', return_value=json.dumps(value)):
                with self.assertRaises(h.Error):
                    s.remote_observe({}, self.target, 'verify', 'installed')

    def test_transport_details_are_not_persisted(self):
        with h.Journal(self.root, 'config') as journal:
            def failed(*args):
                raise ValueError('secret-value')
            s.attempt(journal, {}, self.target, 'target', 'verify', 'installed', failed)
        self.assertNotIn('secret-value', json.dumps(h.read_attempts(self.root)))

    def test_sequence_rechecks_current_state_and_skips_completed_actions(self):
        calls = []
        def ready(*args):
            calls.append(args[-2:])
            return observed(controller='RUNNING', qmpRunning=True, brake='RUNNING', tire='RUNNING',
                            brakeHealthy=True, tireHealthy=True)
        with h.Journal(self.root, 'config') as journal:
            rows = s.execute(journal, {}, self.target, 'target', 'run', 'local-start', ready)
            again = s.execute(journal, {}, self.target, 'target', 'run', 'local-start', ready)
        self.assertTrue(all(kind == 'verify' for kind, _ in calls))
        self.assertEqual(len(rows), len(again))
        self.assertEqual(again[-1]['outcome'], 'PASS')

    def test_sequence_uncertain_read_never_starts_mutation(self):
        calls = []
        def read(*args):
            calls.append(args[-2:])
            if args[-1] == 'installed':
                return observed()
            return dict(observed(), code='INSTALLED_PROBE_BLOCKED')
        with h.Journal(self.root, 'config') as journal:
            rows = s.execute(journal, {}, self.target, 'target', 'run', 'local-start', read)
        self.assertEqual(rows[-1]['outcome'], 'BLOCKED')
        self.assertTrue(all(kind == 'verify' for kind, _ in calls))

    def test_unknown_process_read_is_not_an_action_precondition(self):
        self.assertFalse(s.known_action_precondition('vm-start', {'controller': 'UNKNOWN', 'qmpRunning': None}))
        self.assertFalse(s.known_action_precondition('backends-stop', {'brake': 'RUNNING', 'tire': 'UNKNOWN'}))


if __name__ == '__main__':
    unittest.main()
