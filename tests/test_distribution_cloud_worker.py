# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import base64
import csv
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import stat
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts/distribution'
with patch.object(sys, 'path', [str(SCRIPTS), *sys.path]):
    spec = importlib.util.spec_from_file_location('cloud_worker', SCRIPTS / 'cloud_worker.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)


class CloudWorkerTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()

    def wheel(self, additions=None, *, bad_record=False, unrecorded=False):
        path = self.root / 'fixture-1.0-py3-none-any.whl'
        files = {'fixture/__init__.py': b'',
                 'fixture-1.0.dist-info/METADATA': b'Name: fixture\nVersion: 1.0\nRequires-Dist: six>=1\n'}
        files.update(additions or {})
        text = io.StringIO()
        writer = csv.writer(text, lineterminator='\n')
        for name, data in files.items():
            digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b'=').decode()
            writer.writerow([name, 'sha256=' + ('invalid' if bad_record else digest), len(data)])
        writer.writerow(['fixture-1.0.dist-info/RECORD', '', ''])
        files['fixture-1.0.dist-info/RECORD'] = text.getvalue().encode()
        if unrecorded:
            files['unexpected.py'] = b''
        with zipfile.ZipFile(path, 'w') as archive:
            for name, data in files.items():
                archive.writestr(name, data)
        row = {'name': 'fixture', 'version': '1.0', 'file': path.name,
               'bytes': path.stat().st_size, 'sha256': module.sha256(path)}
        return path, row

    def test_valid_wheel_preserves_all_package_bytes_and_metadata(self):
        path, row = self.wheel()
        files, requirements = module.read_wheel(path, row)
        self.assertEqual(len(files), 3)
        self.assertEqual(requirements, ['six>=1'])

    def test_corrupt_archive_rejected_before_parsing(self):
        path, row = self.wheel()
        row['sha256'] = '0' * 64
        with self.assertRaisesRegex(module.BundleError, 'size/hash'):
            module.read_wheel(path, row)

    def test_record_digest_checked_even_if_outer_hash_matches(self):
        path, row = self.wheel(bad_record=True)
        with self.assertRaisesRegex(module.BundleError, 'RECORD content'):
            module.read_wheel(path, row)

    def test_unrecorded_payload_rejected(self):
        path, row = self.wheel(unrecorded=True)
        with self.assertRaisesRegex(module.BundleError, 'Unrecorded'):
            module.read_wheel(path, row)

    def test_metadata_identity_must_match_lock(self):
        path, row = self.wheel({'fixture-1.0.dist-info/METADATA': b'Name: other\nVersion: 1.0\n'})
        with self.assertRaisesRegex(module.BundleError, 'metadata does not match'):
            module.read_wheel(path, row)

    def test_incompatible_wheel_rejected(self):
        path, row = self.wheel()
        with patch.object(module, 'sys_tags', return_value=iter([])):
            with self.assertRaisesRegex(module.BundleError, 'platform mismatch'):
                module.read_wheel(path, row)

    def test_unsafe_member_paths_rejected(self):
        for name in ('../escape', '/absolute', 'a/../../escape', 'a\\b', 'a/./b'):
            with self.subTest(name=name), self.assertRaises(module.BundleError):
                module.member_path(zipfile.ZipInfo(name))

    def test_symlink_member_rejected(self):
        info = zipfile.ZipInfo('fixture/link')
        info.external_attr = (stat.S_IFLNK | 0o777) << 16
        with self.assertRaisesRegex(module.BundleError, 'non-regular'):
            module.member_path(info)

    def test_startup_hooks_scripts_and_private_containers_rejected(self):
        for name in ('a.pth', 'sitecustomize.py', 'usercustomize/__init__.py', 'private.p12',
                     'private.pfx', 'private.key', 'a.pyc', 'fixture.data/scripts/a'):
            with self.subTest(name=name), self.assertRaises(module.BundleError):
                module.member_path(zipfile.ZipInfo(name))

    def test_dependency_closure_and_dev_extras(self):
        rows = [{'name': name, 'version': '1.0'} for name in ('aos-prov', 'aos-keys', 'aos-signer', 'shared')]
        requirements = {'aos-prov': ['shared>=1'], 'aos-keys': ['dev; extra == "dev"'], 'aos-signer': [], 'shared': []}
        module.check_dependencies(rows, requirements)
        requirements['shared'] = ['absent>=1']
        with self.assertRaisesRegex(module.BundleError, 'Unsatisfied'):
            module.check_dependencies(rows, requirements)

    def test_unrelated_package_and_direct_url_rejected(self):
        rows = [{'name': name, 'version': '1.0'} for name in ('aos-prov', 'aos-keys', 'aos-signer', 'pip')]
        requirements = {row['name']: [] for row in rows}
        with self.assertRaisesRegex(module.BundleError, 'Unrelated'):
            module.check_dependencies(rows, requirements)
        requirements['aos-prov'] = ['pip @ https://example.invalid/pip.whl']
        with self.assertRaisesRegex(module.BundleError, 'unsupported'):
            module.check_dependencies(rows, requirements)

    def test_base_receipt_prevents_developer_packages_and_tamper(self):
        base = self.root / 'base'
        base.mkdir()
        binary = base / 'runtime'
        binary.write_bytes(b'fixture')
        receipt = {'versionFamily': '3.12', 'sitePackagesCopied': False,
                   'developmentCustomizationHooksCopied': False,
                   'files': [{'path': 'runtime', 'bytes': 7, 'sha256': module.sha256(binary)}]}
        (base / 'python-runtime-manifest.json').write_text(json.dumps(receipt))
        self.assertEqual(len(module.base_files(base)), 2)
        (base / 'developer-extra').touch()
        with self.assertRaisesRegex(module.BundleError, 'Extra files'):
            module.base_files(base)
        binary.write_bytes(b'changed')
        with self.assertRaisesRegex(module.BundleError, 'receipt mismatch'):
            module.base_files(base)

    def test_native_allows_vendor_universal2_without_thinning(self):
        base = self.root / 'candidate'
        native = base / module.SITE / 'fixture.so'
        native.parent.mkdir(parents=True)
        native.touch()
        def command(argv):
            return 'x86_64 arm64' if 'lipo' in argv[0] else 'cmd LC_LOAD_DYLIB\nname /usr/lib/libSystem.B.dylib (offset 24)\n'
        with patch.object(module, 'command', side_effect=command):
            rows = module.native_inventory(base)
        self.assertEqual(rows[0]['architectures'], ['x86_64', 'arm64'])
        self.assertTrue(rows[0]['vendorBytesUnmodified'])

    def test_native_missing_arm64_or_developer_load_rejected(self):
        base = self.root / 'candidate'
        native = base / module.SITE / 'fixture.so'
        native.parent.mkdir(parents=True)
        native.touch()
        with patch.object(module, 'command', return_value='x86_64'):
            with self.assertRaisesRegex(module.BundleError, 'arm64'):
                module.native_inventory(base)
        with patch.object(module, 'command', side_effect=['arm64', 'cmd LC_LOAD_DYLIB\nname /opt/homebrew/lib/bad.dylib (offset 24)\n']):
            with self.assertRaisesRegex(module.BundleError, 'non-OS'):
                module.native_inventory(base)

    def test_saved_lock_has_expected_roots_and_no_credentials(self):
        lock = module.load_lock(SCRIPTS.parents[1] / 'workspace/cloud-worker-wheels.lock.json')
        self.assertEqual(len(lock['packages']), 41)
        self.assertEqual({r['name']: r['version'] for r in lock['packages'] if r['name'].startswith('aos-')},
                         {'aos-keys': '1.10.0', 'aos-prov': '5.4.2', 'aos-signer': '2.0.1'})
        self.assertTrue(all(r['url'].startswith('https://files.pythonhosted.org/') for r in lock['packages']))

    def assemble_fixture(self, *, free=100 * 2**30, existing=False):
        base, wheelhouse, integration = [self.root / name for name in ('base', 'wheels', 'integration')]
        for path in (base, wheelhouse, integration):
            path.mkdir()
        (base / 'runtime').write_bytes(b'fixture')
        (base / 'python-runtime-manifest.json').write_text('{}')
        lock_path = self.root / 'lock.json'
        lock_path.write_text('{}')
        lock = {'packages': [{'name': n, 'version': '1.0', 'file': n + '.whl'}
                             for n in ('aos-prov', 'aos-keys', 'aos-signer')]}
        for row in lock['packages']:
            (wheelhouse / row['file']).touch()
        adapters = integration / 'scripts/host'
        adapters.mkdir(parents=True)
        for name in module.ADAPTERS:
            (adapters / name).write_bytes(b'fixture adapter')
        output = self.root / 'output'
        if existing:
            output.mkdir()
        def wheel(path, row):
            return {Path(row['name'] + '/__init__.py'): b'fixture package'}, []
        with patch.object(module, 'load_lock', return_value=lock), \
                patch.object(module, 'base_files', return_value={Path('runtime'): base / 'runtime'}), \
                patch.object(module, 'read_wheel', side_effect=wheel), \
                patch.object(module, 'native_inventory', return_value=[]), \
                patch.object(module.shutil, 'disk_usage', return_value=type('Usage', (), {'free': free})()):
            return module.assemble(base, wheelhouse, lock_path, integration, output)

    def test_assembly_records_payload_and_never_copies_unrelated_inputs(self):
        result = self.assemble_fixture()
        self.assertEqual(result['packageCount'], 3)
        self.assertEqual(len(result['files']), 8)
        self.assertFalse(result['operatorCredentialsCopied'])
        self.assertFalse(result['runtimeSelectorsChanged'])
        for row in result['files']:
            self.assertEqual(module.sha256(self.root / 'output' / row['path']), row['sha256'])

    def test_low_disk_stops_before_copy(self):
        with self.assertRaisesRegex(module.BundleError, 'Disk/input-size'):
            self.assemble_fixture(free=89 * 2**30)
        self.assertFalse((self.root / 'output').exists())

    def test_existing_candidate_never_overwritten(self):
        with self.assertRaisesRegex(module.BundleError, 'Output must be new'):
            self.assemble_fixture(existing=True)


if __name__ == '__main__':
    unittest.main()
