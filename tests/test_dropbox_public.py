# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
import sys
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch
from email.message import Message
import tempfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from reproduction.dropbox_public import public_link,cdn_link,observe,Redirects
from urllib.request import Request

URL='https://www.dropbox.com/scl/fo/folder_public_123/file_public_123/package.dmg?rlkey=reader_public_123&dl=1'
CDN='https://uc12345.dl.dropboxusercontent.com/cd/0/inline2/public_data_123/file?dl=1'


class DropboxPublicTests(TestCase):
    def test_exact_public_file_not_credentials_or_folder_archive(self):
        self.assertEqual(public_link(URL),URL)
        for value in (URL.replace('https:','http:'),URL+'&dl=1',URL.replace('www.dropbox.com','www.dropbox.com.evil.example'),
                      URL.replace('package.dmg','package.zip'),URL.replace('/package.dmg',''),
                      URL.replace('package.dmg','parent%2Fpackage.dmg'),URL.replace('dl=1','dl=0')):
            with self.subTest(value=value),self.assertRaises(ValueError):public_link(value)

    def test_cdn_and_head_only_redirect(self):
        self.assertTrue(cdn_link(CDN))
        self.assertFalse(cdn_link(CDN.replace('https:','http:')))
        result=Redirects().redirect_request(Request(URL,method='HEAD'),None,302,'',{},CDN+'#')
        self.assertEqual(result.get_method(),'HEAD');self.assertEqual(result.full_url,CDN)
        for url,method in [('https://evil.example/file','HEAD'),(CDN,'GET')]:
            with self.assertRaises(ValueError):Redirects().redirect_request(Request(URL,method=method),None,302,'',{},url)

    def test_metadata_adoption_never_reads_payload_or_claims_provider_sha(self):
        class Response:
            status=200;url=CDN
            headers=Message()
            headers['Content-Length']='14'
            def __enter__(self):return self
            def __exit__(self,*args):return False
            def read(self,*args):raise AssertionError('Payload must not be downloaded')
        with patch('reproduction.dropbox_public.build_opener') as create:
            create.return_value.open.return_value=Response()
            result=observe(URL,14)
            self.assertFalse(result['payloadDownloaded']);self.assertFalse(result['providerChecksumAvailable'])
            self.assertTrue(result['consumerChecksumRequired'])
            self.assertEqual(create.return_value.open.call_args.args[0].get_method(),'HEAD')
            with self.assertRaises(ValueError):observe(URL,13)

    def test_delivery_successor_has_separate_records_without_version_change(self):
        from release_owners import Owners
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory).resolve()
            selected=dict(workspace=str(root),gateway=str(root/'gateway'),
                          candidate=dict(directory=str(root/'candidate')),
                          version='1.2.0-rc.1',delivery=dict(folderId='public_folder_123',account='test@example.com'))
            old=Owners(selected)
            current=Owners(dict(selected,delivery=dict(provider='dropbox',downloadURL=URL)))
            self.assertEqual(old.root.name,'1.2.0-rc.1')
            self.assertEqual(current.root.name,'1.2.0-rc.1-dropbox')
            self.assertNotEqual(old.root,current.root)
