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
        guide = (ROOT / 'README.md').read_text().split('## Start here')[1].split('## Choose your route')[0]
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
        (self.root / 'scripts').mkdir()
        shutil.copy2(ROOT / 'scripts/aosedge-sdv-lab.sh', self.root / 'scripts/aosedge-sdv-lab.sh')
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

    def test_non_main_mutable_and_escaping_hosted_links_fail(self):
        prefix = 'https://github.com/alexmaninblack/carla-ego-runtime/blob/'
        pin = '2e3d1164d491dac25e212f59315057deca0bf3d8'
        for suffix in ('unreviewed/README.md', 'v1.0/README.md',
                       pin + '/%2e%2e/README.md', pin + '/README.md?raw=1'):
            with self.subTest(suffix=suffix):
                target = self.root / 'docs/architecture/product-map.md'
                original = target.read_text()
                self.append('[Bad](' + prefix + suffix + ')')
                self.assertNotEqual(self.check().returncode, 0)
                target.write_text(original)

    def test_current_workspace_documentation_is_allowed_without_siblings(self):
        self.append('[Current component documentation](https://github.com/alexmaninblack/carla-ego-runtime/blob/main/README.md)')
        self.assertEqual(self.check().returncode, 0)

    def test_immutable_workspace_citation_is_allowed_without_siblings(self):
        manifest = json.loads((ROOT / 'workspace/repositories.json').read_text())
        repo = next(row for row in manifest['repositories'] if row['id'] == 'vehicle-gateway')
        url = repo['repository'].removesuffix('.git') + '/blob/' + repo['acceptedRevision'] + '/docs/viss-profile.md'
        self.append('[Pinned reference](' + url + ')')
        self.assertEqual(self.check().returncode, 0)

    def test_release_identity_matches_descriptor(self):
        catalog = json.loads((ROOT / 'workspace/launcher-catalog.json').read_text())
        descriptor = json.loads((ROOT / catalog['operatorDescriptor']).read_text())
        guide = (ROOT / 'docs/getting-started/release-status.md').read_text()
        self.assertIn('launcher-catalog.json', guide)
        self.assertEqual(descriptor['sha256'], catalog['operator']['sha256'])
        self.assertEqual(descriptor['bytes'], catalog['operator']['bytes'])
        self.assertEqual(descriptor['manifestSha256'], catalog['operator']['manifestSha256'])
        self.assertFalse(descriptor['notarized'])

    def test_developer_reference_uses_current_launcher_options(self):
        guide = (ROOT / 'docs/getting-started/macos-developer-tools.md').read_text()
        blocks = re.findall(r'```sh\n(.*?)```', guide, re.S)
        self.assertEqual(len(blocks), 2)
        help_result = subprocess.run(
            ['/bin/bash', str(ROOT / 'scripts/aosedge-sdv-lab.sh'), '--help'],
            text=True, capture_output=True, timeout=10,
        )
        self.assertEqual(help_result.returncode, 0, help_result.stderr)
        for block in blocks:
            result = subprocess.run(['sh', '-n'], input=block, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('aosedge-sdv-lab.sh', block)
            self.assertIn('--route B', block)
            for option in set(re.findall(r'--[a-z][a-z-]+', block)):
                self.assertIn(option, help_result.stdout)
        build_guide = (ROOT / 'docs/getting-started/reproduce-demo.md').read_text()
        self.assertNotIn('./lab build --target all', build_guide)
        self.assertNotRegex(build_guide, r'workspace/releases/[\w.-]+\.json')

    def test_user_guide_rejects_internal_status_sections_and_narratives(self):
        target = self.root / 'docs/architecture/product-map.md'
        original = target.read_text()
        for tail in (
            '## What is still being qualified\nInternal acceptance checklist.',
            'The earlier Kit028 run is still pending.',
            'The M1 campaign passed 118 API checks.',
            'VDP-TIMEOUT-01 remains deferred.',
        ):
            with self.subTest(tail=tail):
                target.write_text(original + '\n' + tail + '\n')
                result = self.check()
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('internal qualification/history', result.stderr)

    def test_user_guide_rejects_internal_test_and_backlog_links(self):
        target = self.root / 'docs/architecture/product-map.md'
        original = target.read_text()
        for path in (
            '../qualification/current-baseline.md', '../planning/roadmap.md',
            'https://github.com/alexmaninblack/aosedge-sdv-demo/blob/'
            '84056efdf73c518d14929d66a772673212e8a2d9/docs/qualification/current-baseline.md',
        ):
            with self.subTest(path=path):
                target.write_text(original + '\n[Internal status](' + path + ')\n')
                result = self.check()
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('internal test/backlog record', result.stderr)

    def test_new_getting_started_guide_is_checked_without_an_allowlist_entry(self):
        (self.root / 'docs/getting-started/new-route.md').write_text(
            '# New route\n\n## What is still being qualified\nPending tests.\n'
        )
        self.assertIn('internal qualification/history', self.check().stderr)

    def test_user_restrictions_and_engineering_records_remain_allowed(self):
        self.append('Not notarized: follow macOS security prompts. Docker is required. '
                    'Stop the demo before host sleep; VDP updates need Safe Stop.')
        record = self.root / 'docs/qualification/current-baseline.md'
        record.write_text(record.read_text() + '\n## What is still being qualified\n'
                          'The M1 campaign passed 118 API checks; other gates remain.\n')
        result = self.check()
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
