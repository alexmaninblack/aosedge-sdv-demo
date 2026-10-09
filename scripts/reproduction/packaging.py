# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Build-only packaging over retained inputs and completed component receipts."""
import json
from pathlib import Path
import re
import stat
import tempfile

from .core import ROOT, require, regular, read_json, atomic_json, digest, storage_volume, run_command, GIB
from .cloud import matches, relative as safe_relative
from .sources import git, verify_sources
from . import services
from .artifacts import sha256
from . import recipes

SERVICE_CHECKPOINT = 'workspace/checkpoints/reproduction-services-20261008.json'
FACTORY_CHECKPOINT = 'workspace/checkpoints/factory-41-candidate.json'
SOURCE_FACTORY_CHECKPOINT = 'workspace/checkpoints/factory-41-source-20261008.json'
PREPARATION_MANIFEST = 'vehicle-input-manifest.json'


def producer(storage, target='preparation', checkpoints=()):
    """The cloned root revision owns tooling; it is not a hidden sibling input."""
    env = storage.environment()
    require(not git(ROOT, ['status', '--porcelain', '--untracked-files=all'], env),
            'Commit the root checkout before producing a new package')
    revision = git(ROOT, ['rev-parse', 'HEAD'], env)
    rows = git(ROOT, ['ls-tree', '-r', '-z', 'HEAD'], env).split('\0')
    tracked = {}
    for row in rows:
        if not row:
            continue
        metadata, name = row.split('\t', 1)
        mode, kind, oid = metadata.split()
        tracked[name] = (mode, kind, oid)
    names = set(recipes.paths(ROOT, tracked, target))
    names.update(str(safe_relative(name)) for name in checkpoints)
    require(names <= tracked.keys(), 'Packaging checkpoint is not a committed source input')
    require(all(tracked[name][1] == 'blob' and tracked[name][0] in ('100644', '100755')
                for name in names), 'Recipe contains a linked or non-file input')
    # Include executable mode, not timestamps/revision/docs outside the actual closure.
    identity = {name: {'mode': tracked[name][0], 'blob': tracked[name][2]} for name in sorted(names)}
    return identity, revision


def selected_services(storage, state, pins):
    result = []
    require(len(pins) == 4 and {(r['team'], r['profile']) for r in pins} ==
            {('brake', 'v1'), ('brake', 'v2'), ('brake', 'v3'), ('tire', 'v1')},
            'Exactly four service profiles required')
    for pin in pins:
        target = pin['team'] + '-service'
        found = [(key, value) for key, value in state['builds'].items()
                 if value['target'] == target and value['inputs']['functionalProfile'] == pin['profile']
                 and value['inputs']['source']['revision'] == pin['source']]
        require(len(found) == 1, 'One verified service build required for each selected profile')
        key, value = found[0]
        require(digest(value['inputs']) == key, 'Service build key differs')
        output = storage.path('builds/' + target + '/' + key)
        services.verify_output(output, value['inputs'])
        product = read_json(output / 'product-build.json')
        expected = {'rootfs/usr/bin/' + pin['team'] + '-health-' + role: pin[role + 'Sha256']
                    for role in ('bootstrap', 'service')}
        require({r['path']: r['sha256'] for r in product['binaries']} == expected,
                'Selected service differs from reviewed checkpoint')
        result.append({'target': target, 'key': key, 'pin': pin})
    return result


