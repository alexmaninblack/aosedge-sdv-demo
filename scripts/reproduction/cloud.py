# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Cloud SDK owner adapter: declared Python input and public locked wheels."""
import json
from pathlib import Path
import shutil
import stat

from .core import require, regular, no_links, read_json, atomic_json, digest, storage_volume, GIB
from .artifacts import sha256, cached, public_wheel
from .build import command
from .sources import verify_sources

BASE_MANIFEST = 'python-runtime-manifest.json'
OUTPUT_MANIFEST = 'cloud-runtime-manifest.json'

def relative(value):
    path = Path(value)
    require(path.parts and not path.is_absolute() and '..' not in path.parts,
            'Invalid Cloud input/output path')
    return path

def matches(path, row):
    path = regular(path)
    require(path.stat().st_size == row['bytes'] and sha256(path) == row['sha256'],
            'Cloud input/output digest differs')
    if 'mode' in row:
        require(stat.S_IMODE(path.stat().st_mode) == row['mode'], 'Cloud input/output mode differs')
    return path

def inventory(root, rows, extra=()):
    names = set()
    for row in rows:
        name = str(relative(row['path']))
        require(name not in names and name not in extra, 'Duplicate Cloud inventory path')
        matches(root / name, row)
        names.add(name)
    actual = set()
    for path in root.rglob('*'):
        no_links(path)
        if not path.is_dir():
            regular(path)
            actual.add(str(path.relative_to(root)))
    require(actual == names | set(extra), 'Cloud inventory differs')

def python_input(storage, kit):
    """Inspect only pinned selected inputs, not the complete retained kit."""
    kit = no_links(kit)
    volume = storage_volume(kit)
    require(volume['uuid'] == storage.volume['uuid'], 'Kit inputs must be on the selected volume')
    pin = next(row for row in storage.release.value['inputs'] if row['id'] == 'host-runtime')
    host_path = matches(kit / relative(pin['kitPath']), pin)
    host = read_json(host_path)
    rows = {row['path']: row for row in host['files']}
    require(len(rows) == len(host['files']), 'Duplicate host input path')
    subrow = rows['python/' + BASE_MANIFEST]
    base_root = host_path.parent / 'python'
    subpath = matches(base_root / BASE_MANIFEST, subrow)
    base = read_json(subpath)
    require(base.get('versionFamily') == '3.12' and base.get('sitePackagesCopied') is False
            and base.get('developmentCustomizationHooksCopied') is False, 'Python base is not isolated')
    files = []
    names = set()
    for row in base['files']:
        name = str(relative(row['path']))
        require(name not in names and name != BASE_MANIFEST, 'Duplicate Python base path')
        names.add(name)
        declared = rows['python/' + name]
        require(all(row[k] == declared[k] for k in ('bytes', 'sha256')), 'Python and host manifests disagree')
        files.append({**row, 'mode': declared['mode']})
    require(files and sum(row['bytes'] for row in files) < 512*2**20, 'Python base exceeds budget')
    files.append({**subrow, 'path': BASE_MANIFEST})
    return base_root, files, {'hostManifestSha256': pin['sha256'], 'baseManifestSha256': subrow['sha256']}

def stage_base(storage, source, rows, key):
    target = storage.path('inputs/python-base/' + key)
    marker = target.parent / (key + '.inputs.json')
    if target.exists():
        require(marker.exists() and read_json(marker) == rows, 'Unowned Python input collision')
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        atomic_json(marker, rows)
        target.mkdir(mode=0o700)
    # Only missing declared files are resumed; changed/extra files are preserved and rejected.
    for row in rows:
        storage.check(reserve=90*GIB)
        original = matches(source / row['path'], row)
        destination = no_links(target / row['path'])
        if destination.exists():
            matches(destination, row)
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        with original.open('rb') as src, destination.open('xb') as dst:
            shutil.copyfileobj(src, dst)
        destination.chmod(row['mode'])
        matches(destination, row)
    inventory(target, rows)
    return target

def verify_output(output, inputs):
    receipt = read_json(output / OUTPUT_MANIFEST)
    require(receipt.get('status') == 'ASSEMBLED_NOT_INTEGRATED'
            and receipt.get('wheelLockSha256') == inputs['wheelLockSha256']
            and receipt.get('baseManifestSha256') == inputs['pythonBase']['baseManifestSha256']
            and receipt.get('packageCount') == inputs['packageCount']
            and receipt.get('operatorCredentialsCopied') is False
            and receipt.get('runtimeSelectorsChanged') is False
            and receipt.get('externalDistributionApproved') is False,
            'Cloud owner receipt differs from inputs')
    inventory(output, receipt['files'], (OUTPUT_MANIFEST,))
    return receipt

