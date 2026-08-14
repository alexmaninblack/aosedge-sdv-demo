# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Static safety tests for the R6.1 Yocto build controller."""

from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "guest" / "r6-1-yocto-build"


class R61YoctoBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.content = SCRIPT.read_text(encoding="utf-8")

    def test_exact_moulin_and_manifest_are_required(self) -> None:
        self.assertIn("cbecc1c748a8c5649e9a319b29167bf27dc4fc3a", self.content)
        self.assertIn("77f25a49c439035ab0dc2d8d496048043b1258bb230996428ca730de364bb4fe", self.content)
        self.assertIn("Moulin meta-build system v0.21", self.content)

    def test_build_is_arm64_main_node_only(self) -> None:
        self.assertIn("--MACHINE=qemuarm64", self.content)
        self.assertIn("--NODE_TYPE=main", self.content)
        self.assertIn("main-qemuarm64.img", self.content)

    def test_cache_and_input_boundaries_are_guarded(self) -> None:
        self.assertIn("/home/yocto/yocto-cache/downloads", self.content)
        self.assertIn("/home/yocto/yocto-cache/sstate-cache", self.content)
        self.assertIn("credential-like file", self.content)
        self.assertIn("findmnt -n -o FSTYPE", self.content)

    def test_background_pid_is_ownership_checked(self) -> None:
        self.assertIn('/proc/${pid}/cmdline', self.content)
        self.assertIn("build PID is not owned by R6.1", self.content)
        self.assertIn("nohup", self.content)


if __name__ == "__main__":
    unittest.main()
