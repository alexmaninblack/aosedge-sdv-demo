# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
import native_ui_live as n
from journey_worker import Worker

ID='01234567-89ab-cdef-0123-456789abcdef'


class LiveGuards(unittest.TestCase):
    def test_exercise_observation_reads_bound_owner_without_control_rpc(self):
        worker=Worker.__new__(Worker)
        worker.args={'query':'exercise'}
        worker.binding=Mock(return_value={'source':{'runId':'source',
            'exercise':{'id':ID,'kind':'brake','runId':'source','phase':'RELEASED',
            'result':{'state':'COMPLETED','operationId':ID,'physicalStop':'CONFIRMED','noOp':False}}}})
        result=worker.observe()
        self.assertTrue(result['runMatches']);self.assertTrue(result['operationMatches'])
        self.assertEqual(result['state'],'COMPLETED');worker.binding.assert_called_once()
    def client(self, root):
        client=n.Live.__new__(n.Live)
        client.transport={};client.config={'manifestSha256':'a'*64};client.test=ID
        client.records=Path(root);client.stages=set();client.scenario='native-controls'
        client.profile=dict(candidate='a'*64,test=ID,sessionId=ID,pid=123,
            executable='/exact/KeyboardControl',executableSha256='b'*64,scenario='native-controls')
        client.launch=Mock();client.request=Mock(return_value=dict(requestId=ID,
            outcome='INPUT_DISPATCHED',inputDispatched=True,code='MOUSE_DOWN_UP_POSTED',
            action='driving.safe-stop',binding=dict(candidate='a'*64,test=ID,sessionId=ID,
                stage='native-controls-safe-stop')))
        return client

    def gate(self, **changes):
        return dict(dict(schemaVersion=1,stage='native-controls-safe-stop',action='Safe Stop',
                    test=ID,sessionId=ID,state='WAITING_FOR_UI_CLICK'),**changes)

    def test_input_is_once_and_physical_effect_is_not_fabricated(self):
        with tempfile.TemporaryDirectory() as root:
            client=self.client(root)
            with patch.object(n,'target',return_value=client.profile) as target:
                receipt=client(self.gate())
                self.assertEqual(receipt['state'],'INPUT_DISPATCHED_THROUGH_NATIVE_RUNNER')
                self.assertNotIn('PASS',receipt.values())
                client.request.assert_called_once_with('click','native-controls-safe-stop','driving.safe-stop')
                with self.assertRaises(ValueError):client(self.gate())
                self.assertEqual(target.call_count,1)

    def test_changed_owner_or_unknown_stage_refuses_before_input(self):
        with tempfile.TemporaryDirectory() as root:
            for field,value in [('pid',124),('executableSha256','c'*64),('sessionId','other'),('candidate','c'*64)]:
                client=self.client(root)
                with patch.object(n,'target',return_value=dict(client.profile,**{field:value})):
                    with self.assertRaises(ValueError):client(self.gate())
                client.request.assert_not_called()
            for gate in [self.gate(stage='generic-stop'),self.gate(action='Tire maneuver'),
                         self.gate(test='11234567-89ab-cdef-0123-456789abcdef'),self.gate(schemaVersion=True)]:
                client=self.client(root)
                with patch.object(n,'target') as target:
                    with self.assertRaises(ValueError):client(gate)
                    target.assert_not_called();client.request.assert_not_called()

    def test_control_profile_cannot_execute_campaign_stage(self):
        with tempfile.TemporaryDirectory() as root:
            client=self.client(root)
            with patch.object(n,'target') as target:
                with self.assertRaises(ValueError):client(self.gate(stage='vdp-v1-safe'))
                target.assert_not_called();client.request.assert_not_called()

    def test_campaign_profile_can_only_use_its_explicit_fixed_stages(self):
        with tempfile.TemporaryDirectory() as root:
            client=self.client(root);client.scenario='continuous-campaign'
            client.profile['scenario']='continuous-campaign'
            receipt=client.request.return_value
            receipt['binding']['stage']='vdp-v1-safe'
            with patch.object(n,'target',return_value=client.profile):
                self.assertEqual(client(self.gate(stage='vdp-v1-safe'))['state'],'INPUT_DISPATCHED_THROUGH_NATIVE_RUNNER')
            client=self.client(root);client.scenario='continuous-campaign'
            with patch.object(n,'target') as target:
                with self.assertRaises(ValueError):client(self.gate())
                target.assert_not_called();client.request.assert_not_called()

    def test_python_and_swift_fixed_stage_maps_agree(self):
        import re
        from ui_native_gate import LIVE_STAGES,ACTION_IDS,SCENARIO_STAGES
        text=(Path(n.__file__).parent/'native/NativeUIRunner.swift').read_text()
        block=text.split('let controlStages =',1)[1].split('let liveStages =',1)[0]
        rows=dict(re.findall(r'"([a-z0-9-]+)"\s*:\s*"(driving\.[a-z-]+)"',block))
        self.assertEqual(rows,{k:ACTION_IDS[v] for k,v in LIVE_STAGES.items()})
        self.assertFalse(set(SCENARIO_STAGES['native-controls']) & set(SCENARIO_STAGES['continuous-campaign']))


if __name__=='__main__':unittest.main()
