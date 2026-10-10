# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Offline one-run fixtures: local Git only; no installers, builds or network."""
import contextlib
import fcntl
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import developer_bootstrap as bootstrap
import developer_build as workflow


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir='/private/tmp' if sys.platform == 'darwin' else None)
        self.addCleanup(self.tmp.cleanup)
        self.parent = Path(self.tmp.name)
        self.root = self.parent/'workspace with spaces'
        self.control = self.root/'.developer-preparation'
        self.control.mkdir(parents=True)
        (self.control/'.aosedge-preparation').write_text('aosedge-developer-preparation-v1\n')
        self.origin = self.parent/'fixture-origin'
        self.origin.mkdir()
        self.local('init', '--quiet', '--initial-branch=main')
        (self.origin/'scripts').mkdir()
        (self.origin/'scripts/developer_build.py').write_text('# offline fixture only\n')
        (self.origin/'lock.json').write_text('{}')
        self.local('add', '.')
        self.local('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '--quiet', '-m', 'fixture')
        self.revision = self.local('rev-parse', 'HEAD')
        self.requirements = self.parent/'requirements.json'
        self.requirements.write_text(json.dumps({'sourceFiles': {'lock.json': hashlib.sha256(b'{}').hexdigest()}}))
        self.real_git = bootstrap.git
        self.fetches = 0
        self.fail_fetch = False
        self.addCleanup(patch.stopall)
        patch.object(bootstrap, 'git', side_effect=self.git).start()

    def local(self, *args, cwd=None):
        return subprocess.check_output(['git', '-c', 'core.hooksPath=/dev/null', *args],
                                       cwd=cwd or self.origin, stderr=subprocess.DEVNULL, text=True).strip()

    def git(self, directory, *args, **kwargs):
        if args[0] == 'ls-remote':
            return self.local('rev-parse', 'HEAD')+'\trefs/heads/main'
        if args[0] == 'fetch':
            self.fetches += 1
            if self.fail_fetch:
                # Emulate interrupted Git creating an empty FETCH_HEAD.
                (Path(directory)/'.git/FETCH_HEAD').write_text('')
                raise bootstrap.WorkflowError('fixture network interruption')
            return self.local('fetch', '--quiet', str(self.origin), args[-1], cwd=directory)
        return self.real_git(directory, *args, **kwargs)

    def run_checkout(self):
        with contextlib.redirect_stdout(io.StringIO()):
            return bootstrap.checkout(self.root, 'fixture-volume', self.requirements)

    def test_first_repeat_and_moving_main_keep_one_revision(self):
        first = self.run_checkout()
        self.local('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '--quiet', '--allow-empty', '-m', 'new main')
        second = self.run_checkout()
        self.assertEqual(first, second)
        self.assertEqual(first['revision'], self.revision)
        self.assertEqual(self.fetches, 1)
        self.assertFalse((self.control/'source.partial').exists())

    def test_interrupted_fetch_resumes_original_selection(self):
        self.fail_fetch = True
        with self.assertRaisesRegex(bootstrap.WorkflowError, 'interruption'):
            self.run_checkout()
        self.assertTrue((self.control/'root-source.json').exists())
        self.local('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '--quiet', '--allow-empty', '-m', 'new')
        self.fail_fetch = False
        self.assertEqual(self.run_checkout()['revision'], self.revision)

    def test_changed_source_is_never_reset(self):
        self.run_checkout()
        (self.root/'source/lock.json').write_text('user changes')
        with self.assertRaisesRegex(bootstrap.WorkflowError, 'local changes'):
            self.run_checkout()
        self.assertEqual((self.root/'source/lock.json').read_text(), 'user changes')

    def test_changed_revision_rejected_without_pull(self):
        self.run_checkout()
        self.local('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '--quiet', '--allow-empty', '-m', 'user commit', cwd=self.root/'source')
        with self.assertRaisesRegex(bootstrap.WorkflowError, 'revision changed'):
            self.run_checkout()
        self.assertEqual(self.fetches, 1)

    def test_foreign_checkout_is_not_adopted(self):
        self.run_checkout()
        (self.control/'root-source.json').unlink()
        self.local('remote', 'set-url', 'origin', 'https://example.invalid/foreign.git', cwd=self.root/'source')
        with self.assertRaisesRegex(bootstrap.WorkflowError, 'different repository'):
            self.run_checkout()

    def test_clean_manual_b2_checkout_is_reused(self):
        self.run_checkout()
        (self.control/'root-source.json').unlink()
        self.assertEqual(self.run_checkout()['revision'], self.revision)
        self.assertEqual(self.fetches, 1)

    def test_volume_and_requirement_changes_are_rejected(self):
        self.run_checkout()
        with self.assertRaisesRegex(bootstrap.WorkflowError, 'another volume'):
            bootstrap.checkout(self.root, 'replacement-volume', self.requirements)
        self.requirements.write_text(json.dumps({'sourceFiles': {'lock.json': '0'*64}}))
        with self.assertRaisesRegex(bootstrap.WorkflowError, 'another volume/release'):
            self.run_checkout()

    def test_unowned_partial_and_link_collisions_are_preserved(self):
        partial = self.control/'source.partial'
        partial.mkdir()
        with self.assertRaisesRegex(bootstrap.WorkflowError, 'Unowned partial'):
            self.run_checkout()
        partial.rmdir()
        (self.root/'source').symlink_to(self.origin)
        with self.assertRaisesRegex(bootstrap.WorkflowError, 'linked'):
            self.run_checkout()

    def test_source_mismatch_never_promotes_checkout(self):
        self.requirements.write_text(json.dumps({'sourceFiles': {'lock.json': '0'*64}}))
        with self.assertRaisesRegex(bootstrap.WorkflowError, 'requirements differ'):
            self.run_checkout()
        self.assertFalse((self.root/'source').exists())
        self.assertTrue((self.control/'source.partial').exists())

    def test_active_workspace_owner_prevents_second_bootstrap(self):
        with (self.control/'workflow.lock').open('w') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            with self.assertRaisesRegex(bootstrap.WorkflowError, 'Another source/build'):
                self.run_checkout()
        self.assertFalse((self.control/'root-source.json').exists())


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir='/private/tmp' if sys.platform == 'darwin' else None)
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.control = self.root/'.developer-preparation'
        self.control.mkdir()
        (self.control/'root-source.json').write_text(json.dumps({'revision': 'a'*40, 'volumeUUID': 'fixture-volume'}))
        self.binding = self.root/'binding.json'
        self.binding.write_text('{"schemaVersion":2}')
        self.config = {name: '/fixture/'+name for name in ('SDV_PYTHON', 'SDV_NODE', 'SDV_NPM', 'SDV_CMAKE', 'SDV_DOCKER',
            'SDV_SIGNING_IDENTITY', 'SDV_TMP', 'SDV_SIM_BINDING', 'SDV_PREPARED_SOURCE')}
        self.config.update(SDV_ROOT=str(self.root), SDV_WORKFLOW_VOLUME='fixture-volume', SDV_BUILD_BINDING=str(self.binding),
                           SDV_DRIVE_ACCOUNT='', SDV_GCLOUD='')
        self.paths = {k: str(self.root/'inputs'/k) for k in ('kitInputs', 'gatewaySdk', 'factoryInputs')}
        for path in self.paths.values(): Path(path).mkdir(parents=True)
        self.calls = []
        self.fail = None
        self.addCleanup(patch.stopall)
        patch.object(workflow, 'validate_checkout', return_value='a'*40).start()
        patch.object(workflow, 'source_check').start()

    def owner(self, label, args):
        args = list(map(str, args))
        self.calls.append(args)
        if args[:2] == self.fail:
            raise bootstrap.WorkflowError('fixture failure')
        if args[0] == 'plan': return {'profile': 'developer', 'orderedDeveloperChain': {'fixture': True}}
        if args[:2] == ['inputs', 'plan']: return {'archiveBytes': 123, 'unpackedBytes': 456}
        if args[:2] == ['inputs', 'prepare']: return {'status': 'BUILD_INPUTS_READY_NOT_PROFILE_QUALIFIED', **self.paths}
        if args[0] == 'build': return {'status': 'CHAIN_BUILT_NOT_QUALIFIED', 'chainKey': 'b'*64}
        return {'status': 'fixture'}

    def execute(self):
        with contextlib.redirect_stdout(io.StringIO()) as screen:
            workflow.execute(self.config, self.owner, resolve=lambda *a: ('/fixture/result.dmg', '/fixture/receipt.json'),
                             expose=lambda *a: str(self.root/'output/result.dmg'))
        return screen.getvalue()

    def test_complete_sequence_and_repeat_delegate_to_canonical_owners(self):
        output = self.execute()
        first = self.calls[:]
        self.calls.clear()
        self.execute()
        self.assertEqual(first, self.calls)
        self.assertEqual([a[0] for a in first], ['plan', 'inputs', 'space', 'prepare', 'verify', 'space', 'inputs', 'space', 'build'])
        self.assertNotIn('--account', first[6])
        self.assertIn('--docker', first[2])
        for args in first:
            if '--build-plan' in args:
                self.assertEqual(args[args.index('--build-plan')+1], str(self.root/'source'/workflow.PLAN))
        self.assertIn('--prepare-dependencies', first[-1])
        self.assertNotIn('--resume', first[-1])
        self.assertIn('not release-qualified', output)
        self.assertIn(str(self.root/'output/result.dmg'), output)
        self.assertNotIn('/fixture/receipt.json', output)
        state = json.loads((self.control/'workflow.json').read_text())
        self.assertEqual(state['status'], 'CHAIN_BUILT_NOT_QUALIFIED')

    def test_failure_stops_before_downstream_work_and_repeat_rechecks(self):
        self.fail = ['inputs', 'prepare']
        with self.assertRaisesRegex(bootstrap.WorkflowError, 'fixture failure'): self.execute()
        self.assertFalse(any(a[0] == 'build' for a in self.calls))
        self.assertEqual(json.loads((self.control/'workflow.json').read_text())['status'], 'STOPPED')
        self.fail = None
        self.execute()
        self.assertEqual(sum(a[0] == 'build' for a in self.calls), 1)

    def test_storage_gate_precedes_source_and_archive_acquisition(self):
        self.fail = ['space', '--storage']
        with self.assertRaisesRegex(bootstrap.WorkflowError, 'fixture failure'): self.execute()
        self.assertFalse(any(a[0] in ('prepare', 'build') or a[:2] == ['inputs', 'prepare'] for a in self.calls))

    def test_failed_host_preparation_cannot_invoke_continuation(self):
        with self.assertRaisesRegex(bootstrap.WorkflowError, 'incomplete'):
            workflow.configuration({'SDV_ROOT': str(self.root)})

    def test_malformed_build_success_cannot_be_reported_complete(self):
        def reject(*args): raise bootstrap.WorkflowError('Incomplete chain receipt')
        with self.assertRaisesRegex(bootstrap.WorkflowError, 'Incomplete'), contextlib.redirect_stdout(io.StringIO()):
            workflow.execute(self.config, self.owner, resolve=reject)
        self.assertEqual(json.loads((self.control/'workflow.json').read_text())['status'], 'STOPPED')

    def test_unsafe_input_result_never_reaches_build(self):
        self.paths['factoryInputs'] = '/outside-workspace'
        with self.assertRaisesRegex(bootstrap.WorkflowError, 'outside'): self.execute()
        self.assertFalse(any(a[0] == 'build' for a in self.calls))

    def test_private_mode_forwards_only_explicit_account_and_cli(self):
        self.binding.write_text('{"schemaVersion":1}')
        with self.assertRaisesRegex(bootstrap.WorkflowError, 'private input access'): self.execute()
        self.config.update(SDV_DRIVE_ACCOUNT='fixture@example.invalid', SDV_GCLOUD='/fixture/gcloud')
        self.execute()
        args = next(a for a in self.calls if a[:2] == ['inputs', 'prepare'])
        self.assertIn('--account', args)
        self.assertIn('--gcloud', args)

    def test_cancellation_records_stop(self):
        def cancelled(*args): raise KeyboardInterrupt
        with self.assertRaises(KeyboardInterrupt), contextlib.redirect_stdout(io.StringIO()):
            workflow.execute(self.config, cancelled)
        self.assertEqual(json.loads((self.control/'workflow.json').read_text())['status'], 'STOPPED')

    def test_owner_failure_and_space_explanation(self):
        import reproduction.cli
        def fake(args):
            print(json.dumps({'status': 'SPACE_REPORT', 'producerStorageCompatibility': {'compatible': False}}))
            return 2
        with patch.object(reproduction.cli, 'main', side_effect=fake):
            with self.assertRaisesRegex(bootstrap.WorkflowError, 'successor build plan'):
                workflow.Owner(self.control)('space', ['space'])

    def test_docker_failure_is_not_reported_as_insufficient_capacity(self):
        reason = workflow.failure_reason({'status': 'SPACE_REPORT', 'fitsCheckedPools': True,
            'dockerStorage': {'status': 'BLOCKED', 'reason': 'Reported volume differs from selected storage'}})
        self.assertIn('Docker storage check failed', reason)
        self.assertIn('Reported volume differs', reason)
        self.assertNotIn('Insufficient capacity', reason)

    def test_output_filters_raw_json_but_preserves_log(self):
        log, screen = io.StringIO(), io.StringIO()
        output = workflow.OwnerOutput(log, screen)
        output.write('{"event":"CHAIN_STEP","detail":"gateway"}\n')
        output.write('{"status":"CHAIN_BUILT_NOT_QUALIFIED"}\n')
        self.assertEqual(output.last['status'], 'CHAIN_BUILT_NOT_QUALIFIED')
        self.assertIn('Vehicle Gateway', screen.getvalue())
        self.assertNotIn('status', screen.getvalue())
        self.assertIn('status', log.getvalue())

    def test_dmg_resolution_requires_exact_chain_and_one_output(self):
        from reproduction.core import digest
        from reproduction import media
        chain_key = 'c'*64
        inputs = {'fixture': True}
        key = digest(inputs)
        build = self.root/'build'
        (build/'builds/chains').mkdir(parents=True)
        record = build/'builds/chains'/(chain_key+'.json')
        record.write_text(json.dumps({'status': 'CHAIN_BUILT_NOT_QUALIFIED', 'completed': {'media': key}}))
        (build/'preparation.json').write_text(json.dumps({'builds': {key: {'target': 'dmg', 'inputs': inputs}}}))
        result = {'status': 'CHAIN_BUILT_NOT_QUALIFIED', 'chainKey': chain_key}
        with patch.object(media, 'verify', return_value={'stamps': {'exact.dmg': {}}}):
            path, receipt = workflow.resolve_dmg(build, result)
            self.assertEqual(Path(path).name, 'exact.dmg')
            self.assertEqual(receipt, str(record))
        with patch.object(media, 'verify', return_value={'stamps': {'one.dmg': {}, 'two.dmg': {}}}):
            with self.assertRaisesRegex(bootstrap.WorkflowError, 'one DMG'):
                workflow.resolve_dmg(build, result)


if __name__ == '__main__':
    unittest.main()
