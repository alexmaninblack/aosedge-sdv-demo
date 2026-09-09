# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import copy
import json
import subprocess
from datetime import datetime, timedelta, timezone
from unittest import TestCase
from unittest.mock import Mock, patch

import test_images_environment as fixtures
from aosedge_demo_orchestrator.backend_context import CONTEXT, project_context
from aosedge_demo_orchestrator.backend_retirement import BackendRetirement, COUNTS, FOUNDATION
from aosedge_demo_orchestrator.backends import BackendService, TEAMS
from aosedge_demo_orchestrator.environment import EnvironmentError, JOURNAL, atomic_json, digest
from aosedge_demo_orchestrator.status import read_json

TOKEN = "fixture-only-confirmation-token-never-persist-" + "x" * 32


class FixtureBackend(BackendService):
    def __init__(self, environment):
        super().__init__(environment)
        self.resources = {}
        self.actions = []

    def _inspect(self, kind, name):
        return copy.deepcopy(self.resources.get((kind, name)))

    def _image(self, image):
        return dict(Id=image, Architecture="arm64")

    def _docker(self, kind, action, identity):
        if action != "rm":
            raise AssertionError("Only exact remove")
        self.actions.append((kind, action, identity))
        candidates = [key for key, value in self.resources.items() if key[0] == kind and (key[1] == identity or value.get("Id") == identity)]
        if len(candidates) != 1:
            raise AssertionError("Exact owned resource only")
        del self.resources[candidates[0]]

    def execute(self, action, team):
        if action != "stop":
            raise AssertionError("No build, start or reset")
        self.actions.append(("stop", team))
        self.resources[("container", "aosedge-demo-" + team + "-cloud")]["State"]["Running"] = False
        state = read_json(self.root / JOURNAL)
        state["backends"][team]["state"] = "STOPPED"
        atomic_json(self.root / JOURNAL, state)
        return dict(state="STOPPED")


