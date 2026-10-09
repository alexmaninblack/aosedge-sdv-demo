# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Explicit Factory .41 recipe; historical .11 inputs remain immutable."""
from __future__ import annotations
import hashlib
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import time

from .core import ROOT, Release, Storage, LabError, read_json, require, atomic_json, storage_volume, digest

TEMPLATE = 'manifests/r6-1/aos-vm-project.pinned.yaml'
TEMPLATE_SHA256 = 'b9b49a575798f2bc4a532a794e77352ed21596677ef5aced4304db9e7a87f09e'
HISTORICAL_PLATFORM = 'a12c0aa7f8a680b35407776b12bcc025970abc73'
FACTORY_CHECKPOINT = 'workspace/checkpoints/factory-41-candidate.json'


def recipe(root=ROOT):
    factory = read_json(root / FACTORY_CHECKPOINT)['factory']
    require(factory['version'] == '6.1.1-maninblack.41', 'Factory checkpoint version changed')
    template = (root / TEMPLATE).read_bytes()
    require(hashlib.sha256(template).hexdigest() == TEMPLATE_SHA256, 'Historical Factory template changed')
    text = template.decode()
    # Render a successor input, never edit the historical template/definition.
    for old, new in (('6.1.1-maninblack.11', factory['version']),
                     (HISTORICAL_PLATFORM, factory['sourceRevision'])):
        require(text.count(old) == 1, 'Factory template substitution is not unique')
        text = text.replace(old, new)
    sources = re.findall(r'url: "([^"]+)"\s+rev: "([0-9a-f]{40})"', text)
    require(len(sources) == 10, 'Factory layer list changed')
    unique = dict(sources)
    require(len(unique) == 9, 'Factory layer identities are ambiguous')
    return text, {
        'schemaVersion': 1, 'factoryVersion': factory['version'],
        'platformRevision': factory['sourceRevision'],
        'historicalTemplateSha256': TEMPLATE_SHA256,
        'renderedManifestSha256': hashlib.sha256(text.encode()).hexdigest(),
        'sources': [{'url': url, 'revision': rev, 'name': url.rsplit('/', 1)[-1]}
                    for url, rev in sorted(unique.items())],
        'parameters': ['--MACHINE=qemuarm64', '--NODE_TYPE=main',
                       '--WITH_MESSAGE_PROXY=no', '--CACHE_LOCATION=outside'],
        'qualification': 'qualification/factory-41.conf',
        'historicalImageSha256': factory['sha256'],
        'historicalImageIsBuildInput': False,
    }


def builder_module(storage, builder_root):
    volume = storage_volume(builder_root)
    require(volume['uuid'] == storage.volume['uuid'], 'Builder must be on the same volume')
    os.environ['R61_BUILDER_ROOT'] = str(builder_root)
    os.environ['R61_BUILDER_VOLUME_UUID'] = volume['uuid']
    os.environ['R61_BUILDER_SSH_PORT'] = '10024'
    loader = importlib.machinery.SourceFileLoader('factory_builder', str(ROOT / 'scripts/r6-1-builder'))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    module.check_storage()
    return module


def input_archive(directory, members):
    # BSD tar can emit AppleDouble even with --no-xattrs for some metadata.
    env = dict(os.environ, COPYFILE_DISABLE='1')
    return subprocess.Popen(['tar', '--no-xattrs', '-cf', '-', '-C', str(directory), *members],
                            stdout=subprocess.PIPE, env=env)


