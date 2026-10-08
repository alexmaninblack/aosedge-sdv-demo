# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Offline transport tests; no account, credentials, upload or runtime."""
import copy
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from reproduction import delivery as d
from reproduction.core import LabError, atomic_json, digest


class Response(io.BytesIO):
    def __init__(self, status, headers=None):
        super().__init__()
        self.status, self.headers = status, headers or {}


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='drive-test-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.source = self.root / 'candidate.dmg'
        self.source.write_bytes(b'abcdefgh')
        self.expected = {'file': 'candidate.dmg', 'bytes': 8, 'sha256': hashlib.sha256(b'abcdefgh').hexdigest()}
        self.folder, self.file_id = 'folder_0123456789', 'file_0123456789'
        self.meta = {'id': self.file_id, 'name': 'candidate.dmg', 'size': '8',
                     'sha256Checksum': self.expected['sha256'], 'version': '1', 'parents': [self.folder],
                     'trashed': False, 'shared': False, 'capabilities': {'canDownload': True}}
        self.client = Mock()
        self.client.json.return_value = {'ids': [self.file_id]}
        self.client.named_files.return_value = []
        self.client.metadata.return_value = self.meta
        self.intent = self.root / 'intent.json'

    def upload(self):
        return d.upload(self.client, self.source, self.expected, self.folder, self.intent)

    def test_first_and_repeat_do_not_duplicate(self):
        self.client.request.side_effect = [Response(200, {'Location': d.ORIGIN + '/upload/drive/v3/files?upload_id=secret'}), Response(200)]
        self.assertEqual(self.upload(), self.meta)
        self.assertNotIn('secret', self.intent.read_text())
        self.client.reset_mock()
        self.assertEqual(self.upload(), self.meta)
        self.client.request.assert_not_called()
        self.client.json.assert_not_called()

    def test_response_loss_reconciles_offset_before_resend(self):
        with patch.object(d, 'UPLOAD_CHUNK', 4), patch.object(d.time, 'sleep'):
            self.client.request.side_effect = [Response(200, {'Location': d.ORIGIN + '/upload/drive/v3/files'}),
                LabError('connection lost'), Response(308, {'Range': 'bytes=0-3'}), Response(200)]
            self.upload()
        calls = self.client.request.call_args_list
        self.assertEqual(calls[2].args[2], b'')
        self.assertEqual(calls[2].args[3]['Content-Range'], 'bytes */8')
        self.assertEqual(calls[3].args[2], b'efgh')

    def test_bound_intent_is_retained_after_initiation_loss(self):
        self.client.request.side_effect = LabError('interrupted')
        with self.assertRaises(LabError):
            self.upload()
        self.assertEqual(json.loads(self.intent.read_text())['fileId'], self.file_id)

    def test_reuse_missing_file_uses_same_id(self):
        atomic_json(self.intent, {'descriptorDigest': digest(self.expected), 'folderId': self.folder, 'fileId': self.file_id})
        self.client.metadata.side_effect = [None, self.meta]
        self.client.request.side_effect = [Response(200, {'Location': d.ORIGIN + '/upload/drive/v3/files'}), Response(200)]
        self.upload()
        self.client.json.assert_not_called()
        self.assertEqual(json.loads(self.client.request.call_args_list[0].args[2])['id'], self.file_id)

    def test_wrong_remote_file_never_overwritten(self):
        atomic_json(self.intent, {'descriptorDigest': digest(self.expected), 'folderId': self.folder, 'fileId': self.file_id})
        self.client.metadata.return_value = {**self.meta, 'sha256Checksum': '0'*64}
        with self.assertRaises(LabError):
            self.upload()
        self.client.request.assert_not_called()

    def test_new_workspace_reuses_existing_exact_file(self):
        self.client.named_files.return_value = [self.meta]
        self.assertEqual(self.upload(), self.meta)
        self.client.request.assert_not_called()
        self.client.json.assert_not_called()
        self.assertEqual(json.loads(self.intent.read_text())['fileId'], self.file_id)

    def test_same_name_conflict_is_not_a_new_upload(self):
        self.client.named_files.return_value = [{**self.meta, 'size': '9'}]
        with self.assertRaises(LabError):
            self.upload()
        self.client.request.assert_not_called()
        self.assertFalse(self.intent.exists())

    def test_wrong_intent_and_corrupt_source_rejected(self):
        atomic_json(self.intent, {'descriptorDigest': 'wrong', 'folderId': self.folder, 'fileId': self.file_id})
        with self.assertRaises(LabError):
            self.upload()
        self.intent.unlink()
        self.source.write_bytes(b'corrupt!')
        with self.assertRaises(LabError):
            self.upload()
        self.client.request.assert_not_called()

    def test_bad_range_and_no_progress_rejected(self):
        for value in ('bytes=1-3', 'bytes=0-8', 'garbage'):
            with self.assertRaises(LabError):
                d.acknowledged(Response(308, {'Range': value}), 8)
        self.client.request.side_effect = [Response(200, {'Location': d.ORIGIN + '/upload/drive/v3/files'})] + [Response(308) for _ in range(4)]
        with self.assertRaisesRegex(LabError, 'no progress'):
            self.upload()

    def test_credentials_not_sent_to_foreign_host_or_redirect(self):
        client = d.Client('unused', 'unused')
        client.access_token = Mock(side_effect=AssertionError('must not request credentials'))
        for url in ('http://www.googleapis.com/drive/v3/files', 'https://www.googleapis.com.evil/drive/v3/files',
                    'https://evil/drive/v3/files', 'https://www.googleapis.com/wrong'):
            with self.assertRaises(LabError):
                client.request('PUT', url, b'')
        with self.assertRaises(LabError):
            d.artifacts.NoRedirect().redirect_request(None, None, None, None, None, None)

    def test_private_remote_and_correct_parent_required(self):
        for change in ({'shared': True}, {'parents': ['other']}, {'trashed': True}, {'size': '9'},
                       {'name': 'other'}, {'version': None}, {'capabilities': {'canDownload': False}}):
            with self.assertRaises(LabError):
                d.check_remote({**self.meta, **change}, self.file_id, self.folder, self.expected)

    def test_descriptor_is_engineering_only(self):
        path = d.ROOT / 'workspace/releases/1.2.0-rc.1-delivery.json'
        value = d.descriptor(path)
        self.assertEqual(value['bytes'], 14162125968)
        altered = self.root / 'descriptor.json'
        for field, replacement in [('notarized', True), ('status', 'QUALIFIED'), ('file', '../other.dmg'), ('extra', 'x')]:
            row = copy.deepcopy(value)
            row[field] = replacement
            atomic_json(altered, row)
            with self.assertRaises(LabError):
                d.descriptor(altered)


if __name__ == '__main__':
    unittest.main()
