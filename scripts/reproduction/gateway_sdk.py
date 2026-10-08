# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Freeze explicit, previously accepted native build inputs on external storage."""
import argparse
import json
from pathlib import Path
import shutil

from .core import require, regular, no_links, external_volume, atomic_json, GIB
from .artifacts import sha256
from .cloud import inventory

ANCHORS = {'lib/cmake/Carla/CarlaConfig.cmake': '027e2c1e5523060f4f88f7b10513442d27a5db3ea1ba8de7f69e69fb02714558',
           'lib/libcarla-client.a': 'e5491cbf0221d840788b6243d3956bfddfb5436d950ecf2d84fcb3f52ae02933'}


def freeze(carla, openssl, output):
    carla, openssl = Path(carla).resolve(strict=True), Path(openssl).resolve(strict=True)
    output = no_links(output)
    volume = external_volume(output)
    require(not output.exists() and output.parent.is_dir(), 'SDK output must be new with existing parent')
    for name, expected in ANCHORS.items():
        require(sha256(regular(carla / name)) == expected, 'SDK differs from accepted LibCarla anchors')
    version = regular(openssl / 'include/openssl/opensslv.h').read_text()
    require('# define OPENSSL_VERSION_TEXT "OpenSSL 3.6.3 ' in version,
            'SDK requires accepted OpenSSL 3.6.3')
    for root in (carla, openssl / 'include'):
        for path in root.rglob('*'):
            no_links(path)
    selected = [('carla/' + p.relative_to(carla).as_posix(), regular(p))
                for p in sorted(carla.rglob('*')) if not p.is_dir()]
    selected += [('openssl/' + p.relative_to(openssl).as_posix(), regular(p))
                 for p in sorted((openssl / 'include').rglob('*')) if not p.is_dir()]
    selected += [('openssl/lib/' + name, regular(openssl / 'lib' / name))
                 for name in ('libssl.3.dylib', 'libcrypto.3.dylib')]
    selected.append(('openssl/LICENSE.txt', regular(openssl / 'LICENSE.txt')))
    total = sum(p.stat().st_size for _, p in selected)
    require(total < 512*2**20 and shutil.disk_usage(output.parent).free > 90*GIB + total,
            'SDK input/disk budget exceeded')
    output.mkdir(mode=0o700)
    rows = []
    for name, source in selected:
        require(Path(volume['mount']).is_mount() and output.stat().st_dev == volume['device'], 'SDK SSD disconnected')
        before = source.stat()
        value = sha256(source)
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with source.open('rb') as src, target.open('xb') as dst:
            shutil.copyfileobj(src, dst)
        target.chmod(0o444)
        after = source.stat()
        require((before.st_size, before.st_mtime_ns, before.st_ino) ==
                (after.st_size, after.st_mtime_ns, after.st_ino) and sha256(target) == value,
                'SDK input changed during transfer')
        rows.append({'path': name, 'bytes': before.st_size, 'sha256': value, 'mode': 0o444})
    manifest = {'schemaVersion': 1, 'kind': 'gateway-build-sdk', 'architecture': 'arm64',
                'libcarlaAnchors': ANCHORS, 'opensslVersion': '3.6.3', 'files': rows,
                'provenance': 'Declared prebuilt inputs; accepted LibCarla anchors, not a fresh source build',
                'externalDistributionApproved': False, 'fullSourceQualified': False}
    atomic_json(output / 'sdk-manifest.json', manifest)
    inventory(output, rows, ('sdk-manifest.json',))
    return {'status': 'SDK_FROZEN_NOT_DISTRIBUTION_QUALIFIED', 'files': len(rows), 'bytes': total,
            'manifestSha256': sha256(output / 'sdk-manifest.json')}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('carla', 'openssl', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(freeze(args.carla, args.openssl, args.output), sort_keys=True))
