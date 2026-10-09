# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Acquire the declared source-Factory developer inputs, without an installed kit."""
import argparse
import json
import os
from pathlib import Path
import re
import stat
import tarfile
import time

from . import artifacts, dependencies as sim, delivery, packaging
from .cloud import matches
from .core import (ROOT, GIB, LabError, Release, Storage, atomic_json, digest,
                   storage_volume, no_links, read_json, regular, require)

SET_ID = 'developer-factory41-r1'
ROLES = ('vehicle-bases', 'factory-image')
LOCK = ROOT/'workspace/dependencies/developer-factory41-r1.lock.json'
PREFIX = 'kit-inputs/demo-artifacts/aosedge-sdv-demo/'
PREP = PREFIX+'preparation-inputs/'
VM = PREFIX+'vm-runtime/'
FACTORY = 'factory-inputs/factory-images/6.1.1-maninblack.41/'
PREP_FILES = ('firmware/QEMU_EFI.fd', *(
    f'vdp/profiles/{profile}/{name}' for profile in ('v1', 'v2', 'v3')
    for name in ('package.tar.gz', 'source.json')))
VM_FILES = ('share/qemu/efi-virtio.rom', 'notices/qemu/LICENSE', 'notices/qemu/COPYING')
NAMES = {
    'vehicle-bases': {PREP+packaging.PREPARATION_MANIFEST, VM+'vm-runtime-manifest.json',
                     *(PREP+n for n in PREP_FILES), *(VM+n for n in VM_FILES)},
    'factory-image': {FACTORY+'manifest.json', FACTORY+'main-qemuarm64.img'}}


def allowed(role, name):
    sim.safe_name(name)
    require(role in NAMES and name in NAMES[role], 'Member outside declared build input closure')


def rows_valid(role, rows):
    sim.rows_valid(role, rows, allow=allowed)
    require({r['path'] for r in rows} == NAMES[role], 'Incomplete build input inventory')
    require(all(not r['mode'] & 0o222 for r in rows), 'Build input must be immutable')


def ancestry(release):
    return {'definitionDigest': release.key,
            'simulationLockSha256': artifacts.sha256(sim.LOCK),
            'factoryCheckpointSha256': artifacts.sha256(ROOT/packaging.SOURCE_FACTORY_CHECKPOINT),
            'retainedManifests': {r['id']: r for r in release.value['inputs']
                                  if r['id'] in ('preparation-inputs', 'vm-runtime')}}


def read_lock(path, release):
    value = read_json(path)
    expected = ancestry(release)
    require(set(value) == {'schemaVersion', 'id', 'status', 'packages', *expected}
            and value['schemaVersion'] == 1 and value['id'] == SET_ID
            and value['status'] == 'PRIVATE_BUILD_INPUTS_NOT_PROFILE_QUALIFIED'
            and all(value[k] == v for k, v in expected.items()), 'Build input ancestry differs')
    require(set(value['packages']) == set(ROLES), 'Build input package set differs')
    for role, row in value['packages'].items():
        require(set(row) == {'file', 'bytes', 'sha256', 'manifestSha256', 'files', 'unpackedBytes'}
                and row['file'] == SET_ID+'-'+role+'.tar.gz'
                and type(row['bytes']) is int and 0 < row['bytes'] < 12*GIB
                and type(row['unpackedBytes']) is int and 0 < row['unpackedBytes'] < 12*GIB
                and row['files'] == len(NAMES[role])
                and all(isinstance(row[k], str) and re.fullmatch('[a-f0-9]{64}', row[k])
                        for k in ('sha256', 'manifestSha256')), 'Invalid build input package pin')
    return value


def member(path, name, expected=None):
    path = regular(path)
    mode = stat.S_IMODE(path.stat().st_mode)
    require(not mode & 0o222, 'Export input must be immutable')
    if expected is not None:
        matches(path, expected)
    return ({'path':name, 'bytes':path.stat().st_size,
             'sha256':expected['sha256'] if expected else artifacts.sha256(path), 'mode':mode}, path)


def immutable_manifest(storage, source, expected):
    """Snapshot small mutable producer metadata, without changing its owner."""
    source = matches(source, expected)
    require(source.stat().st_size < 16*2**20, 'Manifest exceeds bounded metadata size')
    target = storage.path('export-metadata/'+expected['sha256']+'.json')
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as stream:
            os.chmod(target, 0o600)
            stream.write(source.read_bytes())
        matches(target, expected)
        target.chmod(0o444)
    matches(target, expected)
    require(not target.stat().st_mode & 0o222, 'Export metadata snapshot changed')
    return target