def prepare(storage, builder, source):
    text, lock = recipe()
    script = ROOT / 'scripts/guest/factory41-prepare.py'
    lock['guestAdapterSha256'] = hashlib.sha256(script.read_bytes()).hexdigest()
    key = digest(lock)
    output = storage.path('factory/' + key)
    output.mkdir(parents=True, exist_ok=True, mode=0o700)
    for name, payload in [('factory41.yaml', text.encode()),
                          ('recipe.json', (json.dumps(lock, sort_keys=True, indent=2) + '\n').encode()),
                          ('factory41-prepare.py', script.read_bytes())]:
        path = output / name
        if path.exists():
            require(path.read_bytes() == payload, 'Factory input changed; preserve the attempt')
        else:
            path.write_bytes(payload)
    env = storage.environment()
    from .sources import git, check_source
    checkout = output / 'platform'
    row = next(row for row in lock['sources'] if row['name'] == 'aos-vehicle-platform')
    if not checkout.exists():
        storage.check(additional=2*2**30, reserve=90*2**30)
        git(source, ['cat-file', '-e', row['revision'] + '^{commit}'], env)
        git(source, ['clone', '--quiet', '--no-hardlinks', '--no-checkout', str(source), str(checkout)], env, timeout=120)
        git(checkout, ['checkout', '--quiet', '--detach', row['revision']], env)
        git(checkout, ['remote', 'set-url', 'origin', row['url']], env)
    check_source(checkout, {'revision': row['revision'], 'repository': row['url']}, env)
    bundle = output / 'platform.bundle'
    if not bundle.exists():
        git(checkout, ['bundle', 'create', str(bundle), 'HEAD'], env, timeout=120)
    ssh = builder.ssh_base()
    ssh[-1:-1] = ['-o', 'HostKeyAlias=[127.0.0.1]:10023', '-o', 'ConnectTimeout=5']
    deadline = time.monotonic() + 90
    while True:
        try:
            ready = subprocess.run(ssh + ['true'], capture_output=True, timeout=7)
        except subprocess.TimeoutExpired:
            ready = subprocess.CompletedProcess(ssh, 255, stderr=b'boot timeout')
        if ready.returncode == 0:
            break
        require(b'Host key verification failed' not in ready.stderr and b'Permission denied' not in ready.stderr,
                'Builder trust or authentication failed')
        require(time.monotonic() < deadline, 'Builder SSH boot deadline exceeded')
        time.sleep(1)
    guest_input = '/home/yocto/r61-input/factory41-' + key[:16]
    guest_project = '/home/yocto/r61-build/factory41-' + key[:16]
    members = ['recipe.json', 'factory41.yaml', 'factory41-prepare.py', 'platform.bundle']
    hashes = {name: hashlib.sha256((output / name).read_bytes()).hexdigest() for name in members}
    probe = ('import hashlib,json; from pathlib import Path; p=Path(%r); expected=%r; '
             'assert not any(x.is_symlink() for x in (p,*p.parents)); '
             'exists=p.exists(); '
             'assert not exists or (p.is_dir() and {x.name for x in p.iterdir()}==set(expected) '
             'and all(not (p/n).is_symlink() and hashlib.sha256((p/n).read_bytes()).hexdigest()==h '
             'for n,h in expected.items())), "Factory input changed or partial; preserve and inspect"; '
             'print(int(exists))') % (guest_input, hashes)
    exists = subprocess.check_output(ssh + ['python3 -c ' + shlex.quote(probe)], text=True, timeout=60).strip() == '1'
    # Source-only input transfer; no previous image, tmp, config or sstate output.
    if not exists:
        subprocess.run(ssh + ['mkdir ' + shlex.quote(guest_input)], check=True, timeout=30)
        archive = input_archive(output, members)
        try:
            subprocess.run(ssh + ['tar --keep-old-files -xf - -C ' + shlex.quote(guest_input)], stdin=archive.stdout, check=True, timeout=120)
        finally:
            archive.stdout.close()
            require(archive.wait(timeout=10) == 0, 'Factory source transfer failed')
        require(subprocess.check_output(ssh + ['python3 -c ' + shlex.quote(probe)], text=True, timeout=60).strip() == '1',
                'Factory source transfer verification failed')
    command = ['python3', guest_input + '/factory41-prepare.py', '--input', guest_input,
               '--project', guest_project, '--source-cache', '/home/yocto/r61-build/project/yocto']
    log = output / ('prepare-' + str(time.time_ns()) + '.log')
    with log.open('x') as stream:
        result = subprocess.run(ssh + [shlex.join(command)], stdout=stream, stderr=subprocess.STDOUT, timeout=600)
    require(result.returncode == 0, 'Factory preparation failed; inspect preserved log: ' + str(log))
    result = {'status': 'FACTORY_CONFIGURED_NOT_BUILT', 'key': key, 'project': guest_project,
              'platform': str(checkout), 'input': guest_input, 'hostOutput': str(output)}
    atomic_json(output / 'preparation.json', result)
    return result


def build_factory(storage, prepared):
    """Call the existing Factory owner in this build-only process, not the UI."""
    import sys
    sys.path.insert(0, str(ROOT / 'apps/demo-orchestrator/src'))
    from aosedge_demo_orchestrator import component_runtime as owner
    require(not subprocess.check_output(['git', '-C', str(ROOT), 'status', '--porcelain']),
            'Factory build tooling must be committed before compilation')
    storage.check(additional=40*2**30, reserve=90*2**30)
    owner.FACTORY_SOURCE = Path(prepared['platform'])
    owner.BUILDER_PROJECT = prepared['project'] + '/yocto'
    owner.ARTIFACT = storage.path('factory-results/runtime-proofs/factory41')
    storage.path('factory-results/factory-images').mkdir(parents=True, exist_ok=True)
    result = owner.build_factory('6.1.1-maninblack.41', preserve_layer_binding=True,
                                 storage_check=lambda: storage.check(reserve=90*2**30))
    atomic_json(storage.path('factory-results/result.json'), result)
    return {'status': 'FACTORY_BUILT_NOT_QUALIFIED', 'image': result['factoryImage']}


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['plan', 'prepare', 'build'])
    parser.add_argument('--storage', type=Path)
    parser.add_argument('--builder-root', type=Path)
    parser.add_argument('--platform-source', type=Path)
    args = parser.parse_args(argv)
    if args.action == 'plan':
        _, value = recipe()
        value['status'] = 'RECIPE_DECLARED_NOT_BUILT'
        print(json.dumps(value, sort_keys=True))
        return 0
    require(args.storage and args.builder_root and args.platform_source, 'Explicit workspace storage, Builder and platform source required')
    storage = Storage(args.storage, Release(), 'developer')
    with storage.locked():
        builder = builder_module(storage, args.builder_root)
        try:
            builder.start(False)
            prepared = prepare(storage, builder, args.platform_source)
            value = build_factory(storage, prepared) if args.action == 'build' else prepared
            print(json.dumps(value, sort_keys=True))
        finally:
            builder.stop()
    return 0
