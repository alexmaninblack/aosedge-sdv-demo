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

from aosedge_demo_orchestrator import service_assignment as assignment
from aosedge_demo_orchestrator.api import execute_operation
from aosedge_demo_orchestrator.application import DemoOrchestrator
from aosedge_demo_orchestrator.cli import build_parser, request_from_arguments
from aosedge_demo_orchestrator.environment import EnvironmentError, JOURNAL, atomic_json
from aosedge_demo_orchestrator.models import OperationRequest, VehicleTarget
from aosedge_demo_orchestrator.status import read_json
from aosedge_demo_orchestrator.unit_cloud import CloudFailure

OWNER = "11111111-1111-4111-8111-111111111111"
USER = "22222222-2222-4222-8222-222222222222"
SP = "33333333-3333-4333-8333-333333333333"
BRAKE = "44444444-4444-4444-8444-444444444444"
TIRE = "55555555-5555-4555-8555-555555555555"
UNIT = "66666666-6666-4666-8666-666666666666"
SUBJECT = "77777777-7777-4777-8777-777777777777"
DEFAULT = "88888888-8888-4888-8888-888888888888"
SET = "99999999-9999-4999-8999-999999999999"
VERSION = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
TEST = dict(unitId=UNIT, systemUid="test-uid", unitSetId=SET)


class AssignmentCloud:
    def __init__(self):
        self.user = dict(role="oem", ownerId=OWNER, userId=USER)
        self.denied = set()
        self.posts, self.reads = [], []
        self.subjects = [dict(id=DEFAULT, label="default", is_group=False, is_protected=True, priority=0, created_by=USER)]
        self.assigned, self.reported, self.services = [], [], []
        self.service_recipients = {BRAKE: [], TIRE: []}
        self.version_state = "ready"
        self.subject_created = dict(id=SUBJECT, label=assignment.LABEL, is_group=True,
            is_protected=False, priority=0, created_by=USER)
        self.runtime = []
        self.unit_value = dict(id=UNIT, system_uid=TEST["systemUid"], status="provisioned", online_status="Online", unit_sets=[SET])

    def require(self, *permissions):
        if set(permissions) & self.denied:
            raise CloudFailure("OEM_PERMISSION_MISSING:" + ",".join(sorted(set(permissions) & self.denied)))

    def unit(self, identity, nodes=False):
        self.require("units_read")
        return copy.deepcopy(self.unit_value)

    def call(self, path, method="GET", body=None, expected=200):
        if method != "GET":
            self.posts.append((path, method, copy.deepcopy(body), expected))
            if path == "subjects/":
                self.subjects.append(copy.deepcopy(self.subject_created))
                return copy.deepcopy(self.subject_created)
            if path.endswith("/units/"):
                self.assigned = [dict(id=UNIT, system_uid=TEST["systemUid"])]
                return dict(subject_id=SUBJECT, system_uids=body["system_uids"])
            if path.endswith("/services/"):
                service_id = body["service_ids"][0]
                self.services.append(dict(service=dict(id=service_id)))
                self.service_recipients[service_id] = [dict(id=UNIT, system_uid=TEST["systemUid"], oem_id=OWNER, subjects=[SUBJECT])]
                self.runtime.append(dict(subject=SUBJECT, service=dict(id=service_id), instances=[]))
                return dict(subject_id=SUBJECT, service_ids=body["service_ids"])
            raise AssertionError(path)
        self.reads.append(path)
        parts = urlsplit(path)
        key = parts.path
        if key == "unit-sets/" + SET + "/":
            return dict(id=SET, is_validation_set=True)
        if key in ("services/" + BRAKE + "/", "services/" + TIRE + "/"):
            identifier = key.split("/")[1]
            return dict(id=identifier, codename=("brake" if identifier == BRAKE else "tire") + "-health-service", service_provider_id=SP)
        if key == "subjects/" + SUBJECT + "/":
            return copy.deepcopy(next(row for row in self.subjects if row["id"] == SUBJECT))
        collections = {"subjects/": self.subjects, "subjects/" + SUBJECT + "/units/": self.assigned,
            "subjects/" + SUBJECT + "/units/reported/": self.reported, "subjects/" + SUBJECT + "/services/": self.services,
            "units/" + UNIT + "/subjects-services/": self.runtime}
        for identifier in (BRAKE, TIRE):
            collections["services/" + identifier + "/service-versions/"] = [dict(id=VERSION, version="8.0.0", container_state=self.version_state)]
            collections["services/" + identifier + "/units/"] = self.service_recipients[identifier]
            collections["units/" + UNIT + "/subjects-services/" + identifier + "/"] = [row for row in self.runtime if row["service"]["id"] == identifier]
        rows = collections[key]
        offset = int(parse_qs(parts.query)["offset"][0])
        return dict(total=len(rows), offset=offset, items=copy.deepcopy(rows[offset:offset + 100]))


