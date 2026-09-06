# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import contextlib
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from aosedge_demo_orchestrator.components import ComponentService
from aosedge_demo_orchestrator.component_cloud import guard, batch_guard, snapshot, COMPONENT_ID
from aosedge_demo_orchestrator.components import COMPONENT
from aosedge_demo_orchestrator.unit_cloud import CloudFailure
from aosedge_demo_orchestrator.environment import EnvironmentError, JOURNAL
from aosedge_demo_orchestrator.component_build import pack
from aosedge_demo_orchestrator.api import execute_operation
from aosedge_demo_orchestrator import source_guest


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.service = ComponentService(SimpleNamespace(root=self.root,
            catalog=SimpleNamespace(project=self.root), _writer=contextlib.nullcontext))
        self.state = dict(vehicles={role: dict(unitId=role, unitSetId=role, systemUid=role)
                                   for role in ("test", "production")})
        self.journal = self.root / JOURNAL
        self.journal.parent.mkdir(parents=True)
        self.save()
        self.before = dict(ownerId="owner", versions=[], deploymentBundles=[], verificationBatches=[],
            testSet=dict(is_validation_set=True), productionSet=dict(is_validation_set=False),
            test=dict(id="test", fleet="fleet", online_status="Online"), production=dict(id="production", fleet="fleet"))

    def save(self):
        self.journal.write_text(json.dumps(self.state))

    def invoke(self, action, responses):
        with patch.object(self.service, "verify", return_value=dict(sha256="digest")), \
                patch.object(self.service, "_bundle", return_value=self.root / "fixture.tar.gz"), \
                patch.object(self.service, "_inspect", return_value=({}, {"config/capability-manifest.json": b'{"readPaths":["Vehicle.Speed"]}'})), \
                patch.object(self.service, "diagnose", return_value=dict(schemaLoadedByService=True, missing=[])), \
                patch.object(self.service, "_worker", side_effect=responses) as worker:
            result = getattr(self.service, action)("2.0.0")
            return result, worker.call_args_list

    def test_upload_exactly_once_and_records_before_attempt(self):
        after = dict(self.before, deploymentBundles=[dict(id="bundle", state="Uploaded")])
        def response(action, **values):
            if action == "upload":
                state = json.loads(self.journal.read_text())
                self.assertTrue(state["componentOperations"]["2.0.0"]["upload"]["attemptStarted"])
                return dict(deploymentId="bundle", httpStatus=201)
            return self.before if not values.get("deploymentId") else after
        result, calls = self.invoke("upload", response)
        self.assertTrue(result["productionUnchanged"])
        self.assertEqual(1, sum(call.args[0] == "upload" for call in calls))
        result, calls = self.invoke("upload", [after])
        self.assertTrue(result["noOp"])
        self.assertEqual(1, len(calls))

    def test_upload_response_loss_is_not_retried(self):
        with self.assertRaises(EnvironmentError):
            self.invoke("upload", [self.before, EnvironmentError("LOST")])
        with self.assertRaisesRegex(EnvironmentError, "RECONCILIATION_REQUIRED"):
            self.invoke("upload", [self.before])

    def test_existing_version_prevents_publication(self):
        with self.assertRaisesRegex(EnvironmentError, "ALREADY_IN_CLOUD"):
            self.invoke("upload", [dict(self.before, versions=[dict(version="2.0.0")])])

    def test_production_change_is_not_hidden(self):
        with self.assertRaisesRegex(EnvironmentError, "PRODUCTION_GUARD_CHANGED"):
            self.invoke("upload", [self.before, dict(deploymentId="bundle"), dict(self.before, production={})])

    def test_wrong_scope_and_batch_rejected(self):
        guard(self.before)
        with self.assertRaises(CloudFailure):
            guard(dict(self.before, productionSet=dict(is_validation_set=True)))
        batch = dict(oem_id="owner", architectures=["arm64"], update_items=[dict(
            identity_id=COMPONENT_ID, codename=COMPONENT, version="2.0.0")])
        batch_guard(batch, dict(version="2.0.0"), "owner")
        for changed in (dict(architectures=["amd64"]), dict(oem_id="other"), dict(update_items=batch["update_items"] * 2)):
            with self.assertRaises(CloudFailure):
                batch_guard(dict(batch, **changed), dict(version="2.0.0"), "owner")

    def test_available_components_uses_array_endpoint_and_filters_identity(self):
        test_id = "11111111-1111-4111-8111-111111111111"
        available_path = "units/" + test_id + "/available-components/"

        class FixtureCloud:
            user = {"ownerId": "owner"}

            def call(self, path):
                if path == "components/" + COMPONENT_ID + "/":
                    return {"codename": COMPONENT}
                if path == available_path:
                    return [dict(id="available", type=COMPONENT, version="1.0.16", file_size=42),
                            dict(id="unrelated", type="other-component", version="9.0.0")]
                if path.endswith("/components/send-requests/"):
                    return []
                if path.startswith("unit-sets/"):
                    return {"id": test_id}
                raise AssertionError(path)

            def pages(self, path):
                if "available-components" in path:
                    raise AssertionError("Available components is an array, not a paginated endpoint")
                return []

        request = dict(version="1.0.16", vehicles={role: dict(
            unitId=test_id, systemUid="uid", unitSetId=test_id) for role in ("test", "production")})
        with patch("aosedge_demo_orchestrator.component_cloud.unit_view", return_value={"id": test_id}):
            result = snapshot(FixtureCloud(), request)
        self.assertEqual([dict(id="available", type=COMPONENT, version="1.0.16", file_size=42)],
                         result["testAvailableComponents"])

    def test_unapprove_existing_batch_then_restore_without_upload(self):
        batch = dict(id="batch", oem_id="owner", architectures=["arm64"], update_items=[dict(
            identity_id=COMPONENT_ID, codename=COMPONENT, version="2.0.0")],
            approval_states={"arm64": {"is_approved": True}})
        before = dict(self.before, verificationBatches=[batch], deploymentBundles=[dict(id="bundle", state="done")])
        after = dict(before, verificationBatches=[dict(batch, approval_states={"arm64": {"is_approved": False}})])
        result, calls = self.invoke("unapprove", [before, dict(batchId="batch", approved=False), after])
        self.assertFalse(result["approved"])
        self.assertTrue(result["productionUnchanged"])
        self.assertEqual(["cloud-status", "unapprove", "cloud-status"], [call.args[0] for call in calls])
        result, calls = self.invoke("unapprove", [after])
        self.assertTrue(result["noOp"])
        result, calls = self.invoke("approve", [after, dict(batchId="batch", approved=True), before])
        self.assertTrue(result["approved"])

    def test_null_approval_does_not_count_as_confirmed_unapproval(self):
        batch = dict(id="batch", oem_id="owner", architectures=["arm64"], update_items=[dict(
            identity_id=COMPONENT_ID, codename=COMPONENT, version="2.0.0")])
        before = dict(self.before, verificationBatches=[batch], deploymentBundles=[dict(id="bundle", state="done")])
        with self.assertRaisesRegex(EnvironmentError, "APPROVAL_NOT_CONFIRMED"):
            self.invoke("unapprove", [before, dict(batchId="batch", approved=None), before])
        with self.assertRaisesRegex(EnvironmentError, "RECONCILIATION_REQUIRED"):
            self.invoke("unapprove", [before])

    def test_single_test_scope_requires_bound_production_set_without_adoption(self):
        del self.state["vehicles"]["production"]
        self.save()
        with self.assertRaisesRegex(EnvironmentError, "PRODUCTION_GUARD_BINDING_REQUIRED"):
            self.service._cloud_scope("2.0.0")
        self.state["cloudBinding"] = {"sets": {"production": "bound-production-set"}}
        self.save()
        scope = self.service._cloud_scope("2.0.0")
        self.assertEqual("bound-production-set", scope["productionSetId"])
        self.assertEqual({"test"}, set(scope["vehicles"]))
        self.assertNotIn("production", json.loads(self.journal.read_text())["vehicles"])

    def test_prepare_tar_is_deterministic(self):
        first = pack({"bin/vehicle-data-provider": b"test", "config/a": b"a"})
        self.assertEqual(first, pack({"config/a": b"a", "bin/vehicle-data-provider": b"test"}))

    def send_before(self):
        return dict(self.before, versions=[dict(id="update", version="2.0.0", state="Ready", is_fake=False)],
            deploymentBundles=[dict(id="bundle", state="done")], testSendRequests=[],
            verificationBatches=[dict(id="batch", oem_id="owner", architectures=["arm64"],
                update_items=[dict(identity_id=COMPONENT_ID, codename=COMPONENT, version="2.0.0")],
                approval_states={"arm64": {"is_approved": True}})])

    def test_send_exactly_once_journal_before_attempt_and_repeat_is_read_only(self):
        before = self.send_before()
        after = dict(before, testSendRequests=[dict(id="receipt", component_type=COMPONENT, update_component="update")])
        def response(action, **values):
            if action == "send":
                intent = json.loads(self.journal.read_text())["componentOperations"]["2.0.0"]["send"]
                self.assertEqual("test", intent["unitId"])
                self.assertEqual("update", intent["updateComponentId"])
                self.assertTrue(intent["attemptStarted"])
                return dict(requestAccepted=True, requestId="receipt", httpStatus=201)
            return before if "componentOperations" not in json.loads(self.journal.read_text()) else after
        result, calls = self.invoke("send", response)
        self.assertEqual("REQUEST_LISTED", result["deliveryObservation"])
        self.assertEqual(["cloud-status", "send", "cloud-status"], [call.args[0] for call in calls])
        result, calls = self.invoke("send", [after])
        self.assertTrue(result["noOp"])
        self.assertEqual(1, len(calls))

    def test_send_response_loss_never_reposts_and_can_reconcile_installed(self):
        before = self.send_before()
        with self.assertRaises(EnvironmentError):
            self.invoke("send", [before, EnvironmentError("LOST")])
        with self.assertRaisesRegex(EnvironmentError, "SEND_RECONCILIATION_REQUIRED"):
            self.invoke("send", [before])
        after = dict(before, test=dict(before["test"], components=[dict(installed_component={"id": "update"})]))
        result, calls = self.invoke("send", [after])
        self.assertTrue(result["noOp"])
        self.assertEqual("INSTALLED_COMPONENT", result["deliveryObservation"])
        self.assertEqual(1, len(calls))

    def test_send_requires_approved_ready_artifact_and_no_other_pending(self):
        before = self.send_before()
        batch = dict(before["verificationBatches"][0], approval_states={"arm64": {"is_approved": False}})
        cases = [(dict(before, verificationBatches=[batch]), "REQUIRES_APPROVAL"),
                 (dict(before, versions=[]), "ARTIFACT_NOT_READY"),
                 (dict(before, test=dict(before["test"], components=[dict(pending_component={"id": "other"})])), "OTHER_UPDATE_PENDING")]
        for value, reason in cases:
            with self.subTest(reason=reason), self.assertRaisesRegex(EnvironmentError, reason):
                self.invoke("send", [value])
        self.assertNotIn("componentOperations", json.loads(self.journal.read_text()))

    def test_send_does_not_claim_acceptance_without_post_read(self):
        before = self.send_before()
        with self.assertRaisesRegex(EnvironmentError, "SEND_RECONCILIATION_REQUIRED"):
            self.invoke("send", [before, dict(requestAccepted=True), before])

    def test_send_adapter_posts_one_version_to_journal_test_only(self):
        from aosedge_demo_orchestrator.component_cloud import execute
        from unittest.mock import Mock
        unit = "11111111-1111-4111-8111-111111111111"
        update = "22222222-2222-4222-8222-222222222222"
        receipt = "33333333-3333-4333-8333-333333333333"
        cloud = Mock()
        cloud.call.return_value = [dict(id=receipt, component_type=COMPONENT, update_component=update)]
        request = dict(action="send", unitId=unit, updateComponentId=update, vehicles={"test": {"unitId": unit}})
        with patch("aosedge_demo_orchestrator.component_cloud.Cloud", return_value=cloud), \
                patch("aosedge_demo_orchestrator.component_cloud.unit_view"):
            result = execute(request)
        self.assertTrue(result["requestAccepted"])
        cloud.call.assert_called_once_with("units/" + unit + "/components/send-requests/",
            "POST", {"update_component_ids": [update]}, expected=201)
        with patch("aosedge_demo_orchestrator.component_cloud.Cloud", return_value=cloud):
            with self.assertRaisesRegex(CloudFailure, "IDENTITY_CHANGED"):
                execute(dict(request, unitId=update))

    def test_send_api_rejects_target_uuid_and_endpoint_overrides(self):
        for extra in (dict(target="production"), dict(unitId="arbitrary"), dict(updateComponentId="arbitrary"), dict(url="elsewhere")):
            with self.assertRaises(ValueError):
                execute_operation(dict(domain="component", action="send", component_version="2.0.0", **extra))

    def test_api_cannot_choose_batch_or_production_promotion(self):
        for extra in (dict(batchId="arbitrary"), dict(target="production"), dict(url="https://elsewhere")):
            with self.assertRaises(ValueError):
                execute_operation(dict(domain="component", action="approve", component_version="2.0.0", **extra))
        with patch.object(ComponentService, "status", return_value=dict(activeVersion="1.0.16")) as observed:
            result = execute_operation(dict(domain="component", action="status", target="test"))
            self.assertEqual("OBSERVED", result["state"])
            observed.assert_called_once_with("test")

    def test_journal_decodes_binary_json_and_hides_secrets_and_ready_flood(self):
        service = SimpleNamespace(returncode=0, stdout="Id=aos-sm.service\nActiveState=active\n")
        messages = [dict(MESSAGE=list(b"\x1b[31mcomponent self-test failed\x1b[0m"), __REALTIME_TIMESTAMP="1", _SYSTEMD_UNIT="aos-sm.service"),
            dict(MESSAGE="component password=SECRET_FIXTURE", __REALTIME_TIMESTAMP="2"),
            dict(MESSAGE='{"message":"component health passed","token":"SECRET_FIXTURE"}', __REALTIME_TIMESTAMP="3"),
            dict(MESSAGE="Selected vehicle data is ready", __REALTIME_TIMESTAMP="4"),
            dict(MESSAGE="Failed to start instance: instance={hidden fixture}, error=a different component transaction is already active", __REALTIME_TIMESTAMP="5")]
        journal = SimpleNamespace(returncode=0, stdout="\n".join(json.dumps(value) for value in messages))
        empty = SimpleNamespace(returncode=0, stdout="")
        with patch.object(source_guest, "command", side_effect=[service, journal, empty, empty, empty]):
            result = source_guest.execute(dict(action="component-logs", vehicle=dict(localVmId="fixture")))
        self.assertEqual(1, result["providerReadyEvents"])
        self.assertEqual(["component self-test failed", "component health passed", "Failed to start instance: instance=[BODY_REDACTED]"], [item["message"] for item in result["entries"]])
        self.assertEqual("a different component transaction is already active", result["entries"][-1]["diagnostic"])
        self.assertNotIn("hidden fixture", json.dumps(result))
        self.assertNotIn("SECRET_FIXTURE", json.dumps(result))

    def test_unconfirmed_approval_does_not_report_completion(self):
        self.state["componentOperations"] = {"2.0.0": dict(deploymentId="bundle", sha256="digest")}
        self.save()
        batch = dict(id="batch", oem_id="owner", architectures=["arm64"], update_items=[dict(
            identity_id=COMPONENT_ID, codename=COMPONENT, version="2.0.0")])
        before = dict(self.before, verificationBatches=[batch])
        with self.assertRaisesRegex(EnvironmentError, "APPROVAL_NOT_CONFIRMED"):
            self.invoke("approve", [before, dict(batchId="batch", approved=False), before])

    def test_missing_schema_prevents_upload_before_attempt(self):
        with patch.object(self.service, "verify", return_value=dict(sha256="digest")), \
                patch.object(self.service, "_inspect", return_value=({}, {"config/capability-manifest.json": b'{"readPaths":["Vehicle.CarlaSimulation.ChaosWheel.Row1.Left.LongitudinalSlip"]}'})), \
                patch.object(self.service, "diagnose", return_value=dict(schemaLoadedByService=True,
                    missing=["Vehicle.CarlaSimulation.ChaosWheel.Row1.Left.LongitudinalSlip"])), \
                patch.object(self.service, "_worker", return_value=self.before) as worker:
            with self.assertRaisesRegex(EnvironmentError, "KUKSA_SCHEMA_MISSING"):
                self.service.upload("2.0.0")
        self.assertEqual(1, worker.call_count)
        self.assertNotIn("componentOperations", json.loads(self.journal.read_text()))


if __name__ == "__main__":
    unittest.main()
