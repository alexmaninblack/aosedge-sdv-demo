#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Create complete local installation media; never deploy or start the runtime."""

import argparse
import json
from pathlib import Path
import plistlib
import shutil
import subprocess
import tempfile

from installation_inputs import Bundle, digest, parse, read_small, require, unlinked
from installation import copy_file
from setup_bridge import release
import setup_signing

APP = 'AosEdge SDV Lab Setup.app'
KIT = 'Runtime Kit'
VOLUME = 'AosEdge SDV Lab'
GUIDE = '''AosEdge Platform - SDV Lab

Complete local installation preview for Apple Silicon / macOS 26 or later.
This engineering candidate is not a notarized public release.

1. Open AosEdge SDV Lab Setup. The included runtime is selected automatically.
2. Check installation, then Install package and Prepare local data.
3. Follow Setup for Docker, Cloud access and opening Presenter.

No Unreal Editor, source checkout, compiler or separate runtime download is needed.
Docker Desktop is a separately installed dependency with its own terms.
Internet and your own authorized Aos Cloud access are needed for the Cloud demo.
Installation does not create a vehicle or publish software.

Keep this disk image until Setup has finished; do not move the Runtime Kit folder.
The program files are copied to the chosen package store. After quitting Setup,
the image can be ejected. For this first consolidated-media preview, reopen Setup
and select the existing private-data folder for Open demo. Do not reinstall just
to launch again. The persistent Applications launcher and simplified wizard are
subsequent work; this preview does not claim to implement them.

Do not bypass a macOS security warning. Contact the kit provider if access is blocked.
'''


def validate_paths(kit, setup, output):
    kit, setup, output = map(unlinked, (kit, setup, output))
    require(kit.is_dir() and setup.is_dir(), 'MEDIA_INPUT_MISSING')
    require(output.suffix == '.dmg' and output.parent.is_dir() and not output.exists(), 'MEDIA_OUTPUT_MUST_BE_NEW')
    for source in (kit, setup):
        require(not output.is_relative_to(source), 'MEDIA_OUTPUT_OVERLAP')
    require(not output.with_suffix('.receipt.json').exists(), 'MEDIA_RECEIPT_EXISTS')
    return kit, setup, output


def setup_pin(setup, pin):
    app = unlinked(setup/APP)
    require(app.is_dir(), 'MEDIA_SETUP_MISSING')
    embedded = app/'Contents/Resources/tooling/scripts/distribution/setup_release.json'
    require(parse(read_small(embedded))['manifestSha256'] == pin, 'MEDIA_SETUP_PIN_MISMATCH')
    info = plistlib.loads((app/'Contents/Info.plist').read_bytes())
    require(info.get('CFBundleIdentifier') == setup_signing.IDENTIFIER, 'MEDIA_SETUP_IDENTITY_MISMATCH')
    setup_signing.run(['/usr/bin/codesign', '--verify', '--deep', '--strict', str(app)], 'MEDIA_SETUP_SIGNATURE_INVALID')
    details = setup_signing.run(['/usr/bin/codesign', '-dvv', str(app)], 'MEDIA_SETUP_SIGNATURE_INVALID')
    require('Signature=adhoc' not in details and ('Authority=Apple Development:' in details or
            'Authority=Developer ID Application:' in details), 'MEDIA_STABLE_SIGNER_REQUIRED')
    receipt = parse(read_small(setup/'build-receipt.json'))
    require(receipt.get('manifestSha256') == pin and receipt.get('stableSigningIdentity') is True,
            'MEDIA_SETUP_RECEIPT_MISMATCH')
    return app, receipt


def copy_payload(bundle, destination, progress=lambda row: None):
    require(not destination.exists(), 'MEDIA_PAYLOAD_EXISTS')
    destination.mkdir(mode=0o700)
    total, done = sum(row.size for row in bundle.rows.values()), 0
    for index, (name, row) in enumerate(sorted(bundle.rows.items()), 1):
        source, target = bundle.root/name, destination/name
        bundle.unchanged(name)
        target.parent.mkdir(parents=True, exist_ok=True)
        copy_file(source, target)
        require(target.stat().st_size == row.size and digest(target) == row.sha256, 'MEDIA_PAYLOAD_DIGEST_MISMATCH')
        bundle.unchanged(name)
        done += row.size
        if index % 2000 == 0:
            progress(dict(stage='MEDIA_COPY_VERIFIED', files=index, bytes=done, totalBytes=total))
    copied = Bundle(destination, bundle.pin)
    require(copied.rows == bundle.rows, 'MEDIA_PAYLOAD_INVENTORY_MISMATCH')
    bundle.check_inventory()
    for name in bundle.rows: bundle.unchanged(name)
    return dict(files=len(bundle.rows), logicalBytes=total)


def build(kit, setup, output, *, progress=lambda row: None, release_checkpoint=None):
    kit, setup, output = validate_paths(kit, setup, output)
    if release_checkpoint is None:
        pin = release()['manifestSha256']
    else:
        from candidate_inputs import setup_release
        pin = setup_release(Path(__file__).resolve().parents[2], release_checkpoint)['manifestSha256']
    bundle = Bundle(kit, pin)
    app, signature = setup_pin(setup, pin)
    # Allow an ordinary staging copy plus compressed-image worst case. Never
    # rely on clone sharing or make the internal disk a temporary staging area.
    needed = 2*sum(row.size for row in bundle.rows.values()) + 4*2**30
    require(shutil.disk_usage(output.parent).free >= needed, 'MEDIA_SPACE_INSUFFICIENT')
    staging = Path(tempfile.mkdtemp(prefix='.full-media-', dir=output.parent))
    progress(dict(stage='MEDIA_STAGING', path=str(staging)))
    try:
        payload = copy_payload(bundle, staging/KIT, progress)
        subprocess.run(['/usr/bin/ditto', str(app), str(staging/APP)], check=True, timeout=120)
        setup_signing.run(['/usr/bin/codesign', '--verify', '--deep', '--strict', str(staging/APP)], 'MEDIA_COPIED_SIGNATURE_INVALID')
        (staging/'Start Here.txt').write_text(GUIDE)
        progress(dict(stage='MEDIA_COMPRESSING'))
        subprocess.run(['/usr/bin/hdiutil', 'create', '-srcfolder', str(staging),
                        '-format', 'UDZO', '-volname', VOLUME, str(output)], check=True, timeout=1800)
        subprocess.run(['/usr/bin/hdiutil', 'verify', str(output)], check=True, timeout=300)
        receipt = dict(schemaVersion=1, status='COMPLETE_MEDIA_BUILT_NOT_INSTALLED',
                       manifestSha256=pin, dmgSha256=digest(output), dmgBytes=output.stat().st_size,
                       **payload, signing=signature['signing'], notarized=False,
                       runtimeStarted=False, cloudAccessed=False, operatorStateCopied=False)
        output.with_suffix('.receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
    except BaseException:
        progress(dict(stage='MEDIA_INCOMPLETE_PRESERVED', scratch=str(staging)))
        raise
    # Only this invocation's complete disposable media staging is removed.
    shutil.rmtree(staging)
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kit', required=True, type=Path)
    parser.add_argument('--setup', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--release-checkpoint')
    args = parser.parse_args()
    result = build(args.kit, args.setup, args.output, progress=lambda row: print(json.dumps(row), flush=True),
                   release_checkpoint=args.release_checkpoint)
    print(json.dumps(result), flush=True)