class WorkerTests(unittest.TestCase):
    def setUp(self):
        self.cloud = AssignmentCloud()
        self.request = dict(action="service-assignment-step", ownerId=OWNER, team="brake", serviceProviderId=SP,
            publishedVersion="8.0.0", serviceId=BRAKE, test=TEST, subject={}, ownedServiceIds=[])

    def retained(self):
        self.cloud.subjects.append(copy.deepcopy(self.cloud.subject_created))
        self.request["subject"] = dict(id=SUBJECT, createdBy=USER)

    def test_exact_openapi_create_bind_assign_bodies_and_no_version_or_count(self):
        result = assignment.execute(self.cloud, dict(self.request, step="create"))
        self.request["subject"] = result["subject"]
        self.assertEqual("ACCEPTED", result["stage"])
        assignment.execute(self.cloud, dict(self.request, step="bind"))
        assignment.execute(self.cloud, dict(self.request, step="assign"))
        self.assertEqual([
            ("subjects/", "POST", {"label": assignment.LABEL, "is_group": True}, 201),
            ("subjects/" + SUBJECT + "/units/", "POST", {"system_uids": [TEST["systemUid"]]}, 201),
            ("subjects/" + SUBJECT + "/services/", "POST", {"service_ids": [BRAKE]}, 201)], self.cloud.posts)
        self.assertEqual(DEFAULT, self.cloud.subjects[0]["id"])
        self.assertEqual("OBSERVED", assignment.execute(self.cloud, dict(self.request, step="assign"))["stage"])
        self.assertEqual(3, len(self.cloud.posts))

    def test_unrecorded_collision_is_not_adopted(self):
        self.cloud.subjects.append(copy.deepcopy(self.cloud.subject_created))
        result = assignment.execute(self.cloud, dict(self.request, step="create"))
        self.assertEqual(("BLOCKED", False), (result["stage"], result["attempted"]))
        self.assertIn("COLLISION", result["reason"])
        self.assertEqual([], self.cloud.posts)

    def test_current_test_owner_sp_and_ready_gates(self):
        for field, value in (("ownerId", SP), ("serviceProviderId", OWNER), ("team", "foreign"), ("publishedVersion", "9.0.0")):
            with self.subTest(field=field):
                result = assignment.execute(self.cloud, dict(self.request, step="create", **{field: value}))
                self.assertEqual(("BLOCKED", False), (result["stage"], result["attempted"]))
        self.cloud.unit_value["system_uid"] = "other-uid"
        self.assertEqual("BLOCKED", assignment.execute(self.cloud, dict(self.request, step="create"))["stage"])
        self.assertEqual([], self.cloud.posts)

    def test_no_production_or_reported_peer_or_unrelated_service(self):
        self.retained()
        for target in (self.cloud.assigned, self.cloud.reported):
            target.append(dict(id=SP, system_uid="production"))
            result = assignment.execute(self.cloud, dict(self.request, step="bind"))
            self.assertIn("NON_TEST", result["reason"])
            target.clear()
        self.cloud.assigned.append(dict(id=UNIT, system_uid=TEST["systemUid"]))
        self.cloud.services.append(dict(service=dict(id=SP)))
        self.assertIn("UNRELATED_SERVICE", assignment.execute(self.cloud, dict(self.request, step="assign"))["reason"])
        self.assertEqual([], self.cloud.posts)

    def test_protected_wrong_creator_group_and_stale_assignments_fail_closed(self):
        self.retained()
        row = self.cloud.subjects[-1]
        for key, invalid in (("is_protected", True), ("is_group", False), ("created_by", SP), ("priority", 1)):
            original = row[key]
            row[key] = invalid
            self.assertEqual("BLOCKED", assignment.execute(self.cloud, dict(self.request, step="bind"))["stage"])
            row[key] = original
        self.cloud.services.append(dict(service=dict(id=BRAKE)))
        self.assertIn("STALE_SERVICE", assignment.execute(self.cloud, dict(self.request, step="bind"))["reason"])

    def test_post_transport_and_bad_response_are_uncertain(self):
        original = self.cloud.call
        self.cloud.call = lambda path, method="GET", *args, **kw: original(path, method, *args, **kw) if method == "GET" else (_ for _ in ()).throw(TimeoutError("secret transport"))
        result = assignment.execute(self.cloud, dict(self.request, step="create"))
        self.assertEqual(("UNCERTAIN", True), (result["stage"], result["attempted"]))
        self.assertNotIn("secret", json.dumps(result))
        self.cloud.call = original
        self.cloud.subject_created["created_by"] = SP
        result = assignment.execute(self.cloud, dict(self.request, step="create"))
        self.assertEqual(("UNCERTAIN", True), (result["stage"], result["attempted"]))

    def test_missing_permission_is_explicit_no_attempt(self):
        self.cloud.denied.add("subjects_create")
        result = assignment.execute(self.cloud, dict(self.request, step="create"))
        self.assertEqual(("BLOCKED", False), (result["stage"], result["attempted"]))
        self.assertEqual([], self.cloud.posts)

    def test_pagination_uses_nested_identity_and_rejects_changed_total(self):
        cloud = Mock()
        cloud.call.side_effect = [dict(total=101, offset=0, items=[dict(service=dict(id=str(i))) for i in range(100)]),
            dict(total=102, offset=100, items=[dict(service=dict(id="100"))])]
        with self.assertRaisesRegex(CloudFailure, "CHANGED"):
            assignment._pages(cloud, "fixture/", lambda row: row["service"]["id"])
        cloud.call = Mock(return_value=dict(total=2, offset=0, items=[dict(id=SUBJECT), dict(id=SUBJECT)]))
        with self.assertRaisesRegex(CloudFailure, "DUPLICATE"):
            assignment._pages(cloud, "fixture/", lambda row: row["id"])


class JournalTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / JOURNAL).parent.mkdir(parents=True)
        self.environment = SimpleNamespace(root=self.root, _writer=contextlib.nullcontext,
            catalog=SimpleNamespace(project=self.root / "artifacts"))
        state = dict(kind="democtl.current-run", cloudBinding=dict(ownerId=OWNER),
            vehicles=dict(test=dict(TEST, localVmId="owned-test", cloud=dict(lifecycle="ONLINE"))))
        atomic_json(self.root / JOURNAL, state)
        self.cloud = AssignmentCloud()
        self.loss = None
        self.units = SimpleNamespace(_cloud=self.call)
        self.service = assignment.ServiceAssignment(self.environment, self.units)
        self.service._publication = Mock(side_effect=lambda identifier: dict(team="brake" if identifier == BRAKE else "tire",
            serviceProviderId=SP, publishedVersion="8.0.0"))

    def call(self, action, **values):
        # Assert intent reached durable storage before every external attempt.
        if action == "service-assignment-step":
            state = read_json(self.root / JOURNAL)
            attempt = state["demoSubject"]["create"] if values["step"] == "create" else state["serviceOperations"][values["serviceId"]]["steps"][values["step"]]
            self.assertIs(attempt["attempted"], True)
            if self.loss == (values["step"], "before"):
                self.loss = None
                raise EnvironmentError("UNIT_WORKER_RESPONSE_UNAVAILABLE")
        try:
            result = assignment.execute(self.cloud, dict(values, action=action))
        except CloudFailure as error:
            raise EnvironmentError(str(error)) from None
        if action == "service-assignment-step" and self.loss == (values["step"], "after"):
            self.loss = None
            raise EnvironmentError("UNIT_WORKER_RESPONSE_UNAVAILABLE")
        return result

    def test_first_repeat_and_independent_peer_preserve_default_and_binding(self):
        result = self.service.assign(BRAKE)
        self.assertEqual(("ASSIGNED", False), (result["state"], result["noOp"]))
        self.assertEqual(3, len(self.cloud.posts))
        repeated = self.service.assign(BRAKE)
        self.assertEqual(("ASSIGNED", True), (repeated["state"], repeated["noOp"]))
        self.assertFalse(repeated["runtimeQualified"])
        self.assertEqual("ASSIGNED", self.service.assign(TIRE)["state"])
        self.assertEqual(4, len(self.cloud.posts))
        self.assertEqual({BRAKE, TIRE}, {row["service"]["id"] for row in self.cloud.services})
        self.assertEqual(DEFAULT, self.cloud.subjects[0]["id"])
        self.assertEqual(2, len(self.cloud.subjects))

    def test_lost_create_never_repeats_or_adopts_by_label(self):
        self.loss = ("create", "after")
        self.assertEqual("UNCERTAIN", self.service.assign(BRAKE)["state"])
        result = self.service.assign(BRAKE)
        self.assertEqual("SERVICE_SUBJECT_CREATE_ID_UNCERTAIN_NO_REPLAY", result["reason"])
        self.assertEqual(1, len(self.cloud.posts))
        self.assertNotIn("id", read_json(self.root / JOURNAL)["demoSubject"])

    def test_lost_known_binding_can_reconcile_without_replay(self):
        for step in ("bind", "assign"):
            with self.subTest(step=step):
                self.setUp()
                self.loss = (step, "after")
                self.assertEqual("UNCERTAIN", self.service.assign(BRAKE)["state"])
                self.assertEqual("ASSIGNED", self.service.assign(BRAKE)["state"])
                self.assertEqual(3, len(self.cloud.posts))

    def test_unconfirmed_absent_binding_does_not_replay(self):
        self.loss = ("bind", "before")
        self.assertEqual("UNCERTAIN", self.service.assign(BRAKE)["state"])
        result = self.service.assign(BRAKE)
        self.assertIn("BIND_NOT_OBSERVED_NO_REPLAY", result["reason"])
        self.assertEqual(1, len(self.cloud.posts))

    def test_known_failed_preflight_can_be_explicitly_repeated(self):
        self.cloud.denied.add("subjects_create")
        self.assertEqual("BLOCKED", self.service.assign(BRAKE)["state"])
        self.cloud.denied.clear()
        self.assertEqual("ASSIGNED", self.service.assign(BRAKE)["state"])
        self.assertEqual(3, len(self.cloud.posts))

    def test_changed_test_binding_and_symlink_block_without_cloud(self):
        self.service.assign(BRAKE)
        state = read_json(self.root / JOURNAL)
        state["vehicles"]["test"]["systemUid"] = "changed"
        atomic_json(self.root / JOURNAL, state)
        with self.assertRaisesRegex(EnvironmentError, "RECORDED_BINDING_CHANGED"):
            self.service.assign(BRAKE)
        self.assertEqual(3, len(self.cloud.posts))

    def test_missing_published_receipt_never_calls_cloud(self):
        del self.service._publication
        with self.assertRaisesRegex(EnvironmentError, "READY_PUBLICATION_REQUIRED"):
            self.service.assign(BRAKE)
        self.assertEqual([], self.cloud.posts)

    def test_ready_publication_mapping_requires_exact_accepted_bundle_and_sp(self):
        del self.service._publication
        directory = self.environment.catalog.project / "services/brake/releases/8.0.0"
        directory.mkdir(parents=True)
        prepared = dict(schemaVersion=1, state="PREPARED", team="brake", version="8.0.0",
            releaseHandle="brake/8.0.0", packagePath=str(directory), files={str(n): {} for n in range(4)},
            serviceProviderId=SP, serviceId=None)
        receipt = dict(attempted=True, deploymentId=VERSION, lastObservation=dict(stage="READY", source="AOS_CLOUD_ONLY",
            serviceId=BRAKE, version="8.0.0", deploymentId=VERSION, bundleState="done", versionState="ready"))
        atomic_json(directory / "prepared.json", prepared)
        atomic_json(directory / "publication.json", receipt)
        self.assertEqual(dict(team="brake", serviceProviderId=SP, publishedVersion="8.0.0"), self.service._publication(BRAKE))
        receipt["lastObservation"]["deploymentId"] = SP
        atomic_json(directory / "publication.json", receipt)
        with self.assertRaisesRegex(EnvironmentError, "RECEIPT_MISMATCH"):
            self.service._publication(BRAKE)

    def test_journal_symlink_blocks_before_cloud(self):
        original = self.root / JOURNAL
        moved = self.root / "fixture-journal.json"
        original.rename(moved)
        original.symlink_to(moved)
        with self.assertRaisesRegex(EnvironmentError, "JOURNAL_UNSAFE"):
            self.service.assign(BRAKE)
        self.assertEqual([], self.cloud.posts)


class SurfaceTests(unittest.TestCase):
    def test_cli_fixed_catalog_and_target_but_browser_stays_read_only(self):
        request = request_from_arguments(build_parser().parse_args(["service", "assign", BRAKE, "--target", "test"]))
        self.assertEqual((BRAKE, VehicleTarget.TEST), (request.service_id, request.target))
        with self.assertRaises(ValueError):
            execute_operation(dict(domain="service", action="assign", service_id=BRAKE, target="test"), Mock())
        app = DemoOrchestrator.__new__(DemoOrchestrator)
        for target in (None, VehicleTarget.PRODUCTION, VehicleTarget.ALL):
            result = app.execute(OperationRequest("service", "assign", target, service_id=BRAKE))
            self.assertEqual("BLOCKED", result.state.value)


if __name__ == "__main__":
    unittest.main()
