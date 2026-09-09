# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import json
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from aosedge_demo_orchestrator.api import execute_operation
from aosedge_demo_orchestrator.application import DemoOrchestrator
from aosedge_demo_orchestrator.cli import build_parser, request_from_arguments
from aosedge_demo_orchestrator.environment import EnvironmentError, EnvironmentService, JOURNAL, digest, atomic_json
from aosedge_demo_orchestrator.images import ImageCatalog, ImageError
from aosedge_demo_orchestrator.status import StatusService, load_configuration


class ImagesAndCreateTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="democtl-create-test-")
        self.addCleanup(self.temporary.cleanup)
        self.workspace = Path(self.temporary.name).resolve()
        self.root = self.workspace / "solution"
        self.root.mkdir()
        self.artifacts = self.workspace / "demo-artifacts"
        project = self.artifacts / "aosedge-sdv-demo"
        self.source = project / "factory-images/version-one/main-qemuarm64.img"
        self.source.parent.mkdir(parents=True)
        self.source.write_bytes(bytes(1024 * 1024))
        self.source.chmod(0o444)
        self.sha = digest(self.source)
        self.manifest = project / "manifest/image.json"
        self.manifest.parent.mkdir()
        self.manifest.write_text(json.dumps({"factoryImage": {
            "path": str(self.source), "version": "version-one", "format": "raw",
            "sha256": self.sha, "sizeBytes": self.source.stat().st_size}}))
        self.catalog = ImageCatalog(self.artifacts, self.workspace)
        self.service = EnvironmentService(self.root, self.catalog)
        self.space = patch("aosedge_demo_orchestrator.environment.shutil.disk_usage",
                           return_value=SimpleNamespace(free=100 * 1024**3))
        self.space.start()
        self.addCleanup(self.space.stop)

    def create(self, target="all"):
        if not self.service.qemu_img:
            self.skipTest("qemu-img required for local integration test")
        return self.service.create(target, selector="version-one/main-qemuarm64")

    def test_list_is_metadata_only_and_resolves_exact_path(self):
        with patch("subprocess.run", side_effect=AssertionError("No process for inventory")):
            data = self.catalog.list()
        self.assertFalse(data["digestChecked"])
        self.assertEqual("version-one/main-qemuarm64", data["images"][0]["selector"])
        self.assertEqual((), self.catalog.resolve(image_path=self.source).problems)
        self.assertFalse((self.root / ".run").exists())

    def test_selector_must_be_explicit_and_unambiguous(self):
        with self.assertRaisesRegex(ImageError, "EXACTLY_ONE"):
            self.catalog.resolve()
        with self.assertRaisesRegex(ImageError, "IMAGE_NOT_FOUND"):
            self.catalog.resolve("latest")
        other = self.source.with_suffix(".qcow2")
        other.write_bytes(bytes(1024))
        other.chmod(0o444)
        with self.assertRaisesRegex(ImageError, "IMAGE_AMBIGUOUS"):
            self.catalog.resolve("version-one/main-qemuarm64")

    def test_component_compatibility_is_declared_not_inferred_from_image_name(self):
        selector = "version-one/main-qemuarm64"
        with self.assertRaisesRegex(ImageError, "COMPATIBILITY_NOT_DECLARED"):
            self.catalog.component_support(selector, self.sha, "vdp", ["Vehicle.Speed"])
        metadata = json.loads(self.manifest.read_text())
        metadata["source"] = dict(repository="aos-vehicle-platform", revision="a" * 40)
        metadata["demoCompatibility"] = dict(schemaVersion=1, runtimeProfile="aos-main-qemuarm64-v1",
            componentType="vdp", supportedReadPaths=["Vehicle.Speed"], sourceRevision="a" * 40)
        self.manifest.write_text(json.dumps(metadata))
        with patch("subprocess.run", side_effect=AssertionError("metadata only")):
            support = self.catalog.component_support(selector, self.sha, "vdp", ["Vehicle.Speed"])
        self.assertEqual(["Vehicle.Speed"], support["supportedReadPaths"])
        for sha, component, paths, reason in (
                ("b" * 64, "vdp", ["Vehicle.Speed"], "DIGEST_MISMATCH"),
                (self.sha, "other", ["Vehicle.Speed"], "DECLARATION_INVALID"),
                (self.sha, "vdp", ["Vehicle.New.Signal"], "PATHS_UNSUPPORTED")):
            with self.assertRaisesRegex(ImageError, reason):
                self.catalog.component_support(selector, sha, component, paths)
        metadata["demoCompatibility"]["sourceRevision"] = "b" * 40
        self.manifest.write_text(json.dumps(metadata))
        with self.assertRaisesRegex(ImageError, "DECLARATION_INVALID"):
            self.catalog.component_support(selector, self.sha, "vdp", ["Vehicle.Speed"])

    def test_conflicting_component_declaration_never_selects_one_silently(self):
        metadata = json.loads(self.manifest.read_text())
        metadata["source"] = dict(repository="aos-vehicle-platform", revision="a" * 40)
        metadata["demoCompatibility"] = dict(schemaVersion=1, runtimeProfile="aos-main-qemuarm64-v1",
            componentType="vdp", supportedReadPaths=["Vehicle.Speed"], sourceRevision="a" * 40)
        self.manifest.write_text(json.dumps(metadata))
        metadata["demoCompatibility"]["supportedReadPaths"].append("Vehicle.Other.Signal")
        self.manifest.with_name("second.json").write_text(json.dumps(metadata))
        with self.assertRaisesRegex(ImageError, "DECLARATION_CONFLICT"):
            self.catalog.component_support("version-one/main-qemuarm64", self.sha, "vdp", ["Vehicle.Speed"])

    def test_missing_conflicting_and_mutable_metadata_block_create(self):
        data = json.loads(self.manifest.read_text())
        data["factoryImage"]["sha256"] = "f" * 64
        second = self.manifest.with_name("conflict.json")
        second.write_text(json.dumps(data))
        with self.assertRaisesRegex(ImageError, "MANIFEST_CONFLICT"):
            self.catalog.resolve("version-one/main-qemuarm64")
        second.unlink()
        self.manifest.unlink()
        with self.assertRaisesRegex(ImageError, "MANIFEST_MISSING"):
            self.catalog.resolve("version-one/main-qemuarm64")
        self.source.chmod(0o644)
        self.assertIn("IMAGE_NOT_READ_ONLY", self.catalog.list()["images"][0]["problems"])

    def test_real_create_one_independent_copy_two_overlays_and_no_cloud_identity(self):
        result = self.create()
        copy = self.root / result["factory"]["path"]
        self.assertEqual(self.sha, digest(copy))
        self.assertEqual(self.sha, digest(self.source))
        self.assertNotEqual(self.source.stat().st_ino, copy.stat().st_ino)
        self.assertEqual(1, copy.stat().st_nlink)
        self.assertEqual(0o444, stat.S_IMODE(copy.stat().st_mode))
        self.assertEqual(0o600, stat.S_IMODE((self.root / JOURNAL).stat().st_mode))
        self.assertEqual(0o700, stat.S_IMODE((self.root / JOURNAL).parent.stat().st_mode))
        self.assertEqual("MANUFACTURED", result["stage"])
        self.assertIsNone(result["currentVehicle"])
        identities = set()
        for vehicle in result["vehicles"].values():
            info = self.service._info(self.root / vehicle["overlay"])
            self.assertEqual(str(copy), info["backing-filename"])
            self.assertNotEqual(str(self.source), info["backing-filename"])
            self.assertEqual("raw", info["backing-filename-format"])
            self.assertIsNone(vehicle["unitId"])
            identities.add(vehicle["localVmId"])
        self.assertEqual(2, len(identities))
        self.assertNotIn(str(self.workspace), (self.root / JOURNAL).read_text())

    def test_second_create_never_overwrites_or_retries(self):
        self.create()
        before = (self.root / JOURNAL).read_bytes()
        with patch.object(self.service, "_command", side_effect=AssertionError("No repeated qemu")):
            with self.assertRaisesRegex(EnvironmentError, "CURRENT_RUN_EXISTS"):
                self.create()
        self.assertEqual(before, (self.root / JOURNAL).read_bytes())

    def test_single_role_is_not_a_complete_dual_role_demo(self):
        result = self.create("production")
        self.assertEqual("SINGLE_ROLE_ENGINEERING", result["scope"])
        self.assertEqual(["production"], list(result["vehicles"]))
        self.assertFalse((self.root / ".local/demo-current/validation.qcow2").exists())

    def test_wrong_digest_preserves_recovery_state_without_overlays(self):
        data = json.loads(self.manifest.read_text())
        data["factoryImage"]["sha256"] = "f" * 64
        self.manifest.write_text(json.dumps(data))
        with self.assertRaisesRegex(EnvironmentError, "SOURCE_DIGEST"):
            self.create()
        self.assertEqual("RECOVERY_REQUIRED", json.loads((self.root / JOURNAL).read_text())["stage"])
        self.assertFalse((self.root / ".local/demo-current/validation.qcow2").exists())
        self.assertEqual(self.sha, digest(self.source))

    def test_interrupted_second_overlay_retains_first_and_blocks_retry(self):
        original = self.service._command
        def interrupted(args):
            if args[0] == "create" and args[-1].endswith("production.qcow2"):
                raise EnvironmentError("QEMU_IMG_FAILED")
            return original(args)
        with patch.object(self.service, "_command", side_effect=interrupted):
            with self.assertRaisesRegex(EnvironmentError, "QEMU_IMG_FAILED"):
                self.create()
        saved = json.loads((self.root / JOURNAL).read_text())
        self.assertEqual("MANUFACTURED", saved["vehicles"]["test"]["state"])
        self.assertEqual("PLANNED", saved["vehicles"]["production"]["state"])
        self.assertEqual("UNCERTAIN", saved["operations"][0]["state"])
        with self.assertRaisesRegex(EnvironmentError, "CURRENT_RUN_EXISTS"):
            self.create()

    def test_managed_status_never_inherits_legacy_unit_or_ssh_credentials(self):
        self.create()
        config = self.root / ".local/demo-control/status.json"
        config.parent.mkdir()
        config.write_text(json.dumps({"schemaVersion": 1, "vehicles": {"test": {
            "overlay": "old.qcow2", "unitId": "70e48e60-de2b-444b-a961-258683f324c4",
            "sshPort": 10022, "accessRoot": "legacy-keys"}, "production": None}}))
        state = load_configuration(self.root)
        self.assertEqual("CURRENT_RUN_JOURNAL", state["configuration"])
        self.assertNotIn("unitId", state["vehicles"]["test"])
        self.assertNotIn("accessRoot", state["vehicles"]["test"])
        self.assertIn("unitId", load_configuration(self.root, config)["vehicles"]["test"])
        with patch("aosedge_demo_orchestrator.probes.process_snapshot", return_value=[]):
            snapshot = StatusService(self.root).collect()
        self.assertEqual("MANUFACTURED", snapshot["journal"]["value"]["stage"])

    def test_symlink_directory_and_orphan_overlays_block_without_deleting(self):
        outside = self.workspace / "outside"
        outside.mkdir()
        (self.root / ".local").symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(EnvironmentError, "LOCAL_DIRECTORY_NOT_OWNED"):
            self.create()
        self.assertEqual([], list(outside.iterdir()))

    def test_missing_qemu_is_an_explicit_block(self):
        self.service.qemu_img = None
        with self.assertRaisesRegex(EnvironmentError, "QEMU_IMG_NOT_INSTALLED"):
            self.service.create("all", "version-one/main-qemuarm64")
        self.assertFalse((self.root / JOURNAL).exists())

    def test_capacity_rejection_does_not_create_a_run(self):
        with patch("aosedge_demo_orchestrator.environment.shutil.disk_usage",
                   return_value=SimpleNamespace(free=10 * 1024**3)):
            with self.assertRaisesRegex(EnvironmentError, "60_GIB"):
                self.create()
        self.assertFalse((self.root / JOURNAL).exists())

    def test_orphan_overlay_is_preserved(self):
        overlay = self.root / ".local/demo-current/validation.qcow2"
        overlay.parent.mkdir(parents=True)
        overlay.write_bytes(b"existing owned diagnostic disk")
        with self.assertRaisesRegex(EnvironmentError, "CURRENT_OVERLAYS_EXIST"):
            self.create()
        self.assertEqual(b"existing owned diagnostic disk", overlay.read_bytes())

    def test_pending_journal_never_falls_back_to_legacy_status(self):
        self.create()
        pending = self.root / (JOURNAL + ".pending")
        pending.write_bytes(b"interrupted")
        with self.assertRaisesRegex(ValueError, "requires recovery"):
            load_configuration(self.root)

    def test_cli_selection_and_api_are_same_core_without_arbitrary_api_paths(self):
        request = request_from_arguments(build_parser().parse_args([
            "environment", "create", "--image", "version-one/main-qemuarm64", "--target", "test"]))
        self.assertEqual("test", request.target.value)
        app = DemoOrchestrator(StatusService(self.root), self.catalog, self.service)
        with self.assertRaises(ValueError):
            execute_operation({"domain": "environment", "action": "create", "target": "all",
                               "image_path": str(self.source)}, app)
        self.assertEqual("OBSERVED", execute_operation({"domain": "image", "action": "list"}, app)["state"])

    def test_retire_and_recreate_copy_factory_again_and_preserve_original(self):
        first = self.create()
        factory = self.root / first["factory"]["path"]
        result = self.service.retire()
        self.assertFalse(result["recoverable"])
        self.assertFalse(result["cloudActions"])
        self.assertFalse((self.root / JOURNAL).exists())
        self.assertFalse((self.root / ".local/demo-current").exists())
        self.assertFalse(factory.exists())
        self.assertFalse((self.root / ".local/factory").exists())
        self.assertEqual(self.sha, digest(self.source))
        self.assertEqual([], self.service.retire()["removed"])
        second = self.create()
        self.assertEqual(self.sha, digest(factory))
        for role in first["vehicles"]:
            self.assertNotEqual(first["vehicles"][role]["localVmId"], second["vehicles"][role]["localVmId"])

    def test_retire_only_role_present_in_current_run(self):
        self.create("production")
        result = self.service.retire()
        self.assertEqual([".local/demo-current/production.qcow2", ".local/factory/oem-demo-factory.img",
                          ".local/factory/oem-demo-factory.manifest.json", JOURNAL], result["removed"])

    def test_retire_cloud_identity_or_wrong_stage_never_deletes(self):
        original = self.create()
        for key in ("unitId", "nodeId", "unitSetId"):
            state = json.loads(json.dumps(original))
            state["vehicles"]["test"][key] = "70e48e60-de2b-444b-a961-258683f324c4"
            atomic_json(self.root / JOURNAL, state)
            with self.assertRaisesRegex(EnvironmentError, "REQUIRES_UNUSED"):
                self.service.retire()
        state = json.loads(json.dumps(original))
        state["stage"] = "RECOVERY_REQUIRED"
        atomic_json(self.root / JOURNAL, state)
        with self.assertRaisesRegex(EnvironmentError, "REQUIRES_UNUSED"):
            self.service.retire()
        self.assertTrue((self.root / original["vehicles"]["test"]["overlay"]).exists())

    def test_retire_checks_all_roles_before_deleting_any(self):
        state = self.create()
        def used(path):
            if path.name == "production.qcow2":
                raise EnvironmentError("CLEANUP_FILE_IN_USE")
        with patch.object(self.service, "_assert_unheld", side_effect=used):
            with self.assertRaisesRegex(EnvironmentError, "CLEANUP_FILE_IN_USE"):
                self.service.retire()
        for item in state["vehicles"].values():
            self.assertTrue((self.root / item["overlay"]).exists())
        self.assertEqual("MANUFACTURED", json.loads((self.root / JOURNAL).read_text())["stage"])

    def retired_cloud_state(self):
        state = self.create()
        state["stage"] = "LOCAL_STOPPED"
        for item in state["vehicles"].values():
            item.update(unitId=item["localVmId"], nodeId=item["localVmId"], unitSetId=item["localVmId"],
                        systemUid=item["localVmId"], cloud={"lifecycle": "DELETED", "absenceConfirmed": True},
                        runtime={"state": "STOPPED", "pid": None, "everStarted": True})
        atomic_json(self.root / JOURNAL, state)
        return state

    def test_cloud_retire_requires_fresh_proof_before_any_unlink(self):
        state = self.retired_cloud_state()
        for check in (None, Mock(return_value=False), Mock(side_effect=EnvironmentError("CLOUD_DENIED"))):
            with self.assertRaises(EnvironmentError):
                self.service.retire(cloud_check=check)
            self.assertTrue(all((self.root / item["overlay"]).exists() for item in state["vehicles"].values()))
        check = Mock(return_value=True)
        result = self.service.retire(cloud_check=check)
        check.assert_called_once()
        self.assertEqual("CLOUD_RETIRED_CLI_RUN", result["scope"])
        self.assertTrue(result["cloudReadsPerformed"])
        self.assertFalse((self.root / JOURNAL).exists())

    def test_retire_borrowed_dns_is_not_owned_or_stopped(self):
        state = self.create("test")
        state["shared"] = {"dns": {"ownership": "EXTERNAL_DEPENDENCY", "state": "RUNNING", "pid": 123,
            "ownerRoot": str(self.workspace / "canonical"), "ownerId": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"}}
        atomic_json(self.root / JOURNAL, state)
        result = self.service.retire()
        self.assertEqual("REMOVED", result["outcome"])
        self.assertFalse(any("canonical" in path for path in result["removed"]))
        self.assertEqual(self.sha, digest(self.source))
        self.create()

    def test_cloud_retire_never_accepts_partial_identity_retirement(self):
        state = self.retired_cloud_state()
        state["vehicles"]["production"]["cloud"]["lifecycle"] = "DEPROVISIONED"
        atomic_json(self.root / JOURNAL, state)
        check = Mock(return_value=True)
        with self.assertRaisesRegex(EnvironmentError, "CLOUD_RETIREMENT_PROOF_REQUIRED"):
            self.service.retire(cloud_check=check)
        check.assert_not_called()

    def source_retirement_fixture(self):
        state = self.retired_cloud_state()
        identity = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
        relative = ".run/demo-current/source/" + identity
        run = self.service._directory(relative)
        self.service._directory(".run/demo-current/control")
        atomic_json(run / "manifest.json", {"run_id": identity, "status": "completed"})
        (run / "runner.log").write_text("owned temporary runtime output\n")
        state["source"] = dict(runId=identity, runDirectory=relative,
            controlDirectory=".run/demo-current/control", state="STOPPED", operation=None,
            runnerCommand=["fixture", "--owned-run", str(run)],
            simulatorCommand=["fixture", "--simulator"])
        state["componentOperations"] = {"9.0.0": {"upload": {"attemptStarted": True, "state": "CONFIRMED"}}}
        state["smDemoProof"] = {"state": "APPLIED"}
        atomic_json(self.root / JOURNAL, state)
        return state, run

    def test_retire_stopped_source_outputs_preserves_original_and_recreates(self):
        state, run = self.source_retirement_fixture()
        result = self.service.retire(cloud_check=Mock(return_value=True))
        self.assertIn(str(run.relative_to(self.root) / "runner.log"), result["removed"])
        self.assertFalse((self.root / ".run/demo-current/source").exists())
        self.assertFalse((self.root / ".run/demo-current/control").exists())
        self.assertEqual(self.sha, digest(self.source))
        self.create()

    def test_retire_source_rejects_live_unknown_and_symlink_before_unlink(self):
        state, run = self.source_retirement_fixture()
        with patch("aosedge_demo_orchestrator.source.SourceDriver.live_process", return_value=123):
            with self.assertRaisesRegex(EnvironmentError, "SIMULATION_MUST_BE_STOPPED"):
                self.service.retire(cloud_check=Mock(return_value=True))
        extra = run / "unowned.txt"
        extra.write_text("must remain")
        with self.assertRaisesRegex(EnvironmentError, "UNTRACKED_SOURCE_RUNTIME_FILE"):
            self.service.retire(cloud_check=Mock(return_value=True))
        extra.unlink()
        log = run / "runner.log"
        log.unlink()
        log.symlink_to(self.source)
        with self.assertRaisesRegex(EnvironmentError, "CLEANUP_FILE_NOT_OWNED"):
            self.service.retire(cloud_check=Mock(return_value=True))
        self.assertTrue((self.root / state["vehicles"]["test"]["overlay"]).exists())
        self.assertEqual(self.sha, digest(self.source))

    def test_retire_source_resumes_after_runtime_unlink_without_manifest(self):
        state, run = self.source_retirement_fixture()
        original = self.service._unlink_owned
        def interrupted(path, identity):
            original(path, identity)
            if path == run / "manifest.json":
                raise OSError("interrupted after manifest unlink")
        with patch.object(self.service, "_unlink_owned", side_effect=interrupted), self.assertRaises(OSError):
            self.service.retire(cloud_check=Mock(return_value=True))
        self.assertEqual("REMOVED", self.service.retire(cloud_check=Mock(return_value=True))["outcome"])
        self.assertFalse(run.exists())

    def test_retire_keeps_uncertain_component_publication(self):
        state, run = self.source_retirement_fixture()
        state["componentOperations"]["9.0.0"]["upload"]["state"] = "UNCERTAIN"
        atomic_json(self.root / JOURNAL, state)
        with self.assertRaisesRegex(EnvironmentError, "COMPONENT_OPERATION_RECONCILIATION_REQUIRED"):
            self.service.retire(cloud_check=Mock(return_value=True))
        self.assertTrue(run.exists())

    def test_retire_cloud_reconciliation_precedes_publication_guard(self):
        state, run = self.source_retirement_fixture()
        state["componentOperations"]["9.0.0"]["upload"]["state"] = "RESPONDED"
        atomic_json(self.root / JOURNAL, state)
        def reconciled(current):
            self.assertTrue(run.exists())
            self.assertTrue(all((self.root / item["overlay"]).exists() for item in current["vehicles"].values()))
            current["componentOperations"]["9.0.0"]["upload"]["state"] = "CONFIRMED"
            return True
        self.assertEqual("REMOVED", self.service.retire(cloud_check=reconciled)["outcome"])
        self.assertFalse(run.exists())

    def test_retire_obsolete_send_needs_exact_deleted_target_and_fresh_proof(self):
        state, run = self.source_retirement_fixture()
        send = {"attemptStarted": True, "state": "UNCERTAIN", "unitId": "wrong-target"}
        state["componentOperations"]["9.0.0"]["send"] = send
        atomic_json(self.root / JOURNAL, state)
        with self.assertRaisesRegex(EnvironmentError, "COMPONENT_OPERATION_RECONCILIATION_REQUIRED"):
            self.service.retire(cloud_check=Mock(return_value=True))
        send["unitId"] = state["vehicles"]["test"]["unitId"]
        atomic_json(self.root / JOURNAL, state)
        with self.assertRaisesRegex(EnvironmentError, "FRESH_CLOUD_RETIREMENT_CHECK_FAILED"):
            self.service.retire(cloud_check=Mock(return_value=False))
        self.assertTrue(run.exists())
        self.assertEqual("REMOVED", self.service.retire(cloud_check=Mock(return_value=True))["outcome"])

    def test_cloud_retire_rechecks_cloud_after_interrupted_unlink(self):
        state = self.retired_cloud_state()
        original = self.service._unlink_owned
        def interrupted(path, identity):
            original(path, identity)
            raise OSError("fixture interruption")
        with patch.object(self.service, "_unlink_owned", side_effect=interrupted), self.assertRaises(OSError):
            self.service.retire(cloud_check=Mock(return_value=True))
        restored = EnvironmentService(self.root, self.catalog)
        with self.assertRaisesRegex(EnvironmentError, "CLOUD_DENIED"):
            restored.retire(cloud_check=Mock(side_effect=EnvironmentError("CLOUD_DENIED")))
        self.assertTrue((self.root / state["vehicles"]["production"]["overlay"]).exists())
        self.assertEqual("REMOVED", restored.retire(cloud_check=Mock(return_value=True))["outcome"])

    def test_retire_real_open_file_is_not_deleted(self):
        state = self.create("test")
        overlay = self.root / state["vehicles"]["test"]["overlay"]
        process = subprocess.Popen([sys.executable, "-c",
            "import sys; f=open(sys.argv[1], 'rb'); print('ready', flush=True); sys.stdin.read()",
            str(overlay)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        try:
            self.assertEqual("ready\n", process.stdout.readline())
            with self.assertRaisesRegex(EnvironmentError, "CLEANUP_FILE_IN_USE"):
                self.service.retire()
            self.assertTrue(overlay.exists())
        finally:
            process.communicate(timeout=5)

    def test_retire_modified_guest_data_requires_full_retirement(self):
        qemu_io = shutil.which("qemu-io")
        if not qemu_io:
            self.skipTest("qemu-io required for modified-overlay proof")
        state = self.create("test")
        overlay = self.root / state["vehicles"]["test"]["overlay"]
        subprocess.run([qemu_io, "-f", "qcow2", "-c", "write -P 0x55 0 512", str(overlay)],
                       capture_output=True, check=True, timeout=10)
        with self.assertRaisesRegex(EnvironmentError, "OVERLAY_MODIFIED"):
            self.service.retire()
        self.assertTrue(overlay.exists())

    def test_retire_does_not_follow_symlinks_or_delete_untracked_files(self):
        state = self.create()
        unrelated = self.root / ".local/demo-current/user-notes.txt"
        unrelated.write_text("keep")
        with self.assertRaisesRegex(EnvironmentError, "UNTRACKED"):
            self.service.retire()
        unrelated.unlink()
        overlay = self.root / state["vehicles"]["test"]["overlay"]
        kept = self.workspace / "keep.qcow2"
        overlay.rename(kept)
        overlay.symlink_to(kept)
        with self.assertRaisesRegex(EnvironmentError, "NOT_OWNED"):
            self.service.retire()
        self.assertTrue(kept.exists())
        self.assertTrue((self.root / state["vehicles"]["production"]["overlay"]).exists())

    def test_retire_restart_reconciles_unlink_before_receipt(self):
        state = self.create()
        unlink = self.service._unlink_owned
        def interrupted(path, identity):
            unlink(path, identity)
            raise OSError("simulated process loss after unlink")
        with patch.object(self.service, "_unlink_owned", side_effect=interrupted):
            with self.assertRaises(OSError):
                self.service.retire()
        saved = json.loads((self.root / JOURNAL).read_text())
        self.assertEqual("RETIRING_LOCAL", saved["stage"])
        self.assertEqual("REMOVE_PENDING", saved["retirement"]["test"]["state"])
        self.assertFalse((self.root / state["vehicles"]["test"]["overlay"]).exists())
        restored = EnvironmentService(self.root, self.catalog)
        with patch.object(restored, "_unlink_owned", wraps=restored._unlink_owned) as calls:
            result = restored.retire()
        self.assertEqual(["production.qcow2", "oem-demo-factory.img", "oem-demo-factory.manifest.json"],
                         [call.args[0].name for call in calls.call_args_list])
        self.assertEqual("REMOVED", result["outcome"])

    def test_retire_handle_visibility_failure_does_not_mutate(self):
        state = self.create("test")
        with patch("aosedge_demo_orchestrator.environment.shutil.which", return_value=None):
            with self.assertRaisesRegex(EnvironmentError, "OPEN_HANDLE_CHECK_UNAVAILABLE"):
                self.service.retire()
        self.assertTrue((self.root / state["vehicles"]["test"]["overlay"]).exists())

    def test_retire_api_same_core_and_rejects_extra_authority(self):
        self.create("test")
        app = DemoOrchestrator(StatusService(self.root), self.catalog, self.service)
        for extra in ({"target": "all"}, {"force": True}, {"path": str(self.root)}):
            with self.assertRaises(ValueError):
                execute_operation(dict(domain="environment", action="retire", **extra), app)
        result = execute_operation({"domain": "environment", "action": "retire"}, app)
        self.assertEqual("COMPLETED", result["state"])
        self.assertEqual("UNUSED_LOCAL_CREATE", result["data"]["scope"])

    def test_retire_removes_factory_left_by_old_retire(self):
        state = self.create()
        for item in state["vehicles"].values():
            (self.root / item["overlay"]).unlink()
        (self.root / ".local/demo-current").rmdir()
        (self.root / JOURNAL).unlink()
        result = self.service.retire()
        self.assertFalse((self.root / ".local/factory").exists())
        self.assertFalse((self.root / JOURNAL).exists())
        self.assertEqual(self.sha, digest(self.source))
        self.assertEqual(3, len(result["removed"]))

    def test_factory_in_use_blocks_before_any_overlay_deletion(self):
        state = self.create()
        def held(path):
            if path.name == "oem-demo-factory.img":
                raise EnvironmentError("CLEANUP_FILE_IN_USE")
        with patch.object(self.service, "_assert_unheld", side_effect=held):
            with self.assertRaisesRegex(EnvironmentError, "CLEANUP_FILE_IN_USE"):
                self.service.retire()
        self.assertTrue((self.root / state["factory"]["path"]).exists())
        for item in state["vehicles"].values():
            self.assertTrue((self.root / item["overlay"]).exists())

    def test_factory_and_manifest_unlink_interruptions_resume_in_order(self):
        for filename in ("oem-demo-factory.img", "oem-demo-factory.manifest.json"):
            with self.subTest(filename=filename):
                state = self.create()
                unlink = self.service._unlink_owned
                def interrupted(path, identity):
                    unlink(path, identity)
                    if path.name == filename:
                        raise OSError("interrupted factory cleanup")
                with patch.object(self.service, "_unlink_owned", side_effect=interrupted):
                    with self.assertRaises(OSError):
                        self.service.retire()
                self.assertTrue((self.root / JOURNAL).exists())
                self.assertFalse((self.root / state["vehicles"]["test"]["overlay"]).exists())
                EnvironmentService(self.root, self.catalog).retire()
                self.assertFalse((self.root / JOURNAL).exists())
                self.assertFalse((self.root / ".local/factory").exists())
                self.assertEqual(self.sha, digest(self.source))


if __name__ == "__main__":
    unittest.main()
