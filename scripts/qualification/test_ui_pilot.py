# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
import unittest
from unittest.mock import patch, Mock
from io import StringIO
import ui_pilot as p
from ui_forward_admin import rule
from ui_native_gate import validate, native_receipt, LIVE_STAGES, ACTION_IDS, SCENARIO_STAGES
from ui_m1 import read_request, Observer


class PilotGuards(unittest.TestCase):
    def test_focused_moving_runner_has_only_its_two_existing_native_inputs(self):
        self.assertEqual(SCENARIO_STAGES['moving-sota'],
            {'moving-sota-autopilot':'Autopilot','moving-sota-safe-stop':'Safe Stop'})
        self.assertTrue(set(SCENARIO_STAGES['moving-sota']) <= set(SCENARIO_STAGES['continuous-campaign']))

    def test_read_refusal_preserves_only_the_fixed_owner_code_and_never_replays(self):
        for code,expected in [('PLATFORM_NOT_CURRENT','PLATFORM_NOT_CURRENT'),
                             ('SIMULATION_NOT_READY','SIMULATION_NOT_READY'),
                             ('private details','UI_OWNER_READ_UNAVAILABLE'),
                             (None,'UI_OWNER_READ_UNAVAILABLE')]:
            with patch.object(p.j,'Remote') as remote:
                remote.return_value.return_value=dict(outcome='BLOCKED',code=code,facts={})
                with self.assertRaisesRegex(ValueError,'^'+expected+'$'):
                    p.read_query({}, {}, 'test', 'local')
                self.assertEqual(remote.return_value.call_count,1)

    def test_native_mouse_receipt_is_bound_but_does_not_claim_physical_success(self):
        identifier='01234567-89ab-cdef-0123-456789abcdef'
        for stage,action in LIVE_STAGES.items():
            gate=dict(schemaVersion=1,stage=stage,action=action,test=identifier,
                      sessionId=identifier,state='WAITING_FOR_UI_CLICK')
            receipt=dict(requestId=identifier,outcome='INPUT_DISPATCHED',inputDispatched=True,
                code='MOUSE_DOWN_UP_POSTED',action=ACTION_IDS[action],
                binding=dict(candidate='a'*64,test=identifier,sessionId=identifier,stage=stage))
            expected=dict(gate,state='INPUT_DISPATCHED_THROUGH_NATIVE_RUNNER',nativeRequestId=identifier)
            self.assertEqual(native_receipt(gate,receipt,'a'*64),expected)
            for change in ({'outcome':'PASS'},{'inputDispatched':False},{'code':'AXPRESS'},
                           {'action':'driving.delete-test'},{'requestId':'bad'}):
                with self.assertRaises(ValueError):native_receipt(gate,dict(receipt,**change),'a'*64)
            for change in ({'candidate':'b'*64},{'test':'other'},{'sessionId':'other'},{'stage':'other'}):
                with self.assertRaises(ValueError):
                    native_receipt(gate,dict(receipt,binding=dict(receipt['binding'],**change)),'a'*64)

    def test_interrupted_tire_binds_settled_releases_without_converting_failure(self):
        report=dict(outcome='FAIL',scenario='release-story',candidate='a'*64,test='bound',ownersClosed=True)
        browser=dict(outcome='FAIL',scenario='release-story',stages=[dict(stage=n,outcome='PASS')
            for n in ('vdp-v1','brake-v1','vdp-v2','brake-v2','vdp-v3','brake-v3')]
            + [dict(stage='tire-v1',outcome='FAIL',code='NATIVE_UI_BROKER_UNAVAILABLE')])
        events=[]
        for i,(action,team,profile,version) in enumerate((('prepare',None,'v3','158.0.0'),
                ('service-prepare','brake','v3','136.0.0'),('service-prepare','tire','v1','68.0.0'))):
            events.extend([dict(state='DISPATCH_INTENT',requestId=str(i),action=action,team=team,profile=profile),
                           dict(requestId=str(i),productState='COMPLETED',version=version)])
        events.extend([dict(state='DISPATCH_INTENT',requestId='publish',action='service-publish',release='tire/68.0.0'),
            dict(requestId='publish',productState='COMPLETED',releaseHandle='tire/68.0.0'),
            dict(state='WAITING_FOR_NATIVE_UI',stage='tire-v1-maneuver',action='Tire maneuver')])
        self.assertEqual(p.interrupted_tire_binding(report,browser,events,'a'*64,'bound')['tire-v1-prepare'],
                         dict(version='68.0.0'))
        self.assertEqual(report['outcome'],'FAIL')
        for change in ({'outcome':'PASS'},{'candidate':'b'*64},{'test':'other'},{'ownersClosed':False}):
            with self.assertRaises(ValueError):
                p.interrupted_tire_binding(dict(report,**change),browser,events,'a'*64,'bound')
        for changed in (events[:-1],events[:-2]+events[-1:],events+events):
            with self.assertRaises(ValueError): p.interrupted_tire_binding(report,browser,changed,'a'*64,'bound')
        for failure in (dict(stage='return-to-road',outcome='FAIL',code='NATIVE_UI_BROKER_UNAVAILABLE'),
                        dict(stage='tire-v1',outcome='FAIL',code='PRODUCT_OPERATION_FAILED')):
            with self.assertRaises(ValueError):
                p.interrupted_tire_binding(report,dict(browser,stages=browser['stages'][:-1]+[failure]),events,'a'*64,'bound')

    def test_completed_story_binds_followup_without_inheriting_another_candidate(self):
        report=dict(outcome='PASS',scenario='release-story',candidate='a'*64,test='bound',ownersClosed=True)
        names=('vdp-v1','brake-v1','vdp-v2','brake-v2','vdp-v3','brake-v3','tire-v1',
               'return-to-road','confirmed-stop')
        browser=dict(outcome='PASS',scenario='release-story',stages=[dict(stage=n,outcome='PASS') for n in names])
        events=[]
        for i,(action,team,profile,version) in enumerate((('prepare',None,'v3','153.0.0'),
                ('service-prepare','brake','v3','131.0.0'),('service-prepare','tire','v1','67.0.0'))):
            events.extend([dict(state='DISPATCH_INTENT',requestId=str(i),action=action,team=team,profile=profile),
                           dict(requestId=str(i),productState='COMPLETED',version=version)])
        self.assertEqual(p.completed_release_binding(report,browser,events,'a'*64,'bound')['vdp-v3-prepare'],
                         dict(version='153.0.0'))
        for change in ({'outcome':'FAIL'},{'candidate':'b'*64},{'test':'other'},
                       {'ownersClosed':False},{'scenario':'installed'}):
            with self.assertRaises(ValueError):
                p.completed_release_binding(dict(report,**change),browser,events,'a'*64,'bound')
        for changed in (dict(browser,outcome='FAIL'),dict(browser,stages=browser['stages'][:-1]),
                        dict(browser,stages=[dict(stage=n,outcome='FAIL') for n in names])):
            with self.assertRaises(ValueError): p.completed_release_binding(report,changed,events,'a'*64,'bound')
        for changed in ([],events+events,[dict(row,version='latest') if 'version' in row else row for row in events]):
            with self.assertRaises(ValueError): p.completed_release_binding(report,browser,changed,'a'*64,'bound')

    def test_autopilot_witness_is_restricted_to_moving_sota_stage(self):
        identifier='01234567-89ab-cdef-0123-456789abcdef'
        gate=dict(schemaVersion=1,stage='moving-sota-autopilot',action='Autopilot',
                  test=identifier,sessionId=identifier,state='WAITING_FOR_UI_CLICK')
        self.assertEqual(validate(gate,gate['stage'],gate['action'])['state'],'CLICKED_THROUGH_CUA')
        with self.assertRaises(ValueError):
            validate(dict(gate,stage='other'), 'other', 'Autopilot')
    def test_read_only_viewer_closes_process_but_preserves_review_profile(self):
        for code,passed in ((0,True),(1,False)):
            viewer=Observer.__new__(Observer)
            viewer.transport={};viewer.root='/fixed/ui-tools';viewer.python='/fixed/python'
            viewer.records='/fixed/records';viewer.process=Mock()
            viewer.process.poll.return_value=code;viewer.process.wait.return_value=code
            viewer.process.stdout=StringIO('OBSERVER_CLOSED\n')
            with patch('ui_m1.h.remote') as remote:
                self.assertEqual(viewer.close(),passed)
                self.assertEqual(remote.call_count,1)
                self.assertIn('/fixed/ui-tools/Google Chrome.app/',remote.call_args.args[1])
                self.assertIn('assert not any',remote.call_args.args[1])
                self.assertNotIn('rmtree',remote.call_args.args[1])
                self.assertNotIn('unlink',remote.call_args.args[1])
            self.assertTrue(viewer.process.stdout.closed)

    def test_continuation_pins_one_completed_unpublished_prepare(self):
        report=dict(outcome='PASS',scenario='vdp-transition',candidate='a'*64,test='bound',ownersClosed=True)
        events=[dict(state='VDP_V2_PREPARATION_CONFIRMED',version='151.0.0',publication='NOT_REQUESTED')]
        self.assertEqual(p.continuation_binding(report,events,'a'*64,'bound'),dict(preparedV2='151.0.0'))
        for change in ({'outcome':'FAIL'},{'scenario':'release-story'},{'candidate':'b'*64},
                       {'test':'other'},{'ownersClosed':False}):
            with self.assertRaises(ValueError): p.continuation_binding(dict(report,**change),events,'a'*64,'bound')
        for rows in ([],events+events,[dict(events[0],version='latest')],[dict(events[0],publication='READY')]):
            with self.assertRaises(ValueError): p.continuation_binding(report,rows,'a'*64,'bound')

    def test_visible_broker_has_no_action_or_secret_input(self):
        request=dict(uiRead=True,id=1,kind='query',args=dict(name='combined'))
        self.assertEqual(read_request(request,0),(1,'query',dict(name='combined')))
        for change in ({'kind':'publish'},{'id':True},{'id':2},{'args':dict(name='combined',certificate='x')},
                       {'args':[]},{'extra':'x'}):
            with self.assertRaises(ValueError): read_request(dict(request,**change),0)
        with self.assertRaises(ValueError): read_request(request,1)

    def test_native_witness_cannot_select_another_action_or_identity(self):
        identifier='01234567-89ab-cdef-0123-456789abcdef'
        gate=dict(schemaVersion=1,stage='brake-v1-maneuver',action='Brake maneuver',
                  test=identifier,sessionId=identifier,state='WAITING_FOR_UI_CLICK')
        self.assertEqual(validate(gate,gate['stage'],gate['action'])['state'],'CLICKED_THROUGH_CUA')
        for change in ({'state':'CLICKED_THROUGH_CUA'},{'action':'Autopilot'},{'test':'bad'}, {'extra':'x'}):
            with self.assertRaises(ValueError):
                validate(dict(gate,**change),gate['stage'],gate['action'])

    def test_query_cannot_dispatch_a_mutation(self):
        for query in ('create','presenter','shutdown','control'):
            with self.assertRaises(ValueError): p.read_query({}, {}, 'test', query)
        for query in ('service','backend','publication'):
            with self.assertRaises(ValueError): p.read_query({}, {}, 'test', query)
    def test_media_receipt_requires_success_digest_and_size(self):
        media = dict(sha256='a'*64, bytes=123)
        row = dict(command='media-consumer-reverification', outcome='PASS',
                   observations=dict(**media, remoteIdentity='1:2:123:4:5:600'))
        with patch.object(p.h, 'read_attempts', return_value=[row]):
            self.assertEqual(p.verified_media(None, media), row)
            for key, value in (('outcome', 'FAIL'), ('command', 'media-mount')):
                with patch.dict(row, {key: value}):
                    self.assertIsNone(p.verified_media(None, media))
            with patch.dict(row['observations'], {'bytes': 124}):
                self.assertIsNone(p.verified_media(None, media))
            with patch.dict(row['observations'], {'sha256': 'b'*64}):
                self.assertIsNone(p.verified_media(None, media))

    def test_admin_rule_restricts_direction_and_destination(self):
        value = rule('tester', '192.168.247.1').decode()
        self.assertIn('AllowTcpForwarding local\n', value)
        self.assertIn('PermitOpen 127.0.0.1:18080\n', value)
        self.assertIn('PermitListen none\n', value)
        for user, source in (('tester\nMatch all', '192.168.247.1'), ('tester', '0.0.0.0')):
            with self.assertRaises(ValueError):
                rule(user, source)

    def test_only_fixed_loopback_forwarding_exception(self):
        with patch.object(p.h, 'ssh_args', return_value=['ssh', '-o', 'ForwardAgent=no',
            '-o', 'ClearAllForwardings=yes', 'target']):
            args = p.forward_args({})
        self.assertIn('ForwardAgent=no', args)
        self.assertIn('ClearAllForwardings=no', args)
        self.assertIn('127.0.0.1:18080:127.0.0.1:18080', args)
        self.assertIn('ExitOnForwardFailure=yes', args)
        self.assertEqual(args[-1], 'target')

    def test_cards_come_from_same_qualified_test(self):
        rows = [dict(step=name, outcome='PASS', observations=dict(facts=facts)) for name, facts in (
            ('created', dict(runId='bound')),
            ('vdp-v3-ready', dict(activeVersion='149.0.0')),
            ('brake-v3-ready', dict(instances=[dict(version='126.0.0')])),
            ('tire-v1-ready', dict(instances=[dict(version='64.0.0')])))]
        with patch.object(p.j, 'read_records', return_value=rows):
            cards = p.qualified_cards({}, {}, 'bound')
            self.assertEqual(cards['Brake service details'], 'v3 · 126.0.0')
            with self.assertRaises(p.h.Error):
                p.qualified_cards({}, {}, 'different')
            rows[-1]['outcome'] = 'FAIL'
            with self.assertRaises(p.h.Error):
                p.qualified_cards({}, {}, 'bound')


if __name__ == '__main__':
    unittest.main()
