# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
import unittest
import contextlib
import signal
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from aosedge_demo_orchestrator.workspace import WorkspaceService, geometry, window, applescript, launch_terminal, close_terminal
from aosedge_demo_orchestrator.environment import EnvironmentError
from aosedge_demo_orchestrator.cli import build_parser, request_from_arguments
from aosedge_demo_orchestrator.api import execute_operation

class WorkspaceTests(unittest.TestCase):
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
