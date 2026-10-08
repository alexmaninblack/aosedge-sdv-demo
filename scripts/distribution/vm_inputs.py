# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Assemble small VM inputs; reuse host QEMU/Python, never boot or install."""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import stat
import sys
import tempfile

from native_bundle import BundleError


def require(condition, reason):
    if not condition:
        raise BundleError(reason)


def source_file(root, name, limit):
    path = root / name
    require(not any(p.is_symlink() for p in (path, *path.parents)), 'Linked VM input')
    info = path.stat()
    require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and not info.st_mode & 0o022 and
            0 < info.st_size <= limit, 'Invalid VM input file')
    with path.open('rb') as stream:
        data = stream.read(limit + 1)
    require(len(data) == info.st_size, 'VM input changed during read')
    return data


def assemble(integration, host, vehicle, output, api, qemu_prefix, *, input_checkpoint=None):
    host_api, preparation_api, vm_api = api
    output = output.absolute()
    require(not output.exists() and not output.is_symlink() and output.parent.is_dir(),
            'Output must be new with an existing parent')
    for path in (integration, host, vehicle, qemu_prefix, output.parent):
        require(not any(p.is_symlink() for p in (path, *path.parents)), 'Linked input or output root')
    if input_checkpoint is None:
        runtime = host_api.HostRuntime(host, integration / host_api.LOCK)
        inputs = preparation_api.PreparationInputs(vehicle, integration / preparation_api.LOCK)
        host_pin = json.loads(source_file(integration, host_api.LOCK, 16384))['manifest']
    else:
        from candidate_inputs import locks
        chosen = locks(integration, input_checkpoint, ('host-runtime', 'preparation-inputs'))
        # Existing validators read temporary copies of independently reviewed
        # source locks; no runtime trust/configuration path is changed.
        with tempfile.TemporaryDirectory(prefix='vm-input-locks-') as temporary:
            holder = Path(temporary)
            for group, raw in chosen.items():
                (holder/group).write_bytes(raw)
            runtime = host_api.HostRuntime(host, holder/'host-runtime')
            inputs = preparation_api.PreparationInputs(vehicle, holder/'preparation-inputs')
        host_pin = json.loads(chosen['host-runtime'])['manifest']
    runtime.verify('native', 'python')
    for name in ('native/bin/qemu-img', 'native/bin/qemu-system-aarch64'):
        runtime.file(name)
    runtime.entry('python')
    firmware = inputs.read('firmware/QEMU_EFI.fd', 4 * 2**20)
    require(hashlib.sha256(firmware).hexdigest() == vm_api.FIRMWARE_SHA, 'Firmware pin mismatch')
    files = {'firmware/QEMU_EFI.fd': firmware,
             'scripts/host/aosvm-dns-bridge': source_file(integration, 'scripts/host/aosvm-dns-bridge', 128 * 2**10),
             'LICENSE': source_file(integration, 'LICENSE', 128 * 2**10)}
    rom = source_file(qemu_prefix, 'share/qemu/efi-virtio.rom', 2**20)
    require(hashlib.sha256(rom).hexdigest() == vm_api.ROM_SHA, 'ROM pin mismatch')
    files['share/qemu/efi-virtio.rom'] = rom
    for name in ('LICENSE', 'COPYING'):
        files['notices/qemu/' + name] = source_file(qemu_prefix, name, 128 * 2**10)
    size = sum(map(len, files.values()))
    require(shutil.disk_usage(output.parent).free >= 90 * 2**30 + size, 'Disk reserve exceeded')
    value = dict(schemaVersion=1, contractId=vm_api.CONTRACT,
                 status='ASSEMBLED_VM_INPUTS_NOT_LIVE_QUALIFIED', hostManifest=host_pin,
                 files=[dict(path=name, bytes=len(data), sha256=hashlib.sha256(data).hexdigest(), mode=0o444)
                        for name, data in sorted(files.items())])
    raw = (json.dumps(value, sort_keys=True, indent=2) + '\n').encode()
    output.mkdir(mode=0o700)
    for name, data in files.items():
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as stream:
            stream.write(data)
        target.chmod(0o444)
        require(target.read_bytes() == data, 'VM input copy changed')
    with (output / vm_api.MANIFEST).open('xb') as stream:
        stream.write(raw)
    (output / vm_api.MANIFEST).chmod(0o444)
    return dict(schemaVersion=1, contractId=vm_api.CONTRACT,
                qualification='ENGINEERING_CANDIDATE_NOT_LIVE_QUALIFIED',
                manifest=dict(path=vm_api.MANIFEST, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-checkpoint', help='Reviewed successor input pins relative to integration source')
    for name in ('integration', 'host', 'vehicle', 'output', 'qemu-prefix'):
        parser.add_argument('--' + name, required=True, type=Path)
    args = parser.parse_args()
    sys.path.insert(0, str(args.integration / 'apps/demo-orchestrator/src'))
    from aosedge_demo_orchestrator import host_runtime, preparation_inputs, vm_runtime
    print(json.dumps(assemble(args.integration, args.host, args.vehicle, args.output,
                              (host_runtime, preparation_inputs, vm_runtime), args.qemu_prefix,
                              input_checkpoint=args.input_checkpoint), indent=2))


if __name__ == '__main__':
    main()
