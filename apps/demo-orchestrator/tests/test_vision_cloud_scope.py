# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
from copy import deepcopy
from types import SimpleNamespace
import unittest
from unittest.mock import Mock
from aosedge_demo_orchestrator import vision_cloud_scope as v
from aosedge_demo_orchestrator.environment import EnvironmentError

UNIT='11111111-1111-4111-8111-111111111111'
TEST='22222222-2222-4222-8222-222222222222'
EXTRA='33333333-3333-4333-8333-333333333333'
NODE='44444444-4444-4444-8444-444444444444'
FOREIGN='55555555-5555-4555-8555-555555555555'


class IsolationTests(unittest.TestCase):
    def setUp(self):
        self.item=dict(unitId=UNIT,unitSetId=TEST,nodeId=NODE,localVmId=UNIT,systemUid='vision',
                       cloud=dict(identity=dict(model='aos-vision-vm',nodeHardwareId='vision')))
        self.state=dict(vmProfile=v.VM_PROFILE,vehicles={'test':self.item},operations=[{'class':'LOCAL_CREATE'}],
                        cloudBinding=dict(ownerId=FOREIGN,fleetId=NODE))
        self.unit=dict(id=UNIT,system_uid='vision',status='provisioned',fleet=NODE,unit_sets=[TEST,EXTRA])
        self.group=dict(id=EXTRA,title='Unrelated automatic campaign',fleet=NODE,is_validation_set=False,
                        members=[dict(id=UNIT,system_uid='vision'),dict(id=FOREIGN,system_uid='retained')])
        self.calls=[];self.lose=False
        def cloud(action,**kw):
            self.calls.append((action,deepcopy(kw)))
            if action=='read':return dict(unit=deepcopy(self.unit))
            if action=='inventory':return dict(sets=[deepcopy(self.group)])
            if action=='remove':
                self.assertEqual(dict(unitId=UNIT,systemUid='vision',unitSetId=EXTRA),kw)
                self.unit['unit_sets'].remove(EXTRA)
                self.group['members']=[v for v in self.group['members'] if v['id']!=UNIT]
                if self.lose:raise TimeoutError('response lost')
                return {}
            raise AssertionError(action)
        def intent(state,role,step):state['operations'].append(dict(step=step))
        def done(state,role):state['operations']=state['operations'][:1]
        self.units=SimpleNamespace(environment=SimpleNamespace(catalog=SimpleNamespace(cloud_setup_profile=v.PROFILE)),
            _cloud=cloud,_intent=intent,_done=done,vm=Mock())

    def test_remove_only_this_new_unit_preserves_other_member_and_repeat_is_read_only(self):
        before=deepcopy(self.group)
        result=v.isolate(self.units,self.state)
        self.assertTrue(result['isolated']);self.assertEqual([TEST],self.unit['unit_sets'])
        self.assertEqual([dict(id=FOREIGN,system_uid='retained')],self.group['members'])
        self.assertEqual(before['title'],self.group['title'])
        self.assertTrue(v.isolate(self.units,self.state)['noOp'])
        self.assertEqual(1,sum(action=='remove' for action,_ in self.calls))

    def test_lost_response_reconciles_by_read_without_replaying_remove(self):
        self.lose=True
        with self.assertRaises(TimeoutError):v.isolate(self.units,self.state)
        self.assertEqual(2,len(self.state['operations']))
        v.confirm(self.units,self.state,self.state['operations'][-1])
        self.assertEqual(1,len(self.state['operations']))
        self.assertEqual(1,sum(action=='remove' for action,_ in self.calls))

    def test_main_or_unknown_native_identity_cannot_be_adopted(self):
        self.state['vmProfile']='aos-main-qemuarm64-v1'
        with self.assertRaisesRegex(EnvironmentError,'PROFILE_REQUIRED'):v.isolate(self.units,self.state)
        self.assertFalse(self.calls)

    def test_foreign_member_change_is_not_hidden_as_success(self):
        self.lose=True
        with self.assertRaises(TimeoutError):v.isolate(self.units,self.state)
        self.group['members']=[]
        with self.assertRaisesRegex(EnvironmentError,'FOREIGN_STATE_CHANGED'):
            v.confirm(self.units,self.state,self.state['operations'][-1])


if __name__=='__main__':unittest.main()
