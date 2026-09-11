# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""N3 schema migration invariants; offline, no runtime or Cloud operations."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts"
FAMILIES = (
    ("brake-telemetry-window", "brake-telemetry-window-chunk"),
    ("brake-telemetry-window", "brake-telemetry-window-completion"),
    ("brake-health-model", "brake-health-assessment"),
    ("brake-health-model", "brake-health-event"),
    ("brake-cloud-api", "brake-advisory-fact"),
    ("tire-health-model", "tire-health-assessment"),
    ("tire-health-model", "tire-health-event"),
    ("tire-cloud-api", "tire-advisory-fact"),
    ("tire-cloud-api", "tire-function-status"),
)


def read(path):
    return json.loads(path.read_text())


class NativeProductContractTests(unittest.TestCase):
    def test_nine_explicit_revisions_preserve_payload_and_legacy_discriminators(self):
        for family, name in FAMILIES:
            with self.subTest(name=name):
                old = read(CONTRACTS / family / (name + ".schema.json"))
                new = read(CONTRACTS / family / (name + ".v2.schema.json"))
                self.assertEqual(1, old["properties"]["schemaVersion"]["const"])
                self.assertEqual("1.0.0", old["properties"]["contractVersion"]["const"])
                self.assertEqual(2, new["properties"]["schemaVersion"]["const"])
                self.assertEqual("2.0.0", new["properties"]["contractVersion"]["const"])
                self.assertNotEqual(old["$id"], new["$id"])
                self.assertFalse(new["additionalProperties"])
                self.assertEqual(old["properties"]["content"], new["properties"]["content"])
                self.assertEqual(old.get("$defs"), new.get("$defs"))
                for field in ("serviceArtifactSha256", "modelArtifactSha256"):
                    self.assertNotIn(field, new["required"])
                    self.assertNotIn(field, new["properties"])
                for field in ("modelConfigSha256", "vdpContractVersion", "vdpContractSha256", "actualVdpContractVersion", "actualVdpContractSha256"):
                    self.assertEqual(old["properties"].get(field), new["properties"].get(field))

    def test_all_products_use_one_native_identity_and_package_release_grammar(self):
        identities = []
        for family, name in FAMILIES:
            schema = read(CONTRACTS / family / (name + ".v2.schema.json"))
            identity = schema["properties"]["serviceInstance"]
            self.assertEqual({"serviceId", "subjectId", "instanceIndex", "instanceId"}, set(identity["required"]))
            self.assertEqual(set(identity["required"]), set(identity["properties"]))
            self.assertFalse(identity["additionalProperties"])
            identities.append(identity)
            version = schema["properties"]["serviceVersion"]
            self.assertEqual(32, version["maxLength"])
            for valid in ("0.0.0", "3.0.0", "18.0.0", "123.10.9"):
                self.assertIsNotNone(re.fullmatch(version["pattern"], valid))
            for invalid in ("01.0.0", "1.0", "1.0.0-dev", "1.0.0+meta", "1.0.0\n"):
                self.assertIsNone(re.fullmatch(version["pattern"], invalid))
        self.assertTrue(all(identity == identities[0] for identity in identities))

    def test_each_native_fixture_has_explicit_provenance_without_artifact_placeholders(self):
        for family, name in FAMILIES:
            with self.subTest(name=name):
                value = read(CONTRACTS / family / "fixtures" / (name + ".v2.valid.json"))
                schema = read(CONTRACTS / family / (name + ".v2.schema.json"))
                value.pop("$comment")
                self.assertTrue(set(schema["required"]) <= set(value))
                self.assertTrue(set(value) <= set(schema["properties"]))
                self.assertEqual(2, value["schemaVersion"])
                self.assertEqual("18.0.0", value["serviceVersion"])
                self.assertNotIn("serviceArtifactSha256", value)
                self.assertNotIn("modelArtifactSha256", value)

    def test_query_summaries_keep_legacy_and_native_shapes_distinct(self):
        schema = read(CONTRACTS / "brake-cloud-api/query-page.v2.schema.json")
        legacy = schema["$defs"]["legacyWindowItem"]
        native = schema["$defs"]["nativeWindowItem"]
        self.assertIn("serviceArtifactSha256", legacy["required"])
        self.assertNotIn("serviceArtifactSha256", native["properties"])
        self.assertIn("messageSchemaVersion", native["required"])
        self.assertIn("serviceInstance", native["required"])
        for name in ("messageItemAssessment", "messageItemEvent", "messageItemAdvisory"):
            alternatives = schema["$defs"][name]["properties"]["message"]["oneOf"]
            self.assertEqual(2, len(alternatives))
            for ref in alternatives:
                self.assertTrue((CONTRACTS / "brake-cloud-api" / ref["$ref"]).is_file())


if __name__ == "__main__":
    unittest.main()
