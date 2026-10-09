# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
import unittest
from unittest.mock import patch
from test_reproduction import StorageFixture
from reproduction import core, host, packaging, revalidate
from reproduction.artifacts import sha256


class RevalidationTests(StorageFixture, unittest.TestCase):
    def fixture(self):
        self.patch('reproduction.revalidate.external_volume', return_value=self.volume)
        inputs = {'fixture':True}
        key = core.digest(inputs)
        output = self.storage.path('builds/host-runtime/'+key)
        output.mkdir(parents=True)
        payload = output/'payload'
        payload.write_bytes(b'fixture')
        payload.chmod(0o444)
        core.atomic_json(output/host.MANIFEST, {'schemaVersion':1,
            'status':'ASSEMBLED_HOST_LAUNCH_NOT_DISTRIBUTION_QUALIFIED', 'credentialsIncluded':False,
            'files':[{'path':'payload', 'bytes':7, 'mode':0o444, 'sha256':sha256(payload)}]})
        old = packaging.stamp(payload)
        old[0] -= 1
        receipt = {'inputs':inputs, 'status':'ASSEMBLED_NOT_RUNTIME_QUALIFIED',
                   'externalDistributionApproved':False, 'manifest':{'path':host.MANIFEST,
                   'bytes':(output/host.MANIFEST).stat().st_size, 'sha256':sha256(output/host.MANIFEST)},
                   'stamps':{'payload':old}}
        core.atomic_json(host.receipt_path(output), receipt)
        self.state['builds'][key] = {'target':'host-runtime', 'inputs':inputs}
        return output, payload, receipt

    def refresh(self):
        return revalidate.refresh(self.storage, self.state, 'host-runtime', lambda *args: None)

    def test_device_only_change_hashes_preserves_original_and_repeats(self):
        output, payload, original = self.fixture()
        before = packaging.stamp(payload)
        result = self.refresh()
        self.assertEqual((result['refreshedReceipts'],result['hashedFiles']), (1,1))
        self.assertEqual(packaging.stamp(payload), before)
        host.verify(output, original['inputs'])
        saved = self.storage.path('builds/storage-revalidation/'+core.digest(original)+'/original.json')
        self.assertEqual(core.read_json(saved), original)
        self.assertEqual(self.refresh()['refreshedReceipts'], 0)

    def test_changed_payload_never_resealed(self):
        output, payload, original = self.fixture()
        payload.chmod(0o644)
        payload.write_bytes(b'changed')
        payload.chmod(0o444)
        with self.assertRaisesRegex(core.LabError, 'beyond the remount'):
            self.refresh()
        self.assertEqual(core.read_json(host.receipt_path(output)), original)

    def test_digest_mismatch_never_resealed(self):
        output, _, original = self.fixture()
        with patch('reproduction.revalidate.sha256', return_value='0'*64):
            with self.assertRaisesRegex(core.LabError, 'digest differs'):
                self.refresh()
        self.assertEqual(core.read_json(host.receipt_path(output)), original)

    def test_wrong_volume_or_extra_file_fails_before_mutation(self):
        output, _, original = self.fixture()
        with patch('reproduction.revalidate.external_volume', return_value={'uuid':'OTHER'}):
            with self.assertRaisesRegex(core.LabError, 'volume changed'):
                self.refresh()
        (output/'extra').write_text('unowned')
        with self.assertRaisesRegex(core.LabError, 'inventory differs'):
            self.refresh()
        self.assertEqual(core.read_json(host.receipt_path(output)), original)

    def test_missing_receipt_is_not_adopted(self):
        output, _, _ = self.fixture()
        host.receipt_path(output).unlink()
        with self.assertRaises(FileNotFoundError):
            self.refresh()
