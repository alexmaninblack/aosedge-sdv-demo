# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "contracts" / "demo-run-state" / "demo-run-state-profile.v1.json"


class DemoRunStateContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profile = json.loads(PROFILE.read_text(encoding="utf-8"))

    def test_all_subdecisions_and_package_are_design_reviewed(self) -> None:
        self.assertEqual("D4-021", self.profile["decision"])
        self.assertEqual("1.1.0", self.profile["contractVersion"])
        self.assertEqual("DESIGN_REVIEWED", self.profile["lifecycleState"])
        self.assertEqual(
            {"D4-021.1", "D4-021.2", "D4-021.3", "D4-021.4", "D4-021.5", "D4-021.6"},
            {item["id"] for item in self.profile["acceptedSubdecisions"]},
        )

    def test_factory_is_independent_immutable_and_digest_checked(self) -> None:
        factory = self.profile["factoryImage"]
        self.assertEqual(".local/factory/oem-demo-factory.qcow2", factory["imagePath"])
        self.assertEqual("0444", factory["fileMode"])
        self.assertFalse(factory["symlinkAllowed"])
        self.assertFalse(factory["hardLinkAllowed"])
        self.assertEqual({"M0_ENTRY", "R0_EXIT"}, set(factory["digestVerificationPoints"]))
        self.assertFalse(factory["modifiedByDemoRun"])
        self.assertTrue(factory["retainedAfterSuccessfulR0"])

    def test_only_two_current_overlays_exist_and_are_never_reused(self) -> None:
        overlays = self.profile["currentOverlays"]
        self.assertEqual(
            {
                "VALIDATION": ".local/demo-current/validation.qcow2",
                "PRODUCTION": ".local/demo-current/production.qcow2",
            },
            overlays["exactFiles"],
        )
        self.assertEqual("0600", overlays["fileMode"])
        self.assertTrue(overlays["createdFreshAtM0"])
        self.assertFalse(overlays["provisionedOverlayMayBeCopiedOrUsedAsNextRunSource"])
        self.assertTrue(overlays["existingCurrentRunBlocksNewM0UntilReconciledOrSuccessfullyRetired"])
        self.assertTrue(overlays["deletedOnlyAfterSuccessfulR0"])
        self.assertFalse(self.profile["repositoryLocalLayout"]["historicalRunDirectoriesAllowed"])

    def test_current_run_journal_is_minimal_restart_safe_and_non_authoritative(self) -> None:
        journal = self.profile["currentRunJournal"]
        self.assertEqual(".run/demo-current/journal.json", journal["path"])
        self.assertEqual("0700", journal["directoryMode"])
        self.assertEqual("0600", journal["fileMode"])
        self.assertTrue(journal["persistsAcrossLauncherAndMacRestart"])
        self.assertEqual("DEMO_ORCHESTRATOR", journal["singleWriter"])
        self.assertEqual("TEMP_FILE_FLUSH_AND_RENAME", journal["atomicUpdate"])
        self.assertFalse(journal["authoritativeExternalStateSource"])
        self.assertTrue(journal["externalStateMustBeRereadAfterRestart"])
        self.assertFalse(journal["audienceVisibleDemoRunIdIntroduced"])
        self.assertFalse(journal["uncertainStateAllowsBlindRetry"])
        self.assertTrue(journal["missingOrCorruptWithExistingOverlayBlocksM0"])
        self.assertTrue(journal["deletedAfterSuccessfulR0"])
        self.assertTrue(journal["retainedUntilReconciledWhenR0Incomplete"])
        allowed = set(journal["allowedContent"])
        self.assertIn("BOUNDED_CURRENT_RUN_EXTERNAL_OPERATION_REGISTRY", allowed)
        self.assertIn("PER_OPERATION_RESOURCE_CONFLICT_KEYS", allowed)
        self.assertNotIn("CURRENT_RUN_EXTERNAL_OPERATION_IDENTIFIERS", allowed)
        forbidden = set(journal["forbiddenContent"])
        self.assertIn("PRIVATE_KEYS", forbidden)
        self.assertIn("RAW_CLOUD_RESPONSES", forbidden)
        self.assertIn("BACKEND_CLEANUP_CONFIRMATION_TOKENS", forbidden)
        self.assertIn("PREVIOUS_RUN_HISTORY", forbidden)

    def test_interrupted_operations_use_resource_scoped_recovery(self) -> None:
        recovery = self.profile["interruptedOperationRecovery"]
        registry = recovery["operationRegistry"]
        conflicts = recovery["resourceConflictPolicy"]
        helper = recovery["helperCapacity"]
        self.assertTrue(registry["bounded"])
        self.assertGreaterEqual(registry["maximumNonterminalEntries"], 3)
        self.assertFalse(registry["ordinaryOperationHistoryRetained"])
        self.assertIn("RESOURCE_CONFLICT_KEYS", registry["requiredPerEntry"])
        self.assertTrue(conflicts["unrelatedMutationsMayProceed"])
        self.assertTrue(conflicts["readOnlyNavigationAndAuthoritativeReadsRemainAvailable"])
        self.assertTrue(conflicts["conflictWhenAnyExactKeyMatches"])
        self.assertEqual(
            {
                "CANDIDATE_DIGEST",
                "PUBLICATION_PROFILE",
                "CLOUD_OBJECT",
                "VERIFICATION_BATCH",
                "FLEET_VALIDATION_BATCH",
                "CAMPAIGN",
                "UNIT",
                "UNIT_SET",
            },
            set(conflicts["conflictKeyNamespaces"]),
        )
        self.assertEqual(
            {
                "PROVISIONING",
                "IDENTITY_RETIREMENT",
                "LIVE_SOURCE_HANDOVER_OR_RESET",
                "R0_FREEZE_AND_CLEANUP",
            },
            set(conflicts["runExclusiveOperationClasses"]),
        )
        self.assertTrue(conflicts["runExclusiveOperationConflictsWithEveryMutation"])
        self.assertTrue(conflicts["r0RequiresNoOtherNonterminalOperation"])
        self.assertTrue(helper["busyAffectsOnlyRequestedOperation"])
        self.assertEqual("WAITING", helper["busyVisibleState"])
        self.assertFalse(helper["presentedAsAosCloudRestriction"])
        self.assertFalse(helper["automaticSubmissionWhenCapacityReturns"])
        self.assertFalse(helper["automaticCrossTeamQueueOrTriggerAllowed"])
        self.assertFalse(recovery["successfulHttpResponseMeansCompleted"])
        self.assertEqual("RECONCILING", recovery["successfulHttpResponseNextState"])
        self.assertEqual("UNCERTAIN", recovery["timeoutLostResponseProcessOrMacRestartState"])
        self.assertFalse(recovery["restartPerformsMutationBeforeReread"])
        self.assertEqual(
            {"APPLIED", "NOT_APPLIED", "CONTRADICTORY", "UNOBSERVABLE"},
            set(recovery["reconciliationClassifications"]),
        )
        self.assertTrue(recovery["appliedAllowsJournalAdvance"])
        self.assertFalse(recovery["notAppliedAllowsAutomaticResubmit"])
        self.assertTrue(recovery["notAppliedRequiresExactProofAndNewExplicitConfirmation"])
        self.assertTrue(recovery["contradictoryOrUnobservableBlocks"])
        self.assertFalse(recovery["unresolvedOperationBlocksUnrelatedResourceScopes"])
        self.assertTrue(recovery["corruptRegistryBlocksAllMutationsButAllowsReadOnlyDiagnosis"])
        self.assertTrue(recovery["notFoundProvesAbsenceOnlyWithIndependentVisibilityProof"])
        self.assertTrue(recovery["partialProvisioningRequiresBothRolesReconciledBeforeRetryDisposalOrNewM0"])
        self.assertTrue(recovery["partialR0ResumesAtFirstUnprovenStep"])
        self.assertFalse(recovery["partialR0RepeatsProvenDestructiveAction"])
        self.assertTrue(recovery["overlaysRetainedUntilCloudIdentityAndBackendCleanupAreProven"])
        self.assertEqual("RECOVERY_REQUIRED", recovery["corruptJournalState"])
        self.assertFalse(recovery["automaticRollbackOrJustInCaseDeletionAllowed"])

    def test_r0_is_ordered_validation_then_demonstration_and_deletes_journal_last(self) -> None:
        r0 = self.profile["completeR0Ordering"]
        self.assertEqual(["VALIDATION", "PRODUCTION"], r0["unitRetirementOrder"])
        self.assertEqual("DELETE_CURRENT_RUN_JOURNAL_LAST", r0["orderedPhases"][-2])
        self.assertEqual("PASS_NEXT_M0_EXIT_GATE", r0["orderedPhases"][-1])
        self.assertFalse(r0["persistentUnitSetObjectsDeleted"])
        self.assertFalse(r0["aosCloudAuditBatchOrCampaignHistoryDeleted"])
        self.assertTrue(r0["functionalCleanupUsesExactCurrentVuAndDuSystemUids"])
        self.assertTrue(r0["functionalVolumeResetRequiresProvenBackendCleanup"])
        self.assertTrue(r0["overlayDeletionRequiresProvenCloudRetirementBackendCleanupAndStoppedVm"])
        self.assertFalse(r0["factoryImageDeletedOrModified"])
        self.assertTrue(r0["journalDeletedLast"])
        self.assertEqual(
            "HALT_RETAIN_JOURNAL_AND_REMAINING_OVERLAYS_BLOCK_NEXT_M0",
            r0["uncertainStepBehavior"],
        )
        self.assertFalse(r0["presentedAsFotaOrSotaRollback"])
        self.assertIn("PROVE_OLD_CREDENTIAL_CANNOT_RETURN_UNIT_ONLINE", r0["perUnitRetirement"])
        self.assertIn("PERSISTENT_VERIFICATION_AND_PRODUCTION_UNIT_SETS_EMPTY", r0["exitGate"])

    def test_function_cleanup_and_unified_carla_shutdown_are_bounded(self) -> None:
        cleanup = self.profile["functionalDataAndSimulatorCleanup"]
        self.assertEqual("DEMO_ORCHESTRATOR_ONLY", cleanup["backendCleanupCaller"])
        self.assertFalse(cleanup["browserOrSotaServiceMayInvokeCleanup"])
        self.assertEqual(["BRAKE", "TIRE"], cleanup["backendOrder"])
        self.assertEqual("MEMORY_ONLY", cleanup["confirmationTokenStorage"])
        self.assertTrue(cleanup["restartRequiresNewPreview"])
        self.assertFalse(cleanup["crossFunctionDeletionAllowed"])
        self.assertTrue(cleanup["containersStopAndVolumesResetOnlyAfterBothBackendsProveClean"])
        self.assertTrue(cleanup["escapeAndR0UseSameUnifiedShutdownPath"])
        self.assertFalse(cleanup["broadProcessKillAllowed"])
        self.assertFalse(cleanup["carlaInstallationMapsAssetsSourceOrPreparedScenariosDeleted"])
        self.assertTrue(cleanup["cleanupFailureBlocksOverlayDeletionAndNextM0"])
        self.assertIn("EXECUTE_D4_004_CANONICAL_FREE_DRIVE_RESET", cleanup["simulatorSequence"])
        self.assertIn("UNIFIED_STACK_SHUTDOWN_CONTROL_UI_CONTROLLER_GATEWAY_CARLA", cleanup["simulatorSequence"])

    def test_next_run_readiness_is_exact_local_state_and_requires_new_m1_identities(self) -> None:
        readiness = self.profile["nextRunReadinessProof"]
        self.assertEqual("READY_FOR_M0", readiness["localState"])
        self.assertFalse(readiness["isAosCloudState"])
        self.assertTrue(readiness["requiresExactEqualityNotWarning"])
        self.assertEqual("BLOCKED", readiness["missingProofState"])
        self.assertFalse(readiness["ordinaryRunHistoryRetained"])
        self.assertTrue(readiness["formalQualificationMayRetainSanitizedDossierOnly"])
        self.assertFalse(readiness["nextM0CreatesCloudIdentity"])
        self.assertTrue(readiness["nextM1MustProveNewSystemUidUnitUuidNodeUuidAndVissFingerprint"])
        self.assertFalse(readiness["repeatabilityProvedByHistoricalRunDatabase"])
        self.assertIn("AOSCLOUD_AUDIT_BATCH_AND_CAMPAIGN_HISTORY_RETAINED", readiness["cloudChecks"])
        self.assertIn("PREBUILT_VDP_BRAKE_TIRE_ARTIFACTS_AND_DIGEST_CATALOGUE_RETAINED", readiness["localChecks"])


if __name__ == "__main__":
    unittest.main()
