# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Bounded native setup protocol. Only trusted embedded tooling is imported."""

import json
import os
from pathlib import Path
import platform
import plistlib
import re
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
from installation import Store, RESERVE, volume_identity
from installation_inputs import Bundle, InstallError, SHA, parse, read_small, require, unlinked
from version_management import Versions, compatible
from aosedge_demo_orchestrator import runtime_paths

LIMIT = 16384
BASE = {'action', 'source', 'store', 'state'}


def release():
    value = parse(read_small(Path(__file__).with_name('setup_release.json'), 4096))
    require(isinstance(value, dict) and set(value) == {'schemaVersion', 'label', 'manifestSha256'}
            and type(value['schemaVersion']) is int and value['schemaVersion'] == 1
            and isinstance(value['label'], str) and len(value['label']) < 120
            and isinstance(value['manifestSha256'], str) and SHA.fullmatch(value['manifestSha256']),
            'SETUP_RELEASE_INVALID')
    return value


def supported_platform():
    version = platform.mac_ver()[0].split('.')[0]
    require(sys.platform == 'darwin' and platform.machine() == 'arm64'
            and version.isdigit() and int(version) >= 26, 'SETUP_PLATFORM_UNSUPPORTED')


def internal_volume(path):
    before = path.stat().st_dev
    result = subprocess.run(['/bin/df', '-P', str(path)], capture_output=True, timeout=15,
                            env={'PATH': '/usr/bin:/bin:/usr/sbin:/sbin', 'LC_ALL': 'C'})
    lines = result.stdout.decode('utf-8').splitlines()
    require(result.returncode == 0 and len(lines) == 2 and lines[1].split(), 'SETUP_STATE_VOLUME_UNAVAILABLE')
    device = lines[1].split()[0]
    require(re.fullmatch(r'/dev/disk\d+(?:s\d+)+', device), 'SETUP_STATE_VOLUME_UNAVAILABLE')
    result = subprocess.run(['/usr/sbin/diskutil', 'info', '-plist', device], capture_output=True, timeout=15)
    require(result.returncode == 0, 'SETUP_STATE_VOLUME_UNAVAILABLE')
    info = plistlib.loads(result.stdout)
    require(info.get('Internal') is True and info.get('GlobalPermissionsEnabled') is True
            and info.get('DeviceNode') == device and path.stat().st_dev == before
            and Path(info['MountPoint']).stat().st_dev == before, 'SETUP_STATE_INTERNAL_REQUIRED')


def request(raw):
    require(len(raw) <= LIMIT, 'SETUP_REQUEST_TOO_LARGE')
    value = parse(raw)
    require(isinstance(value, dict), 'SETUP_REQUEST_INVALID')
    action = value.get('action')
    if action in ('cloud-inspect', 'cloud-save', 'cloud-check'):
        from setup_cloud import request as cloud_request
        return cloud_request(value)
    require(action in ('preflight', 'install', 'prepare'), 'SETUP_ACTION_INVALID')
    keys = BASE if action == 'preflight' else BASE | {'volumeUUID', 'revision'}
    require(set(value) == keys, 'SETUP_REQUEST_INVALID')
    for key in ('source', 'store', 'state'):
        path = value[key]
        require(isinstance(path, str) and 1 < len(os.fsencode(path)) <= 1024
                and path.startswith('/') and not path.startswith('//') and str(Path(path)) == path
                and not any(ord(c) < 32 or c == ',' for c in path)
                and '..' not in Path(path).parts, 'SETUP_PATH_INVALID')
        value[key] = unlinked(path)
    for a, b in (('source', 'store'), ('source', 'state'), ('store', 'state')):
        require(not value[a].is_relative_to(value[b]) and not value[b].is_relative_to(value[a]),
                'SETUP_PATH_OVERLAP')
    if action != 'preflight':
        require(type(value['revision']) is int and 0 <= value['revision'] < 2**53,
                'SELECTION_REVISION_INVALID')
        require(isinstance(value['volumeUUID'], str), 'INSTALL_VOLUME_ID_INVALID')
    return value


