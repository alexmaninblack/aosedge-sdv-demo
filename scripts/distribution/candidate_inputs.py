# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Explicit source-reviewed successor pins; never a runtime adoption mechanism."""
import hashlib
import json
import re

from installation_inputs import parse
from native_bundle import BundleError
from ui_helpers import regular

LOCKS = {
    'host-runtime': 'portable-host-launch/host-runtime.lock.json',
    'preparation-inputs': 'portable-preparation-inputs/vehicle-inputs.lock.json',
    'vm-runtime': 'portable-vm-launch/vm-runtime.lock.json',
    'cloud-runtime': 'portable-cloud-backend-inputs/cloud-runtime.lock.json',
    'backend-inputs': 'portable-cloud-backend-inputs/backend-inputs.lock.json',
}


def read(root, name):
    path = regular(root, name)
    info = path.stat()
    if info.st_nlink != 1 or info.st_mode & 0o7022 or info.st_size > 2**20:
        raise BundleError('Unsafe candidate source input')
    return path.read_bytes()


def pins(root, checkpoint, required):
    value = parse(read(root, checkpoint))
    if (not isinstance(value, dict) or set(value) != {'schemaVersion', 'kind', 'productVersion',
            'baseDefinitionSha256', 'manifests'} or value['schemaVersion'] != 1
            or value['kind'] != 'reviewed-packaging-inputs' or value['productVersion'] != '1.2.0-rc.1'
            or not isinstance(value['manifests'], dict) or not set(required) <= value['manifests'].keys()
            or not value['manifests'].keys() <= LOCKS.keys()):
        raise BundleError('Incomplete or invalid packaging checkpoint')
    definition = parse(read(root, 'workspace/releases/kit028-setup042.json'))
    base = hashlib.sha256(json.dumps(definition, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    if value['baseDefinitionSha256'] != base:
        raise BundleError('Packaging baseline differs')
    for group, pin in value['manifests'].items():
        expected = parse(read(root, 'contracts/'+LOCKS[group]))['manifest']
        if (not isinstance(pin, dict) or set(pin) != {'path', 'bytes', 'sha256'}
                or pin['path'] != expected['path'] or type(pin['bytes']) is not int
                or not 0 < pin['bytes'] <= 8*2**20 or not isinstance(pin['sha256'], str)
                or not re.fullmatch('[a-f0-9]{64}', pin['sha256'])):
            raise BundleError('Packaging manifest pin invalid')
    return value['manifests']


def locks(root, checkpoint, required):
    """Preserve every runtime contract field; substitute only reviewed manifest pins."""
    selected = pins(root, checkpoint, required)
    result = {}
    for group in required:
        value = parse(read(root, 'contracts/'+LOCKS[group]))
        value['manifest'] = selected[group]
        result[group] = (json.dumps(value, sort_keys=True, indent=2)+'\n').encode()
    return result
