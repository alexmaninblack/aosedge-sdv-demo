# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Portable VM selection; no live VM, DNS listener or operator state."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import Mock, patch

from aosedge_demo_orchestrator import vm_runtime as portable
from aosedge_demo_orchestrator.environment import EnvironmentError
from aosedge_demo_orchestrator.images import ImageCatalog
from aosedge_demo_orchestrator.vm import FIRMWARE, VMService
import test_host_runtime as fixtures


class VMRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.support = fixtures.HostTests()
        self.support.setUp()
        self.addCleanup(self.support.doCleanups)
        self.env = self.support.env
        self.env.catalog = ImageCatalog(workspace=self.support.base)
        self.root = self.env.catalog.project / 'vm-runtime'
        self.root.mkdir()
        self.lock = self.env.root / portable.LOCK
        self.lock.parent.mkdir(parents=True)
        for name in portable.FILES:
            p = self.root / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(b'firmware' if name.startswith('firmware/') else b'fixture')
            p.chmod(0o444)
        for name in ('qemu-img', 'qemu-system-aarch64'):
            p = self.support.root / 'native/bin' / name
            p.write_bytes(b'executable-fixture')
            p.chmod(0o755)
        self.support.seal()
        handle = patch.object(portable, 'FIRMWARE_SHA', hashlib.sha256(b'firmware').hexdigest())
        handle.start()
        self.addCleanup(handle.stop)
        rom_pin = patch.object(portable, 'ROM_SHA', hashlib.sha256(b'fixture').hexdigest())
        rom_pin.start(); self.addCleanup(rom_pin.stop)
        self.seal()
        self.vm = VMService(self.env)
        self.state = dict(vehicles={'test': dict(localVmId='11111111-1111-4111-8111-111111111111',
            overlay='.local/demo-current/validation.qcow2', sshPort=10022, mac='02:11:11:11:11:11')},
            shared={'dns': {'ownerId': '22222222-2222-4222-8222-222222222222'}})

    def seal(self, change=None):
        value = dict(schemaVersion=1, contractId=portable.CONTRACT,
            status='ASSEMBLED_VM_INPUTS_NOT_LIVE_QUALIFIED',
            hostManifest=json.loads(self.support.lock.read_text())['manifest'],
            files=[dict(path=name, bytes=(self.root / name).stat().st_size,
                        sha256=hashlib.sha256((self.root / name).read_bytes()).hexdigest(), mode=mode)
                   for name, mode in portable.FILES.items()])
        if change:
            change(value)
        raw = json.dumps(value).encode()
        path = self.root / portable.MANIFEST
        path.write_bytes(raw)
        self.lock.write_text(json.dumps(dict(schemaVersion=1, contractId=portable.CONTRACT,
            manifest=dict(path=portable.MANIFEST, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()))))

    def test_absent_bundle_preserves_developer_commands(self):
        self.root.rename(self.root.with_name('not-selected'))
        self.assertIsNone(portable.selected(self.env))
        with patch('aosedge_demo_orchestrator.vm.shutil.which', return_value='/legacy/qemu'):
            command = self.vm._command(self.state, 'test')
        self.assertEqual('/legacy/qemu', command[0])
        self.assertEqual(str(self.vm.assets / FIRMWARE), command[command.index('-bios')+1])
        self.assertEqual(sys.executable, self.vm._dns_command(self.state)[0])

    def test_packaged_machine_preserves_all_non_input_arguments(self):
        command = self.vm._command(self.state, 'test')
        self.root.rename(self.root.with_name('not-selected'))
        with patch('aosedge_demo_orchestrator.vm.shutil.which', return_value='/legacy/qemu'):
            legacy = self.vm._command(self.state, 'test')
        legacy[0] = command[0]
        legacy[1:1] = ['-L', str(self.root / 'share/qemu')]
        legacy[legacy.index('-bios')+1] = command[command.index('-bios')+1]
        self.assertEqual(legacy, command)
        self.assertIn('/host-runtime/native/bin/qemu-system-aarch64', command[0])
        self.assertIn('/vm-runtime/firmware/', command[command.index('-bios')+1])

    def test_dns_command_independent_of_calling_interpreter(self):
        first = self.vm._dns_command(self.state)
        with patch('aosedge_demo_orchestrator.vm.sys.executable', '/another/Python'):
            self.assertEqual(first, self.vm._dns_command(self.state))
        self.assertEqual(['-I', '-B'], first[1:3])
        self.assertEqual(str(self.support.root / 'python/bin/python3.12'), first[0])
        self.assertEqual(['--listen-port', '18053', '--owner-id', self.state['shared']['dns']['ownerId']], first[-4:])

    def test_exact_owner_from_different_interpreter_and_foreign_rejection(self):
        command = self.vm._dns_command(self.state)
        owner = self.state['shared']['dns']['ownerId']
        with patch('aosedge_demo_orchestrator.vm.sys.executable', '/different/python'), \
                patch.object(self.vm, '_processes', return_value=[(555, ' '.join(command))]):
            self.assertEqual(555, self.vm._owned_pid(command, owner))
        for rows in ([(555, ' '.join(['/legacy/python', *command[1:]]))],
                     [(555, ' '.join(command + ['--different']))],
                     [(555, ' '.join(command)), (556, ' '.join(command))]):
            with patch.object(self.vm, '_processes', return_value=rows), self.assertRaisesRegex(
                    EnvironmentError, 'VM_PROCESS_OWNER_CONTRADICTORY'):
                self.vm._owned_pid(command, owner)

    def test_qemu_img_uses_package_and_no_developer_environment(self):
        self.env.qemu_img = '/must/not/run'
        with patch('aosedge_demo_orchestrator.environment.subprocess.run', return_value=Mock(returncode=0, stdout=b'{}')) as run, \
                patch.dict(os.environ, {'PYTHONPATH': '/developer', 'DYLD_LIBRARY_PATH': '/developer'}):
            self.assertEqual(b'{}', self.env._command(['info', '--output=json', 'fixture']))
        args, kwargs = run.call_args
        self.assertEqual(str(self.support.root / 'native/bin/qemu-img'), args[0][0])
        self.assertNotIn('PYTHONPATH', kwargs['env'])
        self.assertNotIn('DYLD_LIBRARY_PATH', kwargs['env'])
        self.assertEqual('1', kwargs['env']['PYTHONDONTWRITEBYTECODE'])

    def test_tampered_qemu_blocks_before_process(self):
        (self.support.root / 'native/bin/qemu-img').write_bytes(b'changed')
        with patch('aosedge_demo_orchestrator.environment.subprocess.run') as run, self.assertRaises(EnvironmentError):
            self.env._command(['info', 'fixture'])
        run.assert_not_called()

    def test_invalid_selection_blocks_before_create_or_fallback(self):
        (self.root / 'firmware/QEMU_EFI.fd').chmod(0o644)
        with patch.object(self.env.catalog, 'resolve') as resolve, patch.object(self.env, '_writer') as writer, \
                self.assertRaisesRegex(EnvironmentError, 'FILE_CHANGED'):
            self.env.create('test', 'fixture')
        resolve.assert_not_called(); writer.assert_not_called()

    def test_missing_link_and_extra_input_fail_closed(self):
        extra = self.root / 'unexpected.py'
        extra.write_text('not trusted')
        with self.assertRaisesRegex(EnvironmentError, 'UNDECLARED_FILE'):
            portable.selected(self.env)
        extra.unlink()
        extra.symlink_to(self.env.root, target_is_directory=True)
        with self.assertRaisesRegex(EnvironmentError, 'PATH_UNSAFE'):
            portable.selected(self.env)
        extra.unlink()
        (self.root / 'LICENSE').unlink()
        with self.assertRaisesRegex(EnvironmentError, 'FILE_UNAVAILABLE'):
            portable.selected(self.env)

    def test_missing_host_and_changed_host_pin_rejected(self):
        self.support.root.rename(self.support.root.with_name('host-absent'))
        with self.assertRaisesRegex(EnvironmentError, 'HOST_REQUIRED'):
            portable.selected(self.env)
        self.support.root.with_name('host-absent').rename(self.support.root)
        self.seal(lambda v: v['hostManifest'].update(sha256='a'*64))
        with self.assertRaisesRegex(EnvironmentError, 'HOST_PIN_MISMATCH'):
            portable.selected(self.env)

    def test_manifest_requires_independent_source_pin(self):
        path = self.root / portable.MANIFEST
        raw = path.read_bytes().replace(b'"schemaVersion": 1', b'"schemaVersion": 2')
        path.write_bytes(raw)
        with self.assertRaisesRegex(EnvironmentError, 'MANIFEST_CHANGED'):
            portable.selected(self.env)

    def test_missing_or_replaced_nic_rom_is_not_optional(self):
        path = self.root / 'share/qemu/efi-virtio.rom'
        path.chmod(0o644); path.write_bytes(b'corrupt'); path.chmod(0o444)
        with self.assertRaises(EnvironmentError):
            self.vm._command(self.state, 'test')
        self.seal()
        with self.assertRaisesRegex(EnvironmentError, 'ROM_PIN_CHANGED'):
            portable.selected(self.env)

    def test_duplicate_unbounded_and_firmware_repin_rejected(self):
        for change in (lambda v: v['files'].__setitem__(1, v['files'][0]),
                       lambda v: v['files'][0].update(bytes=5*2**20),
                       lambda v: v['files'][0].update(sha256='a'*64)):
            self.seal(change)
            with self.assertRaises(EnvironmentError):
                portable.selected(self.env)

    def test_spawns_validate_closure_and_strip_injection(self):
        (self.env.root / '.run/demo-current').mkdir(parents=True)
        dns = self.vm._dns_command(self.state)
        with patch('aosedge_demo_orchestrator.vm.subprocess.Popen', return_value=Mock(pid=555)) as popen, \
                patch.dict(os.environ, {'PYTHONHOME': '/developer', 'DYLD_INSERT_LIBRARIES': '/bad'}):
            self.assertEqual(555, self.vm._spawn(dns))
        self.assertNotIn('PYTHONHOME', popen.call_args.kwargs['env'])
        self.assertNotIn('DYLD_INSERT_LIBRARIES', popen.call_args.kwargs['env'])
        extra = self.support.root / 'python/extra.py'
        extra.write_text('not trusted')
        with patch('aosedge_demo_orchestrator.vm.subprocess.Popen') as popen, self.assertRaises(EnvironmentError):
            self.vm._spawn(dns)
        popen.assert_not_called()

    def test_profile_checks_selected_qemu_and_firmware_not_path(self):
        with patch('aosedge_demo_orchestrator.vm.platform.system', return_value='Darwin'), \
                patch('aosedge_demo_orchestrator.vm.platform.machine', return_value='arm64'), \
                patch('aosedge_demo_orchestrator.vm.FIRMWARE_SHA', portable.FIRMWARE_SHA), \
                patch('aosedge_demo_orchestrator.vm.shutil.which', side_effect=AssertionError('PATH forbidden')), \
                patch('aosedge_demo_orchestrator.vm.subprocess.run', return_value=Mock(
                    stdout='QEMU emulator version 11.0.3\n')) as run:
            self.vm._host_profile()
        self.assertEqual(str(self.support.root / 'native/bin/qemu-system-aarch64'), run.call_args.args[0][0])
        self.assertEqual(15, run.call_args.kwargs['timeout'])

    def test_version_timeout_is_bounded_local_error_without_spawn(self):
        with patch('aosedge_demo_orchestrator.vm.platform.system', return_value='Darwin'), \
                patch('aosedge_demo_orchestrator.vm.platform.machine', return_value='arm64'), \
                patch('aosedge_demo_orchestrator.vm.FIRMWARE_SHA', portable.FIRMWARE_SHA), \
                patch('aosedge_demo_orchestrator.vm.subprocess.run',
                      side_effect=subprocess.TimeoutExpired(['fixture', '--version'], 15)) as run, \
                patch.object(self.vm, '_spawn') as spawn:
            with self.assertRaisesRegex(EnvironmentError, '^VM_VERSION_PROBE_TIMEOUT$'):
                self.vm._host_profile()
        self.assertEqual(1, run.call_count)
        self.assertEqual(15, run.call_args.kwargs['timeout'])
        spawn.assert_not_called()


if __name__ == '__main__':
    unittest.main()
