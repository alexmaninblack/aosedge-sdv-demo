# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Bounded startup/negative fixtures for automatic retained-Test recovery."""
import copy,importlib.util,json,tempfile,unittest
import threading
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch
from aosedge_demo_orchestrator import source_boot_recovery as boot
BOOT='aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'
OLD='bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb'

class RecoveryTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        self.root=Path(temp.name);(self.root/boot.JOURNAL).parent.mkdir(parents=True)
        self.state=dict(currentVehicle='test',vehicles=dict(test=dict(localVmId='vm',unitId='unit',nodeId='node',
            systemUid='machine',overlay='overlay',runtime=dict(state='RUNNING',externalConnectivity=dict(state='ON')))),
            source=dict(state='RUNNING',runId='run',assignmentGeneration=2,
                trust=dict(enabled=True,fingerprints=dict(vdp='vdp',runtime='runtime'),
                    onboarding=dict(state='COMPLETE',unitId='unit',nodeId='node'))))
        self.write()
        self.driver=Mock()
        self.driver.operation.return_value=nullcontext()
        self.driver.guests.return_value=dict(test=dict(gate='ABSENT'))
        self.driver.ready.return_value=dict(fresh=True,held=False)
        self.driver.rpc.return_value=dict(held=False,phase='RELEASED')
        self.driver.guest.side_effect=lambda s,r,a,**kw: {'gate':'OPEN'} if a=='allow' else {'gate':'BLOCKED'} if a=='block' else {'mutualTlsConfigured':True}
        self.vm=Mock()
        self.vm._save.side_effect=lambda s:(self.root/boot.JOURNAL).write_text(json.dumps(s))
        self.vm.execute.return_value=dict(vehicles=dict(test=dict(state='COMPLETED')))
        self.vm._owned_pid.return_value=123
        self.service=SimpleNamespace(root=self.root,environment=SimpleNamespace(_writer=lambda:nullcontext()),
            vm=self.vm,driver=self.driver)
        self.p=patch.object(boot,'boot_id',return_value=BOOT);self.p.start();self.addCleanup(self.p.stop)
        self.a=patch.object(boot.auth,'observe',side_effect=lambda d:dict(state='SELECTED',
            selectedSource=boot.auth.selection(self.state),assignmentGeneration=2));self.observe=self.a.start();self.addCleanup(self.a.stop)
        self.c=patch.object(boot.auth,'connection',return_value=dict(serverTls=True));self.c.start();self.addCleanup(self.c.stop)
    def write(self): (self.root/boot.JOURNAL).write_text(json.dumps(self.state))
    def test_recovery_and_no_repeat(self):
        self.assertEqual(boot.tick(self.service)['state'],'COMPLETED')
        self.vm.execute.assert_called_once_with('start','test',120)
        actions=[c.args[1] for c in self.driver.rpc.call_args_list]
        self.assertEqual(actions,['safe_stop','release'])
        self.assertTrue(boot.tick(self.service)['noOp'])
        self.assertEqual(self.vm.execute.call_count,1)
    def test_running_same_boot_no_mutation_and_gate_deletion_not_repaired(self):
        self.driver.guests.return_value=dict(test=dict(gate='OPEN'))
        self.assertEqual(boot.tick(self.service)['state'],'OBSERVED')
        self.driver.guests.return_value=dict(test=dict(gate='ABSENT'))
        self.assertEqual(boot.tick(self.service)['state'],'BLOCKED')
        self.vm.execute.assert_not_called();self.driver.rpc.assert_not_called()
    def test_new_boot_after_previous_completion_is_allowed(self):
        boot.tick(self.service)
        with patch.object(boot,'boot_id',return_value=OLD):
            self.assertEqual(boot.tick(self.service)['state'],'COMPLETED')
        self.assertEqual(self.vm.execute.call_count,2)
    def test_explicit_block_not_opened(self):
        self.driver.guests.return_value=dict(test=dict(gate='BLOCKED'))
        self.assertEqual(boot.tick(self.service)['state'],'BLOCKED')
        self.vm.execute.assert_not_called()
    def test_peer_open_rejected_before_side_effects(self):
        self.driver.guests.return_value=dict(test=dict(gate='ABSENT'),production=dict(gate='OPEN'))
        with self.assertRaisesRegex(boot.EnvironmentError,'PEER_NOT_DETACHED'):boot.tick(self.service)
        self.vm.execute.assert_not_called();self.driver.rpc.assert_not_called()
    def test_wrong_assignment_rejected_before_side_effects(self):
        self.observe.side_effect=None;self.observe.return_value=dict(state='SELECTED',selectedSource={},assignmentGeneration=2)
        with self.assertRaisesRegex(boot.EnvironmentError,'ASSIGNMENT_MISMATCH'):boot.tick(self.service)
        self.vm.execute.assert_not_called();self.driver.rpc.assert_not_called()
    def test_pending_or_foreign_onboarding_not_repaired(self):
        for value in ('pending','foreign','handover'):
            s=copy.deepcopy(self.state)
            if value=='pending':s['source']['trust']['pending']={'action':'detach'}
            if value=='foreign':s['source']['trust']['onboarding']['nodeId']='foreign'
            if value=='handover':s['source']['operation']={'target':'production'}
            (self.root/boot.JOURNAL).write_text(json.dumps(s))
            self.assertEqual(boot.tick(self.service)['state'],'NOT_APPLICABLE')
        self.vm.execute.assert_not_called()
    def test_offline_cold_is_not_claimed(self):
        self.state['vehicles']['test']['runtime']['externalConnectivity']['state']='OFF';self.write()
        self.assertEqual(boot.tick(self.service)['state'],'DEFERRED')
        self.vm.execute.assert_not_called()
    def test_failed_attempt_is_not_automatically_retried(self):
        self.vm.execute.return_value=dict(vehicles=dict(test=dict(state='PARTIAL')))
        with self.assertRaisesRegex(boot.EnvironmentError,'REQUIRES_RECONCILIATION'):boot.tick(self.service)
        self.assertEqual(boot.tick(self.service)['state'],'FAILED')
        self.assertEqual(self.vm.execute.call_count,1)
        self.assertFalse(any(c.args[2]=='allow' for c in self.driver.guest.call_args_list))
    def test_context_change_during_restore_never_opens_gate(self):
        def changed(*args):
            s=json.loads((self.root/boot.JOURNAL).read_text());s['source']['runId']='another-run'
            (self.root/boot.JOURNAL).write_text(json.dumps(s))
            return dict(vehicles=dict(test=dict(state='COMPLETED')))
        self.vm.execute.side_effect=changed
        with self.assertRaises(boot.EnvironmentError):boot.tick(self.service)
        self.assertFalse(any(c.args[2]=='allow' for c in self.driver.guest.call_args_list))

    def test_partial_child_journal_is_preserved(self):
        def partial(*args):
            s=json.loads((self.root/boot.JOURNAL).read_text())
            s['operations']=[dict(id='child',state='UNCERTAIN')]
            s['vehicles']['test']['runtime']['observation']='CHILD_OBSERVED'
            (self.root/boot.JOURNAL).write_text(json.dumps(s))
            return dict(vehicles=dict(test=dict(state='BLOCKED',reason='SOURCE_TRUST_RESTORE_UNCONFIRMED')))
        self.vm.execute.side_effect=partial
        with self.assertRaises(boot.EnvironmentError):boot.tick(self.service)
        s=json.loads((self.root/boot.JOURNAL).read_text())
        self.assertEqual(s['operations'],[dict(id='child',state='UNCERTAIN')])
        self.assertEqual(s['vehicles']['test']['runtime']['observation'],'CHILD_OBSERVED')
        self.assertEqual(s['source']['bootRecovery']['guestRestoreReason'],'SOURCE_TRUST_RESTORE_UNCONFIRMED')

    def test_exception_after_child_write_preserves_it(self):
        def partial(*args):
            s=json.loads((self.root/boot.JOURNAL).read_text());s['operations']=[dict(state='UNCERTAIN')]
            (self.root/boot.JOURNAL).write_text(json.dumps(s));raise OSError('sensitive raw message')
        self.vm.execute.side_effect=partial
        with self.assertRaises(boot.EnvironmentError):boot.tick(self.service)
        s=json.loads((self.root/boot.JOURNAL).read_text())
        self.assertEqual(s['operations'],[dict(state='UNCERTAIN')])
        self.assertNotIn('sensitive',json.dumps(s))

    def test_probe_takes_no_writer_and_stable_boot_is_idle(self):
        self.assertTrue(boot.pending(self.service))
        boot.tick(self.service)
        self.assertFalse(boot.pending(self.service))
        self.assertEqual(self.vm.execute.call_count,1)

    def test_unknown_network_and_uncertain_operation_are_not_restored(self):
        self.state['vehicles']['test']['runtime']['externalConnectivity']={};self.write()
        self.assertFalse(boot.pending(self.service))
        self.assertEqual(boot.tick(self.service)['state'],'DEFERRED')
        self.state['operations']=[dict(state='UNCERTAIN')];self.write()
        self.assertEqual(boot.tick(self.service)['state'],'NOT_APPLICABLE')
        self.vm.execute.assert_not_called()

    def test_failed_route_attempt_blocks_and_never_resubmits(self):
        with patch.object(boot.auth,'connection',return_value=dict(serverTls=False)):
            with self.assertRaises(boot.EnvironmentError):boot.tick(self.service)
        self.assertTrue(any(c.args[2]=='block' for c in self.driver.guest.call_args_list))
        self.assertFalse(boot.pending(self.service))

    def test_worker_respects_ui_and_layout_interlocks(self):
        operations=SimpleNamespace(lock=threading.RLock(),active=True,uncertain=False,workspace_busy=False,source_recovery_busy=False)
        worker=boot.SourceBootRecovery(self.service,operations)
        with patch.object(boot,'pending') as p:worker.tick();p.assert_not_called()
        operations.active=False;operations.workspace_busy=True
        with patch.object(boot,'pending') as p:worker.tick();p.assert_not_called()
        operations.workspace_busy=False;worker.tick()
        self.assertFalse(operations.source_recovery_busy)
        self.assertEqual(operations.source_recovery['state'],'COMPLETED')

    def test_worker_clears_busy_on_failure(self):
        operations=SimpleNamespace(lock=threading.RLock(),active=None,uncertain=False,workspace_busy=False,source_recovery_busy=False)
        worker=boot.SourceBootRecovery(self.service,operations)
        self.vm.execute.return_value=dict(vehicles=dict(test=dict(state='PARTIAL')))
        with self.assertRaises(boot.EnvironmentError):worker.tick()
        self.assertFalse(operations.source_recovery_busy)
        self.assertEqual(operations.source_recovery['state'],'FAILED')

if __name__=='__main__':unittest.main()
