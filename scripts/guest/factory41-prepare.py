# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Prepare a new exact-source Factory41 tree; never import warm build outputs."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess


def require(ok, message):
    if not ok:
        raise ValueError(message)


def run(args, cwd=None, capture=True):
    return subprocess.check_output(args, cwd=cwd, text=True, stderr=subprocess.STDOUT) if capture else \
        subprocess.check_call(args, cwd=cwd)


def clean_source(path, row):
    require(path.is_dir() and not path.is_symlink(), 'Unsafe source directory')
    require(run(['git', '-C', str(path), 'rev-parse', 'HEAD']).strip() == row['revision'], 'Wrong source revision')
    require(not run(['git', '-C', str(path), 'status', '--porcelain', '--untracked-files=all']).strip(), 'Dirty source')
    require(run(['git', '-C', str(path), 'remote', 'get-url', 'origin']).strip() == row['url'], 'Wrong source remote')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--source-cache', type=Path, required=True)
    args = parser.parse_args()
    require(re.fullmatch(r'/home/yocto/r61-build/factory41-[a-z0-9-]+', str(args.project)), 'New Factory41 directory required')
    for path in (args.input, args.project, args.source_cache):
        require(not any(p.is_symlink() for p in (path, *path.parents)), 'Linked input/workspace')
    require(run(['uname', '-m']).strip() == 'aarch64', 'ARM64 Builder required')
    require(run(['findmnt', '-n', '-o', 'FSTYPE', '-T', '/home/yocto']).strip() == 'ext4', 'Guest workspace must be ext4')
    require(shutil.disk_usage('/home/yocto').free >= 60 * 2**30, 'Guest free space below 60 GiB')
    lock = json.loads((args.input / 'recipe.json').read_text())
    manifest = args.input / 'factory41.yaml'
    require(hashlib.sha256(manifest.read_bytes()).hexdigest() == lock['renderedManifestSha256'], 'Manifest digest mismatch')
    require(lock['factoryVersion'] == '6.1.1-maninblack.41' and len(lock['sources']) == 9, 'Wrong recipe')
    require(run(['git', '-C', '/home/yocto/r61-work/moulin', 'rev-parse', 'HEAD']).strip()
            == 'cbecc1c748a8c5649e9a319b29167bf27dc4fc3a', 'Wrong Moulin revision')
    require(run(['/home/yocto/.local/pipx/venvs/moulin/bin/python', '-c',
                 'from importlib.metadata import version; print(version("gpt-image"))']).strip() == '0.8.1', 'Wrong Rouge dependency')
    marker = args.project / 'factory-recipe.json'
    if args.project.exists():
        require(marker.is_file() and json.loads(marker.read_text()) == lock, 'Existing directory is not this Factory attempt')
    else:
        args.project.mkdir(mode=0o700)
        marker.write_text(json.dumps(lock, sort_keys=True, indent=2) + '\n')
    source_root = args.project / 'yocto'
    source_root.mkdir(exist_ok=True)
    for row in lock['sources']:
        require(re.fullmatch(r'[a-z0-9-]+', row['name']) and re.fullmatch(r'[0-9a-f]{40}', row['revision']), 'Invalid source pin')
        path = source_root / row['name']
        if not path.exists():
            seed = args.input / 'platform.bundle' if row['name'] == 'aos-vehicle-platform' else args.source_cache / row['name']
            run(['git', 'clone', '--quiet', '--no-hardlinks', '--no-checkout', str(seed), str(path)])
            run(['git', '-C', str(path), 'checkout', '--quiet', '--detach', row['revision']])
            run(['git', '-C', str(path), 'remote', 'set-url', 'origin', row['url']])
        clean_source(path, row)
    os.environ['PATH'] = '/home/yocto/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'
    os.environ['GIT_TERMINAL_PROMPT'] = '0'
    os.environ['GIT_CONFIG_NOSYSTEM'] = '1'
    os.environ['GIT_CONFIG_GLOBAL'] = '/dev/null'
    config = source_root / 'build-main/conf'
    complete = args.project / 'factory-prepared.json'
    if complete.exists():
        record = json.loads(complete.read_text())
        require(all(hashlib.sha256((config / name).read_bytes()).hexdigest() == digest
                    for name, digest in record['configurationSha256'].items()), 'Prepared configuration changed')
        print('FACTORY41_PREPARATION_REUSED')
        return
    require(not (source_root / 'build-main').exists(), 'Partial configuration preserved; inspect before retry')
    run(['moulin', str(manifest), *lock['parameters']], cwd=args.project)
    commands = run(['ninja', '-t', 'commands', 'conf-aos-vm'], cwd=args.project).splitlines()
    # Exact sources above replace only the owner's clone/checkout tasks. Execute
    # the remaining pinned Moulin-generated configuration, not a handwritten conf.
    configuration = [c for c in commands if not (c.startswith('GIT_SSH_COMMAND=') or c.startswith('git -C '))]
    require(len(configuration) == 3 and configuration[0].startswith('bash -c ')
            and configuration[1].startswith('bash -c ') and configuration[2].startswith('cd yocto && '),
            'Moulin configuration graph changed')
    (args.project / '.stamps').mkdir(exist_ok=True)
    for command in configuration:
        run(['bash', '-c', command], cwd=args.project, capture=False)
    require(not (config / 'auto.conf').exists(), 'Warm auto.conf must not be inherited')
    require('6.1.1-maninblack.41' in (config / 'moulin.conf').read_text(), 'Wrong generated version')
    require('r61-build/project/' not in (config / 'bblayers.conf').read_text(), 'Warm layer leaked')
    override = args.project / 'factory41.conf'
    override.write_text('require ' + str(source_root / 'aos-vehicle-platform/qualification/factory-41.conf')
                        + '\nBB_NUMBER_THREADS = "2"\nPARALLEL_MAKE = "-j 4"\n')
    record = {'state': 'CONFIGURED_NOT_BUILT', 'sourceCount': len(lock['sources']),
              'inheritedWarmConfiguration': False, 'reusedDownloadsAndSstate': True,
              'configurationSha256': {name: hashlib.sha256((config / name).read_bytes()).hexdigest()
                                     for name in ('local.conf', 'moulin.conf', 'bblayers.conf')}}
    complete.write_text(json.dumps(record, sort_keys=True, indent=2) + '\n')
    print('FACTORY41_PREPARATION_PASS')


if __name__ == '__main__':
    main()
