# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Tests for the R6.1-6 rootfs-only bootstrap release validator."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate-r6-1-bootstrap-release"


def load_validator():
    loader = importlib.machinery.SourceFileLoader("r6_1_bootstrap_release", str(SCRIPT))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    if spec is None:
        raise RuntimeError("cannot create bootstrap release validator module spec")
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


VALIDATOR = load_validator()


class R61BootstrapReleaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()
        self.image = self.root / "rootfs-full/rootfs.squashfs"
        self.image.parent.mkdir()
        self.image.write_bytes(b"qualified-rootfs")
        self.config = {
            "schemaVersion": 2,
            "publisher": {"company": "maninblack"},
            "items": [
                {
                    "identity": {
                        "type": "component",
                        "codename": VALIDATOR.EXPECTED_CODENAME,
                    },
                    "version": VALIDATOR.EXPECTED_VERSION,
                    "sourceFolder": "rootfs-full",
                    "images": [
                        {
                            "path": "rootfs.squashfs",
                            "mediaType": VALIDATOR.EXPECTED_MEDIA_TYPE,
                            "archInfo": {"architecture": "arm64"},
                            "osInfo": {"os": "linux"},
                        }
                    ],
                    "configuration": {
                        "runtimes": [
                            {
                                "codename": VALIDATOR.EXPECTED_CODENAME,
                                "type": "runtime",
                            }
                        ]
                    },
                }
            ],
        }
        self.write_config()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write_config(self) -> None:
        (self.root / "config.yaml").write_text(
            yaml.safe_dump(self.config, sort_keys=False), encoding="utf-8"
        )

    def validate(self):
        return VALIDATOR.validate_output(self.root)

    def test_rootfs_only_release_passes(self) -> None:
        evidence = self.validate()
        self.assertEqual(VALIDATOR.EXPECTED_VERSION, evidence["version"])
        self.assertEqual(len(b"qualified-rootfs"), evidence["rootfsSize"])

    def test_boot_item_is_rejected(self) -> None:
        self.config["items"].append(dict(self.config["items"][0]))
        self.write_config()
        with self.assertRaisesRegex(VALIDATOR.BootstrapReleaseError, "rootfs-only"):
            self.validate()

    def test_version_change_is_rejected(self) -> None:
        self.config["items"][0]["version"] = "6.1.2-maninblack.1"
        self.write_config()
        with self.assertRaisesRegex(VALIDATOR.BootstrapReleaseError, "version"):
            self.validate()

    def test_stale_file_is_rejected(self) -> None:
        (self.root / "stale.bin").write_bytes(b"stale")
        with self.assertRaisesRegex(VALIDATOR.BootstrapReleaseError, "unexpected"):
            self.validate()

    def test_path_traversal_is_rejected(self) -> None:
        self.config["items"][0]["images"][0]["path"] = "../rootfs.squashfs"
        self.write_config()
        with self.assertRaisesRegex(VALIDATOR.BootstrapReleaseError, "unsafe"):
            self.validate()


if __name__ == "__main__":
    unittest.main()
