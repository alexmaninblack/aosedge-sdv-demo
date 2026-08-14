# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Tests for the fully pinned R6.1 Moulin manifest."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate-r6-1-manifest"


def load_validator():
    loader = importlib.machinery.SourceFileLoader("r6_1_manifest", str(SCRIPT))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    if spec is None:
        raise RuntimeError("cannot create manifest validator module spec")
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


VALIDATOR = load_validator()


class R61ManifestTests(unittest.TestCase):
    def setUp(self) -> None:
        self.lock = VALIDATOR.load_lock()
        self.content = VALIDATOR.MANIFEST_PATH.read_text(encoding="utf-8")

    def validate_modified(self, content: str) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.yaml"
            path.write_text(content, encoding="utf-8")
            lock = dict(self.lock)
            lock["evidence"] = dict(self.lock["evidence"])
            evidence = dict(lock["evidence"]["pinnedMoulinManifest"])
            evidence["sha256"] = VALIDATOR.sha256(path)
            lock["evidence"]["pinnedMoulinManifest"] = evidence
            VALIDATOR.validate_manifest(path, lock)

    def test_tracked_manifest_passes(self) -> None:
        VALIDATOR.validate_manifest()

    def test_floating_revision_is_rejected(self) -> None:
        revision = self.lock["sources"][0]["revision"]
        content = self.content.replace(f'rev: "{revision}"', 'rev: "main"', 1)
        with self.assertRaisesRegex(VALIDATOR.ManifestError, "full commit SHA"):
            self.validate_modified(content)

    def test_nonpersistent_cache_is_rejected(self) -> None:
        content = self.content.replace(
            VALIDATOR.DOWNLOADS_DIR, "${TOPDIR}/downloads", 1
        )
        with self.assertRaisesRegex(VALIDATOR.ManifestError, "DL_DIR"):
            self.validate_modified(content)

    def test_example_publisher_is_rejected(self) -> None:
        content = self.content.replace(
            'company: "maninblack"', 'company: "EPAM Systems"', 1
        )
        with self.assertRaisesRegex(VALIDATOR.ManifestError, "publisher"):
            self.validate_modified(content)

    def test_embedded_private_key_is_rejected(self) -> None:
        content = self.content + "\n# BEGIN PRIVATE KEY\n"
        with self.assertRaisesRegex(VALIDATOR.ManifestError, "forbidden data"):
            self.validate_modified(content)


if __name__ == "__main__":
    unittest.main()
