# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts/distribution'
with patch.object(sys, 'path', [str(SCRIPTS), *sys.path]):
    SPEC = importlib.util.spec_from_file_location('private_python', SCRIPTS / 'private_python.py')
    module = importlib.util.module_from_spec(SPEC)
    SPEC.loader.exec_module(module)


class PrivatePythonTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)

    def test_developer_packages_and_caches_are_never_copied(self):
        names = ['site-packages', '__pycache__', 'test', 'config-3.12-darwin',
                 'cache.pyc', 'cache.pyo', 'lib-dynload', 'encodings', 'ssl.py']
        self.assertEqual(module.excluded(self.base, names), names[:-2])

    def test_unqualified_python_family_rejected(self):
        source = self.base / '3.13'
        source.mkdir()
        with self.assertRaisesRegex(module.BundleError, 'Only the observed'):
            module.assemble(source, self.base / 'output', [self.base])

    def test_incomplete_source_fails_before_output(self):
        source = self.base / '3.12'
        source.mkdir()
        output = self.base / 'output'
        with self.assertRaisesRegex(module.BundleError, 'incomplete'):
            module.assemble(source, output, [self.base])
        self.assertFalse(output.exists())

    def test_distribution_and_user_startup_hooks_are_not_copied(self):
        names = ['sitecustomize.py', 'usercustomize.py', 'sitecustomize',
                 'usercustomize', 'site.py']
        self.assertEqual(module.excluded(self.base, names), names[:-1])

    def test_unexpected_stdlib_symlink_fails_before_output(self):
        source = self.base / '3.12'
        executable = source / 'Resources/Python.app/Contents/MacOS/Python'
        executable.parent.mkdir(parents=True)
        executable.write_bytes(b'fixture')
        standard = source / 'lib/python3.12'
        (standard / 'encodings').mkdir(parents=True)
        (standard / 'encodings/__init__.py').touch()
        (standard / 'external.py').symlink_to(executable)
        output = self.base / 'output'
        with self.assertRaisesRegex(module.BundleError, 'symlink'):
            module.assemble(source, output, [self.base])
        self.assertFalse(output.exists())

    def test_unexpected_native_module_symlink_fails_before_output(self):
        source = self.base / '3.12'
        executable = source / 'Resources/Python.app/Contents/MacOS/Python'
        executable.parent.mkdir(parents=True)
        executable.write_bytes(b'fixture')
        standard = source / 'lib/python3.12'
        (standard / 'encodings').mkdir(parents=True)
        (standard / 'encodings/__init__.py').touch()
        (standard / 'lib-dynload').mkdir()
        (standard / 'lib-dynload/external.so').symlink_to(executable)
        output = self.base / 'output'
        with self.assertRaisesRegex(module.BundleError, 'native-module symlink'):
            module.assemble(source, output, [self.base])
        self.assertFalse(output.exists())

    def test_assembly_excludes_hooks_and_budgets_stdlib(self):
        source = self.base / '3.12'
        executable = source / 'Resources/Python.app/Contents/MacOS/Python'
        executable.parent.mkdir(parents=True)
        executable.write_bytes(b'native-fixture')
        standard = source / 'lib/python3.12'
        (standard / 'encodings').mkdir(parents=True)
        (standard / 'encodings/__init__.py').write_bytes(b'stdlib')
        (standard / 'lib-dynload').mkdir()
        (standard / 'lib-dynload/fixture.so').write_bytes(b'extension')
        (standard / 'sitecustomize.py').write_text('raise RuntimeError("developer hook")')
        (standard / 'usercustomize').mkdir()
        (standard / 'usercustomize/__init__.py').write_text('raise RuntimeError("user hook")')
        (standard / 'site-packages').mkdir()
        (standard / 'site-packages/developer.py').touch()
        output = self.base / 'output'

        def native_stub(roots, allowed, target, provenance, minimum_free, maximum_input):
            target.mkdir()
            (target / 'lib/python3.12/lib-dynload').mkdir(parents=True)
            (target / 'lib/python3.12/lib-dynload/fixture.so').write_bytes(b'relocated')

        with patch.object(module, 'build', side_effect=native_stub) as builder:
            result = module.assemble(source, output, [self.base])
        self.assertEqual(result['stdlibSourceBytes'], 6)
        self.assertEqual(builder.call_args.args[-2:], (90 * 2**30 + 6, 2**30 - 6))
        payload = output / 'lib/python3.12'
        self.assertEqual((payload / 'encodings/__init__.py').read_bytes(), b'stdlib')
        self.assertEqual((payload / 'lib-dynload/fixture.so').read_bytes(), b'relocated')
        self.assertFalse((payload / 'sitecustomize.py').exists())
        self.assertFalse((payload / 'usercustomize').exists())
        self.assertFalse((payload / 'site-packages').exists())
        self.assertFalse(result['developmentCustomizationHooksCopied'])


if __name__ == '__main__':
    unittest.main()
