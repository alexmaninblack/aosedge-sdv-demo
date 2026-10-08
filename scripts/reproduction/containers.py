# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Backend Dockerfile adapters; never start containers or manage the Engine."""
import json
from pathlib import Path
import re
import stat

from .core import require, regular, no_links, read_json, atomic_json, digest, external_volume, GIB
from .build import command
from .artifacts import sha256, identity
from .sources import verify_sources

TARGETS = {'brake-backend': ('brake-health-cloud', 'brake'),
           'tire-backend': ('tire-health-cloud', 'tire')}

class Desktop:
    def __init__(self, storage, docker):
        self.storage = storage
        self.env = storage.environment()
        self.docker = Path(docker).resolve(strict=True)
        # Read the explicitly named local context; never inherit DOCKER_HOST/context.
        endpoint = command([self.docker, '--config', Path.home() / '.docker', 'context', 'inspect', 'desktop-linux', '--format',
                            '{{.Endpoints.docker.Host}}'], self.env, storage.root)
        require(endpoint.startswith('unix:///'), 'Only local Docker Desktop is supported')
        socket = Path(endpoint[len('unix://'):])
        require(stat.S_ISSOCK(socket.stat().st_mode), 'Local Docker Desktop socket unavailable')
        settings = Path.home() / 'Library/Group Containers/group.com.docker/settings-store.json'
        folder = read_json(settings).get('DataFolder')
        require(isinstance(folder, str), 'Move Docker disk to the selected external SSD before container builds')
        self.disk = regular(Path(folder) / 'Docker.raw')
        volume = external_volume(self.disk)
        require(volume['uuid'] == storage.volume['uuid'], 'Docker disk must be on the selected external SSD')
        # Check the actual open backing disk, not just a pending settings value.
        require(command(['/usr/sbin/lsof', '-t', self.disk], self.env, storage.root),
                'Docker backing disk is not active')
        config = storage.path('cache/docker-client')
        config.mkdir(parents=True, exist_ok=True)
        plugins = self.docker.parent.parent / 'cli-plugins'
        require((plugins / 'docker-buildx').is_file(), 'Docker Desktop build plugin unavailable')
        config_value = {'cliPluginsExtraDirs': [str(plugins)]}
        config_path = config / 'config.json'
        if config_path.exists():
            require(read_json(config_path) == config_value, 'Unowned Docker build client configuration')
        else:
            require(not any(config.iterdir()), 'Unowned Docker client directory')
            atomic_json(config_path, config_value)
        self.args = [self.docker, '--config', config, '--host', endpoint]
        self.env['DOCKER_CONFIG'] = str(config)
        self.env['BUILDX_CONFIG'] = str(storage.path('cache/buildx'))
        info = json.loads(self.run(['info', '--format',
            '{"os":{{json .OperatingSystem}},"arch":{{json .Architecture}},"type":{{json .OSType}}}']))
        require(info == {'os': 'Docker Desktop', 'arch': 'aarch64', 'type': 'linux'},
                'Expected local ARM64 Docker Desktop')
        self.version = self.run(['version', '--format', '{{.Server.Version}}'])

    def run(self, args, timeout=30):
        self.storage.check(additional=2*GIB)
        return command(self.args + args, self.env, self.storage.root, timeout=timeout)

    def image(self, image_id, revision, team):
        require(re.fullmatch('sha256:[a-f0-9]{64}', image_id), 'Invalid backend image identity')
        row = json.loads(self.run(['image', 'inspect', image_id, '--format',
            '{"id":{{json .Id}},"os":{{json .Os}},"arch":{{json .Architecture}},'
            '"user":{{json .Config.User}},"labels":{{json .Config.Labels}}}']))
        require(row['id'] == image_id and row['os'] == 'linux' and row['arch'] == 'arm64'
                and row['user'] == 'node' and row['labels'].get('org.opencontainers.image.revision') == revision
                and row['labels'].get('tech.aosedge.demo.team') == team,
                'Backend image platform/source/runtime identity differs')
        return row

def verify_output(output, inputs, desktop=None):
    receipt = read_json(output / 'build-receipt.json')
    require(receipt.get('status') == 'BUILT_NOT_RUNTIME_QUALIFIED' and receipt.get('inputs') == inputs
            and receipt.get('containersStarted') is False and receipt.get('published') is False,
            'Backend build receipt differs')
    image_id = regular(output / 'image-id').read_text().strip()
    require(receipt.get('imageId') == image_id and re.fullmatch('sha256:[a-f0-9]{64}', image_id),
            'Backend image receipt differs')
    require({p.name for p in output.iterdir()} == {'build-receipt.json', 'image-id'}, 'Unexpected backend output files')
    if desktop:
        desktop.image(image_id, inputs['source']['revision'], inputs['team'])
    return receipt

