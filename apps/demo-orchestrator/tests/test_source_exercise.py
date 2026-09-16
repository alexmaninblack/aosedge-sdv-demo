# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
import unittest
from unittest.mock import Mock, patch
from aosedge_demo_orchestrator.source_exercise import execute
from aosedge_demo_orchestrator.environment import EnvironmentError
from aosedge_demo_orchestrator.cli import build_parser, request_from_arguments
from aosedge_demo_orchestrator.models import VehicleTarget


class ExerciseTests(unittest.TestCase):
    def setUp(self):
        self.state = dict(currentVehicle="test", vehicles={"test": {}}, source=dict(runId="run"))
        self.observed = dict(exerciseSupported=True, phase="IDLE", held=False, operationId=None, exercise=None)
        self.calls = []
        self.service = Mock()
        self.service.driver.ready.side_effect = lambda state: dict(self.observed)
        self.service.driver.rpc.side_effect = self.rpc
        self.service.driver.wait.side_effect = self.wait
        self.clock = 0
        def tick():
            self.clock += .1
            return self.clock
        for replacement in (patch("aosedge_demo_orchestrator.source_exercise.time.monotonic", side_effect=tick),
                patch("aosedge_demo_orchestrator.source_exercise.time.sleep")):
            replacement.start()
            self.addCleanup(replacement.stop)

    def rpc(self, source, action, identity):
        self.calls.append(action)
        if action == "status" and self.observed.get("frame"):
            self.observed["frame"]["frameId"] += 1
        if action == "safe_stop": self.observed.update(operationId=identity, held=True, phase="STOPPING")
        if action == "reset": self.observed["phase"] = "RESETTING"
        if action.startswith("exercise_"):
            self.observed.update(phase="STOPPING", exercise=dict(id=identity,
                kind=action.removeprefix("exercise_"), state="COMPLETED", reason="NONE", metrics={"frames": 100}))
        if action == "release": self.observed.update(phase="RELEASED", held=False)
        return dict(self.observed)

    def wait(self, source, identity, phase):
        self.calls.append("wait_" + phase)
        self.observed.update(phase=phase, operationId=identity, fresh=True,
            frame=dict(activeMode="SAFE_STOP", speedKmh=0, brake=1, frameId=1))
        return dict(self.observed)

    def test_cli_requires_explicit_test(self):
        request = request_from_arguments(build_parser().parse_args(["simulation", "exercise", "brake", "--target", "test"]))
        self.assertEqual(("simulation", "exercise", "brake", VehicleTarget.TEST),
            (request.domain, request.action, request.team, request.target))

    def test_motion_then_physical_stop_then_release_no_guest_or_cloud(self):
        result = execute(self.service, self.state, "brake")
        self.assertEqual("COMPLETED", result["state"])
        self.assertEqual("NOT_EVALUATED", result["modelQualification"])
        self.assertEqual(["status", "safe_stop", "wait_SAFE_STOP", "reset", "wait_RESET",
            "exercise_brake", "wait_SAFE_STOP", "release"], [call for index, call in enumerate(self.calls) if call != "status" or index == 0])
        self.service.driver.guest.assert_not_called()
        self.service.units.assert_not_called()

    def test_reset_bounce_must_settle_before_motion(self):
        original = self.rpc
        samples = iter((2, 1, 0, 0, 0, 0, 0, 0, 0, 0))
        def bouncing(source, action, identity):
            result = original(source, action, identity)
            if action == "status" and result.get("phase") == "RESET":
                result["frame"]["speedKmh"] = next(samples, 0)
            if action.startswith("exercise_"):
                self.assertGreaterEqual(self.calls.count("status"), 8)
            return result
        self.service.driver.rpc.side_effect = bouncing
        self.assertEqual("COMPLETED", execute(self.service, self.state, "brake")["state"])

    def test_reset_never_settles_no_motion_sent(self):
        original = self.rpc
        def bouncing(source, action, identity):
            result = original(source, action, identity)
            if result.get("phase") == "RESET": result["frame"]["speedKmh"] = 2
            return result
        self.service.driver.rpc.side_effect = bouncing
        with self.assertRaisesRegex(EnvironmentError, "RESET_NOT_SETTLED"):
            execute(self.service, self.state, "brake")
        self.assertNotIn("exercise_brake", self.calls)

    def test_wrong_target_busy_and_old_controller_rejected_before_mutation(self):
        for change in ("target", "busy", "old"):
            self.setUp()
            if change == "target": self.state["currentVehicle"] = "production"
            if change == "busy": self.observed["held"] = True
            if change == "old": self.observed["exerciseSupported"] = False
            with self.assertRaises(EnvironmentError): execute(self.service, self.state, "brake")
            self.assertEqual([], self.calls)

    def test_response_loss_reconciles_terminal_without_restarting(self):
        original = self.rpc
        def lost(source, action, identity):
            value = original(source, action, identity)
            if action == "exercise_tire": raise OSError("response lost")
            return value
        self.service.driver.rpc.side_effect = lost
        with self.assertRaises(OSError): execute(self.service, self.state, "tire")
        self.calls.clear()
        self.service.driver.rpc.side_effect = self.rpc
        result = execute(self.service, self.state, "tire")
        self.assertTrue(result["noOp"])
        self.assertEqual(["status", "wait_SAFE_STOP", "wait_SAFE_STOP", "release"], self.calls)

    def test_release_response_loss_is_read_only_reconciliation(self):
        original = self.rpc
        def lost(source, action, identity):
            value = original(source, action, identity)
            if action == "release": raise OSError("lost")
            return value
        self.service.driver.rpc.side_effect = lost
        with self.assertRaises(OSError): execute(self.service, self.state, "brake")
        self.calls.clear()
        self.service.driver.rpc.side_effect = self.rpc
        self.assertTrue(execute(self.service, self.state, "brake")["noOp"])
        self.assertEqual(["status"], self.calls)
