# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Freeze input shapes and credential placement; no VM or Cloud calls."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts/service-runtime-inputs"


class ServiceRuntimeInputTests(unittest.TestCase):
    def load(self, name):
        return json.loads((CONTRACT / name).read_text())

    def test_public_fields_exclude_package_identity_and_credentials(self):
        value = self.load("public-metadata.schema.json")
        expected = {"schemaVersion", "unitSystemUid", "unitRole",
                    "vdpContractVersion", "vdpContractSha256"}
        self.assertEqual(expected, set(value["required"]))
        self.assertEqual(expected, set(value["properties"]))
        self.assertFalse(value["additionalProperties"])
        self.assertEqual(2, value["properties"]["schemaVersion"]["const"])

    def test_package_release_and_vdp_use_the_same_version_rules(self):
        value = self.load("service-release.schema.json")
        self.assertEqual({"schemaVersion", "serviceVersion"}, set(value["required"]))
        self.assertEqual(set(value["required"]), set(value["properties"]))
        self.assertFalse(value["additionalProperties"])
        self.assertEqual(1, value["properties"]["schemaVersion"]["const"])
        version = value["properties"]["serviceVersion"]
        self.assertEqual(32, version["maxLength"])
        self.assertEqual(version, self.load("public-metadata.schema.json")["properties"]["vdpContractVersion"])
        for valid in ("0.0.0", "1.0.0", "18.0.0"):
            self.assertIsNotNone(re.fullmatch(version["pattern"], valid))
        for invalid in ("01.0.0", "1.0", "1.0.0-dev", "1.0.0+build", "", "1.0.0\n"):
            self.assertIsNone(re.fullmatch(version["pattern"], invalid))

    def test_private_session_not_private_mount_root(self):
        value = self.load("credential-placement.v1.json")
        self.assertEqual(["rw", "nosuid", "nodev", "noexec", "mode=1777", "size=65536"], value["mountOptions"])
        self.assertEqual("MKDTEMP", value["sessionCreation"])
        self.assertEqual("0700", value["sessionMode"])
        self.assertEqual("0400", value["tokenMode"])
        self.assertEqual(8, value["maximumSessionDirectories"])
        self.assertEqual("FAIL_CLOSED_WITHOUT_DELETING_OTHER_SESSIONS", value["sessionCapacityBehavior"])
        for key in ("preexistingSessionAdoption", "symlinkTraversal", "persistentCredential", "smCodeChangeRequired"):
            self.assertFalse(value[key])

    def test_kac_authority_and_timing_do_not_change(self):
        value = json.loads((ROOT / "contracts/kuksa-current-demo-authorization/kuksa-auth-compat.v1.json").read_text())
        self.assertEqual("AOS_IAM_GET_PERMISSIONS", value["authority"]["authoritativeDecision"])
        self.assertEqual(300, value["timing"]["ttlSeconds"])
        self.assertEqual(180, value["timing"]["renewAfterSecondsFromIssue"])
        self.assertFalse(value["timing"]["cloudRequiredForRenewal"])


if __name__ == "__main__":
    unittest.main()
