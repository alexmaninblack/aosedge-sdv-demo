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

    def test_noninteractive_build_exports_pinned_moulin_tools(self) -> None:
        self.assertIn('readonly tool_bin="/home/yocto/.local/bin"', self.content)
        self.assertIn('export PATH="${tool_bin}:', self.content)
        self.assertIn('readonly rouge="${tool_bin}/rouge"', self.content)
        self.assertIn("Rouge image tool is unavailable", self.content)
        self.assertIn("Moulin and Rouge do not use the same pinned environment", self.content)
        self.assertIn("usage: rouge", self.content)
        self.assertIn('readonly gpt_image_version="0.8.1"', self.content)
        self.assertIn("gpt-image version mismatch", self.content)

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

    def test_project_build_is_pinned_and_credential_free(self) -> None:
        self.assertIn(
            "8d1814540e1c6b6291a6b4b8af3bcb66e2d118e9650af5002dc9847b62115445",
            self.content,
        )
        self.assertIn(
            "ad850e8bad7585cbdf589915a64fee061a0bd405", self.content
        )
        self.assertIn(
            "528b09ca750576a2ab8520802d6f9ed015e7e57cab72d5aae4bbcdb55e2cf4a5",
            self.content,
        )
        self.assertIn("credential reference present", self.content)
        self.assertIn("r6-1-yocto-build run-project", self.content)

    def test_unsigned_fota_waits_for_the_project_image(self) -> None:
        self.assertIn("project image must pass before the FOTA build", self.content)
        self.assertIn("ninja -j 10 fota", self.content)
        self.assertIn("r6-1-yocto-build run-project-fota", self.content)


if __name__ == "__main__":
    unittest.main()
