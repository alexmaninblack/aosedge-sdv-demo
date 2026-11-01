# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
import contextlib
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock,patch

from aosedge_demo_orchestrator import source,source_authentication as auth


class IngressSourceTests(unittest.TestCase):
    def setUp(self):
        self.state=dict(vmProfile='aos-vision-main-qemuarm64-v1',currentVehicle='test',
            vehicles=dict(test=dict(unitId='unit',nodeId='node')),
            source=dict(state='RUNNING',runId='source',assignmentGeneration=7,operation=None,
                trust=dict(enabled=True,fingerprints=dict(vdp='fixture-only',runtime='fixture-only'))))
        self.service=source.SourceService.__new__(source.SourceService)
        self.service.root=Path('/unit')
        self.service.environment=SimpleNamespace(_writer=contextlib.nullcontext)
        self.service.driver=Mock();self.service.driver.operation=contextlib.nullcontext

    def run_action(self,action):
        with patch.object(source,'read_json',return_value=self.state):return self.service.camera_ingress(action)

    def test_main_profile_and_unselected_source_do_not_start_or_read_credentials(self):
        self.state['vmProfile']='aos-main-qemuarm64-v1'
        with self.assertRaisesRegex(ValueError,'PROFILE_REQUIRED'):self.run_action('start')
        self.state['vmProfile']='aos-vision-main-qemuarm64-v1';self.state['currentVehicle']=None
        with self.assertRaisesRegex(ValueError,'SELECTION_REQUIRED'):self.run_action('start')
        self.service.driver.guest.assert_not_called()

    def test_current_selected_generation_is_required_before_start(self):
        selection=auth.selection(self.state)
        with patch.object(auth,'observe',return_value=dict(state='SELECTED',selectedSource=selection,assignmentGeneration=8)):
            with self.assertRaisesRegex(ValueError,'ASSIGNMENT_CHANGED'):self.run_action('start')
        self.service.driver.guest.assert_not_called()
        with patch.object(auth,'observe',return_value=dict(state='SELECTED',selectedSource=selection,assignmentGeneration=7)):
            self.run_action('start')
        self.service.driver.guest.assert_called_once_with(self.state,'test','camera-start',sourceId='source',generation=7)

    def test_stop_uses_the_same_source_guest_owner(self):
        self.run_action('stop');self.service.driver.guest.assert_called_once_with(self.state,'test','camera-stop')

    def test_foreign_gateway_selection_is_not_mutated_even_to_stop_ingress(self):
        driver=SimpleNamespace(guest=Mock(),vm=Mock())
        with patch.object(auth,'observe',return_value=dict(state='SELECTED',selectedSource={},assignmentGeneration=7)):
            with self.assertRaisesRegex(ValueError,'OWNER_CONFLICT'):auth.detach(driver,self.state)
        driver.guest.assert_not_called()


if __name__=='__main__':unittest.main()
