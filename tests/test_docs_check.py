# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Acceptance tests for the deterministic documentation quality gate."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHECK = ROOT / "scripts" / "docs-check"


class DocumentationCheckTests(unittest.TestCase):
    def run_check(self, root: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [str(CHECK), "--root", str(root)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def temporary_documentation(self) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        temporary = tempfile.TemporaryDirectory()
        workspace = Path(temporary.name)
        root = workspace / "aosedge-sdv-demo"
        root.mkdir()
        shutil.copy2(ROOT / ".gitignore", root / ".gitignore")
        shutil.copy2(ROOT / "README.md", root / "README.md")
        shutil.copy2(ROOT / "THIRD_PARTY_NOTICES.md", root / "THIRD_PARTY_NOTICES.md")
        shutil.copy2(ROOT / "LICENSE", root / "LICENSE")
        (root / "workspace").mkdir()
        shutil.copy2(ROOT / "workspace" / "repositories.json", root / "workspace" / "repositories.json")
        coverage = root / "contracts" / "software-delivery-dashboard"
        coverage.mkdir(parents=True)
        shutil.copy2(
            ROOT / "contracts" / "software-delivery-dashboard" / "coverage-matrix.v1.json",
            coverage / "coverage-matrix.v1.json",
        )
        shutil.copytree(ROOT / "docs", root / "docs", ignore=shutil.ignore_patterns(".DS_Store"))
        sibling_files = (
            ("carla-ego-runtime", "docs/carla-setup-macos.md"),
            ("carla-ego-runtime", "docs/macos-launchers.md"),
            ("carla-ego-runtime", "docs/brake-event-scenario.md"),
            ("carla-ego-runtime", "config/m6_2_town10hd_handover.json"),
            ("carla-ego-runtime", "docs/external-control-contract.md"),
            ("carla-ego-runtime", "docs/viss-profile.md"),
            ("carla-ego-runtime", "docs/telemetry-contract.md"),
            ("aos-vehicle-platform", "docs/architecture.md"),
            (
                "aos-vehicle-platform",
                "contracts/vehicle-telemetry-profile/README.md",
            ),
            (
                "aos-vehicle-platform",
                "meta-aos-vehicle-platform/recipes-aos/aos-servicemanager/files/sm.cfg",
            ),
            ("brake-health-service", "docs/architecture.md"),
        )
        for repository, relative_path in sibling_files:
            source = ROOT.parent / repository / relative_path
            destination = workspace / repository / relative_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
        return temporary, root

    def test_current_documentation_passes(self) -> None:
        result = self.run_check(ROOT)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("Documentation quality gate: PASS", result.stdout)

    def test_broken_anchor_is_rejected(self) -> None:
        temporary, root = self.temporary_documentation()
        self.addCleanup(temporary.cleanup)
        target = root / "docs" / "getting-started" / "README.md"
        target.write_text(
            target.read_text(encoding="utf-8")
            + "\n[Broken test link](../README.md#missing-test-anchor)\n",
            encoding="utf-8",
        )
        result = self.run_check(root)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("missing anchor", result.stderr)

    def test_undefined_identifier_is_rejected(self) -> None:
        temporary, root = self.temporary_documentation()
        self.addCleanup(temporary.cleanup)
        target = root / "docs" / "getting-started" / "README.md"
        target.write_text(
            target.read_text(encoding="utf-8")
            + "\nUndefined test requirement: `SYS-FAKE-999`.\n",
            encoding="utf-8",
        )
        result = self.run_check(root)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("undefined identifier: SYS-FAKE-999", result.stderr)

    def test_orphan_document_is_rejected(self) -> None:
        temporary, root = self.temporary_documentation()
        self.addCleanup(temporary.cleanup)
        (root / "docs" / "orphan.md").write_text(
            "<!-- SPDX-FileCopyrightText: 2026 maninblack -->\n"
            "<!-- SPDX-License-Identifier: MIT -->\n\n"
            "# Orphan Test Document\n",
            encoding="utf-8",
        )
        result = self.run_check(root)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("document is not reachable", result.stderr)

    def test_unexplained_requirement_in_reader_view_is_rejected(self) -> None:
        temporary, root = self.temporary_documentation()
        self.addCleanup(temporary.cleanup)
        target = root / "docs" / "requirements" / "component-decomposition-and-interface-register.md"
        text = target.read_text(encoding="utf-8")
        text = text.replace(
            "## Detailed Package Traceability",
            "Unexplained reader reference: SYS-SRC-001.\n\n## Detailed Package Traceability",
            1,
        )
        target.write_text(text, encoding="utf-8")
        result = self.run_check(root)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("reader view contains unexplained system identifiers", result.stderr)

    def test_bare_requirement_in_traceability_is_rejected(self) -> None:
        temporary, root = self.temporary_documentation()
        self.addCleanup(temporary.cleanup)
        target = root / "docs" / "requirements" / "component-decomposition-and-interface-register.md"
        text = target.read_text(encoding="utf-8")
        text = text.replace(
            "[Exact source-to-Unit binding (`SYS-SRC-001`)]"
            "(system-requirements-and-traceability.md#sys-src-001)",
            "`SYS-SRC-001`",
            1,
        )
        target.write_text(text, encoding="utf-8")
        result = self.run_check(root)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("detailed package reference must use a named direct link", result.stderr)

    def test_stale_canonical_input_version_is_rejected(self) -> None:
        temporary, root = self.temporary_documentation()
        self.addCleanup(temporary.cleanup)
        target = root / "docs" / "architecture" / "high-level-architecture.md"
        text = target.read_text(encoding="utf-8").replace(
            "- Version: 1.1", "- Version: 1.2", 1
        )
        target.write_text(text, encoding="utf-8")
        result = self.run_check(root)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("label does not name target version 1.2", result.stderr)

    def test_backup_document_artifact_is_rejected(self) -> None:
        temporary, root = self.temporary_documentation()
        self.addCleanup(temporary.cleanup)
        source = root / "docs" / "getting-started" / "README.md"
        backup = root / "docs" / "getting-started" / "README.md.bak"
        shutil.copy2(source, backup)
        result = self.run_check(root)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("unexpected documentation artifact type", result.stderr)

    def test_mermaid_semicolon_is_rejected(self) -> None:
        temporary, root = self.temporary_documentation()
        self.addCleanup(temporary.cleanup)
        target = root / "docs" / "architecture" / "demo-scenario-architecture-flows.md"
        text = target.read_text(encoding="utf-8").replace(
            "AC->>VU: Check dependency and install through SOTA 2",
            "AC->>VU: Check dependency; install through SOTA 2",
            1,
        )
        target.write_text(text, encoding="utf-8")
        result = self.run_check(root)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("semicolon in sequenceDiagram source is prohibited", result.stderr)

    def test_workspace_github_link_is_rejected(self) -> None:
        temporary, root = self.temporary_documentation()
        self.addCleanup(temporary.cleanup)
        target = root / "docs" / "getting-started" / "README.md"
        target.write_text(
            target.read_text(encoding="utf-8")
            + "\n[Bad workspace link]"
            + "(https://github.com/alexmaninblack/carla-ego-runtime/blob/main/README.md)\n",
            encoding="utf-8",
        )
        result = self.run_check(root)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("workspace repository link must use the local sibling checkout", result.stderr)


if __name__ == "__main__":
    unittest.main()
