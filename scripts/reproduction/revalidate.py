# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Explicit content verification after remount renumbers the same external volume."""
import copy

from .core import require, read_json, atomic_json, digest, regular, external_volume
from .artifacts import sha256
from .cloud import relative, matches
from . import packaging, host, package_chain

TARGETS = {'host-runtime':host.MANIFEST, 'preparation':packaging.PREPARATION_MANIFEST,
           'vm-runtime':'vm-runtime-manifest.json', 'backend-inputs':'backend-image-manifest.json'}


def refresh(storage, state, target, progress):
    require(target in TARGETS, 'Storage revalidation requires an explicit manifest-backed input target')
    require(external_volume(storage.root)['uuid'] == storage.binding['volumeUUID'], 'Storage volume changed')
    selected = [(key,row) for key,row in state['builds'].items() if row['target'] == target]
    require(selected, 'No completed output for storage revalidation')
    refreshed, checked = 0, 0
    for key, row in selected:
        require(digest(row['inputs']) == key, 'Build key differs')
        output = storage.path('builds/'+target+'/'+key)
        path = output/'build-receipt.json' if target == 'preparation' else host.receipt_path(output)
        original = read_json(path)
        require(original['inputs'] == row['inputs'], 'Stored receipt inputs differ')
        manifest = read_json(matches(output/TARGETS[target], original['manifest']))
        candidate = copy.deepcopy(original)
        changed = False
        for name, old in original['stamps'].items():
            actual = packaging.stamp(regular(output/relative(name)))
            require(isinstance(old,list) and len(old) == 6 and actual[1:] == old[1:]
                    and actual[0] == storage.volume['device'],
                    'Output changed beyond the remount device number; preserved')
            changed |= actual[0] != old[0]
            candidate['stamps'][name] = actual
        validator = (host.verify if target == 'host-runtime' else
                     packaging.verify_preparation if target == 'preparation' else package_chain.verify)
        # Original owner validates the proposed receipt and entire inventory before mutation.
        validator(output, row['inputs'], candidate)
        if not changed:
            continue
        rows = manifest.get('files')
        if target == 'backend-inputs':
            rows = [{'path':'backends.tar', 'bytes':manifest['archiveBytes'], 'sha256':manifest['archiveSha256']}]
        require(isinstance(rows,list) and {r['path'] for r in rows} == set(original['stamps']),
                'Pinned payload inventory differs from stamps')
        progress('REVALIDATE_CONTENT', target)
        for item in rows:
            member = regular(output/relative(item['path']))
            require(member.stat().st_size == item['bytes'] and sha256(member) == item['sha256'],
                    'Revalidation payload digest differs; original receipt preserved')
            checked += 1
        storage.check(reserve=0)
        require(external_volume(output)['uuid'] == storage.binding['volumeUUID'], 'Storage volume changed')
        require(read_json(path) == original, 'Receipt changed during revalidation')
        validator(output, row['inputs'], candidate)
        audit = storage.path('builds/storage-revalidation/'+digest(original))
        audit.mkdir(parents=True, exist_ok=True)
        backup = audit/'original.json'
        if backup.exists():
            require(read_json(backup) == original, 'Storage evidence collision')
        else:
            atomic_json(backup, original)
        atomic_json(audit/'verified.json', {'volumeUUID':storage.binding['volumeUUID'],
            'buildKey':key, 'target':target, 'beforeDigest':digest(original), 'afterDigest':digest(candidate),
            'verifiedFiles':len(rows), 'payloadChanged':False})
        atomic_json(path, candidate)
        validator(output, row['inputs'])
        refreshed += 1
    return {'status':'STORAGE_REVALIDATED', 'target':target, 'refreshedReceipts':refreshed,
            'hashedFiles':checked, 'payloadChanged':False, 'profileReady':False}
