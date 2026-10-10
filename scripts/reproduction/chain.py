# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Ordered invocation of exact build owners; no runtime or release promotion."""
import ast
import json
import os
from pathlib import Path
import re

from .core import ROOT, LabError, require, read_json, atomic_json, digest, no_links, storage_volume, run_command, require_capacity, GIB
from .sources import git, check_source, verify_sources
from . import build, cloud, containers, services, gateway, packaging, host, package_chain, media

PLAN = 'workspace/releases/1.2.0-rc.1-build-chain.json'
DEPENDENCIES = {
    'presenter': (), 'cloud-sdk': (), 'brake-backend': (), 'tire-backend': (),
    'backend-export': ('brake-backend', 'tire-backend'),
    'brake-v1': (), 'brake-v2': (), 'brake-v3': (), 'tire-v1': (), 'gateway': (),
    'preparation': ('brake-v1', 'brake-v2', 'brake-v3', 'tire-v1'),
    'host-runtime': ('presenter', 'gateway'), 'backend-inputs': ('backend-export',),
    'vm-runtime': ('host-runtime', 'preparation'),
    'application': ('host-runtime', 'preparation', 'cloud-sdk', 'backend-inputs', 'vm-runtime'),
    'setup': ('application',), 'dmg': ('setup', 'application')}


def read_plan(release, path=None):
    value = read_json(path or ROOT/PLAN)
    developer = isinstance(value, dict) and value.get('schemaVersion') == 2
    require(isinstance(value, dict) and set(value) == {'schemaVersion', 'productVersion',
        'baseDefinitionSha256', 'repository', 'producers', 'steps'} | ({'resultPolicy'} if developer else set())
        and type(value['schemaVersion']) is int and value['schemaVersion'] in (1, 2)
        and (not developer or value['resultPolicy'] == 'seal-developer-results-v1')
        and value['productVersion'] == '1.2.0-rc.1' and value['baseDefinitionSha256'] == release.key,
        'Build chain differs from selected definition')
    require(value['repository'] == release.sources['integration']['repository'], 'Producer repository differs')
    require(isinstance(value['producers'], dict) and value['producers'] and
        all(isinstance(k, str) and re.fullmatch('[a-z][a-z0-9-]{0,39}', k) and
            isinstance(v, str) and re.fullmatch('[a-f0-9]{40}', v) for k, v in value['producers'].items()),
        'Invalid exact producer roles')
    require(isinstance(value['steps'], list) and len(value['steps']) == len(DEPENDENCIES), 'Incomplete build chain')
    seen = set()
    for row in value['steps']:
        require(isinstance(row, dict) and set(row) in (
            {'id','target','producer','python','requires'},
            {'id','target','producer','python','requires','functionalProfile'}), 'Invalid chain step fields')
        name = row['id']
        require(isinstance(name, str) and name in DEPENDENCIES and name not in seen, 'Unknown or duplicate chain step')
        require(row['requires'] == list(DEPENDENCIES[name]) and set(row['requires']) <= seen,
                'Chain dependency missing, reordered or cyclic')
        target = ('brake-service' if name.startswith('brake-v') else
                  'tire-service' if name == 'tire-v1' else name)
        require(row['target'] == target and isinstance(row['producer'], str) and row['producer'] in value['producers']
                and row['python'] == ('ui' if target == 'presenter' else 'build'), 'Invalid owner dispatch')
        require(row.get('functionalProfile') == (name.split('-')[-1] if target in services.TARGETS else None),
                'Invalid chain functional profile')
        seen.add(name)
    return value


def ancestors(plan, name):
    rows = {r['id']: r for r in plan['steps']}
    result = set()
    def visit(key):
        for child in rows[key]['requires']:
            if child not in result:
                result.add(child)
                visit(child)
    visit(name)
    return result

def storage_compatibility(storage, plan, docker_volume=None):
    """Inspect exact local Git blobs without importing/mutating frozen owners."""
    required = {'internal-apfs' if storage.volume.get('internal') else 'external-apfs'}
    separate_docker = docker_volume is not None and docker_volume['uuid'] != storage.volume['uuid']
    rows = []
    for revision in dict.fromkeys(plan['producers'].values()):
        producer_required = set(required)
        if separate_docker and any(plan['producers'][step['producer']] == revision and step['target'] in
                ('brake-backend','tire-backend','backend-export','brake-service','tire-service') for step in plan['steps']):
            producer_required.add('separate-docker-volume')
        try:
            text = git(ROOT, ['show', revision+':scripts/reproduction/core.py'],
                       storage.environment(create=False))
            declarations = [n for n in ast.parse(text).body if isinstance(n, ast.Assign)
                            and any(isinstance(t, ast.Name) and t.id == 'STORAGE_CAPABILITIES' for t in n.targets)]
            require(len(declarations) <= 1, 'Ambiguous storage capabilities')
            capabilities = ast.literal_eval(declarations[0].value) if declarations else ('external-apfs',)
            require(isinstance(capabilities, (list, tuple)) and all(isinstance(c, str) for c in capabilities),
                    'Invalid storage capabilities')
            missing = sorted(producer_required - set(capabilities))
            rows.append({'revision':revision, 'compatible':not missing, 'missingCapabilities':missing})
        except (LabError, SyntaxError, ValueError, TypeError):
            rows.append({'revision':revision, 'compatible':False, 'reason':'Exact producer storage policy is unavailable locally'})
    return {'compatible':all(r['compatible'] for r in rows),
            'requiredCapabilities':sorted(required | ({'separate-docker-volume'} if separate_docker else set())), 'producers':rows}


