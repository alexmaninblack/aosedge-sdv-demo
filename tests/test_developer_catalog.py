# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Catalog discovery/compatibility proofs, with no real network or credentials."""
import copy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import runpy
import unittest
from unittest import mock
import urllib.parse
import urllib.error

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('developer_catalog', ROOT/'scripts/developer_catalog.py')
catalog = importlib.util.module_from_spec(spec)
spec.loader.exec_module(catalog)


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='sdv-catalog-test-', dir='/private/tmp' if sys.platform == 'darwin' else None)
        self.addCleanup(self.tmp.cleanup)
        self.state = Path(self.tmp.name)
        self.record = {'id': catalog.PIN['releaseId'], 'productVersion': '1.2.0-rc.1',
                       'sourceFiles': catalog.PIN['sourceFiles'], 'dependencyGroups': {}}
        self.metadata = {}
        for group, roles in catalog.ROLES.items():
            folder = 'fixture_folder_' + group
            files = {role: 'fixture_file_' + role for role in roles}
            packages = {role: {'file': role+'.tar.gz', 'bytes': 10, 'sha256': 'a'*64} for role in roles}
            self.record['dependencyGroups'][group] = {
                'binding': {'schemaVersion': 1, 'lockDigest': catalog.PIN['lockDigests'][group],
                            'folderId': folder, 'files': files}, 'packages': packages}
            self.metadata[folder] = {'id': folder, 'mimeType': 'application/vnd.google-apps.folder', 'trashed': False}
            for role, ident in files.items():
                self.metadata[ident] = {'id': ident, 'name': packages[role]['file'], 'size': '10',
                    'sha256Checksum': 'a'*64, 'trashed': False, 'parents': [folder], 'capabilities': {'canDownload': True}}
        self.pin_patch = mock.patch.dict(catalog.PIN, {'recordSha256': catalog.digest(self.record)})
        self.pin_patch.start()
        self.addCleanup(self.pin_patch.stop)
        self.value = {'schemaVersion': 1, 'product': 'aosedge-sdv-lab', 'catalogRevision': 1, 'releases': [self.record]}
        self.requests = []

    def folder_row(self):
        return {'id': 'fixture_catalog_folder', 'name': catalog.FOLDER, 'mimeType': 'application/vnd.google-apps.folder', 'trashed': False}

    def index_row(self):
        raw = catalog.canonical(self.value)
        return {'id': 'fixture_catalog_file', 'name': catalog.NAME, 'mimeType': 'application/json',
                'size': str(len(raw)), 'sha256Checksum': hashlib.sha256(raw).hexdigest(), 'version': '1',
                'parents': ['fixture_catalog_folder'], 'trashed': False, 'capabilities': {'canDownload': True}}

    def response(self, relative):
        if relative.startswith('about?'):
            return catalog.canonical({'user': {'emailAddress': 'reader@example.invalid'}})
        if relative.startswith('files?'):
            query = urllib.parse.parse_qs(urllib.parse.urlsplit(relative).query)['q'][0]
            row = self.folder_row() if "name = '"+catalog.FOLDER+"'" in query else self.index_row()
            return catalog.canonical({'files': [row]})
        path, _, query = relative.partition('?')
        ident = path.split('/')[1]
        if 'alt=media' in query:
            self.assertEqual(ident, 'fixture_catalog_file', 'must never fetch an archive')
            return catalog.canonical(self.value)
        return catalog.canonical(self.index_row() if ident == 'fixture_catalog_file' else self.metadata[ident])

    def client(self, transform=None):
        owner = self
        class Response:
            def __init__(self, raw): self.raw = raw
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, size): return self.raw[:size]
        class Opener:
            def open(self, request, timeout):
                owner.assertEqual(request.get_method(), 'GET')
                owner.assertEqual(request.headers['Authorization'], 'Bearer SECRET_FIXTURE_TOKEN')
                relative = request.full_url.split('/drive/v3/')[1]
                owner.requests.append(relative)
                raw = owner.response(relative)
                if transform: raw = transform(relative, raw)
                return Response(raw)
        run = mock.patch.object(catalog.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, 'SECRET_FIXTURE_TOKEN', ''))
        opener = mock.patch.object(catalog.urllib.request, 'build_opener', return_value=Opener())
        run.start(); opener.start()
        self.addCleanup(run.stop); self.addCleanup(opener.stop)
        return catalog.Client('/fake/gcloud', 'reader@example.invalid')

    def args(self, mode='remote'):
        target = self.state/'catalog'/catalog.PIN['recordSha256']/'automatic'
        return ['/fake/gcloud', 'reader@example.invalid', str(target/'developer-inputs.drive.json'),
                str(target/'simulation-inputs.drive.json'), mode, str(self.state), 'no']

    def test_discover_first_repeat_local_and_metadata_only(self):
        self.client()
        for _ in range(2):
            with mock.patch('sys.stdout', new_callable=io.StringIO) as output:
                self.assertEqual(catalog.main(self.args()), 0)
                self.assertNotIn('SECRET', output.getvalue())
        target = self.state/'catalog'/catalog.PIN['recordSha256']/'automatic'
        self.assertEqual(len(list(target.iterdir())), 4)
        self.assertTrue(all(p.stat().st_mode & 0o777 == 0o600 for p in target.iterdir()))
        self.assertEqual(sum('alt=media' in r for r in self.requests), 2)
        stamp = (target/'release.json').stat().st_mtime_ns
        with mock.patch.object(catalog, 'Client', side_effect=AssertionError('no network')):
            self.assertEqual(catalog.main(self.args('local')), 0)
        self.assertEqual(stamp, (target/'release.json').stat().st_mtime_ns)
        self.assertFalse(list(target.parent.glob('.pending-*')))

    def test_selects_compatible_entry_not_newest_and_ignores_filename_versions(self):
        self.value['releases'].insert(0, {'id': '99.0.0-other', 'productVersion': '99.0.0'})
        self.value['catalogRevision'] = 200
        self.assertEqual(catalog.select_record(self.value), self.record)
        self.assertEqual(catalog.NAME, 'release-index.json')

    def test_missing_duplicate_unsupported_and_tampered_records(self):
        cases = []
        for value in (2, True):
            c = copy.deepcopy(self.value); c['schemaVersion'] = value; cases.append(c)
        c = copy.deepcopy(self.value); c['releases'].append(c['releases'][0]); cases.append(c)
        c = copy.deepcopy(self.value); c['releases'] = [{'id': 'newer-only'}]; cases.append(c)
        c = copy.deepcopy(self.value); c['releases'][0]['productVersion'] = '9.9.9'; cases.append(c)
        for c in cases:
            with self.subTest(c=c), self.assertRaises(catalog.CatalogError): catalog.select_record(c)

    def test_duplicate_json_keys_rejected(self):
        with self.assertRaises(catalog.CatalogError): catalog.json_bytes(b'{"schemaVersion":1,"schemaVersion":1}')

    def test_missing_ambiguous_or_incomplete_discovery_is_not_first_match(self):
        for mutation in ({'files': []}, {'files': [self.folder_row(), self.folder_row()]},
                         {'files': [self.folder_row()], 'nextPageToken': 'remaining'},
                         {'files': [self.folder_row()], 'incompleteSearch': True}):
            c = self.client(lambda r, raw: catalog.canonical(mutation) if r.startswith('files?') else raw)
            with self.assertRaises(catalog.CatalogError): c.discover()

    def test_bad_transfer_or_changed_remote_catalog_not_saved(self):
        for change in ('checksum', 'version'):
            def transform(r, raw):
                if change == 'checksum' and 'alt=media' in r: return raw + b' '
                if change == 'version' and r.startswith('files/fixture_catalog_file?') and 'alt=media' not in r:
                    row = json.loads(raw); row['version'] = '2'; return catalog.canonical(row)
                return raw
            c = self.client(transform)
            with self.assertRaises(catalog.CatalogError): c.discover()
        self.assertFalse((self.state/'catalog').exists())

    def test_unavailable_or_changed_input_prevents_state_promotion(self):
        self.client()
        for field, value in (('sha256Checksum', 'b'*64), ('size', '11'), ('capabilities', {'canDownload': False})):
            row = self.metadata['fixture_file_carla-runtime']
            old = row[field]; row[field] = value
            with self.assertRaises(catalog.CatalogError): catalog.main(self.args())
            row[field] = old
            self.assertFalse((self.state/'catalog').exists())

    def test_local_modification_preserved_and_symlink_rejected(self):
        catalog.save_generation(self.state, self.record)
        target = self.state/'catalog'/catalog.PIN['recordSha256']/'automatic'
        path = target/'release.json'
        path.write_text('{}')
        with self.assertRaises(catalog.CatalogError): catalog.save_generation(self.state, self.record)
        self.assertEqual(path.read_text(), '{}')
        path.unlink(); path.symlink_to(target/'source-requirements.json')
        with self.assertRaises(catalog.CatalogError): catalog.read_local(path)

    def test_atomic_failure_cleans_only_owned_pending_generation(self):
        real_open = catalog.os.open
        def fail(path, *a, **kw):
            if str(path).endswith('release.json'): raise OSError('fixture write failure')
            return real_open(path, *a, **kw)
        with mock.patch.object(catalog.os, 'open', side_effect=fail), self.assertRaises(OSError):
            catalog.save_generation(self.state, self.record)
        parent = self.state/'catalog'/catalog.PIN['recordSha256']
        self.assertEqual(list(parent.iterdir()), [])
        catalog.save_generation(self.state, self.record)

    def test_source_drift_fails_before_build_or_download(self):
        file = self.state/'source.json'; file.write_text('{}')
        pin = {'sourceFiles': {'source.json': hashlib.sha256(file.read_bytes()).hexdigest()}}
        with mock.patch.dict(catalog.PIN, pin):
            receipt = self.state/'receipt.json'; receipt.write_bytes(catalog.canonical(catalog.PIN))
            catalog.source_check(receipt, self.state)
            file.write_text('{"changed":true}')
            with self.assertRaises(catalog.CatalogError): catalog.source_check(receipt, self.state)


