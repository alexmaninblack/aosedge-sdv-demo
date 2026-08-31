# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_ROOT = ROOT / "contracts" / "brake-cloud-api"
TELEMETRY_ROOT = ROOT / "contracts" / "brake-telemetry-window"


def load(name: str) -> dict:
    return json.loads((CONTRACT_ROOT / name).read_text(encoding="utf-8"))


class BrakeCloudApiContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profile = load("brake-cloud-api-profile.v1.json")
        cls.query_admin_profile = load("brake-cloud-query-admin-profile.v1.json")
        cls.current_unit_context_schema = load("current-unit-context.schema.json")
        cls.rfc8785_vectors_schema = load("rfc8785-edge-vectors.schema.json")
        cls.ack_schema = load("brake-cloud-ack.schema.json")
        cls.advisory_schema = load("brake-advisory-fact.schema.json")
        cls.cleanup_schema = load("cleanup-preview.schema.json")
        cls.query_schema = load("query-page.schema.json")
        cls.window_detail_schema = load("window-detail.schema.json")
        cls.error_schema = load("error-response.schema.json")
        cls.sse_schema = load("sse-change-notification.schema.json")
        cls.cleanup_preview_request_schema = load("cleanup-preview-request.schema.json")
        cls.cleanup_execute_request_schema = load("cleanup-execute-request.schema.json")
        cls.cleanup_result_schema = load("cleanup-result.schema.json")
        cls.ack = load("fixtures/brake-cloud-ack.valid.json")
        cls.advisory = load("fixtures/brake-advisory-fact.valid.json")
        cls.cleanup = load("fixtures/cleanup-preview.valid.json")
        cls.query_page = load("fixtures/query-window-page.valid.json")
        cls.window_detail = load("fixtures/window-detail.valid.json")
        cls.window_chunk = json.loads(
            (TELEMETRY_ROOT / "fixtures/window-chunk.valid.json").read_text(encoding="utf-8")
        )
        cls.error = load("fixtures/error-response.valid.json")
        cls.sse = load("fixtures/sse-change-notification.valid.json")
        cls.cleanup_preview_request = load("fixtures/cleanup-preview-request.valid.json")
        cls.cleanup_execute_request = load("fixtures/cleanup-execute-request.valid.json")
        cls.cleanup_result = load("fixtures/cleanup-result.valid.json")
        cls.current_unit_context = load("fixtures/current-unit-context.valid.json")
        cls.pending_event_page = load("fixtures/query-event-page.pending-vdp.valid.json")
        cls.rfc8785_vectors = load("fixtures/rfc8785-edge-vectors.json")

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
        self.assertTrue(ack["completionReceiptMayPrecedeTerminalProjection"])
        self.assertEqual("PARTIAL_NON_TERMINAL", ack["missingChunkProjectionState"])
        self.assertEqual("QUARANTINE_NON_TERMINAL", ack["inconsistentCombinedWindowDisposition"])
        self.assertEqual("DURABLE_ACK_ALLOWED", ack["outOfOrderChunkPersistence"])
        self.assertEqual("WITHHELD_NO_SSE_CHANGE", ack["preStartLaterChunkQueryVisibility"])

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
        canonical = json.dumps(
            self.advisory["content"],
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode()
        self.assertEqual(hashlib.sha256(canonical).hexdigest(), self.advisory["contentSha256"])
        self.assertEqual(
            "a2dc0c016d5281c9accead1d6447600d4a2c3736acaef1f725a2831efe334cad",
            hashlib.sha256(
                (CONTRACT_ROOT / "fixtures/brake-advisory-fact.valid.json").read_bytes()
            ).hexdigest(),
        )

    def test_persistence_and_current_run_cleanup_are_explicit(self) -> None:
        persistence = self.profile["persistence"]
        self.assertEqual(("SQLITE", "WAL", "FULL"), (persistence["engine"], persistence["journalMode"], persistence["synchronous"]))
        self.assertEqual("IMMUTABLE_BRAKE_BACKEND_CONTAINER_IMAGE", persistence["runtimeAndMigrationsLocation"])
        self.assertEqual("DEDICATED_EXTERNAL_DOCKER_PERSISTENT_VOLUME", persistence["databaseStorage"])
        self.assertFalse(persistence["dashboardDirectDatabaseAccessAllowed"])
        self.assertEqual("SINGLE_SERIALIZED_WRITER", persistence["writeConcurrency"])
        self.assertEqual("schema_version", persistence["schemaVersionTable"])
        self.assertIn("IMMUTABLE_001", persistence["foundationMigrationOne"])
        self.assertIn("RECORD_V2", persistence["dataMigrationTwo"])
        self.assertEqual("SCHEMA_VERSION_IF_PRESENT_ELSE_SCHEMA_MIGRATIONS", persistence["migrationRunnerLedgerSelection"])
        self.assertIn("receipts", persistence["tables"])
        self.assertIn("windows", persistence["tables"])
        self.assertFalse(persistence["automaticDowngradeAllowed"])
        self.assertTrue(persistence["ordinaryContainerRestartPreservesData"])
        self.assertFalse(persistence["separateDatabaseBackupRequired"])
        self.assertFalse(persistence["failureCreatesDurableAcknowledgement"])
        self.assertFalse(persistence["historicalDemoRunArchive"])
        cleanup = self.profile["cleanup"]
        self.assertEqual("LOCAL_DEMO_ORCHESTRATOR_ONLY", cleanup["accessBoundary"])
        self.assertEqual("CURRENT_RUN_PROVISIONING_JOURNAL", cleanup["selectorSource"])
        self.assertEqual(2, cleanup["exactSystemUidCount"])
        self.assertFalse(cleanup["selectorContainsDemoRunId"])
        self.assertFalse(cleanup["selectorContainsRunTimeRange"])
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
        self.assertEqual("1.0.0", self.cleanup["contractVersion"])
        self.assertEqual(sorted(self.cleanup["systemUids"]), self.cleanup["systemUids"])
        self.assertNotIn("demoRunId", self.cleanup)

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
        self.assertEqual(
            "Test Vehicle",
            self.profile["presentation"]["userFacingUnitRoleLabels"]["VALIDATION"],
        )

    def test_injected_current_unit_context_is_exact_and_not_cloud_state(self) -> None:
        context_profile = self.query_admin_profile["currentUnitContext"]
        self.assertEqual("REQUIRED_EXPLICIT_APPLICATION_INPUT", context_profile["injection"])
        self.assertEqual("CURRENT_RUN_PROVISIONING_JOURNAL", context_profile["acceptedSource"])
        self.assertEqual(2, context_profile["exactUnitCount"])
        self.assertTrue(context_profile["distinctSystemUidsRequired"])
        self.assertFalse(context_profile["cloudLifecycleOrReadinessFieldsAllowed"])
        self.assertFalse(context_profile["cloudLookupOrInferenceAllowed"])
        self.assertIn("DEFERRED", context_profile["liveProvisioningJournalAdapter"])
        context = self.current_unit_context
        self.assertEqual("VALIDATION", context["testUnit"]["unitRole"])
        self.assertEqual("PRODUCTION", context["productionUnit"]["unitRole"])
        self.assertNotEqual(context["testUnit"]["systemUid"], context["productionUnit"]["systemUid"])
        self.assertEqual("Test Vehicle", context["testUnit"]["userFacingRole"])
        self.assertFalse({"ready", "lifecycleState", "cloudState"} & set(context))
        rest = self.query_admin_profile["rest"]
        self.assertEqual("200_EMPTY_PAGE_WITH_CONTEXT_ROLE", rest["emptyCurrentUnitBehavior"])
        self.assertEqual("404_UNIT_NOT_CURRENT", rest["nonCurrentUnitBehavior"])

    def test_query_pagination_and_error_mapping_are_exact(self) -> None:
        annex = self.query_admin_profile
        self.assertEqual("ACCEPTED", annex["lifecycleState"])
        self.assertEqual("1.1.0", annex["contractVersion"])
        self.assertEqual("1.0.0", annex["acceptedBaseContractVersion"])
        pagination = annex["rest"]["pagination"]
        self.assertEqual((1, 50, 100), (pagination["minimumLimit"], pagination["defaultLimit"], pagination["maximumLimit"]))
        self.assertEqual("OPAQUE_KEYSET_CURSOR", pagination["style"])
        self.assertEqual("BASE64URL_NO_PADDING_OF_RFC8785_JSON_ARRAY", pagination["cursorEncoding"])
        self.assertFalse(pagination["snapshotIsolationClaimed"])
        routes = annex["rest"]["routes"]
        self.assertEqual({"WINDOW", "ASSESSMENT", "EVENT", "ADVISORY"}, {route["resourceType"] for route in routes})
        mappings = {item["errorCode"]: (item["httpStatus"], item["retryable"]) for item in annex["errors"]["mappings"]}
        self.assertEqual((400, False), mappings["INVALID_CURSOR"])
        self.assertEqual((404, False), mappings["UNIT_NOT_CURRENT"])
        self.assertEqual((409, False), mappings["PREVIEW_STALE"])
        self.assertEqual((409, False), mappings["PREVIEW_TOKEN_EXPIRED"])
        self.assertEqual((503, True), mappings["TEMPORARILY_UNAVAILABLE"])
        self.assertEqual((503, True), mappings["CURRENT_UNIT_CONTEXT_UNAVAILABLE"])
        self.assertEqual("WINDOW", self.query_page["resourceType"])
        self.assertIsNone(self.query_page["nextCursor"])
        self.assertEqual("INVALID_CURSOR", self.error["errorCode"])

    def test_window_detail_is_additive_bounded_and_non_paged(self) -> None:
        annex = self.query_admin_profile
        self.assertIn("BC-WINDOW-DETAIL-DEC-01", annex["acceptedClarifications"])
        self.assertNotIn("proposedClarifications", annex)
        self.assertEqual(4, len(annex["rest"]["routes"]))
        detail = annex["rest"]["pointReads"]
        self.assertEqual(1, len(detail))
        detail = detail[0]
        self.assertEqual("WINDOW_DETAIL", detail["resourceType"])
        self.assertEqual("GET", detail["method"])
        self.assertEqual("/units/{systemUid}/windows/{eventId}", detail["path"])
        self.assertEqual("LOWERCASE_UUID_V4", detail["eventIdFormat"])
        self.assertEqual("window-detail.schema.json", detail["responseSchema"])
        self.assertFalse(detail["queryParametersAllowed"])
        self.assertFalse(detail["paginationApplied"])
        self.assertEqual("EXISTING_WINDOW_QUERY_PROJECTION", detail["visibilitySource"])
        self.assertEqual("404_NOT_FOUND", detail["missingVisibleProjectionBehavior"])
        self.assertEqual("VALIDATED_CANONICAL_WINDOW_CHUNK_CONTENT_JSON", detail["sampleSource"])
        self.assertEqual("CHUNK_INDEX_ASC_THEN_STORED_SAMPLE_ARRAY_ORDER", detail["sampleOrder"])
        self.assertEqual((0, 150), (detail["minimumSamples"], detail["maximumSamples"]))
        self.assertTrue(detail["storedSampleFieldsPreserved"])
        self.assertFalse(detail["snapshotIsolationClaimed"])
        self.assertFalse(detail["freshnessClaimed"])

    def test_window_detail_schema_and_fixture_are_closed_and_consistent(self) -> None:
        schema = self.window_detail_schema
        fixture = self.window_detail
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(0, schema["properties"]["samples"]["minItems"])
        self.assertEqual(150, schema["properties"]["samples"]["maxItems"])
        self.assertEqual(
            "../brake-telemetry-window/brake-telemetry-window-chunk.schema.json#/$defs/sample",
            schema["properties"]["samples"]["items"]["$ref"],
        )
        self.assertEqual("WINDOW_DETAIL", fixture["resourceType"])
        self.assertEqual("1.0.0", fixture["contractVersion"])
        self.assertEqual(fixture["unitSystemUid"], fixture["window"]["unitSystemUid"])
        self.assertEqual(fixture["unitRole"], fixture["window"]["unitRole"])
        self.assertEqual(fixture["window"]["receivedSampleCount"], len(fixture["samples"]))
        self.assertEqual(self.window_chunk["eventId"], fixture["window"]["eventId"])
        self.assertEqual(self.window_chunk["content"]["samples"], fixture["samples"])
        self.assertEqual([0, 1], [sample["sampleIndex"] for sample in fixture["samples"]])
        self.assertEqual(["PRE", "ACTIVE"], [sample["phase"] for sample in fixture["samples"]])
        self.assertFalse({"limit", "nextCursor", "cursor"} & set(fixture))

    def test_out_of_order_window_visibility_and_event_vdp_provenance_are_exact(self) -> None:
        visibility = self.query_admin_profile["rest"]["windowProjectionVisibility"]
        self.assertEqual("DURABLE_ACK_ALLOWED", visibility["outOfOrderChunkPersistence"])
        self.assertTrue(visibility["visibleOnlyAfterAuthoritativeStart"])
        self.assertEqual(
            ["CHUNK_INDEX_0_FIRST_SAMPLE_SOURCE_TIMESTAMP", "WINDOW_COMPLETION_WINDOW_START_TIMESTAMP"],
            visibility["authoritativeStartSources"],
        )
        self.assertEqual(
            "PERSIST_WITHHOLD_WINDOW_QUERY_PROJECTION_AND_SSE_CHANGE",
            visibility["laterChunkBeforeAuthoritativeStart"],
        )
        provenance = self.query_admin_profile["rest"]["eventVdpProvenance"]
        self.assertEqual("PENDING_ASSESSMENT_CORRELATION", provenance["initialState"])
        self.assertIsNone(provenance["pendingContractVersion"])
        self.assertIsNone(provenance["pendingContractSha256"])
        self.assertFalse(provenance["inferenceFromServiceVersionOrNearbyRecordAllowed"])
        pending = self.pending_event_page["items"][0]
        self.assertEqual("PENDING_ASSESSMENT_CORRELATION", pending["vdpProvenanceState"])
        self.assertIsNone(pending["vdpContractVersion"])
        self.assertIsNone(pending["vdpContractSha256"])

    def test_sse_is_notification_only_and_always_rereads_rest(self) -> None:
        sse = self.query_admin_profile["sse"]
        self.assertEqual("text/event-stream", sse["responseContentType"])
        self.assertEqual("brake-data-changed", sse["eventName"])
        self.assertFalse(sse["statePayloadAllowed"])
        self.assertFalse(sse["replayOrResumeAuthority"])
        self.assertFalse(sse["lastEventIdIsStateAuthority"])
        self.assertIn("AUTHORITATIVE_REST_REREAD", sse["clientRuleAfterEveryNotification"])
        self.assertIn("AUTHORITATIVE_REST_REREAD", sse["clientRuleAfterEveryReconnect"])
        self.assertEqual("BRAKE_DATA_CHANGED", self.sse["notificationType"])

    def test_admin_transport_and_selector_are_closed(self) -> None:
        admin = self.query_admin_profile["admin"]
        self.assertEqual("HTTP_1_1_OVER_UNIX_DOMAIN_SOCKET", admin["transport"])
        self.assertEqual("0600", admin["socketMode"])
        self.assertEqual("LOCAL_DEMO_ORCHESTRATOR_ONLY", admin["accessBoundary"])
        self.assertFalse(admin["browserAccessAllowed"])
        self.assertFalse(admin["guestIngestionRouteAccessAllowed"])
        self.assertFalse(admin["lanAccessAllowed"])
        self.assertFalse(admin["demoRunIdFieldAllowed"])
        self.assertFalse(admin["runTimeRangeFieldAllowed"])
        self.assertTrue(admin["selectorMustEqualInjectedCurrentUnitContext"])
        digest = admin["recordSetDigest"]
        self.assertEqual("SHA256_OF_RFC8785_CANONICAL_JSON", digest["algorithm"])
        self.assertEqual(
            ["messages", "windows", "assessments", "events", "advisories", "quarantine"],
            digest["logicalTableOrder"],
        )
        self.assertEqual(digest["logicalTableOrder"], [table["name"] for table in digest["tables"]])
        self.assertTrue(all(table["fields"] for table in digest["tables"]))
        self.assertTrue(digest["includeEmptyTableArrays"])
        self.assertEqual("REJECT_BEFORE_CANONICALIZATION", digest["duplicateJsonObjectKeyBehavior"])
        token = admin["confirmationToken"]
        self.assertIn("HMAC_SHA256", token["format"])
        self.assertIn("PROCESS_LOCAL", token["key"])
        self.assertEqual(60, token["ttlSeconds"])
        self.assertEqual(1024, token["maximumLength"])
        self.assertEqual("409_PREVIEW_TOKEN_EXPIRED", token["malformedBehavior"])
        self.assertEqual("409_PREVIEW_TOKEN_EXPIRED", token["badMacBehavior"])
        self.assertEqual("409_PREVIEW_TOKEN_EXPIRED", token["previousProcessOrRestartBehavior"])
        self.assertEqual("NEW_PREVIEW_REQUIRED", token["previousProcessOrRestartNextAction"])
        self.assertEqual("409_PREVIEW_STALE", token["validMacChangedCurrentRowSetBehavior"])
        self.assertFalse(token["failureDeletesRecords"])
        self.assertEqual(
            "409_PREVIEW_TOKEN_EXPIRED",
            admin["execute"]["malformedBadMacExpiredOrPreviousProcessTokenBehavior"],
        )
        self.assertEqual(
            "409_PREVIEW_STALE",
            admin["execute"]["validMacChangedCurrentRowSetBehavior"],
        )
        self.assertFalse(admin["execute"]["tokenFailureDeletesRecords"])
        self.assertEqual(1024, self.cleanup_schema["properties"]["confirmationToken"]["maxLength"])
        self.assertEqual(
            1024,
            self.cleanup_execute_request_schema["properties"]["confirmationToken"]["maxLength"],
        )
        self.assertGreater(len(self.cleanup["confirmationToken"]), 512)
        self.assertLessEqual(len(self.cleanup["confirmationToken"]), 1024)
        self.assertEqual(
            self.cleanup["confirmationToken"],
            self.cleanup_execute_request["confirmationToken"],
        )
        cleanup_profile = self.profile["cleanup"]
        self.assertEqual(1024, cleanup_profile["confirmationTokenMaximumLength"])
        self.assertEqual(
            "409_PREVIEW_TOKEN_EXPIRED",
            cleanup_profile["tokenFailureMapping"]["malformedOrBadMac"],
        )
        self.assertEqual(
            "409_PREVIEW_TOKEN_EXPIRED",
            cleanup_profile["tokenFailureMapping"]["previousProcessOrRestart"],
        )
        self.assertEqual(
            "409_PREVIEW_STALE",
            cleanup_profile["tokenFailureMapping"]["validMacWithChangedCurrentRowSet"],
        )
        for fixture in (
            self.cleanup_preview_request,
            self.cleanup_execute_request,
            self.cleanup_result,
        ):
            self.assertEqual(sorted(fixture["systemUids"]), fixture["systemUids"])
            self.assertNotIn("demoRunId", fixture)
        self.assertTrue(all(value == 0 for value in self.cleanup_result["remainingMatchingRecordCounts"].values()))

    def test_rfc8785_unicode_number_and_duplicate_key_vectors_are_frozen(self) -> None:
        vectors = {vector["id"]: vector for vector in self.rfc8785_vectors["canonicalVectors"]}
        self.assertEqual(
            {"RFC8785_UNICODE_UTF16_ORDER", "RFC8785_NUMBER_SERIALIZATION"},
            set(vectors),
        )
        for vector in vectors.values():
            self.assertEqual(
                vector["canonicalSha256"],
                hashlib.sha256(vector["canonicalJson"].encode()).hexdigest(),
            )
        unicode_vector = vectors["RFC8785_UNICODE_UTF16_ORDER"]
        unicode_input = json.loads(unicode_vector["rawInputJson"])
        utf16_ordered = sorted(unicode_input, key=lambda key: key.encode("utf-16-be"))
        unicode_canonical = "{" + ",".join(
            f"{json.dumps(key, ensure_ascii=False, separators=(',', ':'))}:"
            f"{json.dumps(unicode_input[key], ensure_ascii=False, separators=(',', ':'))}"
            for key in utf16_ordered
        ) + "}"
        self.assertEqual(unicode_vector["canonicalJson"], unicode_canonical)
        numeric = vectors["RFC8785_NUMBER_SERIALIZATION"]
        self.assertEqual(
            numeric["canonicalJson"],
            json.dumps(json.loads(numeric["rawInputJson"]), separators=(",", ":")),
        )
        duplicate = self.rfc8785_vectors["rejectedRawJson"][0]
        with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
            json.loads(duplicate["rawInputJson"], object_pairs_hook=reject_duplicate_keys)
        self.assertEqual("DUPLICATE_JSON_KEY", duplicate["errorCode"])

    def test_schemas_are_closed(self) -> None:
        self.assertFalse(self.ack_schema["additionalProperties"])
        self.assertFalse(self.advisory_schema["additionalProperties"])
        self.assertFalse(self.cleanup_schema["additionalProperties"])
        self.assertFalse(self.cleanup_schema["properties"]["recordCounts"]["additionalProperties"])
        for schema in (
            self.current_unit_context_schema,
            self.rfc8785_vectors_schema,
            self.error_schema,
            self.sse_schema,
            self.cleanup_preview_request_schema,
            self.cleanup_execute_request_schema,
            self.cleanup_result_schema,
            self.window_detail_schema,
        ):
            self.assertFalse(schema["additionalProperties"])
        for name in (
            "windowPage",
            "assessmentPage",
            "eventPage",
            "advisoryPage",
            "windowItem",
            "messageItemAssessment",
            "messageItemEvent",
            "messageItemAdvisory",
            "phaseSampleCounts",
        ):
            self.assertFalse(self.query_schema["$defs"][name]["additionalProperties"])


def reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


if __name__ == "__main__":
    unittest.main()
