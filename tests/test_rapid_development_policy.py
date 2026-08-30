# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class RapidDevelopmentPolicyTest(unittest.TestCase):
    def setUp(self) -> None:
        self.agent_instructions = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.policy = (
            ROOT / "docs/governance/rapid-development-and-debugging.md"
        ).read_text(encoding="utf-8")

    def test_agent_instructions_require_accepted_design_and_rapid_proof(self) -> None:
        self.assertIn("Accepted design is authoritative", self.agent_instructions)
        self.assertIn("Rapid-debug before formal build", self.agent_instructions)
        self.assertIn("Never issue a blind retry", self.agent_instructions)
        self.assertIn("Use authenticated APIs/CLIs rather than a browser", self.agent_instructions)

    def test_policy_preserves_human_authority_without_routine_pauses(self) -> None:
        self.assertIn("Human-Involvement Boundary", self.policy)
        self.assertIn("continue without intermediate approval", self.policy)
        self.assertIn("execution safety control", self.policy)
        self.assertIn("irreversible external action", self.policy)

    def test_policy_requires_transient_proof_before_formal_build(self) -> None:
        self.assertIn("Mandatory Rapid-Debug Cycle", self.policy)
        self.assertIn("Prove one minimal reversible hypothesis", self.policy)
        self.assertIn("Consolidate source only after proof", self.policy)
        self.assertIn("one warm incremental image build", self.policy)

    def test_policy_guards_security_and_disk_hygiene(self) -> None:
        self.assertIn("No rootfs remount", self.policy)
        self.assertIn("Delete child overlays before backing images", self.policy)
        self.assertIn("60 GiB", self.policy)
        self.assertIn("Preserve Builder/caches", self.policy)


if __name__ == "__main__":
    unittest.main()
