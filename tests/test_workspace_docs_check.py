# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Workspace documentation regressions: small Git fixtures, no build/network/runtime."""
import json
from pathlib import Path
import runpy
import subprocess
import tempfile
import unittest
from unittest.mock import MagicMock, patch
import urllib.error

ROOT = Path(__file__).resolve().parents[1]
CHECK = runpy.run_path(str(ROOT / "scripts/docs-check"))
CHECK_WORKSPACE = CHECK["check_workspace"]
CHECK_GUIDANCE = CHECK["check_current_guidance"]
LINKS = CHECK["markdown_links"]
URL = "https://github.com/alexmaninblack/carla-ego-runtime/blob/"


class WorkspaceDocumentationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.root = self.base / "aosedge-sdv-demo"
        self.component = self.base / "carla-ego-runtime"
        for repo in (self.root, self.component):
            repo.mkdir()
            subprocess.run(["git", "init", "--quiet", "--initial-branch=main", str(repo)],
                           check=True, capture_output=True)
        (self.root / "workspace").mkdir()
        (self.root / "workspace/repositories.json").write_text(json.dumps({
            "repositories": [{"directory": "carla-ego-runtime", "repository":
                "https://github.com/alexmaninblack/carla-ego-runtime.git",
                "acceptedRevision": "1" * 40}]}))
        (self.root / "README.md").write_text("# Lab\n\n[Gateway](" + URL + "main/README.md)\n")
        (self.component / "README.md").write_text("# Gateway\n\n## Interface\n")

    def result(self):
        # The offline scenario must never fetch a link or launch product code.
        with patch("urllib.request.urlopen", side_effect=AssertionError("unexpected network")):
            return CHECK_WORKSPACE(self.root)

    def messages(self):
        return "\n".join(issue.render() for issue in self.result()[0])

    def test_contract_version_labels_are_validated_across_repository_links(self):
        (self.component / "README.md").write_text("# Gateway\n\n- Contract version: `1.2.3`\n")
        entry = self.root / "README.md"
        entry.write_text("# Lab\n\n[Gateway 1.0.0](" + URL + "main/README.md)\n")
        self.assertIn("versioned document link label is stale", self.messages())
        entry.write_text("# Lab\n\n[Gateway 1.2.3](" + URL + "main/README.md)\n")
        self.assertNotIn("versioned document link label is stale", self.messages())

    def commit_component(self):
        subprocess.run(["git", "-C", str(self.component), "add", "README.md"], check=True)
        # Disposable documentation objects must not invoke the host's signing
        # key/agent. This does not change signing for any real repository.
        subprocess.run(["git", "-C", str(self.component), "-c", "user.name=Documentation Fixture",
                        "-c", "user.email=fixture@example.invalid", "-c", "commit.gpgsign=false",
                        "commit", "--quiet", "-m", "Fixture"],
                       check=True, capture_output=True)
        return subprocess.check_output(["git", "-C", str(self.component), "rev-parse", "HEAD"]).decode().strip()

    def test_review_history_is_evidence_not_a_current_specification(self):
        body = "# Review\n\n## Review Record for Version 0.12\n\nRecorded evidence.\n"
        evidence = self.root / "docs/qualification/transport-evidence.md"
        specification = self.root / "contracts/transport/README.md"
        self.assertEqual(CHECK_GUIDANCE(self.root, {evidence: body}), [])
        issues = CHECK_GUIDANCE(self.root, {specification: body})
        self.assertEqual(len(issues), 1)
        self.assertIn("completed version-review diaries", issues[0].message)

    def test_current_hosted_readmes_are_inspected_offline(self):
        issues, count, _ = self.result()
        self.assertEqual(issues, [])
        self.assertEqual(count, 2)

    def test_nested_component_sibling_link_is_rejected(self):
        with (self.component / "README.md").open("a") as stream:
            stream.write("\n[Lab](../aosedge-sdv-demo/README.md)\n")
        self.assertIn("GitHub-unsafe sibling link", self.messages())

    def test_old_pinned_readme_is_not_current_component_navigation(self):
        revision = self.commit_component()
        (self.root / "README.md").write_text("[Old README](" + URL + revision + "/README.md)\n")
        self.assertIn("current component README navigation must use main", self.messages())

    def test_missing_current_hosted_target_and_anchor_are_rejected(self):
        for suffix, message in (("missing.md", "missing workspace link target"),
                                ("README.md#missing", "missing workspace anchor")):
            with self.subTest(suffix=suffix):
                (self.root / "README.md").write_text("[Bad](" + URL + "main/" + suffix + ")\n")
                self.assertIn(message, self.messages())

    def test_immutable_source_citation_requires_the_exact_git_object(self):
        revision = self.commit_component()
        # A later worktree edit does not alter the immutable source citation.
        (self.component / "README.md").write_text("# Current Gateway\n")
        (self.root / "README.md").write_text("[Exact source](" + URL + revision + "/README.md#interface)\n")
        messages = self.messages()
        self.assertNotIn("missing immutable Git", messages)
        self.assertIn("current component README navigation", messages)
        (self.root / "README.md").write_text("[Missing](" + URL + "0" * 40 + "/docs/spec.md)\n")
        self.assertIn("missing immutable Git target", self.messages())

    def test_directory_without_readme_is_a_valid_navigation_target(self):
        (self.component / "docs").mkdir()
        (self.root / "README.md").write_text("[Directory](" + URL.replace("/blob/", "/tree/") + "main/docs)\n")
        self.assertEqual(self.messages(), "")

    def test_nested_and_nonstandard_tracked_markdown_is_scanned(self):
        nested = self.component / "packaging/reference/README.md"
        nested.parent.mkdir(parents=True)
        nested.write_text("# Package\n\n[Broken](absent.md)\n")
        self.assertIn("missing workspace link target: absent.md", self.messages())
        self.assertEqual(self.result()[1], 3)

    def test_secondary_document_version_is_checked(self):
        (self.component / "README.md").write_text("# Gateway\n\n- Version: 0.18\n")
        (self.root / "README.md").write_text("[Register 0.17](" + URL + "main/README.md)\n")
        self.assertIn("versioned document link label is stale", self.messages())

    def test_product_versions_and_decision_ids_are_not_document_versions(self):
        versions = CHECK["named_document_versions"]
        self.assertEqual(versions("D4-026.17"), [])
        self.assertEqual(versions("Complete v1.0 metadata (REQ-TIRE-001)", "req-tire-001"), [])
        self.assertEqual(versions("Register 0.17"), ["0.17"])
        self.assertEqual(versions("Contract 1.2.3"), ["1.2.3"])

    def test_unsafe_hosted_refs_are_rejected(self):
        for suffix in ("unreviewed/README.md", "main/../README.md", "main/README.md?raw=1"):
            with self.subTest(suffix=suffix):
                (self.root / "README.md").write_text("[Bad](" + URL + suffix + ")\n")
                self.assertIn("unsafe hosted workspace reference", self.messages())

    def test_reference_style_and_html_links_are_checked(self):
        for text in ("[Docs][spec]\n\n[spec]: missing.md\n",
                     '<a href="missing.md">Docs</a>\n',
                     "![Image](missing.png)\n", "[Docs][undefined]\n"):
            with self.subTest(text=text):
                (self.root / "README.md").write_text(text)
                self.assertIn("missing workspace link target", self.messages())

    def test_fenced_markdown_examples_are_not_navigation(self):
        text = "```markdown\n[Example](missing.md)\n```\n[Real](README.md)\n"
        self.assertEqual(LINKS(text), [("Real", "README.md")])

    def test_known_superseded_guidance_is_rejected(self):
        vectors = ((self.root / "docs/operations/aosvm-apple-silicon.md",
                    "To reproduce the larger SDV demo,\ncomplete this guide first", "not an SDV Lab prerequisite"),
                   (self.root / "docs/demo/README.md", "The HTML mockups are design/test fixtures", "retired HTML"),
                   (self.component / "README.md", 'export TMPDIR="$SDV_VOLUME/tmp"', "superseded storage"))
        for path, text, expected in vectors:
            with self.subTest(expected=expected):
                messages = [issue.message for issue in CHECK_GUIDANCE(self.root, {path: text})]
                self.assertTrue(any(expected in message for message in messages), messages)

    def test_engine_checkouts_are_not_required_by_documentation_scope(self):
        manifest = self.root / "workspace/repositories.json"
        data = json.loads(manifest.read_text())
        for name in ("CarlaSim", "UnrealEngine5_carla"):
            data["repositories"].append({"directory": name, "repository": "https://github.com/example/engine"})
        manifest.write_text(json.dumps(data))
        self.assertEqual(self.messages(), "")


class ExternalDocumentationProbeTests(unittest.TestCase):
    def test_head_rejection_uses_only_a_bounded_get_prefix(self):
        response = MagicMock()
        response.status = 206
        response.__enter__.return_value = response
        requests = []
        def open_request(request, timeout):
            requests.append(request)
            if request.method == "HEAD":
                raise urllib.error.HTTPError(request.full_url, 404, "HEAD unavailable", {}, None)
            return response
        with patch("urllib.request.urlopen", side_effect=open_request):
            self.assertEqual(CHECK["check_external_links"]({"https://example.invalid/document"}), [])
        self.assertEqual([request.method for request in requests], ["HEAD", "GET"])
        self.assertEqual(requests[1].get_header("Range"), "bytes=0-1023")
        response.read.assert_called_once_with(1024)

    def test_access_denial_is_reported_not_bypassed(self):
        with patch("urllib.request.urlopen", side_effect=urllib.error.HTTPError(
                "https://example.invalid/document", 403, "Denied", {}, None)):
            issues = CHECK["check_external_links"]({"https://example.invalid/document"})
        self.assertEqual([issue.message for issue in issues], ["HTTP 403"])


if __name__ == "__main__":
    unittest.main()
