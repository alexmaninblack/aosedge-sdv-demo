# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Assemble host inputs using compiled UI/Gateway and declared heavy binaries."""
from pathlib import Path
import stat

from .core import ROOT, require, regular, read_json, atomic_json, digest, storage_volume, run_command, GIB
from .artifacts import sha256
from .cloud import matches, relative
from .sources import verify_sources
from . import build, gateway, packaging

MANIFEST = 'host-runtime-manifest.json'


def retained(storage, kit):
    require(kit is not None, 'Specify --kit-inputs for retained simulator, Python and QEMU')
    require(storage_volume(kit)['uuid'] == storage.volume['uuid'], 'Host kit must be on bound volume')
    pin = next(r for r in storage.release.value['inputs'] if r['id'] == 'host-runtime')
    path = matches(Path(kit)/relative(pin['kitPath']), pin)
    value = read_json(path)
    require(value.get('status') == 'ASSEMBLED_HOST_LAUNCH_NOT_DISTRIBUTION_QUALIFIED'
            and value.get('credentialsIncluded') is False, 'Retained host identity invalid')
    return path.parent, pin


def selected(storage, state, target):
    choices = [(key, v) for key, v in state['builds'].items() if v['target'] == target]
    require(len(choices) == 1, 'Exactly one completed '+target+' build required')
    key, value = choices[0]
    require(digest(value['inputs']) == key, 'Upstream build key differs')
    output = storage.path('builds/'+target+'/'+key)
    if target == 'presenter':
        build.verify_output(output)
    else:
        gateway.verify_output(output, value['inputs'])
    return key, output


def receipt_path(output):
    return output.parent/(output.name+'.receipt.json')


def verify(output, inputs, receipt=None):
    receipt = read_json(receipt_path(output)) if receipt is None else receipt
    require(receipt.get('inputs') == inputs and receipt.get('status') == 'ASSEMBLED_NOT_RUNTIME_QUALIFIED'
            and receipt.get('externalDistributionApproved') is False, 'Host build receipt differs')
    matches(output/MANIFEST, receipt['manifest'])
    value = read_json(output/MANIFEST)
    require(value.get('schemaVersion') == 1 and value.get('credentialsIncluded') is False
            and value.get('status') == 'ASSEMBLED_HOST_LAUNCH_NOT_DISTRIBUTION_QUALIFIED', 'Host identity differs')
    names = {MANIFEST}
    require(len(receipt['stamps']) == len(value['files']), 'Host stamp count differs')
    for row in value['files']:
        name = str(relative(row['path']))
        require(name not in names, 'Duplicate host file')
        names.add(name)
        path = regular(output/name)
        require(path.stat().st_size == row['bytes'] and stat.S_IMODE(path.stat().st_mode) == row['mode']
                and packaging.stamp(path) == receipt['stamps'].get(name), 'Host output changed')
    actual = {MANIFEST}
    for path in output.rglob('*'):
        require(not path.is_symlink(), 'Linked host output')
        if not path.is_dir():
            actual.add(path.relative_to(output).as_posix())
    require(names == actual, 'Host output inventory differs')
    return receipt


def probe_native(storage, output):
    """A separate process boundary: macOS rejects sandbox_apply inside a sandbox."""
    policy = '(version 1)(allow default)(deny network*)(deny file-read* (subpath "/opt/homebrew"))'
    env = storage.environment()
    cache = storage.path('cache/carla')
    cache.mkdir(parents=True, exist_ok=True)
    env['CARLA_CACHE_DIR'] = str(cache)
    result = []
    for name in ('carla-ego-runtime', 'carla-viss-client', 'qemu-img', 'qemu-system-aarch64'):
        flag = '--help' if name == 'carla-viss-client' else '--version'
        response = run_command(['/usr/bin/sandbox-exec', '-p', policy, output/'native/bin'/name, flag],
                               env=env, cwd=storage.root, timeout=30)
        require(response.returncode == 0 and response.stdout.strip(), 'Relocated native probe failed: '+name)
        result.append({'entry': name, 'argument': flag, 'exitCode': 0,
                       'homebrewReadDenied': True, 'networkDenied': True})
    return result


def assemble(storage, state, kit, sdk, python, progress):
    require(storage.profile == 'developer', 'Host adapter requires developer profile')
    verify_sources(storage, state)
    storage.check(additional=24*GIB, reserve=90*GIB)
    trees, revision = packaging.producer(storage, 'host-runtime')
    source, pin = retained(storage, kit)
    sdk = Path(sdk) if sdk is not None else None
    sdk_pin = gateway.sdk_input(storage, sdk)
    ui_key, ui = selected(storage, state, 'presenter')
    gateway_key, native = selected(storage, state, 'gateway')
    require(state['builds'][gateway_key]['inputs']['sdk'] == sdk_pin, 'Gateway SDK selection differs')
    inputs = {'producerTrees': trees, 'hostManifest': pin, 'sdk': sdk_pin,
              'presenter': ui_key, 'gateway': gateway_key,
              'adapterSha256': sha256(ROOT/'scripts/reproduction/host.py'),
              'workerSha256': sha256(ROOT/'scripts/reproduction/host_worker.py')}
    key = digest(inputs)
    output = storage.path('builds/host-runtime/'+key)
    marker = output.parent/(key+'.inputs.json')
    if key in state['builds']:
        require(state['builds'][key] == {'target': 'host-runtime', 'inputs': inputs}, 'Host state differs')
        verify(output, inputs)
        progress('BUILD_REUSED', 'host-runtime')
        return key
    if output.exists():
        require(marker.exists() and read_json(marker) == inputs, 'Unowned host collision')
        verify(output, inputs)
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        atomic_json(marker, inputs)
        policy = output.parent/(key+'.sb')
        policy.write_text('(version 1)\n(allow default)\n(deny network*)\n')
        progress('BUILD_STARTED', 'host-runtime')
        result = run_command(['/usr/bin/sandbox-exec', '-f', policy, python, '-I', '-B',
            ROOT/'scripts/reproduction/host_worker.py', ROOT, storage.path('sources/integration'),
            storage.path('sources/vehicle-gateway'), source, sdk, ui, native, output],
            env=storage.environment(), cwd=storage.root, timeout=900)
        output.parent.joinpath(key+'.log').write_bytes((result.stdout+result.stderr)[-2**20:])
        require(result.returncode == 0, 'Host owner failed; inspect retained workspace log')
        probes = probe_native(storage, output)
        value = read_json(output/MANIFEST)
        atomic_json(receipt_path(output), {'status': 'ASSEMBLED_NOT_RUNTIME_QUALIFIED',
            'inputs': inputs, 'producerRevision': revision, 'externalDistributionApproved': False,
            'nativeProbes': probes,
            'manifest': {'path': MANIFEST, 'bytes': (output/MANIFEST).stat().st_size, 'sha256': sha256(output/MANIFEST)},
            'stamps': {r['path']: packaging.stamp(regular(output/r['path'])) for r in value['files']}})
    verify_sources(storage, state)
    require(packaging.producer(storage, 'host-runtime')[0] == trees, 'Producer changed during host assembly')
    verify(output, inputs)
    state['builds'][key] = {'target': 'host-runtime', 'inputs': inputs}
    storage.save(state)
    progress('ASSEMBLED_NOT_RUNTIME_QUALIFIED', 'host-runtime')
    return key
