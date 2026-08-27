# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_ROOT = ROOT / "contracts" / "brake-cloud-api"


def load(name: str) -> dict:
    return json.loads((CONTRACT_ROOT / name).read_text(encoding="utf-8"))


class BrakeCloudApiContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profile = load("brake-cloud-api-profile.v1.json")
        cls.ack_schema = load("brake-cloud-ack.schema.json")
        cls.advisory_schema = load("brake-advisory-fact.schema.json")
        cls.cleanup_schema = load("cleanup-preview.schema.json")
        cls.ack = load("fixtures/brake-cloud-ack.valid.json")
        cls.advisory = load("fixtures/brake-advisory-fact.valid.json")
        cls.cleanup = load("fixtures/cleanup-preview.valid.json")

    def test_review_candidate_and_authority_boundary(self) -> None:
        self.assertEqual("D4-017", self.profile["decision"])
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
        self.assertEqual("D4-020", transport["networkIsolationQualificationDecision"])
        self.assertEqual("CORRELATION_ONLY_NOT_AUTHENTICATED_IDENTITY", transport["messageSystemUidUsage"])
        self.assertEqual("FUNCTIONAL_BACKEND_RECORDS_ONLY", self.profile["query"]["dashboardAuthority"])

    def test_transport_cannot_block_local_vehicle_behavior(self) -> None:
        transport = self.profile["transport"]
        self.assertEqual("ASYNCHRONOUS_FROM_BOUNDED_PERSISTENT_OUTBOX", transport["deliveryExecution"])
        self.assertFalse(transport["deliveryMayBlockKuksaConsumption"])
        self.assertFalse(transport["deliveryMayBlockLocalAnalytics"])
        self.assertFalse(transport["deliveryMayBlockLocalAdvisory"])

    def test_durable_ack_is_required_before_local_delete(self) -> None:
        ack = self.profile["acknowledgement"]
        self.assertTrue(ack["deleteLocalOnlyAfterMatchingDurableAck"])
        self.assertFalse(ack["responseBeforeTransactionCommitAllowed"])
        self.assertIn(self.ack["state"], ack["successStates"])
        self.assertEqual(64, len(self.ack["messageKeySha256"]))
        self.assertEqual(64, len(self.ack["contentSha256"]))
        self.assertTrue(ack["duplicateReusesOriginalReceiptIdAndReceivedAt"])
        self.assertIn("ALL_EXPECTED_CHUNKS", ack["windowLocalDeleteRule"])
        self.assertIn("DELIVERY_CONFLICT", ack["conflictLocalDisposition"])
        self.assertFalse(ack["gatewayApplicationAcknowledged"])
        self.assertFalse(ack["driverReceiptAcknowledged"])
        self.assertFalse(ack["oemAcceptanceAcknowledged"])

    def test_idempotency_keys_are_unique_and_bounded(self) -> None:
        kinds = self.profile["messageKinds"]
        self.assertEqual(5, len(kinds))
        self.assertEqual(len(kinds), len({kind["messageType"] for kind in kinds}))
        self.assertTrue(all(kind["idempotencyKeyFields"] for kind in kinds))
        self.assertTrue(all(kind["idempotencyKeyFields"][:2] == ["unitSystemUid", "messageType"] for kind in kinds))
        self.assertTrue(all(kind["maximumCanonicalBytes"] <= 65536 for kind in kinds))
        by_type = {kind["messageType"]: kind for kind in kinds}
        self.assertIn("BRAKE_HEALTH_EVENT", by_type)
        self.assertNotIn("BRAKE_CONDITION_BAND_CHANGED", by_type)
        self.assertEqual("BRAKE_CONDITION_BAND_CHANGED", by_type["BRAKE_HEALTH_EVENT"]["requiredEventType"])

    def test_advisory_fact_is_closed_and_gateway_correlated(self) -> None:
        self.assertFalse(self.advisory_schema["additionalProperties"])
        self.assertFalse(self.advisory_schema["properties"]["content"]["additionalProperties"])
        self.assertEqual("BRAKE_ADVISORY_FACT", self.advisory["messageType"])
        self.assertEqual("APPLIED", self.advisory["gatewayState"])
        self.assertEqual(64, len(self.advisory["contentSha256"]))

    def test_persistence_and_current_run_cleanup_are_explicit(self) -> None:
        persistence = self.profile["persistence"]
        self.assertEqual(("SQLITE", "WAL", "FULL"), (persistence["engine"], persistence["journalMode"], persistence["synchronous"]))
        self.assertEqual("IMMUTABLE_BRAKE_BACKEND_CONTAINER_IMAGE", persistence["runtimeAndMigrationsLocation"])
        self.assertEqual("DEDICATED_EXTERNAL_DOCKER_PERSISTENT_VOLUME", persistence["databaseStorage"])
        self.assertFalse(persistence["dashboardDirectDatabaseAccessAllowed"])
        self.assertEqual("SINGLE_SERIALIZED_WRITER", persistence["writeConcurrency"])
        self.assertFalse(persistence["automaticDowngradeAllowed"])
        self.assertTrue(persistence["ordinaryContainerRestartPreservesData"])
        self.assertFalse(persistence["separateDatabaseBackupRequired"])
        self.assertFalse(persistence["failureCreatesDurableAcknowledgement"])
        self.assertFalse(persistence["historicalDemoRunArchive"])
        cleanup = self.profile["cleanup"]
        self.assertEqual("LOCAL_DEMO_ORCHESTRATOR_ONLY", cleanup["accessBoundary"])
        self.assertEqual("CURRENT_RUN_PROVISIONING_JOURNAL", cleanup["selectorSource"])
        self.assertEqual(2, cleanup["exactSystemUidCount"])
        self.assertFalse(cleanup["wildcardAllowed"])
        self.assertFalse(cleanup["emptySelectorAllowed"])
        self.assertTrue(cleanup["emptyMatchingRecordSetAllowed"])
        self.assertEqual("ONE_SQLITE_TRANSACTION", cleanup["transactionScope"])
        self.assertFalse(cleanup["browserAccessAllowed"])
        self.assertFalse(cleanup["guestIngestionRouteAccessAllowed"])
        self.assertFalse(cleanup["lanAccessAllowed"])
        self.assertFalse(cleanup["blindRepeatAllowed"])
        self.assertFalse(cleanup["deletesAosCloudAudit"])
        self.assertFalse(cleanup["deletesTireBackendData"])
        self.assertFalse(cleanup["deletesCloudUnitsOrNodes"])
        self.assertFalse(cleanup["deletesVmOrOverlay"])
        self.assertTrue(cleanup["mustCompleteBeforeVolumeReset"])
        self.assertEqual("D4-021", cleanup["overallResetOrderingDecision"])
        self.assertEqual(2, len(self.cleanup["systemUids"]))

    def test_dashboard_uses_functional_rest_truth_and_sse_only_as_notification(self) -> None:
        query = self.profile["query"]
        self.assertNotIn("/units/{systemUid}/readiness", query["routes"])
        self.assertEqual(["/health/live", "/health/ready"], query["backendHealthRoutes"])
        self.assertEqual("FUNCTIONAL_BACKEND_RECORDS_ONLY", query["dashboardAuthority"])
        self.assertEqual(
            "AOSCLOUD_AND_AOSCORE_VIA_SOFTWARE_DELIVERY_DASHBOARD",
            query["unitServiceReadinessAuthority"],
        )
        self.assertEqual("CHANGE_NOTIFICATION_ONLY_NOT_STATE_AUTHORITY", query["sseRole"])
        self.assertEqual("AUTHORITATIVE_REST_REREAD", query["sseReconnectBehavior"])
        self.assertIn(
            "AOSCORE_READINESS_DERIVED_FROM_FUNCTIONAL_DATA",
            self.profile["presentation"]["forbiddenClaims"],
        )

    def test_schemas_are_closed(self) -> None:
        self.assertFalse(self.ack_schema["additionalProperties"])
        self.assertFalse(self.advisory_schema["additionalProperties"])
        self.assertFalse(self.cleanup_schema["additionalProperties"])
        self.assertFalse(self.cleanup_schema["properties"]["recordCounts"]["additionalProperties"])


if __name__ == "__main__":
    unittest.main()
