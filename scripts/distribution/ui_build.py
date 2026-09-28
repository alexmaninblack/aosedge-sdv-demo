# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Prebuild unchanged UI sources; no installation or dependency download."""

import argparse
import json
from pathlib import Path
import plistlib
import shutil
import subprocess
import time

from native_bundle import BundleError, sha256
from ui_helpers import PACKAGE, regular, tracked


def controller_metadata(data):
    metadata = plistlib.loads(data)
    if metadata.get('CFBundleExecutable') != 'KeyboardControl':
        raise BundleError('Unexpected Controller executable metadata')
    metadata['LSMinimumSystemVersion'] = '26.0'
    return plistlib.dumps(metadata)


def build(integration, gateway, node, output):
    integration, gateway, node = (p.resolve(strict=True) for p in (integration, gateway, node))
    output = output.absolute()
    if output.exists() or output.is_symlink() or not output.parent.is_dir():
        raise BundleError('Output must be new with an existing parent')
    if shutil.disk_usage(output.parent).free < 90 * 2**30 + 128 * 2**20:
        raise BundleError('UI build disk reserve unavailable')
    web = integration / 'apps/presenter-ui'
    presenter = regular(integration, PACKAGE / 'native/PresenterWorkspace.swift')
    keyboard = regular(gateway, Path('tools/KeyboardControl.swift'))
    info = regular(gateway, Path('tools/KeyboardControl-Info.plist'))
    # Include tracked web source/config/assets, not an old dist or node_modules.
    web_inputs = [regular(integration, p) for p in tracked(integration, 'apps/presenter-ui')]
    sources = [presenter, keyboard, info, *web_inputs]
    hashes = {str(p): sha256(p) for p in sources}
    declared = json.loads((web / 'package.json').read_text())
    actual = subprocess.check_output([str(node), '--version'], text=True, timeout=10).strip()
    if actual != 'v' + declared['engines']['node']:
        raise BundleError('Node version differs from the source build pin')
    if not all((web / p).is_file() for p in ('node_modules/typescript/bin/tsc', 'node_modules/vite/bin/vite.js')):
        raise BundleError('Prepared offline web build dependencies required')
    output.mkdir(mode=0o700)
    (output / 'swift-cache').mkdir()
    app = output / 'native/Driving Control.app'
    (app / 'Contents/MacOS').mkdir(parents=True)
    # Runtime requires macOS 26 in this first engineering candidate. Do not
    # retain an older plist minimum that contradicts the actual deployment target.
    (app / 'Contents/Info.plist').write_bytes(controller_metadata(info.read_bytes()))
    policy = output / 'build-offline.sb'
    policy.write_text('(version 1)\n(allow default)\n(deny network*)\n')
    steps = []
    result = {'status': 'BUILDING', 'inputHashes': hashes, 'steps': steps,
              'runtimeInstallationChanged': False, 'network': 'denied per build subprocess',
              'metadataNormalization': {'LSMinimumSystemVersion': '26.0'}}

    def run(name, arguments, cwd=output):
        started = time.monotonic()
        command = ['/usr/bin/sandbox-exec', '-f', str(policy), *map(str, arguments)]
        value = subprocess.run(command, cwd=cwd, capture_output=True, timeout=100)
        (output / (name + '.log')).write_bytes(value.stdout + value.stderr)
        steps.append({'name': name, 'command': command, 'exitCode': value.returncode,
                      'elapsedSeconds': round(time.monotonic() - started, 3)})
        if value.returncode:
            raise BundleError(name + ' failed; see bounded build log')
        return value.stdout.decode()

    try:
        result['swift'] = run('swift-version', ['/usr/bin/xcrun', 'swiftc', '--version']).strip()
        result['node'] = actual
        common = ['/usr/bin/xcrun', 'swiftc', '-O', '-target', 'arm64-apple-macos26.0',
                  '-module-cache-path', output / 'swift-cache']
        run('presenter-build', [*common, presenter, '-o', output / 'native/Demo Presenter',
                                '-framework', 'AppKit', '-framework', 'WebKit'])
        run('controller-build', [*common, keyboard, '-o', app / 'Contents/MacOS/KeyboardControl',
                                 '-framework', 'AppKit'])
        for name, target in [('presenter', output / 'native/Demo Presenter'), ('controller', app)]:
            run(name + '-sign', ['/usr/bin/codesign', '--force', '--sign', '-', target])
            run(name + '-verify', ['/usr/bin/codesign', '--verify', '--deep', '--strict', target])
            rights = run(name + '-rights', ['/usr/bin/codesign', '-d', '--entitlements', '-', '--xml', target])
            if rights.strip() and plistlib.loads(rights):
                raise BundleError('Unexpected UI entitlements')
        run('web-typecheck', [node, web / 'node_modules/typescript/bin/tsc', '--noEmit'], cwd=web)
        run('web-build', [node, web / 'node_modules/vite/bin/vite.js', 'build', '--outDir', output / 'web'], cwd=web)
        if any(sha256(p) != hashes[str(p)] for p in sources):
            raise BundleError('Source changed while building')
        result['files'] = [{'path': str(p.relative_to(output)), 'bytes': p.stat().st_size, 'sha256': sha256(p)}
                           for directory in (output / 'native', output / 'web')
                           for p in sorted(directory.rglob('*')) if p.is_file()]
        result.update(status='BUILT_NOT_RUNTIME_QUALIFIED', sourcesUnchanged=True,
                      architecture='arm64', initialMacOSTarget='26.0', externalDistributionApproved=False)
    except BaseException:
        result['status'] = 'FAILED_BUILD'
        raise
    finally:
        (output / 'build-receipt.json').write_text(json.dumps(result, indent=2))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('integration', 'gateway', 'node', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    result = build(args.integration, args.gateway, args.node, args.output)
    print(json.dumps({'status': result['status'], 'files': len(result['files'])}))


if __name__ == '__main__':
    main()
