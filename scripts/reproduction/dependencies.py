# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Immutable prebuilt simulation inputs; no compilation, installation or launch."""
import argparse
import gzip
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import tarfile
import time

from . import artifacts, delivery, gateway, host
from .core import ROOT, GIB, LabError, Release, Storage, atomic_json, digest, no_links, read_json, regular, require

SET_ID = 'carla-macos-arm64-r1'
ROLES = ('carla-runtime', 'host-support', 'gateway-sdk')
HOST = 'kit-inputs/demo-artifacts/aosedge-sdv-demo/host-runtime/'
LOCK = ROOT / 'workspace/dependencies/carla-macos-arm64-r1.lock.json'
MANIFEST = 'dependency-manifest.json'


def safe_name(name):
    require(isinstance(name, str) and name and '\\' not in name and '\x00' not in name
            and not name.startswith('/') and all(p not in ('', '.', '..') for p in name.split('/')),
            'Unsafe dependency member path')
    require(str(PurePosixPath(name)) == name, 'Noncanonical dependency member path')
    return name


def allowed(role, name):
    safe_name(name)
    prefixes = {'carla-runtime': (HOST+'simulator/', HOST+'python/'),
                'host-support': (HOST+'native/', HOST+'openssl/'),
                'gateway-sdk': ('gateway-sdk/',)}
    require(name.startswith(prefixes[role]) or
            (role == 'host-support' and name == HOST+'host-runtime-manifest.json'),
            'Member outside selected dependency role')


def rows_valid(role, rows, allow=allowed):
    require(isinstance(rows, list) and 0 < len(rows) <= 40000, 'Invalid dependency inventory')
    names = set()
    for row in rows:
        require(set(row) == {'path', 'bytes', 'sha256', 'mode'}, 'Unexpected dependency row')
        allow(role, row['path'])
        require(row['path'] not in names and type(row['bytes']) is int and row['bytes'] >= 0
                and type(row['mode']) is int and 0 <= row['mode'] <= 0o777
                and re.fullmatch('[a-f0-9]{64}', row['sha256']), 'Invalid/duplicate dependency row')
        names.add(row['path'])
    require(sum(r['bytes'] for r in rows) < 40*GIB, 'Dependency exceeds unpacked budget')


def read_lock(path, release):
    value = read_json(path)
    require(set(value) == {'schemaVersion', 'id', 'status', 'hostManifestSha256', 'sdkManifestSha256',
                          'sourceRevisions', 'compatibility', 'packages'}
            and value['schemaVersion'] == 1 and value['id'] == SET_ID
            and value['status'] == 'RETAINED_PREBUILT_PRIVATE_NOT_DISTRIBUTION_QUALIFIED', 'Invalid dependency lock')
    pin = next(r for r in release.value['inputs'] if r['id'] == 'host-runtime')
    require(value['hostManifestSha256'] == pin['sha256']
            and value['sdkManifestSha256'] == read_json(gateway.SDK_LOCK)['manifestSha256'],
            'Dependency ancestry differs from selected release')
    require(value['sourceRevisions'] == {r: release.sources[r]['revision'] for r in ('carla', 'unreal-engine')},
            'Dependency source correspondence differs')
    require(value['compatibility'] == {'os': 'macOS', 'architecture': 'arm64', 'python': '3.12',
            'map': '/Game/Carla/Maps/Town10HD_Opt', 'editorRequired': False, 'freshSourceBuild': False},
            'Unexpected dependency compatibility')
    require(set(value['packages']) == set(ROLES), 'Dependency set incomplete')
    for role, row in value['packages'].items():
        require(set(row) == {'file', 'bytes', 'sha256', 'manifestSha256', 'files', 'unpackedBytes'}
                and row['file'] == SET_ID+'-'+role+'.tar.gz'
                and type(row['bytes']) is int and 0 < row['bytes'] < 40*GIB
                and type(row['files']) is int and 0 < row['files'] <= 40000
                and type(row['unpackedBytes']) is int and 0 < row['unpackedBytes'] < 40*GIB
                and all(re.fullmatch('[a-f0-9]{64}', row[k]) for k in ('sha256', 'manifestSha256')),
                'Invalid dependency archive pin')
    return value


class CheckedReader:
    def __init__(self, stream, check):
        self.stream, self.check, self.hash = stream, check, hashlib.sha256()

    def read(self, count):
        self.check()
        data = self.stream.read(count)
        self.hash.update(data)
        return data


