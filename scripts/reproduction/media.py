# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Explicit stable-signed Setup and complete media builds, never installation."""
from pathlib import Path

from .core import ROOT, require, regular, read_json, atomic_json, digest, run_command, GIB
from .artifacts import sha256
from .sources import verify_sources
from . import packaging, package_chain, host

TARGETS = ('setup', 'dmg')
RELEASE = 'workspace/releases/1.2.0-rc.1-setup.json'


def verify(output, inputs):
    receipt = read_json(host.receipt_path(output))
    require(receipt.get('inputs') == inputs and receipt.get('status') == 'BUILT_NOT_INSTALLED'
            and receipt.get('published') is False, 'Media receipt differs')
    names = set()
    for name, identity in receipt['stamps'].items():
        from .cloud import relative
        name = str(relative(name))
        require(name not in names and packaging.stamp(regular(output/name)) == identity, 'Media output changed')
        names.add(name)
    actual = set()
    for path in output.rglob('*'):
        require(not path.is_symlink(), 'Linked media output')
        if not path.is_dir():
            actual.add(path.relative_to(output).as_posix())
    require(actual == names and names, 'Media inventory differs')
    return receipt


def assemble(storage, state, target, python, signing_identity, progress,
             input_checkpoint=None, release_checkpoint=None):
    require(storage.profile == 'developer' and target in TARGETS, 'Unsupported media target/profile')
    verify_sources(storage, state)
    storage.check(additional=(76 if target == 'dmg' else 2)*GIB, reserve=90*GIB)
    from .cloud import relative
    require((input_checkpoint is None) == (release_checkpoint is None), 'Select both group and Setup checkpoints')
    checkpoint_path = str(relative(input_checkpoint)) if input_checkpoint is not None else package_chain.CHECKPOINT
    release_path = str(relative(release_checkpoint)) if release_checkpoint is not None else RELEASE
    extras = (checkpoint_path, release_path) if input_checkpoint is not None else ()
    trees, revision = packaging.producer(storage, target, extras)
    trusted = read_json(ROOT/release_path)
    if release_checkpoint is not None:
        kit_key, kit = package_chain.upstream(storage, state, 'application',
            {'path':'application-manifest.json', 'sha256':trusted['manifestSha256']})
    else:
        kit_key, kit = package_chain.upstream(storage, state, 'application')
    require(sha256(regular(kit/'application-manifest.json')) == trusted['manifestSha256'],
            'Application differs from independent Setup checkpoint')
    setup_key, setup = None, None
    if target == 'setup':
        require(signing_identity is not None, 'Explicit authorized Apple Development signing identity required')
    else:
        found = [(k, v) for k, v in state['builds'].items() if v['target'] == 'setup'
                 and v['inputs']['application'] == kit_key and v['inputs']['release'] == trusted]
        require(len(found) == 1, 'Matching signed Setup required')
        setup_key, value = found[0]
        setup = storage.path('builds/setup/'+setup_key)
        require(digest(value['inputs']) == setup_key, 'Setup key differs')
        verify(setup, value['inputs'])
        signing_identity = value['inputs']['signingIdentity']
    inputs = {'target': target, 'producerTrees': trees, 'application': kit_key, 'setup': setup_key,
              'release': trusted, 'signingIdentity': signing_identity,
              'checkpointSha256': sha256(ROOT/checkpoint_path),
              'adapterSha256': sha256(ROOT/'scripts/reproduction/media.py'),
              'workerSha256': sha256(ROOT/'scripts/reproduction/media_worker.py')}
    key = digest(inputs)
    output = storage.path('builds/'+target+'/'+key)
    marker = output.parent/(key+'.inputs.json')
    if key in state['builds']:
        require(state['builds'][key] == {'target': target, 'inputs': inputs}, 'Media state differs')
        verify(output, inputs)
        progress('BUILD_REUSED', target)
        return key
    if output.exists():
        require(marker.exists() and read_json(marker) == inputs, 'Unowned media collision')
        verify(output, inputs)
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        atomic_json(marker, inputs)
        progress('BUILD_STARTED', target)
        result = run_command([python, '-I', '-B', ROOT/'scripts/reproduction/media_worker.py',
            ROOT, target, kit, str(setup or '-'), output, signing_identity, checkpoint_path, release_path],
            env=storage.environment(), cwd=storage.root, timeout=2700 if target == 'dmg' else 600)
        output.parent.joinpath(key+'.log').write_bytes((result.stdout+result.stderr)[-2**20:])
        require(result.returncode == 0, 'Media owner failed; inspect retained workspace log')
        atomic_json(host.receipt_path(output), {'status': 'BUILT_NOT_INSTALLED', 'inputs': inputs,
            'producerRevision': revision, 'published': False,
            'stamps': {p.relative_to(output).as_posix(): packaging.stamp(regular(p))
                       for p in output.rglob('*') if p.is_file()}})
    require(packaging.producer(storage, target, extras)[0] == trees, 'Producer changed during media build')
    verify_sources(storage, state)
    verify(output, inputs)
    state['builds'][key] = {'target': target, 'inputs': inputs}
    storage.save(state)
    progress('BUILT_NOT_INSTALLED', target)
    return key
