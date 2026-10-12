# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
from pathlib import Path
import socket
import subprocess
import tempfile
import unittest
from unittest.mock import Mock,patch
from ui_read_transport import ReadTransport
import ui_pilot


class ReadTransportGuards(unittest.TestCase):
    def fixture(self,root):
        channel=ReadTransport({},Path(root).resolve());endpoint=socket.socket(socket.AF_UNIX);endpoint.bind(str(channel.socket))
        self.addCleanup(endpoint.close)
        master=Mock();master.poll.return_value=None;channel.master=master
        master.wait.side_effect=lambda **k:master.poll.configure_mock(return_value=0)
        self.addCleanup(channel.socket.unlink,missing_ok=True)
        return channel

    def test_fixed_transport_retains_pins_and_forbids_reconnect(self):
        with tempfile.TemporaryDirectory() as root,patch('ui_read_transport.h.ssh_args',return_value=['ssh','-o','ForwardAgent=no','target']):
            channel=ReadTransport({},Path(root).resolve());args=channel.arguments()
            self.assertIn('ForwardAgent=no',args);self.assertIn('ProxyCommand=/usr/bin/false',args)
            self.assertIn('ControlMaster=no',args);self.assertEqual(args[-1],'target')
            with self.assertRaisesRegex(ValueError,'LOST_NO_RECONNECT'):channel.remote('never')

    def test_two_reads_share_only_connection_and_close_exact_owners(self):
        with tempfile.TemporaryDirectory() as root:
            channel=self.fixture(root)
            first=Mock(returncode=0);first.poll.return_value=0;first.communicate.return_value=('first',None)
            second=Mock(returncode=0);second.poll.return_value=0;second.communicate.return_value=('second',None)
            with patch('ui_read_transport.h.ssh_args',return_value=['ssh','target']),patch('ui_read_transport.subprocess.Popen',side_effect=[first,second]) as start:
                self.assertEqual(channel.remote('fresh-one'),'first');self.assertEqual(channel.remote('fresh-two'),'second')
            self.assertEqual(start.call_count,2);self.assertEqual(len(channel.calls),2)
            with patch('ui_read_transport.h.ssh_args',return_value=['ssh','target']),patch('ui_read_transport.h.run'):
                channel.close()
            self.assertTrue(channel.report()['closed']);self.assertFalse(channel.report()['cachedOwnerResponses'])

    def test_lost_master_refuses_before_starting_a_reader(self):
        with tempfile.TemporaryDirectory() as root:
            channel=self.fixture(root);channel.master.poll.return_value=0
            with patch('ui_read_transport.subprocess.Popen') as start:
                with self.assertRaisesRegex(ValueError,'LOST_NO_RECONNECT'):channel.remote('never')
            start.assert_not_called()

    def test_timeout_cancels_exact_client_group_and_never_replays(self):
        with tempfile.TemporaryDirectory() as root:
            channel=self.fixture(root);task=Mock(pid=321);task.poll.return_value=None
            task.communicate.side_effect=[subprocess.TimeoutExpired('unit',1),('',None)]
            def killed(pid,sig):self.assertEqual(pid,321);task.poll.return_value=-15
            with patch('ui_read_transport.h.ssh_args',return_value=['ssh','target']),patch('ui_read_transport.subprocess.Popen',return_value=task) as start,patch('ui_read_transport.os.killpg',side_effect=killed):
                with self.assertRaisesRegex(ValueError,'TIMEOUT_NO_RETRY'):channel.remote('read',timeout=1)
            self.assertEqual(start.call_count,1);self.assertIsNone(channel.active)

    def test_reused_transport_cannot_admit_mutation_queries(self):
        channel=Mock()
        for name in ['create','publish','shutdown','presenter','mode']:
            with self.assertRaises(ValueError):ui_pilot.read_query({}, {}, 'test', name,channel=channel)
        channel.remote.assert_not_called()

    def test_every_reused_read_creates_an_exact_fresh_observe_payload(self):
        channel=Mock();channel.remote.side_effect=['{"outcome":"PASS","code":"POSTCONDITION_OBSERVED","facts":{"boot":"one"}}',
            '{"outcome":"PASS","code":"POSTCONDITION_OBSERVED","facts":{"boot":"two"}}']
        config={'packageRoot':'/private/unit-package'}
        self.assertEqual(ui_pilot.read_query({},config,'same-test','exercise',channel=channel),{'boot':'one'})
        self.assertEqual(ui_pilot.read_query({},config,'same-test','exercise',channel=channel),{'boot':'two'})
        first,second=[c.args[0] for c in channel.remote.call_args_list]
        self.assertNotEqual(first,second);self.assertIn('"phase": "observe"',first);self.assertIn('"kind": "observe"',first)
        self.assertIn('"expectedRun": "same-test"',first)

if __name__=='__main__':unittest.main()
