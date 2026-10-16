# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Static contract tests for the read-only workspace doctor."""

from __future__ import annotations

import json
import re
import runpy
import unittest
import tempfile
from unittest.mock import patch
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

    def test_current_map_is_default_and_has_no_release_or_launcher_claim(self):
        api = runpy.run_path(str(DOCTOR))
        current = ROOT / 'workspace/repository-map.json'
        data = api['load_current_map'](current)
        self.assertEqual(api['DEFAULT_MANIFEST'], current)
        self.assertNotIn('launcherPaths', data)
        self.assertTrue(all('acceptedRevision' not in r for r in data['repositories']))
        self.assertEqual({'carla', 'unreal-engine'},
                         {r['id'] for r in data['repositories'] if r['optionalSourceDependency']})

    def test_current_map_rejects_missing_duplicate_unsafe_or_pinned_entries(self):
        api = runpy.run_path(str(DOCTOR))
        raw = (ROOT / 'workspace/repository-map.json').read_text()
        cases = []
        value = json.loads(raw); value['repositories'].pop(); cases.append(value)
        value = json.loads(raw); value['repositories'][1] = value['repositories'][0]; cases.append(value)
        for key, bad in [('directory', '..'), ('remote', '--upload-pack'),
                         ('acceptedRevision', 'a'*40), ('optionalSourceDependency', True)]:
            value = json.loads(raw); value['repositories'][2][key] = bad; cases.append(value)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'map.json'
            for value in cases:
                path.write_text(json.dumps(value))
                with self.subTest(value=value), self.assertRaises(api['DoctorError']):
                    api['load_current_map'](path)
            path.write_text(raw[:-2] + ', "schemaVersion": 1}')
            with self.assertRaises(api['DoctorError']):
                api['load_current_map'](path)

    def test_current_source_check_compares_tracking_not_frozen_release(self):
        api = runpy.run_path(str(DOCTOR))
        row = api['load_current_map'](ROOT / 'workspace/repository-map.json')['repositories'][2]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); repo = root / row['directory']; repo.mkdir(); (repo / '.git').mkdir()
            def git(path, args):
                return {('rev-parse', '--show-toplevel'): str(repo),
                        ('rev-parse', 'HEAD'): 'b'*40,
                        ('branch', '--show-current'): 'main',
                        ('remote', 'get-url', 'origin'): row['repository'],
                        ('rev-parse', 'origin/main'): 'b'*40}[tuple(args)]
            namespace = api['check_repository'].__globals__
            with patch.dict(namespace, run_git=git, dirty_paths=lambda p: []):
                report = api['Report'](); api['check_repository'](report, root, row, False)
                self.assertEqual(0, report.errors)
            def behind(path, args):
                return 'c'*40 if args == ['rev-parse', 'origin/main'] else git(path, args)
            with patch.dict(namespace, run_git=behind, dirty_paths=lambda p: []):
                report = api['Report'](); api['check_repository'](report, root, row, False)
                self.assertEqual(1, report.errors)

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
