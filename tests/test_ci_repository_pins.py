# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Prevent hosted boundary checks from silently drifting from workspace pins."""

import json
from pathlib import Path
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]


class RepositoryCiPinsTests(unittest.TestCase):
    def test_dependency_checkouts_match_accepted_workspace_revisions(self):
        manifest = json.loads((ROOT / "workspace/repositories.json").read_text())
        expected = {item["directory"]: item["acceptedRevision"]
                    for item in manifest["repositories"]}
        workflow = yaml.safe_load((ROOT / ".github/workflows/repository-boundaries.yml").read_text())
        checkouts = [step["with"] for step in workflow["jobs"]["qualify"]["steps"]
                     if step.get("uses", "").startswith("actions/checkout@")]
        self.assertEqual({item["path"].split("/")[-1] for item in checkouts},
                         {"aosedge-sdv-demo", "carla-ego-runtime", "aos-vehicle-platform", "brake-health-service", "tire-health-service"})
        for item in checkouts:
            directory = item["path"].split("/")[-1]
            if directory == "aosedge-sdv-demo":
                continue
            with self.subTest(repository=directory):
                self.assertEqual(item["ref"], expected[directory])
        platform = next(item for item in checkouts if item["path"].endswith("/aos-vehicle-platform"))
        self.assertEqual(platform["fetch-depth"], 0)


if __name__ == "__main__":
    unittest.main()