def retained_preparation(storage, kit):
    require(kit is not None, 'Specify --kit-inputs for declared Factory and unsigned VDP bases')
    require(storage_volume(kit)['uuid'] == storage.volume['uuid'], 'Kit must be on the bound volume')
    pin = next(r for r in storage.release.value['inputs'] if r['id'] == 'preparation-inputs')
    path = matches(Path(kit) / pin['kitPath'], pin)
    manifest = read_json(path)
    require(manifest.get('schemaVersion') == 1 and
            manifest.get('status') == 'ASSEMBLED_PREPARATION_INPUTS_NOT_UPLOAD_READY',
            'Retained preparation manifest invalid')
    factory = read_json(ROOT / FACTORY_CHECKPOINT)['factory']
    require(manifest['factory'] == factory, 'Retained Factory differs from source checkpoint')
    names = ['firmware/QEMU_EFI.fd', 'factory/' + factory['version'] + '/manifest.json',
             'factory/' + factory['version'] + '/' + factory['image']]
    for profile in ('v1', 'v2', 'v3'):
        names += ['vdp/profiles/' + profile + '/' + name for name in ('package.tar.gz', 'source.json')]
    rows = {r['path']: r for r in manifest['files']}
    require(len(rows) == len(manifest['files']) and set(names) <= set(rows), 'Retained input inventory incomplete')
    selected = [rows[name] for name in names]
    return path.parent, selected, pin, factory


def verify_preparation(output, inputs, receipt=None):
    receipt = read_json(output / 'build-receipt.json') if receipt is None else receipt
    require(receipt.get('status') == 'ASSEMBLED_NOT_RUNTIME_QUALIFIED' and receipt.get('inputs') == inputs
            and receipt.get('signed') is False and receipt.get('published') is False,
            'Preparation build receipt differs')
    matches(output / PREPARATION_MANIFEST, receipt['manifest'])
    manifest = read_json(output / PREPARATION_MANIFEST)
    require(manifest['status'] == 'ASSEMBLED_PREPARATION_INPUTS_NOT_UPLOAD_READY'
            and manifest['factory'] == inputs['factory']
            and manifest['serviceProfiles'] == [r['pin'] for r in inputs['services']]
            and manifest['runtimeSelectorsChanged'] is False and manifest['externalDistributionApproved'] is False,
            'Preparation owner identity differs')
    # Large immutable files are hashed at creation/transfer, not each status call.
    names = {PREPARATION_MANIFEST, 'build-receipt.json'}
    require(len(receipt['stamps']) == len(manifest['files']), 'Preparation stamp inventory differs')
    for row in manifest['files']:
        name = str(safe_relative(row['path']))
        require(name not in names, 'Duplicate preparation output')
        names.add(name)
        path = regular(output / name)
        require(path.stat().st_size == row['bytes'] and
                stamp(path) == receipt['stamps'].get(name), 'Preparation output changed')
    actual = set()
    for p in output.rglob('*'):
        require(not p.is_symlink(), 'Preparation output contains link')
        if not p.is_dir():
            actual.add(p.relative_to(output).as_posix())
    require(actual == names, 'Preparation output inventory differs')
    return receipt


def stamp(path):
    s = path.stat()
    return [s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns, stat.S_IMODE(s.st_mode)]


def source_factory(storage, root):
    """Select only the independently pinned source build, never adopt a receipt."""
    require(storage_volume(root)['uuid'] == storage.volume['uuid'], 'Factory inputs must be on the bound volume')
    pin = read_json(ROOT / SOURCE_FACTORY_CHECKPOINT)
    factory = pin['factory']
    manifest_path = matches(Path(root) / safe_relative(pin['manifest']['path']), pin['manifest'])
    manifest = read_json(manifest_path)
    require(manifest['state'] == factory['manifestState'] and
            manifest['source']['revision'] == factory['sourceRevision'] and
            manifest['factoryImage'] == dict(version=factory['version'], architecture='main-qemuarm64',
                path=factory['image'], byteLength=factory['sizeBytes'], sha256=factory['sha256'], format='raw') and
            all(manifest['build'][key] == 'PASS' for key in ('targetedTests', 'packageQa', 'imageQa')) and
            manifest['build']['hostTransferSha256Matched'] is True and
            manifest['build']['mainlineQualification']['solutionRevision'] == pin['qualificationToolsRevision'],
            'Source Factory build evidence differs from reviewed checkpoint')
    image = regular(manifest_path.parent / factory['image'])
    require(image.stat().st_size == factory['sizeBytes'] and not image.stat().st_mode & 0o222,
            'Source Factory image must be immutable and match its size')
    return pin, manifest_path, image


