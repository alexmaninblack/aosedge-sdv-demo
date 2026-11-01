# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch
import unittest
from aosedge_demo_orchestrator import vision_source_guest as v
from vision_first_restore_proof import RESTORE
from vision_pending_reselect_proof import RESUME
import json
import ast
import inspect
import textwrap


class FirstRestoreTests(unittest.TestCase):
    def candidate(self):
        scope=dict(v.__dict__);exec(RESTORE,scope);return scope['restore_initial_projection'],scope
    def test_restores_only_volatile_dropin_without_persistent_write(self):
        action,scope=self.candidate();native=Mock(return_value=('transaction','candidate'))
        scope.update(first_install_state=native,read=lambda path,mode:'unchanged',validate_material=Mock())
        trust=Mock();trust.call.return_value='ActiveState=inactive\nJob=0\n'
        expected={Path('/persistent/enrollment'):('unchanged',0o600),v.DROPIN:('volatile',0o644)}
        with patch.object(v.os.path,'lexists',return_value=False):
            value=action(dict(action='trust-restore'),trust,{}, {},expected)
        trust.write.assert_called_once_with(v.DROPIN,'volatile',0o644)
        self.assertTrue(value['persistentEnrollmentUnchanged']);self.assertEqual(native.call_count,3)
        trust.activate_consumers.assert_called_once_with(['aos-sm.service'])
    def test_changed_persistence_or_existing_dropin_never_stops_native_owner(self):
        for changed,exists in ((True,False),(False,True)):
            action,scope=self.candidate();scope.update(first_install_state=Mock(return_value=('a','b')),
                read=lambda path,mode:'changed' if changed else 'unchanged')
            trust=Mock();expected={Path('/persistent/enrollment'):('unchanged',0o600),v.DROPIN:('volatile',0o644)}
            with patch.object(v.os.path,'lexists',return_value=exists):
                with self.assertRaises(ValueError):action(dict(action='trust-restore'),trust,{}, {},expected)
            trust.call.assert_not_called();trust.write.assert_not_called()
    def test_not_a_second_configure_path(self):
        action,_=self.candidate()
        with self.assertRaisesRegex(ValueError,'FIRST_INSTALL_RESTORE_ONLY'):
            action(dict(action='trust-configure'),Mock(),{}, {},{})


class PendingReselectTests(unittest.TestCase):
    def test_product_function_matches_the_exact_live_proven_candidate(self):
        self.assertEqual(ast.dump(ast.parse(RESUME).body[0]),
            ast.dump(ast.parse(textwrap.dedent(inspect.getsource(v.resume_initial_projection))).body[0]))
    def fixture(self,generation=3,foreign=False,changed=False):
        selected=v.INPUTS/'selected.json';binding=v.INPUTS/'viss-update-binding';key=Path('/persisted/key')
        previous={selected:json.dumps(dict(selectedSource=dict(unitId='same-unit',assignmentGeneration=1))),
                  binding:json.dumps(dict(unitId='same-unit',assignmentGeneration=1)),key:'SAME'}
        expected={selected:(json.dumps(dict(selectedSource=dict(unitId='foreign' if foreign else 'same-unit',assignmentGeneration=generation))),0o644),
                  binding:(json.dumps(dict(unitId='same-unit',assignmentGeneration=generation)),0o644),key:('CHANGED' if changed else 'SAME',0o600),v.DROPIN:('volatile',0o644)}
        scope=dict(v.__dict__);exec(RESUME,scope)
        scope.update(first_install_state=Mock(return_value=('transaction','candidate')),read=lambda path,mode:previous[path],
            validate_material=Mock(),status=Mock(return_value={}))
        trust=Mock();trust.call.return_value='ActiveState=inactive\nJob=0\n'
        return scope['resume_initial_projection'],scope,trust,expected,key
    def test_changes_only_public_generation_selectors_and_volatile_binding(self):
        action,scope,trust,expected,key=self.fixture()
        with patch.object(v.os.path,'lexists',return_value=False):
            value=action(dict(action='trust-configure'),trust,{}, {},expected)
        self.assertEqual({c.args[0] for c in trust.write.call_args_list},set(expected)-{key})
        self.assertTrue(value['persistentEnrollmentUnchanged']);self.assertEqual(scope['first_install_state'].call_count,3)
    def test_foreign_identity_changed_key_and_regression_fail_before_native_stop(self):
        for options in (dict(foreign=True),dict(changed=True),dict(generation=0)):
            action,_,trust,expected,_=self.fixture(**options)
            with patch.object(v.os.path,'lexists',return_value=False):
                with self.assertRaises(ValueError):action(dict(action='trust-configure'),trust,{}, {},expected)
            trust.call.assert_not_called();trust.write.assert_not_called()


if __name__=='__main__':unittest.main()