def assemble(storage, state, target, docker, prepare_dependencies, progress):
    require(storage.profile == 'developer' and target in TARGETS, 'Unsupported backend build profile/target')
    verify_sources(storage, state)
    storage.check(additional=2*GIB)
    client = Desktop(storage, docker)
    source, team = TARGETS[target]
    checkout = storage.path('sources/' + source)
    owner = regular(checkout / 'Dockerfile')
    inputs = {'source': state['sources'][source], 'recipeSha256': sha256(owner),
              'platform': 'linux/arm64', 'team': team, 'docker': client.version}
    key = digest(inputs)
    output = storage.path('builds/' + target + '/' + key)
    marker = output.parent / (key + '.inputs.json')
    if key in state['builds']:
        require(state['builds'][key] == {'target': target, 'inputs': inputs}, 'Backend build key differs')
        verify_output(output, inputs, client)
        progress('BUILD_REUSED', target)
        return key
    if output.exists():
        require(marker.exists() and read_json(marker) == inputs, 'Unowned backend build collision')
        # An iidfile is only written after successful export; reconcile without rebuilding.
        image_id = regular(output / 'image-id').read_text().strip()
        client.image(image_id, inputs['source']['revision'], team)
    else:
        require(prepare_dependencies, 'First backend build requires --prepare-dependencies for pinned public inputs')
        output.parent.mkdir(parents=True, exist_ok=True)
        atomic_json(marker, inputs)
        output.mkdir(mode=0o700)
        progress('BUILD_STARTED', target)
        client.run(['build', '--platform', 'linux/arm64', '--progress', 'plain', '--iidfile', output / 'image-id',
                    '--label', 'org.opencontainers.image.revision=' + inputs['source']['revision'],
                    '--label', 'tech.aosedge.demo.team=' + team, '--file', owner, checkout], timeout=600)
        image_id = regular(output / 'image-id').read_text().strip()
        client.image(image_id, inputs['source']['revision'], team)
    verify_sources(storage, state)
    receipt_path = output / 'build-receipt.json'
    if not receipt_path.exists():
        atomic_json(receipt_path, {'status': 'BUILT_NOT_RUNTIME_QUALIFIED', 'inputs': inputs,
                                  'imageId': image_id, 'containersStarted': False, 'published': False})
    verify_output(output, inputs, client)
    state['builds'][key] = {'target': target, 'inputs': inputs}
    storage.save(state)
    progress('BUILT_NOT_RUNTIME_QUALIFIED', target)
    return key

def verify_export(output, inputs):
    receipt = read_json(output / 'build-receipt.json')
    owner = read_json(output / 'archive-receipt.json')
    archive = regular(output / 'images.tar')
    require(receipt.get('inputs') == inputs
            and receipt.get('status') == 'OFFLINE_VERIFIED_NOT_RUNTIME_QUALIFIED'
            and owner.get('status') == 'OFFLINE_INTEGRITY_VERIFIED_NOT_CLEAN_ENGINE_QUALIFIED'
            and owner.get('operatorDataIncluded') is False
            and owner.get('externalDistributionApproved') is False,
            'Backend export receipt differs')
    require({(r['team'], r['imageId'], r['source']) for r in owner['images']} ==
            {(r['team'], r['localImageId'], r['source']) for r in inputs['images']},
            'Backend export image identity differs')
    require(archive.stat().st_size == owner['archiveBytes'], 'Backend archive size differs')
    if identity(archive) != receipt.get('archiveIdentity'):
        require(sha256(archive) == owner['archiveSha256'], 'Backend archive digest differs')
        receipt['archiveIdentity'] = identity(archive)
        atomic_json(output / 'build-receipt.json', receipt)
    require({p.name for p in output.iterdir()} ==
            {'images.tar', 'input-inventory.json', 'archive-receipt.json', 'build-receipt.json'},
            'Unexpected backend export files')
    require(read_json(output / 'input-inventory.json') == {'backendImages': inputs['images']},
            'Backend export inventory differs')
    return owner

def export(storage, state, docker, prepare_dependencies, progress, python):
    keys = {target: assemble(storage, state, target, docker, prepare_dependencies, progress)
            for target in TARGETS}
    client = Desktop(storage, docker)
    integration = storage.path('sources/integration')
    owner = integration / 'scripts/distribution/backend_archive.py'
    images = []
    for target, key in keys.items():
        inputs = state['builds'][key]['inputs']
        receipt = verify_output(storage.path('builds/' + target + '/' + key), inputs, client)
        images.append({'team': inputs['team'], 'source': inputs['source']['revision'],
                       'localImageId': receipt['imageId']})
    inputs = {'sources': state['sources']['integration'], 'builds': keys, 'images': images,
              'recipeSha256': sha256(owner)}
    key = digest(inputs)
    output = storage.path('builds/backend-export/' + key)
    marker = output.parent / (key + '.inputs.json')
    if key in state['builds']:
        require(state['builds'][key] == {'target': 'backend-export', 'inputs': inputs}, 'Export build key differs')
        verify_export(output, inputs)
        progress('BUILD_REUSED', 'backend-export')
        return key
    if output.exists():
        require(marker.exists() and read_json(marker) == inputs, 'Unowned backend export collision')
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        atomic_json(marker, inputs)
        output.mkdir(mode=0o700)
    inventory_path = output / 'input-inventory.json'
    if inventory_path.exists():
        require(read_json(inventory_path) == {'backendImages': images}, 'Export inventory collision')
    else:
        atomic_json(inventory_path, {'backendImages': images})
    archive = output / 'images.tar'
    if not archive.exists():
        progress('BUILD_STARTED', 'backend-export')
        client.run(['image', 'save', '--output', archive, *[r['localImageId'] for r in images]], timeout=180)
    receipt_path = output / 'archive-receipt.json'
    if not receipt_path.exists():
        command([python, '-B', owner, '--archive', archive, '--inventory', inventory_path,
                 '--receipt', receipt_path], storage.environment(), storage.root, timeout=180)
    receipt = read_json(receipt_path)
    require(sha256(archive) == receipt['archiveSha256'], 'Export archive differs from owner proof')
    summary = output / 'build-receipt.json'
    if not summary.exists():
        atomic_json(summary, {'status': 'OFFLINE_VERIFIED_NOT_RUNTIME_QUALIFIED', 'inputs': inputs,
                              'archiveIdentity': identity(archive)})
    verify_export(output, inputs)
    verify_sources(storage, state)
    state['builds'][key] = {'target': 'backend-export', 'inputs': inputs}
    storage.save(state)
    progress('BUILT_NOT_RUNTIME_QUALIFIED', 'backend-export')
    return key
