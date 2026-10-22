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
    def test_capacity_includes_unpacked_runtime_and_only_missing_media(self):
        receipt=dict(logicalBytes=35*2**30,dmgBytes=14*2**30)
        self.assertEqual(c.consumer_space_required(receipt,False,False),139*2**30)
        self.assertEqual(c.consumer_space_required(receipt,True,False),125*2**30)
        self.assertEqual(c.consumer_space_required(receipt,True,True),90*2**30)
        with self.assertRaisesRegex(h.Error,'MEDIA_CAPACITY_RECEIPT_INVALID'):
            c.consumer_space_required(dict(dmgBytes=10),False,False)

    def test_only_ctime_change_allows_existing_media_reverification(self):
        before='1:2:300:4:5:600'
        self.assertTrue(c.metadata_only_media_change(before,'1:2:300:4:6:600'))
        for after in ('2:2:300:4:6:600','1:3:300:4:6:600','1:2:301:4:6:600',
                      '1:2:300:5:6:600','1:2:300:4:6:644','bad',before):
            self.assertFalse(c.metadata_only_media_change(before,after))

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

    def test_consumer_only_receipt_is_explicit_and_cannot_copy_a_missing_payload(self):
        receipt=self.root/'lab.receipt.json'
        receipt.write_text(json.dumps(dict(dmgBytes=7,dmgSha256='a'*64,manifestSha256='b'*64)))
        value=c.media_input(receipt,dict(manifestSha256='b'*64),
                            '/Users/tester/SDV-Qualification/run/lab.dmg','tester')
        self.assertIsNone(value['path'])
        media=c.Media({}, {}, value);media.remote=Mock(return_value='ABSENT')
        with self.assertRaisesRegex(h.Error,'CONSUMER_MEDIA_MISSING'):media.transfer()
        with self.assertRaises((h.Error,OSError)):c.media_input(self.root/'absent.dmg',dict(manifestSha256='b'*64),
                            '/Users/tester/SDV-Qualification/run/lab.dmg','tester')

    def test_capacity_recovery_is_explicit_and_requires_independent_no_effect_proof(self):
        for proof in (dict(installationEffectsAbsent=True,capacityNowSufficient=True),
                      dict(installationEffectsAbsent=False,capacityNowSufficient=True)):
            media=Mock(transfer=Mock(return_value=dict(remoteIdentity='identity')),
                       file_identity=Mock(return_value='identity'),mount=Mock(return_value={}))
            media.setup.side_effect=[h.Error('INSTALL_SPACE_INSUFFICIENT'),{},{}]
            media.capacity_preflight.return_value=proof
            with h.Journal(self.root/('records-'+str(proof['installationEffectsAbsent'])), 'pin') as journal:
                self.assertFalse(c.installation(media,journal,lambda _:None))
                self.assertTrue(c.installation(media,journal,lambda _:None,resume_capacity=True)
                                is proof['installationEffectsAbsent'])
                rows=h.read_attempts(journal.root)
                self.assertTrue(any(r['code']=='INSTALL_SPACE_INSUFFICIENT' for r in rows))
                if proof['installationEffectsAbsent']:
                    self.assertEqual(media.setup.call_args_list[1].args,('install',False))
                else:
                    self.assertEqual(media.setup.call_count,1)

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

    def test_guest_role_suffix_keeps_fixed_reason_but_no_free_text(self):
        self.assertEqual(w.fixed_reason('SOURCE_TRUST_COMPONENT_TRANSACTION_ACTIVE:test'),
                         'SOURCE_TRUST_COMPONENT_TRANSACTION_ACTIVE')
        self.assertEqual(w.fixed_reason('SOURCE_READ_TIMEOUT:production'),'SOURCE_READ_TIMEOUT')
        for text in ('SOURCE_ERROR:PRIVATE_TEXT','SOURCE_ERROR:test:PRIVATE_TEXT',
                     'SOURCE_ERROR:test\nPRIVATE_TEXT','private arbitrary text'):
            self.assertIsNone(w.fixed_reason(text))
        value=w.job_projection(dict(state='BLOCKED',results=[dict(state='BLOCKED',
            message='SOURCE_TRUST_COMPONENT_TRANSACTION_ACTIVE:test')]))
        self.assertEqual(value['results'][0]['code'],'SOURCE_TRUST_COMPONENT_TRANSACTION_ACTIVE')

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
        reference='ref_'+'a'*32
        worker=object.__new__(w.Worker)
        worker.request=dict(expectedRun=None); worker.binding=Mock(return_value={'state':'fixture'})
        with patch.object(worker,'snapshot',return_value=dict(runId=identity,_browserRunId=reference)):
            self.assertEqual(worker.bind_created(dict(runId=reference))[0],identity)
            worker.request['expectedRun']=other
            with self.assertRaisesRegex(ValueError,'TEST_IDENTITY_CHANGED'):
                worker.bind_created(dict(runId=reference))
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
