# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Offline Dropbox delivery fixtures; no real payload or account access."""
from pathlib import Path
import subprocess
import tempfile
import unittest

PARSER = Path(__file__).resolve().parents[1]/'scripts/launcher/drive-download-macos.pl'
URL = ('https://www.dropbox.com/scl/fo/public_folder_123/public_file_123/'
       'AosEdge-SDV-Lab-preview.dmg?rlkey=public_reader_123&dl=1')
CDN = 'https://uc123456789.dl.dropboxusercontent.com/cd/0/inline/public_download_123/file?dl=1'


class DropboxParserTests(unittest.TestCase):
    def parse(self, mode, text, url=URL, size=None):
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/'response';path.write_text(text)
            args=['/usr/bin/perl',str(PARSER),mode,str(path),url]
            if size is not None:args.append(str(size))
            return subprocess.run(args,
                                  capture_output=True,text=True)

    def test_observed_cdn_redirect_and_binary(self):
        result=self.parse('headers','HTTP/2 302\r\nLocation: '+CDN+'#\r\n\r\n')
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(result.stdout,'redirect\t'+CDN+'\n')
        result=self.parse('headers','HTTP/2 200\r\nContent-Type: application/octet-stream\r\n\r\n',CDN)
        self.assertEqual(result.stdout,'binary\t'+CDN+'\n')

    def test_file_share_is_supported_but_folder_zip_is_not(self):
        share=URL.replace('fo/public_folder_123/public_file_123','fi/public_file_123')
        header='HTTP/2 200\r\nContent-Type: application/octet-stream\r\n\r\n'
        self.assertEqual(self.parse('headers',header,share).returncode,0)
        for url in (URL.replace('/AosEdge-SDV-Lab-preview.dmg',''),
                    URL.replace('.dmg?', '.zip?'),URL.replace('dl=1','dl=0')):
            self.assertNotEqual(self.parse('headers',header,url).returncode,0)

    def test_cross_provider_foreign_host_and_credentials_are_rejected(self):
        targets=['https://evil.example/file',CDN.replace('dl.dropboxusercontent.com','dl.dropboxusercontent.com.evil.example'),
                 CDN.replace('https://','https://user:secret@'),CDN.replace('https:','http:'),
                 CDN+'#meaningful','https://drive.google.com/uc?export=download&id=public_file_12345']
        for target in targets:
            with self.subTest(target=target):
                result=self.parse('headers','HTTP/2 302\r\nLocation: '+target+'\r\n\r\n')
                self.assertNotEqual(result.returncode,0);self.assertEqual(result.stdout,'')

    def test_drive_cannot_redirect_to_dropbox(self):
        source='https://drive.google.com/uc?export=download&id=public_file_12345'
        self.assertNotEqual(self.parse('headers','HTTP/2 302\r\nLocation: '+CDN+'\r\n\r\n',source).returncode,0)

    def test_html_never_becomes_an_installer_or_google_confirmation(self):
        result=self.parse('headers','HTTP/2 200\r\nContent-Type: text/html\r\n\r\n',CDN)
        self.assertEqual(result.stdout,'html\t'+CDN+'\n')
        self.assertNotEqual(self.parse('form',"Google Drive can't scan this file for viruses.").returncode,0)

    def test_ambiguous_headers_and_bad_queries_are_rejected(self):
        for header in ('HTTP/2 302\r\nLocation: '+CDN+'\r\nLocation: '+CDN+'\r\n\r\n',
                       'HTTP/2 200\r\nContent-Type: text/html\r\nContent-Type: application/octet-stream\r\n\r\n'):
            self.assertNotEqual(self.parse('headers',header).returncode,0)
        for url in (URL+'&dl=1',URL+'&unknown=value',URL.replace('preview.dmg','preview%2Ffile.dmg')):
            self.assertNotEqual(self.parse('headers','HTTP/2 200\r\nContent-Type: application/octet-stream\r\n\r\n',url).returncode,0)

    def test_observed_relative_second_cdn_redirect(self):
        target=CDN.replace('/inline/','/inline2/')
        relative=target[target.index('/cd/'):]
        result=self.parse('headers','HTTP/2 302\r\nLocation: '+relative+'\r\n\r\n',CDN)
        self.assertEqual(result.stdout,'redirect\t'+target+'\n')
        self.assertNotEqual(self.parse('headers','HTTP/2 302\r\nLocation: //evil.example/file\r\n\r\n',CDN).returncode,0)
        for shape in ('get','get2'):
            target=CDN.replace('/inline/','/'+shape+'/')
            result=self.parse('headers','HTTP/2 302\r\nLocation: '+target+'\r\n\r\n',CDN)
            self.assertEqual(result.stdout,'redirect\t'+target+'\n')

    def test_observed_json_attachment_requires_exact_approved_length(self):
        header=('HTTP/2 200\r\nContent-Type: application/json\r\n'
                'Content-Disposition: attachment; filename=unspecified\r\nContent-Length: 14165529112\r\n\r\n')
        self.assertEqual(self.parse('headers',header,CDN,14165529112).stdout,'binary\t'+CDN+'\n')
        for url,size,text in [(CDN,None,header),(CDN,10,header),(URL,14165529112,header),
                              (CDN,14165529112,header.replace('filename=unspecified','filename=error.json')),
                              (CDN,14165529112,header.replace('14165529112','25'))]:
            self.assertNotEqual(self.parse('headers',text,url,size).returncode,0)
