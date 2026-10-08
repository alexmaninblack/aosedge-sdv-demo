# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Offline build worker; no UI, simulator, VM or service process is launched."""
import json
import os
from pathlib import Path
import shutil
import stat
import sys
import subprocess
import tempfile


def assemble(root, integration, gateway, retained, sdk, ui, binaries, output):
    sys.path.insert(0, str(root/'scripts/distribution'))
    sys.path.insert(0, str(root/'apps/demo-orchestrator/src'))
    import native_bundle as native
    import ui_helpers
    from application import clone_group
    from aosedge_demo_orchestrator import host_runtime

    def require(ok, message):
        if not ok:
            raise native.BundleError(message)

    original = json.loads((retained/host_runtime.MANIFEST).read_bytes())
    original_rows = host_runtime.manifest_rows(json.dumps(original).encode())
    # Each heavy group is already pinned by the adapter's historical host manifest.
    # Clone and hash once at transfer, preserving source identity and file modes.
    require(not output.exists() and output.parent.is_dir(), 'Host output must be new')
    output.mkdir(mode=0o700)
    copied = []
    for group in ('python', 'simulator', 'openssl'):
        rows = [{**r, 'path': name[len(group)+1:]} for name, r in original_rows.items()
                if name.startswith(group+'/')]
        require(rows, 'Missing retained host group')
        # clone_group's manifest argument can be one inventory row; do not invent
        # a second per-group manifest or change the established runtime format.
        clone_group(retained/group, output/group, rows[1:], rows[0])
        copied.extend({**r, 'path': group+'/'+r['path']} for r in rows)
        print(json.dumps({'stage': 'HOST_GROUP_TRANSFERRED', 'group': group}), flush=True)
    ui_helpers.assemble(integration, gateway, ui, output/'ui')
    print(json.dumps({'stage': 'UI_ASSEMBLED'}), flush=True)
    with tempfile.TemporaryDirectory(prefix='host-native-') as temporary:
        staging = Path(temporary)
        old_native = retained/'native'
        rows = [{**r, 'path': name[len('native/'):]} for name, r in original_rows.items()
                if name.startswith('native/')]
        for row in rows:
            source = ui_helpers.regular(old_native, row['path'])
            require(source.stat().st_size == row['bytes'] and native.sha256(source) == row['sha256'],
                    'Retained native payload changed')
        old_manifest = json.loads((old_native/'native-manifest.json').read_bytes())
        old_records = {r['path']: r for r in old_manifest['files']}
        sdk_manifest = json.loads((sdk/'sdk-manifest.json').read_bytes())
        sdk_rows = {r['path']: r for r in sdk_manifest['files']}
        replacements = {}
        for name in ('libssl.3.dylib', 'libcrypto.3.dylib'):
            # The retained relocated libraries originate from exactly the same
            # unsigned SDK libraries used for compilation, not just a version label.
            require(old_records['lib/'+name]['sourceSha256'] == sdk_rows['openssl/lib/'+name]['sha256'],
                    'Retained OpenSSL does not originate from the declared Gateway SDK')
            identity = native.inspect(sdk/'openssl/lib'/name)['id']
            require(identity and identity.startswith('/'), 'Invalid SDK library identity')
            replacements[identity] = str(old_native/'lib'/name)
        roots = {'qemu-img': old_native/'bin/qemu-img', 'qemu-system-aarch64': old_native/'bin/qemu-system-aarch64'}
        for name in ('carla-ego-runtime', 'carla-viss-client'):
            target = staging/name
            shutil.copyfile(binaries/name, target)
            target.chmod(0o755)
            info = native.inspect(target)
            edits = []
            for load in info['dependencies']:
                if not load.startswith(native.SYSTEM):
                    require(load in replacements, 'Gateway contains undeclared native dependency')
                    edits.extend(['-change', load, replacements[load]])
            if edits:
                native.command(['/usr/bin/install_name_tool', *edits, target])
            # install_name_tool invalidates the original local signature.
            native.command(['/usr/bin/codesign', '--force', '--sign', '-', target])
            roots[name] = target
        result = native.build(roots, [old_native, staging], output/'native',
            'R2 verified Gateway build and retained host native manifest; exact OpenSSL SDK source hashes checked',
            90*2**30, 512*2**20)
        policy = staging/'no-developer-libraries.sb'
        policy.write_text('(version 1)\n(allow default)\n(deny network*)\n'
                          '(deny file-read* (subpath "/opt/homebrew"))\n')
        probes = []
        for name in ('carla-ego-runtime', 'carla-viss-client', 'qemu-img', 'qemu-system-aarch64'):
            flag = '--help' if name == 'carla-viss-client' else '--version'
            probe = subprocess.run(['/usr/bin/sandbox-exec', '-f', str(policy),
                str(output/'native/bin'/name), flag], capture_output=True, timeout=30,
                env={**os.environ, 'CARLA_CACHE_DIR': str(staging/'carla-cache')})
            require(probe.returncode == 0 and probe.stdout.strip(), 'Relocated native version probe failed: '+name)
            probes.append({'entry': name, 'argument': flag, 'exitCode': 0, 'homebrewReadDenied': True, 'networkDenied': True})
        notices = [r for r in rows if r['path'].startswith('notices/')]
        for row in notices:
            target = output/'native'/row['path']
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(old_native/row['path'], target)
            target.chmod(row['mode'])
        result['retainedNoticeFiles'] = notices
        result['gatewayBuildReceiptSha256'] = native.sha256(binaries/'build-receipt.json')
        result['versionProbes'] = probes
        (output/'native/native-manifest.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'stage': 'NATIVE_RELOCATED_AND_SIGNATURES_VERIFIED'}), flush=True)
    # New UI/native outputs are small; heavy bytes already have transfer hashes.
    for group in ('ui', 'native'):
        for path in sorted((output/group).rglob('*')):
            require(not path.is_symlink(), 'Host output contains a symlink')
            if path.is_file():
                copied.append({'path': path.relative_to(output).as_posix(), 'bytes': path.stat().st_size,
                    'mode': stat.S_IMODE(path.stat().st_mode), 'sha256': native.sha256(path)})
    value = {'schemaVersion': 1, 'status': 'ASSEMBLED_HOST_LAUNCH_NOT_DISTRIBUTION_QUALIFIED',
        'credentialsIncluded': False, 'files': sorted(copied, key=lambda r: r['path']),
        'simulator': original['simulator'], 'derivedFromManifestSha256': native.sha256(retained/host_runtime.MANIFEST),
        'change': 'Rebuilt UI and Gateway, exact retained native dependencies, unchanged simulator/Python/OpenSSL tool',
        'sourceRevisions': {name: native.command(['/usr/bin/git', '-C', path, 'rev-parse', 'HEAD']).strip()
                            for name, path in [('integration', integration), ('gateway', gateway)]}}
    host_runtime.manifest_rows(json.dumps(value).encode())
    with (output/host_runtime.MANIFEST).open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
    (output/host_runtime.MANIFEST).chmod(0o444)
    return value


if __name__ == '__main__':
    result = assemble(*map(Path, sys.argv[1:9]))
    print(json.dumps({'status': result['status'], 'files': len(result['files'])}), flush=True)
