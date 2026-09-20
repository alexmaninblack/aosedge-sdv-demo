# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
import json
import tempfile
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import ANY, Mock, patch

from aosedge_demo_orchestrator.backends import BackendService
from aosedge_demo_orchestrator.environment import EnvironmentService, EnvironmentError, JOURNAL, atomic_json
from aosedge_demo_orchestrator.api import execute_operation
from aosedge_demo_orchestrator.cli import build_parser, request_from_arguments

OWNER = "11111111-1111-4111-8111-111111111111"
IMAGE = "sha256:" + "a" * 64


class BackendTests(unittest.TestCase):
    def test_reset_uses_owned_admin_only_and_reuses_uncertain_command(self):
        self.state["vehicles"]["test"]["systemUid"] = OWNER
        self.state["backends"] = {"brake": {"imageId": IMAGE}}
        atomic_json(self.root / JOURNAL, self.state)
        self.container = dict(Id="b" * 64, Image=IMAGE, Config=dict(Labels={"tech.aosedge.demo.owner": OWNER,
            "tech.aosedge.demo.team": "brake"}), State=dict(Running=True))
        status = dict(schemaVersion=1, unitSystemUid=OWNER, connected=True, command=None)
        self.service._reset_status = Mock(return_value=status)
        with patch("aosedge_demo_orchestrator.backend_retirement.BackendRetirement._private") as admin:
            admin.side_effect = EnvironmentError("BACKEND_PRIVATE_RESPONSE_UNCERTAIN")
            with self.assertRaisesRegex(EnvironmentError, "UNCERTAIN"):
                self.service.execute("reset-scenario", "brake")
            identifier = admin.call_args.args[3]["commandId"]
            status["connected"] = False
            admin.side_effect = None
            admin.return_value = dict(status, command=dict(commandId=identifier, unitSystemUid=OWNER,
                operation="RESET_DEMO_SCENARIO", state="CLEARED"))
            result = self.service.execute("reset-scenario", "brake")
            self.assertEqual("CLEARED", result["state"])
            self.assertTrue(result["noOp"])
            self.assertEqual(identifier, admin.call_args.args[3]["commandId"])
            self.assertEqual(("brake", "b" * 64, "demo-reset"), admin.call_args.args[:3])
        self.assertEqual([], self.commands)

    def test_reset_read_and_pending_are_non_mutating_and_foreign_scope_rejected(self):
        for team in ("brake", "tire"):
            parsed = request_from_arguments(build_parser().parse_args(["backend", "reset-status", team, "--target", "test"]))
            self.assertEqual("test", parsed.target.value)
            application = Mock()
            application.execute.return_value.to_dict.return_value = {}
            execute_operation(dict(domain="backend", action="reset-scenario", team=team, target="test"), application)
            with self.assertRaises(ValueError):
                execute_operation(dict(domain="backend", action="reset-scenario", team=team, target="production"), application)
        with self.assertRaisesRegex(EnvironmentError, "SCOPE_OR_SHAPE"):
            self.service._validate_reset(dict(schemaVersion=1, unitSystemUid="foreign", connected=True, command=None), OWNER)

    def test_presenter_native_prepare_does_not_force_the_old_mock_workaround(self):
        application = Mock()
        application.execute.return_value.to_dict.return_value = {}
        execute_operation(dict(domain="service", action="prepare", team="brake", content_profile="v3"), application)
        request = application.execute.call_args.args[0]
        self.assertFalse(request.without_permissions)
        self.assertFalse(request.demo_mocked_data)

    def test_observation_does_not_acquire_writer_but_mutations_still_do(self):
        self.service._context_handles = Mock(return_value=dict(state="CLEAR", owners=[]))
        self.state["vehicles"]["test"]["systemUid"] = "test-uid"
        self.state["backends"] = dict(brake=dict(imageId=IMAGE))
        atomic_json(self.root / JOURNAL, self.state)
        self.container = dict(Image=IMAGE, Config=dict(Labels={"tech.aosedge.demo.owner": OWNER,
            "tech.aosedge.demo.team": "brake"}), State=dict(Running=True))
        self.service._product_observation = Mock(return_value=dict(state="OBSERVED"))
        held, release = threading.Event(), threading.Event()
        def writer():
            with self.environment._writer():
                held.set()
                release.wait(5)
        thread = threading.Thread(target=writer)
        thread.start()
        try:
            self.assertTrue(held.wait(2))
            before = (self.root / JOURNAL).read_bytes()
            self.assertEqual("OBSERVED", self.service.execute("inspect", "brake")["state"])
            self.service._product_observation.assert_called_once_with("brake", "test-uid", deadline=ANY)
            self.assertEqual("RUNNING", self.service.execute("status", "brake")["state"])
            with self.assertRaisesRegex(EnvironmentError, "CURRENT_RUN_BUSY"):
                self.service.execute("stop", "brake")
            self.assertEqual(before, (self.root / JOURNAL).read_bytes())
            self.assertEqual([], self.commands)
        finally:
            release.set()
            thread.join(3)
        self.assertFalse(thread.is_alive())

    def test_observation_rejects_changed_binding_but_not_unrelated_upload(self):
        for field in ("vehicle", "owner", "backend", "upload"):
            with self.subTest(field=field):
                initial = json.loads((self.root / JOURNAL).read_text())
                def inspect(kind, name, **kwargs):
                    current = json.loads((self.root / JOURNAL).read_text())
                    if field == "vehicle":
                        current["vehicles"]["test"]["systemUid"] = "replacement"
                    elif field == "owner":
                        current["operations"][0]["id"] = "other-run"
                    elif field == "backend":
                        current["backends"] = dict(brake=dict(imageId="replacement"))
                    else:
                        current["servicePublication"] = dict(state="UPLOADED")
                    atomic_json(self.root / JOURNAL, current)
                    return None
                self.service._inspect = inspect
                if field == "upload":
                    self.assertEqual("STOPPED", self.service.execute("inspect", "brake")["state"])
                else:
                    with self.assertRaisesRegex(EnvironmentError, "OBSERVATION_BINDING_CHANGED"):
                        self.service.execute("inspect", "brake")
                atomic_json(self.root / JOURNAL, initial)

    def test_product_inspect_uses_only_fixed_local_endpoints_and_mock_provenance(self):
        connection = Mock()
        response = connection.getresponse.return_value
        response.status = 200
        response.read.side_effect = [b'{"ready":true}', b'{"state":"CURRENT"}', json.dumps(dict(
            source="DEMO_MOCK", vehicleTelemetry=False, unitSystemUid="test-uid", counts={})).encode()] + [
                b'{"unitSystemUid":"test-uid","items":[]}'] * 4 + [json.dumps(dict(schemaVersion=3, contractVersion="3.0.0", resourceType="FUNCTION_OBSERVATION", unitSystemUid="test-uid", items=[], truncated=False)).encode(), b'{"schemaVersion":1,"unitSystemUid":"test-uid","connected":false,"command":null}']
        with patch("aosedge_demo_orchestrator.backends.http.client.HTTPConnection", return_value=connection) as factory:
            result = self.service._product_observation("tire", "test-uid")
        self.assertEqual("OBSERVED", result["state"])
        self.assertFalse(result["cloudAuthority"])
        self.assertFalse(result["vehicleTelemetry"])
        self.assertEqual(9, connection.close.call_count)
        self.assertTrue(all(call.args == ("127.0.0.1", 18092) and call.kwargs == {"timeout": 3} for call in factory.call_args_list))
        self.assertEqual(["/health/ready", "/health/context", "/api/v1/tire/demo-mock/summary"] + [
            "/api/v1/tire/units/test-uid/" + name + "?limit=10" for name in ("assessments", "events", "advisories", "function-status", "function-observations")] + ["/api/v1/tire/units/test-uid/demo-reset"],
            [call.args[1] for call in connection.request.call_args_list])

    def test_product_inspect_rejects_wrong_scope_or_fabricated_source(self):
        for mock in (dict(source="LIVE", vehicleTelemetry=False, unitSystemUid="test-uid"),
                     dict(source="DEMO_MOCK", vehicleTelemetry=True, unitSystemUid="test-uid"),
                     dict(source="DEMO_MOCK", vehicleTelemetry=False, unitSystemUid="production-uid")):
            connection = Mock()
            connection.getresponse.return_value.status = 200
            connection.getresponse.return_value.read.side_effect = [b'{}', b'{}', json.dumps(mock).encode()]
            with patch("aosedge_demo_orchestrator.backends.http.client.HTTPConnection", return_value=connection):
                with self.assertRaisesRegex(EnvironmentError, "SCOPE_OR_PROVENANCE"):
                    self.service._product_observation("brake", "test-uid")
            self.assertEqual(3, connection.close.call_count)

    def test_brake_product_windows_are_read_separately_from_mock_data(self):
        connection = Mock()
        response = connection.getresponse.return_value
        response.status = 200
        window = dict(unitSystemUid="test-uid", resourceType="WINDOW", items=[dict(eventId="event-1", unitSystemUid="test-uid")])
        response.read.side_effect = [b'{"ready":true}', b'{}', json.dumps(dict(
            source="DEMO_MOCK", vehicleTelemetry=False, unitSystemUid="test-uid")).encode(),
            json.dumps(window).encode()] + [json.dumps(dict(unitSystemUid="test-uid", resourceType=kind, items=[])).encode()
                for kind in ("ASSESSMENT", "EVENT", "ADVISORY")] + [json.dumps(dict(schemaVersion=3, contractVersion="3.0.0", resourceType="FUNCTION_OBSERVATION", unitSystemUid="test-uid", items=[], truncated=False)).encode(), b'{"schemaVersion":1,"unitSystemUid":"test-uid","connected":false,"command":null}']
        with patch("aosedge_demo_orchestrator.backends.http.client.HTTPConnection", return_value=connection):
            result = self.service._product_observation("brake", "test-uid")
        self.assertEqual("OBSERVED", result["state"])
        self.assertEqual(window, result["observations"]["productData"]["data"])
        self.assertEqual("DEMO_MOCK", result["observations"]["mockData"]["data"]["source"])
        self.assertEqual("/api/v1/brake/units/test-uid/windows?limit=10", connection.request.call_args_list[3].args[1])
        self.assertEqual("/api/v1/brake/units/test-uid/demo-reset", connection.request.call_args.args[1])
        self.assertEqual(9, connection.close.call_count)

    def test_brake_product_windows_reject_wrong_unit_or_shape(self):
        for change in (dict(unitSystemUid="production-uid"), dict(resourceType="MOCK"),
                       dict(items={}), dict(items=[{}] * 11)):
            with self.subTest(change=change):
                connection = Mock()
                response = connection.getresponse.return_value
                response.status = 200
                window = dict(unitSystemUid="test-uid", resourceType="WINDOW", items=[])
                window.update(change)
                response.read.side_effect = [b'{}', b'{}', json.dumps(dict(source="DEMO_MOCK",
                    vehicleTelemetry=False, unitSystemUid="test-uid")).encode(), json.dumps(window).encode()]
                with patch("aosedge_demo_orchestrator.backends.http.client.HTTPConnection", return_value=connection):
                    with self.assertRaisesRegex(EnvironmentError, "PRODUCT_SCOPE_OR_SHAPE"):
                        self.service._product_observation("brake", "test-uid")
                self.assertEqual(4, connection.close.call_count)

    def test_product_inspect_missing_context_malformed_or_unavailable_is_not_success(self):
        with patch("aosedge_demo_orchestrator.backends.http.client.HTTPConnection") as factory:
            with self.assertRaises(EnvironmentError):
                self.service._product_observation("brake", None)
            factory.assert_not_called()
            connection = factory.return_value
            response = connection.getresponse.return_value
            response.status = 200
            response.read.side_effect = [b'[]', OSError("not available"), b'not JSON'] + [b'not JSON'] * 6
            result = self.service._product_observation("brake", "test-uid")
            self.assertEqual("PARTIAL", result["state"])
            self.assertTrue(all(item["state"] == "UNAVAILABLE" for item in result["observations"].values()))

    def test_window_detail_is_bounded_current_unit_read_without_arbitrary_path(self):
        event_id = "4cba2d80-c04a-4d24-9f03-f4a85d56da13"
        detail = dict(schemaVersion=2, contractVersion="2.0.0", resourceType="WINDOW_DETAIL", unitSystemUid="test-uid",
            unitRole="VALIDATION", window=dict(eventId=event_id, unitSystemUid="test-uid"), samples=[])
        connection = Mock()
        connection.getresponse.return_value.status = 200
        connection.getresponse.return_value.read.return_value = json.dumps(detail).encode()
        with patch("aosedge_demo_orchestrator.backends.http.client.HTTPConnection", return_value=connection) as factory:
            self.assertEqual(detail, self.service._window_detail("test-uid", event_id))
            factory.assert_called_once_with("127.0.0.1", 18091, timeout=3)
            self.assertEqual("/api/v1/brake/units/test-uid/windows/" + event_id, connection.request.call_args.args[1])
            for change in (dict(unitSystemUid="other"), dict(samples=[{}] * 151), dict(window=dict(eventId="other", unitSystemUid="test-uid"))):
                connection.getresponse.return_value.read.return_value = json.dumps(dict(detail, **change)).encode()
                with self.assertRaisesRegex(EnvironmentError, "SCOPE_OR_SHAPE"):
                    self.service._window_detail("test-uid", event_id)
            for invalid in ("../other", event_id + "?target=production", None):
                with self.assertRaisesRegex(EnvironmentError, "IDENTITY_INVALID"):
                    self.service._window_detail("test-uid", invalid)

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
        self.service._inspect = lambda kind, name, **kwargs: self.container if kind == "container" else None
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

    def test_readiness_only_inspects_owned_processes_without_storage_forensics(self):
        self.state["backends"] = {team: dict(imageId=IMAGE) for team in ("brake", "tire")}
        atomic_json(self.root / JOURNAL, self.state)
        self.service._inspect = Mock(side_effect=lambda kind, name: dict(Image=IMAGE,
            Config=dict(Labels={"tech.aosedge.demo.owner": OWNER, "tech.aosedge.demo.team": "brake" if "brake" in name else "tire"}),
            State=dict(Running=True, Health=dict(Status="healthy"))))
        before = (self.root / JOURNAL).read_bytes()
        with patch.object(self.service, "_context_handles") as handles:
            self.assertEqual("CURRENT", self.service.observe_stack()["state"])
            self.assertEqual(2, self.service._inspect.call_count)
            handles.assert_not_called()
        self.service._image.assert_not_called()
        self.assertEqual([], self.commands)
        self.assertEqual(before, (self.root / JOURNAL).read_bytes())
        self.service._inspect.side_effect = EnvironmentError("BACKEND_DOCKER_ENGINE_UNAVAILABLE")
        result = self.service.observe_stack()
        self.assertEqual("UNKNOWN", result["state"])
        self.assertTrue(all(item["state"] == "UNKNOWN" for item in result["teams"].values()))

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

    def test_authorized_watt_restart_restores_same_five_instances_and_data(self):
        self.state.update(demoLifecycle=dict(action="retire", state="PARTIAL", reason="CLEANUP_FILE_IN_USE",
            phase="retire-test-data-and-overlay"), backends={team: dict(state="STOPPED", cleanup=dict(containerRemoval="REMOVED"))
                for team in ("brake", "tire")})
        atomic_json(self.root / JOURNAL, self.state)
        containers = {}
        for index, service in enumerate(("db", "redis", "api", "admin", "tunnel"), 1):
            name = "watt-the-app-" + service + "-1"
            containers[name] = dict(Id=str(index) * 64, Image=IMAGE,
                Config=dict(Labels={"com.docker.compose.project": "watt-the-app", "com.docker.compose.service": service}),
                State=dict(Running=True, Health=dict(Status="healthy")),
                Mounts=[dict(Type="volume", Name=service + "-data", Destination="/data", RW=True),
                    dict(Type="bind", Source="/fixed/source", Destination="/app", RW=False)])
        self.service._inspect = lambda kind, name: containers.get(name)
        actions = []
        def docker(*args, **kwargs):
            actions.append(args)
            if args == ("container", "ls", "--quiet"):
                return "\n".join(value["Id"][:12] for value in containers.values())
            if args[:2] == ("desktop", "restart"):
                for value in containers.values():
                    value["State"]["Running"] = False
                    value["Mounts"].reverse()
            if args[:2] == ("container", "start"):
                next(value for value in containers.values() if value["Id"] == args[2])["State"]["Running"] = True
            return ""
        self.service._docker = docker
        held = dict(state="HELD", owners=[dict(pid=123, processClass="VIRTUAL_MACHINE")])
        self.service._context_handles = Mock(side_effect=[held, dict(state="CLEAR", owners=[]), dict(state="CLEAR", owners=[])])
        self.service._run = Mock(side_effect=["p123\n", "/usr/bin/python\n"])
        with patch("aosedge_demo_orchestrator.backends.sys.platform", "darwin"), patch.object(Path, "is_file", return_value=True), patch(
                "aosedge_demo_orchestrator.backends.shutil.which", return_value="/fixed/lsof"):
            result = self.service.recover_file_sharing("watt-the-app")
            self.assertEqual("COMPLETED", result["state"])
            self.assertEqual(set(containers), set(result["restoredContainers"]))
            self.assertTrue(self.service.recover_file_sharing("watt-the-app")["noOp"])
        self.assertEqual(1, sum(args[:2] == ("desktop", "restart") for args in actions))
        self.assertEqual(5, sum(args[:2] == ("container", "start") for args in actions))
        self.assertFalse(any("rm" in args or "prune" in args for args in actions))

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
