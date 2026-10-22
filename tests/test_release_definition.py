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
    def operator_fixture(self,root,**changes):
        self.copy_current_fixture(root)
        catalog_path=root/self.selected['operatorSelection']
        catalog=gate.read_json(catalog_path)
        delivery_path=root/catalog['operatorDescriptor']
        delivery=gate.read_json(delivery_path)
        delivery.update(changes)
        for field in ('productVersion','status','file','bytes','sha256','manifestSha256','notarized'):
            catalog['operator'][field]=delivery[field]
        delivery_path.write_text(json.dumps(delivery));catalog_path.write_text(json.dumps(catalog))
        return catalog_path
    def test_operator_successor_preserves_frozen_developer_input_and_cache_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            self.operator_fixture(root,productVersion='1.2.0-rc.99',
                file='AosEdge-SDV-Lab-1.2.0-rc.99.dmg',bytes=456,sha256='a'*64)
            before={p:(root/p).read_bytes() for p in self.selected['inputs'].values()}
            self.assertEqual(gate.resolve(self.selected,root),self.value)
            self.assertTrue(all((root/p).read_bytes()==raw for p,raw in before.items()))
    def test_operator_media_is_not_a_runtime_build_input(self):
        self.assertNotIn('dmg', self.value['artifacts'])
        self.assertNotIn('application', self.value)
        self.assertNotIn('applicationManifest', self.value['artifacts'])
        value=copy.deepcopy(self.value)
        value['artifacts']['dmg']=dict(name='obsolete.dmg',bytes=123,sha256='a'*64,digestEvidence='fixture')
        with self.assertRaises(gate.DefinitionError):gate.validate_inputs(value)
    def test_retained_groups_do_not_require_an_old_application(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);rows=[]
            for name in ('host-runtime','preparation-inputs','vm-runtime','cloud-runtime','backend-inputs'):
                value={'fixture':name}
                if name=='vm-runtime':value['hostManifest']={k:rows[0][k] for k in ('path','bytes','sha256')}
                raw=json.dumps(value).encode();path=name+'.json';(root/path).write_bytes(raw)
                rows.append(dict(id=name,path=path,kitPath=path,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
            value={'inputs':rows}
            self.assertEqual(gate.verify_kit(value,root),5)
            self.assertFalse((root/'application-manifest.json').exists())
            (root/'host-runtime.json').write_bytes(b'changed')
            with self.assertRaisesRegex(gate.DefinitionError,'digest/size mismatch'):gate.verify_kit(value,root)
    def test_retained_vm_host_binding_is_still_independently_required(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);rows=[]
            for name in ('host-runtime','vm-runtime'):
                raw=json.dumps({'hostManifest':{}}).encode();path=name+'.json';(root/path).write_bytes(raw)
                rows.append(dict(id=name,path=path,kitPath=path,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
            with self.assertRaisesRegex(gate.DefinitionError,'VM/host manifest binding mismatch'):
                gate.verify_kit({'inputs':rows},root)
    def test_changed_material_closure_cannot_reuse_cache_namespace_automatically(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);self.copy_current_fixture(root)
            selected=copy.deepcopy(self.selected)
            path=selected['inputs']['runtime']
            runtime=gate.read_json(root/path);runtime['artifacts']['factory']['sha256']='f'*64
            raw=(json.dumps(runtime,indent=2)+'\n').encode();(root/path).write_bytes(raw)
            next(row for row in selected['authorities'] if row['path']==path)['sha256']=hashlib.sha256(raw).hexdigest()
            with self.assertRaisesRegex(gate.DefinitionError,'Cache compatibility input closure differs'):
                gate.resolve(selected,root)
    def test_operator_mismatch_or_invalid_successor_is_rejected(self):
        for changes in (dict(sha256='invalid'),dict(bytes=True),dict(notarized=True)):
            with self.subTest(changes=changes),tempfile.TemporaryDirectory() as temporary:
                root=Path(temporary);self.operator_fixture(root,**changes)
                with self.assertRaises(gate.DefinitionError):gate.resolve(self.selected,root)
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);path=self.operator_fixture(root)
            catalog=gate.read_json(path);catalog['operator']['sha256']='a'*64
            path.write_text(json.dumps(catalog))
            with self.assertRaises(gate.DefinitionError):gate.resolve(self.selected,root)
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
                            ('old-application',lambda v:v.update(application={'sha256':'a'*64}))]:
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
