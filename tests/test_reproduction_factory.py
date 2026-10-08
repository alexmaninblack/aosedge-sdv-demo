# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Factory recipe generation does not inherit warm configuration or outputs."""
import hashlib
import io
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from reproduction import factory
from reproduction.core import LabError


class FactoryRecipeTests(unittest.TestCase):
    @unittest.skipUnless(sys.platform == 'darwin', 'macOS archive metadata regression')
    def test_transfer_excludes_macos_appledouble_sidecars(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'recipe.json'
            path.write_bytes(b'{}\n')
            subprocess.run(['/usr/bin/xattr', '-w', 'com.aosedge.reproduction.test', 'metadata', str(path)], check=True)
            with factory.input_archive(directory, [path.name]) as process:
                raw, _ = process.communicate(timeout=10)
                self.assertEqual(process.returncode, 0)
            with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
                self.assertEqual(archive.getnames(), [path.name])
                self.assertEqual(archive.extractfile(path.name).read(), b'{}\n')

    def test_successor_changes_only_version_and_platform(self):
        original = (ROOT / factory.TEMPLATE).read_text()
        rendered, lock = factory.recipe()
        self.assertEqual(rendered.replace(lock['factoryVersion'], '6.1.1-maninblack.11')
                         .replace(lock['platformRevision'], factory.HISTORICAL_PLATFORM), original)
        self.assertNotIn(factory.HISTORICAL_PLATFORM, rendered)
        self.assertNotIn('maninblack.11', rendered)
        self.assertEqual(lock['platformRevision'], '3fd1f8eb8e8d51c7e89c9f89f1646c7d4f55494f')
        self.assertEqual(lock['renderedManifestSha256'], hashlib.sha256(rendered.encode()).hexdigest())

    def test_no_ambient_layers_or_historical_image_reuse(self):
        _, lock = factory.recipe()
        self.assertEqual(len(lock['sources']), 9)
        self.assertFalse(lock['historicalImageIsBuildInput'])
        self.assertEqual(lock['qualification'], 'qualification/factory-41.conf')
        self.assertTrue(all(len(row['revision']) == 40 for row in lock['sources']))
        self.assertIn('--MACHINE=qemuarm64', lock['parameters'])

    def test_changed_template_is_rejected(self):
        original = Path.read_bytes
        def changed(path):
            return b'changed' if path.name == 'aos-vm-project.pinned.yaml' else original(path)
        with patch.object(Path, 'read_bytes', changed):
            with self.assertRaisesRegex(LabError, 'template changed'):
                factory.recipe()

    def test_changed_checkpoint_version_is_not_silently_selected(self):
        with patch.object(factory, 'read_json', return_value={'factory': {'version': '42'}}):
            with self.assertRaisesRegex(LabError, 'version changed'):
                factory.recipe()


if __name__ == '__main__':
    unittest.main()
