# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Integrated presentation of existing installation owners; no new lifecycle."""

import json
import os
from pathlib import Path
import re
import shutil
import tempfile

from installation_inputs import Bundle, require, unlinked
from aosedge_demo_orchestrator import installed_control, runtime_paths, backend_inputs
from aosedge_demo_orchestrator.cloud_connection import CloudConnection
from aosedge_demo_orchestrator.environment import EnvironmentService
from setup_backends import Docker
from version_management import compatible

ACTIONS = ('setup-status', 'setup-install', 'install-launcher')


def request(value):
    action = value.get('action')
    require(action in ACTIONS, 'SETUP_ACTION_INVALID')
    if action == 'setup-install':
        from setup_bridge import request as base_request
        require(set(value) == {'action', 'source', 'store', 'state'}, 'SETUP_REQUEST_INVALID')
        return dict(base_request(json.dumps(dict(value, action='preflight')).encode()), action=action)
    from setup_launch import request as path_request
    require(set(value) == {'action', 'state'}, 'SETUP_REQUEST_INVALID')
    path_request(dict(value, action='launch'))
    return value


def backend_observation(state, pin):
    root, identity = runtime_paths.instance(state)
    selected = installed_control.selection(root, identity)
    require(selected and selected['current'] == pin, 'SETUP_LOCAL_PREPARATION_REQUIRED')
    program = Path(selected['storePath']) / 'versions' / pin / 'aosedge-sdv-demo'
    with runtime_paths.installed_session(root, _program=program):
        Bundle(program.parent, pin).verify_file('aosedge-sdv-demo/' + backend_inputs.LOCK)
        inputs = backend_inputs.selected(EnvironmentService(root=root))
        require(inputs is not None, 'SETUP_BACKENDS_INPUTS_REQUIRED')
        docker = Docker()
        docker.engine()
        require(len(docker.available([inputs.candidate(team) for team in ('brake', 'tire')])) == 2,
                'SETUP_BACKENDS_IMAGES_MISSING')


def status(state, pin):
    state = unlinked(state)
    if not state.exists():
        return dict(status='SETUP_NOT_INSTALLED', runtimeChanged=False, cloudAccessed=False,
                    demoReady=False, localInstalled=False, backendsObserved=False, launcherObserved=False)
    root, identity = runtime_paths.instance(state)
    selected = installed_control.selection(root, identity)
    if not selected or selected['current'] is None:
        return dict(status='SETUP_NOT_INSTALLED', runtimeChanged=False, cloudAccessed=False,
                    demoReady=False, localInstalled=False, backendsObserved=False, launcherObserved=False)
    if selected['current'] != pin:
        return dict(status='SETUP_UPDATE_AVAILABLE', runtimeChanged=False, cloudAccessed=False,
                    demoReady=False, localInstalled=False, backendsObserved=False,
                    launcherObserved=False)
    program = Path(selected['storePath']) / 'versions' / pin / 'aosedge-sdv-demo'
    with runtime_paths.installed_session(root, _program=program):
        compatible(Bundle(program.parent, pin))
        config = CloudConnection(EnvironmentService(root=root))._configuration()
        profiles = config.get('cloudProfiles', {})
        result = dict(status='SETUP_INSTALLED_OBSERVED', runtimeChanged=False, cloudAccessed=False,
                      demoReady=False, localInstalled=True, backendsObserved=False,
                      launcherObserved=False,
                      storePath=selected['storePath'],
                      oemPath=profiles.get('oem-delivery', {}).get('credential', ''),
                      spPath=profiles.get('service-provider', {}).get('credential', ''))
    try:
        backend_observation(root, pin)
        result['backendsObserved'] = True
    except ValueError as error:
        code = str(error)
        require(re.fullmatch(r'SETUP_BACKENDS_[A-Z_]+', code), 'SETUP_BACKENDS_OBSERVATION_FAILED')
        result['prerequisite'] = code
    application = unlinked(Path.home() / 'Applications/AosEdge SDV Lab.app')
    if application.exists():
        signature(application)
        result['launcherObserved'] = json.loads((application / 'Contents/Resources/tooling/scripts/distribution/setup_release.json').read_bytes())['manifestSha256'] == pin
    return result


