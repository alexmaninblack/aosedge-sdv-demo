# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Public R2 build-only command boundary."""
import argparse
import http.client
import json
import os
import re
from pathlib import Path
import shutil
import sys
from .core import Release, Storage, LabError, require, read_json, digest
from .sources import prepare_sources, verify_sources
from .artifacts import Drive, binding_entry, download, cached
from . import build, cloud, containers, services, gateway, packaging, host, package_chain, media, chain, cache, space

def emit(value):
    print(json.dumps(value, sort_keys=True), flush=True)

def progress(event, detail):
    # Fixed stage identifiers and non-secret counts/role IDs only.
    if event != 'DOWNLOAD_BYTES' or detail % (64*2**20) == 0:
        emit({'event': event, 'detail': detail})

def plan(release, profile, build_plan=None):
    ordered = chain.read_plan(release, build_plan) if profile == 'developer' else None
    return {'release': release.value['id'], 'definitionDigest': release.key, 'profile': profile,
            'sources': list(release.selected_sources(profile)), 'buildOrder': release.graph(profile),
            'implementedBuildTargets': ['presenter', 'cloud-sdk', *containers.TARGETS, 'backend-export', *services.TARGETS, 'gateway', 'preparation', 'host-runtime', *package_chain.MANIFESTS, *media.TARGETS] if profile == 'developer' else [],
            'serviceProfiles': {'brake-service': ['v1', 'v2', 'v3'], 'tire-service': ['v1']},
            'gates': release.gates(profile), 'qualified': False,
            'orderedDeveloperChain': ordered,
            'storage': 'Explicit external SSD; no internal fallback',
            'space': {'reserveGiB': 60, 'presenterReserveGiB': 90,
                      'chainAdditionalGiB': 76, 'chainReserveGiB': 90,
                      'fullProfilePeak': 'Unmeasured; guards are conservative, not a cold-build measurement'}}

def status(storage, state):
    sources = verify_sources(storage, state, complete=False)
    missing = sorted(set(storage.release.selected_sources(storage.profile)) - set(state['sources']))
    artifacts = []
    require(set(state['artifacts']).issubset(storage.release.value['artifacts']), 'Unknown artifact receipt')
    for name, expected in storage.release.value['artifacts'].items():
        if name in state['artifacts']:
            require(state['artifacts'][name] == expected.get('sha256'), 'Artifact receipt differs from release')
            require('bytes' in expected and 'sha256' in expected and cached(storage, expected), 'Artifact receipt has no verified cache entry')
            artifacts.append(name)
    for key, receipt in state['builds'].items():
        target = receipt.get('target')
        require(target in ('presenter', 'cloud-sdk', *containers.TARGETS, 'backend-export', *services.TARGETS, 'gateway', 'preparation', 'host-runtime', *package_chain.MANIFESTS, *media.TARGETS) and re.fullmatch('[a-f0-9]{64}', key), 'Unknown build receipt')
        require(digest(receipt.get('inputs')) == key, 'Build receipt key differs from inputs')
        if target == 'presenter':
            build.verify_output(storage.path('builds/presenter/' + key))
        elif target == 'cloud-sdk':
            cloud.verify_output(storage.path('builds/cloud-sdk/' + key), receipt['inputs'])
        elif target == 'backend-export':
            containers.verify_export(storage.path('builds/backend-export/' + key), receipt['inputs'])
        elif target in services.TARGETS:
            services.verify_output(storage.path('builds/' + target + '/' + key), receipt['inputs'])
        elif target == 'gateway':
            gateway.verify_output(storage.path('builds/gateway/' + key), receipt['inputs'])
        elif target == 'preparation':
            packaging.verify_preparation(storage.path('builds/preparation/' + key), receipt['inputs'])
        elif target == 'host-runtime':
            host.verify(storage.path('builds/host-runtime/' + key), receipt['inputs'])
        elif target in package_chain.MANIFESTS:
            package_chain.verify(storage.path('builds/'+target+'/'+key), receipt['inputs'])
        elif target in media.TARGETS:
            media.verify(storage.path('builds/'+target+'/'+key), receipt['inputs'])
        else:
            containers.verify_output(storage.path('builds/' + target + '/' + key), receipt['inputs'])
    return {'status': ('SOURCES_PARTIAL' if missing else 'SOURCE_READY') if storage.profile != 'operator' else 'OPERATOR_INPUTS_PENDING',
            'sourceCount': sources, 'verifiedArtifacts': artifacts, 'buildCount': len(state['builds']),
            'missingSources': missing,
            'profileReady': False, 'qualified': False, 'gates': storage.release.gates(storage.profile)}

