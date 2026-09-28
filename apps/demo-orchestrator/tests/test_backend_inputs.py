# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Portable image metadata; no real engine, load, container or user data."""

import hashlib
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from aosedge_demo_orchestrator import backend_inputs as portable
from aosedge_demo_orchestrator.backends import BackendService
from aosedge_demo_orchestrator.environment import EnvironmentError, EnvironmentService


class BackendInputTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='backend inputs ')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.env = EnvironmentService(self.root, catalog=SimpleNamespace(project=self.root / 'catalog'))
        self.bundle = self.env.catalog.project / 'backend-inputs'
        self.bundle.mkdir(parents=True)
        self.lock = self.root / portable.LOCK
        self.lock.parent.mkdir(parents=True)
        (self.bundle / 'backends.tar').write_bytes(b'not an OCI archive: selection fixture')
        self.service = BackendService(self.env)
        self.seal()

    def seal(self, change=None):
        archive = (self.bundle / 'backends.tar').read_bytes()
        value = dict(schemaVersion=1, status='OFFLINE_INTEGRITY_VERIFIED_NOT_CLEAN_ENGINE_QUALIFIED',
            operatorDataIncluded=False, archiveBytes=len(archive), archiveSha256=hashlib.sha256(archive).hexdigest(),
            images=[dict(team=t, imageId='sha256:'+h*64, source=h*40, architecture='linux/arm64')
                    for t,h in [('brake','a'), ('tire','b')]])
        if change:
            change(value)
        raw = json.dumps(value).encode()
        (self.bundle / portable.MANIFEST).write_bytes(raw)
        self.lock.write_text(json.dumps(dict(schemaVersion=1, contractId=portable.CONTRACT,
            manifest=dict(path=portable.MANIFEST, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()),
            protocols=dict(brake=dict(mockCleanupProtocol='isolated-mock-v1'),
                tire=dict(mockCleanupProtocol='isolated-mock-v1', privateCleanupProtocol='tire-product-v1')))))

    def test_selected_candidates_do_not_build_load_or_read_archive(self):
        with patch.object(self.service, '_docker') as docker, patch.object(self.service, 'build') as build, \
                patch.object(portable.BackendInputs, 'archive', side_effect=AssertionError('not a selection read')):
            for team in ('brake', 'tire'):
                item = self.service._candidate(team)
                self.assertEqual(team, item['team'])
                self.assertEqual('isolated-mock-v1', item['mockCleanupProtocol'])
        docker.assert_not_called(); build.assert_not_called()

    def test_absence_preserves_legacy_catalogue(self):
        self.bundle.rename(self.bundle.with_name('not-selected'))
        self.assertIsNone(portable.selected(self.env))
        with self.assertRaisesRegex(EnvironmentError, 'BACKEND_BUILD_REQUIRED'):
            self.service._candidate('brake')
        directory = self.service.catalog / 'brake' / ('c'*40)
        directory.mkdir(parents=True)
        row = dict(schemaVersion=1, team='brake', imageId='sha256:'+'c'*64, builtAt='fixture')
        (directory / 'manifest.json').write_text(json.dumps(row))
        self.assertEqual(row, self.service._candidate('brake'))

    def test_existing_run_keeps_record_and_does_not_require_successor(self):
        (self.bundle / portable.MANIFEST).write_text('invalid')
        record = dict(imageId='sha256:'+'e'*64, sourceRevision='e'*40, mockCleanupProtocol='isolated-mock-v1')
        self.assertEqual(record, self.service._runtime_candidate({'backends': {'brake': record}}, 'brake'))
        with self.assertRaises(EnvironmentError):
            self.service._runtime_candidate({}, 'brake')

    def test_archive_verification_checks_same_size_modification_after_cache(self):
        bundle = portable.selected(self.env)
        archive = bundle.archive()
        self.assertEqual(archive, bundle.archive())
        raw = archive.read_bytes()
        archive.write_bytes(b'X' + raw[1:])
        with self.assertRaisesRegex(EnvironmentError, 'ARCHIVE_CHANGED'):
            bundle.archive()

    def test_changed_manifest_is_not_self_authenticating(self):
        path = self.bundle / portable.MANIFEST
        path.write_bytes(path.read_bytes().replace(b'"brake"', b'"break"'))
        with self.assertRaisesRegex(EnvironmentError, 'MANIFEST_CHANGED'):
            portable.selected(self.env)

    def test_links_extras_and_bad_mode_block(self):
        extra = self.bundle / 'extra'
        extra.mkdir()
        with self.assertRaisesRegex(EnvironmentError, 'UNDECLARED_FILE'):
            portable.selected(self.env)
        extra.rmdir()
        archive = self.bundle / 'backends.tar'
        archive.chmod(0o666)
        with self.assertRaisesRegex(EnvironmentError, 'FILE_CHANGED'):
            portable.selected(self.env)
        archive.unlink()
        archive.symlink_to(self.lock)
        with self.assertRaises(EnvironmentError):
            portable.selected(self.env)

    def test_missing_archive_does_not_select_developer_build(self):
        (self.bundle / 'backends.tar').unlink()
        with patch.object(self.service, 'build') as build, self.assertRaises(EnvironmentError):
            self.service._candidate('brake')
        build.assert_not_called()

    def test_duplicate_platform_size_and_protocol_fail_closed(self):
        for change in (lambda v: v['images'].__setitem__(1, v['images'][0]),
                       lambda v: v['images'][0].update(architecture='linux/amd64'),
                       lambda v: v.update(archiveBytes=2**30),
                       lambda v: v.update(operatorDataIncluded=True)):
            self.seal(change)
            with self.assertRaises(EnvironmentError):
                portable.selected(self.env)
        self.seal()
        value = json.loads(self.lock.read_text())
        value['protocols']['brake']['privateCleanupProtocol'] = 'invented'
        self.lock.write_text(json.dumps(value))
        with self.assertRaisesRegex(EnvironmentError, 'PROTOCOL_INVALID'):
            portable.selected(self.env)

    def test_selected_image_still_requires_engine_inspection_not_auto_import(self):
        candidate = self.service._candidate('brake')
        with patch.object(self.service, '_docker', side_effect=EnvironmentError('BACKEND_DOCKER_ENGINE_UNAVAILABLE')) as docker:
            with self.assertRaisesRegex(EnvironmentError, 'ENGINE_UNAVAILABLE'):
                self.service._image(candidate['imageId'])
        docker.assert_called_once_with('image', 'inspect', candidate['imageId'])


if __name__ == '__main__':
    unittest.main()