def producer(storage, plan, revision, acquire, progress):
    """An independent detached build-input checkout, never a working-tree edit."""
    env = storage.environment()
    path = storage.path('sources/build-tools/'+revision)
    marker = path.with_suffix('.json')
    source = {'repository': plan['repository'], 'revision': revision}
    if marker.exists():
        require(read_json(marker) == source, 'Producer ownership marker differs')
    else:
        require(not path.exists(), 'Unowned producer directory; preserved')
        path.parent.mkdir(parents=True, exist_ok=True)
        atomic_json(marker, source)
    path.mkdir(mode=0o700, exist_ok=True)
    no_links(path/'.git')
    require(not (path/'.git').exists() or (path/'.git').is_dir(), 'Expected independent producer checkout')
    if not (path/'.git').exists():
        require(not any(path.iterdir()), 'Unowned incomplete producer files')
        git(path, ['init', '--quiet'], env)
    if not git(path, ['remote'], env):
        require({p.name for p in path.iterdir()} == {'.git'}, 'Incomplete producer contains user files')
        git(path, ['remote', 'add', 'origin', source['repository']], env)
    require(git(path, ['remote','get-url','origin'], env) == source['repository'], 'Producer remote differs')
    head = run_command(['git','-C',path,'rev-parse','--verify','HEAD'], env=env)
    if head.returncode:
        require({p.name for p in path.iterdir()} == {'.git'}, 'Partial producer checkout preserved')
        # The user-selected root checkout is explicit source authority, not a
        # hidden sibling fallback. Copy an exact available Git object offline.
        require(git(ROOT, ['remote','get-url','origin'], env) == source['repository'], 'Root repository differs')
        available = run_command(['git','-C',ROOT,'cat-file','-e',revision+'^{commit}'], env=env)
        require(available.returncode == 0 or acquire, 'Producer object missing; use --prepare-dependencies')
        source_repository = ROOT if available.returncode == 0 else 'origin'
        progress('PREPARE_PRODUCER', revision[:12])
        git(path, ['fetch','--quiet','--depth=1','--no-tags',str(source_repository),revision], env, timeout=180)
        git(path, ['-c','submodule.recurse=false','checkout','--quiet','--detach',revision], env)
    check_source(path, source, env)
    return path


def preflight(storage, args):
    required = ('kit_inputs','gateway_sdk','test_tmp_parent','python','ui_python','node','npm','cmake','docker')
    require(all(getattr(args, k, None) is not None for k in required), 'Complete chain requires declared kit, SDK and build tools')
    require(isinstance(args.signing_identity, str) and re.fullmatch('[a-fA-F0-9]{40}', args.signing_identity),
            'Complete signed-media chain requires explicit authorized signing identity')
    require(not args.resume and args.functional_profile is None, 'Use the target command for inspected Gateway resume or a single service profile')
    config = {k: str(Path(getattr(args, k)).absolute()) for k in required}
    for name in ('kit_inputs', 'gateway_sdk'):
        path = no_links(config[name])
        require(path.is_dir() and storage_volume(path)['uuid'] == storage.volume['uuid'],
                'Chain input must exist on the bound volume')
    gateway.temporary_parent(storage, config['test_tmp_parent'])
    for name in ('python','ui_python','node','npm','cmake','docker'):
        path = Path(config[name])
        # Preserve a virtual-environment Python entry point, not its symlink target.
        require(path.is_file() and os.access(path, os.X_OK), 'Declared chain tool is unavailable: '+name)
    config.update(signing_identity=args.signing_identity.upper(), prepare_dependencies=args.prepare_dependencies)
    if getattr(args, 'factory_inputs', None) is not None:
        path = no_links(Path(args.factory_inputs).absolute())
        require(path.is_dir() and storage_volume(path)['uuid'] == storage.volume['uuid'],
                'Factory inputs must exist on the bound volume')
        config['factory_inputs'] = str(path)
    for name in ('input_checkpoint', 'release_checkpoint'):
        if getattr(args, name, None) is not None:
            from .cloud import relative
            config[name] = str(relative(getattr(args, name)))
    return config


def visible_results(plan, step, selected, state):
    return ({selected[n] for n in ancestors(plan, step['id'])} |
            {k for k,v in state['builds'].items() if v['target'] == step['target']})


