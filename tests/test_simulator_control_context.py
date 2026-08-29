# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import json
import math
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_ROOT = ROOT / "contracts" / "simulator-control-context"
CONTRACT = CONTRACT_ROOT / "simulator-control-context.v1.json"
SCHEMA = CONTRACT_ROOT / "simulator-control-context.schema.json"
HANDOFF_FIXTURE = (
    CONTRACT_ROOT / "fixtures" / "controller-gateway-handoff-record.valid.json"
)


class SimulatorControlContextContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        cls.schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        cls.handoff_fixture = json.loads(HANDOFF_FIXTURE.read_text(encoding="utf-8"))

    def test_identity_and_state_sets_are_frozen(self) -> None:
        self.assertEqual("D4-004", self.contract["decision"])
        self.assertEqual("1.1.0", self.contract["contractVersion"])
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

    def test_controller_gateway_transport_is_local_atomic_and_bounded(self) -> None:
        handoff = self.contract["controllerGatewayHandoff"]
        transport = handoff["transport"]
        self.assertEqual("AF_UNIX", transport["addressFamily"])
        self.assertEqual("SOCK_DGRAM", transport["socketType"])
        self.assertEqual("NON_BLOCKING", transport["controllerSend"])
        self.assertEqual(4096, transport["maximumDatagramBytes"])
        self.assertTrue(transport["linuxPeerCredentialsRequired"])
        self.assertTrue(transport["rejectTruncatedOrOversizeBeforeJson"])
        self.assertFalse(transport["streamProtocol"])
        self.assertFalse(transport["reconnectProtocol"])
        self.assertFalse(transport["historyOrReplay"])

        join = handoff["join"]
        self.assertEqual(["frameId", "simulationTime"], join["matchKeys"])
        self.assertEqual(4, join["maximumUnmatchedPhysicalRecords"])
        self.assertEqual(4, join["maximumUnmatchedControlRecords"])
        self.assertEqual(250, join["maximumResidenceMs"])
        self.assertEqual(
            "OMIT_ALL_SIX_CONTROL_RESET_FACTS_FOR_FRAME",
            join["missingFactBehavior"],
        )
        self.assertFalse(join["lastKnownReuse"])
        self.assertFalse(join["safeStopFreshnessPolicy"])

    def test_handoff_fixture_has_the_exact_closed_record_shape(self) -> None:
        record_contract = self.contract["controllerGatewayHandoff"]["record"]
        self.assertEqual(
            set(record_contract["requiredFields"]), set(self.handoff_fixture)
        )
        self.assertFalse(record_contract["additionalProperties"])
        self.assertEqual(1, self.handoff_fixture["schemaVersion"])
        self.assertTrue(self.handoff_fixture["runId"])
        self.assertGreaterEqual(self.handoff_fixture["egoActorId"], 0)
        self.assertGreaterEqual(self.handoff_fixture["frameId"], 0)
        self.assertTrue(math.isfinite(self.handoff_fixture["simulationTime"]))
        self.assertGreaterEqual(self.handoff_fixture["simulationTime"], 0)
        self.assertIn(
            self.handoff_fixture["activeMode"], self.contract["states"]["driveModes"]
        )
        transition_values = next(
            item["allowedValues"]
            for item in self.contract["projection"]
            if item["path"]
            == "Vehicle.CarlaSimulation.Control.TransitionState"
        )
        self.assertIn(self.handoff_fixture["transitionState"], transition_values)

    def test_reset_emission_never_fabricates_a_carla_frame(self) -> None:
        reset = self.contract["controllerGatewayHandoff"]["resetEmission"]
        self.assertEqual("EMIT_NOTHING", reset["blockingWithoutFrame"])
        self.assertEqual(
            "NO_RESET_SUCCESS_EVIDENCE", reset["failedResetWithoutFrame"]
        )
        self.assertIn(
            "DISCONTINUITY_TRUE", reset["firstPostResetCompletedFrame"]
        )
        self.assertEqual("DISCONTINUITY_FALSE", reset["nextCompletedFrame"])
        self.assertTrue(reset["uiOperationStateSeparate"])

    def test_schema_and_contract_versions_agree(self) -> None:
        self.assertEqual({"const": 1}, self.schema["properties"]["schemaVersion"])
        self.assertEqual(
            "./simulator-control-context.schema.json",
            self.contract["$schema"],
        )


if __name__ == "__main__":
    unittest.main()
