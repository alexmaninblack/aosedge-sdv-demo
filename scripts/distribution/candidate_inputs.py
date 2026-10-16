# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Explicit source-reviewed successor pins; never a runtime adoption mechanism."""
import hashlib
import json
import re

from installation_inputs import parse
from native_bundle import BundleError
from ui_helpers import regular
from developer_inputs import DeveloperInputs

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


def checked_input(root, role):
    selected = parse(read(root, 'workspace/build-definition.json'))
    if type(selected.get('schemaVersion')) is not int or selected['schemaVersion'] != 3:
        raise BundleError('Unsupported current input definition')
    path = selected['inputs'][role]
    rows = [row for row in selected['authorities'] if row['path'] == path]
    raw = read(root, path)
    if len(rows) != 1 or hashlib.sha256(raw).hexdigest() != rows[0]['sha256']:
        raise BundleError('Current input authority digest differs')
    return parse(raw)


def pins(root, checkpoint, required):
    developer = isinstance(checkpoint, DeveloperInputs)
    value = checkpoint.value()['checkpoint'] if developer else parse(read(root, checkpoint))
    if (not isinstance(value, dict) or set(value) != {'schemaVersion', 'kind', 'productVersion',
            'baseDefinitionSha256', 'manifests'} or type(value['schemaVersion']) is not int or value['schemaVersion'] != 1
            or value['kind'] != ('developer-packaging-inputs' if developer else 'reviewed-packaging-inputs')
            or not isinstance(value['productVersion'], str) or not re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+(?:-[A-Za-z0-9.-]+)?', value['productVersion'])
            or not isinstance(value['manifests'], dict) or not set(required) <= value['manifests'].keys()
            or not value['manifests'].keys() <= LOCKS.keys()):
        raise BundleError('Incomplete or invalid packaging checkpoint')
    compatibility = checked_input(root, 'cache')
    base = compatibility['definitionDigest']
    sources = checked_input(root, 'sources')['sources']
    if value['baseDefinitionSha256'] != base:
        raise BundleError('Packaging baseline differs')
    if developer and checkpoint.value()['sources'] != {s['id']: s for s in sources}:
        raise BundleError('Developer source selection differs')
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


def setup_release(root, checkpoint):
    """Read an independent source pin before selecting any supplied kit bytes."""
    if isinstance(checkpoint, DeveloperInputs):
        pins(root, checkpoint, LOCKS)
        value = checkpoint.value()['release']
    else:
        value = parse(read(root, checkpoint))
    if (not isinstance(value, dict) or set(value) != {'schemaVersion', 'label', 'manifestSha256'}
            or type(value['schemaVersion']) is not int or value['schemaVersion'] != 1
            or not isinstance(value['label'], str) or not 0 < len(value['label']) < 120
            or not isinstance(value['manifestSha256'], str)
            or not re.fullmatch('[a-f0-9]{64}', value['manifestSha256'])):
        raise BundleError('Invalid reviewed Setup release pin')
    return value


def identity(root, checkpoint):
    if isinstance(checkpoint, DeveloperInputs):
        checkpoint.value()
        return {'kind': 'developer-build-results', 'sha256': checkpoint.key}
    return {'path': checkpoint, 'sha256': hashlib.sha256(read(root, checkpoint)).hexdigest()}
