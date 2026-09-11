# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import copy
from datetime import datetime, timedelta, timezone
from unittest import TestCase
from unittest.mock import Mock

from test_backend_retirement import BackendRetirementTests, TOKEN
from aosedge_demo_orchestrator.backend_retirement import TIRE_COUNTS
from aosedge_demo_orchestrator.environment import EnvironmentError, JOURNAL, atomic_json


class TireProductRetirementTests(TestCase):
    setUp = BackendRetirementTests.setUp
    create = BackendRetirementTests.create
    backend_fixture = BackendRetirementTests.backend_fixture
    private = BackendRetirementTests.private

    def product(self, production=True):
        state = self.backend_fixture(production)
        state["backends"]["tire"]["privateCleanupProtocol"] = "tire-product-v1"
        self.tire_matching = dict.fromkeys(TIRE_COUNTS, 0)
        self.tire_matching.update(messages=3, functionStatus=2)
        self.tire_peer = dict.fromkeys(TIRE_COUNTS, 0)
        self.tire_peer["assessments"] = 7 if production else 0
        self.cleanup._private = Mock(side_effect=self.tire_private)
        atomic_json(self.root / JOURNAL, state)
        return state

    def tire_private(self, team, identity, operation, payload=None):
        if team != "tire":
            return self.private(team, identity, operation, payload)
        self.calls.append((team, operation))
        if operation == "empty-proof":
            counts = {key: self.tire_matching[key] + self.tire_peer[key] for key in TIRE_COUNTS}
            return dict(schemaVersion=1, contractVersion="1.0.0", state="NONEMPTY" if any(counts.values()) else "EMPTY",
                databaseSchemaVersion=2, recordCounts=counts, observedAt=datetime.now(timezone.utc).isoformat())
        self.assertEqual(["test-uid"], payload["systemUids"])
        if operation == "preview":
            return dict(schemaVersion=1, systemUids=["test-uid"], recordCounts=dict(self.tire_matching),
                nonmatchingRecordCounts=dict(self.tire_peer), recordSetSha256="a" * 64,
                nonmatchingRecordSetSha256="b" * 64, confirmationToken=TOKEN,
                expiresAt=(datetime.now(timezone.utc) + timedelta(seconds=60)).isoformat())
        self.assertEqual("execute", operation)
        self.assertEqual(TOKEN, payload["confirmationToken"])
        previous, self.tire_matching = self.tire_matching, dict.fromkeys(TIRE_COUNTS, 0)
        return dict(schemaVersion=1, contractVersion="1.0.0", state="CLEANED", systemUids=["test-uid"],
            deletedRecordCounts=previous, remainingRecordCounts=dict(self.tire_matching),
            nonmatchingRecordCounts=dict(self.tire_peer), nonmatchingRecordSetSha256="b" * 64,
            completedAt=datetime.now(timezone.utc).isoformat())

    def test_brake_migration_does_not_enable_tire_schema_three(self):
        state = self.product(False)
        state["backends"]["tire"]["cleanup"] = {}
        self.cleanup._empty_store(state, allow_nonempty=True, team="tire")
        def response(team, identity, operation, payload=None):
            value = self.tire_private(team, identity, operation, payload)
            value["databaseSchemaVersion"] = 3
            return value
        self.cleanup._private = Mock(side_effect=response)
        with self.assertRaisesRegex(EnvironmentError, "BACKEND_WHOLE_STORE_EMPTY_PROOF_UNAVAILABLE"):
            self.cleanup._empty_store(state, allow_nonempty=True, team="tire")

    def test_product_test_cleanup_preserves_peer_and_never_uses_foundation_proof(self):
        state = self.product()
        peer = copy.deepcopy(state["vehicles"]["production"])
        self.assertTrue(self.cleanup.confirm_test_cleanup(state))
        self.assertEqual(peer, state["vehicles"]["production"])
        self.assertEqual(7, self.tire_peer["assessments"])
        self.assertEqual("EXACT_TEST_PRODUCT_DATA", state["backends"]["tire"]["cleanup"]["scope"])
        self.assertNotIn(("tire", "foundation-proof"), self.calls)
        self.assertNotIn(TOKEN, (self.root / JOURNAL).read_text())

    def test_single_store_requires_both_product_empty_proofs(self):
        state = self.product(False)
        self.assertTrue(self.cleanup.confirm_test_cleanup(state))
        self.assertIn(("tire", "empty-proof"), self.calls)
        self.assertEqual({}, self.backend.resources)

    def test_nonmatching_tire_data_prevents_single_store_removal(self):
        state = self.product(False)
        self.tire_peer["messages"] = 1
        with self.assertRaisesRegex(EnvironmentError, "NONMATCHING_DATA_PRESERVED"):
            self.cleanup.confirm_test_cleanup(state)
        self.assertFalse(any("rm" in action for action in self.backend.actions))

    def test_changed_peer_digest_marks_uncertain_and_never_replays_delete(self):
        state = self.product()
        def corrupt(team, identity, operation, payload=None):
            result = self.tire_private(team, identity, operation, payload)
            if team == "tire" and operation == "execute":
                result["nonmatchingRecordSetSha256"] = "c" * 64
            return result
        self.cleanup._private.side_effect = corrupt
        with self.assertRaisesRegex(EnvironmentError, "TIRE_CLEANUP_RESULT_INVALID"):
            self.cleanup.confirm_test_cleanup(state)
        self.assertEqual("UNCERTAIN", state["backends"]["tire"]["cleanup"]["state"])
        self.assertFalse(self.backend.actions)

    def test_unknown_protocol_never_falls_back_to_foundation(self):
        state = self.product()
        state["backends"]["tire"]["privateCleanupProtocol"] = "future"
        with self.assertRaisesRegex(EnvironmentError, "PROTOCOL_UNSUPPORTED"):
            self.cleanup._tire(state, "test-uid", self.cleanup._owned(state, "tire", running=True))
        self.assertEqual([], self.calls)

    def test_unprovisioned_product_observation_uses_no_invented_uid(self):
        state = self.product(False)
        self.tire_matching = dict.fromkeys(TIRE_COUNTS, 0)
        self.cleanup._tire(state, None, self.cleanup._owned(state, "tire", running=True))
        proof = state["backends"]["tire"]["cleanup"]
        self.assertTrue(proof["wholeStoreEmpty"])
        self.assertEqual("UNPROVISIONED_STORE_OBSERVATION", proof["scope"])
        self.assertNotIn("systemUid", proof)
