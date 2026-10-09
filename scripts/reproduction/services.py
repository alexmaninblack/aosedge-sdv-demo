# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Unsigned service exports through pinned Dockerfiles and owner validators."""
import json
from pathlib import Path
import stat

from .core import require, read_json, atomic_json, digest, regular, no_links, GIB
from .artifacts import sha256
from .build import command
from .cloud import inventory
from .containers import Desktop
from .sources import verify_sources, git

TARGETS = {'brake-service': ('functional-service', 'brake', 'BHS', ('v1', 'v2', 'v3')),
           'tire-service': ('tire-health-service', 'tire', 'THS', ('v1',))}


def verify_output(output, inputs):
    receipt = read_json(output / 'build-receipt.json')
    require(receipt.get('status') == 'BUILT_NOT_RUNTIME_QUALIFIED'
            and receipt.get('inputs') == inputs and receipt.get('published') is False
            and receipt.get('signed') is False and receipt.get('liveQualified') is False,
            'Service build receipt differs')
    inventory(output, receipt['files'], ('build-receipt.json',))
    product = read_json(output / 'product-build.json')
    require(product.get('sourceRevision') == inputs['source']['revision']
            and product.get('functionalProfile') == inputs['functionalProfile']
            and product.get('sourceDateEpoch') == inputs['epoch']
            and product.get('kind') == inputs['team'] + '-health-linux-arm64-product'
            and product.get('tests', {}).get('ctest') == 'passed'
            and product.get('liveQualified') is False,
            'Service product receipt differs')
    return receipt


def owner_check(storage, output, checkout, integration, inputs, python):
    """Use owner test and payload checks without starting the runtime controller."""
    checker = Path(__file__).with_name('service_check.py')
    result = json.loads(command([python, '-I', '-B', checker, str(integration), str(checkout),
        str(output), inputs['team'], inputs['functionalProfile'], inputs['source']['revision'], str(inputs['epoch'])],
        storage.environment(), storage.root, timeout=60))
    require(result.get('status') == 'OWNER_PRODUCT_CHECK_PASSED', 'Service owner check failed')
    return result


def assemble(storage, state, target, profile, docker, python, prepare_dependencies, progress):
    require(storage.profile == 'developer' and target in TARGETS, 'Unsupported service build target/profile')
    source, team, prefix, profiles = TARGETS[target]
    require(profile in profiles, 'Select a supported --functional-profile for this service')
    verify_sources(storage, state)
    storage.check(additional=8*GIB, reserve=90*GIB)
    checkout = storage.path('sources/' + source)
    integration = storage.path('sources/integration')
    recipe = regular(checkout / 'Dockerfile')
    env = storage.environment()
    epoch = git(checkout, ['show', '-s', '--format=%ct', 'HEAD'], env)
    require(epoch.isdigit() and int(epoch) > 0, 'Invalid service source timestamp')
    client = Desktop(storage, docker, additional=8*GIB, reserve=90*GIB)
    inputs = {'source': state['sources'][source], 'integration': state['sources']['integration'],
              'recipeSha256': sha256(recipe), 'team': team, 'functionalProfile': profile,
              'epoch': int(epoch), 'platform': 'linux/arm64', 'docker': client.version,
              'buildJobs': 4, 'checkerSha256': sha256(Path(__file__).with_name('service_check.py'))}
    key = digest(inputs)
    output = storage.path('builds/' + target + '/' + key)
    require(',' not in str(output), 'Service export path must not contain Docker output option separators')
    marker = output.parent / (key + '.inputs.json')
    if key in state['builds']:
        require(state['builds'][key] == {'target': target, 'inputs': inputs}, 'Service build key differs')
        verify_output(output, inputs)
        progress('BUILD_REUSED', target + '/' + profile)
        return key
    if output.exists():
        require(marker.exists() and read_json(marker) == inputs, 'Unowned service build collision')
        # Completed export is reconciled; partial output is never silently overwritten.
        require((output / 'product-build.json').is_file(), 'Incomplete service export; inspect before retry')
    else:
        require(prepare_dependencies, 'First service build requires --prepare-dependencies for pinned public inputs')
        output.parent.mkdir(parents=True, exist_ok=True)
        atomic_json(marker, inputs)
        progress('BUILD_STARTED', target + '/' + profile)
        client.run(['buildx', 'build', '--platform', 'linux/arm64', '--pull=false', '--progress', 'plain',
                    '--target', 'export', '--output', 'type=local,dest=' + str(output),
                    '--build-arg', 'SOURCE_REVISION=' + inputs['source']['revision'],
                    '--build-arg', 'SOURCE_DATE_EPOCH=' + epoch,
                    '--build-arg', prefix + '_FUNCTIONAL_PROFILE=' + profile,
                    '--build-arg', 'BUILD_JOBS=4', '--file', recipe, checkout], timeout=1800)
    verify_sources(storage, state)
    if not (output / 'build-receipt.json').exists():
        owner = owner_check(storage, output, checkout, integration, inputs, python)
        rows, total = [], 0
        for path in sorted(output.rglob('*')):
            no_links(path)
            if path.is_dir():
                continue
            info = regular(path).stat()
            total += info.st_size
            require(total <= 256*2**20 and len(rows) < 4098, 'Service export exceeds owner budget')
            rows.append({'path': str(path.relative_to(output)), 'bytes': info.st_size,
                         'mode': stat.S_IMODE(info.st_mode), 'sha256': sha256(path)})
        atomic_json(output / 'build-receipt.json', {'status': 'BUILT_NOT_RUNTIME_QUALIFIED',
            'inputs': inputs, 'files': rows, 'ownerCheck': owner,
            'signed': False, 'published': False, 'liveQualified': False})
    verify_output(output, inputs)
    state['builds'][key] = {'target': target, 'inputs': inputs}
    storage.save(state)
    progress('BUILT_NOT_RUNTIME_QUALIFIED', target + '/' + profile)
    return key
