# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Build-only native closure candidate; does not install or launch the demo."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import plistlib
import re
import shutil
import subprocess
from build_scratch import directory


class BundleError(ValueError):
    pass


LOADS = {'LC_LOAD_DYLIB', 'LC_LOAD_WEAK_DYLIB', 'LC_REEXPORT_DYLIB', 'LC_LOAD_UPWARD_DYLIB'}
SYSTEM = ('/usr/lib/', '/System/Library/')
GATEWAY_PATHS = tuple(
    ('Vehicle.OEM.' + service + '.Advisory.' + member).encode()
    for service in ('BrakeHealth', 'TireHealth')
    for member in ('Request', 'Availability', 'GatewayStatus')
)


def validate_gateway_contract(roots):
    """Reject known pre-advisory inputs; this is not functional qualification."""
    for name, source in roots.items():
        if name not in ('carla-ego-runtime', 'carla-viss-client',
                        'bin/carla-ego-runtime', 'bin/carla-viss-client'):
            continue
        if not 0 < source.stat().st_size <= 64 * 2**20:
            raise BundleError('Gateway input size outside contract')
        data = source.read_bytes()
        if any(path not in data for path in GATEWAY_PATHS):
            raise BundleError('Gateway input lacks current QM advisory contract: ' + name)


def command(arguments):
    result = subprocess.run([str(arg) for arg in arguments], capture_output=True, timeout=60)
    if result.returncode:
        raise BundleError('Tool failed: ' + str(arguments[0]) + ': ' + result.stderr.decode(errors='replace')[:800])
    return result.stdout.decode()


def parse_loads(text):
    result = {'dependencies': [], 'rpaths': [], 'id': None}
    current = None
    for line in text.splitlines():
        words = line.strip().split()
        if len(words) == 2 and words[0] == 'cmd':
            current = words[1]
        elif current in LOADS | {'LC_ID_DYLIB', 'LC_RPATH'}:
            match = re.match(r'\s*(?:name|path) (.*?) \(offset \d+\)$', line)
            if match:
                name = match.group(1)
                if current in LOADS:
                    result['dependencies'].append(name)
                elif current == 'LC_RPATH':
                    result['rpaths'].append(name)
                else:
                    result['id'] = name
    return result


def inspect(path):
    if command(['/usr/bin/lipo', '-archs', path]).strip() != 'arm64':
        raise BundleError('Input must be arm64 only: ' + str(path))
    return parse_loads(command(['/usr/bin/otool', '-l', path]))


def dependency(path, owner, allowed):
    if path.startswith(SYSTEM):
        return None
    if path.startswith('@loader_path/'):
        candidate = owner.parent / path[len('@loader_path/'):]
    elif path.startswith('/'):
        candidate = Path(path)
    else:
        raise BundleError('Unresolved load path (no fallback): ' + path)
    try:
        resolved = candidate.resolve(strict=True)
    except FileNotFoundError as error:
        raise BundleError('Missing library: ' + path) from error
    if not resolved.is_file() or not any(resolved.is_relative_to(root) for root in allowed):
        raise BundleError('Library outside explicit input roots: ' + path)
    return resolved


def plan(roots, allowed, inspector=inspect):
    nodes, destinations, pending = {}, {}, []
    for name, source in roots.items():
        parts = name.split('/')
        if (any(not re.fullmatch(r'[A-Za-z0-9_][A-Za-z0-9_.-]*', part) for part in parts)
                or any(part in ('.', '..') for part in parts)
                or len(parts) > 1 and parts[0] not in ('bin', 'lib')):
            raise BundleError('Unsafe executable name')
        source = source.resolve(strict=True)
        if not source.is_file() or source in destinations:
            raise BundleError('Duplicate or non-file executable')
        destination = Path(name) if len(parts) > 1 else Path('bin') / name
        if destination in destinations.values():
            raise BundleError('Duplicate destination')
        destinations[source] = destination
        pending.append(source)
    while pending:
        source = pending.pop()
        if source in nodes:
            continue
        info = inspector(source)
        edges = {}
        for load in info['dependencies']:
            target = dependency(load, source, allowed)
            edges[load] = target
            if target is not None and target not in destinations:
                destination = Path('lib') / target.name
                if destination in destinations.values():
                    raise BundleError('Library basename collision: ' + target.name)
                destinations[target] = destination
                pending.append(target)
        nodes[source] = dict(info, edges=edges)
    return nodes, destinations


def relative_load(owner, target):
    return '@loader_path/' + os.path.relpath(target, owner.parent)


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def entitlements(path):
    result = subprocess.run(['/usr/bin/codesign', '-d', '--entitlements', '-', '--xml', str(path)],
                            capture_output=True, timeout=30)
    # Unsigned input is allowed, but never suppress malformed signed metadata.
    if result.returncode:
        if b'code object is not signed at all' in result.stderr:
            return {}
        raise BundleError('Cannot read entitlements')
    return plistlib.loads(result.stdout) if result.stdout.strip() else {}


def verify_tree(output, destinations):
    for relative in destinations.values():
        path = output / relative
        info = inspect(path)
        if info['rpaths']:
            raise BundleError('Unexpected remaining rpath')
        for load in info['dependencies']:
            resolved = dependency(load, path, [output.resolve()])
            if resolved is not None and resolved.relative_to(output) not in destinations.values():
                raise BundleError('Load escapes packaged closure')
        command(['/usr/bin/codesign', '--verify', '--strict', path])


