# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_ROOT = ROOT / "contracts" / "brake-telemetry-window"
PROFILE = CONTRACT_ROOT / "brake-telemetry-window-profile.v1.json"
PROFILE_SCHEMA = CONTRACT_ROOT / "brake-telemetry-window-profile.schema.json"
CHUNK_SCHEMA = CONTRACT_ROOT / "brake-telemetry-window-chunk.schema.json"
COMPLETION_SCHEMA = CONTRACT_ROOT / "brake-telemetry-window-completion.schema.json"
CHUNK_FIXTURE = CONTRACT_ROOT / "fixtures" / "window-chunk.valid.json"
COMPLETION_FIXTURE = CONTRACT_ROOT / "fixtures" / "window-completion.valid.json"


def canonical_json_bytes(value: object) -> bytes:
    """RFC 8785-compatible encoding for the bounded golden-fixture values."""
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def content_sha256(message: dict) -> str:
    return hashlib.sha256(canonical_json_bytes(message["content"])).hexdigest()


class BrakeTelemetryWindowContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profile = json.loads(PROFILE.read_text(encoding="utf-8"))
        cls.profile_schema = json.loads(PROFILE_SCHEMA.read_text(encoding="utf-8"))
        cls.chunk_schema = json.loads(CHUNK_SCHEMA.read_text(encoding="utf-8"))
        cls.completion_schema = json.loads(COMPLETION_SCHEMA.read_text(encoding="utf-8"))
        cls.chunk = json.loads(CHUNK_FIXTURE.read_text(encoding="utf-8"))
        cls.completion = json.loads(COMPLETION_FIXTURE.read_text(encoding="utf-8"))

    def test_identity_and_accepted_scope_are_frozen(self) -> None:
        self.assertEqual("D4-016", self.profile["decision"])
        self.assertEqual(["D4-016.1", "D4-016.2"], self.profile["acceptedSubdecisions"])
        self.assertEqual("1.0.0", self.profile["contractVersion"])
        self.assertEqual("HARD_BRAKING_EPISODE_V1", self.profile["eventType"])

    def test_six_signal_acquisition_subset_and_trigger_are_exact(self) -> None:
        inputs = self.profile["input"]
        self.assertEqual(30, inputs["sourceCadenceHz"])
        self.assertEqual(10, inputs["retainedCadenceHz"])
        self.assertEqual(6, len(inputs["paths"]))
        self.assertEqual(
            ["Vehicle.Chassis.Axle.Row1.SteeringAngle"],
            inputs["excludedAvailableVdpV1Paths"],
        )
        self.assertEqual(
            {
                "Vehicle.Speed",
                "Vehicle.Acceleration.Longitudinal",
                "Vehicle.Chassis.Brake.PedalPosition",
            },
            set(inputs["mandatoryTriggerPaths"]),
        )
        trigger = self.profile["trigger"]
        self.assertEqual(10, trigger["minimumSpeedKph"])
        self.assertEqual(50, trigger["minimumBrakePedalPercent"])
        self.assertEqual(200, trigger["activationHoldMs"])
        self.assertFalse(trigger["longitudinalAccelerationIsTrigger"])

    def test_window_message_and_spool_bounds_are_frozen(self) -> None:
        window = self.profile["window"]
        self.assertEqual((3, 10, 2), (window["preSeconds"], window["maximumActiveSeconds"], window["postSeconds"]))
        self.assertEqual(150, window["maximumSamples"])
        messages = self.profile["messages"]
        self.assertEqual("RFC8785", messages["canonicalization"])
        self.assertEqual(10, messages["maximumSamplesPerChunk"])
        self.assertEqual(65536, messages["maximumCanonicalMessageBytes"])
        self.assertEqual("NONE", messages["embeddedCompression"])
        spool = self.profile["spool"]
        self.assertEqual(8, spool["maximumUnacknowledgedWindows"])
        self.assertEqual(4 * 1024 * 1024, spool["maximumEncodedBytes"])
        self.assertFalse(spool["sendBeforeDurable"])
        self.assertFalse(spool["deleteBeforeAllDurableAcks"])
        self.assertFalse(spool["databaseRuntimeRequired"])

    def test_schemas_reject_undeclared_message_fields(self) -> None:
        self.assertFalse(self.chunk_schema["additionalProperties"])
        self.assertFalse(self.completion_schema["additionalProperties"])
        chunk_content = self.chunk_schema["properties"]["content"]
        self.assertFalse(chunk_content["additionalProperties"])
        self.assertEqual(10, chunk_content["properties"]["samples"]["maxItems"])
        self.assertFalse(self.chunk_schema["$defs"]["sample"]["additionalProperties"])
        completion_content = self.completion_schema["properties"]["content"]
        self.assertFalse(completion_content["additionalProperties"])

    def test_golden_chunk_is_internally_consistent(self) -> None:
        content = self.chunk["content"]
        self.assertEqual(content["sampleCount"], len(content["samples"]))
        self.assertEqual(
            list(range(content["firstSampleIndex"], content["firstSampleIndex"] + content["sampleCount"])),
            [sample["sampleIndex"] for sample in content["samples"]],
        )
        self.assertTrue(all(sample["quality"] == "VALID_COMPLETE_FRAME" for sample in content["samples"]))
        self.assertEqual(self.chunk["contentSha256"], content_sha256(self.chunk))
        self.assertLessEqual(len(canonical_json_bytes(self.chunk)), 65536)

    def test_golden_completion_commits_to_ordered_chunks(self) -> None:
        content = self.completion["content"]
        self.assertEqual(self.chunk["eventId"], self.completion["eventId"])
        self.assertEqual("ABORTED_SERVICE_STOP", content["terminalState"])
        self.assertEqual("SERVICE_STOP", content["reasonCode"])
        self.assertEqual(
            {"PRE": 1, "ACTIVE": 1, "POST": 0},
            content["phaseSampleCounts"],
        )
        self.assertEqual([self.chunk["contentSha256"]], content["chunkContentSha256"])
        expected_window_hash = hashlib.sha256(bytes.fromhex(self.chunk["contentSha256"])).hexdigest()
        self.assertEqual(expected_window_hash, content["windowSha256"])
        self.assertEqual(content["totalChunks"], len(content["chunkContentSha256"]))
        self.assertEqual(content["totalSamples"], sum(content["phaseSampleCounts"].values()))
        self.assertEqual(self.completion["contentSha256"], content_sha256(self.completion))


if __name__ == "__main__":
    unittest.main()
