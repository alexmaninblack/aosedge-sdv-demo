# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
import copy
import hashlib
import io
import os
from pathlib import Path
import shutil
from contextlib import redirect_stdout
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from test_reproduction import StorageFixture
from reproduction import artifacts, cache, cli, core, space


class CacheTests(StorageFixture, unittest.TestCase):
    def fixture(self):
        self.donor = core.Storage(self.base/'donor', self.release, 'developer')
        self.donor.initialize()
        data = b'public cache fixture'
        self.row = {'sha256':hashlib.sha256(data).hexdigest(), 'bytes':len(data), 'names':['fixture']}
        self.original = self.donor.path('cache/sha256/'+self.row['sha256'])
        self.original.parent.mkdir(parents=True)
        self.original.write_bytes(data)
        self.patch('reproduction.cache.storage_volume', return_value=self.volume)
        self.patch('reproduction.cache.catalogue', return_value={self.row['sha256']:self.row})
        # Only fixtures use a copy; real reuse requires the tested macOS clonefile.
        self.cloner = self.patch('reproduction.cache.clone', side_effect=shutil.copyfile)

    def reuse(self):
        return cache.reuse(self.storage, self.donor.root, lambda *e:None)

    def test_first_repeat_and_legacy_consumer_reuses_no_network(self):
        self.fixture()
        state_before = self.storage.state_path.read_bytes()
        donor_before = self.donor.state_path.read_bytes()
        first = self.reuse()
        self.assertEqual((first['imported'], first['reused'], first['missing']), (1,0,[]))
        self.assertEqual(first['downloadedBytes'], 0)
        self.assertFalse(first['profileReady'])
        second = self.reuse()
        self.assertEqual((second['imported'], second['reused']), (0,1))
        self.cloner.assert_called_once()
        with patch.object(artifacts.Drive, 'metadata', side_effect=AssertionError):
            self.assertEqual(artifacts.download(self.storage, artifacts.Drive('fixture'),
                'fixture-file-id', 'fixture-folder-id', self.row).read_bytes(), self.original.read_bytes())
        self.assertEqual(self.storage.state_path.read_bytes(), state_before)
        self.assertEqual(self.donor.state_path.read_bytes(), donor_before)
        self.assertEqual(list(self.original.parent.iterdir()), [self.original])  # donor is read-only

    def test_missing_objects_remain_explicit_and_do_not_download(self):
        self.fixture(); self.original.unlink()
        value = self.reuse()
        self.assertEqual(value['status'], 'CACHE_REUSE_PARTIAL')
        self.assertEqual(value['missing'], [self.row['sha256']])
        self.cloner.assert_not_called()

    def test_corrupt_source_and_destination_preserved(self):
        self.fixture(); self.original.write_bytes(b'x'*self.row['bytes'])
        with self.assertRaisesRegex(core.LabError, 'digest differs'):
            self.reuse()
        self.cloner.assert_not_called()
        self.original.write_bytes(b'public cache fixture'); self.reuse()
        output = self.storage.path('cache/sha256/'+self.row['sha256'])
        output.chmod(0o600); output.write_bytes(b'x'*self.row['bytes'])
        with self.assertRaisesRegex(core.LabError, 'digest differs'):
            self.reuse()
        self.assertEqual(output.read_bytes(), b'x'*self.row['bytes'])

    def test_digest_is_verified_after_clone_even_with_forged_source_receipt(self):
        self.fixture(); self.original.write_bytes(b'x'*self.row['bytes'])
        core.atomic_json(self.original.with_suffix('.json'), {'sha256':self.row['sha256'],
                                                            'identity':artifacts.identity(self.original)})
        with self.assertRaisesRegex(core.LabError, 'transfer digest'):
            self.reuse()
        self.assertFalse(self.storage.path('cache/sha256/'+self.row['sha256']).exists())

    def test_source_mutation_during_clone_rejected(self):
        self.fixture()
        def mutate(source, target):
            shutil.copyfile(source, target); source.write_bytes(b'x'*self.row['bytes'])
        self.cloner.side_effect = mutate
        with self.assertRaisesRegex(core.LabError, 'source changed'):
            self.reuse()

    def test_complete_interrupted_clone_recovers_without_new_clone(self):
        self.fixture()
        with patch.object(cache, 'sha256', side_effect=KeyboardInterrupt):
            # Source inspection is interrupted before clone; leave source intact.
            with self.assertRaises(KeyboardInterrupt):
                self.reuse()
        core.atomic_json(self.original.with_suffix('.json'), {'sha256':self.row['sha256'],
                                                            'identity':artifacts.identity(self.original)})
        with patch.object(cache, 'sha256', side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.reuse()
        self.assertEqual(self.reuse()['imported'], 1)
        self.cloner.assert_called_once()

    def test_unowned_partial_preserved(self):
        self.fixture()
        part = self.storage.path('cache/sha256/'+self.row['sha256']+'.reuse')
        part.parent.mkdir(parents=True); part.write_bytes(b'user data')
        with self.assertRaisesRegex(core.LabError, 'Unowned'):
            self.reuse()
        self.assertEqual(part.read_bytes(), b'user data')

    def test_clone_failure_does_not_fallback(self):
        self.fixture(); self.cloner.side_effect = core.LabError('APFS clone failed')
        with self.assertRaisesRegex(core.LabError, 'APFS'):
            self.reuse()
        self.assertFalse(self.storage.path('cache/sha256/'+self.row['sha256']).exists())

    def test_links_foreign_volumes_and_nested_workspaces_rejected(self):
        self.fixture()
        self.original.unlink(); self.original.symlink_to(self.storage.state_path)
        with self.assertRaisesRegex(core.LabError, 'Symlink'):
            self.reuse()
        with patch.object(cache, 'storage_volume', return_value={'uuid':'OTHER'}):
            with self.assertRaisesRegex(core.LabError, 'bound volume'):
                self.reuse()
        for root in (self.storage.root, self.storage.root/'nested', self.storage.root.parent):
            with self.assertRaisesRegex(core.LabError, 'separate'):
                cache.source(self.storage, root)

    def test_low_space_prevents_clone(self):
        self.fixture()
        with patch('reproduction.core.shutil.disk_usage', return_value=SimpleNamespace(free=59*core.GIB)):
            with self.assertRaisesRegex(core.LabError, 'space'):
                self.reuse()
        self.cloner.assert_not_called()

    def test_hardlinked_source_and_wrong_volume_binding_rejected(self):
        self.fixture(); alias = self.original.with_name('alias'); os.link(self.original, alias)
        with self.assertRaisesRegex(core.LabError, 'regular'):
            self.reuse()
        alias.unlink()
        state = self.donor.state(); state['binding']['volumeUUID'] = 'OTHER'
        core.atomic_json(self.donor.state_path, state)
        with self.assertRaisesRegex(core.LabError, 'binding'):
            self.reuse()


class CatalogueTests(StorageFixture, unittest.TestCase):
    def fixture(self):
        self.owner = self.storage.path('sources/integration')
        (self.owner/'workspace').mkdir(parents=True)
        self.row = {'sha256':'a'*64, 'bytes':100, 'file':'fixture.whl'}
        self.lock = self.owner/'workspace/cloud-worker-wheels.lock.json'
        self.write([self.row])
        self.check = self.patch('reproduction.cache.check_source')

    def write(self, rows):
        core.atomic_json(self.lock, {'python':'3.12','platform':'macOS-arm64','packages':rows})

    def test_expected_rows_only_and_deduplicated(self):
        self.fixture(); self.write([self.row, {**self.row,'file':'alias.whl'}])
        rows = cache.catalogue(self.storage)
        self.assertEqual(len(rows), 3)  # two declared release artifacts plus one wheel digest
        self.assertEqual(len(rows['a'*64]['names']), 2)
        self.assertEqual(self.check.call_args.args[1]['revision'], self.release.sources['integration']['revision'])
        self.assertEqual(self.check.call_args.args[2]['GIT_OPTIONAL_LOCKS'], '0')

    def test_wrong_source_pin_and_conflicting_size_rejected(self):
        self.fixture(); self.check.side_effect = core.LabError('Wrong source revision')
        with self.assertRaisesRegex(core.LabError, 'revision'):
            cache.catalogue(self.storage)
        self.check.side_effect = None; self.write([self.row, {**self.row,'bytes':101}])
        with self.assertRaisesRegex(core.LabError, 'Conflicting'):
            cache.catalogue(self.storage)

    def test_missing_source_not_silently_guessed(self):
        with self.assertRaisesRegex(core.LabError, 'Prepared exact integration'):
            cache.catalogue(self.storage)
        self.storage.profile = 'operator'
        rows = cache.catalogue(self.storage)
        self.assertEqual(list(rows.values())[0]['names'], ['dmg'])
        self.assertEqual(len(rows), 1)


class SpaceTests(StorageFixture, unittest.TestCase):
    def fixture(self):
        self.patch('reproduction.cache.catalogue', return_value={})

    def test_report_is_read_only_and_does_not_claim_peak_or_reuse(self):
        self.fixture()
        before = sorted(self.storage.root.rglob('*'))
        value = space.report(self.storage, self.state)
        self.assertEqual(sorted(self.storage.root.rglob('*')), before)
        self.assertIsNone(value['coldBuildPeakBytes'])
        self.assertTrue(value['recordedCandidatesAreNotVerifiedReuse'])
        self.assertFalse(value['physicalCloneSharingMeasured'])
        self.assertEqual(len(value['ownerGuards']), 17)
        self.assertEqual(value['largestStepGuardBytes'], 166*core.GIB)
        self.assertEqual(value['sumOfStepReservationsBytes'], 285*core.GIB)

    def test_footprint_never_follows_links_and_counts_hardlink_once(self):
        self.fixture()
        path = self.storage.path('cache'); path.mkdir(); (path/'one').write_bytes(b'123')
        os.link(path/'one', path/'two'); (path/'outside').symlink_to(self.base)
        value = space.footprint(path, lambda:None)
        self.assertEqual(value['files'], 1); self.assertEqual(value['logicalBytes'], 3)
        self.assertEqual(value['linksNotFollowed'], 1)

    def test_cli_space_does_not_initialize_new_workspace(self):
        self.fixture(); destination = self.base/'new-space'
        with redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main(['space','--profile','operator','--storage',str(destination)]), 0)
        self.assertFalse(destination.exists())

    def test_corrupt_record_does_not_count_as_candidate(self):
        self.fixture(); self.state['builds']['bad-key'] = {'target':'gateway','inputs':{}}
        with self.assertRaisesRegex(core.LabError, 'identity differs'):
            space.report(self.storage, self.state)

    def test_cache_cli_rejects_missing_source(self):
        with redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main(['cache','--storage',str(self.storage.root)]), 1)

    def test_guard_table_tracks_current_owner_reservations(self):
        # Fail on recipe drift rather than silently presenting stale capacity numbers.
        expected = {'build': ('additional=2*GIB, reserve=90*GIB',),
            'cloud': ('additional=GIB, reserve=90*GIB',),
            'containers': ('additional=2*GIB',), 'services': ('additional=8*GIB, reserve=90*GIB',),
            'gateway': ('additional=2*GIB, reserve=90*GIB',),
            'packaging': ('additional=8*GIB, reserve=90*GIB',),
            'host': ('additional=24*GIB, reserve=90*GIB',),
            'package_chain': ("additional=(40 if target == 'application' else 1)*GIB, reserve=90*GIB",),
            'media': ("additional=(76 if target == 'dmg' else 2)*GIB, reserve=90*GIB",)}
        for module, expressions in expected.items():
            text = (core.ROOT/'scripts/reproduction'/f'{module}.py').read_text()
            for expression in expressions:
                self.assertIn('storage.check('+expression+')', text, module)
        self.assertEqual(core.Storage.check.__defaults__, (0,60*core.GIB))

    def test_unreviewed_plan_cannot_reuse_capacity_claim(self):
        self.fixture(); original = space.chain.read_plan(self.release)
        changed = copy.deepcopy(original); changed['producers']['media'] = 'f'*40
        with patch.object(space.chain, 'read_plan', side_effect=[changed,original,original,original]):
            with self.assertRaisesRegex(core.LabError, 'reviewed producer'):
                space.report(self.storage, self.state, build_plan=Path('different.json'))

    def test_source_factory_plan_is_supported_without_changing_its_pins(self):
        self.fixture()
        plan = core.ROOT/'workspace/releases/1.2.0-rc.1-source-factory-build-chain.json'
        before = plan.read_bytes()
        value = space.report(self.storage, self.state, build_plan=plan)
        self.assertEqual(plan.read_bytes(), before)
        self.assertEqual(len(value['ownerGuards']), 17)

    def test_public_plan_preserves_steps_and_only_adopts_component_storage_fix(self):
        self.fixture()
        old = space.chain.read_plan(self.release, core.ROOT/'workspace/releases/1.2.0-rc.1-source-factory-build-chain.json')
        path = core.ROOT/'workspace/releases/1.2.0-rc.1-public-build-chain-r1.json'
        new = space.chain.read_plan(self.release, path)
        self.assertEqual(new['steps'], old['steps'])
        self.assertEqual(new['baseDefinitionSha256'], old['baseDefinitionSha256'])
        self.assertNotEqual(new['producers']['components'], old['producers']['components'])
        self.assertEqual({k:v for k,v in new['producers'].items() if k != 'components'},
                         {k:v for k,v in old['producers'].items() if k != 'components'})
        self.assertEqual(len(space.report(self.storage, self.state, build_plan=path)['ownerGuards']), 17)

    def test_fresh_developer_workspace_does_not_require_a_prepared_wheel_source(self):
        value = space.report(self.storage, self.state)
        self.assertFalse(value['cache']['wheelScopeComplete'])
        self.assertFalse(value['storagePreflightComplete'])
        self.assertFalse(value['qualified'])

    def test_non_docker_target_does_not_probe_or_require_engine(self):
        self.fixture()
        with patch.object(space.containers, 'inspect_storage', side_effect=AssertionError):
            value = space.report(self.storage, self.state, target='presenter', docker=Path('/unused'))
        self.assertTrue(value['storagePreflightComplete'])

    def test_separate_docker_capacity_is_visible_and_not_added_to_workspace_free(self):
        self.fixture()
        disk = self.base/'Docker.raw'; disk.touch()
        volume = {**self.volume, 'uuid':'DOCKER', 'pool':'disk8'}
        with patch.object(space.containers, 'inspect_storage', return_value={'disk':disk,'volume':volume}), \
             patch.object(space.chain, 'storage_compatibility', return_value={'compatible':True}):
            value = space.report(self.storage, self.state, docker=Path('/unused'))
        self.assertEqual(len(value['capacityPools']), 2)
        self.assertEqual(value['freeBytes'], 300*core.GIB)
        self.assertTrue(value['storagePreflightComplete'])

    def test_missing_engine_cannot_report_completed_storage_preflight(self):
        self.fixture()
        with patch.object(space.containers, 'inspect_storage', side_effect=core.LabError('stopped')):
            value = space.report(self.storage, self.state, docker=Path('/unused'))
        self.assertEqual(value['dockerStorage']['status'], 'BLOCKED')
        self.assertEqual(value['dockerStorage']['reason'], 'stopped')
        self.assertFalse(value['storagePreflightComplete'])


if __name__ == '__main__':
    unittest.main()
