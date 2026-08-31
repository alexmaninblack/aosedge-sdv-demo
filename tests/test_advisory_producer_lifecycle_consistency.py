# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class AdvisoryProducerLifecycleConsistencyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = load(
            "contracts/brake-health-advisory-policy/brake-health-advisory-policy.v1.json"
        )
        cls.brake_runtime = load(
            "contracts/brake-health-runtime/brake-health-runtime-profile.v1.json"
        )
        cls.shared_evidence = load(
            "contracts/shared-evidence-correlation/shared-evidence-correlation-profile.v1.json"
        )
        cls.tire = load(
            "contracts/tire-health-model/tire-health-product-profile.v1.json"
        )

    def test_all_runtime_and_evidence_contracts_share_exact_lifecycle(self) -> None:
        expected = self.brake_runtime["stateCompatibility"]["producerLifecycle"]
        self.assertEqual(
            expected,
            self.shared_evidence["orderingAndAnomalies"]["producerLifecycle"],
        )
        self.assertEqual(expected, self.tire["advisory"]["producerLifecycle"])

    def test_lifecycle_matches_owner_approved_restart_and_replacement_rule(self) -> None:
        lifecycle = self.brake_runtime["stateCompatibility"]["producerLifecycle"]
        self.assertEqual(
            {
                "scopes": ["PROCESS", "CONTAINER", "VM"],
                "producerEpoch": "PRESERVE",
                "sequence": "CONTINUE_MONOTONIC_FROM_PERSISTED_NEXT_WITHOUT_REUSE",
            },
            lifecycle["ordinaryRestart"],
        )
        self.assertEqual(
            {"producerEpoch": "ROTATE_EXACTLY_ONCE", "sequence": "START_AT_ONE"},
            lifecycle["explicitReplacementOrNewProducerLifecycle"],
        )
        self.assertEqual({"producerState": "DESTROY"}, lifecycle["r0"])
        self.assertFalse(
            lifecycle["lateOldEpochEvidence"]["mayMutateCurrentStateOrAdvisory"]
        )

    def test_brake_policy_retains_persistent_monotonic_base_contract(self) -> None:
        persistence = self.policy["persistence"]
        self.assertTrue(persistence["producerEpochPersistent"])
        self.assertTrue(persistence["sequenceMonotonicPersistent"])
        self.assertEqual(
            "READ_STATUS_THEN_REFRESH_OR_RETRY_WITHOUT_SEQUENCE_REUSE",
            persistence["restartBehavior"],
        )


if __name__ == "__main__":
    unittest.main()
