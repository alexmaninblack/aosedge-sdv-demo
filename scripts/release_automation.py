# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Deterministic release coordination with receipts and no blind mutation replay."""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
STAGES = ('freeze', 'source-gates', 'artifact', 'qualification',
          'main-integration', 'publication', 'operator-promotion')
MUTATIONS = frozenset(('main-integration', 'publication', 'operator-promotion'))


class CampaignError(RuntimeError):
    pass


def require(ok, code):
    if not ok:
        raise CampaignError(code)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def safe(path):
    path = Path(path)
    require(path.is_absolute() and '..' not in path.parts and
            not any(p.is_symlink() for p in (path, *path.parents)), 'UNSAFE_PATH')
    return path


def private_file(path):
    path = safe(path)
    info = path.stat()
    require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and
            info.st_uid == os.getuid() and stat.S_IMODE(info.st_mode) == 0o600
            and info.st_size <= 2**20, 'PRIVATE_RECORD_REQUIRED')
    return path


def pairs(items):
    result = {}
    for name, value in items:
        require(name not in result, 'DUPLICATE_JSON_FIELD')
        result[name] = value
    return result


def read(path):
    return json.loads(private_file(path).read_bytes(), object_pairs_hook=pairs)


def atomic(path, value):
    path = safe(path)
    if path.exists():
        private_file(path)
    pending = path.with_name(path.name + '.pending')
    fd = os.open(pending, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump(value, stream, sort_keys=True, indent=2)
            stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
        os.replace(pending, path)
    finally:
        if pending.exists():
            pending.unlink()


def configuration(path):
    value = read(path)
    required = {'schemaVersion', 'version', 'workspace', 'volumeUUID', 'gateway',
                'expectedMain', 'candidate', 'remoteConfig', 'operatorJourney', 'evidence', 'delivery'}
    require(isinstance(value, dict) and set(value) == required and
            type(value['schemaVersion']) is int and value['schemaVersion'] == 1,
            'CONFIG_SCHEMA_INVALID')
    require(isinstance(value['version'], str) and
            re.fullmatch(r'\d+\.\d+\.\d+-rc\.\d+', value['version']), 'VERSION_INVALID')
    for key in ('workspace', 'gateway', 'remoteConfig', 'operatorJourney'):
        safe(value[key])
    require(re.fullmatch(r'[A-Fa-f0-9-]{36}', value['volumeUUID']) is not None, 'VOLUME_ID_INVALID')
    require(set(value['expectedMain']) == {'integration', 'gateway'} and
            all(re.fullmatch('[a-f0-9]{40}', s) for s in value['expectedMain'].values()),
            'EXPECTED_MAIN_INVALID')
    require(set(value['candidate']) == {'directory', 'dmgSha256', 'manifestSha256'} and
            all(re.fullmatch('[a-f0-9]{64}', value['candidate'][k]) for k in
                ('dmgSha256', 'manifestSha256')), 'CANDIDATE_INVALID')
    safe(value['candidate']['directory'])
    require(set(value['evidence']) == {'campaign', 'closure', 'browser', 'sourcePin'} and
            re.fullmatch('[a-f0-9]{64}', value['evidence']['sourcePin']), 'EVIDENCE_INVALID')
    for key in ('campaign', 'closure', 'browser'):
        safe(value['evidence'][key])
    require(set(value['delivery']) == {'folderId', 'account'} and
            re.fullmatch(r'[A-Za-z0-9_-]{10,200}', value['delivery']['folderId']) and
            re.fullmatch(r'[A-Za-z0-9_.+@-]{3,200}', value['delivery']['account']),
            'DELIVERY_SELECTION_INVALID')
    return value


@contextmanager
def lease(root, binding):
    root = safe(root)
    root.mkdir(mode=0o700, parents=False, exist_ok=True)
    info = root.stat()
    require(info.st_uid == os.getuid() and stat.S_IMODE(info.st_mode) == 0o700,
            'RECORD_DIRECTORY_NOT_PRIVATE')
    lock = root / '.lease'
    fd = os.open(lock, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        private_file(lock)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise CampaignError('RELEASE_ALREADY_ACTIVE') from None
        marker = root / 'identity.json'
        if marker.exists():
            require(read(marker) == binding, 'CAMPAIGN_REBINDING_FORBIDDEN')
        else:
            require(set(p.name for p in root.iterdir()) == {'.lease'}, 'UNOWNED_RECORD_DIRECTORY')
            atomic(marker, binding)
        yield
    finally:
        os.close(fd)


def code(error):
    text = str(error)
    return text if re.fullmatch('[A-Z][A-Z0-9_]{1,100}', text) else 'CAMPAIGN_OPERATION_FAILED'


def execute(root, binding, owner, *, resume=False, until=None, clock=time.monotonic, emit=print):
    """The owner exposes only fixed named stages; config cannot supply commands."""
    require(until is None or until in STAGES, 'INVALID_STOP_STAGE')
    started = clock(); results = []; outcome = 'PASS'; failure = None
    with lease(root, binding):
        for name in STAGES:
            path = root / (name + '.json')
            previous = read(path) if path.exists() else None
            if previous is not None:
                require(resume, 'EXISTING_CAMPAIGN_REQUIRES_RESUME')
                try:
                    require(previous.get('stage') == name and previous.get('outcome') in
                            ('PASS','BLOCKED','UNCERTAIN'), 'SAVED_STAGE_INVALID')
                    if previous['outcome'] == 'PASS':
                        owner.verify_saved(name, previous['facts'])
                    else:
                        require(name not in MUTATIONS or owner.reconcile(name, previous),
                                'UNCERTAIN_MUTATION_REQUIRES_RECONCILIATION')
                except (Exception, KeyboardInterrupt) as error:
                    # Preserve authoritative stage evidence, but never leave a
                    # formerly green top-level report after revalidation fails.
                    atomic(root/'report.json', dict(schemaVersion=1,outcome='BLOCKED',
                        code=code(error),seconds=round(clock()-started,3),complete=False,
                        agentStepScheduling=False,stages=results,
                        notRun=list(STAGES[len(results):])))
                    raise
                if previous['outcome'] == 'PASS':
                    results.append({**previous, 'reused': True})
                    emit(f'[{len(results)}/{len(STAGES)}] {name}: verified existing result')
                    if until == name:
                        break
                    continue
            begin = clock()
            intent = dict(stage=name, outcome='UNCERTAIN', code='INTENT_RECORDED', facts={},
                          startedAt=datetime.now(timezone.utc).isoformat(), seconds=None)
            atomic(path, intent)
            emit(f'[{len(results)+1}/{len(STAGES)}] {name}: started')
            try:
                facts = owner.stage(name)
                require(isinstance(facts, dict), 'STAGE_RESPONSE_INVALID')
                row = dict(intent, outcome='PASS', code='POSTCONDITION_CONFIRMED', facts=facts,
                           seconds=round(clock()-begin, 3))
            except (Exception, KeyboardInterrupt) as error:
                status = 'UNCERTAIN' if name in MUTATIONS else 'BLOCKED'
                row = dict(intent, outcome=status, code=code(error), seconds=round(clock()-begin, 3))
                outcome = status; failure = row['code']
            atomic(path, row); results.append(row)
            emit(f'[{len(results)}/{len(STAGES)}] {name}: {row["outcome"]} ({row["seconds"]}s)')
            if row['outcome'] != 'PASS' or until == name:
                break
        complete = len(results) == len(STAGES) and all(r['outcome'] == 'PASS' for r in results)
        if outcome == 'PASS' and not complete:
            outcome = 'PARTIAL'
        report = dict(schemaVersion=1, outcome=outcome, code=failure or
                      ('RELEASE_COMPLETE' if complete else 'SELECTED_BOUNDARY_COMPLETE'),
                      seconds=round(clock()-started, 3), agentStepScheduling=False,
                      stages=results, notRun=list(STAGES[len(results):]), complete=complete)
        atomic(root / 'report.json', report)
        emit(f'Release campaign: {outcome}. Report: {root / "report.json"}')
    return report


def main(argv=None):
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('plan', 'run', 'resume'))
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--until', choices=STAGES)
    args = parser.parse_args(argv)
    try:
        selected = configuration(args.config.absolute())
        if args.mode == 'plan':
            print(json.dumps(dict(version=selected['version'], stages=STAGES,
                policy='SSD build, M1 acceptance, staging only; no changes in plan mode'), indent=2))
            return 0
        from release_owners import Owners
        owner = Owners(selected)
        binding = owner.binding()
        parent = safe(Path(selected['workspace']) / 'build/release-campaign')
        parent.mkdir(mode=0o700, exist_ok=True)
        root = parent / selected['version']
        with owner.global_lease(parent):
            result = execute(root, binding, owner, resume=args.mode == 'resume', until=args.until)
        return 0 if result['outcome'] in ('PASS', 'PARTIAL') else 2
    except (Exception, KeyboardInterrupt) as error:
        print('STOP: ' + code(error), file=sys.stderr)
        return 2
