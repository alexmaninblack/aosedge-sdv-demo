# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_ROOT = ROOT / "contracts" / "simulator-control-context"
CONTRACT = CONTRACT_ROOT / "simulator-control-context.v1.json"
SCHEMA = CONTRACT_ROOT / "simulator-control-context.schema.json"


class SimulatorControlContextContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        cls.schema = json.loads(SCHEMA.read_text(encoding="utf-8"))

    def test_identity_and_state_sets_are_frozen(self) -> None:
        self.assertEqual("D4-004", self.contract["decision"])
        self.assertEqual("1.0.0", self.contract["contractVersion"])
        self.assertEqual(
            {"SAFE_STOP", "SCENARIO", "MANUAL", "AUTOPILOT"},
            set(self.contract["states"]["driveModes"]),
        )
        self.assertEqual(
            {"FREE_DRIVE", "BRAKE_EVENT"},
            set(self.contract["states"]["worldContexts"]),
        )

    def test_transition_ids_and_projection_paths_are_unique(self) -> None:
        transition_ids = [item["id"] for item in self.contract["transitions"]]
        paths = [item["path"] for item in self.contract["projection"]]
        self.assertEqual(len(transition_ids), len(set(transition_ids)))
        self.assertEqual(len(paths), len(set(paths)))
        self.assertTrue(all(path.startswith("Vehicle.CarlaSimulation.") for path in paths))

    def test_autopilot_never_inherits_brake_event_obstacle(self) -> None:
        rows = {
            item["id"]: item for item in self.contract["transitions"]
        }
        transition = rows["brake-context-to-autopilot"]
        self.assertEqual("REMOVE", transition["obstacle"])
        self.assertEqual("CANONICAL_FREE_DRIVE", transition["reset"])
        self.assertEqual("FREE_DRIVE", transition["targetContext"])

    def test_reset_and_reverse_boundaries_are_fail_closed(self) -> None:
        self.assertTrue(self.contract["resetSemantics"]["sameActor"])
        self.assertTrue(self.contract["resetSemantics"]["safeStopFirst"])
        self.assertFalse(
            self.contract["reversePolicy"]["firstDemoControlUiAuthorized"]
        )
        self.assertEqual(
            {"SCENARIO_RESTART", "AUTOPILOT_CONTEXT_RESET"},
            set(self.contract["reversePolicy"]["recovery"]),
        )

    def test_schema_and_contract_versions_agree(self) -> None:
        self.assertEqual({"const": 1}, self.schema["properties"]["schemaVersion"])
        self.assertEqual(
            "./simulator-control-context.schema.json",
            self.contract["$schema"],
        )


if __name__ == "__main__":
    unittest.main()
