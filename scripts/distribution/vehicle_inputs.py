# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Assemble unsigned vehicle preparation inputs; never build, sign or publish."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys

from native_bundle import BundleError, sha256
from ui_helpers import regular

CONTRACTS = (
    'vdp-compatibility-profile/vdp-compatibility-profile.v1.json',
    'qm-advisory-profile/qm-advisory-profile.v1.json',
    'brake-telemetry-window/brake-telemetry-window-profile.v1.json',
    'brake-health-model/brake-health-model-profile.v1.json',
    'brake-health-runtime/brake-health-runtime-profile.v1.json',
    'tire-health-model/tire-health-product-profile.v1.json',
)
MAX_SMALL = 256 * 2**20
DEFAULT_FACTORY_CHECKPOINT = 'workspace/checkpoints/demo-v1.1.json'


def require(condition, message):
    if not condition:
        raise BundleError(message)


def read(root, name, limit=2**20):
    path = regular(root, name)
    require(path.stat().st_size <= limit and path.stat().st_nlink == 1, 'Unsafe input size/link count')
    return path.read_bytes()


def service_inputs(artifacts, pin, product_files):
    team, profile = pin['team'], pin['profile']
    require((team == 'brake' and profile in ('v1', 'v2', 'v3')) or (team == 'tire' and profile == 'v1'),
            'Unexpected service profile')
    output = artifacts / 'services' / team / 'builds' / pin['source'] / profile / 'output'
    raw = read(output, 'product-build.json')
    product = json.loads(raw)
    require(product.get('schemaVersion') == 1 and product.get('sourceRevision') == pin['source'] and
            product.get('functionalProfile') == profile and product.get('os') == 'linux' and
            product.get('architecture') == 'arm64' and product.get('kind') == team + '-health-linux-arm64-product',
            'Service build identity mismatch')
    expected = {'rootfs/usr/bin/' + team + '-health-' + role: pin[role + 'Sha256']
                for role in ('bootstrap', 'service')}
    require(len(product['binaries']) == 2 and {r['path']: r['sha256'] for r in product['binaries']} == expected,
            'Service binary pins mismatch')
    report = read(output, 'evidence/ctest-results.xml')
    require(product['tests'].get('ctest') == 'passed' and product['tests'].get('count', 0) > 0 and
            product['tests'].get('report') == 'evidence/ctest-results.xml' and
            hashlib.sha256(report).hexdigest() == product['tests'].get('reportSha256'), 'Service test receipt mismatch')
    payload = product_files({'outputPath': str(output), 'binaries': expected}, team)
    for row in product['binaries']:
        require(len(payload[row['path'][7:]][0]) == row['size'], 'Service binary size mismatch')
    files = {'rootfs/' + name: value for name, value in payload.items()}
    files['product-build.json'] = raw, 0o444
    files['evidence/ctest-results.xml'] = report, 0o444
    return files


