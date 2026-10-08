# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Build only the native local-setup preview with an authenticated Python bootstrap."""

import argparse
import json
import os
from pathlib import Path
import plistlib
import shutil
import stat
import subprocess
import tempfile

from installation_inputs import Bundle, digest, file_info, require, unlinked
from setup_bridge import release, supported_platform
import setup_signing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PYTHON = 'demo-artifacts/aosedge-sdv-demo/host-runtime/python/'
HELPERS = ('setup_bridge.py', 'setup_cloud.py', 'setup_launch.py', 'setup_backends.py', 'setup_release.json', 'installation.py', 'installation_inputs.py', 'version_management.py')


def python_files(bundle):
    rows = {name: row for name, row in bundle.rows.items() if name.startswith(PYTHON)}
    require(PYTHON + 'bin/python3.12' in rows and 10 < len(rows) < 10000,
            'SETUP_BOOTSTRAP_MISSING')
    return rows


def copy_python(bundle, destination):
    rows = python_files(bundle)
    for name, row in sorted(rows.items()):
        source = bundle.root / name
        bundle.unchanged(name)
        require(digest(source) == row.sha256, 'SETUP_BOOTSTRAP_DIGEST_MISMATCH')
        target = destination / name[len(PYTHON):]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        target.chmod(row.mode)
        require(target.stat().st_size == row.size and digest(target) == row.sha256
                and stat.S_IMODE(target.stat().st_mode) == row.mode, 'SETUP_BOOTSTRAP_TRANSFER_MISMATCH')
    return len(rows)


def bundle_info(executable):
    return dict(CFBundleIdentifier=setup_signing.IDENTIFIER, CFBundleName='SDV Lab Setup',
                CFBundleDisplayName='AosEdge SDV Lab Setup', CFBundleExecutable=executable,
                CFBundlePackageType='APPL', CFBundleShortVersionString='0.1.0', CFBundleVersion='1',
                LSMinimumSystemVersion='26.0', NSHighResolutionCapable=True, NSPrincipalClass='NSApplication',
                NSRemovableVolumesUsageDescription='SDV Lab installs and reads its packages in your selected folder on an external drive.')


