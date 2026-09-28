# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Assemble a non-installed native UI/web/helper candidate from explicit inputs."""

import argparse
import json
from pathlib import Path
import shutil
import stat
import subprocess

from native_bundle import BundleError, SYSTEM, command, entitlements, inspect, sha256

HELPERS = (
    'run_m6_interactive.py', 'run_m5.py', 'behavior_agent_controller.py',
    'external_control_controller.py', 'external_control_protocol.py',
    'external_control_client.py', 'keyboard_control_bridge.py',
    'brake_event_scenario.py', 'road_recovery.py',
)
PACKAGE = Path('apps/demo-orchestrator/src/aosedge_demo_orchestrator')


def safe_relative(value):
    path = Path(value)
    if (not value or path.is_absolute() or '..' in path.parts or '.' in value.split('/')
            or '\\' in value or '\x00' in value or '\n' in value):
        raise BundleError('Unsafe relative payload path')
    return path


def regular(root, relative):
    relative = safe_relative(str(relative))
    path = root / relative
    if root.is_symlink() or any(part.is_symlink() for part in (path, *path.parents) if part != root.parent):
        raise BundleError('Payload source has a symlink')
    if not stat.S_ISREG(path.stat().st_mode):
        raise BundleError('Payload source is not a regular file')
    return path


def tracked(root, scope):
    value = subprocess.run(['/usr/bin/git', '-C', str(root), 'ls-files', '-z', '--', scope],
                           capture_output=True, check=True, timeout=10).stdout.decode()
    return [safe_relative(name) for name in value.split('\0') if name]


def web_allowed(path):
    return (path == Path('index.html') or path == Path('.vite/manifest.json')
            or len(path.parts) >= 2 and path.parts[0] == 'assets'
            and not any(part.startswith('.') for part in path.parts)
            and path.suffix in ('.html', '.js', '.css', '.png', '.svg', '.woff2', '.ico'))


def insert(files, target, source):
    target = safe_relative(str(target))
    if target in files:
        raise BundleError('Duplicate payload destination')
    files[target] = source


def plan(integration, gateway, inputs):
    files = {}
    python_paths = [p for p in tracked(integration, str(PACKAGE)) if p.suffix == '.py']
    if PACKAGE / '__init__.py' not in python_paths or PACKAGE / 'presenter.py' not in python_paths:
        raise BundleError('Orchestrator source package incomplete')
    for path in python_paths:
        insert(files, Path('demo') / path, regular(integration, path))
    gateway_tracked = set(tracked(gateway, 'tools')) | set(tracked(gateway, 'config'))
    gateway_paths = [Path('tools') / name for name in HELPERS]
    gateway_paths.append(Path('config/m6_2_town10hd_handover.json'))
    for path in gateway_paths:
        if path not in gateway_tracked:
            raise BundleError('Gateway helper must be tracked')
        insert(files, Path('gateway') / path, regular(gateway, path))
    for owner, root in [('integration', integration), ('gateway', gateway)]:
        insert(files, Path('notices') / owner / 'LICENSE', regular(root, Path('LICENSE')))
    receipt = json.loads(regular(inputs, Path('build-receipt.json')).read_text())
    if receipt.get('status') != 'BUILT_NOT_RUNTIME_QUALIFIED' or not receipt.get('sourcesUnchanged'):
        raise BundleError('Native/web build has no completed receipt')
    recorded = {safe_relative(row['path']): row for row in receipt['files']}
    if len(recorded) != len(receipt['files']):
        raise BundleError('Build receipt contains duplicate paths')
    actual = set()
    for subdirectory in ('native', 'web'):
        for source in sorted((inputs / subdirectory).rglob('*')):
            if source.is_symlink():
                raise BundleError('Build output has a symlink')
            if source.is_dir():
                continue
            relative = source.relative_to(inputs)
            actual.add(relative)
            row = recorded.get(relative)
            source = regular(inputs, relative)
            if row is None or source.stat().st_size != row['bytes'] or sha256(source) != row['sha256']:
                raise BundleError('Build output changed after receipt')
            if subdirectory == 'web':
                within = source.relative_to(inputs / 'web')
                if not web_allowed(within):
                    raise BundleError('Unexpected web output (maps/private data are forbidden)')
                target = Path('demo/apps/presenter-ui/dist') / within
            else:
                if relative not in (
                    Path('native/Demo Presenter'),
                    Path('native/Driving Control.app/Contents/Info.plist'),
                    Path('native/Driving Control.app/Contents/MacOS/KeyboardControl'),
                    Path('native/Driving Control.app/Contents/_CodeSignature/CodeResources')):
                    raise BundleError('Unexpected native output')
                target = relative
            insert(files, target, source)
    if actual != set(recorded):
        raise BundleError('Build receipt/output inventory mismatch')
    for required in ('native/Demo Presenter', 'native/Driving Control.app/Contents/Info.plist',
                     'native/Driving Control.app/Contents/MacOS/KeyboardControl',
                     'demo/apps/presenter-ui/dist/index.html'):
        if Path(required) not in files:
            raise BundleError('Required native/web entry missing')
    # Freeze source identity, not merely a current Git revision label.
    for source in (integration / PACKAGE / 'native/PresenterWorkspace.swift',
                   gateway / 'tools/KeyboardControl.swift', gateway / 'tools/KeyboardControl-Info.plist',
                   integration / 'apps/presenter-ui/package-lock.json'):
        if receipt['inputHashes'].get(str(source)) != sha256(source):
            raise BundleError('Source no longer matches the build receipt')
    return files, receipt


