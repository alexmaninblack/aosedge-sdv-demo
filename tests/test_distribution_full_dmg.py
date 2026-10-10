# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Complete-media boundaries with tiny non-executable payloads."""
import json
from pathlib import Path
import plistlib
import shutil
import subprocess
import sys
import unittest
from unittest.mock import patch
import test_distribution_installation as fixtures

with patch.object(sys, 'path', [str(fixtures.SCRIPTS), *sys.path]):
    import full_dmg as media


class CompleteMediaTests(unittest.TestCase):
    def setUp(self):
        self.f = fixtures.InstallationTests()
        self.f.addCleanup = self.addCleanup
        self.f.setUp()
        self.setup = self.f.root/'setup'
        self.setup.mkdir()

    def test_complete_copy_preserves_independent_pin(self):
        bundle = fixtures.Bundle(self.f.source, self.f.pin)
        copied = self.f.root/'Runtime Kit'
        result = media.copy_payload(bundle, copied)
        self.assertEqual(result['files'], len(bundle.rows))
        fixtures.Bundle(copied, self.f.pin).verify()
        self.assertFalse((self.f.root/'state').exists())

    def test_changed_payload_fails_without_success(self):
        bundle = fixtures.Bundle(self.f.source, self.f.pin)
        payload = next(self.f.source.rglob('payload.bin'))
        payload.chmod(0o644); payload.write_bytes(b'corrupt')
        with self.assertRaises(ValueError): media.copy_payload(bundle, self.f.root/'copy')

    def test_wrong_pin_and_extra_file_rejected(self):
        with self.assertRaises(ValueError): fixtures.Bundle(self.f.source, '0'*64)
        (self.f.source/'unexpected').write_text('not allowed')
        with self.assertRaises(ValueError): fixtures.Bundle(self.f.source, self.f.pin)

    def test_existing_output_not_overwritten(self):
        out = self.f.root/'demo.dmg'; out.write_bytes(b'preserve')
        with self.assertRaises(ValueError): media.validate_paths(self.f.source, self.setup, out)
        self.assertEqual(out.read_bytes(), b'preserve')

    def test_overlap_and_symlink_rejected(self):
        with self.assertRaises(ValueError): media.validate_paths(self.f.source, self.setup, self.f.source/'demo.dmg')
        link = self.f.root/'linked'; link.symlink_to(self.f.source)
        with self.assertRaises(ValueError): media.validate_paths(link, self.setup, self.f.root/'demo.dmg')

    def test_setup_pin_mismatch_before_signature_execution(self):
        embedded = self.setup/media.APP/'Contents/Resources/tooling/scripts/distribution/setup_release.json'
        embedded.parent.mkdir(parents=True)
        embedded.write_text(json.dumps(dict(manifestSha256='0'*64)))
        with patch.object(media.setup_signing, 'run') as call:
            with self.assertRaisesRegex(ValueError, 'MEDIA_SETUP_PIN_MISMATCH'): media.setup_pin(self.setup, self.f.pin)
            call.assert_not_called()

    def test_guide_discloses_first_slice(self):
        self.assertIn('separately installed', media.GUIDE)
        self.assertIn('persistent Applications launcher', media.GUIDE)
        self.assertIn('not a notarized public release', media.GUIDE)

    def test_media_success_and_error_clean_staging_without_touching_inputs(self):
        for fail in (False, True):
            output = self.f.root / ('failed.dmg' if fail else 'complete.dmg')
            stages = []
            def fake_command(command, **kwargs):
                if 'create' in command:
                    output.write_bytes(b'partial' if fail else b'complete')
                    if fail:
                        raise subprocess.CalledProcessError(1, command)
                return subprocess.CompletedProcess(command, 0)
            with patch.object(media, 'release', return_value={'manifestSha256': self.f.pin}), \
                 patch.object(media, 'setup_pin', return_value=(self.setup, {'signing': 'fixture'})), \
                 patch.object(media, 'copy_file', side_effect=shutil.copy2), \
                 patch.object(media.setup_signing, 'run'), \
                 patch.object(media.subprocess, 'run', side_effect=fake_command), \
                 patch.object(media.shutil, 'disk_usage', return_value=type('Usage', (), {'free': 100*2**30})()):
                if fail:
                    with self.assertRaises(subprocess.CalledProcessError):
                        media.build(self.f.source, self.setup, output, progress=stages.append)
                    self.assertEqual(json.loads(output.with_suffix('.failure.json').read_text())['status'], 'MEDIA_FAILED')
                else:
                    self.assertEqual(media.build(self.f.source, self.setup, output, progress=stages.append)['status'],
                                     'COMPLETE_MEDIA_BUILT_NOT_INSTALLED')
            staging = Path(next(s['path'] for s in stages if s['stage'] == 'MEDIA_STAGING'))
            self.assertFalse(staging.exists())
            self.assertTrue(output.exists())
            fixtures.Bundle(self.f.source, self.f.pin).verify()
