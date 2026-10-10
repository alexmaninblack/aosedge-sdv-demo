# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Offline anonymous transport proofs. No Google requests or credentials."""
import hashlib
import http.client
import io
from pathlib import Path
import sys
import unittest
from unittest import mock
import urllib.error

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import public_drive as p
from test_reproduction import StorageFixture
from reproduction import artifacts, core

URL = 'https://drive.google.com/uc?export=download&id=synthetic_fixture_123'
DIRECT = 'https://drive.usercontent.google.com/download?export=download&id=synthetic_fixture_123'


class Response(io.BytesIO):
    def __init__(self, raw=b'data', status=200, **headers):
        super().__init__(raw)
        self.status = status
        self.headers = {'Content-Type': 'application/octet-stream', 'Content-Length': str(len(raw)), **headers}


def form(**overrides):
    fields = {'id': 'synthetic_fixture_123', 'export': 'download', 'confirm': 't', 'uuid': 'fixture-confirmation'}
    fields.update(overrides)
    return ("<html>Google Drive can't scan this file for viruses."
            '<form id="download-form" action="https://drive.usercontent.google.com/download" method="get">' +
            ''.join(f'<input type="hidden" name="{k}" value="{v}">' for k, v in fields.items()) + '</form></html>').encode()


class PublicTransportTests(unittest.TestCase):
    def client(self, responses):
        client = p.Client()
        self.requests = []
        def open(req, timeout):
            self.requests.append(req)
            self.assertEqual(req.get_method(), 'GET')
            self.assertNotIn('Authorization', req.headers)
            self.assertNotIn('Cookie', req.headers)
            self.assertEqual(timeout, 30)
            item = responses.pop(0)
            if isinstance(item, Exception): raise item
            return item
        client.opener = mock.Mock(open=open)
        return client

    def test_direct_bytes_no_credentials_cookies_or_api_key(self):
        client = self.client([Response(b'{}', **{'Content-Type':'application/json'})])
        self.assertEqual(client.catalog(URL), b'{}')
        self.assertEqual(len(self.requests), 1)

    def test_no_ambient_proxy_cookie_or_auth_handlers(self):
        with mock.patch.object(p.urllib.request, 'build_opener') as build:
            p.Client()
        self.assertEqual(build.call_args.args[0].proxies, {})
        self.assertEqual(len(build.call_args.args), 2)

    def test_redirect_same_identity_then_bounded_probe(self):
        client = self.client([Response(b'', 302, Location=DIRECT),
            Response(b'x', 206, **{'Content-Range':'bytes 0-0/123'})])
        client.probe(URL, {'bytes':123})
        self.assertEqual([r.headers['Range'] for r in self.requests], ['bytes=0-0']*2)

    def test_large_file_confirmation_and_range_no_cookies(self):
        client = self.client([Response(form(), **{'Content-Type':'text/html'}),
                             Response(b'abc',206,**{'Content-Range':'bytes 7-9/10'})])
        with client.open(URL,7) as response: self.assertEqual(response.read(), b'abc')
        self.assertEqual(self.requests[-1].headers['Range'],'bytes=7-')
        self.assertIn('confirm=t',self.requests[-1].full_url)

    def test_confirmation_preserves_resource_key_without_logging_it(self):
        client = self.client([Response(form(), **{'Content-Type':'text/html'}), Response()])
        with client.open(URL+'&resourcekey=fixture_key') as response: response.read()
        self.assertIn('resourcekey=fixture_key',self.requests[-1].full_url)

    def test_rejects_untrusted_links_and_embedded_credentials_before_request(self):
        bad = ['http://drive.google.com/uc?export=download&id=synthetic_fixture_123',
               URL+'&key=API_KEY',URL+'&id=second_file_123',URL+'#fragment',
               URL.replace('drive.google.com','drive.google.com.evil.invalid'),
               URL.replace('drive.google.com','user:pass@drive.google.com'),
               URL.replace('/uc','/file/d/id/view')]
        for url in bad:
            client = self.client([])
            with self.subTest(url=url), self.assertRaises(p.PublicDriveError): client.open(url)
            self.assertFalse(self.requests)

    def test_rejects_redirect_to_login_foreign_host_or_other_object(self):
        for target in ('https://accounts.google.com/login', 'https://evil.invalid/',
                       DIRECT.replace('synthetic_fixture_123','different_fixture_123')):
            client = self.client([Response(b'',302,Location=target)])
            with self.assertRaises(p.PublicDriveError): client.open(URL)
            self.assertEqual(len(self.requests),1)

    def test_quota_auth_malware_unknown_and_oversized_html_fail_closed(self):
        for raw in (b'<html>Too many users have downloaded this file</html>',
                    b'<html>Sign in</html>',form().replace(b"can't scan",b"infected; can't scan"),
                    form(id='different_fixture_123'),b'x'*(p.HTML_LIMIT+1)):
            client = self.client([Response(raw,**{'Content-Type':'text/html'})])
            with self.assertRaises(p.PublicDriveError): client.open(URL)
            self.assertEqual(len(self.requests),1)

    def test_duplicate_or_unexpected_confirmation_fields_rejected(self):
        for raw in (form(extra='unexpected'), form().replace(b'</form>',b'<input type="hidden" name="id" value="duplicate"></form>'),
                    form().replace(b'method="get"',b'method="post"')):
            client = self.client([Response(raw,**{'Content-Type':'text/html'})])
            with self.assertRaises(p.PublicDriveError): client.open(URL)
            self.assertEqual(len(self.requests),1)

    def test_repeated_confirmation_has_no_loop(self):
        client = self.client([Response(form(),**{'Content-Type':'text/html'}) for _ in range(2)])
        with self.assertRaises(p.PublicDriveError): client.open(URL)
        self.assertEqual(len(self.requests),2)

    def test_http_failures_are_sanitized_and_never_retry_login(self):
        for code in (403,404,429,503):
            client = self.client([urllib.error.HTTPError(URL,code,'SECRET',{},io.BytesIO(b'SECRET'))])
            with self.assertRaises(p.PublicDriveError) as caught: client.open(URL)
            self.assertNotIn('SECRET',str(caught.exception))
            self.assertEqual(len(self.requests),1)

    def test_catalog_limit_and_probe_length_or_ignored_range(self):
        client=self.client([Response(b'x'*11)])
        with self.assertRaises(p.PublicDriveError): client.catalog(URL,10)
        for response in (Response(b'x',200),Response(b'x',206,**{'Content-Range':'bytes 0-0/99'})):
            client=self.client([response])
            with self.assertRaises(p.PublicDriveError): client.probe(URL,{'bytes':100})

    def test_interrupted_catalog_is_sanitized(self):
        response=Response()
        response.read=mock.Mock(side_effect=http.client.IncompleteRead(b'SECRET'))
        client=self.client([response])
        with self.assertRaises(p.PublicDriveError) as error: client.catalog(URL)
        self.assertNotIn('SECRET',str(error.exception))
        self.assertTrue(response.closed)

    def test_unexpected_encoding_type_or_redirect_loop_closes_responses(self):
        for headers in ({'Content-Encoding':'gzip'}, {'Content-Type':'text/plain'}):
            response=Response(**headers);client=self.client([response])
            with self.assertRaises(p.PublicDriveError): client.open(URL)
            self.assertTrue(response.closed)
        client=self.client([Response(b'',302,Location=DIRECT) for _ in range(5)])
        with self.assertRaises(p.PublicDriveError): client.open(URL)
        self.assertEqual(len(self.requests),5)

    def test_public_binding_rejects_hash_overrides_private_ids_and_boolean_schema(self):
        value={'schemaVersion':2,'transport':'google-drive-public','lockDigest':'a'*64,'files':{'role':URL}}
        self.assertEqual(p.binding(value,'a'*64,{'role'}),value)
        for bad in ({**value,'schemaVersion':True},{**value,'lockDigest':'b'*64},
                    {**value,'folderId':'private_fixture'},{**value,'sha256':'b'*64},
                    {**value,'files':{'role':'private_file_123'}}):
            with self.assertRaises(p.PublicDriveError): p.binding(bad,'a'*64,{'role'})


