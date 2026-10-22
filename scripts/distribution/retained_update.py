# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Read-only exact-Test upgrade proof, held across atomic package selection."""
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
import os
import re

from installation_inputs import CATALOGUE, parse, read_small, require
from aosedge_demo_orchestrator import installed_control as control, runtime_paths


def descriptor(bundle, group):
    manifest = parse(read_small(bundle.root / 'application-manifest.json', 2**20))
    return parse(read_small(bundle.root / CATALOGUE / group / manifest['inputs'][group]['path']))


def compatibility(before, after):
    """No schema migration, Factory replacement, backend activation or VM change."""
    old, new = (descriptor(b, 'preparation-inputs') for b in (before, after))
    for name in ('factory', 'vdpProfiles', 'runtimePin', 'serviceProfiles'):
        require(name in old and old[name] == new.get(name), 'UPDATE_PREPARATION_INCOMPATIBLE')
    old, new = (descriptor(b, 'host-runtime') for b in (before, after))
    require(old.get('simulator') is not None and old['simulator'] == new.get('simulator'),
            'UPDATE_SIMULATOR_INCOMPATIBLE')
    old, new = (descriptor(b, 'vm-runtime') for b in (before, after))
    require(old.get('files') and old['files'] == new.get('files'), 'UPDATE_VM_RUNTIME_INCOMPATIBLE')
    require(descriptor(before, 'cloud-runtime') == descriptor(after, 'cloud-runtime'),
            'UPDATE_CLOUD_RUNTIME_INCOMPATIBLE')


def state_stamp(root):
    """Identity proof, not repeated multi-GB VM hashing; never persist state bytes."""
    result = {}
    for parent, directories, files in os.walk(root, followlinks=False):
        for name in [*directories, *files]:
            path = runtime_paths.canonical(Path(parent) / name)
            relative = path.relative_to(root).as_posix()
            if relative in ('installation.json', 'installation.json.pending'):
                continue
            require(not path.name.endswith('.pending'), 'UPDATE_STATE_PENDING')
            st = path.lstat()
            result[relative] = (st.st_dev, st.st_ino, st.st_mode, st.st_size,
                                st.st_mtime_ns, st.st_ctime_ns, st.st_nlink)
            require(len(result) <= 50000, 'UPDATE_STATE_INVENTORY_TOO_LARGE')
    return result


def publication_idle(state):
    """A replied upload is terminal locally, not a claim of Cloud readiness."""
    from uuid import UUID
    from aosedge_demo_orchestrator.service_assignment import retirement_subjects
    retirement_subjects(state)  # Validate the existing assignment receipts only.
    for row in state.get('componentOperations', {}).values():
        require(isinstance(row, dict), 'UPDATE_PUBLICATION_UNRESOLVED')
        for action in ('upload', 'approve', 'unapprove', 'send'):
            value = row.get(action) or {}
            if not value.get('attemptStarted'):
                continue
            if value.get('state') == 'CONFIRMED':
                continue
            response, publication = value.get('response') or {}, row.get('publication') or {}
            require(action == 'upload' and value.get('state') == 'RESPONDED'
                    and response.get('httpStatus') == 201 and isinstance(row.get('deploymentId'), str)
                    and str(UUID(row['deploymentId'])) == row['deploymentId']
                    and response.get('deploymentId') == row['deploymentId']
                    and publication.get('deploymentId') == row['deploymentId']
                    and publication.get('stage') in ('ACCEPTED', 'READY')
                    and row.get('target') == 'test' and row.get('publicationPath') == 'VERIFICATION_TEST'
                    and row.get('cloudDomain') == state.get('selectedCloudDomain'),
                    'UPDATE_PUBLICATION_UNRESOLVED')