def stage_source_factory(storage, scratch, pin, manifest, image):
    dest = scratch / 'factory-images' / pin['factory']['version']
    dest.mkdir(parents=True)
    for source in (manifest, image):
        before = stamp(source)
        result = run_command(['/bin/cp', '-c', '-p', source, dest/source.name],
                             env=storage.environment(), cwd=scratch, timeout=60)
        require(result.returncode == 0 and stamp(source) == before, 'Source Factory clone failed or changed')
        (dest/source.name).chmod(0o444)
    matches(dest / manifest.name, pin['manifest'])
    # The canonical vehicle-input owner verifies the complete image at transfer.


def stage_inputs(storage, scratch, source, rows, factory, chosen):
    for row in rows:
        original = regular(source / safe_relative(row['path']))
        require(original.stat().st_size == row['bytes'] and not original.stat().st_mode & 0o222,
                'Retained input must match size and be immutable')
        relative = row['path']
        if relative.startswith('factory/'):
            destination = scratch / 'factory-images' / Path(relative).relative_to('factory')
        elif relative.startswith('vdp/profiles/'):
            profile, name = Path(relative).parts[2:]
            version = {'v1': '1.0.16', 'v2': '2.0.0', 'v3': '3.0.0'}[profile]
            destination = scratch / 'components/vehicle-data-provider/.source-profiles' / version / name
        else:
            destination = scratch / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        before = stamp(original)
        result = run_command(['/bin/cp', '-c', '-p', original, destination],
                             env=storage.environment(), cwd=scratch, timeout=60)
        require(result.returncode == 0 and stamp(original) == before, 'Input clone failed or source changed')
        # The unchanged owner hashes the large Factory at final clone/transfer.
        if row['bytes'] <= 32*2**20:
            matches(destination, row)
    for item in chosen:
        pin = item['pin']
        src = storage.path('builds/' + item['target'] + '/' + item['key'])
        dest = scratch / 'services' / pin['team'] / 'builds' / pin['source'] / pin['profile'] / 'output'
        dest.parent.mkdir(parents=True, exist_ok=True)
        result = run_command(['/bin/cp', '-c', '-R', '-p', src, dest],
                             env=storage.environment(), cwd=scratch, timeout=60)
        require(result.returncode == 0, 'Service input clone failed')


def runtime_object(storage, state, pin, acquire, progress):
    """Fetch one declared history object without changing the prepared HEAD."""
    require(all(isinstance(pin.get(k), str) and re.fullmatch('[a-f0-9]{40}', pin[k])
                for k in ('revision', 'tree')), 'Invalid reviewed runtime object')
    checkout = storage.path('sources/vehicle-platform')
    env = storage.environment()
    probe = run_command(['git', '-C', checkout, 'cat-file', '-e', pin['revision']+'^{commit}'], env=env)
    if probe.returncode:
        require(acquire, 'Reviewed runtime Git object missing; use --prepare-dependencies')
        progress('FETCH_SOURCE_OBJECT', 'vdp-reviewed-runtime')
        git(checkout, ['fetch', '--quiet', '--depth=1', '--no-tags', 'origin', pin['revision']], env, timeout=180)
    require(git(checkout, ['rev-parse', pin['revision']+'^{tree}'], env) == pin['tree'],
            'Reviewed runtime tree differs')
    require(git(checkout, ['rev-parse', 'HEAD'], env) == state['sources']['vehicle-platform']['revision'],
            'Prepared platform revision changed')