def verify_native(root):
    for relative in ('native/Demo Presenter', 'native/Driving Control.app/Contents/MacOS/KeyboardControl'):
        path = root / relative
        info = inspect(path)
        if any(not load.startswith(SYSTEM) for load in info['dependencies']):
            raise BundleError('UI has a non-system native dependency')
        if any(not value.startswith(('/usr/lib/swift', '@executable_path/')) for value in info['rpaths']):
            raise BundleError('UI has a development rpath')
        if entitlements(path):
            raise BundleError('Unexpected UI entitlements')
        command(['/usr/bin/codesign', '--verify', '--strict', path])
    command(['/usr/bin/codesign', '--verify', '--deep', '--strict', root / 'native/Driving Control.app'])


def assemble(integration, gateway, inputs, output):
    integration, gateway, inputs = (p.resolve(strict=True) for p in (integration, gateway, inputs))
    output = output.absolute()
    if output.exists() or output.is_symlink() or not output.parent.is_dir():
        raise BundleError('Output must be new with an existing parent')
    files, receipt = plan(integration, gateway, inputs)
    total = sum(p.stat().st_size for p in files.values())
    if total > 128 * 2**20 or shutil.disk_usage(output.parent).free < 90 * 2**30 + total:
        raise BundleError('Disk/input-size budget exceeded')
    verify_native(inputs)
    source_hashes = {target: sha256(path) for target, path in files.items()}
    output.mkdir(mode=0o700)
    entries = []
    for target, source in sorted(files.items()):
        destination = output / target
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        destination.chmod(0o755 if target.parts[0] == 'native' and
                          (target.name == 'Demo Presenter' or target.name == 'KeyboardControl') else 0o644)
        if sha256(destination) != source_hashes[target] or sha256(source) != source_hashes[target]:
            raise BundleError('Payload source/copy changed during assembly')
        entries.append({'path': str(target), 'bytes': destination.stat().st_size, 'sha256': source_hashes[target]})
    verify_native(output)
    revisions = {owner: command(['/usr/bin/git', '-C', root, 'rev-parse', 'HEAD']).strip()
                 for owner, root in [('integration', integration), ('gateway', gateway)]}
    manifest = {'schemaVersion': 1, 'status': 'ASSEMBLED_NOT_INTEGRATED', 'revisions': revisions,
                'files': entries, 'sourceFilesByteIdentical': True, 'runtimeSelectorsChanged': False,
                'buildReceiptSha256': sha256(inputs / 'build-receipt.json'),
                'buildTools': {'swift': receipt['swift'], 'node': receipt['node']},
                'nativeArchitecture': receipt['architecture'], 'initialMacOSTarget': receipt['initialMacOSTarget'],
                'excluded': ['credentials', 'run state', 'operator configuration', 'source maps',
                             'node_modules', 'Swift sources', 'developer Python environments'],
                'externalDistributionApproved': False,
                'openGates': ['operator selectors', 'native integrated session', 'Cloud worker',
                              'full Stage 2', 'clean Mac', 'redistribution review']}
    with (output / 'ui-helper-manifest.json').open('x') as stream:
        json.dump(manifest, stream, indent=2)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('integration', 'gateway', 'inputs', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    result = assemble(args.integration, args.gateway, args.inputs, args.output)
    print(json.dumps({'status': result['status'], 'files': len(result['files']),
                      'bytes': sum(row['bytes'] for row in result['files'])}))


if __name__ == '__main__':
    main()
