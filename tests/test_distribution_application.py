# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts/distribution'
with patch.object(sys, 'path', [str(SCRIPTS), *sys.path]):
    SPEC = importlib.util.spec_from_file_location('distribution_application', SCRIPTS / 'application.py')
    module = importlib.util.module_from_spec(SPEC)
    SPEC.loader.exec_module(module)


class ApplicationExportTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name).resolve()
        self.app = self.root / 'source'; self.app.mkdir()
        self.output = self.root / 'Output with spaces'
        self.tracked = [module.PACKAGE / name for name in ('__init__.py', 'cli.py', 'presenter.py')]
        for name in (*self.tracked, *(module.PACKAGE / n for n in module.REVIEWED)):
            self.put(self.app, str(name), b'# reviewed module\n')
        for name in module.EXTRA:
            self.put(self.app, name, b'{}' if name.endswith('.json') else b'MIT\n')
        mock = patch.object(module, 'tracked', return_value=self.tracked)
        mock.start(); self.addCleanup(mock.stop)

    def put(self, root, name, raw):
        path = root / name; path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw); return path

    def group(self, backend=False):
        root = self.root / 'input'; root.mkdir()
        name = 'backends.tar' if backend else 'payload/file'
        raw = b'public bytes'
        self.put(root, name, raw)
        digest = hashlib.sha256(raw).hexdigest()
        manifest = ({'archiveBytes': len(raw), 'archiveSha256': digest} if backend else
                    {'files': [dict(path=name, bytes=len(raw), sha256=digest)]})
        data = json.dumps(manifest).encode()
        self.put(root, 'manifest.json', data)
        lock = json.dumps({'manifest': dict(path='manifest.json', bytes=len(data),
                                           sha256=hashlib.sha256(data).hexdigest())}).encode()
        return root, lock

    def test_explicit_new_modules_and_contracts_included_state_excluded(self):
        self.put(self.app, '.run/secret.pem', b'sentinel not exported')
        self.put(self.app, '.local/demo-control/status.json', b'sentinel not exported')
        files = module.export_plan(self.app)
        self.assertEqual(set(files), {*map(str, self.tracked),
            *(str(module.PACKAGE / n) for n in module.REVIEWED), *module.EXTRA})
        self.assertFalse(any(b'sentinel' in raw for raw in files.values()))
        self.assertIn('config/aosvm-single-node-unitconfig.json', files)
        self.assertIn(str(module.PACKAGE / 'runtime_paths.py'), files)

    def test_unreviewed_module_fails(self):
        self.put(self.app, str(module.PACKAGE / 'surprise.py'), b'pass')
        with self.assertRaisesRegex(module.BundleError, 'Unreviewed or missing'):
            module.export_plan(self.app)

    def test_missing_selector_fails(self):
        (self.app / module.PACKAGE / 'host_entry.py').unlink()
        with self.assertRaisesRegex(module.BundleError, 'Unreviewed or missing'):
            module.export_plan(self.app)

    def test_unresolved_relative_import_fails(self):
        self.put(self.app, str(module.PACKAGE / 'cli.py'), b'from . import forgotten\n')
        with self.assertRaisesRegex(module.BundleError, 'import closure incomplete'):
            module.export_plan(self.app)

    def test_valid_relative_imports_pass(self):
        self.put(self.app, str(module.PACKAGE / 'cli.py'), b'from . import host_runtime\nfrom .presenter import main\n')
        module.export_plan(self.app)

    def test_package_version_export_is_not_a_missing_module(self):
        self.put(self.app, str(module.PACKAGE / '__init__.py'), b'__version__ = "0.1.0"\n')
        self.put(self.app, str(module.PACKAGE / 'cli.py'), b'from . import __version__\n')
        module.export_plan(self.app)

    def test_symlink_module_rejected(self):
        path = self.app / module.PACKAGE / 'cli.py'
        path.unlink(); path.symlink_to(self.app / 'LICENSE')
        with self.assertRaisesRegex(module.BundleError, 'symlink'):
            module.export_plan(self.app)

    def test_unsafe_mode_rejected(self):
        (self.app / module.PACKAGE / 'cli.py').chmod(0o666)
        with self.assertRaisesRegex(module.BundleError, 'Unsafe application input'):
            module.export_plan(self.app)

    def test_pinned_group_and_backend_archive_shapes(self):
        root, lock = self.group(True)
        pin, rows, size = module.checked_group(root, lock)
        self.assertEqual('backends.tar', rows[0]['path'])
        self.assertEqual(12, size)
        self.assertEqual('manifest.json', pin['path'])

    def test_extra_file_or_symlink_rejected(self):
        root, lock = self.group()
        extra = self.put(root, 'extra.py', b'pass')
        with self.assertRaisesRegex(module.BundleError, 'inventory mismatch'):
            module.checked_group(root, lock)
        extra.unlink(); extra.symlink_to(root / 'payload/file')
        with self.assertRaisesRegex(module.BundleError, 'contains link'):
            module.checked_group(root, lock)

    def test_changed_manifest_rejected(self):
        root, lock = self.group()
        (root / 'manifest.json').write_text('{}')
        with self.assertRaisesRegex(module.BundleError, 'manifest size mismatch'):
            module.checked_group(root, lock)

    def test_bad_payload_size_rejected(self):
        root, lock = self.group()
        (root / 'payload/file').write_text('different size')
        with self.assertRaisesRegex(module.BundleError, 'payload size/mode mismatch'):
            module.checked_group(root, lock)

    def test_existing_output_preserved(self):
        self.output.mkdir(); self.put(self.output, 'keep', b'keep')
        with self.assertRaisesRegex(module.BundleError, 'Output must be new'):
            module.assemble(self.app, {}, self.output)
        self.assertEqual(b'keep', (self.output / 'keep').read_bytes())

    def test_low_disk_blocks_before_assembly(self):
        with patch.object(module.shutil, 'disk_usage', return_value=SimpleNamespace(free=90*2**30)), \
                self.assertRaisesRegex(module.BundleError, 'Disk reserve exceeded'):
            module.assemble(self.app, {k: self.root for k in module.LOCKS}, self.output)
        self.assertFalse(self.output.exists())


if __name__ == '__main__':
    unittest.main()
