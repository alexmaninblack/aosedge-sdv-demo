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

    def recovery_driver(self):
        self.observed["roadRecoverySupported"]=True
        original=self.rpc
        def rpc(source,action,identity):
            result=original(source,action,identity)
            if action=="manual_ready":self.observed["phase"]="MANUAL_PREPARING"
            if action=="release_manual":self.observed.update(phase="RELEASED",held=False)
            return dict(self.observed)
        self.service.driver.rpc.side_effect=rpc
        original_wait=self.wait
        def wait(source,identity,phase):
            original_wait(source,identity,phase)
            self.observed["frame"].update(roadReady=True,activeMode="MANUAL" if phase=="MANUAL_READY" else "SAFE_STOP")
            return dict(self.observed)
        self.service.driver.wait.side_effect=wait
        return rpc

    def test_return_to_road_finishes_stationary_manual_without_autopilot_or_reset_model(self):
        self.recovery_driver()
        request=request_from_arguments(build_parser().parse_args(["simulation","return-to-road","--target","test"]))
        self.assertEqual("return-to-road",request.action)
        result=execute(self.service,self.state,"return_to_road")
        self.assertEqual("COMPLETED",result["state"])
        self.assertEqual("MANUAL",result["driveMode"])
        self.assertFalse(result["autopilotStarted"])
        self.assertEqual(1,self.calls.count("reset"))
        self.assertIn("release_manual",self.calls)
        self.assertFalse(any(call.startswith("exercise_") for call in self.calls))
        self.service.driver.guest.assert_not_called()

    def test_return_to_road_requires_confirmed_placement_not_only_stopped(self):
        self.recovery_driver()
        original=self.service.driver.wait.side_effect
        def wait(*args):
            result=original(*args);self.observed["frame"]["roadReady"]=False;return result
        self.service.driver.wait.side_effect=wait
        with self.assertRaisesRegex(EnvironmentError,"RESET_NOT_SETTLED"):
            execute(self.service,self.state,"return_to_road")
        self.assertNotIn("manual_ready",self.calls)

    def test_recovery_response_loss_reconciles_manual_without_repeated_reset(self):
        original=self.recovery_driver()
        def lost(source,action,identity):
            result=original(source,action,identity)
            if action=="release_manual":raise OSError("lost")
            return result
        self.service.driver.rpc.side_effect=lost
        with self.assertRaises(OSError):execute(self.service,self.state,"return_to_road")
        self.calls.clear();self.service.driver.rpc.side_effect=original
        self.assertEqual("COMPLETED",execute(self.service,self.state,"return_to_road")["state"])
        self.assertEqual(["status"],self.calls)

    def test_blocked_placement_release_loss_never_becomes_recovery_success(self):
        original=self.recovery_driver()
        previous_wait=self.service.driver.wait.side_effect
        def wait(source,identity,phase):
            result=previous_wait(source,identity,phase)
            if phase=="RESET":self.observed.update(phase="RESET_FAILED",resetError="ROAD_POSITION_OCCUPIED")
            return dict(self.observed)
        self.service.driver.wait.side_effect=wait
        def lost(source,action,identity):
            result=original(source,action,identity)
            if action=="release":raise OSError("lost")
            return result
        self.service.driver.rpc.side_effect=lost
        with self.assertRaises(OSError):execute(self.service,self.state,"return_to_road")
        self.calls.clear();self.service.driver.rpc.side_effect=original
        result=execute(self.service,self.state,"return_to_road")
        self.assertEqual(("FAILED","ROAD_POSITION_OCCUPIED"),(result["state"],result["reason"]))
        self.assertEqual(["status"],self.calls)

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
