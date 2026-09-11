# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

from aosedge_demo_orchestrator.api import execute_operation
from aosedge_demo_orchestrator.cli import build_parser, request_from_arguments
from aosedge_demo_orchestrator.demo_lifecycle import DemoLifecycle
from aosedge_demo_orchestrator.environment import EnvironmentService, EnvironmentError, JOURNAL, atomic_json
from aosedge_demo_orchestrator.models import OperationResult, OperationState
from aosedge_demo_orchestrator.components import COMPONENT


def completed():
    return OperationResult("fixture", OperationState.COMPLETED, "Observed fixture")


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.catalog = Mock()
        self.catalog.resolve.return_value = SimpleNamespace(problems=[], sha256="sha")
        self.environment = EnvironmentService(self.root, catalog=self.catalog)
        self.environment._directory(".run/demo-current")
        self.state = dict(kind="democtl.current-run", vehicles=dict(test={}, production=dict(unitId="preserved")),
            currentVehicle=None, operations=[dict(state="COMPLETED")], factory=dict(sha256="sha"))
        self.write()
        self.app = Mock()
        self.app.environment_service = self.environment
        self.app.execute.return_value = completed()
        self.app.vm_service.observe_readiness.return_value = dict(state="CURRENT", guestReady=True, guestDnsReady=True)
        self.backends = Mock()
        self.backends._candidate.return_value = dict(imageId="immutable")
        self.backends.start_stack.return_value = dict(state="RUNNING")
        self.backends.stop_stack.return_value = dict(state="STOPPED")
        self.backends.observe_stack.return_value = dict(state="CURRENT")
        self.app.source_service.simulation.side_effect = self.simulation
        self.workflow = DemoLifecycle(self.app, self.backends)
        from aosedge_demo_orchestrator.cloud_observation import SECTIONS
        self.observed = {key: dict(state="CURRENT", value=[]) for key in SECTIONS}
        self.observed["serviceDetails"] = {}
        self.app.unit_service.observe.return_value = self.observed

    def write(self):
        atomic_json(self.root / JOURNAL, self.state)

    def simulation(self, action, target):
        self.assertEqual("test", target)
        state = self.read()
        state["currentVehicle"] = None
        state["source"] = dict(state="RUNNING" if action == "start" else "STOPPED")
        atomic_json(self.root / JOURNAL, state)
        return dict(state="RUNNING" if action == "start" else "STOPPED")

    def read(self):
        return json.loads((self.root / JOURNAL).read_text())

    def provisioned(self):
        self.state["vehicles"]["test"]["unitId"] = "test-unit"
        self.state.update(currentVehicle="test", source=dict(state="RUNNING"))
        self.write()

    def test_create_boots_only_test_and_backends_without_cloud_or_simulation(self):
        result = self.workflow.create("factory/arch")
        self.assertEqual("CONTROLLER_RUNNING", result.data["phase"])
        request = self.app.execute.call_args.args[0]
        self.assertEqual(("vm", "start", "test"), (request.domain, request.action, request.target.value))
        self.backends.start_stack.assert_called_once()
        self.app.unit_service.observe.assert_not_called()
        self.app.source_service.simulation.assert_not_called()
        self.assertEqual(self.state["vehicles"]["production"], self.read()["vehicles"]["production"])
        self.app.execute.reset_mock()
        self.assertTrue(self.workflow.create("factory/arch").data["noOp"])
        self.app.execute.assert_not_called()

    def test_repeated_create_reads_current_readiness_without_replaying_steps(self):
        self.workflow.create("factory/arch")
        saved = (self.root / JOURNAL).read_bytes()
        self.app.execute.reset_mock()
        self.backends.start_stack.reset_mock()
        self.app.vm_service.observe_readiness.return_value = dict(state="UNKNOWN", reason="VM_NOT_RUNNING")
        result = self.workflow.create("factory/arch")
        self.assertEqual(OperationState.PARTIAL, result.state)
        self.assertEqual("INCOMPLETE", result.data["readiness"]["state"])
        self.app.vm_service.observe_readiness.assert_called_once_with("test")
        self.app.execute.assert_not_called()
        self.backends.start_stack.assert_not_called()
        self.app.unit_service.observe.assert_not_called()
        self.assertEqual(saved, (self.root / JOURNAL).read_bytes())

    def test_create_missing_backend_does_not_start_vm(self):
        self.backends._candidate.side_effect = EnvironmentError("MISSING_BACKEND")
        with self.assertRaisesRegex(EnvironmentError, "MISSING_BACKEND"):
            self.workflow.create("factory/arch")
        self.app.execute.assert_not_called()

    def test_retire_preserves_per_service_subject_records_until_cleanup_integration(self):
        self.provisioned()
        self.state["demoSubjects"] = {"brake-id": dict(id="retained-brake")}
        self.write()
        with self.assertRaisesRegex(EnvironmentError, "SUBJECT_RETIREMENT_INTEGRATION_REQUIRED"):
            self.workflow.retire()
        self.assertEqual(self.state["demoSubjects"], self.read()["demoSubjects"])
        self.app.execute.assert_not_called()
        self.backends.stop_stack.assert_not_called()

    def test_partial_create_resumes_same_owned_step_not_another_vm(self):
        self.backends.start_stack.return_value = dict(state="PARTIAL", reason="TIRE_FAILED")
        self.assertEqual(OperationState.PARTIAL, self.workflow.create("factory/arch").state)
        self.backends.start_stack.return_value = dict(state="RUNNING")
        self.assertEqual(OperationState.COMPLETED, self.workflow.create("factory/arch").state)
        self.app.execute.assert_called_once()

    def test_create_does_not_adopt_current_provisioned_test(self):
        self.provisioned()
        with self.assertRaisesRegex(EnvironmentError, "CANNOT_ADOPT_PROVISIONED"):
            self.workflow.create("factory/arch")
        self.backends.start_stack.assert_not_called()

    def test_park_stops_source_test_backends_in_order_and_retains_identity(self):
        self.provisioned()
        order = []
        simulation = self.simulation
        self.app.source_service.simulation.side_effect = lambda *a, **k: order.append("source") or simulation(*a, **k)
        self.app.execute.side_effect = lambda req: order.append(req.domain + "." + req.action + ":" + req.target.value) or completed()
        self.backends.stop_stack.side_effect = lambda: order.append("backends") or dict(state="STOPPED")
        self.assertEqual("PARKED", self.workflow.park().data["phase"])
        self.assertEqual(["source", "vm.stop:test", "backends"], order)
        self.assertEqual(self.state["vehicles"], self.read()["vehicles"])
        self.assertEqual("test", self.read()["demoLifecycle"]["retainedConnection"])

    def test_pending_component_refuses_before_safe_stop_or_any_shutdown(self):
        self.provisioned()
        self.observed["components"]["value"] = [dict(pending_component=dict(version="next"))]
        with self.assertRaisesRegex(EnvironmentError, "COMPONENT_UPDATE_PENDING"):
            self.workflow.park()
        self.app.source_service.simulation.assert_not_called()
        self.app.execute.assert_not_called()
        self.backends.stop_stack.assert_not_called()
        self.assertNotIn("demoLifecycle", self.read())

    def test_pending_service_and_unknown_cloud_refuse_without_mutation(self):
        self.provisioned()
        self.observed["services"]["value"] = [dict(service_versions=dict(pending_service_version_id="new"))]
        with self.assertRaisesRegex(EnvironmentError, "SERVICE_UPDATE_PENDING"):
            self.workflow.park()
        self.observed["services"] = dict(state="STALE", value=[])
        with self.assertRaisesRegex(EnvironmentError, "UPDATE_STATE_NOT_CURRENT"):
            self.workflow.park()
        self.app.execute.assert_not_called()
        self.backends.stop_stack.assert_not_called()

    def test_published_not_dispatched_update_cannot_be_hidden_by_empty_pending(self):
        self.provisioned()
        self.state["componentOperations"] = {"20.0.0": dict(upload=dict(attemptStarted=True), deploymentId="bundle", publication=dict(stage="READY"))}
        self.write()
        self.observed["components"]["value"] = [dict(type=COMPONENT, installed_component=dict(version="19.0.0"))]
        with self.assertRaisesRegex(EnvironmentError, "PUBLISHED_COMPONENT_NOT_INSTALLED"):
            self.workflow.park()
        self.observed["components"]["value"][0]["installed_component"]["version"] = "20.0.0"
        self.assertEqual("PARKED", self.workflow.park().data["phase"])

    def test_selected_production_refuses_before_every_external_read_or_mutation(self):
        self.state["currentVehicle"] = "production"
        self.write()
        with self.assertRaisesRegex(EnvironmentError, "SELECTED_PRODUCTION"):
            self.workflow.park()
        self.app.unit_service.observe.assert_not_called()
        self.app.source_service.simulation.assert_not_called()

    def test_resume_restores_same_identity_only_previously_connected_source(self):
        self.provisioned()
        self.workflow.park()
        self.app.execute.reset_mock()
        result = self.workflow.resume()
        self.assertEqual("RESUMED", result.data["phase"])
        requests = [call.args[0] for call in self.app.execute.call_args_list]
        self.assertEqual([("vm", "start"), ("vehicle", "initialize")], [(r.domain, r.action) for r in requests])
        self.assertTrue(all(r.target.value == "test" for r in requests))
        self.assertEqual(self.state["vehicles"], self.read()["vehicles"])
        self.backends.start_stack.assert_called_once()

    def test_partially_prepared_resume_does_not_provision_or_attach(self):
        self.workflow.park()
        self.app.execute.reset_mock()
        self.app.source_service.simulation.reset_mock()
        self.workflow.resume()
        self.app.source_service.simulation.assert_not_called()
        request = self.app.execute.call_args.args[0]
        self.assertEqual(("vm", "start"), (request.domain, request.action))
        self.assertNotIn("unitId", self.read()["vehicles"]["test"])

    def test_resume_read_failure_retries_observation_not_startup(self):
        self.provisioned()
        self.workflow.park()
        self.observed["unit"] = dict(state="UNKNOWN", value=None)
        self.assertEqual(OperationState.PARTIAL, self.workflow.resume().state)
        self.app.execute.reset_mock()
        self.app.unit_service.observe.reset_mock()
        self.backends.start_stack.reset_mock()
        self.observed["unit"] = dict(state="CURRENT", value={})
        result = self.workflow.resume()
        self.assertTrue(result.data["noOp"])
        self.app.execute.assert_not_called()
        self.backends.start_stack.assert_not_called()
        self.app.unit_service.observe.assert_called_once_with("cloud-status", "test")

    def test_optional_not_reported_inventory_does_not_block_resume(self):
        self.provisioned()
        self.workflow.park()
        self.observed["layers"] = dict(state="UNKNOWN", reason="NOT_REPORTED", value=None)
        result = self.workflow.resume()
        self.assertEqual(OperationState.COMPLETED, result.state)
        self.assertIsNone(result.data["cloud"]["layers"]["value"])

    def test_cli_and_api_share_fixed_scope_and_no_operator_capabilities(self):
        for action in ("create", "retire", "park", "resume"):
            domain = "demo" if action in ("create", "retire") else "environment"
            args = [domain, action] + (["--image", "factory/arch"] if action == "create" else [])
            request = request_from_arguments(build_parser().parse_args(args))
            self.assertEqual(action, request.action)
            payload = dict(domain=domain, action=action)
            if action == "create":
                payload["image"] = "factory/arch"
            app = Mock()
            execute_operation(payload, app)
            self.assertEqual(request, app.execute.call_args.args[0])
            with self.assertRaises(ValueError):
                execute_operation(dict(payload, target="production"), app)

    def test_retire_orders_cloud_before_backend_data_and_overlay_removal(self):
        self.provisioned()
        order = []
        self.app.execute.side_effect = lambda req: order.append(req.domain + "." + req.action + ":" + req.target.value) or completed()
        def leaf(**kwargs):
            self.assertEqual(self.app.unit_service.confirm_test_retired, kwargs["cloud_check"])
            self.assertEqual(self.workflow._backend_cleanup, kwargs["backend_check"])
            order.append("data-and-overlay")
            state = self.read()
            state["vehicles"].pop("test")
            atomic_json(self.root / JOURNAL, state)
            return dict(removed=["owned-test-overlay"], productionPreserved=True)
        self.environment.retire_test = Mock(side_effect=leaf)
        result = self.workflow.retire()
        self.assertEqual("RETIRED", result.data["phase"])
        self.assertEqual(["unit.deprovision:test", "unit.delete:test", "vm.stop:test", "data-and-overlay"], order)
        self.assertEqual({"production": dict(unitId="preserved")}, self.read()["vehicles"])
        self.assertNotIn("demoLifecycle", self.read())

    def test_retire_partial_local_cleanup_does_not_replay_completed_cloud_mutations(self):
        self.provisioned()
        self.environment.retire_test = Mock(side_effect=[EnvironmentError("DATA_CLEANUP_PENDING"), dict(removed=[])])
        result = self.workflow.retire()
        self.assertEqual(OperationState.PARTIAL, result.state)
        self.assertEqual("test-unit", self.read()["vehicles"]["test"]["unitId"])
        self.app.execute.reset_mock()
        self.assertEqual(OperationState.COMPLETED, self.workflow.retire().state)
        self.app.execute.assert_not_called()
        self.assertEqual(2, self.environment.retire_test.call_count)

    def test_never_provisioned_retire_does_not_call_cloud(self):
        self.environment.retire_test = Mock(return_value=dict(removed=[]))
        self.workflow.retire()
        request = self.app.execute.call_args.args[0]
        self.assertEqual(("vm", "stop"), (request.domain, request.action))
        self.app.execute.assert_called_once()
        self.app.unit_service.observe.assert_not_called()

    def test_pending_update_prevents_retire_from_implicitly_entering_safe_stop(self):
        self.provisioned()
        self.observed["components"]["value"] = [dict(pending_component=dict(version="next"))]
        with self.assertRaisesRegex(EnvironmentError, "UPDATE_PENDING"):
            self.workflow.retire()
        self.app.source_service.simulation.assert_not_called()
        self.app.execute.assert_not_called()
