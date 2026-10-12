# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock,patch

import native_controls_campaign as c

TEST='01234567-89ab-cdef-0123-456789abcdef'


def answer(outcome='PASS',code='CHECK_PASSED',**facts):
    return dict(outcome=outcome,code=code,facts=facts)


class CampaignExecution(unittest.TestCase):
    def ops(self):
        return SimpleNamespace(config=dict(manifestSha256='a'*64),test=TEST,
            preflight=Mock(return_value=answer()),prepare=Mock(return_value=answer()),
            ui=Mock(return_value=answer()),cleanup=Mock(return_value=answer()))

    def execute(self,ops):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            with patch('builtins.print'):
                exit_code=c.execute(ops,root)
            report=json.loads((root/'campaign-report.json').read_bytes())
            files={p.name:p.read_text() for p in root.iterdir() if p.is_file()}
            return exit_code,report,files

    def test_one_call_runs_every_phase_and_closes(self):
        ops=self.ops();order=[]
        for name in ('preflight','prepare','ui','cleanup'):
            getattr(ops,name).side_effect=lambda name=name:(order.append(name) or answer())
        status,report,_=self.execute(ops)
        self.assertEqual(order,['preflight','prepare','ui','cleanup'])
        self.assertEqual(status,0);self.assertEqual(report['nativeControls'],'PASS')
        self.assertTrue(report['cleanupConfirmed']);self.assertFalse(report['agentStepScheduling'])
        self.assertEqual(report['fullE2E'],'NOT_COMPLETE')

    def test_cloud_conflict_stops_before_preparation_and_input(self):
        ops=self.ops();ops.preflight.return_value=answer('BLOCKED','TEST_UNIT_SET_HAS_OTHER_UNITS',cloudMutation=False)
        status,report,files=self.execute(ops)
        self.assertEqual(status,2);self.assertEqual(report['outcome'],'BLOCKED')
        ops.prepare.assert_not_called();ops.ui.assert_not_called();ops.cleanup.assert_called_once()
        self.assertFalse(report['nativeStageStarted'])
        skipped=[r for r in report['stages'] if r['outcome']=='NOT_RUN']
        self.assertEqual({r['stage'] for r in skipped},{'prepare-baseline','native-ui'})
        self.assertTrue(all(r['seconds'] is None for r in skipped))
        self.assertNotIn('native-ui.intent.json',files)

    def test_uncertain_preparation_is_not_retried(self):
        ops=self.ops();ops.prepare.return_value=answer('UNCERTAIN','SUBMISSION_UNCONFIRMED')
        status,report,_=self.execute(ops)
        self.assertEqual(status,1);self.assertEqual(report['outcome'],'UNCERTAIN')
        ops.prepare.assert_called_once();ops.ui.assert_not_called();ops.cleanup.assert_called_once()

    def test_ui_failure_and_cleanup_are_recorded_separately(self):
        ops=self.ops();ops.ui.return_value=answer('FAIL','LIVE_MANEUVER_NOT_CONFIRMED')
        _,report,_=self.execute(ops)
        self.assertEqual(report['code'],'LIVE_MANEUVER_NOT_CONFIRMED')
        self.assertEqual(report['nativeControls'],'NOT_QUALIFIED');self.assertTrue(report['cleanupConfirmed'])

    def test_cleanup_failure_cannot_pass_the_campaign(self):
        ops=self.ops();ops.cleanup.return_value=answer('FAIL','NATIVE_RUNNER_CLOSE_UNCONFIRMED')
        status,report,_=self.execute(ops)
        self.assertEqual(status,1);self.assertFalse(report['cleanupConfirmed'])
        self.assertEqual(report['nativeControls'],'NOT_QUALIFIED')

    def test_raw_exception_does_not_enter_evidence(self):
        ops=self.ops();ops.prepare.side_effect=ValueError('sensitive raw diagnostic secret-token')
        _,report,files=self.execute(ops)
        self.assertEqual(report['code'],'CAMPAIGN_OPERATION_UNAVAILABLE')
        self.assertNotIn('secret-token',''.join(files.values()))

    def test_interruption_remains_uncertain_and_closes(self):
        ops=self.ops();ops.ui.side_effect=KeyboardInterrupt()
        status,report,_=self.execute(ops)
        self.assertEqual(status,1);self.assertEqual(report['outcome'],'UNCERTAIN')
        self.assertEqual(report['code'],'CAMPAIGN_INTERRUPTED');ops.cleanup.assert_called_once()

    def test_malformed_stage_response_cannot_pass(self):
        ops=self.ops();ops.preflight.return_value=answer(code='unsafe free-form text')
        _,report,_=self.execute(ops)
        self.assertEqual(report['code'],'CAMPAIGN_STAGE_RESPONSE_INVALID')
        ops.prepare.assert_not_called();ops.ui.assert_not_called()

    def test_unexpected_internal_error_is_not_a_false_pass(self):
        ops=self.ops();ops.prepare.side_effect=KeyError('sensitive internal input')
        _,report,files=self.execute(ops)
        self.assertEqual(report['outcome'],'UNCERTAIN');ops.ui.assert_not_called()
        self.assertNotIn('sensitive internal input',''.join(files.values()))

    def test_remote_preflight_program_parses_and_does_not_call_mutation_adapter(self):
        import ast
        config=dict(packageRoot='/Users/test/Packages/candidate')
        def read_only(transport,program,timeout):
            source=program.split("<<'SDV_CAMPAIGN_PREFLIGHT'\n",1)[1].rsplit('\nSDV_CAMPAIGN_PREFLIGHT',1)[0]
            ast.parse(source)
            tail=source.split('REQUEST=',1)[1]
            self.assertNotIn("worker.setup(",tail);self.assertNotIn('worker.presenter(',tail)
            self.assertNotIn('method="POST"',tail);self.assertNotIn(".execute(OperationRequest",tail)
            return json.dumps(answer('BLOCKED','TEST_UNIT_SET_HAS_OTHER_UNITS'))
        with patch.object(c.h,'remote',side_effect=read_only),patch('builtins.print'):
            self.assertEqual(c.preflight({},config,None,'native-ui-live-20261012-test')['outcome'],'BLOCKED')