def completed_key(output):
    lines = output.splitlines()
    require(lines, 'Missing chain worker result')
    try:
        reply = json.loads(lines[-1])
    except (ValueError, UnicodeError):
        require(False, 'Invalid chain worker result')
    require(isinstance(reply, dict) and reply.get('status') == 'OWNER_STEP_COMPLETED'
            and isinstance(reply.get('buildKey'), str) and re.fullmatch('[a-f0-9]{64}', reply['buildKey']),
            'Invalid chain worker result')
    return reply['buildKey']


def verify_result(storage, key, row, expected_target):
    require(row['target'] == expected_target and digest(row['inputs']) == key, 'Chain result identity differs')
    path = storage.path('builds/'+expected_target+'/'+key)
    if expected_target == 'presenter':
        return build.verify_output(path)
    validator = {'cloud-sdk': cloud.verify_output, 'backend-export': containers.verify_export,
        'gateway': gateway.verify_output, 'preparation': packaging.verify_preparation,
        'host-runtime': host.verify}.get(expected_target)
    if validator is None:
        validator = (services.verify_output if expected_target in services.TARGETS else
            package_chain.verify if expected_target in package_chain.MANIFESTS else
            media.verify if expected_target in media.TARGETS else containers.verify_output)
    return validator(path, row['inputs'])


def execute(storage, state, args, progress):
    require(storage.profile == 'developer', 'Complete chain currently supports developer only')
    plan = read_plan(storage.release, args.build_plan)
    verify_sources(storage, state)
    config = preflight(storage, args)
    if plan.get('resultPolicy') == 'seal-developer-results-v1':
        require(not any(name in config for name in ('input_checkpoint', 'release_checkpoint')),
                'Developer chain cannot select reviewed output checkpoints')
        config['developer_results'] = True
    # Preserve mandatory per-owner guards; this is not a measured cold peak.
    storage.check(additional=76*GIB, reserve=90*GIB)
    docker_storage = containers.inspect_storage(args.docker, storage.environment(create=False), storage.root)
    require_capacity(containers.capacity_requests(storage, docker_storage['disk'], docker_storage['volume'],
                                                  additional=76*GIB, reserve=90*GIB))
    compatibility = storage_compatibility(storage, plan, docker_storage['volume'])
    require(compatibility['compatible'],
            'Selected frozen producers do not support this storage layout (or their policy is unavailable); '
            'use a reviewed successor producer plan, not edited historical pins')
    selected, paths = {}, {}
    for rev in dict.fromkeys(plan['producers'].values()):
        paths[rev] = producer(storage, plan, rev, args.prepare_dependencies, progress)
    key = digest({'plan': plan, 'signer': args.signing_identity.upper()})
    selection = {name: config[name] for name in ('factory_inputs', 'input_checkpoint', 'release_checkpoint') if name in config}
    if selection:
        key = digest({'plan':plan, 'signer':args.signing_identity.upper(), 'selection':selection})
    record = storage.path('builds/chains/'+key+'.json')
    record.parent.mkdir(parents=True, exist_ok=True)
    progress('CHAIN_STARTED', len(plan['steps']))
    for step in plan['steps']:
        # Select exact dependencies for this invocation without deleting older
        # valid results. The canonical owner's own result cache remains visible.
        visible = visible_results(plan, step, selected, state)
        invocation = {'storage': str(storage.root), 'producer': str(paths[plan['producers'][step['producer']]]),
            'revision': plan['producers'][step['producer']], 'repository': plan['repository'],
            'step': step, 'visible': sorted(visible), 'options': config}
        request = Path(storage.environment()['TMPDIR']) / ('chain-'+key+'-'+step['id']+'.json')
        atomic_json(request, invocation)
        progress('CHAIN_STEP', step['id'])
        response = run_command([config['ui_python' if step['python']=='ui' else 'python'], '-I','-B',
            ROOT/'scripts/reproduction/chain_worker.py', request], env=storage.environment(), cwd=storage.root, timeout=3600)
        log = storage.path('builds/chains/'+key+'-'+step['id']+'.log')
        log.write_bytes((response.stdout+response.stderr)[-2**20:])
        if response.returncode:
            first = storage.path('builds/chains/'+key+'-'+step['id']+'.first-failure.log')
            if not first.exists():
                first.write_bytes((response.stdout+response.stderr)[-2**20:])
        require(response.returncode == 0, 'Chain step '+step['id']+' failed; prior completed results preserved, inspect workspace log')
        result_key = completed_key(response.stdout)
        fresh = storage.state()
        state.clear(); state.update(fresh)
        verify_result(storage, result_key, state['builds'][result_key], step['target'])
        selected[step['id']] = result_key
        atomic_json(record, {'schemaVersion':1, 'planDigest':digest(plan), 'completed':selected,
            'status':'CHAIN_BUILT_NOT_QUALIFIED' if len(selected)==len(plan['steps']) else 'PARTIAL',
            'profileReady':False, 'runtimeStarted':False, 'published':False})
        request.unlink()
        progress('CHAIN_STEP_VERIFIED', step['id'])
    return {'status':'CHAIN_BUILT_NOT_QUALIFIED', 'buildCount':len(selected),
            'chainKey':key, 'profileReady':False, 'qualified':False, 'published':False}
