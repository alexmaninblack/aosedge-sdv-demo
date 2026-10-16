# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Offline dependency transport/publisher coverage; no network or builds."""
import hashlib
import sys
from pathlib import Path
import unittest
from unittest.mock import Mock, patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import public_drive as p
from test_public_drive import Response
from test_reproduction import StorageFixture
import test_dropbox_delivery as fixtures
from reproduction import dropbox_delivery as delivery, dropbox_public

URL = 'https://www.dropbox.com/scl/fi/archive_file_123/carla-macos-arm64-r1-host-support.tar.gz?rlkey=public_reader_123&dl=1'
CDN = 'https://dl.dropboxusercontent.com/cd/0/get/synthetic_object_123/file?dl=1'


class DropboxArchiveTests(unittest.TestCase):
    def client(self, rows):
        client = p.Client(); self.requests = []
        def open(req, timeout):
            self.requests.append(req)
            self.assertEqual(timeout, 30)
            self.assertNotIn('Authorization', req.headers)
            self.assertNotIn('Cookie', req.headers)
            return rows.pop(0)
        client.opener = Mock(open=open)
        return client

    def test_binding_checks_provider_and_unchanged_lock(self):
        binding = dict(schemaVersion=2, transport='dropbox-public', lockDigest='a'*64, files={'role': URL})
        self.assertEqual(p.binding(binding, 'a'*64, {'role'}), binding)
        for changed in ({**binding, 'transport':'google-drive-public'}, {**binding, 'lockDigest':'b'*64},
                        {**binding, 'files':{'role':URL.replace('dl=1','dl=0')}},
                        {**binding, 'files':{'role':'https://drive.google.com/uc?export=download&id=file_fixture_123'}}):
            with self.assertRaises(p.PublicDriveError): p.binding(changed, 'a'*64, {'role'})

    def test_range_preserved_and_probe_reads_one_byte(self):
        client = self.client([Response(b'',302,Location=CDN), Response(b'x',206,**{'Content-Type':'application/binary','Content-Range':'bytes 0-0/123'})])
        client.probe(URL, {'bytes':123})
        self.assertEqual([r.headers['Range'] for r in self.requests], ['bytes=0-0']*2)

    def test_resume_preserved_across_relative_cdn_redirect(self):
        target = '/cd/0/get2/synthetic_object_456/file?dl=1'
        client = self.client([Response(b'',302,Location=CDN),Response(b'',302,Location=target),Response(b'end',206)])
        with client.open(URL,7) as response: self.assertEqual(response.read(),b'end')
        self.assertEqual([r.headers['Range'] for r in self.requests],['bytes=7-']*3)

    def test_bad_links_rejected_without_network(self):
        for url in (URL.replace('www.dropbox.com','evil.invalid'), URL+'&token=secret',URL+'&dl=1',
                    URL.replace('https:','http:'),URL.replace('host-support','host%2Fsupport'),URL+'#fragment', CDN):
            client=self.client([])
            with self.subTest(url=url),self.assertRaises(p.PublicDriveError): client.open(url)
            self.assertFalse(self.requests)

    def test_foreign_drive_login_redirect_html_and_errors_fail_closed(self):
        for target in ('https://evil.invalid/', 'https://www.dropbox.com/login',
                       'https://drive.google.com/uc?export=download&id=file_fixture_123'):
            response=Response(b'',302,Location=target);client=self.client([response])
            with self.assertRaises(p.PublicDriveError): client.open(URL)
            self.assertTrue(response.closed)
        for response in (Response(b'<html>login</html>',**{'Content-Type':'text/html'}),Response(b'',429),
                         Response(b'',200,**{'Content-Encoding':'gzip'})):
            client=self.client([Response(b'',302,Location=CDN),response])
            with self.assertRaises(p.PublicDriveError): client.open(URL)
            self.assertTrue(response.closed)

    def test_operator_parser_stays_dmg_only(self):
        with self.assertRaises(ValueError): dropbox_public.public_link(URL)
        self.assertEqual(dropbox_public.public_link(URL,suffix='.tar.gz'),URL)

    def test_legacy_drive_cannot_redirect_to_dropbox(self):
        client=self.client([Response(b'',302,Location=URL)])
        with self.assertRaises(p.PublicDriveError):
            client.open('https://drive.google.com/uc?export=download&id=synthetic_fixture_123')
        self.assertEqual(len(self.requests),1)

    def test_ignored_range_and_oversized_probe_are_rejected(self):
        for response in (Response(b'x',200),Response(b'xx',206,**{'Content-Range':'bytes 0-0/123'}),
                         Response(b'x',206,**{'Content-Range':'bytes 0-0/999'})):
            client=self.client([Response(b'',302,Location=CDN),response])
            with self.assertRaises(p.PublicDriveError): client.probe(URL,{'bytes':123})
            self.assertTrue(response.closed)

    def test_redirect_loop_has_fixed_bound(self):
        client=self.client([Response(b'',302,Location=CDN) for _ in range(4)])
        with self.assertRaises(p.PublicDriveError): client.open(URL)
        self.assertEqual(len(self.requests),4)


class ArchiveUploadTests(unittest.TestCase):
    setUp = fixtures.DeliveryTests.setUp
    upload = fixtures.DeliveryTests.upload
    def test_archive_requires_explicit_kind_then_reuses_immutable_object(self):
        self.expected['file']='carla-macos-arm64-r1-host-support.tar.gz'
        self.selected['folderPath']='/dependencies'
        with self.assertRaises(Exception): self.upload()
        first=self.upload(suffix='.tar.gz')
        counts=(self.cloud.sessions,self.cloud.appends,self.cloud.finishes)
        self.assertEqual(self.upload(suffix='.tar.gz'),first)
        self.assertEqual(counts,(self.cloud.sessions,self.cloud.appends,self.cloud.finishes))


class DropboxArchiveCacheTests(StorageFixture, unittest.TestCase):
    def expected(self):
        return {'bytes':6,'sha256':hashlib.sha256(b'abcdef').hexdigest()}
    def test_resume_and_verified_cache_reuse_without_network(self):
        from reproduction import artifacts
        expected=self.expected();target=self.storage.path('cache/sha256/'+expected['sha256'])
        target.parent.mkdir(parents=True);target.with_suffix('.part').write_bytes(b'ab')
        client=Mock();client.open.return_value=Response(b'cdef',206,**{'Content-Range':'bytes 2-5/6'})
        with patch.object(p,'Client',return_value=client):
            result=artifacts.download_public(self.storage,URL,expected)
        self.assertEqual(result.read_bytes(),b'abcdef')
        client.open.assert_called_once_with(URL,2)
        with patch.object(p,'Client',side_effect=AssertionError('cache repeat must stay offline')):
            self.assertEqual(artifacts.download_public(self.storage,URL,expected),result)
