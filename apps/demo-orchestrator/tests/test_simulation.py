# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import contextlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from aosedge_demo_orchestrator.api import execute_operation
from aosedge_demo_orchestrator.application import DemoOrchestrator
from aosedge_demo_orchestrator.cli import build_parser, request_from_arguments, render_human
from aosedge_demo_orchestrator.environment import EnvironmentError
from aosedge_demo_orchestrator.models import OperationRequest
from aosedge_demo_orchestrator.source import SourceDriver, SourceService
from aosedge_demo_orchestrator import source_guest


class SimulationTests(unittest.TestCase):
    def setUp(self):
        self.vm, self.units, self.driver = Mock(), Mock(), Mock()
        self.vm.root = Path("/not-live")
        self.vm.environment._writer.side_effect = contextlib.nullcontext
        self.driver.operation.side_effect = lambda **kw: contextlib.nullcontext()
        self.service = SourceService(self.vm, self.units, self.driver)
        self.state = dict(currentVehicle="test", vehicles=dict(test={}, production={}),
            source=dict(state="RUNNING", runId="run", assignmentGeneration=2, operation=None,
                        runnerCommand=["runner"], simulatorCommand=["carla"]))
        self.driver.guests.return_value = {r: dict(gate="BLOCKED") for r in self.state["vehicles"]}
        self.driver.live_process.return_value = 123
        self.driver.ready.return_value = dict(fresh=True)
        self.read = patch("aosedge_demo_orchestrator.source.read_json", return_value=self.state)
        self.read.start()
        self.addCleanup(self.read.stop)

    def tearDown(self):
        self.vm.execute.assert_not_called()
        self.units.execute.assert_not_called()
        self.units._cloud.assert_not_called()

    def test_ready_start_noop_preserves_selection(self):
        result = self.service.simulation("start")
        self.assertTrue(result["noOp"])
        self.assertEqual("test", result["currentVehicle"])
        self.driver.start.assert_not_called()
        self.driver.guests.assert_not_called()
        self.vm._save.assert_not_called()

    def test_terminal_started_session_is_observed_without_relaunch(self):
        self.state["source"]["state"] = "STARTING"
        result = self.service.simulation("start")
        self.assertTrue(result["noOp"])
        self.driver.finish_start.assert_called_once_with(self.state)
        self.driver.start.assert_not_called()
        self.driver.guests.assert_not_called()

    def test_start_blocks_before_launch_and_does_not_attach(self):
        self.state.update(source=None, currentVehicle=None)
        self.driver.start.return_value = dict(runId="new")
        order = []
        self.driver.guests.side_effect = lambda *a: order.append("block") or {"test": dict(gate="BLOCKED")}
        self.driver.start.side_effect = lambda *a: order.append("start") or dict(runId="new")
        result = self.service.simulation("start")
        self.assertEqual(["block", "start"], order)
        self.assertIsNone(result["currentVehicle"])

    def test_stop_orders_safe_stop_detach_shutdown_and_repeats_noop(self):
        order = []
        self.driver.rpc.side_effect = lambda *a: order.append("safe_stop")
        self.driver.wait.side_effect = lambda *a: order.append("confirmed")
        self.driver.guests.side_effect = lambda *a: order.append("detach") or {"test": dict(gate="BLOCKED")}
        self.driver.stop.side_effect = lambda *a: order.append("shutdown")
        result = self.service.simulation("stop")
        self.assertEqual(["safe_stop", "confirmed", "detach", "shutdown"], order)
        self.assertEqual("CONFIRMED", result["physicalStop"])
        self.assertIsNone(self.state["currentVehicle"])
        self.assertEqual(2, self.state["source"]["assignmentGeneration"])
        self.driver.live_process.return_value = None
        self.assertTrue(self.service.simulation("stop")["noOp"])
        self.assertEqual(4, len(order))

    def test_stop_does_not_hide_missing_physical_evidence(self):
        self.driver.live_process.return_value = None
        result = self.service.simulation("stop")
        self.assertEqual("NOT_OBSERVED", result["physicalStop"])
        self.driver.rpc.assert_not_called()
        self.driver.stop.assert_called_once()

    def test_test_scoped_stop_never_changes_production_gate(self):
        self.assertEqual("STOPPED", self.service.simulation("stop", target="test")["state"])
        self.driver.guests.assert_any_call(self.state, "status")
        self.driver.guests.assert_any_call(self.state, "block", roles=["test"])
        self.assertNotIn(unittest.mock.call(self.state, "block"), self.driver.guests.call_args_list)

    def test_test_scoped_stop_cannot_stop_selected_production(self):
        self.state["currentVehicle"] = "production"
        with self.assertRaisesRegex(EnvironmentError, "TEST_SCOPE_CONFLICT"):
            self.service.simulation("stop", target="test")
        self.driver.rpc.assert_not_called()
        self.driver.guests.assert_not_called()
        self.driver.stop.assert_not_called()

    def test_test_scoped_start_does_not_repair_an_open_preserved_peer(self):
        self.state.update(source=None, currentVehicle=None)
        self.driver.guests.return_value["production"]["gate"] = "OPEN"
        with self.assertRaisesRegex(EnvironmentError, "PRESERVED_PEER_NOT_DETACHED"):
            self.service.simulation("start", target="test")
        self.driver.guests.assert_called_once_with(self.state, "status")
        self.driver.start.assert_not_called()

    def test_stop_cancels_owned_initialization_only_after_actual_safe_stop(self):
        self.state["currentVehicle"] = None
        self.state["source"].update(assignmentGeneration=0,
            operation=dict(id="initial", initialManual=True, phase="DETACHED"))
        self.driver.rpc.return_value = dict(operationId="initial", held=True, fresh=True,
            frame=dict(activeMode="SAFE_STOP", speedKmh=0, brake=1))
        self.assertEqual("STOPPED", self.service.simulation("stop")["state"])
        self.driver.rpc.assert_called_once_with(self.state["source"], "status", "initial")
        self.driver.guests.assert_called_once_with(self.state, "block")
        self.driver.stop.assert_called_once()
        self.assertIsNone(self.state["source"]["operation"])

    def test_initialization_cancel_rejects_unknown_moving_or_other_owner(self):
        self.state["currentVehicle"] = None
        self.state["source"].update(assignmentGeneration=0,
            operation=dict(id="initial", initialManual=True, phase="DETACHED"))
        safe = dict(operationId="initial", held=True, fresh=True,
            frame=dict(activeMode="SAFE_STOP", speedKmh=0, brake=1))
        for change in (dict(fresh=False), dict(held=False), dict(operationId="other"),
                       dict(frame=dict(activeMode="MANUAL", speedKmh=0, brake=1)),
                       dict(frame=dict(activeMode="SAFE_STOP", speedKmh=10, brake=1))):
            self.driver.rpc.return_value = dict(safe, **change)
            with self.assertRaisesRegex(EnvironmentError, "CANCEL_REQUIRES_SAFE_STOP"):
                self.service.simulation("stop")
        self.driver.guests.assert_not_called()
        self.driver.stop.assert_not_called()

    def test_partial_start_without_controller_can_be_stopped(self):
        self.state["source"].update(state="STARTING", controlDirectory="control")
        self.state["currentVehicle"] = None
        self.assertEqual("NOT_OBSERVED", self.service.simulation("stop")["physicalStop"])
        self.driver.rpc.assert_not_called()
        self.driver.stop.assert_called_once()

    def test_start_does_not_change_gates_of_an_expired_session(self):
        self.driver.live_process.return_value = None
        with self.assertRaisesRegex(EnvironmentError, "SIMULATION_NOT_READY"):
            self.service.simulation("start")
        self.driver.guests.assert_not_called()
        self.driver.start.assert_not_called()

    def test_start_with_pending_operation_is_not_ready_noop(self):
        self.state["source"]["operation"] = dict(id="pending")
        with self.assertRaisesRegex(EnvironmentError, "RECONCILIATION"):
            self.service.simulation("start")
        self.driver.guests.assert_not_called()

    def test_failed_detach_does_not_shutdown(self):
        self.driver.guests.return_value = dict(test=dict(gate="UNKNOWN"))
        with self.assertRaisesRegex(EnvironmentError, "DETACH_NOT_CONFIRMED"):
            self.service.simulation("stop")
        self.driver.stop.assert_not_called()
        self.assertIsNotNone(self.state["source"]["stopOperation"])

    def test_resume_stop_after_detach_does_not_repeat_physical_stop(self):
        self.state["source"].update(state="STOPPING", stopOperation=dict(id="op", phase="DETACHED", physicalStop="CONFIRMED"))
        self.state["currentVehicle"] = None
        self.assertEqual("STOPPED", self.service.simulation("stop")["state"])
        self.driver.rpc.assert_not_called()
        self.driver.guests.assert_not_called()

    def test_select_fails_before_guest_cloud_or_vm_checks(self):
        for code in ("SIMULATION_NOT_RUNNING", "SIMULATION_NOT_READY"):
            self.driver.ready.side_effect = EnvironmentError(code)
            with self.assertRaisesRegex(EnvironmentError, code):
                self.service.select("test")
        self.driver.guests.assert_not_called()
        self.vm._validate.assert_not_called()
        self.vm._save.assert_not_called()

    def test_fast_status_does_not_call_guest_and_marks_historical_confirmation(self):
        self.state["source"]["lastConnectionConfirmation"] = dict(role="test", confirmedAt="old")
        value = self.service.observe(timeout=.5)
        self.assertEqual("SELECTED_NOT_PROBED", value["state"])
        self.assertNotIn("currentVehicle", value)
        self.assertEqual("old", value["lastConnectionConfirmation"]["confirmedAt"])
        self.driver.guests.assert_not_called()
        self.driver.guest.assert_not_called()
        self.vm._save.assert_not_called()
        self.driver.operation.assert_called_once_with(timeout=.5)

    def test_live_status_combines_guest_read_and_connection(self):
        self.driver.guests.return_value = dict(test=dict(gate="OPEN", connection=dict(serverTls=True)),
                                               production=dict(gate="BLOCKED"))
        value = self.service.observe(guest=True)
        self.assertEqual("CONNECTED", value["state"])
        self.driver.guests.assert_called_once_with(self.state, "observe")
        self.driver.guest.assert_not_called()

    def test_cli_and_api_share_simulation_operation_and_reject_capabilities(self):
        app = DemoOrchestrator(vm_service=self.vm, unit_service=self.units, source_service=self.service)
        request = request_from_arguments(build_parser().parse_args(["simulation", "start"]))
        self.assertEqual("simulation", request.domain)
        result = app.execute(request)
        self.assertIn("Simulation: RUNNING (unchanged)", render_human(result))
        self.assertEqual("COMPLETED", execute_operation(dict(domain="simulation", action="start"), app)["state"])
        for field in ("target", "command", "force", "credential", "socket"):
            with self.assertRaises(ValueError):
                execute_operation(dict(domain="simulation", action="start", **{field: "test"}), app)


