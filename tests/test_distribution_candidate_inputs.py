# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
import copy
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts/distribution'))
import candidate_inputs as module


class CandidateInputTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.checkpoint = 'workspace/releases/1.2.0-rc.1-packaging.json'
        for name in ('workspace/releases/kit028-setup042.json', self.checkpoint,
                     *('contracts/'+p for p in module.LOCKS.values())):
            path = self.root/name
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT/name, path)
        self.value = json.loads((self.root/self.checkpoint).read_bytes())

    def save(self):
        (self.root/self.checkpoint).write_text(json.dumps(self.value))

    def test_reviewed_manifest_only_contract_fields_unchanged(self):
        raw = module.locks(self.root, self.checkpoint, ('backend-inputs',))['backend-inputs']
        result = json.loads(raw)
        original = json.loads((self.root/'contracts'/module.LOCKS['backend-inputs']).read_bytes())
        self.assertEqual(result['manifest'], self.value['manifests']['backend-inputs'])
        result.pop('manifest'); original.pop('manifest')
        self.assertEqual(result, original)

    def test_incomplete_checkpoint_cannot_assemble_complete_application(self):
        self.value['manifests'].pop('vm-runtime', None)
        self.save()
        with self.assertRaisesRegex(module.BundleError, 'Incomplete'):
            module.locks(self.root, self.checkpoint, module.LOCKS)

    def test_full_checkpoint_and_historical_source_unchanged(self):
        original = (self.root/'contracts'/module.LOCKS['vm-runtime']).read_bytes()
        self.value['manifests']['vm-runtime'] = json.loads(original)['manifest']
        self.save()
        self.assertEqual(set(module.locks(self.root, self.checkpoint, module.LOCKS)), set(module.LOCKS))
        self.assertEqual((self.root/'contracts'/module.LOCKS['vm-runtime']).read_bytes(), original)

    def test_unknown_fields_and_wrong_baseline_fail(self):
        self.value['unexpected'] = True
        self.save()
        with self.assertRaisesRegex(module.BundleError, 'invalid packaging'):
            module.pins(self.root, self.checkpoint, ('host-runtime',))
        self.value.pop('unexpected')
        self.value['baseDefinitionSha256'] = 'f'*64
        self.save()
        with self.assertRaisesRegex(module.BundleError, 'baseline differs'):
            module.pins(self.root, self.checkpoint, ('host-runtime',))

    def test_invalid_manifest_fields_rejected(self):
        original = copy.deepcopy(self.value)
        for key, value in [('path', '../escape'), ('bytes', True), ('sha256', 'bad')]:
            self.value = copy.deepcopy(original)
            self.value['manifests']['host-runtime'][key] = value
            self.save()
            with self.assertRaisesRegex(module.BundleError, 'pin invalid'):
                module.pins(self.root, self.checkpoint, ('host-runtime',))

    def test_link_and_escape_rejected(self):
        path = self.root/self.checkpoint
        path.unlink()
        path.symlink_to(ROOT/self.checkpoint)
        with self.assertRaisesRegex(module.BundleError, 'symlink'):
            module.pins(self.root, self.checkpoint, ('host-runtime',))
        with self.assertRaisesRegex(module.BundleError, 'Unsafe relative'):
            module.pins(self.root, '../escape', ('host-runtime',))

    def test_setup_independent_pin_validation(self):
        name = 'workspace/releases/setup-fixture.json'
        good = {'schemaVersion': 1, 'label': 'Engineering fixture', 'manifestSha256': 'a'*64}
        (self.root/name).write_text(json.dumps(good))
        self.assertEqual(module.setup_release(self.root, name), good)
        for change in ({'manifestSha256': 'bad'}, {'extra': True}, {'schemaVersion': True}):
            (self.root/name).write_text(json.dumps({**good, **change}))
            with self.assertRaisesRegex(module.BundleError, 'Invalid reviewed Setup'):
                module.setup_release(self.root, name)


if __name__ == '__main__':
    unittest.main()
