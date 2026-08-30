# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import hashlib
import json
import unittest
import uuid
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_ROOT = ROOT / "contracts" / "brake-health-model"


def load(name: str) -> dict:
    return json.loads((CONTRACT_ROOT / name).read_text(encoding="utf-8"))


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()


def round_half_up(numerator: int, denominator: int) -> int:
    return (numerator + denominator // 2) // denominator


def quantize_milli(value: object) -> int:
    return int((Decimal(str(value)) * 1000).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def uuid_name(fields: list[str]) -> str:
    if any(any(forbidden in field for forbidden in ("\r", "\n", "\0")) for field in fields):
        raise ValueError("UUIDv5 field contains a forbidden byte")
    return b"\x0a".join(field.encode("utf-8") for field in fields).decode("utf-8")


class BrakeHealthModelContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profile_path = CONTRACT_ROOT / "brake-health-model-profile.v1.json"
        cls.profile = load("brake-health-model-profile.v1.json")
        cls.input_schema = load("brake-health-model-input.schema.json")
        cls.episode = load("fixtures/brake-health-model-input.valid.json")
        cls.input_quality_cases = load("fixtures/brake-health-model-input-quality-cases.v1.json")
        cls.quantization_cases = load("fixtures/brake-health-model-quantization-cases.v1.json")
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

    def test_exact_vdp_v2_subset_and_units_are_frozen(self) -> None:
        inputs = self.profile["input"]
        self.assertEqual(["VDP_V2", "VDP_V3"], inputs["compatibleVdpVersions"])
        self.assertEqual(12, len(inputs["paths"]))
        self.assertEqual(set(inputs["paths"]), set(inputs["normativeUnits"]))
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

    def test_complete_golden_episode_is_80_samples_at_10_hz(self) -> None:
        self.assertEqual("COMPLETE", self.episode["terminalState"])
        self.assertEqual(10, self.episode["retainedCadenceHz"])
        samples = self.episode["samples"]
        self.assertEqual(80, len(samples))
        self.assertEqual({"PRE": 30, "ACTIVE": 30, "POST": 20}, {
            phase: sum(sample["phase"] == phase for sample in samples)
            for phase in ("PRE", "ACTIVE", "POST")
        })
        expected_paths = set(self.profile["input"]["paths"])
        previous = None
        for index, sample in enumerate(samples):
            self.assertEqual(index, sample["sampleIndex"])
            self.assertEqual("VALID_COMPLETE_FRAME", sample["quality"])
            self.assertLessEqual(sample["maxSourceAgeMs"], 250)
            self.assertEqual(expected_paths, set(sample["signals"]))
            current = datetime.fromisoformat(sample["sourceTimestamp"].replace("Z", "+00:00"))
            if previous is not None:
                self.assertEqual(100, int((current - previous).total_seconds() * 1000))
            previous = current
        active = [sample for sample in samples if sample["phase"] == "ACTIVE"]
        first = datetime.fromisoformat(active[0]["sourceTimestamp"].replace("Z", "+00:00"))
        last = datetime.fromisoformat(active[-1]["sourceTimestamp"].replace("Z", "+00:00"))
        self.assertEqual(2900, int((last - first).total_seconds() * 1000))
        self.assertEqual(samples[0]["sourceTimestamp"], self.assessment["content"]["sourceWindowStartTimestamp"])
        self.assertEqual(samples[-1]["sourceTimestamp"], self.assessment["content"]["sourceWindowEndTimestamp"])

    def test_one_time_quantization_vectors_are_exact(self) -> None:
        quantization = self.profile["input"]["quantization"]
        self.assertTrue(quantization["normativeUnitConversionBeforeQuantization"])
        self.assertTrue(quantization["rejectNonFiniteBeforeQuantization"])
        self.assertTrue(quantization["normalizeNegativeZeroToZero"])
        self.assertEqual("AWAY_FROM_ZERO", quantization["exactHalfBehavior"])
        self.assertFalse(quantization["coreSecondQuantizationAllowed"])
        cases = self.quantization_cases["acceptedCases"]
        quantities = {case["quantity"] for case in cases if case["id"] != "negative-zero"}
        self.assertEqual(
            {"speed", "longitudinalAcceleration", "brakeEffort", "steering", "wheelLinearSpeed", "wheelAngularSpeed"},
            quantities,
        )
        for case in cases:
            with self.subTest(case=case["id"]):
                self.assertEqual(case["expected"], quantize_milli(case["sourceValue"]))
        self.assertEqual(
            {"NON_FINITE_VALUE", "OUT_OF_RANGE_VALUE"},
            {case["expectedReason"] for case in self.quantization_cases["rejectedCases"]},
        )

    def test_exact_feature_reduction_and_golden_result(self) -> None:
        active = [sample for sample in self.episode["samples"] if sample["phase"] == "ACTIVE"]
        value = lambda sample, path: quantize_milli(sample["signals"][path])
        peak = max(0, max(-value(sample, "Vehicle.Acceleration.Longitudinal") for sample in active))
        peak_bps = min(10000, round_half_up(peak * 10000, 8000))
        duration_ms = len(active) * 100
        duration_bps = min(10000, round_half_up(duration_ms * 10000, 5000))
        reduction = max(0, value(active[0], "Vehicle.Speed") - value(active[-1], "Vehicle.Speed"))
        reduction_bps = min(10000, round_half_up(reduction * 10000, 40000))
        mean_brake = round_half_up(
            sum(value(sample, "Vehicle.Chassis.Brake.PedalPosition") for sample in active),
            len(active),
        )
        brake_bps = min(10000, round_half_up(max(0, mean_brake - 50000) * 10000, 50000))
        wheel_bps = 0
        for sample in active:
            signals = sample["signals"]
            self.assertGreaterEqual(value(sample, "Vehicle.Speed"), 10000)
            self.assertLessEqual(abs(value(sample, "Vehicle.Chassis.Axle.Row1.SteeringAngle")), 5000)
            linear = [quantize_milli(v) for p, v in signals.items() if ".Wheel." in p and p.endswith(".Speed") and not p.endswith("AngularSpeed")]
            angular = [abs(quantize_milli(v)) for p, v in signals.items() if p.endswith(".AngularSpeed")]
            linear_bps = round_half_up((max(linear) - min(linear)) * 10000, max(max(linear), 5000))
            angular_bps = round_half_up((max(angular) - min(angular)) * 10000, max(max(angular), 30000))
            wheel_bps = max(wheel_bps, linear_bps, angular_bps)
        normalized_wheel_bps = min(10000, round_half_up(wheel_bps * 10000, 1500))
        normalized = [peak_bps, duration_bps, reduction_bps, brake_bps, normalized_wheel_bps]
        self.assertEqual([8000, 6000, 8000, 5000, 6000], normalized)
        weights = [30, 20, 15, 15, 20]
        load_bps = round_half_up(sum(weight * feature for weight, feature in zip(weights, normalized)), 100)
        self.assertEqual(6750, load_bps)
        increment = 4 + round_half_up(6 * load_bps, 10000)
        self.assertEqual(8, increment)
        content = self.assessment["content"]
        self.assertEqual(increment, content["wearIncrement"])
        self.assertEqual(62, content["wearIndexAfter"])
        self.assertEqual(38, content["conditionScore"])
        self.assertEqual(("MONITOR", "INSPECTION_RECOMMENDED"), (content["previousBand"], content["currentBand"]))

    def test_invalid_input_outcome_is_closed_and_non_mutating(self) -> None:
        eligibility = self.profile["eligibility"]
        expected_reasons = [
            "EPISODE_NOT_COMPLETE",
            "MISSING_REQUIRED_SIGNAL",
            "STALE_SAMPLE",
            "NON_FINITE_VALUE",
            "OUT_OF_RANGE_VALUE",
            "NON_MONOTONIC_SOURCE_TIME",
            "INSUFFICIENT_ACTIVE_SAMPLES",
            "INSUFFICIENT_QUALIFIED_WHEEL_SAMPLES",
        ]
        self.assertEqual(expected_reasons, eligibility["invalidReasonPriority"])
        self.assertEqual(expected_reasons, [case["expectedReason"] for case in self.input_quality_cases["cases"]])
        self.assertEqual("LOCAL_NON_WIRE_NON_PERSISTENT", eligibility["invalidResultTransport"])
        for key in (
            "invalidInputProducesAssessment",
            "invalidInputProducesEvent",
            "invalidInputAdvancesState",
            "invalidInputAdvancesGeneration",
            "invalidInputChangesBand",
            "invalidInputAdvancesRecentSourceEventLedger",
        ):
            self.assertFalse(eligibility[key])
        self.assertTrue(all(value is False for value in self.input_quality_cases["expectedMutation"].values()))

    def test_deterministic_ids_content_hashes_and_provenance_match(self) -> None:
        messages = self.profile["messages"]
        profile_sha = hashlib.sha256(self.profile_path.read_bytes()).hexdigest()
        self.assertEqual(profile_sha, self.assessment["modelConfigSha256"])
        self.assertEqual(profile_sha, self.event["modelConfigSha256"])
        self.assertEqual(profile_sha, self.state["modelConfigSha256"])
        self.assertEqual(self.assessment["serviceArtifactSha256"], self.assessment["modelArtifactSha256"])
        name = uuid_name([
            self.assessment["unitSystemUid"],
            self.assessment["sourceEventId"],
            self.assessment["modelConfigSha256"],
        ])
        expected_assessment_id = str(uuid.uuid5(uuid.UUID(messages["assessmentIdNamespaceUuid"]), name))
        self.assertEqual(expected_assessment_id, self.assessment["assessmentId"])
        event_name = uuid_name([
            self.assessment["assessmentId"],
            self.event["content"]["eventType"],
            self.event["content"]["currentBand"],
        ])
        expected_event_id = str(uuid.uuid5(uuid.UUID(messages["eventIdNamespaceUuid"]), event_name))
        self.assertEqual(expected_event_id, self.event["eventId"])
        for invalid in ("bad\rfield", "bad\nfield", "bad\0field"):
            with self.assertRaises(ValueError):
                uuid_name([invalid])
        for message in (self.assessment, self.event):
            self.assertEqual(hashlib.sha256(canonical(message["content"])).hexdigest(), message["contentSha256"])
            self.assertLessEqual(len(canonical(message)), 16384)
        self.assertEqual("DETERMINISTIC_IDENTIFICATION_ONLY", messages["uuidv5Purpose"])
        self.assertFalse(messages["uuidv5AuthenticationOrIntegrityClaimed"])
        self.assertFalse(messages["coreDiscoversOrHashesInstallation"])
        self.assertFalse(messages["separateRuntimeModelFileRequired"])

    def test_timestamp_relations_are_exact(self) -> None:
        timestamps = self.profile["timestamps"]
        self.assertEqual("FULL_RETAINED_PRE_ACTIVE_POST", timestamps["episodeScope"])
        self.assertEqual("ACTIVE_ONLY", timestamps["featureSampleScope"])
        self.assertEqual("QUALIFIED_NEAR_STRAIGHT_ACTIVE_ONLY", timestamps["wheelFeatureSampleScope"])
        assessed = datetime.fromisoformat(self.assessment["assessedAt"].replace("Z", "+00:00"))
        end = datetime.fromisoformat(self.assessment["content"]["sourceWindowEndTimestamp"].replace("Z", "+00:00"))
        self.assertGreaterEqual(assessed, end)
        self.assertEqual(self.assessment["content"]["sourceWindowEndTimestamp"], self.event["content"]["effectiveAt"])
        self.assertTrue(timestamps["retryAndRecoveryReuseCommittedAssessedAt"])
        self.assertFalse(timestamps["processingTransportOrBackendTimeMayBeEffectiveAt"])

    def test_state_journal_pair_overflow_and_qualification_are_frozen(self) -> None:
        content = self.assessment["content"]
        self.assertEqual(content["wearIndexAfter"], self.state["wearIndex"])
        self.assertEqual(content["conditionScore"], self.state["conditionScore"])
        self.assertEqual(content["currentBand"], self.state["conditionBand"])
        self.assertEqual(self.assessment["sourceEventId"], self.state["lastAppliedSourceEventId"])
        self.assertEqual(self.assessment["assessmentId"], self.state["lastAssessmentId"])
        state = self.profile["state"]
        self.assertEqual("ATOMIC_PAIR_OR_NEITHER", self.profile["messages"]["assessmentAndOptionalBandEventAdmission"])
        self.assertEqual("ADVANCE_STATE_AND_LEDGER_ENQUEUE_NEITHER_ATOMIC_PAIR", state["overflowAdmission"])
        self.assertFalse(state["overflowMayFabricateLaterMessageForAppliedSourceEvent"])
        self.assertFalse(state["overflowStopsLocalAssessment"])
        self.assertEqual(["JOURNAL_BEFORE", "JOURNAL_AFTER"], state["recoveryAcceptedCurrentStateMatches"])
        self.assertEqual("QUARANTINE_NOT_READY_STATE", state["otherRecoveryCombination"])
        self.assertFalse(state["silentResetAllowed"])
        qualification = self.profile["qualification"]
        self.assertFalse(self.profile["features"]["minimumQualifiedEpisodeLoadIsRuntimeEligibilityFilter"])
        self.assertEqual("CALIBRATION_FAILURE_NO_OUTPUT_MANIPULATION", qualification["belowMinimumScriptedRunResult"])
        self.assertEqual((7000, 8000, 20, 20), (
            qualification["nominalVisibleResultBudgetMs"],
            qualification["maximumVisibleResultBudgetMs"],
            qualification["requiredScriptedRuns"],
            qualification["requiredRunsWithinMaximumBudget"],
        ))
        self.assertFalse(qualification["productionLatencyKpiClaimed"])

    def test_schemas_are_closed(self) -> None:
        self.assertFalse(self.input_schema["additionalProperties"])
        self.assertFalse(self.input_schema["$defs"]["sample"]["additionalProperties"])
        self.assertFalse(self.input_schema["$defs"]["signals"]["additionalProperties"])
        self.assertFalse(self.assessment_schema["additionalProperties"])
        self.assertFalse(self.assessment_schema["properties"]["content"]["additionalProperties"])
        self.assertFalse(self.event_schema["additionalProperties"])
        self.assertFalse(self.event_schema["properties"]["content"]["additionalProperties"])
        self.assertFalse(self.state_schema["additionalProperties"])


if __name__ == "__main__":
    unittest.main()
