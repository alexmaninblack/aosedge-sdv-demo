# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest

from test_reproduction import StorageFixture
from reproduction import core, host, package_chain as module


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


if __name__ == '__main__':
    unittest.main()