def signature(app):
    from setup_signing import run, IDENTIFIER
    run(['/usr/bin/codesign', '--verify', '--deep', '--strict', str(app)], 'SETUP_LAUNCHER_SIGNATURE_INVALID')
    text = run(['/usr/bin/codesign', '-dvv', str(app)], 'SETUP_LAUNCHER_SIGNATURE_INVALID')
    require('Identifier=' + IDENTIFIER in text.splitlines() and 'Signature=adhoc' not in text.splitlines(),
            'SETUP_LAUNCHER_IDENTITY_INVALID')
    teams = re.findall(r'^TeamIdentifier=([A-Z0-9]{10})$', text, re.M)
    require(len(teams) == 1, 'SETUP_LAUNCHER_IDENTITY_INVALID')
    return teams[0]


def launcher(pin):
    # Only the app containing this trusted helper can install itself.
    source = unlinked(Path(__file__).parents[5])
    require(source.suffix == '.app', 'SETUP_LAUNCHER_BUNDLE_REQUIRED')
    team = signature(source)
    leaf = 'Contents/Resources/tooling/scripts/distribution/setup_release.json'
    require(json.loads((source / leaf).read_bytes())['manifestSha256'] == pin, 'SETUP_LAUNCHER_PIN_MISMATCH')
    parent = unlinked(Path.home() / 'Applications')
    if not parent.exists():
        parent.mkdir(mode=0o700)
    require(parent.is_dir() and parent.stat().st_uid == os.getuid(), 'SETUP_LAUNCHER_PARENT_UNSAFE')
    target = unlinked(parent / 'AosEdge SDV Lab.app')
    if target == source:
        return
    if target.exists():
        require(signature(target) == team, 'SETUP_LAUNCHER_FOREIGN_APPLICATION')
        installed_control.unused((target,))
        # Replacing a nonempty app is not atomic. Preserve it until the verified
        # copy exists, then use a fixed recoverable predecessor, not delete first.
    previous = unlinked(parent / '.AosEdge SDV Lab.previous.app')
    if previous.exists():
        require(signature(previous) == team, 'SETUP_LAUNCHER_RECONCILIATION_REQUIRED')
        installed_control.unused((previous, target))
        if not target.exists():
            previous.rename(target)
        else:
            require(signature(target) == team and json.loads((target / leaf).read_bytes())['manifestSha256'] == pin,
                    'SETUP_LAUNCHER_RECONCILIATION_REQUIRED')
            shutil.rmtree(previous)
    with tempfile.TemporaryDirectory(prefix='.sdv-launcher-', dir=parent) as scratch:
        copied = Path(scratch) / target.name
        shutil.copytree(source, copied)
        require(signature(copied) == team and json.loads((copied / leaf).read_bytes())['manifestSha256'] == pin,
                'SETUP_LAUNCHER_TRANSFER_INVALID')
        if target.exists():
            require(signature(target) == team, 'SETUP_LAUNCHER_FOREIGN_APPLICATION')
            installed_control.unused((target,))
            target.rename(previous)
        try:
            copied.rename(target)
        except OSError:
            if previous.exists() and not target.exists():
                previous.rename(target)
            raise
        require(signature(target) == team, 'SETUP_LAUNCHER_TRANSFER_INVALID')
        if previous.exists():
            shutil.rmtree(previous)


def perform(value, pin, emit=lambda event: None):
    from setup_bridge import perform as step
    state = unlinked(value['state'])
    if value['action'] == 'setup-status':
        return status(state, pin)
    if value['action'] == 'install-launcher':
        emit(dict(kind='progress', stage='INSTALLING_LAUNCHER'))
        require(status(state, pin)['localInstalled'], 'SETUP_LOCAL_PREPARATION_REQUIRED')
        launcher(pin)
        return dict(status='SETUP_LAUNCHER_INSTALLED', runtimeChanged=False, cloudAccessed=False, demoReady=False)
    emit(dict(kind='progress', stage='CHECKING_DOCKER'))
    Docker().engine()  # Prerequisite before any copy or instance mutation.
    observed = status(state, pin)
    if not observed['localInstalled']:
        base = dict(value, action='preflight')
        checked = step(base, pin, emit)
        base.update(volumeUUID=checked['volumeUUID'], revision=checked['revision'])
        step(dict(base, action='install'), pin, emit)
        step(dict(base, action='prepare'), pin, emit)
    if not observed.get('backendsObserved'):
        step(dict(action='prepare-backends', state=str(state)), pin, emit)
    emit(dict(kind='progress', stage='INSTALLING_LAUNCHER'))
    launcher(pin)
    return dict(status='SETUP_LOCAL_INSTALLED', runtimeChanged=False, cloudAccessed=False,
                demoReady=False, localInstalled=True, backendsObserved=True, launcherObserved=True)
