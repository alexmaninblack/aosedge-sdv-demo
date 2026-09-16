# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import http.client
import json
import stat
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import Mock
from uuid import uuid4

from aosedge_demo_orchestrator.presenter import make_server
from aosedge_demo_orchestrator.api import execute_operation
from aosedge_demo_orchestrator.models import OperationResult, OperationState, VehicleTarget
from aosedge_demo_orchestrator.presenter_operations import NativeSession, SessionOperations, operation_plan, public_result, reset_plan


def payload(session, action="start-vms", **values):
    return dict(requestId=str(uuid4()), sessionId=session.session_id, action=action, **values)


def completed(request):
    return dict(operation=request["domain"] + "." + request["action"], state="COMPLETED", message="done", data={})


class OperationTests(unittest.TestCase):
    def test_receipt_rollover_preserves_finish_and_duplicate_identity(self):
        execute = Mock(side_effect=completed)
        session = SessionOperations(execute)
        first = payload(session, "observe-test")
        session.submit(first)
        self.finish(session)
        for _ in range(128):
            session.submit(payload(session, "observe-test"))
            self.finish(session)
        before = execute.call_count
        archived = session.submit(first)
        self.assertTrue(archived["archived"])
        self.assertEqual(before, execute.call_count)
        self.assertIn(first["requestId"], session.snapshot()["recordedRequestIds"])
        self.assertEqual(128, len(session.snapshot()["jobs"]))
        with self.assertRaisesRegex(ValueError, "REQUEST_ID_INPUT_CHANGED"):
            session.submit(dict(first, action="reset"))
        session.submit(payload(session, "reset"))
        self.assertEqual("COMPLETED", self.finish(session)["state"])

    def test_service_publication_and_first_assignment_keep_native_authority(self):
        session = SessionOperations()
        request = payload(session, "service-prepare", team="brake", profile="v3")
        self.assertEqual([dict(domain="service", action="prepare", team="brake", content_profile="v3")],
            operation_plan(request)[1])
        plan = operation_plan(payload(session, "service-publish", release="brake/12.0.0"))[1]
        self.assertEqual(["sign", "upload"], [row["action"] for row in plan])
        self.assertTrue(all(row["service_release"] == "brake/12.0.0" for row in plan))
        identifier = str(uuid4())
        self.assertEqual([dict(domain="service", action="runtime-prepare", target="test"),
            dict(domain="service", action="assign", target="test", service_id=identifier)],
            operation_plan(payload(session, "service-assign", serviceId=identifier))[1])
        for action, values in (("service-prepare", dict(team="tire", profile="v2")),
                ("service-publish", dict(release="../private")), ("service-assign", dict(serviceId=identifier, target="production")),
                ("service-assign", dict(serviceId=identifier, version="12.0.0"))):
            with self.assertRaises(ValueError):
                operation_plan(payload(session, action, **values))

    def test_composed_publication_stops_before_upload_if_sign_fails(self):
        execute = Mock(return_value=dict(operation="service.sign", state="BLOCKED", message="SIGN_FAILED"))
        session = SessionOperations(execute)
        session.submit(payload(session, "service-publish", release="tire/10.0.0"))
        self.assertEqual("BLOCKED", self.finish(session)["state"])
        self.assertEqual(1, execute.call_count)

    def test_first_service_deploy_prepares_inputs_then_assigns_once(self):
        execute = Mock(side_effect=completed)
        session = SessionOperations(execute)
        request = payload(session, "service-assign", serviceId=str(uuid4()))
        session.submit(request)
        job = self.finish(session)
        self.assertEqual("COMPLETED", job["state"])
        self.assertEqual([dict(domain="service", action="runtime-prepare", target="test"),
            dict(domain="service", action="assign", target="test", service_id=request["serviceId"])],
            [call.args[0] for call in execute.call_args_list])
        self.assertEqual(["service.runtime-prepare", "service.assign"],
            [result["operation"] for result in job["results"]])
        session.submit(request)
        self.assertEqual(2, execute.call_count)

    def test_service_deploy_does_not_assign_after_input_failure(self):
        for state in ("BLOCKED", "PARTIAL"):
            with self.subTest(state=state):
                execute = Mock(return_value=dict(operation="service.runtime-prepare", state=state,
                    message="SERVICE_INPUTS_NOT_READY"))
                session = SessionOperations(execute)
                session.submit(payload(session, "service-assign", serviceId=str(uuid4())))
                self.assertEqual(state, self.finish(session)["state"])
                execute.assert_called_once_with(dict(domain="service", action="runtime-prepare", target="test"))

    def test_service_deploy_input_noop_still_reconciles_assignment(self):
        def execute(request):
            result = completed(request)
            if request["action"] == "runtime-prepare":
                result["data"] = dict(noOp=True)
            return result
        worker = Mock(side_effect=execute)
        session = SessionOperations(worker)
        session.submit(payload(session, "service-assign", serviceId=str(uuid4())))
        self.assertEqual("COMPLETED", self.finish(session)["state"])
        self.assertEqual(["runtime-prepare", "assign"], [call.args[0]["action"] for call in worker.call_args_list])

    def test_service_deploy_unknown_input_outcome_never_assigns_or_replays(self):
        execute = Mock(side_effect=RuntimeError("SECRET"))
        session = SessionOperations(execute)
        request = payload(session, "service-assign", serviceId=str(uuid4()))
        session.submit(request)
        self.assertEqual("UNCERTAIN", self.finish(session)["state"])
        session.submit(request)
        execute.assert_called_once_with(dict(domain="service", action="runtime-prepare", target="test"))
        self.assertNotIn("SECRET", json.dumps(session.snapshot()))

    def test_studio_simulation_start_and_stop_are_test_scoped(self):
        for action in ("start", "stop"):
            with self.subTest(action=action):
                execute = Mock(side_effect=completed)
                session = SessionOperations(execute)
                session.submit(payload(session, action + "-simulation"))
                self.assertEqual("COMPLETED", self.finish(session)["state"])
                execute.assert_called_once_with(dict(domain="simulation", action=action, target="test"))
                for target in ("production", "all"):
                    with self.assertRaises(ValueError):
                        operation_plan(payload(session, action + "-simulation", target=target))

    def test_fixed_studio_plans_cross_the_real_api_adapter(self):
        cases = [("service-assign", dict(serviceId=str(uuid4())),
                  ["service.runtime-prepare", "service.assign"]),
                 ("start-simulation", {}, ["simulation.start"]),
                 ("stop-simulation", {}, ["simulation.stop"])]
        for action, fields, expected in cases:
            with self.subTest(action=action):
                application = Mock()
                application.execute.side_effect = lambda request: OperationResult(
                    request.domain + "." + request.action, OperationState.COMPLETED, "done")
                session = SessionOperations(lambda request: execute_operation(request, application))
                session.submit(payload(session, action, **fields))
                self.assertEqual("COMPLETED", self.finish(session)["state"])
                requests = [call.args[0] for call in application.execute.call_args_list]
                self.assertEqual(expected, [request.domain + "." + request.action for request in requests])
                self.assertTrue(all(request.target == VehicleTarget.TEST for request in requests))
                self.assertTrue(all(not request.restart_sm and not request.restart_cm for request in requests))

    def finish(self, session):
        deadline = time.monotonic() + 2
        while session.snapshot()["active"] and time.monotonic() < deadline:
            threading.Event().wait(.005)
        self.assertIsNone(session.snapshot()["active"])
        return session.snapshot()["jobs"][-1]

    def test_allowlist_and_exact_recipient(self):
        session = SessionOperations()
        cases = [("create", dict(image="factory-31/arm64"), dict(domain="demo", action="create", image="factory-31/arm64")),
                 ("connect-test", {}, dict(domain="vehicle", action="initialize", target="test")),
                 ("prepare", dict(profile="v1"), dict(domain="component", action="prepare", content_profile="v1")),
                 ("upload", dict(version="13.0.0"), dict(domain="component", action="upload", component_version="13.0.0")),
                 ("park", {}, dict(domain="environment", action="park")),
                 ("resume", {}, dict(domain="environment", action="resume")),
                 ("provision", {}, dict(domain="unit", action="provision", target="test"))]
        for action, params, expected in cases:
            self.assertEqual([expected], operation_plan(payload(session, action, **params))[1])
        for params in (dict(target="production"), dict(path="/tmp/file"), dict(url="https://example.com"), dict(force=True), dict(profile="admin")):
            with self.assertRaises(ValueError):
                operation_plan(payload(session, **params))
        for action in ("shell", "send", "approve", "unapprove", "production-approve", "test-logs"):
            with self.assertRaises(ValueError):
                operation_plan(payload(session, action))
        self.assertEqual([dict(domain="component", action="cloud-status")], operation_plan(payload(session, "observe-test"))[1])
        with self.assertRaises(ValueError):
            operation_plan(payload(session, "prepare", version="../bad", profile="v1"))

    def test_receipt_is_immediate_and_duplicate_is_not_reexecuted(self):
        entered, release = threading.Event(), threading.Event()
        calls = []
        def execute(request):
            calls.append(request)
            entered.set()
            release.wait(2)
            return completed(request)
        session = SessionOperations(execute)
        request = payload(session)
        try:
            receipt = session.submit(request)
            self.assertEqual(request["requestId"], receipt["id"])
            self.assertTrue(entered.wait(1))
            self.assertEqual(receipt["id"], session.submit(request)["id"])
            with self.assertRaises(ValueError):
                session.submit(payload(session))
            with self.assertRaises(ValueError):
                session.submit(dict(request, action="stop-vms"))
        finally:
            release.set()
        self.assertEqual("COMPLETED", self.finish(session)["state"])
        session.submit(request)
        self.assertEqual(1, len(calls))

    def test_unknown_outcome_is_not_retried_and_session_generation_is_bound(self):
        session = SessionOperations(Mock(side_effect=RuntimeError("SECRET")))
        session.submit(payload(session))
        self.assertEqual("UNCERTAIN", self.finish(session)["state"])
        self.assertNotIn("SECRET", json.dumps(session.snapshot()))
        with self.assertRaises(ValueError):
            session.submit(payload(session))
        session.executor = completed
        session.submit(payload(session, "observe-test"))
        self.assertEqual("COMPLETED", self.finish(session)["state"])
        with self.assertRaises(ValueError):
            session.submit(dict(payload(session, "observe-test"), sessionId=str(uuid4())))

    def test_reset_order_stops_at_first_blocker(self):
        execute = Mock(side_effect=completed)
        session = SessionOperations(execute)
        session.submit(payload(session, "reset"))
        self.assertEqual("COMPLETED", self.finish(session)["state"])
        self.assertEqual(["demo.retire"],
                         [call.args[0]["domain"] + "." + call.args[0]["action"] for call in execute.call_args_list])
        execute.reset_mock()
        execute.side_effect = [dict(operation="simulation.stop", state="BLOCKED", message="owned source unavailable")]
        session.submit(payload(session, "reset"))
        self.assertEqual("BLOCKED", self.finish(session)["state"])
        self.assertEqual(1, execute.call_count)

    def test_projection_does_not_forward_arbitrary_worker_data(self):
        result = public_result(dict(operation="component.status", state="OBSERVED", message="read", data=dict(activeVersion="13.0.0", password="SECRET", rawResponse="SECRET", path="SECRET")))
        self.assertEqual(dict(activeVersion="13.0.0"), result["facts"])
        self.assertNotIn("SECRET", json.dumps(result))
        logs = public_result(dict(operation="component.logs", data=dict(entries=[dict(message="safe log", raw="SECRET")], providerReadyEvents=2)))
        self.assertEqual([dict(message="safe log")], logs["facts"]["entries"])
        self.assertNotIn("SECRET", json.dumps(logs))

    def test_empty_or_never_provisioned_reset_uses_only_applicable_core_steps(self):
        from aosedge_demo_orchestrator.environment import JOURNAL
        plan = operation_plan(payload(SessionOperations(), "reset"))[1]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertEqual([plan[-1]], reset_plan(root, plan))
            journal = root / JOURNAL
            journal.parent.mkdir(parents=True)
            journal.write_text(json.dumps(dict(vehicles=dict(test=dict(unitId=None), production=dict(unitId=None)))))
            self.assertEqual(["demo"], [request["domain"] for request in reset_plan(root, plan)])
            journal.write_text(json.dumps(dict(vehicles=dict(test=dict(systemUid="partial-identity")))))
            self.assertEqual(plan, reset_plan(root, plan))

    def test_private_session_auth_and_ephemeral_capability(self):
        native = NativeSession(("127.0.0.1", 0), SessionOperations(completed))
        directory = Path(native.directory.name)
        try:
            self.assertEqual(0o700, stat.S_IMODE(directory.stat().st_mode))
            self.assertEqual(0o400, stat.S_IMODE((directory / "platform-oem").stat().st_mode))
            connection = http.client.HTTPConnection(*native.server.server_address, timeout=2)
            for headers in ({}, {"Authorization": "Bearer " + native.capability, "Origin": "http://127.0.0.1:18080"}):
                connection.request("GET", "/operations", headers=headers)
                response = connection.getresponse()
                self.assertEqual(403, response.status)
                response.read()
            connection.close()
            code, result = native.call()
            self.assertEqual(200, code)
            self.assertNotIn(native.capability, json.dumps(result))
        finally:
            native.close()
        self.assertFalse(directory.exists())


