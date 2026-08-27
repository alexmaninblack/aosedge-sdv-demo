# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "contracts" / "e2e-stage-evidence" / "e2e-stage-evidence-profile.v1.json"
SCHEMA = ROOT / "contracts" / "e2e-stage-evidence" / "e2e-stage-record.schema.json"
DOSSIER_SCHEMA = ROOT / "contracts" / "e2e-stage-evidence" / "demo-baseline-qualification-dossier.schema.json"
HUMAN_REVIEW_SCHEMA = ROOT / "contracts" / "e2e-stage-evidence" / "human-presenter-review.schema.json"
QUALIFICATION_STATUS_SCHEMA = ROOT / "contracts" / "e2e-stage-evidence" / "qualification-status.schema.json"
STAGE_MAP = ROOT / "contracts" / "e2e-stage-evidence" / "e2e-stage-map.v1.json"


class E2EStageEvidenceContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profile = json.loads(PROFILE.read_text(encoding="utf-8"))
        cls.schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        cls.dossier_schema = json.loads(DOSSIER_SCHEMA.read_text(encoding="utf-8"))
        cls.human_review_schema = json.loads(HUMAN_REVIEW_SCHEMA.read_text(encoding="utf-8"))
        cls.qualification_status_schema = json.loads(QUALIFICATION_STATUS_SCHEMA.read_text(encoding="utf-8"))
        cls.stage_map = json.loads(STAGE_MAP.read_text(encoding="utf-8"))

    def test_all_subdecisions_are_accepted(self) -> None:
        self.assertEqual("D4-025", self.profile["decision"])
        self.assertEqual("DESIGN_REVIEWED", self.profile["lifecycleState"])
        self.assertEqual(
            ["D4-025.1", "D4-025.2", "D4-025.3", "D4-025.4", "D4-025.5"],
            [item["id"] for item in self.profile["acceptedSubdecisions"]],
        )
        self.assertEqual([], self.profile["pendingSubdecisions"])

    def test_stable_cases_are_composed_of_atomic_stages(self) -> None:
        hierarchy = self.profile["hierarchy"]
        self.assertFalse(hierarchy["acceptanceCasesRenumbered"])
        self.assertEqual("AT-E2E-NNN/SNN", hierarchy["atomicStageIdPattern"])
        self.assertTrue(hierarchy["complexAcceptanceCaseContainsOrderedAtomicStages"])
        self.assertTrue(hierarchy["eachAtomicStageHasExactlyOneBoundedAction"])
        self.assertTrue(hierarchy["topLevelCaseVerdictComposedFromAtomicStageVerdicts"])

    def test_external_orchestration_and_verdict_states_remain_separate(self) -> None:
        states = self.profile["stateSeparation"]
        self.assertIn("UNCERTAIN", states["orchestrationStates"])
        self.assertIn("ABORTED", states["acceptanceVerdicts"])
        self.assertFalse(states["externalStateMayBeReplacedByOrchestrationOrVerdict"])

    def test_progression_fails_closed(self) -> None:
        rules = self.profile["progressionRules"]
        self.assertFalse(rules["blockedSubmitsAction"])
        self.assertFalse(rules["timeoutOrLostResponseAssignsVerdictAutomatically"])
        self.assertFalse(rules["uncertainAllowsBlindRetry"])
        self.assertTrue(rules["reconciliationRequiresAuthoritativeReRead"])
        self.assertTrue(rules["passedRequiresAllMandatoryExitAssertions"])
        self.assertFalse(rules["topLevelCasePassesWithAnyMandatoryStageNotPassed"])

    def test_schema_is_closed_and_has_one_action_object(self) -> None:
        self.assertEqual("object", self.schema["type"])
        self.assertFalse(self.schema["additionalProperties"])
        self.assertEqual("object", self.schema["properties"]["action"]["type"])
        self.assertNotIn("actions", self.schema["properties"])
        self.assertFalse(self.schema["properties"]["action"]["additionalProperties"])

    def test_assertions_use_closed_predicates_and_evidence_references(self) -> None:
        accepted = self.profile["assertionsAndEvidence"]
        self.assertIn("SET_EQUALS", accepted["predicates"])
        self.assertIn("NO_FORBIDDEN_FIELDS", accepted["predicates"])
        assertion = self.schema["$defs"]["assertion"]
        self.assertFalse(assertion["additionalProperties"])
        self.assertEqual(set(accepted["predicates"]), set(assertion["properties"]["predicate"]["enum"]))
        self.assertIn("evidenceReferences", assertion["required"])
        self.assertFalse(self.schema["$defs"]["evidenceReference"]["additionalProperties"])

    def test_evidence_cannot_be_replaced_by_success_screenshot_or_prose(self) -> None:
        accepted = self.profile["assertionsAndEvidence"]
        self.assertTrue(accepted["mutationRereadMustOccurAfterAction"])
        self.assertFalse(accepted["successfulHttpResponseAloneIsAuthoritativeEvidence"])
        self.assertFalse(accepted["screenshotAloneIsProof"])
        self.assertFalse(accepted["operatorStatementAloneIsProof"])
        self.assertFalse(accepted["rawExternalResponseCopiedIntoStageRecord"])

    def test_gate_semantics_distinguish_mismatch_from_missing_evidence(self) -> None:
        accepted = self.profile["assertionsAndEvidence"]
        self.assertTrue(accepted["mandatoryEntryMustPassBeforeAction"])
        self.assertEqual("BLOCKED_WITH_PROVEN_MISMATCH", accepted["failedEntryState"])
        self.assertEqual("BLOCKED_WITHOUT_SYSTEM_FAILURE_CLAIM", accepted["unknownStaleOrConflictingEntryState"])
        self.assertEqual("FAILED", accepted["provenExitMismatchVerdict"])
        self.assertFalse(accepted["optionalAssertionAffectsVerdict"])
        self.assertTrue(accepted["optionalAssertionAlwaysDisplayed"])

    def test_ordinary_demo_does_not_retain_stage_history(self) -> None:
        retention = self.profile["retentionBoundary"]
        self.assertFalse(retention["ordinaryDemoRunHistoryRetained"])
        self.assertTrue(retention["stageRecordsRetainedOnlyForExplicitFormalQualificationOrAcceptanceRun"])

    def test_dossier_is_demo_baseline_acceptance_not_release_approval(self) -> None:
        dossier = self.profile["demoBaselineQualificationDossier"]
        self.assertEqual("DEMO_SOLUTION_QUALIFICATION_RUN", dossier["qualificationRunName"])
        self.assertEqual("DEMO_BASELINE_QUALIFICATION_DOSSIER", dossier["dossierName"])
        self.assertFalse(dossier["isPerArtifactReleaseApproval"])
        self.assertFalse(dossier["isCreatedForOrdinaryAudienceDemo"])
        self.assertTrue(dossier["mustBeDesignatedBeforeRunStart"])
        self.assertFalse(dossier["postHocSuccessfulRunSelectionAllowed"])

    def test_dossier_is_sanitized_sealed_and_r0_bound(self) -> None:
        dossier = self.profile["demoBaselineQualificationDossier"]
        self.assertIn("FULL_UNIT_NODE_OR_SYSTEM_UID", dossier["forbiddenContent"])
        self.assertFalse(dossier["screenshotsAreProof"])
        self.assertFalse(dossier["copiesAosCloudSystemOfRecord"])
        self.assertTrue(dossier["sealedDossierImmutable"])
        self.assertTrue(dossier["correctionCreatesNewVersionWithSupersedesDossierId"])
        self.assertTrue(dossier["passRequiresR0CleanupPass"])
        self.assertEqual("INCOMPLETE", dossier["uncertainCleanupState"])

    def test_dossier_manifest_schema_is_closed(self) -> None:
        self.assertEqual("object", self.dossier_schema["type"])
        self.assertFalse(self.dossier_schema["additionalProperties"])
        self.assertEqual("DEMO_BASELINE_QUALIFICATION", self.dossier_schema["properties"]["dossierType"]["const"])
        self.assertTrue(self.dossier_schema["properties"]["designation"]["properties"]["designatedBeforeStart"]["const"])
        self.assertIn("humanReview", self.dossier_schema["required"])
        self.assertIn("qualificationDecision", self.dossier_schema["required"])
        self.assertIn("human-review.json", self.dossier_schema["properties"]["files"]["items"]["properties"]["relativePath"]["pattern"])

    def test_stage_instance_key_is_part_of_record_and_map_identity(self) -> None:
        self.assertIn("stageInstanceKey", self.schema["required"])
        self.assertEqual(
            ["acceptanceCaseId", "stageId", "stageInstanceKey", "targetOrArtifactCorrelationSha256"],
            self.stage_map["identity"],
        )

    def test_release_template_has_seven_instances_and_ten_atomic_stages(self) -> None:
        release = self.stage_map["releaseTemplate"]
        self.assertEqual(7, len(release["instances"]))
        self.assertEqual(10, len(release["stages"]))
        self.assertEqual("PROTECTED_SIGN_AND_PUBLISH", release["stages"][1]["actionType"])
        self.assertEqual("OEM_DU_CAMPAIGN_APPROVAL", release["stages"][8]["actionType"])

    def test_all_stable_acceptance_cases_are_mapped(self) -> None:
        case_ids = {item["acceptanceCaseId"] for item in self.stage_map["acceptanceCases"]}
        self.assertEqual({f"AT-E2E-{number:03d}" for number in range(1, 12)}, case_ids)

    def test_r0_has_both_role_instances_and_journal_deleted_last(self) -> None:
        r0 = next(item for item in self.stage_map["acceptanceCases"] if item["acceptanceCaseId"] == "AT-E2E-010")
        self.assertEqual(["VALIDATION", "PRODUCTION"], r0["perRoleTemplate"]["instances"])
        self.assertEqual("DELETE_CURRENT_RUN_JOURNAL_LAST", r0["fixedStages"][-1]["actionType"])

    def test_d4026_mode_and_case_allocation_is_non_overlapping(self) -> None:
        allocation = self.profile["qualificationModesAndCaseAllocation"]
        self.assertEqual(["D4-026.1", "D4-026.2", "D4-026.3"], allocation["acceptedDecisions"])
        self.assertEqual(
            {
                "STATIC_CONFORMANCE",
                "CONTROLLED_DISPOSABLE_QUALIFICATION",
                "LIVE_BASELINE_POSITIVE",
                "AUDIENCE_PRESENTATION",
            },
            set(allocation["modes"]),
        )
        self.assertEqual(
            {"AT-E2E-009", "AT-E2E-011"},
            set(allocation["controlledDisposableQualification"]["requiredAcceptanceCases"]),
        )
        self.assertEqual(
            {f"AT-E2E-{number:03d}" for number in range(1, 9)} | {"AT-E2E-010"},
            set(allocation["liveBaselinePositive"]["requiredAcceptanceCases"]),
        )
        self.assertFalse(allocation["staticConformance"]["isIntegratedAcceptanceCaseVerdict"])
        self.assertFalse(allocation["audiencePresentation"]["createsQualificationVerdictOrDossier"])
        self.assertFalse(allocation["audiencePresentation"]["runsDestructiveOrNegativeVectors"])

    def test_repeatability_requires_machine_pass_and_human_acceptance(self) -> None:
        policy = self.profile["repeatabilityToleranceAndHumanAcceptance"]
        live = policy["liveBaselinePositive"]
        human = policy["humanPresenterAcceptance"]
        self.assertEqual(2, live["requiredConsecutiveCompleteCycles"])
        self.assertFalse(live["thirdProvisioningCycleRequired"])
        self.assertEqual("LIVE_BASELINE_POSITIVE_CYCLE_B", human["usesCycle"])
        self.assertEqual("MACHINE_PASSED_AND_HUMAN_ACCEPTED", human["qualificationFormula"])
        self.assertFalse(human["machinePassWithoutHumanAcceptanceQualifies"])
        self.assertTrue(human["humanRejectMayVetoMachinePass"])
        self.assertFalse(human["humanAcceptMayOverrideNonPassingMachineVerdict"])
        self.assertEqual("FAIL_CLOSED_NOT_QUALIFIED", human["machineHumanConflictPolicy"])
        self.assertFalse(
            human["hiddenStateInjectionSourceEditCompilationDirectDatabaseOrTerminalOnlyLifecycleShortcutAllowed"]
        )
        self.assertFalse(policy["tolerancePolicy"]["arbitraryGlobalPercentageToleranceAllowed"])
        self.assertTrue(policy["inMotionReadiness"]["baselineSpecificMaximaFrozenBeforeFormalQualification"])

    def test_dossier_retention_status_and_atomic_replacement_are_closed(self) -> None:
        retention = self.profile["qualificationDossierRetentionStatusAndReplacement"]
        self.assertEqual("D4-026.5", retention["decision"])
        self.assertEqual(".local/qualification/candidate/", retention["paths"]["candidate"])
        self.assertEqual(".local/qualification/current/", retention["paths"]["current"])
        self.assertEqual(
            {"ABSENT", "QUALIFIED", "STALE", "WITHDRAWN", "NOT_QUALIFIED"},
            set(retention["currentStatusVocabulary"]),
        )
        self.assertTrue(retention["gitIgnored"])
        self.assertFalse(retention["automaticRemoteUploadAllowed"])
        self.assertTrue(retention["replacement"]["atomicCurrentReplacementRequired"])
        self.assertTrue(retention["replacement"]["previousCurrentPreservedUntilNewCurrentVerified"])
        self.assertFalse(retention["replacement"]["dossierHistoryRetained"])
        self.assertFalse(retention["failedCandidate"]["replacesCurrentDossier"])
        self.assertFalse(retention["humanPolicy"]["withdrawalMayBeReversedByStatusEditOrOlderDossierRestore"])
        self.assertTrue(retention["r0PreservesCurrentDossierAndShortStatus"])
        self.assertFalse(retention["statusIsSecondLifecycleAuthority"])

    def test_human_review_and_current_status_schemas_are_closed(self) -> None:
        self.assertFalse(self.human_review_schema["additionalProperties"])
        self.assertEqual(
            "MACHINE_PASSED_AND_HUMAN_ACCEPTED",
            self.human_review_schema["properties"]["qualificationRule"]["const"],
        )
        self.assertFalse(self.qualification_status_schema["additionalProperties"])
        self.assertEqual(
            {"ABSENT", "QUALIFIED", "STALE", "WITHDRAWN", "NOT_QUALIFIED"},
            set(self.qualification_status_schema["properties"]["status"]["enum"]),
        )

    def test_audience_policy_has_bounded_core_without_weakening_gates(self) -> None:
        audience = self.profile["audiencePresentationPolicy"]
        self.assertEqual("D4-026.6", audience["decision"])
        self.assertEqual("AUDIENCE_PRESENTATION", audience["mode"])
        self.assertEqual(30, audience["plannedCoreNarrativeMinutes"])
        self.assertEqual(45, audience["reservedAudienceSlotMinutes"])
        self.assertFalse(audience["questionAndAnswerInsideReservedAudienceSlot"])
        self.assertFalse(audience["timingIsAosCloudOrVehiclePerformanceKpi"])
        self.assertTrue(audience["realCloudWaitStateMustRemainVisible"])
        self.assertFalse(audience["cloudWaitMayBeHiddenConvertedToReplayOrPresentedAsVehicleKpi"])
        self.assertEqual(8, len(audience["mandatoryCoreStory"]))
        self.assertIn("VU_VALIDATION", audience["mandatoryLifecycleControls"])
        self.assertIn("OEM_AUTHORIZATION", audience["mandatoryLifecycleControls"])
        self.assertTrue(audience["presenterUiMaySummarizeMandatoryControls"])
        self.assertFalse(audience["presenterUiMaySkipPreapproveOrSimulateMandatoryControls"])
        self.assertFalse(audience["optionalExtensionMayReplaceMandatoryGate"])
        self.assertIn("DESTRUCTIVE_QUALIFICATION", audience["forbiddenAudienceSteps"])
        self.assertFalse(audience["createsOrModifiesQualificationDossier"])

    def test_stage_and_case_verdicts_fail_closed(self) -> None:
        rules = self.profile["verdictCompositionAndQualification"]
        self.assertEqual("NOT_EVALUATED", rules["stageVerdictRules"]["entryBlockedBeforeAction"]["acceptanceVerdict"])
        self.assertEqual("FAILED", rules["stageVerdictRules"]["provenMandatoryExitMismatch"])
        self.assertFalse(rules["stageVerdictRules"]["optionalAssertionAffectsVerdict"])
        self.assertEqual("ANY_MANDATORY_STAGE_FAILED_MEANS_FAILED", rules["acceptanceCasePrecedence"][0])
        self.assertFalse(rules["manualVerdictOverrideAllowed"])
        self.assertFalse(rules["oemApprovalAutomaticallyPassesStageOrCase"])

    def test_dossier_pass_needs_r0_and_forbidden_data_scan(self) -> None:
        dossier = self.profile["verdictCompositionAndQualification"]["dossierVerdictRules"]
        self.assertEqual("PASSED", dossier["allD4026RequiredCasesAndR0Passed"])
        self.assertEqual("INCOMPLETE", dossier["blockedMissingStaleUncertainOrUnreconciledStage"])
        self.assertTrue(dossier["passRequiresForbiddenDataScanPass"])
        self.assertEqual("D4_026", dossier["requiredCaseAndModeSetOwnedBy"])

    def test_framework_qualification_precedes_real_operations(self) -> None:
        accepted = self.profile["verdictCompositionAndQualification"]
        self.assertIn("FULL_VERDICT_TRUTH_TABLE_PASSES", accepted["frameworkQualification"])
        self.assertIn("ONE_CONTROLLED_SYNTHETIC_FRAMEWORK_RUN_PASSES_BEFORE_REAL_OPERATIONS", accepted["frameworkQualification"])
        self.assertTrue(accepted["implementationAndRealBaselineApplicationRemainOpen"])
        self.assertFalse(accepted["designReviewAuthorizesImplementationOrExternalMutation"])


if __name__ == "__main__":
    unittest.main()
