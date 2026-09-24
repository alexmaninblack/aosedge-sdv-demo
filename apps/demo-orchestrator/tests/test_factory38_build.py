# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import inspect
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from aosedge_demo_orchestrator import component_runtime as runtime
from aosedge_demo_orchestrator import factory_mainline_gates as gates


class DiagnosticSuccessorFactoryTests(unittest.TestCase):
    def test_successor_pin_does_not_replace_37(self):
        self.assertEqual(runtime.FACTORY_RELEASES['6.1.1-maninblack.38'],
                         '378c00efad0ec67b2fb0c90328b68c4e8970b511')
        self.assertEqual(runtime.FACTORY_RELEASES['6.1.1-maninblack.37'],
                         '77d99770a3d9476736da55c3e2196396899bc563')

    def test_native_counts_preserve_37_and_require_async_cases_for_38(self):
        self.assertEqual(gates.SM_LAUNCHER_TEST_COUNTS, {"37": 27, "38": 32, "39": 32})
        with tempfile.TemporaryDirectory() as directory:
            native = gates.NativeGates(Path('/unused'), Path(directory) / 'new', '38')
            self.assertEqual(native.factory_suffix, '38')
            self.assertIn('SM_LAUNCHER_TEST_COUNTS[self.factory_suffix]', inspect.getsource(native.run))
            with self.assertRaises(ValueError):
                gates.NativeGates(Path('/unused'), Path(directory) / 'bad', '40')
            self.assertFalse((Path(directory) / 'bad').exists())

    def test_gate_export_uses_successor_config_and_separate_evidence(self):
        calls = []
        with patch.object(runtime.subprocess, 'check_output',
                          side_effect=[b'', b'a' * 40, b'archive']), \
             patch.object(runtime.subprocess, 'run') as run:
            result = runtime.stage_mainline_factory_gates([], calls.append, '/build', '/source', '38')
        run.assert_called_once()
        self.assertIn('/factory38-gates-', result['conf'])
        self.assertIn('/qualification/factory-38.conf', '\n'.join(calls))
        self.assertNotIn('/qualification/factory-37.conf', '\n'.join(calls))

    def test_unknown_gate_version_rejected_before_source_or_remote(self):
        with patch.object(runtime.subprocess, 'check_output') as read:
            with self.assertRaisesRegex(runtime.EnvironmentError, 'UNSUPPORTED'):
                runtime.stage_mainline_factory_gates([], lambda *_: self.fail(), '', '', '40')
            read.assert_not_called()

    def test_policy_and_native_matrix_gate_image_and_keep_guards(self):
        source = inspect.getsource(runtime.build_factory)
        self.assertIn('targets += " refpolicy-aos"', source)
        self.assertLess(source.index('targets += " refpolicy-aos"'), source.index('"-c compile "'))
        self.assertIn('" --factory-suffix " + suffix', source)
        self.assertLess(source.index('" native --root "'), source.index('"package the managers'))
        self.assertLess(source.index('" package --root "'), source.index('flags + "aos-image-vm"'))
        for guard in ('FACTORY_COMMITTED_SOURCE_REQUIRED', 'FACTORY_SOURCE_REVISION_MISMATCH',
                      'FACTORY_ARTIFACT_EXISTS_RECONCILE_WITHOUT_REBUILD',
                      'FACTORY_HOST_FREE_SPACE_BELOW_60_GIB', 'FACTORY_BUILDER_FREE_SPACE_BELOW_60_GIB'):
            self.assertIn(guard, source)


if __name__ == '__main__':
    unittest.main()