class PublicCacheTests(StorageFixture, unittest.TestCase):
    def expected(self, raw=b'abcdef'):
        return {'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}

    def test_partial_resume_then_cache_reuse_without_network(self):
        expected=self.expected()
        target=self.storage.path('cache/sha256/'+expected['sha256'])
        target.parent.mkdir(parents=True)
        target.with_suffix('.part').write_bytes(b'ab')
        client=mock.Mock()
        client.open.return_value=Response(b'cdef',206,**{'Content-Range':'bytes 2-5/6'})
        with mock.patch.object(p,'Client',return_value=client):
            result=artifacts.download_public(self.storage,URL,expected)
        self.assertEqual(result.read_bytes(),b'abcdef')
        client.open.assert_called_once_with(URL,2)
        with mock.patch.object(p,'Client',side_effect=AssertionError('must not construct a network client')):
            self.assertEqual(artifacts.download_public(self.storage,URL,expected),result)

    def test_bad_hash_or_ignored_resume_never_promoted(self):
        expected=self.expected()
        client=mock.Mock()
        client.open.return_value=Response(b'xxxxxx')
        with mock.patch.object(p,'Client',return_value=client),self.assertRaises(core.LabError):
            artifacts.download_public(self.storage,URL,expected)
        target=self.storage.path('cache/sha256/'+expected['sha256'])
        self.assertFalse(target.exists())
        target.with_suffix('.part').write_bytes(b'ab')
        client.open.return_value=Response(b'abcdef')
        with mock.patch.object(p,'Client',return_value=client),self.assertRaises(core.LabError):
            artifacts.download_public(self.storage,URL,expected)
        self.assertEqual(target.with_suffix('.part').read_bytes(),b'ab')

    def test_actual_interruption_retains_bytes_and_next_attempt_resumes(self):
        expected=self.expected();target=self.storage.path('cache/sha256/'+expected['sha256'])
        first=Response(b'',206,**{'Content-Range':'bytes 0-5/6','Content-Length':'6'})
        first.read=mock.Mock(side_effect=[b'ab',http.client.IncompleteRead(b'')])
        client=mock.Mock();client.open.return_value=first
        with mock.patch.object(p,'Client',return_value=client),self.assertRaises(core.LabError):
            artifacts.download_public(self.storage,URL,expected)
        self.assertFalse(target.exists())
        self.assertEqual(target.with_suffix('.part').read_bytes(),b'ab')
        client.open.return_value=Response(b'cdef',206,**{'Content-Range':'bytes 2-5/6'})
        with mock.patch.object(p,'Client',return_value=client):
            self.assertEqual(artifacts.download_public(self.storage,URL,expected).read_bytes(),b'abcdef')
        self.assertEqual(client.open.call_args.args,(URL,2))

    def test_html_denial_never_creates_partial_archive(self):
        expected=self.expected()
        client=PublicTransportTests().client([Response(b'<html>Sign in</html>',**{'Content-Type':'text/html'})])
        with mock.patch.object(p,'Client',return_value=client),self.assertRaises(core.LabError):
            artifacts.download_public(self.storage,URL,expected)
        self.assertFalse(self.storage.path('cache/sha256/'+expected['sha256']).with_suffix('.part').exists())


if __name__ == '__main__': unittest.main()
