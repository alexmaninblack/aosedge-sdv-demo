# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_ROOT = ROOT / "contracts" / "qm-advisory-profile"
PROFILE = CONTRACT_ROOT / "qm-advisory-profile.v1.json"
REQUEST_SCHEMA = CONTRACT_ROOT / "qm-advisory-request.schema.json"
STATUS_SCHEMA = CONTRACT_ROOT / "qm-advisory-status.schema.json"


class QmAdvisoryProfileTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profile = json.loads(PROFILE.read_text(encoding="utf-8"))
        cls.request_schema = json.loads(REQUEST_SCHEMA.read_text(encoding="utf-8"))
        cls.status_schema = json.loads(STATUS_SCHEMA.read_text(encoding="utf-8"))
        cls.endpoints = {item["id"]: item for item in cls.profile["endpoints"]}

    def test_contract_identity_and_exact_endpoints_are_frozen(self) -> None:
        self.assertEqual("D4-008", self.profile["decision"])
        self.assertEqual("1.0.2", self.profile["contractVersion"])
        self.assertEqual("1.0.1", self.profile["inputs"]["vdpCompatibilityContractVersion"])
        self.assertEqual(
            {"BRAKE_HEALTH_ADVISORY", "TIRE_HEALTH_ADVISORY"},
            set(self.endpoints),
        )
        request_paths = {item["requestPath"] for item in self.endpoints.values()}
        status_paths = {item["statusPath"] for item in self.endpoints.values()}
        self.assertEqual(2, len(request_paths))
        self.assertEqual(2, len(status_paths))
        self.assertTrue(request_paths.isdisjoint(status_paths))

    def test_authorization_provenance_uses_current_release_decision(self) -> None:
        self.assertIn(
            "KUKSA_ENFORCES_D4_027_PATH_PERMISSION",
            self.profile["dataFlow"],
        )
        self.assertEqual(
            "D4-027",
            self.profile["deferred"]["credentialIssuanceAndRefresh"],
        )

    def test_services_cannot_share_or_cross_write_targets(self) -> None:
        brake = self.endpoints["BRAKE_HEALTH_ADVISORY"]
        tire = self.endpoints["TIRE_HEALTH_ADVISORY"]
        self.assertEqual("BRAKE_HEALTH", brake["ownerService"])
        self.assertEqual("TIRE_HEALTH", tire["ownerService"])
        self.assertFalse(self.profile["authority"]["serviceCrossEndpointWriteAllowed"])
        self.assertFalse(self.profile["authority"]["arbitraryVssWriteAllowed"])
        self.assertFalse(self.profile["authority"]["vehicleMotionAuthorityAllowed"])

    def test_request_is_one_bounded_schema_typed_value(self) -> None:
        encoding = self.profile["encoding"]
        self.assertEqual("string", encoding["vssDatatype"])
        self.assertEqual("RFC8785", encoding["canonicalization"])
        self.assertLessEqual(encoding["maxRequestBytes"], 2048)
        self.assertFalse(encoding["arbitraryDisplayTextAllowed"])
        self.assertFalse(self.request_schema["additionalProperties"])

    def test_gateway_status_is_only_application_authority(self) -> None:
        authority = self.profile["authority"]
        self.assertTrue(authority["gatewayFinalAuthority"])
        self.assertIn("GatewayStatus", authority["authoritativeApplicationEvidence"])
        self.assertFalse(authority["engineeringDashboardWriteAllowed"])
        self.assertFalse(self.status_schema["additionalProperties"])

    def test_time_replay_and_clear_policy_is_bounded(self) -> None:
        timing = self.profile["temporalPolicy"]
        self.assertEqual(2000, timing["maxGatewayAcceptanceAgeMs"])
        self.assertEqual(30000, timing["maxLeaseMs"])
        self.assertGreaterEqual(
            timing["minimumReplayRetentionMs"], timing["maxLeaseMs"]
        )
        self.assertTrue(timing["explicitClearRequired"])
        self.assertTrue(timing["automaticExpiryRequired"])
        self.assertEqual(
            "REJECT_SEQUENCE_ROLLBACK",
            self.profile["replayPolicy"]["sequenceRollbackBehavior"],
        )

    def test_external_offline_does_not_break_local_advisory(self) -> None:
        offline = self.profile["offlinePolicy"]
        self.assertFalse(offline["externalConnectivityRequiredForLocalAdvisory"])
        self.assertFalse(offline["aosCloudRequiredForLocalAdvisory"])
        self.assertFalse(offline["functionalBackendRequiredForLocalAdvisory"])
        self.assertEqual(
            {"KUKSA", "VDP", "VISS", "GATEWAY"},
            set(offline["internalChainRequired"]),
        )


if __name__ == "__main__":
    unittest.main()
