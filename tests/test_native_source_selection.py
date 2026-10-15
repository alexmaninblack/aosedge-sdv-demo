# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from reproduction import native_sources,chain
from reproduction.core import LabError,Release
import developer_build


class SelectionTests(unittest.TestCase):
    def setUp(self):
        self.release=Release()
        self.selection={r:{k:self.release.sources[r][k] for k in ('repository','revision')}
                        for r in native_sources.ROLES}
    def test_complete_explicit_roles(self):
        self.assertEqual(native_sources.validate(self.selection,self.release),self.selection)
    def test_arbitrary_repository_rejected(self):
        self.selection['vehicle-gateway']['repository']='https://example.com/foreign.git'
        with self.assertRaises(LabError):native_sources.validate(self.selection,self.release)
    def test_mutable_revision_rejected(self):
        self.selection['integration']['revision']='main'
        with self.assertRaises(LabError):native_sources.validate(self.selection,self.release)
    def test_missing_and_additional_roles_rejected(self):
        for role in ('missing','extra'):
            value=deepcopy(self.selection)
            if role=='missing':del value['vehicle-gateway']
            else:value['arbitrary']=value['integration']
            with self.assertRaises(LabError):native_sources.validate(value,self.release)
    def test_extra_executable_field_rejected(self):
        self.selection['integration']['command']='do something'
        with self.assertRaises(LabError):native_sources.validate(self.selection,self.release)
    def test_declared_producer_can_be_current_integration_tree(self):
        storage=SimpleNamespace(environment=lambda:{},path=lambda p:Path('/selected')/p)
        row=self.selection['integration']
        with patch.object(native_sources,'git',return_value=row['revision']):
            self.assertEqual(native_sources.location(storage,'integration',row),native_sources.ROOT)
    def test_gateway_never_adopts_unrelated_sibling_checkout(self):
        storage=SimpleNamespace(environment=lambda:{},path=lambda p:Path('/selected')/p)
        row=self.selection['vehicle-gateway'];path=native_sources.location(storage,'vehicle-gateway',row)
        self.assertEqual(path,Path('/selected/sources/native-ui/vehicle-gateway')/row['revision'])
    def test_schema_three_preserves_historical_base(self):
        value=json.loads(developer_build.selected_plan(chain.ROOT).read_bytes())
        value['schemaVersion']=3;value['nativeSources']=self.selection
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory).resolve()/'plan.json';p.write_text(json.dumps(value))
            self.assertEqual(chain.read_plan(self.release,p)['nativeSources'],self.selection)
    def test_old_schema_cannot_sneak_in_native_override(self):
        value=json.loads((chain.ROOT/chain.PLAN).read_bytes())
        value['nativeSources']=self.selection
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory).resolve()/'plan.json';p.write_text(json.dumps(value))
            with self.assertRaises(LabError):chain.read_plan(self.release,p)

    def test_missing_active_plan_cannot_fall_back_to_a_retired_build(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory).resolve()
            with self.assertRaisesRegex(developer_build.WorkflowError, 'selection is missing'):
                developer_build.selected_plan(root)

    def test_active_plan_is_pinned_not_a_mutable_filename(self):
        import hashlib
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory).resolve();(root/'workspace/releases').mkdir(parents=True)
            relative='workspace/releases/successor.json';(root/relative).write_bytes(b'{}')
            selector=root/'workspace/current-developer-build.json'
            selector.write_text(json.dumps(dict(schemaVersion=1,path=relative,sha256=hashlib.sha256(b'{}').hexdigest())))
            self.assertEqual(developer_build.selected_plan(root),root/relative)
            (root/relative).write_bytes(b'changed')
            with self.assertRaises(developer_build.WorkflowError):developer_build.selected_plan(root)

    def test_active_plan_cannot_escape_release_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory).resolve();(root/'workspace').mkdir()
            selector=root/'workspace/current-developer-build.json'
            selector.write_text(json.dumps(dict(schemaVersion=1,path='../foreign.json',sha256='a'*64)))
            with self.assertRaises(developer_build.WorkflowError):developer_build.selected_plan(root)


if __name__=='__main__':unittest.main()
