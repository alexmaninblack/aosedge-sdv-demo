# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
import contextlib
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
from aosedge_demo_orchestrator.demo_preparation import DemoPreparation
from aosedge_demo_orchestrator.environment import JOURNAL
from aosedge_demo_orchestrator.models import OperationResult, OperationState, VehicleTarget


class DemoPreparationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.path = self.root / JOURNAL
        self.path.parent.mkdir(parents=True)
        self.state = dict(factory=dict(sha256="factory"), vehicles=dict(test={}))
        self.path.write_text(json.dumps(self.state))
        env = SimpleNamespace(root=self.root, _writer=contextlib.nullcontext,
            catalog=Mock(resolve=Mock(return_value=SimpleNamespace(sha256="factory", problems=[]))))
        self.component = Mock()
        self.component._directory.side_effect = lambda version: self.root / "components" / version
        self.component.list.return_value = dict(components=[dict(version="12.0.0")])
        self.component._worker.return_value = dict(versions=["12.0.0"], latest="12.0.0")
        self.calls = []
        def execute(request):
            self.calls.append((request.domain, request.action))
            return OperationResult(request.domain + "." + request.action, OperationState.COMPLETED, "done", data=dict(activeVersion="0.0.0",
                publication=dict(stage="READY"), deploymentBundles=[dict(state="done")], versions=[dict(state="Ready")]))
        self.app = SimpleNamespace(environment_service=env, vm_service=Mock(), source_service=SimpleNamespace(
            initialize_test=lambda: None, simulation=lambda *a, **k: self.calls.append(("simulation", "start")) or dict(state="RUNNING")), execute=execute)
        self.backends = Mock()
        self.backends._candidate.return_value = dict(imageId="pinned")
        self.backends.start_stack.return_value = dict(state="RUNNING")
        self.workflow = DemoPreparation(self.app, self.component, self.backends)

    def test_plan_selects_next_version_without_native_mutation(self):
        self.assertEqual("13.0.0", self.workflow.plan("31/arm64")["version"])
        self.assertEqual([], self.calls)
        self.assertNotIn("demoPreparation", json.loads(self.path.read_text()))

    def test_reuses_this_runs_v1_and_keeps_order_and_repeat_idempotent(self):
        self.state["componentOperations"] = {"13.0.1": {}}
        self.path.write_text(json.dumps(self.state))
        directory = self.component._directory("13.0.1")
        directory.mkdir(parents=True)
        (directory / "prepared.json").write_text(json.dumps(dict(version="13.0.1", contentProfile="v1")))
        result = self.workflow.prepare("31/arm64")
        self.assertEqual("READY_TO_DRIVE", result.data["phase"])
        self.assertEqual("13.0.1", result.data["version"])
        self.assertEqual([("vm", "start"), ("simulation", "start"), ("vehicle", "initialize"),
            ("component", "inspect"), ("component", "sign"), ("component", "upload"), ("component", "cloud-status"),
            ("unit", "provision"), ("component", "status")], self.calls)
        self.calls.clear()
        self.assertTrue(self.workflow.prepare("31/arm64").data["noOp"])
        self.assertEqual([], self.calls)

    def test_blocked_publication_preserves_running_manual_and_does_not_provision(self):
        execute = self.app.execute
        def blocked(request):
            if request.action == "cloud-status":
                return OperationResult("component.cloud-status", OperationState.BLOCKED, "CLOUD_UNAVAILABLE")
            return execute(request)
        self.app.execute = blocked
        result = self.workflow.prepare("31/arm64")
        self.assertEqual(OperationState.BLOCKED, result.state)
        self.assertEqual("publication", result.data["phase"])
        self.assertEqual(["start-vms", "start-backends", "simulation", "connect-test-manual", "prepare-v1", "sign-v1", "upload-v1"], result.data["completedSteps"])
        self.assertNotIn(("unit", "provision"), self.calls)

    def test_processing_is_not_published_and_retry_does_not_reupload(self):
        execute = self.app.execute
        def processing(request):
            if request.action == "cloud-status":
                return OperationResult("component.cloud-status", OperationState.OBSERVED, "processing",
                    data=dict(publication=dict(stage="PROCESSING"), deploymentBundles=[dict(state="processing")], versions=[]))
            return execute(request)
        self.app.execute = processing
        result = self.workflow.prepare("31/arm64")
        self.assertEqual(OperationState.PARTIAL, result.state)
        self.calls.clear()
        self.app.execute = execute
        self.workflow.prepare("31/arm64")
        self.assertEqual([("component", "cloud-status"), ("unit", "provision"), ("component", "status")], self.calls)

    def test_dual_role_engineering_selection_is_explicit(self):
        self.state["vehicles"]["production"] = {}
        self.path.write_text(json.dumps(self.state))
        self.assertEqual("all", self.workflow.plan("31/arm64", VehicleTarget.ALL)["target"])
        self.state["vehicles"]["production"] = dict(unitId="preserved", systemUid="preserved-uid")
        self.path.write_text(json.dumps(self.state))
        self.assertEqual("test", self.workflow.plan("31/arm64")["target"])

    def test_new_test_plan_can_follow_scoped_retirement_with_production_preserved(self):
        self.state["vehicles"] = dict(production=dict(unitId="preserved"))
        self.state["testRetirement"] = dict(state="COMPLETED")
        self.path.write_text(json.dumps(self.state))
        self.assertFalse(self.workflow.plan("31/arm64")["existingEnvironment"])

    def test_backend_failure_prevents_source_and_cloud_start(self):
        self.backends.start_stack.return_value = dict(state="PARTIAL", reason="TIRE_START_FAILED")
        result = self.workflow.prepare("31/arm64")
        self.assertEqual(OperationState.PARTIAL, result.state)
        self.assertEqual("start-backends", result.data["phase"])
        self.assertEqual([("vm", "start")], self.calls)
