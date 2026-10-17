# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Source-only consistency checks for effective design profiles and traceability.

These checks read documentation/contracts. They never build or start a runtime
and never substitute for target-host acceptance or the expanded fault matrix.
"""
import json
import re
import runpy
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECK = runpy.run_path(str(ROOT / "scripts/docs-check"))


def read(relative):
    return (ROOT / relative).read_text()


def prose(relative):
    return " ".join(read(relative).split())


class EffectiveDesignDocumentationTests(unittest.TestCase):
    def test_current_component_heading_keeps_strict_reader_validation(self):
        path = (ROOT / "docs/requirements/component-decomposition-and-interface-register.md").resolve()
        text = path.read_text()
        check = CHECK["check_reader_traceability"]
        self.assertEqual(check(ROOT, {path: text}), [])
        missing = text.replace("## Component requirement packages", "## Missing packages")
        self.assertTrue(any("sections are missing" in issue.message
                            for issue in check(ROOT, {path: missing})))
        unexplained = text.replace("| Package | Human-readable responsibility |",
                                   "SYS-OBS-001\n| Package | Human-readable responsibility |")
        self.assertTrue(any("unexplained system identifiers" in issue.message
                            for issue in check(ROOT, {path: unexplained})))

    def test_all_component_packages_have_current_authority_not_review_diaries(self):
        packages = list((ROOT / "docs/requirements/components").glob("*.md"))
        concrete = [p for p in packages if p.name not in {"README.md", "template.md"}]
        self.assertEqual(len(concrete), 13)
        for path in concrete:
            with self.subTest(package=path.name):
                text = path.read_text()
                self.assertNotIn("## Review provenance", text)
                self.assertNotIn("preserves prior version deltas and review dates", text)
                self.assertNotIn("| Proposed resolution | Review state |", text)
                self.assertTrue(any(heading in text for heading in (
                    "## Verification Traceability", "## Verification Allocation",
                    "## Stable Unit-Test Obligations")), path.name)

    def test_ui_rules_and_cases_remain_complete(self):
        spec = read("docs/demo/mockups/aosedge-demo-interaction-specification.md")
        register = read("docs/demo/mockups/aosedge-demo-ui-traceability-register.md")
        self.assertEqual(set(re.findall(r'<a id="ui-int-(\d{3})"', spec)),
                         {f"{n:03d}" for n in range(1, 80)})
        self.assertEqual(set(re.findall(r'<a id="ui-at-(\d{3})"', spec)),
                         {f"{n:03d}" for n in range(1, 51)})
        rows = re.findall(r'^\| \[`UI-INT-(\d{3})`\]', register, re.M)
        self.assertEqual(len(rows), 79)
        self.assertEqual(len(set(rows)), 79)

    def test_ui_acceptance_matches_native_integrated_surfaces(self):
        spec = prose("docs/demo/mockups/aosedge-demo-interaction-specification.md")
        self.assertIn("combined native Driving Control/Telemetry", spec)
        self.assertNotIn("remains the native text-only Terminal", spec)
        self.assertNotIn("Common five-stage release template", spec)
        self.assertNotIn("exactly three Cloud user certificates", spec)
        self.assertIn("one OEM certificate and one associated SP certificate", spec)
        self.assertIn("expanded two-provider profile", spec)

    def test_installed_and_expanded_retirement_are_explicit(self):
        req = prose("docs/requirements/components/demo-orchestration.md")
        self.assertIn("Installed Finish shall stop owned source/VM/backends", req)
        self.assertIn("Ordinary Finish shall not require a deliberate old-credential reconnect", req)
        self.assertIn("bounded reconnect proving old credentials cannot restore", req)
        self.assertIn("In the expanded Validation/Production profile, R0", req)
        self.assertIn("Installed protected mutations shall be serialized", req)
        self.assertIn("expanded concurrent-operation design", req)

    def test_selected_peer_trust_is_not_the_retired_local_exception(self):
        for path in ["contracts/viss-trust-telemetry-profile/README.md",
                     "contracts/exclusive-live-source-assignment/README.md",
                     "docs/requirements/components/demo-orchestration.md"]:
            with self.subTest(path=path):
                text = prose(path)
                self.assertIn("strict selected-Unit mTLS", text)
                self.assertNotIn("per-Unit VISS mTLS is deferred", text)
                self.assertNotIn("strict authenticated-peer clause below remains the future target", text)

    def test_source_bucket_definition_is_integrated_not_overridden(self):
        for path in ["contracts/brake-telemetry-window/README.md",
                     "docs/requirements/d4-decision-register.md"]:
            with self.subTest(path=path):
                text = prose(path)
                self.assertIn("100-ms source-time bucket", text)
                self.assertIn("20/30-Hz", text)
                self.assertNotIn("Service v1 retains every third", text)
        self.assertIn("5000 ms", prose("contracts/brake-telemetry-window/README.md"))

    def test_resource_declarations_match_current_profiles_without_claiming_proof(self):
        brake = json.loads(read("contracts/brake-health-runtime/brake-health-runtime-profile.v1.json"))
        tire = json.loads(read("contracts/tire-health-model/tire-health-product-profile.v1.json"))
        self.assertEqual(brake["aosRequestedQuotas"]["cpuLimit"], 250)
        self.assertEqual(tire["runtime"]["requestedQuota"]["cpuLimit"], 600)
        d4 = prose("docs/requirements/d4-decision-register.md")
        self.assertIn("250", d4)
        self.assertIn("600", d4)
        self.assertIn("No fixed CPU worker/control is enabled", prose("docs/requirements/components/tire-health-service.md"))
        self.assertIn("not enforcement proof", prose("contracts/tire-health-model/README.md"))

    def test_advisory_restart_and_replacement_are_not_conflated(self):
        for path in ["contracts/shared-evidence-correlation/README.md",
                     "docs/demo/mockups/aosedge-demo-interaction-specification.md"]:
            with self.subTest(path=path):
                text = prose(path)
                self.assertIn("restart preserves the", text)
                self.assertIn("producer replacement", text)
                self.assertIn("rotates the epoch", text)
                self.assertNotIn("restart/new epoch", text)

    def test_design_ids_survive_chronology_consolidation(self):
        end_to_end = read("docs/requirements/components/end-to-end-acceptance.md")
        cross = read("docs/requirements/components/cross-cutting.md")
        for n in range(1, 7):
            self.assertIn(f"`E2E-D{n}`", end_to_end)
        for n in range(1, 5):
            self.assertIn(f"`CROSS-D{n}`", cross)
        self.assertIn('id="d3-review-decisions"', end_to_end)
        self.assertIn("Effective allocation", end_to_end)


if __name__ == "__main__":
    unittest.main()