def assemble(storage, state, kit, python, prepare_dependencies, progress):
    require(storage.profile == 'developer', 'Cloud adapter currently requires the developer profile')
    require(kit is not None, 'Specify --kit-inputs for the declared prebuilt Python base on the selected volume')
    verify_sources(storage, state)
    storage.check(additional=GIB, reserve=90*GIB)
    env = storage.environment()
    integration = storage.path('sources/integration')
    # Preserve a declared venv entry point: resolving its symlink drops packaging.
    python = Path(python).absolute()
    require(python.is_file(), 'Declared build Python is unavailable')
    toolchain = json.loads(command([python, '-I', '-B', '-c',
        'import sys, packaging, platform, json; print(json.dumps({"python":sys.version.split()[0],'
        '"packaging":packaging.__version__,"machine":platform.machine()}))'], env, storage.root))
    require(toolchain['python'].startswith('3.12.') and toolchain['machine'] == 'arm64',
            'Cloud build requires ARM64 Python 3.12 with packaging')
    owner = integration / 'scripts/distribution/cloud_worker.py'
    lock_path = integration / 'workspace/cloud-worker-wheels.lock.json'
    lock = read_json(lock_path)
    require(lock.get('python') == '3.12' and lock.get('platform') == 'macOS-arm64'
            and 0 < len(lock['packages']) <= 100, 'Invalid Cloud wheel lock')
    base_source, base_rows, base_identity = python_input(storage, kit)
    inputs = {'source': state['sources']['integration'], 'toolchain': toolchain,
              'recipeSha256': sha256(owner), 'wheelLockSha256': sha256(lock_path),
              'packageCount': len(lock['packages']), 'pythonBase': base_identity}
    key = digest(inputs)
    output = storage.path('builds/cloud-sdk/' + key)
    marker = output.parent / (key + '.inputs.json')
    if key in state['builds']:
        require(state['builds'][key] == {'target': 'cloud-sdk', 'inputs': inputs}, 'Cloud build key receipt mismatch')
        verify_output(output, inputs)
        progress('BUILD_REUSED', 'cloud-sdk')
        return key
    if output.exists():
        require(marker.exists() and read_json(marker) == inputs, 'Unowned Cloud build collision')
        verify_output(output, inputs)
    else:
        base = stage_base(storage, base_source, base_rows, base_identity['baseManifestSha256'])
        wheelhouse = storage.path('inputs/cloud-wheels/' + inputs['wheelLockSha256'])
        wheel_marker = wheelhouse.parent / (wheelhouse.name + '.inputs.json')
        if wheelhouse.exists():
            require(wheel_marker.exists() and read_json(wheel_marker) == lock, 'Unowned wheelhouse collision')
        else:
            wheelhouse.parent.mkdir(parents=True, exist_ok=True)
            atomic_json(wheel_marker, lock)
            wheelhouse.mkdir(mode=0o700)
        names = set()
        for row in lock['packages']:
            name = str(relative(row['file']))
            require(len(Path(name).parts) == 1 and name not in names, 'Invalid wheelhouse filename')
            names.add(name)
            target = no_links(wheelhouse / name)
            if target.exists():
                matches(target, row)
                continue
            cached_file = cached(storage, row)
            require(cached_file or prepare_dependencies, 'Missing wheels; use --prepare-dependencies')
            if not cached_file:
                progress('DOWNLOAD_WHEEL', row['name'])
                cached_file = public_wheel(storage, row, progress)
            with cached_file.open('rb') as src, target.open('xb') as dst:
                shutil.copyfileobj(src, dst)
            matches(target, row)
        require({p.name for p in wheelhouse.iterdir()} == names, 'Unexpected wheelhouse files')
        output.parent.mkdir(parents=True, exist_ok=True)
        atomic_json(marker, inputs)
        storage.check(additional=512*2**20, reserve=90*GIB)
        progress('BUILD_STARTED', 'cloud-sdk')
        command([python, '-B', owner, '--base', base, '--wheelhouse', wheelhouse, '--lock', lock_path,
                 '--integration', integration, '--output', output], env, storage.root, timeout=180)
        verify_output(output, inputs)
    verify_sources(storage, state)
    state['builds'][key] = {'target': 'cloud-sdk', 'inputs': inputs}
    storage.save(state)
    progress('BUILT_NOT_RUNTIME_QUALIFIED', 'cloud-sdk')
    return key
