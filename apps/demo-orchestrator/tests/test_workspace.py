# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
import unittest
import contextlib
import signal
import tempfile
import json
import threading
from pathlib import Path
from unittest.mock import Mock, patch
from aosedge_demo_orchestrator.workspace import WorkspaceService, WorkspaceRecovery, geometry, window, applescript, launch_terminal, close_terminal
from aosedge_demo_orchestrator.environment import EnvironmentError, JOURNAL, atomic_json
from aosedge_demo_orchestrator.presenter_operations import public_result, operation_plan
from uuid import uuid4
from aosedge_demo_orchestrator.cli import build_parser, request_from_arguments
from aosedge_demo_orchestrator.api import execute_operation

class WorkspaceTests(unittest.TestCase):
    def layout_fixture(self, root):
        environment = Mock(root=Path(root))
        environment._writer.side_effect = contextlib.nullcontext
        driver = Mock()
        driver.live_process.side_effect = lambda command: 10 if command == ["/carla"] else 30
        driver.vm._processes.return_value = [(20, "/keyboard /control/run")]
        service = WorkspaceService(environment, driver)
        service.ordering = Mock(return_value=dict(state="VERIFIED"))
        service.directory.mkdir(parents=True)
        service.binary.touch()
        state = dict(source=dict(runId="run", nativeTelemetry=True, simulatorCommand=["/carla"],
            runnerCommand=["/runner", "--keyboard-ui", "/keyboard"], controlDirectory="/control/run"),
            workspace=dict(profile="builtin-v1", presenterBuild=service.binary.stat().st_mtime_ns))
        (Path(root) / JOURNAL).parent.mkdir(parents=True)
        atomic_json(Path(root) / JOURNAL, state)
        return service, driver

    def test_locked_then_unlock_recovers_exact_owners_without_lifecycle(self):
        with tempfile.TemporaryDirectory() as folder:
            service, driver = self.layout_fixture(folder)
            screen = dict(x=0, y=39, width=2056, height=1224, desktopState="LOCKED")
            desired = geometry(screen, combined=True)
            def observe(pid, rectangle=None, title=None):
                return rectangle or desired[{"Demo Presenter — Header": "header", "Demo Presenter — Platform": "browser", "Demo Presenter — Background": "backdrop"}[title]]
            with patch.object(service, "build"), patch("aosedge_demo_orchestrator.workspace.subprocess.run") as probe, patch("aosedge_demo_orchestrator.workspace.window", side_effect=observe) as move, patch("aosedge_demo_orchestrator.workspace.os.kill") as kill:
                probe.return_value = Mock(returncode=0, stdout=json.dumps(screen))
                self.assertEqual("WAITING_FOR_UNLOCK", service.execute("restore")["state"])
                move.assert_not_called(); kill.assert_not_called()
                before = (Path(folder) / JOURNAL).read_bytes()
                service.execute("restore", recovery=True)
                self.assertEqual(before, (Path(folder) / JOURNAL).read_bytes())
                probe.return_value.stdout = json.dumps(dict(screen, desktopState="UNLOCKED"))
                result = service.execute("restore", recovery=True)
                self.assertEqual("PLACED_AWAITING_VISUAL_REVIEW", result["state"])
                self.assertFalse(result["retryPending"])
                self.assertEqual([10, 20], [call.args[0] for call in move.call_args_list if len(call.args) > 1 and call.args[1]])
                kill.assert_called_once_with(30, signal.SIGUSR1)
                count = move.call_count
                service.execute("restore", recovery=True)
                self.assertEqual(count, move.call_count)
                service.execute("restore")  # Explicit idempotent repeat reuses all owners.
                self.assertEqual(2, kill.call_count)
            driver.start.assert_not_called(); driver.stop.assert_not_called(); driver.vm.execute.assert_not_called()

    def test_readiness_retry_is_bounded_and_permission_or_ambiguity_is_terminal(self):
        for failure, retry in (("WORKSPACE_WINDOW_COUNT:0", True), ("WORKSPACE_ACCESSIBILITY_REQUIRED", False), ("WORKSPACE_WINDOW_COUNT:2", False)):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as folder:
                service, _ = self.layout_fixture(folder)
                screen = dict(x=0, y=39, width=2056, height=1224, desktopState="UNLOCKED")
                with patch.object(service, "build"), patch("aosedge_demo_orchestrator.workspace.subprocess.run", return_value=Mock(returncode=0, stdout=json.dumps(screen))), patch("aosedge_demo_orchestrator.workspace.window", side_effect=EnvironmentError(failure)), patch("aosedge_demo_orchestrator.workspace.os.kill"):
                    result = service.execute("restore")
                    self.assertEqual(retry, result["retryPending"])
                    for _ in range(3):
                        result = service.execute("restore", recovery=True)
                    self.assertFalse(result["retryPending"])
                    self.assertEqual("INCOMPLETE", result["state"])

    def test_unknown_desktop_and_new_run_never_move_old_windows(self):
        with tempfile.TemporaryDirectory() as folder:
            service, _ = self.layout_fixture(folder)
            screen = dict(x=0, y=39, width=2056, height=1224, desktopState="UNKNOWN")
            with patch.object(service, "build"), patch("aosedge_demo_orchestrator.workspace.subprocess.run", return_value=Mock(returncode=0, stdout=json.dumps(screen))), patch("aosedge_demo_orchestrator.workspace.window") as move:
                self.assertFalse(service.execute("restore")["retryPending"])
                state = json.loads((Path(folder) / JOURNAL).read_text())
                state["workspace"]["placement"]["retryPending"] = True
                state["source"]["runId"] = "different"
                atomic_json(Path(folder) / JOURNAL, state)
                self.assertEqual({}, service.execute("restore", recovery=True))
                move.assert_not_called()

    def test_recovery_worker_reserves_only_idle_operations_and_releases_on_error(self):
        service = Mock()
        service.cached.return_value = dict(retryPending=True)
        operations = Mock(lock=threading.RLock(), active="job", uncertain=False, source_recovery_busy=False)
        recovery = WorkspaceRecovery(service, operations)
        recovery.tick(); service.execute.assert_not_called()
        operations.active = None
        service.execute.side_effect = EnvironmentError("CURRENT_RUN_BUSY")
        recovery.tick()
        service.execute.assert_called_once_with("restore", recovery=True)
        self.assertFalse(operations.workspace_busy)
        service.execute.reset_mock()
        operations.source_recovery_busy = True
        recovery.tick()
        service.execute.assert_not_called()

    def test_public_receipt_exposes_placement_but_no_process_paths(self):
        result = public_result(dict(operation="simulation.start", state="COMPLETED", data=dict(state="RUNNING",
            workspace=dict(state="WAITING_FOR_UNLOCK", problems=["WORKSPACE_DESKTOP_LOCKED"], retryPending=True,
                surfaces={"pid": 22}, command="private path"))))
        self.assertEqual("WAITING_FOR_UNLOCK", result["facts"]["workspace"]["state"])
        self.assertNotIn("surfaces", result["facts"]["workspace"])
        self.assertNotIn("command", result["facts"]["workspace"])
        payload = dict(action="workspace-restore", requestId=str(uuid4()), sessionId="session")
        self.assertEqual([dict(domain="workspace", action="restore")], operation_plan(payload)[1])
        with self.assertRaises(ValueError):
            operation_plan(dict(payload, pid=22))

    def test_closed_presenter_does_not_reopen_during_recovery(self):
        with tempfile.TemporaryDirectory() as folder:
            service, driver = self.layout_fixture(folder)
            state = json.loads((Path(folder) / JOURNAL).read_text())
            state["workspace"]["placement"] = dict(runId="run", retryPending=True, attempt=0)
            atomic_json(Path(folder) / JOURNAL, state)
            driver.live_process.return_value = None
            driver.live_process.side_effect = None
            screen = dict(x=0, y=39, width=2056, height=1224, desktopState="UNLOCKED")
            with patch.object(service, "build"), patch("aosedge_demo_orchestrator.workspace.subprocess.run", return_value=Mock(returncode=0, stdout=json.dumps(screen))), patch("aosedge_demo_orchestrator.workspace.subprocess.Popen") as launch, patch("aosedge_demo_orchestrator.workspace.window") as move:
                result = service.execute("restore", recovery=True)
                self.assertFalse(result["retryPending"])
                self.assertEqual(["WORKSPACE_PRESENTER_CLOSED"], result["problems"])
                launch.assert_not_called(); move.assert_not_called()

    def test_window_geometry_must_have_four_valid_fields(self):
        for value in ("1, 2", "1, 2, 0, 10"):
            with patch("aosedge_demo_orchestrator.workspace.applescript", return_value=value), self.assertRaisesRegex(EnvironmentError, "WORKSPACE_GEOMETRY_INVALID"):
                window(123)

    def test_order_evidence_requires_exact_host_generation_and_fresh_time(self):
        with tempfile.TemporaryDirectory() as folder:
            service, _ = self.layout_fixture(folder)
            from aosedge_demo_orchestrator.status import now
            value = dict(state="VERIFIED", generation=9, presenterPid=30, observedAt=now(), repairs=1)
            atomic_json(service.directory / "ordering.json", value)
            self.assertEqual("VERIFIED", WorkspaceService.ordering(service, 9, 30)["state"])
            self.assertEqual("UNAVAILABLE", WorkspaceService.ordering(service, 10, 30)["state"])
            self.assertEqual("UNAVAILABLE", WorkspaceService.ordering(service, 9, 31)["state"])
            value["observedAt"] = "2000-01-01T00:00:00Z"
            atomic_json(service.directory / "ordering.json", value)
            self.assertEqual("UNAVAILABLE", WorkspaceService.ordering(service, 9, 30)["state"])

    def test_bad_z_order_prevents_geometry_only_success_and_does_not_expose_pid(self):
        with tempfile.TemporaryDirectory() as folder:
            service, _ = self.layout_fixture(folder)
            state = json.loads((Path(folder) / JOURNAL).read_text())
            service.record(state, dict(state="PLACED_AWAITING_VISUAL_REVIEW", problems=[],
                orderingGeneration=9, hostPid=30), 0, False)
            service.ordering.return_value = dict(state="BACKGROUND_ABOVE_DEMO")
            cached = service.cached()
            self.assertEqual("INCOMPLETE", cached["state"])
            self.assertNotIn("hostPid", cached)
            service.ordering.return_value = dict(state="VERIFIED")
            self.assertEqual("PLACED_AWAITING_VISUAL_REVIEW", service.cached()["state"])

    def test_native_order_guard_never_raises_or_activates_peer_apps(self):
        source = (Path(__file__).parents[1] / "src/aosedge_demo_orchestrator/native/PresenterWorkspace.swift").read_text()
        guard = source[source.index("    func orderObservation()"):source.index("    func userContentController(")]
        self.assertIn("backgroundOrder(numbers", guard)
        self.assertIn("orderObservation()", guard)
        self.assertIn("orderRepairAttempts < 3", guard)
        self.assertNotIn("NSApp.activate", guard)
        self.assertNotIn("AXRaise", guard)
        self.assertNotIn("orderFront", guard)
        self.assertIn("background.ignoresMouseEvents = true", source)
        self.assertNotIn("TRANSIENT T10 PROOF", source)
        self.assertNotIn("orderFrontRegardless", source)

    def test_combined_control_and_telemetry_keep_the_carla_column(self):
        layout = geometry(dict(x=0, y=39, width=2056, height=1224), combined=True)
        self.assertEqual([8, 753, 914, 502], layout["controller"])
        self.assertNotIn("dashboard", layout)
        self.assertEqual(layout["controller"][2], layout["carla"][2])

    def test_close_owns_only_presenter_and_repeat_is_noop(self):
        environment = Mock(root=Path("/not-live"))
        environment._writer.side_effect = contextlib.nullcontext
        driver = Mock()
        driver.live_process.side_effect = [123, None, None]
        service = WorkspaceService(environment, driver)
        with patch("aosedge_demo_orchestrator.workspace.os.kill") as kill, patch.object(service, "build") as build:
            self.assertFalse(service.execute("close")["noOp"])
            self.assertTrue(service.execute("close")["noOp"])
            kill.assert_called_once_with(123, signal.SIGTERM)
            build.assert_not_called()
        driver.start.assert_not_called()
        driver.stop.assert_not_called()
        driver.vm.execute.assert_not_called()
    def test_terminal_cleanup_never_closes_an_unowned_or_active_window(self):
        with patch("aosedge_demo_orchestrator.workspace.applescript") as run:
            close_terminal({})
            run.assert_not_called()
            close_terminal(dict(terminalWindowId=123, runId="12345678-run"))
            script = run.call_args.args[0]
            self.assertIn("window id 123", script)
            self.assertIn("Engineering Telematics — 12345678", script)
            self.assertIn("if (count tabs of w) is not 1 then return", script)
            self.assertIn("if busy of selected tab of w then return", script)

    def test_terminal_uses_literal_unicode_and_the_single_existing_runner(self):
        with tempfile.TemporaryDirectory() as folder, patch("aosedge_demo_orchestrator.workspace.applescript", return_value="123") as run:
            self.assertEqual(123, launch_terminal(["/owned/python", "/owned/runner"], Path(folder) / "runner.log", "12345678-run"))
            script = run.call_args.args[0]
            self.assertIn("Engineering Telematics — 12345678", script)
            self.assertNotIn("\\u2014", script)
            self.assertEqual(1, script.count("do script"))
            self.assertNotIn("carla-viss-client", script)

    def test_builtin_layout_is_bounded_and_nonoverlapping(self):
        for width, height in ((2056, 1220), (1728, 1030), (1440, 900)):
            layout = geometry(dict(x=0, y=38, width=width, height=height))
            self.assertEqual([0, 38, width, height], layout["backdrop"])
            rectangles = [r for name, r in layout.items() if name != "backdrop"]
            for x, y, w, h in rectangles:
                self.assertGreaterEqual(x, 0)
                self.assertGreaterEqual(y, 38)
                self.assertLessEqual(x + w, width)
                self.assertLessEqual(y + h, height + 38)
            for i, a in enumerate(rectangles):
                for b in rectangles[i + 1:]:
                    self.assertTrue(a[0]+a[2] <= b[0] or b[0]+b[2] <= a[0] or a[1]+a[3] <= b[1] or b[1]+b[3] <= a[1])
            self.assertGreaterEqual(layout["controller"][2], 360)
            self.assertEqual(layout["carla"][0] + layout["carla"][2],
                             layout["dashboard"][0] + layout["dashboard"][2])
            self.assertEqual(layout["dashboard"][0] + layout["dashboard"][2] + 8,
                             layout["browser"][0])

    def test_compact_builtin_profile_preserves_dashboard_width(self):
        layout = geometry(dict(x=0, y=39, width=2056, height=1224))
        self.assertEqual([8, 131, 914, 614], layout["carla"])
        self.assertEqual([8, 753, 402, 502], layout["controller"])
        self.assertEqual([418, 753, 504, 502], layout["dashboard"])
        self.assertEqual([930, 131, 1118, 1124], layout["browser"])
        self.assertEqual([8, 47, 2040, 76], layout["header"])
        self.assertEqual([0, 39, 2056, 1224], layout["backdrop"])

    def test_backdrop_is_nonactivating_black_and_not_always_on_top(self):
        source = (Path(__file__).parents[1] / "src/aosedge_demo_orchestrator/native/PresenterWorkspace.swift").read_text()
        self.assertIn("background.backgroundColor = .black", source)
        self.assertIn("background.level = .normal", source)
        self.assertIn(".nonactivatingPanel", source)
        self.assertIn("backdrop.order(.below, relativeTo: backmost)", source)
        self.assertNotIn("CGWindowListCreateImage", source)

    def test_too_small_is_explicit_not_unreadable_success(self):
        with self.assertRaises(EnvironmentError):
            geometry(dict(x=0, y=0, width=1024, height=768))

    def test_read_only_window_has_no_mutation(self):
        with patch("aosedge_demo_orchestrator.workspace.applescript", return_value="1, 2, 3, 4") as run:
            self.assertEqual([1, 2, 3, 4], window(123))
            script = run.call_args.args[0]
            self.assertNotIn("set position", script)
            self.assertNotIn("AXRaise", script)
            self.assertIn("unix id is 123", script)
            self.assertIn("return {position, size} of w", script)

    def test_window_target_requires_real_pid_and_unique_owned_window(self):
        with self.assertRaises(EnvironmentError):
            window("UnrealEditor")
        with patch("aosedge_demo_orchestrator.workspace.applescript", return_value="1, 2, 3, 4") as run:
            window(123, [1, 2, 3, 4])
            script = run.call_args.args[0]
            self.assertIn('if (count ws) is not 1', script)
            self.assertLess(script.index("set size of w"), script.index("set position of w"))

    def test_cli_workspace_has_no_vm_target(self):
        for action in ("status", "restore", "close"):
            request = request_from_arguments(build_parser().parse_args(["workspace", action]))
            self.assertEqual("workspace", request.domain)
            self.assertEqual(action, request.action)
            self.assertIsNone(request.target)

    def test_api_rejects_arbitrary_windows_profiles_and_lifecycle_targets(self):
        app = Mock()
        for field in ("target", "pid", "window", "command", "path", "profile"):
            with self.assertRaises(ValueError):
                execute_operation(dict(domain="workspace", action="restore", **{field: "test"}), app)
        app.execute.assert_not_called()

    def test_permissions_failure_does_not_dump_private_script_or_raw_response(self):
        with patch("aosedge_demo_orchestrator.workspace.subprocess.run", return_value=Mock(returncode=1, stderr="osascript is not allowed assistive access")):
            with self.assertRaisesRegex(EnvironmentError, "^WORKSPACE_ACCESSIBILITY_REQUIRED$"):
                applescript("private fixture")
