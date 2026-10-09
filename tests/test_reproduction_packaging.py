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
        core.atomic_json(self.base / packaging.PREPARATION_MANIFEST, {'runtimePin': {'revision': 'd'*40, 'tree': 'e'*40}})
        self.patch('reproduction.packaging.verify_sources')
        self.patch('reproduction.packaging.producer', return_value=({'recipe': 'a'*40}, 'b'*40))
        self.patch('reproduction.packaging.selected_services', return_value=self.chosen)
        self.patch('reproduction.packaging.retained_preparation',
                   return_value=(self.base, [], {'sha256': 'c'*64}, self.factory))
        self.stage = self.patch('reproduction.packaging.stage_inputs')
        self.patch('reproduction.packaging.runtime_object')
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

    def test_runtime_acquisition_is_explicit_exact_and_preserves_head(self):
        self.state['sources']['vehicle-platform'] = {'revision': 'a'*40}
        pin = {'revision': 'd'*40, 'tree': 'e'*40}
        with patch('reproduction.packaging.run_command', return_value=SimpleNamespace(returncode=1)), \
                patch('reproduction.packaging.git', side_effect=['', 'e'*40, 'a'*40]) as git:
            with self.assertRaisesRegex(core.LabError, 'prepare-dependencies'):
                packaging.runtime_object(self.storage, self.state, pin, False, lambda *args: None)
            git.assert_not_called()
            packaging.runtime_object(self.storage, self.state, pin, True, lambda *args: None)
            self.assertEqual(git.call_args_list[0].args[1][-1], 'd'*40)
            self.assertNotIn('checkout', str(git.call_args_list))

    def test_source_factory_selection_first_repeat_and_historical_default(self):
        self.fixture()
        old = self.build()
        pin = {'factory': self.factory, 'manifest': {'sha256': 'f'*64}}
        with patch('reproduction.packaging.source_factory', return_value=(pin, self.base/'manifest', self.base/'image')), \
                patch('reproduction.packaging.stage_source_factory') as stage:
            new = packaging.preparation(self.storage, self.state, self.base, sys.executable,
                                        lambda *args: None, factory_inputs=self.base)
            again = packaging.preparation(self.storage, self.state, self.base, sys.executable,
                                          lambda *args: None, factory_inputs=self.base)
        self.assertNotEqual(old, new)
        self.assertEqual(new, again)
        self.assertEqual(stage.call_count, 1)
        self.assertEqual(self.state['builds'][new]['inputs']['sourceFactory'], pin)
        self.assertEqual(self.build(), old)
        owners = [call.args[0] for call in self.command.call_args_list
                  if str(call.args[0][0]) == '/usr/bin/sandbox-exec']
        self.assertEqual(owners[-1][-2], packaging.SOURCE_FACTORY_CHECKPOINT)

    def source_fixture(self):
        root = self.base/'factory-result'
        manifest = root/'factory-images/fixture/manifest.json'
        manifest.parent.mkdir(parents=True)
        image = manifest.parent/'main-qemuarm64.img'
        image.write_bytes(b'factory')
        image.chmod(0o444)
        factory = dict(version='fixture', image=image.name, sizeBytes=7, sha256=sha256(image),
                       sourceRevision='a'*40, manifestState='BUILT_NOT_LIVE_QUALIFIED')
        value = {'state': factory['manifestState'], 'source': {'revision':'a'*40},
                 'factoryImage': dict(version='fixture', architecture='main-qemuarm64', path=image.name,
                                     byteLength=7, sha256=sha256(image), format='raw'),
                 'build': dict(targetedTests='PASS', packageQa='PASS', imageQa='PASS',
                               hostTransferSha256Matched=True,
                               mainlineQualification={'solutionRevision':'b'*40})}
        core.atomic_json(manifest, value)
        pin = {'factory':factory, 'qualificationToolsRevision':'b'*40,
               'manifest': {'path':str(manifest.relative_to(root)), 'bytes':manifest.stat().st_size,
                            'sha256':sha256(manifest)}}
        self.patch('reproduction.packaging.ROOT', self.base)
        checkpoint = self.base/packaging.SOURCE_FACTORY_CHECKPOINT
        checkpoint.parent.mkdir(parents=True)
        core.atomic_json(checkpoint, pin)
        self.patch('reproduction.packaging.external_volume', return_value=self.storage.volume)
        return root, manifest, image, pin

    def test_source_factory_pin_and_readonly_image(self):
        root, manifest, image, pin = self.source_fixture()
        self.assertEqual(packaging.source_factory(self.storage, root), (pin, manifest, image))
        image.chmod(0o644)
        with self.assertRaisesRegex(core.LabError, 'immutable'):
            packaging.source_factory(self.storage, root)

    def test_source_factory_modified_manifest_and_wrong_volume(self):
        root, manifest, _, _ = self.source_fixture()
        with patch('reproduction.packaging.external_volume', return_value={'uuid':'OTHER'}):
            with self.assertRaisesRegex(core.LabError, 'bound SSD'):
                packaging.source_factory(self.storage, root)
        manifest.write_bytes(manifest.read_bytes()+b' ')
        with self.assertRaises(core.LabError):
            packaging.source_factory(self.storage, root)

    def test_source_factory_rejects_failed_gates_even_with_matching_manifest_digest(self):
        root, manifest, _, pin = self.source_fixture()
        value = core.read_json(manifest)
        value['build']['imageQa'] = 'FAIL'
        core.atomic_json(manifest, value)
        pin['manifest'].update(bytes=manifest.stat().st_size, sha256=sha256(manifest))
        core.atomic_json(self.base/packaging.SOURCE_FACTORY_CHECKPOINT, pin)
        with self.assertRaisesRegex(core.LabError, 'evidence differs'):
            packaging.source_factory(self.storage, root)


if __name__ == '__main__':
    unittest.main()
