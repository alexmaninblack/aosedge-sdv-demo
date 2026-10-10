#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Resumable, test-only qualification. Product owners remain authoritative."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import stat
import sys
import threading
import time
from uuid import uuid4

import remote_harness as h
from journey_plan import plan, evaluate, resolve, MUTATIONS, CONTINUOUS_GROUPS

HERE = Path(__file__).resolve().parent
WORKER = HERE / 'journey_worker.py'
DOMAIN = 'aws-stage.epmp-aos.projects.epam.com'
FIELDS = {'schemaVersion', 'manifestSha256', 'packageRoot', 'instanceRoot',
          'setupApp', 'setupSha256', 'sourceRoot', 'storeRoot', 'image',
          'oemCertificate', 'spCertificate', 'records'}
OPTIONAL_FIELDS = {'subjectReferences', 'vmPasswordFile'}


def configuration(path, user):
    path = h.unlinked(path)
    info = path.stat()
    h.require(info.st_uid == os.getuid() and stat.S_IMODE(info.st_mode) == 0o600
              and info.st_size < 16384, 'JOURNEY_CONFIG_NOT_PRIVATE')
    value = h.parse(path.read_bytes())
    h.require(isinstance(value, dict) and FIELDS <= set(value) <= FIELDS | OPTIONAL_FIELDS and value['schemaVersion'] == 1,
              'JOURNEY_CONFIG_INVALID')
    references = value.get('subjectReferences', [])
    h.require(isinstance(references, list) and len(references) <= 2, 'SUBJECT_REFERENCES_INVALID')
    teams = set()
    for reference in references:
        h.require(isinstance(reference, dict) and set(reference) ==
            {'team','ownerId','serviceProviderId','id','serviceId','createdBy'}, 'SUBJECT_REFERENCE_INVALID')
        h.require(reference['team'] in ('brake','tire') and reference['team'] not in teams,
                  'SUBJECT_REFERENCE_TEAM_INVALID')
        teams.add(reference['team'])
        from uuid import UUID
        for key in set(reference) - {'team'}:
            h.require(str(UUID(reference[key])) == reference[key], 'SUBJECT_REFERENCE_ID_INVALID')
    for key in ('manifestSha256', 'setupSha256'):
        h.require(isinstance(value[key], str) and re.fullmatch('[a-f0-9]{64}', value[key]), 'PIN_INVALID')
    for key in FIELDS - {'schemaVersion', 'manifestSha256', 'setupSha256', 'image'}:
        raw = value[key]
        h.require(isinstance(raw, str) and raw.startswith('/') and '..' not in Path(raw).parts
                  and str(Path(raw)) == raw and not any(ord(c) < 32 for c in raw), 'PATH_INVALID')
    home = Path('/Users') / user
    if 'vmPasswordFile' in value:
        raw = value['vmPasswordFile']
        h.require(isinstance(raw, str) and raw.startswith('/') and '..' not in Path(raw).parts
                  and str(Path(raw)) == raw and not any(ord(c) < 32 for c in raw)
                  and Path(raw).is_relative_to(home) and Path(raw) != home,
                  'VM_ACCESS_PATH_INVALID')
    for key in ('packageRoot', 'instanceRoot', 'storeRoot', 'oemCertificate', 'spCertificate'):
        p = Path(value[key])
        h.require(p.is_relative_to(home) and p != home, 'TARGET_OUTSIDE_HOME')
    store, state = Path(value['storeRoot']), Path(value['instanceRoot'])
    h.require(not store.is_relative_to(state) and not state.is_relative_to(store), 'STATE_STORE_OVERLAP')
    h.require(Path(value['packageRoot']) == store / 'versions' / value['manifestSha256'], 'PACKAGE_PIN_MISMATCH')
    h.require(Path(value['setupApp']).parent == Path(value['sourceRoot']).parent
              and Path(value['setupApp']).name == 'AosEdge SDV Lab Setup.app'
              and Path(value['sourceRoot']).name == 'Runtime Kit', 'MEDIA_LAYOUT_INVALID')
    h.require('/.local/remote-qualification/' in value['records'], 'RECORD_LOCATION_INVALID')
    h.require(value['image'] in ('6.1.1-maninblack.39/main-qemuarm64',
                                '6.1.1-maninblack.40/main-qemuarm64',
                                '6.1.1-maninblack.41/main-qemuarm64'), 'FACTORY_OUTSIDE_ACCEPTED_SCOPE')
    return value


