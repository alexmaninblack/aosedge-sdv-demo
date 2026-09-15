# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import copy
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from aosedge_demo_orchestrator.cloud_setup import CloudSetup, inspect_setup, create_step
from aosedge_demo_orchestrator.unit_cloud import CloudFailure
from aosedge_demo_orchestrator.units import UnitService
from aosedge_demo_orchestrator.cloud_connection import bind_tenant, cloud_binding, cloud_subjects, CONFIG
from aosedge_demo_orchestrator.package_artifacts import publication_path
from aosedge_demo_orchestrator.environment import EnvironmentService, EnvironmentError, atomic_json, JOURNAL
from aosedge_demo_orchestrator.status import read_json
from aosedge_demo_orchestrator.presenter_operations import operation_plan, public_result

OEM = "11111111-1111-4111-8111-111111111111"
SP = "22222222-2222-4222-8222-222222222222"
FLEET = "33333333-3333-4333-8333-333333333333"
MODEL = "44444444-4444-4444-8444-444444444444"
SET = "55555555-5555-4555-8555-555555555555"
OTHER = "66666666-6666-4666-8666-666666666666"
DOMAIN = "stage.example.test"
CONFIGURATION = {"nodes": [{"nodeType": "aos-vm-main", "labels": ["main"], "priority": 100}]}
REQUEST = dict(cloudDomain=DOMAIN, spCredential="/private/unused.p12", unitConfig=CONFIGURATION)


class CloudFixture:
    def __init__(self):
        self.user = {"ownerId": OEM}
        self.models = []
        self.nodes = []
        self.sets = [dict(id=OTHER, title="Unrelated campaign", fleet=FLEET, is_validation_set=False)]
        self.members = []
        self.posts = []
        self.denied = None
        self.lose_response = False

    def require(self, *permissions):
        if self.denied in permissions:
            raise CloudFailure("PERMISSION_DENIED")

    def pages(self, path):
        if path == "unit-models/": return copy.deepcopy(self.models)
        if path == "node-types/": return copy.deepcopy(self.nodes)
        if path == "unit-sets/": return copy.deepcopy(self.sets)
        if path == "service-providers/": return [{"id": SP}]
        if path == "unit-sets/" + SET + "/units/": return copy.deepcopy(self.members)
        raise AssertionError(path)

    def call(self, path, method="GET", body=None, expected=200):
        if method == "POST":
            self.posts.append((path, copy.deepcopy(body)))
            if path == "unit-models/":
                self.models = [dict(body, id=MODEL, oem_id=OEM)]
                self.nodes = [{"name": "aos-vm-main"}]
                result = self.models[0]
            elif path == "unit-sets/":
                result = dict(body, id=SET)
                self.sets.append(result)
            else: raise AssertionError(path)
            if self.lose_response: raise TimeoutError()
            return result
        if path == "fleets/default/": return dict(id=FLEET, is_default=True)
        if path.endswith("/architectures/"): return {"architectures": ["arm64"]}
        if path == "unit-models/" + MODEL + "/": return copy.deepcopy(self.models[0])
        raise AssertionError(path)