class CampaignPlans(unittest.TestCase):
    def plan(self,root):
        records=root/'.local/remote-qualification/one-campaign'
        return dict(schemaVersion=1,scenario='native-controls',mode='fresh',test=None,
            config=str(root/'transport.json'),journey=str(root/'journey.json'),nativeBuild=str(root/'native'),
            nativeRunId='native-ui-live-20261012-tests',dmg=str(root/'release.dmg'),
            remoteDmg='/Users/test/SDV-Qualification/media/release.dmg',
            mediaRecords=str(root/'.local/remote-qualification/media'),records=str(records),workspace=str(root),
            versions=dict(vdp='158.0.0',brake='137.0.0',tire='69.0.0'))

    def test_private_exact_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();value=self.plan(root);path=root/'plan.json'
            path.write_text(json.dumps(value));path.chmod(0o600)
            self.assertEqual(c.configuration(path),value)

    def test_invalid_plans_fail_before_remote_execution(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();value=self.plan(root);path=root/'plan.json'
            for changes in [dict(schemaVersion=True),dict(mode='delete-everything'),dict(test=TEST),
                            dict(nativeRunId='arbitrary-app'),dict(workspace='/tmp/../Users'),
                            dict(versions={'vdp':'latest','brake':'137.0.0','tire':'69.0.0'}),dict(extra=True)]:
                path.write_text(json.dumps(dict(value,**changes)));path.chmod(0o600)
                with self.assertRaises(ValueError):c.configuration(path)
            path.write_text(json.dumps(value));path.chmod(0o644)
            with self.assertRaises(ValueError):c.configuration(path)

    def test_retained_mode_requires_exact_test(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();value=dict(self.plan(root),mode='retained',test=TEST);path=root/'plan.json'
            path.write_text(json.dumps(value));path.chmod(0o600)
            self.assertEqual(c.configuration(path)['test'],TEST)

    def test_existing_campaign_is_never_replayed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();value=self.plan(root);Path(value['records']).mkdir(parents=True)
            path=root/'plan.json';path.write_text(json.dumps(value));path.chmod(0o600)
            with self.assertRaisesRegex(ValueError,'NEW_PRIVATE_CAMPAIGN_REQUIRED'):c.configuration(path)

    def test_preparation_has_no_publication_retirement_or_reset(self):
        plan=dict(mode='fresh',versions=dict(vdp='158.0.0',brake='137.0.0',tire='69.0.0'))
        config=dict(image='6.1.1-maninblack.41/main-qemuarm64',subjectReferences=[
            dict(team='brake',serviceId=TEST),dict(team='tire',serviceId='11234567-89ab-cdef-0123-456789abcdef')])
        steps=c.preparation_steps(plan,config)
        actions={r.get('args',{}).get('action') for r in steps}
        self.assertFalse(actions & {'publish','service-publish','retire','backend-reset','prepare','service-prepare'})
        positions={r['id']:i for i,r in enumerate(steps)}
        self.assertLess(positions['safe-stop'],positions['connect'])
        self.assertLess(positions['brake-ready'],positions['tire-assign'])
        self.assertEqual(steps[positions['vdp-ready']]['until']['version'],'158.0.0')

    def test_retained_preparation_does_not_recreate_or_reassign(self):
        self.assertEqual([r['kind'] for r in c.preparation_steps(dict(mode='retained'),{})],['vm-access'])


if __name__=='__main__':unittest.main()
