# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""First-use path isolation fixtures: no SSH, Cloud, installation or signing."""
import json
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts/qualification'))
import setup_first_use_campaign as first


class FirstUsePathTests(unittest.TestCase):
    def media_fixture(self, root, name='AosEdge-SDV-Lab-1.2.0-rc.99.dmg'):
        media = root / 'media'
        (media / 'Setup').mkdir(parents=True)
        (media / 'Setup/build-receipt.json').write_text(json.dumps(
            dict(manifestSha256='a' * 64, binarySha256='b' * 64)))
        path = media / name
        path.write_bytes(b'media fixture')
        path.with_suffix('.receipt.json').write_text(json.dumps(dict(
            manifestSha256='a' * 64, dmgSha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            dmgBytes=path.stat().st_size)))
        return media, path

    def test_remote_paths_use_the_validated_target_not_local_home(self):
        with patch.object(Path, 'home', return_value=Path('/Users/developer')):
            remote, dmg = first.remote_paths('test_operator')
        self.assertEqual(remote, '/Users/test_operator/' + first.REMOTE)
        self.assertEqual(dmg, '/Users/test_operator/' + first.DMG)

    def test_invalid_target_users_are_rejected_before_paths_are_used(self):
        for user in ('', '../operator', '/Users/operator', 'operator/name',
                     'operator;command', 'operator\n', 'a' * 33, None):
            with self.subTest(user=user), self.assertRaisesRegex(first.h.Error, 'USER_INVALID'):
                first.remote_paths(user)

    def test_producer_certificate_paths_are_local_and_role_bounded(self):
        with patch.object(Path, 'home', return_value=Path('/Users/developer')):
            for role in ('oem', 'sp'):
                self.assertEqual(first.local_certificate(role),
                    '/Users/developer/.aos/security prod/aos-user-' + role + '.p12')
            with self.assertRaisesRegex(first.h.Error, 'CERTIFICATE_ROLE_INVALID'):
                first.local_certificate('../other')

    def test_initialization_binds_both_existing_and_supplied_media_to_target(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            media, path = self.media_fixture(root)
            for supplied in (None, media):
                with self.subTest(supplied=supplied is not None), \
                     patch.object(first.h, 'configuration', return_value=({'user': 'tester'}, None)), \
                     patch.object(first.j, 'configuration', return_value={'manifestSha256': 'a' * 64}), \
                     patch.object(first.os, 'umask'):
                    campaign = first.Campaign(root / 'runner', root / ('records-media' if supplied else 'records'),
                                              media=supplied)
                remote, existing = first.remote_paths('tester')
                self.assertEqual(campaign.remote_root, remote)
                self.assertEqual(campaign.remote_dmg,
                    remote + '/' + path.name if supplied else existing)
                if supplied:
                    self.assertEqual(campaign.media_dmg, path)
                    self.assertEqual(campaign.selected_media['sha256'], hashlib.sha256(path.read_bytes()).hexdigest())

    def test_media_selection_rejects_missing_ambiguous_linked_or_wrong_receipts(self):
        for condition in ('absent', 'ambiguous', 'linked', 'manifest', 'size', 'digest', 'receipt-link'):
            with self.subTest(condition=condition), tempfile.TemporaryDirectory() as temporary:
                media, path = self.media_fixture(Path(temporary).resolve())
                receipt = path.with_suffix('.receipt.json')
                if condition == 'absent': path.unlink()
                elif condition == 'ambiguous': (media/'other.dmg').write_bytes(b'other')
                elif condition == 'linked':
                    source=path.with_suffix('.original'); path.rename(source); path.symlink_to(source)
                elif condition == 'receipt-link':
                    source=receipt.with_suffix('.original'); receipt.rename(source); receipt.symlink_to(source)
                else:
                    row=json.loads(receipt.read_bytes())
                    row[{'manifest':'manifestSha256', 'size':'dmgBytes', 'digest':'dmgSha256'}[condition]] = {
                        'manifest':'c'*64, 'size':123, 'digest':'invalid'}[condition]
                    receipt.write_text(json.dumps(row))
                with self.assertRaises((first.h.Error, first.h.InstallError)):
                    first.supplied_media(media, {'manifestSha256':'a'*64},
                        first.remote_paths('tester')[0], 'tester')

    def test_invalid_selection_has_no_campaign_journal_or_remote_effect(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary).resolve();media,path=self.media_fixture(root)
            (media/'other.dmg').write_bytes(b'other')
            with patch.object(first.h, 'configuration', return_value=({'user':'tester'}, None)), \
                    patch.object(first.j, 'configuration', return_value={'manifestSha256':'a'*64}), \
                    patch.object(first.h, 'remote', side_effect=AssertionError('No remote effects')), \
                    patch.object(first.os, 'umask'), self.assertRaises(first.h.Error):
                first.Campaign(root/'runner', root/'records', media=media)
            self.assertFalse((root/'records').exists())

    def test_changed_media_receipt_cannot_reselect_at_launch(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary).resolve();media,path=self.media_fixture(root)
            campaign=object.__new__(first.Campaign)
            campaign.media=media;campaign.c={'manifestSha256':'a'*64};campaign.t={'user':'tester'}
            remote=first.remote_paths('tester')[0]
            campaign.media_dmg,campaign.selected_media=first.supplied_media(media,campaign.c,remote,'tester')
            campaign.remote_dmg=campaign.selected_media['remotePath']
            receipt=path.with_suffix('.receipt.json');row=json.loads(receipt.read_bytes())
            row['dmgSha256']='c'*64;receipt.write_text(json.dumps(row))
            with patch.object(first.h, 'remote', side_effect=AssertionError('No remote effects')), \
                    self.assertRaisesRegex(first.h.Error, 'FIRST_USE_MEDIA_SELECTION_CHANGED'):
                campaign.launch()

    def campaign(self):
        campaign = object.__new__(first.Campaign)
        campaign.t = {'user': 'tester'}
        campaign.c = dict(instanceRoot='/Users/tester/Selected data',
                          storeRoot='/Users/tester/Selected packages')
        campaign.remote_root, campaign.remote_dmg = first.remote_paths('tester')
        campaign.installed = campaign.reconcile = campaign.parked = False
        campaign.worker = Mock(return_value={'retiredTest': first.TEST})
        campaign.remote = Mock(return_value='{}')
        return campaign

    def test_parking_uses_configured_target_paths_and_preserves_guards(self):
        campaign = self.campaign()
        with patch.object(first.h, 'probe', return_value={'demoProcesses': 0, 'busyPorts': 0}):
            result = campaign.prepare()
        source = campaign.remote.call_args.args[0]
        compile(source, '<remote-parking-fixture>', 'exec')
        for key in ('instanceRoot', 'storeRoot'):
            self.assertIn(repr(campaign.c[key]), source)
        self.assertIn(repr(campaign.remote_root), source)
        self.assertIn('pathlib.Path.home()', source)
        self.assertIn('PARKING_VOLUME_CHANGED', source)
        self.assertIn('PARKING_OPEN_HANDLES', source)
        self.assertTrue(campaign.parked)
        self.assertEqual(result['sharedDocker'], 'PRESERVED')

    def test_progress_reads_only_the_same_target_campaign_root(self):
        campaign = self.campaign()
        self.assertEqual(campaign.progress(), {})
        source = campaign.remote.call_args.args[0]
        self.assertIn(repr(campaign.remote_root + '/progress.json'), source)
        compile(source, '<remote-progress-fixture>', 'exec')


if __name__ == '__main__':
    unittest.main()
