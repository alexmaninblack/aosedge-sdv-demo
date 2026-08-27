# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_ROOT = ROOT / "contracts" / "exclusive-live-source-assignment"
CONTRACT = CONTRACT_ROOT / "exclusive-live-source-assignment.v1.json"
SCHEMA = CONTRACT_ROOT / "exclusive-live-source-assignment.schema.json"


class ExclusiveLiveSourceAssignmentContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        cls.schema = json.loads(SCHEMA.read_text(encoding="utf-8"))

    def test_identity_and_two_vehicle_audience_model_are_frozen(self) -> None:
        self.assertEqual("D4-005", self.contract["decision"])
        self.assertEqual("1.0.0", self.contract["contractVersion"])
        vehicles = self.contract["audienceModel"]["vehicles"]
        self.assertEqual(
            {"VALIDATION_VEHICLE", "PRODUCTION_VEHICLE"},
            {item["vehicleRole"] for item in vehicles},
        )
        self.assertEqual(
            {"VALIDATION_UNIT", "PRODUCTION_UNIT"},
            {item["unitRole"] for item in vehicles},
        )
        self.assertEqual(1, self.contract["audienceModel"]["currentVehicleCount"])

    def test_primary_ui_hides_demo_plumbing_and_vehicle_path_has_no_role(self) -> None:
        prohibited = set(self.contract["audienceModel"]["primaryUiProhibitedTerms"])
        self.assertIn("ATTACH CARLA", prohibited)
        self.assertIn("SOURCE BINDING", prohibited)
        self.assertFalse(self.contract["audienceModel"]["roleInVehicleDataPath"])

    def test_audience_sources_use_test_vehicle_label(self) -> None:
        audience_sources = [
            ROOT / "docs" / "architecture" / "high-level-architecture.md",
            ROOT / "docs" / "demo" / "mockups" / "aosedge-demo-interaction-specification.md",
            ROOT / "docs" / "demo" / "mockups" / "aosedge-demo-linear-flow-mockup.html",
        ]
        for source in audience_sources:
            rendered_source = source.read_text(encoding="utf-8")
            self.assertIn("Test Vehicle", rendered_source, source)
            self.assertNotIn("Validation Vehicle", rendered_source, source)

    def test_assignment_is_exclusive_while_both_units_may_be_cloud_online(self) -> None:
        assignment = self.contract["technicalAssignment"]
        self.assertTrue(assignment["bothUnitsMayRemainCloudOnline"])
        self.assertTrue(assignment["oneActiveBinding"])
        self.assertEqual("D4-006", assignment["authenticationDecision"])

    def test_detach_reset_and_exclusive_evidence_are_mandatory(self) -> None:
        proof = set(self.contract["evidence"]["exclusiveProof"])
        self.assertIn("confirmedDetach", proof)
        self.assertIn("noOverlappingFrameRanges", proof)
        self.assertIn("newResetGenerationBeforeNextAssignment", proof)
        self.assertTrue(self.contract["failurePolicy"]["safeStop"])
        self.assertTrue(self.contract["failurePolicy"]["blockNextAssignment"])

    def test_replay_and_second_vehicle_are_deferred(self) -> None:
        self.assertEqual(
            {"TELEMETRY_REPLAY", "SECOND_SIMULATED_VEHICLE"},
            set(self.contract["deferred"]),
        )

    def test_schema_and_contract_versions_agree(self) -> None:
        self.assertEqual({"const": 1}, self.schema["properties"]["schemaVersion"])
        self.assertEqual(
            "./exclusive-live-source-assignment.schema.json",
            self.contract["$schema"],
        )


if __name__ == "__main__":
    unittest.main()