def test_state(root):
    from aosedge_demo_orchestrator.environment import JOURNAL
    from aosedge_demo_orchestrator.test_environment import _state
    from aosedge_demo_orchestrator.status import load_configuration
    runtime_paths.private(root / '.run/demo-current', directory=True)
    pending = root / (JOURNAL + '.pending')
    require(not pending.exists() and not pending.is_symlink(), 'UPDATE_JOURNAL_PENDING')
    env = SimpleNamespace(root=root, _owned_file=runtime_paths.private)
    state = _state(env)
    require(set(state['vehicles']) == {'test'} and state['stage'] in ('MANUFACTURED', 'LOCAL_STOPPED')
            and state.get('currentVehicle') is None, 'UPDATE_STOPPED_TEST_REQUIRED')
    require(len(state['operations']) == 1 and not state.get('testRetirement'),
            'UPDATE_OPERATION_UNRESOLVED')
    publication_idle(state)
    for name in ('demoLifecycle', 'demoPreparation'):
        value = state.get(name)
        require(not value or value.get('state') == 'COMPLETED', 'UPDATE_OPERATION_UNRESOLVED')
    source = state.get('source') or {}
    require(not source or source.get('state') == 'STOPPED' and not source.get('operation')
            and not source.get('stopOperation'), 'UPDATE_SOURCE_NOT_STOPPED')
    require(all(v.get('state') == 'STOPPED' for v in state.get('backends', {}).values()),
            'UPDATE_BACKENDS_NOT_STOPPED')
    vehicle = state['vehicles']['test']
    require(vehicle.get('runtime', {}).get('state') == 'STOPPED', 'UPDATE_VM_NOT_STOPPED')
    runtime_paths.private(root / vehicle['overlay'])
    # Reuse the normal schema/domain reader; no configuration or Cloud writes.
    configured = load_configuration(root)
    require(configured['journal']['state'] == 'CURRENT', 'UPDATE_JOURNAL_NOT_CURRENT')
    return state


def local_idle(root, store, state):
    from aosedge_demo_orchestrator.probes import process_snapshot, owns_overlay
    from setup_backends import Docker
    from installation_inputs import parse
    control.unused((root, store))
    processes = process_snapshot(5)
    require(processes is not None and not any(owns_overlay(args, root / state['vehicles']['test']['overlay'])
            for _, args in processes), 'UPDATE_VM_PROCESS_PRESENT_OR_UNKNOWN')
    docker = Docker()
    engine = docker.engine()
    owner = state['operations'][0]['id']
    ids = docker.read('container', 'ls', '--quiet', '--no-trunc').split()
    require(len(ids) <= 64 and all(re.fullmatch('[a-f0-9]{64}', x) for x in ids),
            'UPDATE_CONTAINER_OBSERVATION_INVALID')
    if ids:
        rows = parse(docker.read('container', 'inspect', *ids).encode())
        require(isinstance(rows, list) and len(rows) == len(ids), 'UPDATE_CONTAINER_OBSERVATION_INVALID')
        for row in rows:
            require(isinstance(row, dict) and row.get('Id') in ids, 'UPDATE_CONTAINER_OBSERVATION_INVALID')
            labels = (row.get('Config') or {}).get('Labels') or {}
            require(labels.get('tech.aosedge.demo.owner') != owner
                    and row.get('Name') not in ('/aosedge-demo-brake-cloud', '/aosedge-demo-tire-cloud'),
                    'UPDATE_BACKEND_CONTAINER_ACTIVE')
            for mount in row.get('Mounts', []):
                source = mount.get('Source')
                if isinstance(source, str):
                    path = Path(source)
                    require(not any(path == p or path.is_relative_to(p) for p in (root, store)),
                            'UPDATE_CONTAINER_HOLDS_DATA')
    require(docker.engine() == engine, 'UPDATE_DOCKER_ENGINE_CHANGED')


@contextmanager
def proof(root, store, before, after):
    """Caller holds store writer and exclusive instance selection lease."""
    with control.lease(root / '.run/demo-current/writer.lock', exclusive=True, create=False):
        compatibility(before, after)
        state = test_state(root)
        local_idle(root, store, state)
        stamp = state_stamp(root)
        yield dict(testPreserved=True, userDataChanged=False, migrationPerformed=False)
        require(state_stamp(root) == stamp, 'UPDATE_STATE_CHANGED')
