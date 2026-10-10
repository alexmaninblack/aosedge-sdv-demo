# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Root-only reader navigation and documented command-shape regression tests."""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECK = ROOT / 'scripts/docs-check'


class InteractivePreparationSnippetTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('zsh'), 'interactive zsh is required')
    def test_short_preparation_blocks_survive_interactive_history_expansion(self):
        guide = (ROOT / 'README.md').read_text().split('### B1.')[1].split('### B2.')[0]
        blocks = re.findall(r'```sh\n(.*?)```', guide, re.S)
        self.assertEqual(len(blocks), 2)
        # Parse, but never execute downloads, setup or the environment handoff.
        candidates = [('guide-' + str(i), 'sdv_check_storage() {\n' + block + '\n}')
                      for i, block in enumerate(blocks)]
        for label, candidate in (*candidates,
                ('known-unsafe-control', 'sdv_check_storage() {\ncase 123 in\n'
                 "  *[!0-9]*) printf invalid ;;\nesac\n}")):
            with self.subTest(label=label):
                result = subprocess.run(
                    [shutil.which('zsh'), '-d', '-f', '-i'],
                    input='setopt BANG_HIST\n' + candidate
                          + '\nwhence -w sdv_check_storage\nexit\n',
                    text=True, capture_output=True, timeout=10,
                    env={**os.environ, 'HISTFILE': '/dev/null', 'LC_ALL': 'C'},
                )
                if label == 'known-unsafe-control':
                    self.assertIn('event not found', result.stderr)
                    self.assertNotIn('sdv_check_storage: function', result.stdout)
                else:
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertNotIn('event not found', result.stderr)
                    self.assertNotIn('parse error', result.stderr)
                    self.assertIn('sdv_check_storage: function', result.stdout)


class ReaderRouteTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / 'entry'
        self.root.mkdir()
        for name in ('docs', 'contracts', 'workspace'):
            shutil.copytree(ROOT / name, self.root / name)
        for name in ('README.md', 'CONTRIBUTING.md', 'LICENSE', 'THIRD_PARTY_NOTICES.md'):
            shutil.copy2(ROOT / name, self.root / name)
        for source in (ROOT / 'apps').glob('*/README.md'):
            target = self.root / source.relative_to(ROOT)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)

    def check(self):
        return subprocess.run([sys.executable, '-B', str(CHECK), '--reader-routes',
                               '--root', str(self.root)], capture_output=True, text=True)

    def append(self, text):
        target = self.root / 'docs/architecture/product-map.md'
        target.write_text(target.read_text() + '\n' + text + '\n')

    def test_routes_work_without_siblings(self):
        result = self.check()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('no sibling checkout required', result.stdout)

    def test_missing_guide_fails(self):
        (self.root / 'docs/getting-started/full-source-build.md').unlink()
        self.assertNotEqual(self.check().returncode, 0)

    def test_broken_local_anchor_fails(self):
        self.append('[Broken](../getting-started/reproduce-demo.md#missing)')
        self.assertIn('missing anchor', self.check().stderr)

    def test_sibling_dependency_fails_even_when_present(self):
        sibling = self.root.parent / 'carla-ego-runtime'
        sibling.mkdir()
        (sibling / 'README.md').write_text('# Existing sibling\n')
        self.append('[Sibling](../../../carla-ego-runtime/README.md)')
        self.assertIn('requires a sibling', self.check().stderr)

    def test_unpinned_wrong_pin_and_escaping_hosted_links_fail(self):
        prefix = 'https://github.com/alexmaninblack/carla-ego-runtime/blob/'
        pin = '2e3d1164d491dac25e212f59315057deca0bf3d8'
        for suffix in ('main/README.md', '0' * 40 + '/README.md',
                       pin + '/%2e%2e/README.md', pin + '/README.md?raw=1'):
            with self.subTest(suffix=suffix):
                target = self.root / 'docs/architecture/product-map.md'
                original = target.read_text()
                self.append('[Bad](' + prefix + suffix + ')')
                self.assertNotEqual(self.check().returncode, 0)
                target.write_text(original)

    def test_exact_workspace_pin_is_allowed(self):
        manifest = json.loads((ROOT / 'workspace/repositories.json').read_text())
        repo = next(row for row in manifest['repositories'] if row['id'] == 'vehicle-gateway')
        url = repo['repository'].removesuffix('.git') + '/blob/' + repo['acceptedRevision'] + '/README.md'
        self.append('[Pinned reference](' + url + ')')
        self.assertEqual(self.check().returncode, 0)

    def test_release_identity_matches_descriptor(self):
        descriptor = json.loads((ROOT / 'workspace/releases/1.2.0-rc.1-source-factory-delivery.json').read_text())
        guide = (ROOT / 'docs/getting-started/release-status.md').read_text()
        self.assertIn(descriptor['sha256'], guide)
        self.assertIn(f"{descriptor['bytes']:,}", guide)
        self.assertFalse(descriptor['notarized'])

    def test_build_guide_shell_syntax_and_flags(self):
        guide = (ROOT / 'docs/getting-started/reproduce-demo.md').read_text()
        blocks = re.findall(r'```sh\n(.*?)```', guide, re.S)
        self.assertGreater(len(blocks), 3)
        for block in blocks:
            result = subprocess.run(['sh', '-n'], input=block, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
        for prefix in ([], ['inputs']):
            help_result = subprocess.run([sys.executable, '-B', str(ROOT / 'lab'), *prefix, '--help'],
                                         text=True, capture_output=True)
            self.assertEqual(help_result.returncode, 0, help_result.stderr)
        help_text = subprocess.check_output([sys.executable, '-B', str(ROOT / 'lab'), '--help'], text=True)
        build = next(block for block in blocks if './lab build --target all' in block)
        for option in set(re.findall(r'--[a-z][a-z-]+', build)):
            self.assertIn(option, help_text)
        for path in re.findall(r'workspace/[\w./-]+\.json', guide):
            self.assertTrue((ROOT / path).is_file(), path)


if __name__ == '__main__':
    unittest.main()
