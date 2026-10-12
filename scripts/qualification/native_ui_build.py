#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Build two small signed qualification apps; no runtime/DMG change or GUI launch."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import plistlib
import shutil
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent/'distribution'))
from build_scratch import directory, safe

IDENTITY = '0514708CB8DA6BB8C26823D4F01C9F6869908008'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def control_prefix(path):
    source = path.read_text()
    if source.count('final class TelemetryView: NSView {') != 1:
        raise ValueError('CONTROL_SOURCE_BOUNDARY_INVALID')
    return source.split('final class TelemetryView: NSView {', 1)[0]


def build(workspace, gateway, output):
    os.umask(0o077)
    workspace, gateway, output = safe(workspace), safe(gateway), safe(output)
    if output.exists() or not output.parent.is_dir() or output.parent.stat().st_dev != workspace.stat().st_dev:
        raise ValueError('NEW_OUTPUT_ON_WORKSPACE_VOLUME_REQUIRED')
    if shutil.disk_usage(workspace).free < 60*2**30:
        raise ValueError('BUILD_RESERVE_UNAVAILABLE')
    source = gateway/'tools/KeyboardControl.swift'
    fixture = HERE/'native/ControlFixture.swift'
    runner = HERE/'native/NativeUIRunner.swift'
    inputs = {str(p): digest(p) for p in (source, fixture, runner)}
    output.mkdir(mode=0o700)
    steps = []
    with directory(workspace) as scratch:
        policy = scratch/'offline.sb'
        policy.write_text('(version 1)\n(allow default)\n(deny network*)\n')

        def run(label, command):
            began = time.monotonic()
            child = subprocess.run(command, capture_output=True, text=True, timeout=100)
            (output/(label+'.log')).write_text(child.stdout+child.stderr)
            steps.append(dict(stage=label, seconds=round(time.monotonic()-began,3), exitCode=child.returncode))
            if child.returncode: raise ValueError('NATIVE_BUILD_FAILED_'+label.upper().replace('-','_'))

        common = ['/usr/bin/sandbox-exec','-f',str(policy),'/usr/bin/xcrun','swiftc','-O',
                  '-target','arm64-apple-macos26.0','-module-cache-path',str(scratch/'swift-cache')]
        targets = (('DrivingControlPilot.app','ControlFixture','org.aosedge.sdv.qualification.control-fixture'),
                   ('Native UI Runner.app','NativeUIRunner','org.aosedge.sdv.qualification.native-ui-runner'))
        compiled = []
        for app_name, executable, bundle_id in targets:
            app = output/app_name
            (app/'Contents/MacOS').mkdir(parents=True)
            info = dict(CFBundleIdentifier=bundle_id,CFBundleExecutable=executable,
                CFBundleName=app_name[:-4],CFBundlePackageType='APPL',CFBundleVersion='1',
                CFBundleShortVersionString='0.1.0',LSMinimumSystemVersion='26.0',NSHighResolutionCapable=True)
            if executable == 'NativeUIRunner': info['LSUIElement'] = True
            (app/'Contents/Info.plist').write_bytes(plistlib.dumps(info))
            main = scratch/(executable+'.swift')
            main.write_text(control_prefix(source)+'\n'+fixture.read_text() if executable=='ControlFixture' else runner.read_text())
            binary = app/'Contents/MacOS'/executable
            run(executable+'-compile',[*common,str(main),'-o',str(binary),'-framework','AppKit',
                                      '-framework','ApplicationServices','-framework','CryptoKit'])
            if executable == 'NativeUIRunner':
                # Pure parser assertions only: this path never creates NSApplication.
                run('runner-unit',[str(binary),'--self-test'])
            run(executable+'-sign',['/usr/bin/codesign','--force','--sign',IDENTITY,str(app)])
            run(executable+'-verify',['/usr/bin/codesign','--verify','--deep','--strict',str(app)])
            compiled.append(dict(app=app_name,bundleId=bundle_id,executable=executable,sha256=digest(binary)))
        if any(digest(Path(p)) != expected for p,expected in inputs.items()):
            raise ValueError('NATIVE_INPUT_CHANGED')
    receipt = dict(status='BUILT_NOT_UI_QUALIFIED',artifact='NATIVE_QUALIFICATION_PILOT',
        productPayloadChanged=False,vehicleConnected=False,signatureIdentity=IDENTITY,
        inputs=inputs,apps=compiled,steps=steps)
    (output/'build-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return receipt


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for field in ('workspace','gateway','output'): p.add_argument('--'+field,type=Path,required=True)
    a=p.parse_args()
    result=build(a.workspace,a.gateway,a.output)
    print(json.dumps(dict(status=result['status'],steps=result['steps'])))


if __name__=='__main__': main()
