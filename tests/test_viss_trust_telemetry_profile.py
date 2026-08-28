# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_ROOT = ROOT / "contracts" / "viss-trust-telemetry-profile"
CONTRACT = CONTRACT_ROOT / "viss-trust-telemetry-profile.v1.json"
SCHEMA = CONTRACT_ROOT / "viss-trust-telemetry-profile.schema.json"
HARDWARE_PROFILE = (
    ROOT
    / "contracts"
    / "vehicle-hardware-profile"
    / "vehicle-hardware-capability-profile.v1.json"
)
CONTROL_CONTRACT = (
    ROOT
    / "contracts"
    / "simulator-control-context"
    / "simulator-control-context.v1.json"
)
ACCEPTED_CONTRACT_SHA256 = (
    "4a1a2bd804c3a49f707b5e640632bd8a0357901f59e4615c340622b043d4c12c"
)


class VissTrustTelemetryProfileTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        cls.schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        cls.hardware = json.loads(HARDWARE_PROFILE.read_text(encoding="utf-8"))
        cls.control = json.loads(CONTROL_CONTRACT.read_text(encoding="utf-8"))

    def test_identity_standards_and_schema_are_frozen(self) -> None:
        self.assertEqual("D4-006", self.contract["decision"])
        self.assertEqual("1.1.0", self.contract["contractVersion"])
        self.assertEqual(
            {"viss": "3.1", "vss": "6.0", "projectOverlay": "Vehicle.CarlaSimulation.*"},
            self.contract["standards"],
        )
        self.assertEqual({"const": 1}, self.schema["properties"]["schemaVersion"])
        self.assertEqual(
            "./viss-trust-telemetry-profile.schema.json",
            self.contract["$schema"],
        )
        self.assertEqual(
            ACCEPTED_CONTRACT_SHA256,
            hashlib.sha256(CONTRACT.read_bytes()).hexdigest(),
        )

    def test_private_transport_and_per_unit_credential_lifecycle_fail_closed(self) -> None:
        transport = self.contract["transport"]
        self.assertTrue(transport["mutualTls"])
        self.assertFalse(transport["unencryptedWebSocket"])
        self.assertEqual("TLS1.2", transport["minimumTlsVersion"])

        lifecycle = self.contract["credentialLifecycle"]
        self.assertTrue(lifecycle["unitUnique"])
        self.assertTrue(lifecycle["purposeBound"])
        self.assertEqual(
            {"SELECTED_PLATFORM_UNIT", "PLATFORM_UPDATE_RUNTIME"},
            set(lifecycle["separateForRoles"]),
        )
        self.assertTrue(lifecycle["retiredAtR0"])
        self.assertEqual("systemd LoadCredential", lifecycle["delivered"])
        self.assertEqual(
            {"FACTORY_IMAGE", "FOTA_COMPONENT", "GIT", "LOGS", "DASHBOARD"},
            set(lifecycle["excludedFrom"]),
        )

    def test_peer_roles_preserve_one_selected_unit_and_read_only_dashboard(self) -> None:
        roles = {item["role"]: item for item in self.contract["peerRoles"]}
        self.assertEqual(
            {
                "SELECTED_PLATFORM_UNIT",
                "PLATFORM_UPDATE_RUNTIME",
                "ENGINEERING_DASHBOARD",
                "QUALIFICATION_CLIENT",
            },
            set(roles),
        )
        self.assertEqual(
            {"GET", "SUBSCRIBE", "UNSUBSCRIBE"},
            set(roles["SELECTED_PLATFORM_UNIT"]["allowedOperations"]),
        )
        self.assertEqual("DENY_UNTIL_D4_008", roles["SELECTED_PLATFORM_UNIT"]["setPolicy"])
        self.assertEqual("ALWAYS_DENY", roles["PLATFORM_UPDATE_RUNTIME"]["setPolicy"])
        self.assertEqual("ALWAYS_DENY", roles["ENGINEERING_DASHBOARD"]["setPolicy"])
        self.assertEqual("ALWAYS_DENY", roles["QUALIFICATION_CLIENT"]["setPolicy"])

        gate = self.contract["selectedUnitGate"]
        self.assertEqual(
            {"SELECTED_PLATFORM_UNIT", "PLATFORM_UPDATE_RUNTIME"},
            set(gate["selectedBoundRoles"]),
        )
        self.assertEqual(1, gate["maximumConnectionsPerSelectedRole"])
        self.assertTrue(gate["distinctCredentialPerSelectedRole"])
        self.assertEqual(
            {"UnitId", "NodeId", "clientCertificateFingerprint", "assignmentGeneration"},
            set(gate["selectedIdentity"]),
        )
        self.assertIn("NON_SELECTED_UNIT", gate["reject"])
        self.assertIn("ADDITIONAL_UNIT_SESSION", gate["reject"])

    def test_platform_update_runtime_has_only_safe_stop_read_paths(self) -> None:
        runtime_paths = {
            item["path"]
            for item in self.contract["paths"]
            if "PLATFORM_UPDATE_RUNTIME" in item["access"]
        }
        self.assertEqual(
            {
                "Vehicle.CarlaSimulation.FrameId",
                "Vehicle.CarlaSimulation.Control.ActiveMode",
                "Vehicle.CarlaSimulation.Control.TransitionState",
                "Vehicle.CarlaSimulation.Control.Generation",
                "Vehicle.CarlaSimulation.Reset.Generation",
                "Vehicle.CarlaSimulation.Reset.InProgress",
                "Vehicle.CarlaSimulation.Reset.Discontinuity",
                "Vehicle.Speed",
                "Vehicle.Chassis.Accelerator.PedalPosition",
                "Vehicle.Chassis.Brake.PedalPosition",
            },
            runtime_paths,
        )
        roles = {item["role"]: item for item in self.contract["peerRoles"]}
        self.assertEqual(
            {"GET", "SUBSCRIBE", "UNSUBSCRIBE"},
            set(roles["PLATFORM_UPDATE_RUNTIME"]["allowedOperations"]),
        )

    def test_timing_queue_and_recovery_semantics_are_bounded(self) -> None:
        self.assertEqual(
            {
                "subscriptionPeriodMs": 50,
                "freshnessTimeoutMs": 250,
                "reconnectInitialMs": 500,
                "reconnectMaximumMs": 10000,
            },
            self.contract["timing"],
        )
        self.assertEqual(8, self.contract["limits"]["maximumPendingMessagesPerClient"])
        self.assertEqual("DROP_NEW_EVENT_AND_INCREMENT_COUNTER", self.contract["operations"]["eventOverflow"])
        self.assertEqual("DENY_ALL_WITHOUT_SIDE_EFFECT", self.contract["operations"]["setBeforeD4008"])
        self.assertIn("NotAvailable", self.contract["dataSemantics"]["disconnect"])
        self.assertIn("NotAvailable", self.contract["dataSemantics"]["stale"])
        self.assertIn("monotonic frame", self.contract["dataSemantics"]["recovery"])

    def test_paths_are_unique_and_include_the_complete_d4_004_projection(self) -> None:
        profile_paths = [item["path"] for item in self.contract["paths"]]
        self.assertEqual(len(profile_paths), len(set(profile_paths)))
        control_paths = {item["path"] for item in self.control["projection"]}
        self.assertTrue(control_paths <= set(profile_paths))

    def test_known_vss_6_unit_boundaries_are_canonical(self) -> None:
        paths = {item["path"]: item for item in self.contract["paths"]}
        for axis in ("Longitudinal", "Lateral", "Vertical"):
            self.assertEqual("m/s^2", paths[f"Vehicle.Acceleration.{axis}"]["unit"])
        for axle in ("Row1", "Row2"):
            for side in ("Left", "Right"):
                path = f"Vehicle.Chassis.Axle.{axle}.Wheel.{side}.AngularSpeed"
                self.assertEqual("degrees/s", paths[path]["unit"])
                self.assertEqual("PARTIAL", paths[path]["implementationState"])

    def test_every_d4_002_capability_is_mapped_or_explicitly_excluded(self) -> None:
        hardware_ids = {item["id"] for item in self.hardware["capabilities"]}
        mapped_ids = {
            capability_id
            for path in self.contract["paths"]
            for capability_id in path["capabilityIds"]
        }
        excluded_ids = {
            item["capabilityId"] for item in self.contract["excludedCapabilities"]
        }
        self.assertFalse(mapped_ids & excluded_ids)
        self.assertEqual(hardware_ids, mapped_ids | excluded_ids)
        self.assertEqual(
            len(excluded_ids),
            len(self.contract["excludedCapabilities"]),
        )


if __name__ == "__main__":
    unittest.main()
