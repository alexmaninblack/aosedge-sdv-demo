# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import gzip
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts/distribution'
with patch.object(sys, 'path', [str(SCRIPTS), *sys.path]):
    SPEC = importlib.util.spec_from_file_location('backend_archive', SCRIPTS / 'backend_archive.py')
    module = importlib.util.module_from_spec(SPEC)
    SPEC.loader.exec_module(module)


class BackendArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.path = Path(self.temporary.name) / 'backends.tar'
        self.files, self.pins, self.rows, self.roots = {}, [], [], []

    def blob(self, value, kind):
        raw = value if isinstance(value, bytes) else json.dumps(value).encode()
        digest = hashlib.sha256(raw).hexdigest()
        self.files['blobs/sha256/' + digest] = raw
        return {'mediaType': kind, 'digest': 'sha256:' + digest, 'size': len(raw)}

    def fixture(self, *, arch='arm64', source='a' * 40, diff=None, layers=None):
        for team in ('brake', 'tire'):
            raw = b'fixture layer bytes'
            layer = self.blob(gzip.compress(raw), module.LAYER)
            config = self.blob({'os': 'linux', 'architecture': arch, 'config': {'User': 'node', 'Labels': {
                'org.opencontainers.image.revision': source, 'tech.aosedge.demo.team': team}},
                'rootfs': {'type': 'layers', 'diff_ids': [diff or 'sha256:' + hashlib.sha256(raw).hexdigest()]}}, module.CONFIG)
            manifest = self.blob({'schemaVersion': 2, 'mediaType': module.MANIFEST, 'config': config,
                                  'layers': layers if layers is not None else [layer]}, module.MANIFEST)
            manifest['platform'] = {'os': 'linux', 'architecture': arch}
            empty = self.blob({}, module.EMPTY)
            empty['data'] = 'e30='
            attestation = self.blob({'schemaVersion': 2, 'mediaType': module.MANIFEST, 'config': empty,
                'layers': [self.blob({'fixture': team}, module.ATTESTATION)]}, module.MANIFEST)
            attestation['platform'] = {'os': 'unknown', 'architecture': 'unknown'}
            root = self.blob({'schemaVersion': 2, 'mediaType': module.INDEX, 'manifests': [manifest, attestation]}, module.INDEX)
            self.roots.append(root)
            self.pins.append({'team': team, 'localImageId': root['digest'], 'source': 'a' * 40})
            self.rows.append({'Config': 'blobs/sha256/' + config['digest'][7:], 'RepoTags': None,
                              'Layers': ['blobs/sha256/' + layer['digest'][7:]]})
        self.files['oci-layout'] = json.dumps({'imageLayoutVersion': '1.0.0'}).encode()
        self.files['index.json'] = json.dumps({'schemaVersion': 2, 'mediaType': module.INDEX, 'manifests': self.roots}).encode()
        self.files['manifest.json'] = json.dumps(self.rows).encode()

    def save(self, extra=None):
        with tarfile.open(self.path, 'w') as archive:
            for name, raw in self.files.items():
                entry = tarfile.TarInfo(name)
                entry.size = len(raw)
                archive.addfile(entry, io.BytesIO(raw))
            if extra:
                archive.addfile(extra)

    def verify(self):
        return module.verify(self.path, self.pins)

    def test_valid_index_identity_is_not_config_identity(self):
        self.fixture()
        self.save()
        result = self.verify()
        self.assertEqual(result['uniqueRuntimeLayers'], 1)
        self.assertEqual([r['team'] for r in result['images']], ['brake', 'tire'])
        self.assertEqual(result, self.verify())
        self.assertFalse(result['externalDistributionApproved'])

    def test_corrupt_blob(self):
        self.fixture()
        self.files[next(iter(self.files))] += b'changed'
        self.save()
        with self.assertRaisesRegex(module.BundleError, 'digest'):
            self.verify()

    def test_missing_reference(self):
        self.fixture()
        del self.files[next(iter(self.files))]
        self.save()
        with self.assertRaisesRegex(module.BundleError, 'reference'):
            self.verify()

    def test_unreferenced_blob(self):
        self.fixture()
        self.blob(b'unrelated', module.CONFIG)
        self.save()
        with self.assertRaisesRegex(module.BundleError, 'Unreferenced'):
            self.verify()

    def test_wrong_image_identity(self):
        self.fixture()
        self.pins[0]['localImageId'] = 'sha256:' + '0' * 64
        self.save()
        with self.assertRaisesRegex(module.BundleError, 'identity set'):
            self.verify()

    def test_wrong_architecture(self):
        self.fixture(arch='amd64')
        self.save()
        with self.assertRaisesRegex(module.BundleError, 'arm64'):
            self.verify()

    def test_wrong_source_revision(self):
        self.fixture(source='b' * 40)
        self.save()
        with self.assertRaisesRegex(module.BundleError, 'source identity'):
            self.verify()

    def test_wrong_expanded_digest(self):
        self.fixture(diff='sha256:' + '0' * 64)
        self.save()
        with self.assertRaisesRegex(module.BundleError, 'Expanded layer'):
            self.verify()

    def test_mutable_tags(self):
        self.fixture()
        self.rows[0]['RepoTags'] = ['backend:latest']
        self.files['manifest.json'] = json.dumps(self.rows).encode()
        self.save()
        with self.assertRaisesRegex(module.BundleError, 'mutable tags'):
            self.verify()

    def test_docker_compatibility_mismatch(self):
        self.fixture()
        self.rows[0]['Layers'] = []
        self.files['manifest.json'] = json.dumps(self.rows).encode()
        self.save()
        with self.assertRaisesRegex(module.BundleError, 'disagree'):
            self.verify()

    def test_outer_links_and_escaping_paths_rejected(self):
        self.fixture()
        for name, kind in (('../escape', tarfile.REGTYPE), ('unexpected', tarfile.REGTYPE),
                           ('blobs/sha256/' + '0' * 64, tarfile.SYMTYPE)):
            entry = tarfile.TarInfo(name)
            entry.type = kind
            entry.linkname = '/outside'
            self.save(entry)
            with self.subTest(name=name), self.assertRaisesRegex(module.BundleError, 'Unexpected archive member'):
                self.verify()

    def test_duplicate_outer_member(self):
        self.fixture()
        self.save(tarfile.TarInfo('index.json'))
        with self.assertRaisesRegex(module.BundleError, 'Duplicate'):
            self.verify()

    def test_size_and_expansion_budgets(self):
        self.fixture()
        self.save()
        for constant in ('MAX_ARCHIVE', 'MAX_EXPANDED'):
            with self.subTest(constant=constant), patch.object(module, constant, 1), self.assertRaises(module.BundleError):
                self.verify()

    def test_archive_symlink(self):
        self.fixture()
        self.save()
        link = self.path.with_suffix('.link')
        link.symlink_to(self.path)
        with self.assertRaises(module.BundleError):
            module.verify(link, self.pins)


if __name__ == '__main__':
    unittest.main()
