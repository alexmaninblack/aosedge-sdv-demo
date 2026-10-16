# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Standalone current input security proofs; no builds, Git history or network."""
import copy
import hashlib
import importlib.machinery
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[1]
loader = importlib.machinery.SourceFileLoader('release_definition', str(ROOT/'scripts/validate-release-definition'))
spec = importlib.util.spec_from_loader(loader.name,loader)
gate = importlib.util.module_from_spec(spec)
loader.exec_module(gate)

class ReleaseDefinitionTests(unittest.TestCase):
    @staticmethod
    def copy_current_fixture(root):
        selected=gate.read_json(ROOT/gate.DEFAULT)
        value=gate.resolve(selected)
        paths={str(gate.DEFAULT),str(gate.CURRENT_SCHEMA),str(gate.SCHEMA),
               '.github/workflows/repository-boundaries.yml',*selected['documentation'],
               *(r['path'] for r in selected['authorities']),selected['developerSelection'],selected['operatorSelection']}
        paths.add(gate.read_json(ROOT/selected['developerSelection'])['path'])
        paths.add(gate.read_json(ROOT/selected['operatorSelection'])['operatorDescriptor'])
        paths.update(t['evidence'] for t in value['toolchains'])
        paths.update(r['path'] for c in value['components'] for r in c['recipes'] if r['source']=='integration')
        for name in paths:
            target=root/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
    def setUp(self):
        self.selected=gate.read_json(ROOT/gate.DEFAULT)
        self.value=gate.resolve(self.selected)
    def test_current_definition_is_self_contained(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);self.copy_current_fixture(root)
            with patch.object(gate.subprocess,'run',side_effect=AssertionError('No subprocess')):
                self.assertEqual(gate.resolve(self.selected,root),self.value)
            self.assertFalse((root/'.git').exists());self.assertFalse((root/'workspace/checkpoints').exists())
    def test_schema_negative_matrix(self):
        cases=[('unknown',lambda v:v.update(ready=True)),('profile',lambda v:v['profiles'][0].update(id='automatic')),
               ('bool-size',lambda v:v['inputs'][0].update(bytes=True)),('branch',lambda v:v['sources'][0].update(revision='main')),
               ('missing-component',lambda v:v['components'].pop()),('gate-empty',lambda v:v.update(gates=[]))]
        for name,change in cases:
            v=copy.deepcopy(self.value);change(v)
            with self.subTest(name=name),self.assertRaises(gate.DefinitionError):gate.validate_inputs(v)
    def test_source_and_runtime_tampering_rejected(self):
        for name,change in [('source',lambda v:v['sources'][0].update(revision='a'*40)),
                            ('access',lambda v:next(s for s in v['sources'] if s['id']=='unreal-engine').update(access='public-git')),
                            ('manifest',lambda v:v['inputs'][0].update(sha256='a'*64)),
                            ('provenance',lambda v:v['application'].update(originalBuildHadUncommittedSources=False))]:
            v=copy.deepcopy(self.value);change(v)
            with self.subTest(name=name),self.assertRaises(gate.DefinitionError):gate.validate_inputs(v)
    def test_dependency_cycle_and_unknown_dependency_rejected(self):
        for requirements in (['carla'],['unknown']):
            v=copy.deepcopy(self.value);v['components'][0]['requires']=requirements
            with self.assertRaises(gate.DefinitionError):gate.validate_inputs(v)
    def test_operator_never_builds(self):
        v=copy.deepcopy(self.value);v['components'][0]['actions']['operator']='build'
        with self.assertRaises(gate.DefinitionError):gate.validate_inputs(v)
    def test_all_profiles_fail_closed_on_qualification(self):
        for profile in gate.PROFILES:self.assertIn('PROFILE_NOT_QUALIFIED',gate.readiness(self.value,profile)[-1])
    def test_unknown_schema_keyword_fails(self):
        with self.assertRaises(gate.DefinitionError):gate.schema_check('x',{'format':'email'})
    def test_duplicate_json_and_escaping_paths_fail(self):
        with tempfile.TemporaryDirectory() as temporary:
            p=Path(temporary)/'duplicate.json';p.write_text('{"a":1,"a":2}')
            with self.assertRaises(gate.DefinitionError):gate.read_json(p)
            with self.assertRaises(gate.DefinitionError):gate.safe_path(Path(temporary),'../escape')
