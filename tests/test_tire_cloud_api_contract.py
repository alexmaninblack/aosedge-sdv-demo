# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import json
import hashlib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_ROOT = ROOT / "contracts" / "tire-cloud-api"


def load(name: str) -> dict:
    return json.loads((CONTRACT_ROOT / name).read_text(encoding="utf-8"))


class TireCloudApiContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profile = load("tire-cloud-api-profile.v1.json")
        cls.ack_schema = load("tire-cloud-ack.schema.json")
        cls.advisory_schema = load("tire-advisory-fact.schema.json")
        cls.status_schema = load("tire-function-status.schema.json")
        cls.cleanup_schema = load("cleanup-preview.schema.json")
        cls.ack = load("fixtures/tire-cloud-ack.valid.json")
        cls.advisory = load("fixtures/tire-advisory-fact.valid.json")
        cls.status = load("fixtures/tire-function-status.valid.json")
        cls.cleanup = load("fixtures/cleanup-preview.valid.json")

    def test_review_candidate_and_tenant_boundary(self) -> None:
        self.assertEqual("D4-019", self.profile["decision"])
        self.assertEqual("ACCEPTED", self.profile["lifecycleState"])
        transport = self.profile["transport"]
        self.assertEqual("HTTP_1_1", transport["protocol"])
        self.assertEqual("LOCAL_ISOLATED_DEMO_ROUTE", transport["scope"])
        self.assertEqual("OUT_OF_SCOPE_FOR_FIRST_DEMO", transport["authentication"])
        self.assertFalse(transport["applicationLayerAuthenticationImplemented"])
        self.assertFalse(transport["productionBackendSecurityClaimed"])
        self.assertFalse(transport["clientCredentialProvisioningRequired"])
        self.assertFalse(transport["lanExposureAllowed"])
        self.assertFalse(transport["publicNetworkExposureAllowed"])
        self.assertFalse(transport["browserIngestionAllowed"])
        self.assertEqual("CORRELATION_ONLY_NOT_AUTHENTICATED_IDENTITY", transport["messageSystemUidUsage"])
        self.assertFalse(self.profile["persistence"]["sharesDatabaseOrVolumeWithBrakeCloud"])
        self.assertEqual("ASYNCHRONOUS_FROM_BOUNDED_PERSISTENT_OUTBOX", transport["deliveryExecution"])
        self.assertFalse(transport["deliveryMayBlockLocalAssessment"])
        isolation = self.profile["tenantIsolation"]
        self.assertEqual("tire-sp2", isolation["publicationProfile"])
        self.assertFalse(isolation["sharesFailureBoundaryWithBrakeCloud"])
        self.assertFalse(isolation["oemLifecycleAuthority"])

    def test_only_derived_functional_products_are_accepted(self) -> None:
        kinds = self.profile["messageKinds"]
        self.assertEqual(4, len(kinds))
        self.assertEqual(
            {"TIRE_HEALTH_ASSESSMENT", "TIRE_CONDITION_BAND_CHANGED", "TIRE_ADVISORY_FACT", "TIRE_FUNCTION_STATUS"},
            {item["messageType"] for item in kinds},
        )
        self.assertTrue(all(item["idempotencyKeyFields"][:2] == ["unitSystemUid", "messageType"] for item in kinds))
        self.assertIn("CONTINUOUS_RAW_TELEMETRY", self.profile["prohibitedPayload"])
        self.assertIn("FRICTION_FORCE_MULTIPLIER", self.profile["prohibitedPayload"])
        self.assertEqual("FUNCTION_TEAM_REPORTED_NOT_AOSCORE_LIFECYCLE_READINESS", self.profile["functionStatus"]["authority"])
        self.assertEqual(30, self.profile["functionStatus"]["maximumHeartbeatFrequencySeconds"])

    def test_new_logical_fixtures_are_closed_and_digest_bound(self) -> None:
        self.assertFalse(self.advisory_schema["additionalProperties"])
        self.assertFalse(self.advisory_schema["properties"]["content"]["additionalProperties"])
        self.assertFalse(self.status_schema["additionalProperties"])
        self.assertFalse(self.status_schema["properties"]["content"]["additionalProperties"])
        for message in (self.advisory, self.status):
            canonical = json.dumps(message["content"], ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()
            self.assertEqual(hashlib.sha256(canonical).hexdigest(), message["contentSha256"])

    def test_durable_ack_and_cleanup_are_exact(self) -> None:
        acknowledgement = self.profile["acknowledgement"]
        self.assertTrue(acknowledgement["deleteLocalOnlyAfterMatchingDurableAck"])
        self.assertFalse(acknowledgement["responseBeforeTransactionCommitAllowed"])
        self.assertIn(self.ack["state"], acknowledgement["successStates"])
        self.assertEqual("messageKeySha256", acknowledgement["acknowledgementKeyField"])
        self.assertEqual(64, len(self.ack["messageKeySha256"]))
        self.assertTrue(acknowledgement["duplicateReusesOriginalReceiptIdAndReceivedAt"])
        self.assertFalse(acknowledgement["gatewayApplicationAcknowledged"])
        persistence = self.profile["persistence"]
        self.assertEqual("IMMUTABLE_TIRE_BACKEND_CONTAINER_IMAGE", persistence["runtimeAndMigrationsLocation"])
        self.assertEqual("/data/tire-health.sqlite", persistence["databasePath"])
        self.assertFalse(persistence["dashboardDirectDatabaseAccessAllowed"])
        self.assertEqual("SINGLE_SERIALIZED_WRITER", persistence["writeConcurrency"])
        self.assertFalse(persistence["automaticDowngradeAllowed"])
        self.assertTrue(persistence["ordinaryContainerRestartPreservesData"])
        self.assertFalse(persistence["separateDatabaseBackupRequired"])
        self.assertFalse(persistence["failureCreatesDurableAcknowledgement"])
        cleanup = self.profile["cleanup"]
        self.assertEqual("LOCAL_DEMO_ORCHESTRATOR_ONLY", cleanup["accessBoundary"])
        self.assertEqual("CURRENT_RUN_PROVISIONING_JOURNAL", cleanup["selectorSource"])
        self.assertEqual(2, cleanup["exactSystemUidCount"])
        self.assertFalse(cleanup["wildcardAllowed"])
        self.assertTrue(cleanup["emptyMatchingRecordSetAllowed"])
        self.assertEqual("ONE_SQLITE_TRANSACTION", cleanup["transactionScope"])
        self.assertFalse(cleanup["browserAccessAllowed"])
        self.assertFalse(cleanup["guestIngestionRouteAccessAllowed"])
        self.assertFalse(cleanup["lanAccessAllowed"])
        self.assertFalse(cleanup["blindRepeatAllowed"])
        self.assertFalse(cleanup["deletesAosCloudAudit"])
        self.assertFalse(cleanup["deletesBrakeCloudData"])
        self.assertFalse(cleanup["deletesCloudUnitsOrNodes"])
        self.assertFalse(cleanup["deletesVmOrOverlay"])
        self.assertTrue(cleanup["mustCompleteBeforeVolumeReset"])
        self.assertEqual("D4-021", cleanup["overallResetOrderingDecision"])
        self.assertIn("functionStatus", self.cleanup["recordCounts"])
        self.assertNotIn("readiness", self.cleanup["recordCounts"])
        self.assertEqual(2, len(self.cleanup["systemUids"]))

    def test_incompatible_vdp_is_factual_not_admission(self) -> None:
        presentation = self.profile["presentation"]
        self.assertIn("INCOMPATIBLE_VDP", presentation["functionStatusReasons"])
        self.assertEqual("CONTACT_PLATFORM_TEAM_FOR_VDP_V3", presentation["incompatibleVdpGuidance"])
        self.assertFalse(presentation["incompatibleVdpGuidanceIsLifecycleMutation"])
        self.assertEqual(90, presentation["functionStatusStaleAfterSeconds"])
        self.assertIn("EXACT_TREAD_DEPTH", presentation["forbiddenClaims"])

    def test_dashboard_uses_rest_truth_and_sse_only_as_notification(self) -> None:
        query = self.profile["query"]
        self.assertNotIn("/units/{systemUid}/readiness", query["routes"])
        self.assertIn("/units/{systemUid}/function-status", query["routes"])
        self.assertEqual(["/health/live", "/health/ready"], query["backendHealthRoutes"])
        self.assertEqual("CHANGE_NOTIFICATION_ONLY_NOT_STATE_AUTHORITY", query["sseRole"])
        self.assertEqual("AUTHORITATIVE_REST_REREAD", query["sseReconnectBehavior"])
        self.assertEqual("AOSCLOUD_AND_AOSCORE_VIA_SOFTWARE_DELIVERY_DASHBOARD", query["unitServiceReadinessAuthority"])
        self.assertIn("AOSCORE_READINESS_DERIVED_FROM_FUNCTION_STATUS", self.profile["presentation"]["forbiddenClaims"])

    def test_cpu_load_control_is_fixed_and_not_enforcement_authority(self) -> None:
        control = self.profile["qualificationControl"]
        self.assertEqual("D4-023.3", control["decision"])
        self.assertEqual("TIRE_CPU_ISOLATION_PROOF_V1", control["profileId"])
        self.assertEqual({"START_FIXED_CPU_LOAD", "STOP_FIXED_CPU_LOAD"}, set(control["allowedCommands"]))
        self.assertEqual("TIRE_SERVICE_INITIATES_OUTBOUND_BACKEND_REQUEST", control["serviceRouteDirection"])
        self.assertEqual(1, control["maximumConcurrentWorkers"])
        self.assertEqual(180, control["absoluteSafetyCeilingSeconds"])
        self.assertFalse(control["callerSelectedParametersAllowed"])
        self.assertTrue(control["dashboardButtonDisabledWhenSelectedVehicleOffline"])
        self.assertFalse(control["stateProvesAosCoreQuotaEnforcement"])
        self.assertFalse(control["adminExecOrSignalFallbackAllowed"])

    def test_schemas_are_closed(self) -> None:
        self.assertFalse(self.ack_schema["additionalProperties"])
        self.assertFalse(self.cleanup_schema["additionalProperties"])
        self.assertFalse(self.cleanup_schema["properties"]["recordCounts"]["additionalProperties"])


if __name__ == "__main__":
    unittest.main()
