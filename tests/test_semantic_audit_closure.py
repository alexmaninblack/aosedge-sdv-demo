# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""In-memory negative regressions for the consolidated documentation correction."""
from pathlib import Path
import re
import runpy
import unittest

ROOT = Path(__file__).resolve().parents[1]
CHECK = runpy.run_path(str(ROOT / "scripts/docs-check"))


class SemanticAuditClosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.documents = CHECK["markdown_documents"](ROOT)

    def altered(self, name, old, new):
        documents = dict(self.documents)
        path = (ROOT / name).resolve()
        self.assertIn(old, documents[path])
        documents[path] = documents[path].replace(old, new, 1)
        return documents

    def test_current_metadata_and_effective_contracts_pass(self):
        self.assertEqual([], CHECK["check_metadata"](ROOT, self.documents))
        self.assertEqual([], CHECK["check_effective_contracts"](ROOT, self.documents))

    def test_markdown_contract_versions_are_checked_like_document_versions(self):
        for name, old, new in (
            ("docs/requirements/components/demo-orchestration.md", "[Demo Run State, Overlays and Cleanup]", "[Demo Run State, Overlays and Cleanup 1.2.0]"),
            ("docs/requirements/d4-decision-register.md", "[Tire Health In-Vehicle Product Contract]", "[Tire Health In-Vehicle Product Contract 1.0.0]"),
            ("docs/requirements/d4-decision-register.md", "[Shared Evidence, Correlation and Chronology]", "[Shared Evidence, Correlation and Chronology 1.0.0]"),
        ):
            with self.subTest(name=name, label=new):
                issues = CHECK["check_metadata"](ROOT, self.altered(name, old, new))
                self.assertTrue(any("versioned document link label is stale" in issue.message for issue in issues))

    def test_ingestion_summary_cannot_reintroduce_client_authentication_claim(self):
        for name, old, new in (
            ("brake-health-service", "Isolated local transport", "Versioned authenticated endpoint"),
            ("tire-health-service", "Isolated local transport", "Authenticated bounded summary/event schemas"),
            ("brake-health-cloud", "isolate VM ingestion", "authenticate VM ingestion"),
            ("brake-health-cloud", "isolated ingestion/correlation and authenticated helper", "ingestion/helper authentication"),
        ):
            with self.subTest(name=name, old=old):
                issues = CHECK["check_effective_contracts"](ROOT, self.altered("docs/requirements/components/" + name + ".md", old, new))
                self.assertTrue(any("superseded normative rule" in issue.message for issue in issues))

    def test_applicability_must_be_local_to_each_lifecycle_statement(self):
        path = (ROOT / "docs/requirements/components/aos-lifecycle.md").resolve()
        for number in ("001", "003", "005", "006", "015", "016"):
            with self.subTest(number=number):
                documents = dict(self.documents)
                pattern = r'(- ID: `REQ-AOS-' + number + r'`\n- Statement: )([^\n]+)'
                documents[path], count = re.subn(pattern, lambda m: m[1] + re.sub(r"(?i)installed|expanded", "unscoped", m[2]), documents[path])
                self.assertEqual(1, count)
                issues = CHECK["check_effective_contracts"](ROOT, documents)
                self.assertTrue(any("REQ-AOS-" + number in issue.message for issue in issues))

    def test_shared_evidence_requires_native_identity_and_independent_observation_generation(self):
        name = "contracts/shared-evidence-correlation/README.md"
        for old, new in (("native instance identity", "Service version/digest"),
                         ("separate persisted positive generation", "shared advisory epoch")):
            with self.subTest(old=old):
                issues = CHECK["check_effective_contracts"](ROOT, self.altered(name, old, new))
                self.assertTrue(any("shared evidence must distinguish" in issue.message for issue in issues))

    def test_resource_scope_is_not_a_staging_candidate_or_old_requirement_revision(self):
        for name, old, new in (
            ("contracts/service-tenant-quota-proof/README.md", "600 DMIPS |", "600 DMIPS (staging requalification candidate) |"),
            ("docs/requirements/components/tire-health-cloud.md", "the current [in-vehicle resource envelope]", "the accepted CR-TIRE 0.2 in-vehicle resource envelope"),
        ):
            with self.subTest(name=name):
                issues = CHECK["check_effective_contracts"](ROOT, self.altered(name, old, new))
                self.assertTrue(any("superseded normative rule" in issue.message for issue in issues))


if __name__ == "__main__":
    unittest.main()
