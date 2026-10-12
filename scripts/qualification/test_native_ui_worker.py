# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch
import native_ui_worker as n


class NativePilotGuards(unittest.TestCase):
    def pilot(self):
        return n.Pilot(Path('/unused'),{'apps':[{'executable':'ControlFixture','sha256':'a'*64}]})

    def test_blocked_inspection_cannot_pass(self):
        p=self.pilot()
        with patch.object(p,'request',return_value=({},dict(outcome='BLOCKED',code='UI_ELEMENT_MISSING'))):
            with self.assertRaisesRegex(ValueError,'UI_INSPECTION_UNCONFIRMED'):
                p.stage('semantic-elements',p.inspect)
        self.assertEqual(p.stages[0]['outcome'],'FAIL')

    def test_inspection_requires_all_unique_semantic_ids(self):
        p=self.pilot()
        rows=[{'id':id,'enabled':True,'frame':[1,2,3,4]} for id in n.ACTIONS]
        with patch.object(p,'request',return_value=({},dict(outcome='PASS',code='UI_CONTRACT_OBSERVED',buttons=rows))):
            self.assertEqual(len(p.inspect()['buttons']),5)
            rows[-1]['id']=rows[0]['id']
            with self.assertRaisesRegex(ValueError,'UI_SEMANTIC_CONTRACT_MISMATCH'):p.inspect()

    def test_mouse_submission_alone_does_not_prove_effect(self):
        p=self.pilot()
        receipt=dict(outcome='INPUT_DISPATCHED',inputDispatched=True)
        with patch.object(p,'request',return_value=({},receipt)),patch.object(p,'events',return_value=[]),\
                patch.object(n,'wait',side_effect=ValueError('MOUSE_EFFECT_UNCONFIRMED')):
            with self.assertRaisesRegex(ValueError,'MOUSE_EFFECT_UNCONFIRMED'):p.click(n.ACTIONS[0])

    def test_negative_requires_no_input_and_no_callback(self):
        p=self.pilot()
        receipt=dict(outcome='BLOCKED',code='UI_ELEMENT_DISABLED',inputDispatched=False)
        with patch.object(p,'request',return_value=({},receipt)),patch.object(p,'events',side_effect=[[],[{'action':'bad'}]]):
            with self.assertRaisesRegex(ValueError,'NEGATIVE_EMITTED_ACTION'):
                p.negative('click','UI_ELEMENT_DISABLED',action=n.ACTIONS[0])

    def test_existing_report_is_never_overwritten_or_replayed(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);report=root/'pilot-report.json'
            report.write_text('{"outcome":"PASS"}')
            with patch.object(n,'verify',return_value={}),patch.object(n,'Pilot') as pilot,patch('builtins.print'):
                self.assertEqual(n.main(root),2)
                pilot.assert_not_called()
            self.assertEqual(report.read_text(),'{"outcome":"PASS"}')

    def test_invalid_root_has_no_report_write(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            with patch.object(n,'verify',side_effect=ValueError('PILOT_ROOT_INVALID')),patch('builtins.print'):
                self.assertEqual(n.main(root),2)
            self.assertEqual(list(root.iterdir()),[])


if __name__=='__main__':unittest.main()
