# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
import sys
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from test_reproduction import StorageFixture
from reproduction import core, media, host
from reproduction.artifacts import sha256


class MediaTests(StorageFixture, unittest.TestCase):
    def fixture(self):
        self.storage.environment()
        self.kit = self.base/'kit'
        self.kit.mkdir()
        (self.kit/'application-manifest.json').write_text('{}')
        self.patch('reproduction.media.verify_sources')
        self.patch('reproduction.packaging.producer', return_value=({'recipe':'a'*40}, 'b'*40))
        self.patch('reproduction.package_chain.upstream', return_value=('a'*64, self.kit))
        original = media.read_json
        self.patch('reproduction.media.read_json', side_effect=lambda path:
            {'schemaVersion':1, 'label':'fixture', 'manifestSha256':sha256(self.kit/'application-manifest.json')}
            if str(path).endswith(media.RELEASE) else original(path))
        self.command = self.patch('reproduction.media.run_command', side_effect=self.owner)

    def owner(self, args, **kwargs):
        output = Path(args[-4])
        output.mkdir()
        (output/'fixture').write_bytes(b'fixture')
        return SimpleNamespace(returncode=0, stdout=b'{}', stderr=b'')

    def build(self, target='setup', signer='A'*40):
        return media.assemble(self.storage, self.state, target, sys.executable, signer, lambda *args: None)

    def test_first_repeat_and_dmg_reuses_exact_signed_setup(self):
        self.fixture()
        key = self.build()
        self.assertEqual(self.build(), key)
        self.assertEqual(self.command.call_count, 1)
        dmg = self.build('dmg', None)
        self.assertEqual(self.state['builds'][dmg]['inputs']['setup'], key)
        self.assertEqual(self.build('dmg', None), dmg)
        self.assertEqual(self.command.call_count, 2)

    def test_unsigned_setup_and_dmg_without_setup_block(self):
        self.fixture()
        with self.assertRaisesRegex(core.LabError, 'Explicit authorized'):
            self.build(signer=None)
        with self.assertRaisesRegex(core.LabError, 'Matching signed Setup'):
            self.build('dmg', None)
        self.command.assert_not_called()

    def test_corruption_rejected_no_rebuild(self):
        self.fixture()
        key = self.build()
        self.storage.path('builds/setup/'+key+'/fixture').write_bytes(b'changed')
        with self.assertRaisesRegex(core.LabError, 'output changed'):
            self.build()
        self.assertEqual(self.command.call_count, 1)

    def test_interrupted_outer_state_is_recovered(self):
        self.fixture()
        key = self.build()
        del self.state['builds'][key]
        self.assertEqual(self.build(), key)
        self.assertEqual(self.command.call_count, 1)


if __name__ == '__main__':
    unittest.main()
