# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Installed-instance routing without Cloud, native apps, credentials or VMs."""

import hashlib
import io
import json
import os
from pathlib import Path
import plistlib
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from aosedge_demo_orchestrator import runtime_paths as paths
from aosedge_demo_orchestrator import host_runtime, cloud_runtime, backend_inputs, preparation_inputs, vm_runtime
from aosedge_demo_orchestrator.environment import EnvironmentError, EnvironmentService
from aosedge_demo_orchestrator.images import ImageCatalog
from aosedge_demo_orchestrator.status import load_configuration, project_root

VOLUME = '591578E3-8196-4B44-A575-CEC76B406789'  # Identifier only; no real volume is accessed.


def record(path, value):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.write_text(json.dumps(value))
    path.chmod(0o600)


class InstalledPathsTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='ip.', dir='/private/tmp')
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.state = self.base / 'state'
        self.identity = paths.create_instance(self.state)['instanceId']
        self.store = self.base / 'store'
        self.program = self.package('one')
        self.patch = patch.object(paths, 'volume_uuid', return_value=VOLUME)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.environment = patch.dict(os.environ, {}, clear=True)
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def package(self, version):
        raw = json.dumps(dict(operatorStateCopied=False, fixtureVersion=version)).encode()
        pin = hashlib.sha256(raw).hexdigest()
        kit = self.store / 'versions' / pin
        program = kit / 'aosedge-sdv-demo'
        program.mkdir(parents=True, mode=0o700)
        for directory in (self.store, self.store / 'versions'):
            directory.chmod(0o700)
        (kit / 'application-manifest.json').write_bytes(raw)
        record(self.store / 'store.json', dict(schemaVersion=1, kind='aosedge-package-store', volumeUUID=VOLUME))
        record(self.store / 'receipts' / (pin + '.json'), dict(schemaVersion=1,
            status='INSTALLED_NOT_ACTIVATED', volumeUUID=VOLUME, manifestSha256=pin,
            runtimeChanged=False, operatorStateCopied=False, cloudAccessed=False, activeVersionSelected=False))
        return program

    def session(self, program=None):
        return paths.installed_session(self.state, _program=program or self.program)

    def test_create_is_private_idempotent_and_empty_of_credentials(self):
        self.assertEqual(paths.create_instance(self.state), dict(instanceId=self.identity, reused=True))
        self.assertEqual({p.name for p in self.state.iterdir()}, {'instance.json', '.local', '.run', 'artifacts'})
        self.assertEqual((self.state / 'instance.json').stat().st_mode & 0o777, 0o600)
        for name in ('', '.local', '.run', 'artifacts'):
            self.assertEqual((self.state / name).stat().st_mode & 0o777, 0o700)

    def test_unknown_existing_directory_is_not_adopted(self):
        other = self.base / 'foreign'
        other.mkdir(mode=0o700)
        (other / 'note').write_text('preserve')
        with self.assertRaises(FileNotFoundError):
            paths.create_instance(other)
        self.assertEqual([p.name for p in other.iterdir()], ['note'])

    def test_unknown_schema_duplicate_keys_and_nonprivate_marker_block(self):
        marker = self.state / paths.MARKER
        original = marker.read_bytes()
        for raw in (b'{"schemaVersion":2}', b'{"schemaVersion":1,"schemaVersion":1}'):
            with self.subTest(raw=raw):
                marker.write_bytes(raw)
                with self.assertRaisesRegex(ValueError, 'INSTALLED_'):
                    paths.instance(self.state)
        marker.write_bytes(original)
        marker.chmod(0o644)
        with self.assertRaisesRegex(ValueError, 'STATE_NOT_PRIVATE'):
            paths.instance(self.state)

    def test_symlink_and_long_socket_path_block_before_creation(self):
        link = self.base / 'linked'
        link.symlink_to(self.state, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'PATH_LINKED'):
            paths.create_instance(link)
        long = self.base / ('x' * 100)
        with self.assertRaisesRegex(ValueError, 'SOCKET_PATH_TOO_LONG'):
            paths.create_instance(long)
        self.assertFalse(long.exists())

    def test_no_other_instance_or_artifact_override(self):
        with self.session():
            with self.assertRaisesRegex(ValueError, 'FOREIGN_STATE_ROOT'):
                EnvironmentService(self.base)
            with self.assertRaisesRegex(ValueError, 'ARTIFACT_OVERRIDE_FORBIDDEN'):
                ImageCatalog(root=self.base)
            with self.assertRaisesRegex(ValueError, 'INSTANCE_ALREADY_SELECTED'):
                with self.session():
                    pass
        with patch.dict(os.environ, {'DEMO_ARTIFACT_ROOT': str(self.base)}):
            with self.assertRaisesRegex(ValueError, 'ARTIFACT_OVERRIDE_FORBIDDEN'):
                with self.session():
                    pass

    def test_roots_and_credentials_are_private_without_inherited_settings(self):
        with self.session():
            env = EnvironmentService()
            self.assertEqual(project_root(), self.state)
            self.assertEqual(env.root, self.state)
            self.assertEqual(paths.program_root(), self.program)
            self.assertEqual(env.catalog.project, self.state / 'artifacts/aosedge-sdv-demo')
            self.assertEqual(env.catalog.input_root, self.program.parent / 'demo-artifacts')
            config = load_configuration(self.state)
            for profile in config['cloudProfiles'].values():
                self.assertTrue(profile['credential'].is_relative_to(self.state / '.local/demo-control/credentials'))
                self.assertFalse(profile['credential'].exists())
            self.assertTrue(config['cloudPython'].is_relative_to(paths.input_root()))
        self.assertEqual(project_root(), paths.CODE_ROOT)
        self.assertFalse(paths.installed())

    def test_all_five_missing_groups_block_without_developer_fallback(self):
        with self.session():
            env = EnvironmentService()
            functions = (lambda: host_runtime.selected(), lambda: cloud_runtime.selected(self.state),
                         lambda: backend_inputs.selected(env), lambda: preparation_inputs.selected(env),
                         lambda: vm_runtime.selected(env))
            for function in functions:
                with self.subTest(function=function):
                    with self.assertRaisesRegex(ValueError, 'PACKAGED_INPUT_REQUIRED'):
                        function()

    def test_corrupt_group_is_not_treated_as_absent(self):
        with self.session():
            root = paths.input_root() / 'aosedge-sdv-demo/host-runtime'
            root.mkdir(parents=True)
            with self.assertRaisesRegex(EnvironmentError, 'HOST_RUNTIME_'):
                host_runtime.selected()

    def test_selectors_use_program_locks_and_inputs_not_state_files(self):
        with self.session():
            env = EnvironmentService()
            for module, group, constructor, invoke in (
                (host_runtime, 'host-runtime', 'HostRuntime', lambda: host_runtime.selected()),
                (cloud_runtime, 'cloud-runtime', 'CloudRuntime', lambda: cloud_runtime.selected(self.state)),
                (backend_inputs, 'backend-inputs', 'BackendInputs', lambda: backend_inputs.selected(env)),
                (preparation_inputs, 'preparation-inputs', 'PreparationInputs', lambda: preparation_inputs.selected(env)),
                (vm_runtime, 'vm-runtime', 'VMRuntime', lambda: vm_runtime.selected(env)),
            ):
                with self.subTest(group=group):
                    folder = paths.input_root() / 'aosedge-sdv-demo' / group
                    folder.mkdir(parents=True)
                    with patch.object(module, constructor) as selected:
                        invoke()
                        self.assertEqual(selected.call_args.args[:2], (folder, self.program / module.LOCK))

    def test_packaged_child_command_preserves_instance(self):
        host = object.__new__(host_runtime.HostRuntime)
        host.verify = Mock()
        host.entry = Mock(return_value=Path('/fixture/python'))
        with self.session():
            command = host.cli(self.state)
            self.assertEqual(command[-2:], ['--instance-root', str(self.state)])
            self.assertTrue(command[3].startswith(str(self.program) + '/'))
            self.assertEqual(command[1:3], ['-I', '-B'])

    def test_keychain_namespace_is_per_instance_without_reading_keychain(self):
        from aosedge_demo_orchestrator.native_access import Keychain, SERVICE
        with patch('aosedge_demo_orchestrator.native_access.ctypes.CDLL') as api:
            legacy = Keychain().service
            with self.session():
                keychain = Keychain()
                self.assertEqual(keychain.service, SERVICE + b'.' + self.identity.encode())
                self.assertNotEqual(keychain.service, legacy)
            api.return_value.SecKeychainFindGenericPassword.assert_not_called()

    def test_tls_paths_are_instance_owned_and_not_from_workspace_manifest(self):
        from aosedge_demo_orchestrator.source import SourceDriver
        driver = SourceDriver(Mock(root=self.state))
        with self.session(), patch.object(host_runtime, 'selected', return_value=Mock()) as select:
            select.return_value.source_assets.return_value = {}
            with self.assertRaisesRegex(EnvironmentError, 'SOURCE_OPERATOR_TLS_REQUIRED'):
                driver.assets()
            tls = self.state / '.local/demo-control/tls'
            tls.mkdir(parents=True)
            for name in ('server-cert.pem', 'server-key.pem'):
                (tls / name).write_text('fixture, not a certificate')
            self.assertEqual(driver.assets()['tls'], tls)

    def test_generated_components_and_backends_belong_to_instance(self):
        from aosedge_demo_orchestrator.components import ComponentService
        from aosedge_demo_orchestrator.backends import BackendService
        with self.session():
            env = EnvironmentService()
            component = ComponentService(env)
            backend = BackendService(env)
            self.assertTrue(component.root.is_relative_to(self.state / 'artifacts'))
            self.assertTrue(backend.catalog.is_relative_to(self.state / 'artifacts'))

    def test_selecting_another_version_does_not_reset_any_state(self):
        names = ('.run/demo-current/journal.json',
                 'artifacts/aosedge-sdv-demo/backends/history.json', '.local/demo-control/credentials/fixture.txt')
        for name in names:
            record(self.state / name, dict(sentinel=name))
        before = {name: (self.state / name).read_bytes() for name in names}
        from aosedge_demo_orchestrator.releases import LEDGER, ReleaseContinuity
        record(self.state / LEDGER, dict(schemaVersion=1, versions={'vdp': '123.0.0', 'brake': '84.0.0', 'tire': '47.0.0'}))
        ledger = (self.state / LEDGER).read_bytes()
        other = self.package('two')
        for program in (self.program, other, self.program):
            with self.session(program):
                self.assertEqual(paths.program_root(), program)
                self.assertEqual(paths.instance_id(), self.identity)
                self.assertEqual({name: (self.state / name).read_bytes() for name in names}, before)
                self.assertEqual(ReleaseContinuity(EnvironmentService()).next('vdp'), '124.0.0')
                self.assertEqual((self.state / LEDGER).read_bytes(), ledger)
        self.assertFalse((self.program / '.local').exists())
        self.assertFalse((other / '.run').exists())

    def test_modified_receipt_manifest_and_volume_fail_closed(self):
        receipt = self.store / 'receipts' / (self.program.parent.name + '.json')
        original = json.loads(receipt.read_text())
        for key, value in (('schemaVersion', 2), ('runtimeChanged', True), ('manifestSha256', '0' * 64)):
            with self.subTest(key=key):
                record(receipt, original | {key: value})
                with self.assertRaisesRegex(ValueError, 'PACKAGE_RECEIPT_INVALID'):
                    with self.session():
                        pass
        record(receipt, original)
        with patch.object(paths, 'volume_uuid', return_value='OTHER'):
            with self.assertRaisesRegex(ValueError, 'VOLUME_CHANGED'):
                with self.session():
                    pass
        manifest = self.program.parent / 'application-manifest.json'
        manifest.write_text('{}')
        with self.assertRaisesRegex(ValueError, 'PACKAGE_RECEIPT_INVALID'):
            with self.session():
                pass
        self.assertFalse(paths.installed())

    def test_cli_invalid_instance_is_redacted(self):
        from aosedge_demo_orchestrator.cli import main
        with patch('sys.stderr', new_callable=io.StringIO) as output:
            result = main(['--instance-root', str(self.base / 'private-missing'), 'image', 'list'])
        self.assertEqual(result, 1)
        self.assertEqual(output.getvalue(), 'BLOCKED INSTALLED_STATE_UNAVAILABLE\n')

    def test_installed_build_requests_never_reach_developer_tools(self):
        from aosedge_demo_orchestrator.application import DemoOrchestrator
        from aosedge_demo_orchestrator.models import OperationRequest
        orchestrator = object.__new__(DemoOrchestrator)
        with self.session():
            for domain, action in (('image', 'build'), ('component', 'sm-build'), ('component', 'cm-test'),
                                   ('vehicle', 'build-runtime'), ('service', 'build'), ('backend', 'build')):
                with self.subTest(domain=domain):
                    result = orchestrator.execute(OperationRequest(domain=domain, action=action))
                    self.assertEqual(result.message, 'INSTALLED_DEVELOPER_OPERATION_UNAVAILABLE')

    def test_cloud_unit_template_is_read_from_program_not_private_state(self):
        from aosedge_demo_orchestrator.cloud_setup import CloudSetup
        document = {'nodes': [{'nodeType': 'fixture'}]}
        record(self.program / 'config/aosvm-single-node-unitconfig.json', document)
        setup = object.__new__(CloudSetup)
        setup.root = self.state
        with self.session(), patch('aosedge_demo_orchestrator.cloud_setup.credential_stamp', return_value='fixture'):
            # Certificate validation/Cloud selection precede this template read.
            config = load_configuration(self.state) | {'cloudConnection': {'domain': 'fixture.example'}}
            with patch('aosedge_demo_orchestrator.cloud_setup.load_configuration', return_value=config):
                self.assertEqual(setup._request()['unitConfig'], document)


class VolumeBindingTests(unittest.TestCase):
    def test_disk_identity_not_mount_label_is_required(self):
        path = Path('/private/tmp')
        info = dict(GlobalPermissionsEnabled=True, DeviceNode='/dev/disk9s1', MountPoint='/private/tmp', VolumeUUID=VOLUME)
        with patch.object(paths.subprocess, 'run', side_effect=[
            SimpleNamespace(returncode=0, stdout=b'Filesystem blocks used avail cap mount\n/dev/disk9s1 1 0 1 0% /same label\n'),
            SimpleNamespace(returncode=0, stdout=plistlib.dumps(info))]) as run:
            self.assertEqual(paths.volume_uuid(path), VOLUME)
            self.assertEqual(run.call_args.args[0][-1], '/dev/disk9s1')

    def test_unavailable_volume_has_fixed_reason(self):
        with patch.object(paths.subprocess, 'run', side_effect=PermissionError('private detail')):
            with self.assertRaisesRegex(ValueError, '^INSTALLED_VOLUME_UNAVAILABLE$'):
                paths.volume_uuid(Path('/private/tmp'))


if __name__ == '__main__':
    unittest.main()
