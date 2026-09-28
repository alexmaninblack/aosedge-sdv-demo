# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Small opt-in VM inputs, reusing the locked native/Python host closure."""

import hashlib
import json
import os
from pathlib import Path
import stat

from .environment import EnvironmentError
from . import host_runtime
from .status import read_json

LOCK = 'contracts/portable-vm-launch/vm-runtime.lock.json'
MANIFEST = 'vm-runtime-manifest.json'
CONTRACT = 'aosedge-demo-portable-vm-launch'
FILES = {'firmware/QEMU_EFI.fd': 0o444, 'scripts/host/aosvm-dns-bridge': 0o444, 'LICENSE': 0o444,
         'share/qemu/efi-virtio.rom': 0o444, 'notices/qemu/LICENSE': 0o444, 'notices/qemu/COPYING': 0o444}
FIRMWARE_SHA = '30f7042c23b81c28b8196a76f4af6bcf10046f08049c9d78b4387472c5bbcd10'
ROM_SHA = '26be36901db7f8181c306cc62bd74891d8646528965a78e40cceadba5dd7c8e7'
_verified = {}


def require(condition, reason):
    if not condition:
        raise EnvironmentError('VM_RUNTIME_' + reason)


def clean_environment():
    return {k: v for k, v in os.environ.items()
            if not k.startswith(('PYTHON', 'DYLD_'))} | {'PYTHONDONTWRITEBYTECODE': '1'}


def selected(environment):
    from .runtime_paths import catalogue_inputs, installed, program_root, required_group
    path = catalogue_inputs(environment.catalog) / 'vm-runtime'
    if not path.exists() and not path.is_symlink():
        if installed():
            required_group(environment.root, False)
        return None
    return VMRuntime(path, program_root(environment.root) / LOCK, environment)


class VMRuntime:
    def __init__(self, root, lock, environment):
        self.root = root
        try:
            require(root.is_dir() and not root.is_symlink(), 'PATH_UNSAFE')
            expected = read_json(lock)
            require(isinstance(expected, dict) and expected.get('schemaVersion') == 1 and
                    expected.get('contractId') == CONTRACT, 'LOCK_INVALID')
            pin = expected['manifest']
            require(pin['path'] == MANIFEST and type(pin['bytes']) is int and
                    0 < pin['bytes'] <= 16384, 'LOCK_INVALID')
            path = host_runtime.safe(root, MANIFEST)
            info = path.lstat()
            require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and not info.st_mode & 0o022 and
                    info.st_size == pin['bytes'], 'MANIFEST_INVALID')
            with path.open('rb') as stream:
                raw = stream.read(pin['bytes'] + 1)
            require(len(raw) == pin['bytes'] and hashlib.sha256(raw).hexdigest() == pin['sha256'], 'MANIFEST_CHANGED')
            value = json.loads(raw)
            require(value.get('schemaVersion') == 1 and value.get('contractId') == CONTRACT and
                    value.get('status') == 'ASSEMBLED_VM_INPUTS_NOT_LIVE_QUALIFIED', 'MANIFEST_INVALID')
            rows = value['files']
            require(isinstance(rows, list) and len(rows) == len(FILES), 'MANIFEST_INVALID')
            self.files = {}
            for row in rows:
                require(isinstance(row, dict) and set(row) == {'path', 'bytes', 'sha256', 'mode'}, 'MANIFEST_INVALID')
                name = row['path']
                require(name in FILES and name not in self.files and row['mode'] == FILES[name] and
                        type(row['bytes']) is int and 0 < row['bytes'] <= 4 * 2**20 and
                        isinstance(row['sha256'], str) and len(row['sha256']) == 64 and
                        all(c in '0123456789abcdef' for c in row['sha256']), 'MANIFEST_INVALID')
                self.files[name] = row
            require(self.files['firmware/QEMU_EFI.fd']['sha256'] == FIRMWARE_SHA, 'FIRMWARE_PIN_CHANGED')
            require(self.files['share/qemu/efi-virtio.rom']['sha256'] == ROM_SHA, 'ROM_PIN_CHANGED')
            # Two independent source locks must agree; the bundle cannot name
            # arbitrary host paths or supply its own executable trust anchor.
            from .runtime_paths import program_root
            host_pin = read_json(program_root(environment.root) / host_runtime.LOCK)['manifest']
            require(value['hostManifest'] == host_pin, 'HOST_PIN_MISMATCH')
            self.host = host_runtime.selected(environment.root, environment.catalog)
            require(self.host is not None, 'HOST_REQUIRED')
            self.verify()
        except EnvironmentError:
            raise
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            raise EnvironmentError('VM_RUNTIME_UNAVAILABLE_OR_INVALID') from None

    def file(self, name):
        try:
            require(name in self.files, 'FILE_NOT_DECLARED')
            row = self.files[name]
            path = host_runtime.safe(self.root, name)
            stamp = host_runtime.identity(path)
            require(stat.S_ISREG(stamp[5]) and stamp[6] == 1 and stamp[2] == row['bytes'] and
                    stat.S_IMODE(stamp[5]) == row['mode'], 'FILE_CHANGED')
            if _verified.get((path, row['sha256'])) != stamp:
                require(hashlib.sha256(path.read_bytes()).hexdigest() == row['sha256'] and
                        host_runtime.identity(path) == stamp, 'FILE_CHANGED')
                _verified[path, row['sha256']] = stamp
            return path
        except EnvironmentError:
            raise
        except OSError:
            raise EnvironmentError('VM_RUNTIME_FILE_UNAVAILABLE') from None

    def verify(self):
        for path in self.root.rglob('*'):
            require(not path.is_symlink(), 'PATH_UNSAFE')
            if not path.is_dir():
                require(path.relative_to(self.root).as_posix() in {*FILES, MANIFEST}, 'UNDECLARED_FILE')
        for name in FILES:
            self.file(name)

    def image_tool(self):
        self.host.verify('native')
        return str(self.host.file('native/bin/qemu-img'))

    def machine(self, *, execute=False):
        if execute:
            self.host.verify('native')
        return str(self.host.file('native/bin/qemu-system-aarch64')), str(self.file('firmware/QEMU_EFI.fd'))

    def data_directory(self):
        return self.file('share/qemu/efi-virtio.rom').parent

    def dns_command(self, owner):
        return [str(self.host.entry('python')), '-I', '-B', str(self.file('scripts/host/aosvm-dns-bridge')),
                '--listen-port', '18053', '--owner-id', owner]

    def verify_dns(self):
        self.host.verify('python')
        self.file('scripts/host/aosvm-dns-bridge')
