#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts/validate-component-lock"
LOCK = ROOT / "components/baseline.lock.json"


class ComponentLockTests(unittest.TestCase):
    def run_validator(self, lock: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [str(VALIDATOR), "--lock", str(lock)], text=True, capture_output=True
        )

    def write_mutation(self, value: dict) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        path = Path(temp_dir.name) / "lock.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def test_published_lock_is_valid(self) -> None:
        result = self.run_validator(LOCK)
        self.assertEqual(0, result.returncode, result.stderr)

    def test_floating_branch_is_rejected(self) -> None:
        value = json.loads(LOCK.read_text(encoding="utf-8"))
        value["components"]["aos-vehicle-platform"]["source"]["branch"] = "main"
        result = self.run_validator(self.write_mutation(value))
        self.assertNotEqual(0, result.returncode)
        self.assertIn("must not lock a branch", result.stderr)

    def test_missing_architecture_is_rejected(self) -> None:
        value = json.loads(LOCK.read_text(encoding="utf-8"))
        value["components"]["brake-health-service"]["architectures"] = []
        result = self.run_validator(self.write_mutation(value))
        self.assertNotEqual(0, result.returncode)
        self.assertIn("architectures are missing", result.stderr)

    def test_embedded_digest_mismatch_is_rejected(self) -> None:
        value = json.loads(LOCK.read_text(encoding="utf-8"))
        value["components"]["kuksa-databroker"]["artifact"][
            "containerArtifactSha256"
        ] = "0" * 64
        result = self.run_validator(self.write_mutation(value))
        self.assertNotEqual(0, result.returncode)
        self.assertIn("container digest mismatch", result.stderr)

    def test_local_path_is_rejected(self) -> None:
        value = json.loads(LOCK.read_text(encoding="utf-8"))
        value["components"]["carla-ego-runtime"]["source"][
            "localPath"
        ] = "/Users/example/runtime"
        result = self.run_validator(self.write_mutation(value))
        self.assertNotEqual(0, result.returncode)
        self.assertIn("local or unresolved path", result.stderr)

    def test_generated_bundle_digest_is_rejected(self) -> None:
        value = json.loads(LOCK.read_text(encoding="utf-8"))
        value["components"]["aos-vehicle-platform"]["artifact"][
            "generatedBundle"
        ]["sha256"] = "not-a-digest"
        result = self.run_validator(self.write_mutation(value))
        self.assertNotEqual(0, result.returncode)
        self.assertIn("generated bundle digest is invalid", result.stderr)


if __name__ == "__main__":
    unittest.main()