class SetupTests(unittest.TestCase):
    def setUp(self):
        self.cloud = CloudFixture()
        self.sp = Mock(return_value=SimpleNamespace(user={"ownerId": SP}))
        self.cert = patch("aosedge_demo_orchestrator.cloud_connection.inspect_certificate", return_value={})
        self.cert.start(); self.addCleanup(self.cert.stop)
        self.provider = patch("aosedge_demo_orchestrator.unit_cloud.Cloud", self.sp)
        self.provider.start(); self.addCleanup(self.provider.stop)

    def report(self): return inspect_setup(self.cloud, REQUEST)

    def step(self, key): return create_step(self.cloud, dict(REQUEST, step=key, owners={"oem": OEM, "sp": SP}))

    def ready(self):
        self.assertEqual("CONFIRMED", self.step("model")["stage"])
        self.assertEqual("CONFIRMED", self.step("testSet")["stage"])

    def test_check_reports_all_missing_together_and_never_writes(self):
        result = self.report()
        self.assertEqual("MISSING", result["stage"])
        self.assertEqual(["model", "testSet"], result["steps"])
        self.assertEqual([OTHER], result["objects"]["unrelatedSetIds"])
        self.assertEqual([], self.cloud.posts)

    def test_first_create_repeat_and_unrelated_objects(self):
        prior = copy.deepcopy(self.cloud.sets[0])
        self.ready()
        self.assertEqual("READY", self.report()["stage"])
        self.assertFalse(self.step("model")["attempted"])
        self.assertFalse(self.step("testSet")["attempted"])
        self.assertEqual(2, len(self.cloud.posts))
        self.assertEqual(prior, self.cloud.sets[0])
        self.assertEqual(CONFIGURATION, self.cloud.posts[0][1]["unit_config"])
        self.assertEqual(FLEET, self.cloud.posts[1][1]["fleet"])
        self.assertTrue(self.cloud.posts[1][1]["is_validation_set"])

    def test_node_catalog_can_be_empty_until_provisioning_without_deadlock(self):
        self.ready()
        self.cloud.nodes = []
        report = self.report()
        self.assertEqual("READY", report["stage"])
        self.assertEqual("AFTER_PROVISION", next(v for v in report["checks"] if v["key"] == "nodeType")["state"])

    def test_existing_unit_cannot_defer_missing_node_type(self):
        self.ready()
        self.cloud.nodes = []
        report = inspect_setup(self.cloud, dict(REQUEST, testUnitId=OTHER))
        self.assertEqual("BLOCKED", report["stage"])
        self.assertEqual("PROVISIONED_TEST_NODE_TYPE_NOT_CONFIRMED",
            next(v for v in report["checks"] if v["key"] == "nodeType")["detail"])

    def test_existing_conflicting_model_never_overwritten(self):
        self.step("model")
        self.cloud.models[0]["unit_config"] = {"nodes": []}
        before = len(self.cloud.posts)
        self.assertEqual("BLOCKED", self.step("testSet")["stage"])
        self.assertEqual(before, len(self.cloud.posts))

    def test_existing_conflicting_set_and_foreign_members_block(self):
        self.ready()
        for key, value in (("is_validation_set", False), ("fleet", OTHER), ("allow_unknown_components", True)):
            prior = self.cloud.sets[1][key]
            self.cloud.sets[1][key] = value
            self.assertEqual("BLOCKED", self.report()["stage"])
            self.cloud.sets[1][key] = prior
        self.cloud.members = [{"id": OTHER}]
        self.assertEqual("BLOCKED", self.report()["stage"])

    def test_denied_read_is_not_missing_and_sp_failure_preserves_oem_report(self):
        self.cloud.denied = "unit_models_list"
        self.sp.side_effect = CloudFailure("SP_AUTHORITY_NOT_PROVEN")
        result = self.report()
        self.assertEqual("BLOCKED", result["stage"])
        rows = {v["key"]: v for v in result["checks"]}
        self.assertEqual("READY", rows["fleet"]["state"])
        self.assertEqual("BLOCKED", rows["model"]["state"])
        self.assertEqual("BLOCKED", rows["sp"]["state"])
        self.assertEqual([], self.cloud.posts)

    def test_lost_create_response_is_uncertain_not_retried(self):
        self.cloud.lose_response = True
        result = self.step("model")
        self.assertEqual("UNCERTAIN", result["stage"])
        self.assertTrue(result["attempted"])
        self.assertEqual(1, len(self.cloud.posts))

    def test_changed_sp_between_check_and_create_blocks(self):
        self.sp.return_value.user["ownerId"] = OTHER
        self.assertEqual("BLOCKED", self.step("model")["stage"])
        self.assertEqual([], self.cloud.posts)

    def test_private_worker_fields_never_reach_presenter(self):
        value = public_result(dict(operation="cloud.check", data=dict(self.report(), credential="secret", token="secret")))
        self.assertNotIn("owners", value["facts"])
        self.assertNotIn("objects", value["facts"])
        self.assertNotIn("secret", str(value))
        self.assertEqual(8, len(value["facts"]["checks"]))

    def test_terminal_report_includes_each_check_not_just_observed_heading(self):
        from aosedge_demo_orchestrator.cli import render_human
        from aosedge_demo_orchestrator.models import OperationResult, OperationState
        report = dict(self.report(), credential="private-marker")
        value = render_human(OperationResult("cloud.check", OperationState.OBSERVED, "Read-only", data=report))
        self.assertIn("Setup: MISSING", value)
        for row in report["checks"]:
            self.assertIn(row["label"] + ": " + row["state"], value)
        self.assertNotIn("private-marker", value)
        self.ready()
        repeated = render_human(OperationResult("cloud.prepare", OperationState.COMPLETED, "Prepared",
            data=dict(self.report(), noOp=True)))
        self.assertIn("Setup: READY (unchanged)", repeated)

    def test_orchestration_durable_intent_and_repeat(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            env = EnvironmentService(root=root)
            env._directory(".local/demo-control")
            atomic_json(root / CONFIG, dict(schemaVersion=1, cloudProfiles={
                "oem-delivery": dict(credential="/unused/oem.p12", expectedRole="oem"),
                "service-provider": dict(credential="/unused/sp.p12", expectedRole="service provider")}))
            def worker(action, **kw):
                if action == "cloud-setup-check": return self.report()
                stored = read_json(root / CONFIG)["cloudSetupContexts"]
                self.assertEqual("ATTEMPTING", next(iter(stored.values()))["attempts"][kw["step"]]["stage"])
                return self.step(kw["step"])
            units = SimpleNamespace(root=root, environment=env, _cloud=worker, progress=lambda _: None)
            setup = CloudSetup(units)
            with patch.object(setup, "_request", return_value=REQUEST):
                self.assertEqual("READY", setup.prepare()["stage"])
                self.assertTrue(setup.prepare()["noOp"])
            self.assertEqual(2, len(self.cloud.posts))
            config = read_json(root / CONFIG)
            self.assertEqual(OEM, config["cloudProfiles"]["oem-delivery"]["expectedOwnerId"])

    def test_orchestration_unknown_post_blocks_next_call(self):
        with tempfile.TemporaryDirectory() as folder:
            env = EnvironmentService(root=Path(folder)); env._directory(".local/demo-control")
            atomic_json(env.root / CONFIG, dict(schemaVersion=1))
            self.cloud.lose_response = True
            units = SimpleNamespace(root=env.root, environment=env, progress=lambda _: None,
                _cloud=lambda action, **kw: self.report() if action == "cloud-setup-check" else self.step(kw["step"]))
            setup = CloudSetup(units)
            with patch.object(setup, "_request", return_value=REQUEST):
                self.assertEqual("BLOCKED", setup.prepare()["stage"])
                with self.assertRaisesRegex(EnvironmentError, "RECONCILIATION_REQUIRED"):
                    setup.prepare()
            self.assertEqual(1, len(self.cloud.posts))


class IsolationTests(unittest.TestCase):
    def test_owner_change_requires_finish_but_same_owner_renewal_does_not(self):
        with tempfile.TemporaryDirectory() as folder:
            env = EnvironmentService(root=Path(folder))
            env._directory(".local/demo-control")
            env._directory(".run/demo-current")
            atomic_json(env.root / CONFIG, dict(schemaVersion=1,
                cloudConnection=dict(domain=DOMAIN, owners=dict(oem=OEM, sp=SP))))
            atomic_json(env.root / JOURNAL, dict(vehicles={"test": {"unitId": SET}}))
            setup = CloudSetup(SimpleNamespace(root=env.root, environment=env))
            same = dict(stage="READY", owners=dict(oem=OEM, sp=SP), checks=[])
            setup._check_owner_switch(same, apply=True)
            changed = dict(stage="READY", owners=dict(oem=OTHER, sp=SP), checks=[])
            setup._check_owner_switch(changed)
            self.assertEqual("BLOCKED", changed["stage"])
            with self.assertRaisesRegex(EnvironmentError, "REQUIRES_FINISH_TEST"):
                setup._check_owner_switch(changed, apply=True)
            # A completed run leaves no identity to transplant to the new owner.
            atomic_json(env.root / JOURNAL, dict(vehicles={"test": {}}))
            setup._check_owner_switch(changed, apply=True)

    def test_tenant_migration_retains_old_production_and_subjects(self):
        state = dict(cloudBinding=dict(ownerId=OEM, sets={"test": SET, "production": OTHER}),
                     demoSubjects={"brake": {"id": "retained"}})
        original = copy.deepcopy(state)
        bind_tenant(state, "aoscloud.io", {"oem": OEM, "sp": SP})
        self.assertEqual(original["cloudBinding"], cloud_binding(state))
        self.assertEqual(original["demoSubjects"], cloud_subjects(state))
        bind_tenant(state, "aoscloud.io", {"oem": OTHER, "sp": SP})
        self.assertEqual({}, cloud_binding(state))
        self.assertEqual(original["cloudBinding"], state["cloudBinding"])
        bind_tenant(state, "aoscloud.io", {"oem": OEM, "sp": SP})
        self.assertEqual(original["demoSubjects"], cloud_subjects(state))

    def test_owner_scoped_publications_and_same_owner_legacy_receipt(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            legacy = publication_path(directory, DOMAIN, "oem", create=True)
            atomic_json(legacy, dict(ownerId=OEM, cloudDomain=DOMAIN, deploymentId="original", upload={"attemptStarted": True}))
            self.assertEqual(legacy, publication_path(directory, DOMAIN, "oem", owner_id=OEM))
            new = publication_path(directory, DOMAIN, "oem", owner_id=OTHER, create=True)
            self.assertNotEqual(legacy, new)
            self.assertFalse(new.exists())
            self.assertEqual("original", read_json(legacy)["deploymentId"])

    def test_unknown_legacy_owner_cannot_be_silently_republished(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            atomic_json(publication_path(directory, DOMAIN, "oem", create=True), dict(upload={"attemptStarted": True}))
            with self.assertRaisesRegex(EnvironmentError, "RECONCILIATION"):
                publication_path(directory, DOMAIN, "oem", owner_id=OEM)

    def test_test_only_set_and_dual_role_guards(self):
        service = object.__new__(UnitService)
        inventory = dict(ownerId=OEM, sets=[dict(id=SET, title="Test Vehicles", fleet=FLEET, is_validation_set=True)])
        state = dict(vehicles={"test": {}, "production": {}})
        self.assertEqual({"test"}, set(service._bindings(state, inventory, roles=("test",))))
        with self.assertRaisesRegex(EnvironmentError, "production"):
            service._bindings(state, inventory, roles=("test", "production"))

    def test_presenter_actions_are_fixed_and_have_no_browser_authority_selectors(self):
        for action in ("cloud-check", "cloud-prepare"):
            payload = dict(requestId=OEM, sessionId="session", action=action)
            self.assertEqual([dict(domain="cloud", action=action.split("-")[1])], operation_plan(payload)[1])
            with self.assertRaises(ValueError): operation_plan(dict(payload, ownerId=OTHER))


if __name__ == "__main__": unittest.main()
