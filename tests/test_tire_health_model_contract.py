# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import hashlib
import json
import unittest
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_ROOT = ROOT / "contracts" / "tire-health-model"


def load(name: str) -> dict:
    return json.loads((CONTRACT_ROOT / name).read_text(encoding="utf-8"))


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()


def round_half_up(numerator: int, denominator: int) -> int:
    return (numerator + denominator // 2) // denominator


class TireHealthModelContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profile = load("tire-health-product-profile.v1.json")
        cls.assessment = load("fixtures/tire-health-assessment.valid.json")
        cls.event = load("fixtures/tire-health-event.valid.json")
        cls.state = load("fixtures/tire-health-state.valid.json")
        cls.assessment_schema = load("tire-health-assessment.schema.json")
        cls.event_schema = load("tire-health-event.schema.json")
        cls.state_schema = load("tire-health-state.schema.json")

    def test_review_candidate_and_claim_boundary(self) -> None:
        self.assertEqual("D4-018", self.profile["decision"])
        self.assertEqual("ACCEPTED", self.profile["lifecycleState"])
        product = self.profile["product"]
        self.assertFalse(product["hiddenSimulatorTruthAllowed"])
        self.assertFalse(product["exactTreadDepthClaimAllowed"])
        self.assertFalse(product["productionDiagnosticClaimAllowed"])
        self.assertFalse(product["safetyFunctionClaimAllowed"])

    def test_exact_vdp_v3_subset_and_oracle_exclusion(self) -> None:
        inputs = self.profile["input"]
        self.assertEqual("VDP_V3", inputs["requiredVdpVersion"])
        self.assertEqual("PROCESS_HEALTHY_FUNCTIONALLY_NOT_READY", inputs["incompatibleVdpBehavior"])
        self.assertEqual("INCOMPATIBLE_VDP", inputs["incompatibleVdpReason"])
        self.assertFalse(inputs["conditionResultAllowedWhenIncompatible"])
        self.assertFalse(inputs["advisoryAllowedWhenIncompatible"])
        self.assertTrue(inputs["automaticReevaluationWhenCompatibleVdpAppears"])
        self.assertFalse(inputs["cloudAdmissionDependencyClaimed"])
        self.assertEqual(15, len(inputs["paths"]))
        self.assertEqual(4, len([p for p in inputs["paths"] if p.endswith(".LongitudinalSlip")]))
        self.assertEqual(4, len([p for p in inputs["paths"] if p.endswith(".LateralSlipAngle")]))
        self.assertIn("frictionForceMultiplier", inputs["forbiddenQualificationInputs"])

    def test_episode_is_bounded_per_maneuver_not_per_demo_run(self) -> None:
        episode = self.profile["episode"]
        self.assertEqual("VEHICLE_SIGNAL_SOURCE_TIMESTAMPS", episode["timeBase"])
        self.assertFalse(episode["controlModeIsModelInput"])
        self.assertTrue(episode["multipleEpisodesPerDemoRunAllowed"])
        self.assertTrue(episode["onlyOneEpisodeActiveAtATime"])
        self.assertEqual("SUPPRESS_UNTIL_CLEAR_CONDITION", episode["maximumDurationRetriggerBehavior"])
        self.assertEqual("CURRENT_UNINTERRUPTED_MANEUVER_ONLY", episode["suppressionScope"])
        self.assertTrue(episode["newManeuverAfterClearMayStartNewEpisode"])
        self.assertEqual(20, episode["minimumValidActiveSamples"])
        self.assertEqual(["COMPLETE", "TRUNCATED_MAX_DURATION"], episode["eligibleTerminalStates"])

    def test_golden_integer_estimator_result(self) -> None:
        clamp = self.profile["estimator"]["normalizedFeatureClampBps"]
        self.assertEqual({"minimum": 0, "maximum": 10000}, clamp)
        self.assertTrue(self.profile["estimator"]["clampAppliedBeforeWeighting"])
        features = self.assessment["content"]["features"]
        values = [features["longitudinalSlipBps"], features["lateralSlipBps"], features["wheelDispersionBps"], features["slipPersistenceBps"]]
        weights = [30, 30, 20, 20]
        load_bps = round_half_up(sum(weight * value for weight, value in zip(weights, values)), 100)
        self.assertEqual(6600, load_bps)
        self.assertEqual(34, 100 - round_half_up(load_bps, 100))
        self.assertEqual("REPLACEMENT_RECOMMENDED", self.assessment["content"]["currentBand"])

    def test_deterministic_ids_and_hashes(self) -> None:
        messages = self.profile["messages"]
        assessment_name = "\n".join([self.assessment["unitSystemUid"], self.assessment["sourceExerciseId"], self.assessment["modelConfigSha256"]])
        expected_assessment = str(uuid.uuid5(uuid.UUID(messages["assessmentIdNamespaceUuid"]), assessment_name))
        self.assertEqual(expected_assessment, self.assessment["assessmentId"])
        event_name = "\n".join([self.assessment["assessmentId"], self.event["content"]["eventType"], self.event["content"]["currentBand"]])
        expected_event = str(uuid.uuid5(uuid.UUID(messages["eventIdNamespaceUuid"]), event_name))
        self.assertEqual(expected_event, self.event["eventId"])
        for message in (self.assessment, self.event):
            self.assertEqual(hashlib.sha256(canonical(message["content"])).hexdigest(), message["contentSha256"])

    def test_hysteresis_and_state_are_idempotent(self) -> None:
        estimator = self.profile["estimator"]
        self.assertEqual(1, estimator["worseningEpisodesRequired"])
        self.assertEqual(3, estimator["improvingEpisodesRequired"])
        self.assertTrue(estimator["improvingEpisodesMustBeConsecutiveAndSameCandidateBand"])
        self.assertTrue(estimator["differentBetterCandidateResetsImprovementCount"])
        self.assertTrue(estimator["worseningAppliesImmediatelyAndClearsImprovementCandidate"])
        self.assertFalse(estimator["invalidInputAdvancesState"])
        self.assertFalse(estimator["invalidInputResetsImprovementCount"])
        messages = self.profile["messages"]
        self.assertTrue(messages["localAssessmentComputedForEveryEligibleEpisode"])
        self.assertEqual(30, messages["assessmentMinimumIntervalSeconds"])
        self.assertTrue(messages["bandChangeMayEmitImmediately"])
        self.assertTrue(self.profile["state"]["oneSourceExerciseAdvancesStateAtMostOnce"])

    def test_calibration_and_qualification_precede_the_demo(self) -> None:
        qualification = self.profile["qualification"]
        self.assertEqual("BEFORE_PRODUCTION", qualification["executionPhase"])
        self.assertEqual(5, qualification["calibrationRunsPerProfile"])
        self.assertTrue(qualification["configurationFrozenAndDigestPinnedBeforeQualification"])
        self.assertEqual(10, qualification["independentQualificationRunsPerProfile"])
        self.assertEqual(10, qualification["requiredSuccessesPerProfile"])
        self.assertTrue(qualification["freshModelStatePerClassificationRun"])
        self.assertTrue(qualification["persistenceAndHysteresisQualifiedSeparately"])
        self.assertFalse(qualification["qualificationRunsExecutedDuringPresentedDemo"])
        self.assertTrue(qualification["qualificationReportRequiredForArtifactAcceptance"])
        self.assertFalse(qualification["profileAndFrictionValuesVisibleToService"])

    def test_persistence_advisory_and_resource_isolation(self) -> None:
        self.assertEqual(self.assessment["assessmentId"], self.state["lastAssessmentId"])
        state = self.profile["state"]
        self.assertEqual(256, state["maximumUnacknowledgedMessages"])
        self.assertFalse(state["outboxContainsRawTelemetry"])
        self.assertEqual("PRESERVE_EXISTING_REJECT_NEW_CLOUD_MESSAGE", state["overflowAdmission"])
        self.assertFalse(state["overflowStopsLocalAssessmentOrAdvisory"])
        self.assertTrue(state["ordinaryServiceRestartPreservesState"])
        self.assertTrue(state["ordinaryVmRestartPreservesState"])
        self.assertEqual("QUARANTINE_NO_SILENT_RESET", state["unknownStateBehavior"])
        runtime = self.profile["runtime"]
        self.assertEqual(150, runtime["requestedQuota"]["cpuLimit"])
        self.assertEqual("DMIPS", runtime["requestedQuota"]["cpuLimitUnit"])
        self.assertEqual("4MiB", runtime["requestedQuota"]["storageLimit"])
        self.assertEqual("AOSCORE", runtime["quotaAuthority"])
        self.assertFalse(runtime["serviceResourceManagerImplemented"])
        self.assertEqual("DEGRADED_LOCAL_FUNCTION_CONTINUES", runtime["externalConnectivityLossState"])
        self.assertEqual("CPU_ONLY_INSIDE_TIRE_SERVICE", runtime["firstDemoIntentionalLoad"])
        self.assertEqual("AOSCORE_THROTTLING_NO_STOP_RESTART_OR_REDEPLOY", runtime["cpuQuotaBehavior"])
        self.assertTrue(runtime["brakeHealthIsHealthyControlTenant"])
        self.assertTrue(runtime["sameTireInstanceRecoversAfterLoadStops"])
        self.assertFalse(runtime["commonBehaviorClaimedForOtherQuotaExhaustion"])
        control = runtime["qualificationCpuLoadControl"]
        self.assertEqual("TIRE_CPU_ISOLATION_PROOF_V1", control["profileId"])
        self.assertEqual(1, control["maximumConcurrentWorkers"])
        self.assertEqual(180, control["absoluteSafetyCeilingSeconds"])
        self.assertFalse(control["callerSelectedParametersAllowed"])
        self.assertFalse(control["serviceStatusIsEnforcementEvidence"])
        advisory = self.profile["advisory"]
        self.assertFalse(advisory["vehicleMotionAuthorityAllowed"])
        self.assertTrue(advisory["clearOnlyAfterAcceptedImprovementHysteresis"])
        self.assertEqual("REESTABLISH_LEASE_USING_LAST_ACCEPTED_ASSESSMENT", advisory["restartWithPersistedNonGoodBand"])
        self.assertFalse(advisory["stopOrCrashCreatesClear"])
        self.assertTrue(advisory["ambiguousWriteRetriesIdenticalRequest"])
        self.assertTrue(advisory["refreshUsesNewSequenceAndRequestId"])
        self.assertEqual(["requestId", "producerEpoch", "sequence"], advisory["requiredStatusCorrelation"])
        self.assertFalse(advisory["externalConnectivityRequired"])
        self.assertEqual("ENGINEERING_TELEMATICS_DASHBOARD_ONLY", advisory["presentedIndicationSurface"])
        self.assertFalse(advisory["driverClusterImplemented"])
        lifecycle = advisory["producerLifecycle"]
        self.assertEqual(["PROCESS", "CONTAINER", "VM"], lifecycle["ordinaryRestart"]["scopes"])
        self.assertEqual("PRESERVE", lifecycle["ordinaryRestart"]["producerEpoch"])
        self.assertEqual(
            "START_AT_ONE",
            lifecycle["explicitReplacementOrNewProducerLifecycle"]["sequence"],
        )
        self.assertEqual("DESTROY", lifecycle["r0"]["producerState"])
        self.assertFalse(lifecycle["lateOldEpochEvidence"]["mayMutateCurrentStateOrAdvisory"])

    def test_logs_and_faults_are_bounded_and_isolated(self) -> None:
        runtime = self.profile["runtime"]
        self.assertEqual(2048, runtime["maximumLogBytes"])
        self.assertEqual(60, runtime["maximumLogRecordsPerMinute"])
        self.assertTrue(runtime["repeatedLogEventsAggregatedWithCount"])
        self.assertFalse(runtime["perSampleLoggingAllowed"])
        self.assertFalse(runtime["perMessageSuccessLoggingAllowed"])
        self.assertEqual("AOSCORE_AND_AOSCLOUD_D4_014", runtime["nativeLogDeliveryAuthority"])
        self.assertFalse(runtime["separateServiceLogArchiveImplemented"])
        self.assertFalse(runtime["quantitativeLatencyBenchmarkClaimed"])
        isolation = self.profile["faultIsolation"]
        self.assertFalse(isolation["tireServiceCrashStopsPeerOrPlatform"])
        self.assertFalse(isolation["cpuThrottleDegradesBrakeHealth"])
        self.assertFalse(isolation["backendFailureStopsLocalEstimatorOrAdvisory"])
        self.assertFalse(isolation["outboxOverflowStopsLocalEstimatorOrAdvisory"])
        self.assertFalse(isolation["invalidInputMutatesAcceptedState"])

    def test_schemas_are_closed(self) -> None:
        self.assertFalse(self.assessment_schema["additionalProperties"])
        self.assertFalse(self.assessment_schema["properties"]["content"]["additionalProperties"])
        self.assertFalse(self.event_schema["additionalProperties"])
        self.assertFalse(self.state_schema["additionalProperties"])


if __name__ == "__main__":
    unittest.main()
