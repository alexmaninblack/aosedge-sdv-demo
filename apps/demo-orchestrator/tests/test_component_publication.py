# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import contextlib
import copy
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
from urllib.parse import parse_qs, urlsplit

from aosedge_demo_orchestrator.components import ComponentService, COMPONENT
from aosedge_demo_orchestrator.component_cloud import COMPONENT_ID
from aosedge_demo_orchestrator.component_publication import Reads, snapshot, publication
from aosedge_demo_orchestrator.environment import JOURNAL, MANIFEST, EnvironmentError, digest
from aosedge_demo_orchestrator.unit_cloud import CloudFailure

OWNER = "11111111-1111-4111-8111-111111111111"
TEST = "22222222-2222-4222-8222-222222222222"
SET = "33333333-3333-4333-8333-333333333333"
BUNDLE = "44444444-4444-4444-8444-444444444444"
RELEASE = "55555555-5555-4555-8555-555555555555"


def ready(version="16.0.0", identity=BUNDLE):
    return dict(id=identity, state="done", build_info=None, items=[dict(
        type="component", codename=COMPONENT, version=version)])


class FixtureCloud:
    user = dict(ownerId=OWNER)

    def __init__(self):
        self.calls, self.permissions = [], []
        self.collections = {"components/" + COMPONENT_ID + "/versions/": [], "deployment-bundles/": [],
            "unit-sets/": [dict(id=SET, is_validation_set=True)], "unit-sets/" + SET + "/units/": []}
        self.unit = dict(id=TEST, system_uid="test-uid", status="provisioned", online_status="Offline",
            unit_sets=[dict(id=SET)], unit_update_components=[])
        self.component_owner = OWNER

    def require(self, *permissions):
        self.permissions.extend(permissions)

    def call(self, path):
        self.calls.append(path)
        if path == "components/" + COMPONENT_ID + "/":
            return dict(codename=COMPONENT, oem_id=self.component_owner)
        if path == "units/" + TEST + "/":
            return copy.deepcopy(self.unit)
        parsed = urlsplit(path)
        if parsed.path not in self.collections:
            raise AssertionError("Undocumented/unrelated read: " + path)
        query = parse_qs(parsed.query)
        offset, limit = int(query["offset"][0]), int(query["limit"][0])
        rows = self.collections[parsed.path]
        return dict(offset=offset, total=len(rows), items=copy.deepcopy(rows[offset:offset + limit]))


