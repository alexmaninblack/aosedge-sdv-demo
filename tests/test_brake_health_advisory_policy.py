# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import json
import unittest
import uuid
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_ROOT = ROOT / "contracts" / "brake-health-advisory-policy"


class BrakeHealthAdvisoryPolicyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = json.loads((CONTRACT_ROOT / "brake-health-advisory-policy.v1.json").read_text())
        cls.request = json.loads((CONTRACT_ROOT / "fixtures" / "brake-advisory-set.valid.json").read_text())
        cls.qm = json.loads((ROOT / "contracts" / "qm-advisory-profile" / "qm-advisory-profile.v1.json").read_text())

    def test_accepted_policy_reuses_exact_brake_endpoint(self) -> None:
        self.assertEqual("ACCEPTED", self.policy["lifecycleState"])
        brake = next(e for e in self.qm["endpoints"] if e["id"] == "BRAKE_HEALTH_ADVISORY")
        self.assertEqual(brake["requestPath"], self.policy["request"]["path"])
        self.assertEqual(brake["statusPath"], self.policy["status"]["path"])
        self.assertEqual(brake["recommendations"][0], self.policy["request"]["recommendation"])

    def test_request_is_deterministically_bound_to_assessment(self) -> None:
        fields = [
            self.request["producerEpoch"],
            str(self.request["sequence"]),
            self.request["operation"],
            self.request["decisionId"],
        ]
        expected = uuid.uuid5(uuid.UUID(self.policy["request"]["requestIdNamespaceUuid"]), "\n".join(fields))
        self.assertEqual(str(expected), self.request["requestId"])
        self.assertEqual("3.0.0", self.request["serviceVersion"])

    def test_v3_activation_reuses_existing_inspection_assessment_once(self) -> None:
        trigger = self.policy["trigger"]
        self.assertEqual(
            {"NEW_BAND_TRANSITION", "V3_ACTIVATION_WITH_PERSISTED_ACTIVE_CONDITION"},
            set(trigger["acceptedCauses"]),
        )
        activation = trigger["activationWithPersistedCondition"]
        self.assertTrue(activation["enabled"])
        self.assertEqual("INSPECTION_RECOMMENDED", activation["requiredPersistedBand"])
        self.assertEqual("LAST_ACCEPTED_ASSESSMENT_ID", activation["decisionIdSource"])
        self.assertTrue(activation["requiresNoRecordedAdvisoryForDecisionId"])
        self.assertFalse(activation["createsSyntheticAssessmentOrBandChangeEvent"])
        self.assertTrue(activation["persistsDecisionToRequestBindingBeforeWrite"])

    def test_lease_and_refresh_are_within_qm_bounds(self) -> None:
        issued = datetime.fromisoformat(self.request["issuedAt"].replace("Z", "+00:00"))
        expires = datetime.fromisoformat(self.request["expiresAt"].replace("Z", "+00:00"))
        self.assertEqual(30000, int((expires - issued).total_seconds() * 1000))
        self.assertEqual(30000, self.policy["request"]["leaseMs"])
        self.assertEqual(20000, self.policy["request"]["refreshIntervalMs"])
        self.assertGreaterEqual(self.policy["request"]["refreshIntervalMs"], self.qm["temporalPolicy"]["minRefreshIntervalMs"])

    def test_gateway_status_is_final_and_external_cloud_is_not_required(self) -> None:
        self.assertTrue(self.policy["status"]["serviceSubscribesReadOnly"])
        self.assertFalse(self.policy["status"]["kuksaWriteMeansApplied"])
        self.assertFalse(self.policy["status"]["vissSetMeansApplied"])
        self.assertTrue(self.policy["authority"]["gatewayFinalAuthority"])
        self.assertFalse(self.policy["authority"]["externalConnectivityRequired"])

    def test_current_model_does_not_invent_clear_or_fallback(self) -> None:
        self.assertFalse(self.policy["clear"]["currentMonotonicModelProducesClear"])
        self.assertTrue(self.policy["clear"]["noRefreshUsesGatewayExpiry"])
        self.assertFalse(self.policy["authority"]["alternateTargetAllowed"])
        self.assertFalse(self.policy["authority"]["arbitraryTextAllowed"])
        self.assertFalse(self.policy["authority"]["vehicleMotionAllowed"])

    def test_persistence_requires_epoch_and_sequence_reuse_protection(self) -> None:
        persistence = self.policy["persistence"]
        self.assertTrue(persistence["producerEpochPersistent"])
        self.assertTrue(persistence["sequenceMonotonicPersistent"])
        self.assertEqual(
            "READ_STATUS_THEN_REFRESH_OR_RETRY_WITHOUT_SEQUENCE_REUSE",
            persistence["restartBehavior"],
        )


if __name__ == "__main__":
    unittest.main()
