# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
import copy
from pathlib import Path
import unittest
from unittest.mock import patch
import vision_fresh_retire_worker as worker


class FreshRetirementTests(unittest.TestCase):
    def state(self):
        return dict(vmProfile='aos-vision-main-qemuarm64-v1',currentVehicle=None,source=dict(state='STOPPED'),
            vehicles=dict(test=dict(unitId=worker.OLD_UNIT,nodeId=worker.OLD_NODE,localVmId=worker.OLD_VM,runtime=dict(state='STOPPED'))))
    def test_only_exact_discarded_vision_is_accepted(self):
        root=Path('/Users/alexagizim')/worker.INSTANCE;state=self.state()
        self.assertEqual(worker.target(root,state)['unitId'],worker.OLD_UNIT)
        for field in ('unitId','nodeId','localVmId'):
            other=copy.deepcopy(state);other['vehicles']['test'][field]='foreign'
            with self.assertRaises(ValueError):worker.target(root,other)
        with self.assertRaises(ValueError):worker.target(Path('/Users/alexagizim/SDV-Lab-Data'),state)
        state['currentVehicle']='test'
        with self.assertRaises(ValueError):worker.target(root,state)
    def test_absence_uses_selected_set_not_main_title_lookup(self):
        from aosedge_demo_orchestrator.units import UnitService
        from types import SimpleNamespace
        unit=UnitService(SimpleNamespace(root=Path('/unused'),environment=SimpleNamespace(root=Path('/unused')),progress=lambda _:None))
        with patch('aosedge_demo_orchestrator.units.load_configuration',return_value=dict(cloudProfiles={'oem-delivery':{}})), \
             patch('aosedge_demo_orchestrator.units.read_json',return_value={}), \
             patch('aosedge_demo_orchestrator.units.cloud_binding',return_value=dict(sets=dict(test='vision-only'))), \
             patch.object(unit,'_cloud_profile',return_value={}) as call:
            unit._cloud('absence',unitId=worker.OLD_UNIT)
            self.assertEqual(call.call_args.kwargs['setIds'],dict(test='vision-only'))


if __name__=='__main__':unittest.main()