def pack(storage, role, members, progress, *, set_id=SET_ID, validate=rows_valid):
    """Only explicit manifest members; deterministic tar metadata and gzip header."""
    rows = [row for row, _ in members]
    require(isinstance(set_id, str) and re.fullmatch('[a-z0-9-]{1,80}', set_id), 'Invalid dependency set ID')
    validate(role, rows)
    manifest = json.dumps({'schemaVersion': 1, 'role': role, 'files': rows},
                          sort_keys=True, separators=(',', ':')).encode()
    filename = set_id+'-'+role+'.tar.gz'
    target = storage.path('exports/'+filename)
    receipt_path = target.with_suffix('.receipt.json')
    if target.exists():
        receipt = read_json(receipt_path)
        require(receipt['manifestSha256'] == hashlib.sha256(manifest).hexdigest()
                and receipt['identity'] == artifacts.identity(target), 'Existing dependency archive changed')
        progress('EXPORT_REUSED', role)
        return {k: v for k, v in receipt.items() if k != 'identity'}
    storage.check(additional=sum(r['bytes'] for r in rows)+64*2**20, reserve=90*GIB)
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_suffix('.part')
    require(not partial.exists(), 'Incomplete export preserved; inspect it before creating a replacement')
    with partial.open('xb') as output:
        os.chmod(partial, 0o600)
        with gzip.GzipFile(filename='', mode='wb', compresslevel=1, fileobj=output, mtime=0) as zipped:
            with tarfile.open(fileobj=zipped, mode='w|', format=tarfile.PAX_FORMAT) as archive:
                archive.copybufsize = 4*2**20
                info = tarfile.TarInfo(MANIFEST)
                info.size, info.mode = len(manifest), 0o600
                archive.addfile(info, io.BytesIO(manifest))
                for index, (row, source) in enumerate(members):
                    before = artifacts.identity(source)
                    require(before[0] == storage.volume['device'] and before[2] == row['bytes']
                            and stat.S_IMODE(source.stat().st_mode) == row['mode'], 'Source size/mode/volume differs')
                    info = tarfile.TarInfo(row['path'])
                    info.size, info.mode = row['bytes'], row['mode']
                    with source.open('rb') as stream:
                        reader = CheckedReader(stream, lambda: storage.check(reserve=90*GIB))
                        archive.addfile(info, reader)
                    require(reader.hash.hexdigest() == row['sha256'] and artifacts.identity(source) == before,
                            'Source digest changed or differs from retained manifest')
                    if index % 200 == 0:
                        progress('EXPORT_FILES', {'role': role, 'count': index+1})
        output.flush()
        os.fsync(output.fileno())
    expected = {'file': filename, 'bytes': partial.stat().st_size,
                'sha256': artifacts.sha256(partial, lambda: storage.check(reserve=0)),
                'manifestSha256': hashlib.sha256(manifest).hexdigest(),
                'files': len(rows), 'unpackedBytes': sum(r['bytes'] for r in rows)}
    os.rename(partial, target)
    atomic_json(receipt_path, {**expected, 'identity': artifacts.identity(target)})
    progress('EXPORTED', {'role': role, 'bytes': expected['bytes']})
    return expected


def export(storage, kit, sdk, progress):
    root, pin = host.retained(storage, kit)
    sdk_lock = gateway.sdk_input(storage, sdk)
    manifest = read_json(root/host.MANIFEST)
    groups = {role: [] for role in ROLES}
    for row in sorted(manifest['files'], key=lambda r: r['path']):
        group = row['path'].split('/')[0]
        if group not in ('simulator', 'python', 'native', 'openssl'):
            continue
        role = 'carla-runtime' if group in ('simulator', 'python') else 'host-support'
        groups[role].append(({**row, 'path': HOST+row['path']}, regular(root/row['path'])))
    p = root/host.MANIFEST
    groups['host-support'].append(({'path': HOST+host.MANIFEST, 'bytes': pin['bytes'],
        'sha256': pin['sha256'], 'mode': stat.S_IMODE(p.stat().st_mode)}, p))
    sdk = no_links(sdk)
    for row in read_json(sdk/'sdk-manifest.json')['files']:
        groups['gateway-sdk'].append(({**row, 'path': 'gateway-sdk/'+row['path']}, regular(sdk/row['path'])))
    p = sdk/'sdk-manifest.json'
    groups['gateway-sdk'].append(({'path': 'gateway-sdk/sdk-manifest.json', 'bytes': p.stat().st_size,
        'sha256': sdk_lock['manifestSha256'], 'mode': stat.S_IMODE(p.stat().st_mode)}, p))
    value = {'schemaVersion': 1, 'id': SET_ID,
        'status': 'RETAINED_PREBUILT_PRIVATE_NOT_DISTRIBUTION_QUALIFIED',
        'hostManifestSha256': pin['sha256'], 'sdkManifestSha256': sdk_lock['manifestSha256'],
        'sourceRevisions': {r: storage.release.sources[r]['revision'] for r in ('carla', 'unreal-engine')},
        'compatibility': {'os': 'macOS', 'architecture': 'arm64', 'python': '3.12',
            'map': '/Game/Carla/Maps/Town10HD_Opt', 'editorRequired': False, 'freshSourceBuild': False},
        'packages': {role: pack(storage, role, members, progress) for role, members in groups.items()}}
    path = storage.path('exported-dependencies.lock.json')
    atomic_json(path, value)
    read_lock(path, storage.release)
    return {'status': 'EXPORTED_FOR_REVIEW', 'lock': str(path)}


