# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Static contract tests for the read-only workspace doctor."""

from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "workspace" / "repositories.json"
SCHEMA = ROOT / "workspace" / "repositories.schema.json"
DOCTOR = ROOT / "scripts" / "workspace-doctor"


class WorkspaceDoctorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        cls.schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        cls.doctor = DOCTOR.read_text(encoding="utf-8")

    def test_manifest_has_unique_pinned_sibling_repositories(self) -> None:
        repositories = self.manifest["repositories"]
        self.assertEqual(len(repositories), len({item["id"] for item in repositories}))
        self.assertEqual(len(repositories), len({item["directory"] for item in repositories}))
        for item in repositories:
            self.assertRegex(item["acceptedRevision"], r"^[0-9a-f]{40}$")
            self.assertTrue(item["repository"].startswith("https://github.com/"))
            self.assertIn(item["visibility"], {"public", "private"})

    def test_contract_contains_no_personal_absolute_path(self) -> None:
        for path in (MANIFEST, SCHEMA, DOCTOR):
            self.assertNotIn("/Users/" + "alexagizim", path.read_text(encoding="utf-8"))

    def test_manifest_covers_runtime_and_component_boundaries(self) -> None:
        identifiers = {item["id"] for item in self.manifest["repositories"]}
        self.assertEqual(
            {
                "carla",
                "unreal-engine",
                "vehicle-gateway",
                "vehicle-platform",
                "functional-service",
                "brake-health-cloud",
            },
            identifiers,
        )

    def test_doctor_is_read_only_by_construction(self) -> None:
        prohibited = ("unlink(", "rmtree(", "remove(", "rename(", "replace(", "write_text(", "open(\"w")
        for marker in prohibited:
            self.assertNotIn(marker, self.doctor)
        self.assertIn('subprocess.run(["ps", "-axo", "command="]', self.doctor)

    def test_schema_and_manifest_version_agree(self) -> None:
        self.assertEqual(1, self.manifest["schemaVersion"])
        self.assertEqual({"const": 1}, self.schema["properties"]["schemaVersion"])


if __name__ == "__main__":
    unittest.main()
