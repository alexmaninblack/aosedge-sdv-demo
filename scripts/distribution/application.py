# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Export current application and bind locked inputs; no installation or launch."""

import argparse
import ast
import hashlib
import json
from pathlib import Path
import shutil
import stat
import subprocess

from native_bundle import BundleError, sha256
from ui_helpers import PACKAGE, regular, safe_relative, tracked
from vehicle_inputs import CONTRACTS, clone_factory

REVIEWED = frozenset(('backend_inputs.py', 'cloud_runtime.py', 'host_entry.py',
                     'host_runtime.py', 'preparation_inputs.py', 'vm_runtime.py', 'runtime_paths.py', 'installed_control.py',
                     'source_server_trust.py', 'cloud_enrollment.py', 'subject_first_use.py'))
LOCKS = {
    'host-runtime': 'portable-host-launch/host-runtime.lock.json',
    'preparation-inputs': 'portable-preparation-inputs/vehicle-inputs.lock.json',
    'vm-runtime': 'portable-vm-launch/vm-runtime.lock.json',
    'cloud-runtime': 'portable-cloud-backend-inputs/cloud-runtime.lock.json',
    'backend-inputs': 'portable-cloud-backend-inputs/backend-inputs.lock.json',
}
EXTRA = ('LICENSE', 'workspace/repositories.json', 'config/aosvm-single-node-unitconfig.json',
         'contracts/qm-advisory-profile/advisory-readiness.v1.json',
         *('contracts/' + name for name in CONTRACTS),
         *('contracts/' + name for name in LOCKS.values()))
MAX_APP = 16 * 2**20
MAX_PAYLOAD = 48 * 2**30


def require(ok, message):
    if not ok:
        raise BundleError(message)


def small(root, name):
    path = regular(root, name)
    info = path.stat()
    require(info.st_nlink == 1 and not info.st_mode & 0o7022 and info.st_size <= 2**20,
            'Unsafe application input')
    raw = path.read_bytes()
    require(len(raw) == info.st_size, 'Application input changed')
    return raw


def export_plan(integration, input_checkpoint=None):
    tracked_py = {p for p in tracked(integration, str(PACKAGE)) if p.suffix == '.py'}
    reviewed = {PACKAGE / name for name in REVIEWED}
    allowed = tracked_py | reviewed
    actual = {p.relative_to(integration) for p in (integration / PACKAGE).rglob('*.py')}
    require(actual == allowed, 'Unreviewed or missing application module')
    require({PACKAGE / '__init__.py', PACKAGE / 'cli.py', PACKAGE / 'presenter.py'} <= actual,
            'Application entry missing')
    files = {str(path): small(integration, path) for path in sorted(allowed)}
    names = {p.stem for p in allowed if p.parent == PACKAGE}
    initializer = ast.parse(files[str(PACKAGE / '__init__.py')])
    exports = {target.id for node in initializer.body if isinstance(node, ast.Assign)
               for target in node.targets if isinstance(target, ast.Name)}
    for name, raw in files.items():
        tree = ast.parse(raw, filename=name)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.level:
                require(node.level == 1, 'Unsupported relative application import')
                imports = [node.module.split('.')[0]] if node.module else [x.name for x in node.names]
                require(set(imports) <= (names if node.module else names | exports),
                        'Application import closure incomplete')
    for name in EXTRA:
        files[name] = small(integration, name)
        if name.endswith('.json'):
            json.loads(files[name])
    if input_checkpoint is not None:
        from candidate_inputs import locks
        for group, raw in locks(integration, input_checkpoint, LOCKS).items():
            files['contracts/'+LOCKS[group]] = raw
    require(sum(map(len, files.values())) <= MAX_APP, 'Application export too large')
    return files


def checked_group(root, lock):
    """Validate source-pinned inventory before any copy; never read arbitrary state."""
    pin = json.loads(lock)['manifest']
    manifest = safe_relative(pin['path'])
    path = regular(root, manifest)
    require(type(pin['bytes']) is int and 0 < pin['bytes'] <= 8*2**20 and
            path.stat().st_size == pin['bytes'], 'Input manifest size mismatch')
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == pin['sha256'], 'Input manifest pin mismatch')
    value = json.loads(raw)
    if 'files' in value:
        rows = value['files']
    else:
        # The existing backend manifest has one exported OCI archive.
        rows = [dict(path='backends.tar', bytes=value['archiveBytes'], sha256=value['archiveSha256'])]
    require(isinstance(rows, list) and 0 < len(rows) <= 20000, 'Input inventory invalid')
    expected = {str(manifest)}
    total = 0
    for row in rows:
        name = str(safe_relative(row['path']))
        require(name not in expected, 'Duplicate input inventory path')
        expected.add(name)
        source = regular(root, name)
        info = source.stat()
        require(type(row['bytes']) is int and 0 <= row['bytes'] <= 16*2**30 and
                info.st_nlink == 1 and not info.st_mode & 0o7022 and info.st_size == row['bytes'],
                'Input payload size/mode mismatch')
        if 'mode' in row:
            require(stat.S_IMODE(info.st_mode) == row['mode'], 'Input payload mode mismatch')
        # Transfer verification below hashes the clone; cp clones these exact inodes.
        total += info.st_size
    actual = set()
    for item in root.rglob('*'):
        require(not item.is_symlink(), 'Input inventory contains link')
        if not item.is_dir():
            actual.add(item.relative_to(root).as_posix())
    require(actual == expected and total <= MAX_PAYLOAD, 'Input inventory mismatch')
    return pin, rows, total