class SourceTransportTests(unittest.TestCase):
    def test_terminal_exec_is_allowed_to_appear_after_acknowledgment(self):
        driver = SourceDriver(Mock(root=Path("/not-live")))
        state = dict(source=dict(runnerCommand=["owned-runner"], runDirectory="run", state="STARTING"))
        driver.live_process = Mock(side_effect=[None, 123])
        driver.rpc = Mock(return_value=dict(fresh=True))
        with patch("aosedge_demo_orchestrator.source.time.sleep") as sleep, patch(
                "aosedge_demo_orchestrator.source.read_json", return_value=dict(stages=[dict(stage="keyboard_ready")])):
            driver.finish_start(state)
        self.assertEqual("RUNNING", state["source"]["state"])
        sleep.assert_called_once_with(.1)
        driver.vm._save.assert_called_once_with(state)

    def test_observed_runner_exit_is_not_retried(self):
        driver = SourceDriver(Mock(root=Path("/not-live")))
        state = dict(source=dict(runnerCommand=["owned-runner"], runDirectory="run", state="STARTING"))
        driver.live_process = Mock(side_effect=[123, None])
        driver.rpc = Mock(side_effect=OSError("not ready"))
        with patch("aosedge_demo_orchestrator.source.time.sleep"), self.assertRaisesRegex(EnvironmentError, "SOURCE_RUNNER_EXITED"):
            driver.finish_start(state)

    def test_ssh_reused_within_operation_and_closed_afterwards(self):
        vm = Mock(root=Path("/not-live"))
        driver = SourceDriver(vm)
        state = dict(vehicles=dict(test=dict(sshPort=10022)))
        commands = []
        def run(command, **kw):
            commands.append(command)
            return subprocess.CompletedProcess(command, 0, json.dumps(dict(ok=True, data={})), "")
        with patch("aosedge_demo_orchestrator.source.subprocess.run", side_effect=run):
            with driver.operation():
                driver.guest(state, "test", "status")
                driver.guest(state, "test", "probe")
                path = driver._session
                self.assertEqual(0o700, path.stat().st_mode & 0o777)
            self.assertFalse(path.exists())
        self.assertEqual(commands[0], commands[1])
        self.assertIn("ControlMaster=auto", commands[0])
        self.assertIn("StrictHostKeyChecking=yes", commands[0])
        self.assertIn("ControlPersist=10", commands[0])
        self.assertEqual(["-O", "exit", "root@127.0.0.1"], commands[-1][-3:])

    def test_expired_source_deadline_does_not_spawn_ssh(self):
        driver = SourceDriver(Mock(root=Path("/not-live")))
        driver._deadline = 0
        with patch("aosedge_demo_orchestrator.source.subprocess.run") as run:
            with self.assertRaisesRegex(EnvironmentError, "SOURCE_READ_TIMEOUT"):
                driver.guest(dict(vehicles=dict(test=dict(sshPort=10022))), "test", "status")
            run.assert_not_called()

    def test_guest_probe_only_for_selected_open_path(self):
        request = dict(action="observe", vehicle=dict(localVmId="id", sourceProbeSelected=False))
        with patch.object(source_guest, "command", return_value=Mock(stdout="ActiveState=inactive\n")), \
             patch.object(source_guest, "gate_state", return_value="BLOCKED"), \
             patch.object(source_guest, "probe") as probe:
            self.assertEqual("BLOCKED", source_guest.execute(request)["gate"])
            probe.assert_not_called()


if __name__ == "__main__":
    unittest.main()
