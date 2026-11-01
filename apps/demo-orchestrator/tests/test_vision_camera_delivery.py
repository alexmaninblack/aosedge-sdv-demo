# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
from copy import deepcopy
import unittest
from unittest.mock import Mock,patch
from aosedge_demo_orchestrator import vision_camera_delivery as v
from aosedge_demo_orchestrator.unit_cloud import CloudFailure

UNIT='11111111-1111-4111-8111-111111111111'
SET='22222222-2222-4222-8222-222222222222'
NODE='33333333-3333-4333-8333-333333333333'
FLEET='44444444-4444-4444-8444-444444444444'
REQUEST=dict(setupProfile=v.PROFILE,version=v.VERSION,vehicles={'test':dict(unitId=UNIT,nodeId=NODE,nodeHardwareId='vision-native',systemUid='vision-native',unitSetId=SET)})


class ScopeTests(unittest.TestCase):
    def setUp(self):
        self.unit=dict(id=UNIT,system_uid='vision-native',status='provisioned',online_status='Online',
                       unit_sets=[SET],fleet=FLEET,nodes=[dict(id=NODE,node_id='vision-native',node_type=v.NODE_TYPE,is_main=True)])
        self.selected=dict(title=v.SET_TITLE,is_validation_set=True,allow_unknown_components=False,fleet=FLEET)
        self.members=[dict(id=UNIT,system_uid='vision-native')]
        self.cloud=Mock()
        self.cloud.unit.side_effect=lambda *a,**kw:deepcopy(self.unit)
        self.cloud.call.side_effect=lambda path:deepcopy(self.selected)
        self.cloud.pages.side_effect=lambda path:deepcopy(self.members)

    def test_only_native_vision_unit_and_own_verification_set_are_accepted(self):
        self.assertEqual(REQUEST['vehicles']['test'],v.scope(self.cloud,REQUEST))
        self.cloud.call.assert_called_once_with('unit-sets/'+SET+'/')

    def test_main_node_or_changed_unit_identity_blocks(self):
        for key,value in (('system_uid','main'),('online_status','Offline'),('unit_sets',[SET,FLEET])):
            prior=self.unit[key];self.unit[key]=value
            with self.assertRaises(CloudFailure):v.scope(self.cloud,REQUEST)
            self.unit[key]=prior
        self.unit['nodes'][0]['node_type']='aos-vm-main'
        with self.assertRaisesRegex(CloudFailure,'NODE_BINDING_CHANGED'):v.scope(self.cloud,REQUEST)

    def test_main_set_foreign_member_or_permissive_set_blocks(self):
        for key,value in (('title','Test Vehicles'),('is_validation_set',False),('allow_unknown_components',True)):
            old=self.selected[key];self.selected[key]=value
            with self.assertRaisesRegex(CloudFailure,'SET_BINDING_CHANGED'):v.scope(self.cloud,REQUEST)
            self.selected[key]=old
        self.members.append(dict(id=FLEET,system_uid='foreign'))
        with self.assertRaisesRegex(CloudFailure,'FOREIGN_RECIPIENT'):v.scope(self.cloud,REQUEST)

    def test_wrong_version_profile_or_production_role_blocks(self):
        for request in (dict(REQUEST,setupProfile='main'),dict(REQUEST,version='2.0.0'),
                        dict(REQUEST,vehicles={'production':REQUEST['vehicles']['test']})):
            with self.assertRaises(CloudFailure):v.scope(self.cloud,request)

    def test_nullable_cloud_main_flag_still_requires_exact_native_hardware_identity(self):
        self.unit['nodes'][0]['is_main']=None
        v.scope(self.cloud,REQUEST)
        self.unit['nodes'][0]['node_id']='foreign'
        with self.assertRaisesRegex(CloudFailure,'NODE_BINDING_CHANGED'):v.scope(self.cloud,REQUEST)
        self.unit['nodes'][0]['node_id']='vision-native';self.unit['nodes'][0]['is_main']=False
        with self.assertRaisesRegex(CloudFailure,'NODE_BINDING_CHANGED'):v.scope(self.cloud,REQUEST)

    def test_status_is_the_existing_publication_reader_with_fixed_camera_identity(self):
        with patch.object(v,'snapshot',return_value={'observed':True}) as read:
            self.assertEqual({'observed':True},v.execute(self.cloud,dict(REQUEST,action='vision-camera-status')))
        self.assertEqual(v.COMPONENT,read.call_args.kwargs['component_type'])

    def test_exact_automatic_verification_delivery_is_observed_without_second_post(self):
        request=dict(REQUEST,action='vision-camera-send',updateComponentId=FLEET)
        with patch.object(v,'scope',return_value=REQUEST['vehicles']['test']), \
             patch.object(v,'snapshot',return_value={'publication':dict(stage='READY',versionId=FLEET)}), \
             patch.object(v,'unit_view',return_value={'components':[dict(pending_component=dict(id=FLEET))]}):
            self.cloud.call.side_effect=lambda path:[]
            observed=v.execute(self.cloud,request)
        self.assertTrue(observed['noOp']);self.assertFalse(observed['requestAccepted'])
        self.assertEqual('pending_component',observed['deliveryObserved'])
        self.assertTrue(all(len(c.args)==1 and not c.kwargs for c in self.cloud.call.call_args_list))


if __name__=='__main__':unittest.main()
