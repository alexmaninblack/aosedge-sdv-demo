#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Test-only checkpoint and transfer helper; never a product lifecycle owner."""

import argparse
import base64
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import stat
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent/'distribution'))
from installation_inputs import Bundle, InstallError, Row, digest, parse, unlinked

NUMERIC = {'memoryBytes', 'freeKiB', 'dockerPresent', 'homebrewPresent',
           'xcodePresent', 'demoProcesses', 'busyPorts', 'stagingHttp'}
FIELDS = NUMERIC | {'arch', 'model', 'os', 'build', 'user', 'console', 'internal', 'swapUsedMiB'}
CONFIG_FIELDS = {'schemaVersion', 'runId', 'host', 'source', 'user', 'model', 'os',
                 'key', 'knownHosts', 'fingerprint', 'kit', 'manifestSha256',
                 'setup', 'setupSha256', 'remoteRoot', 'records'}


class Error(ValueError):
    pass


def require(ok, code):
    if not ok:
        raise Error(code)


def utc():
    return datetime.now(timezone.utc).isoformat()


def atomic(path, value):
    pending = path.with_suffix('.pending')
    fd = os.open(pending, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w') as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(pending, path)
    fd = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def run(args, *, data=None, timeout=60):
    try:
        result = subprocess.run(args, input=data, text=True, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, timeout=timeout, check=False)
    except subprocess.TimeoutExpired:
        raise Error('COMMAND_TIMEOUT') from None
    if result.returncode != 0:
        # Classify transport failures without persisting raw SSH/app diagnostics.
        messages = result.stderr.lower()
        for text, code in (('operation timed out', 'REMOTE_UNREACHABLE'),
                           ('connection timed out', 'REMOTE_UNREACHABLE'),
                           ('no route to host', 'REMOTE_UNREACHABLE'),
                           ('connection refused', 'REMOTE_CONNECTION_REFUSED'),
                           ('host key verification failed', 'SSH_HOST_VERIFICATION_FAILED'),
                           ('permission denied (publickey', 'SSH_AUTHENTICATION_FAILED')):
            if text in messages:
                raise Error(code)
        raise Error('REMOTE_COMMAND_FAILED')
    require(len(result.stdout) < 4*2**20, 'OUTPUT_LIMIT_EXCEEDED')
    return result.stdout


def ssh_args(config):
    return ['/usr/bin/ssh', '-F', '/dev/null', '-T', '-b', config['source'], '-i', config['key'],
            '-o', 'IdentitiesOnly=yes', '-o', 'IdentityAgent=none', '-o', 'BatchMode=yes',
            '-o', 'StrictHostKeyChecking=yes', '-o', 'UserKnownHostsFile='+config['knownHosts'],
            '-o', 'GlobalKnownHostsFile=/dev/null', '-o', 'HostKeyAlgorithms=ssh-ed25519',
            '-o', 'UpdateHostKeys=no', '-o', 'ConnectTimeout=8', '-o', 'ConnectionAttempts=1',
            '-o', 'ServerAliveInterval=10', '-o', 'ServerAliveCountMax=3',
            '-o', 'ForwardAgent=no', '-o', 'ClearAllForwardings=yes',
            config['user']+'@'+config['host']]


def remote(config, script, timeout=60):
    return run(ssh_args(config)+['/bin/sh -s'], data=script, timeout=timeout)


def configuration(path):
    path = unlinked(path)
    info = path.stat()
    require(info.st_uid == os.getuid() and stat.S_IMODE(info.st_mode) == 0o600,
            'CONFIG_NOT_PRIVATE')
    require(info.st_size <= 16384, 'CONFIG_TOO_LARGE')
    raw = path.read_bytes()
    value = parse(raw)
    require(isinstance(value, dict) and set(value) == CONFIG_FIELDS and value['schemaVersion'] == 1,
            'CONFIG_SCHEMA_INVALID')
    require(all(isinstance(v, str) for k, v in value.items() if k != 'schemaVersion'),
            'CONFIG_VALUE_INVALID')
    require(value['host'] == '192.168.247.2' and value['source'] == '192.168.247.1',
            'TARGET_OUTSIDE_ACCEPTED_PROFILE')
    require(re.fullmatch(r'[a-z][a-z0-9_]{0,31}', value['user']), 'USER_INVALID')
    require(re.fullmatch(r'[a-z0-9][a-z0-9-]{0,63}', value['runId']), 'RUN_ID_INVALID')
    require(value['remoteRoot'] == '/Users/'+value['user']+'/SDV-Qualification/'+value['runId'],
            'DESTINATION_OUTSIDE_ACCEPTED_PROFILE')
    for name in ('manifestSha256', 'setupSha256'):
        require(re.fullmatch('[a-f0-9]{64}', value[name]), 'PIN_INVALID')
    for name in ('kit', 'setup', 'records', 'key', 'knownHosts'):
        require(Path(value[name]).is_absolute(), 'PATH_NOT_ABSOLUTE')
        unlinked(value[name])
    require('/.local/remote-qualification/' in value['records'], 'RECORD_LOCATION_INVALID')
    key = Path(value['key']).stat()
    require(stat.S_ISREG(key.st_mode) and key.st_uid == os.getuid()
            and stat.S_IMODE(key.st_mode) == 0o600, 'SSH_KEY_PERMISSIONS_INVALID')
    hosts = Path(value['knownHosts']).read_text().splitlines()
    require(len(hosts) == 1, 'HOST_PIN_INVALID')
    fields = hosts[0].split()
    require(len(fields) == 3 and fields[:2] == [value['host'], 'ssh-ed25519'], 'HOST_PIN_INVALID')
    fingerprint = 'SHA256:'+base64.b64encode(hashlib.sha256(base64.b64decode(fields[2], validate=True)).digest()).decode().rstrip('=')
    require(fingerprint == value['fingerprint'], 'HOST_PIN_MISMATCH')
    return value, hashlib.sha256(raw).hexdigest()


def read_attempts(root):
    unlinked(root)
    if not root.exists():
        return []
    require(not list(root.glob('*.pending')), 'RECORD_RECOVERY_REQUIRED')
    paths = sorted(root.glob('attempt-*.json'))
    require(len(paths) <= 1000, 'RECORD_RETENTION_LIMIT')
    return [parse(unlinked(path).read_bytes()) for path in paths]


class Journal:
    def __init__(self, root, config_pin):
        self.root, self.pin, self.fd = unlinked(root), config_pin, None

    def __enter__(self):
        self.root.mkdir(parents=True, mode=0o700, exist_ok=True)
        require(self.root.stat().st_uid == os.getuid()
                and stat.S_IMODE(self.root.stat().st_mode) == 0o700, 'RECORD_NOT_PRIVATE')
        lock = unlinked(self.root/'writer.lock')
        self.fd = os.open(lock, os.O_RDWR | os.O_CREAT, 0o600)
        try:
            fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            identity = self.root/'identity.json'
            if identity.exists():
                require(parse(unlinked(identity).read_bytes()) == {'schemaVersion': 1, 'configSha256': self.pin},
                        'RUN_REBINDING_FORBIDDEN')
            else:
                atomic(identity, {'schemaVersion': 1, 'configSha256': self.pin})
            read_attempts(self.root)
        except BaseException as exc:
            os.close(self.fd)
            self.fd = None
            if isinstance(exc, BlockingIOError):
                raise Error('WRITER_ALREADY_ACTIVE') from None
            raise
        return self

    def __exit__(self, *args):
        os.close(self.fd)

    def begin(self, command):
        index = len(read_attempts(self.root))+1
        revision = hashlib.sha256(Path(__file__).read_bytes()+(HERE/'remote_probe.sh').read_bytes()).hexdigest()
        result = dict(schemaVersion=1, attempt=index, command=command, startedAt=utc(),
                      finishedAt=None, outcome='UNCERTAIN', code='INTENT_RECORDED', harnessSha256=revision)
        atomic(self.root/f'attempt-{index:04d}.json', result)
        self.started = time.monotonic()
        return result

    def finish(self, record, outcome, code, observations=None):
        record.update(outcome=outcome, code=code, finishedAt=utc(),
                      durationSeconds=round(time.monotonic()-self.started, 3), observations=observations or {})
        atomic(self.root/f"attempt-{record['attempt']:04d}.json", record)


def parse_probe(raw):
    result = {}
    for line in raw.splitlines():
        parts = line.split('\t')
        require(len(parts) == 2 and parts[0] in FIELDS and parts[0] not in result, 'PROBE_SCHEMA_INVALID')
        key, value = parts
        require(re.fullmatch(r'[A-Za-z0-9.,_-]{1,80}', value), 'PROBE_VALUE_INVALID')
        if key in NUMERIC:
            require(value.isdigit(), 'PROBE_NUMBER_INVALID')
            value = int(value)
        result[key] = value
    require(set(result) == FIELDS, 'PROBE_INCOMPLETE')
    return result


def probe(config):
    result = parse_probe(remote(config, (HERE/'remote_probe.sh').read_text()))
    require(result['arch'] == 'arm64' and result['model'] == config['model']
            and result['os'] == config['os'] and result['user'] == config['user'], 'HOST_MISMATCH')
    return result


def required_bytes(kit_bytes, setup_bytes):
    return 90*2**30 + 2*kit_bytes + setup_bytes


def stage_attempted(rows):
    return any(row['command'] == 'stage-kit' for row in rows)


def summary(config, rows):
    staged = any(row['command'] in ('stage-kit', 'reconcile-stage') and row['outcome'] == 'PASS'
                 for row in rows)
    uncertain = [row['attempt'] for row in rows if row['outcome'] == 'UNCERTAIN'
                 and not (row['command'] == 'stage-kit' and staged)]
    latest_probe = next((row for row in reversed(rows) if row['command'] == 'preflight'), None)
    next_step = 'preflight'
    if staged:
        # This helper does not observe native Setup actions. An absent harness
        # step is not evidence that installation has never started.
        next_step = 'consult_native_qualification_receipt'
    elif stage_attempted(rows):
        next_step = 'reconcile_stage_before_any_retry'
    elif latest_probe and latest_probe['outcome'] == 'PASS':
        next_step = 'stage-kit'
    return dict(runId=config['runId'], candidate=config['manifestSha256'],
                formalQualification='NOT_RUN', nextStep=next_step,
                unresolvedAttempts=uncertain, attempts=rows)


def marker(config):
    return config['runId']+':'+config['manifestSha256']+':'+config['setupSha256']


def verification_script(root, identity, rows):
    q = shlex.quote
    lines = ['set -eu', 'cd '+q(root), 'test "$(cat .candidate)" = '+q(identity),
             'test -z "$(find . -type l -print -quit)"',
             'test -z "$(find . ! -type d ! -type f -print -quit)"',
             'test -z "$(find . ! -user "$(id -un)" -print -quit)"',
             'test "$(find . -type f | wc -l | tr -d \' \')" = '+str(len(rows)+1)]
    for name, row in sorted(rows.items()):
        require(not any(c in name for c in '\n\r\\'), 'TRANSFER_PATH_UNSUPPORTED')
        lines.append('test "$(stat -f %z:%Lp:%l '+q(name)+')" = '+q(f'{row.size}:{row.mode:o}:1'))
    lines.append('/usr/bin/shasum -a 256 -c - >/dev/null <<\'SDV_CHECKSUMS\'')
    lines.extend(row.sha256+'  '+name for name, row in sorted(rows.items()))
    lines.extend(['SDV_CHECKSUMS', "printf 'VERIFIED\\n'"])
    return '\n'.join(lines)+'\n'


def transfer_rows(config, bundle):
    rows = {'kit/'+name: row for name, row in bundle.rows.items()}
    setup = Path(config['setup'])
    require(digest(setup) == config['setupSha256'], 'SETUP_DIGEST_MISMATCH')
    rows['setup.dmg'] = Row(setup.stat().st_size, config['setupSha256'], stat.S_IMODE(setup.stat().st_mode))
    return rows


def preflight(config, bundle):
    facts = probe(config)
    try:
        require(facts['console'] == config['user'], 'CONSOLE_USER_MISMATCH')
        require(facts['internal'] == 'true', 'DESTINATION_NOT_INTERNAL')
        require(facts['memoryBytes'] >= 16*2**30, 'MEMORY_ENTRY_GUARD')
        require(facts['freeKiB']*1024 >= required_bytes(bundle.total_bytes, Path(config['setup']).stat().st_size), 'SPACE_ENTRY_GUARD')
        require(facts['busyPorts'] == 0 and facts['demoProcesses'] == 0, 'EXISTING_RUNTIME_CONFLICT')
        require(100 <= facts['stagingHttp'] < 500, 'STAGING_NETWORK_UNAVAILABLE')
    except Error as exc:
        exc.observations = facts
        raise
    return facts


def stage(config, bundle):
    bundle.verify()
    rows = transfer_rows(config, bundle)
    facts = preflight(config, bundle)
    root, q = config['remoteRoot'], shlex.quote
    parent = str(Path(root).parent)
    script = ['set -eu', 'umask 077']
    for path in reversed(Path(root).parents):
        script.append('test ! -L '+q(str(path)))
    script += ['test ! -e '+q(root),
               'if test -e '+q(parent)+'; then test "$(stat -f %u:%Lp '+q(parent)+')" = "$(id -u):700"; else mkdir '+q(parent)+'; fi',
               'mkdir '+q(root), 'printf %s '+q(marker(config))+' > '+q(root+'/.candidate')]
    remote(config, '\n'.join(script)+'\n')
    shell = shlex.join(ssh_args(config)[:-1])
    target = config['user']+'@'+config['host']+':'+root
    run(['/usr/bin/rsync', '-rpt', '--partial', '-e', shell, config['kit']+'/', target+'/kit/'], timeout=1800)
    run(['/usr/bin/rsync', '-pt', '--partial', '-e', shell, config['setup'], target+'/setup.dmg'], timeout=120)
    require(remote(config, verification_script(root, marker(config), rows), timeout=900).strip() == 'VERIFIED', 'TRANSFER_NOT_VERIFIED')
    return dict(files=len(rows), payloadBytes=sum(row.size for row in rows.values()), preflight=facts)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--target', type=Path, help='private installed Test binding for engineering scenarios')
    parser.add_argument('command', choices=('status', 'report', 'preflight', 'stage-kit', 'reconcile-stage', 'collect', 'stop',
                                           'verify', 'action', 'reconcile', 'run'))
    parser.add_argument('scenario', nargs='?')
    args = parser.parse_args()
    config, pin = configuration(args.config)
    root = Path(config['records'])
    if args.command in ('verify', 'action', 'reconcile', 'run') or args.target:
        # The extension must share the running module's error types and writer.
        sys.modules.setdefault('remote_harness', sys.modules[__name__])
        import installed_scenarios as scenarios
        require(args.target is not None, 'INSTALLED_TARGET_REQUIRED')
        target, target_pin = scenarios.target_configuration(args.target, config)
        if args.command in ('status', 'report'):
            rows = read_attempts(root)
            print(json.dumps(scenarios.checkpoint(rows, target_pin), indent=2))
            return 0
        require(args.command in ('verify', 'action', 'reconcile', 'run'), 'TARGET_COMMAND_INVALID')
        require((args.command == 'verify' and args.scenario in scenarios.CHECKS + ('local-baseline',))
                or (args.command == 'action' and args.scenario in scenarios.ACTIONS)
                or (args.command == 'run' and args.scenario in scenarios.SEQUENCES)
                or (args.command == 'reconcile' and args.scenario is None), 'SCENARIO_NOT_ALLOWED')
        with Journal(root, pin) as journal:
            results = scenarios.execute(journal, config, target, target_pin, args.command, args.scenario)
        print(json.dumps(results, indent=2))
        # Sequence prerequisite reads may show the expected pre-action state.
        return 0 if results and (results[-1]['outcome'] == 'PASS' if args.command == 'run'
                                else all(row['outcome'] == 'PASS' for row in results)) else 1
    require(args.scenario is None, 'SCENARIO_NOT_ALLOWED')
    if args.command in ('status', 'report'):
        rows = read_attempts(root)
        print(json.dumps(summary(config, rows), indent=2))
        return 0
    with Journal(root, pin) as journal:
        if args.command == 'stage-kit':
            require(not stage_attempted(read_attempts(root)), 'TRANSFER_RECONCILIATION_REQUIRED')
        record = journal.begin(args.command)
        try:
            if args.command in ('collect', 'stop'):
                result = probe(config)
                if args.command == 'stop':
                    require(result['demoProcesses'] == 0 and result['busyPorts'] == 0, 'OWNER_SHUTDOWN_REQUIRED')
                    result['verificationScope'] = 'NO_DETECTED_DEMO_PROCESS_OR_PORT'
            else:
                bundle = Bundle(config['kit'], config['manifestSha256'])
                if args.command == 'preflight':
                    result = preflight(config, bundle)
                elif args.command == 'stage-kit':
                    result = stage(config, bundle)
                else:
                    rows = transfer_rows(config, bundle)
                    require(remote(config, verification_script(config['remoteRoot'], marker(config), rows), timeout=900).strip() == 'VERIFIED', 'TRANSFER_NOT_VERIFIED')
                    result = dict(files=len(rows), resolution='EXACT_CANDIDATE_PRESENT')
            journal.finish(record, 'PASS', 'CHECK_COMPLETED', result)
        except (Error, InstallError, OSError) as exc:
            code = str(exc) if isinstance(exc, (Error, InstallError)) else 'LOCAL_IO_ERROR'
            outcome = 'UNCERTAIN' if args.command == 'stage-kit' else 'BLOCKED'
            journal.finish(record, outcome, code, getattr(exc, 'observations', None))
        print(json.dumps(record, indent=2))
        return 0 if record['outcome'] == 'PASS' else 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (Error, InstallError) as exc:
        print(json.dumps({'outcome': 'BLOCKED', 'code': str(exc)}))
        sys.exit(1)
    except (OSError, ValueError):
        print(json.dumps({'outcome': 'BLOCKED', 'code': 'LOCAL_INPUT_ERROR'}))
        sys.exit(1)
