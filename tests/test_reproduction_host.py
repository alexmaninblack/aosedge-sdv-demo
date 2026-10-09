# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Host packaging receipts do not imply live or installer qualification."""
import json
import shutil
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from test_reproduction import StorageFixture
from reproduction import core, host, host_worker
from reproduction.artifacts import sha256


class HostTests(StorageFixture, unittest.TestCase):
    def fixture(self):
        self.storage.environment()
        self.patch('reproduction.host.verify_sources')
        self.patch('reproduction.packaging.producer', return_value=({'recipe': 'a'*40}, 'b'*40))
        self.patch('reproduction.host.retained', return_value=(self.base/'retained', {'sha256': 'a'*64}))
        self.patch('reproduction.gateway.sdk_input', return_value={'sha256': 'b'*64})
        self.patch('reproduction.host.selected', side_effect=lambda storage, state, target:
                   (target, self.base/target))
        self.state['builds']['gateway'] = {'inputs': {'sdk': {'sha256': 'b'*64}}}
        self.command = self.patch('reproduction.host.run_command', side_effect=self.owner)
        self.patch('reproduction.host.probe_native', return_value=[])

    def owner(self, args, **kwargs):
        output = Path(args[-1])
        output.mkdir()
        path = output/'file'
        path.write_bytes(b'fixture')
        path.chmod(0o444)
        core.atomic_json(output/host.MANIFEST, {
            'schemaVersion': 1, 'status': 'ASSEMBLED_HOST_LAUNCH_NOT_DISTRIBUTION_QUALIFIED',
            'credentialsIncluded': False,
            'files': [{'path': path.name, 'bytes': 7, 'sha256': sha256(path), 'mode': 0o444}]})
        return SimpleNamespace(returncode=0, stdout=b'{}', stderr=b'')

    def build(self):
        return host.assemble(self.storage, self.state, self.base, self.base/'sdk', sys.executable, lambda *args: None)

    def test_first_repeat_and_state_recovery(self):
        self.fixture()
        key = self.build()
        self.assertEqual(self.build(), key)
        del self.state['builds'][key]
        self.assertEqual(self.build(), key)
        self.assertEqual(self.command.call_count, 1)
        output = self.storage.path('builds/host-runtime/'+key)
        self.assertFalse((output/'build-receipt.json').exists())
        self.assertTrue(host.receipt_path(output).exists())

    def test_failed_worker_does_not_complete_or_retry(self):
        self.fixture()
        def failed(args, **kwargs):
            self.owner(args, **kwargs)
            return SimpleNamespace(returncode=1, stdout=b'', stderr=b'fixture failure')
        self.command.side_effect = failed
        with self.assertRaisesRegex(core.LabError, 'Host owner failed'):
            self.build()
        with self.assertRaises(FileNotFoundError):
            self.build()
        self.assertEqual(self.command.call_count, 1)

    def test_changed_payload_refused(self):
        self.fixture()
        key = self.build()
        path = self.storage.path('builds/host-runtime/'+key+'/file')
        path.chmod(0o644)
        path.write_bytes(b'changed')
        path.chmod(0o444)
        with self.assertRaisesRegex(core.LabError, 'Host output changed'):
            self.build()

    def test_extra_output_refused(self):
        self.fixture()
        key = self.build()
        self.storage.path('builds/host-runtime/'+key+'/extra').write_text('extra')
        with self.assertRaisesRegex(core.LabError, 'inventory differs'):
            self.build()

    def test_sdk_cannot_differ_from_compilation(self):
        self.fixture()
        self.state['builds']['gateway']['inputs']['sdk'] = {'sha256': 'd'*64}
        with self.assertRaisesRegex(core.LabError, 'SDK selection differs'):
            self.build()
        self.command.assert_not_called()

    def test_missing_or_ambiguous_upstream_refused(self):
        with self.assertRaisesRegex(core.LabError, 'Exactly one completed'):
            host.selected(self.storage, self.state, 'gateway')
        self.state['builds'] = {'one': {'target': 'gateway'}, 'two': {'target': 'gateway'}}
        with self.assertRaisesRegex(core.LabError, 'Exactly one completed'):
            host.selected(self.storage, self.state, 'gateway')

    def test_explicit_kit_and_same_ssd_required(self):
        with self.assertRaisesRegex(core.LabError, 'Specify --kit-inputs'):
            host.retained(self.storage, None)
        with patch('reproduction.host.storage_volume', return_value={'uuid': 'OTHER'}):
            with self.assertRaisesRegex(core.LabError, 'bound volume'):
                host.retained(self.storage, self.base)

    def test_worker_runs_offline_without_home_or_dyld_overrides(self):
        self.fixture()
        self.build()
        args = self.command.call_args.args[0]
        self.assertEqual(str(args[0]), '/usr/bin/sandbox-exec')
        self.assertIn('(deny network*)', Path(args[2]).read_text())
        env = self.command.call_args.kwargs['env']
        self.assertNotIn('HOME', env)
        self.assertNotIn('DYLD_LIBRARY_PATH', env)

    def test_native_probes_are_separate_and_do_not_start_runtime(self):
        with patch('reproduction.host.run_command', return_value=SimpleNamespace(returncode=0, stdout=b'help')) as run:
            rows = host.probe_native(self.storage, self.base/'output')
        self.assertEqual(len(rows), 4)
        for call in run.call_args_list:
            self.assertEqual(str(call.args[0][0]), '/usr/bin/sandbox-exec')
            self.assertIn(call.args[0][-1], ('--help', '--version'))
            self.assertIn('deny network*', call.args[0][2])
            self.assertIn('/opt/homebrew', call.args[0][2])

    def test_only_declared_files_are_cloned_not_finder_metadata(self):
        source = self.base/'source'
        source.mkdir()
        (source/'file').write_bytes(b'fixture')
        (source/'.DS_Store').write_bytes(b'not a package input')
        def command(args):
            for path in args[3:-1]:
                shutil.copy2(path, Path(args[-1])/path.name)
        native = SimpleNamespace(command=command, sha256=sha256, BundleError=core.LabError)
        rows = [{'path': 'file', 'bytes': 7, 'sha256': sha256(source/'file'),
                 'mode': (source/'file').stat().st_mode & 0o777}]
        output = self.base/'copy'
        host_worker.clone_selected(source, output, rows, native, lambda root, name: core.regular(root/name))
        self.assertEqual({p.name for p in output.iterdir()}, {'file'})
        self.assertTrue((source/'.DS_Store').exists())


if __name__ == '__main__':
    unittest.main()
