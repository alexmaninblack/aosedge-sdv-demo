# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
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
        value['schemaVersion']=2
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


class AcquisitionTests(unittest.TestCase):
    """Real tiny Git repositories; no network, SDK, build or runtime."""
    def setUp(self):
        temporary=tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base=Path(temporary.name).resolve()
        self.env=dict(os.environ,GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL='/dev/null',GIT_TERMINAL_PROMPT='0')
        self.origin=self.base/'origin';self.origin.mkdir()
        self.git(self.origin,'init','--quiet')
        self.git(self.origin,'-c','user.name=Fixture','-c','user.email=fixture@example.invalid',
                 'commit','--allow-empty','--quiet','-m','application')
        self.wanted=self.git(self.origin,'rev-parse','HEAD')
        self.git(self.origin,'-c','user.name=Fixture','-c','user.email=fixture@example.invalid',
                 'commit','--allow-empty','--quiet','-m','producer')
        self.producer=self.base/'producer'
        subprocess.run(['/usr/bin/git','clone','--quiet','--depth=1',self.origin.as_uri(),str(self.producer)],
                       env=self.env,check=True,capture_output=True)
        self.selected={role:dict(repository=self.origin.as_uri(),revision=self.wanted) for role in native_sources.ROLES}
        workspace=self.base/'workspace';workspace.mkdir()
        self.storage=SimpleNamespace(release=SimpleNamespace(sources=self.selected),
            path=lambda relative:workspace/relative,environment=lambda **kwargs:self.env)

    def git(self,path,*args):
        return subprocess.run(['/usr/bin/git','-C',str(path),'-c','core.hooksPath=/dev/null',*args],
            env=self.env,check=True,text=True,capture_output=True).stdout.strip()

    def prepare(self,acquire=True):
        with patch.object(native_sources,'ROOT',self.producer):
            return native_sources.prepare(self.storage,self.selected,acquire,lambda *args:None)

    def test_shallow_producer_acquires_missing_exact_commit_from_declared_origin(self):
        with self.assertRaises(subprocess.CalledProcessError):
            self.git(self.producer,'cat-file','-e',self.wanted+'^{commit}')
        before=self.git(self.producer,'rev-parse','HEAD')
        paths=self.prepare()
        for path in paths.values():
            self.assertEqual(self.git(path,'rev-parse','HEAD'),self.wanted)
            self.assertEqual(self.git(path,'remote','get-url','origin'),self.origin.as_uri())
        self.assertEqual(self.git(self.producer,'rev-parse','HEAD'),before)
        with self.assertRaises(subprocess.CalledProcessError):
            self.git(self.producer,'cat-file','-e',self.wanted+'^{commit}')
        self.assertEqual(self.prepare(False),paths)

    def test_existing_exact_object_is_reused_without_changing_producer(self):
        self.git(self.producer,'fetch','--quiet','origin',self.wanted)
        with patch.object(native_sources,'git',wraps=native_sources.git) as calls:
            paths=self.prepare()
        fetches=[call.args[1] for call in calls.call_args_list if call.args[1][0]=='fetch']
        self.assertEqual(fetches[0][-2:],[str(self.producer),self.wanted])
        self.assertEqual(self.git(paths['integration'],'rev-parse','HEAD'),self.wanted)

    def test_no_acquire_permission_cannot_create_or_fetch_a_checkout(self):
        with self.assertRaisesRegex(LabError,'explicit preparation'):
            self.prepare(False)
        self.assertFalse(self.storage.path('sources').exists())

    def test_wrong_producer_repository_cannot_supply_native_objects(self):
        self.git(self.producer,'remote','set-url','origin','https://example.invalid/unrelated.git')
        with self.assertRaisesRegex(LabError,'producer repository differs'):
            self.prepare()
        path=self.storage.path('sources/native-ui/integration')/self.wanted
        with self.assertRaises(subprocess.CalledProcessError):self.git(path,'rev-parse','HEAD')


if __name__=='__main__':unittest.main()
