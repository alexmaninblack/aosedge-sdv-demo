# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import copy
import json
import io
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from aosedge_demo_orchestrator.browser_projection import BrowserProjection
from aosedge_demo_orchestrator.presenter_operations import operation_plan
from aosedge_demo_orchestrator import presenter


UNIT = "11111111-1111-4111-8111-111111111111"
NODE = "22222222-2222-4222-8222-222222222222"
SERVICE = "33333333-3333-4333-8333-333333333333"
EVENT = "44444444-4444-4444-8444-444444444444"
REQUEST = "55555555-5555-4555-8555-555555555555"
UID = "test-controller.non-uuid.private-identity"


class BrowserProjectionTests(unittest.TestCase):
    def setUp(self):
        self.projection = BrowserProjection()

    def test_exact_ids_keys_and_composite_binding_are_projected_without_mutation(self):
        original = dict(bindingKey=UNIT + ":" + UID, unitId=UNIT, nodeId=NODE, systemUid=UID,
                        serviceDetails={SERVICE: dict(serviceId=SERVICE)},
                        message="Current " + UID + " on " + NODE, source="Aos Cloud", state="CURRENT")
        before = copy.deepcopy(original)
        result = self.projection.project(original)
        encoded = json.dumps(result)
        for identity in (UNIT, NODE, SERVICE, UID):
            self.assertNotIn(identity, encoded)
        self.assertEqual(before, original)
        self.assertEqual(result["unitId"] + ":" + result["systemUid"], result["bindingKey"])
        self.assertIn(result["serviceDetails"].popitem()[0], encoded)
        self.assertEqual("CURRENT", result["state"])

    def test_cloud_backend_monitoring_and_job_facts_use_the_same_fingerprints(self):
        inventory = self.projection.project(dict(unitId=UNIT, systemUid=UID, subject="native-subject", teamServiceIds=dict(brake=SERVICE)))
        backend = self.projection.project(dict(unitSystemUid=UID, serviceInstance=dict(serviceId=SERVICE, subjectId="native-subject"), eventId=EVENT))
        monitoring = self.projection.project(dict(unitId=UNIT, value=dict(nodeId=NODE)))
        job = self.projection.project(dict(action="service-assign", id=REQUEST, startedAt="2026-10-18T00:00:00Z",
                                           serviceId=SERVICE, message=UID), protocol=True)
        self.assertEqual(inventory["systemUid"], backend["unitSystemUid"])
        self.assertEqual(inventory["unitId"], monitoring["unitId"])
        self.assertEqual(inventory["teamServiceIds"]["brake"], backend["serviceInstance"]["serviceId"])
        self.assertEqual(inventory["subject"], backend["serviceInstance"]["subjectId"])
        self.assertEqual(job["serviceId"], backend["serviceInstance"]["serviceId"])
        self.assertEqual(REQUEST, job["id"])
        self.assertNotIn(UID, job["message"])
        self.assertEqual(EVENT, self.projection.resolve(backend["eventId"]))

    def test_public_ui_request_protocol_is_not_a_cloud_identifier(self):
        state = dict(sessionId=REQUEST, active=REQUEST, recordedRequestIds=[REQUEST],
                     jobs=[dict(id=REQUEST, action="create", startedAt="now", serviceId=SERVICE)])
        projected = self.projection.project(state, protocol=True)
        self.assertEqual(REQUEST, projected["sessionId"])
        self.assertEqual(REQUEST, projected["active"])
        self.assertEqual([REQUEST], projected["recordedRequestIds"])
        self.assertEqual(REQUEST, projected["jobs"][0]["id"])
        self.assertNotEqual(SERVICE, projected["jobs"][0]["serviceId"])

    def test_private_non_uuid_context_is_redacted_from_text_before_any_cloud_read(self):
        result = self.projection.project(dict(message="Controller " + UID, progress=["Bound " + UID],
            error_message="Disconnected " + UID, title="Vehicle " + UID, anotherField=UID),
                                         dict(vehicles=dict(test=dict(systemUid=UID))))
        self.assertNotIn(UID, json.dumps(result))

    def test_property_names_and_public_team_enums_are_not_identity_selectors(self):
        result = self.projection.project(dict(id="brake", team="brake", serviceId="service",
                                             service=dict(id=SERVICE), state="CURRENT"))
        self.assertEqual("brake", result["team"])
        self.assertEqual("brake", result["id"])
        self.assertIn("service", result)
        self.assertTrue(result["serviceId"].startswith("ref_"))

    def test_service_assignment_resolves_only_issued_references_then_keeps_native_validation(self):
        reference = self.projection.project(dict(serviceId=SERVICE))["serviceId"]
        payload = dict(action="service-assign", requestId=REQUEST, sessionId="public-session", serviceId=reference)
        resolved = self.projection.operation(payload)
        _, plan = operation_plan(resolved)
        self.assertEqual(SERVICE, plan[-1]["service_id"])
        self.assertEqual(reference, payload["serviceId"])
        for invalid in (SERVICE, "ref_" + "0" * 32, "", None, reference + "\n"):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                self.projection.operation(dict(payload, serviceId=invalid))
        with self.assertRaises(ValueError):
            operation_plan(dict(resolved, target="production"))

    def test_restart_or_other_presenter_cannot_resolve_previous_reference(self):
        reference = self.projection.project(dict(unitId=UNIT))["unitId"]
        other = BrowserProjection()
        self.assertNotEqual(reference, other.project(dict(unitId=UNIT))["unitId"])
        with self.assertRaises(ValueError):
            other.resolve(reference)

    def test_capacity_is_bounded_and_fail_closed_without_eviction_or_rebinding(self):
        projection = BrowserProjection(limit=1)
        reference = projection.project(dict(unitId=UNIT))["unitId"]
        with self.assertRaises(ValueError):
            projection.project(dict(nodeId=NODE))
        self.assertEqual(UNIT, projection.resolve(reference))

    def test_projection_does_not_change_versions_times_bounds_or_digest_claims(self):
        content = dict(serviceVersion="18.0.0", generation=2, sequence=4,
                       sourceTime="2026-10-18T00:00:00.000Z", contentSha256="a" * 64,
                       source="FUNCTION_TEAM_REPORTED_OBSERVATION", serviceId=SERVICE)
        result = self.projection.project(content)
        for key in set(content) - {"serviceId"}:
            self.assertEqual(content[key], result[key])


