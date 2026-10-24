# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Secure-input SSH must have one unambiguous TTY policy and unchanged scope."""
import unittest
from unittest.mock import patch
import remote_harness as h


class InteractiveTTYTests(unittest.TestCase):
    def setUp(self):
        self.config = dict(source='192.168.247.1', host='192.168.247.2',
                           user='tester', key='/private/test-key', knownHosts='/private/test-hosts')

    def test_only_explicit_interactive_entry_replaces_no_tty_flag(self):
        ordinary = h.ssh_args(self.config)
        interactive = h.interactive_ssh_args(self.config)
        expected = list(ordinary)
        expected[expected.index('-T')] = '-tt'
        self.assertEqual(interactive, expected)
        self.assertNotIn('-T', interactive)
        self.assertEqual(interactive.count('-tt'), 1)
        self.assertNotIn('-tt', ordinary)
        self.assertEqual(ordinary.count('-T'), 1)
        self.assertEqual(interactive[-1], 'tester@192.168.247.2')
        for guard in ('IdentityAgent=none', 'StrictHostKeyChecking=yes',
                      'ForwardAgent=no', 'ClearAllForwardings=yes'):
            self.assertIn(guard, interactive)

    def test_missing_or_ambiguous_base_tty_policy_fails_closed(self):
        for args in (['ssh', 'target'], ['ssh', '-T', '-T', 'target']):
            with self.subTest(args=args), patch.object(h, 'ssh_args', return_value=args):
                with self.assertRaisesRegex(h.Error, 'SSH_TTY_POLICY_INVALID'):
                    h.interactive_ssh_args(self.config)


if __name__ == '__main__':
    unittest.main()
