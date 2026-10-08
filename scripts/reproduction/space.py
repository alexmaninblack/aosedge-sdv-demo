# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Read-only cache/capacity accounting; never an invented cold-build peak."""
import os
import shutil
import stat

from .core import GIB, require, digest
from . import cache, chain

# Additional GiB and reserve GiB from the existing owner guards. These are
# reservations, not upper bounds on output or shared Docker layer growth.
GUARDS = {'presenter':(2,90), 'cloud-sdk':(1,90), 'brake-backend':(2,60),
    'tire-backend':(2,60), 'backend-export':(2,60), 'brake-service':(8,90),
    'tire-service':(8,90), 'gateway':(2,90), 'preparation':(8,90),
    'host-runtime':(24,90), 'backend-inputs':(1,90), 'vm-runtime':(1,90),
    'application':(40,90), 'setup':(2,90), 'dmg':(76,90)}


def footprint(path, check):
    result = {'logicalBytes':0, 'fileReportedAllocatedBytes':0, 'files':0, 'linksNotFollowed':0}
    seen = set()
    if not path.exists():
        return result
    for parent, dirs, files in os.walk(path, followlinks=False):
        check()
        for name in dirs + files:
            item = os.path.join(parent, name)
            value = os.lstat(item)
            if stat.S_ISLNK(value.st_mode):
                result['linksNotFollowed'] += 1
            elif stat.S_ISREG(value.st_mode) and (value.st_dev, value.st_ino) not in seen:
                seen.add((value.st_dev, value.st_ino))
                result['files'] += 1
                result['logicalBytes'] += value.st_size
                result['fileReportedAllocatedBytes'] += value.st_blocks * 512
    return result


def report(storage, state, target='all', build_plan=None, donor_path=None):
    require(storage.profile in ('developer','operator'), 'Full-source capacity closure is not yet supported')
    check = lambda: storage.check(reserve=0)
    check()
    donor = cache.source(storage, donor_path) if donor_path is not None else None
    rows = cache.catalogue(storage, donor)
    local, shared, missing = [], [], []
    for key, row in rows.items():
        if cache.verified(storage.root, row, check):
            local.append(key)
        elif donor is not None and cache.verified(donor, row, check):
            shared.append(key)
        else:
            missing.append(key)
    steps = []
    if storage.profile == 'developer':
        plan = chain.read_plan(storage.release, build_plan)
        require(plan == chain.read_plan(storage.release), 'Capacity guards require the reviewed default producer plan')
        selected = plan['steps'] if target == 'all' else [{'id':target,'target':target}]
        for step in selected:
            additional, reserve = GUARDS[step['target']]
            recorded = []
            for key, receipt in state['builds'].items():
                require(digest(receipt['inputs']) == key, 'Build record identity differs')
                if receipt['target'] == step['target'] and (not step.get('functionalProfile')
                        or receipt['inputs'].get('functionalProfile') == step['functionalProfile']):
                    recorded.append(key)
            steps.append({'id':step['id'], 'additionalBytes':additional*GIB,
                          'reserveBytes':reserve*GIB, 'recordedCandidateCount':len(recorded)})
    free = shutil.disk_usage(storage.root if storage.root.exists() else storage.root.parent).free
    envelope = sum(r['additionalBytes'] for r in steps) + max((r['reserveBytes'] for r in steps), default=60*GIB)
    largest = max((r['additionalBytes']+r['reserveBytes'] for r in steps), default=60*GIB)
    return {'status':'SPACE_REPORT', 'profile':storage.profile, 'freeBytes':free,
        'cache':{'declaredObjectCount':len(rows), 'localCount':len(local), 'shareableCount':len(shared),
                 'missingCount':len(missing), 'localLogicalBytes':sum(rows[k]['bytes'] for k in local),
                 'shareableLogicalBytes':sum(rows[k]['bytes'] for k in shared),
                 'absentFromCachesLogicalBytes':sum(rows[k]['bytes'] for k in missing),
                 'cacheAbsenceIsNotMissingRetainedInput':True},
        'workspace':{name:footprint(storage.path(name), check) for name in ('sources','cache','inputs','builds','tmp')},
        'ownerGuards':steps, 'largestStepGuardBytes':largest, 'fitsLargestStepGuard':free >= largest,
        'sumOfStepReservationsBytes':envelope, 'fitsSumOfStepReservations':free >= envelope,
        'reservationSumIsNotPeak':True, 'coldBuildPeakBytes':None,
        'physicalCloneSharingMeasured':False,
        'unmeasured':['shared Docker growth', 'cold source/tool acquisition', 'cold peak and APFS unique extents'],
        'recordedCandidatesAreNotVerifiedReuse':True, 'profileReady':False, 'qualified':False}
