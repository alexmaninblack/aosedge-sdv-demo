# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Explicit, pinned local Docker image preparation; no runtime lifecycle."""

import json
import os
from pathlib import Path
import re
import subprocess

from installation_inputs import Bundle, require, unlinked
from aosedge_demo_orchestrator import backend_inputs, installed_control, runtime_paths
from aosedge_demo_orchestrator.environment import EnvironmentService, JOURNAL, atomic_json

DOCKER = '/Applications/Docker.app/Contents/Resources/bin/docker'
RECORD = '.local/demo-control/backend-preparation.json'
IMAGE = re.compile(r'sha256:[0-9a-f]{64}')


def request(value):
    from setup_launch import request as checked_path
    require(set(value) == {'action', 'state'} and value['action'] == 'prepare-backends',
            'SETUP_REQUEST_INVALID')
    checked_path(dict(value, action='launch'))
    return value


class Docker:
    def __init__(self):
        require(Path(DOCKER).is_file(), 'SETUP_BACKENDS_DOCKER_MISSING')
        self.env = dict(HOME=str(Path.home()), PATH='/usr/bin:/bin:/usr/sbin:/sbin', LC_ALL='C')
        self.endpoint = 'unix://' + str(Path.home() / '.docker/run/docker.sock')

    def read(self, *args, local=True):
        command = [DOCKER, *(['--host', self.endpoint] if local else []), *args]
        try:
            result = subprocess.run(command, capture_output=True, timeout=5, env=self.env)
        except (OSError, subprocess.SubprocessError):
            raise ValueError('SETUP_BACKENDS_ENGINE_UNAVAILABLE') from None
        require(result.returncode == 0, 'SETUP_BACKENDS_ENGINE_UNAVAILABLE')
        require(len(result.stdout) <= 262144, 'SETUP_BACKENDS_RESPONSE_INVALID')
        return result.stdout.decode('utf-8')

    def engine(self):
        require(self.read('context', 'show', local=False).strip() == 'desktop-linux',
                'SETUP_BACKENDS_LOCAL_CONTEXT_REQUIRED')
        endpoint = json.loads(self.read('context', 'inspect', 'desktop-linux',
                              '--format', '{{json .Endpoints.docker.Host}}', local=False))
        require(endpoint == self.endpoint, 'SETUP_BACKENDS_LOCAL_CONTEXT_REQUIRED')
        value = json.loads(self.read('info', '--format',
            '{"id":{{json .ID}},"os":{{json .OSType}},"arch":{{json .Architecture}}}'))
        require(isinstance(value, dict) and value.get('os') == 'linux'
                and value.get('arch') in ('aarch64', 'arm64'), 'SETUP_BACKENDS_PLATFORM_UNSUPPORTED')
        identity = value.get('id')
        require(isinstance(identity, str) and re.fullmatch(r'[A-Za-z0-9:.-]{1,128}', identity),
                'SETUP_BACKENDS_RESPONSE_INVALID')
        return identity

    def available(self, rows):
        # The pinned archive is intentionally untagged. Docker's default list
        # can omit those objects even though exact image inspect succeeds.
        ids = set(self.read('image', 'ls', '--all', '--quiet', '--no-trunc').split())
        require(all(IMAGE.fullmatch(x) for x in ids), 'SETUP_BACKENDS_RESPONSE_INVALID')
        found = []
        for row in rows:
            if row['imageId'] not in ids:
                continue
            value = json.loads(self.read('image', 'inspect', row['imageId'], '--format',
                '{"id":{{json .Id}},"os":{{json .Os}},"arch":{{json .Architecture}},"labels":{{json .Config.Labels}}}'))
            require(isinstance(value, dict) and value.get('id') == row['imageId']
                    and value.get('os') == 'linux' and value.get('arch') == 'arm64'
                    and isinstance(value.get('labels'), dict)
                    and value['labels'].get('tech.aosedge.demo.team') == row['team']
                    and value['labels'].get('org.opencontainers.image.revision') == row['sourceRevision'],
                    'SETUP_BACKENDS_IMAGE_MISMATCH')
            found.append(row['imageId'])
        return found

    def load(self, stream):
        # No raw daemon output in UI/evidence; the following reads decide success.
        try:
            subprocess.run([DOCKER, '--host', self.endpoint, 'image', 'load', '--quiet'],
                stdin=stream, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                env=self.env, timeout=75, check=False)
        except (OSError, subprocess.SubprocessError):
            pass


