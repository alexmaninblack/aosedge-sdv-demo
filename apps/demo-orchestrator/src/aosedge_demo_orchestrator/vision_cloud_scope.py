# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Isolate only the new Vision Test from automatically assigned campaigns."""
from .environment import EnvironmentError
from .cloud_connection import cloud_binding
from .status import object_id
from .vision_bootstrap import PROFILE,VM_PROFILE


def require(ok,code):
    if not ok:raise EnvironmentError('VISION_CLOUD_SCOPE_'+code)


def identity(units,state):
    require(getattr(units.environment.catalog,'cloud_setup_profile',None)==PROFILE
            and state.get('vmProfile')==VM_PROFILE and set(state['vehicles'])=={'test'},'PROFILE_REQUIRED')
    item=state['vehicles']['test']
    require(item.get('cloud',{}).get('identity',{}).get('model')=='aos-vision-vm'
            and item['cloud']['identity']['nodeHardwareId']==item['systemUid'],'NATIVE_IDENTITY_REQUIRED')
    for key in ('unitId','unitSetId','nodeId'):object_id(item[key])
    return item


def collection(units,identity):
    result=units._cloud('inventory',setIds={'observed':identity},includeUnits=False)
    require(len(result['sets'])==1 and result['sets'][0]['id']==identity,'SET_NOT_OBSERVED')
    return result['sets'][0]


def others(value,item):
    return sorted((row['id'],row['system_uid']) for row in value['members'] if row['id']!=item['unitId'])


def confirm(units,state,op):
    item=identity(units,state)
    target=object_id(op['removedSetId']);before=op['setBefore']
    require(target!=item['unitSetId'] and before['id']==target,'TARGET_CHANGED')
    unit=units._cloud('read',unitId=item['unitId'],nodes=False)['unit']
    require(unit and unit['system_uid']==item['systemUid'],'UNIT_CHANGED')
    after=collection(units,target)
    fields=('id','title','fleet','is_validation_set','update_strategy','allow_unknown_components')
    require(all(before.get(k)==after.get(k) for k in fields) and others(before,item)==others(after,item),'FOREIGN_STATE_CHANGED')
    require(target not in unit['unit_sets'] and all(row['id']!=item['unitId'] for row in after['members']),
            'REMOVAL_RECONCILIATION_REQUIRED')
    units._done(state,'test')
    return dict(removedSetId=target,otherMembersPreserved=True,settingsPreserved=True)


def isolate(units,state):
    item=identity(units,state)
    require(len(state['operations'])==1,'PRIOR_OPERATION_REQUIRES_RECONCILIATION')
    unit=units._cloud('read',unitId=item['unitId'],nodes=False)['unit']
    require(unit and unit['system_uid']==item['systemUid'] and unit['status']=='provisioned'
            and unit['fleet']==cloud_binding(state)['fleetId'] and item['unitSetId'] in unit['unit_sets'],'UNIT_CHANGED')
    extra=sorted(set(unit['unit_sets'])-{item['unitSetId']})
    require(len(extra)<=16,'MEMBERSHIP_LIMIT')
    result=[]
    for target in extra:
        before=collection(units,target)
        own=[row for row in before['members'] if row['id']==item['unitId']]
        require(len(own)==1 and own[0]['system_uid']==item['systemUid'],'MEMBERSHIP_CHANGED')
        units._intent(state,'test','VISION_REMOVE_UNREQUESTED_SET')
        op=state['operations'][-1]
        op.update(removedSetId=target,setBefore=before,
                  requestFingerprint='VISION_REMOVE_UNREQUESTED_SET:'+item['localVmId']+':'+target)
        units.vm._save(state)
        # Existing bounded OEM Unit-Set transport. Only this new Unit's UID is
        # removed; no set definition, auto-assignment rule or foreign Unit is changed.
        units._cloud('remove',unitId=item['unitId'],systemUid=item['systemUid'],unitSetId=target)
        result.append(confirm(units,state,op))
    return dict(isolated=True,removed=result,noOp=not extra)
