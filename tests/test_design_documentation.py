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
    def effective_issues(self, relative, old, replacement):
        documents = CHECK["markdown_documents"](ROOT)
        path = (ROOT / relative).resolve()
        self.assertIn(old, documents[path])
        documents[path] = documents[path].replace(old, replacement, 1)
        return CHECK["check_effective_contracts"](ROOT, documents)

    def test_effective_gate_rejects_stale_hash_and_both_conflicting_quota_locations(self):
        d4 = "docs/requirements/d4-decision-register.md"
        cases = [("1024 files and 24 PIDs", "64 files and 16 PIDs"),
                 ("| Brake | 250 | 16 | 8 | 1 | 8 | 1024 | 24 |",
                  "| Brake | 250 | 16 | 8 | 1 | 8 | 64 | 16 |")]
        for old, new in cases:
            with self.subTest(old=old):
                self.assertTrue(any("quota" in x.message for x in self.effective_issues(d4, old, new)))
        contract = ROOT / "contracts/brake-health-model/brake-health-model-profile.v1.json"
        import hashlib
        digest = hashlib.sha256(contract.read_bytes()).hexdigest()
        self.assertTrue(any("hash differs" in x.message
                            for x in self.effective_issues(d4, digest, "0" * 64)))

    def test_effective_gate_rejects_wrong_link_version_and_plain_reading_chain(self):
        self.assertTrue(any("JSON profile version" in x.message for x in self.effective_issues(
            "docs/requirements/components/brake-health-service.md",
            "[Typed QM Advisory Profile 1.2.0]", "[Typed QM Advisory Profile 1.0.2]")))
        path = "docs/architecture/demo-scenario-architecture-flows.md"
        current = CHECK["metadata"](read(path), "Version")
        self.assertTrue(any("plain-text design-chain" in x.message for x in self.effective_issues(
            "docs/architecture/current-implementation.md", "Flows " + current, "Flows 0.0")))

    def test_effective_gate_checks_wrapped_plain_design_versions(self):
        cases = (
            ("Demo Scenario", "docs/demo/staged-post-sop-brake-health-demo-scenarios.md"),
            ("Architecture Flows", "docs/architecture/demo-scenario-architecture-flows.md"),
            ("System Requirements and Traceability", "docs/requirements/system-requirements-and-traceability.md"),
        )
        path = (ROOT / "docs/architecture/current-implementation.md").resolve()
        for title, owner in cases:
            version = CHECK["metadata"](read(owner), "Version")
            for separator in ("\n  ", "\t", "  "):
                for stale in (False, True):
                    with self.subTest(title=title, separator=separator, stale=stale):
                        documents = CHECK["markdown_documents"](ROOT)
                        documents[path] += "\n" + title + separator + ("0.0" if stale else version) + ".\n"
                        issues = CHECK["check_effective_contracts"](ROOT, documents)
                        messages = [x.message for x in issues if "plain-text design-chain" in x.message]
                        self.assertEqual(bool(messages), stale, messages)
                        self.assertTrue(all("\n" not in message for message in messages))

    def test_effective_gate_rejects_duplicate_non_identifier_anchor(self):
        marker = '<a id="independent-window-metadata--accepted-29-september-2026"></a>'
        self.assertTrue(any("duplicate explicit anchor" in x.message for x in self.effective_issues(
            "contracts/distribution-installation/native-setup.md", marker, marker + "\n" + marker)))

    def test_current_status_preserves_candidate_specific_setup_scope(self):
        for path in ("docs/architecture/current-implementation.md",
                     "docs/requirements/components/demo-orchestration.md"):
            with self.subTest(path=path):
                text = prose(path)
                self.assertIn("rc.2", text)
                self.assertIn("rc.3", text)
                self.assertIn("not inherited by rc.3", text)
                self.assertIn("current-baseline.md#qualified-current-profiles", text)
                self.assertNotIn("not new package/M1 qualification", text)
                self.assertNotIn("native/live activation remains open", text)

    def test_reproduction_evidence_is_not_a_second_build_procedure(self):
        guide = prose("docs/development/release-reproduction-r2.md")
        proof = prose("docs/qualification/developer-reproduction.md")
        self.assertIn("../qualification/developer-reproduction.md", guide)
        for campaign_detail in ("7412.094", "14,158,955,472", "r4-rc3-20261020"):
            self.assertNotIn(campaign_detail, guide)
            self.assertIn(campaign_detail, proof)
        self.assertIn("not fresh-macOS or cold-cache proof", proof)
        self.assertIn("not root-caused", proof)
        self.assertIn("option A selection were not overwritten or promoted", proof)
        self.assertIn("for this exact rebuilt media", proof)

    def test_native_setup_keeps_unique_runtime_provenance_without_old_campaign_diary(self):
        text = prose("docs/qualification/m1-clean-install-e2e-2026-10-14.md")
        self.assertIn("71063a5d05ce9287feb0964d661b8408343aa85a58b4c3baaed8c0fd14664270", text)
        self.assertIn("0f6216c8f300d5106e5ad80cc5ebe25682e397b7ae4174977055018477ffedb8", text)
        self.assertIn("blob/35dcdeb0cbd859f016148a505437b9b74886b261/", text)
        self.assertIn('id="corrected-immutable-candidate-complete-production-api-and-visible-ui-pass"', text)
        self.assertIn("not another current release or qualification of rc.3 bytes", text)
        self.assertNotIn("These are isolated correction branches", text)
        self.assertNotIn("separate subsequent release gates", text)

    def test_effective_gate_rejects_missing_explicit_test_timing_exception(self):
        path = "docs/requirements/components/factory-substrate.md"
        self.assertTrue(any("Safe Stop profiles" in x.message for x in self.effective_issues(
            path, "`demo-5s`", "`standard`")))

    def test_effective_gate_rejects_old_authority_and_publication_rules(self):
        for name, bad in (
            ("docs/requirements/d4-decision-register.md", "only after a future accepted state/model"),
            ("docs/requirements/d4-decision-register.md", "FOTA reconciliation searches the"),
            ("docs/requirements/d4-decision-register.md", "cannot select or use credentials bound"),
            ("docs/requirements/components/brake-health-service.md", "verify installed identity/capabilities"),
            ("docs/requirements/components/tire-health-cloud.md", "When that status reports `INCOMPATIBLE_VDP`"),
            ("docs/requirements/components/cross-cutting.md", "The normative presentation selects PU"),
        ):
            with self.subTest(rule=bad):
                documents = CHECK["markdown_documents"](ROOT)
                documents[(ROOT / name).resolve()] += "\n" + bad + "\n"
                self.assertTrue(any("superseded normative rule" in x.message
                                    for x in CHECK["check_effective_contracts"](ROOT, documents)))

    def test_brake_requested_quotas_match_actual_packaging_not_only_summary_presence(self):
        path = ROOT.parent / "brake-health-service/packaging/aos/config.yaml"
        if not path.is_file():
            self.skipTest("component checkout unavailable; root-only quota checks still run")
        profile = json.loads(read("contracts/brake-health-runtime/brake-health-runtime-profile.v1.json"))["aosRequestedQuotas"]
        for field in ("cpuLimit", "ramLimit", "storageLimit", "stateLimit", "tmpLimit", "noFileLimit", "pidsLimit"):
            match = re.search(r'^\s+' + field + r':\s*(\S+)\s*$', path.read_text(), re.M)
            self.assertIsNotNone(match, field)
            self.assertEqual(match[1], str(profile[field]), field)

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

    def test_active_contract_navigation_has_no_completed_relocation_or_stage_plan(self):
        reset = prose("contracts/qm-advisory-profile/readiness-and-reset.md")
        self.assertNotIn("relocation only", reset)
        self.assertNotIn("completed implementation work packet", reset)
        self.assertNotIn("changed by this move", reset)
        self.assertNotIn("The maintained contract", reset)
        self.assertIn("60-second execution deadline", reset)
        self.assertIn("command-expiry boundary remains 250 ms", reset)
        self.assertIn("Only a matching Gateway CLEARED result", reset)
        installation = prose("contracts/distribution-installation/README.md")
        self.assertIn("- Parent: [Integrated native Setup contract](native-setup.md#integrated-user-journey)", installation)
        self.assertIn("[ADR 0018]", installation)
        self.assertNotIn("Parent: [Stage 3]", installation)
        self.assertNotIn("installable-distribution-and-reproducibility.md", installation)

    def test_effective_gate_rejects_superseded_source_status_and_history(self):
        cases = (
            ("docs/requirements/d4-decision-register.md", "normative presentation uses PU"),
            ("docs/requirements/component-decomposition-and-interface-register.md",
             "Unmodified external executable"),
            ("docs/requirements/component-decomposition-and-interface-register.md",
             "fresh serial .39 qualification open"),
            ("docs/requirements/components/vehicle-gateway.md", "No implementation | `TARGET`"),
            ("docs/requirements/components/vehicle-gateway.md", "Candidate correction not started"),
            ("docs/requirements/components/brake-health-service.md", "implementation/qualification open"),
            ("docs/requirements/components/tire-health-service.md", "implementation and integration open"),
            ("docs/requirements/components/factory-substrate.md", "awaits prepared VDP artifacts"),
            ("docs/requirements/components/README.md", "legacy cleanup schema drift"),
            ("contracts/qm-advisory-profile/README.md", "Earlier 1.0.2 repinned the profile"),
            ("contracts/kuksa-current-demo-authorization/README.md", "implemented in Factory39"),
            ("contracts/distribution-installation/version-selection.md",
             "Native activation, installed live E2E, migration"),
        )
        for name, stale in cases:
            with self.subTest(path=name, stale=stale):
                documents = CHECK["markdown_documents"](ROOT)
                documents[(ROOT / name).resolve()] += "\n" + stale + "\n"
                issues = CHECK["check_effective_contracts"](ROOT, documents)
                self.assertTrue(any(x.path == name and "superseded normative rule" in x.message
                                    for x in issues), issues)

    def test_kuksa_owner_row_cannot_hide_patch_details_in_another_section(self):
        path = "docs/requirements/component-decomposition-and-interface-register.md"
        documents = CHECK["markdown_documents"](ROOT)
        source = (ROOT / path).resolve()
        row = next(line for line in documents[source].splitlines() if '<a id="cmp-kuksa">' in line)
        documents[source] = documents[source].replace(row, row.replace("scope-path", "authorization"))
        self.assertTrue(any("KUKSA source boundary" in x.message
                            for x in CHECK["check_effective_contracts"](ROOT, documents)))

    def test_timing_table_does_not_allow_an_unscoped_competing_rule(self):
        path = "contracts/platform-fota-safe-stop/README.md"
        documents = CHECK["markdown_documents"](ROOT)
        source = (ROOT / path).resolve()
        documents[source] += "\nEvery admitted sample must carry source time and be no older than 250 ms.\n"
        self.assertTrue(any(x.path == path and "superseded normative rule" in x.message
                            for x in CHECK["check_effective_contracts"](ROOT, documents)))

    def test_effective_profiles_reject_missing_test_timing_and_peer_applicability(self):
        cases = (
            ("contracts/platform-fota-safe-stop/README.md", "-5000 through +5000 ms", "0 through 250 ms"),
            ("contracts/vehicle-external-connectivity/README.md",
             "installed single-Test profile\nrequires no second VM", "installed profile requires a second VM"),
            ("contracts/vehicle-external-connectivity/README.md",
             "preservation of every existing peer VM", "preservation of the selected VM only"),
            ("contracts/vehicle-external-connectivity/README.md",
             "Expanded two-role acceptance starts", "Live acceptance starts"),
        )
        for path, old, new in cases:
            with self.subTest(path=path, old=old):
                issues = self.effective_issues(path, old, new)
                self.assertTrue(any("profile applicability" in x.message for x in issues), issues)

    def test_updated_status_distinguishes_source_from_full_acceptance(self):
        gateway = prose("docs/requirements/components/vehicle-gateway.md")
        brake = prose("docs/requirements/components/brake-health-service.md")
        factory = prose("docs/requirements/components/factory-substrate.md")
        selection = prose("contracts/distribution-installation/version-selection.md")
        for source in ("qm_advisory_test.cpp", "simulator_control_channel_test.cpp"):
            self.assertIn(source, gateway)
        for source in ("tests/cpp/v1/v1_tests.cpp", "tests/cpp/v2/v2_tests.cpp",
                       "tests/token_session_tests.cpp"):
            self.assertIn(source, brake)
        self.assertIn("complete chronology obligation remains open", gateway)
        self.assertIn("complete conformance, calibration and failure-matrix acceptance remain required", brake)
        self.assertIn("complete interruption/negative/recovery acceptance remains required", factory)
        self.assertIn("not blanket selection/recovery acceptance", selection)
        self.assertIn("destructive pruning/uninstall", selection)
        self.assertIn("not unfinished delivery phases", brake)
        for packet in ("BHS-CORE-001", "BHS-CORE-002", "BHS-CORE-003",
                       "BHS-ADAPTERS-001", "BHS-PACKAGING-001"):
            self.assertIn(packet, brake)

    def test_profile_applicability_keeps_timing_and_expanded_proofs_unchanged(self):
        timing = prose("contracts/platform-fota-safe-stop/README.md")
        connectivity = prose("contracts/vehicle-external-connectivity/README.md")
        self.assertLess(timing.index("## Effective timing profiles"),
                        timing.index("Every admitted sample must carry source time"))
        for term in ("twelve distinct coherent advancing frames", "unknown profile values are rejected",
                     "immediately before every destructive runtime operation"):
            self.assertIn(term, timing)
        for term in ("both VU and PU concurrently running", "two complete disconnect/ restore cycles for each role",
                     "an unchanged online peer VM", "Complete negative/recovery and expanded acceptance remain explicit gates"):
            self.assertIn(term, connectivity)
        decision = prose("docs/requirements/d4-decision-register.md")
        self.assertIn("installed presentation uses Test, expanded presentation uses PU", decision)
        self.assertIn("For expanded two-role acceptance, D4-022.4 requires two complete live", decision)

    def test_current_admin_summary_does_not_retire_compatibility_or_cpu_obligations(self):
        text = prose("docs/requirements/components/README.md")
        self.assertIn("separate current admin schemas describe the handler", text)
        self.assertIn("legacy fixtures remain compatibility inputs", text)
        self.assertIn("CPU control is not implemented", text)
        self.assertIn("formal calibration and CPU worker remain open", text)

    def test_current_product_links_precede_explicit_legacy_compatibility(self):
        for family in ("brake-telemetry-window", "brake-health-model", "tire-health-model", "brake-cloud-api"):
            with self.subTest(family=family):
                text = read("contracts/" + family + "/README.md")
                self.assertLess(text.index("## Current product messages"),
                                text.index("## Current and legacy product provenance"))
                self.assertIn("Only the original wire-provenance", text)
                self.assertNotIn("Earlier sections and v1 schema", prose("contracts/" + family + "/README.md"))
        model = read("contracts/brake-health-model/README.md")
        self.assertIn("Model/input/state schemas", model)
        self.assertIn("not an OCI artifact digest", prose("contracts/brake-health-model/README.md"))
        self.assertIn("Administrative/cleanup protocols are unaffected", model)

    def test_effective_gate_rejects_blanket_legacy_and_old_digest_rule(self):
        for family in ("brake-telemetry-window", "brake-health-model", "tire-health-model", "brake-cloud-api"):
            name = "contracts/" + family + "/README.md"
            for stale in ("Earlier sections and v1 schema files remain legacy evidence",
                          "`modelArtifactSha256` is the immutable deployed artifact digest"):
                with self.subTest(family=family, stale=stale):
                    documents = CHECK["markdown_documents"](ROOT)
                    documents[(ROOT / name).resolve()] += "\n" + stale
                    self.assertTrue(any(x.path == name and "legacy scope" in x.message
                                        for x in CHECK["check_effective_contracts"](ROOT, documents)))

    def test_effective_gate_rejects_a_legacy_schema_as_current_product_link(self):
        for family, schema in (("brake-health-model", "brake-health-assessment"),
                               ("brake-telemetry-window", "brake-telemetry-window-chunk"),
                               ("tire-health-model", "tire-health-assessment"),
                               ("brake-cloud-api", "query-page")):
            with self.subTest(family=family):
                issues = self.effective_issues("contracts/" + family + "/README.md",
                                              "(" + schema + ".v2.schema.json)", "(" + schema + ".schema.json)")
                self.assertTrue(any("current product provenance" in x.message for x in issues), issues)

    def test_empty_store_summary_preserves_current_and_compatible_proof_shapes(self):
        import ast
        text = prose("contracts/service-runtime-inputs/product-message-migration.md")
        path = ROOT / "apps/demo-orchestrator/src/aosedge_demo_orchestrator/backend_retirement.py"
        assignments = [n for n in ast.walk(ast.parse(path.read_text())) if isinstance(n, ast.Assign)
                       and any(isinstance(t, ast.Name) and t.id == "supported_schema_versions" for t in n.targets)]
        self.assertEqual(len(assignments), 1)
        branch = assignments[0].value
        self.assertIsInstance(branch, ast.IfExp)
        for team, values in (("Brake", ast.literal_eval(branch.body)),
                             ("Tire", ast.literal_eval(branch.orelse))):
            self.assertIn(team + " " + "/".join(map(str, values)), text)
            profile = json.loads(read("contracts/" + team.lower() + "-cloud-api/current-admin-profile.v1.json"))
            self.assertEqual(profile["databaseSchemaVersion"], values[-1])
        for counter in ("resetProducers", "resetCommands", "functionObservations", "functionObservationConflicts"):
            self.assertIn(counter, text)
        self.assertIn("schema match alone never authorizes deletion", text)
        issues = self.effective_issues("contracts/service-runtime-inputs/product-message-migration.md",
                                      "Brake database schema 5 and Tire schema 4", "Brake database 2/3 and Tire 2")
        self.assertTrue(any("empty-store summary" in x.message for x in issues), issues)

    def test_portable_contracts_use_current_parents_not_a_retired_stage_plan(self):
        for family in ("portable-host-launch", "portable-vm-launch", "portable-cloud-backend-inputs",
                       "portable-preparation-inputs"):
            with self.subTest(family=family):
                name = "contracts/" + family + "/README.md"
                text = read(name)
                self.assertNotIn("installable-distribution-and-reproducibility.md", text)
                issues = self.effective_issues(name, "- Parent: [Integrated native Setup contract]",
                                              "- Parent: [distribution plan, Stage 2]")
                self.assertTrue(any("portable-input parent" in x.message for x in issues), issues)

    def test_host_contract_separates_installed_trust_from_developer_tls(self):
        text = prose("contracts/portable-host-launch/README.md")
        for fact in ("Installed mode uses", "explicit Start simulator action", "Installation and read-only status",
                     "do not generate trust", "Developer mode retains", "not an installed first-use prerequisite or fallback",
                     "input selection alone does not qualify installation"):
            self.assertIn(fact, text)
        issues = self.effective_issues("contracts/portable-host-launch/README.md",
                                      "Installed mode", "First-use credential setup is a later installation contract. Installed mode")
        self.assertTrue(any("sequential Stage-2 framing" in x.message for x in issues), issues)


if __name__ == "__main__":
    unittest.main()