class CatalogSourceTests(unittest.TestCase):
    def test_source_projection_and_embedded_helper_are_current(self):
        for name, sha in catalog.PIN['sourceFiles'].items():
            self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(), sha)
        for group, name in (('buildInputs', 'developer-factory41-r1'), ('simulation', 'carla-macos-arm64-r1')):
            lock = json.loads((ROOT/'workspace/dependencies'/f'{name}.lock.json').read_text())
            self.assertEqual(catalog.digest(lock), catalog.PIN['lockDigests'][group])
        result = subprocess.run([sys.executable, '-B', str(ROOT/'scripts/sync-preparation-catalog'), '--check'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('SDV_CATALOG_RECORD='+catalog.PIN['recordSha256'], (ROOT/'scripts/prepare-macos.sh').read_text())

    def test_catalog_append_repeat_preserves_history_and_refuses_mutation(self):
        owner = runpy.run_path(str(ROOT/'scripts/preparation-catalog'))
        create = owner['create']
        old = {'buildPlan': 'workspace/releases/1.2.0-rc.1-source-factory-build-chain.json',
               'descriptorPath': 'workspace/releases/1.2.0-rc.1-source-factory-delivery.json',
               'productVersion': '1.2.0-rc.1', 'dependencyGroups': {}}
        old['descriptorCanonicalJsonSha256'] = catalog.digest(json.loads((ROOT/old['descriptorPath']).read_text()))
        for group, name in (('buildInputs', 'developer-factory41-r1'), ('simulation', 'carla-macos-arm64-r1')):
            path = 'workspace/dependencies/'+name+'.lock.json'
            lock = json.loads((ROOT/path).read_text())
            files = {role: 'fixture_object_'+role for role in lock['packages']}
            old['dependencyGroups'][group] = {'lockPath': path,
                'lockSha256': hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),
                'binding': {'schemaVersion': 1, 'lockDigest': catalog.digest(lock), 'folderId': 'fixture_folder_'+group, 'files': files},
                'objects': {role: {'id': files[role], **{k: row[k] for k in ('file', 'bytes', 'sha256')}} for role, row in lock['packages'].items()}}
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve(); receipt = root/'receipt.json'; receipt.write_text(json.dumps(old))
            previous = root/'previous.json'
            historical = {'id': 'older-release', 'productVersion': '0.1.0', 'note': 'must stay unchanged'}
            previous.write_text(json.dumps({'schemaVersion': 1, 'product': 'aosedge-sdv-lab', 'catalogRevision': 1, 'releases': [historical]}))
            first = root/'first.json'; create(receipt, first, previous)
            value = json.loads(first.read_text())
            self.assertEqual(value['catalogRevision'], 2)
            self.assertEqual(value['releases'][0], historical)
            second = root/'second.json'; create(receipt, second, first)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertEqual(first.stat().st_mode & 0o777, 0o600)
            old['extraHistoricalEvidence'] = 'changed'; receipt.write_text(json.dumps(old))
            with self.assertRaises(owner['LabError']): create(receipt, root/'rejected.json', first)
            self.assertFalse((root/'rejected.json').exists())
            with self.assertRaises(owner['LabError']): create(receipt, ROOT/'private-catalog-must-not-appear.json')
            self.assertFalse((ROOT/'private-catalog-must-not-appear.json').exists())


if __name__ == '__main__': unittest.main()
