# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Verify a pinned Docker OCI export offline, without loading or extracting it."""

import argparse
import base64
import gzip
import hashlib
import json
from pathlib import Path
import re
import tarfile

from native_bundle import BundleError, sha256

INDEX = 'application/vnd.oci.image.index.v1+json'
MANIFEST = 'application/vnd.oci.image.manifest.v1+json'
CONFIG = 'application/vnd.oci.image.config.v1+json'
EMPTY = 'application/vnd.oci.empty.v1+json'
LAYER = 'application/vnd.oci.image.layer.v1.tar+gzip'
ATTESTATION = 'application/vnd.in-toto+json'
MAX_ARCHIVE = 512 * 2**20
MAX_EXPANDED = 1024 * 2**20


def require(condition, reason):
    if not condition:
        raise BundleError(reason)


def hash_stream(stream, limit):
    value, size = hashlib.sha256(), 0
    for block in iter(lambda: stream.read(1024 * 1024), b''):
        size += len(block)
        require(size <= limit, 'Archive expansion exceeds budget')
        value.update(block)
    return 'sha256:' + value.hexdigest(), size


def verify(path, expected):
    require(not path.is_symlink() and path.is_file(), 'Archive must be a regular file')
    require(path.stat().st_size <= MAX_ARCHIVE, 'Archive exceeds budget')
    require(len(expected) == 2 and {r['team'] for r in expected} == {'brake', 'tire'},
            'Exactly one pinned image per team is required')
    with tarfile.open(path, 'r:') as archive:
        members, total = {}, 0
        for member in archive:
            name = member.name
            require(name not in members and len(members) < 256, 'Duplicate or excessive archive members')
            require((member.isdir() and name in ('blobs', 'blobs/sha256')) or
                    (member.isfile() and (name in ('index.json', 'manifest.json', 'oci-layout') or
                     re.fullmatch(r'blobs/sha256/[0-9a-f]{64}', name))), 'Unexpected archive member')
            total += member.size
            require(0 <= member.size <= MAX_ARCHIVE and total <= MAX_ARCHIVE, 'Archive exceeds budget')
            members[name] = member

        def read(name):
            require(name in members and members[name].isfile() and members[name].size <= 2**20,
                    'Missing or oversized archive metadata')
            with archive.extractfile(members[name]) as stream:
                return json.load(stream)

        blobs = {name for name in members if re.fullmatch(r'blobs/sha256/[0-9a-f]{64}', name)}
        for name in blobs:
            with archive.extractfile(members[name]) as stream:
                digest, size = hash_stream(stream, MAX_ARCHIVE)
            require(digest[7:] == name.split('/')[-1] and size == members[name].size, 'Blob digest mismatch')
        require(read('oci-layout') == {'imageLayoutVersion': '1.0.0'}, 'Unsupported OCI layout')
        index = read('index.json')
        require(index.get('schemaVersion') == 2 and index.get('mediaType') == INDEX, 'Invalid OCI index')
        roots = index.get('manifests', [])
        require(len(roots) == len(expected) and {r['digest'] for r in roots} ==
                {r['localImageId'] for r in expected}, 'Image identity set mismatch')
        reached = set()

        def walk(descriptor, depth=0):
            require(depth < 8 and descriptor.get('mediaType') in (INDEX, MANIFEST, CONFIG, EMPTY, LAYER, ATTESTATION),
                    'Unsupported OCI graph')
            digest = descriptor.get('digest', '')
            require(re.fullmatch(r'sha256:[0-9a-f]{64}', digest) is not None, 'Invalid OCI digest')
            name = 'blobs/sha256/' + digest[7:]
            require(name in blobs and descriptor.get('size') == members[name].size, 'OCI reference mismatch')
            if 'data' in descriptor:
                embedded = base64.b64decode(descriptor['data'], validate=True)
                require(len(embedded) == members[name].size and 'sha256:' + hashlib.sha256(embedded).hexdigest() == digest,
                        'Embedded OCI data mismatch')
            if descriptor['mediaType'] == EMPTY:
                require(read(name) == {}, 'Invalid empty OCI config')
            if name in reached:
                return
            reached.add(name)
            if descriptor['mediaType'] in (INDEX, MANIFEST):
                body = read(name)
                require(body.get('schemaVersion') == 2 and body.get('mediaType') == descriptor['mediaType'],
                        'OCI document type mismatch')
                if descriptor['mediaType'] == INDEX:
                    for child in body['manifests']:
                        walk(child, depth + 1)
                else:
                    walk(body['config'], depth + 1)
                    for child in body['layers']:
                        walk(child, depth + 1)

        for root in roots:
            walk(root)
        require(reached == blobs, 'Unreferenced blob in export')
        images, docker_rows, expanded = [], [], {}
        for pin in expected:
            body = read('blobs/sha256/' + pin['localImageId'][7:])
            candidates = [m for m in body['manifests'] if m.get('platform') == {'architecture': 'arm64', 'os': 'linux'}]
            require(len(candidates) == 1, 'Exactly one Linux/arm64 image required')
            selected = candidates[0]
            manifest = read('blobs/sha256/' + selected['digest'][7:])
            config_name = 'blobs/sha256/' + manifest['config']['digest'][7:]
            config = read(config_name)
            require((config.get('os'), config.get('architecture')) == ('linux', 'arm64'), 'Image platform mismatch')
            labels = config['config'].get('Labels', {})
            require(labels.get('org.opencontainers.image.revision') == pin['source'] and
                    labels.get('tech.aosedge.demo.team') == pin['team'], 'Image source identity mismatch')
            require(config['config'].get('User') == 'node', 'Unexpected backend runtime identity')
            layers = manifest['layers']
            require(config['rootfs'].get('type') == 'layers' and
                    len(layers) == len(config['rootfs']['diff_ids']), 'Layer count mismatch')
            layer_names = []
            for layer, expected_diff in zip(layers, config['rootfs']['diff_ids']):
                require(layer['mediaType'] == LAYER, 'Unsupported runtime layer compression')
                name = 'blobs/sha256/' + layer['digest'][7:]
                layer_names.append(name)
                if name not in expanded:
                    with archive.extractfile(members[name]) as stream, gzip.GzipFile(fileobj=stream) as decoded:
                        expanded[name] = hash_stream(decoded, MAX_EXPANDED)
                    require(sum(size for _, size in expanded.values()) <= MAX_EXPANDED, 'Total layer budget exceeded')
                require(expanded[name][0] == expected_diff, 'Expanded layer digest mismatch')
            docker_rows.append({'Config': config_name, 'Layers': layer_names})
            images.append({'team': pin['team'], 'imageId': pin['localImageId'], 'source': pin['source'],
                           'architecture': 'linux/arm64', 'layers': len(layers)})
        compatibility = read('manifest.json')
        require(len(compatibility) == len(docker_rows), 'Docker compatibility image count mismatch')
        require(all(not row.get('RepoTags') for row in compatibility), 'Export must not install mutable tags')
        require(sorted(docker_rows, key=lambda r: r['Config']) == sorted(
            ({'Config': r['Config'], 'Layers': r['Layers']} for r in compatibility), key=lambda r: r['Config']),
            'Docker/OCI manifests disagree')
    return {'schemaVersion': 1, 'status': 'OFFLINE_INTEGRITY_VERIFIED_NOT_CLEAN_ENGINE_QUALIFIED',
            'archiveBytes': path.stat().st_size, 'archiveSha256': sha256(path), 'images': images,
            'blobs': len(blobs), 'uniqueRuntimeLayers': len(expanded),
            'expandedRuntimeBytes': sum(size for _, size in expanded.values()),
            'operatorDataIncluded': False, 'externalDistributionApproved': False,
            'openGates': ['fresh Docker engine import', 'packaged operator selection', 'redistribution review']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--inventory', type=Path, required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    args = parser.parse_args()
    require(not args.receipt.exists() and not args.receipt.is_symlink(), 'Receipt must be new')
    result = verify(args.archive, json.loads(args.inventory.read_text())['backendImages'])
    with args.receipt.open('x') as stream:
        json.dump(result, stream, indent=2)
    print(json.dumps(result))


if __name__ == '__main__':
    main()
