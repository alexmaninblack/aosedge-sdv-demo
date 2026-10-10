# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
import copy
import hashlib
import json
import sys
import unittest
from unittest.mock import patch

from test_reproduction import StorageFixture
from reproduction import core, build_results, chain, chain_worker, package_chain, media

sys.path.insert(0, str(core.ROOT/'scripts/distribution'))
from developer_inputs import DeveloperInputs
import candidate_inputs
from native_bundle import BundleError


class SealedResultsTests(StorageFixture, unittest.TestCase):
    def fixture(self):
        source = self.base/'backend'
        source.mkdir()
        (source/'archive-receipt.json').write_text('{}')
        return build_results.seal(self.storage, {'backend-export': 'a'*64}, {'backend-export': source})

    def test_seal_repeat_and_typed_checkpoint_preserve_contract(self):
        path, key, checkpoint, release = self.fixture()
        sealed = DeveloperInputs.load(path, key)
        original = core.read_json(core.ROOT/'contracts'/candidate_inputs.LOCKS['backend-inputs'])
        result = json.loads(candidate_inputs.locks(core.ROOT, sealed, ('backend-inputs',))['backend-inputs'])
        self.assertEqual(result['manifest'], checkpoint['manifests']['backend-inputs'])
        result.pop('manifest'); original.pop('manifest')
        self.assertEqual(result, original)
        self.assertIsNone(release)
        self.assertEqual(build_results.seal(self.storage, {'backend-export': 'a'*64},
            {'backend-export': self.base/'backend'})[:2], (path, key))
        self.assertEqual(candidate_inputs.identity(core.ROOT, sealed),
                         {'kind':'developer-build-results', 'sha256':key})
        with self.assertRaisesRegex(BundleError, 'Incomplete'):
            candidate_inputs.setup_release(core.ROOT, sealed)

    def test_changed_bytes_links_modes_and_digest_refused(self):
        path, key, _, _ = self.fixture()
        for expected in ('0'*64, '../escape'):
            with self.assertRaisesRegex(BundleError, 'digest differs'):
                DeveloperInputs.load(path, expected)
        linked = self.base/'linked'
        linked.symlink_to(path)
        with self.assertRaisesRegex(BundleError, 'Linked'):
            DeveloperInputs.load(linked, key)
        path.chmod(0o666)
        with self.assertRaisesRegex(BundleError, 'Unsafe'):
            DeveloperInputs.load(path, key)
        path.chmod(0o644)
        path.write_bytes(b'{}')
        with self.assertRaisesRegex(BundleError, 'digest differs'):
            DeveloperInputs.load(path, key)

    def test_invalid_pin_base_source_and_extra_fields_refused(self):
        path, key, _, _ = self.fixture()
        value = json.loads(path.read_bytes())
        changes = [lambda v: v.update(extra=True),
                   lambda v: v['checkpoint']['manifests']['backend-inputs'].update(path='../escape'),
                   lambda v: v['checkpoint'].update(baseDefinitionSha256='0'*64),
                   lambda v: v.update(sources={'wrong':{}})]
        for change in changes:
            v = copy.deepcopy(value); change(v)
            raw = json.dumps(v).encode()
            sealed = DeveloperInputs(raw, hashlib.sha256(raw).hexdigest())
            with self.assertRaises(BundleError):
                candidate_inputs.pins(core.ROOT, sealed, ('backend-inputs',))

    def test_plain_file_cannot_opt_into_developer_authority(self):
        _, _, value, _ = self.fixture()
        path = self.base/'plain.json'
        path.write_text(json.dumps(value))
        with self.assertRaisesRegex(BundleError, 'invalid packaging checkpoint'):
            candidate_inputs.pins(self.base, 'plain.json', ('backend-inputs',))

    def test_complete_application_binds_release_to_exact_manifest(self):
        kit = self.base/'application'; kit.mkdir()
        pins = {k: core.read_json(core.ROOT/'contracts'/v)['manifest'] for k,v in candidate_inputs.LOCKS.items()}
        (kit/'application-manifest.json').write_text(json.dumps({'inputs':pins}))
        path, key, _, trusted = build_results.seal(self.storage, {'application':'b'*64}, {}, application=kit)
        selected = DeveloperInputs.load(path, key)
        self.assertEqual(candidate_inputs.setup_release(core.ROOT, selected), trusted)
        self.assertEqual(json.loads(selected.release_bytes()), trusted)

    def test_modes_cannot_be_mixed_before_upstream_work(self):
        with patch.object(package_chain, 'verify_sources') as verify:
            with self.assertRaisesRegex(core.LabError, 'Cannot mix'):
                package_chain.assemble(self.storage, self.state, 'backend-inputs', None, sys.executable,
                                       None, 'old.json', developer_results=True)
            verify.assert_not_called()
        with patch.object(media, 'verify_sources') as verify:
            with self.assertRaisesRegex(core.LabError, 'Cannot mix'):
                media.assemble(self.storage, self.state, 'setup', sys.executable, 'A'*40, None,
                               'old.json', 'release.json', developer_results=True)
            verify.assert_not_called()

    def test_schema_two_requires_exact_policy_and_schema_one_unchanged(self):
        plan = chain.read_plan(self.release)
        self.assertEqual(plan['schemaVersion'], 1)
        plan.update(schemaVersion=2, resultPolicy='seal-developer-results-v1')
        with patch.object(chain, 'read_json', return_value=plan):
            self.assertEqual(chain.read_plan(self.release), plan)
            plan['resultPolicy'] = 'trust-everything'
            with self.assertRaises(core.LabError):
                chain.read_plan(self.release)

    def test_policy_forwarded_only_to_downstream_owners(self):
        options = dict(python='python', kit_inputs='kit', signing_identity='A'*40,
                       developer_results=True, prepare_dependencies=False)
        for target in ('backend-inputs', 'vm-runtime', 'application', 'setup', 'dmg'):
            with patch.object(chain_worker.importlib, 'import_module') as module:
                chain_worker.dispatch(None, None, target, None, options, None)
                self.assertTrue(module.return_value.assemble.call_args.kwargs['developer_results'])


if __name__ == '__main__':
    unittest.main()
