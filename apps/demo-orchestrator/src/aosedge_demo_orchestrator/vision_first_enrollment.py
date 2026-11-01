# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Closed fresh-Vision recovery; no VM, Cloud or component lifecycle replacement."""
import copy
import re

from .environment import EnvironmentError
from .status import now

PROFILE='aos-vision-main-qemuarm64-v1'


def pending(state):
    source=state.get('source') or {};trust=source.get('trust') or {}
    item=state.get('vehicles',{}).get('test') or {};record=trust.get('onboarding') or {}
    fingerprints=trust.get('fingerprints') or {}
    return (state.get('vmProfile')==PROFILE and set(state.get('vehicles',{}))=={'test'}
        and state.get('currentVehicle') is None and trust.get('enabled') is True
        and trust.get('profile')=='SELECTED_UNIT_MUTUAL_TLS' and trust.get('target')=='test'
        and not trust.get('pending') and record.get('state')=='PENDING'
        and bool(item.get('unitId')) and bool(item.get('nodeId'))
        and record.get('unitId')==item['unitId'] and record.get('nodeId')==item['nodeId']
        and (item.get('cloud') or {}).get('identity',{}).get('model')=='aos-vision-vm'
        and set(fingerprints)=={'dashboard','vdp','runtime'}
        and all(isinstance(v,str) and re.fullmatch('[a-f0-9]{64}',v) for v in fingerprints.values())
        and type(source.get('assignmentGeneration')) is int and source['assignmentGeneration']>=0)


def deferred_boot(state):
    """Boot the same pending Unit without pretending guest enrollment exists.

    The ordinary guest projection later proves empty/matching native state.
    No source_restore, credential write or component mutation is done at boot.
    """
    source=state.get('source') or {}
    return (pending(state) and source.get('state')=='STOPPED'
        and not source.get('operation') and not source.get('stopOperation'))


def cancel(service,state):
    """Cancel only a known fresh connection, proving live hold or actor absence."""
    if not pending(state):return None
    source=state['source'];operation=source.get('operation') or {}
    if (operation.get('initialManual') is not True or operation.get('target')!='test'
            or operation.get('previous') is not None or operation.get('phase') not in
            ('SAFE_STOP_REQUESTED','DETACHED','RESET_CONFIRMED')):
        return None
    driver=service.driver
    runner=driver.live_process(source['runnerCommand']);simulator=driver.live_process(source['simulatorCommand'])
    if bool(runner)!=bool(simulator):
        raise EnvironmentError('VISION_SOURCE_INITIAL_CANCEL_OWNER_INCOMPLETE')
    evidence='SIMULATOR_TERMINATED_NO_LIVE_ACTOR'
    if runner:
        frame=driver.rpc(source,'status',operation['id']);actual=frame.get('frame') or {}
        if (frame.get('operationId')!=operation['id'] or not frame.get('fresh') or not frame.get('held')
                or frame.get('phase') not in ('SAFE_STOP','MANUAL_READY')
                or actual.get('activeMode')!=('SAFE_STOP' if frame['phase']=='SAFE_STOP' else 'MANUAL')
                or actual.get('speedKmh',float('inf'))>.5 or actual.get('brake',0)<.99):
            raise EnvironmentError('VISION_SOURCE_INITIAL_CANCEL_HOLD_UNCONFIRMED')
        evidence='HELD_STATIONARY_ACTOR_TERMINATED'
    views=service._detach(state,'test',stopping=not bool(runner))
    if any(v.get('gate')!='BLOCKED' for v in views.values()):
        raise EnvironmentError('SOURCE_DETACH_NOT_CONFIRMED')
    # Existing owner performs native Quit/runner shutdown. Preserve the intent
    # until all children/listeners have actually gone; no synthetic Safe Stop.
    driver.stop(source)
    if any(driver.live_process(source[k]) for k in ('runnerCommand','simulatorCommand')):
        raise EnvironmentError('VISION_SOURCE_INITIAL_CANCEL_OWNER_REMAINS')
    source['initializationCancellation']=dict(operation=copy.deepcopy(operation),
        unitId=state['vehicles']['test']['unitId'],nodeId=state['vehicles']['test']['nodeId'],
        evidence=evidence,confirmedAt=now(),safeStopClaim=False)
    source.update(state='STOPPED',stoppedAt=now(),operation=None)
    source.pop('stopOperation',None);source.pop('lastConnectionConfirmation',None)
    service.vm._save(state)
    return dict(state='STOPPED',currentVehicle=None,initializationCancelled=True,
        physicalStop='SIMULATOR_TERMINATED',safeStopClaim=False)
