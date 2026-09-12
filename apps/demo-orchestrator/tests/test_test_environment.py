# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import copy
import json
from dataclasses import replace
from unittest import TestCase
from unittest.mock import Mock, patch

import test_images_environment as fixtures
from aosedge_demo_orchestrator.environment import EnvironmentError, EnvironmentService, JOURNAL, MANIFEST, atomic_json, digest, factory_for
from aosedge_demo_orchestrator.status import load_configuration
from aosedge_demo_orchestrator.guest_access import ACCESS_FILES


class TestOnlyRetirementTests(TestCase):
    setUp = fixtures.ImagesAndCreateTests.setUp
    create = fixtures.ImagesAndCreateTests.create

    def read(self):
        return json.loads((self.root / JOURNAL).read_text())

    def retired(self):
        state = self.create()
        state["stage"] = "LOCAL_ACTIVE"
        test = state["vehicles"]["test"]
        test.update(unitId=test["localVmId"], nodeId=test["localVmId"], unitSetId=test["localVmId"],
            systemUid="test-old-uid", cloud=dict(lifecycle="DELETED", absenceConfirmed=True),
            runtime=dict(state="STOPPED", pid=None, everStarted=True, accessCreated=True))
        production = state["vehicles"]["production"]
        production.update(unitId=production["localVmId"], nodeId=production["localVmId"], unitSetId=production["localVmId"],
            systemUid="production-uid", cloud=dict(lifecycle="ONLINE"),
            runtime=dict(state="RUNNING", pid=43210, everStarted=True))
        state["shared"] = dict(dns=dict(ownerId=state["operations"][0]["id"], pid=12345, state="RUNNING"))
        state["currentVehicle"] = "production"
        state["cloudBinding"] = dict(ownerId=production["localVmId"], sets=dict(test=test["unitSetId"], production=production["unitSetId"]))
        directory = self.service._directory(".run/demo-current/test-access")
        for name in ACCESS_FILES:
            (directory / name).write_text("fixture-not-real-access")
        atomic_json(self.root / JOURNAL, state)
        return state

    def unheld(self):
        return patch.object(self.service, "_assert_unheld")

    def test_first_retire_preserves_running_production_dns_factory_and_ledger(self):
        state = self.retired()
        state["workspace"] = dict(profile="builtin-v1", combined=True)
        atomic_json(self.root / JOURNAL, state)
        factory = self.root / state["factory"]["path"]
        before = (factory.stat().st_ino, factory.read_bytes(), (self.root / MANIFEST).read_bytes())
        production_file = self.root / state["vehicles"]["production"]["overlay"]
        peer_before = (production_file.stat().st_ino, production_file.read_bytes())
        ledger = self.root / ".local/release-continuity.json"
        ledger.write_text('{"vdp":15}')
        with self.unheld() as handles:
            result = self.service.retire_test(cloud_check=Mock(return_value=True))
        current = self.read()
        self.assertEqual("REMOVED", result["outcome"])
        for key in ("production",):
            self.assertEqual(state["vehicles"][key], current["vehicles"][key])
        for key in ("shared", "factory", "cloudBinding", "currentVehicle", "workspace"):
            self.assertEqual(state[key], current[key])
        self.assertEqual(before, (factory.stat().st_ino, factory.read_bytes(), (self.root / MANIFEST).read_bytes()))
        self.assertEqual(peer_before, (production_file.stat().st_ino, production_file.read_bytes()))
        self.assertEqual('{"vdp":15}', ledger.read_text())
        self.assertFalse(any(call.args[0] == factory or call.args[0] == production_file for call in handles.call_args_list))
        self.assertFalse((self.root / state["vehicles"]["test"]["overlay"]).exists())

    def test_fresh_test_same_image_no_second_copy_and_no_old_identity(self):
        original = self.retired()
        with self.unheld():
            self.service.retire_test(cloud_check=lambda state: True)
        with patch.object(self.service, "_copy_factory", side_effect=AssertionError("No copy")):
            created = self.create("test")
        self.assertNotEqual(original["vehicles"]["test"]["localVmId"], created["vehicles"]["test"]["localVmId"])
        self.assertEqual(original["vehicles"]["production"], created["vehicles"]["production"])
        self.assertEqual(original["shared"], created["shared"])
        self.assertIsNone(created["vehicles"]["test"]["unitId"])
        self.assertNotIn("cloud", created["vehicles"]["test"])
        self.assertNotIn("testRetirement", created)
        self.assertEqual(original["operations"], created["operations"])
        with self.assertRaisesRegex(EnvironmentError, "CURRENT_RUN_EXISTS"):
            self.create("test")

    def test_retire_retains_subjects_discards_only_terminal_old_test_receipts(self):
        from test_service_assignment import BRAKE, SUBJECT, USER
        state = self.retired()
        test = state["vehicles"]["test"]
        owner = state["cloudBinding"]["ownerId"]
        state["demoSubjects"] = {BRAKE: dict(ownerId=owner, id=SUBJECT, label="AosEdge SDV demo Brake",
            isGroup=True, priority=0, createdBy=USER, create=dict(stage="CONFIRMED"))}
        state["serviceOperations"] = {BRAKE: dict(ownerId=owner, serviceId=BRAKE, team="brake", state="ASSIGNED",
            test={key: test[key] for key in ("unitId", "systemUid", "unitSetId")},
            steps={key: dict(stage="CONFIRMED") for key in ("bind", "assign")})}
        state["smServiceUpdateProof"] = dict(state="APPLIED")
        state["cmServiceUpdateProof"] = dict(state="APPLIED")
        atomic_json(self.root / JOURNAL, state)
        with self.unheld():
            self.service.retire_test(cloud_check=lambda value: True)
        current = self.read()
        self.assertEqual(state["demoSubjects"], current["demoSubjects"])
        self.assertEqual(state["vehicles"]["production"], current["vehicles"]["production"])
        for key in ("serviceOperations", "smServiceUpdateProof", "cmServiceUpdateProof"):
            self.assertNotIn(key, current)
        recreated = self.create("test")
        self.assertEqual(state["demoSubjects"], recreated["demoSubjects"])

    def test_cloud_proof_required_and_never_production_absence(self):
        original = self.retired()
        for check in (None, lambda state: False):
            with self.assertRaisesRegex(EnvironmentError, "FRESH_CLOUD_RETIREMENT"):
                self.service.retire_test(cloud_check=check)
        def check(state):
            self.assertEqual(original["vehicles"]["production"], state["vehicles"]["production"])
            self.assertEqual("DELETED", state["vehicles"]["test"]["cloud"]["lifecycle"])
            return True
        with self.unheld():
            self.service.retire_test(cloud_check=check)

    def test_interrupted_unlink_rechecks_cloud_and_completes_without_duplicate_delete(self):
        self.retired()
        original = self.service._unlink_owned
        def interrupted(path, identity):
            original(path, identity)
            raise OSError("injected interruption after unlink")
        with self.unheld(), patch.object(self.service, "_unlink_owned", side_effect=interrupted):
            with self.assertRaises(OSError):
                self.service.retire_test(cloud_check=lambda state: True)
        self.assertEqual("REMOVE_PENDING", self.read()["testRetirement"]["targets"]["overlay"]["state"])
        check = Mock(return_value=False)
        with self.assertRaisesRegex(EnvironmentError, "FRESH_CLOUD_RETIREMENT"):
            self.service.retire_test(cloud_check=check)
        check.assert_called_once()
        with self.unheld(), patch.object(self.service, "_unlink_owned", wraps=original) as unlink:
            self.service.retire_test(cloud_check=lambda state: True)
        self.assertEqual(3, unlink.call_count)
        with patch.object(self.service, "_unlink_owned", side_effect=AssertionError("No repeat")):
            self.assertEqual("NO_CURRENT_TEST", self.service.retire_test()["outcome"])

    def test_unknown_files_block_before_deletion(self):
        state = self.retired()
        unexpected = self.root / ".run/demo-current/test-access/unknown-key"
        unexpected.write_text("preserve")
        with self.assertRaisesRegex(EnvironmentError, "UNTRACKED_ACCESS"):
            self.service.retire_test(cloud_check=lambda state: True)
        self.assertTrue((self.root / state["vehicles"]["test"]["overlay"]).exists())
        unexpected.unlink()
        orphan = self.root / ".local/demo-current/foreign.qcow2"
        orphan.write_text("preserve")
        with self.assertRaisesRegex(EnvironmentError, "UNTRACKED_RUNTIME"):
            self.service.retire_test(cloud_check=lambda state: True)

    def test_symlink_overlay_and_changed_target_preserve_peer(self):
        state = self.retired()
        test = self.root / state["vehicles"]["test"]["overlay"]
        peer = self.root / state["vehicles"]["production"]["overlay"]
        test.unlink()
        test.symlink_to(peer)
        with self.unheld(), self.assertRaisesRegex(EnvironmentError, "NOT_OWNED"):
            self.service.retire_test(cloud_check=lambda state: True)
        self.assertTrue(peer.exists())

    def test_running_or_selected_test_blocks(self):
        state = self.retired()
        state["currentVehicle"] = "test"
        atomic_json(self.root / JOURNAL, state)
        with self.assertRaisesRegex(EnvironmentError, "REQUIRES_PARK"):
            self.service.retire_test(cloud_check=lambda state: True)
        state["currentVehicle"] = None
        state["vehicles"]["test"]["runtime"]["state"] = "RUNNING"
        atomic_json(self.root / JOURNAL, state)
        with self.assertRaisesRegex(EnvironmentError, "MUST_BE_STOPPED"):
            self.service.retire_test(cloud_check=lambda state: True)

    def test_backend_proof_required_then_terminal_receipts_removed_not_ledger(self):
        state = self.retired()
        state["backends"] = dict(brake=dict(state="STOPPED"))
        state["componentOperations"] = {"15.0.0": dict(upload=dict(attemptStarted=True, state="CONFIRMED"))}
        state["demoPreparation"] = dict(target="test", phase="READY_TO_DRIVE")
        state["demoLifecycle"] = dict(action="retire", target="test", state="SUBMITTING", completedSteps=[])
        atomic_json(self.root / JOURNAL, state)
        with self.assertRaisesRegex(EnvironmentError, "BACKEND_CLEANUP"):
            self.service.retire_test(cloud_check=lambda state: True)
        backend = Mock(return_value=True)
        with self.unheld():
            self.service.retire_test(cloud_check=lambda state: True, backend_check=backend)
        backend.assert_called_once()
        current = self.read()
        self.assertNotIn("componentOperations", current)
        self.assertNotIn("demoPreparation", current)
        self.assertEqual(state["demoLifecycle"], current["demoLifecycle"])

    def test_uncertain_publication_never_erased(self):
        state = self.retired()
        state["componentOperations"] = {"15.0.0": dict(upload=dict(attemptStarted=True, state="UNCERTAIN"))}
        atomic_json(self.root / JOURNAL, state)
        with self.assertRaisesRegex(EnvironmentError, "COMPONENT_OPERATION_RECONCILIATION"):
            self.service.retire_test(cloud_check=lambda state: True)
        self.assertEqual(state["componentOperations"], self.read()["componentOperations"])

    def test_unprovisioned_test_requires_extent_or_stop_proof(self):
        state = self.create()
        with self.unheld():
            self.service.retire_test()
        self.assertEqual({"production"}, set(self.read()["vehicles"]))

    def test_recreate_wrong_digest_preserves_peer_and_failed_copy_intent(self):
        self.retired()
        with self.unheld():
            self.service.retire_test(cloud_check=lambda state: True)
        image = copy.copy(self.catalog.resolve("version-one/main-qemuarm64"))
        object.__setattr__(image, "sha256", "a" * 64)
        before = self.read()
        with patch.object(self.catalog, "resolve", return_value=image):
            with self.assertRaisesRegex(EnvironmentError, "SOURCE_DIGEST"):
                self.create("test")
        self.assertEqual(before["vehicles"]["production"], self.read()["vehicles"]["production"])
        self.assertEqual("RECOVERY_REQUIRED", self.read()["stage"])

    def new_image(self):
        image = self.catalog.resolve("version-one/main-qemuarm64")
        path = self.source.parent.parent / "version-two/main-qemuarm64.img"
        path.parent.mkdir()
        path.write_bytes(b"new factory" + bytes(image.size - 11))
        path.chmod(0o444)
        return replace(image, version="version-two", selector="version-two/main-qemuarm64", path=path, sha256=digest(path))

    def mixed(self):
        original = self.retired()
        with self.unheld():
            self.service.retire_test(cloud_check=lambda state: True)
        image = self.new_image()
        with patch.object(self.catalog, "resolve", return_value=image):
            created = self.create("test")
        return original, image, created

    def test_new_test_image_copy_status_and_retirement_preserve_production(self):
        original, image, created = self.mixed()
        self.assertEqual(original["factory"], created["factory"])
        self.assertEqual(original["vehicles"]["production"], created["vehicles"]["production"])
        self.assertEqual(original["shared"], created["shared"])
        new = factory_for(created, "test")
        self.assertEqual(image.sha256, digest(self.root / new["path"]))
        self.assertEqual(original["factory"], factory_for(created, "production"))
        self.assertEqual(str(self.root / new["path"]), self.service._info(self.root / created["vehicles"]["test"]["overlay"])["backing-filename"])
        observed = load_configuration(self.root)
        self.assertEqual("version-two", observed["vehicles"]["test"]["imageVersion"])
        self.assertEqual("version-one", observed["vehicles"]["production"]["imageVersion"])
        with self.assertRaisesRegex(EnvironmentError, "TEST_SCOPED_RETIRE"):
            self.service.retire()
        with self.unheld():
            result = self.service.retire_test()
        self.assertLess(result["removed"].index(created["vehicles"]["test"]["overlay"]), result["removed"].index(new["path"]))
        self.assertFalse((self.root / new["path"]).exists())
        self.assertTrue((self.root / original["factory"]["path"]).exists())
        self.assertTrue(image.path.exists())
        self.assertEqual(original["vehicles"]["production"], self.read()["vehicles"]["production"])

    def test_mixed_factory_unlink_interruption_resumes_without_deleting_peer(self):
        original, image, created = self.mixed()
        factory = factory_for(created, "test")
        unlink = self.service._unlink_owned
        def interrupted(path, identity):
            unlink(path, identity)
            if path == self.root / factory["path"]:
                raise OSError("after dedicated factory unlink")
        with self.unheld(), patch.object(self.service, "_unlink_owned", side_effect=interrupted):
            with self.assertRaises(OSError):
                self.service.retire_test()
        with self.unheld():
            self.service.retire_test()
        self.assertEqual(original["vehicles"]["production"], self.read()["vehicles"]["production"])
        self.assertFalse((self.root / factory["manifestPath"]).exists())

    def test_interrupted_recreate_keeps_peer_and_does_not_retry_create(self):
        old = self.retired()
        with self.unheld():
            self.service.retire_test(cloud_check=lambda state: True)
        with patch.object(self.service, "_command", side_effect=EnvironmentError("INJECTED")):
            with self.assertRaisesRegex(EnvironmentError, "INJECTED"):
                self.create("test")
        self.assertEqual(old["vehicles"]["production"], self.read()["vehicles"]["production"])
        self.assertEqual("RECOVERY_REQUIRED", self.read()["stage"])
        with patch.object(self.service, "_command", side_effect=AssertionError("No blind retry")):
            with self.assertRaises(EnvironmentError):
                self.create("test")

    def test_single_test_uses_existing_symmetric_retire(self):
        self.create("test")
        with self.unheld():
            result = self.service.retire_test()
        self.assertEqual("UNUSED_LOCAL_CREATE", result["scope"])
        self.assertFalse((self.root / JOURNAL).exists())

    def test_recreated_access_material_is_not_adopted_after_retirement(self):
        self.retired()
        with self.unheld():
            self.service.retire_test(cloud_check=lambda state: True)
        self.service._directory(".run/demo-current/test-access")
        with self.assertRaisesRegex(EnvironmentError, "ORPHAN_ACCESS"):
            self.service.retire_test()
        with self.assertRaisesRegex(EnvironmentError, "ORPHAN_ACCESS"):
            self.create("test")

    def test_backend_callback_cannot_change_production_or_dns(self):
        state = self.retired()
        state["backends"] = dict(brake=dict(state="STOPPED"))
        atomic_json(self.root / JOURNAL, state)
        def wrong_scope(value):
            value["shared"]["dns"]["state"] = "STOPPED"
            return True
        with self.assertRaisesRegex(EnvironmentError, "PEER_CHANGED"):
            self.service.retire_test(cloud_check=lambda state: True, backend_check=wrong_scope)
        self.assertTrue((self.root / state["vehicles"]["test"]["overlay"]).exists())
        self.assertEqual(state["shared"], self.read()["shared"])
