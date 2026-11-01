# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
import copy
import ast
from pathlib import Path
import unittest
from unittest.mock import patch
import vision_fresh_retire_worker as worker
from vision_fresh_accept_worker import pairs
from vision_fresh_cold_finish import prior_gate,WARM_STAGES


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


class FreshReaderEvidenceTests(unittest.TestCase):
    def test_detach_probe_releases_its_own_physical_stop_before_normal_stop(self):
        tree=ast.parse(Path(__file__).with_name('vision_fresh_accept_worker.py').read_text())
        probe=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='detached_denial')
        guarded=next(n for n in ast.walk(probe) if isinstance(n,ast.Try))
        release=ast.unparse(guarded.finalbody[0])
        self.assertIn("'release', operation",release)
        self.assertNotIn('attach',ast.unparse(probe))

    def test_cold_continuation_requires_exact_failed_stop_and_all_warm_proofs(self):
        value=dict(outcome='NOT_COMPLETE',code='SOURCE_CONTROL_REJECTED',cloudMutation=False,
            cleanup=dict(ownedRuntimesStopped=False,sameFreshIdentity=True,retainedJournalsUnchanged=True),
            phases=[dict(stage=name) for name in WARM_STAGES])
        prior_gate(value)
        for mutate in (lambda v:v.update(cloudMutation=True),lambda v:v.update(code='UNKNOWN'),
                lambda v:v['phases'].pop(),lambda v:v['cleanup'].update(sameFreshIdentity=False)):
            wrong=copy.deepcopy(value);mutate(wrong)
            with self.assertRaises(ValueError):prior_gate(wrong)

    def observation(self):
        epoch='5c281add-e6d3-47fc-abeb-67bb85479471'
        frame=dict(sourceId='e5da8297-853e-4b43-a0fa-48d3ee7adfbd',sourceEpoch='1b93e071-367c-4078-89ca-d603adf4dbaa',
            cameraId='front',calibrationId='test-calibration',frame=10,simulationTimeNs=1000000000,sha256='a'*64)
        return dict(health=dict(componentEpoch=epoch),messages=[dict(probe='LIVE_METADATA',bytesVerified=True,
            value=dict(componentEpoch=epoch,frames=[frame,dict(frame,frame=11,simulationTimeNs=1100000000)]))])
    def test_native_verified_current_pair(self):
        self.assertEqual(len(pairs(self.observation())),1)
    def test_rejects_unverified_old_epoch_and_invalid_cadence(self):
        for change in ('unverified','old-core','different-source','regression','cadence','bad-hash'):
            value=self.observation();row=value['messages'][0];frame=row['value']['frames'][1]
            if change=='unverified':row['bytesVerified']=False
            elif change=='old-core':row['value']['componentEpoch']='past'
            elif change=='different-source':frame['sourceEpoch']='different'
            elif change=='regression':frame['frame']=10
            elif change=='cadence':frame['simulationTimeNs']=1400000000
            else:frame['sha256']='not-a-sha256'
            with self.subTest(change=change):self.assertEqual(pairs(value),[])


if __name__=='__main__':unittest.main()
