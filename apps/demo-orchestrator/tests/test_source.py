# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import Mock

from aosedge_demo_orchestrator.environment import EnvironmentService, EnvironmentError
from aosedge_demo_orchestrator.source import SourceService, SourceDriver
from aosedge_demo_orchestrator.source_guest import rules


class Driver:
    def __init__(self, vm):
        self.vm = vm
        self.calls = []
        self.gates = dict(test="BLOCKED", production="BLOCKED")
        self.fail = None
        self.fresh = True
        self.tls = True

    def guests(self, state, action):
        self.calls.append((action, "all"))
        if action == "block":
            self.gates = {role: "BLOCKED" for role in self.gates}
        return {r: dict(gate=g, vdpProcess="inactive", vdpData="NOT_OBSERVED") for r, g in self.gates.items()}

    def guest(self, state, role, action):
        self.calls.append((action, role))
        if action == "allow": self.gates[role] = "OPEN"
        if action == "block": self.gates[role] = "BLOCKED"
        return dict(serverTls=self.tls, advancingVissFrames=self.tls, gate=self.gates[role])

    def rpc(self, source, action, identity):
        self.calls.append((action, identity))
        return dict(fresh=self.fresh, held=False, phase="RELEASED")

    def wait(self, source, identity, phase):
        self.calls.append(("wait", phase))
        if self.fail == phase:
            raise EnvironmentError("SOURCE_COMPLETED_FRAME_TIMEOUT:" + phase)
        return dict(fresh=True, frame=dict(resetGeneration=1))


