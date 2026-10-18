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
                     "docs/requirements/d4-decision-register.md",
                     "docs/architecture/demo-scenario-architecture-flows.md",
                     "docs/demo/staged-post-sop-brake-health-demo-scenarios.md"]:
            with self.subTest(path=path):
                text = prose(path)
                self.assertIn("100-ms source-time bucket", text)
                self.assertIn("20/30-Hz", text)
                self.assertNotIn("Service v1 retains every third", text)
                self.assertNotIn("selects every third", text)
        self.assertIn("5000 ms", prose("contracts/brake-telemetry-window/README.md"))

    def test_kac_design_does_not_claim_existing_units_are_missing(self):
        for path in ["docs/requirements/d4-decision-register.md",
                     "docs/requirements/components/kuksa-authorization-compatibility.md",
                     "contracts/kuksa-current-demo-authorization/README.md"]:
            with self.subTest(path=path):
                text = prose(path)
                self.assertNotIn("No helper or public-verifier-preparation unit exists", text)
                self.assertNotIn("but no helper or verifier-preparation unit", text)
                self.assertNotIn("Unmodified KUKSA", text)
                self.assertIn("aos-kuksa-verifier-prepare", text)

    def test_factory_compatibility_is_consistent_in_decisions_and_flows(self):
        for path in ["docs/architecture/demo-scenario-architecture-flows.md",
                     "docs/requirements/d4-decision-register.md",
                     "docs/architecture/decisions/0005-kuksa-vehicle-data-boundary.md"]:
            with self.subTest(path=path):
                text = prose(path)
                self.assertNotIn("KUKSA remains unchanged", text)
                self.assertNotIn("KUKSA remains an unchanged", text)
                self.assertIn("scope-path", text)
                self.assertIn("source-timestamp", text)
        d4 = prose("docs/requirements/d4-decision-register.md")
        self.assertNotIn("the current baked", d4)
        self.assertIn("Factory Image shall contain no shared static verifier", d4)

    def test_backend_ownership_does_not_describe_fixture_dashboards_as_installed(self):
        text = prose("docs/architecture/repository-boundaries.md")
        self.assertIn("integrated Presenter", text)
        self.assertIn("source-only Dashboard is a non-live fixture", text)
        self.assertIn("Tire has no standalone web dashboard", text)
        self.assertNotIn("repositories are now present", text)
        self.assertNotIn("public repository exists", text)
        self.assertIn("not a requirement for two SP accounts", text)

    def test_launcher_recovery_does_not_require_manual_shell_reconstruction(self):
        text = prose("docs/getting-started/troubleshooting.md")
        self.assertIn("It restores the selected workspace environment", text)
        self.assertNotIn("Restore declared values after a terminal restart", text)

    def test_scenario_authoring_does_not_require_a_second_controller(self):
        text = prose("docs/development/add-demo-scenario.md")
        self.assertIn("installed single Test", text)
        self.assertIn("does not require a separate Production controller", text)
        self.assertIn("same accepted artifact bytes and digest without rebuild", text)

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

    def test_native_input_source_citation_matches_selected_factory(self):
        lock = json.loads(read("workspace/inputs/controller-images.lock.json"))
        text = prose("docs/architecture/demo-control-service-inputs.md")
        for kind in ("prebuilt", "rebuilt"):
            revision = lock[kind]["factory"]["sourceRevision"]
            self.assertIn(f"aos-vehicle-platform/blob/{revision}/", text)
        self.assertIn("AosCore applications", text)
        self.assertIn("AosCore library", text)
        self.assertIn("AosCore API", text)
        self.assertIn("ExecStartPre", text)
        self.assertIn("ExecStartPost", text)
        self.assertNotIn("9eecb80c4994937b5c8cbe0464970f81e8ad4c2d", text)
        self.assertNotIn("aos_iamanager/blob/", text)
        decision = prose("docs/architecture/decisions/0015-use-native-aos-service-runtime-inputs.md")
        self.assertIn("demo-control-service-inputs.md#native-launch-boundary", decision)
        self.assertNotIn("9eecb80c4994937b5c8cbe0464970f81e8ad4c2d", decision)

    def test_unattended_access_requirement_retains_exact_test_only_authority(self):
        text = prose("docs/requirements/components/demo-orchestration.md")
        self.assertIn("`REQ-DEMO-025`", text)
        self.assertIn("bound instance, exact Factory digest, explicitly authorized Cloud domain", text)
        self.assertIn("explicit OEM/SP owner pins and exact Test-only binding", text)
        self.assertIn("shall not grant access to a Production-role vehicle", text)
        self.assertNotIn("Factory digest and staging Test", text)

    def test_tire_admin_protocol_has_one_current_owner_and_keeps_legacy_inputs(self):
        path = "contracts/tire-cloud-api/README.md"
        text = prose(path)
        self.assertIn("## Current-Test administrative protocol", text)
        self.assertIn("Cleanup accepts exactly `[currentTestUid]`", text)
        self.assertIn("Production-only selectors", text)
        self.assertIn("mode-0600 Unix socket", text)
        self.assertIn("4096 bytes", text)
        self.assertIn("at most 16 previews", text)
        self.assertIn("60 seconds", text)
        self.assertIn("no `contractVersion` field", text)
        self.assertIn("database schema 4", text)
        for field in ("messages", "assessments", "events", "advisories",
                      "functionStatus", "quarantine", "resetProducers", "resetCommands",
                      "functionObservations", "functionObservationConflicts"):
            self.assertIn(f"`{field}`", text)
        self.assertIn("## Retained compatibility inputs", text)
        for legacy in ("tire-cloud-api-profile.v1.json", "cleanup-preview.schema.json",
                       "fixtures/cleanup-preview.valid.json"):
            self.assertTrue((ROOT / "contracts/tire-cloud-api" / legacy).is_file())
        self.assertFalse((ROOT / "contracts/tire-cloud-api/studio-current-wire.md").exists())
        for owner in (path, "docs/architecture/demo-control-backends.md",
                      "contracts/implementation-status.md"):
            self.assertNotIn("studio-current-wire.md", read(owner))
        self.assertNotIn("implemented v1.1 demo", text)

    def test_d4_current_factory_rule_does_not_select_superseded_hla(self):
        text = prose("docs/requirements/d4-decision-register.md")
        self.assertNotIn("required by HLA 1.4", text)
        self.assertIn("accepted HLA's installed profile", text)

    def test_scratch_policy_matches_automatic_launcher_and_explicit_specialist(self):
        text = prose("docs/governance/rapid-development-and-debugging.md")
        self.assertIn("the launcher selects an owned shorter", text)
        self.assertIn("same volume", text)
        self.assertIn("direct specialist tools retain explicit selection", text)
        self.assertNotIn("explicitly select a shorter `.tmp`", text)


if __name__ == "__main__":
    unittest.main()