def export(storage, kit, factory, progress):
    require(storage_volume(kit)['uuid'] == storage.volume['uuid'], 'Kit is not on bound volume')
    pins = ancestry(storage.release)
    members = []
    for role, names, prefix in (('preparation-inputs', PREP_FILES, PREP), ('vm-runtime', VM_FILES, VM)):
        pin = pins['retainedManifests'][role]
        path = matches(Path(kit)/pin['kitPath'], pin)
        value = read_json(path)
        rows = {r['path']: r for r in value['files']}
        require(len(rows) == len(value['files']) and set(names) <= rows.keys(), 'Retained inputs incomplete')
        members.append(member(path, prefix+path.name, pin))
        members.extend(member(path.parent/n, prefix+n, rows[n]) for n in names)
    source_pin, manifest, image = packaging.source_factory(storage, factory)
    # Export hashes the image during packing. Small manifest was checked by its owner.
    fm = member(immutable_manifest(storage, manifest, source_pin['manifest']),
                FACTORY+'manifest.json', source_pin['manifest'])
    fi = ({'path':FACTORY+'main-qemuarm64.img', 'bytes':source_pin['factory']['sizeBytes'],
           'sha256':source_pin['factory']['sha256'], 'mode':stat.S_IMODE(image.stat().st_mode)}, image)
    value = {'schemaVersion':1, 'id':SET_ID, 'status':'PRIVATE_BUILD_INPUTS_NOT_PROFILE_QUALIFIED',
             **pins, 'packages': {role: sim.pack(storage, role, sorted(rows, key=lambda r:r[0]['path']), progress,
                 set_id=SET_ID, validate=rows_valid)
                 for role, rows in (('vehicle-bases', members), ('factory-image', [fm, fi]))}}
    path = storage.path('exported-build-inputs.lock.json')
    atomic_json(path, value)
    read_lock(path, storage.release)
    return {'status':'BUILD_INPUTS_EXPORTED_FOR_REVIEW', 'lock':str(path)}


def binding(value, lock, roles):
    require(set(value) == {'schemaVersion', 'lockDigest', 'folderId', 'files'}
            and value['schemaVersion'] == 1 and value['lockDigest'] == digest(lock)
            and set(value['files']) == set(roles), 'Build input Drive binding differs')
    delivery.identifier(value['folderId'])
    for ident in value['files'].values():
        delivery.identifier(ident)
    return value


def combined(lock, simulation):
    return {'buildInputs': lock, 'simulation': simulation}


def consumers(storage, root, lock):
    """Check the same small authorities required by the frozen build owners."""
    for pin in lock['retainedManifests'].values():
        matches(root/'kit-inputs'/pin['kitPath'], pin)
    simulation = sim.read_lock(sim.LOCK, storage.release)
    require(artifacts.sha256(root/sim.HOST/'host-runtime-manifest.json') == simulation['hostManifestSha256']
            and artifacts.sha256(root/'gateway-sdk/sdk-manifest.json') == simulation['sdkManifestSha256'],
            'Restored simulation consumer pins differ')
    packaging.source_factory(storage, root/'factory-inputs')


def verify(storage, lock, simulation):
    key = digest(combined(lock, simulation))
    output = storage.path('build-inputs/'+key)
    receipt = read_json(output.with_suffix('.json'))
    require(set(receipt) == {'inputDigest', 'stamps'} and receipt['inputDigest'] == key,
            'Build input receipt differs')
    packages = {**simulation['packages'], **lock['packages']}
    require(len(receipt['stamps']) == sum(p['files'] for p in packages.values()), 'Build input receipt incomplete')
    actual = set()
    for path in output.rglob('*'):
        no_links(path)
        if not path.is_dir():
            name = path.relative_to(output).as_posix()
            require(artifacts.identity(path) == receipt['stamps'].get(name), 'Prepared build input changed')
            actual.add(name)
    require(actual == set(receipt['stamps']), 'Prepared build input inventory differs')
    consumers(storage, output, lock)
    return {'status':'BUILD_INPUTS_READY_NOT_PROFILE_QUALIFIED', 'inputDigest':key,
            'kitInputs':str(output/'kit-inputs'), 'gatewaySdk':str(output/'gateway-sdk'),
            'factoryInputs':str(output/'factory-inputs'), 'files':len(actual), 'profileReady':False}