class BrowserHttpBoundaryTests(unittest.TestCase):
    """Invoke the actual handlers with mocks: no listener, VM, Cloud or UI."""
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        (root / "index.html").write_text("<main>unit fixture</main>")
        self.raw = dict(unitId=UNIT, nodeId=NODE, systemUid=UID, serviceId=SERVICE, eventId=EVENT)
        self.cloud = Mock(return_value=self.raw)
        self.cloud.application.environment_service.root = root
        for name in ("monitoring", "monitoring_history", "backend", "brake_window"):
            getattr(self.cloud, name).return_value = self.raw
        self.native = Mock()
        self.native.call.return_value = 200, dict(sessionId=REQUEST, jobs=[], active=None)
        with patch.object(presenter, "StudioCloudReader", return_value=self.cloud), \
                patch.object(presenter, "ThreadingHTTPServer", side_effect=lambda address, handler: handler):
            handler = presenter.make_server(root, reader=lambda: self.raw, native=self.native)
        self.handler = object.__new__(handler)
        self.handler.server = SimpleNamespace(server_port=18080)
        self.handler.headers = {"Host": "127.0.0.1:18080"}
        self.handler.reply = Mock()

    def tearDown(self):
        self.temporary.cleanup()

    def get(self, path):
        self.handler.path = path
        self.handler.reply.reset_mock()
        self.handler.do_GET()
        code, raw = self.handler.reply.call_args.args
        return code, json.loads(raw)

    def post(self, payload):
        self.handler.path = "/api/presenter/operations"
        raw = json.dumps(payload).encode()
        self.handler.rfile = io.BytesIO(raw)
        self.handler.headers = {"Host": "127.0.0.1:18080", "Origin": "http://127.0.0.1:18080",
                                "Content-Type": "application/json", "Content-Length": str(len(raw))}
        self.handler.reply.reset_mock()
        self.handler.do_POST()
        return self.handler.reply.call_args.args[0]

    def test_every_observation_endpoint_projects_before_json_serialization(self):
        reference = None
        for path in ("snapshot", "platform", "monitoring", "monitoring-history", "backend/brake", "backend/tire"):
            with self.subTest(path=path):
                code, value = self.get("/api/presenter/" + path)
                self.assertEqual(200, code)
                for private in (UNIT, NODE, UID, SERVICE, EVENT):
                    self.assertNotIn(private, json.dumps(value))
                reference = reference or value["systemUid"]
                self.assertEqual(reference, value["systemUid"])
        self.native.call.assert_not_called()

    def test_window_uses_issued_reference_and_keeps_exact_server_side_read(self):
        _, value = self.get("/api/presenter/backend/brake")
        self.assertEqual(200, self.get("/api/presenter/backend/brake/windows/" + value["eventId"])[0])
        self.cloud.brake_window.assert_called_once_with(EVENT)
        self.cloud.brake_window.reset_mock()
        self.assertNotEqual(200, self.get("/api/presenter/backend/brake/windows/" + EVENT)[0])
        self.assertNotEqual(200, self.get("/api/presenter/backend/brake/windows/ref_" + "0" * 32)[0])
        self.cloud.brake_window.assert_not_called()

    def test_operations_hide_private_facts_preserve_request_protocol_and_reject_raw_selectors(self):
        _, public = self.get("/api/presenter/platform")
        self.native.call.return_value = 200, dict(id=REQUEST, action="service-assign", startedAt="now", serviceId=SERVICE)
        payload = dict(requestId=REQUEST, sessionId=REQUEST, action="service-assign", serviceId=public["serviceId"])
        self.assertEqual(200, self.post(payload))
        self.assertEqual(SERVICE, self.native.call.call_args.args[0]["serviceId"])
        code, body = self.handler.reply.call_args.args
        self.assertEqual(REQUEST, json.loads(body)["id"])
        self.assertNotIn(SERVICE, body.decode())
        self.native.call.reset_mock()
        self.assertEqual(400, self.post(dict(payload, serviceId=SERVICE)))
        self.native.call.assert_not_called()

    def test_operation_snapshot_and_client_state_share_the_public_session_generation(self):
        self.native.call.return_value = 200, dict(sessionId=REQUEST, active=None,
            jobs=[dict(id=EVENT, action="create", startedAt="now", serviceId=SERVICE)], uncertain=False)
        _, operations = self.get("/api/presenter/operations")
        _, state = self.get("/api/presenter/client-state")
        self.assertEqual(REQUEST, operations["sessionId"])
        self.assertEqual(REQUEST, state["sessionId"])
        self.assertEqual(EVENT, operations["jobs"][0]["id"])
        self.assertNotIn(SERVICE, json.dumps(operations))

    def test_client_build_refresh_does_not_depend_on_a_readable_run_journal(self):
        with patch("aosedge_demo_orchestrator.status.read_json", side_effect=ValueError("fixture journal")):
            self.assertEqual(200, self.get("/api/presenter/client-state")[0])


if __name__ == "__main__":
    unittest.main()
