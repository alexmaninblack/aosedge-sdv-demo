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
        self.assertEqual("1.7.0", self.profile["contractVersion"])
        self.assertEqual("DESIGN_REVIEWED", self.profile["lifecycleState"])
        self.assertEqual(
            {"D4-021.1", "D4-021.2", "D4-021.3", "D4-021.4", "D4-021.5", "D4-021.6"},
            {item["id"] for item in self.profile["acceptedSubdecisions"]},
        )

    def test_unit_increment_does_not_silently_claim_or_perform_full_r0(self) -> None:
        unit = self.profile["unitLifecycleIncrement"]
        self.assertEqual(["unit provision", "unit deprovision", "unit delete"], unit["commands"])
        self.assertEqual(["test", "production"], unit["allOrder"])
        for key in ("runExclusive", "oneSdkAttemptPerFreshGuest", "deprovisionRequiresOffline",
                    "deleteRequiresUnitAndNodeAbsenceWithIndependentVisibility",
                    "retainPersistentRoleSetsAndCampaignDefinitions", "retainLocalDisksAccessAndJournal"):
            self.assertTrue(unit[key])
        self.assertEqual(["AUTHORITATIVE_NEW_OFFLINE", "VM_STOPPED"], unit["deprovisionCompletion"])
        for key in ("oldIdentityProbeIsTlsRevocationProof", "oldIdentityReconnectProbe", "foreignRoleMembersRemovedAutomatically",
                    "retiredOverlayReuseAllowed", "fullR0OrRepeatabilityQualificationClaim"):
            self.assertFalse(unit[key])

    def test_test_scoped_retirement_keeps_peer_and_requires_fresh_exact_proofs(self) -> None:
        scoped = self.profile["testScopedLocalLifecycleAmendment"]
        self.assertEqual("TEST_ONLY_WITH_EXISTING_PRODUCTION_PRESERVED", scoped["scope"])
        for key in ("productionRoleSetMayRemainNonempty", "backendCleanupRequiresExactTestUidProofBeforeIdentityRemoval",
                    "callbacksReceiveFullJournalToPreservePeerOnReconciliation", "callbacksMustReturnLiteralTrue",
                    "cloudAndBackendProofRepeatedOnInterruptedUnlink", "deleteOnlyOwnedStoppedUnheldTestOverlayAndAccessFiles",
                    "removeTerminalTestComponentAndPreparationReceipts", "uncertainOrPeerTargetedComponentReceiptsBlock"):
            self.assertTrue(scoped[key])
        for key in ("freshTestCopiesFactoryAgain", "retiredTestOverlayReuseAllowed",
                    "changesLegacyAllRetireSemantics", "fullStudioLifecycleQualificationClaim"):
            self.assertFalse(scoped[key])
        self.assertIn("PRODUCTION_RUNTIME", scoped["preserve"])
        self.assertIn("RELEASE_NUMBER_CONTINUITY", scoped["preserve"])

    def test_cloud_retired_cli_cleanup_keeps_original_and_requires_fresh_proof(self) -> None:
        cleanup = self.profile["cloudRetiredLocalCleanup"]
        self.assertEqual("environment retire", cleanup["command"])
        for key in ("requiresAllCurrentCloudIdentitiesDeleted",
                    "requiresFreshAuthenticatedUnitNodeAndSystemUidAbsence", "requiresPersistentRoleSetsEmpty",
                    "requiresStoppedVmsDnsAndUnheldOwnedFiles", "freshCloudReadsRepeatedOnInterruptedCleanup",
                    "deleteTrackedOverlaysAndAccessMaterial", "deleteWorkingFactoryCopyAndGeneratedManifest",
                    "deleteJournalLast", "preserveOriginalArtifactAndPublishedManifests"):
            self.assertTrue(cleanup[key])
        for key in ("requiresRecordedOldIdentityRejection", "performsCloudMutations", "backupCreated", "fullScenarioR0Claim"):
            self.assertFalse(cleanup[key])

    def test_factory_is_independent_immutable_and_digest_checked(self) -> None:
        factory = self.profile["factoryImage"]
        self.assertEqual(".local/factory/oem-demo-factory.qcow2", factory["imagePath"])
        self.assertEqual(".local/factory/oem-demo-factory.img", factory["imagePathsByFormat"]["raw"])
        self.assertTrue(factory["copyPreservesSourceBytesFormatAndDigest"])
        self.assertEqual("0444", factory["fileMode"])
        self.assertFalse(factory["symlinkAllowed"])
        self.assertFalse(factory["hardLinkAllowed"])
        self.assertEqual({"M0_ENTRY", "R0_EXIT"}, set(factory["digestVerificationPoints"]))
        self.assertFalse(factory["modifiedByDemoRun"])
        self.assertTrue(factory["retainedAfterSuccessfulR0"])

    def test_unused_manufactured_cleanup_is_not_a_cloud_retirement_shortcut(self) -> None:
        cleanup = self.profile["localCreationAmendment"]["unusedManufacturedCleanup"]
        self.assertEqual("UNPROVISIONED_LOCAL_CREATE_ONLY", cleanup["scope"])
        self.assertTrue(cleanup["requiresSuccessfulCreate"])
        self.assertTrue(cleanup["requiresNoCloudIdentityOrLiveSource"])
        self.assertTrue(cleanup["requiresNoOpenHandles"])
        self.assertTrue(cleanup["neverStartedRequiresNoGuestOwnedDataExtents"])
        self.assertTrue(cleanup["bootedRequiresStoppedUnprovisionedObservationAndMatchingOverlayDigest"])
        self.assertTrue(cleanup["deleteTrackedLocalAccessKeysWithOverlays"])
        self.assertTrue(cleanup["preserveOriginalArtifactAndPublishedManifests"])
        self.assertTrue(cleanup["deleteLocalFactoryCopyAndGeneratedManifestAfterOverlays"])
        self.assertTrue(cleanup["supportsBoundFactoryCopyLeftByFormerRetire"])
        self.assertTrue(cleanup["journalDeletedAfterAllRecordedOverlays"])
        self.assertFalse(cleanup["backupCreated"])
        self.assertFalse(cleanup["fullCloudR0Claim"])

    def test_local_vm_lifecycle_does_not_hide_cloud_or_force_kill(self) -> None:
        lifecycle = self.profile["localVmLifecycleAmendment"]
        self.assertEqual(["vm start", "vm stop"], lifecycle["commands"])
        self.assertTrue(lifecycle["processOwnershipRereadBeforeRetry"])
        self.assertTrue(lifecycle["sharedDnsStoppedAfterLastManagedVm"])
        self.assertTrue(lifecycle["currentVehicleStopRequiresDetachOrPark"])
        self.assertFalse(lifecycle["passwordPersistedOrDiscoveredFromLegacyScripts"])
        self.assertFalse(lifecycle["automaticVmForceKill"])
        self.assertFalse(lifecycle["cloudOrCarlaActions"])
        self.assertFalse(lifecycle["fullDemoQualificationClaim"])

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
