# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Product owner guards use Git blobs, not version labels or executable owners."""
import json
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
            root=Path(temporary).resolve();path=root/'plan.json'
            path.write_text(json.dumps({'producers':{'application':'a'*40,'media':'b'*40}}))
            row={'app.py':('100644','blob','c'*40)}
            with patch.object(product,'tree',return_value=row), \
                    patch.object(product.recipes,'paths',return_value=['app.py']):
                checked=product.check(root,path)
            self.assertEqual(set(checked),{'application','media'})
            self.assertTrue(all(x['verifiedFiles']==1 for x in checked.values()))
