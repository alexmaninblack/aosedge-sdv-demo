# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts/distribution'
with patch.object(sys, 'path', [str(SCRIPTS), *sys.path]):
    SPEC = importlib.util.spec_from_file_location('vm_inputs', SCRIPTS / 'vm_inputs.py')
    module = importlib.util.module_from_spec(SPEC)
    SPEC.loader.exec_module(module)


class VMInputAssemblyTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.integration, self.host, self.vehicle = (self.root / name for name in ('app', 'host', 'vehicle'))
        self.output = self.root / 'VM inputs with spaces'
        for path in (self.integration, self.host, self.vehicle):
            path.mkdir()
        self.put('scripts/host/aosvm-dns-bridge', b'# unchanged DNS helper\n')
        self.put('LICENSE', b'MIT\n')
        self.qemu = self.integration
        self.put('share/qemu/efi-virtio.rom', b'rom')
        self.put('COPYING', b'GPL\n')
        self.pin = dict(path='host-runtime-manifest.json', bytes=1234, sha256='a'*64)
        self.put('contracts/host.lock.json', json.dumps({'manifest': self.pin}).encode())
        self.runtime = Mock()
        self.inputs = Mock()
        self.inputs.read.return_value = b'firmware'
        self.api = (SimpleNamespace(LOCK='contracts/host.lock.json', HostRuntime=Mock(return_value=self.runtime)),
                    SimpleNamespace(LOCK='contracts/vehicle.lock.json', PreparationInputs=Mock(return_value=self.inputs)),
                    SimpleNamespace(FIRMWARE_SHA=hashlib.sha256(b'firmware').hexdigest(),
                                    ROM_SHA=hashlib.sha256(b'rom').hexdigest(),
                                    CONTRACT='aosedge-demo-portable-vm-launch', MANIFEST='vm-runtime-manifest.json'))
        disk = patch.object(module.shutil, 'disk_usage', return_value=SimpleNamespace(free=100*2**30))
        disk.start(); self.addCleanup(disk.stop)

    def put(self, name, raw):
        path = self.integration / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)

    def build(self):
        return module.assemble(self.integration, self.host, self.vehicle, self.output, self.api, self.qemu)

    def test_bounded_bundle_reuses_host_without_copying_factory_or_secrets(self):
        self.put('.run/secret.pem', b'not copied')
        lock = self.build()
        files = {p.relative_to(self.output).as_posix() for p in self.output.rglob('*') if p.is_file()}
        self.assertEqual({'firmware/QEMU_EFI.fd', 'scripts/host/aosvm-dns-bridge', 'LICENSE',
                          'share/qemu/efi-virtio.rom', 'notices/qemu/LICENSE', 'notices/qemu/COPYING',
                          self.api[2].MANIFEST}, files)
        self.runtime.verify.assert_called_once_with('native', 'python')
        self.assertEqual(2, self.runtime.file.call_count)
        self.runtime.entry.assert_called_once_with('python')
        raw = (self.output / self.api[2].MANIFEST).read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), lock['manifest']['sha256'])
        self.assertEqual(len(raw), lock['manifest']['bytes'])
        value = json.loads(raw)
        self.assertEqual(self.pin, value['hostManifest'])
        for row in value['files']:
            self.assertEqual(0o444, (self.output / row['path']).stat().st_mode & 0o777)
            self.assertEqual(hashlib.sha256((self.output / row['path']).read_bytes()).hexdigest(), row['sha256'])

    def test_existing_output_preserved(self):
        self.output.mkdir(); (self.output / 'keep').write_text('keep')
        with self.assertRaisesRegex(module.BundleError, 'Output must be new'):
            self.build()
        self.assertEqual('keep', (self.output / 'keep').read_text())
        self.api[0].HostRuntime.assert_not_called()

    def test_bad_host_dependency_does_not_create_output(self):
        self.runtime.verify.side_effect = ValueError('invalid host')
        with self.assertRaisesRegex(ValueError, 'invalid host'):
            self.build()
        self.assertFalse(self.output.exists())

    def test_wrong_firmware_does_not_create_output(self):
        self.inputs.read.return_value = b'wrong'
        with self.assertRaisesRegex(module.BundleError, 'Firmware pin mismatch'):
            self.build()
        self.assertFalse(self.output.exists())

    def test_wrong_rom_does_not_create_output(self):
        self.put('share/qemu/efi-virtio.rom', b'wrong')
        with self.assertRaisesRegex(module.BundleError, 'ROM pin mismatch'):
            self.build()
        self.assertFalse(self.output.exists())

    def test_linked_helper_not_followed(self):
        path = self.integration / 'scripts/host/aosvm-dns-bridge'
        path.unlink(); path.symlink_to(self.integration / 'LICENSE')
        with self.assertRaisesRegex(module.BundleError, 'Linked VM input'):
            self.build()
        self.assertFalse(self.output.exists())

    def test_group_writable_helper_not_packaged(self):
        (self.integration / 'scripts/host/aosvm-dns-bridge').chmod(0o666)
        with self.assertRaisesRegex(module.BundleError, 'Invalid VM input file'):
            self.build()

    def test_oversized_helper_not_read(self):
        self.put('scripts/host/aosvm-dns-bridge', b'x' * (128*2**10+1))
        with self.assertRaisesRegex(module.BundleError, 'Invalid VM input file'):
            self.build()

    def test_low_disk_blocks_before_output(self):
        with patch.object(module.shutil, 'disk_usage', return_value=SimpleNamespace(free=90*2**30)), \
                self.assertRaisesRegex(module.BundleError, 'Disk reserve exceeded'):
            self.build()
        self.assertFalse(self.output.exists())


if __name__ == '__main__':
    unittest.main()
