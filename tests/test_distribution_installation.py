# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Offline fixtures for the installer; no payload execution or live resources."""

import hashlib
import importlib.util
import json
import os
import plistlib
from pathlib import Path
import shutil
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1]/'scripts/distribution'
with patch.object(sys, 'path', [str(SCRIPTS), *sys.path]):
    SPEC = importlib.util.spec_from_file_location('distribution_installation', SCRIPTS/'installation.py')
    module = importlib.util.module_from_spec(SPEC)
    SPEC.loader.exec_module(module)
from installation_inputs import Bundle, InstallError, LOCKS, CATALOGUE

UUID = '591578E3-8196-4B44-A575-CEC76B406789'
OTHER = '870130E1-51A1-4ED8-841E-DB84B7941376'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


class InstallationTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name).resolve()
        self.source = self.root/'Source Kit'
        self.source.mkdir(mode=0o700)
        self.target = self.root/'Package Store'
        self.parent_state = self.root/'operator-state.json'
        self.parent_state.write_text('preserved release numbers and identities')
        self.fixture()
        self.volume = UUID
        self.store = module.Store(self.target, UUID, lambda path: self.volume)
        mock = patch.object(module.shutil, 'disk_usage', return_value=SimpleNamespace(free=200*2**30))
        mock.start(); self.addCleanup(mock.stop)
        self.copy = lambda src, dst: module.copy_file(src, dst, clone=False)

    def put(self, name, raw=b'not executed'):
        path = self.source/name
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            path.chmod(0o644)
        path.write_bytes(raw)
        path.chmod(0o444)
        return dict(path=name, bytes=len(raw), sha256=sha(raw))

    def rewrite_manifest(self):
        raw = json.dumps(self.manifest).encode()
        self.put('application-manifest.json', raw)
        self.pin = sha(raw)

    def fixture(self):
        self.manifest = dict(schemaVersion=1, operatorStateCopied=False, applicationFiles=[], inputs={})
        prefix = 'aosedge-sdv-demo/'
        files = ['LICENSE', 'workspace/repositories.json']
        files += ['apps/demo-orchestrator/src/aosedge_demo_orchestrator/'+n
                  for n in ('__init__.py', 'cli.py', 'presenter.py', 'host_entry.py')]
        for name in files:
            row = self.put(prefix+name, b'raise RuntimeError("must not execute")\n')
            self.manifest['applicationFiles'].append(dict(row, path=name))
        for group, lock_path in LOCKS.items():
            base = CATALOGUE+'/'+group+'/'
            if group == 'backend-inputs':
                row = self.put(base+'backends.tar')
                manifest = dict(archiveBytes=row['bytes'], archiveSha256=row['sha256'])
            else:
                names = ['payload.bin']
                if group == 'preparation-inputs':
                    names += ['factory/39/manifest.json', 'factory/39/factory.img']
                rows = []
                for name in names:
                    row = self.put(base+name)
                    rows.append(dict(row, path=name, mode=0o444))
                manifest = dict(files=rows)
                if group == 'preparation-inputs':
                    manifest['factory'] = dict(version='39', image='factory.img')
                    for leaf in ('manifest.json', 'factory.img'):
                        self.put(CATALOGUE+'/factory-images/39/'+leaf)
            raw = json.dumps(manifest).encode()
            pin = dict(path='manifest.json', bytes=len(raw), sha256=sha(raw))
            self.put(base+'manifest.json', raw)
            self.manifest['inputs'][group] = pin
            lock_name = 'contracts/'+lock_path
            row = self.put(prefix+lock_name, json.dumps(dict(manifest=pin)).encode())
            self.manifest['applicationFiles'].append(dict(row, path=lock_name))
        self.rewrite_manifest()

    def install(self, **kwargs):
        return self.store.install(self.source, self.pin, copier=self.copy, **kwargs)

    def test_plan_does_not_create_store_or_claim_payload_verification(self):
        bundle = self.store.plan(self.source, self.pin)
        self.assertEqual(26, len(bundle.rows))
        self.assertFalse(self.target.exists())

    def test_install_repeat_verify_preserves_inputs_and_other_state(self):
        original = {p.relative_to(self.source): (p.read_bytes(), p.stat().st_mode)
                    for p in self.source.rglob('*') if p.is_file()}
        first = self.install()
        self.assertEqual('INSTALLED_NOT_ACTIVATED', first['status'])
        self.assertFalse(first['reused'])
        self.assertFalse(first['runtimeChanged'])
        self.assertFalse(first['cloudAccessed'])
        self.assertTrue(self.install()['reused'])
        self.assertTrue(self.store.verify(self.pin)['reused'])
        self.assertEqual([], list((self.target/'staging').iterdir()))
        self.assertEqual({self.pin}, {p.name for p in (self.target/'versions').iterdir()})
        for name, (raw, mode) in original.items():
            self.assertEqual(raw, (self.source/name).read_bytes())
            self.assertEqual(mode, (self.source/name).stat().st_mode)
        self.assertEqual('preserved release numbers and identities', self.parent_state.read_text())

    def test_wrong_application_pin_before_writes(self):
        with self.assertRaisesRegex(InstallError, 'APPLICATION_MANIFEST_MISMATCH'):
            self.store.install(self.source, '0'*64)
        self.assertFalse(self.target.exists())

    def test_missing_group_cannot_select_developer_fallback(self):
        del self.manifest['inputs']['host-runtime']; self.rewrite_manifest()
        with self.assertRaisesRegex(InstallError, 'REQUIRED_INPUT_GROUP_MISSING'):
            self.install()
        self.assertFalse(self.target.exists())

    def test_changed_lock_rejected(self):
        path = self.source/'aosedge-sdv-demo/contracts'/LOCKS['host-runtime']
        path.chmod(0o644)
        raw = path.read_bytes(); path.write_bytes(bytes([raw[0]^1])+raw[1:])
        with self.assertRaisesRegex(InstallError, 'INPUT_DIGEST_MISMATCH'):
            self.install()

    def test_changed_group_manifest_rejected(self):
        path = self.source/CATALOGUE/'vm-runtime/manifest.json'
        path.chmod(0o644); raw = path.read_bytes(); path.write_bytes(bytes([raw[0]^1])+raw[1:])
        with self.assertRaisesRegex(InstallError, 'INPUT_DIGEST_MISMATCH'):
            self.install()

    def test_payload_corruption_never_promoted(self):
        path = self.source/'aosedge-sdv-demo/LICENSE'
        path.chmod(0o644); raw = path.read_bytes(); path.write_bytes(bytes([raw[0]^1])+raw[1:])
        with self.assertRaisesRegex(InstallError, 'INSTALL_TRANSFER_MISMATCH'):
            self.install()
        self.assertFalse((self.target/'versions'/self.pin).exists())

    def test_extra_file_blocks_before_store_creation(self):
        self.put('aosedge-sdv-demo/.local/credentials', b'fixture only')
        with self.assertRaisesRegex(InstallError, 'INPUT_INVENTORY_MISMATCH'):
            self.install()
        self.assertFalse(self.target.exists())

    def test_missing_factory_mirror_blocks(self):
        (self.source/CATALOGUE/'factory-images/39/factory.img').unlink()
        with self.assertRaises(FileNotFoundError):
            self.install()
        self.assertFalse(self.target.exists())

    def test_traversal_rejected(self):
        self.manifest['applicationFiles'][0]['path'] = '../outside'
        self.rewrite_manifest()
        with self.assertRaisesRegex(InstallError, 'INPUT_PATH_INVALID'):
            self.install()

    def test_case_duplicate_rejected(self):
        row = dict(self.manifest['applicationFiles'][0])
        self.manifest['applicationFiles'].append(row)
        self.rewrite_manifest()
        with self.assertRaisesRegex(InstallError, 'INPUT_PATH_DUPLICATE'):
            self.install()
        # Real mixed-case collision under a permitted application prefix.
        row['path'] = self.manifest['applicationFiles'][2]['path'].replace('__init__.py', '__INIT__.py')
        self.rewrite_manifest()
        with self.assertRaisesRegex(InstallError, 'INPUT_PATH_DUPLICATE'):
            self.install()

    def test_duplicate_json_keys_rejected(self):
        raw = b'{"schemaVersion":1,"schemaVersion":1}'
        self.put('application-manifest.json', raw)
        with self.assertRaisesRegex(InstallError, 'JSON_DUPLICATE_KEY'):
            self.store.install(self.source, sha(raw))

    def test_links_and_hardlinks_rejected(self):
        path = self.source/'aosedge-sdv-demo/LICENSE'
        raw = path.read_bytes(); path.unlink(); path.symlink_to(self.parent_state)
        with self.assertRaisesRegex(InstallError, 'PATH_HAS_LINK'):
            self.install()
        path.unlink(); os.link(self.parent_state, path)
        with self.assertRaisesRegex(InstallError, 'INPUT_FILE_UNSAFE'):
            self.install()

    def test_unsafe_file_and_directory_modes_rejected(self):
        path = self.source/'aosedge-sdv-demo/LICENSE'; path.chmod(0o666)
        with self.assertRaisesRegex(InstallError, 'INPUT_FILE_UNSAFE'):
            self.install()
        path.chmod(0o444); self.source.chmod(0o777)
        with self.assertRaisesRegex(InstallError, 'INPUT_DIRECTORY_UNSAFE'):
            self.install()

    def test_nonempty_unrecognized_store_preserved(self):
        self.target.mkdir(mode=0o700); keep = self.target/'keep'; keep.write_text('keep')
        with self.assertRaisesRegex(InstallError, 'INSTALL_STORE_UNRECOGNIZED'):
            self.install()
        self.assertEqual('keep', keep.read_text())

    def test_missing_parent_cannot_create_replacement_mount(self):
        with self.assertRaisesRegex(InstallError, 'INSTALL_PARENT_MISSING'):
            module.Store(self.root/'missing-volume'/'store', UUID, lambda path: UUID)
        self.assertFalse((self.root/'missing-volume').exists())

    def test_wrong_volume_blocks_before_write(self):
        self.volume = OTHER
        with self.assertRaisesRegex(InstallError, 'INSTALL_VOLUME_CHANGED'):
            self.install()
        self.assertFalse(self.target.exists())

    def test_changed_volume_before_promotion_blocks(self):
        def progress(event):
            self.volume = OTHER
        with self.assertRaisesRegex(InstallError, 'INSTALL_VOLUME_CHANGED'):
            self.install(progress=progress)
        self.assertFalse((self.target/'versions'/self.pin).exists())

    def test_low_space_blocks_without_store(self):
        with patch.object(module.shutil, 'disk_usage', return_value=SimpleNamespace(free=module.RESERVE)), \
                self.assertRaisesRegex(InstallError, 'INSTALL_SPACE_INSUFFICIENT'):
            self.install()
        self.assertFalse(self.target.exists())

    def test_free_space_lost_during_copy_blocks_promotion(self):
        free = [200*2**30]
        def progress(event):
            free[0] = module.RESERVE-1
        with patch.object(module.shutil, 'disk_usage', side_effect=lambda path: SimpleNamespace(free=free[0])), \
                self.assertRaisesRegex(InstallError, 'INSTALL_SPACE_INSUFFICIENT'):
            self.install(progress=progress)
        self.assertFalse((self.target/'versions'/self.pin).exists())

    def test_interruption_resumes_verified_files(self):
        def progress(event):
            if event['files'] == 3:
                raise RuntimeError('injected interruption')
        with self.assertRaisesRegex(RuntimeError, 'injected interruption'):
            self.install(progress=progress)
        self.assertFalse((self.target/'versions'/self.pin).exists())
        self.store = module.Store(self.target, UUID, lambda path: UUID)
        with patch.object(module, 'copy_file', wraps=module.copy_file) as copy:
            result = self.install()
        self.assertEqual(result['files']-3, copy.call_count)

    def test_partial_copy_replaced_in_owned_transaction(self):
        def interrupted(src, dst):
            dst.write_bytes(b'partial')
            raise OSError('injected I/O interruption')
        with self.assertRaises(OSError):
            self.store.install(self.source, self.pin, copier=interrupted)
        self.store = module.Store(self.target, UUID, lambda path: UUID)
        self.assertEqual('INSTALLED_NOT_ACTIVATED', self.install()['status'])

    def test_changed_completed_staging_file_blocks(self):
        def progress(event):
            raise RuntimeError('pause')
        with self.assertRaises(RuntimeError):
            self.install(progress=progress)
        path = next(p for p in (self.target/'staging'/self.pin/'bundle').rglob('*') if p.is_file())
        path.chmod(0o644); path.write_bytes(b'changed')
        with self.assertRaisesRegex(InstallError, 'INSTALL_STAGED_FILE_CHANGED'):
            self.install()

    def test_post_promotion_receipt_recovered_without_recopy(self):
        real = module.atomic_record
        def fail_receipt(path, value):
            if path.parent.name == 'receipts':
                raise OSError('receipt interrupted')
            return real(path, value)
        with patch.object(module, 'atomic_record', side_effect=fail_receipt), self.assertRaises(OSError):
            self.install()
        self.assertTrue((self.target/'versions'/self.pin).exists())
        self.store = module.Store(self.target, UUID, lambda path: UUID)
        with patch.object(module, 'copy_file', side_effect=AssertionError('must not recopy')):
            self.assertTrue(self.install()['reused'])

    def test_completed_file_mutated_later_in_transaction_blocks_promotion(self):
        def progress(event):
            if event['files'] == event['totalFiles']:
                path = self.target/'staging'/self.pin/'bundle'/sorted(Bundle(self.source, self.pin).rows)[0]
                path.chmod(0o644); path.write_bytes(b'changed after verification')
        with self.assertRaisesRegex(InstallError, 'INSTALL_STAGED_FILE_CHANGED'):
            self.install(progress=progress)
        self.assertFalse((self.target/'versions'/self.pin).exists())

    def test_corrupt_promoted_version_not_repaired_or_deleted(self):
        self.install()
        path = self.target/'versions'/self.pin/'aosedge-sdv-demo/LICENSE'
        path.chmod(0o644); path.write_bytes(b'bad')
        with self.assertRaisesRegex(InstallError, 'INPUT_FILE_SIZE_MISMATCH'):
            self.install()
        self.assertEqual(b'bad', path.read_bytes())

    def test_verify_detects_earlier_file_changed_while_later_file_is_checked(self):
        self.install()
        bundle = Bundle(self.target/'versions'/self.pin, self.pin)
        original = bundle.verify_file
        count = [0]
        def verify_file(name):
            original(name)
            count[0] += 1
            if count[0] == len(bundle.rows):
                (bundle.root/'application-manifest.json').chmod(0o644)
        with patch.object(bundle, 'verify_file', side_effect=verify_file), \
                self.assertRaisesRegex(InstallError, 'SOURCE_CHANGED'):
            bundle.verify()

    def test_source_mutation_during_copy_blocks_promotion(self):
        def copier(src, dst):
            self.copy(src, dst)
            src.chmod(0o644)
        with self.assertRaisesRegex(InstallError, 'SOURCE_CHANGED'):
            self.store.install(self.source, self.pin, copier=copier)
        self.assertFalse((self.target/'versions'/self.pin).exists())

    def test_source_store_overlap_rejected(self):
        store = module.Store(self.source/'store', UUID, lambda path: UUID)
        with self.assertRaisesRegex(InstallError, 'INSTALL_SOURCE_STORE_OVERLAP'):
            store.install(self.source, self.pin)

    def test_exclusive_writer(self):
        with self.store.writer(), self.assertRaisesRegex(InstallError, 'INSTALL_BUSY'):
            self.install()

    def test_marker_volume_binding_preserved(self):
        self.install()
        store = module.Store(self.target, OTHER, lambda path: OTHER)
        with self.assertRaisesRegex(InstallError, 'INSTALL_STORE_BINDING_INVALID'):
            store.inspect()

    def test_clone_failure_has_explicit_verified_copy_fallback(self):
        dst = self.root/'copy'
        with patch.object(module.subprocess, 'run', return_value=SimpleNamespace(returncode=1)):
            module.copy_file(self.source/'aosedge-sdv-demo/LICENSE', dst)
        self.assertEqual((self.source/'aosedge-sdv-demo/LICENSE').read_bytes(), dst.read_bytes())

    def test_volume_probe_resolves_directory_to_device(self):
        # Actual macOS plist has MountPoint, not a Mounted boolean.
        info = dict(GlobalPermissionsEnabled=True, MountPoint=str(self.root), DeviceNode='/dev/disk13s1', VolumeUUID=UUID)
        results = [SimpleNamespace(returncode=0, stdout=b'Filesystem Blocks Used Available Capacity Mounted on\n/dev/disk13s1 1 1 1 1% /Volumes/Name With Spaces\n'),
                   SimpleNamespace(returncode=0, stdout=plistlib.dumps(info))]
        with patch.object(module.subprocess, 'run', side_effect=results) as run:
            self.assertEqual(UUID, module.volume_identity(self.root))
            self.assertEqual(['/usr/sbin/diskutil', 'info', '-plist', '/dev/disk13s1'], run.call_args.args[0])

    def test_volume_probe_rejects_non_device_and_missing_ownership(self):
        with patch.object(module.subprocess, 'run', return_value=SimpleNamespace(returncode=0, stdout=b'header\nserver:/share 1 1 1 1% /mount\n')), \
                self.assertRaisesRegex(InstallError, 'INSTALL_VOLUME_INVALID'):
            module.volume_identity(self.root)
        info = dict(GlobalPermissionsEnabled=False, MountPoint=str(self.root), DeviceNode='/dev/disk13s1', VolumeUUID=UUID)
        results = [SimpleNamespace(returncode=0, stdout=b'header\n/dev/disk13s1 1 1 1 1% /mount\n'),
                   SimpleNamespace(returncode=0, stdout=plistlib.dumps(info))]
        with patch.object(module.subprocess, 'run', side_effect=results), \
                self.assertRaisesRegex(InstallError, 'INSTALL_VOLUME_OWNERSHIP_REQUIRED'):
            module.volume_identity(self.root)


if __name__ == '__main__':
    unittest.main()
