# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Explicit, instance/Factory-bound Test credential; never a shipped default."""

import re
from .environment import EnvironmentError, JOURNAL, atomic_json, factory_for
from . import runtime_paths

PROFILE = '.local/demo-control/qualification-vm-access.json'
DOMAIN = 'aws-stage.epmp-aos.projects.epam.com'
FIELDS = {'schemaVersion', 'kind', 'instanceId', 'domain', 'factorySha256', 'password'}


def valid_password(value):
    return (isinstance(value, str) and 0 < len(value.encode()) <= 256
            and not any(c in value for c in '\r\n\x00'))


def check_scope(environment, factory_sha):
    from .status import load_configuration, read_json
    root = environment.root
    if not runtime_paths.installed(root):
        raise EnvironmentError('QUALIFICATION_ACCESS_INSTALLED_TEST_REQUIRED')
    config = load_configuration(root)
    if ((config.get('cloudConnection') or {}).get('domain') != DOMAIN
            or config.get('vehicles', {}).get('test', {}).get('cloudHost') != DOMAIN):
        raise EnvironmentError('QUALIFICATION_ACCESS_STAGING_REQUIRED')
    if (root / JOURNAL).exists():
        state = read_json(root / JOURNAL)
        if (set(state.get('vehicles', {})) != {'test'}
                or state.get('selectedCloudDomain') != DOMAIN
                or factory_for(state, 'test').get('sha256') != factory_sha):
            raise EnvironmentError('QUALIFICATION_ACCESS_TEST_FACTORY_MISMATCH')


def password(environment, role, factory_sha=None):
    """None means ordinary first use. Invalid presence must never fall back."""
    path = environment.root / PROFILE
    if path.with_name(path.name + '.pending').exists() or path.with_name(path.name + '.pending').is_symlink():
        raise EnvironmentError('QUALIFICATION_ACCESS_WRITE_UNCONFIRMED')
    if not path.exists() and not path.is_symlink():
        return None
    if role != 'test':
        raise EnvironmentError('QUALIFICATION_ACCESS_TEST_ONLY')
    try:
        value, _ = runtime_paths.small_json(path, limit=4096, owned=True)
        if (not isinstance(value, dict) or set(value) != FIELDS
                or type(value['schemaVersion']) is not int or value['schemaVersion'] != 1
                or value['kind'] != 'democtl.qualification-vm-access'
                or value['instanceId'] != runtime_paths.instance_id()
                or value['domain'] != DOMAIN
                or not isinstance(value['factorySha256'], str)
                or not re.fullmatch('[a-f0-9]{64}', value['factorySha256'])
                or not valid_password(value['password'])):
            raise ValueError()
    except (OSError, ValueError, TypeError, KeyError):
        raise EnvironmentError('QUALIFICATION_ACCESS_PROFILE_INVALID') from None
    if factory_sha is not None and value['factorySha256'] != factory_sha:
        raise EnvironmentError('QUALIFICATION_ACCESS_TEST_FACTORY_MISMATCH')
    # A runtime call without a selected candidate needs the existing VM's
    # authoritative Factory. The pre-Create check supplies the resolved digest.
    if factory_sha is None and not (environment.root / JOURNAL).exists():
        raise EnvironmentError('QUALIFICATION_ACCESS_FACTORY_REQUIRED')
    check_scope(environment, value['factorySha256'])
    return value['password']


def input_password(source):
    try:
        value, _ = runtime_paths.small_json(source, limit=1024, owned=True)
        if not isinstance(value, dict) or set(value) != {'password'} or not valid_password(value['password']):
            raise ValueError()
    except (OSError, ValueError, TypeError):
        raise EnvironmentError('QUALIFICATION_ACCESS_INPUT_REQUIRED') from None
    return value['password']


def prepare(environment, image, source):
    """Explicit test setup from an existing private file, not an HTTP action.

    Read only a bounded JSON object {password: ...}; never return its value.
    The source stays outside the immutable package and qualification evidence.
    """
    with environment._writer():
        candidate = environment.catalog.resolve(image)
        if candidate.problems:
            raise EnvironmentError('DEMO_FACTORY_IMAGE_UNAVAILABLE')
        check_scope(environment, candidate.sha256)
        value = input_password(source)
        path = environment.root / PROFILE
        if path.exists() or path.is_symlink():
            existing = password(environment, 'test', candidate.sha256)
            if existing != value:
                raise EnvironmentError('QUALIFICATION_ACCESS_PROFILE_CONFLICT')
        else:
            runtime_paths.private(path.parent, directory=True)
            atomic_json(path, dict(schemaVersion=1, kind='democtl.qualification-vm-access',
                instanceId=runtime_paths.instance_id(), domain=DOMAIN,
                factorySha256=candidate.sha256, password=value))
        return dict(available=True, mode='EXPLICIT_TEST_PROFILE', nativeInputTested=False)


def preflight(environment, image):
    candidate = environment.catalog.resolve(image)
    if candidate.problems:
        raise EnvironmentError('DEMO_FACTORY_IMAGE_UNAVAILABLE')
    if password(environment, 'test', candidate.sha256) is None:
        raise EnvironmentError('QUALIFICATION_ACCESS_INPUT_REQUIRED')
    return dict(available=True, mode='EXPLICIT_TEST_PROFILE', nativeInputTested=False)
