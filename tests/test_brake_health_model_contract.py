# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import hashlib
import json
import unittest
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_ROOT = ROOT / "contracts" / "brake-health-model"


def load(name: str) -> dict:
    return json.loads((CONTRACT_ROOT / name).read_text(encoding="utf-8"))


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()


def round_half_up(numerator: int, denominator: int) -> int:
    return (numerator + denominator // 2) // denominator


class BrakeHealthModelContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profile = load("brake-health-model-profile.v1.json")
        cls.assessment = load("fixtures/brake-health-assessment.valid.json")
        cls.event = load("fixtures/brake-health-event.valid.json")
        cls.state = load("fixtures/brake-health-state.valid.json")
        cls.assessment_schema = load("brake-health-assessment.schema.json")
        cls.event_schema = load("brake-health-event.schema.json")
        cls.state_schema = load("brake-health-state.schema.json")

    def test_accepted_identity_and_claim_boundary(self) -> None:
        self.assertEqual("D4-016.3", self.profile["decision"])
        self.assertEqual("ACCEPTED", self.profile["lifecycleState"])
        model = self.profile["model"]
        self.assertEqual("brake-condition-demo-v1", model["id"])
        self.assertEqual("DEMO_SYNTHETIC", model["provenance"])
        self.assertFalse(model["networkInferenceAllowed"])
        self.assertFalse(model["liveTrainingAllowed"])
        self.assertFalse(model["productionDiagnosticClaimAllowed"])
        self.assertFalse(model["safetyFunctionClaimAllowed"])

    def test_exact_vdp_v2_subset_is_frozen(self) -> None:
        inputs = self.profile["input"]
        self.assertEqual(["VDP_V2", "VDP_V3"], inputs["compatibleVdpVersions"])
        self.assertEqual(12, len(inputs["paths"]))
        self.assertEqual(4, len([p for p in inputs["paths"] if p.endswith(".AngularSpeed")]))
        self.assertEqual(4, len([p for p in inputs["paths"] if p.endswith(".Speed") and ".Wheel." in p]))
        self.assertEqual(
            {
                "Vehicle.Acceleration.Lateral",
                "Vehicle.Acceleration.Vertical",
                "Vehicle.Chassis.Accelerator.PedalPosition",
            },
            set(inputs["excludedVdpV2Paths"]),
        )

    def test_golden_integer_model_result_is_exact(self) -> None:
        features = self.assessment["content"]["features"]
        weights = [30, 20, 15, 15, 20]
        values = [
            features["peakDecelerationBps"],
            features["activeDurationBps"],
            features["speedReductionBps"],
            features["meanBrakeEffortBps"],
            features["wheelDispersionBps"],
        ]
        load_bps = round_half_up(sum(w * v for w, v in zip(weights, values)), 100)
        self.assertEqual(6750, load_bps)
        increment = 4 + round_half_up(6 * load_bps, 10000)
        self.assertEqual(8, increment)
        content = self.assessment["content"]
        self.assertEqual(increment, content["wearIncrement"])
        self.assertEqual(62, content["wearIndexAfter"])
        self.assertEqual(38, content["conditionScore"])
        self.assertEqual(("MONITOR", "INSPECTION_RECOMMENDED"), (content["previousBand"], content["currentBand"]))

    def test_deterministic_ids_and_content_hashes_match(self) -> None:
        messages = self.profile["messages"]
        name = "\n".join([
            self.assessment["unitSystemUid"],
            self.assessment["sourceEventId"],
            self.assessment["modelConfigSha256"],
        ])
        expected_assessment_id = str(uuid.uuid5(uuid.UUID(messages["assessmentIdNamespaceUuid"]), name))
        self.assertEqual(expected_assessment_id, self.assessment["assessmentId"])
        event_name = "\n".join([
            self.assessment["assessmentId"],
            self.event["content"]["eventType"],
            self.event["content"]["currentBand"],
        ])
        expected_event_id = str(uuid.uuid5(uuid.UUID(messages["eventIdNamespaceUuid"]), event_name))
        self.assertEqual(expected_event_id, self.event["eventId"])
        for message in (self.assessment, self.event):
            self.assertEqual(
                hashlib.sha256(canonical(message["content"])).hexdigest(),
                message["contentSha256"],
            )
            self.assertLessEqual(len(canonical(message)), 16384)

    def test_state_is_consistent_and_bounded(self) -> None:
        content = self.assessment["content"]
        self.assertEqual(content["wearIndexAfter"], self.state["wearIndex"])
        self.assertEqual(content["conditionScore"], self.state["conditionScore"])
        self.assertEqual(content["currentBand"], self.state["conditionBand"])
        self.assertEqual(self.assessment["sourceEventId"], self.state["lastAppliedSourceEventId"])
        self.assertEqual(self.assessment["assessmentId"], self.state["lastAssessmentId"])
        self.assertEqual(64, self.profile["state"]["recentSourceEventLedgerEntries"])
        self.assertFalse(self.profile["state"]["databaseRuntimeRequired"])
        self.assertFalse(self.profile["state"]["overflowStopsLocalAssessment"])

    def test_schemas_are_closed(self) -> None:
        self.assertFalse(self.assessment_schema["additionalProperties"])
        self.assertFalse(self.assessment_schema["properties"]["content"]["additionalProperties"])
        self.assertFalse(self.event_schema["additionalProperties"])
        self.assertFalse(self.event_schema["properties"]["content"]["additionalProperties"])
        self.assertFalse(self.state_schema["additionalProperties"])


if __name__ == "__main__":
    unittest.main()