def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == 'dependencies':
        from .dependencies import main as dependencies_main
        return dependencies_main(argv[1:])
    if argv and argv[0] == 'factory':
        from .factory import main as factory_main
        return factory_main(argv[1:])
    parser = argparse.ArgumentParser(description=__doc__, epilog='Reusable prebuilt CARLA inputs: lab dependencies --help')
    parser.add_argument('action', choices=('plan', 'prepare', 'status', 'verify', 'build', 'cache', 'space', 'revalidate'))
    parser.add_argument('--profile', choices=('operator', 'developer', 'full-source'))
    parser.add_argument('--storage', type=Path)
    parser.add_argument('--manifest', type=Path)
    parser.add_argument('--sources-only', action='store_true')
    parser.add_argument('--cache-from', type=Path, help='Explicit existing workspace on the same SSD for verified digest-cache reuse')
    parser.add_argument('--drive-binding', type=Path)
    parser.add_argument('--drive-token-fd', type=int)
    parser.add_argument('--target', choices=('all', 'presenter', 'cloud-sdk', *containers.TARGETS, 'backend-export', *services.TARGETS, 'gateway', 'preparation', 'host-runtime', *package_chain.MANIFESTS, *media.TARGETS), default='all')
    parser.add_argument('--signing-identity', help='Explicit authorized Apple Development certificate fingerprint for Setup')
    parser.add_argument('--build-plan', type=Path, help='Reviewed ordered producer plan for --target all')
    parser.add_argument('--ui-python', type=Path, default=Path('/usr/bin/python3'), help='Declared interpreter for the pinned UI owner')
    parser.add_argument('--gateway-sdk', type=Path)
    parser.add_argument('--test-tmp-parent', type=Path)
    parser.add_argument('--resume', action='store_true', help='Explicitly resume an inspected incomplete Gateway build')
    parser.add_argument('--cmake', type=Path, default=shutil.which('cmake'))
    parser.add_argument('--functional-profile', choices=('v1', 'v2', 'v3'))
    parser.add_argument('--docker', type=Path, default=shutil.which('docker'))
    parser.add_argument('--kit-inputs', type=Path)
    parser.add_argument('--factory-inputs', type=Path, help='Explicit source-built Factory result root; must match the independent source checkpoint')
    parser.add_argument('--input-checkpoint', help='Committed successor group checkpoint relative to the selected producer')
    parser.add_argument('--release-checkpoint', help='Committed independent Setup pin relative to the selected producer')
    parser.add_argument('--python', type=Path, default=sys.executable)
    parser.add_argument('--node', type=Path, default=shutil.which('node'))
    parser.add_argument('--npm', type=Path, default=shutil.which('npm'))
    parser.add_argument('--prepare-dependencies', action='store_true')
    args = parser.parse_args(argv)
    try:
        release = Release(args.manifest)
        profile = args.profile
        if profile is None and args.storage and (args.storage / 'preparation.json').exists():
            profile = read_json(args.storage / 'preparation.json')['binding']['profile']
        profile = profile or 'developer'
        if args.action == 'plan':
            emit(plan(release, profile, args.build_plan))
            return 0
        require(args.storage is not None, 'Specify --storage on an external SSD')
        storage = Storage(args.storage, release, profile)
        if args.action == 'space':
            state = storage.state() if storage.state_path.exists() else {
                'binding':storage.binding, 'sources':{}, 'artifacts':{}, 'builds':{}}
            require(storage.state_path.exists() or not storage.root.exists() or not any(storage.root.iterdir()),
                    'Refusing an unowned nonempty workspace')
            emit(space.report(storage, state, args.target, args.build_plan, args.cache_from))
            return 0
        if args.action == 'cache':
            require(args.cache_from is not None, 'Specify --cache-from with an existing prepared workspace')
            require(profile != 'full-source', 'Full-source cache closure is not yet supported')
        if args.action in ('status', 'verify', 'revalidate'):
            require(storage.state_path.exists(), 'No prepared state; use prepare first')
        with storage.locked() as state:
            if args.action == 'revalidate':
                from .revalidate import refresh
                emit(refresh(storage, state, args.target, progress))
                return 0
            if args.action == 'cache':
                emit(cache.reuse(storage, args.cache_from, progress))
                return 0
            if args.action == 'prepare':
                require(profile != 'full-source', 'Full-source preparation blocked by Factory/native/entitlement input closure; see plan')
                prepare_sources(storage, state, progress)
                if args.sources_only:
                    emit({'status': 'SOURCES_PREPARED', 'profileReady': False, 'sourceCount': len(state['sources'])})
                    return 0
                if args.drive_binding:
                    require(args.drive_token_fd is not None and args.drive_token_fd >= 0, 'Authorized Drive token descriptor required')
                    token = os.read(args.drive_token_fd, 4097).decode().strip()
                    file_id, folder_id, expected = binding_entry(read_json(args.drive_binding), release, 'dmg')
                    download(storage, Drive(token), file_id, folder_id, expected, progress)
                    state['artifacts']['dmg'] = expected['sha256']
                    storage.save(state)
                emit(status(storage, state))
                emit({'status': 'PROFILE_BLOCKED', 'reason': 'Source preparation is complete; artifact/profile gates remain. See plan.'})
                return 2
            if args.action in ('status', 'verify'):
                result = status(storage, state)
                emit(result)
                if args.action == 'status':
                    return 0
                return 0 if args.sources_only and not result['missingSources'] else 2
            if args.target == 'all':
                emit(chain.execute(storage, state, args, progress))
                return 0
            if args.target == 'presenter':
                require(args.node and args.npm, 'Pinned Node and npm are required')
                key = build.presenter(storage, state, args.node, args.npm, args.prepare_dependencies, progress)
            elif args.target == 'cloud-sdk':
                key = cloud.assemble(storage, state, args.kit_inputs, args.python, args.prepare_dependencies, progress)
            elif args.target == 'gateway':
                key = gateway.assemble(storage, state, args.gateway_sdk, args.cmake, args.python, progress,
                                       args.test_tmp_parent, args.resume)
            elif args.target == 'preparation':
                key = packaging.preparation(storage, state, args.kit_inputs, args.python, progress,
                                            args.prepare_dependencies, args.factory_inputs)
            elif args.target == 'host-runtime':
                key = host.assemble(storage, state, args.kit_inputs, args.gateway_sdk, args.python, progress)
            elif args.target in package_chain.MANIFESTS:
                key = package_chain.assemble(storage, state, args.target, args.kit_inputs, args.python, progress,
                                             args.input_checkpoint)
            elif args.target in media.TARGETS:
                key = media.assemble(storage, state, args.target, args.python, args.signing_identity, progress,
                                     args.input_checkpoint, args.release_checkpoint)
            else:
                require(args.docker, 'Docker Desktop CLI required; Engine is not started automatically')
                if args.target in services.TARGETS:
                    key = services.assemble(storage, state, args.target, args.functional_profile,
                        args.docker, args.python, args.prepare_dependencies, progress)
                elif args.target == 'backend-export':
                    key = containers.export(storage, state, args.docker, args.prepare_dependencies, progress, args.python)
                else:
                    key = containers.assemble(storage, state, args.target, args.docker, args.prepare_dependencies, progress)
            emit({'status': 'TARGET_BUILT_NOT_QUALIFIED', 'target': args.target, 'buildKey': key, 'profileReady': False})
            return 0
    except KeyboardInterrupt:
        emit({'status': 'INTERRUPTED', 'reason': 'Partial work retained; inspect status before resuming'})
        return 130
    except (LabError, OSError, ValueError, KeyError, TypeError, http.client.HTTPException) as exc:
        emit({'status': 'BLOCKED', 'reason': str(exc) if isinstance(exc, LabError) else 'Invalid or unavailable local input; no implicit repair'})
        return 1

if __name__ == '__main__':
    raise SystemExit(main())
