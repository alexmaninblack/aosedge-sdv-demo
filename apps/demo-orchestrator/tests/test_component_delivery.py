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
from aosedge_demo_orchestrator.component_cloud import guard, batch_guard, snapshot, COMPONENT_ID, reconcile_list_guard
from aosedge_demo_orchestrator.components import COMPONENT
from aosedge_demo_orchestrator.unit_cloud import CloudFailure
from aosedge_demo_orchestrator.environment import EnvironmentError, JOURNAL
from aosedge_demo_orchestrator.component_build import pack
from aosedge_demo_orchestrator.api import execute_operation
from aosedge_demo_orchestrator import source_guest


class DeliveryTests(unittest.TestCase):
    def test_focused_cloud_status_never_reads_a_guest_or_an_artifact(self):
        with patch.object(self.service, "_worker", return_value={"source": "AOS_CLOUD_ONLY"}) as worker, \
                patch.object(self.service, "status") as guest, patch.object(self.service, "inspect") as inspect:
            self.assertEqual("AOS_CLOUD_ONLY", self.service.cloud_status()["source"])
        guest.assert_not_called()
        inspect.assert_not_called()
        worker.assert_called_once_with("cloud-status", purpose="overview", vehicles={"test": self.state["vehicles"]["test"]})

    def test_legacy_list_guard_reconciles_only_null_strategy_for_empty_set(self):
        import copy
        before = dict(members=[], unitSet=dict(id="production", is_validation_set=False, update_strategy=None))
        after = dict(members=[], unitSet=dict(before["unitSet"], update_strategy="MinimizeRestarts"))
        original = dict(productionBefore=before, upload=dict(state="RESPONDED", response=dict(httpStatus=201)))
        observed = dict(preProvisioning=True, productionListObservation=before, production=after)
        record = copy.deepcopy(original)
        self.assertTrue(reconcile_list_guard(record, observed))
        self.assertEqual(after, record["productionBefore"])
        self.assertEqual(before, record["guardReconciliation"]["previous"])
        for changed in (dict(after, members=[dict(id="other")]), dict(after, unitSet=dict(after["unitSet"], is_validation_set=True))):
            self.assertFalse(reconcile_list_guard(copy.deepcopy(original), dict(observed, production=changed)))

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

    def test_preprovision_scope_requires_pristine_dual_factory(self):
        from aosedge_demo_orchestrator.component_runtime import FACTORY_VERSION
        self.state = dict(stage="MANUFACTURED", factory=dict(version=FACTORY_VERSION, sha256="factory"),
            vehicles={role: dict(unitId=None, nodeId=None, unitSetId=None) for role in ("test", "production")})
        self.save()
        self.assertTrue(self.service._cloud_scope("10.0.0")["preProvisioning"])
        self.state["stage"] = "LOCAL_STOPPED"
        self.save()
        self.assertTrue(self.service._cloud_scope("10.0.0")["preProvisioning"])
        self.state["vehicles"]["test"]["systemUid"] = "partial-identity"
        self.save()
        with self.assertRaisesRegex(EnvironmentError, "PRISTINE_DUAL_FACTORY"):
            self.service._cloud_scope("10.0.0")

    def test_empty_cloud_snapshot_has_no_unit_requests_and_rejects_any_members(self):
        ids = {"test": "11111111-1111-4111-8111-111111111111", "production": "22222222-2222-4222-8222-222222222222"}
        sets = {role: dict(id=identity, title="Test Vehicles" if role == "test" else "Production Vehicles",
            fleet="fleet", is_validation_set=role == "test", members=[])
            for role, identity in ids.items()}
        class EmptyCloud:
            user = {"ownerId": "owner"}
            def inventory(self):
                return dict(sets=list(sets.values()), units=[])
            def call(self, path):
                if path == "components/" + COMPONENT_ID + "/":
                    return dict(codename=COMPONENT)
                for item in sets.values():
                    if path == "unit-sets/" + item["id"] + "/":
                        return item
                raise AssertionError("No Unit-specific calls before provisioning: " + path)
            def pages(self, path):
                if path.startswith("units/"):
                    raise AssertionError(path)
                return []
        value = snapshot(EmptyCloud(), dict(version="10.0.0", preProvisioning=True,
            vehicles={role: dict(unitId=None) for role in ids}))
        guard(value)
        self.assertEqual([], value["testAvailableComponents"])
        with self.assertRaises(CloudFailure):
            guard(dict(value, remainingUnits=["another-unit"]))
        with self.assertRaises(CloudFailure):
            guard(dict(value, test=dict(members=["another-unit"])))

    def test_preprovision_v1_upload_is_once_and_does_not_probe_a_guest(self):
        from aosedge_demo_orchestrator.component_runtime import FACTORY_VERSION
        self.state = dict(stage="MANUFACTURED", factory=dict(version=FACTORY_VERSION, sha256="factory"),
            vehicles={role: dict(unitId=None, nodeId=None, unitSetId=None) for role in ("test", "production")})
        self.save()
        directory = self.service._directory("10.0.0")
        directory.mkdir(parents=True)
        prepared = dict(version="10.0.0", contentProfile="v1")
        (directory / "prepared.json").write_text(json.dumps(prepared))
        contract = self.root / "contracts/vdp-compatibility-profile/vdp-compatibility-profile.v1.json"
        contract.parent.mkdir(parents=True)
        contract.write_text(json.dumps(dict(componentVersions=[dict(id="VDP_V1", readPaths=["Vehicle.Speed"])])))
        before = dict(self.before, preProvisioning=True, remainingUnits=[],
            test=dict(members=[]), production=dict(members=[]),
            testSet=dict(id="test-set", fleet="fleet", is_validation_set=True),
            productionSet=dict(id="prod-set", fleet="fleet", is_validation_set=False))
        after = dict(before, deploymentBundles=[dict(id="bundle", state="uploaded")])
        files = {"config/capability-manifest.json": b'{"readPaths":["Vehicle.Speed"]}',
            "provenance/provenance.json": json.dumps(dict(contentProfile="v1", factoryImageVersion=FACTORY_VERSION,
                factoryImageRawSha256="factory")).encode()}
        with patch.object(self.service, "verify", return_value=dict(sha256="digest")), \
                patch.object(self.service, "_bundle", return_value=directory / "fixture.tar.gz"), \
                patch.object(self.service, "_inspect", return_value=({}, files)), \
                patch.object(self.service, "diagnose", side_effect=AssertionError("No guest before provisioning")), \
                patch.object(self.service, "_worker", side_effect=[before, dict(deploymentId="bundle", httpStatus=201), after]) as worker:
            result = self.service.upload("10.0.0")
            self.assertTrue(result["productionUnchanged"])
            self.assertEqual(["cloud-status", "upload", "cloud-status"], [call.args[0] for call in worker.call_args_list])
        prepared["contentProfile"] = "v2"
        (directory / "prepared.json").write_text(json.dumps(prepared))
        with patch.object(self.service, "verify", return_value=dict(sha256="digest")), \
                patch.object(self.service, "_worker") as worker, \
                self.assertRaisesRegex(EnvironmentError, "PREPROVISION_V1_ONLY"):
            self.service.upload("10.0.0")
        worker.assert_not_called()

    def test_upload_response_loss_is_not_retried(self):
        with self.assertRaises(EnvironmentError):
            self.invoke("upload", [self.before, EnvironmentError("LOST")])
        with self.assertRaisesRegex(EnvironmentError, "RECONCILIATION_REQUIRED"):
            self.invoke("upload", [self.before])

    def test_confirmation_reads_exact_bundle_and_production_only(self):
        from unittest.mock import Mock
        deployment = "33333333-3333-4333-8333-333333333333"
        cloud = Mock()
        cloud.user = dict(ownerId="owner")
        cloud.pages.return_value = [dict(id=deployment, state="uploaded"), dict(id="unrelated", state="done")]
        with patch("aosedge_demo_orchestrator.component_cloud.unit_view", return_value=self.before["production"]) as unit:
            result = snapshot(cloud, dict(version="10.0.0", purpose="confirm", deploymentId=deployment,
                vehicles={role: dict(unitId=role) for role in ("test", "production")}))
        cloud.call.assert_not_called()
        cloud.pages.assert_called_once_with("deployment-bundles/")
        cloud.inventory.assert_not_called()
        unit.assert_called_once_with(cloud, dict(unitId="production"))
        self.assertEqual(deployment, result["deploymentBundles"][0]["id"])

    def test_approval_does_not_verify_local_archive(self):
        from unittest.mock import Mock
        batch = dict(id="batch", oem_id="owner", architectures=["arm64"], update_items=[dict(
            identity_id=COMPONENT_ID, codename=COMPONENT, version="2.0.0")],
            approval_states={"arm64": {"is_approved": True}})
        before = dict(self.before, verificationBatches=[batch], deploymentBundles=[dict(id="bundle", state="done")])
        with patch.object(self.service, "verify", side_effect=AssertionError("No local signing work during approval")), \
                patch.object(self.service, "_worker", return_value=before) as worker:
            result = self.service.approve("2.0.0")
        self.assertTrue(result["noOp"])
        worker.assert_called_once()
        self.assertEqual("approve", worker.call_args.kwargs["purpose"])

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

            def require(self, *permissions):
                raise AssertionError("No extra Production validation permissions: " + ",".join(permissions))

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
                if path.startswith(("fleet-validation-batch/", "campaigns/")):
                    raise AssertionError("Production rollout is deferred: " + path)
                return []

        request = dict(version="1.0.16", vehicles={role: dict(
            unitId=test_id, systemUid="uid", unitSetId=test_id) for role in ("test", "production")})
        with patch("aosedge_demo_orchestrator.component_cloud.unit_view", return_value={"id": test_id}):
            result = snapshot(FixtureCloud(), request)
        self.assertEqual([dict(id="available", type=COMPONENT, version="1.0.16", file_size=42)],
                         result["testAvailableComponents"])
        self.assertNotIn("validationBatches", result)
        self.assertNotIn("validationObservation", result)
        self.assertEqual({"id": test_id}, result["production"])

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

    def test_journal_preserves_cm_phases_and_typed_instance_status(self):
        service = SimpleNamespace(returncode=0, stdout="Id=aos-cm.service\n")
        messages = [dict(MESSAGE=message, __REALTIME_TIMESTAMP=str(index), _SYSTEMD_UNIT="aos-cm.service")
            for index, message in enumerate((
                "(updatemanager) Update state changed: state=activating",
                "(launcher) Instance status received: instance={component:1:factory-vdp:aos-vm-main:0}, version=0.0.0, state=activating",
                "(updatemanager) Current update canceled",
                "(launcher) Instance status received: instance={component:0:vdp:subject:0}, version=8.0.0, state=active, token=SECRET_FIXTURE"))]
        journal = SimpleNamespace(returncode=0, stdout="\n".join(json.dumps(value) for value in messages))
        empty = SimpleNamespace(returncode=0, stdout="")
        with patch.object(source_guest, "command", side_effect=[service, journal, empty, empty, empty]):
            result = source_guest.execute(dict(action="component-logs", vehicle=dict(localVmId="fixture")))
        self.assertEqual(2, len(result["cmUpdatePhases"]))
        self.assertEqual(dict(type="component", preinstalled=True, itemId="factory-vdp", subjectId="aos-vm-main",
            instance=0, version="0.0.0", state="activating"), result["entries"][1]["nativeInstance"])
        self.assertNotIn("SECRET_FIXTURE", json.dumps(result))
        self.assertNotIn("{component:", json.dumps(result))

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
