# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
import inspect
import unittest
from unittest.mock import patch
from aosedge_demo_orchestrator import component_runtime as runtime
from aosedge_demo_orchestrator import factory_mainline_gates as gates


class IgnitionSuccessorFactoryTests(unittest.TestCase):
    def test_exact_pin_and_historical_counts(self):
        self.assertEqual(runtime.FACTORY_RELEASES['6.1.1-maninblack.39'],
                         '793b1fc035d2b7c123f9a4161788955f389bb81d')
        self.assertEqual(gates.CM_LAUNCHER_TEST_COUNTS, {'37': 47, '38': 47, '39': 53})
        self.assertEqual(gates.SM_LAUNCHER_TEST_COUNTS['39'], 32)
        self.assertIn('CM_LAUNCHER_TEST_COUNTS[self.factory_suffix]', inspect.getsource(gates.NativeGates.run))

    def test_committed_gate_export_has_distinct_evidence(self):
        calls = []
        with patch.object(runtime.subprocess, 'check_output', side_effect=[b'', b'a' * 40, b'archive']), \
             patch.object(runtime.subprocess, 'run'):
            result = runtime.stage_mainline_factory_gates([], calls.append, '/build', '/source', '39')
        self.assertIn('/factory39-gates-', result['conf'])
        self.assertIn('/qualification/factory-39.conf', '\n'.join(calls))

    def test_early_projection_package_is_gated_before_image(self):
        source = inspect.getsource(runtime.build_factory)
        self.assertIn('targets += " aos-vehicle-data-provider-platform"', source)
        self.assertIn("helper.read_bytes()==(src/'aos-demo-viss-boot-projection.py').read_bytes()", source)
        self.assertIn("Before=aos-sm.service", source)
        self.assertLess(source.index('Factory early retained VISS projection package: PASS'),
                        source.index('flags + "aos-image-vm"'))
