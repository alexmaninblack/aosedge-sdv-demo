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
from aosedge_demo_orchestrator.models import OperationResult, OperationState


class DemoPreparationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.path = self.root / JOURNAL
        self.path.parent.mkdir(parents=True)
        self.state = dict(factory=dict(sha256="factory"), vehicles=dict(test={}, production={}))
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
            return OperationResult(request.domain + "." + request.action, OperationState.COMPLETED, "done", data=dict(activeVersion="0.0.0"))
        self.app = SimpleNamespace(environment_service=env, vm_service=Mock(), source_service=SimpleNamespace(initialize_test=lambda: None), execute=execute)
        self.workflow = DemoPreparation(self.app, self.component)

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
        self.assertEqual([("component", "inspect"), ("component", "sign"), ("component", "upload"), ("component", "approve"),
            ("vm", "start"), ("unit", "provision"), ("simulation", "start"), ("vehicle", "initialize"), ("component", "status")], self.calls)
        self.calls.clear()
        self.assertTrue(self.workflow.prepare("31/arm64").data["noOp"])
        self.assertEqual([], self.calls)

    def test_blocked_stage_preserves_completed_steps_and_does_not_start_vms(self):
        execute = self.app.execute
        def blocked(request):
            if request.action == "approve":
                return OperationResult("component.approve", OperationState.BLOCKED, "EXACT_BATCH_REQUIRED")
            return execute(request)
        self.app.execute = blocked
        result = self.workflow.prepare("31/arm64")
        self.assertEqual(OperationState.BLOCKED, result.state)
        self.assertEqual("approve-v1", result.data["phase"])
        self.assertEqual(["prepare-v1", "sign-v1", "upload-v1"], result.data["completedSteps"])
        self.assertNotIn(("vm", "start"), self.calls)
