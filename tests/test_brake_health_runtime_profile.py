# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "contracts" / "brake-health-runtime" / "brake-health-runtime-profile.v1.json"
SCAFFOLD = ROOT.parent / "brake-health-service" / "packaging" / "aos" / "config.yaml"


class BrakeHealthRuntimeProfileTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profile = json.loads(PROFILE.read_text())

    def test_version_capabilities_are_explicit(self) -> None:
        self.assertEqual("ACCEPTED", self.profile["lifecycleState"])
        versions = self.profile["versions"]
        self.assertEqual({"1.0.0", "2.0.0", "3.0.0"}, set(versions))
        self.assertFalse(versions["1.0.0"]["modelRequired"])
        self.assertTrue(versions["2.0.0"]["modelRequired"])
        self.assertTrue(versions["3.0.0"]["advisoryRequired"])

    def test_backend_and_cloud_are_not_local_readiness_dependencies(self) -> None:
        readiness = self.profile["readiness"]
        self.assertFalse(readiness["backendConnectivityRequiredForServiceReady"])
        self.assertFalse(readiness["aosCloudConnectivityRequiredForServiceReady"])
        self.assertFalse(readiness["invalidStateMayReportReady"])
        self.assertIn("NOT_READY", readiness["analyticsStates"])
        self.assertIn("DEGRADED", readiness["advisoryStates"])
        self.assertEqual(
            {"STARTING", "OPERATIONAL", "DEGRADED", "NOT_READY"},
            set(readiness["applicationModes"]),
        )
        self.assertNotIn("INPUT_QUALITY_INSUFFICIENT", readiness["analyticsReasons"])
        self.assertIn("INPUT_QUALITY_INSUFFICIENT", readiness["episodeOutcomeReasons"])
        self.assertFalse(readiness["singleAdvisoryCommandOutcomeChangesCapabilityReadiness"])
        self.assertFalse(readiness["capabilityStateMayTriggerAosProcessRestart"])
        self.assertIn("ADVISORY_READY_AT_LEAST_ONCE", readiness["deploymentAcceptanceRules"]["3.0.0"])

    def test_requested_quotas_match_current_scaffold_and_are_not_claimed_qualified(self) -> None:
        quotas = self.profile["aosRequestedQuotas"]
        scaffold = SCAFFOLD.read_text()
        for key in ("cpuLimit", "ramLimit", "storageLimit", "stateLimit", "tmpLimit", "noFileLimit", "pidsLimit"):
            self.assertIn(f"{key}: {quotas[key]}", scaffold)
        self.assertEqual("AOSCORE", quotas["enforcementAuthority"])
        self.assertFalse(quotas["qualified"])

    def test_internal_storage_bounds_fit_declared_storage(self) -> None:
        bounds = self.profile["ownedBounds"]
        used = bounds["v1WindowSpoolBytes"] + bounds["v2V3OutboxBytes"] + bounds["modelStateBytes"]
        self.assertLess(used, 8 * 1024 * 1024)

    def test_state_never_silently_resets(self) -> None:
        state = self.profile["stateCompatibility"]
        self.assertFalse(state["arbitraryBackwardServiceSelectionClaimed"])
        self.assertFalse(state["silentResetAllowed"])
        self.assertIn("QUARANTINE", state["unknownSchemaBehavior"])
        self.assertEqual("REMOVE_WITH_DISPOSABLE_UNIT_OVERLAY", state["r0Behavior"])
        self.assertFalse(state["v1ToV2"]["legacySpoolMayGateV2Analytics"])
        self.assertIn("BACKGROUND", state["v1ToV2"]["legacySpoolHandling"])
        self.assertIn("D4_016_4", state["v2ToV3"]["persistedInspectionBehavior"])
        lifecycle = state["producerLifecycle"]
        self.assertEqual("PRESERVE", lifecycle["ordinaryRestart"]["producerEpoch"])
        self.assertEqual(
            "ROTATE_EXACTLY_ONCE",
            lifecycle["explicitReplacementOrNewProducerLifecycle"]["producerEpoch"],
        )
        self.assertEqual(
            "START_AT_ONE",
            lifecycle["explicitReplacementOrNewProducerLifecycle"]["sequence"],
        )
        self.assertEqual("DESTROY", lifecycle["r0"]["producerState"])
        self.assertFalse(lifecycle["lateOldEpochEvidence"]["mayMutateCurrentStateOrAdvisory"])

    def test_logging_is_allowlisted_redacted_and_native(self) -> None:
        logging = self.profile["nativeLogging"]
        self.assertEqual("STDOUT_STDERR_TO_AOSCORE_NATIVE_LOG_COLLECTION", logging["transport"])
        self.assertFalse(logging["independentLogArchiveAllowed"])
        self.assertFalse(logging["perChunkSuccessLogAllowed"])
        self.assertIn("jwt", logging["forbiddenFields"])
        self.assertIn("rawTelemetrySample", logging["forbiddenFields"])
        self.assertIn("ASSESSMENT_SKIPPED_INPUT_QUALITY", logging["eventTypes"])
        self.assertFalse(logging["serviceMayClaimCpuOrRamQuotaExceeded"])
        self.assertEqual("AOSCORE_NATIVE_RESOURCE_EVIDENCE", logging["resourceQuotaEvidenceAuthority"])

    def test_failure_isolation_has_no_service_resource_manager(self) -> None:
        isolation = self.profile["failureIsolation"]
        self.assertFalse(isolation["serviceProvidesResourceManager"])
        self.assertTrue(isolation["cpuQuotaEnforcementThrottlesAtLimit"])
        self.assertFalse(isolation["cpuQuotaEnforcementMayStopOrRestartThisService"])
        self.assertFalse(isolation["cpuQuotaEnforcementMayStopOrDegradePeerService"])
        self.assertFalse(isolation["nonCpuQuotaOverrunBehaviorClaimed"])
        self.assertTrue(isolation["restartMustRecoverOrExplicitlyQuarantinePersistentState"])

        qualification = self.profile["quotaQualification"]
        self.assertEqual("TIRE_HEALTH_SERVICE", qualification["intentionalSaturationTarget"])
        self.assertEqual("HEALTHY_CONTROL_TENANT", qualification["brakeHealthRole"])
        self.assertEqual("CPU", qualification["intentionalResource"])
        self.assertFalse(qualification["nonCpuOverrunDemonstratedInFirstDemo"])


if __name__ == "__main__":
    unittest.main()
