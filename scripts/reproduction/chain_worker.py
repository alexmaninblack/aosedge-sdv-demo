# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""One pinned owner invocation under the parent command's workspace lock."""
import copy
import importlib
import json
from pathlib import Path
import signal
import sys


def dispatch(storage, state, target, profile, options, progress):
    # Earlier frozen owners intentionally predate later adapters. Import only
    # the selected owner's module, never modules from another source revision.
    modules = {'presenter':'build', 'cloud-sdk':'cloud', 'brake-backend':'containers',
        'tire-backend':'containers', 'backend-export':'containers',
        'brake-service':'services', 'tire-service':'services', 'gateway':'gateway',
        'preparation':'packaging', 'host-runtime':'host', 'backend-inputs':'package_chain',
        'vm-runtime':'package_chain', 'application':'package_chain', 'setup':'media', 'dmg':'media'}
    owner = importlib.import_module('reproduction.'+modules[target])
    python = options['python']
    if target == 'presenter':
        return owner.presenter(storage, state, options['node'], options['npm'], options['prepare_dependencies'], progress)
    if target == 'cloud-sdk':
        return owner.assemble(storage, state, options['kit_inputs'], python, options['prepare_dependencies'], progress)
    if target in ('brake-backend', 'tire-backend'):
        return owner.assemble(storage, state, target, options['docker'], options['prepare_dependencies'], progress)
    if target == 'backend-export':
        return owner.export(storage, state, options['docker'], options['prepare_dependencies'], progress, python)
    if target in ('brake-service', 'tire-service'):
        return owner.assemble(storage, state, target, profile, options['docker'], python,
                                 options['prepare_dependencies'], progress)
    if target == 'gateway':
        return owner.assemble(storage, state, options['gateway_sdk'], options['cmake'], python, progress,
                                 options['test_tmp_parent'], False)
    if target == 'preparation':
        optional = {'factory_inputs': options['factory_inputs']} if options.get('factory_inputs') else {}
        return owner.preparation(storage, state, options['kit_inputs'], python, progress,
                                     options['prepare_dependencies'], **optional)
    if target == 'host-runtime':
        return owner.assemble(storage, state, options['kit_inputs'], options['gateway_sdk'], python, progress)
    if target in ('backend-inputs', 'vm-runtime', 'application'):
        optional = {'input_checkpoint': options['input_checkpoint']} if target != 'backend-inputs' and options.get('input_checkpoint') else {}
        if options.get('developer_results'):
            optional['developer_results'] = True
        return owner.assemble(storage, state, target, options['kit_inputs'], python, progress, **optional)
    if target in ('setup', 'dmg'):
        optional = {name:options[name] for name in ('input_checkpoint','release_checkpoint') if name in options}
        if options.get('developer_results'):
            optional['developer_results'] = True
        return owner.assemble(storage, state, target, python, options['signing_identity'], progress, **optional)
    raise ValueError('Unknown build-only owner target')


def merged_state(original, selected, require, digest):
    require(set(original) == set(selected) and all(selected[k] == original[k]
            for k in ('binding','sources','artifacts')), 'Owner changed non-build state')
    result = copy.deepcopy(original)
    for key, row in selected['builds'].items():
        require(digest(row['inputs']) == key and (key not in original['builds'] or original['builds'][key] == row),
                'Owner replaced an immutable build receipt')
        result['builds'][key] = copy.deepcopy(row)
    return result


def main(path):
    # Unwind an adapter's separately owned compiler groups before its caller
    # removes scratch. A default SIGTERM would orphan those child sessions.
    def cancel(signum, frame):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, cancel)
    signal.signal(signal.SIGINT, cancel)
    request = json.loads(Path(path).read_bytes())
    root = Path(request['producer'])
    sys.path.insert(0, str(root/'scripts'))
    from reproduction.core import Storage, Release, require, digest
    from reproduction.sources import check_source

    class SelectedStorage(Storage):
        def save(self, selected):
            # Keep every prior result, including other candidates/signers. The
            # parent holds the ordinary workspace lock throughout this worker.
            result = merged_state(super().state(), selected, require, digest)
            super().save(result)

    storage = SelectedStorage(Path(request['storage']), Release(), 'developer')
    source = {'repository':request['repository'], 'revision':request['revision']}
    check_source(root, source, storage.environment())
    state = storage.state()
    require(set(request['visible']) <= state['builds'].keys(), 'Selected dependency result missing')
    state['builds'] = {key: state['builds'][key] for key in request['visible']}
    def progress(event, detail):
        print(json.dumps({'event':event, 'detail':detail}), flush=True)
    key = dispatch(storage, state, request['step']['target'], request['step'].get('functionalProfile'),
                   request['options'], progress)
    check_source(root, source, storage.environment())
    print(json.dumps({'status':'OWNER_STEP_COMPLETED', 'buildKey':key}), flush=True)


if __name__ == '__main__':
    try:
        main(sys.argv[1])
    except Exception as exc:
        # Owner subprocess logs may be retained by that owner's bounded logger;
        # do not expose an arbitrary exception or invocation to the terminal.
        error = sys.modules.get('reproduction.core')
        known = error is not None and isinstance(exc, error.LabError)
        print(json.dumps({'status':'OWNER_STEP_FAILED',
            'reason':str(exc) if known else 'Invalid or unavailable owner input',
            'errorType':type(exc).__name__}), flush=True)
        raise SystemExit(1)
