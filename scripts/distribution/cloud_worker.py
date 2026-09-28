# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Build an offline Cloud Python candidate from hash-locked wheels, not a venv.

Developer build dependency: Python 3.12 with packaging. No network is used here.
This does not select a runtime, install trust, sign a package or contact Cloud.
"""

import argparse
import base64
import csv
import email
import hashlib
import io
import json
from pathlib import Path
import re
import shutil
import stat
import zipfile

from packaging.requirements import Requirement
from packaging.tags import sys_tags
from packaging.utils import canonicalize_name, parse_wheel_filename

from native_bundle import BundleError, SYSTEM, command, parse_loads, sha256
from ui_helpers import regular, safe_relative

SITE = Path('lib/python3.12/site-packages')
ADAPTERS = ('aos-prov-5-4-2-compat', 'aos_prov_5_4_2_guard.py', 'aos-prov-5.4.2-source-lock.json')
LIMIT = 512 * 2**20


def load_lock(path):
    lock = json.loads(path.read_text())
    if lock.get('schemaVersion') != 1 or lock.get('python') != '3.12' or lock.get('platform') != 'macOS-arm64':
        raise BundleError('Unsupported Cloud wheel lock')
    seen = set()
    for row in lock['packages']:
        name = row['name']
        filename = safe_relative(row['file'])
        if (name != canonicalize_name(name) or name in seen or len(filename.parts) != 1
                or not filename.name.endswith('.whl') or not re.fullmatch('[0-9a-f]{64}', row['sha256'])
                or not isinstance(row['bytes'], int) or not 0 < row['bytes'] < LIMIT
                or not row['url'].startswith('https://files.pythonhosted.org/packages/')
                or row['url'].rsplit('/', 1)[-1] != filename.name):
            raise BundleError('Invalid or duplicate Cloud wheel lock entry')
        seen.add(name)
    if not {'aos-prov', 'aos-keys', 'aos-signer'} <= seen or len(seen) > 100:
        raise BundleError('Cloud SDK roots missing or unbounded')
    return lock


def member_path(info):
    path = safe_relative(info.filename.rstrip('/'))
    mode = info.external_attr >> 16
    kind = stat.S_IFMT(mode)
    if kind not in (0, stat.S_IFREG, stat.S_IFDIR):
        raise BundleError('Wheel contains a non-regular member')
    if (path.parts[0].endswith('.data') or path.name.endswith(('.pth', '.pyc', '.pyo', '.p12', '.pfx', '.key'))
            or any(part in ('__pycache__', 'sitecustomize.py', 'usercustomize.py',
                            'sitecustomize', 'usercustomize') for part in path.parts)):
        raise BundleError('Wheel contains an unsupported layout or startup/private file')
    return path


def read_wheel(path, row):
    if path.is_symlink() or path.stat().st_size != row['bytes'] or sha256(path) != row['sha256']:
        raise BundleError('Cloud wheel size/hash mismatch')
    name, version, _, tags = parse_wheel_filename(path.name)
    if name != row['name'] or str(version) != row['version'] or not tags.intersection(sys_tags()):
        raise BundleError('Cloud wheel identity/interpreter/platform mismatch')
    with zipfile.ZipFile(path) as archive:
        members = archive.infolist()
        if len(members) > 10000 or sum(info.file_size for info in members) > LIMIT:
            raise BundleError('Wheel expansion budget exceeded')
        files = {}
        for info in members:
            relative = member_path(info)
            if info.is_dir():
                continue
            if relative in files:
                raise BundleError('Duplicate wheel member')
            files[relative] = archive.read(info)
    metadata_paths = [p for p in files if len(p.parts) == 2 and p.parts[0].endswith('.dist-info') and p.name == 'METADATA']
    if len(metadata_paths) != 1:
        raise BundleError('Wheel metadata missing or ambiguous')
    metadata_path = metadata_paths[0]
    meta = email.message_from_bytes(files[metadata_path])
    if canonicalize_name(meta['Name']) != row['name'] or meta['Version'] != row['version']:
        raise BundleError('Wheel metadata does not match lock')
    record = metadata_path.with_name('RECORD')
    if record not in files:
        raise BundleError('Wheel RECORD missing')
    recorded = set()
    for relative, digest, size in csv.reader(io.StringIO(files[record].decode())):
        relative = safe_relative(relative)
        if relative in recorded or relative not in files:
            raise BundleError('Wheel RECORD inventory mismatch')
        recorded.add(relative)
        if relative == record and not digest and not size:
            continue
        actual = base64.urlsafe_b64encode(hashlib.sha256(files[relative]).digest()).rstrip(b'=').decode()
        if digest != 'sha256=' + actual or size != str(len(files[relative])):
            raise BundleError('Wheel RECORD content mismatch')
    if recorded != set(files):
        raise BundleError('Unrecorded wheel member')
    return files, meta.get_all('Requires-Dist', [])


def check_dependencies(packages, requirements):
    rows = {row['name']: row for row in packages}
    edges = {}
    for name, dependencies in requirements.items():
        edges[name] = []
        for text in dependencies:
            requirement = Requirement(text)
            if requirement.marker and not requirement.marker.evaluate({'extra': ''}):
                continue
            dependency = canonicalize_name(requirement.name)
            if (requirement.url or requirement.extras or dependency not in rows
                    or rows[dependency]['version'] not in requirement.specifier):
                raise BundleError('Unsatisfied or unsupported Cloud dependency')
            edges[name].append(dependency)
    reached, pending = set(), ['aos-prov', 'aos-keys', 'aos-signer']
    while pending:
        name = pending.pop()
        if name not in reached:
            reached.add(name)
            pending.extend(edges.get(name, []))
    if reached != set(rows):
        raise BundleError('Unrelated package in Cloud wheelhouse')


def base_files(base):
    manifest = json.loads(regular(base, 'python-runtime-manifest.json').read_text())
    if (manifest.get('versionFamily') != '3.12' or manifest.get('sitePackagesCopied') is not False
            or manifest.get('developmentCustomizationHooksCopied') is not False):
        raise BundleError('Private Python base is not the isolated candidate')
    files = {}
    for row in manifest['files']:
        relative = safe_relative(row['path'])
        path = regular(base, relative)
        if relative in files or path.stat().st_size != row['bytes'] or sha256(path) != row['sha256']:
            raise BundleError('Private Python base receipt mismatch')
        files[relative] = path
    files[Path('python-runtime-manifest.json')] = regular(base, 'python-runtime-manifest.json')
    actual = set()
    for path in base.rglob('*'):
        if path.is_symlink():
            raise BundleError('Private Python base symlink')
        if path.is_file():
            actual.add(path.relative_to(base))
    if actual != set(files) or any(p.is_relative_to(SITE) for p in files):
        raise BundleError('Extra files in private Python base')
    return files


def native_inventory(output):
    result = []
    for path in sorted((output / SITE).rglob('*')):
        if path.suffix not in ('.so', '.dylib'):
            continue
        arches = command(['/usr/bin/lipo', '-archs', path]).split()
        if 'arm64' not in arches or not set(arches) <= {'arm64', 'x86_64'}:
            raise BundleError('Cloud native wheel has no supported arm64 slice')
        info = parse_loads(command(['/usr/bin/otool', '-arch', 'arm64', '-l', path]))
        if info['rpaths'] or any(not dep.startswith(SYSTEM) for dep in info['dependencies']):
            raise BundleError('Cloud native wheel has a non-OS dependency or rpath')
        result.append({'path': str(path.relative_to(output)), 'architectures': arches,
                       'arm64Loads': info['dependencies'], 'vendorBytesUnmodified': True})
    if not result:
        raise BundleError('Cloud native modules missing')
    return result


def assemble(base, wheelhouse, lock_path, integration, output):
    base, wheelhouse, lock_path, integration = (p.resolve(strict=True) for p in (base, wheelhouse, lock_path, integration))
    if output.exists() or output.is_symlink() or not output.parent.is_dir():
        raise BundleError('Output must be new with an existing parent')
    lock = load_lock(lock_path)
    if {p.name for p in wheelhouse.iterdir()} != {row['file'] for row in lock['packages']}:
        raise BundleError('Wheelhouse inventory differs from lock')
    sources = base_files(base)
    sources[Path('cloud-wheels.lock.json')] = lock_path
    for name in ADAPTERS:
        sources[Path('demo/scripts/host') / name] = regular(integration, Path('scripts/host') / name)
    payload, requirements = {}, {}
    expanded = sum(path.stat().st_size for path in sources.values())
    for row in lock['packages']:
        members, requires = read_wheel(wheelhouse / row['file'], row)
        expanded += sum(map(len, members.values()))
        if expanded > LIMIT:
            raise BundleError('Combined Cloud expansion budget exceeded')
        requirements[row['name']] = requires
        for relative, data in members.items():
            target = SITE / relative
            if target in payload or target in sources:
                raise BundleError('Cloud payload path collision')
            payload[target] = data
    check_dependencies(lock['packages'], requirements)
    total = sum(path.stat().st_size for path in sources.values()) + sum(map(len, payload.values()))
    if total > LIMIT or shutil.disk_usage(output.parent).free < 90 * 2**30 + total:
        raise BundleError('Disk/input-size budget exceeded')
    hashes = {relative: sha256(path) for relative, path in sources.items()}
    output.mkdir(mode=0o700)
    for relative, source in sources.items():
        target = output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        target.chmod(stat.S_IMODE(source.stat().st_mode))
        if sha256(target) != hashes[relative] or sha256(source) != hashes[relative]:
            raise BundleError('Cloud input changed during assembly')
    for relative, data in payload.items():
        target = output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as stream:
            stream.write(data)
        target.chmod(0o644)
    native = native_inventory(output)
    entries = [{'path': str(path.relative_to(output)), 'bytes': path.stat().st_size, 'sha256': sha256(path)}
               for path in sorted(output.rglob('*')) if path.is_file()]
    manifest = {'schemaVersion': 1, 'status': 'ASSEMBLED_NOT_INTEGRATED', 'files': entries,
                'packageCount': len(lock['packages']), 'nativeModules': native,
                'wheelLockSha256': sha256(lock_path), 'baseManifestSha256': sha256(base / 'python-runtime-manifest.json'),
                'operatorCredentialsCopied': False, 'runtimeSelectorsChanged': False,
                'consoleScriptsGenerated': False, 'entryPoints': ['python3.12 -I -B -m ' + n for n in ('aos_keys', 'aos_prov', 'aos_signer')],
                'adapterIntegrationDestination': 'demo/scripts/host; alongside the packaged orchestrator root',
                'externalDistributionApproved': False,
                'openGates': ['operator selectors', 'live Cloud', 'credential enrollment', 'redistribution review', 'clean Mac']}
    with (output / 'cloud-runtime-manifest.json').open('x') as stream:
        json.dump(manifest, stream, indent=2)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('base', 'wheelhouse', 'lock', 'integration', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    result = assemble(args.base, args.wheelhouse, args.lock, args.integration, args.output.absolute())
    print(json.dumps({'status': result['status'], 'packages': result['packageCount'],
                      'nativeModules': len(result['nativeModules']), 'files': len(result['files']),
                      'bytes': sum(row['bytes'] for row in result['files'])}))


if __name__ == '__main__':
    main()