def collect(integration, platform, artifacts, firmware, api, *, factory_checkpoint=DEFAULT_FACTORY_CHECKPOINT):
    inventory = json.loads(read(integration, 'workspace/distribution-stage0-inventory.json'))
    # Build-time source checkpoint only: never rewrite the historical return
    # point or adopt a Factory from an adjacent self-generated receipt.
    checkpoint = json.loads(read(integration, factory_checkpoint))
    factory = checkpoint['factory']
    require(isinstance(factory, dict) and
            re.fullmatch(r'6\.1\.1-maninblack\.[0-9]+', str(factory.get('version', ''))) and
            factory.get('image') == 'main-qemuarm64.img' and factory.get('format') == 'raw' and
            type(factory.get('sizeBytes')) is int and 0 < factory['sizeBytes'] <= 16*2**30 and
            re.fullmatch('[a-f0-9]{64}', str(factory.get('sha256', ''))) and
            re.fullmatch('[a-f0-9]{40}', str(factory.get('sourceRevision', ''))),
            'Factory checkpoint identity invalid')
    manifest_path = 'factory-images/' + factory['version'] + '/manifest.json'
    manifest_raw = read(artifacts, manifest_path)
    manifest = json.loads(manifest_raw)
    info = manifest['factoryImage']
    require(info == dict(version=factory['version'], architecture='main-qemuarm64', path=factory['image'],
                         byteLength=factory['sizeBytes'], sha256=factory['sha256'], format='raw') and
            manifest['source']['revision'] == factory['sourceRevision'], 'Factory checkpoint mismatch')
    image = regular(artifacts, Path(manifest_path).parent / info['path'])
    require(image.stat().st_size == info['byteLength'] and not stat.S_IMODE(image.stat().st_mode) & 0o222,
            'Factory input must be immutable and match its size')
    firmware_pin = next(row for row in inventory['publicBinaryObservations'] if row['component'] == 'QEMU_EFI.fd')
    firmware_raw = read(firmware.parent, firmware.name, 4 * 2**20)
    require(len(firmware_raw) == firmware_pin['bytes'] and hashlib.sha256(firmware_raw).hexdigest() == firmware_pin['sha256'],
            'Firmware digest mismatch')
    files = {'factory/' + factory['version'] + '/manifest.json': (manifest_raw, 0o444),
             'firmware/QEMU_EFI.fd': (firmware_raw, 0o444)}
    inspector, builder, products = api
    vdp_rows = []
    require({row['version'] for row in inventory['unsignedVdpInputs']} == {'1.0.16', '2.0.0', '3.0.0'} and
            len(inventory['unsignedVdpInputs']) == 3, 'Incomplete VDP profile inventory')
    for pin in inventory['unsignedVdpInputs']:
        relative = 'components/vehicle-data-provider/.source-profiles/' + pin['version']
        path = regular(artifacts, relative + '/package.tar.gz')
        raw = read(artifacts, relative + '/package.tar.gz', 16 * 2**20)
        require(len(raw) == pin['bytes'] and hashlib.sha256(raw).hexdigest() == pin['sha256'], 'Unsigned VDP digest mismatch')
        source_raw = read(artifacts, relative + '/source.json')
        source = json.loads(source_raw)
        profile = next(k for k, v in builder.PROFILE_BASES.items() if v[0] == pin['version'])
        require(source == dict(schemaVersion=1, version=pin['version'], unsignedSha256=pin['sha256'],
                    legacyArchiveSha256=builder.PROFILE_BASES[profile][1], trust='REVIEWED_SOURCE_DIGESTS'),
                'VDP source receipt mismatch')
        inspection, _ = inspector._inspect(pin['version'], path)
        require(not inspection['problems'] and not inspection['signedEnvelope'] and inspection['sha256'] == pin['sha256'],
                'VDP input inspection failed')
        files['vdp/profiles/' + profile + '/package.tar.gz'] = raw, 0o444
        files['vdp/profiles/' + profile + '/source.json'] = source_raw, 0o444
        vdp_rows.append({'profile': profile, 'sourceVersion': pin['version'], 'readPaths': inspection['readPathCount']})
    runtime_pin = builder.advisory_runtime_pin()
    require(runtime_pin['revision'] == inventory['vdpPreparationSource']['commonAndAdvisoryRuntime'], 'VDP runtime pin mismatch')
    for name, raw in builder.advisory_source(platform).items():
        files['vdp/reviewed-runtime/' + name] = raw, 0o444
    files['vdp/reviewed-runtime/pin.json'] = json.dumps(runtime_pin, indent=2).encode(), 0o444
    require(len(inventory['serviceExports']) == 4 and {(r['team'], r['profile']) for r in inventory['serviceExports']} ==
            {('brake', 'v1'), ('brake', 'v2'), ('brake', 'v3'), ('tire', 'v1')}, 'Incomplete service profile inventory')
    for pin in inventory['serviceExports']:
        for name, value in service_inputs(artifacts, pin, products).items():
            files['services/' + pin['team'] + '/' + pin['profile'] + '/' + name] = value
    for contract in CONTRACTS:
        raw = read(integration, 'contracts/' + contract)
        json.loads(raw)
        files['contracts/' + contract] = raw, 0o444
    for owner, root in [('integration', integration), ('platform', platform)]:
        files['notices/' + owner + '/LICENSE'] = read(root, 'LICENSE'), 0o444
    require(sum(len(raw) for raw, _ in files.values()) <= MAX_SMALL, 'Vehicle input budget exceeded')
    return files, image, {'factory': factory, 'vdpProfiles': vdp_rows, 'runtimePin': runtime_pin,
                          'serviceProfiles': inventory['serviceExports']}


