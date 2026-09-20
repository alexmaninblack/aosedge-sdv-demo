# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from aosedge_demo_orchestrator.component_profile import InstalledProfileResolver


class InstalledProfileTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / "bundle"
        self.path.write_bytes(b"fixture")
        self.component = Mock()
        self.component._bundle.return_value = self.path
        self.component.inspect.return_value = dict(version="79.0.0", problems=[], contentProfile="v3", unsignedBundleSha256="a" * 64)
        self.resolver = InstalledProfileResolver(lambda: self.component)
        self.record = dict(ownerId="owner", cloudDomain="aoscloud.io", deploymentId="bundle",
            prepare=dict(state="COMPLETED", contentProfile="v3", sha256="a" * 64), preparedSha256="a" * 64,
            signed=dict(state="COMPLETED", cloudDomain="aoscloud.io", sha256="b" * 64), sha256="b" * 64,
            upload=dict(state="RESPONDED", response=dict(httpStatus=201, deploymentId="bundle")))
        self.journal = dict(cloudBinding=dict(ownerId="owner"), vehicles=dict(test=dict(unitId="unit", systemUid="native")),
            componentOperations={"79.0.0": self.record})
        self.inventory = dict(unitId="unit", systemUid="native", unit=dict(state="CURRENT", value=dict(oem="owner", connectivity="ONLINE")),
            components=dict(state="CURRENT"))
        self.row = dict(installed_component=dict(id="version-uuid", version="79.0.0"))
        self.publications = {("79.0.0", "bundle"): dict(stage="READY", deploymentId="bundle", versionId="version-uuid")}

    def resolve(self):
        return self.resolver.resolve(self.journal, self.inventory, self.row, self.publications)

    def test_exact_publication_and_inspected_package_bind_profile(self):
        self.assertEqual("v3", self.resolve()["profile"])
        self.assertEqual("CURRENT", self.resolve()["state"])
        self.component.inspect.assert_called_once_with("79.0.0")
        self.assertNotIn("sha256", self.resolve())

    def test_bundle_change_invalidates_inspection_cache(self):
        self.resolve()
        self.path.write_bytes(b"changed bundle")
        self.component.inspect.return_value["unsignedBundleSha256"] = "c" * 64
        self.assertEqual("UNKNOWN", self.resolve()["state"])
        self.assertEqual(2, self.component.inspect.call_count)

    def test_wrong_cloud_owner_unit_and_publication_cannot_reuse_profile(self):
        self.resolve()
        for field, value in (("ownerId", "other"), ("cloudDomain", "stage.example.com"), ("deploymentId", "other")):
            with self.subTest(field=field):
                original = self.record[field]; self.record[field] = value
                self.assertIsNone(self.resolve()["profile"])
                self.record[field] = original
        for field in ("unitId", "systemUid"):
            original = self.inventory[field]; self.inventory[field] = "other"
            self.assertIsNone(self.resolve()["profile"])
            self.inventory[field] = original
        self.inventory["unit"]["value"]["oem"] = "other"
        self.assertIsNone(self.resolve()["profile"])

    def test_pending_same_number_wrong_uuid_or_unconfirmed_publication_is_unknown(self):
        for stage, identifier in (("PROCESSING", "version-uuid"), ("READY", "pending-uuid"), ("ERROR", "version-uuid")):
            with self.subTest(stage=stage, identifier=identifier):
                self.publications[("79.0.0", "bundle")].update(stage=stage, versionId=identifier)
                self.assertIsNone(self.resolve()["profile"])
        self.component.inspect.assert_not_called()

    def test_artifact_and_receipts_must_agree(self):
        original = copy.deepcopy(self.record)
        for mutation in (lambda r:r["prepare"].update(contentProfile="v2"),
                         lambda r:r["prepare"].update(sha256="c" * 64),
                         lambda r:r["upload"].update(state="UNCERTAIN"),
                         lambda r:r["signed"].update(sha256="c" * 64)):
            self.record.clear(); self.record.update(copy.deepcopy(original)); mutation(self.record)
            self.assertIsNone(self.resolve()["profile"])

    def test_missing_or_invalid_package_never_guesses_profile_from_major(self):
        self.component.inspect.return_value["problems"] = ["bad manifest"]
        self.assertIsNone(self.resolve()["profile"])
        self.path.unlink()
        self.assertIsNone(self.resolve()["profile"])

    def test_stale_installation_and_offline_keep_separate_meanings(self):
        self.inventory["unit"]["value"]["connectivity"] = "OFFLINE"
        self.assertEqual("CURRENT", self.resolve()["state"])
        self.inventory["components"]["state"] = "STALE"
        result = self.resolve()
        self.assertEqual("STALE", result["state"])
        self.assertEqual("v3", result["profile"])

    def test_absent_installation_or_missing_receipt_does_not_scan_artifacts(self):
        self.row["installed_component"] = None
        self.assertIsNone(self.resolve()["profile"])
        self.component.inspect.assert_not_called()
