# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Bounded engineering scenarios; native acceptance is always separate."""

import hashlib
import json
import math
import os
from pathlib import Path
import re
import shlex
import stat
import time
from uuid import UUID

import remote_harness as h

CHECKS = ('installed', 'controller-running', 'backends-running', 'presenter-consistency', 'stopped')
ACTIONS = ('vm-start', 'vm-stop', 'brake-start', 'tire-start', 'backends-stop')
EXPECTATIONS = {'vm-start': 'controller-powered', 'vm-stop': 'controller-stopped',
                'brake-start': 'brake-running', 'tire-start': 'tire-running',
                'backends-stop': 'backends-stopped'}
PROBE = Path(__file__).with_name('installed_probe.py')
SEQUENCES = {
    'local-start': (('verify', 'installed'), ('action', 'vm-start'), ('action', 'brake-start'),
                    ('action', 'tire-start'), ('verify', 'controller-running'), ('verify', 'backends-running')),
    'local-stop': (('action', 'vm-stop'), ('action', 'backends-stop'), ('verify', 'stopped')),
}


def target_configuration(path, config):
    path = h.unlinked(path)
    info = path.stat()
    h.require(stat.S_ISREG(info.st_mode) and info.st_uid == os.getuid()
              and stat.S_IMODE(info.st_mode) == 0o600 and info.st_size <= 4096, 'TARGET_NOT_PRIVATE')
    raw = path.read_bytes()
    value = h.parse(raw)
    h.require(isinstance(value, dict) and set(value) == {'schemaVersion', 'packageRoot',
              'instanceRoot', 'manifestSha256', 'localVmId'} and value['schemaVersion'] == 1,
              'TARGET_SCHEMA_INVALID')
    h.require(all(isinstance(v, str) for k, v in value.items() if k != 'schemaVersion'), 'TARGET_SCHEMA_INVALID')
    h.require(re.fullmatch('[a-f0-9]{64}', value['manifestSha256']), 'TARGET_PIN_INVALID')
    h.require(str(UUID(value['localVmId'])) == value['localVmId'], 'TARGET_VM_INVALID')
    home = Path('/Users') / config['user']
    for name in ('packageRoot', 'instanceRoot'):
        p = Path(value[name])
        h.require(p.is_relative_to(home) and p != home and '..' not in p.parts
                  and str(p) == value[name] and not any(c in value[name] for c in '\n\r\x00'), 'TARGET_PATH_INVALID')
    package, root = Path(value['packageRoot']), Path(value['instanceRoot'])
    h.require(package.name == value['manifestSha256'] and package.parent.name == 'versions'
              and not root.is_relative_to(package.parent.parent)
              and not package.parent.parent.is_relative_to(root), 'TARGET_PACKAGE_INVALID')
    return value, hashlib.sha256(raw).hexdigest()


def source_digest():
    return hashlib.sha256(Path(__file__).read_bytes() + PROBE.read_bytes()
                          + Path(h.__file__).read_bytes()).hexdigest()


def remote_observe(config, target, kind, name):
    request = dict(target=target, kind=kind, name=name)
    python = target['packageRoot'] + '/demo-artifacts/aosedge-sdv-demo/host-runtime/python/bin/python3.12'
    script = shlex.quote(python) + " -I -B - <<'SDV_INSTALLED_PROBE'\n" + PROBE.read_text()
    script += '\nprint(json.dumps(entry(json.loads(' + repr(json.dumps(request)) + '))))\nSDV_INSTALLED_PROBE\n'
    raw = h.remote(config, script, timeout=240 if kind == 'action' else 75)
    value = h.parse(raw)
    h.require(isinstance(value, dict) and set(value) == {'schemaVersion', 'code', 'stage', 'actionAttempted',
              'facts', 'operationSeconds', 'observationSeconds'} and value['schemaVersion'] == 1,
              'SCENARIO_RESPONSE_INVALID')
    h.require(value['code'] in ('OBSERVED', 'ACTION_UNCERTAIN', 'INSTALLED_PROBE_BLOCKED')
              and type(value['actionAttempted']) is bool, 'SCENARIO_RESPONSE_INVALID')
    h.require(value['stage'] in ('PACKAGE_BINDING', 'TEST_BINDING', 'OPERATION_INTERLOCK',
              'OWNER_OPERATION', 'CONTROLLER_OBSERVATION', 'BACKEND_OBSERVATION', 'PRESENTER_OBSERVATION'),
              'SCENARIO_RESPONSE_INVALID')
    facts = value['facts']
    allowed = {'installed', 'controller', 'qmpRunning', 'brake', 'tire', 'brakeHealthy', 'tireHealthy', 'presenter'}
    h.require(isinstance(facts, dict) and set(facts) <= allowed, 'SCENARIO_RESPONSE_INVALID')
    for key, item in facts.items():
        if key in ('controller', 'brake', 'tire', 'presenter'):
            h.require(item in ('RUNNING', 'STOPPED', 'NOT_CREATED', 'UNKNOWN', None), 'SCENARIO_RESPONSE_INVALID')
        else:
            h.require(type(item) is bool or (key == 'qmpRunning' and item is None), 'SCENARIO_RESPONSE_INVALID')
    for key in ('operationSeconds', 'observationSeconds'):
        h.require(type(value[key]) in (int, float) and math.isfinite(value[key])
                  and 0 <= value[key] <= 240, 'SCENARIO_RESPONSE_INVALID')
    return value


