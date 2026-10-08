# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Target adapters over existing owner recipes, never a runtime launcher."""
from pathlib import Path
import sys
from .core import require, digest, read_json, atomic_json, regular, GIB, run_command
from .sources import verify_sources, check_source
from .artifacts import sha256

def command(args, env, cwd, timeout=15):
    value = run_command(args, cwd=cwd, env=env, timeout=timeout)
    require(value.returncode == 0, 'Owner build command failed; no output promoted')
    return value.stdout.decode('utf-8').strip()

def verify_output(output):
    receipt = read_json(output / 'build-receipt.json')
    require(type(receipt) is dict, 'Invalid owner build receipt')
    require(receipt.get('status') == 'BUILT_NOT_RUNTIME_QUALIFIED' and receipt.get('sourcesUnchanged') is True,
            'No completed owner build receipt')
    rows = receipt.get('files', [])
    require(isinstance(rows, list) and rows, 'No build output inventory')
    names = set()
    for row in rows:
        relative = Path(row['path'])
        require(relative.parts and not relative.is_absolute() and '..' not in relative.parts and str(relative) not in names,
                'Invalid build output path')
        require(relative.parts[0] in ('native', 'web'), 'Unexpected output inventory root')
        path = regular(output / relative)
        require(path.stat().st_size == row['bytes'] and sha256(path) == row['sha256'], 'Build output changed')
        names.add(str(relative))
    actual = {str(p.relative_to(output)) for sub in ('native', 'web') for p in (output / sub).rglob('*') if not p.is_dir()}
    require(names == actual, 'Build output inventory differs')
    return receipt

def presenter(storage, state, node, npm, prepare_dependencies, progress):
    require(storage.profile != 'operator', 'Operator profile does not build')
    verify_sources(storage, state)
    storage.check(additional=2*GIB, reserve=90*GIB)
    env = storage.environment()
    node, npm = Path(node).resolve(strict=True), Path(npm).resolve(strict=True)
    env['PATH'] = str(node.parent) + ':' + env.get('PATH', '')
    integration = storage.path('sources/integration')
    gateway = storage.path('sources/vehicle-gateway')
    web = integration / 'apps/presenter-ui'
    engines = read_json(web / 'package.json')['engines']
    require(command([node, '--version'], env, web) == 'v' + engines['node'], 'Node differs from source pin')
    require(command([npm, '--version'], env, web) == engines['npm'], 'npm differs from source pin')
    toolchain = {'node': engines['node'], 'npm': engines['npm'],
                 'swift': command(['/usr/bin/xcrun', 'swiftc', '--version'], env, web),
                 'sdk': command(['/usr/bin/xcrun', '--sdk', 'macosx', '--show-sdk-version'], env, web),
                 'python': sys.version.split()[0]}
    source_rows = {n: state['sources'][n] for n in ('integration', 'vehicle-gateway')}
    owner = integration / 'scripts/distribution/ui_build.py'
    inputs = {'sources': source_rows, 'toolchain': toolchain, 'recipeSha256': sha256(owner),
              'packageLockSha256': sha256(web / 'package-lock.json')}
    key = digest(inputs)
    output = storage.path('builds/presenter/' + key)
    if key in state['builds']:
        require(state['builds'][key] == {'target': 'presenter', 'inputs': inputs}, 'Build key receipt mismatch')
        verify_output(output)
        progress('BUILD_REUSED', 'presenter')
        return key
    if output.exists():
        # Reconcile an owner success after interruption before the outer state save.
        stamp = output.parent / (key + '.inputs.json')
        require(stamp.exists() and read_json(stamp) == inputs, 'Unowned build collision; preserved')
        verify_output(output)
    else:
        require(prepare_dependencies, 'First Presenter build requires explicit --prepare-dependencies for pinned npm inputs')
        progress('PREPARE_NPM_INPUTS', 'presenter')
        command([npm, 'ci', '--ignore-scripts', '--no-audit', '--no-fund', '--cache', env['npm_config_cache']],
                env, web, timeout=180)
        check_source(integration, storage.release.sources['integration'], env)
        output.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        atomic_json(output.parent / (key + '.inputs.json'), inputs)
        storage.check(additional=128*2**20, reserve=90*GIB)
        progress('BUILD_STARTED', 'presenter')
        command([sys.executable, '-B', owner, '--integration', integration, '--gateway', gateway,
                 '--node', node, '--output', output], env, storage.root, timeout=360)
        verify_output(output)
    verify_sources(storage, state)
    state['builds'][key] = {'target': 'presenter', 'inputs': inputs}
    storage.save(state)
    progress('BUILT_NOT_RUNTIME_QUALIFIED', 'presenter')
    return key
