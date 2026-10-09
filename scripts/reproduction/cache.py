# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Explicit cross-workspace digest-cache reuse; no acquisition or build reuse."""
import ctypes
import os
from pathlib import Path
import re

from .core import require, no_links, regular, read_json, atomic_json, storage_volume
from .artifacts import identity, sha256
from .sources import check_source


def source(storage, path):
    root = no_links(path)
    require(root != storage.root and not root.is_relative_to(storage.root)
            and not storage.root.is_relative_to(root), 'Cache workspaces must be separate')
    require(root.is_dir() and storage_volume(root)['uuid'] == storage.volume['uuid'],
            'Cache source must be on the bound volume')
    value = read_json(root/'preparation.json')
    require(isinstance(value, dict), 'Invalid cache workspace state')
    binding = value.get('binding', {})
    require(set(value) == {'binding','sources','artifacts','builds'}
            and all(isinstance(value[k], dict) for k in value)
            and type(binding.get('schemaVersion')) is int and binding['schemaVersion'] == 1
            and binding.get('volumeUUID') == storage.volume['uuid']
            and binding.get('profile') in ('developer','operator','full-source')
            and isinstance(binding.get('release'), str)
            and re.fullmatch('[a-f0-9]{64}', binding['release']), 'Invalid cache workspace binding')
    return root


def catalogue(storage, donor=None, *, allow_unprepared=False):
    """Expected hashes come from the release and its exact public source lock."""
    selected = {}
    def add(row, name):
        key, size = row.get('sha256'), row.get('bytes')
        require(isinstance(key, str) and re.fullmatch('[a-f0-9]{64}', key)
                and type(size) is int and 0 < size < 2**40, 'Invalid cache object identity')
        require(key not in selected or selected[key]['bytes'] == size, 'Conflicting cache object sizes')
        selected.setdefault(key, {'sha256':key, 'bytes':size, 'names':[]})['names'].append(name)
    for name, row in storage.release.value['artifacts'].items():
        if 'bytes' in row and 'sha256' in row and (storage.profile != 'operator' or name == 'dmg'):
            add(row, name)
    if storage.profile != 'operator':
        expected = storage.release.sources['integration']
        owner = None
        for root in (storage.root, donor):
            if root is not None and (root/'sources/integration').exists():
                candidate = no_links(root/'sources/integration')
                env = {**storage.environment(create=False), 'GIT_OPTIONAL_LOCKS':'0'}
                check_source(candidate, expected, env)
                owner = candidate
                break
        if owner is None and allow_unprepared:
            return selected
        require(owner is not None, 'Prepared exact integration source required to resolve the wheel cache')
        lock = read_json(owner/'workspace/cloud-worker-wheels.lock.json')
        require(lock.get('python') == '3.12' and lock.get('platform') == 'macOS-arm64'
                and isinstance(lock.get('packages'), list) and 0 < len(lock['packages']) <= 100,
                'Invalid selected wheel cache lock')
        for row in lock['packages']:
            add(row, 'wheel/'+row['file'])
    return selected


def verified(root, row, check):
    """Read-only inspection. Existing receipts never authorize changed bytes."""
    path = no_links(root/'cache/sha256'/row['sha256'])
    if not path.exists():
        return None
    stamp = identity(path)
    require(stamp[2] == row['bytes'], 'Cached object size differs; preserved')
    receipt = path.with_suffix('.json')
    if receipt.exists() and read_json(receipt) == {'sha256':row['sha256'], 'identity':stamp}:
        return path
    require(sha256(path, check) == row['sha256'], 'Cached object digest differs; preserved')
    return path


def clone(source_path, target):
    """Direct clonefile: no regular-copy fallback, no existing-file overwrite."""
    regular(source_path); no_links(target)
    require(not target.exists(), 'Cache clone target already exists')
    api = ctypes.CDLL('/usr/lib/libSystem.B.dylib', use_errno=True).clonefile
    api.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
    api.restype = ctypes.c_int
    require(api(os.fsencode(source_path), os.fsencode(target), 1) == 0,
            'APFS cache clone failed; no full-copy fallback')


def transfer(storage, original, row):
    check = lambda: storage.check(reserve=0)
    destination = storage.path('cache/sha256/'+row['sha256'])
    temporary = destination.with_suffix('.reuse')
    marker = temporary.with_suffix('.reuse.json')
    expected = {'schemaVersion':1, 'sha256':row['sha256'], 'bytes':row['bytes']}
    storage.check()  # Clones share data, but never waive the normal free-space reserve.
    destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if marker.exists():
        require(read_json(marker) == expected, 'Cache transfer marker differs')
    else:
        require(not temporary.exists(), 'Unowned cache transfer preserved')
        atomic_json(marker, expected)
    before = identity(original)
    if not temporary.exists():
        clone(original, temporary)
    require(regular(temporary).stat().st_dev == storage.volume['device']
            and temporary.stat().st_size == row['bytes']
            and sha256(temporary, check) == row['sha256'], 'Cache transfer digest differs; preserved')
    require(identity(original) == before, 'Cache source changed during transfer; preserved')
    temporary.chmod(0o444)
    with temporary.open('rb') as stream:
        os.fsync(stream.fileno())
    check()
    require(not no_links(destination).exists(), 'Cache destination appeared; no overwrite')
    os.rename(temporary, destination)
    atomic_json(destination.with_suffix('.json'), {'sha256':row['sha256'], 'identity':identity(destination)})
    marker.unlink()
    return destination


def reuse(storage, donor_path, progress):
    donor = source(storage, donor_path)
    rows = catalogue(storage, donor)
    result = {'status':'CACHE_REUSE_COMPLETE', 'imported':0, 'reused':0, 'missing':[],
              'importedLogicalBytes':0, 'method':'APFS clonefile', 'downloadedBytes':0,
              'profileReady':False, 'qualified':False}
    check = lambda: storage.check(reserve=0)
    for key, row in rows.items():
        if verified(storage.root, row, check):
            result['reused'] += 1
            continue
        original = verified(donor, row, check)
        if original is None:
            result['missing'].append(key)
            continue
        transfer(storage, original, row)
        result['imported'] += 1
        result['importedLogicalBytes'] += row['bytes']
        progress('CACHE_CLONED', key[:12])
    if result['missing']:
        result['status'] = 'CACHE_REUSE_PARTIAL'
    return result
