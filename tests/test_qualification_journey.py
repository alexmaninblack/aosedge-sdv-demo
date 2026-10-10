# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts/qualification'))
import journey as j
import journey_plan as p
import journey_worker as w
import remote_harness as h


class Clock:
    value = 0
    def now(self): return self.value
    def sleep(self, seconds): self.value += seconds


class JourneyTests(unittest.TestCase):
    def test_simulator_precedes_provisioning_and_automatic_fota_membership(self):
        ids = [step['id'] for step in p.plan({'image': 'factory'})]
        self.assertLess(ids.index('controller-create'), ids.index('simulation'))
        self.assertLess(ids.index('simulation'), ids.index('provision'))
        self.assertLess(ids.index('provision'), ids.index('connect'))
        self.assertLess(ids.index('connect'), ids.index('vdp-v1-safe'))
        self.assertLess(ids.index('vdp-v1-safe-observed'), ids.index('vdp-v1-prior-update-settled'))
        self.assertLess(ids.index('vdp-v1-prior-update-settled'), ids.index('vdp-v1-prepare'))

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()/'records'
        self.clock = Clock()
        self.calls = []
        self.steps = [dict(id='read',kind='observe',args={'query':'installed'}),
                      dict(id='create',kind='presenter',args={'action':'create'})]

    def remote(self, step, phase, context, request_id, prepared=None):
        self.calls.append((step['id'],phase,request_id,prepared))
        return w.result(dict(sessionId='session') if phase == 'prepare' else dict(runId='test-id'))

    def runner(self, journal, remote=None):
        return j.Runner(journal, remote or self.remote, clock=self.clock.now, sleep=self.clock.sleep, emit=lambda x:None)

    def test_resume_does_not_replay_completed_operations(self):
        with h.Journal(self.root,'x') as journal:
            runner = self.runner(journal)
            runner.run(self.steps)
            calls = len(self.calls)
            runner.run(self.steps)
            self.assertEqual(len(self.calls),calls)
            self.assertEqual(j.report(h.read_attempts(self.root),self.steps)['scriptedSequence'],'PASS')
            self.assertEqual(j.report(h.read_attempts(self.root),self.steps)['fullE2E'],'NOT_COMPLETE')

    def test_intent_and_session_are_saved_before_dispatch(self):
        def remote(step,phase,context,identity,prepared=None):
            if phase == 'execute':
                row=h.read_attempts(self.root)[-1]
                self.assertEqual(row['outcome'],'UNCERTAIN')
                self.assertEqual(row['requestId'],identity)
                self.assertEqual(row['prepared'],{'sessionId':'session'})
            return self.remote(step,phase,context,identity,prepared)
        with h.Journal(self.root,'x') as journal:
            self.runner(journal,remote).run(self.steps)

    def test_lost_reply_reconciles_same_identity_without_redispatch(self):
        def remote(step,phase,*args):
            if phase=='execute': raise OSError('secret-value')
            return self.remote(step,phase,*args)
        with h.Journal(self.root,'x') as journal:
            self.runner(journal,remote).run(self.steps)
            rows=h.read_attempts(self.root)
            self.assertEqual(rows[-1]['outcome'],'UNCERTAIN')
            prior=rows[-1]['requestId']
            self.runner(journal).run(self.steps)
            self.assertEqual(self.calls[-1][1:3],('reconcile',prior))
            self.assertEqual(len([x for x in self.calls if x[1]=='prepare']),1)
            self.assertNotIn('secret-value',json.dumps(h.read_attempts(self.root)))

    def test_uncertain_reconciliation_keeps_later_steps_closed(self):
        with h.Journal(self.root,'x') as journal:
            runner=self.runner(journal,lambda *a,**k:w.result(outcome='UNCERTAIN',code='UNCONFIRMED'))
            result=runner.run(self.steps)
            self.assertEqual(result['engineering'][1]['outcome'],'NOT_RUN')

    def test_changed_step_does_not_inherit_a_pass(self):
        with h.Journal(self.root,'x') as journal:
            runner=self.runner(journal);runner.run(self.steps)
            changed=copy.deepcopy(self.steps);changed[0]['args']['query']='other'
            self.assertEqual(j.report(h.read_attempts(self.root),changed)['engineering'][0]['outcome'],'STALE')
            with self.assertRaises(h.Error):runner.run(changed)

    def test_failed_read_retries_only_failed_step(self):
        steps=self.steps+[dict(id='last',kind='observe')]
        def remote(step,*args):
            return w.result(outcome='FAIL',code='NOT_READY') if step['id']=='last' else self.remote(step,*args)
        with h.Journal(self.root,'x') as journal:
            self.runner(journal,remote).run(steps)
            self.calls.clear();self.runner(journal).run(steps)
            self.assertEqual([x[0] for x in self.calls],['last'])

    def test_named_boundary_does_not_skip_prerequisites(self):
        with h.Journal(self.root,'x') as journal:
            result=self.runner(journal).run(self.steps,'read')
            self.assertEqual(result['engineering'][1]['outcome'],'NOT_RUN')
            with self.assertRaises(h.Error):self.runner(journal).run(self.steps,'typo')

    def test_gate_polls_reads_until_actual_result(self):
        step=dict(id='gate',kind='observe',timeout=10,until=dict(test='equals',actual='$sample.ready',expected=True))
        count=[0]
        def remote(*args):
            count[0]+=1;return w.result(dict(ready=count[0]==3))
        with h.Journal(self.root,'x') as journal:
            row=self.runner(journal,remote).run_step(step,{})
            self.assertEqual(row['outcome'],'PASS');self.assertEqual(count[0],3)
            self.assertEqual(self.clock.value,6)

    def test_gate_deadline_is_failure_not_success(self):
        step=dict(id='gate',kind='observe',timeout=7,until=dict(test='equals',actual='$sample.ready',expected=True))
        with h.Journal(self.root,'x') as journal:
            row=self.runner(journal,lambda *a:w.result(dict(ready=False))).run_step(step,{})
            self.assertEqual(row['outcome'],'FAIL');self.assertEqual(self.clock.value,7)

    def test_soak_is_real_duration_with_repeated_observations(self):
        step=dict(id='soak',kind='hold',seconds=300,check=dict(test='equals',actual='$sample.ready',expected=True))
        calls=[]
        def remote(*args):calls.append(self.clock.value);return w.result(dict(ready=True))
        with h.Journal(self.root,'x') as journal:
            self.assertEqual(self.runner(journal,remote).run_step(step,{})['outcome'],'PASS')
            self.assertEqual(self.clock.value,300);self.assertEqual(len(calls),61)
            self.assertEqual(calls[-1],300)

    def test_soak_aborts_on_broken_invariant(self):
        step=dict(id='soak',kind='hold',seconds=300,check=dict(test='equals',actual='$sample.ready',expected=True))
        with h.Journal(self.root,'x') as journal:
            row=self.runner(journal,lambda *a:w.result(dict(ready=False))).run_step(step,{})
            self.assertEqual(row['outcome'],'FAIL');self.assertEqual(self.clock.value,0)

    def test_missing_reference_is_not_silently_accepted(self):
        with h.Journal(self.root,'x') as journal:
            row=self.runner(journal).run_step(dict(id='bad',kind='presenter',args={'version':'$missing.version'}),{})
            self.assertNotEqual(row['outcome'],'PASS');self.assertFalse(self.calls)

    def test_plan_unique_serial_and_no_automatic_finish(self):
        steps=p.plan({'image':'factory'});ids=[s['id'] for s in steps]
        self.assertEqual(len(ids),len(set(ids)))
        for a,b in (('brake-v1-product','vdp-v2-prepare'),('brake-v2-product','vdp-v3-prepare'),
                    ('brake-v3-product','tire-v1-prepare')):
            self.assertLess(ids.index(a),ids.index(b))
        self.assertFalse(any(s.get('args',{}).get('action')=='reset' for s in steps))
        self.assertEqual(next(s for s in steps if s['id']=='offline-soak')['seconds'],300)
        self.assertLess(ids.index('cloud-subjects'),ids.index('controller-create'))
        for team in ('brake','tire'):
            step=next(s for s in steps if s['id']==team+'-v1-assign')
            self.assertEqual(p.resolve(step['args'],{team+'-v1-publish':dict(serviceId='published-id')})['serviceId'],
                             'published-id')
            self.assertLess(ids.index(team+'-v1-publish'),ids.index(team+'-v1-published'))
            self.assertLess(ids.index(team+'-v1-published'),ids.index(team+'-v1-assign'))

    def test_published_service_requires_exact_cloud_ready_identity(self):
        value=dict(stage='READY',source='AOS_CLOUD_ONLY',version='104.0.0',serviceId='sid',
                   deploymentId='deployment',versionId='version-id')
        check=dict(test='published-service',actual=value,version='104.0.0',serviceId='sid')
        self.assertTrue(p.evaluate(check,{}))
        for key,bad in [('stage','ACCEPTED'),('source',None),('version','103.0.0'),
                        ('serviceId','other'),('deploymentId',None),('versionId',None)]:
            changed=copy.deepcopy(check);changed['actual'][key]=bad
            self.assertFalse(p.evaluate(changed,{}))

    def test_runtime_failure_never_becomes_a_native_pass(self):
        report=j.report([],p.plan({'image':'factory'}))
        self.assertEqual(report['nativeAcceptance'],'NOT_RUN')
        self.assertIn('moving-SOTA',report['separateGates'])
        self.assertIn('VDP-TIMEOUT-01',report['deferred'])

    def test_resume_refreshes_stopped_dependencies_without_republishing(self):
        steps=[dict(id='installed',kind='observe'),dict(id='docker',kind='dependency'),
               dict(id='cloud-pair',kind='setup'),dict(id='presenter',kind='presenter-start')]
        with h.Journal(self.root,'x') as journal:
            runner=self.runner(journal)
            runner.run(steps,'cloud-pair')
            runner.run_step(dict(id='shutdown',kind='shutdown'),{})
            self.calls.clear()
            runner.run(steps,'presenter')
            self.assertEqual([x[0] for x in self.calls if x[1]=='execute'],['docker','presenter'])
            self.assertIn('resume-installed',[x[0] for x in self.calls])

    def test_fully_completed_boundary_does_not_restart_docker(self):
        steps=[dict(id='installed',kind='observe'),dict(id='docker',kind='dependency')]
        with h.Journal(self.root,'x') as journal:
            runner=self.runner(journal);runner.run(steps)
            runner.run_step(dict(id='shutdown',kind='shutdown'),{})
            self.calls.clear();runner.run(steps)
            self.assertEqual(self.calls,[])

    def test_interrupted_offline_experiment_is_not_spliced_across_shutdown(self):
        steps=[dict(id='offline-off',kind='control'),dict(id='cloud-online',kind='observe')]
        with h.Journal(self.root,'x') as journal:
            runner=self.runner(journal);runner.run(steps,'offline-off')
            runner.run_step(dict(id='shutdown',kind='shutdown'),{})
            self.calls.clear();report=runner.run(steps)
            self.assertEqual(self.calls,[])
            self.assertEqual(report['support'][-1]['code'],'EXPERIMENT_INTERRUPTED_REBASE_REQUIRED')
            self.assertEqual(report['engineering'][1]['outcome'],'NOT_RUN')

    def test_resume_restores_only_previously_reached_runtime_owners(self):
        steps=[dict(id='controller-create',kind='presenter'),dict(id='controller-start',kind='presenter'),
               dict(id='next',kind='observe')]
        with h.Journal(self.root,'x') as journal:
            runner=self.runner(journal);runner.run(steps,'controller-start')
            runner.run_step(dict(id='shutdown',kind='shutdown'),{})
            self.calls.clear();runner.run(steps)
            executed=[x[0] for x in self.calls if x[1]=='execute']
            self.assertEqual(executed,['resume-brake','resume-tire','resume-vm'])

    def test_unknown_support_action_reconciled_not_repeated(self):
        step=dict(id='resume-vm',kind='restore',args=dict(owner='vm'))
        def broken(s,phase,*args):
            if phase=='execute':raise OSError()
            return self.remote(s,phase,*args)
        with h.Journal(self.root,'x') as journal:
            self.runner(journal,broken).run_step(step,{})
            self.calls.clear()
            self.runner(journal).run([dict(id='done',kind='observe')])
            self.assertEqual(self.calls[0][0:2],('resume-vm','reconcile'))
            self.assertFalse(any(x[1]=='execute' for x in self.calls))

    def test_resume_reestablishes_physical_fota_gate(self):
        steps=[dict(id='connect',kind='observe'),dict(id='vdp-v1-safe',kind='observe'),
               dict(id='vdp-v1-ready',kind='observe')]
        with h.Journal(self.root,'x') as journal:
            runner=self.runner(journal)
            runner.run(steps,'vdp-v1-safe')
            runner.run_step(dict(id='shutdown',kind='shutdown'),{})
            self.calls.clear()
            def remote(step,*args):
                if step['id']=='resume-vdp-safe-observed':
                    self.calls.append((step['id'],args[0],None,None))
                    return w.result(dict(controller=dict(fresh=True,held=False,mode='SAFE_STOP',speed=0,brake=1)))
                return self.remote(step,*args)
            self.runner(journal,remote).run(steps)
            names=[x[0] for x in self.calls]
            self.assertLess(names.index('resume-connection'),names.index('resume-vdp-safe'))
            self.assertLess(names.index('resume-vdp-safe-observed'),names.index('vdp-v1-ready'))

    def test_changed_harness_evidence_is_not_current_full_script_pass(self):
        with h.Journal(self.root,'x') as journal:
            self.runner(journal).run(self.steps)
            with patch.object(j,'source_pin',return_value='new-source'):
                report=j.report(h.read_attempts(self.root),self.steps)
                self.assertTrue(report['sourceReviewRequired'])
                self.assertEqual(report['scriptedSequence'],'NOT_COMPLETE')

    def test_support_failure_cannot_be_hidden_by_main_passes(self):
        with h.Journal(self.root,'x') as journal:
            runner=self.runner(journal);runner.run(self.steps)
            self.runner(journal,lambda *a:w.result(outcome='FAIL',code='NOT_READY')).run_step(
                dict(id='support-check',kind='observe'),{})
            self.assertEqual(j.report(h.read_attempts(self.root),self.steps)['scriptedSequence'],'NOT_COMPLETE')

    def test_status_does_not_create_records_or_require_writable_lock(self):
        import contextlib,io
        transport=dict(host='host',source='source',user='user',fingerprint='pin')
        config=dict(records=str(self.root),image='factory')
        with patch.object(sys,'argv',['journey.py','--config','unused','--journey','unused','status']), \
             patch.object(h,'configuration',return_value=(transport,'pin')), \
             patch.object(j,'configuration',return_value=config), \
             patch.object(h,'Journal',side_effect=AssertionError('status is read-only')), \
             contextlib.redirect_stdout(io.StringIO()) as output:
            j.main()
        self.assertFalse(self.root.exists())
        self.assertEqual(json.loads(output.getvalue())['nextStep'],'installed')

    def test_read_only_status_checks_record_identity(self):
        transport=dict(host='host',source='source',user='user',fingerprint='pin')
        config=dict(records=str(self.root),image='factory')
        with h.Journal(self.root,j.identity(config,transport)):pass
        self.assertEqual(j.read_records(config,transport),[])
        with self.assertRaises(h.Error):j.read_records(dict(config,image='another'),transport)


