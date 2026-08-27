# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "contracts" / "service-tenant-quota-proof" / "service-tenant-quota-proof-profile.v1.json"


class ServiceTenantQuotaContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profile = json.loads(PROFILE.read_text(encoding="utf-8"))

    def test_accepted_subdecisions_are_explicit(self) -> None:
        self.assertEqual("D4-023", self.profile["decision"])
        self.assertEqual("DESIGN_REVIEWED", self.profile["lifecycleState"])
        self.assertEqual(
            {"D4-023.1", "D4-023.2", "D4-023.3", "D4-023.4", "D4-023.5", "D4-023.6"},
            {item["id"] for item in self.profile["acceptedSubdecisions"]},
        )

    def test_authority_is_not_duplicated_by_demo_code(self) -> None:
        authority = self.profile["authority"]
        self.assertEqual("OEM_AFTER_VALIDATION_EVIDENCE", authority["approvalAuthority"])
        self.assertEqual("AOSCORE_SERVICE_MANAGER", authority["inVehicleEnforcementAuthority"])
        self.assertEqual("READ_ONLY_PRESENTATION", authority["dashboardAuthority"])
        self.assertFalse(authority["demoOrchestratorMaySetOverrideOrEnforceQuotas"])
        self.assertFalse(authority["projectResourceManagerAllowed"])

    def test_metadata_fields_are_exact_but_cpu_semantics_remain_open(self) -> None:
        metadata = self.profile["serviceMetadata"]
        self.assertEqual("configuration.quotas", metadata["path"])
        self.assertEqual(
            {"cpuLimit", "ramLimit", "storageLimit", "stateLimit", "tmpLimit", "noFileLimit", "pidsLimit"},
            set(metadata["fields"]),
        )
        self.assertFalse(metadata["cpuLimitMayBePresentedAsCpuPercentBeforeNativeMappingQualification"])
        self.assertEqual("DMIPS", metadata["cpuLimitUnit"])
        self.assertEqual("BYTES", metadata["sizeFieldNativeUnit"])
        self.assertEqual("cpuDmipsLimit", metadata["signedNativeCpuField"])
        self.assertFalse(metadata["liveOciAndCgroupMappingQualified"])

    def test_first_demo_saturates_only_tire_cpu(self) -> None:
        scope = self.profile["firstDemoScope"]
        self.assertEqual("TIRE_HEALTH_SERVICE", scope["intentionallySaturatedService"])
        self.assertEqual("CPU", scope["intentionallySaturatedResource"])
        self.assertFalse(scope["nonCpuExhaustionPresentedToAudience"])
        self.assertEqual("UNLOADED_CONTROL_TENANT", scope["brakeHealthRole"])

    def test_exact_requested_envelopes_are_distinct(self) -> None:
        envelopes = self.profile["approvedRequestedEnvelopes"]
        self.assertEqual(250, envelopes["brakeHealth"]["cpuLimit"])
        self.assertEqual(150, envelopes["tireHealth"]["cpuLimit"])
        self.assertEqual("8MiB", envelopes["brakeHealth"]["storageLimit"])
        self.assertEqual("4MiB", envelopes["tireHealth"]["storageLimit"])
        self.assertEqual("2MiB", envelopes["tireHealth"]["stateLimit"])
        self.assertFalse(envelopes["networkQuotaRequested"])
        self.assertFalse(envelopes["silentInflationAllowed"])

    def test_runtime_mapping_must_be_observed_before_enforcement_claim(self) -> None:
        mapping = self.profile["mappingAcceptance"]
        self.assertTrue(mapping["signerInputAndSignedNativeConfigMustMatch"])
        self.assertIn("CGROUP_V2_MEMORY_MAX", mapping["postDeploymentInspect"])
        self.assertIn("NODE_DMIPS_CAPACITY_USED_FOR_CPU_MAPPING", mapping["postDeploymentInspect"])
        self.assertFalse(mapping["unsupportedOrUnobservedFieldMayBePresentedAsEnforced"])
        self.assertTrue(mapping["declaredDmipsAndObservedCpuUtilizationShownSeparately"])

    def test_tire_load_control_is_fixed_bounded_and_in_instance(self) -> None:
        control = self.profile["tireCpuLoadControl"]
        self.assertEqual("START_CPU_ISOLATION_PROOF", control["dashboardControl"])
        self.assertEqual("TIRE_CPU_ISOLATION_PROOF_V1", control["fixedLoadProfileId"])
        self.assertEqual({"START_FIXED_CPU_LOAD", "STOP_FIXED_CPU_LOAD"}, set(control["commands"]))
        self.assertEqual(1, control["maximumConcurrentWorkers"])
        self.assertEqual(180, control["absoluteSafetyCeilingSeconds"])
        self.assertIn("SAME_AOS_MANAGED_CGROUP", control["workerLocation"])
        self.assertFalse(control["separateLoadServiceOrContainerAllowed"])
        self.assertFalse(control["arbitraryShellAllowed"])
        self.assertFalse(control["callerSelectedThreadsAllowed"])
        self.assertFalse(control["callerSelectedIntensityAllowed"])
        self.assertFalse(control["callerSelectedDurationAllowed"])
        self.assertFalse(control["serviceReportedStateProvesQuotaEnforcement"])
        self.assertFalse(control["offlineDashboardControlEnabled"])
        self.assertEqual("INACTIVE_NO_PERSISTENCE_NO_RESUME", control["serviceOrVmRestartState"])

    def test_cloud_facts_and_cgroup_qualification_are_distinct(self) -> None:
        evidence = self.profile["authoritativeEvidence"]
        self.assertIn("/api/v11/units/{unitId}/monitoring/", evidence["cloudReadEndpoints"])
        self.assertIn("/api/v11/units/{unitId}/monitoring/dashboard/", evidence["cloudReadEndpoints"])
        self.assertIn("/api/v11/alerts/", evidence["cloudReadEndpoints"])
        self.assertIn("CURRENT_INSTANCE_CPU_USAGE_DMIPS", evidence["requiredAudienceFacts"])
        self.assertEqual("SUPPLEMENTARY_FACT_NOT_REQUIRED_FOR_PASS", evidence["instanceQuotaAlertRole"])
        self.assertFalse(evidence["cloudApiExposesRawCgroupCapOrThrottleCounters"])
        self.assertIn("CGROUP_V2_CPU_MAX", evidence["technicalAcceptanceEvidence"])
        self.assertIn("CGROUP_V2_CPU_STAT_THROTTLE_COUNTER_DELTA", evidence["technicalAcceptanceEvidence"])
        self.assertFalse(evidence["technicalEvidenceMustBeRecollectedDuringEveryAudienceDemo"])
        self.assertFalse(evidence["serviceOrBackendLoadStateMayProveEnforcement"])
        self.assertFalse(evidence["dashboardMayConflateCloudAndQualificationEvidence"])
        self.assertEqual("UNKNOWN_BLOCK_PASS", evidence["missingStaleAmbiguousOrMismatchedEvidenceState"])
        self.assertTrue(evidence["finalPassCriteriaFrozen"])

    def test_verdict_is_sample_driven_and_baseline_bound(self) -> None:
        verdict = self.profile["verdictAndThresholds"]
        self.assertEqual("SAMPLE_DRIVEN_NOT_FIXED_DURATION", verdict["evaluationMode"])
        self.assertEqual(3, verdict["freshConsecutiveCloudSamplesPerPhase"])
        self.assertEqual(
            {"PRE_LOAD_BASELINE", "SATURATION", "POST_STOP_RECOVERY"},
            set(verdict["phases"]),
        )
        self.assertFalse(verdict["arbitraryPercentToleranceAllowed"])
        self.assertIn("NODE_DMIPS_CAPACITY", verdict["qualificationProfileBoundTo"])
        self.assertIn("THREE_FRESH_CLOUD_SAMPLES_IN_SATURATION_BAND", verdict["passRequires"])
        self.assertIn("BRAKE_READY_NO_RESTART_AND_ONE_DETERMINISTIC_EVENT_COMPLETED", verdict["passRequires"])
        self.assertIn("CGROUP_CAP_OR_DMIPS_MAPPING_MISMATCH", verdict["failConditions"])
        self.assertIn("MISSING_STALE_OR_INCOMPLETE_CLOUD_SAMPLES", verdict["inconclusiveConditions"])
        self.assertIn("SELECTED_UNIT_EXTERNALLY_OFFLINE", verdict["notReadyConditions"])
        self.assertFalse(verdict["instanceQuotaAlertAffectsVerdictByItself"])
        self.assertFalse(verdict["quantitativeLatencyKpiIntroduced"])

    def test_qualification_separates_characterization_from_acceptance(self) -> None:
        plan = self.profile["qualificationPlan"]
        self.assertEqual(3, plan["validationUnitCharacterizationCycles"])
        self.assertTrue(plan["freezeQualificationProfileAfterCharacterization"])
        self.assertFalse(plan["profileMayBeAdjustedDuringIndependentQualification"])
        self.assertEqual(2, plan["independentValidationUnitQualificationCycles"])
        self.assertEqual(2, plan["requiredIndependentValidationPasses"])
        self.assertFalse(plan["inconclusiveCountsAsPass"])
        self.assertTrue(plan["failBlocksQualification"])
        self.assertEqual(1, plan["productionUnitRehearsalCycles"])
        self.assertEqual(1, plan["requiredProductionUnitPasses"])
        self.assertEqual(1, plan["retainedDossierCount"])
        self.assertFalse(plan["ordinaryDemoRunHistoryRetained"])
        self.assertIn("VM_RESTART", plan["validationUnitLiveFaultCases"])
        self.assertIn("AOSCORE_RELEASE_CHANGE", plan["requalificationTriggers"])
        self.assertFalse(plan["freshProvisioningIdentityAloneInvalidatesTechnicalProfile"])
        self.assertTrue(plan["implementationAndLiveEvidenceStillRequired"])
        self.assertFalse(plan["acceptanceAuthorizesBuildLoadDeploymentCloudOrVmMutation"])


if __name__ == "__main__":
    unittest.main()
