# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Public Docker inputs remain readable under the private launcher umask."""
import io
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from reproduction import containers, core


class BackendContextTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.source = self.root/'source'
        self.source.mkdir(mode=0o700)
        self.env = dict(os.environ, GIT_CONFIG_NOSYSTEM='1')
        self.git('init', '-q')
        (self.source/'Dockerfile').write_text('FROM scratch\nCOPY src /app/src\n')
        (self.source/'src').mkdir(mode=0o700)
        (self.source/'src/main.mjs').write_text('export const publicCode = true;\n')
        (self.source/'script').write_text('#!/bin/sh\nexit 0\n')
        (self.source/'script').chmod(0o700)
        (self.source/'Dockerfile').chmod(0o600)
        (self.source/'src/main.mjs').chmod(0o600)
        self.git('add', 'Dockerfile', 'src', 'script')
        self.git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                 'commit', '-qm', 'fixture')
        self.revision = self.git('rev-parse', 'HEAD').strip()
        self.output = self.root/'context'

    def git(self, *args):
        return subprocess.run(['git', '-C', str(self.source), *args], env=self.env,
                              check=True, capture_output=True, text=True).stdout

    def test_private_checkout_exports_readable_files_without_changing_inputs(self):
        secret = self.source/'untracked-private-input'
        secret.write_text('fixture-not-exported')
        secret.chmod(0o600)
        before = {str(p.relative_to(self.source)): (p.stat().st_mode, p.read_bytes())
                  for p in (secret, self.source/'Dockerfile', self.source/'src/main.mjs', self.source/'script')}
        old = os.umask(0o077)
        try:
            containers.build_context(self.source, self.revision, self.output, self.env)
            self.assertEqual(os.umask(0o077), 0o077)
        finally:
            os.umask(old)
        self.assertEqual(self.output.stat().st_mode & 0o777, 0o700)
        self.assertEqual((self.output/'src').stat().st_mode & 0o777, 0o755)
        for path in ('Dockerfile', 'src/main.mjs'):
            self.assertEqual((self.output/path).stat().st_mode & 0o777, 0o644)
            self.assertEqual((self.output/path).read_bytes(), (self.source/path).read_bytes())
        self.assertEqual((self.output/'script').stat().st_mode & 0o777, 0o755)
        self.assertFalse((self.output/'.git').exists())
        self.assertFalse((self.output/secret.name).exists())
        for path, value in before.items():
            self.assertEqual(((self.source/path).stat().st_mode, (self.source/path).read_bytes()), value)

    def test_existing_context_is_never_overwritten(self):
        self.output.mkdir()
        with self.assertRaisesRegex(core.LabError, 'must be new'):
            containers.build_context(self.source, self.revision, self.output, self.env)

    def test_links_traversal_git_and_duplicate_members_fail_closed(self):
        for kind in ('symlink', 'hardlink', 'traversal', 'absolute', 'git', 'duplicate'):
            with self.subTest(kind=kind):
                stream = io.BytesIO()
                with tarfile.open(fileobj=stream, mode='w') as archive:
                    row = tarfile.TarInfo({'traversal':'../escape', 'absolute':'/escape',
                                         'git':'.git/config'}.get(kind, 'file'))
                    if kind in ('symlink', 'hardlink'):
                        row.type = tarfile.SYMTYPE if kind == 'symlink' else tarfile.LNKTYPE
                        row.linkname = '../escape'
                    archive.addfile(row)
                    if kind == 'duplicate':
                        archive.addfile(row)
                result = subprocess.CompletedProcess([], 0, stream.getvalue(), b'')
                with patch('reproduction.containers.run_command', return_value=result):
                    with self.assertRaisesRegex(core.LabError, 'Unsafe'):
                        containers.build_context(self.source, self.revision, self.output, self.env)
                self.assertFalse(self.output.exists())

    def test_changed_exported_recipe_is_rejected(self):
        (self.source/'Dockerfile').write_text('changed checkout recipe')
        with self.assertRaisesRegex(core.LabError, 'recipe differs'):
            containers.build_context(self.source, self.revision, self.output, self.env)


if __name__ == '__main__':
    unittest.main()
