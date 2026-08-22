# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_ROOT = ROOT / "contracts" / "kuksa-current-demo-authorization"
PROFILE = CONTRACT_ROOT / "kuksa-auth-compat.v1.json"
REQUEST_SCHEMA = CONTRACT_ROOT / "kuksa-auth-request.schema.json"
RESPONSE_SCHEMA = CONTRACT_ROOT / "kuksa-auth-response.schema.json"


class KuksaAuthorizationContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profile = json.loads(PROFILE.read_text(encoding="utf-8"))
        cls.request_schema = json.loads(REQUEST_SCHEMA.read_text(encoding="utf-8"))
        cls.response_schema = json.loads(RESPONSE_SCHEMA.read_text(encoding="utf-8"))

    def test_contract_identity_and_framing_are_frozen(self) -> None:
        self.assertEqual("D4-027.8", self.profile["decision"])
        self.assertEqual("1.4.0", self.profile["contractVersion"])
        self.assertEqual("aos-kuksa-auth-compat/v1", self.profile["protocol"])
        self.assertEqual("UNIX_STREAM", self.profile["transport"]["socketType"])
        self.assertEqual("REJECT", self.profile["transport"]["duplicateObjectMembers"])
        self.assertEqual("REJECT", self.profile["transport"]["trailingObjects"])

    def test_only_status_and_issue_requests_exist(self) -> None:
        self.assertEqual(["status", "issue"], self.profile["operations"])
        self.assertEqual("issue", self.profile["renewalOperation"])
        branches = self.request_schema["oneOf"]
        self.assertEqual({"status", "issue"}, {
            branch["properties"]["operation"]["const"] for branch in branches
        })
        self.assertTrue(all(not branch["additionalProperties"] for branch in branches))
        issue = next(
            branch for branch in branches
            if branch["properties"]["operation"]["const"] == "issue"
        )
        self.assertEqual({"protocol", "operation", "aosSecret"}, set(issue["required"]))

    def test_caller_cannot_select_identity_or_authority(self) -> None:
        authority = self.profile["authority"]
        self.assertEqual("kuksa", authority["fixedResource"])
        self.assertFalse(authority["resourceInRequest"])
        self.assertFalse(authority["callerIdentityInRequest"])
        self.assertFalse(authority["callerAuthorityInRequest"])
        self.assertFalse(authority["callerCorrelationIdAllowed"])
        request_properties = {
            key
            for branch in self.request_schema["oneOf"]
            for key in branch["properties"]
        }
        self.assertEqual({"protocol", "operation", "aosSecret"}, request_properties)

    def test_response_statuses_and_rejection_codes_are_closed(self) -> None:
        self.assertEqual(
            {"ready", "issued", "rejected"},
            set(self.profile["responseStatuses"]),
        )
        branches = self.response_schema["oneOf"]
        self.assertTrue(all(not branch["additionalProperties"] for branch in branches))
        rejected = next(
            branch for branch in branches
            if branch["properties"]["status"]["const"] == "rejected"
        )
        self.assertEqual(set(self.profile["rejectionCodes"]), set(rejected["properties"]["code"]["enum"]))
        self.assertNotIn("message", rejected["properties"])
        self.assertFalse(self.profile["humanReadableErrorAllowed"])

    def test_issued_response_contains_only_delivery_fields(self) -> None:
        issued = next(
            branch for branch in self.response_schema["oneOf"]
            if branch["properties"]["status"]["const"] == "issued"
        )
        self.assertEqual(
            {
                "protocol",
                "status",
                "correlationId",
                "token",
                "expiresAtUnixSeconds",
                "renewAfterUnixSeconds",
            },
            set(issued["properties"]),
        )

    def test_permission_mapping_never_widens_service_authority(self) -> None:
        mapping = self.profile["permissionMapping"]
        self.assertEqual({"r": ["read"], "rw": ["actuate"]}, mapping["supportedModes"])
        self.assertEqual(["w"], mapping["unsupportedModes"])
        self.assertEqual(
            "REJECT_WHOLE_ISSUE_NO_PARTIAL_TRIMMING",
            mapping["completeSetPolicy"],
        )
        jwt = self.profile["jwtProfile"]
        self.assertEqual(["read", "actuate"], jwt["serviceActionsAllowed"])
        self.assertEqual(["provide", "create"], jwt["serviceActionsForbidden"])
        self.assertFalse(jwt["wildcardsAllowed"])

    def test_jwt_timing_and_reconnect_are_frozen(self) -> None:
        timing = self.profile["timing"]
        self.assertEqual(300, timing["ttlSeconds"])
        self.assertEqual(180, timing["renewAfterSecondsFromIssue"])
        self.assertEqual(120, timing["renewalReserveSeconds"])
        self.assertTrue(timing["renewalRequiresFreshIamLookup"])
        self.assertTrue(timing["renewalRequiresKuksaReconnect"])
        self.assertFalse(timing["instantRevocationClaimed"])
        self.assertFalse(timing["cloudRequiredForRenewal"])

    def test_signer_and_verifier_lifecycle_is_fail_closed(self) -> None:
        signer = self.profile["signerVerifier"]
        self.assertEqual("kuksa-jwt", signer["certificateModule"])
        self.assertEqual("RSA", signer["keyAlgorithm"])
        self.assertFalse(signer["privateKeyExportAllowed"])
        self.assertFalse(signer["fileKeyFallbackAllowed"])
        self.assertEqual(
            "aos-kuksa-verifier-prepare.service",
            signer["preparationService"],
        )
        self.assertEqual(
            "/run/aos-kuksa-verifier/kuksa-jwt-public.pem",
            signer["publicVerifierPath"],
        )
        self.assertEqual("0444", signer["publicVerifierMode"])
        self.assertTrue(signer["preparationRequiresProtectedSignVerifySelfTest"])
        self.assertEqual(
            "DO_NOT_START_FAIL_CLOSED",
            signer["kuksaMissingVerifierPolicy"],
        )
        self.assertFalse(signer["liveRotationInFirstDemo"])
        self.assertEqual("REJECT", signer["crossUnitTokenAcceptance"])

    def test_trustworthy_time_is_boot_scoped_and_offline_capable(self) -> None:
        clock = self.profile["trustworthyTime"]
        self.assertEqual(
            "SYSTEMD_TIMESYNCD_NTP_SYNCHRONIZED_ONCE_PER_BOOT",
            clock["initialAuthority"],
        )
        self.assertEqual(10, clock["stableWindowSeconds"])
        self.assertEqual("CLOCK_REALTIME_UTC", clock["wallClockSource"])
        self.assertEqual("CLOCK_BOOTTIME", clock["scheduleClockSource"])
        self.assertEqual(5, clock["maximumWallToBootClockDeviationSeconds"])
        self.assertTrue(clock["anchorPersistsAcrossProcessRestart"])
        self.assertFalse(clock["anchorPersistsAcrossVmReboot"])
        self.assertFalse(clock["externalConnectivityLossAfterTrustRevokesTrust"])
        self.assertEqual(
            "TIME_UNTRUSTED_STOP_KUKSA_DELETE_TOKENS_AND_BLOCK_ISSUANCE",
            clock["clockDiscontinuityPolicy"],
        )
        self.assertFalse(clock["unrelatedAosCoreServicesBlocked"])
        self.assertFalse(clock["cloudApiRequired"])

    def test_operational_bounds_and_retry_classes_are_closed(self) -> None:
        bounds = self.profile["operationalBounds"]
        self.assertEqual(16384, bounds["maxRequestFrameBytes"])
        self.assertEqual(32768, bounds["maxResponseFrameBytes"])
        self.assertEqual(16384, bounds["maxJwtBytes"])
        self.assertEqual(64, bounds["maxPermissionEntries"])
        self.assertEqual(512, bounds["maxVssPathBytes"])
        self.assertEqual(4, bounds["maxConcurrentRequests"])
        self.assertEqual(8, bounds["socketBacklog"])
        self.assertEqual({"requestsPerMinute": 12, "burst": 4}, bounds["perPeerRate"])
        self.assertEqual({"requestsPerMinute": 30, "burst": 10}, bounds["globalRate"])
        self.assertEqual(
            {"requestRead": 2, "iamOperation": 3, "signOperation": 3, "wholeRequest": 8},
            bounds["timeoutsSeconds"],
        )

        retry = self.profile["retry"]
        self.assertEqual([1, 2, 4, 8, 16, 30], retry["backoffSeconds"])
        self.assertEqual(30, retry["maximumBackoffSeconds"])
        self.assertEqual(20, retry["jitterPercent"])
        self.assertTrue(retry["hardStopAtJwtExpiry"])
        self.assertEqual(
            {"IAM_UNAVAILABLE", "SIGNER_UNAVAILABLE", "TIME_UNTRUSTED", "BUSY"},
            set(retry["retryableCodes"]),
        )
        self.assertEqual(
            {"INVALID_REQUEST", "DENIED", "POLICY_UNSUPPORTED", "INTERNAL_ERROR"},
            set(retry["nonRetryableCodes"]),
        )

    def test_process_envelope_and_diagnostics_are_fail_closed(self) -> None:
        process = self.profile["processEnvelope"]
        self.assertEqual(67108864, process["memoryMaxBytes"])
        self.assertEqual(10, process["cpuQuotaPercent"])
        self.assertEqual(32, process["tasksMax"])
        self.assertEqual(128, process["limitNoFile"])
        self.assertEqual(["AF_UNIX"], process["restrictAddressFamilies"])
        self.assertFalse(process["tcpIpAllowed"])
        self.assertTrue(process["noNewPrivileges"])

        diagnostics = self.profile["diagnostics"]
        self.assertEqual(
            {"eventCode", "correlationId", "outcome", "retryable"},
            set(diagnostics["allowedFields"]),
        )
        self.assertIn("AOS_SECRET", diagnostics["forbiddenContent"])
        self.assertIn("JWT", diagnostics["forbiddenContent"])
        self.assertFalse(diagnostics["freeTextProtocolErrorAllowed"])


if __name__ == "__main__":
    unittest.main()
