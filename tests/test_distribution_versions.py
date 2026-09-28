# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Nonexecuting package fixtures; no actual Cloud, VM, Docker or simulator."""

import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import test_distribution_installation as fixtures
with patch.object(sys, 'path', [str(fixtures.SCRIPTS), *sys.path]):
    from version_management import Versions, repair, main, control
from aosedge_demo_orchestrator import runtime_paths

UUID, OTHER = fixtures.UUID, fixtures.OTHER


class VersionTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix='versions.', dir='/tmp')
        self.addCleanup(directory.cleanup)
        self.short = Path(directory.name).resolve()
        fixture = fixtures.InstallationTests()
        fixture.addCleanup = self.addCleanup
        fixture.setUp()
        self.fixture = fixture
        fixture.manifest['installedStateContract'] = control.CONTRACT
        fixture.rewrite_manifest()
        fixture.install()
        self.store = fixture.store
        self.state = self.short / 'state'
        self.identity = runtime_paths.create_instance(self.state)['instanceId']
        self.versions = Versions(self.store, self.state)
        self.pin1 = fixture.pin
        self.app = self.store.root / 'versions' / self.pin1 / 'aosedge-sdv-demo'
        self.native = patch.object(control, 'unused')
        self.native.start(); self.addCleanup(self.native.stop)
        self.volume = patch.object(runtime_paths, 'volume_uuid', return_value=UUID)
        self.volume.start(); self.addCleanup(self.volume.stop)
        self.variables = patch.dict(os.environ, {}, clear=True)
        self.variables.start(); self.addCleanup(self.variables.stop)
        self.sentinel = self.state / '.local/release-continuity.json'
        self.sentinel.write_text('{"schemaVersion":1,"versions":{"vdp":"123.0.0"}}')
        self.before = self.sentinel.read_bytes()

    def new_version(self, contract=control.CONTRACT):
        self.fixture.manifest['installedStateContract'] = contract
        self.fixture.manifest['fixtureVersion'] = 2
        self.fixture.rewrite_manifest()
        self.fixture.install()
        return self.fixture.pin

    def selected(self):
        return self.versions.change('select', 0, self.pin1)

    def record(self):
        return (self.state / control.RECORD).read_bytes()

    def damage(self):
        path = self.app / 'LICENSE'
        path.chmod(0o644)
        path.write_bytes(b'broken program')
        path.chmod(0o444)

    def fix(self, **options):
        return repair(self.store, self.fixture.source, self.pin1, copier=self.fixture.copy, **options)

    def test_first_repeat_status_and_restart(self):
        self.assertEqual(self.versions.status()['revision'], 0)
        result = self.selected()
        self.assertEqual((result['status'], result['revision']), ('SELECTED_NOT_STARTED', 1))
        before = self.record()
        again = Versions(self.store, self.state).change('select', 1, self.pin1)
        self.assertTrue(again['reused'])
        self.assertEqual(before, self.record())
        self.assertEqual(self.before, self.sentinel.read_bytes())

    def test_managed_runtime_requires_existing_instance_lock(self):
        self.selected()
        lock = self.state / control.LOCK
        lock.unlink()
        with self.assertRaises(FileNotFoundError):
            with runtime_paths.installed_session(self.state, _program=self.app):
                self.fail('missing managed lock accepted')
        self.assertFalse(lock.exists())

    def test_update_rollback_unselect_preserves_data_and_both_versions(self):
        self.selected()
        pin2 = self.new_version()
        self.assertEqual(self.versions.change('select', 1, pin2)['previous'], self.pin1)
        self.assertEqual(self.versions.change('rollback', 2)['current'], self.pin1)
        result = self.versions.change('unselect', 3)
        self.assertEqual(result['status'], 'UNSELECTED_DATA_RETAINED')
        self.assertEqual(result['bytesFreed'], 0)
        self.assertEqual(self.versions.change('rollback', 4)['current'], self.pin1)
        self.assertEqual(self.before, self.sentinel.read_bytes())
        self.assertTrue((self.store.root / 'versions' / pin2).is_dir())
        self.assertTrue(self.app.is_dir())

    def test_stale_action_never_overwrites_new_choice(self):
        self.selected(); before = self.record()
        with self.assertRaisesRegex(ValueError, 'STALE_REVISION'):
            self.versions.change('unselect', 0)
        self.assertEqual(self.record(), before)

    def test_no_predecessor_cannot_guess_a_rollback(self):
        self.selected(); self.new_version()
        with self.assertRaisesRegex(ValueError, 'ROLLBACK_NOT_AVAILABLE'):
            self.versions.change('rollback', 1)

    def test_revision_exhaustion_keeps_a_readable_selection(self):
        self.selected()
        value = json.loads(self.record())
        value['revision'] = 2**53 - 1
        control.commit_selection(self.state, value)
        before = self.record()
        with self.assertRaisesRegex(ValueError, 'REVISION_EXHAUSTED'):
            self.versions.change('unselect', value['revision'])
        self.assertEqual(self.record(), before)
        self.assertEqual(self.versions.status()['revision'], value['revision'])

    def test_incompatible_and_undeclared_version_block(self):
        self.selected(); before = self.record()
        for contract in ('future/2', None):
            with self.subTest(contract=contract):
                pin2 = self.new_version(contract)
                with self.assertRaisesRegex(ValueError, 'COMPATIBILITY_UNSUPPORTED'):
                    self.versions.change('select', 1, pin2)
                self.assertEqual(self.record(), before)

    def test_new_runtime_requires_explicit_matching_selection(self):
        with self.assertRaisesRegex(ValueError, 'VERSION_NOT_SELECTED'):
            with runtime_paths.installed_session(self.state, _program=self.app):
                pass
        self.selected()
        with runtime_paths.installed_session(self.state, _program=self.app):
            self.assertEqual(runtime_paths.state_root(), self.state)
        pin2 = self.new_version()
        self.versions.change('select', 1, pin2)
        with self.assertRaisesRegex(ValueError, 'VERSION_NOT_SELECTED'):
            with runtime_paths.installed_session(self.state, _program=self.app):
                pass

    def test_runtime_lease_prevents_selection_and_repair(self):
        self.selected()
        with runtime_paths.installed_session(self.state, _program=self.app):
            with self.assertRaisesRegex(ValueError, 'IN_USE'):
                self.versions.change('unselect', 1)
            self.damage()
            with self.assertRaisesRegex(ValueError, 'IN_USE'):
                self.fix()
        self.assertEqual(self.versions.status()['current'], self.pin1)

    def test_exclusive_manager_lease_blocks_runtime(self):
        self.selected()
        with control.lease(self.state / control.LOCK, exclusive=True):
            with self.assertRaisesRegex(ValueError, 'IN_USE'):
                with runtime_paths.installed_session(self.state, _program=self.app):
                    pass

    def test_retained_journal_or_overlay_blocks_without_erasing_it(self):
        self.selected(); before = self.record()
        for relative in ('.run/demo-current/journal.json', '.local/demo-current'):
            path = self.state / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('retained data')
            with self.assertRaisesRegex(ValueError, 'CURRENT_RUN_RETAINED'):
                self.versions.change('unselect', 1)
            self.assertEqual(path.read_text(), 'retained data')
            self.assertEqual(self.record(), before)
            path.unlink()  # Owned fixture only, not a product recovery action.

    def test_unknown_native_usage_leaves_selection_unchanged(self):
        self.selected(); before = self.record()
        with patch.object(control, 'unused', side_effect=ValueError('INSTALLED_USAGE_UNKNOWN')):
            with self.assertRaisesRegex(ValueError, 'USAGE_UNKNOWN'):
                self.versions.change('unselect', 1)
        self.assertEqual(self.record(), before)

    def test_wrong_volume_and_foreign_store_block(self):
        self.selected(); before = self.record()
        self.fixture.volume = OTHER
        with self.assertRaisesRegex(ValueError, 'VOLUME_CHANGED'):
            self.versions.change('unselect', 1)
        self.assertEqual(self.record(), before)

    def test_failed_atomic_commit_preserves_prior_selection(self):
        self.selected(); before = self.record()
        with patch.object(control.os, 'replace', side_effect=OSError('fixture')):
            with self.assertRaises(OSError):
                self.versions.change('unselect', 1)
        self.assertEqual(self.record(), before)
        result = self.versions.change('unselect', 1)
        self.assertEqual(result['revision'], 2)
        self.assertEqual(self.before, self.sentinel.read_bytes())

    def test_corrupted_selection_cannot_be_overwritten(self):
        self.selected()
        (self.state / control.RECORD).write_text('{"schemaVersion":2}')
        with self.assertRaisesRegex(ValueError, 'SELECTION_INVALID'):
            self.versions.change('select', 0, self.pin1)

    def test_symlink_lock_never_follows_or_overwrites_target(self):
        target = self.short / 'unrelated'
        target.write_text('preserve')
        (self.state / control.LOCK).symlink_to(target)
        with self.assertRaises(ValueError):
            self.selected()
        self.assertEqual(target.read_text(), 'preserve')

    def test_repair_preserves_corrupt_original_and_selection(self):
        self.selected(); before = self.record(); self.damage()
        result = self.fix()
        self.assertEqual(result['status'], 'REPAIRED_PROGRAM_ONLY')
        saved = self.store.root / 'quarantine' / self.pin1 / 'original/aosedge-sdv-demo/LICENSE'
        self.assertEqual(saved.read_bytes(), b'broken program')
        self.assertNotEqual((self.app / 'LICENSE').read_bytes(), b'broken program')
        self.assertEqual(before, self.record())
        self.assertEqual(self.before, self.sentinel.read_bytes())
        self.assertTrue(self.fix()['reused'])

    def test_healthy_repair_is_verification_only(self):
        self.assertEqual(self.fix()['status'], 'PROGRAM_VERIFIED_NO_REPAIR')
        self.assertFalse((self.store.root / 'quarantine').exists())

    def test_interruption_before_repair_record_blocks_runtime(self):
        self.selected(); self.damage()
        with patch('version_management.atomic_record', side_effect=OSError('fixture record failure')):
            with self.assertRaises(OSError):
                self.fix()
        self.assertTrue((self.store.root / 'quarantine' / self.pin1).is_dir())
        with self.assertRaisesRegex(ValueError, 'REPAIR_RECONCILIATION_REQUIRED'):
            with runtime_paths.installed_session(self.state, _program=self.app):
                pass
        self.assertEqual(self.before, self.sentinel.read_bytes())
        self.assertEqual(self.fix()['status'], 'REPAIRED_PROGRAM_ONLY')
        self.assertEqual(self.before, self.sentinel.read_bytes())

    def test_interrupted_initial_repair_record_rename_is_resumable(self):
        self.selected(); self.damage()
        with patch('installation.os.replace', side_effect=OSError('fixture rename failure')):
            with self.assertRaises(OSError):
                self.fix()
        with self.assertRaisesRegex(ValueError, 'REPAIR_RECONCILIATION_REQUIRED'):
            with runtime_paths.installed_session(self.state, _program=self.app):
                pass
        self.assertEqual(self.fix()['status'], 'REPAIRED_PROGRAM_ONLY')
        self.assertEqual(self.before, self.sentinel.read_bytes())

    def test_unrecognized_pre_record_repair_content_is_not_removed(self):
        self.selected(); self.damage()
        with patch('version_management.atomic_record', side_effect=OSError('fixture record failure')):
            with self.assertRaises(OSError):
                self.fix()
        foreign = self.store.root / 'quarantine' / self.pin1 / 'unknown'
        foreign.write_bytes(b'preserve')
        with self.assertRaisesRegex(ValueError, 'REPAIR_WORK_UNRECOGNIZED'):
            self.fix()
        self.assertEqual(foreign.read_bytes(), b'preserve')

    def test_interrupted_repair_reconciles_without_losing_original(self):
        self.selected(); self.damage()
        def fail(stage):
            if stage == self.interrupt_at:
                raise OSError('simulated interruption')
        self.interrupt_at = 'AFTER_ORIGINAL_MOVE'
        with self.assertRaises(OSError):
            self.fix(checkpoint=fail)
        self.assertFalse(self.app.exists())
        self.assertEqual(self.fix()['status'], 'REPAIRED_PROGRAM_ONLY')
        self.assertEqual(self.before, self.sentinel.read_bytes())

    def test_interruption_before_original_move_preserves_old_bytes(self):
        self.selected(); self.damage()
        def fail(stage):
            if stage == 'BEFORE_ORIGINAL_MOVE':
                raise OSError('simulated interruption')
        with self.assertRaises(OSError):
            self.fix(checkpoint=fail)
        self.assertEqual((self.app / 'LICENSE').read_bytes(), b'broken program')
        self.assertEqual(self.fix()['status'], 'REPAIRED_PROGRAM_ONLY')

    def test_interrupted_copy_leaves_current_package_in_place(self):
        self.selected(); self.damage()
        def fail(source, target):
            target.write_bytes(b'partial')
            raise OSError('simulated copy failure')
        with self.assertRaises(OSError):
            repair(self.store, self.fixture.source, self.pin1, copier=fail)
        self.assertEqual((self.app / 'LICENSE').read_bytes(), b'broken program')
        self.assertEqual(self.fix()['status'], 'REPAIRED_PROGRAM_ONLY')

    def test_after_promotion_before_receipt_blocks_runtime_until_reconcile(self):
        self.selected(); self.damage()
        def fail(stage):
            if stage == 'AFTER_REPLACEMENT_MOVE':
                raise OSError('simulated receipt gap')
        with self.assertRaises(OSError):
            self.fix(checkpoint=fail)
        with self.assertRaisesRegex(ValueError, 'REPAIR_RECONCILIATION_REQUIRED'):
            with runtime_paths.installed_session(self.state, _program=self.app):
                pass
        self.fix()
        with runtime_paths.installed_session(self.state, _program=self.app):
            pass

    def test_bad_source_cannot_replace_damaged_package(self):
        self.damage()
        source = self.fixture.source / 'aosedge-sdv-demo/LICENSE'
        source.chmod(0o644); source.write_bytes(b'bad source'); source.chmod(0o444)
        with self.assertRaises(ValueError):
            self.fix()
        self.assertEqual((self.app / 'LICENSE').read_bytes(), b'broken program')
        self.assertFalse((self.store.root / 'quarantine').exists())

    def test_second_damaged_generation_is_not_overwritten(self):
        self.damage(); self.fix(); self.damage()
        with self.assertRaises(ValueError):
            self.fix()
        original = self.store.root / 'quarantine' / self.pin1 / 'original/aosedge-sdv-demo/LICENSE'
        self.assertEqual(original.read_bytes(), b'broken program')

    def test_cli_redacts_filesystem_errors(self):
        with patch('version_management.Store', side_effect=OSError('private path fixture')), \
                patch('sys.stdout', new_callable=io.StringIO) as output:
            code = main(['status', '--store', str(self.store.root), '--volume-uuid', UUID,
                         '--instance-root', str(self.state)])
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(output.getvalue())['reason'], 'VERSION_IO_UNAVAILABLE')