def preparation(storage, state, kit, python, progress, prepare_dependencies=False, factory_inputs=None):
    require(storage.profile == 'developer', 'Preparation currently requires developer profile')
    verify_sources(storage, state)
    storage.check(additional=8*GIB, reserve=90*GIB)
    tooling, revision = producer(storage)
    pins = read_json(ROOT / SERVICE_CHECKPOINT)['serviceExports']
    chosen = selected_services(storage, state, pins)
    source, rows, retained_pin, factory = retained_preparation(storage, kit)
    source_selection = source_factory(storage, factory_inputs) if factory_inputs is not None else None
    if source_selection:
        factory = source_selection[0]['factory']
        rows = [row for row in rows if not row['path'].startswith('factory/')]
    runtime_pin = read_json(source / PREPARATION_MANIFEST)['runtimePin']
    runtime_object(storage, state, runtime_pin, prepare_dependencies, progress)
    python = Path(python).absolute()
    require(python.is_file(), 'Declared build Python is unavailable')
    probe = run_command([python, '-I', '-B', '-c',
        'import json,sys,platform; print(json.dumps({"python":sys.version.split()[0],"machine":platform.machine()}))'],
        env=storage.environment(), cwd=storage.root)
    require(probe.returncode == 0, 'Cannot identify build Python')
    toolchain = json.loads(probe.stdout)
    require(toolchain['machine'] == 'arm64' and tuple(map(int, toolchain['python'].split('.')[:2])) >= (3, 10),
            'Preparation requires ARM64 Python 3.10 or newer')
    inputs = {'producerTrees': tooling, 'retainedManifest': retained_pin, 'factory': factory,
              'services': chosen, 'platform': state['sources']['vehicle-platform'], 'toolchain': toolchain,
              'runtimePin': runtime_pin, 'signed': False}
    if source_selection:
        inputs['sourceFactory'] = source_selection[0]
    key = digest(inputs)
    output = storage.path('builds/preparation/' + key)
    marker = output.parent / (key + '.inputs.json')
    if key in state['builds']:
        require(state['builds'][key] == {'target': 'preparation', 'inputs': inputs}, 'Preparation build key differs')
        verify_preparation(output, inputs)
        progress('BUILD_REUSED', 'preparation')
        return key
    if output.exists():
        require(marker.exists() and read_json(marker) == inputs, 'Unowned preparation collision')
        # Owner-only completion is not promoted without transfer verification; preserve for diagnosis.
        verify_preparation(output, inputs)
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        atomic_json(marker, inputs)
        progress('BUILD_STARTED', 'preparation')
        with tempfile.TemporaryDirectory(prefix='preparation-', dir=storage.path('tmp')) as temporary:
            scratch = Path(temporary)
            stage_inputs(storage, scratch, source, rows, factory, chosen)
            if source_selection:
                stage_source_factory(storage, scratch, *source_selection)
            policy = scratch / 'offline.sb'
            policy.write_text('(version 1)\n(allow default)\n(deny network*)\n')
            worker = ROOT / 'scripts/reproduction/preparation_worker.py'
            result = run_command(['/usr/bin/sandbox-exec', '-f', policy, python, '-I', '-B', worker,
                ROOT, storage.path('sources/vehicle-platform'), scratch, output,
                SOURCE_FACTORY_CHECKPOINT if source_selection else FACTORY_CHECKPOINT, SERVICE_CHECKPOINT],
                env=storage.environment(), cwd=scratch, timeout=300)
            output.parent.joinpath(key + '.log').write_bytes((result.stdout + result.stderr)[-2**20:])
            require(result.returncode == 0, 'Preparation owner failed; inspect retained workspace log')
            storage.check(reserve=90*GIB)
        manifest = read_json(output / PREPARATION_MANIFEST)
        # Owner verifies copied bytes, Factory hash and product/VDP identities before returning.
        regular(output / PREPARATION_MANIFEST).chmod(0o444)
        atomic_json(output / 'build-receipt.json', {'status': 'ASSEMBLED_NOT_RUNTIME_QUALIFIED',
            'inputs': inputs, 'producerRevision': revision, 'signed': False, 'published': False,
            'manifest': {'path': PREPARATION_MANIFEST, 'bytes': (output / PREPARATION_MANIFEST).stat().st_size,
                         'sha256': sha256(output / PREPARATION_MANIFEST)},
            'stamps': {r['path']: stamp(regular(output / r['path'])) for r in manifest['files']}})
    verify_sources(storage, state)
    require(producer(storage)[0] == tooling, 'Producer source changed during assembly')
    verify_preparation(output, inputs)
    state['builds'][key] = {'target': 'preparation', 'inputs': inputs}
    storage.save(state)
    progress('ASSEMBLED_NOT_RUNTIME_QUALIFIED', 'preparation')
    return key
