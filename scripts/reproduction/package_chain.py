# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Remaining input/application assembly over explicit successor manifest pins."""
from pathlib import Path
import stat

from .core import ROOT, require, regular, read_json, atomic_json, digest, run_command, external_volume, GIB
from .artifacts import sha256
from .cloud import matches, relative
from .sources import verify_sources
from . import packaging, host, cloud, containers

CHECKPOINT = 'workspace/releases/1.2.0-rc.1-packaging.json'
MANIFESTS = {'vm-runtime': 'vm-runtime-manifest.json', 'backend-inputs': 'backend-image-manifest.json',
             'application': 'application-manifest.json'}
GROUP_TARGETS = {'host-runtime': 'host-runtime', 'preparation-inputs': 'preparation',
                'cloud-runtime': 'cloud-sdk', 'backend-inputs': 'backend-inputs', 'vm-runtime': 'vm-runtime'}


def upstream(storage, state, target, pin=None):
    found = [(key, value) for key, value in state['builds'].items() if value['target'] == target]
    if pin is not None:
        found = [(key, value) for key, value in found
                 if sha256(regular(storage.path('builds/'+target+'/'+key)/relative(pin['path']))) == pin['sha256']]
    require(len(found) == 1, 'Exactly one completed '+target+' build required')
    key, value = found[0]
    require(digest(value['inputs']) == key, 'Upstream key differs')
    path = storage.path('builds/'+target+'/'+key)
    validator = {'host-runtime': host.verify, 'preparation': packaging.verify_preparation,
                 'cloud-sdk': cloud.verify_output, 'backend-export': containers.verify_export}.get(target, verify)
    validator(path, value['inputs'])
    return key, path


def verify(output, inputs, receipt=None):
    receipt = read_json(host.receipt_path(output)) if receipt is None else receipt
    require(receipt.get('inputs') == inputs and receipt.get('status') == 'ASSEMBLED_NOT_RUNTIME_QUALIFIED'
            and receipt.get('runtimeStarted') is False, 'Package receipt differs')
    manifest = MANIFESTS[inputs['target']]
    matches(output/manifest, receipt['manifest'])
    names = {manifest}
    for name, identity in receipt['stamps'].items():
        name = str(relative(name))
        require(name not in names and packaging.stamp(regular(output/name)) == identity, 'Package output changed')
        names.add(name)
    actual = set()
    for path in output.rglob('*'):
        require(not path.is_symlink(), 'Linked package output')
        if not path.is_dir():
            actual.add(path.relative_to(output).as_posix())
    require(actual == names, 'Package inventory differs')
    return receipt


def assemble(storage, state, target, kit, python, progress, input_checkpoint=None):
    require(storage.profile == 'developer' and target in MANIFESTS, 'Unsupported package target/profile')
    verify_sources(storage, state)
    storage.check(additional=(40 if target == 'application' else 1)*GIB, reserve=90*GIB)
    checkpoint_path = str(relative(input_checkpoint)) if input_checkpoint is not None else CHECKPOINT
    extras = (checkpoint_path,) if input_checkpoint is not None else ()
    trees, revision = packaging.producer(storage, target, extras)
    checkpoint = read_json(ROOT/checkpoint_path)
    chosen, paths = {}, {}
    roles = ('backend-export',) if target == 'backend-inputs' else (
        ('host-runtime', 'preparation') if target == 'vm-runtime' else tuple(GROUP_TARGETS.values()))
    for role in roles:
        if input_checkpoint is not None and role != 'backend-export':
            group = next(group for group, selected in GROUP_TARGETS.items() if selected == role)
            chosen[role], paths[role] = upstream(storage, state, role, checkpoint['manifests'][group])
        else:
            chosen[role], paths[role] = upstream(storage, state, role)
    retained_pin = None
    if target == 'vm-runtime':
        require(kit is not None and external_volume(kit)['uuid'] == storage.volume['uuid'], 'VM kit must be on bound SSD')
        retained_pin = next(r for r in storage.release.value['inputs'] if r['id'] == 'vm-runtime')
        paths['retained-vm'] = matches(Path(kit)/relative(retained_pin['kitPath']), retained_pin).parent
    inputs = {'target': target, 'producerTrees': trees, 'upstream': chosen, 'retainedManifest': retained_pin,
              'checkpoint': checkpoint, 'adapterSha256': sha256(ROOT/'scripts/reproduction/package_chain.py'),
              'workerSha256': sha256(ROOT/'scripts/reproduction/package_worker.py')}
    key = digest(inputs)
    output = storage.path('builds/'+target+'/'+key)
    marker = output.parent/(key+'.inputs.json')
    if key in state['builds']:
        require(state['builds'][key] == {'target': target, 'inputs': inputs}, 'Package state differs')
        verify(output, inputs)
        progress('BUILD_REUSED', target)
        return key
    if output.exists():
        require(marker.exists() and read_json(marker) == inputs, 'Unowned package collision')
        verify(output, inputs)
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        atomic_json(marker, inputs)
        selected = output.parent/(key+'.paths.json')
        atomic_json(selected, {name: str(path) for name, path in paths.items()})
        policy = output.parent/(key+'.sb')
        policy.write_text('(version 1)\n(allow default)\n(deny network*)\n')
        progress('BUILD_STARTED', target)
        result = run_command(['/usr/bin/sandbox-exec', '-f', policy, python, '-I', '-B',
            ROOT/'scripts/reproduction/package_worker.py', ROOT, target, selected, output, checkpoint_path],
            env=storage.environment(), cwd=storage.root, timeout=900)
        output.parent.joinpath(key+'.log').write_bytes((result.stdout+result.stderr)[-2**20:])
        require(result.returncode == 0, 'Package owner failed; inspect retained SSD log')
        manifest = MANIFESTS[target]
        atomic_json(host.receipt_path(output), {'status': 'ASSEMBLED_NOT_RUNTIME_QUALIFIED', 'inputs': inputs,
            'producerRevision': revision, 'runtimeStarted': False,
            'manifest': {'path': manifest, 'bytes': (output/manifest).stat().st_size, 'sha256': sha256(output/manifest)},
            'stamps': {p.relative_to(output).as_posix(): packaging.stamp(regular(p))
                       for p in output.rglob('*') if p.is_file() and p.name != manifest}})
    verify_sources(storage, state)
    require(packaging.producer(storage, target, extras)[0] == trees, 'Producer changed during package assembly')
    verify(output, inputs)
    state['builds'][key] = {'target': target, 'inputs': inputs}
    storage.save(state)
    progress('ASSEMBLED_NOT_RUNTIME_QUALIFIED', target)
    return key
