# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Exact approved assets/examples must not become general publication bypasses."""

import hashlib
import json
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
GUARD = runpy.run_path(str(ROOT / "scripts/qualify-repository-boundaries"))
SCAN = GUARD["_scan_public_source"]
ERROR = GUARD["QualificationError"]
LOCAL = "http://" + "10.0.0.1"
ICON = "apps/presenter-ui/src/assets/icons/image1.png"


class PublicSourceGuardTests(unittest.TestCase):
    def scan(self, content, relative="example.txt", repository="aosedge-sdv-demo", symlink=False):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / repository
            path = root / relative
            path.parent.mkdir(parents=True)
            if symlink:
                original = Path(directory) / "original.png"
                original.write_bytes(content)
                path.symlink_to(original)
            else:
                path.write_bytes(content)
            with patch.dict(SCAN.__globals__, _tracked_files=lambda unused: [path]):
                SCAN(root)

    def test_reviewed_inventory_matches_all_57_existing_visual_files(self):
        entries = GUARD["_visual_assets"](ROOT)
        self.assertEqual(len(entries), 57)
        for name, digest in entries.items():
            with self.subTest(name=name):
                self.assertEqual(hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), digest)

    def test_exact_existing_visual_passes(self):
        self.scan((ROOT / ICON).read_bytes(), ICON)

    def test_changed_visual_is_rejected(self):
        with self.assertRaisesRegex(ERROR, "visual content changed"):
            self.scan((ROOT / ICON).read_bytes() + b"modified", ICON)

    def test_copied_visual_at_unreviewed_path_is_rejected(self):
        with self.assertRaisesRegex(ERROR, "binary content"):
            self.scan((ROOT / ICON).read_bytes(), "docs/new.png")

    def test_visual_exception_is_not_shared_with_other_repositories(self):
        with self.assertRaisesRegex(ERROR, "binary content"):
            self.scan((ROOT / ICON).read_bytes(), ICON, "brake-health-service")

    def test_visual_symlink_is_rejected(self):
        with self.assertRaisesRegex(ERROR, "visual content changed"):
            self.scan((ROOT / ICON).read_bytes(), ICON, symlink=True)

    def test_only_exact_existing_url_and_file_pairs_pass(self):
        for (repository, relative), urls in GUARD["PUBLIC_QEMU_EXAMPLES"].items():
            for url in urls:
                with self.subTest(repository=repository, file=relative, url=url):
                    self.scan(url.encode(), relative, repository)

    def test_same_host_other_file_or_port_or_path_is_rejected(self):
        contract = "contracts/local-demo-hosting/local-demo-hosting-profile.v1.json"
        for url, relative in [(LOCAL + ":18091/api/v1/brake/messages", "new.md"),
                              (LOCAL + ":18093/api/v1/brake/messages", contract),
                              (LOCAL + ":18091/private", contract),
                              (LOCAL + ":18091/api/v1/brake/messages?token=value", contract)]:
            with self.subTest(url=url, file=relative), self.assertRaisesRegex(ERROR, "private URL"):
                self.scan(url.encode(), relative)

    def test_unrelated_private_urls_remain_rejected(self):
        for host in ("192.168.1.2", "172.16.2.3", "10.0.0.2", "internal.corp"):
            with self.subTest(host=host), self.assertRaisesRegex(ERROR, "private URL"):
                self.scan(("https://" + host + "/api").encode())

    def test_credentials_and_prohibited_files_stay_rejected(self):
        fixtures = [b"-----BEGIN " + b"PRIVATE KEY-----", b"AK" + b"IA" + b"A" * 16,
                    b"api" + b"Token='" + b"test" * 4 + b"'"]
        for value in fixtures:
            with self.subTest(value=value[:4]), self.assertRaisesRegex(ERROR, "possible credential"):
                self.scan(value)
        for name in ("secret.pem", "image.qcow2", "source.uasset"):
            with self.subTest(name=name), self.assertRaisesRegex(ERROR, "prohibited"):
                self.scan(b"text", name)

    def test_allowlisted_document_still_has_secret_checks(self):
        with self.assertRaisesRegex(ERROR, "possible credential"):
            self.scan((LOCAL + ":18091/...\n").encode() + b"-----BEGIN " + b"PRIVATE KEY-----",
                      "docs/requirements/d4-decision-register.md")

    def test_malformed_asset_inventory_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "inventory.json"
            for value in ({"schemaVersion": 1, "files": {}}, {"schemaVersion": 2}):
                path.write_text(json.dumps(value))
                with patch.dict(GUARD["_visual_assets"].__globals__, VISUAL_MANIFEST=path):
                    with self.assertRaises(ERROR):
                        GUARD["_visual_assets"](ROOT)


if __name__ == "__main__":
    unittest.main()