class BackendRetirementTests(TestCase):
    setUp = fixtures.ImagesAndCreateTests.setUp
    create = fixtures.ImagesAndCreateTests.create

    def backend_fixture(self, production=True):
        state = self.create("all" if production else "test")
        for role, item in state["vehicles"].items():
            item.update(systemUid=role + "-uid", unitId=item["localVmId"], nodeId=item["localVmId"], unitSetId=item["localVmId"],
                cloud=dict(lifecycle="DELETED" if role == "test" else "ONLINE", absenceConfirmed=role == "test"),
                runtime=dict(state="STOPPED" if role == "test" else "RUNNING", pid=None if role == "test" else 444))
        backend = FixtureBackend(self.service)
        owner = state["operations"][0]["id"]
        state["backends"] = {}
        directory = self.service._directory(".run/demo-current/backends")
        self.service._directory(".run/demo-current/backends/context")
        atomic_json(self.root / CONTEXT, project_context(state))
        for index, team in enumerate(TEAMS):
            image = "sha256:" + ("a" if index == 0 else "b") * 64
            name = "aosedge-demo-" + team + "-cloud"
            compose = directory / (team + "-compose.json")
            atomic_json(compose, backend._spec(state, team, image))
            state["backends"][team] = dict(owner=owner, imageId=image, state="RUNNING", containerName=name,
                sourceRevision="c" * 40, composePath=str(compose.relative_to(self.root)))
            labels = {"tech.aosedge.demo.owner": owner, "tech.aosedge.demo.team": team}
            backend.resources[("container", name)] = dict(Id=("1" if index == 0 else "2") * 64,
                Image=image, Config=dict(Labels=labels), State=dict(Running=True, Health=dict(Status="healthy")),
                Mounts=[dict(Type="volume", Name="aosedge_demo_" + team + "_cloud_v1", Destination="/data", RW=True),
                        dict(Type="bind", Source=str((self.root / CONTEXT).parent), Destination="/run/demo-control/context", RW=False)])
            backend.resources[("volume", "aosedge_demo_" + team + "_cloud_v1")] = dict(Labels=dict(labels))
            backend.resources[("network", name + "-v1")] = dict(Labels=dict(labels))
        atomic_json(self.root / JOURNAL, state)
        self.backend = backend
        self.cleanup = BackendRetirement(backend)
        self.matching = dict.fromkeys(COUNTS, 0)
        self.matching["messages"] = 2
        self.nonmatching = dict.fromkeys(COUNTS, 0)
        if production:
            self.nonmatching["messages"] = 7
        self.calls = []
        self.cleanup._private = Mock(side_effect=self.private)
        self.addCleanup(patch.stopall)
        patch.object(self.service, "_assert_unheld").start()
        return state

    def private(self, team, identity, operation, payload=None):
        self.calls.append((team, operation))
        if team == "tire":
            return dict(FOUNDATION)
        if operation == "empty-proof":
            counts = {key: self.matching[key] + self.nonmatching[key] for key in COUNTS}
            return dict(schemaVersion=1, contractVersion="1.0.0", state="NONEMPTY" if any(counts.values()) else "EMPTY",
                databaseSchemaVersion=2, recordCounts=counts, observedAt=datetime.now(timezone.utc).isoformat())
        self.assertEqual(["test-uid"], payload["systemUids"])
        if operation == "preview":
            return dict(schemaVersion=1, contractVersion="1.0.0", systemUids=["test-uid"],
                recordCounts=dict(self.matching), nonmatchingRecordCounts=dict(self.nonmatching),
                recordSetSha256="a" * 64, confirmationToken=TOKEN,
                expiresAt=(datetime.now(timezone.utc) + timedelta(seconds=60)).isoformat())
        self.assertEqual(TOKEN, payload["confirmationToken"])
        before = self.matching
        self.matching = dict.fromkeys(COUNTS, 0)
        return dict(schemaVersion=1, contractVersion="1.0.0", systemUids=["test-uid"], deletedRecordCounts=before,
            remainingMatchingRecordCounts=dict(self.matching), nonmatchingRecordCounts=dict(self.nonmatching),
            nonmatchingRecordSetSha256="b" * 64, completedAt=datetime.now(timezone.utc).isoformat())

    def test_dual_cleanup_preserves_peer_volume_owner_and_removes_current_test_context(self):
        state = self.backend_fixture()
        peer = copy.deepcopy(state["vehicles"]["production"])
        owner = state["operations"][0]["id"]
        self.assertTrue(self.cleanup.confirm_test_cleanup(state))
        self.assertEqual(peer, state["vehicles"]["production"])
        self.assertEqual(7, self.nonmatching["messages"])
        self.assertEqual(6, len(self.backend.resources))
        self.assertFalse((self.root / CONTEXT).exists())
        self.assertEqual([("stop", "brake"), ("stop", "tire")], self.backend.actions)
        for team in TEAMS:
            self.assertEqual(owner, state["backends"][team]["owner"])
            self.assertEqual("STOPPED", state["backends"][team]["state"])
        self.assertEqual("FOUNDATION_ONLY", state["backends"]["tire"]["cleanup"]["scope"])
        self.assertNotIn(TOKEN, (self.root / JOURNAL).read_text())
        self.assertEqual([("brake", "preview"), ("brake", "execute"), ("brake", "preview"), ("tire", "foundation-proof")], self.calls)

    def test_repeated_dual_cleanup_reuses_only_proven_stopped_owned_generation(self):
        state = self.backend_fixture()
        self.cleanup.confirm_test_cleanup(state)
        calls = len(self.calls)
        self.assertTrue(self.cleanup.confirm_test_cleanup(state))
        self.assertEqual(calls, len(self.calls))
        self.backend.resources[("container", "aosedge-demo-brake-cloud")]["State"]["Running"] = True
        with self.assertRaisesRegex(EnvironmentError, "RESTARTED_AFTER_PROOF"):
            self.cleanup.confirm_test_cleanup(state)

    def test_single_cleanup_proves_total_empty_before_fixed_resource_removal(self):
        state = self.backend_fixture(production=False)
        self.assertTrue(self.cleanup.confirm_test_cleanup(state))
        self.assertEqual({}, self.backend.resources)
        self.assertNotIn("backends", state)
        self.assertNotIn("backends", read_json(self.root / JOURNAL))
        self.assertFalse((self.root / ".run/demo-current/backends").exists())
        self.assertEqual(6, len([action for action in self.backend.actions if len(action) == 3]))
        self.assertNotIn(TOKEN, (self.root / JOURNAL).read_text())

    def test_single_foreign_uid_data_blocks_volume_reset_and_preserves_state(self):
        state = self.backend_fixture(production=False)
        self.nonmatching["events"] = 1
        with self.assertRaisesRegex(EnvironmentError, "NONMATCHING_DATA_PRESERVED"):
            self.cleanup.confirm_test_cleanup(state)
        self.assertEqual(6, len(self.backend.resources))
        self.assertIn("backends", read_json(self.root / JOURNAL))
        self.assertTrue((self.root / CONTEXT).exists())

    def test_missing_total_counts_is_not_inferred_from_hash_or_zero_matching(self):
        state = self.backend_fixture(production=False)
        def older(*args):
            response = self.private(*args)
            response.pop("nonmatchingRecordCounts", None)
            return response
        self.cleanup._private.side_effect = older
        with self.assertRaisesRegex(EnvironmentError, "PREVIEW_INVALID"):
            self.cleanup.confirm_test_cleanup(state)
        self.assertEqual([], self.backend.actions)
        self.assertEqual(2, self.matching["messages"])

    def test_private_response_loss_is_journaled_and_zero_reconciles_without_second_execute(self):
        state = self.backend_fixture()
        def lost(team, identity, action, payload=None):
            result = self.private(team, identity, action, payload)
            if action == "execute":
                raise EnvironmentError("BACKEND_PRIVATE_RESPONSE_UNCERTAIN")
            return result
        self.cleanup._private.side_effect = lost
        with self.assertRaisesRegex(EnvironmentError, "RESPONSE_UNCERTAIN"):
            self.cleanup.confirm_test_cleanup(state)
        self.assertEqual("UNCERTAIN", state["backends"]["brake"]["cleanup"]["state"])
        self.cleanup._private.side_effect = self.private
        self.assertTrue(self.cleanup.confirm_test_cleanup(state))
        self.assertEqual(1, self.calls.count(("brake", "execute")))

    def test_unknown_response_with_remaining_records_never_replays_execute(self):
        state = self.backend_fixture()
        def lost(team, identity, action, payload=None):
            if action == "execute":
                raise EnvironmentError("BACKEND_PRIVATE_RESPONSE_UNCERTAIN")
            return self.private(team, identity, action, payload)
        self.cleanup._private.side_effect = lost
        with self.assertRaises(EnvironmentError):
            self.cleanup.confirm_test_cleanup(state)
        self.cleanup._private.side_effect = self.private
        with self.assertRaisesRegex(EnvironmentError, "UNCERTAIN_OR_NEW_RECORDS"):
            self.cleanup.confirm_test_cleanup(state)
        self.assertEqual(2, self.matching["messages"])

    def test_context_unlink_interruption_resumes_without_token_or_context_recreation(self):
        state = self.backend_fixture()
        original = self.service._unlink_owned
        def interrupted(path, identity):
            original(path, identity)
            raise OSError("after unlink")
        with patch.object(self.service, "_unlink_owned", side_effect=interrupted):
            with self.assertRaises(OSError):
                self.cleanup.confirm_test_cleanup(state)
        self.assertEqual("REMOVE_PENDING", state["backends"]["brake"]["cleanup"]["contextRemoval"])
        self.assertTrue(self.cleanup.confirm_test_cleanup(state))
        self.assertFalse((self.root / CONTEXT).exists())
        self.assertEqual(1, self.calls.count(("brake", "execute")))

    def test_single_container_removal_response_loss_resumes_exact_remaining_resources(self):
        state = self.backend_fixture(production=False)
        original = self.backend._docker
        def interrupted(*args):
            original(*args)
            raise EnvironmentError("response lost")
        with patch.object(self.backend, "_docker", side_effect=interrupted):
            with self.assertRaisesRegex(EnvironmentError, "response lost"):
                self.cleanup.confirm_test_cleanup(state)
        self.assertTrue(self.cleanup.confirm_test_cleanup(state))
        self.assertEqual({}, self.backend.resources)
        self.assertEqual(1, len([call for call in self.backend.actions if call == ("container", "rm", "1" * 64)]))

    def test_partial_stop_resumes_stopping_without_requiring_stopped_backend_to_serve_reads(self):
        state = self.backend_fixture()
        original = self.backend.execute
        def interrupted(action, team):
            original(action, team)
            if team == "brake":
                raise EnvironmentError("stop response lost")
        with patch.object(self.backend, "execute", side_effect=interrupted):
            with self.assertRaisesRegex(EnvironmentError, "stop response lost"):
                self.cleanup.confirm_test_cleanup(state)
        self.assertEqual("STOPPED", state["backends"]["brake"]["state"])
        self.assertEqual(read_json(self.root / JOURNAL), state)
        calls = len(self.calls)
        self.assertTrue(self.cleanup.confirm_test_cleanup(state))
        self.assertEqual(calls, len(self.calls))

    def test_foreign_resource_or_mount_blocks_before_private_mutation(self):
        state = self.backend_fixture()
        resource = self.backend.resources[("volume", "aosedge_demo_brake_cloud_v1")]
        resource["Labels"]["tech.aosedge.demo.owner"] = "foreign"
        with self.assertRaisesRegex(EnvironmentError, "FOREIGN_VOLUME"):
            self.cleanup.confirm_test_cleanup(state)
        self.assertEqual([], self.calls)
        resource["Labels"]["tech.aosedge.demo.owner"] = state["operations"][0]["id"]
        self.backend.resources[("container", "aosedge-demo-brake-cloud")]["Mounts"][0]["Name"] = "foreign"
        with self.assertRaisesRegex(EnvironmentError, "MOUNT_BINDING"):
            self.cleanup.confirm_test_cleanup(state)

    def test_context_mismatch_and_unknown_tire_product_schema_preserve_data_ownership(self):
        state = self.backend_fixture()
        def future_tire(team, identity, operation, payload=None):
            result = self.private(team, identity, operation, payload)
            if team == "tire":
                result["productIngestion"] = True
            return result
        self.cleanup._private.side_effect = future_tire
        with self.assertRaisesRegex(EnvironmentError, "TIRE_FOUNDATION"):
            self.cleanup.confirm_test_cleanup(state)
        self.assertTrue((self.root / CONTEXT).exists())
        self.assertEqual([], self.backend.actions)

    def test_token_transport_is_stdin_only_and_never_echoes_private_errors(self):
        self.backend_fixture()
        cleanup = BackendRetirement(self.backend)
        private = dict(schemaVersion=1, contractVersion="1.0.0", systemUids=["test-uid"], confirmationToken=TOKEN)
        with patch("shutil.which", return_value="/fixed/docker"), patch("subprocess.run", return_value=Mock(returncode=0,
                stdout=json.dumps(dict(status=200, body=dict(ok=True))))) as run:
            self.assertEqual(dict(ok=True), cleanup._private("brake", "1" * 64, "execute", private))
        self.assertNotIn(TOKEN, " ".join(run.call_args.args[0]))
        self.assertIn(TOKEN, run.call_args.kwargs["input"])
        with patch("shutil.which", return_value="/fixed/docker"), patch("subprocess.run",
                side_effect=subprocess.TimeoutExpired("private", 12, output=TOKEN)):
            with self.assertRaisesRegex(EnvironmentError, "^BACKEND_PRIVATE_RESPONSE_UNCERTAIN$"):
                cleanup._private("brake", "1" * 64, "execute", private)
        self.assertNotIn(TOKEN, (self.root / JOURNAL).read_text())

    def test_zero_record_counts_do_not_replace_whole_store_schema_proof(self):
        state = self.backend_fixture(production=False)
        def bad_store(team, identity, operation, payload=None):
            if operation == "empty-proof":
                raise EnvironmentError("BACKEND_PRIVATE_RESPONSE_FAILED")
            return self.private(team, identity, operation, payload)
        self.cleanup._private.side_effect = bad_store
        with self.assertRaisesRegex(EnvironmentError, "PRIVATE_RESPONSE_FAILED"):
            self.cleanup.confirm_test_cleanup(state)
        self.assertEqual(6, len(self.backend.resources))
        self.assertIn("backends", read_json(self.root / JOURNAL))

    def test_absent_unit_identity_is_not_implicitly_authorization_to_erase_store(self):
        state = self.backend_fixture(production=False)
        state["vehicles"]["test"].pop("systemUid")
        with self.assertRaisesRegex(EnvironmentError, "RETIRED_STOPPED_TEST"):
            self.cleanup.confirm_test_cleanup(state)
        self.assertEqual([], self.calls)
        self.assertEqual(6, len(self.backend.resources))

    def unprovisioned(self, production=False):
        state = self.backend_fixture(production=production)
        test = state["vehicles"]["test"]
        for key in ("unitId", "nodeId", "systemUid", "unitSetId", "cloud"):
            test.pop(key, None)
        test["runtime"] = dict(state="STOPPED", pid=None, everStarted=True,
            stopProof=dict(unprovisioned=True, overlaySha256=digest(self.root / test["overlay"])))
        (self.root / CONTEXT).unlink()
        atomic_json(self.root / JOURNAL, state)
        return state

    def test_unprovisioned_single_uses_empty_proofs_without_invented_uid_or_selector(self):
        state = self.unprovisioned()
        self.matching = dict.fromkeys(COUNTS, 0)
        self.assertTrue(self.cleanup.confirm_unprovisioned_cleanup(state))
        self.assertEqual([("brake", "empty-proof"), ("tire", "foundation-proof")], self.calls)
        self.assertEqual({}, self.backend.resources)
        self.assertNotIn("backends", state)
        self.assertNotIn("systemUid", state["vehicles"]["test"])

    def test_unprovisioned_dual_preserves_nonempty_storage_without_test_absence_claim(self):
        state = self.unprovisioned(production=True)
        peer = copy.deepcopy(state["vehicles"]["production"])
        self.assertTrue(self.cleanup.confirm_unprovisioned_cleanup(state))
        self.assertEqual(peer, state["vehicles"]["production"])
        self.assertEqual(6, len(self.backend.resources))
        self.assertEqual(2, self.matching["messages"])
        self.assertEqual(7, self.nonmatching["messages"])
        proof = state["backends"]["brake"]["cleanup"]
        self.assertEqual("UNPROVISIONED_STORE_OBSERVATION", proof["scope"])
        self.assertNotIn("matchingRecordCounts", proof)
        self.assertNotIn("systemUid", proof)
        self.assertFalse(proof["wholeStoreEmpty"])
        calls = len(self.calls)
        self.assertTrue(self.cleanup.confirm_unprovisioned_cleanup(state))
        self.assertEqual(calls, len(self.calls))

    def test_unprovisioned_single_nonempty_store_is_never_erased(self):
        state = self.unprovisioned()
        with self.assertRaisesRegex(EnvironmentError, "NONMATCHING_DATA_PRESERVED"):
            self.cleanup.confirm_unprovisioned_cleanup(state)
        self.assertEqual(6, len(self.backend.resources))
        self.assertEqual([], self.backend.actions)

    def test_unprovisioned_partial_cloud_attempt_or_unknown_stop_proof_blocks(self):
        state = self.unprovisioned()
        for change in (dict(cloud={}), dict(systemUid="partial-sdk-uid"),
                       dict(runtime=dict(state="STOPPED", pid=None, everStarted=True))):
            candidate = copy.deepcopy(state)
            candidate["vehicles"]["test"].update(change)
            with self.assertRaisesRegex(EnvironmentError, "NEVER_PROVISIONED_TEST"):
                self.cleanup.confirm_unprovisioned_cleanup(candidate)
        self.assertEqual([], self.calls)

    def test_unprovisioned_stale_context_is_not_unlinked_or_adopted(self):
        state = self.unprovisioned()
        atomic_json(self.root / CONTEXT, dict(stale="old-test"))
        with self.assertRaisesRegex(EnvironmentError, "CONTEXT_MUST_BE_ABSENT"):
            self.cleanup.confirm_unprovisioned_cleanup(state)
        self.assertTrue((self.root / CONTEXT).exists())

    def test_unprovisioned_single_interrupted_resource_cleanup_resumes_without_new_proof(self):
        state = self.unprovisioned()
        self.matching = dict.fromkeys(COUNTS, 0)
        original = self.backend._docker
        def interrupted(*args):
            original(*args)
            raise EnvironmentError("removed before response loss")
        with patch.object(self.backend, "_docker", side_effect=interrupted):
            with self.assertRaisesRegex(EnvironmentError, "response loss"):
                self.cleanup.confirm_unprovisioned_cleanup(state)
        self.assertTrue(self.cleanup.confirm_unprovisioned_cleanup(state))
        self.assertEqual({}, self.backend.resources)
        self.assertEqual([("brake", "empty-proof"), ("tire", "foundation-proof")], self.calls)

    def test_owned_test_disk_must_be_released_before_product_records_are_deleted(self):
        state = self.backend_fixture()
        with patch.object(self.service, "_assert_unheld", side_effect=EnvironmentError("CLEANUP_FILE_IN_USE")):
            with self.assertRaisesRegex(EnvironmentError, "FILE_IN_USE"):
                self.cleanup.confirm_test_cleanup(state)
        self.assertEqual([], self.calls)
        self.assertEqual(2, self.matching["messages"])

    def test_unprovisioned_changed_stopped_overlay_does_not_erase_backend_store(self):
        state = self.unprovisioned()
        state["vehicles"]["test"]["runtime"]["stopProof"]["overlaySha256"] = "f" * 64
        with self.assertRaisesRegex(EnvironmentError, "STOPPED_UNPROVISIONED_PROOF"):
            self.cleanup.confirm_unprovisioned_cleanup(state)
        self.assertEqual([], self.calls)