def identity(config, transport):
    # Transport artifact fields may describe an earlier transfer. They are not
    # evidence for this candidate; only its pinned connection is reused.
    return hashlib.sha256(json.dumps(dict(candidate=config,
        connection={k: transport[k] for k in ('host', 'source', 'user', 'fingerprint')}),
        sort_keys=True).encode()).hexdigest()


def read_records(config, transport):
    """Status must not create a directory or acquire a writable lock."""
    root = h.unlinked(Path(config['records']))
    if not root.exists():
        return []
    info = root.stat()
    h.require(info.st_uid == os.getuid() and stat.S_IMODE(info.st_mode) == 0o700, 'RECORD_NOT_PRIVATE')
    saved = h.parse(h.unlinked(root/'identity.json').read_bytes())
    h.require(saved == dict(schemaVersion=1,configSha256=identity(config,transport)), 'RUN_REBINDING_FORBIDDEN')
    return h.read_attempts(root)


def summary(value):
    return dict(outcomes={state:sum(row['outcome']==state for row in value['engineering'])
        for state in ('PASS','FAIL','BLOCKED','UNCERTAIN','STALE','NOT_RUN')},
        nextStep=value['nextStep'], nativeAcceptance=value['nativeAcceptance'],
        unresolved=value['unresolved'], sourceReviewRequired=value['sourceReviewRequired'],
        supportProblems=[r for r in value['support'] if r['outcome'] != 'PASS'])


def definition(step):
    return hashlib.sha256(json.dumps(step, sort_keys=True).encode()).hexdigest()


def source_pin():
    return hashlib.sha256(b''.join((HERE / name).read_bytes() for name in
        ('journey.py', 'journey_plan.py', 'journey_worker.py', 'campaign.py', 'remote_harness.py'))).hexdigest()


class Progress:
    """A local heartbeat, not another remote probe or fabricated percentage."""
    def __init__(self, label, emit=print, interval=15):
        self.label, self.emit, self.interval = label, emit, interval
        self.done = threading.Event()

    def __enter__(self):
        self.started = time.monotonic()
        def notify():
            while not self.done.wait(self.interval):
                self.emit(json.dumps(dict(stage=self.label, state='IN_PROGRESS',
                    elapsedSeconds=round(time.monotonic()-self.started))))
        self.thread = threading.Thread(target=notify, daemon=True)
        self.thread.start()
        return self

    def __exit__(self, *args):
        self.done.set()
        self.thread.join()


class Remote:
    def __init__(self, transport, config):
        self.transport, self.config = transport, config

    def __call__(self, step, phase, context, request_id, prepared=None):
        payload = dict(config=self.config, kind=step['kind'], args=step.get('args', {}),
            phase=phase, requestId=request_id, expectedRun=context.get('runId'),
            prepared=prepared or {})
        # No arbitrary remote script from configuration, no development imports
        # on M1. The reviewed adapter uses only packaged Python/product owners.
        python = (self.config['setupApp'] + '/Contents/Resources/python/bin/python3.12'
                  if step['kind'] == 'setup' else self.config['packageRoot'] +
                  '/demo-artifacts/aosedge-sdv-demo/host-runtime/python/bin/python3.12')
        script = WORKER.read_text() + '\nmain(' + repr(json.dumps(payload)) + ')\n'
        command = shlex.quote(python) + " -I -B - <<'SDV_JOURNEY_WORKER'\n" + script + '\nSDV_JOURNEY_WORKER\n'
        with Progress(step['id']+':'+phase, emit=lambda value: print(value, flush=True)):
            value = h.parse(h.remote(self.transport, command, timeout=step.get('timeout', 180) + 20))
        h.require(isinstance(value, dict) and set(value) == {'outcome', 'code', 'facts'}
                  and value['outcome'] in ('PASS', 'FAIL', 'BLOCKED', 'UNCERTAIN')
                  and isinstance(value['facts'], dict)
                  and re.fullmatch('[A-Z][A-Z0-9_]{1,100}', value['code']), 'WORKER_RESPONSE_INVALID')
        # The worker projects fixed fields. Do not persist unbounded/raw payloads.
        h.require(len(json.dumps(value)) <= 512 * 1024, 'WORKER_RESPONSE_TOO_LARGE')
        return value

    def diagnose(self, step, context, request_id):
        return self(dict(id='diagnostic', kind='diagnostic', timeout=35,
            args=dict(failedStep=step['id'])), 'observe', context, request_id)['facts']


