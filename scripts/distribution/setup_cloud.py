# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Native Cloud adapter; explicit enrollment and read-only access checks."""

from pathlib import Path

from installation_inputs import SHA, require, unlinked
from aosedge_demo_orchestrator import runtime_paths, installed_control
from aosedge_demo_orchestrator.cloud_connection import CloudConnection
from aosedge_demo_orchestrator.cloud_setup import CloudSetup
from aosedge_demo_orchestrator.environment import EnvironmentService
from aosedge_demo_orchestrator.units import UnitService
from aosedge_demo_orchestrator.vm import VMService

ENROLLMENT = ('cloud-enrollment-status', 'cloud-enrollment-recover', 'cloud-enrollment-submit')
SUBJECTS = ('cloud-subjects-inspect', 'cloud-subjects-save')
ACTIONS = ('cloud-inspect', 'cloud-save', 'cloud-check', *ENROLLMENT, *SUBJECTS)
LABELS = dict(oem='OEM access', sp='Service Provider access', association='OEM / SP association',
              fleet='Default fleet', architecture='arm64 support', model='Factory model',
              nodeType='Node type', testSet='Test verification set',
              componentDelivery='VDP delivery permissions', serviceDelivery='Brake and Tire delivery permissions',
              tenant='Tenant context')


def request(value):
    action = value.get('action')
    require(action in ACTIONS, 'SETUP_ACTION_INVALID')
    enrollment = action in ENROLLMENT
    keys = {'action', 'state', 'domain', 'role'} if enrollment else {'action', 'state', 'oem', 'sp'}
    if action == 'cloud-enrollment-submit':
        keys |= {'token', 'reconcileAttempt'}
    elif not enrollment and action != 'cloud-inspect':
        keys.add('selectionToken')
    if action == 'cloud-subjects-save':
        keys.add('reference')
    require(set(value) == keys, 'SETUP_REQUEST_INVALID')
    if action == 'cloud-subjects-save':
        from aosedge_demo_orchestrator.status import object_id
        reference = value['reference']
        require(isinstance(reference, dict) and set(reference) == {'team', 'ownerId', 'serviceProviderId', 'id', 'serviceId', 'createdBy'}
                and reference['team'] in ('brake', 'tire'), 'SETUP_REFERENCE_INVALID')
        for key in set(reference) - {'team'}:
            object_id(reference[key])
    for key in (('state',) if enrollment else ('state', 'oem', 'sp')):
        raw = value[key]
        require(isinstance(raw, str) and 1 < len(raw) <= 1024 and raw.startswith('/')
                and not raw.startswith('//') and str(Path(raw)) == raw
                and not any(ord(c) < 32 or c == ',' for c in raw)
                and '..' not in Path(raw).parts, 'SETUP_PATH_INVALID')
        unlinked(raw)
    if enrollment:
        from aosedge_demo_orchestrator.cloud_enrollment import validate
        validate(value['domain'], value['role'])
        if action == 'cloud-enrollment-submit':
            token = value['token']
            require(isinstance(token, str) and 1 <= len(token) <= 4096 and all(33 <= ord(c) <= 126 for c in token), 'SETUP_TOKEN_INVALID')
            if value['reconcileAttempt'] is not None:
                from aosedge_demo_orchestrator.status import object_id
                object_id(value['reconcileAttempt'])
    elif action != 'cloud-inspect':
        require(isinstance(value['selectionToken'], str) and SHA.fullmatch(value['selectionToken']),
                'SETUP_SELECTION_TOKEN_INVALID')
    return value