def satisfied(name, facts):
    if facts.get('installed') is not True:
        return False
    if name == 'installed':
        return True
    running = facts.get('controller') == 'RUNNING' and facts.get('qmpRunning') is True
    stopped = facts.get('controller') == 'STOPPED' and facts.get('qmpRunning') is None
    healthy = lambda t: facts.get(t) == 'RUNNING' and facts.get(t + 'Healthy') is True
    return {'controller-running': running, 'controller-stopped': stopped,
            'controller-powered': facts.get('qmpRunning') is True,
            'backends-running': healthy('brake') and healthy('tire'),
            'brake-running': healthy('brake'), 'tire-running': healthy('tire'),
            'backends-stopped': facts.get('brake') == facts.get('tire') == 'STOPPED',
            'stopped': stopped and facts.get('brake') == facts.get('tire') == 'STOPPED',
            'presenter-consistency': (running or stopped) and facts.get('presenter') == facts.get('controller')}.get(name, False)


def unresolved(rows):
    resolved = {r.get('observations', {}).get('resolvesAttempt') for r in rows
                if r['command'] == 'scenario-reconcile' and r['outcome'] == 'PASS'}
    return [r for r in rows if r['command'].startswith('action:')
            and r['outcome'] == 'UNCERTAIN' and r['attempt'] not in resolved]


def known_action_precondition(name, facts):
    if name == 'vm-start':
        return facts.get('controller') == 'STOPPED' and facts.get('qmpRunning') is None
    if name == 'vm-stop':
        return facts.get('qmpRunning') is True
    if name in ('brake-start', 'tire-start'):
        return facts.get(name.split('-')[0]) == 'STOPPED'
    return all(facts.get(t) in ('RUNNING', 'STOPPED') for t in ('brake', 'tire'))


def checkpoint(rows, target_pin):
    current = [r for r in rows if r.get('targetSha256') == target_pin
               and r.get('scenarioSha256') == source_digest()]
    checks = {name: 'NOT_RUN' for name in CHECKS}
    for row in current:
        if row['command'].startswith('verify:') and row['command'][7:] in CHECKS:
            checks[row['command'][7:]] = row['outcome']
    pending = unresolved(rows)
    return dict(engineeringChecks=checks, nativeAcceptance='NOT_RUN', fullE2E='NOT_RUN',
                unresolvedActions=[r['attempt'] for r in pending],
                nextStep='reconcile' if pending else next((k for k in CHECKS[:4] if checks[k] != 'PASS'),
                                                         'native_UI_and_serial_deployment'),
                observationOnly=True)


def attempt(journal, config, target, target_pin, kind, name, observer=remote_observe, resolves=None):
    h.require(kind in ('verify', 'action', 'reconcile'), 'SCENARIO_KIND_INVALID')
    h.require(name in (ACTIONS if kind == 'action' else CHECKS + tuple(EXPECTATIONS.values())), 'SCENARIO_NOT_ALLOWED')
    command = 'scenario-reconcile' if kind == 'reconcile' else kind + ':' + name
    record = journal.begin(command)
    record.update(targetSha256=target_pin, candidate=target['manifestSha256'], scenarioSha256=source_digest(),
                  evidenceMode='ENGINEERING', nativeAcceptance='NOT_RUN')
    h.atomic(journal.root / ('attempt-%04d.json' % record['attempt']), record)
    try:
        result = observer(config, target, 'action' if kind == 'action' else 'verify', name)
        expectation = EXPECTATIONS.get(name, name) if kind == 'action' else name
        ok = result['code'] == 'OBSERVED' and satisfied(expectation, result['facts'])
        outcome = 'PASS' if ok else ('UNCERTAIN' if kind == 'action' and result['actionAttempted'] else
                                    'FAIL' if result['code'] == 'OBSERVED' else 'BLOCKED')
        observations = dict(result, expectation=expectation)
        if resolves is not None:
            observations['resolvesAttempt'] = resolves
        journal.finish(record, outcome, 'POSTCONDITION_CONFIRMED' if ok else
                       'POSTCONDITION_NOT_MET' if result['code'] == 'OBSERVED' else result['code'], observations)
    except (h.Error, h.InstallError, OSError, ValueError):
        journal.finish(record, 'UNCERTAIN' if kind == 'action' else 'BLOCKED', 'SCENARIO_TRANSPORT_OR_RESPONSE_FAILED')
    return record


def execute(journal, config, target, pin, command, name, observer=remote_observe):
    rows = h.read_attempts(journal.root)
    pending = unresolved(rows)
    if command == 'run':
        h.require(name in SEQUENCES, 'SEQUENCE_NOT_ALLOWED')
        output = []
        if pending:
            output.extend(execute(journal, config, target, pin, 'reconcile', None, observer))
            if output[-1]['outcome'] != 'PASS':
                return output
        for kind, step in SEQUENCES[name]:
            if kind == 'action':
                before = attempt(journal, config, target, pin, 'verify', EXPECTATIONS[step], observer)
                output.append(before)
                if before['outcome'] == 'PASS':
                    continue
                if before['outcome'] != 'FAIL':
                    break
                if not known_action_precondition(step, before.get('observations', {}).get('facts', {})):
                    break
            output.append(attempt(journal, config, target, pin, kind, step, observer))
            if output[-1]['outcome'] != 'PASS':
                break
        return output
    if command == 'action':
        h.require(not pending, 'ACTION_RECONCILIATION_REQUIRED')
    if command == 'reconcile':
        h.require(len(pending) == 1 and pending[0].get('targetSha256') == pin, 'RECONCILE_EXACT_TARGET_REQUIRED')
        prior = pending[0]
        return [attempt(journal, config, target, pin, 'reconcile', EXPECTATIONS[prior['command'][7:]],
                        observer, prior['attempt'])]
    names = ('installed', 'controller-running', 'backends-running') if name == 'local-baseline' else (name,)
    result = []
    for step in names:
        row = attempt(journal, config, target, pin, command, step, observer)
        result.append(row)
        if row['outcome'] != 'PASS':
            break
    return result
