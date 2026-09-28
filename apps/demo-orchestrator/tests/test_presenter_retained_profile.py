# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import copy
import json
import tempfile
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from aosedge_demo_orchestrator import presenter
from aosedge_demo_orchestrator.component_profile import InstalledProfileResolver
from aosedge_demo_orchestrator.components import ComponentService, COMPONENT
from aosedge_demo_orchestrator.environment import JOURNAL


class RetainedProfileTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.environment = SimpleNamespace(root=self.root, catalog=SimpleNamespace(project=self.root))
        self.components = ComponentService(self.environment)
        self.application = SimpleNamespace(environment_service=self.environment)
        self.owner = "11111111-1111-4111-8111-111111111111"
        self.journal = dict(cloudBinding=dict(ownerId=self.owner), vehicles=dict(test=dict(
            localVmId="new-run", unitId="unit", systemUid="native")))
        self.journal_path = self.root / JOURNAL
        self.journal_path.parent.mkdir(parents=True)
        self.journal_path.write_text(json.dumps(self.journal))
        self.original_journal = self.journal_path.read_bytes()
        self.record = dict(ownerId=self.owner, cloudDomain="aoscloud.io", deploymentId="bundle",
            prepare=dict(state="COMPLETED", contentProfile="v3", sha256="a" * 64), preparedSha256="a" * 64,
            signed=dict(state="COMPLETED", cloudDomain="aoscloud.io", sha256="b" * 64), sha256="b" * 64,
            upload=dict(state="RESPONDED", response=dict(httpStatus=201, deploymentId="bundle")),
            publication=dict(stage="READY", versionId="old-observation-is-not-authority"))
        self.receipt = self.components._publication_path("117.0.0", self.journal, create=True)
        self.save_receipt()
        self.bundle = self.components._directory("117.0.0") / "aosedge-vdp-component-117.0.0-linux-arm64.unsigned.tar.gz"
        self.bundle.write_bytes(b"fixture")
        self.components.inspect = Mock(return_value=dict(version="117.0.0", problems=[],
            contentProfile="v3", unsignedBundleSha256="a" * 64))
        self.inventory = dict(unitId="unit", systemUid="native",
            unit=dict(state="CURRENT", value=dict(oem=self.owner, connectivity="ONLINE")),
            components=dict(state="CURRENT", value=[dict(type=COMPONENT,
                installed_component=dict(version="117.0.0", id="installed-uuid"),
                pending_component=dict(version="118.0.0", id="pending-uuid"))]))
        self.publication = dict(stage="READY", deploymentId="bundle", versionId="installed-uuid")
        self.calls = []
        self.reader = self.make_reader()

    def save_receipt(self):
        self.receipt.write_text(json.dumps(self.record))

    def make_reader(self):
        with patch("aosedge_demo_orchestrator.application.DemoOrchestrator", return_value=self.application):
            reader = presenter.StudioCloudReader()
        reader.profile_resolver = InstalledProfileResolver(lambda: self.components)
        self.addCleanup(reader.pool.shutdown)
        return reader

    def execute(self, request, application):
        self.calls.append(request)
        key = request["domain"], request["action"]
        if key == ("service", "releases"):
            return dict(state="OBSERVED", data=dict(releases=[]))
        if key == ("unit", "cloud-status"):
            return dict(data=copy.deepcopy(self.inventory))
        self.assertEqual(("component", "cloud-status"), key)
        self.assertEqual("117.0.0", request["component_version"])
        return dict(data=dict(publication=self.publication))

    def read(self, reader=None):
        with patch.object(presenter, "execute_operation", side_effect=self.execute):
            return (reader or self.reader)()

    def reconcile(self, reader=None):
        reader = reader or self.reader
        self.read(reader)
        result = self.read(reader)
        if "component" in reader.publication_reads:
            reader.publication_reads["component"][1].result(timeout=1)
            result = self.read(reader)
        return result

    def test_retained_publication_binds_after_inventory_without_journal_write(self):
        first = self.read()
        self.assertIsNone(first["value"]["installedProfile"]["profile"])
        self.assertFalse(any(call["domain"] == "component" for call in self.calls))
        result = self.reconcile()
        profile = result["value"]["installedProfile"]
        self.assertEqual(("CURRENT", "v3", "117.0.0"),
                         (profile["state"], profile["profile"], profile["releaseVersion"]))
        self.assertEqual(profile, result["value"]["inventory"]["components"]["value"][0]["installedProfile"])
        self.assertEqual(self.original_journal, self.journal_path.read_bytes())
        self.components.inspect.assert_called_once_with("117.0.0")
        self.read()
        self.assertEqual(1, sum(call["domain"] == "component" for call in self.calls))

    def test_restart_reconstructs_binding_and_rereads_publication(self):
        self.assertEqual("v3", self.reconcile()["value"]["installedProfile"]["profile"])
        self.assertEqual("v3", self.reconcile(self.make_reader())["value"]["installedProfile"]["profile"])
        self.assertEqual(2, sum(call["domain"] == "component" for call in self.calls))

    def test_saved_ready_without_fresh_matching_cloud_publication_is_not_enough(self):
        self.publication["versionId"] = "pending-uuid"
        self.assertIsNone(self.reconcile()["value"]["installedProfile"]["profile"])
        self.components.inspect.assert_not_called()

    def test_unreadable_malformed_or_wrong_scope_receipt_preserves_inventory(self):
        for value in ("{broken", "[]", json.dumps(dict(self.record, ownerId="other")),
                      json.dumps(dict(self.record, cloudDomain="other.example.com"))):
            with self.subTest(value=value):
                self.receipt.write_text(value)
                result = self.reconcile(self.make_reader())
                self.assertEqual("ONLINE", result["value"]["online"])
                self.assertEqual("117.0.0", result["value"]["installedVersion"])
                self.assertIsNone(result["value"]["installedProfile"]["profile"])
        self.receipt.unlink()
        self.assertIsNone(self.reconcile(self.make_reader())["value"]["installedProfile"]["profile"])
        self.assertFalse(any(call["domain"] == "component" for call in self.calls))

    def test_changed_artifact_or_removed_receipt_invalidates_bound_profile(self):
        self.assertEqual("v3", self.reconcile()["value"]["installedProfile"]["profile"])
        self.bundle.write_bytes(b"different fixture")
        self.components.inspect.return_value["unsignedBundleSha256"] = "c" * 64
        self.assertIsNone(self.read()["value"]["installedProfile"]["profile"])
        self.receipt.unlink()
        self.assertIsNone(self.read()["value"]["installedProfile"]["profile"])

    def test_wrong_unit_or_changed_installed_uuid_does_not_reuse_binding(self):
        self.assertEqual("v3", self.reconcile()["value"]["installedProfile"]["profile"])
        self.inventory["components"]["value"][0]["installed_component"]["id"] = "replacement-uuid"
        self.assertIsNone(self.read()["value"]["installedProfile"]["profile"])
        self.inventory["unitId"] = "other-unit"
        self.assertIsNone(self.read()["value"]["installedProfile"]["profile"])

    def test_receipt_symlink_is_not_followed(self):
        self.receipt.rename(self.receipt.with_suffix(".old"))
        self.receipt.symlink_to(self.receipt.with_suffix(".old"))
        self.assertIsNone(self.reconcile()["value"]["installedProfile"]["profile"])
        self.assertFalse(any(call["domain"] == "component" for call in self.calls))

    def test_absent_installation_never_scans_retained_catalog(self):
        self.inventory["components"]["value"] = []
        with patch.object(self.components, "_publication_record", wraps=self.components._publication_record) as read:
            self.reconcile()
            read.assert_not_called()

    def test_slow_retained_publication_does_not_block_or_duplicate_inventory(self):
        self.read()
        released = threading.Event()
        self.addCleanup(released.set)
        original = self.execute
        def execute(request, application):
            if request["domain"] == "component":
                released.wait(2)
            return original(request, application)
        with patch.object(presenter, "execute_operation", side_effect=execute):
            first = self.reader()
            self.assertEqual("ONLINE", first["value"]["online"])
            self.assertIsNone(first["value"]["installedProfile"]["profile"])
            future = self.reader.publication_reads["component"][1]
            self.reader()
            self.assertIs(future, self.reader.publication_reads["component"][1])
            released.set()
            future.result(timeout=1)
            self.assertEqual("v3", self.reader()["value"]["installedProfile"]["profile"])
        self.assertEqual(1, sum(call["domain"] == "component" for call in self.calls))

    def test_changed_cloud_context_discards_retained_hint_and_cache(self):
        self.assertEqual("v3", self.reconcile()["value"]["installedProfile"]["profile"])
        self.journal["selectedCloudDomain"] = "other.example.com"
        self.journal_path.write_text(json.dumps(self.journal))
        self.assertIsNone(self.reconcile()["value"]["installedProfile"]["profile"])
        self.assertEqual({}, self.reader.publications)
        self.assertEqual(1, sum(call["domain"] == "component" for call in self.calls))

    def test_offline_inventory_is_not_confused_with_stale_installation(self):
        self.inventory["unit"]["value"]["connectivity"] = "OFFLINE"
        self.assertEqual("CURRENT", self.reconcile()["value"]["installedProfile"]["state"])
        self.inventory["components"]["state"] = "STALE"
        profile = self.read()["value"]["installedProfile"]
        self.assertEqual(("STALE", "v3"), (profile["state"], profile["profile"]))


if __name__ == "__main__":
    unittest.main()
