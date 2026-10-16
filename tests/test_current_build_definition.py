# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Current selection and unchanged dependency/cache identities, without builds."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from test_release_definition import gate,ROOT,ReleaseDefinitionTests
class CurrentBuildDefinitionTests(unittest.TestCase):
    def setUp(self):self.value=gate.read_json(ROOT/gate.DEFAULT)
    def test_v3_has_no_compatibility_base_or_old_reports(self):
        self.assertEqual(self.value['schemaVersion'],3)
        self.assertNotIn('compatibilityBase',self.value);self.assertNotIn('historicalEvidence',self.value)
        self.assertEqual(gate.resolve(self.value)['id'],'sdv-lab-current')
    def test_bad_authority_and_missing_authority_fail(self):
        for change in (lambda v:v['authorities'][0].update(sha256='0'*64),lambda v:v['authorities'].pop(0)):
            v=copy.deepcopy(self.value);change(v)
            with self.assertRaises(gate.DefinitionError):gate.resolve(v)
    def test_unknown_fields_and_boolean_schema_fail(self):
        for field,value in [('schemaVersion',True),('ready',True),('qualified',True)]:
            v=copy.deepcopy(self.value);v[field]=value
            with self.assertRaises(gate.DefinitionError):gate.resolve(v)
    def test_current_working_tree_does_not_depend_on_git_history(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);ReleaseDefinitionTests.copy_current_fixture(root)
            with patch.object(gate.subprocess,'run',side_effect=AssertionError):gate.resolve(self.value,root)
    def test_exact_cache_namespace_preserved_without_receipt_rewriting(self):
        from reproduction.core import Release
        r=Release();self.assertEqual(r.key,'cdfec741dc784774a1bcbe57c536a65e9d8c4a2077a68ad8b97104eabd7c2598')
        self.assertEqual(r.cache_id,'kit028-setup042');self.assertEqual(r.value['id'],'sdv-lab-current')
    def test_only_current_plan_selected(self):
        from reproduction.core import Release
        from reproduction.chain import read_plan
        selector=gate.read_json(ROOT/self.value['developerSelection'])
        self.assertEqual(selector['path'],'workspace/releases/build-plan.json')
        self.assertEqual(read_plan(Release()),gate.read_json(ROOT/selector['path']))
    def test_deleted_paths_are_not_inputs(self):
        self.assertFalse((ROOT/'workspace/checkpoints').exists())
        self.assertEqual({p.name for p in (ROOT/'workspace/releases').glob('*')},{'build-plan.json','delivery.json'})
    def test_changed_lock_fails_before_use(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);ReleaseDefinitionTests.copy_current_fixture(root)
            for role in ('sources','runtime','controllers','services','cache'):
                path=root/self.value['inputs'][role];original=path.read_bytes();path.write_bytes(b'{}')
                with self.subTest(role=role),self.assertRaises(gate.DefinitionError):gate.resolve(self.value,root)
                path.write_bytes(original)