def build(kit, output, *, signing_identity=None, ad_hoc=False,
          developer_id_identity=None, hardened_runtime=False,
          input_checkpoint=None, release_checkpoint=None):
    from application import export_plan, LOCKS
    supported_platform()
    # Fail before copying or compiling when stable signing is unavailable.
    distribution = developer_id_identity is not None
    require(not distribution or (signing_identity is None and not ad_hoc),
            'SETUP_SIGNING_MODE_REQUIRED')
    require(type(hardened_runtime) is bool and not (hardened_runtime and ad_hoc),
            'SETUP_SIGNING_HARDENED_MODE_INVALID')
    signer = setup_signing.select(developer_id_identity if distribution else signing_identity,
                                  ad_hoc, distribution=distribution)
    kit, output = unlinked(kit), unlinked(output)
    require(output.parent.is_dir() and not output.exists(), 'SETUP_OUTPUT_MUST_BE_NEW')
    require(not output.is_relative_to(kit) and not kit.is_relative_to(output), 'SETUP_OUTPUT_OVERLAP')
    require((input_checkpoint is None) == (release_checkpoint is None), 'SETUP_CHECKPOINT_PAIR_REQUIRED')
    if release_checkpoint is None:
        trusted = release()
    else:
        from candidate_inputs import setup_release
        trusted = setup_release(ROOT, release_checkpoint)
    bundle = Bundle(kit, trusted['manifestSha256'])
    rows = python_files(bundle)
    application_sources = export_plan(ROOT) if input_checkpoint is None else export_plan(ROOT, input_checkpoint)
    for lock_name in LOCKS.values():
        selected = json.loads(application_sources['contracts/'+lock_name])['manifest']
        shipped = json.loads((kit/'aosedge-sdv-demo/contracts'/lock_name).read_bytes())['manifest']
        require(selected == shipped, 'SETUP_APPLICATION_INPUT_PIN_MISMATCH')
    require(shutil.disk_usage(output.parent).free >= sum(row.size for row in rows.values()) + 2 * 2**30,
            'SETUP_BUILD_SPACE_INSUFFICIENT')
    output.mkdir(mode=0o700)
    app = output / 'AosEdge SDV Lab Setup.app'
    contents = app / 'Contents'
    executable = contents / 'MacOS/SDVLabSetup'
    resources = contents / 'Resources'
    executable.parent.mkdir(parents=True)
    resources.mkdir()
    count = copy_python(bundle, resources / 'python')
    for leaf in HELPERS:
        target = resources / 'tooling/scripts/distribution' / leaf
        target.parent.mkdir(parents=True, exist_ok=True)
        source = ROOT/release_checkpoint if leaf == 'setup_release.json' and release_checkpoint else HERE/leaf
        shutil.copyfile(source, target)
    for name, raw in application_sources.items():
        relative = Path(name)
        target = resources / 'tooling' / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    info = bundle_info(executable.name)
    (contents / 'Info.plist').write_bytes(plistlib.dumps(info))
    env = {'PATH': '/usr/bin:/bin:/usr/sbin:/sbin', 'HOME': str(Path.home()), 'LC_ALL': 'C'}
    with tempfile.TemporaryDirectory(prefix='sdv-setup-compile.') as scratch:
        command = ['/usr/bin/sandbox-exec', '-p', '(version 1)(allow default)(deny network*)',
                   '/usr/bin/xcrun', 'swiftc', '-O', '-target', 'arm64-apple-macos26.0',
                   '-module-cache-path', str(Path(scratch) / 'cache'), str(HERE / 'native/Setup.swift'),
                   '-o', str(executable), '-framework', 'AppKit']
        subprocess.run(command, check=True, env=env, timeout=180)
    subprocess.run([str(executable), '--self-test'], check=True, env=env, timeout=30)
    signing = setup_signing.sign(app, signer, hardened=hardened_runtime or distribution,
                                 distribution=distribution)
    # Prove the embedded interpreter + trusted helper can start, without kit code.
    probe = subprocess.run([str(resources / 'python/bin/python3.12'), '-I', '-B',
                            str(resources / 'tooling/scripts/distribution/setup_bridge.py')],
                           input=b'{}', capture_output=True, timeout=30, env=env)
    require(probe.returncode == 1 and probe.stderr == b''
            and json.loads(probe.stdout) == dict(kind='error', code='SETUP_ACTION_INVALID'),
            'SETUP_EMBEDDED_PROBE_FAILED')
    source_files = [ROOT/release_checkpoint if leaf == 'setup_release.json' and release_checkpoint else HERE/leaf
                    for leaf in HELPERS] + [
        HERE / 'native/Setup.swift', HERE / 'setup_build.py', HERE / 'setup_signing.py']
    source_files += [ROOT / name for name in application_sources]
    receipt = dict(schemaVersion=1, status=('DISTRIBUTION_SETUP_UNNOTARIZED' if distribution
                                          else 'LOCAL_NATIVE_SETUP_PREVIEW'), manifestSha256=bundle.pin,
                   bootstrapFiles=count, binarySha256=digest(executable),
                   sources={str(p.relative_to(ROOT)): digest(p) for p in source_files},
                   **signing, notarized=False, cloudEnrollmentImplemented=True,
                   cloudEnrollmentLiveQualified=False, exactSubjectReferencesImplemented=True,
                   existingCloudAccessImplemented=True,
                   presenterLaunchImplemented=True,
                   runtimeLaunched=False, developerCredentialsCopied=False)
    if input_checkpoint is not None:
        import hashlib
        receipt['packagingCheckpoint'] = dict(path=input_checkpoint, sha256=digest(ROOT/input_checkpoint))
        receipt['exportedApplicationHashes'] = {name: hashlib.sha256(raw).hexdigest()
                                                 for name, raw in application_sources.items()}
    (output / 'build-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kit', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--input-checkpoint')
    parser.add_argument('--release-checkpoint')
    signing = parser.add_mutually_exclusive_group(required=True)
    signing.add_argument('--signing-identity', help='Exact SHA-1 identity from security find-identity; Apple Development only')
    signing.add_argument('--developer-id-identity', help='Exact Developer ID Application SHA-1; hardened/timestamped output, no notarization submission')
    signing.add_argument('--ad-hoc', action='store_true', help='Engineering-only preview; permissions may reset between builds')
    parser.add_argument('--hardened-runtime', action='store_true', help='Explicit Apple Development hardening proof; implicit for Developer ID')
    args = parser.parse_args()
    print(json.dumps(build(args.kit, args.output, signing_identity=args.signing_identity,
                           ad_hoc=args.ad_hoc, developer_id_identity=args.developer_id_identity,
                           hardened_runtime=args.hardened_runtime, input_checkpoint=args.input_checkpoint,
                           release_checkpoint=args.release_checkpoint), sort_keys=True))
