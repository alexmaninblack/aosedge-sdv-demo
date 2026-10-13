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
        for mime,mode in [('application/octet-stream','binary'),('text/html; charset=utf-8','html')]:
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