class ProtectedFrontendTests(unittest.TestCase):
    def test_same_origin_fixed_dispatch_and_unknown_response(self):
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / "index.html").write_text("Presenter")
            native = Mock()
            native.call.return_value = (202, dict(id="accepted"))
            server = make_server(directory, ("127.0.0.1", 0), native=native)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                session = SessionOperations()
                request = payload(session)
                def send(body, origin=None):
                    connection = http.client.HTTPConnection(*server.server_address, timeout=2)
                    headers = {"Content-Type": "application/json"}
                    if origin:
                        headers["Origin"] = origin
                    connection.request("POST", "/api/presenter/operations", body=json.dumps(body), headers=headers)
                    response = connection.getresponse()
                    result = response.status, response.read()
                    connection.close()
                    return result
                origin = "http://127.0.0.1:" + str(server.server_port)
                self.assertEqual(403, send(request)[0])
                self.assertEqual(403, send(request, "https://other.example")[0])
                self.assertEqual(400, send(dict(request, target="production"), origin)[0])
                native.call.assert_not_called()
                self.assertEqual(202, send(request, origin)[0])
                native.call.assert_called_once_with(request)
                native.call.side_effect = RuntimeError("SECRET")
                code, body = send(request, origin)
                self.assertEqual(503, code)
                self.assertNotIn(b"SECRET", body)
                self.assertIn(b"DO_NOT_RESUBMIT", body)
            finally:
                server.shutdown()
                server.server_close()
                thread.join()