def prepare(env, pin, inputs, docker, emit):
    path = unlinked(env.root / RECORD)
    require(not path.with_name(path.name + '.pending').exists() and not path.with_name(path.name + '.pending').is_symlink(), 'SETUP_BACKENDS_RECORD_PENDING')
    prior = None
    if path.exists():
        runtime_paths.private(path)
        prior, _ = runtime_paths.small_json(path, 4096, owned=True)
        require(isinstance(prior, dict) and set(prior) ==
                {'schemaVersion', 'manifestSha256', 'archiveSha256', 'engineId', 'attempt'}
                and type(prior['schemaVersion']) is int and prior['schemaVersion'] == 1
                and prior['attempt'] in ('ATTEMPTED', 'RECONCILED')
                and isinstance(prior['manifestSha256'], str)
                and re.fullmatch(r'[0-9a-f]{64}', prior['manifestSha256'])
                and (prior['manifestSha256'] == pin or prior['attempt'] == 'RECONCILED')
                and prior['archiveSha256'] == inputs.digest,
                'SETUP_BACKENDS_RECORD_INVALID')
    emit(dict(kind='progress', stage='BACKENDS_VERIFYING_ARCHIVE'))
    archive = inputs.archive()
    rows = [inputs.candidate(team) for team in ('brake', 'tire')]
    emit(dict(kind='progress', stage='BACKENDS_CHECKING_ENGINE'))
    engine = docker.engine()
    require(prior is None or prior['engineId'] == engine, 'SETUP_BACKENDS_ENGINE_CHANGED')
    record = dict(schemaVersion=1, manifestSha256=pin, archiveSha256=inputs.digest,
                  engineId=engine, attempt='ATTEMPTED')
    imported = False
    if len(docker.available(rows)) != 2:
        require(prior is None or prior['attempt'] == 'RECONCILED', 'SETUP_BACKENDS_IMPORT_UNCONFIRMED')
        # Recheck the verified archive at the consumption boundary, keep its FD
        # open, then persist intent before sending any byte to the daemon.
        archive = inputs.archive()
        fd = os.open(archive, os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(fd, 'rb') as stream:
            current, opened = archive.stat(), os.fstat(stream.fileno())
            require((current.st_dev, current.st_ino, current.st_size, current.st_mtime_ns) ==
                    (opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns),
                    'SETUP_BACKENDS_ARCHIVE_CHANGED')
            require(docker.engine() == engine, 'SETUP_BACKENDS_ENGINE_CHANGED')
            atomic_json(path, record)
            emit(dict(kind='progress', stage='BACKENDS_IMPORTING'))
            imported = True
            docker.load(stream)
    emit(dict(kind='progress', stage='BACKENDS_RECONCILING'))
    require(docker.engine() == engine, 'SETUP_BACKENDS_ENGINE_CHANGED')
    require(len(docker.available(rows)) == 2, 'SETUP_BACKENDS_IMPORT_UNCONFIRMED')
    # A completed older-kit import of these exact bytes is not an unresolved
    # import. Advance its pin only after both images and the same engine have
    # been observed again. Never carry an uncertain cross-kit attempt forward.
    if imported or prior and (prior['attempt'] == 'ATTEMPTED' or prior['manifestSha256'] != pin):
        atomic_json(path, dict(record, attempt='RECONCILED'))
    return dict(status='BACKEND_IMAGES_AVAILABLE', runtimeChanged=False, cloudAccessed=False,
                demoReady=False, dockerEngineChecked=True, imagesVerified=2, importAttempted=imported)


def perform(value, pin, emit=lambda event: None):
    emit(dict(kind='progress', stage='BACKENDS_VERIFYING_SELECTION'))
    state, identity = runtime_paths.instance(value['state'])
    selection = installed_control.selection(state, identity)
    require(selection and selection['current'] == pin, 'SETUP_LOCAL_PREPARATION_REQUIRED')
    program = Path(selection['storePath']) / 'versions' / pin / 'aosedge-sdv-demo'
    with runtime_paths.installed_session(state, _program=program):
        # Authenticate the consumed lock against the independent full-kit pin.
        bundle = Bundle(program.parent, pin)
        bundle.verify_file('aosedge-sdv-demo/' + backend_inputs.LOCK)
        env = EnvironmentService(root=state)
        with env._writer():
            require(not (state / JOURNAL).exists() and not (state / JOURNAL).is_symlink()
                    and not (state / (JOURNAL + '.pending')).exists()
                    and not (state / (JOURNAL + '.pending')).is_symlink(), 'SETUP_BACKENDS_RETAINED_RUN')
            inputs = backend_inputs.selected(env)
            require(inputs is not None, 'SETUP_BACKENDS_INPUTS_REQUIRED')
            return prepare(env, pin, inputs, Docker(), emit)
