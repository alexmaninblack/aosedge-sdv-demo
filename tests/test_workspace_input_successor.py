# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Public source successors preserve old catalog records and binary caches."""
import ast
from contextlib import redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import runpy
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]


class SuccessorTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root=Path(temporary.name).resolve()
        self.write('workspace/inputs/source.json',dict(unchanged=True))
        self.write('workspace/inputs/cache.json',dict(inputClosure={
            'workspace/inputs/source.json':self.sha('workspace/inputs/source.json')}))
        self.write('workspace/build-definition.json',dict(inputs=dict(
            sources='workspace/inputs/source.json',cache='workspace/inputs/cache.json'),
            authorities=[dict(path='workspace/inputs/source.json',sha256=self.sha('workspace/inputs/source.json'))]))
        self.write('workspace/releases/build-plan.json',dict(productVersion='1.2.0-rc.1'))
        self.write('workspace/current-developer-build.json',dict(schemaVersion=1,
            path='workspace/releases/build-plan.json',sha256=self.sha('workspace/releases/build-plan.json')))
        files={p:self.sha(p) for p in ('workspace/build-definition.json','workspace/releases/build-plan.json')}
        self.original=dict(id='inputs-old-dropbox',productVersion='1.2.0-rc.1',sourceFiles=files,
            dependencyGroups=dict(unchangedBinaryPackages=dict(sha256='a'*64,bytes=100)))
        self.write('workspace/dependencies/catalog.json',dict(schemaVersion=1,product='aosedge-sdv-lab',
            catalogRevision=1,releases=[self.original]))
        pin=dict(releaseId='inputs-private',sourceFiles=files,recordSha256='b'*64)
        public=dict(releaseId=self.original['id'],recordSha256=self.digest(self.original),url='https://example.invalid/catalog')
        path=self.root/'scripts/developer_catalog.py';path.parent.mkdir(parents=True)
        path.write_text('PIN = '+repr(pin)+'\nPUBLIC_PIN = '+repr(public)+'\n')
        self.main=runpy.run_path(str(ROOT/'scripts/sync-workspace-inputs'))['main']
        self.main.__globals__['ROOT']=self.root
        self.cache=(self.root/'workspace/inputs/cache.json').read_bytes()

    def write(self,name,value):
        path=self.root/name;path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(value,indent=2)+'\n')

    def read(self,name):return json.loads((self.root/name).read_bytes())
    def sha(self,name):return hashlib.sha256((self.root/name).read_bytes()).hexdigest()
    def digest(self,value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    def run_tool(self,*args):
        with patch.object(sys,'argv',['sync-workspace-inputs',*args]),redirect_stdout(io.StringIO()):
            self.main()

    def change_plan(self):self.write('workspace/releases/build-plan.json',dict(productVersion='1.2.0-rc.3'))

    def test_changed_source_requires_explicit_successor_without_partial_writes(self):
        self.change_plan()
        before=(self.root/'workspace/current-developer-build.json').read_bytes()
        with self.assertRaisesRegex(SystemExit,'explicit --new-record-id'):self.run_tool('--write')
        self.assertEqual((self.root/'workspace/current-developer-build.json').read_bytes(),before)
        self.assertEqual(self.read('workspace/dependencies/catalog.json')['releases'],[self.original])

    def test_successor_repeat_and_check_preserve_old_record_and_cache(self):
        self.change_plan()
        self.run_tool('--write','--new-record-id','inputs-rc3-dropbox')
        catalog=self.read('workspace/dependencies/catalog.json')
        self.assertEqual(catalog['catalogRevision'],2)
        self.assertEqual(catalog['releases'][0],self.original)
        selected=catalog['releases'][1]
        self.assertEqual(selected['productVersion'],'1.2.0-rc.3')
        self.assertEqual(selected['dependencyGroups'],self.original['dependencyGroups'])
        self.assertNotEqual(selected['sourceFiles'],self.original['sourceFiles'])
        values={node.targets[0].id:ast.literal_eval(node.value) for node in ast.parse(
            (self.root/'scripts/developer_catalog.py').read_text()).body}
        self.assertEqual(values['PUBLIC_PIN']['releaseId'],'inputs-rc3-dropbox')
        self.assertEqual(values['PUBLIC_PIN']['recordSha256'],self.digest(selected))
        self.run_tool('--write','--new-record-id','inputs-rc3-dropbox')
        self.run_tool('--check')
        self.assertEqual(self.read('workspace/dependencies/catalog.json'),catalog)
        self.assertEqual((self.root/'workspace/inputs/cache.json').read_bytes(),self.cache)

    def test_collision_corruption_and_changed_input_closure_fail_closed(self):
        self.change_plan()
        catalog=self.read('workspace/dependencies/catalog.json')
        catalog['releases'].append(dict(id='inputs-rc3-dropbox',foreign=True))
        self.write('workspace/dependencies/catalog.json',catalog)
        with self.assertRaisesRegex(SystemExit,'collision'):
            self.run_tool('--write','--new-record-id','inputs-rc3-dropbox')
        catalog['releases'][0]['productVersion']='modified'
        self.write('workspace/dependencies/catalog.json',catalog)
        with self.assertRaisesRegex(SystemExit,'record changed'):
            self.run_tool('--write','--new-record-id','inputs-rc3-dropbox')
        self.write('workspace/inputs/source.json',dict(changed=True))
        with self.assertRaisesRegex(SystemExit,'Input semantics changed'):
            self.run_tool('--write','--new-record-id','inputs-rc3-dropbox')

    def test_missing_or_invalid_explicit_identity_is_not_adopted(self):
        for arguments in (('--new-record-id','inputs-new-dropbox'),
                          ('--write','--new-record-id','../escape'),
                          ('--write','--new-record-id','inputs-new')):
            with self.subTest(arguments=arguments),self.assertRaises(SystemExit):self.run_tool(*arguments)
