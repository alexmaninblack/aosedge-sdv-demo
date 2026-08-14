# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Tests for the R6.1 exact source lock."""

from __future__ import annotations

import copy
import importlib.machinery
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate-r6-1-source-lock"


def load_validator():
    loader = importlib.machinery.SourceFileLoader("r6_1_source_lock", str(SCRIPT))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    if spec is None:
        raise RuntimeError("cannot create validator module spec")
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


VALIDATOR = load_validator()


class R61SourceLockTests(unittest.TestCase):
    def setUp(self) -> None:
        self.lock = VALIDATOR.load_lock()

    def test_tracked_lock_passes(self) -> None:
        VALIDATOR.validate_lock(self.lock)

    def test_floating_revision_is_rejected(self) -> None:
        value = copy.deepcopy(self.lock)
        value["sources"][0]["revision"] = "main"
        with self.assertRaisesRegex(VALIDATOR.LockError, "full commit SHA"):
            VALIDATOR.validate_lock(value)

    def test_service_manager_srcrev_mismatch_is_rejected(self) -> None:
        value = copy.deepcopy(self.lock)
        value["evidence"]["serviceManagerRecipe"]["sourceRevision"] = "0" * 40
        with self.assertRaisesRegex(VALIDATOR.LockError, "SRCREV"):
            VALIDATOR.validate_lock(value)

    def test_local_path_is_rejected(self) -> None:
        value = copy.deepcopy(self.lock)
        value["manifest"]["path"] = "/Users/example/aos-vm.yaml"
        with self.assertRaisesRegex(VALIDATOR.LockError, "local path"):
            VALIDATOR.validate_lock(value)

    def test_unresolved_meta_arm_selector_is_rejected(self) -> None:
        value = copy.deepcopy(self.lock)
        source = next(item for item in value["sources"] if item["name"] == "meta-arm")
        source["pinSource"] = "manifest-commit"
        with self.assertRaisesRegex(VALIDATOR.LockError, "not resolved"):
            VALIDATOR.validate_lock(value)

    def test_builder_image_digest_is_required(self) -> None:
        value = copy.deepcopy(self.lock)
        value["builder"]["imageSha256"] = "latest"
        with self.assertRaisesRegex(VALIDATOR.LockError, "image digest"):
            VALIDATOR.validate_lock(value)

    def test_builder_release_is_pinned(self) -> None:
        value = copy.deepcopy(self.lock)
        value["builder"]["release"] = "latest"
        with self.assertRaisesRegex(VALIDATOR.LockError, "builder release"):
            VALIDATOR.validate_lock(value)

    def test_builder_conan_version_is_pinned(self) -> None:
        value = copy.deepcopy(self.lock)
        value["builder"]["toolchain"]["conanVersion"] = "latest"
        with self.assertRaisesRegex(VALIDATOR.LockError, "Conan version"):
            VALIDATOR.validate_lock(value)

    def test_builder_pydantic_wheel_is_pinned(self) -> None:
        value = copy.deepcopy(self.lock)
        value["builder"]["toolchain"]["pydanticWheelSha256"] = "latest"
        with self.assertRaisesRegex(VALIDATOR.LockError, "Pydantic wheel digest"):
            VALIDATOR.validate_lock(value)

    def test_cloud_openapi_digest_is_required(self) -> None:
        value = copy.deepcopy(self.lock)
        value["evidence"]["cloudApi"]["sha256"] = "current"
        with self.assertRaisesRegex(VALIDATOR.LockError, "OpenAPI digest"):
            VALIDATOR.validate_lock(value)

    def test_mechanism_qualification_revision_is_pinned(self) -> None:
        value = copy.deepcopy(self.lock)
        value["evidence"]["mechanismQualification"]["revision"] = "HEAD"
        with self.assertRaisesRegex(VALIDATOR.LockError, "full commit SHA"):
            VALIDATOR.validate_lock(value)


if __name__ == "__main__":
    unittest.main()