def state_check(path):
    runtime_paths.canonical(path)
    require(path.parent.is_dir(), 'SETUP_STATE_PARENT_MISSING')
    require(len(os.fsencode(path / '.run/demo-current/control/control.sock')) < 104,
            'INSTALLED_SOCKET_PATH_TOO_LONG')
    probe = path if path.exists() else path.parent
    require(probe.stat().st_dev == Path.home().stat().st_dev, 'SETUP_STATE_INTERNAL_REQUIRED')
    internal_volume(probe)
    if path.exists():
        runtime_paths.instance(path)


def perform(value, pin, emit=lambda event: None):
    supported_platform()
    if value['action'].startswith('cloud-'):
        from setup_cloud import perform as cloud_perform
        state_check(Path(value['state']))
        return cloud_perform(value, pin, emit)
    source, destination, state = (value[k] for k in ('source', 'store', 'state'))
    state_check(state)
    require(destination.parent.is_dir(), 'INSTALL_PARENT_MISSING')
    uuid = value.get('volumeUUID') or volume_identity(destination if destination.exists() else destination.parent)
    store = Store(destination, uuid, volume_probe=volume_identity)
    action = value['action']
    if action == 'preflight':
        bundle = store.plan(source, pin)
        compatible(bundle)
        record = Versions(store, state).read() if state.exists() else None
        return dict(status='PREFLIGHT_PASSED', volumeUUID=store.uuid,
                    revision=record['revision'] if record else 0, files=len(bundle.rows),
                    logicalBytes=bundle.total_bytes, reserveBytes=RESERVE,
                    payloadDigestsVerified=False, runtimeChanged=False, cloudAccessed=False)
    if action == 'install':
        emit(dict(kind='progress', stage='VERIFYING_AND_INSTALLING'))
        last = [0.0]
        def progress(event):
            now = time.monotonic()
            if now - last[0] >= .2 or event['files'] == event['totalFiles']:
                emit(dict(event, kind='progress')); last[0] = now
        return store.install(source, pin, progress=progress)
    # Check installed metadata/receipt presence before creating private state.
    require(store.inspect(), 'INSTALL_STORE_MISSING')
    bundle = Bundle(store.root / 'versions' / pin, pin)
    compatible(bundle)
    receipt, _ = runtime_paths.small_json(store.root / 'receipts' / (pin + '.json'), 4096, owned=True)
    require(isinstance(receipt, dict) and receipt == store.receipt(bundle, bool(receipt.get('reused'))),
            'INSTALL_RECEIPT_INVALID')
    require(state.exists() or value['revision'] == 0, 'SELECTION_STALE_REVISION')
    emit(dict(kind='progress', stage='VERIFYING_LOCAL_SELECTION'))
    runtime_paths.create_instance(state)
    result = Versions(store, state).change('select', value['revision'], pin)
    return dict(result, cloudAccessed=False, cloudConfigured=False, demoReady=False,
                dockerApplicationPresent=Path('/Applications/Docker.app').is_dir(),
                dockerEngineChecked=False)


def error_code(error):
    value = str(error)
    if isinstance(error, ValueError) and re.fullmatch(r'[A-Z][A-Z0-9_]{2,100}', value):
        return value
    return 'SETUP_OPERATION_FAILED'


def main():
    def emit(value):
        print(json.dumps(value, separators=(',', ':')), flush=True)
    try:
        # Native deadlines terminate only this helper's process group, including
        # any bounded Cloud worker. Never leave an orphan worker after timeout.
        if os.getpgrp() != os.getpid():
            os.setpgid(0, 0)
        value = request(sys.stdin.buffer.read(LIMIT + 1))
        result = perform(value, release()['manifestSha256'], emit)
        emit(dict(kind='result', result=result))
        return 0
    except (OSError, ValueError, KeyError, TypeError, AttributeError,
            subprocess.SubprocessError, plistlib.InvalidFileException) as error:
        emit(dict(kind='error', code=error_code(error)))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
