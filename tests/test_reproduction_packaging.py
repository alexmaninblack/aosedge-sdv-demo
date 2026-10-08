# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Build-only preparation proof; fixture files stay in the selected test TMPDIR."""
import copy
import json
import shutil
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from test_reproduction import StorageFixture
from reproduction import core, packaging
from reproduction.artifacts import sha256


class PreparationTests(StorageFixture, unittest.TestCase):
    def fixture(self):
        self.storage.environment()
        self.state['sources']['vehicle-platform'] = {'revision': 'a'*40}
        self.pins = core.read_json(core.ROOT / packaging.SERVICE_CHECKPOINT)['serviceExports']
        self.chosen = [{'target': r['team']+'-service', 'key': str(n)*64, 'pin': r}
                       for n, r in enumerate(self.pins)]
        self.factory = {'version': 'fixture', 'sha256': 'a'*64}
        self.patch('reproduction.packaging.verify_sources')
        self.patch('reproduction.packaging.producer', return_value=({'recipe': 'a'*40}, 'b'*40))
        self.patch('reproduction.packaging.selected_services', return_value=self.chosen)
        self.patch('reproduction.packaging.retained_preparation',
                   return_value=(self.base, [], {'sha256': 'c'*64}, self.factory))
        self.stage = self.patch('reproduction.packaging.stage_inputs')
        self.command = self.patch('reproduction.packaging.run_command', side_effect=self.owner)

    def owner(self, args, **kwargs):
        if str(args[0]) != '/usr/bin/sandbox-exec':
            return SimpleNamespace(returncode=0, stdout=b'{"python":"3.12.14","machine":"arm64"}', stderr=b'')
        output = Path(args[-3])
        output.mkdir()
        data = output / 'factory.img'
        data.write_bytes(b'fixture')
        data.chmod(0o444)
        core.atomic_json(output / packaging.PREPARATION_MANIFEST, {
            'status': 'ASSEMBLED_PREPARATION_INPUTS_NOT_UPLOAD_READY', 'factory': self.factory,
            'serviceProfiles': self.pins, 'runtimeSelectorsChanged': False,
            'externalDistributionApproved': False,
            'files': [{'path': data.name, 'bytes': data.stat().st_size, 'sha256': sha256(data)}]})
        return SimpleNamespace(returncode=0, stdout=b'{}', stderr=b'')

    def build(self):
        return packaging.preparation(self.storage, self.state, self.base, sys.executable, lambda *args: None)

    def test_first_repeat_and_state_recovery_never_reassemble(self):
        self.fixture()
        key = self.build()
        self.assertEqual(self.state['builds'][key]['inputs']['platform'], self.state['sources']['vehicle-platform'])
        self.assertEqual(self.build(), key)
        self.assertEqual(self.stage.call_count, 1)
        del self.state['builds'][key]
        self.assertEqual(self.build(), key)
        self.assertEqual(self.stage.call_count, 1)

    def test_failed_owner_not_adopted_or_blindly_retried(self):
        self.fixture()
        real = self.owner
        def failed(args, **kwargs):
            result = real(args, **kwargs)
            if str(args[0]) == '/usr/bin/sandbox-exec':
                result.returncode = 1
            return result
        self.command.side_effect = failed
        with self.assertRaisesRegex(core.LabError, 'owner failed'):
            self.build()
        self.assertFalse(self.state['builds'])
        with self.assertRaises(FileNotFoundError):
            self.build()
        self.assertEqual(self.stage.call_count, 1)

    def test_changed_output_not_reused_even_same_size(self):
        self.fixture()
        key = self.build()
        path = self.storage.path('builds/preparation/'+key+'/factory.img')
        path.chmod(0o644)
        path.write_bytes(b'changed')
        path.chmod(0o444)
        with self.assertRaisesRegex(core.LabError, 'output changed'):
            self.build()

    def test_extra_and_symlink_rejected(self):
        self.fixture()
        key = self.build()
        path = self.storage.path('builds/preparation/'+key+'/extra')
        path.write_text('extra')
        with self.assertRaisesRegex(core.LabError, 'inventory differs'):
            self.build()
        path.unlink()
        path.symlink_to('factory.img')
        with self.assertRaisesRegex(core.LabError, 'contains link'):
            self.build()

    def test_escaping_manifest_path_rejected_before_file_read(self):
        self.fixture()
        key = self.build()
        output = self.storage.path('builds/preparation/'+key)
        path = output / packaging.PREPARATION_MANIFEST
        value = core.read_json(path)
        value['files'][0]['path'] = '../escape'
        core.atomic_json(path, value)
        receipt = core.read_json(output/'build-receipt.json')
        receipt['manifest'].update(bytes=path.stat().st_size, sha256=sha256(path))
        core.atomic_json(output/'build-receipt.json', receipt)
        with self.assertRaisesRegex(core.LabError, 'Invalid Cloud input/output path'):
            self.build()

    def test_declared_interpreter_and_offline_owner(self):
        self.fixture()
        self.build()
        args = self.command.call_args.args[0]
        self.assertEqual(str(args[0]), '/usr/bin/sandbox-exec')
        self.assertIn('-I', args)
        self.assertIn(self.storage.path('sources/vehicle-platform'), args)
        self.assertEqual(args[-1], packaging.SERVICE_CHECKPOINT)
        self.assertNotIn('HOME', self.command.call_args.kwargs['env'])

    def test_dirty_root_refused_without_compilation(self):
        with patch('reproduction.packaging.git', return_value=' M source'):
            with self.assertRaisesRegex(core.LabError, 'Commit the root'):
                packaging.producer(self.storage)

    def test_service_checkpoint_requires_exact_four_profiles(self):
        with self.assertRaisesRegex(core.LabError, 'four service profiles'):
            packaging.selected_services(self.storage, self.state, [])

    def test_missing_service_build_fails(self):
        pins = core.read_json(core.ROOT / packaging.SERVICE_CHECKPOINT)['serviceExports']
        with self.assertRaisesRegex(core.LabError, 'One verified service build'):
            packaging.selected_services(self.storage, self.state, pins)

    def test_wrong_ssd_and_missing_kit_fail(self):
        with self.assertRaisesRegex(core.LabError, 'Specify --kit-inputs'):
            packaging.retained_preparation(self.storage, None)
        with patch('reproduction.packaging.external_volume', return_value={'uuid': 'OTHER'}):
            with self.assertRaisesRegex(core.LabError, 'bound SSD'):
                packaging.retained_preparation(self.storage, self.base)

    def test_actual_input_staging_maps_factory_and_profiles(self):
        source, scratch = self.base/'retained', self.base/'staged'
        scratch.mkdir()
        rows = []
        for name in ('firmware/QEMU_EFI.fd', 'factory/fixture/manifest.json', 'vdp/profiles/v2/source.json'):
            path = source/name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'fixture')
            path.chmod(0o444)
            rows.append({'path': name, 'bytes': 7, 'sha256': sha256(path)})
        def clone(args, **kwargs):
            shutil.copy2(args[-2], args[-1])
            return SimpleNamespace(returncode=0)
        with patch('reproduction.packaging.run_command', side_effect=clone):
            packaging.stage_inputs(self.storage, scratch, source, rows, {}, [])
        self.assertTrue((scratch/'factory-images/fixture/manifest.json').is_file())
        self.assertTrue((scratch/'components/vehicle-data-provider/.source-profiles/2.0.0/source.json').is_file())
        self.assertEqual((scratch/'firmware/QEMU_EFI.fd').read_bytes(), b'fixture')

    def test_changed_tooling_is_new_key_and_docs_commit_reuses(self):
        self.fixture()
        key = self.build()
        with patch('reproduction.packaging.producer', return_value=({'recipe': 'a'*40}, 'c'*40)):
            self.assertEqual(self.build(), key)
        with patch('reproduction.packaging.producer', return_value=({'recipe': 'c'*40}, 'c'*40)):
            self.assertNotEqual(self.build(), key)
        self.assertEqual(self.stage.call_count, 2)


if __name__ == '__main__':
    unittest.main()