def rows_by_step(rows):
    values = {}
    for row in rows:
        if 'step' in row:
            values[row['step']] = row
    return values


def context_from(rows):
    context = {}
    for row in rows:
        if row['outcome'] == 'PASS' and 'step' in row:
            facts = row.get('observations', {}).get('facts', {})
            context[row['step']] = facts
            if facts.get('runId'):
                context['runId'] = facts['runId']
        # A terminal partial Create is not a successful step. Its corroborated
        # identity is nevertheless necessary for exact-owner diagnosis/cleanup.
        facts = row.get('observations', {}).get('facts', {})
        if (row.get('stepDefinition', {}).get('args', {}).get('action') == 'create'
                and facts.get('partialRunBound') is True and facts.get('runId')):
            h.require(context.get('runId') in (None, facts['runId']), 'PARTIAL_TEST_IDENTITY_CHANGED')
            context['runId'] = facts['runId']
    return context


def continuity_broken(rows):
    latest = rows_by_step(rows)
    closed = latest.get('shutdown')
    if not closed:
        return False
    for begin, end in CONTINUOUS_GROUPS:
        first, last = latest.get(begin), latest.get(end)
        if (first and first['attempt'] < closed['attempt'] and
                not (last and last['outcome'] == 'PASS' and last['attempt'] > first['attempt'])):
            return True
    return False


def report(rows, steps):
    latest = rows_by_step(rows)
    results = []
    for step in steps:
        row = latest.get(step['id'])
        status = row['outcome'] if row else 'NOT_RUN'
        if row and row.get('definitionSha256') != definition(step):
            status = 'STALE'
        results.append(dict(step=step['id'], outcome=status,
            seconds=row.get('durationSeconds', 0) if row else None,
            code=row.get('code') if row else None))
    unresolved = [r['step'] for r in latest.values() if r['outcome'] == 'UNCERTAIN']
    support = [dict(step=r['step'], outcome=r['outcome'], code=r.get('code'),
                    seconds=r.get('durationSeconds')) for r in latest.values()
               if r['step'] not in {s['id'] for s in steps}]
    source_review = any(r.get('sourceSha256') != source_pin() for r in rows if r.get('step') and r['outcome'] == 'PASS')
    return dict(engineering=results, support=support, nativeAcceptance='NOT_RUN', fullE2E='NOT_COMPLETE',
        scriptedSequence='PASS' if all(r['outcome'] == 'PASS' for r in results + support)
            and not unresolved and not source_review else 'NOT_COMPLETE',
        separateGates=['moving-SOTA', 'native-secure-token-entry', 'native-operator-journey',
                       'installation-interruption-and-repair'],
        unresolved=unresolved, excluded=['host-sleep-wake', 'external-ssd'],
        deferred=['VDP-TIMEOUT-01'], attempts=len(rows),
        evidenceSourceRevisions=sorted({r['sourceSha256'] for r in rows if r.get('sourceSha256')}),
        sourceReviewRequired=source_review,
        nextStep=next((r['step'] for r in results if r['outcome'] != 'PASS'), 'final-native-acceptance'))