class PublicationAdapterTests(unittest.TestCase):
    def setUp(self):
        self.cloud = FixtureCloud()
        self.request = dict(version="16.0.0", vehicles={}, verificationTest=True, purpose="upload")

    def mark_ready(self):
        self.request["deploymentId"] = BUNDLE
        self.cloud.collections["deployment-bundles/"] = [ready()]
        self.cloud.collections["components/" + COMPONENT_ID + "/versions/"] = [
            dict(id=RELEASE, version="16.0.0", state="Ready", is_fake=False)]

    def test_preprovision_empty_recipients_no_unit_production_or_batch_reads(self):
        result = snapshot(self.cloud, self.request)
        self.assertEqual("NOT_PUBLISHED", result["publication"]["stage"])
        self.assertEqual([], result["recipientCoverage"]["recipientUnitIds"])
        self.assertTrue(result["recipientCoverage"]["complete"])
        self.assertFalse(any("verification-batch" in path or path.startswith("units/") for path in self.cloud.calls))

    def test_offline_owned_test_in_verification_set_can_publish(self):
        self.request["vehicles"] = dict(test=dict(unitId=TEST, unitSetId=SET, systemUid="test-uid"))
        self.cloud.collections["unit-sets/" + SET + "/units/"] = [dict(id=TEST, system_uid="test-uid")]
        result = snapshot(self.cloud, self.request)
        self.assertEqual("Offline", result["test"]["online_status"])
        self.assertEqual([TEST], result["recipientCoverage"]["recipientUnitIds"])

    def test_unrelated_verification_recipient_or_uid_always_blocks(self):
        self.request["vehicles"] = dict(test=dict(unitId=TEST, unitSetId=SET, systemUid="test-uid"))
        for member in (dict(id=RELEASE, system_uid="test-uid"), dict(id=TEST, system_uid="wrong")):
            self.cloud.collections["unit-sets/" + SET + "/units/"] = [member]
            with self.assertRaisesRegex(CloudFailure, "UNRELATED_VERIFICATION_RECIPIENT"):
                snapshot(self.cloud, self.request)

    def test_missing_membership_or_wrong_filter_or_owner_is_blocked(self):
        self.request["vehicles"] = dict(test=dict(unitId=TEST, unitSetId=SET, systemUid="test-uid"))
        with self.assertRaisesRegex(CloudFailure, "MEMBERSHIP_NOT_PROVEN"):
            snapshot(self.cloud, self.request)
        self.cloud.collections["unit-sets/"][0]["is_validation_set"] = False
        with self.assertRaisesRegex(CloudFailure, "FILTER_NOT_PROVEN"):
            snapshot(self.cloud, self.request)
        self.cloud.component_owner = RELEASE
        with self.assertRaisesRegex(CloudFailure, "IDENTITY_OR_OWNER_MISMATCH"):
            snapshot(self.cloud, self.request)

    def test_missing_component_report_is_unknown_not_empty(self):
        self.request["vehicles"] = dict(test=dict(unitId=TEST, unitSetId=SET, systemUid="test-uid"))
        self.cloud.collections["unit-sets/" + SET + "/units/"] = [dict(id=TEST, system_uid="test-uid")]
        self.cloud.unit.pop("unit_update_components")
        self.assertIsNone(snapshot(self.cloud, dict(self.request, purpose="status"))["test"]["components"])
        with self.assertRaisesRegex(CloudFailure, "UPDATE_STATE_NOT_PROVEN"):
            snapshot(self.cloud, self.request)

    def test_verification_retirement_needs_ready_bundle_not_batch(self):
        from aosedge_demo_orchestrator import unit_cloud
        self.mark_ready()
        entry = dict(version="16.0.0", deploymentId=BUNDLE, verificationTest=True)
        with patch.object(unit_cloud, "Cloud", return_value=self.cloud):
            self.assertEqual(dict(confirmedUploads=[entry]), unit_cloud.execute(dict(action="reconcile-uploads", uploads=[entry])))
            self.cloud.collections["deployment-bundles/"][0]["state"] = "error"
            with self.assertRaisesRegex(CloudFailure, "RECONCILIATION_REQUIRED"):
                unit_cloud.execute(dict(action="reconcile-uploads", uploads=[entry]))
        self.assertNotIn("verification_batch_read", self.cloud.permissions)
        self.assertFalse(any("verification-batch" in path for path in self.cloud.calls))

    def test_exact_bundle_on_second_page_and_ready_without_approval(self):
        self.mark_ready()
        self.cloud.collections["deployment-bundles/"] = [dict(id=str(index)) for index in range(100)] + [ready()]
        result = snapshot(self.cloud, dict(self.request, purpose="status"))
        self.assertEqual("READY", result["publication"]["stage"])
        self.assertEqual(2, sum(path.startswith("deployment-bundles/") for path in self.cloud.calls))
        self.assertFalse(any("verification" in path for path in self.cloud.calls))

    def test_error_keeps_sanitized_build_info_never_ready(self):
        self.mark_ready()
        bundle = self.cloud.collections["deployment-bundles/"][0]
        bundle.update(state="Error", build_info="payload must be a file, not a directory")
        result = snapshot(self.cloud, dict(self.request, purpose="status"))
        self.assertEqual("ERROR", result["publication"]["stage"])
        self.assertIn("must be a file", result["publication"]["buildInfo"])
        self.assertTrue(result["problems"])
        bundle["build_info"] = "token=private-material"
        self.assertNotIn("private-material", json.dumps(snapshot(self.cloud, self.request)))

    def test_publication_stages_missing_fake_ambiguous_and_content_mismatch(self):
        row = dict(id=RELEASE, version="16.0.0", state="Ready", is_fake=False)
        for bundle, versions, expected in (
                (dict(ready(), state="uploaded"), [], "PROCESSING"),
                (ready(), [], "PROCESSING"), (ready(), [dict(row, is_fake=True)], "UNKNOWN"),
                (ready(), [row, row], "ERROR"), (dict(ready(), items=[]), [row], "ERROR"),
                (dict(ready(), state="surprise"), [row], "UNKNOWN"), (ready(), [row], "READY")):
            with self.subTest(expected=expected, bundle=bundle):
                self.assertEqual(expected, publication("16.0.0", BUNDLE, [bundle], versions)["stage"])
        self.assertEqual("UNKNOWN", publication("16.0.0", BUNDLE, [], [row])["stage"])

    def test_partial_duplicate_offset_and_limits_never_prove_coverage(self):
        for value in (dict(offset=0, total=2, items=[dict(id=SET)]),
                      dict(offset=1, total=0, items=[]),
                      dict(offset=0, total=2, items=[dict(id=SET), dict(id=SET)])):
            with self.assertRaises(CloudFailure):
                Reads(SimpleNamespace(call=lambda path: value)).pages("unit-sets/")
        self.cloud.collections["deployment-bundles/"] = [dict(id=str(index)) for index in range(801)]
        with self.assertRaisesRegex(CloudFailure, "COLLECTION_LIMIT"):
            Reads(self.cloud).pages("deployment-bundles/")
        reads = Reads(self.cloud)
        reads.remaining = 0
        with self.assertRaisesRegex(CloudFailure, "READ_BUDGET"):
            reads.call("unit-sets/")

    def test_previous_publication_uses_same_bounded_bundle_collection(self):
        self.mark_ready()
        self.request.pop("deploymentId")
        self.request.update(version="17.0.0", previousPublication=dict(version="16.0.0", deploymentId=BUNDLE))
        result = snapshot(self.cloud, self.request)
        self.assertEqual("READY", result["previousPublication"]["stage"])
        self.assertEqual([], result["deploymentBundles"])
        self.assertEqual(1, sum(path.startswith("deployment-bundles/") for path in self.cloud.calls))

    def test_malformed_extra_bundle_item_cannot_be_dropped_to_claim_ready(self):
        self.mark_ready()
        self.cloud.collections["deployment-bundles/"][0]["items"].append("invalid")
        with self.assertRaisesRegex(CloudFailure, "ITEMS_SCHEMA_INVALID"):
            snapshot(self.cloud, dict(self.request, purpose="status"))


class PublicationServiceTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.catalog = SimpleNamespace(project=self.root, component_support=Mock(return_value={"schemaVersion": 1}))
        self.service = ComponentService(SimpleNamespace(root=self.root, catalog=self.catalog, _writer=contextlib.nullcontext))
        self.state = dict(stage="LOCAL_ACTIVE", currentVehicle="test", factory=dict(path=".local/factory/oem-demo-factory.img", format="raw",
            version="1.0.31", sha256="a" * 64, manifestPath=MANIFEST),
            vehicles=dict(test=dict(localVmId=TEST, runtime=dict(state="RUNNING"))))
        manifest = self.root / MANIFEST
        manifest.parent.mkdir(parents=True)
        manifest.write_text(json.dumps(dict(schemaVersion=1, kind="democtl.factory-copy", sourceSelector="31/arm64",
            image={key: self.state["factory"][key] for key in ("path", "format", "version", "sha256")})))
        self.state["factory"]["manifestSha256"] = digest(manifest)
        self.journal = self.root / JOURNAL
        self.journal.parent.mkdir(parents=True)
        self.save()
        directory = self.service._directory("16.0.0")
        directory.mkdir(parents=True)
        self.prepared_path = directory / "prepared.json"
        self.prepared_path.write_text(json.dumps(dict(version="16.0.0", contentProfile="v1")))
        self.files = {"config/capability-manifest.json": b'{"readPaths":["Vehicle.Speed"]}',
            "provenance/provenance.json": json.dumps(dict(factoryImageRawSha256="a" * 64, factoryImageVersion="1.0.31")).encode()}
        self.before = dict(versions=[], deploymentBundles=[], ownerId=OWNER,
            recipientCoverage=dict(complete=True, recipientUnitIds=[]))
        self.response = dict(deploymentId=BUNDLE, httpStatus=201, state="uploaded")

    def save(self):
        self.journal.write_text(json.dumps(self.state))

    def upload(self, responses):
        profile = json.loads(self.prepared_path.read_text())["contentProfile"]
        with patch.object(self.service, "_inspect", return_value=(dict(problems=[], signedEnvelope=True, sha256="signed", contentProfile=profile), self.files)), \
                patch.object(self.service, "_bundle", return_value=self.root / "bundle"), \
                patch.object(self.service, "diagnose", side_effect=AssertionError("No guest publication checks")), \
                patch.object(self.service, "_worker", side_effect=responses) as worker:
            return self.service.upload("16.0.0"), worker.call_args_list

    def test_acceptance_is_once_immediate_and_journal_precedes_request(self):
        def respond(action, **values):
            if action == "upload":
                self.assertTrue(json.loads(self.journal.read_text())["componentOperations"]["16.0.0"]["upload"]["attemptStarted"])
                self.assertEqual(OWNER, values["ownerId"])
                return self.response
            return self.before
        result, calls = self.upload(respond)
        self.assertEqual("ACCEPTED", result["publication"]["stage"])
        self.assertEqual(["cloud-status", "upload"], [call.args[0] for call in calls])
        record = json.loads(self.journal.read_text())["componentOperations"]["16.0.0"]
        self.assertEqual("RESPONDED", record["upload"]["state"])
        self.assertNotIn("approve", record)
        self.assertNotIn("productionBefore", record)
        self.catalog.component_support.assert_called_once_with("31/arm64", "a" * 64, COMPONENT, ["Vehicle.Speed"])

    def test_immediate_cloud_error_is_not_successful_publication(self):
        result, _ = self.upload([self.before, dict(self.response, state="Error", buildInfo="invalid payload")])
        self.assertEqual("ERROR", result["publication"]["stage"])
        self.assertTrue(result["problems"])
        self.assertFalse(result["noOp"])

    def test_api_preserves_error_stage_and_refuses_scope_overrides(self):
        from aosedge_demo_orchestrator.api import execute_operation
        from aosedge_demo_orchestrator.application import DemoOrchestrator
        app = DemoOrchestrator(environment_service=self.service.environment)
        payload = dict(domain="component", action="upload", component_version="16.0.0")
        with patch.object(ComponentService, "upload", return_value=dict(publication=dict(stage="ERROR"), problems=["error"], noOp=False)):
            result = execute_operation(payload, app)
        self.assertEqual("PARTIAL", result["state"])
        self.assertEqual("ERROR", result["data"]["publication"]["stage"])
        for key, value in (("verificationTest", True), ("ownerId", OWNER), ("deploymentId", BUNDLE), ("target", "production")):
            with self.assertRaises(ValueError):
                execute_operation(dict(payload, **{key: value}), app)

    def test_existing_or_nonincremented_version_never_uploads(self):
        for before, reason in ((dict(self.before, versions=[dict(version="16.0.0")]), "ALREADY_IN_CLOUD"),
                               (dict(self.before, latestPublishedVersion="17.0.0"), "MUST_INCREMENT")):
            with self.assertRaisesRegex(EnvironmentError, reason):
                self.upload([before])
        self.assertNotIn("componentOperations", json.loads(self.journal.read_text()))

    def test_warehouse_all_profiles_publish_before_provision_connected_running(self):
        for profile in ("v1", "v2", "v3"):
            self.save()
            self.prepared_path.write_text(json.dumps(dict(version="16.0.0", contentProfile=profile)))
            result, calls = self.upload([self.before, self.response])
            self.assertEqual("ACCEPTED", result["publication"]["stage"])
            self.assertTrue(calls[0].kwargs["preProvisioning"])
            self.assertEqual({}, calls[0].kwargs["vehicles"])

    def test_repeated_upload_is_read_only_and_error_never_successful_noop(self):
        self.upload([self.before, self.response])
        for stage in ("PROCESSING", "ERROR", "UNKNOWN", "READY"):
            observed = dict(publication=dict(stage=stage), problems=[] if stage in ("READY", "PROCESSING") else ["error"])
            with patch.object(self.service, "_worker", return_value=observed) as worker, \
                    patch.object(self.service, "_inspect", side_effect=AssertionError("No archive reread")):
                result = self.service.upload("16.0.0")
            self.assertEqual(stage == "READY", result["noOp"])
            self.assertEqual("cloud-status", worker.call_args.args[0])
            self.assertEqual(1, worker.call_count)

    def test_response_loss_never_retries(self):
        with self.assertRaisesRegex(EnvironmentError, "LOST"):
            self.upload([self.before, EnvironmentError("LOST")])
        with self.assertRaisesRegex(EnvironmentError, "RECONCILIATION_REQUIRED"), \
                patch.object(self.service, "_worker") as worker:
            self.service.upload("16.0.0")
        worker.assert_not_called()

    def test_older_lost_response_is_not_hidden_by_a_newer_ready_record(self):
        self.state["componentOperations"] = {
            "14.0.0": dict(upload=dict(attemptStarted=True, state="UNCERTAIN")),
            "15.0.0": dict(deploymentId=RELEASE, upload=dict(attemptStarted=True, state="CONFIRMED"))}
        self.save()
        with self.assertRaisesRegex(EnvironmentError, "PREVIOUS_PUBLICATION_RECONCILIATION_REQUIRED"):
            self.upload([])

    def test_receipt_provenance_or_catalog_failure_blocks_before_cloud(self):
        from aosedge_demo_orchestrator.images import ImageError
        self.catalog.component_support.side_effect = ImageError("IMAGE_COMPONENT_SUPPORT_NOT_DECLARED")
        with self.assertRaisesRegex(EnvironmentError, "SUPPORT_NOT_DECLARED"):
            self.upload([])
        self.catalog.component_support.side_effect = None
        self.state["factory"]["manifestSha256"] = "different"
        self.save()
        with self.assertRaisesRegex(EnvironmentError, "RECEIPT_NOT_PROVEN"):
            self.upload([])

    def test_outstanding_previous_update_blocks_but_warehouse_ready_allows(self):
        self.state["componentOperations"] = {"15.0.0": dict(deploymentId=RELEASE, upload=dict(attemptStarted=True))}
        self.save()
        for stage in ("PROCESSING", "ERROR", "UNKNOWN"):
            with self.assertRaisesRegex(EnvironmentError, "PREVIOUS_PUBLICATION_NOT_READY"):
                self.upload([dict(self.before, previousPublication=dict(stage=stage))])
        result, _ = self.upload([dict(self.before, previousPublication=dict(stage="READY")), self.response])
        self.assertEqual("ACCEPTED", result["publication"]["stage"])

    def test_pending_error_or_missing_previous_install_blocks_successor(self):
        self.state["vehicles"]["test"].update(unitId=TEST, unitSetId=SET, systemUid="test-uid")
        self.state["cloudBinding"] = dict(ownerId=OWNER)
        self.save()
        for row in (dict(pending_component={"version": "15.0.0"}), dict(pending_component_error="failed")):
            with self.assertRaisesRegex(EnvironmentError, "PENDING_OR_FAILED"):
                self.upload([dict(self.before, test=dict(components=[row]))])
        self.state["componentOperations"] = {"15.0.0": dict(deploymentId=RELEASE, upload=dict(attemptStarted=True))}
        self.save()
        with self.assertRaisesRegex(EnvironmentError, "PREVIOUS_UPDATE_NOT_INSTALLED"):
            self.upload([dict(self.before, previousPublication=dict(stage="READY"), test=dict(components=[]))])

    def test_scope_rejects_partial_retired_identity_and_owner_change(self):
        self.state["vehicles"]["test"]["unitId"] = TEST
        self.save()
        with self.assertRaisesRegex(EnvironmentError, "INCOMPLETE_OR_RETIRED"):
            self.service._verification_scope("16.0.0")
        self.state["vehicles"]["test"].update(unitSetId=SET, systemUid="test-uid", cloud=dict(lifecycle="DELETED"))
        self.save()
        with self.assertRaisesRegex(EnvironmentError, "INCOMPLETE_OR_RETIRED"):
            self.service._verification_scope("16.0.0")


if __name__ == "__main__":
    unittest.main()
