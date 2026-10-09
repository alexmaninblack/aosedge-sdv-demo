# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Static contract tests for the read-only workspace doctor."""

from __future__ import annotations

import json
import re
import runpy
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "workspace" / "repositories.json"
SCHEMA = ROOT / "workspace" / "repositories.schema.json"
DOCTOR = ROOT / "scripts" / "workspace-doctor"
WORKFLOW = ROOT / ".github" / "workflows" / "repository-boundaries.yml"


def pinned_ci_dependencies(workflow: str) -> dict[str, tuple[str, str]]:
    """Extract the deliberately fixed sibling-checkout shape used by this job."""
    return {repository: (revision, path) for repository, revision, path in re.findall(
        r"repository: ([^\s]+)\n\s+ref: ([0-9a-f]{40})\n\s+path: ([^\s]+)", workflow)}


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

    def test_main_and_historical_branches_do_not_require_rewriting_release_pins(self) -> None:
        accepted_branch = runpy.run_path(str(DOCTOR))["accepted_branch"]
        for item in [self.manifest["workspace"], *self.manifest["repositories"]]:
            branches = item["acceptedBranches"]
            self.assertTrue(accepted_branch("main", branches))
            for branch in branches:
                self.assertTrue(accepted_branch(branch, branches))
            self.assertFalse(accepted_branch("", branches))
            self.assertFalse(accepted_branch("unreviewed-experiment", branches))

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
                "tire-health-service",
                "tire-health-cloud",
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

    def test_ci_checks_out_all_owned_documentation_dependencies_at_manifest_pins(self) -> None:
        checkouts = pinned_ci_dependencies(WORKFLOW.read_text(encoding="utf-8"))
        for item in self.manifest["repositories"]:
            if item["id"] in {"carla", "unreal-engine"}:
                continue
            repository = item["repository"].removeprefix("https://github.com/").removesuffix(".git")
            with self.subTest(repository=repository):
                self.assertEqual((item["acceptedRevision"], "workspace/" + item["directory"]),
                                 checkouts.get(repository))

    def test_ci_dependency_extraction_does_not_treat_branch_or_comment_as_a_pin(self) -> None:
        for invalid in ("main", "# 42395715103d9f512c2586a2c9b98c3975c06ab7"):
            fixture = ("repository: alexmaninblack/brake-health-cloud\n"
                       "  ref: " + invalid + "\n  path: workspace/brake-health-cloud\n")
            self.assertEqual({}, pinned_ci_dependencies(fixture))


if __name__ == "__main__":
    unittest.main()
