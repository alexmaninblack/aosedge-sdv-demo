# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch
import unittest
from aosedge_demo_orchestrator import vision_source_guest as v
from vision_first_restore_proof import RESTORE


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


if __name__=='__main__':unittest.main()
