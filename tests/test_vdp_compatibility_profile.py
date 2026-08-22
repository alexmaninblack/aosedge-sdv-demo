# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_ROOT = ROOT / "contracts" / "vdp-compatibility-profile"
CONTRACT = CONTRACT_ROOT / "vdp-compatibility-profile.v1.json"
VISS = ROOT / "contracts" / "viss-trust-telemetry-profile" / "viss-trust-telemetry-profile.v1.json"


class VdpCompatibilityProfileTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        cls.viss = json.loads(VISS.read_text(encoding="utf-8"))
        cls.versions = {
            item["id"]: item for item in cls.contract["componentVersions"]
        }
        cls.services = {
            (item["serviceId"], item["serviceVersion"]): item
            for item in cls.contract["serviceCompatibility"]
        }

    def test_identity_and_versions_are_frozen(self) -> None:
        self.assertEqual("D4-007", self.contract["decision"])
        self.assertEqual("1.0.0", self.contract["contractVersion"])
        self.assertEqual({"VDP_V1", "VDP_V2", "VDP_V3"}, set(self.versions))

    def test_component_versions_are_strict_additive_supersets(self) -> None:
        v1 = set(self.versions["VDP_V1"]["readPaths"])
        v2 = set(self.versions["VDP_V2"]["readPaths"])
        v3 = set(self.versions["VDP_V3"]["readPaths"])
        self.assertTrue(v1 < v2 < v3)
        self.assertEqual(v2 - v1, set(self.versions["VDP_V2"]["addedReadPaths"]))
        self.assertEqual(v3 - v2, set(self.versions["VDP_V3"]["addedReadPaths"]))

    def test_every_staged_path_exists_in_accepted_viss_profile(self) -> None:
        accepted = {item["path"] for item in self.viss["paths"]}
        for version in self.versions.values():
            self.assertLessEqual(set(version["readPaths"]), accepted)

    def test_service_compatibility_graph_is_explicit(self) -> None:
        self.assertEqual(
            ["VDP_V1", "VDP_V2", "VDP_V3"],
            self.services[("BRAKE_HEALTH", "1.0.0")]["compatibleVdpVersions"],
        )
        self.assertEqual(
            ["VDP_V2", "VDP_V3"],
            self.services[("BRAKE_HEALTH", "2.0.0")]["compatibleVdpVersions"],
        )
        self.assertEqual(
            ["VDP_V3"],
            self.services[("BRAKE_HEALTH", "3.0.0")]["compatibleVdpVersions"],
        )
        self.assertEqual(
            ["VDP_V3"],
            self.services[("TIRE_HEALTH", "1.0.0")]["compatibleVdpVersions"],
        )

    def test_tire_incompatible_state_points_to_platform_team(self) -> None:
        rows = {
            item["category"]: item
            for item in self.contract["readinessContract"]["dashboardGuidance"]
        }
        self.assertEqual("PLATFORM_TEAM", rows["INCOMPATIBLE_VDP"]["owner"])
        self.assertIn(
            "COMPONENT_VERSION_UNSUPPORTED",
            rows["INCOMPATIBLE_VDP"]["reasonCodes"],
        )
        self.assertNotIn(
            "TELEMETRY_DISCONNECTED",
            rows["INCOMPATIBLE_VDP"]["reasonCodes"],
        )

    def test_runtime_defense_does_not_become_cloud_admission_proxy(self) -> None:
        boundary = self.contract["admissionBoundary"]
        self.assertFalse(boundary["nativePreTransferAdmissionAvailable"])
        self.assertFalse(boundary["projectAdmissionProxyAllowed"])
        self.assertTrue(boundary["runtimeDefenseRequired"])
        self.assertIn(
            "NO_CRASH_LOOP",
            self.contract["readinessContract"]["notReadyEffects"],
        )


if __name__ == "__main__":
    unittest.main()