class NativeGuardTests(unittest.TestCase):
    @unittest.skipUnless(os.environ.get('RUN_INSTALLED_PROCESS_GUARD') == '1', 'explicit local process-inspection proof')
    def test_live_detached_consumer_blocks_without_a_runtime_lease(self):
        with tempfile.TemporaryDirectory(dir='/tmp', prefix='native-use.') as directory:
            root = Path(directory).resolve()
            path = root / 'native-owned'
            path.write_text('fixture')
            code = 'import sys,time; f=open(sys.argv[1]); print("open",flush=True); time.sleep(20)'
            process = subprocess.Popen([sys.executable, '-I', '-B', '-c', code, str(path)],
                                       stdout=subprocess.PIPE, text=True)
            try:
                self.assertEqual(process.stdout.readline().strip(), 'open')
                with self.assertRaisesRegex(ValueError, 'NATIVE_CONSUMER_ACTIVE'):
                    control.unused((root,))
            finally:
                process.terminate(); process.wait(timeout=5); process.stdout.close()
            control.unused((root,))

    def test_exact_descendant_not_sibling_name_blocks(self):
        base = Path('/private/tmp/owned-instance')
        for name, blocked in ((str(base / 'file'), True), (str(base) + '-another/file', False)):
            with self.subTest(name=name), patch.object(control.subprocess, 'run', return_value=
                subprocess.CompletedProcess([], 0, ('p999999\nn' + name + '\n').encode(), b'')):
                if blocked:
                    with self.assertRaisesRegex(ValueError, 'NATIVE_CONSUMER_ACTIVE'):
                        control.unused((base,))
                else:
                    control.unused((base,))

    def test_failed_empty_or_warning_scan_is_unknown(self):
        for response in (subprocess.CompletedProcess([], 1, b'', b''),
                         subprocess.CompletedProcess([], 0, b'', b''),
                         subprocess.CompletedProcess([], 0, b'p999999\n', b'warning')):
            with patch.object(control.subprocess, 'run', return_value=response):
                with self.assertRaisesRegex(ValueError, 'USAGE_UNKNOWN'):
                    control.unused((Path('/private/tmp/owned'),))

    def test_real_cross_process_shared_lease_blocks_writer(self):
        with tempfile.TemporaryDirectory(dir='/tmp') as directory:
            path = Path(directory).resolve() / 'lease'
            path.touch(mode=0o600)
            code = 'import fcntl,sys,time; f=open(sys.argv[1]); fcntl.flock(f,fcntl.LOCK_SH); print("leased",flush=True); time.sleep(20)'
            process = subprocess.Popen([sys.executable, '-I', '-B', '-c', code, str(path)],
                                       stdout=subprocess.PIPE, text=True)
            try:
                self.assertEqual(process.stdout.readline().strip(), 'leased')
                with self.assertRaisesRegex(ValueError, 'IN_USE'):
                    with control.lease(path, exclusive=True):
                        pass
            finally:
                process.terminate(); process.wait(timeout=5); process.stdout.close()
            with control.lease(path, exclusive=True):
                pass


if __name__ == '__main__':
    unittest.main()