class ProjectionTests(unittest.TestCase):
    def test_prior_component_update_must_settle_before_new_publication(self):
        def sample(state='CURRENT', rows=None):
            return w.component_idle_projection(dict(components=dict(state=state, value=rows)))
        self.assertTrue(sample(rows=[])['idle'])
        self.assertTrue(sample(rows=[dict(installed_component=dict(version='136.0.0'))])['idle'])
        for state, rows in [('UNKNOWN',[]),('STALE',[]),('CURRENT',None),('CURRENT',[None]),
                            ('CURRENT',[dict(pending_component=dict(version='136.0.0'))]),
                            ('CURRENT',[dict(pending_component_error='FAILED')])]:
            self.assertFalse(sample(state,rows)['idle'])

    def test_setup_launch_requires_gui_and_reconciliation_never_replays(self):
        with tempfile.TemporaryDirectory() as tmp:
            app=Path(tmp)/'Setup.app'
            executable=app/'Contents/MacOS/SDVLabSetup'
            release=app/'Contents/Resources/tooling/scripts/distribution/setup_release.json'
            executable.parent.mkdir(parents=True);executable.write_bytes(b'fixture')
            release.parent.mkdir(parents=True);release.write_text(json.dumps(dict(manifestSha256='a'*64)))
            worker=object.__new__(w.Worker)
            worker.config=dict(setupApp=str(app),setupSha256=hashlib.sha256(b'fixture').hexdigest())
            worker.pin='a'*64;worker.args=dict(action='launch');worker.request=dict(phase='execute')
            worker.setup_call=Mock()
            worker.shutdown=Mock(return_value=w.result(dict(ownedDemoProcesses=0,reconciliationOnly=True)))
            with patch.object(w.subprocess,'run'):
                for phase in ('prepare','execute','observe'):
                    worker.request['phase']=phase
                    self.assertEqual(worker.setup()['code'],'SETUP_NATIVE_GUI_REQUIRED')
                worker.shutdown.assert_not_called()
                worker.request['phase']='reconcile'
                result=worker.setup()
                self.assertEqual(result['outcome'],'FAIL')
                self.assertEqual(result['code'],'SETUP_LAUNCH_STOPPED_WITHOUT_ACCEPTANCE')
                self.assertTrue(result['facts']['reconciliationOnly'])
                worker.shutdown.assert_called_once_with()
                worker.setup_call.assert_not_called()

    def test_input_gate_requires_fresh_receiving_exact_release(self):
        current=dict(version='55.0.0',fresh=True,connection='CONNECTED',input='RECEIVING',
                     inputReason='NONE',instance=dict(instanceId='native-instance'))
        check=dict(test='receiving-inputs',actual=dict(functions=[current]),version='55.0.0')
        self.assertTrue(p.evaluate(check,{}))
        for key,bad in [('version','54.0.0'),('fresh',False),('connection','STARTING'),
                        ('input','WAITING'),('inputReason','SOURCE_GAP'),('instance',None),('instance',{})]:
            changed=copy.deepcopy(check);changed['actual']['functions'][0][key]=bad
            self.assertFalse(p.evaluate(changed,{}),key)

    def test_moving_gate_needs_actual_fresh_unheld_autopilot_motion(self):
        row=dict(fresh=True,held=False,mode='AUTOPILOT',speed=10)
        check=dict(test='autopilot-moving',actual=dict(controller=row))
        self.assertTrue(p.evaluate(check,{}))
        for key,bad in [('fresh',False),('held',True),('mode','SAFE_STOP'),('speed',0),('speed',True)]:
            changed=copy.deepcopy(check);changed['actual']['controller'][key]=bad
            self.assertFalse(p.evaluate(changed,{}),key)

    def test_ignition_waits_for_a_fresh_new_input_generation(self):
        instance=dict(serviceId='service',subjectId='subject',instanceIndex=0,instanceId='instance')
        before=dict(functions=[dict(version='3.0.0',instance=instance,generation=4)])
        current=dict(version='3.0.0',instance=instance,generation=5,fresh=True,
                     connection='CONNECTED',input='RECEIVING',inputReason='NONE')
        check=dict(test='restarted-inputs',before=before,actual=dict(functions=[current]),version='3.0.0')
        self.assertTrue(p.evaluate(check,{}))
        for key,bad in [('version','2.0.0'),('generation',4),('fresh',False),
                        ('connection','STARTING'),('input','WAITING'),('inputReason','AWAITING_INPUT'),
                        ('instance',dict(instance,instanceId='other'))]:
            changed=copy.deepcopy(check);changed['actual']['functions'][0][key]=bad
            self.assertFalse(p.evaluate(changed,{}),key)
        changed=copy.deepcopy(check);changed['before']['functions']=[]
        self.assertFalse(p.evaluate(changed,{}))

    def test_function_projection_excludes_raw_content_and_conflicts(self):
        instance=dict(serviceId='s',subjectId='u',instanceIndex=0,instanceId='i')
        row=dict(authority='FUNCTION_TEAM_REPORTED_OBSERVATION',stale=False,clockSkew=False,
                 deliveryState='DURABLY_RECEIVED',message=dict(serviceVersion='3.0.0',serviceInstance=instance,
                 generation=5,content=dict(connection='CONNECTED',
                 input=dict(state='RECEIVING',reason='NONE'),secret='SECRET')))
        raw=dict(state='OBSERVED',observations=dict(functionObservations=dict(data=dict(items=[row],truncated=False))))
        projected=w.backend_projection(raw)
        self.assertTrue(projected['functions'][0]['fresh'])
        self.assertEqual(projected['functions'][0]['connection'],'CONNECTED')
        self.assertNotIn('SECRET',json.dumps(projected))
        for key,bad in [('stale',True),('clockSkew',True),('deliveryState','CONFLICT'),('authority','UNKNOWN')]:
            changed=copy.deepcopy(raw);changed['observations']['functionObservations']['data']['items'][0][key]=bad
            self.assertFalse(w.backend_projection(changed)['functions'][0]['fresh'])

    def test_postboot_maneuvers_follow_per_service_input_readiness(self):
        ids=[s['id'] for s in p.plan(dict(image='factory'))]
        for team in ('brake','tire'):
            self.assertLess(ids.index('ignition-'+team+'-inputs'),ids.index('ignition-'+team+'-maneuver'))

    def test_vdp_requires_actual_slot_readiness_and_zero_restarts(self):
        row=dict(activeVersion='1.0.0',vdpData='REPORTED_READY',vdpRestarts='0',processSlotMatches=True)
        self.assertTrue(p.evaluate(dict(test='ready-vdp',actual=row,version='1.0.0'),{}))
        for key,value in (('vdpRestarts','1'),('processSlotMatches',False),('vdpData','UNKNOWN')):
            self.assertFalse(p.evaluate(dict(test='ready-vdp',actual=dict(row,**{key:value}),version='1.0.0'),{}))

    def test_service_requires_installed_and_running_same_version(self):
        value={'state':'CURRENT','value':{'inventory':{'teamServiceIds':{'brake':'id'},'serviceDetails':{'id':{'value':[
            {'service_versions':{'installed_service_version':{'version':'2.0.0'}},'instances':{'value':[
              {'version':'1.0.0','run_state':'active','error_message':'','error_exit_code':0}]}}]}}}}}
        self.assertFalse(p.evaluate(dict(test='ready-service',actual=w.service_projection(value,'brake'),version='2.0.0'),{}))

    def test_new_product_rejects_old_id_and_wrong_version(self):
        for identifier,version,expected in [('old','2.0.0',False),('new','1.0.0',False),('new','2.0.0',True)]:
            self.assertEqual(p.evaluate(dict(test='new-product',before={'productIds':['old']},
                actual={'products':[{'id':identifier,'version':version}]},version='2.0.0'),{}),expected)

    def test_v1_partial_window_does_not_pass_and_secrets_are_not_projected(self):
        row=dict(eventId='event',serviceVersion='1.0.0',terminalState='COMPLETE',deliveryState='DURABLY_RECEIVED',
                 receivedChunkCount=7,expectedChunkCount=8,token='SECRET')
        raw=dict(state='OBSERVED',observations={'productData':{'data':{'items':[row]}}})
        self.assertFalse(w.backend_projection(raw)['products'])
        row['receivedChunkCount']=8
        projected=w.backend_projection(raw)
        self.assertEqual(projected['productIds'],['event']);self.assertNotIn('SECRET',json.dumps(projected))

    def test_reset_correlates_command_and_preserves_other_model_and_history(self):
        before=dict(local={'teams':{'brake':{'model':'b'},'tire':{'model':'t'}}},brake={'productIds':['b']},tire={'productIds':['t']})
        after=copy.deepcopy(before);after['brake'].update(resetState='CLEARED',resetId='new-command')
        check=dict(test='reset-independent',before=before,after=after,team='brake',other='tire',commandId='new-command')
        self.assertTrue(p.evaluate(check,{}))
        after['local']['teams']['tire']['model']='changed';self.assertFalse(p.evaluate(check,{}))

    def test_advisory_must_match_assessment_and_version(self):
        row={'products':[],'productIds':['new'],'advisories':[dict(assessmentId='old',version='3.0.0',state='APPLIED')]}
        self.assertFalse(p.evaluate(dict(test='advisory-applied',actual=row,version='3.0.0'),{}))
        row['advisories'][0]['assessmentId']='new'
        self.assertTrue(p.evaluate(dict(test='advisory-applied',actual=row,version='3.0.0'),{}))
        self.assertFalse(p.evaluate(dict(test='advisory-applied',actual=row,version='3.0.0',
                                        before=dict(productIds=['new'])),{}))

    def test_binding_uses_real_journal_domain_and_rejects_other_targets(self):
        state=dict(schemaVersion=1,kind='democtl.current-run',selectedCloudDomain=w.DOMAIN,
                   vehicles={'test':{'localVmId':'test'}})
        w.validate_binding(state,'test')  # raw vehicle has no synthetic cloudHost
        for bad, expected in ((dict(state,selectedCloudDomain='aoscloud.io'),'test'),
                              (dict(state,vehicles={'test':{'localVmId':'test'},'production':{}}),'test'),
                              (state,'other')):
            with self.assertRaises(ValueError):w.validate_binding(bad,expected)

    def test_brake_v3_activation_accepts_only_the_pinned_valid_v2_condition(self):
        assessment=dict(id='persisted',version='2.0.0',quality='VALID_DEMO_SYNTHETIC',
                        currentBand='INSPECTION_RECOMMENDED')
        fact=dict(assessmentId='persisted',version='3.0.0',state='APPLIED')
        row=dict(products=[assessment],productIds=['persisted'],advisories=[fact])
        check=dict(test='advisory-applied',actual=row,version='3.0.0',
                   before=dict(productIds=['persisted']),activationSourceVersion='2.0.0')
        self.assertTrue(p.evaluate(check,{}))
        for key,value in (('version','1.0.0'),('quality','INVALID'),('currentBand','GOOD')):
            bad=copy.deepcopy(check);bad['actual']['products'][0][key]=value
            self.assertFalse(p.evaluate(bad,{}))
        for key,value in (('version','2.0.0'),('state','RECEIVED'),('assessmentId','unknown')):
            bad=copy.deepcopy(check);bad['actual']['advisories'][0][key]=value
            self.assertFalse(p.evaluate(bad,{}))
        bad=copy.deepcopy(check);bad['actual']['products']=[]
        self.assertFalse(p.evaluate(bad,{}))
        bad=copy.deepcopy(check);bad.pop('activationSourceVersion')
        self.assertFalse(p.evaluate(bad,{}))

    def test_backend_projection_retains_only_condition_eligibility_fields(self):
        message=dict(assessmentId='a',serviceVersion='2.0.0',
            content=dict(quality='VALID_DEMO_SYNTHETIC',currentBand='INSPECTION_RECOMMENDED',secret='SECRET'))
        raw=dict(state='OBSERVED',observations={'assessments':{'data':{'items':[dict(message=message)]}}})
        self.assertEqual(w.backend_projection(raw)['products'],[dict(id='a',version='2.0.0',
            quality='VALID_DEMO_SYNTHETIC',currentBand='INSPECTION_RECOMMENDED')])
        self.assertNotIn('SECRET',json.dumps(w.backend_projection(raw)))

    def test_only_brake_v3_plan_allows_persisted_activation(self):
        steps={s['id']:s for s in p.plan(dict(image='image'))}
        self.assertEqual(steps['brake-v3-advisory']['until']['activationSourceVersion'],
                         '$brake-v2-prepare.version')
        self.assertNotIn('activationSourceVersion',steps['tire-v1-advisory']['until'])

    def test_tire_advisory_uses_contract_content_assessment_id(self):
        root=Path(__file__).resolve().parents[1]
        message=json.loads((root/'contracts/tire-cloud-api/fixtures/tire-advisory-fact.v2.valid.json').read_text())
        raw=dict(state='OBSERVED',observations={'advisories':{'data':{'items':[dict(message=message)]}}})
        fact=w.backend_projection(raw)['advisories'][0]
        self.assertEqual(fact['assessmentId'],message['content']['assessmentId'])
        self.assertEqual(fact['state'],'APPLIED')

    def test_publication_read_waits_for_busy_lock_but_never_hides_other_errors(self):
        from types import SimpleNamespace
        from unittest.mock import Mock
        class OwnerError(Exception): pass
        reader=Mock()
        worker=w.Worker.__new__(w.Worker)
        worker.args=dict(query='publication',release='exact-release')
        worker.app=SimpleNamespace(environment_service=object())
        worker.binding=Mock();worker.idle=Mock()
        modules={'aosedge_demo_orchestrator.environment':SimpleNamespace(EnvironmentError=OwnerError),
                 'aosedge_demo_orchestrator.service_packages':SimpleNamespace(ServicePackages=lambda env:reader)}
        clock=Clock()
        with patch.dict(sys.modules,modules),patch.object(w.time,'monotonic',clock.now),patch.object(w.time,'sleep',clock.sleep):
            reader.cloud_status.side_effect=[OwnerError('CURRENT_RUN_BUSY'),dict(stage='READY')]
            self.assertEqual(worker.observe()['stage'],'READY')
            self.assertEqual(reader.cloud_status.call_count,2)
            self.assertEqual(clock.value,.5)
            self.assertEqual(reader.cloud_status.call_args.args,('exact-release',))
            reader.cloud_status.reset_mock()
            reader.cloud_status.side_effect=OwnerError('OTHER_OWNER_ERROR')
            with self.assertRaisesRegex(OwnerError,'OTHER_OWNER_ERROR'):worker.observe()
            self.assertEqual(reader.cloud_status.call_count,1)
            reader.cloud_status.side_effect=OwnerError('CURRENT_RUN_BUSY')
            with self.assertRaisesRegex(OwnerError,'CURRENT_RUN_BUSY'):worker.observe()
            self.assertEqual(clock.value,20.5)

    def test_factory_candidate_scope_remains_explicit(self):
        home = '/Users/tester'
        pin = 'a' * 64
        value = dict(schemaVersion=1, manifestSha256=pin, setupSha256='b'*64,
            packageRoot=home+'/store/versions/'+pin, instanceRoot=home+'/state',
            storeRoot=home+'/store', setupApp='/Volumes/test/AosEdge SDV Lab Setup.app',
            sourceRoot='/Volumes/test/Runtime Kit', oemCertificate=home+'/oem.p12',
            spCertificate=home+'/sp.p12', records=home+'/.local/remote-qualification/record')
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path=Path(tmp.name).resolve()/'config.json'
        for suffix in ('39', '40', '41', '42', '../40'):
            value['image']='6.1.1-maninblack.'+suffix+'/main-qemuarm64'
            path.write_text(json.dumps(value)); path.chmod(0o600)
            if suffix in ('39','40','41'):
                self.assertEqual(j.configuration(path,'tester')['image'],value['image'])
            else:
                with self.assertRaisesRegex(h.Error,'FACTORY_OUTSIDE_ACCEPTED_SCOPE'):
                    j.configuration(path,'tester')

    def test_offline_rejects_local_restart_and_changed_identity(self):
        before=dict(local=dict(bootId='boot',identity={'unitId':'unit'},services={'vdp':dict(
            ActiveState='active',Result='success',NRestarts='0')},teams={t:dict(model=t,queuedIds=['q']) for t in ('brake','tire')}),
            brake=dict(productIds=[]),tire=dict(productIds=[]))
        after=copy.deepcopy(before)
        self.assertTrue(p.evaluate(dict(test='offline',before=before,after=after),{}))
        after['local']['services']['vdp']['NRestarts']='1'
        self.assertFalse(p.evaluate(dict(test='offline',before=before,after=after),{}))
        after=copy.deepcopy(before);after['local']['identity']['unitId']='changed'
        self.assertFalse(p.evaluate(dict(test='offline',before=before,after=after),{}))

    def test_exit_wait_allows_normal_signal_to_complete_without_resending(self):
        import subprocess
        clock=Clock();calls=[]
        class Connection:
            def __enter__(self): return self
            def __exit__(self,*args): pass
        def connect(endpoint,**kwargs):
            calls.append(endpoint)
            if clock.value<.5:return Connection()
            raise ConnectionRefusedError()
        with patch.object(w.socket,'create_connection',side_effect=connect), \
             patch.object(w.time,'monotonic',clock.now),patch.object(w.time,'sleep',clock.sleep), \
             patch.object(w.subprocess,'run',return_value=subprocess.CompletedProcess([],0,stdout='')):
            self.assertEqual(w.wait_for_exit()['ownedDemoProcesses'],0)
            self.assertEqual(clock.value,.5)

    def test_exit_wait_does_not_swallow_unknown_socket_errors(self):
        with patch.object(w.socket,'create_connection',side_effect=TimeoutError()):
            with self.assertRaises(TimeoutError):w.wait_for_exit()

    def test_redirect_is_forbidden(self):
        with self.assertRaisesRegex(ValueError,'REDIRECT_FORBIDDEN'):w.NoRedirect().redirect_request(None)

    def test_worker_does_not_expose_unknown_exception_text(self):
        import contextlib,io
        out=io.StringIO()
        with patch.object(w.Worker,'__init__',side_effect=RuntimeError('secret VALUE')),contextlib.redirect_stdout(out):
            w.main('{}')
        self.assertNotIn('secret',out.getvalue())


