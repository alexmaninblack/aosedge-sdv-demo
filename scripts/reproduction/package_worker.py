# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Offline canonical owner dispatch for VM, backend and complete application inputs."""
import json
from pathlib import Path
import shutil
import sys


def assemble(root, target, paths, output, checkpoint):
    sys.path.insert(0, str(root/'scripts/distribution'))
    sys.path.insert(0, str(root/'apps/demo-orchestrator/src'))
    import application
    import candidate_inputs
    import native_bundle as native
    from build_scratch import directory
    from ui_helpers import regular
    from aosedge_demo_orchestrator import host_runtime, preparation_inputs, vm_runtime
    if target == 'backend-inputs':
        source = paths['backend-export']
        pins = candidate_inputs.pins(root, checkpoint, ('backend-inputs',))
        manifest = source/'archive-receipt.json'
        pin = pins['backend-inputs']
        application.require(manifest.stat().st_size == pin['bytes'] and native.sha256(manifest) == pin['sha256'],
                            'Backend manifest differs from reviewed checkpoint')
        value = json.loads(manifest.read_bytes())
        output.mkdir(mode=0o700)
        native.command(['/bin/cp', '-c', '-p', source/'images.tar', output/'backends.tar'])
        application.require(native.sha256(output/'backends.tar') == value['archiveSha256'], 'Backend transfer differs')
        shutil.copyfile(manifest, output/pin['path'])
        (output/pin['path']).chmod(0o444)
        return value
    if target == 'vm-runtime':
        import vm_inputs
        retained = paths['retained-vm']
        manifest = json.loads((retained/'vm-runtime-manifest.json').read_bytes())
        rows = {r['path']: r for r in manifest['files']}
        with directory(output.parent) as temporary:
            qemu = Path(temporary)
            for original, name in [('share/qemu/efi-virtio.rom', 'share/qemu/efi-virtio.rom'),
                                   ('notices/qemu/LICENSE', 'LICENSE'), ('notices/qemu/COPYING', 'COPYING')]:
                source = regular(retained, original)
                row = rows[original]
                application.require(source.stat().st_size == row['bytes'] and native.sha256(source) == row['sha256'],
                                    'Retained VM input changed')
                destination = qemu/name
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, destination)
            return vm_inputs.assemble(root, paths['host-runtime'], paths['preparation'], output,
                (host_runtime, preparation_inputs, vm_runtime), qemu, input_checkpoint=checkpoint)
    application.require(target == 'application', 'Unknown packaging owner')
    # The build receipt is adapter evidence, not an installed input. Only its
    # verified payload is cloned into this invocation's private staging directory.
    with directory(output.parent) as temporary:
        staged = Path(temporary)/'preparation-inputs'
        native.command(['/bin/cp', '-cR', '-p', paths['preparation'], staged])
        regular(staged, 'build-receipt.json').unlink()
        groups = {name: paths[name] for name in ('host-runtime', 'cloud-sdk', 'backend-inputs', 'vm-runtime')}
        groups['cloud-runtime'] = groups.pop('cloud-sdk')
        groups['preparation-inputs'] = staged
        result = application.assemble(root, groups, output, input_checkpoint=checkpoint)
        from installation_inputs import Bundle
        bundle = Bundle(output, native.sha256(output/'application-manifest.json'))
        bundle.check_inventory()
        return result


if __name__ == '__main__':
    root, target, selected, output, checkpoint = sys.argv[1:6]
    if sys.argv[6:]:
        if len(sys.argv[6:]) != 3 or sys.argv[6] != '--developer-seal':
            raise ValueError('Invalid developer result arguments')
        sys.path.insert(0, str(Path(root)/'scripts/distribution'))
        from developer_inputs import DeveloperInputs
        checkpoint = DeveloperInputs.load(sys.argv[7], sys.argv[8])
    paths = {k: Path(v) for k, v in json.loads(Path(selected).read_bytes()).items()}
    result = assemble(Path(root), target, paths, Path(output), checkpoint)
    print(json.dumps({'status': result.get('status', 'ASSEMBLED_VM_INPUTS_NOT_LIVE_QUALIFIED')}), flush=True)
