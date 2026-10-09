# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Pinned Gateway CMake owner, with explicit external SDK and offline builds."""
import json
from pathlib import Path
import stat
import tempfile
import xml.etree.ElementTree as ET

from .core import ROOT, require, regular, read_json, atomic_json, digest, storage_volume, run_command, GIB
from .artifacts import sha256
from .build import command
from .cloud import inventory
from .sources import verify_sources

SDK_LOCK = ROOT / 'workspace/gateway-build-sdk.lock.json'
BINARIES = ('carla-ego-runtime', 'carla-viss-client')


def sdk_input(storage, sdk):
    require(sdk is not None, 'Specify --gateway-sdk with the declared prebuilt SDK on the selected volume')
    sdk = Path(sdk)
    require(storage_volume(sdk)['uuid'] == storage.volume['uuid'], 'Gateway SDK must be on the bound volume')
    lock = read_json(SDK_LOCK)
    manifest = regular(sdk / 'sdk-manifest.json')
    require(sha256(manifest) == lock['manifestSha256'], 'Gateway SDK manifest differs from lock')
    value = read_json(manifest)
    require(value.get('kind') == 'gateway-build-sdk' and value.get('architecture') == 'arm64'
            and len(value['files']) == lock['files'] and sum(r['bytes'] for r in value['files']) == lock['bytes'],
            'Gateway SDK inventory differs from lock')
    inventory(sdk, value['files'], ('sdk-manifest.json',))
    return lock


def test_result(report, names):
    root = ET.parse(regular(report)).getroot()
    cases = list(root.iter('testcase'))
    require(len(cases) == len(names) and {c.get('name') for c in cases} == set(names)
            and all(c.get('status') == 'run' and not any(c.find(n) is not None for n in ('failure', 'error', 'skipped'))
                    for c in cases), 'Gateway CTest suite incomplete, failed or skipped')
    return len(cases)


def verify_output(output, inputs):
    receipt = read_json(output / 'build-receipt.json')
    require(receipt.get('status') == 'BUILT_NOT_RUNTIME_QUALIFIED' and receipt.get('inputs') == inputs
            and receipt.get('sourcesUnchanged') is True and receipt.get('runtimeRelocated') is False,
            'Gateway build receipt differs')
    expected = {*BINARIES, 'ctest-results.xml'}
    require({row['path'] for row in receipt['files']} == expected and len(receipt['files']) == len(expected),
            'Gateway output inventory differs')
    for row in receipt['files']:
        path = regular(output / row['path'])
        require(path.stat().st_size == row['bytes'] and sha256(path) == row['sha256']
                and stat.S_IMODE(path.stat().st_mode) == row['mode'], 'Gateway output changed')
    require(test_result(output / 'ctest-results.xml', receipt['testNames']) == receipt['testCount'],
            'Gateway test receipt differs')
    return receipt


def temporary_parent(storage, parent):
    require(parent is not None, 'Specify --test-tmp-parent: an existing short directory on the bound volume')
    parent = Path(parent)
    require(parent.is_dir() and storage_volume(parent)['uuid'] == storage.volume['uuid'],
            'Gateway test temporary parent must be on the bound volume')
    # mkdtemp adds ten bytes; the unchanged owner appends its fixture/socket names.
    require(len(str(parent).encode()) <= 29, 'Gateway test temporary parent is too long for Unix sockets')
    return parent


