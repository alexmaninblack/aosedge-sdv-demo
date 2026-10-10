# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import tarfile
import unittest
from unittest.mock import Mock, patch

from test_reproduction import StorageFixture
from reproduction import artifacts, core, dependencies as d, delivery


class DependencyTests(StorageFixture, unittest.TestCase):
    def test_reviewed_lock_and_wrong_ancestry(self):
        value = d.read_lock(d.LOCK, self.release)
        self.assertEqual(set(value['packages']), set(d.ROLES))
        target = self.base/'altered-lock.json'
        for field, replacement in (('hostManifestSha256', '0'*64),
                ('sdkManifestSha256', '0'*64), ('id', 'latest'), ('status', 'QUALIFIED')):
            core.atomic_json(target, {**value, field: replacement})
            with self.assertRaises(core.LabError):
                d.read_lock(target, self.release)

    def test_lock_cannot_override_package_format_or_size(self):
        value = d.read_lock(d.LOCK, self.release)
        target = self.base/'altered-lock.json'
        for field, replacement in (('file', '../escape.tar.gz'), ('bytes', -1), ('files', 50000), ('extra', 'x')):
            bad = copy.deepcopy(value)
            bad['packages']['carla-runtime'][field] = replacement
            core.atomic_json(target, bad)
            with self.assertRaises(core.LabError):
                d.read_lock(target, self.release)

    def fixture(self, role='carla-runtime'):
        self.role = role
        source = self.base/'original'
        source.write_bytes(b'fixture bytes')
        source.chmod(0o755)
        self.name = d.HOST+'simulator/fixture' if role == 'carla-runtime' else 'gateway-sdk/fixture'
        self.row = {'path': self.name, 'bytes': 13, 'sha256': artifacts.sha256(source), 'mode': 0o755}
        self.members = [(self.row, source)]
        self.expected = d.pack(self.storage, role, self.members, lambda *a: None)
        self.archive = self.storage.path('exports/'+self.expected['file'])
        self.output = self.storage.path('output')
        self.output.mkdir()

    def extract(self):
        return d.unpack(self.storage, self.archive, self.role, self.expected, self.output, lambda *a: None)

    def test_roundtrip_modes_bytes_and_repeat_archive(self):
        self.fixture()
        before = artifacts.identity(self.archive)
        self.assertEqual(self.expected, d.pack(self.storage, self.role, self.members, lambda *a: None))
        self.assertEqual(before, artifacts.identity(self.archive))
        stamps = self.extract()
        target = self.output/self.name
        self.assertEqual(target.read_bytes(), b'fixture bytes')
        self.assertEqual(target.stat().st_mode & 0o777, 0o755)
        self.assertEqual(stamps[self.name], artifacts.identity(target))

    def test_source_corruption_rejected(self):
        self.fixture()
        self.archive.unlink()
        self.members[0][1].write_bytes(b'broken bytes!')
        with self.assertRaisesRegex(core.LabError, 'digest'):
            d.pack(self.storage, self.role, self.members, lambda *a: None)
        self.assertFalse(self.archive.exists())

    def test_archive_changed_not_reused(self):
        self.fixture()
        self.archive.write_bytes(b'changed')
        with self.assertRaisesRegex(core.LabError, 'changed'):
            d.pack(self.storage, self.role, self.members, lambda *a: None)

    def test_no_overwrite(self):
        self.fixture(); self.extract()
        with self.assertRaisesRegex(core.LabError, 'collision'):
            self.extract()
        self.assertEqual((self.output/self.name).read_bytes(), b'fixture bytes')

    def test_unsafe_paths_and_roles(self):
        for path in ('/escape', '../escape', 'a/../b', 'a//b', './b', 'a\\b', 'a/./b'):
            with self.assertRaises(core.LabError):
                d.safe_name(path)
        for role, path in [('carla-runtime', 'gateway-sdk/a'), ('host-support', d.HOST+'simulator/a')]:
            with self.assertRaises(core.LabError):
                d.allowed(role, path)

    def test_duplicate_and_privileged_mode_rejected(self):
        self.fixture()
        for rows in ([self.row, self.row], [{**self.row, 'mode': 0o4755}]):
            with self.assertRaises(core.LabError):
                d.rows_valid(self.role, rows)

    def rewrite_archive(self, transform):
        with tarfile.open(self.archive, 'r:gz') as src:
            content = [(member, src.extractfile(member).read()) for member in src]
        content = transform(content)
        with tarfile.open(self.archive, 'w:gz') as dst:
            for member, data in content:
                dst.addfile(member, io.BytesIO(data))
        self.expected['bytes'] = self.archive.stat().st_size

    def test_link_and_extra_member_rejected(self):
        self.fixture()
        def linked(content):
            content[1][0].type = tarfile.SYMTYPE
            content[1][0].linkname = '/tmp/escape'
            content[1][0].size = 0
            return content
        self.rewrite_archive(linked)
        with self.assertRaisesRegex(core.LabError, 'Unsafe'):
            self.extract()

    def test_extra_member_rejected(self):
        self.fixture()
        self.rewrite_archive(lambda content: content+[content[1]])
        with self.assertRaisesRegex(core.LabError, 'extra'):
            self.extract()

    def test_payload_hash_and_manifest_hash_rejected(self):
        self.fixture()
        self.rewrite_archive(lambda content: [content[0], (content[1][0], b'broken bytes!')])
        with self.assertRaisesRegex(core.LabError, 'digest'):
            self.extract()
        self.expected['manifestSha256'] = '0'*64
        with self.assertRaisesRegex(core.LabError, 'manifest digest'):
            self.extract()

    def test_destination_symlink_rejected(self):
        self.fixture()
        (self.output/'kit-inputs').symlink_to(self.base, target_is_directory=True)
        with self.assertRaisesRegex(core.LabError, 'Symlink'):
            self.extract()

    def test_binding_mismatch_never_requests_network(self):
        client = Mock()
        with self.assertRaises(core.LabError):
            d.prepare(self.storage, {}, {}, client, lambda *a: None)
        client.metadata.assert_not_called()

    def test_missing_extraction_receipt_not_adopted(self):
        lock = {'packages': {'x': {'files': 1}}}
        output = self.storage.path('dependencies/'+core.digest(lock))
        output.mkdir(parents=True)
        with self.assertRaises((core.LabError, OSError)):
            d.verify(self.storage, lock)

    def bundle(self):
        rows = {
            'carla-runtime': d.HOST+'simulator/fixture',
            'host-support': d.HOST+'host-runtime-manifest.json',
            'gateway-sdk': 'gateway-sdk/sdk-manifest.json'}
        packages = {}
        for role, name in rows.items():
            source = self.base/(role+'.json')
            source.write_bytes(b'{}')
            source.chmod(0o600)
            row = {'path': name, 'bytes': 2, 'sha256': artifacts.sha256(source), 'mode': 0o600}
            packages[role] = d.pack(self.storage, role, [(row, source)], lambda *a: None)
            original = self.storage.path('exports/'+packages[role]['file'])
            cached = self.storage.path('cache/sha256/'+packages[role]['sha256'])
            cached.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(original, cached)
        self.lock = {'packages': packages, 'hostManifestSha256': row['sha256'], 'sdkManifestSha256': row['sha256']}
        self.binding = {'schemaVersion': 1, 'lockDigest': core.digest(self.lock),
                        'folderId': 'folder_0123456789', 'files': {r: 'file_0123456789_'+r for r in d.ROLES}}
        self.client = Mock()
        self.client.metadata.side_effect = AssertionError('No network from complete cache')

    def test_prepare_complete_cache_and_repeat_are_offline(self):
        self.bundle()
        before = self.storage.state_path.read_bytes()
        result = d.prepare(self.storage, self.lock, self.binding, self.client, lambda *a: None)
        self.assertEqual(result, d.prepare(self.storage, self.lock, self.binding, self.client, lambda *a: None))
        self.client.metadata.assert_not_called()
        self.client.content.assert_not_called()
        self.assertEqual(self.storage.state_path.read_bytes(), before)
        target = Path(result['kitInputs'])/'demo-artifacts/aosedge-sdv-demo/host-runtime/simulator/fixture'
        target.write_bytes(b'!!')
        with self.assertRaisesRegex(core.LabError, 'changed'):
            d.prepare(self.storage, self.lock, self.binding, self.client, lambda *a: None)
        self.assertEqual(target.read_bytes(), b'!!')

    def test_public_selection_reuses_cache_without_authenticated_client(self):
        self.bundle()
        value={'schemaVersion':2,'transport':'google-drive-public','lockDigest':core.digest(self.lock),
               'files':{r:'https://drive.google.com/uc?export=download&id=public_fixture_'+r for r in d.ROLES}}
        with patch('public_drive.Client',side_effect=AssertionError('cached acquisition stays offline')):
            first=d.prepare(self.storage,self.lock,value,None,lambda *a:None)
            self.assertEqual(first,d.prepare(self.storage,self.lock,value,None,lambda *a:None))

    def test_corrupt_cached_archive_not_extracted(self):
        self.bundle()
        row = self.lock['packages']['carla-runtime']
        self.storage.path('cache/sha256/'+row['sha256']).write_bytes(b'x'*row['bytes'])
        with self.assertRaisesRegex(core.LabError, 'digest'):
            d.prepare(self.storage, self.lock, self.binding, self.client, lambda *a: None)
        self.assertFalse(self.storage.path('dependencies').exists())

    def test_partial_extraction_preserved_not_adopted(self):
        self.bundle()
        partial = self.storage.path('dependencies/'+core.digest(self.lock)+'.partial')
        partial.mkdir(parents=True)
        (partial/'keep').write_text('evidence')
        with self.assertRaisesRegex(core.LabError, 'Incomplete extraction'):
            d.prepare(self.storage, self.lock, self.binding, self.client, lambda *a: None)
        self.assertEqual((partial/'keep').read_text(), 'evidence')

    def test_binding_cannot_supply_new_expected_digests(self):
        self.bundle()
        for altered in ({**self.binding, 'lockDigest': '0'*64}, {**self.binding, 'sha256': '0'*64}):
            with self.assertRaises(core.LabError):
                d.prepare(self.storage, self.lock, altered, self.client, lambda *a: None)
        self.client.metadata.assert_not_called()


if __name__ == '__main__':
    unittest.main()