class Runner:
    def __init__(self, journal, remote, *, clock=time.monotonic, sleep=time.sleep, emit=print):
        self.journal, self.remote = journal, remote
        self.clock, self.sleep, self.emit = clock, sleep, emit

    def run_step(self, step, context, previous=None):
        mutation = step['kind'] in MUTATIONS
        record = self.journal.begin('journey:' + step['id'])
        record.update(step=step['id'], definitionSha256=definition(step), sourceSha256=source_pin(),
            stepDefinition=step,
            requestId=previous['requestId'] if previous else str(uuid4()),
            prepared=previous.get('prepared', {}) if previous else {},
            evidenceMode='ENGINEERING', nativeAcceptance='NOT_RUN', mutation=mutation)
        path = self.journal.root / ('attempt-%04d.json' % record['attempt'])
        h.atomic(path, record)
        self.emit(json.dumps(dict(step=step['id'], state='RECONCILING' if previous else 'STARTED')))
        start = self.clock()
        timings = dict(remoteSeconds=0., observationWaitSeconds=0., calls=0)
        last_feedback = [start]
        def remote(*args):
            began = self.clock()
            try:
                return self.remote(*args)
            finally:
                timings['remoteSeconds'] += self.clock() - began
                timings['calls'] += 1
        def pause(seconds):
            began = self.clock()
            self.sleep(seconds)
            timings['observationWaitSeconds'] += self.clock() - began
            if self.clock()-last_feedback[0] >= 15:
                self.emit(json.dumps(dict(step=step['id'], state='WAITING_FOR_POSTCONDITION',
                                         elapsedSeconds=round(self.clock()-start, 1))))
                last_feedback[0] = self.clock()
        dispatched = bool(previous and mutation)
        try:
            resolved = dict(step, args=resolve(step.get('args', {}), context))
            if step['kind'] == 'continuity':
                result = dict(outcome='BLOCKED', code='EXPERIMENT_INTERRUPTED_REBASE_REQUIRED', facts={})
            elif step['kind'] == 'assert':
                result = dict(outcome='PASS' if evaluate(step['check'], context) else 'FAIL',
                              code='ASSERTION_EVALUATED', facts={})
            elif step['kind'] == 'hold':
                # Real soak duration survives neither reboot nor interruption;
                # repeat its reads/time, never shorten it from a checkpoint.
                seconds = step['seconds']
                while True:
                    result = remote(resolved, 'observe', context, record['requestId'])
                    if result['outcome'] != 'PASS':
                        break
                    if not evaluate(step['check'], dict(context, sample=result['facts'])):
                        result = dict(outcome='FAIL', code='SOAK_INVARIANT_FAILED', facts={}); break
                    if self.clock() - start >= seconds:
                        result = dict(outcome='PASS', code='SOAK_DURATION_CONFIRMED', facts=dict(seconds=seconds))
                        break
                    pause(min(5, seconds - (self.clock() - start)))
            elif previous and mutation:
                result = remote(resolved, 'reconcile', context, record['requestId'], record['prepared'])
            else:
                if mutation:
                    before = remote(resolved, 'prepare', context, record['requestId'])
                    if before['outcome'] != 'PASS':
                        result = before
                    else:
                        record['prepared'] = before['facts']
                        h.atomic(path, record)  # Persist identity/session BEFORE dispatch.
                        dispatched = True
                        result = remote(resolved, 'execute', context, record['requestId'], before['facts'])
                else:
                    result = remote(resolved, 'observe', context, record['requestId'])
                if step.get('until'):
                    while result['outcome'] == 'PASS' and not evaluate(step['until'], dict(context, sample=result['facts'])):
                        if self.clock() - start >= step.get('timeout', 180):
                            result = dict(outcome='FAIL', code='POSTCONDITION_DEADLINE', facts=result['facts']); break
                        pause(min(3, max(0, step.get('timeout', 180) - (self.clock()-start))))
                        result = remote(resolved, 'observe', context, record['requestId'])
        except (OSError, ValueError, KeyError, TypeError, h.Error, h.InstallError):
            result = dict(outcome='UNCERTAIN' if dispatched else 'BLOCKED',
                          code='TRANSPORT_OR_EVIDENCE_UNAVAILABLE', facts={})
        observations = dict(facts=result['facts'], timing={k:round(v,3) for k,v in timings.items()})
        if result['outcome'] != 'PASS':
            reason = result['facts'].get('reason') or result['code']
            observations['failureClass'] = ('INPUT_REQUIRED' if reason in (
                'QUALIFICATION_ACCESS_INPUT_REQUIRED', 'VM_ACCESS_DIALOG_TIMED_OUT',
                'VM_ACCESS_CANCELLED_OR_DIALOG_UNAVAILABLE') else
                'UNRESOLVED_EFFECT' if result['outcome'] == 'UNCERTAIN' else
                'PRODUCT' if result['code'] == 'PRODUCT_OPERATION_NOT_COMPLETED' else 'PREREQUISITE_OR_CHECK')
        if result['outcome'] != 'PASS' and callable(getattr(self.remote, 'diagnose', None)):
            began = self.clock()
            scope = dict(context)
            if result['facts'].get('partialRunBound'):
                scope['runId'] = result['facts']['runId']
            try:
                observations['diagnostic'] = self.remote.diagnose(step, scope, record['requestId'])
            except (OSError, ValueError, KeyError, TypeError):
                observations['diagnostic'] = dict(state='UNAVAILABLE')
            observations['timing']['diagnosticSeconds'] = round(self.clock()-began,3)
        self.journal.finish(record, result['outcome'], result['code'], observations)
        self.emit(json.dumps(dict(step=step['id'], outcome=record['outcome'],
                                 seconds=record['durationSeconds'], code=record['code'])))
        return record

    def resume(self, steps, until):
        rows = h.read_attempts(self.journal.root)
        if not rows:
            return True
        latest = rows_by_step(rows)
        # Reconcile the exact uncertain identity before restarting any owner.
        for prior in list(latest.values()):
            if prior['outcome'] == 'UNCERTAIN':
                step = next((s for s in steps if s['id'] == prior['step']), prior.get('stepDefinition'))
                h.require(step and definition(step) == prior['definitionSha256'], 'UNCERTAIN_STEP_CHANGED')
                if self.run_step(step, context_from(h.read_attempts(self.journal.root)), prior)['outcome'] != 'PASS':
                    return False
        rows = h.read_attempts(self.journal.root)
        latest = rows_by_step(rows)
        subset = steps[:next((i+1 for i,s in enumerate(steps) if s['id'] == until), len(steps))]
        if all(latest.get(s['id'], {}).get('outcome') == 'PASS' for s in subset):
            return True
        if continuity_broken(rows):
            self.run_step(dict(id='resume-continuity', kind='continuity'), context_from(rows))
            return False
        passed = {key for key,row in latest.items() if row['outcome'] == 'PASS'}
        refresh = ([dict(id='resume-installed', kind='observe', args=dict(query='installed'))]
                   if any(s['id'] == 'installed' for s in steps) else [])
        if 'docker' in passed:
            refresh.append(next(s for s in steps if s['id'] == 'docker'))
        if 'presenter' in passed:
            refresh.append(next(s for s in steps if s['id'] == 'presenter'))
        for milestone, owners in (
            ('controller-create', ('brake','tire')),
            ('controller-start', ('vm',)),
            ('simulation', ('source',)),
            ('connect', ('connection',)),
        ):
            if milestone in passed:
                refresh.extend(dict(id='resume-'+owner, kind='restore', args=dict(owner=owner), timeout=180)
                               for owner in owners)
        if 'connect' in passed and any('vdp-'+p+'-safe' in passed and
                'vdp-'+p+'-ready' not in passed for p in ('v1','v2','v3')):
            # A previous physical stop is not current after runtime restoration.
            refresh.append(dict(id='resume-vdp-safe',kind='mode',args=dict(mode='safe_stop'),timeout=75))
            refresh.append(dict(id='resume-vdp-safe-observed',kind='observe',args=dict(query='local'),
                until=dict(test='safe-stop',actual='$sample'),timeout=60))
        for step in refresh:
            if self.run_step(step, context_from(h.read_attempts(self.journal.root)))['outcome'] != 'PASS':
                return False
        return True

    def run(self, steps, until=None, retry_create=False):
        h.require(until is None or until in {s['id'] for s in steps}, 'UNKNOWN_STOP_BOUNDARY')
        initial_rows = h.read_attempts(self.journal.root)
        latest = rows_by_step(initial_rows)
        for step in steps:
            prior = latest.get(step['id'])
            h.require(not prior or prior['outcome'] != 'PASS' or prior.get('definitionSha256') == definition(step),
                      'PASSED_STEP_DEFINITION_CHANGED')
            if prior and prior['outcome'] == 'FAIL' and prior.get('mutation'):
                permitted = (retry_create and step.get('args', {}).get('action') == 'create'
                             and prior.get('observations', {}).get('facts', {}).get('partialRunBound'))
                if not permitted:
                    # Do not restart infrastructure just to discover that a
                    # known failed mutation cannot be replayed.
                    return report(initial_rows, steps)
        if not self.resume(steps, until):
            return report(h.read_attempts(self.journal.root), steps)
        for step in steps:
            rows = h.read_attempts(self.journal.root)
            latest = rows_by_step(rows)
            prior = latest.get(step['id'])
            if prior and prior['outcome'] == 'FAIL' and prior.get('mutation'):
                # Only the product's idempotent partial-Create continuation is
                # explicitly resumable here. Never replay a failed publication.
                if not (retry_create and step.get('args', {}).get('action') == 'create'
                        and prior.get('observations', {}).get('facts', {}).get('partialRunBound')):
                    break
            uncertain = [r for r in latest.values() if r['outcome'] == 'UNCERTAIN']
            h.require(not uncertain or (len(uncertain) == 1 and uncertain[0]['step'] == step['id'])
                      or (prior and prior['outcome'] == 'PASS'), 'RECONCILE_EARLIER_ACTION')
            if prior and prior['outcome'] == 'PASS' and step['id'] != 'shutdown':
                h.require(prior.get('definitionSha256') == definition(step), 'PASSED_STEP_DEFINITION_CHANGED')
            else:
                row = self.run_step(step, context_from(rows), prior if prior and prior['outcome'] == 'UNCERTAIN' else None)
                if row['outcome'] != 'PASS':
                    break
            if step['id'] == until:
                break
        return report(h.read_attempts(self.journal.root), steps)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True, help='existing pinned SSH configuration')
    parser.add_argument('--journey', type=Path, required=True, help='private exact candidate/instance binding')
    parser.add_argument('command', choices=('plan', 'status', 'report', 'run', 'stop', 'verify-host'))
    parser.add_argument('--until', help='named checkpoint; does not skip earlier gates')
    parser.add_argument('--resume-partial-create', action='store_true',
                        help='after a diagnosed fix, continue only the same bound partial Create')
    args = parser.parse_args()
    transport, _ = h.configuration(args.config)
    config = configuration(args.journey, transport['user'])
    steps = plan(config)
    h.require(args.until is None or args.command == 'run', 'STOP_BOUNDARY_REQUIRES_RUN')
    if args.command == 'plan':
        print(json.dumps(steps, indent=2)); return
    if args.command == 'status':
        print(json.dumps(summary(report(read_records(config,transport),steps)))); return
    with h.Journal(Path(config['records']), identity(config, transport)) as journal:
        runner = Runner(journal, Remote(transport, config), emit=lambda value: print(value, flush=True))
        if args.command in ('run', 'verify-host'):
            try:
                if args.command == 'run':
                    result = runner.run(steps, args.until, args.resume_partial_create)
                else:
                    # Fresh, small infrastructure smoke. No journal creation,
                    # publication, reset, provisioning, VM or CARLA startup.
                    rows = h.read_attempts(journal.root)
                    h.require(not any(r['outcome'] == 'UNCERTAIN' for r in rows_by_step(rows).values()),
                              'RECONCILE_BEFORE_HOST_SMOKE')
                    for step in (dict(id='verify-host-installed',kind='observe',args=dict(query='installed')),
                                 dict(id='docker',kind='dependency',timeout=120),
                                 dict(id='verify-host-presenter',kind='presenter-start',timeout=90)):
                        if runner.run_step(step,context_from(h.read_attempts(journal.root)))['outcome'] != 'PASS':
                            break
            finally:
                # Stop only through ownership-checked product paths. A busy or
                # uncertain product owner blocks cleanup, never invites a kill.
                rows = h.read_attempts(journal.root)
                if any(r.get('step') in ('presenter','docker','verify-host-presenter') for r in rows):
                    last = rows[-1]
                    if last.get('step') != 'shutdown' or last['outcome'] != 'PASS':
                        prior = rows_by_step(rows).get('shutdown')
                        runner.run_step(dict(id='shutdown', kind='shutdown', timeout=120), context_from(rows),
                            prior if prior and prior['outcome'] == 'UNCERTAIN' else None)
            result = report(h.read_attempts(journal.root), steps)
        elif args.command == 'stop':
            rows = h.read_attempts(journal.root)
            prior = rows_by_step(rows).get('shutdown')
            result = runner.run_step(dict(id='shutdown', kind='shutdown', timeout=120), context_from(rows),
                prior if prior and prior['outcome'] == 'UNCERTAIN' else None)
        else:
            result = report(h.read_attempts(journal.root), steps)
        if args.command in ('run','report','verify-host'):
            h.atomic(journal.root/'report.json', result)
        if args.command in ('run','verify-host'):
            print(json.dumps(summary(result)))
        else:
            print(json.dumps(result, indent=2))
        if args.command in ('run', 'stop', 'verify-host') and (result.get('outcome') not in (None, 'PASS') or
                any(x['outcome'] in ('FAIL', 'BLOCKED', 'UNCERTAIN', 'STALE') for x in result.get('engineering', []))):
            raise SystemExit(2)
        if args.command in ('run','verify-host') and any(x['outcome'] != 'PASS' for x in result.get('support', [])):
            raise SystemExit(2)


if __name__ == '__main__':
    try:
        main()
    except (h.Error, h.InstallError, OSError, ValueError):
        # Never print arbitrary exceptions/configuration/credential references.
        print(json.dumps(dict(outcome='BLOCKED', code='JOURNEY_PREFLIGHT_OR_RECONCILIATION_REQUIRED')))
        raise SystemExit(2)
