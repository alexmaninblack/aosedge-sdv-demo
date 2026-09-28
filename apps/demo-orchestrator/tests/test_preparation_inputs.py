# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Portable input selection must fail closed before Cloud/allocation."""

import hashlib
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from aosedge_demo_orchestrator.components import ComponentService
from aosedge_demo_orchestrator.environment import EnvironmentError, EnvironmentService
from aosedge_demo_orchestrator.preparation_inputs import LOCK, MANIFEST, PreparationInputs, selected
from aosedge_demo_orchestrator.releases import LEDGER
from aosedge_demo_orchestrator.service_build import ServiceBuilder
from aosedge_demo_orchestrator.service_packages import ServicePackages


def encoded(value):
    return json.dumps(value, sort_keys=True).encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


class InputTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.base = Path(temp.name)
        self.env = EnvironmentService(self.base / 'app', catalog=SimpleNamespace(project=self.base / 'catalog'))
        self.root = self.env.catalog.project / 'preparation-inputs'
        self.root.mkdir(parents=True)
        self.lock = self.env.root / LOCK
        self.lock.parent.mkdir(parents=True)
        self.put('payload.bin', b'bounded fixture')
        self.seal()

    def put(self, name, raw):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        path.chmod(0o644)

    def seal(self, transform=None):
        rows = [dict(path=p.relative_to(self.root).as_posix(), bytes=p.stat().st_size, sha256=sha(p.read_bytes()))
                for p in self.root.rglob('*') if p.is_file() and p.name != MANIFEST]
        value = dict(schemaVersion=1, status='ASSEMBLED_PREPARATION_INPUTS_NOT_UPLOAD_READY', files=rows)
        if transform:
            value = transform(value)
        raw = encoded(value)
        self.put(MANIFEST, raw)
        self.lock.write_bytes(encoded(dict(schemaVersion=1, contractId='aosedge-demo-portable-preparation-inputs',
            contractVersion='1.0.0', manifest=dict(path=MANIFEST, bytes=len(raw), sha256=sha(raw)))))

    def reader(self):
        return PreparationInputs(self.root, self.lock)

    def test_absent_selection_retains_development_path(self):
        self.root.rename(self.root.with_name('not-selected'))
        self.assertIsNone(selected(self.env))

    def test_reads_pinned_payload_without_mutation(self):
        before = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in self.root.rglob('*') if p.is_file()}
        self.assertEqual(b'bounded fixture', selected(self.env).read('payload.bin'))
        self.assertEqual(before, {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in before})

    def test_payload_digest_checked_on_use_not_large_inventory_scan(self):
        self.put('payload.bin', b'changed fixture')
        reader = self.reader()
        with self.assertRaisesRegex(EnvironmentError, 'DIGEST_MISMATCH'):
            reader.read('payload.bin')

    def test_manifest_not_self_authorizing(self):
        manifest = self.root / MANIFEST
        manifest.write_bytes(manifest.read_bytes().replace(b'payload.bin', b'unknown.bin'))
        with self.assertRaisesRegex(EnvironmentError, 'MANIFEST_DIGEST_MISMATCH'):
            self.reader()

    def test_missing_untrusted_and_wrong_shape_lock(self):
        for value in (None, [], {}, dict(schemaVersion=1, contractId='aosedge-demo-portable-preparation-inputs',
                                       contractVersion='1.0.0', manifest=[])):
            with self.subTest(value=value):
                if value is None:
                    self.lock.unlink()
                else:
                    self.lock.write_bytes(encoded(value))
                with self.assertRaises(EnvironmentError):
                    self.reader()

    def test_missing_file_and_changed_size(self):
        path = self.root / 'payload.bin'
        path.unlink()
        with self.assertRaises(EnvironmentError):
            self.reader()
        path.write_bytes(b'wrong size')
        with self.assertRaisesRegex(EnvironmentError, 'FILE_MISMATCH'):
            self.reader()

    def test_symlink_root_is_not_absent_fallback(self):
        self.root.rename(self.root.with_name('elsewhere'))
        self.root.symlink_to(self.root.with_name('elsewhere'), target_is_directory=True)
        with self.assertRaisesRegex(EnvironmentError, 'PATH_UNSAFE'):
            selected(self.env)
        self.root.unlink()
        self.root.symlink_to(self.root.with_name('missing'), target_is_directory=True)
        with self.assertRaisesRegex(EnvironmentError, 'PATH_UNSAFE'):
            selected(self.env)

    def test_symlink_and_hardlink_payload_rejected(self):
        path = self.root / 'payload.bin'
        other = self.base / 'elsewhere'
        path.rename(other)
        path.symlink_to(other)
        with self.assertRaisesRegex(EnvironmentError, 'PATH_UNSAFE'):
            self.reader()
        path.unlink()
        os.link(other, path)
        with self.assertRaisesRegex(EnvironmentError, 'FILE_MISMATCH'):
            self.reader()

    def test_linked_parent_rejected(self):
        self.put('nested/file', b'text')
        self.seal()
        (self.root / 'nested').rename(self.base / 'nested')
        (self.root / 'nested').symlink_to(self.base / 'nested', target_is_directory=True)
        with self.assertRaisesRegex(EnvironmentError, 'PATH_UNSAFE'):
            self.reader()

    def test_world_or_group_writable_payload_rejected(self):
        for mode in (0o646, 0o664):
            (self.root / 'payload.bin').chmod(mode)
            with self.subTest(mode=mode), self.assertRaisesRegex(EnvironmentError, 'FILE_MISMATCH'):
                self.reader()

    def test_path_escape_noncanonical_duplicates_and_invalid_rows(self):
        for name in ('../outside', '/outside', 'nested//file', './payload.bin', 'a\\b', 'a\nb'):
            self.seal(lambda v: dict(v, files=[dict(v['files'][0], path=name)]))
            with self.subTest(name=name), self.assertRaises(EnvironmentError):
                self.reader()
        for rows in ([], [dict(path='payload.bin', bytes=True, sha256='a'*64)],
                     [dict(path='payload.bin', bytes=9*2**30, sha256='a'*64)]):
            self.seal(lambda v: dict(v, files=rows))
            with self.subTest(rows=rows), self.assertRaises(EnvironmentError):
                self.reader()
        self.seal(lambda v: dict(v, files=v['files']*2))
        with self.assertRaises(EnvironmentError):
            self.reader()
        self.seal(lambda v: [])
        with self.assertRaises(EnvironmentError):
            self.reader()

    def test_undeclared_or_oversized_reads_rejected(self):
        for name, limit in (('not-listed', 100), ('payload.bin', 1)):
            with self.subTest(name=name), self.assertRaisesRegex(EnvironmentError, 'FILE_NOT_DECLARED_OR_TOO_LARGE'):
                self.reader().read(name, limit)

    def test_invalid_selection_blocks_both_prepares_before_cloud_or_ledger(self):
        (self.root / 'payload.bin').unlink()
        component, service = ComponentService(self.env), ServicePackages(self.env)
        with patch.object(component, '_worker') as cloud, \
                patch('aosedge_demo_orchestrator.service_packages.ServiceCatalog') as catalog, \
                patch('aosedge_demo_orchestrator.releases.ReleaseContinuity.reserve') as reserve, \
                patch('aosedge_demo_orchestrator.service_build.BackendService._run') as command:
            for action in (lambda: component.prepare(None, 'v1'), lambda: service.prepare('brake', 'v1')):
                with self.assertRaises(EnvironmentError):
                    action()
            for mock in (cloud, catalog, reserve, command):
                mock.assert_not_called()
        self.assertFalse((self.env.root / LEDGER).exists())

    def test_no_build_uses_packaged_product_but_explicit_build_keeps_developer_path(self):
        with patch.object(PreparationInputs, 'service', return_value={'fixture': True}) as product, \
                patch('aosedge_demo_orchestrator.service_build.BackendService._run', side_effect=RuntimeError('developer-path')):
            builder = ServiceBuilder(self.env)
            self.assertEqual({'fixture': True}, builder.execute('brake', 'v3', build_missing=False))
            product.assert_called_once_with('brake', 'v3')
            with self.assertRaisesRegex(RuntimeError, 'developer-path'):
                builder.execute('brake', 'v3', build_missing=True)
            product.assert_called_once()


if __name__ == '__main__':
    unittest.main()
