# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import importlib.util
import json
from pathlib import Path
import plistlib
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts/distribution'
with patch.object(sys, 'path', [str(SCRIPTS), *sys.path]):
    SPEC = importlib.util.spec_from_file_location('ui_build', SCRIPTS / 'ui_build.py')
    module = importlib.util.module_from_spec(SPEC)
    SPEC.loader.exec_module(module)


class UIBuildTests(unittest.TestCase):
    def test_minimum_macos_matches_the_compiled_target(self):
        original = {'CFBundleExecutable': 'KeyboardControl', 'LSMinimumSystemVersion': '13.0',
                    'CFBundleIdentifier': 'unchanged'}
        raw = plistlib.dumps(original)
        actual = plistlib.loads(module.controller_metadata(raw))
        self.assertEqual(actual, dict(original, LSMinimumSystemVersion='26.0'))
        self.assertEqual(plistlib.loads(raw), original)

    def test_wrong_native_entrypoint_rejected(self):
        with self.assertRaises(module.BundleError):
            module.controller_metadata(plistlib.dumps({'CFBundleExecutable': 'Other'}))

    def test_existing_output_rejected_before_build(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            with self.assertRaisesRegex(module.BundleError, 'Output must be new'):
                module.build(root, root, root, root)

    def test_low_disk_rejected_before_build(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            with patch.object(module.shutil, 'disk_usage', return_value=type('Usage', (), {'free': 1})()):
                with self.assertRaisesRegex(module.BundleError, 'disk reserve'):
                    module.build(root, root, root, root / 'output')
            self.assertFalse((root / 'output').exists())

    def test_wrong_node_pin_does_not_start_compiler(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            paths = [module.PACKAGE / 'native/PresenterWorkspace.swift',
                     Path('tools/KeyboardControl.swift'), Path('tools/KeyboardControl-Info.plist'),
                     Path('apps/presenter-ui/package.json')]
            for path in paths:
                (root / path).parent.mkdir(parents=True, exist_ok=True)
                (root / path).write_text('{}')
            (root / paths[-1]).write_text(json.dumps({'engines': {'node': '26.0.0'}}))
            with patch.object(module, 'tracked', return_value=[paths[-1]]), \
                    patch.object(module.subprocess, 'check_output', return_value='v25.0.0\n'), \
                    patch.object(module.shutil, 'disk_usage', return_value=type('Usage', (), {'free': 200 * 2**30})()):
                with self.assertRaisesRegex(module.BundleError, 'Node version'):
                    module.build(root, root, root, root / 'output')
            self.assertFalse((root / 'output').exists())


if __name__ == '__main__':
    unittest.main()
