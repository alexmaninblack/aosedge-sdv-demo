# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
import importlib.util,unittest
import tempfile
from pathlib import Path
from unittest.mock import patch
from aosedge_demo_orchestrator import source_trust_guest as m
U=['aos-sm.service','aos-vehicle-data-provider.service']
def states(state,job):return '\n\n'.join('Id='+u+'\nActiveState='+state+'\nJob='+job for u in U)
class RestartTests(unittest.TestCase):
 def test_empty_factory_provider_is_condition_skipped_not_failure(self):
  with tempfile.TemporaryDirectory() as folder,patch.object(m,'INPUTS',Path(folder)/'demo-inputs'),patch.object(m,'call',side_effect=['','Id=aos-sm.service\nActiveState=active\nJob=\n\nId=aos-vehicle-data-provider.service\nActiveState=inactive\nJob=']):
   m.activate_consumers(U)
 def test_inactive_installed_provider_is_not_reported_as_empty_factory(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);(root/'state').mkdir();(root/'state/installed.json').write_text('{}')
   with patch.object(m,'INPUTS',root/'demo-inputs'),patch.object(m,'call',side_effect=['',states('inactive','')]),patch.object(m.time,'sleep'),patch.object(m.time,'monotonic',side_effect=[0,1,66]):
    with self.assertRaisesRegex(ValueError,'RESTART_UNCONFIRMED'):m.activate_consumers(U)
 def test_delayed_cm_does_not_resubmit_restart(self):
  with patch.object(m,'call',side_effect=['',states('inactive','1'),states('active','1'),states('active','')]) as c,patch.object(m.time,'sleep'),patch.object(m.time,'monotonic',side_effect=[0,1,31,51]):
   m.activate_consumers(U)
  self.assertEqual(sum('restart' in x.args[0] for x in c.call_args_list),1)
  self.assertEqual(c.call_args_list[0].args[0],['systemctl','--no-block','restart',*U])
 def test_repeat_no_change_does_not_restart(self):
  with patch.object(m,'call') as c:m.activate_consumers([])
  c.assert_not_called()
 def test_timeout_no_resubmit(self):
  with patch.object(m,'call',return_value='') as c,patch.object(m.time,'monotonic',side_effect=[0,66]):
   with self.assertRaisesRegex(ValueError,'RESTART_UNCONFIRMED'):m.activate_consumers(U)
  self.assertEqual(c.call_count,1)
 def test_failed_consumer_not_success(self):
  with patch.object(m,'call',side_effect=['',states('failed','')]):
   with self.assertRaisesRegex(ValueError,'CONSUMER_FAILED'):m.activate_consumers(U)
if __name__=='__main__':unittest.main()
