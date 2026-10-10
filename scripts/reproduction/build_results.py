# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Seal only upstream results already verified by the canonical build adapters."""
import hashlib
import json

from .core import ROOT, require, regular, read_json
from .artifacts import sha256

MANIFESTS = {
    'host-runtime': ('host-runtime', 'host-runtime-manifest.json'),
    'preparation': ('preparation-inputs', 'vehicle-input-manifest.json'),
    'cloud-sdk': ('cloud-runtime', 'cloud-runtime-manifest.json'),
    'backend-export': ('backend-inputs', 'archive-receipt.json'),
    'backend-inputs': ('backend-inputs', 'backend-image-manifest.json'),
    'vm-runtime': ('vm-runtime', 'vm-runtime-manifest.json'),
}


def seal(storage, chosen, paths, application=None):
    manifests = {}
    for role, path in paths.items():
        if role not in MANIFESTS:
            continue
        group, name = MANIFESTS[role]
        manifest = regular(path/name)
        require(0 < manifest.stat().st_size <= 8*2**20, 'Developer manifest size invalid')
        destination = 'backend-image-manifest.json' if role == 'backend-export' else name
        manifests[group] = {'path': destination, 'bytes': manifest.stat().st_size, 'sha256': sha256(manifest)}
    release = None
    if application is not None:
        manifest = regular(application/'application-manifest.json')
        require(0 < manifest.stat().st_size <= 8*2**20, 'Developer application manifest size invalid')
        manifests = read_json(manifest)['inputs']
        release = {'schemaVersion': 1, 'label': 'AosEdge SDV Lab developer build',
                   'manifestSha256': sha256(manifest)}
    checkpoint = {'schemaVersion': 1, 'kind': 'developer-packaging-inputs', 'productVersion': '1.2.0-rc.1',
                  'baseDefinitionSha256': storage.release.key, 'manifests': manifests}
    value = {'schemaVersion': 1, 'kind': 'developer-build-results', 'checkpoint': checkpoint,
             'release': release, 'sources': storage.release.sources, 'upstreamBuilds': chosen}
    raw = (json.dumps(value, sort_keys=True, indent=2)+'\n').encode()
    key = hashlib.sha256(raw).hexdigest()
    path = storage.path('builds/developer-seals/'+key+'.json')
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        require(regular(path).read_bytes() == raw, 'Developer result seal collision')
    else:
        with path.open('xb') as stream:
            stream.write(raw)
        path.chmod(0o444)
    return path, key, checkpoint, release
