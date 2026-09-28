# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts/distribution'
with patch.object(sys, 'path', [str(SCRIPTS), *sys.path]):
    SPEC = importlib.util.spec_from_file_location('ui_helpers', SCRIPTS / 'ui_helpers.py')
    module = importlib.util.module_from_spec(SPEC)
    SPEC.loader.exec_module(module)


class UIHelperTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.integration, self.gateway, self.inputs = (self.root / n for n in ('integration', 'gateway', 'inputs'))
        self.pyfiles = [module.PACKAGE / p for p in ('__init__.py', 'presenter.py')]
        for path in self.pyfiles:
            self.put(self.integration / path, b'# fixture')
        self.gwfiles = [Path('tools') / name for name in module.HELPERS]
        self.gwfiles += [Path('config/m6_2_town10hd_handover.json')]
        for path in self.gwfiles:
            self.put(self.gateway / path, b'{}')
        for directory in (self.integration, self.gateway):
            self.put(directory / 'LICENSE', b'MIT')
        hashes = {}
        for path in (self.integration / module.PACKAGE / 'native/PresenterWorkspace.swift',
                     self.gateway / 'tools/KeyboardControl.swift', self.gateway / 'tools/KeyboardControl-Info.plist',
                     self.integration / 'apps/presenter-ui/package-lock.json'):
            self.put(path, b'input')
            hashes[str(path)] = module.sha256(path)
        files = []
        for name in ('native/Demo Presenter', 'native/Driving Control.app/Contents/Info.plist',
                     'native/Driving Control.app/Contents/MacOS/KeyboardControl', 'web/index.html',
                     'web/assets/index.js', 'web/assets/index.css'):
            self.put(self.inputs / name, b'output')
            files.append(dict(path=name, bytes=6, sha256=module.sha256(self.inputs / name)))
        self.receipt = dict(status='BUILT_NOT_RUNTIME_QUALIFIED', sourcesUnchanged=True,
                            inputHashes=hashes, files=files, swift='fixture', node='fixture',
                            architecture='arm64', initialMacOSTarget='26.0')
        self.save_receipt()
        self.tracked = patch.object(module, 'tracked', side_effect=lambda root, scope:
                                    self.pyfiles if root == self.integration else self.gwfiles)
        self.tracked.start()
        self.addCleanup(self.tracked.stop)

    def put(self, path, data):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def save_receipt(self):
        (self.inputs / 'build-receipt.json').write_text(json.dumps(self.receipt))

    def test_plan_uses_only_explicit_sources_and_build_outputs(self):
        self.put(self.integration / '.run/private.pem', b'not copied')
        self.put(self.gateway / 'tools/experiment.py', b'not copied')
        files, _ = module.plan(self.integration, self.gateway, self.inputs)
        self.assertEqual(len(files), 20)
        self.assertFalse(any('private' in str(p) or 'experiment' in str(p) for p in files))
        self.assertIn(Path('demo/apps/presenter-ui/dist/index.html'), files)

    def test_unsafe_relative_paths_rejected(self):
        for value in ('', '/root', '../outside', 'assets/../outside', './a', 'a\\b', 'a\nb'):
            with self.subTest(value=value), self.assertRaises(module.BundleError):
                module.safe_relative(value)

    def test_web_private_files_and_source_maps_rejected(self):
        for value in ('secret.json', '.env', 'assets/index.js.map', 'assets/.secret.js', '../a.js'):
            self.assertFalse(module.web_allowed(Path(value)))
        self.assertTrue(module.web_allowed(Path('.vite/manifest.json')))

    def test_symlink_not_followed(self):
        target = self.gateway / self.gwfiles[0]
        target.unlink()
        target.symlink_to(self.integration / 'LICENSE')
        with self.assertRaisesRegex(module.BundleError, 'symlink'):
            module.plan(self.integration, self.gateway, self.inputs)

    def test_changed_build_bytes_rejected(self):
        self.put(self.inputs / 'web/index.html', b'wrong!')
        with self.assertRaisesRegex(module.BundleError, 'changed after receipt'):
            module.plan(self.integration, self.gateway, self.inputs)

    def test_changed_source_rejected(self):
        self.put(self.gateway / 'tools/KeyboardControl.swift', b'changed')
        with self.assertRaisesRegex(module.BundleError, 'Source no longer matches'):
            module.plan(self.integration, self.gateway, self.inputs)

    def test_incomplete_build_rejected(self):
        self.receipt['status'] = 'BUILDING'
        self.save_receipt()
        with self.assertRaisesRegex(module.BundleError, 'completed receipt'):
            module.plan(self.integration, self.gateway, self.inputs)

    def test_duplicate_build_receipt_rejected(self):
        self.receipt['files'].append(self.receipt['files'][0])
        self.save_receipt()
        with self.assertRaisesRegex(module.BundleError, 'duplicate'):
            module.plan(self.integration, self.gateway, self.inputs)

    def test_missing_recorded_file_rejected(self):
        (self.inputs / 'web/assets/index.css').unlink()
        with self.assertRaisesRegex(module.BundleError, 'inventory mismatch'):
            module.plan(self.integration, self.gateway, self.inputs)

    def test_existing_output_never_overwritten(self):
        output = self.root / 'output'
        output.mkdir()
        with self.assertRaisesRegex(module.BundleError, 'Output must be new'):
            module.assemble(self.integration, self.gateway, self.inputs, output)

    def test_low_disk_fails_before_output(self):
        output = self.root / 'output'
        with patch.object(module.shutil, 'disk_usage', return_value=type('Usage', (), {'free': 1})()):
            with self.assertRaisesRegex(module.BundleError, 'budget'):
                module.assemble(self.integration, self.gateway, self.inputs, output)
        self.assertFalse(output.exists())

    def test_assembly_hashes_sources_and_never_changes_selectors(self):
        output = self.root / 'output'
        with patch.object(module, 'verify_native'), patch.object(module, 'command', return_value='revision'), \
                patch.object(module.shutil, 'disk_usage', return_value=type('Usage', (), {'free': 200 * 2**30})()):
            result = module.assemble(self.integration, self.gateway, self.inputs, output)
        self.assertFalse(result['runtimeSelectorsChanged'])
        for row in result['files']:
            self.assertEqual(row['sha256'], module.sha256(output / row['path']))
        self.assertEqual((output / 'native/Demo Presenter').stat().st_mode & 0o777, 0o755)


if __name__ == '__main__':
    unittest.main()
