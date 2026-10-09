# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from test_reproduction import StorageFixture
from reproduction import core, host, package_chain as module
from reproduction.artifacts import sha256


class PackageChainTests(StorageFixture, unittest.TestCase):
    def fixture(self):
        self.storage.environment()
        self.patch('reproduction.package_chain.verify_sources')
        self.patch('reproduction.packaging.producer', return_value=({'recipe': 'a'*40}, 'b'*40))
        self.patch('reproduction.package_chain.upstream', side_effect=lambda s, state, role: (role, self.base/role))
        self.command = self.patch('reproduction.package_chain.run_command', side_effect=self.owner)

    def owner(self, args, **kwargs):
        output = Path(args[-2])
        output.mkdir()
        target = args[-4]
        core.atomic_json(output/module.MANIFESTS[target], {'fixture': True})
        (output/'payload').write_bytes(b'fixture')
        return SimpleNamespace(returncode=0, stdout=b'{}', stderr=b'')

    def build(self, target='backend-inputs'):
        return module.assemble(self.storage, self.state, target, self.base, sys.executable, lambda *args: None)

    def test_first_repeat_and_interrupted_outer_state_recovery(self):
        self.fixture()
        key = self.build()
        self.assertEqual(self.build(), key)
        del self.state['builds'][key]
        self.assertEqual(self.build(), key)
        self.assertEqual(self.command.call_count, 1)

    def test_corrupt_and_extra_output_refused(self):
        self.fixture()
        key = self.build()
        output = self.storage.path('builds/backend-inputs/'+key)
        (output/'extra').write_text('extra')
        with self.assertRaisesRegex(core.LabError, 'inventory differs'):
            self.build()
        (output/'extra').unlink()
        (output/'payload').write_text('changed')
        with self.assertRaisesRegex(core.LabError, 'output changed'):
            self.build()

    def test_owner_failure_preserved_not_retried(self):
        self.fixture()
        def fail(args, **kwargs):
            result = self.owner(args, **kwargs)
            result.returncode = 1
            return result
        self.command.side_effect = fail
        with self.assertRaisesRegex(core.LabError, 'owner failed'):
            self.build()
        with self.assertRaises(FileNotFoundError):
            self.build()
        self.assertEqual(self.command.call_count, 1)

    def test_application_needs_each_selected_group_and_offline_worker(self):
        self.fixture()
        self.build('application')
        args = self.command.call_args.args[0]
        selected = core.read_json(args[-3])
        self.assertEqual(set(selected), set(module.GROUP_TARGETS.values()))
        self.assertIn('(deny network*)', Path(args[2]).read_text())

    def test_explicit_pin_selects_one_upstream_without_dropping_history(self):
        for value in ('old', 'new'):
            inputs = {'generation':value}
            key = core.digest(inputs)
            self.state['builds'][key] = {'target':'application', 'inputs':inputs}
            output = self.storage.path('builds/application/'+key)
            output.mkdir(parents=True)
            (output/'application-manifest.json').write_text(value)
        pin = {'path':'application-manifest.json', 'sha256':sha256(output/'application-manifest.json')}
        with patch('reproduction.package_chain.verify'):
            with self.assertRaisesRegex(core.LabError, 'Exactly one'):
                module.upstream(self.storage, self.state, 'application')
            self.assertEqual(module.upstream(self.storage, self.state, 'application', pin)[0], key)
            pin['sha256'] = '0'*64
            with self.assertRaisesRegex(core.LabError, 'Exactly one'):
                module.upstream(self.storage, self.state, 'application', pin)
        self.assertEqual(len(self.state['builds']), 2)

    def test_explicit_checkpoint_passed_to_owner_and_fingerprinted(self):
        self.fixture()
        original = core.read_json(core.ROOT/module.CHECKPOINT)
        for name in ('package_chain.py', 'package_worker.py'):
            destination = self.base/'scripts/reproduction'/name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes((core.ROOT/'scripts/reproduction'/name).read_bytes())
        self.patch('reproduction.package_chain.ROOT', self.base)
        self.patch('reproduction.package_chain.upstream', side_effect=lambda s, state, role, pin: (role, self.base/role))
        core.atomic_json(self.base/'candidate.json', original)
        key = module.assemble(self.storage, self.state, 'application', self.base, sys.executable,
                              lambda *args: None, 'candidate.json')
        self.assertEqual(self.command.call_args.args[0][-1], 'candidate.json')
        self.assertEqual(self.state['builds'][key]['inputs']['checkpoint'], original)
        with self.assertRaises(core.LabError):
            module.assemble(self.storage, self.state, 'application', self.base, sys.executable,
                            lambda *args: None, '../outside.json')


if __name__ == '__main__':
    unittest.main()