def assemble(storage, state, sdk, cmake, python, progress, test_tmp_parent=None, resume=False):
    require(storage.profile == 'developer', 'Gateway adapter currently requires developer profile')
    verify_sources(storage, state)
    storage.check(additional=2*GIB, reserve=90*GIB)
    sdk = Path(sdk) if sdk is not None else None
    lock = sdk_input(storage, sdk)
    tmp_parent = temporary_parent(storage, test_tmp_parent)
    require(cmake, 'CMake is required for Gateway')
    cmake = Path(cmake).resolve(strict=True)
    ctest = regular(cmake.parent / 'ctest')
    python = Path(python).absolute()
    checkout = storage.path('sources/vehicle-gateway')
    env = storage.environment()
    carla_cache = storage.path('cache/carla')
    carla_cache.mkdir(parents=True, exist_ok=True)
    env['CARLA_CACHE_DIR'] = str(carla_cache)
    toolchain = {'cmake': command([cmake, '--version'], env, storage.root),
                 'clang': command(['/usr/bin/xcrun', 'clang++', '--version'], env, storage.root),
                 'sdk': command(['/usr/bin/xcrun', '--sdk', 'macosx', '--show-sdk-version'], env, storage.root),
                 'python': command([python, '-I', '-B', '--version'], env, storage.root)}
    inputs = {'source': state['sources']['vehicle-gateway'], 'sdk': lock,
              'toolchain': toolchain, 'deploymentTarget': '26.0', 'architecture': 'arm64',
              'recipeSha256': sha256(regular(checkout / 'CMakeLists.txt')),
              'carlaEnabled': True, 'vissEnabled': True, 'testsEnabled': True}
    key = digest(inputs)
    output = storage.path('builds/gateway/' + key)
    marker = output.parent / (key + '.inputs.json')
    if key in state['builds']:
        require(state['builds'][key] == {'target': 'gateway', 'inputs': inputs}, 'Gateway build key differs')
        verify_output(output, inputs)
        progress('BUILD_REUSED', 'gateway')
        return key
    if output.exists():
        require(marker.exists() and read_json(marker) == inputs, 'Unowned Gateway build collision')
        if (output / 'build-receipt.json').exists():
            verify_output(output, inputs)
        else:
            require(resume, 'Incomplete Gateway build; inspect logs then explicitly use --resume')
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        atomic_json(marker, inputs)
        output.mkdir(mode=0o700)
    if not (output / 'build-receipt.json').exists():
        policy = output / 'build-offline.sb'
        policy.write_text('(version 1)\n(allow default)\n(deny network*)\n')
        def step(name, args, timeout=600, offline=True, extra=None):
            progress('GATEWAY_STAGE', name)
            storage.check(reserve=90*GIB)
            prefix = ['/usr/bin/sandbox-exec', '-f', policy] if offline else []
            result = run_command(prefix + args, env={**env, **(extra or {})}, cwd=output, timeout=timeout)
            log = result.stdout + result.stderr
            log_path = output / (name + '.log')
            if log_path.exists() and not (output / (name + '.first.log')).exists():
                (output / (name + '.first.log')).write_bytes(regular(log_path).read_bytes())
            log_path.write_bytes(log[-4*2**20:])
            require(result.returncode == 0, 'Gateway ' + name + ' failed; inspect retained workspace log')
            return result.stdout.decode()
        progress('BUILD_STARTED', 'gateway')
        step('configure', [cmake, '-S', checkout, '-B', output,
            '-DCMAKE_BUILD_TYPE=Release', '-DBUILD_TESTING=ON', '-DCARLA_EGO_WITH_CARLA=ON', '-DCARLA_EGO_WITH_VISS=ON',
            '-DCMAKE_OSX_ARCHITECTURES=arm64', '-DCMAKE_OSX_DEPLOYMENT_TARGET=26.0',
            '-DCMAKE_CXX_COMPILER=/usr/bin/clang++', '-DCMAKE_MAKE_PROGRAM=/usr/bin/make',
            '-DCMAKE_FIND_USE_PACKAGE_REGISTRY=OFF', '-DCMAKE_FIND_USE_SYSTEM_PACKAGE_REGISTRY=OFF',
            '-DCarla_DIR=' + str(sdk / 'carla/lib/cmake/Carla'),
            '-DCARLA_EGO_BOOST_INCLUDE_DIR=' + str(sdk / 'carla/include'),
            '-DOPENSSL_INCLUDE_DIR=' + str(sdk / 'openssl/include'),
            '-DOPENSSL_SSL_LIBRARY=' + str(sdk / 'openssl/lib/libssl.3.dylib'),
            '-DOPENSSL_CRYPTO_LIBRARY=' + str(sdk / 'openssl/lib/libcrypto.3.dylib'),
            '-DPython3_EXECUTABLE=' + str(python)])
        step('compile', [cmake, '--build', output, '--parallel', '4'])
        listed = json.loads(step('list-tests', [ctest, '--test-dir', output, '--show-only=json-v1']))
        names = [row['name'] for row in listed['tests']]
        require(len(names) == len(set(names)) and {'viss_network', 'qm_advisory', 'runtime_reports_version',
                'keyboard_control_native', 'm6_gateway_trust'} <= set(names), 'Gateway required tests missing')
        # Unit tests bind ephemeral local sockets; no simulator or deployment is started.
        # Raw compiler outputs are not relocated packages. Select only this declared SDK for test loading.
        # The short temporary directory is the sole workspace-layout exception:
        # same verified volume, mode 0700, only this test invocation, removed on exit.
        with tempfile.TemporaryDirectory(prefix='t', dir=tmp_parent) as test_tmp:
            require(Path(test_tmp).stat().st_dev == storage.volume['device'], 'Test temporary directory escaped its selected volume')
            step('tests', [ctest, '--test-dir', output, '--output-on-failure', '--output-junit', output / 'ctest-results.xml'],
                 offline=False, extra={'DYLD_LIBRARY_PATH': str(sdk / 'openssl/lib'), 'TMPDIR': test_tmp})
            storage.check(reserve=0)
        count = test_result(output / 'ctest-results.xml', names)
        for name in BINARIES:
            require(step('arch-' + name, ['/usr/bin/lipo', '-archs', output / name]).strip() == 'arm64',
                    'Gateway binary is not ARM64')
        verify_sources(storage, state)
        rows = [{'path': name, 'bytes': (output / name).stat().st_size,
                 'mode': stat.S_IMODE((output / name).stat().st_mode), 'sha256': sha256(output / name)}
                for name in (*BINARIES, 'ctest-results.xml')]
        atomic_json(output / 'build-receipt.json', {'status': 'BUILT_NOT_RUNTIME_QUALIFIED',
            'inputs': inputs, 'files': rows, 'sourcesUnchanged': True, 'testNames': names, 'testCount': count,
            'testEnvironment': 'Explicit workspace CARLA cache and short-lived same-volume socket temporary directory',
            'runtimeRelocated': False, 'externalDistributionApproved': False})
    verify_output(output, inputs)
    state['builds'][key] = {'target': 'gateway', 'inputs': inputs}
    storage.save(state)
    progress('BUILT_NOT_RUNTIME_QUALIFIED', 'gateway')
    return key
