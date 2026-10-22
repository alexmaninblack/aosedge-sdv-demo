# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Product owner guards use Git blobs, not version labels or executable owners."""
import json
import hashlib
import os
import subprocess
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from reproduction import product_sources as product
from reproduction.core import LabError


class ProductSourceTests(unittest.TestCase):
    def plan(self, root, revision):
        path=root/'workspace/releases/build-plan.json';path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps({'producers':{'application':revision,'media':revision}}))
        (root/'workspace/current-developer-build.json').write_text(json.dumps(dict(
            schemaVersion=1,path='workspace/releases/build-plan.json',
            sha256=hashlib.sha256(path.read_bytes()).hexdigest())))
        return path

    def test_unchanged_blobs_and_modes_are_accepted(self):
        row=('100644','blob','a'*40)
        product.compare({'app.py':row}, {'app.py':row,'docs.md':('100644','blob','b'*40)}, {'app.py'})

    def test_missing_changed_linked_or_mode_changed_inputs_are_rejected(self):
        current={'app.py':('100644','blob','a'*40)}
        for selected in ({}, {'app.py':('100644','blob','b'*40)},
                         {'app.py':('100755','blob','a'*40)}, {'app.py':('120000','blob','a'*40)}):
            with self.subTest(selected=selected), self.assertRaises(LabError):
                product.compare(current,selected,{'app.py'})

    def test_git_inspection_disables_fetch_prompts_and_has_no_execution(self):
        result=SimpleNamespace(returncode=0,stdout=b'100644 blob '+b'a'*40+b'\tapp.py\0')
        with patch.object(product.subprocess,'run',return_value=result) as run:
            self.assertIn('app.py',product.tree(Path('/fixture'),'a'*40))
        args=run.call_args
        self.assertEqual(args.args[0][3:], ['ls-tree','-r','-z','a'*40])
        self.assertEqual(args.kwargs['env']['GIT_NO_LAZY_FETCH'],'1')
        self.assertEqual(args.kwargs['env']['GIT_TERMINAL_PROMPT'],'0')
        with patch.object(product.subprocess,'run',side_effect=AssertionError('No Git')):
            with self.assertRaises(LabError):product.tree(Path('/fixture'),'main')

    def test_both_packaging_roles_are_checked_without_importing_them(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary).resolve();path=self.plan(root,'a'*40)
            row={'app.py':('100644','blob','c'*40)}
            with patch.object(product,'tree',return_value=row), \
                    patch.object(product.recipes,'paths',return_value=['app.py']):
                checked=product.check(root,path)
            self.assertEqual(set(checked),{'application','media'})
            self.assertTrue(all(x['verifiedFiles']==1 for x in checked.values()))

    def test_tampered_selector_is_rejected_before_git_inspection(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary).resolve();path=self.plan(root,'a'*40)
            path.write_text(path.read_text()+' ')
            with patch.object(product,'tree',side_effect=AssertionError('No Git')), \
                    self.assertRaisesRegex(LabError,'selector digest differs'):
                product.check(root,path)

    def test_source_freeze_then_selector_commit_is_not_a_payload_change(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary).resolve();path=self.plan(root,'a'*40)
            (root/'app.py').write_text('unchanged product\n')
            env={**os.environ,'GIT_CONFIG_GLOBAL':os.devnull,'GIT_CONFIG_NOSYSTEM':'1'}
            def git(*args):
                return subprocess.run(['git','-C',str(root),'-c','user.name=Fixture',
                    '-c','user.email=fixture@example.invalid',*args],env=env,check=True,
                    capture_output=True,text=True,timeout=20).stdout.strip()
            git('init','--quiet');git('add','.');git('commit','--quiet','-m','Freeze product sources')
            owner=git('rev-parse','HEAD');self.plan(root,owner)
            git('add','.');git('commit','--quiet','-m','Select frozen owner independently')
            names=['app.py','workspace/current-developer-build.json','workspace/releases/build-plan.json']
            with patch.object(product.recipes,'paths',return_value=names):
                self.assertTrue(all(v['verifiedFiles']==1 for v in product.check(root,path).values()))
                (root/'app.py').write_text('changed product\n')
                git('add','.');git('commit','--quiet','-m','Change actual product input')
                with self.assertRaisesRegex(LabError,'owner differs'):
                    product.check(root,path)