def prepare(storage, lock, simulation, bindings, client, progress):
    binding(bindings['buildInputs'], lock, ROLES)
    binding(bindings['simulation'], simulation, sim.ROLES)
    key = digest(combined(lock, simulation))
    output = storage.path('build-inputs/'+key)
    if output.exists():
        return verify(storage, lock, simulation)
    partial = output.with_suffix('.partial')
    require(not partial.exists(), 'Incomplete build input extraction preserved; inspect before retry')
    packages = {**simulation['packages'], **lock['packages']}
    needed = sum(p['bytes'] for p in packages.values() if artifacts.cached(storage, p) is None)
    storage.check(additional=needed+sum(p['unpackedBytes'] for p in packages.values()), reserve=90*GIB)
    archives = {}
    for role, expected in packages.items():
        selected = bindings['simulation' if role in sim.ROLES else 'buildInputs']
        file_id, folder = selected['files'][role], selected['folderId']
        if artifacts.cached(storage, expected) is None:
            require(bool(client.account), 'Missing authorized Google account for uncached build inputs')
            delivery.check_remote(client.metadata(file_id), file_id, folder, expected)
        archives[role] = artifacts.download(storage, client, file_id, folder, expected, progress)
    partial.mkdir(parents=True)
    stamps = {}
    for role, expected in packages.items():
        rows = sim.unpack(storage, archives[role], role, expected, partial, progress,
                          validate=sim.rows_valid if role in sim.ROLES else rows_valid)
        require(not stamps.keys() & rows.keys(), 'Overlapping build input packages')
        stamps.update(rows)
    consumers(storage, partial, lock)
    os.rename(partial, output)
    atomic_json(output.with_suffix('.json'), {'inputDigest':key, 'stamps':stamps})
    return verify(storage, lock, simulation)


def upload(storage, lock, client, folder, progress):
    client.preflight(folder, {'bytes':sum(p['bytes'] for p in lock['packages'].values())})
    files = {}
    for role, expected in lock['packages'].items():
        meta = delivery.upload(client, regular(storage.path('exports/'+expected['file'])), expected, folder,
            storage.path('upload-'+role+'.json'), lambda: storage.check(reserve=0), progress,
            mime_type='application/gzip')
        files[role] = meta['id']
    value = {'schemaVersion':1, 'lockDigest':digest(lock), 'folderId':folder, 'files':files}
    path = storage.path('uploaded-build-inputs.drive.json')
    atomic_json(path, value)
    return {'status':'PRIVATE_BUILD_INPUTS_UPLOADED', 'binding':str(path)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('export', 'upload', 'prepare', 'verify', 'plan'))
    parser.add_argument('--storage', type=Path)
    parser.add_argument('--lock', type=Path, default=LOCK)
    parser.add_argument('--binding', type=Path)
    parser.add_argument('--simulation-binding', type=Path)
    parser.add_argument('--kit-inputs', type=Path)
    parser.add_argument('--factory-inputs', type=Path)
    parser.add_argument('--account')
    parser.add_argument('--folder-id')
    parser.add_argument('--gcloud', default='gcloud')
    args = parser.parse_args(argv)
    try:
        release = Release()
        lock = read_lock(args.lock, release) if args.action != 'export' else None
        simulation = sim.read_lock(sim.LOCK, release)
        if args.action == 'plan':
            rows = {**simulation['packages'], **lock['packages']}
            print(json.dumps({'status':'BUILD_INPUT_PLAN', 'packages':list(rows),
                'archiveBytes':sum(p['bytes'] for p in rows.values()),
                'unpackedBytes':sum(p['unpackedBytes'] for p in rows.values()),
                'reserveGiB':90, 'profileReady':False}), flush=True)
            return 0
        require(args.storage is not None, 'Explicit storage directory required')
        storage = Storage(args.storage, release, 'developer')
        last = [0]
        def progress(stage, value):
            now = time.monotonic()
            if now-last[0] >= 15 or not stage.endswith(('BYTES', 'FILES')):
                print(json.dumps({'stage':stage, 'value':value}), flush=True)
                last[0] = now
        with storage.locked():
            if args.action == 'export':
                require(args.kit_inputs is not None and args.factory_inputs is not None, 'Explicit export sources required')
                result = export(storage, args.kit_inputs, args.factory_inputs, progress)
            elif args.action == 'verify':
                result = verify(storage, lock, simulation)
            else:
                client = delivery.Client(args.gcloud, args.account)
                if args.action == 'upload':
                    require(args.account and args.folder_id, 'Explicit authorized account and private folder required')
                    result = upload(storage, lock, client, args.folder_id, progress)
                else:
                    require(args.binding is not None and args.simulation_binding is not None, 'Both private bindings required')
                    result = prepare(storage, lock, simulation, {'buildInputs':read_json(args.binding),
                        'simulation':read_json(args.simulation_binding)}, client, progress)
        print(json.dumps(result), flush=True)
        return 0
    except (LabError, OSError, ValueError, KeyError, TypeError, tarfile.TarError) as exc:
        print(json.dumps({'status':'BUILD_INPUTS_FAILED', 'reason':str(exc) if isinstance(exc, LabError)
                         else type(exc).__name__+'; details omitted'}), flush=True)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
