# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts/qualification'))
import campaign as c
import journey as j
import journey_worker as w
import remote_harness as h


class CampaignTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()

    def test_install_sequence_has_one_authority_no_runtime_in_between(self):
        media = Mock()
        media.transfer.return_value = dict(remoteIdentity='identity')
        media.file_identity.return_value = 'identity'
        media.mount.return_value = {}
        media.setup.return_value = {}
        with h.Journal(self.root/'records', 'pin') as journal:
            self.assertTrue(c.installation(media, journal, lambda _: None))
            calls = [(x[0],x[1]) for x in media.mock_calls]
            self.assertEqual(calls, [('transfer',()),('mount',()),('setup',('install',False)),('setup',('prepare',False))])
            media.reset_mock()
            self.assertTrue(c.installation(media, journal, lambda _: None))
            media.transfer.assert_not_called(); media.setup.assert_not_called()
            media.mount.assert_called_once()

    def test_interrupted_install_reconciles_before_continuing(self):
        media = Mock(transfer=Mock(return_value=dict(remoteIdentity='identity')),
                     file_identity=Mock(return_value='identity'), mount=Mock(return_value={}))
        media.setup.side_effect = [OSError('PRIVATE_TEXT'), {}, {}]
        with h.Journal(self.root/'records', 'pin') as journal:
            self.assertFalse(c.installation(media, journal, lambda _: None))
            self.assertTrue(c.installation(media, journal, lambda _: None))
        self.assertEqual(media.setup.call_args_list[1].args, ('install',True))
        self.assertNotIn('PRIVATE_TEXT', json.dumps(h.read_attempts(self.root/'records')))

    def test_wrong_receipt_or_remote_target_fails_before_transfer(self):
        dmg = self.root/'lab.dmg'; dmg.write_bytes(b'fixture')
        receipt = dict(dmgBytes=7, dmgSha256='a'*64, manifestSha256='b'*64)
        dmg.with_suffix('.receipt.json').write_text(json.dumps(receipt))
        config = dict(manifestSha256='b'*64)
        self.assertEqual(c.media_input(dmg,config,'/Users/tester/SDV-Qualification/run/lab.dmg','tester')['bytes'],7)
        for path in ('/tmp/lab.dmg','/Users/tester/SDV-Qualification/lab.dmg',
                     '/Users/tester/SDV-Qualification/run/../lab.dmg'):
            with self.assertRaises(h.Error): c.media_input(dmg,config,path,'tester')
        with self.assertRaises(h.Error): c.media_input(dmg,dict(manifestSha256='c'*64),
            '/Users/tester/SDV-Qualification/run/lab.dmg','tester')

    def test_foreign_mount_is_never_detached(self):
        media = c.Media({},dict(setupApp='/Volumes/Lab/AosEdge SDV Lab Setup.app'),dict(remotePath='/mine'))
        media.attachments = lambda: [dict(**{'image-path':'/other','system-entities':[{'mount-point':'/Volumes/Lab'}]})]
        media.remote = Mock()
        with self.assertRaisesRegex(h.Error,'MOUNT_OCCUPIED'): media.mount()
        media.remote.assert_not_called()

    def test_partial_identity_is_for_cleanup_not_step_success(self):
        row = dict(outcome='FAIL', step='controller-create', stepDefinition=dict(args=dict(action='create')),
            observations=dict(facts=dict(partialRunBound=True,runId='test')))
        self.assertEqual(j.context_from([row]), {'runId':'test'})
        row['stepDefinition']['args']['action']='publish'
        self.assertEqual(j.context_from([row]), {})

    def test_failed_mutation_is_not_replayed_on_ordinary_resume(self):
        step = dict(id='publish', kind='presenter', args=dict(action='publish'))
        remote = Mock(side_effect=[w.result(dict(sessionId='s')), w.result(outcome='FAIL',code='FAILED')])
        # A plain callable has no diagnostic hook.
        call = lambda *a: remote(*a)
        with h.Journal(self.root/'records','pin') as journal:
            runner=j.Runner(journal,call,emit=lambda _:None)
            runner.run([step]); remote.reset_mock()
            runner.run([step],retry_create=True)
            remote.assert_not_called()

    def test_diagnostics_collected_before_finish_and_are_not_pass(self):
        class Remote:
            def __call__(self,*a): return w.result(outcome='BLOCKED',code='MISSING')
            def diagnose(self,*a): return dict(state='OBSERVED',reason='INPUT_REQUIRED')
        with h.Journal(self.root/'records','pin') as journal:
            runner = j.Runner(journal,Remote(),emit=lambda _:None)
            row = runner.run_step(dict(id='access',kind='vm-access'),{})
            self.assertEqual(row['outcome'],'BLOCKED')
            self.assertEqual(row['observations']['diagnostic']['reason'],'INPUT_REQUIRED')
            self.assertIn('diagnosticSeconds',row['observations']['timing'])

    def test_projection_bounds_and_omits_free_text_and_secrets(self):
        job=dict(state='PARTIAL',progress=['PRIVATE_TEXT'],password='PRIVATE_TEXT',results=[
            dict(state='PARTIAL',message='private arbitrary text',facts=dict(reason='VM_ACCESS_INPUT_INVALID',password='PRIVATE_TEXT'))]*100)
        value=w.job_projection(job)
        self.assertEqual(len(value['results']),12)
        self.assertNotIn('PRIVATE_TEXT',json.dumps(value))
        self.assertNotIn('private arbitrary text',json.dumps(value))

    def test_access_precedes_creation_and_no_native_success_is_inferred(self):
        steps=c.plan(dict(image='factory'))
        ids=[s['id'] for s in steps]
        self.assertLess(ids.index('vm-access'),ids.index('controller-create'))
        self.assertEqual(j.report([],steps)['nativeAcceptance'],'NOT_RUN')

    def test_bound_partial_create_can_continue_only_when_explicit(self):
        step=dict(id='controller-create',kind='presenter',args=dict(action='create'))
        calls=[]
        def remote(step,phase,*args):
            calls.append(phase)
            if phase=='prepare': return w.result(dict(sessionId='s'))
            if calls.count('execute')==1:
                return w.result(dict(runId='test',partialRunBound=True),outcome='FAIL',code='PARTIAL_CREATE')
            return w.result(dict(runId='test'))
        with h.Journal(self.root/'records','pin') as journal:
            runner=j.Runner(journal,remote,emit=lambda _:None)
            runner.run([step]); self.assertEqual(calls,['prepare','execute'])
            runner.run([step]); self.assertEqual(calls,['prepare','execute'])
            runner.run([step],retry_create=True)
            self.assertEqual(calls,['prepare','execute','prepare','execute'])
            self.assertEqual(j.report(h.read_attempts(journal.root),[step])['scriptedSequence'],'PASS')

    def test_created_identity_must_match_existing_binding_and_receipt(self):
        from uuid import uuid4
        identity=str(uuid4());other=str(uuid4())
        worker=object.__new__(w.Worker)
        worker.request=dict(expectedRun=None); worker.binding=Mock(return_value={'state':'fixture'})
        with patch.object(w,'exchange',return_value=dict(runId=identity)):
            self.assertEqual(worker.bind_created(dict(runId=identity))[0],identity)
            worker.request['expectedRun']=other
            with self.assertRaisesRegex(ValueError,'TEST_IDENTITY_CHANGED'):
                worker.bind_created(dict(runId=identity))
            worker.request['expectedRun']=None
            with self.assertRaisesRegex(ValueError,'CREATE_IDENTITY_UNCONFIRMED'):
                worker.bind_created(dict(runId=other))

    def test_progress_thread_stops_on_error(self):
        import time
        rows=[]
        with self.assertRaises(ValueError):
            with j.Progress('fixture',rows.append,interval=.001) as progress:
                time.sleep(.005)
                raise ValueError('fixture')
        self.assertTrue(rows); self.assertFalse(progress.thread.is_alive())


if __name__ == '__main__': unittest.main()
