# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Build a private Python framework-derived candidate, never copy site-packages."""

import argparse
import json
from pathlib import Path
import re
import shutil

from native_bundle import BundleError, build, sha256


def excluded(directory, names):
    # Homebrew installs a customization hook into stdlib, outside site-packages.
    # Copying it reintroduces the developer prefix even under isolated (-I) mode.
    return [name for name in names if name in ('__pycache__', 'site-packages', 'test', 'lib-dynload',
                                              'sitecustomize.py', 'usercustomize.py',
                                              'sitecustomize', 'usercustomize')
            or name.startswith('config-') or name.endswith(('.pyc', '.pyo'))]


def assemble(version_root, output, allowed):
    version_root = version_root.resolve(strict=True)
    version = version_root.name
    if not re.fullmatch(r'3\.12', version):
        raise BundleError('Only the observed Python 3.12 candidate is in scope')
    executable = version_root / 'Resources/Python.app/Contents/MacOS/Python'
    standard = version_root / 'lib' / ('python' + version)
    if not executable.is_file() or not (standard / 'encodings/__init__.py').is_file():
        raise BundleError('Framework runtime inputs incomplete')
    # Resolve every source/symlink before the native assembler creates output.
    def check_tree(directory):
        size = 0
        for path in directory.iterdir():
            if path.name in excluded(directory, [path.name]):
                continue
            if path.is_symlink():
                raise BundleError('Unexpected stdlib symlink: ' + path.name)
            if path.is_dir():
                size += check_tree(path)
            elif path.is_file():
                size += path.stat().st_size
        return size
    standard_bytes = check_tree(standard)
    if standard_bytes >= 2**30:
        raise BundleError('Stdlib input-size budget exceeded')
    roots = {'python' + version: executable}
    for path in sorted((standard / 'lib-dynload').iterdir()):
        if path.is_symlink():
            raise BundleError('Unexpected native-module symlink: ' + path.name)
        if path.is_file() and path.name.endswith('.so'):
            roots['lib/python' + version + '/lib-dynload/' + path.name] = path
    if len(roots) < 2:
        raise BundleError('No stdlib native modules found')
    build(roots, allowed, output,
          'Stage 2 local Python 3.12 framework candidate; native runtime and stdlib only; no developer packages',
          90 * 2**30 + standard_bytes, 2**30 - standard_bytes)
    destination = output / 'lib' / ('python' + version)
    shutil.copytree(standard, destination, dirs_exist_ok=True, ignore=excluded,
                    copy_function=shutil.copyfile)
    entries = []
    for path in sorted(output.rglob('*')):
        if path.is_dir():
            path.chmod(0o755)
        elif path.is_file():
            if path.suffix != '.so' and path.parent.name != 'bin' and path.name != 'Python' and path.suffix != '.dylib':
                path.chmod(0o644)
            entries.append({'path': str(path.relative_to(output)), 'bytes': path.stat().st_size,
                            'sha256': sha256(path)})
    result = {'schemaVersion': 1, 'status': 'ASSEMBLED_NOT_RUNTIME_QUALIFIED',
              'versionFamily': version, 'sitePackagesCopied': False, 'files': entries,
              'excludedFromStdlib': ['__pycache__', 'site-packages', 'test', 'config-*', '*.pyc', '*.pyo',
                                    'sitecustomize.py', 'usercustomize.py', 'sitecustomize', 'usercustomize'],
              'stdlibSourceBytes': standard_bytes,
              'developmentCustomizationHooksCopied': False,
              'libDynloadHandling': 'packaged and relocated separately by native closure builder',
              'externalDistributionApproved': False}
    with (output / 'python-runtime-manifest.json').open('x') as stream:
        json.dump(result, stream, indent=2)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version-root', type=Path, required=True)
    parser.add_argument('--library-root', action='append', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = assemble(args.version_root, args.output.absolute(), args.library_root)
    print(json.dumps({'status': result['status'], 'fileCount': len(result['files']),
                      'bytes': sum(item['bytes'] for item in result['files'])}))


if __name__ == '__main__':
    main()
