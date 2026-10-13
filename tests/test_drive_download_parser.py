# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Stock-macOS parser fixtures; no provider payload or credential needed."""
from pathlib import Path
import subprocess
import tempfile
import unittest

PARSER = Path(__file__).resolve().parents[1]/'scripts/launcher/drive-download-macos.pl'
ID = 'public_file_123456789'
URL = 'https://drive.google.com/uc?export=download&id='+ID


class DriveParserTests(unittest.TestCase):
    def parse(self, mode, raw, url=URL):
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/'response';path.write_text(raw)
            return subprocess.run(['/usr/bin/perl',str(PARSER),mode,str(path),url],
                                  capture_output=True,text=True)
    def test_binary_and_html_headers(self):
        for mime,mode in [('application/octet-stream','binary'),('application/binary','binary'),('text/html; charset=utf-8','html')]:
            result=self.parse('headers','HTTP/2 200\r\nContent-Type: '+mime+'\r\n\r\n')
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(result.stdout,mode+'\t'+URL+'\n')
    def test_exact_redirect(self):
        target='https://drive.usercontent.google.com/download?export=download&id='+ID
        result=self.parse('headers','HTTP/2 303\r\nLocation: '+target+'\r\n\r\n')
        self.assertEqual(result.stdout,'redirect\t'+target+'\n')
    def form(self, id=ID, extra=''):
        return "Google Drive can't scan this file for viruses."+'''<form id="download-form" action="https://drive.usercontent.google.com/download" method="get">'''+''.join(
            '<input type="hidden" name="'+k+'" value="'+v+'">' for k,v in
            [('id',id),('export','download'),('confirm','t'),('uuid','123-abc')])+extra+'</form>'
    def test_confirmation_is_bounded_same_file(self):
        result=self.parse('form',self.form())
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('confirm\thttps://drive.usercontent.google.com/download?',result.stdout)
        self.assertIn('id='+ID,result.stdout)
    def test_resource_key_retained(self):
        result=self.parse('form',self.form(),URL+'&resourcekey=0-public')
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('resourcekey=0-public',result.stdout)
    def test_real_unnamed_submit_control_and_escaped_warning(self):
        raw=self.form(extra='<input type="submit" class="jfk-button" value="Download anyway">')
        raw=raw.replace("can't","can&#39;t")
        result=self.parse('form',raw)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('confirm\thttps://drive.usercontent.google.com/download?',result.stdout)
        self.assertNotIn('Download',result.stdout)
    def test_current_large_executable_warning_is_not_a_malware_verdict(self):
        raw=self.form(extra='<input type="submit" value="Download anyway">').replace(
            "Google Drive can't scan this file for viruses.",
            'Google Drive has detected issues with your download. This file is too large for Google to scan for viruses. '
            'This file is executable and may harm your computer.')
        self.assertEqual(self.parse('form',raw).returncode,0)
    def test_http_200_quota_page_is_not_a_binary_download(self):
        result=self.parse('payload-status','<title>Google Drive - Quota exceeded</title>Sorry, you can\'t view or download this file at this time.')
        self.assertEqual(result.stdout,'quota\n')
        self.assertEqual(self.parse('payload-status','<title>Unknown page</title>').stdout,'unsupported\n')
    def test_rejects_foreign_duplicate_quota_and_oversized(self):
        cases=[('headers','HTTP/2 302\r\nLocation: https://evil.example/file\r\n\r\n'),
               ('headers','HTTP/2 200\r\nContent-Type: text/html\r\nContent-Type: application/octet-stream\r\n\r\n'),
               ('form',self.form('different_file_12345')),
               ('form',self.form(extra='<input type="hidden" name="id" value="'+ID+'">')),
               ('form',self.form()+' Download quota exceeded'),
               ('form',self.form()+'x'*65536)]
        for mode,raw in cases:
            with self.subTest(mode=mode,raw=raw[:70]):
                result=self.parse(mode,raw)
                self.assertNotEqual(result.returncode,0)
                self.assertEqual(result.stdout,'')