def unpack(storage, archive_path, role, expected, output, progress, *, validate=rows_valid):
    before = artifacts.identity(archive_path)
    require(before[2] == expected['bytes'], 'Archive size differs')
    # Caller must establish archive digest through the existing verified cache.
    stamps = {}
    with tarfile.open(archive_path, mode='r|gz') as archive:
        first = archive.next()
        require(first and first.name == MANIFEST and first.isreg() and 0 < first.size < 16*2**20,
                'Missing/bounded dependency manifest required')
        raw = archive.extractfile(first).read()
        require(hashlib.sha256(raw).hexdigest() == expected['manifestSha256'], 'Package manifest digest differs')
        manifest = json.loads(raw)
        require(set(manifest) == {'schemaVersion', 'role', 'files'} and manifest['schemaVersion'] == 1
                and manifest['role'] == role, 'Package role differs')
        rows = manifest['files']
        validate(role, rows)
        require(len(rows) == expected['files'] and sum(r['bytes'] for r in rows) == expected['unpackedBytes'],
                'Package inventory differs')
        for index, row in enumerate(rows):
            member = archive.next()
            require(member and member.isreg() and member.name == row['path'] and member.size == row['bytes']
                    and member.mode == row['mode'] and not member.sparse, 'Unsafe or unexpected archive member')
            target = no_links(output/row['path'])
            require(not target.exists(), 'Extraction collision; existing files preserved')
            target.parent.mkdir(parents=True, exist_ok=True)
            h = hashlib.sha256()
            with archive.extractfile(member) as source, target.open('xb') as dst:
                os.chmod(target, 0o600)
                total = 0
                while data := source.read(4*2**20):
                    storage.check(additional=len(data), reserve=90*GIB)
                    total += len(data)
                    require(total <= row['bytes'], 'Member exceeds pinned size')
                    h.update(data)
                    dst.write(data)
            require(total == row['bytes'] and h.hexdigest() == row['sha256'], 'Extracted member digest differs')
            target.chmod(row['mode'])
            stamps[row['path']] = artifacts.identity(target)
            if index % 200 == 0:
                progress('EXTRACT_FILES', {'role': role, 'count': index+1})
        require(archive.next() is None, 'Unexpected extra archive member')
    require(artifacts.identity(archive_path) == before, 'Archive changed during extraction')
    return stamps


def verify(storage, lock):
    key = digest(lock)
    output = storage.path('dependencies/'+key)
    receipt = read_json(output.with_suffix('.json'))
    require(set(receipt) == {'lockDigest', 'stamps'} and receipt['lockDigest'] == key,
            'Dependency receipt binding differs')
    require(len(receipt['stamps']) == sum(r['files'] for r in lock['packages'].values()), 'Dependency receipt incomplete')
    actual = set()
    for path in output.rglob('*'):
        no_links(path)
        if path.is_dir():
            continue
        name = path.relative_to(output).as_posix()
        require(artifacts.identity(path) == receipt['stamps'].get(name), 'Extracted dependency changed')
        actual.add(name)
    require(actual == set(receipt['stamps']), 'Extracted dependency inventory differs')
    return {'status': 'DEPENDENCIES_VERIFIED_NOT_PROFILE_QUALIFIED', 'kitInputs': str(output/'kit-inputs'),
            'gatewaySdk': str(output/'gateway-sdk'), 'lockDigest': key}


