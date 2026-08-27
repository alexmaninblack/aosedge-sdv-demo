# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "contracts" / "shared-evidence-correlation" / "shared-evidence-correlation-profile.v1.json"
SCHEMA = ROOT / "contracts" / "shared-evidence-correlation" / "structured-evidence-record.schema.json"


class SharedEvidenceCorrelationContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profile = json.loads(PROFILE.read_text(encoding="utf-8"))
        cls.schema = json.loads(SCHEMA.read_text(encoding="utf-8"))

    def test_all_subdecisions_are_accepted(self) -> None:
        self.assertEqual("D4-024", self.profile["decision"])
        self.assertEqual("DESIGN_REVIEWED", self.profile["lifecycleState"])
        self.assertEqual(
            ["D4-024.1", "D4-024.2", "D4-024.3", "D4-024.4", "D4-024.5"],
            [item["id"] for item in self.profile["acceptedSubdecisions"]],
        )
        self.assertEqual([], self.profile["pendingSubdecisions"])

    def test_no_global_or_historical_run_identity_is_added(self) -> None:
        context = self.profile["canonicalCorrelationContext"]
        self.assertFalse(context["audienceVisibleGlobalDemoRunIdIntroduced"])
        self.assertFalse(context["historicalDemoRunDatabaseAllowed"])
        self.assertFalse(context["localRunCorrelationSentToFunctionBackends"])

    def test_operational_and_function_scopes_remain_separate(self) -> None:
        context = self.profile["canonicalCorrelationContext"]
        self.assertIn("AOSCLOUD_UNIT_UUID", context["postProvisioningOperationalCorrelation"])
        self.assertIn("MAIN_NODE_UUID", context["postProvisioningOperationalCorrelation"])
        self.assertIn("unitSystemUid", context["functionMessageCorrelation"])
        self.assertNotIn("AOSCLOUD_UNIT_UUID", context["functionMessageCorrelation"])
        self.assertFalse(context["cloudUnitAndNodeUuidsSentToFunctionBackends"])
        self.assertEqual("CURRENT_AOSCLOUD_STATE_JOINED_BY_SYSTEM_UID", context["functionToCloudMappingAuthority"])

    def test_collision_and_failure_rules_are_explicit(self) -> None:
        context = self.profile["canonicalCorrelationContext"]
        self.assertEqual(
            {"FUNCTION_TEAM", "UNIT_SYSTEM_UID", "MESSAGE_TYPE", "DOMAIN_IDENTIFIER"},
            set(context["collisionNamespace"]),
        )
        self.assertEqual("CAMEL_CASE", context["jsonWireNaming"])
        self.assertIn("JWT", context["forbiddenCorrelationContent"])
        self.assertEqual(
            "UNKNOWN_OR_BLOCKED_NEVER_SUCCESS",
            context["missingStaleConflictingOrCrossRunBinding"],
        )

    def test_chronology_has_separate_authorities_and_no_latency_claim(self) -> None:
        chronology = self.profile["chronology"]
        roles = chronology["timestampRoles"]
        self.assertEqual("GATEWAY_SOURCE_CAPTURE", roles["sourceEventTime"]["authority"])
        self.assertEqual("FUNCTION_SERVICE_INSTANCE", roles["localDecisionAt"]["authority"])
        self.assertEqual("VEHICLE_GATEWAY", roles["gatewayObservedAt"]["authority"])
        self.assertTrue(roles["backendReceivedAt"]["duplicateReusesOriginalValue"])
        self.assertFalse(roles["synchronizationCompletedAt"]["reconnectTimeAloneIsSufficient"])
        self.assertFalse(chronology["crossClockWallTimeComparisonProvesCausality"])
        self.assertFalse(chronology["latencyKpiCalculated"])

    def test_claim_boundary_is_demo_only(self) -> None:
        boundary = self.profile["chronology"]["claimBoundary"]
        self.assertIn("DEMO_CAUSAL_LINKAGE", boundary["proves"])
        self.assertIn("PRODUCTION_CLOCK_SYNCHRONIZATION", boundary["doesNotProve"])
        self.assertIn("WORST_CASE_OR_END_TO_END_LATENCY", boundary["doesNotProve"])
        self.assertIn("AUTOMOTIVE_SAFETY_SUITABILITY", boundary["doesNotProve"])

    def test_structured_evidence_is_sanitized_projection_not_archive(self) -> None:
        evidence = self.profile["structuredEvidence"]
        self.assertFalse(evidence["isSystemOfRecord"])
        self.assertFalse(evidence["isAosCloudLogReplacement"])
        self.assertFalse(evidence["createsHistoricalEvidenceArchive"])
        self.assertTrue(evidence["redactionBeforeBrowserUiState"])
        self.assertTrue(evidence["exactBindingCheckedBeforeFingerprintProjection"])
        self.assertFalse(evidence["fullCloudUnitOrNodeIdInAudienceRecord"])
        self.assertFalse(evidence["freeFormLogMessageIsEvidence"])
        self.assertFalse(evidence["unknownFieldsAutomaticallyDisplayed"])
        self.assertIn("JWT", evidence["forbiddenBeforeProjection"])
        self.assertFalse(evidence["silentOmissionAllowed"])

    def test_structured_evidence_schema_is_closed(self) -> None:
        self.assertEqual("https://json-schema.org/draft/2020-12/schema", self.schema["$schema"])
        self.assertEqual("object", self.schema["type"])
        self.assertFalse(self.schema["additionalProperties"])
        self.assertFalse(self.schema["properties"]["correlation"]["additionalProperties"])
        self.assertFalse(self.schema["properties"]["details"]["additionalProperties"])

    def test_duplicates_and_conflicts_are_distinct(self) -> None:
        ordering = self.profile["orderingAndAnomalies"]
        self.assertEqual("REUSE_ORIGINAL_RECEIPT_AND_RESULT", ordering["idempotentDuplicate"]["result"])
        self.assertFalse(ordering["idempotentDuplicate"]["createsDashboardRowOrSecondAction"])
        self.assertEqual("REJECT_IDEMPOTENCY_CONFLICT", ordering["idempotencyConflict"]["result"])
        self.assertFalse(ordering["idempotencyConflict"]["mayReplaceAcceptedRecord"])

    def test_epoch_sequence_and_reconnect_protect_current_state(self) -> None:
        ordering = self.profile["orderingAndAnomalies"]
        self.assertEqual(["PRODUCER_EPOCH", "SEQUENCE"], ordering["stateChangingOrder"])
        self.assertFalse(ordering["backendReceiptTimeDeterminesStateOrder"])
        self.assertTrue(ordering["serviceRestart"]["createsNewProducerEpoch"])
        self.assertFalse(ordering["serviceRestart"]["oldEpochLateEvidenceMayMutateCurrentStateOrAdvisory"])
        self.assertTrue(ordering["reconnectRetry"]["onlyUnacknowledgedMessages"])
        self.assertTrue(ordering["reconnectRetry"]["synchronizationRequiresAllSequencesThroughDeclaredWatermarkAcknowledged"])

    def test_clock_difference_cannot_reorder_causality(self) -> None:
        ordering = self.profile["orderingAndAnomalies"]
        self.assertEqual("REJECT_SCHEMA", ordering["timestampHandling"]["invalidRfc3339Utc"])
        self.assertFalse(ordering["timestampHandling"]["crossClockDifferenceMayChangeCausalOrder"])
        self.assertTrue(ordering["dashboard"]["ignoredDuplicateCountVisible"])
        self.assertTrue(ordering["claimBoundaryRemainsDemoOnly"])

    def test_qualification_is_bounded_and_has_no_separate_archive(self) -> None:
        plan = self.profile["qualificationPlan"]
        self.assertTrue(plan["clockAnomaliesUseFixturesWithoutChangingMacOrVmClock"])
        self.assertIn("LOCAL_DECISION_WHILE_OFFLINE", plan["validationUnitIntegration"])
        self.assertEqual(2, len(plan["productionUnitRehearsals"]))
        self.assertTrue(plan["productionUsesSameReviewedContractsAndPreparedArtifactsAsValidation"])
        self.assertIn("NO_FORBIDDEN_DATA_IN_BROWSER_STATE", plan["passRequires"])
        self.assertEqual("D4_025_DEMO_BASELINE_QUALIFICATION_DOSSIER", plan["evidenceDestination"])
        self.assertFalse(plan["separateD4024HistoricalArchiveCreated"])
        self.assertTrue(plan["implementationAndLiveQualificationRemainOpen"])
        self.assertFalse(plan["designReviewAuthorizesImplementationPublicationCloudOrVmMutation"])


if __name__ == "__main__":
    unittest.main()
