# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Tests for unsigned R6.1-2 FOTA output validation."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate-r6-1-fota-output"


def load_validator():
    loader = importlib.machinery.SourceFileLoader("r6_1_fota_output", str(SCRIPT))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    if spec is None:
        raise RuntimeError("cannot create FOTA validator module spec")
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


VALIDATOR = load_validator()


def item(codename: str, media_type: str, path: str) -> dict:
    return {
        "identity": {"codename": codename, "type": "component"},
        "version": "6.1.0",
        "images": [
            {
                "mediaType": media_type,
                "path": path,
                "archInfo": {"architecture": "arm64"},
                "osInfo": {"os": "linux"},
            }
        ],
        "configuration": {
            "runtimes": [{"codename": codename, "type": "runtime"}]
        },
    }


class R61FotaOutputTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()
        boot = "aos-vm-1.0.0-main-qemuarm64-boot"
        rootfs = "aos-vm-1.0.0-main-qemuarm64-rootfs"
        self.config = {
            "schemaVersion": 2,
            "publisher": {"company": "maninblack"},
            "items": [
                item(
                    boot,
                    "application/vnd.aos.image.component.full.v1+gzip",
                    "boot/boot.gz",
                ),
                item(
                    rootfs,
                    "application/vnd.aos.image.component.full.v1+squashfs",
                    "rootfs-full/rootfs.squashfs",
                ),
            ],
        }
        for path in (self.root / "boot/boot.gz", self.root / "rootfs-full/rootfs.squashfs"):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"qualified-r61-output")
        self.write_config()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write_config(self) -> None:
        (self.root / "config.yaml").write_text(
            yaml.safe_dump(self.config, sort_keys=False), encoding="utf-8"
        )

    def validate(self) -> list[dict]:
        original = VALIDATOR.EXPECTED_ROOT
        try:
            VALIDATOR.EXPECTED_ROOT = self.root
            return VALIDATOR.validate_output(self.root)
        finally:
            VALIDATOR.EXPECTED_ROOT = original

    def test_unsigned_full_output_passes(self) -> None:
        evidence = self.validate()
        self.assertEqual(len(evidence), 2)
        self.assertTrue(all(entry["size"] > 0 for entry in evidence))

    def test_publish_credentials_are_rejected(self) -> None:
        self.config["publish"] = {"tlsKey": "oem.p12"}
        self.write_config()
        with self.assertRaisesRegex(VALIDATOR.FotaOutputError, "tlsKey"):
            self.validate()

    def test_path_traversal_is_rejected(self) -> None:
        self.config["items"][0]["images"][0]["path"] = "../boot.gz"
        self.write_config()
        with self.assertRaisesRegex(VALIDATOR.FotaOutputError, "unsafe path"):
            self.validate()

    def test_incremental_or_extra_item_is_rejected(self) -> None:
        self.config["items"].append(dict(self.config["items"][1]))
        self.write_config()
        with self.assertRaisesRegex(VALIDATOR.FotaOutputError, "item count"):
            self.validate()


if __name__ == "__main__":
    unittest.main()
