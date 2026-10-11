# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
import unittest
from unittest.mock import patch
import ui_pilot as p
from ui_forward_admin import rule
from ui_native_gate import validate
from ui_m1 import read_request


class PilotGuards(unittest.TestCase):
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