def prepare(storage, lock, binding, client, progress):
    require(isinstance(binding, dict), 'Invalid dependency selection')
    public = binding.get('schemaVersion') == 2
    if public:
        artifacts.public_binding(binding, digest(lock), ROLES)
    else:
        require(set(binding) == {'schemaVersion', 'lockDigest', 'folderId', 'files'}
                and binding['schemaVersion'] == 1 and binding['lockDigest'] == digest(lock)
                and set(binding['files']) == set(ROLES), 'Dependency Drive binding differs')
        folder = delivery.identifier(binding['folderId'])
        for file_id in binding['files'].values():
            delivery.identifier(file_id)
    key = digest(lock)
    output = storage.path('dependencies/'+key)
    if output.exists():
        return verify(storage, lock)
    partial = output.with_suffix('.partial')
    require(not partial.exists(), 'Incomplete extraction preserved; inspect before replacing its exact owned directory')
    archive_bytes = sum(p['bytes'] for p in lock['packages'].values()
                        if artifacts.cached(storage, p) is None)
    storage.check(additional=archive_bytes+sum(p['unpackedBytes'] for p in lock['packages'].values()), reserve=90*GIB)
    archives = {}
    for role, expected in lock['packages'].items():
        if public:
            archives[role] = artifacts.download_public(storage, binding['files'][role], expected, progress)
            continue
        if artifacts.cached(storage, expected) is None:
            require(bool(client.account), 'Missing authorized Google account for an uncached dependency')
            delivery.check_remote(client.metadata(binding['files'][role]), binding['files'][role], folder, expected)
        archives[role] = artifacts.download(storage, client, binding['files'][role], folder, expected, progress)
    partial.mkdir(parents=True)
    stamps = {}
    for role, expected in lock['packages'].items():
        found = unpack(storage, archives[role], role, expected, partial, progress)
        require(not stamps.keys() & found.keys(), 'Overlapping dependency packages')
        stamps.update(found)
    # Manifest ancestry is checked by the same frozen build consumers later.
    require(artifacts.sha256(partial/HOST/host.MANIFEST) == lock['hostManifestSha256']
            and artifacts.sha256(partial/'gateway-sdk/sdk-manifest.json') == lock['sdkManifestSha256'],
            'Restored consumer manifest differs')
    os.rename(partial, output)
    atomic_json(output.with_suffix('.json'), {'lockDigest': key, 'stamps': stamps})
    return verify(storage, lock)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('export', 'upload', 'prepare', 'verify'))
    parser.add_argument('--storage', type=Path, required=True)
    parser.add_argument('--lock', type=Path, default=LOCK)
    parser.add_argument('--binding', type=Path, help='Prepared public/private input selection; never credentials')
    parser.add_argument('--kit-inputs', type=Path)
    parser.add_argument('--gateway-sdk', type=Path)
    parser.add_argument('--folder-id')
    parser.add_argument('--account')
    parser.add_argument('--gcloud', default='gcloud')
    args = parser.parse_args(argv)
    try:
        storage = Storage(args.storage, Release(), 'developer')
        last = [0]
        def progress(stage, value):
            now = time.monotonic()
            if now-last[0] >= 15 or not stage.endswith(('BYTES', 'FILES')):
                print(json.dumps({'stage': stage, 'value': value}), flush=True)
                last[0] = now
        with storage.locked():
            if args.action == 'export':
                require(args.kit_inputs is not None and args.gateway_sdk is not None, 'Export requires explicit retained inputs')
                result = export(storage, args.kit_inputs, args.gateway_sdk, progress)
            else:
                lock = read_lock(args.lock, storage.release)
                if args.action == 'verify':
                    result = verify(storage, lock)
                else:
                    client = delivery.Client(args.gcloud, args.account)
                    if args.action == 'prepare':
                        require(args.binding is not None, 'Preparation requires an explicit input selection')
                        # A complete cache remains usable offline without an account.
                        result = prepare(storage, lock, read_json(args.binding), client, progress)
                    else:
                        require(args.account and args.folder_id, 'Upload requires explicit authorized account and private folder')
                        client.preflight(args.folder_id, {'bytes': sum(r['bytes'] for r in lock['packages'].values())})
                        files = {}
                        for role, expected in lock['packages'].items():
                            source = regular(storage.path('exports/'+expected['file']))
                            meta = delivery.upload(client, source, expected, args.folder_id,
                                storage.path('upload-'+role+'.json'), lambda: storage.check(reserve=0),
                                progress, mime_type='application/gzip')
                            files[role] = meta['id']
                        path = storage.path('uploaded-dependencies.drive.json')
                        atomic_json(path, {'schemaVersion': 1, 'lockDigest': digest(lock),
                                          'folderId': args.folder_id, 'files': files})
                        result = {'status': 'PRIVATE_DEPENDENCIES_UPLOADED', 'binding': str(path)}
        print(json.dumps(result), flush=True)
        return 0
    except (LabError, OSError, ValueError, KeyError, TypeError, tarfile.TarError) as exc:
        print(json.dumps({'status': 'DEPENDENCIES_FAILED', 'reason': str(exc) if isinstance(exc, LabError)
                          else type(exc).__name__+'; details omitted'}), flush=True)
        return 1
