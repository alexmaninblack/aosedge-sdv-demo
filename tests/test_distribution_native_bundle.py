# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Isolated build-tool tests; never starts QEMU or a real simulator."""

import importlib.util
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

MODULE = Path(__file__).resolve().parents[1] / 'scripts/distribution/native_bundle.py'
SPEC = importlib.util.spec_from_file_location('native_bundle', MODULE)
bundle = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bundle)


def info(*dependencies):
    return {'dependencies': list(dependencies), 'rpaths': [], 'id': None}


class NativeBundleTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.executable = self.file('source/tool')
        self.library = self.file('libraries/libone.dylib')

    def file(self, name):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b'fixture only, not an executable')
        return path

    def test_parse_load_commands_excludes_own_id_and_handles_spaces(self):
        parsed = bundle.parse_loads('''
      cmd LC_ID_DYLIB
     name /old/path/self.dylib (offset 24)
      cmd LC_LOAD_DYLIB
     name /path with spaces/lib.dylib (offset 24)
      cmd LC_LOAD_WEAK_DYLIB
     name /usr/lib/libSystem.B.dylib (offset 24)
      cmd LC_RPATH
     path /old path/lib (offset 12)
''')
        self.assertEqual(parsed['id'], '/old/path/self.dylib')
        self.assertEqual(parsed['dependencies'], ['/path with spaces/lib.dylib', '/usr/lib/libSystem.B.dylib'])
        self.assertEqual(parsed['rpaths'], ['/old path/lib'])

    def test_pre_advisory_gateway_is_rejected_before_output(self):
        output = self.root / 'candidate'
        with self.assertRaisesRegex(bundle.BundleError, 'QM advisory'):
            bundle.build({'carla-ego-runtime': self.executable}, [self.root], output, 'test', 0, 2**30)
        self.assertFalse(output.exists())

    def test_gateway_and_client_require_both_service_contracts(self):
        for name in ('carla-ego-runtime', 'bin/carla-viss-client'):
            for missing in bundle.GATEWAY_PATHS:
                with self.subTest(name=name, missing=missing):
                    self.executable.write_bytes(b'\0'.join(p for p in bundle.GATEWAY_PATHS if p != missing))
                    with self.assertRaisesRegex(bundle.BundleError, 'QM advisory'):
                        bundle.validate_gateway_contract({name: self.executable})
            self.executable.write_bytes(b'\0'.join(bundle.GATEWAY_PATHS))
            bundle.validate_gateway_contract({name: self.executable})

    def test_unrelated_native_inputs_do_not_require_gateway_paths(self):
        bundle.validate_gateway_contract({'qemu-img': self.executable})

    def test_system_libraries_do_not_need_files_on_build_host(self):
        self.assertIsNone(bundle.dependency('/usr/lib/system-cache-only.dylib', self.executable, []))

    def test_system_prefix_lookalike_is_not_trusted(self):
        with self.assertRaises(bundle.BundleError):
            bundle.dependency('/usr/library/untrusted.dylib', self.executable, [])

    def test_unresolved_rpath_fails_without_environment_fallback(self):
        with self.assertRaisesRegex(bundle.BundleError, 'Unresolved'):
            bundle.dependency('@rpath/libone.dylib', self.executable, [self.root])

    def test_missing_library_fails(self):
        with self.assertRaisesRegex(bundle.BundleError, 'Missing'):
            bundle.dependency(str(self.root / 'missing.dylib'), self.executable, [self.root])

    def test_symlink_escape_is_rejected(self):
        link = self.root / 'libraries/escape.dylib'
        link.symlink_to(self.executable)
        with self.assertRaisesRegex(bundle.BundleError, 'outside'):
            bundle.dependency(str(link), self.executable, [self.library.parent])

    def test_loader_relative_resolution(self):
        self.assertEqual(bundle.dependency('@loader_path/../libraries/libone.dylib',
                                          self.executable, [self.library.parent]), self.library)

    def test_transitive_cycle_is_collected_once(self):
        second = self.file('libraries/libtwo.dylib')
        descriptions = {self.executable: info(str(self.library)),
                        self.library: info(str(second)), second: info(str(self.library))}
        nodes, destinations = bundle.plan({'tool': self.executable}, [self.library.parent], descriptions.__getitem__)
        self.assertEqual(len(nodes), 3)
        self.assertEqual(destinations[second], Path('lib/libtwo.dylib'))

    def test_basename_collision_rejected_before_copy(self):
        second = self.file('other/libone.dylib')
        with self.assertRaisesRegex(bundle.BundleError, 'collision'):
            bundle.plan({'tool': self.executable}, [self.root],
                        lambda path: info(str(self.library), str(second)))

    def test_unsafe_output_executable_name_rejected(self):
        with self.assertRaisesRegex(bundle.BundleError, 'Unsafe'):
            bundle.plan({'../outside': self.executable}, [self.root], lambda path: info())

    def test_duplicate_source_executable_rejected(self):
        with self.assertRaisesRegex(bundle.BundleError, 'Duplicate'):
            bundle.plan({'one': self.executable, 'two': self.executable}, [self.root], lambda path: info())

    def test_module_destination_is_explicit_and_relative(self):
        _, destinations = bundle.plan({'lib/python3.12/lib-dynload/_ssl.so': self.executable},
                                      [self.root], lambda path: info())
        self.assertEqual(destinations[self.executable], Path('lib/python3.12/lib-dynload/_ssl.so'))

    def test_unsafe_nested_destination_rejected(self):
        for name in ('lib/../../escape', 'lib//empty', '/lib/absolute', 'etc/settings', 'lib/./dot'):
            with self.subTest(name=name), self.assertRaises(bundle.BundleError):
                bundle.plan({name: self.executable}, [self.root], lambda path: info())

    def test_alias_destination_collision_rejected(self):
        with self.assertRaisesRegex(bundle.BundleError, 'Duplicate destination'):
            bundle.plan({'tool': self.executable, 'bin/tool': self.library}, [self.root], lambda path: info())

    def test_package_relative_reference(self):
        self.assertEqual(bundle.relative_load(Path('bin/tool'), Path('lib/libone.dylib')),
                         '@loader_path/../lib/libone.dylib')
        self.assertEqual(bundle.relative_load(Path('lib/libtwo.dylib'), Path('lib/libone.dylib')),
                         '@loader_path/libone.dylib')

    def test_existing_output_is_not_overwritten(self):
        with self.assertRaisesRegex(bundle.BundleError, 'must be new'):
            bundle.build({}, [], self.root, 'test', 0, 1)
        self.assertTrue(self.executable.is_file())

    def test_non_arm64_fails(self):
        with patch.object(bundle, 'command', return_value='x86_64 arm64'):
            with self.assertRaisesRegex(bundle.BundleError, 'arm64 only'):
                bundle.inspect(self.executable)

    def test_entitlements_request_machine_readable_xml(self):
        response = SimpleNamespace(returncode=0, stdout=b'<?xml version="1.0"?><plist version="1.0"><dict><key>com.apple.security.hypervisor</key><true/></dict></plist>', stderr=b'')
        with patch.object(bundle.subprocess, 'run', return_value=response) as call:
            self.assertEqual(bundle.entitlements(self.executable), {'com.apple.security.hypervisor': True})
        self.assertIn('--xml', call.call_args.args[0])

    def test_unsigned_input_is_distinct_from_bad_signature(self):
        with patch.object(bundle.subprocess, 'run', return_value=SimpleNamespace(
                returncode=1, stdout=b'', stderr=b'code object is not signed at all')):
            self.assertEqual(bundle.entitlements(self.executable), {})
        with patch.object(bundle.subprocess, 'run', return_value=SimpleNamespace(
                returncode=1, stdout=b'', stderr=b'cannot read file')):
            with self.assertRaises(bundle.BundleError):
                bundle.entitlements(self.executable)

    def test_insufficient_disk_has_no_output(self):
        output = self.root / 'candidate'
        with patch.object(bundle, 'plan', return_value=({self.executable: info()}, {self.executable: Path('bin/tool')})):
            with self.assertRaisesRegex(bundle.BundleError, 'budget'):
                bundle.build({'tool': self.executable}, [self.root], output, 'test', 2**80, 2**40)
        self.assertFalse(output.exists())

    def test_input_budget_has_no_output(self):
        output = self.root / 'candidate'
        with patch.object(bundle, 'plan', return_value=({self.executable: info()}, {self.executable: Path('bin/tool')})):
            with self.assertRaisesRegex(bundle.BundleError, 'budget'):
                bundle.build({'tool': self.executable}, [self.root], output, 'test', 0, 1)
        self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main()
