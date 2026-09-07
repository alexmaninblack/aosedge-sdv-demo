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
from aosedge_demo_orchestrator.presenter_operations import NativeSession, SessionOperations, operation_plan, public_result, reset_plan


def payload(session, action="start-vms", **values):
    return dict(requestId=str(uuid4()), sessionId=session.session_id, action=action, **values)


def completed(request):
    return dict(operation=request["domain"] + "." + request["action"], state="COMPLETED", message="done", data={})


class OperationTests(unittest.TestCase):
    def finish(self, session):
        deadline = time.monotonic() + 2
        while session.snapshot()["active"] and time.monotonic() < deadline:
            threading.Event().wait(.005)
        self.assertIsNone(session.snapshot()["active"])
        return session.snapshot()["jobs"][-1]

    def test_allowlist_and_exact_recipient(self):
        session = SessionOperations()
        cases = [("create", dict(image="factory-31/arm64"), dict(domain="environment", action="create", target="all", image="factory-31/arm64")),
                 ("connect-test", {}, dict(domain="vehicle", action="select", target="test")),
                 ("prepare", dict(version="13.0.0", profile="v1"), dict(domain="component", action="prepare", component_version="13.0.0", content_profile="v1")),
                 ("approve", dict(version="13.0.0"), dict(domain="component", action="approve", component_version="13.0.0"))]
        for action, params, expected in cases:
            self.assertEqual([expected], operation_plan(payload(session, action, **params))[1])
        for params in (dict(target="production"), dict(path="/tmp/file"), dict(url="https://example.com"), dict(force=True), dict(profile="admin")):
            with self.assertRaises(ValueError):
                operation_plan(payload(session, **params))
        for action in ("shell", "send", "unapprove", "production-approve", "test-logs"):
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
        self.assertEqual(["simulation.stop", "unit.deprovision", "unit.delete", "vm.stop", "environment.retire"],
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
            self.assertEqual(["simulation", "vm", "environment"], [request["domain"] for request in reset_plan(root, plan)])
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