def stamp(path):
    info = path.stat()
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns,
            info.st_ctime_ns, info.st_mode, info.st_nlink)


def clone_group(source, target, rows, pin):
    require(not target.exists() and not target.is_symlink(), 'Input destination already exists')
    items = [*rows, pin]
    before = {row['path']: stamp(source / row['path']) for row in items}
    subprocess.run(['/bin/cp', '-cR', '-p', str(source), str(target)],
                   check=True, capture_output=True, timeout=180)
    for row in items:
        path = regular(target, row['path'])
        require(path.stat().st_nlink == 1 and path.stat().st_size == row['bytes'] and
                sha256(path) == row['sha256'], 'Input transfer changed')
        require(stamp(source / row['path']) == before[row['path']], 'Input source changed during transfer')


def write_new(root, name, raw):
    path = root / safe_relative(name)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(raw)
    path.chmod(0o444)
    require(path.read_bytes() == raw, 'Application transfer changed')


def assemble(integration, groups, output, *, input_checkpoint=None):
    output = output.absolute()
    require(not output.exists() and not output.is_symlink() and output.parent.is_dir(), 'Output must be new')
    require(not any(p.is_symlink() for p in (output.parent, *output.parents)), 'Linked output root')
    require(set(groups) == set(LOCKS), 'Exactly five input groups required')
    require(shutil.disk_usage(output.parent).free >= 90*2**30 + MAX_APP, 'Disk reserve exceeded')
    files = export_plan(integration) if input_checkpoint is None else export_plan(integration, input_checkpoint)
    checked = {name: checked_group(root, files['contracts/' + LOCKS[name]]) for name, root in groups.items()}
    vm_manifest = json.loads(small(groups['vm-runtime'], checked['vm-runtime'][0]['path']))
    require(vm_manifest.get('hostManifest') == checked['host-runtime'][0],
            'VM host manifest binding mismatch')
    require(sum(value[2] for value in checked.values()) <= MAX_PAYLOAD, 'Combined input budget exceeded')
    output.mkdir(mode=0o700)
    app = output / 'aosedge-sdv-demo'
    for name, raw in files.items():
        write_new(app, name, raw)
    catalogue = output / 'demo-artifacts/aosedge-sdv-demo'
    catalogue.mkdir(parents=True)
    for name, source in groups.items():
        pin, rows, _ = checked[name]
        clone_group(source, catalogue / name, rows, pin)
        print(json.dumps({'stage': 'INPUT_TRANSFER_VERIFIED', 'group': name}), flush=True)
        require(shutil.disk_usage(output).free >= 90*2**30, 'Disk reserve exceeded during transfer')
    # Preserve the accepted catalogue's fixed discovery layout. The second logical
    # path shares APFS blocks; no hardlink/symlink or discovery change is introduced.
    vehicle = json.loads((catalogue / 'preparation-inputs' / checked['preparation-inputs'][0]['path']).read_bytes())
    factory = vehicle['factory']
    original = catalogue / 'preparation-inputs/factory' / factory['version'] / 'manifest.json'
    destination = catalogue / 'factory-images' / safe_relative(factory['version'])
    write_new(destination, 'manifest.json', original.read_bytes())
    clone_factory(original.parent / safe_relative(factory['image']),
                  destination / safe_relative(factory['image']), factory)
    report = dict(schemaVersion=1, status='ASSEMBLED_NOT_LIVE_OR_INSTALLER_QUALIFIED',
                  installedStateContract='aosedge-demo-installed-state/1',
                  applicationFiles=[dict(path=name, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
                                    for name, raw in sorted(files.items())],
                  inputs={name: value[0] for name, value in checked.items()},
                  inputLogicalBytes=sum(value[2] for value in checked.values()),
                  sourceRevision=subprocess.run(['/usr/bin/git', '-C', str(integration), 'rev-parse', 'HEAD'],
                      capture_output=True, check=True, text=True, timeout=10).stdout.strip(),
                  sourceBytesRecorded=True, operatorStateCopied=False,
                  newRuntimeOwner=False, externalDistributionApproved=False,
                  factoryCatalogueMethod='APFS clone, unchanged catalogue and source manifest',
                  openGates=['integrated live validation',
                             'Docker installation/licensing and fresh-engine import',
                             'first-use TLS and credentials', 'installer', 'clean Mac', 'redistribution'])
    if input_checkpoint is not None:
        from candidate_inputs import identity
        report['packagingCheckpoint'] = identity(integration, input_checkpoint)
    write_new(output, 'application-manifest.json', (json.dumps(report, indent=2) + '\n').encode())
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--integration', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--input-checkpoint', help='Reviewed successor input pins relative to integration source')
    for name in LOCKS:
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    result = assemble(args.integration, {name: getattr(args, name.replace('-', '_')) for name in LOCKS}, args.output,
                      input_checkpoint=args.input_checkpoint)
    print(json.dumps({'status': result['status'], 'applicationFiles': len(result['applicationFiles']),
                      'inputLogicalBytes': result['inputLogicalBytes']}))


if __name__ == '__main__':
    main()
