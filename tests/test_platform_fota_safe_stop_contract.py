# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "contracts" / "platform-fota-safe-stop" / "platform-fota-safe-stop-profile.v1.json"


class PlatformFotaSafeStopContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profile = json.loads(PROFILE.read_text(encoding="utf-8"))

    def test_authority_is_runtime_owned_and_not_cloud_or_ui_owned(self) -> None:
        self.assertEqual("1.1.1", self.profile["contractVersion"])
        authority = self.profile["authority"]
        self.assertEqual("VEHICLE_GATEWAY", authority["physicalStateSource"])
        self.assertEqual("FACTORY_INSTALLED_OEM_COMPONENT_RUNTIME", authority["applicationEnforcement"])
        self.assertIn("AOSCLOUD_MOTION_INFERENCE", authority["forbiddenSources"])
        self.assertIn("DEMO_UI_DECISION", authority["forbiddenSources"])
        self.assertIn("VDP_BEING_UPDATED", authority["forbiddenSources"])
        self.assertIn("KUKSA", authority["forbiddenSources"])

    def test_safe_stop_requires_mode_transition_and_factual_evidence(self) -> None:
        evidence = self.profile["evidence"]
        self.assertEqual("PLATFORM_UPDATE_RUNTIME", evidence["runtimeReadRole"])
        self.assertTrue(evidence["purposeBoundCredentialRequired"])
        self.assertTrue(evidence["distinctMonotonicFrameRequired"])
        self.assertTrue(evidence["sourceTimestampRequired"])
        self.assertTrue(evidence["sourceFreshnessCheckedAtAcquisition"])
        self.assertIn("Vehicle.CarlaSimulation.FrameId", evidence["requiredPaths"])
        policy = self.profile["policy"]
        self.assertEqual("SAFE_STOP", policy["activeMode"])
        self.assertEqual("STABLE", policy["transitionState"])
        self.assertEqual(0.3, policy["maximumSpeedKmh"])
        self.assertEqual(12, policy["consecutiveSamples"])
        self.assertEqual(250, policy["maximumSampleAgeMs"])
        self.assertEqual("AT_EACH_SAMPLE_ACQUISITION", policy["maximumSampleAgeScope"])
        self.assertEqual(250, policy["latestSampleMaximumAgeMsAtGate"])
        self.assertEqual("STABILITY_ONLY_NOT_CURRENT_STATE", policy["historyMeaning"])
        self.assertEqual("LATEST_COMPLETE_FRESH_SAMPLE", policy["destructiveGateRevalidation"])
        self.assertGreater(
            (policy["consecutiveSamples"] - 1) * policy["expectedSamplePeriodMs"],
            policy["maximumSampleAgeMs"],
        )
        self.assertEqual("NOT_SAFE", policy["stoppedInAnotherMode"])
        self.assertFalse(policy["resetInProgressAllowed"])
        self.assertFalse(policy["resetDiscontinuityAllowed"])

    def test_gate_covers_stop_and_start_without_unbounded_wait(self) -> None:
        gate = self.profile["gate"]
        self.assertTrue(gate["replacementStopInstanceBeforeDestructiveStop"])
        self.assertTrue(gate["removalStopInstanceBeforeDestructiveStop"])
        self.assertTrue(gate["firstInstallStartInstanceBeforeActivation"])
        self.assertTrue(gate["replacementStartInstanceRevalidationBeforeActivation"])
        self.assertTrue(gate["continuousValidationThroughDestructiveApply"])
        self.assertFalse(gate["unboundedWaitAllowed"])
        self.assertLess(gate["waitTimeoutSeconds"], gate["aosCoreNodeStatusTimeoutUpperBoundSeconds"])
        self.assertFalse(gate["automaticDrivingResume"])

    def test_waiting_is_durable_idempotent_and_distinguishes_install_modes(self) -> None:
        state = self.profile["runtimeState"]
        self.assertEqual("WAITING_FOR_SAFE_STOP", state["durablePhase"])
        self.assertEqual("ACTIVATING", state["nativeAosStateWhileWaiting"])
        self.assertEqual("IDEMPOTENT_REATTACH", state["sameCandidateRetry"])
        self.assertEqual("REJECT", state["differentCandidateWhileActive"])
        self.assertEqual("EMPTY_SLOT_REMAINS_EMPTY", state["firstInstallBehaviorWhileWaiting"])
        self.assertEqual(
            "PREVIOUS_HEALTHY_RELEASE_REMAINS_ACTIVE",
            state["replacementBehaviorWhileWaiting"],
        )
        self.assertEqual(
            "CURRENT_HEALTHY_RELEASE_REMAINS_ACTIVE",
            state["removalBehaviorWhileWaiting"],
        )

    def test_waiting_worker_is_asynchronous_bounded_and_never_persists_samples(self) -> None:
        implementation = self.profile["runtimeImplementation"]
        self.assertEqual("VehicleStateProviderItf", implementation["vehicleStateInterface"])
        self.assertEqual(
            "VISS_3_1_MTLS_PLATFORM_UPDATE_RUNTIME_ROLE",
            implementation["transportAdapter"],
        )
        self.assertEqual("PURE_SAFE_STOP_POLICY", implementation["policyEvaluator"])
        self.assertEqual("ASYNCHRONOUS_BOUNDED_WORKER", implementation["waitingExecution"])
        self.assertFalse(implementation["runtimeMutexHeldWhileWaiting"])
        self.assertEqual(
            "DURABLE_WAIT_THEN_RETURN_ACTIVATING",
            implementation["startInstanceWaitingResult"],
        )
        self.assertTrue(implementation["singleWorker"])
        self.assertEqual("BOUNDED_CANCEL_AND_JOIN", implementation["stopCancellation"])
        self.assertEqual("TRANSACTION_METADATA_ONLY", implementation["persistedContent"])
        self.assertFalse(implementation["persistedSamplesAllowed"])

    def test_restart_and_safe_stop_loss_fail_closed(self) -> None:
        recovery = self.profile["recovery"]
        self.assertFalse(recovery["reusePersistedSafeStopEvidence"])
        self.assertTrue(recovery["freshEvidenceAfterRestartRequired"])
        self.assertEqual("EMPTY_SLOT_REMAINS_EMPTY", recovery["firstInstallRecoveryBehavior"])
        self.assertEqual(
            "RESTORE_PREVIOUS_HEALTHY_RELEASE",
            recovery["replacementRecoveryBehavior"],
        )
        self.assertEqual(
            "RESTORE_CURRENT_HEALTHY_RELEASE",
            recovery["removalRecoveryBehavior"],
        )
        self.assertEqual("RETURN_TO_WAITING", recovery["safeStopLossBeforeDestructiveApply"])
        self.assertEqual("FAIL_AND_ROLL_BACK", recovery["safeStopLossDuringDestructiveApply"])

    def test_observability_preserves_authoritative_sources(self) -> None:
        observability = self.profile["observability"]
        self.assertEqual("AOSCORE_AOSCLOUD", observability["authoritativeLifecycleState"])
        self.assertEqual("OEM_COMPONENT_RUNTIME_NATIVE_AOS_LOGS", observability["structuredReasonSource"])
        self.assertEqual("VEHICLE_GATEWAY", observability["vehicleFactSource"])
        self.assertEqual(
            "DERIVED_FROM_NATIVE_ACTIVATING_STATE_AND_FRESH_GATEWAY_NOT_SAFE_STOP",
            observability["audienceWaitingInterpretation"],
        )
        self.assertFalse(observability["interpretationIsNativeCloudState"])
        self.assertFalse(observability["uiMayEnforceOrInventState"])
        self.assertFalse(observability["credentialsOrRawSecretsInEvidence"])

    def test_qualification_covers_current_and_failure_lifecycles(self) -> None:
        qualification = self.profile["qualification"]
        self.assertEqual({"TEST", "PRODUCTION"}, set(qualification["roles"]))
        self.assertIn("FIRST_INSTALL_WHILE_MOVING_WAITS", qualification["cases"])
        self.assertIn("REPLACEMENT_WHILE_MOVING_KEEPS_OLD_RELEASE_ACTIVE", qualification["cases"])
        self.assertIn("ZERO_SPEED_OUTSIDE_SAFE_STOP_IS_REJECTED", qualification["cases"])
        self.assertIn("VM_RESTART_WHILE_WAITING_REQUIRES_FRESH_EVIDENCE", qualification["cases"])
        self.assertEqual("OPEN", qualification["implementationState"])
        self.assertEqual("OPEN", qualification["liveEvidenceState"])


if __name__ == "__main__":
    unittest.main()
