# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
import copy
import io
from pathlib import Path
import shutil
import unittest
from unittest.mock import Mock, patch
from contextlib import redirect_stdout

from test_reproduction import StorageFixture
from reproduction import artifacts, build_inputs as b, core, dependencies as d, cli
import public_drive


class BuildInputsTests(StorageFixture, unittest.TestCase):
    def test_mutable_metadata_snapshotted_without_changing_producer(self):
        source=self.base/'factory-manifest.json'; source.write_bytes(b'{}')
        source.chmod(0o644)
        expected={'bytes':2, 'sha256':artifacts.sha256(source)}
        result=b.immutable_manifest(self.storage,source,expected)
        self.assertEqual(result.read_bytes(),source.read_bytes())
        self.assertEqual(result.stat().st_mode & 0o777,0o444)
        self.assertEqual(source.stat().st_mode & 0o777,0o644)
        self.assertEqual(result,b.immutable_manifest(self.storage,source,expected))
        result.chmod(0o644); result.write_bytes(b'[]')
        with self.assertRaises(core.LabError): b.immutable_manifest(self.storage,source,expected)
        self.assertEqual(result.read_bytes(),b'[]')

    def packages(self):
        result = {}
        for role, names in b.NAMES.items():
            members = []
            for i, name in enumerate(sorted(names)):
                source = self.base/(role+str(i))
                source.write_bytes(name.encode())
                source.chmod(0o444)
                members.append(b.member(source, name))
            result[role] = d.pack(self.storage, role, members, lambda *a:None,
                                  set_id=b.SET_ID, validate=b.rows_valid)
        return result

    def bundle(self):
        self.lock = {'schemaVersion':1, 'id':b.SET_ID, 'status':'PRIVATE_BUILD_INPUTS_NOT_PROFILE_QUALIFIED',
                     **b.ancestry(self.release), 'packages':self.packages()}
        self.lockfile = self.base/'lock.json'
        core.atomic_json(self.lockfile, self.lock)
        sim = {}
        for role, name in (('carla-runtime',d.HOST+'simulator/fixture'),
                           ('host-support',d.HOST+'host-runtime-manifest.json'),
                           ('gateway-sdk','gateway-sdk/sdk-manifest.json')):
            source = self.base/role
            source.write_bytes(b'{}')
            source.chmod(0o444)
            sim[role] = d.pack(self.storage, role, [b.member(source,name)], lambda *a:None)
        self.simulation = {'packages':sim}
        for row in (*sim.values(), *self.lock['packages'].values()):
            target = self.storage.path('cache/sha256/'+row['sha256'])
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(self.storage.path('exports/'+row['file']), target)
        self.bindings = {name:{'schemaVersion':1, 'lockDigest':core.digest(lock),
            'folderId':'private_folder_12345', 'files':{role:'file_123456789_'+role for role in lock['packages']}}
            for name,lock in (('buildInputs',self.lock),('simulation',self.simulation))}
        self.client = Mock(account=None)
        self.client.metadata.side_effect = AssertionError('No network with complete cache')
        self.patch('reproduction.build_inputs.consumers')

    def prepare(self):
        return b.prepare(self.storage,self.lock,self.simulation,self.bindings,self.client,lambda *a:None)

    def test_five_packages_first_repeat_offline_without_old_kit(self):
        self.bundle()
        state = self.storage.state_path.read_bytes()
        first = self.prepare()
        self.assertEqual(first['files'],17)
        self.assertFalse(first['profileReady'])
        self.assertEqual(first,self.prepare())
        self.assertEqual(self.storage.state_path.read_bytes(),state)
        self.client.metadata.assert_not_called()
        self.client.content.assert_not_called()

    def test_five_public_packages_first_download_repeat_and_no_oauth(self):
        from test_public_drive import Response
        self.bundle()
        contents={}
        for group,lock in (('buildInputs',self.lock),('simulation',self.simulation)):
            files={}
            for role,row in lock['packages'].items():
                url='https://drive.google.com/uc?export=download&id=public_fixture_'+role
                cache=self.storage.path('cache/sha256/'+row['sha256'])
                contents[url]=cache.read_bytes();cache.unlink()
                files[role]=url
            self.bindings[group]={'schemaVersion':2,'transport':'google-drive-public','lockDigest':core.digest(lock),'files':files}
        public=Mock()
        def open(url,offset):
            raw=contents[url]
            return Response(raw[offset:],206,**{'Content-Range':f'bytes {offset}-{len(raw)-1}/{len(raw)}'})
        public.open.side_effect=open
        with patch.object(public_drive,'Client',return_value=public): first=self.prepare()
        self.assertEqual(public.open.call_count,5)
        self.assertEqual(first['files'],17)
        with patch.object(public_drive,'Client',side_effect=AssertionError('complete cache stays offline')):
            self.assertEqual(self.prepare(),first)
        self.client.metadata.assert_not_called();self.client.content.assert_not_called()

    def test_reviewed_lock_rejects_ancestry_and_package_override(self):
        self.bundle()
        self.assertEqual(b.read_lock(self.lockfile,self.release),self.lock)
        for field,value in (('definitionDigest','0'*64),('factoryCheckpointSha256','0'*64),
                            ('simulationLockSha256','0'*64),('status','QUALIFIED')):
            core.atomic_json(self.lockfile,{**self.lock,field:value})
            with self.assertRaises(core.LabError): b.read_lock(self.lockfile,self.release)
        for field,value in (('file','../escape.tar.gz'),('files',1),('bytes',-1),('extra','x')):
            bad=copy.deepcopy(self.lock); bad['packages']['vehicle-bases'][field]=value
            core.atomic_json(self.lockfile,bad)
            with self.assertRaises(core.LabError): b.read_lock(self.lockfile,self.release)

    def test_only_exact_immutable_member_set_permitted(self):
        packages=self.packages()
        name=next(iter(b.NAMES['factory-image']))
        row={'path':name,'bytes':1,'mode':0o444,'sha256':'0'*64}
        for rows in ([row], [row,row], [{**row,'path':'operator-state/secret'}], [{**row,'mode':0o644}]):
            with self.assertRaises(core.LabError): b.rows_valid('factory-image',rows)
        self.assertEqual(packages['vehicle-bases']['files'],12)

    def test_changed_payload_preserved_and_not_adopted(self):
        self.bundle(); result=self.prepare()
        path=Path(result['factoryInputs'])/'factory-images/6.1.1-maninblack.41/main-qemuarm64.img'
        path.chmod(0o644); path.write_bytes(b'changed')
        with self.assertRaisesRegex(core.LabError,'changed'): self.prepare()
        self.assertEqual(path.read_bytes(),b'changed')

    def test_extra_file_and_missing_receipt_rejected(self):
        self.bundle(); result=self.prepare()
        root=Path(result['kitInputs']).parent
        extra=root/'unexpected'; extra.write_text('preserve')
        with self.assertRaises(core.LabError): self.prepare()
        self.assertTrue(extra.exists())
        root.with_suffix('.json').unlink()
        with self.assertRaises(OSError): self.prepare()

    def test_corrupted_archive_never_promoted(self):
        self.bundle(); expected=self.lock['packages']['vehicle-bases']
        self.storage.path('cache/sha256/'+expected['sha256']).write_bytes(b'X'*expected['bytes'])
        with self.assertRaisesRegex(core.LabError,'digest'): self.prepare()
        self.assertFalse(self.storage.path('build-inputs').exists())

    def test_wrong_binding_never_contacts_drive(self):
        self.bundle(); self.bindings['simulation']['lockDigest']='0'*64
        with self.assertRaisesRegex(core.LabError,'binding'): self.prepare()
        self.client.metadata.assert_not_called()

    def test_insufficient_space_has_no_extraction(self):
        self.bundle()
        with patch('reproduction.core.shutil.disk_usage') as disk:
            disk.return_value.free=90*core.GIB
            with self.assertRaisesRegex(core.LabError,'space'): self.prepare()
        self.assertFalse(self.storage.path('build-inputs').exists())

    def test_interrupted_extraction_is_preserved_not_retried(self):
        self.bundle()
        output=self.storage.path('build-inputs/'+core.digest(b.combined(self.lock,self.simulation)))
        partial=output.with_suffix('.partial'); partial.mkdir(parents=True)
        evidence=partial/'keep'; evidence.write_text('incomplete')
        with self.assertRaisesRegex(core.LabError,'Incomplete'): self.prepare()
        self.assertEqual(evidence.read_text(),'incomplete')

    def test_consumer_failure_does_not_promote(self):
        self.bundle()
        with patch('reproduction.build_inputs.consumers',side_effect=core.LabError('pin mismatch')):
            with self.assertRaisesRegex(core.LabError,'pin mismatch'): self.prepare()
        root=self.storage.path('build-inputs/'+core.digest(b.combined(self.lock,self.simulation)))
        self.assertFalse(root.exists()); self.assertTrue(root.with_suffix('.partial').exists())

    def test_public_cli_plan_uses_lock_and_no_host_access(self):
        self.bundle()
        with patch('reproduction.build_inputs.sim.read_lock',return_value=self.simulation), \
             patch('reproduction.build_inputs.Storage',side_effect=AssertionError), \
             redirect_stdout(io.StringIO()) as stream:
            self.assertEqual(cli.main(['inputs','plan','--lock',str(self.lockfile)]),0)
        self.assertIn('BUILD_INPUT_PLAN',stream.getvalue())


if __name__=='__main__': unittest.main()