def clone_factory(source, target, expected):
    """APFS clone only: no silent full-copy fallback or existing-file overwrite."""
    require(not target.exists() and not target.is_symlink(), 'Factory output already exists')
    before = source.stat()
    subprocess.run(['/bin/cp', '-c', '-p', str(source), str(target)], check=True, capture_output=True, timeout=60)
    target.chmod(0o444)
    require(target.stat().st_size == expected['sizeBytes'] and sha256(target) == expected['sha256'], 'Factory transfer mismatch')
    after = source.stat()
    require((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) ==
            (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns), 'Factory source changed during clone')


def assemble(integration, platform, artifacts, firmware, output, api, *, factory_checkpoint=DEFAULT_FACTORY_CHECKPOINT):
    require(not output.exists() and not output.is_symlink() and output.parent.is_dir(), 'Output must be new')
    require(shutil.disk_usage(output.parent).free >= 90 * 2**30 + MAX_SMALL, 'Insufficient disk reserve')
    files, image, identities = collect(integration, platform, artifacts, firmware, api,
                                       factory_checkpoint=factory_checkpoint)
    output.mkdir(mode=0o700)
    entries = []
    for name, (raw, mode) in sorted(files.items()):
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as stream:
            stream.write(raw)
        target.chmod(mode)
        digest = hashlib.sha256(raw).hexdigest()
        require(sha256(target) == digest, 'Vehicle input copy mismatch')
        entries.append({'path': name, 'bytes': len(raw), 'sha256': digest})
    factory = identities['factory']
    relative = 'factory/' + factory['version'] + '/' + factory['image']
    clone_factory(image, output / relative, factory)
    entries.append({'path': relative, 'bytes': factory['sizeBytes'], 'sha256': factory['sha256']})
    manifest = {'schemaVersion': 1, 'status': 'ASSEMBLED_PREPARATION_INPUTS_NOT_UPLOAD_READY',
                **identities, 'files': entries, 'factoryCopyMethod': 'APFS clone, SHA-256 verified at transfer',
                'runtimeSelectorsChanged': False, 'externalDistributionApproved': False,
                'excluded': ['signed releases', 'operator credentials', 'VM overlays', 'run/model data', 'release ledgers'],
                'openGates': ['operator input selectors', 'new release preparation/signing',
                              'packaged VM boot', 'full native E2E', 'redistribution/source-offer review', 'clean Mac']}
    with (output / 'vehicle-input-manifest.json').open('x') as stream:
        json.dump(manifest, stream, indent=2)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('integration', 'platform', 'artifacts', 'firmware', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--factory-checkpoint', default=DEFAULT_FACTORY_CHECKPOINT,
                        help='Reviewed source checkpoint relative to integration; historical default is unchanged')
    args = parser.parse_args()
    # Build-time only: runtime input selectors are deliberately not changed here.
    sys.path.insert(0, str(args.integration / 'apps/demo-orchestrator/src'))
    from aosedge_demo_orchestrator.components import ComponentService
    from aosedge_demo_orchestrator import component_build
    from aosedge_demo_orchestrator.service_packages import product_files
    result = assemble(args.integration, args.platform, args.artifacts, args.firmware, args.output,
                      (ComponentService.__new__(ComponentService), component_build, product_files),
                      factory_checkpoint=args.factory_checkpoint)
    print(json.dumps({'status': result['status'], 'files': len(result['files']),
                      'bytes': sum(row['bytes'] for row in result['files'])}))


if __name__ == '__main__':
    main()
