# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from aosedge_demo_orchestrator.backends import BackendService
from aosedge_demo_orchestrator.environment import EnvironmentService, EnvironmentError, JOURNAL, atomic_json
from aosedge_demo_orchestrator.api import execute_operation
from aosedge_demo_orchestrator.cli import build_parser, request_from_arguments

OWNER = "11111111-1111-4111-8111-111111111111"
IMAGE = "sha256:" + "a" * 64


class BackendTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.environment = EnvironmentService(self.root, catalog=SimpleNamespace(project=self.root / "catalog"))
        self.environment._directory(".run/demo-current")
        self.state = dict(kind="democtl.current-run", vehicles=dict(test={}), operations=[dict(id=OWNER, **{"class": "LOCAL_CREATE"}, state="COMPLETED")])
        atomic_json(self.root / JOURNAL, self.state)
        self.service = BackendService(self.environment)
        self.container = None
        self.commands = []
        self.service._candidate = Mock(return_value=dict(imageId=IMAGE, sourceRevision="source"))
        self.service._image = Mock()
        self.service._inspect = lambda kind, name: self.container if kind == "container" else None
        def docker(*args, **kwargs):
            self.commands.append(args)
            if "up" in args:
                self.container = dict(Image=IMAGE, Config=dict(Labels={"tech.aosedge.demo.owner": OWNER, "tech.aosedge.demo.team": "brake"}),
                    State=dict(Running=True, Health=dict(Status="healthy")))
            if "stop" in args:
                self.container["State"]["Running"] = False
        self.service._docker = docker

    def test_context_handle_status_exposes_only_fixed_class_and_pid(self):
        path = self.root / ".run/demo-current/backends/context/current-unit-context.json"
        path.parent.mkdir(parents=True)
        path.write_text("{}")
        response = SimpleNamespace(returncode=0, stderr="", stdout="p123\nccom.apple.Virtualization.VirtualMachine\n")
        with patch("aosedge_demo_orchestrator.backends.shutil.which", return_value="/fixed/lsof"), patch(
                "aosedge_demo_orchestrator.backends.subprocess.run", return_value=response):
            self.assertEqual(dict(state="HELD", owners=[dict(pid=123, processClass="VIRTUAL_MACHINE")]),
                self.service._context_handles())
            response.stderr = "visibility denied"
            self.assertEqual(dict(state="UNKNOWN", owners=[]), self.service._context_handles())

    def test_recovery_never_restarts_engine_with_unrelated_running_container(self):
        self.state.update(demoLifecycle=dict(action="retire", state="PARTIAL", reason="CLEANUP_FILE_IN_USE",
            phase="retire-test-data-and-overlay"), backends={team: dict(state="STOPPED", cleanup=dict(containerRemoval="REMOVED"))
                for team in ("brake", "tire")})
        atomic_json(self.root / JOURNAL, self.state)
        self.service._context_handles = Mock(return_value=dict(state="HELD", owners=[dict(pid=123, processClass="VIRTUAL_MACHINE")]))
        self.service._docker = Mock(return_value="unrelated-id\n")
        self.service._run = Mock(return_value="p123\n")
        with patch("aosedge_demo_orchestrator.backends.sys.platform", "darwin"), patch.object(Path, "is_file", return_value=True), patch(
                "aosedge_demo_orchestrator.backends.shutil.which", return_value="/fixed/lsof"):
            with self.assertRaisesRegex(EnvironmentError, "OTHER_CONTAINER_RUNNING"):
                self.service.recover_file_sharing()
        self.assertEqual([(("container", "ls", "--quiet"),)], [tuple([call.args]) for call in self.service._docker.call_args_list])

    def test_recovery_restart_once_then_clear_and_repeat_is_read_only(self):
        self.state.update(demoLifecycle=dict(action="retire", state="PARTIAL", reason="CLEANUP_FILE_IN_USE",
            phase="retire-test-data-and-overlay"), backends={team: dict(state="STOPPED", cleanup=dict(containerRemoval="REMOVED"))
                for team in ("brake", "tire")})
        atomic_json(self.root / JOURNAL, self.state)
        held = dict(state="HELD", owners=[dict(pid=123, processClass="VIRTUAL_MACHINE")])
        self.service._context_handles = Mock(side_effect=[held, dict(state="CLEAR", owners=[]), dict(state="CLEAR", owners=[])])
        self.service._docker = Mock(return_value="")
        self.service._run = Mock(side_effect=["p123\n", "/usr/bin/python\n"])
        with patch("aosedge_demo_orchestrator.backends.sys.platform", "darwin"), patch.object(Path, "is_file", return_value=True), patch(
                "aosedge_demo_orchestrator.backends.shutil.which", return_value="/fixed/lsof"):
            self.assertEqual("COMPLETED", self.service.recover_file_sharing()["state"])
            self.assertTrue(self.service.recover_file_sharing()["noOp"])
        self.assertEqual(1, sum(call.args[:2] == ("desktop", "restart") for call in self.service._docker.call_args_list))

    def test_start_is_digest_pinned_loopback_only_no_build_or_pull(self):
        result = self.service.execute("start", "brake")
        self.assertEqual("RUNNING", result["state"])
        args = self.commands[0]
        self.assertIn("--no-build", args)
        self.assertEqual("never", args[args.index("--pull") + 1])
        path = self.root / ".run/demo-current/backends/brake-compose.json"
        spec = json.loads(path.read_text())
        service = spec["services"]["brake"]
        self.assertEqual(IMAGE, service["image"])
        self.assertEqual(["127.0.0.1:18091:18091"], service["ports"])
        self.assertTrue(service["volumes"][1]["read_only"])
        self.assertTrue(service["volumes"][1]["source"].endswith("/backends/context"))
        self.assertNotIn("environment", service)
        self.commands.clear()
        self.assertTrue(self.service.execute("start", "brake")["noOp"])
        self.assertEqual([], self.commands)

    def test_stop_retains_volume_and_stopped_repeat_is_noop(self):
        self.service.execute("start", "brake")
        self.commands.clear()
        self.assertTrue(self.service.execute("stop", "brake")["dataPreserved"])
        self.assertEqual("stop", self.commands[0][3])
        self.assertNotIn("down", self.commands[0])
        self.commands.clear()
        self.assertTrue(self.service.execute("stop", "brake")["noOp"])
        self.assertEqual([], self.commands)

    def test_foreign_container_is_neither_adopted_nor_stopped(self):
        self.container = dict(Config=dict(Labels={}), State=dict(Running=True))
        for action in ("start", "stop", "status"):
            with self.assertRaisesRegex(EnvironmentError, "FOREIGN_CONTAINER"):
                self.service.execute(action, "brake")
        self.assertEqual([], self.commands)

    def test_changed_container_identity_cannot_confirm_start_success(self):
        original = self.service._docker
        def changed(*args, **kwargs):
            original(*args, **kwargs)
            self.container["Config"]["Labels"]["tech.aosedge.demo.owner"] = "other"
        self.service._docker = changed
        with self.assertRaisesRegex(EnvironmentError, "FOREIGN_CONTAINER"):
            self.service.execute("start", "brake")
        journal = json.loads((self.root / JOURNAL).read_text())
        self.assertEqual("UNCERTAIN", journal["backends"]["brake"]["state"])

    def test_other_team_storage_is_not_reused_even_with_same_run_owner(self):
        self.service._inspect = lambda kind, name: dict(Labels={"tech.aosedge.demo.owner": OWNER,
            "tech.aosedge.demo.team": "tire"}) if kind == "volume" else None
        with self.assertRaisesRegex(EnvironmentError, "FOREIGN_VOLUME"):
            self.service.execute("start", "brake")
        self.assertEqual([], self.commands)

    def test_unrecorded_compose_file_is_not_overwritten(self):
        directory = self.environment._directory(".run/demo-current/backends")
        path = directory / "brake-compose.json"
        path.write_text("untracked")
        with self.assertRaisesRegex(EnvironmentError, "COMPOSE_RECONCILIATION_REQUIRED"):
            self.service.execute("start", "brake")
        self.assertEqual("untracked", path.read_text())
        self.assertEqual([], self.commands)

    def test_lost_start_reply_is_reconciled_by_observation_not_second_start(self):
        normal = self.service._docker
        def lost(*args, **kwargs):
            normal(*args, **kwargs)
            raise EnvironmentError("BACKEND_COMMAND_UNAVAILABLE_OR_UNCERTAIN")
        self.service._docker = lost
        with self.assertRaises(EnvironmentError):
            self.service.execute("start", "brake")
        self.assertEqual(1, len(self.commands))
        self.service._docker = normal
        self.assertTrue(self.service.execute("start", "brake")["noOp"])
        self.assertEqual(1, len(self.commands))

    def test_tire_has_separate_identity_network_volume_and_namespace(self):
        spec = self.service._spec(self.state, "tire", IMAGE)
        service = spec["services"]["tire"]
        self.assertEqual(["127.0.0.1:18092:18092"], service["ports"])
        self.assertIn("/data/tire-health.sqlite", service["command"])
        self.assertEqual(["aosedge_demo_tire_cloud_v1"], list(spec["volumes"]))
        self.assertEqual(["aosedge-demo-tire-cloud-v1"], list(spec["networks"]))

    def test_cli_and_api_are_fixed_team_only_build_is_not_browser_action(self):
        request = request_from_arguments(build_parser().parse_args(["backend", "start", "brake"]))
        self.assertEqual("brake", request.team)
        app = Mock()
        execute_operation(dict(domain="backend", action="status", team="tire"), app)
        self.assertEqual("tire", app.execute.call_args.args[0].team)
        for payload in (dict(domain="backend", action="build", team="brake"),
                        dict(domain="backend", action="start", team="brake", image="arbitrary")):
            with self.assertRaises(ValueError):
                execute_operation(payload, app)

    def test_unavailable_engine_is_not_absence_and_raw_error_is_never_public(self):
        with patch("aosedge_demo_orchestrator.backends.subprocess.run", return_value=SimpleNamespace(
                returncode=1, stdout="", stderr="Cannot connect to the Docker daemon at unix:///private/socket?token=secret")):
            with self.assertRaisesRegex(EnvironmentError, "^BACKEND_DOCKER_ENGINE_UNAVAILABLE$"):
                self.service._run(["docker", "container", "ls"])

    def stack_execute(self, before=None, fail=None):
        before = before or {}
        calls = []
        def execute(action, team):
            calls.append((action, team))
            if (action, team) == fail:
                raise EnvironmentError("TEST_FAILURE")
            return dict(state=(before.get(team, "STOPPED") if action == "status" else
                "RUNNING" if action == "start" else "STOPPED"))
        self.service.execute = execute
        return calls

    def test_stack_preflights_both_images_before_any_start(self):
        calls = self.stack_execute()
        self.service._candidate.side_effect = [dict(imageId=IMAGE), EnvironmentError("MISSING_TIRE")]
        with self.assertRaisesRegex(EnvironmentError, "MISSING_TIRE"):
            self.service.start_stack()
        self.assertEqual([("status", "brake"), ("status", "tire")], calls)

    def test_partial_stack_start_stops_only_newly_attempted_teams(self):
        calls = self.stack_execute(before=dict(brake="RUNNING"), fail=("start", "tire"))
        result = self.service.start_stack()
        self.assertEqual("PARTIAL", result["state"])
        self.assertEqual({"tire"}, set(result["partialStartupCleanup"]))
        self.assertNotIn(("stop", "brake"), calls)
        self.assertEqual(("stop", "tire"), calls[-1])

    def test_partial_new_stack_start_stops_both_in_reverse_order(self):
        calls = self.stack_execute(fail=("start", "tire"))
        self.assertEqual("PARTIAL", self.service.start_stack()["state"])
        self.assertEqual([("stop", "tire"), ("stop", "brake")], calls[-2:])

    def test_stack_start_success_preserves_both_data_stores(self):
        calls = self.stack_execute()
        result = self.service.start_stack()
        self.assertEqual("RUNNING", result["state"])
        self.assertTrue(result["dataPreserved"])
        self.assertEqual([("start", "brake"), ("start", "tire")], calls[-2:])

    def test_stack_stop_reports_partial_and_continues_after_one_failure(self):
        calls = self.stack_execute(fail=("stop", "tire"))
        result = self.service.stop_stack()
        self.assertEqual("PARTIAL", result["state"])
        self.assertEqual("UNKNOWN", result["teams"]["tire"]["state"])
        self.assertEqual([("stop", "tire"), ("stop", "brake")], calls)
        self.assertTrue(result["dataPreserved"])

    def test_new_build_does_not_change_the_image_on_normal_start_or_resume(self):
        self.service.execute("start", "brake")
        self.service.execute("stop", "brake")
        self.service._candidate.return_value = dict(imageId="sha256:" + "b" * 64, sourceRevision="new")
        self.service.execute("start", "brake")
        journal = json.loads((self.root / JOURNAL).read_text())
        self.assertEqual(IMAGE, journal["backends"]["brake"]["imageId"])

    def test_activation_refuses_running_container_before_any_mutation(self):
        self.service.execute("start", "brake")
        self.commands.clear()
        self.service._candidate.return_value = dict(imageId="sha256:" + "b" * 64, sourceRevision="new")
        with self.assertRaisesRegex(EnvironmentError, "OWNED_STOPPED"):
            self.service.execute("activate", "brake")
        self.assertEqual([], self.commands)

    def test_stopped_activation_reconciles_lost_removal_without_deleting_data(self):
        self.service.execute("start", "brake")
        self.service.execute("stop", "brake")
        self.commands.clear()
        replacement = "sha256:" + "b" * 64
        self.service._candidate.return_value = dict(imageId=replacement, sourceRevision="new")
        def lost_removal(*args, **kwargs):
            self.commands.append(args)
            self.container = None
            raise EnvironmentError("LOST_REPLY")
        self.service._docker = lost_removal
        with self.assertRaisesRegex(EnvironmentError, "LOST_REPLY"):
            self.service.execute("activate", "brake")
        self.assertEqual([("container", "rm", "aosedge-demo-brake-cloud")], self.commands)
        self.assertEqual("UNCERTAIN", json.loads((self.root / JOURNAL).read_text())["backends"]["brake"]["state"])
        result = self.service.execute("activate", "brake")
        self.assertEqual("STOPPED", result["state"])
        self.assertEqual(1, len(self.commands))
        self.assertEqual(replacement, json.loads((self.root / JOURNAL).read_text())["backends"]["brake"]["imageId"])
        self.assertTrue(self.service.execute("activate", "brake")["noOp"])

    def test_activation_is_cli_only(self):
        request = request_from_arguments(build_parser().parse_args(["backend", "activate", "brake"]))
        self.assertEqual("activate", request.action)
        with self.assertRaises(ValueError):
            execute_operation(dict(domain="backend", action="activate", team="brake"), Mock())
