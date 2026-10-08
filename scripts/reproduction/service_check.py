# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Build-only adapter to the selected source owners' product validators."""
import json
from pathlib import Path
import runpy
import sys


def check(integration, checkout, output, team, profile, revision, epoch):
    if team not in ('brake', 'tire') or profile not in (('v1', 'v2', 'v3') if team == 'brake' else ('v1',)):
        raise ValueError('Unsupported service profile')
    sys.path.insert(0, str(integration / 'apps/demo-orchestrator/src'))
    from aosedge_demo_orchestrator.service_packages import product_files
    owner = runpy.run_path(str(checkout / 'tools' / ('build_scaffold.py' if team == 'brake' else 'build_product.py')))
    product = json.loads((output / 'product-build.json').read_text())
    prefix = 'BHS' if team == 'brake' else 'THS'
    expected = {'schemaVersion': 1, 'kind': team + '-health-linux-arm64-product',
                'sourceRevision': revision, 'sourceDateEpoch': epoch, 'functionalProfile': profile,
                'architecture': 'arm64', 'os': 'linux', 'productTarget': prefix + '_BUILD_KUKSA_RUNTIME=ON',
                'liveQualified': False}
    if any(product.get(key) != value for key, value in expected.items()):
        raise ValueError('Service product identity mismatch')
    tests = owner['inspect_test_report'](output / 'evidence/ctest-results.xml')
    if product['tests'] != tests:
        raise ValueError('Service test receipt mismatch')
    dependencies = [{'name': name, 'revision': value} for name, value in owner['DEPENDENCY_REVISIONS'].items()]
    dependencies.append({'name': 'openssl', 'version': '3.2.6', 'archiveSha256': owner['OPENSSL_ARCHIVE_SHA256']})
    if product['dependencies'] != dependencies:
        raise ValueError('Service dependency receipt mismatch')
    binaries = {row['path']: row['sha256'] for row in product['binaries']}
    if len(product['binaries']) != 2 or set(binaries) != {'rootfs/usr/bin/' + name for name in owner['PRODUCT_BINARIES']}:
        raise ValueError('Service binary inventory mismatch')
    payload = product_files({'outputPath': str(output), 'binaries': binaries}, team)
    for row in product['binaries']:
        if len(payload[row['path'][7:]][0]) != row['size']:
            raise ValueError('Service binary size mismatch')
    allowed = {'rootfs/' + name for name in payload} | {'product-build.json', 'evidence/ctest-results.xml'}
    actual = set()
    for path in output.rglob('*'):
        if path.is_symlink():
            raise ValueError('Service export contains a link')
        if path.is_file():
            if path.stat().st_nlink != 1:
                raise ValueError('Service export contains a hard link')
            actual.add(path.relative_to(output).as_posix())
    if actual != allowed:
        raise ValueError('Unexpected service export file')
    return {'status': 'OWNER_PRODUCT_CHECK_PASSED', 'team': team, 'functionalProfile': profile,
            'testCount': tests['count'], 'fileCount': len(allowed), 'liveQualified': False}


if __name__ == '__main__':
    try:
        value = check(*map(Path, sys.argv[1:4]), *sys.argv[4:7], int(sys.argv[7]))
    except Exception:
        print('Service owner validation failed; no raw exception or payload recorded', file=sys.stderr)
        raise SystemExit(1)
    print(json.dumps(value, sort_keys=True))
