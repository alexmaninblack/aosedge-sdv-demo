# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
import inspect
import unittest
from unittest.mock import patch
from aosedge_demo_orchestrator import component_runtime as runtime
from aosedge_demo_orchestrator import factory_mainline_gates as gates


class VlanSuccessorFactoryTests(unittest.TestCase):
    def test_exact_successor_pin_and_preserved_matrix(self):
        self.assertEqual(runtime.FACTORY_RELEASES['6.1.1-maninblack.40'],
                         '9adee816b4f942ceafb4d30da4adba318352bf59')
        self.assertEqual(gates.CM_LAUNCHER_TEST_COUNTS['40'], 53)
        self.assertEqual(gates.SM_LAUNCHER_TEST_COUNTS['40'], 32)
        self.assertIn('"cm-vlan", 31', inspect.getsource(gates.NativeGates.run))

    def test_committed_tooling_export(self):
        calls = []
        with patch.object(runtime.subprocess, 'check_output', side_effect=[b'', b'a' * 40, b'archive']), \
             patch.object(runtime.subprocess, 'run'):
            result = runtime.stage_mainline_factory_gates([], calls.append, '/build', '/source', '40')
        self.assertIn('/factory40-gates-', result['conf'])
        self.assertIn('/qualification/factory-40.conf', '\n'.join(calls))

    def test_predecessor_pin_is_not_promoted(self):
        self.assertEqual(runtime.FACTORY_RELEASES['6.1.1-maninblack.39'],
                         '793b1fc035d2b7c123f9a4161788955f389bb81d')
