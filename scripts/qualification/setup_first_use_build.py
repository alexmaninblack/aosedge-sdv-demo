#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Build the fixed Setup-only native qualification client on the selected SSD."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import plistlib
import subprocess
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'distribution'))
from build_scratch import directory, safe
from native_ui_build import IDENTITY


def build(workspace, output):
    os.umask(0o077)
    workspace, output = safe(workspace), safe(output)
    if output.exists() or output.parent.stat().st_dev != workspace.stat().st_dev:
        raise ValueError('NEW_SSD_OUTPUT_REQUIRED')
    output.mkdir(mode=0o700)
    app = output / 'Native UI Runner.app'
    binary = app / 'Contents/MacOS/NativeUIRunner'
    binary.parent.mkdir(parents=True)
    info = dict(CFBundleIdentifier='org.aosedge.sdv.qualification.native-ui-runner',
        CFBundleExecutable='NativeUIRunner', CFBundleName='Native UI Runner',
        CFBundlePackageType='APPL', CFBundleVersion='2', CFBundleShortVersionString='0.2.0',
        LSMinimumSystemVersion='26.0', LSUIElement=True)
    (app / 'Contents/Info.plist').write_bytes(plistlib.dumps(info))
    source = HERE / 'native/SetupFirstUse.swift'
    with directory(workspace) as scratch:
        policy = scratch / 'offline.sb'
        policy.write_text('(version 1)\n(allow default)\n(deny network*)\n')
        commands = [
            ['/usr/bin/sandbox-exec', '-f', str(policy), '/usr/bin/xcrun', 'swiftc', '-O',
             '-target', 'arm64-apple-macos26.0', '-module-cache-path', str(scratch / 'swift-cache'),
             str(source), '-o', str(binary), '-framework', 'AppKit', '-framework', 'ApplicationServices', '-framework', 'CryptoKit'],
            [str(binary), '--self-test'],
            ['/usr/bin/codesign', '--force', '--sign', IDENTITY, str(app)],
            ['/usr/bin/codesign', '--verify', '--deep', '--strict', str(app)]]
        for index, command in enumerate(commands):
            p = subprocess.run(command, capture_output=True, text=True, timeout=120)
            (output / ('build-' + str(index) + '.log')).write_text(p.stdout + p.stderr)
            if p.returncode:
                raise ValueError('FIRST_USE_BUILD_FAILED_' + str(index))
    result = dict(sourceSha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        executableSha256=hashlib.sha256(binary.read_bytes()).hexdigest(), signer=IDENTITY,
        productPayloadChanged=False, status='BUILT_NOT_UI_QUALIFIED')
    (output / 'build-receipt.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--workspace', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(build(a.workspace, a.output)))