def perform(value, pin, emit=lambda event: None):
    def progress(stage): emit(dict(kind='progress', stage=stage))
    progress('CLOUD_LOCAL_STATE')
    state, identity = runtime_paths.instance(value['state'])
    selected = installed_control.selection(state, identity)
    require(selected and selected['current'] == pin, 'SETUP_LOCAL_PREPARATION_REQUIRED')
    program = Path(selected['storePath']) / 'versions' / pin / 'aosedge-sdv-demo'
    # Imported sources belong to the installer; consumed SDK/configuration belong
    # to the explicitly selected, leased package. No developer credential fallback.
    progress('CLOUD_PACKAGE_LEASE')
    with runtime_paths.installed_session(state, _program=program):
        if value['action'] in ENROLLMENT:
            from aosedge_demo_orchestrator.cloud_enrollment import run_worker, directory
            action = {'cloud-enrollment-status': 'status', 'cloud-enrollment-recover': 'recover', 'cloud-enrollment-submit': 'enroll'}[value['action']]
            progress('CLOUD_ENROLLMENT_STATE')
            reply = run_worker(state, value['domain'], value['role'], action, value.get('token'), value.get('reconcileAttempt'))
            result = dict(reply, status='CLOUD_ENROLLMENT_OBSERVED', runtimeChanged=False, demoReady=False)
            if reply['enrollmentStage'] == 'RECEIVED':
                result['credentialPath'] = str(directory(state, value['role']) / 'client.p12')
            return result
        if value['action'] in SUBJECTS:
            from aosedge_demo_orchestrator.subject_first_use import FirstUseSubjects
            progress('CLOUD_SUBJECTS_CHECK')
            env = EnvironmentService(root=state)
            return FirstUseSubjects(UnitService(VMService(environment=env))).perform(
                value['oem'], value['sp'], value['selectionToken'], value.get('reference'))
        progress('CLOUD_CONFIGURATION_LOCK')
        env = EnvironmentService(root=state)
        connection = CloudConnection(env)
        with env._writer():
            progress('CLOUD_PAIR_CHECK')
            oem, sp = value['oem'], value['sp']
            metadata = connection.inspect_pair(oem, sp)
            result = dict(runtimeChanged=False, cloudAccessed=False, demoReady=False, **metadata)
            action = value['action']
            if action == 'cloud-inspect':
                return dict(result, status='CERTIFICATE_PAIR_INSPECTED')
            require(metadata['selectionToken'] == value['selectionToken'],
                    'CLOUD_CERTIFICATE_CHANGED_SINCE_PREVIEW')
            if action == 'cloud-save':
                progress('CLOUD_REFERENCE_WRITE')
                return dict(result, **{'status': 'CLOUD_REFERENCES_SAVED',
                                      'selectionToken': connection.select_pair(oem, sp, value['selectionToken'])['selectionToken']})
            config = connection._configuration()
            profiles = config.get('cloudProfiles', {})
            require(profiles.get('oem-delivery', {}).get('credential') == oem
                    and profiles.get('service-provider', {}).get('credential') == sp
                    and config.get('cloudConnection', {}).get('domain') == metadata['domain'],
                    'SETUP_SAVE_PAIR_FIRST')
            progress('CLOUD_ACCESS_CHECK')
            report = CloudSetup(UnitService(VMService(environment=env))).check(first_use=True)
            require(connection._pair_stamp(oem, sp) == value['selectionToken'],
                    'CLOUD_CERTIFICATE_CHANGED_SINCE_PREVIEW')
            require(report.get('domain') == metadata['domain']
                    and report.get('stage') in ('READY', 'MISSING', 'BLOCKED'), 'SETUP_CLOUD_REPORT_INVALID')
            checks = []
            for row in report['checks']:
                require(row['key'] in LABELS and row['state'] in ('READY', 'MISSING', 'BLOCKED', 'CONFLICT', 'AFTER_PROVISION'),
                        'SETUP_CLOUD_REPORT_INVALID')
                checks.append(dict(label=LABELS[row['key']], state=row['state']))
            require(len(checks) <= len(LABELS), 'SETUP_CLOUD_REPORT_INVALID')
            # Project only fixed labels/states, not raw errors, paths or Cloud objects.
            authenticated = {row['key'] for row in report['checks'] if row['state'] == 'READY'}
            result.update(status='CLOUD_ACCESS_OBSERVED', cloudAccessed=True,
                          rolesChecked={'oem', 'sp'} <= authenticated,
                          cloudStage=report['stage'], checks=checks)
            return result