class DockerPolicyTests(unittest.TestCase):
    def worker(self):
        return w.Worker(dict(config=dict(instanceRoot='/private/tmp/instance',packageRoot='/private/tmp/package',
            manifestSha256='a'*64,setupApp='/private/tmp/Setup.app'),args={},kind='dependency',
            phase='execute',requestId='40000000-0000-0000-0000-000000000004',expectedRun=None,
            prepared=dict(wasRunning=True),dockerOwned=True))

    def test_ready_engine_neither_opens_dashboard_nor_starts_again(self):
        worker=self.worker()
        with patch.object(w,'docker_info',return_value=dict(engineId='id',runningContainers=0)), \
             patch.object(w,'docker_backend_present') as backend,patch.object(w.subprocess,'run') as run:
            self.assertEqual(worker.dependency()['outcome'],'PASS')
            backend.assert_not_called();run.assert_not_called()

    def test_idle_waits_for_background_layout_without_mutation(self):
        worker=self.worker();clock=Clock()
        def exchange(name):
            if name=='snapshot':return {'runId':None}
            return dict(sessionId='session',cloudDomain=w.DOMAIN,active=None,uncertain=False,
                        workspaceBusy=clock.value<1,sourceRecoveryBusy=False)
        with patch.object(w,'exchange',side_effect=exchange), \
             patch.object(w.time,'sleep',clock.sleep),patch.object(w.time,'monotonic',clock.now):
            self.assertFalse(worker.idle()['workspaceBusy'])
            self.assertEqual(clock.value,1)
            self.assertFalse(worker.attempted)

    def test_idle_never_waits_past_uncertain_owner(self):
        worker=self.worker()
        with patch.object(w,'exchange',side_effect=[{'runId':None},dict(sessionId='s',
                cloudDomain=w.DOMAIN,active=None,uncertain=True)]),patch.object(w.time,'sleep') as sleep:
            with self.assertRaisesRegex(ValueError,'OWNER_UNCERTAIN'):worker.idle()
            sleep.assert_not_called()

    def test_absent_assignment_reconciliation_only_reads_authority(self):
        from types import SimpleNamespace as N
        worker=self.worker();worker.args={'action':'service-assign','serviceId':'sid'}
        worker.request.update(phase='reconcile')
        worker.app=N(unit_service=N(observe=lambda *a:dict(services=dict(
            state='CURRENT',value=[],coverage=dict(complete=True)))))
        modules={'aosedge_demo_orchestrator.presenter_operations':N(operation_plan=lambda v:None)}
        with patch.dict(sys.modules,modules),patch.object(worker,'binding',return_value={}), \
             patch.object(w,'exchange',side_effect=AssertionError('no Presenter mutation/read needed')):
            value=worker.presenter()
            self.assertEqual(value['code'],'ASSIGNMENT_NOT_SUBMITTED')
            self.assertEqual(value['outcome'],'FAIL')
            self.assertFalse(worker.attempted)

    def test_assignment_absence_rejects_incomplete_cloud_coverage(self):
        from types import SimpleNamespace as N
        worker=self.worker();worker.args={'action':'service-assign','serviceId':'sid'}
        worker.request.update(phase='reconcile')
        worker.app=N(unit_service=N(observe=lambda *a:dict(services=dict(
            state='CURRENT',value=[],coverage=dict(complete=False)))))
        modules={'aosedge_demo_orchestrator.presenter_operations':N(operation_plan=lambda v:None)}
        with patch.dict(sys.modules,modules),patch.object(worker,'binding',return_value={}):
            with self.assertRaisesRegex(ValueError,'ASSIGNMENT_ABSENCE_UNCONFIRMED'):worker.presenter()

    def test_publication_read_projects_only_fixed_fields(self):
        from types import SimpleNamespace as N
        worker=self.worker();worker.args={'query':'publication','release':'brake/104.0.0'}
        worker.app=N(environment_service=None)
        modules={'aosedge_demo_orchestrator.environment':N(EnvironmentError=RuntimeError),
            'aosedge_demo_orchestrator.service_packages':N(ServicePackages=lambda env:N(
            cloud_status=lambda handle:dict(stage='READY',version='104.0.0',secret='NOT_EVIDENCE')))}
        with patch.dict(sys.modules,modules),patch.object(worker,'binding'),patch.object(worker,'idle'):
            self.assertEqual(worker.observe()['stage'],'READY')
            self.assertNotIn('secret',worker.observe())

    def test_safe_stop_projection_does_not_require_service_models(self):
        from types import SimpleNamespace as N
        worker=self.worker()
        worker.app=N(source_service=N(driver=N(ready=lambda state:{})))
        modules={
            'aosedge_demo_orchestrator.vm':N(access_path=lambda *a:'access'),
            'aosedge_demo_orchestrator.guest_access':N(ssh_command=lambda *a:['ssh']),
        }
        state={'vehicles':{'test':{'sshPort':22022}}}
        with patch.dict(sys.modules,modules),patch.object(worker,'binding',return_value=state), \
             patch.object(w.subprocess,'run',return_value=N(returncode=0,stdout='{"teams":{}}')) as run:
            self.assertEqual(worker.local(require_teams=False)['teams'],{})
            self.assertIn('COLLECT_TEAMS=False',run.call_args.kwargs['input'])
            with self.assertRaisesRegex(ValueError,'SERVICE_PROJECTION_INCOMPLETE'):
                worker.local(require_teams=True)
            self.assertIn('COLLECT_TEAMS=True',run.call_args.kwargs['input'])

    def test_shutdown_reconciliation_never_repeats_stop(self):
        from types import SimpleNamespace as N
        worker=self.worker();worker.request.update(kind='shutdown',phase='reconcile')
        modules={
            'aosedge_demo_orchestrator':N(presenter=N(stop=lambda: self.fail('must not stop'))),
            'aosedge_demo_orchestrator.models':N(OperationRequest=N,VehicleTarget=N(TEST='test')),
            'aosedge_demo_orchestrator.backends':N(BackendService=lambda env:N(observe_stack=lambda:
                dict(teams={t:dict(state='STOPPED') for t in ('brake','tire')}))),
            'aosedge_demo_orchestrator.host_runtime':N(selected=lambda state:N(cli=lambda state:['democtl'])),
            'setup_launch':N(owner=lambda command:None),
        }
        worker.app=N(environment_service=None,execute=lambda *a:self.fail('must only observe'))
        with patch.dict(sys.modules,modules),patch.object(worker,'binding',return_value={'vehicles':{}}), \
             patch.object(w,'wait_for_exit',return_value=dict(ownedDemoListeners=0,ownedDemoProcesses=0)):
            self.assertTrue(worker.shutdown()['facts']['reconciliationOnly'])

    def test_existing_backend_with_delayed_api_is_only_observed(self):
        worker=self.worker();clock=Clock()
        with patch.object(w,'docker_info',side_effect=[None,dict(engineId='id',runningContainers=0)]), \
             patch.object(w,'docker_backend_present',return_value=True),patch.object(w.subprocess,'run') as run, \
             patch.object(w.time,'sleep',clock.sleep),patch.object(w.time,'monotonic',clock.now):
            self.assertEqual(worker.dependency()['outcome'],'PASS')
            run.assert_not_called()

    def test_confirmed_stopped_backend_starts_via_cli_once_without_open(self):
        worker=self.worker();worker.request['prepared']['wasRunning']=False;clock=Clock()
        with patch.object(w,'docker_info',side_effect=[None,dict(engineId='id',runningContainers=0)]), \
             patch.object(w,'docker_backend_present',return_value=False),patch.object(w.subprocess,'run') as run, \
             patch.object(w.time,'sleep',clock.sleep),patch.object(w.time,'monotonic',clock.now):
            self.assertTrue(worker.dependency()['facts']['startedByJourney'])
            self.assertEqual(run.call_args.args[0],[w.DOCKER,'desktop','start','--detach'])
            self.assertEqual(run.call_count,1)

    def test_shutdown_preserves_engine_even_with_legacy_owned_flag(self):
        from types import SimpleNamespace as N
        worker=self.worker();worker.request['kind']='shutdown'
        runtime=N(cli=lambda state:['installed-democtl'])
        modules={
            'aosedge_demo_orchestrator':N(presenter=N()),
            'aosedge_demo_orchestrator.models':N(OperationRequest=N,VehicleTarget=N(TEST='test')),
            'aosedge_demo_orchestrator.backends':N(BackendService=N),
            'aosedge_demo_orchestrator.host_runtime':N(selected=lambda state:runtime),
            'setup_launch':N(owner=lambda command:None),
        }
        with patch.dict(sys.modules,modules),patch.object(worker,'binding',return_value=None), \
             patch.object(w,'wait_for_exit',return_value=dict(ownedDemoListeners=0,ownedDemoProcesses=0)), \
             patch.object(w,'docker_info') as info,patch.object(w.subprocess,'run') as run:
            answer=worker.shutdown()
            self.assertEqual(answer['facts']['dockerEnginePolicy'],'PRESERVED')
            info.assert_not_called();run.assert_not_called()


if __name__=='__main__':unittest.main()
