# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Isolated installed-path proof; run under the documented deny profile."""

import argparse
from contextlib import nullcontext
import importlib
import json
from pathlib import Path
import socket
import subprocess
import sys
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kit', type=Path, required=True)
    parser.add_argument('--denied-source', type=Path, required=True)
    parser.add_argument('--instance-root', type=Path, help='explicit disposable preselected instance for managed kits')
    args = parser.parse_args()
    kit = args.kit
    app = kit / 'aosedge-sdv-demo'
    catalogue = kit / 'demo-artifacts/aosedge-sdv-demo'
    for denied in (args.denied_source / 'LICENSE', Path('/opt/homebrew/bin/python3.12')):
        try:
            denied.read_bytes()
        except PermissionError:
            pass
        else:
            raise AssertionError('Developer-read denial did not apply')
    try:
        socket.create_connection(('192.0.2.1', 9), timeout=.2)
    except PermissionError:
        pass
    else:
        raise AssertionError('Network denial did not apply')
    try:
        with (kit / 'must-not-write').open('xb'):
            pass
    except PermissionError:
        pass
    else:
        raise AssertionError('Immutable-package write denial did not apply')

    sys.path.insert(0, str(app / 'apps/demo-orchestrator/src'))
    manifest = json.loads((kit / 'application-manifest.json').read_bytes())
    count = 0
    for row in manifest['applicationFiles']:
        path = Path(row['path'])
        if path.suffix == '.py':
            importlib.import_module('aosedge_demo_orchestrator.' + path.stem)
            count += 1
    from aosedge_demo_orchestrator import runtime_paths, status, host_runtime, vm_runtime
    from aosedge_demo_orchestrator import cloud_runtime, backend_inputs, preparation_inputs
    from aosedge_demo_orchestrator.environment import EnvironmentService, EnvironmentError
    from aosedge_demo_orchestrator.service_packages import package_configuration
    from aosedge_demo_orchestrator.source import SourceDriver
    from aosedge_demo_orchestrator.vm import VMService
    from aosedge_demo_orchestrator.cloud_setup import CloudSetup
    from aosedge_demo_orchestrator.units import UnitService
    from aosedge_demo_orchestrator.releases import LEDGER, ReleaseContinuity
    if manifest.get('installedStateContract'):
        assert args.instance_root is not None, 'Managed proof requires a previously selected disposable instance'
    context = nullcontext(args.instance_root.parent) if args.instance_root else tempfile.TemporaryDirectory(prefix='sdvip.', dir='/private/tmp')
    with context as directory:
        state = args.instance_root or Path(directory) / 's'
        created = runtime_paths.create_instance(state)
        sentinel = state / 'artifacts/retention-fixture.json'
        with sentinel.open('x') as stream:
            stream.write('{"releaseCounter":123,"history":"preserve"}')
        before = sentinel.read_bytes()
        ledger = state / LEDGER
        with ledger.open('x') as stream:
            stream.write('{"schemaVersion":1,"versions":{"vdp":"123.0.0","brake":"84.0.0","tire":"47.0.0"}}')
        ledger.chmod(0o600)
        original_ledger = ledger.read_bytes()
        for repeat in range(2):
            with runtime_paths.installed_session(state):
                assert status.project_root() == state
                env = EnvironmentService()
                assert env.catalog.project == state / 'artifacts/aosedge-sdv-demo'
                assert env.catalog.input_project == catalogue
                assert runtime_paths.program_root() == app
                config = status.load_configuration(state)
                assert all(p['credential'].is_relative_to(state) and not p['credential'].exists()
                           for p in config['cloudProfiles'].values())
                host = host_runtime.selected()
                if repeat == 0:
                    host.verify('ui', 'native', 'python', 'openssl')
                    vm = vm_runtime.selected(env)
                    assert Path(vm.image_tool()).is_relative_to(catalogue)
                    assert vm.data_directory().is_relative_to(catalogue)
                    cloud = cloud_runtime.selected(state)
                    cloud.verify()
                    for worker in cloud_runtime.WORKERS:
                        command, _ = cloud_runtime.launch(state, Path('/denied/python'), worker)
                        assert Path(command[0]).is_relative_to(catalogue)
                        assert Path(command[-1]).is_relative_to(app)
                    backend_inputs.selected(env).archive()
                    assert preparation_inputs.selected(env).runtime()
                    images = env.catalog.list()
                    assert len(images['images']) == 1 and not images['issues']
                    assert images['images'][0]['version'] == '6.1.1-maninblack.39'
                    assert not images['images'][0]['problems']
                    for team, profiles in (('brake', ('v1', 'v2', 'v3')), ('tire', ('v1',))):
                        for profile in profiles:
                            product = preparation_inputs.selected(env).service(team, profile)
                            configuration = package_configuration(Path(product['preparationInputsRoot']), team, profile, '999.0.0')
                            assert configuration == package_configuration(state, team, profile, '999.0.0')
                            assert configuration['items'][0]['configuration']['quotas']['noFileLimit'] == 1024
                    vm_service = VMService(env)
                    for call, reason in ((lambda: SourceDriver(vm_service).assets(), 'SOURCE_OPERATOR_TLS_REQUIRED'),
                                         (lambda: CloudSetup(UnitService(vm_service))._request(), 'CLOUD_CREDENTIAL_MISSING_OR_UNSAFE')):
                        try:
                            call()
                        except EnvironmentError as error:
                            assert str(error) == reason
                        else:
                            raise AssertionError('Unexpected inherited access')
                    unit = json.loads((app / 'config/aosvm-single-node-unitconfig.json').read_bytes())
                    assert unit['nodes'][0]['nodeType'] == 'aos-vm-main'
                done = subprocess.run(host.cli(state) + ['--output', 'json', 'image', 'list'],
                                      capture_output=True, text=True, timeout=30)
                assert done.returncode == 0, done.stderr
                assert '6.1.1-maninblack.39' in done.stdout
                assert sentinel.read_bytes() == before
                assert ReleaseContinuity(env).next('vdp') == '124.0.0'
                assert ledger.read_bytes() == original_ledger
                assert runtime_paths.instance_id() == created['instanceId']
            assert not (app / '.local').exists() and not (app / '.run').exists()
        assert runtime_paths.create_instance(state)['reused']
        assert sentinel.read_bytes() == before
        assert all(not getattr(module, '__file__', None) or module is sys.modules['__main__'] or
                   Path(module.__file__).is_relative_to(kit) for module in sys.modules.values())
    print(json.dumps(dict(status='PASS_ISOLATED_INSTALLED_STATE', applicationModules=count,
        separateState=True, allFiveSelectors=True, factoryCatalogue=True, privateCli=True,
        repeatedSelectionPreservedState=True, firstUseTlsAndCredentialsBlocked=True,
        developerReadsDenied=True, packageWritesDenied=True, networkDenied=True,
        liveRuntimeChanged=False, operatorStateCopied=False, cleanMacQualified=False)))


if __name__ == '__main__':
    main()
