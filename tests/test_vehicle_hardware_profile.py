# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_ROOT = ROOT / "contracts" / "vehicle-hardware-profile"
PROFILE = CONTRACT_ROOT / "vehicle-hardware-capability-profile.v1.json"
SCHEMA = CONTRACT_ROOT / "vehicle-hardware-capability-profile.schema.json"
ACCEPTED_PROFILE_SHA256 = (
    "ac0ba26464219482dcb41e56ebbc1538489e13bd6c84725dbc124e59514cb7e5"
)


class VehicleHardwareCapabilityProfileTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profile_bytes = PROFILE.read_bytes()
        cls.profile = json.loads(cls.profile_bytes)
        cls.schema = json.loads(SCHEMA.read_text(encoding="utf-8"))

    def test_accepted_identity_and_digest_are_stable(self) -> None:
        self.assertEqual(1, self.profile["schemaVersion"])
        self.assertEqual("D4-002", self.profile["decision"])
        self.assertEqual("carla-lincoln-mkz-chaos", self.profile["profileId"])
        self.assertEqual("1.0.0", self.profile["profileVersion"])
        self.assertEqual(
            ACCEPTED_PROFILE_SHA256,
            hashlib.sha256(self.profile_bytes).hexdigest(),
        )

    def test_schema_and_manifest_version_agree(self) -> None:
        self.assertEqual({"const": 1}, self.schema["properties"]["schemaVersion"])
        self.assertEqual(
            "./vehicle-hardware-capability-profile.schema.json",
            self.profile["$schema"],
        )

    def test_every_capability_has_one_unique_accounting_record(self) -> None:
        capabilities = self.profile["capabilities"]
        identifiers = [item["id"] for item in capabilities]
        self.assertEqual(len(identifiers), len(set(identifiers)))
        self.assertGreater(len(identifiers), 0)

        for item in capabilities:
            with self.subTest(capability=item["id"]):
                self.assertIn("disposition", item["gateway"])
                self.assertIn("implementationState", item["gateway"])
                self.assertTrue(item["availability"])

    def test_truth_and_installation_boundaries_fail_closed(self) -> None:
        for item in self.profile["capabilities"]:
            with self.subTest(capability=item["id"]):
                installation = item["installation"]
                provenance = item["provenance"]
                disposition = item["gateway"]["disposition"]

                if installation == "NOT_INSTALLED":
                    self.assertEqual("NOT_INSTALLED", disposition)
                if installation == "NATIVE_UNAVAILABLE":
                    self.assertEqual("REVIEWED_UNSUPPORTED", disposition)
                if provenance == "QUALIFICATION_ONLY":
                    self.assertEqual("EXCLUDED_QUALIFICATION", disposition)
                if provenance == "DEMO_VISUALIZATION":
                    self.assertEqual("EXCLUDED_DEMO", disposition)

    def test_every_actuator_names_applied_state_evidence(self) -> None:
        actuators = [
            item for item in self.profile["capabilities"] if item["kind"] == "ACTUATOR"
        ]
        self.assertGreater(len(actuators), 0)
        capability_ids = {item["id"] for item in self.profile["capabilities"]}
        for actuator in actuators:
            with self.subTest(actuator=actuator["id"]):
                applied_state = actuator["gateway"].get("appliedStateCapability")
                self.assertIn(applied_state, capability_ids)

    def test_control_modes_are_not_actuators(self) -> None:
        self.assertEqual(
            {"SCENARIO", "MANUAL", "AUTOPILOT", "SAFE_STOP"},
            set(self.profile["excludedControlModes"]),
        )
        actuator_ids = {
            item["id"]
            for item in self.profile["capabilities"]
            if item["kind"] == "ACTUATOR"
        }
        self.assertFalse(
            actuator_ids
            & {"actuator.scenario", "actuator.manual", "actuator.autopilot", "actuator.safe_stop"}
        )


if __name__ == "__main__":
    unittest.main()