class SourceTests(unittest.TestCase):
    def test_initial_manual_waits_before_opening_test_source(self):
        self.service._select(self.state, "test", initial_manual=True)
        calls = self.driver.calls
        self.assertLess(calls.index(("wait", "MANUAL_READY")), calls.index(("allow", "test")))
        self.assertLess(calls.index(("probe", "test")), next(index for index, call in enumerate(calls) if call[0] == "release_manual"))
        self.assertNotIn("release", [call[0] for call in calls])

    def test_initial_manual_cannot_be_used_for_handover(self):
        self.state["source"]["assignmentGeneration"] = 1
        with self.assertRaisesRegex(EnvironmentError, "FIRST_TEST_CONNECTION"):
            self.service._select(self.state, "test", initial_manual=True)
        self.assertNotIn("allow", [call[0] for call in self.driver.calls])

    def setUp(self):
        self.vm = Mock()
        self.driver = Driver(self.vm)
        self.service = SourceService(self.vm, Mock(), self.driver)
        self.state = dict(currentVehicle=None, vehicles=dict(test={}, production={}),
                          source=dict(assignmentGeneration=0, operation=None))

    def test_handover_orders_physical_stop_detach_reset_attach(self):
        result = self.service._select(self.state, "test")
        names = [x[0] for x in self.driver.calls]
        self.assertLess(names.index("safe_stop"), names.index("block"))
        self.assertLess(names.index("block"), names.index("reset"))
        self.assertLess(names.index("reset"), names.index("allow"))
        self.assertLess(names.index("probe"), names.index("release"))
        self.assertEqual("test", result["currentVehicle"])
        self.assertEqual(dict(test="OPEN", production="BLOCKED"), self.driver.gates)
        self.assertEqual(1, names.count("status"))
        self.assertEqual("test", self.state["source"]["lastConnectionConfirmation"]["role"])
        self.service._select(self.state, "production")
        self.assertEqual(dict(test="BLOCKED", production="OPEN"), self.driver.gates)
        self.assertEqual(2, self.state["source"]["assignmentGeneration"])

    def test_same_role_is_observed_no_op(self):
        self.service._select(self.state, "test")
        self.driver.calls.clear()
        self.vm._save.reset_mock()
        result = self.service._select(self.state, "test")
        self.assertTrue(result["noOp"])
        self.assertEqual(["status", "status", "probe"], [x[0] for x in self.driver.calls])
        self.vm._save.assert_not_called()

    def test_stop_or_reset_failure_never_attaches(self):
        for phase in ("SAFE_STOP", "RESET"):
            with self.subTest(phase=phase):
                self.setUp()
                self.driver.fail = phase
                with self.assertRaises(EnvironmentError):
                    self.service._select(self.state, "test")
                self.assertNotIn("allow", [x[0] for x in self.driver.calls])
                self.assertIsNotNone(self.state["source"]["operation"])

    def test_wrong_live_assignment_does_not_mutate(self):
        self.driver.gates["production"] = "OPEN"
        with self.assertRaisesRegex(EnvironmentError, "CONTRADICTORY"):
            self.service._select(self.state, "test")
        self.assertEqual([("status", "all")], self.driver.calls)
        self.vm._save.assert_not_called()

    def test_tls_failure_closes_new_gate_and_keeps_hold(self):
        self.driver.tls = False
        with self.assertRaisesRegex(EnvironmentError, "NOT_READY"):
            self.service._select(self.state, "test")
        self.assertEqual(dict(test="BLOCKED", production="BLOCKED"), self.driver.gates)
        self.assertNotIn("release", [x[0] for x in self.driver.calls])

    def test_unknown_same_role_never_becomes_success(self):
        self.service._select(self.state, "test")
        self.driver.fresh = False
        with self.assertRaisesRegex(EnvironmentError, "NOT_READY"):
            self.service._select(self.state, "test")

    def test_resume_confirmed_reset_does_not_reset_again(self):
        identity = "11111111-1111-4111-8111-111111111111"
        self.state["source"]["operation"] = dict(id=identity, target="test", previous=None, phase="RESET_CONFIRMED")
        original = self.driver.rpc
        def rpc(source, action, supplied):
            if action == "status":
                self.driver.calls.append((action, supplied))
                return dict(operationId=identity, phase="RESET", fresh=True, held=True)
            return original(source, action, supplied)
        self.driver.rpc = rpc
        result = self.service._select(self.state, "test")
        self.assertEqual("test", result["currentVehicle"])
        self.assertNotIn("reset", [x[0] for x in self.driver.calls])
        self.assertNotIn("safe_stop", [x[0] for x in self.driver.calls])

    def test_other_role_cannot_take_over_uncertain_operation(self):
        self.state["source"]["operation"] = dict(id="pending", target="test", phase="DETACHED")
        with self.assertRaisesRegex(EnvironmentError, "RECONCILIATION"):
            self.service._select(self.state, "production")
        self.vm._save.assert_not_called()

    def test_wait_requires_current_stopped_frame_not_only_completed_phase(self):
        from unittest.mock import patch
        driver = SourceDriver(self.vm)
        moving = dict(operationId="id", phase="RESET", fresh=True,
            frame=dict(activeMode="SAFE_STOP", speedKmh=1.28, brake=1))
        stopped = dict(moving, frame=dict(activeMode="SAFE_STOP", speedKmh=0, brake=1))
        driver.rpc = Mock(side_effect=[moving, stopped])
        with patch("aosedge_demo_orchestrator.source.time.sleep"):
            self.assertEqual(stopped, driver.wait({}, "id", "RESET"))
        self.assertEqual(2, driver.rpc.call_count)

    def test_block_filters_both_directions_and_only_viss(self):
        blocked = rules(True)
        self.assertEqual(["output", "input"], [x["chain"] for x in blocked])
        self.assertTrue(all(x["expr"][-1] == {"drop": None} for x in blocked))
        self.assertTrue(all(x["expr"][0]["match"]["right"] == "10.0.0.1" for x in blocked))
        self.assertTrue(all(x["expr"][1]["match"]["right"] == 6443 for x in blocked))
        self.assertEqual(16443, rules(False)[0]["expr"][-1]["dnat"]["port"])

    def test_composite_writer_is_reentrant_but_not_cross_thread(self):
        with tempfile.TemporaryDirectory() as directory:
            environment = EnvironmentService(root=directory)
            errors = []
            def contender():
                try:
                    with environment._writer():
                        errors.append("WRONG_SUCCESS")
                except EnvironmentError as error:
                    errors.append(str(error))
            with environment._writer():
                with environment._writer():
                    thread = threading.Thread(target=contender)
                    thread.start(); thread.join()
                with self.assertRaisesRegex(EnvironmentError, "BUSY"):
                    with EnvironmentService(root=directory)._writer():
                        pass
            self.assertEqual(["CURRENT_RUN_BUSY"], errors)