def collect_notices(sources, output):
    """Collect installed formula notices; not a redistribution/legal approval."""
    formulae = set()
    for source in sources:
        for parent in source.parents:
            if (parent / 'INSTALL_RECEIPT.json').is_file() and (parent / '.brew').is_dir():
                formulae.add(parent)
                break
    records = []
    for formula in sorted(formulae):
        label = formula.parent.name + '-' + formula.name
        found = []
        for path in sorted(formula.iterdir()):
            if not re.match(r'^(LICENSE|COPYING|COPYRIGHT|NOTICE|AUTHORS)([._-]|$)', path.name, re.I):
                continue
            if path.is_symlink() or not path.is_file() or path.stat().st_size > 2**21:
                continue
            destination = output / 'notices' / label / path.name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, destination)
            found.append({'path': str(destination.relative_to(output)), 'sha256': sha256(destination)})
        records.append({'formula': label, 'availableNotices': found,
                        'completeRedistributionReview': False})
    return records


def build(roots, allowed, output, provenance, minimum_free, maximum_input):
    output = output.absolute()
    if output.exists() or output.is_symlink() or not output.parent.is_dir():
        raise BundleError('Output must be new, with an existing parent')
    validate_gateway_contract(roots)
    allowed = [path.resolve(strict=True) for path in allowed]
    nodes, destinations = plan(roots, allowed)
    total = sum(path.stat().st_size for path in nodes)
    if total > maximum_input or shutil.disk_usage(output.parent).free < minimum_free + total:
        raise BundleError('Disk/input-size budget exceeded')
    if not provenance.strip():
        raise BundleError('Missing source provenance reference')
    source_meta = {path: (path.stat().st_size, path.stat().st_mtime_ns, sha256(path)) for path in nodes}
    rights = {path: entitlements(path) for path in nodes}
    output.mkdir(mode=0o700)
    (output / 'bin').mkdir()
    (output / 'lib').mkdir()
    for source, destination in destinations.items():
        (output / destination).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, output / destination)
        (output / destination).chmod(0o755)
    records = []
    for source, info in nodes.items():
        path = output / destinations[source]
        edits = []
        for load, target in info['edges'].items():
            if target is not None:
                edits += ['-change', load, relative_load(destinations[source], destinations[target])]
        for rpath in info['rpaths']:
            edits += ['-delete_rpath', rpath]
        if info['id']:
            edits += ['-id', '@rpath/' + path.name]
        if edits:
            command(['/usr/bin/install_name_tool', *edits, path])
        with directory(output.parent) as temporary:
            arguments = ['/usr/bin/codesign', '--force', '--sign', '-']
            if rights[source]:
                entitlement_file = Path(temporary) / 'entitlements.plist'
                entitlement_file.write_bytes(plistlib.dumps(rights[source]))
                arguments += ['--entitlements', entitlement_file]
            command([*arguments, path])
        if entitlements(path) != rights[source]:
            raise BundleError('Entitlement preservation failed')
        records.append({'path': str(destinations[source]), 'sourceBytes': source_meta[source][0],
                        'sourceSha256': source_meta[source][2], 'bytes': path.stat().st_size,
                        'sha256': sha256(path), 'entitlements': rights[source],
                        'loads': inspect(path)['dependencies']})
    verify_tree(output, destinations)
    for source, (size, mtime, digest) in source_meta.items():
        if source.stat().st_size != size or source.stat().st_mtime_ns != mtime or sha256(source) != digest:
            raise BundleError('Source binary changed during assembly')
    notices = collect_notices(nodes, output)
    manifest = {'schemaVersion': 1, 'status': 'STATIC_NATIVE_CLOSURE_ONLY',
                'provenance': provenance, 'architecture': 'arm64', 'signing': 'local-ad-hoc',
                'externalDistributionApproved': False, 'noticesAndSourceOffer': 'REVIEW_REQUIRED',
                'dynamicPluginsDataAndFunctionalQualification': 'NOT_COMPLETE',
                'sourceBytes': total, 'files': sorted(records, key=lambda item: item['path']),
                'dependencyNotices': notices}
    with (output / 'native-manifest.json').open('x') as stream:
        json.dump(manifest, stream, indent=2)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--executable', action='append', required=True,
                        help='name=/absolute/input or bin/lib-relative-path=/absolute/native/input')
    parser.add_argument('--library-root', action='append', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--provenance', required=True)
    parser.add_argument('--minimum-free-gib', type=float, default=90)
    parser.add_argument('--maximum-input-gib', type=float, default=1)
    args = parser.parse_args()
    roots = {}
    for entry in args.executable:
        name, separator, path = entry.partition('=')
        if not separator or name in roots or not Path(path).is_absolute():
            parser.error('Executables need distinct names and explicit absolute paths')
        roots[name] = Path(path)
    if args.minimum_free_gib < 0 or args.maximum_input_gib <= 0:
        parser.error('Invalid disk budget')
    manifest = build(roots, [Path(path) for path in args.library_root], args.output,
                     args.provenance, int(args.minimum_free_gib * 2**30), int(args.maximum_input_gib * 2**30))
    print(json.dumps({'status': manifest['status'], 'files': len(manifest['files']),
                      'sourceBytes': manifest['sourceBytes'], 'output': str(args.output)}))


if __name__ == '__main__':
    main()
