# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import copy
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from aosedge_demo_orchestrator.api import execute_operation
from aosedge_demo_orchestrator.cli import build_parser, request_from_arguments
from aosedge_demo_orchestrator.demo_lifecycle import DemoLifecycle
from aosedge_demo_orchestrator.environment import EnvironmentService, EnvironmentError, JOURNAL, atomic_json
from aosedge_demo_orchestrator.models import OperationResult, OperationState
from aosedge_demo_orchestrator.components import COMPONENT, ComponentService


def completed():
    return OperationResult("fixture", OperationState.COMPLETED, "Observed fixture")


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.catalog = Mock()
        self.catalog.project = self.root
        self.catalog.resolve.return_value = SimpleNamespace(problems=[], sha256="sha")
        self.environment = EnvironmentService(self.root, catalog=self.catalog)
        self.environment._directory(".run/demo-current")
        self.state = dict(kind="democtl.current-run", vehicles=dict(test={}, production=dict(unitId="preserved")),
            currentVehicle=None, operations=[dict(state="COMPLETED")], factory=dict(sha256="sha",
                format="raw", path=".local/factory/oem-demo-factory.img", manifestPath=".local/factory/oem-demo-factory.manifest.json"))
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
        self.app.unit_service.confirm_unassigned_subjects.return_value = True
        cm_patch = patch.object(ComponentService, "cm_status")
        self.cm_status = cm_patch.start()
        self.addCleanup(cm_patch.stop)
        self.cm_status.return_value = dict(service=dict(ActiveState="active", Result="success"),
            delivery=dict(mutation=False, storedDesired=dict(state="none", payload=dict(itemsCount=0, items=[]))))
        self.app.source_service.observe.return_value = dict(selectedVehicle="test", controller=dict(fresh=True,
            frame=dict(activeMode="SAFE_STOP", speedKmh=0, brake=1)))

    def write(self):
        atomic_json(self.root / JOURNAL, self.state)

    def simulation(self, action, target, **kwargs):
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

    def test_retire_preserves_unresolved_subject_records(self):
        self.provisioned()
        self.state["demoSubjects"] = {"brake-id": dict(id="retained-brake")}
        self.write()
        result = self.workflow.retire()
        self.assertEqual("SERVICE_RETIREMENT_BINDINGS_REQUIRE_RECONCILIATION", result.data["reason"])
        self.assertEqual(["stop-simulation", "stop-test", "stop-backends"], result.data["completedSteps"])
        self.assertEqual(self.state["demoSubjects"], self.read()["demoSubjects"])
        self.assertEqual("stop", self.app.execute.call_args.args[0].action)
        self.backends.stop_stack.assert_called_once()

    def test_retire_unused_subjects_reconciles_after_local_shutdown(self):
        self.provisioned()
        self.environment.retire_test = Mock(return_value=dict(removed=[]))
        self.app.unit_service.confirm_unassigned_subjects.side_effect = EnvironmentError("SERVICE_RETIRED_SUBJECT_STILL_HAS_UNITS")
        first = self.workflow.retire()
        self.assertEqual("reconcile-subjects", first.data["phase"])
        self.assertIn("STILL_HAS_UNITS", first.data["reason"])
        self.assertEqual(["stop-simulation", "stop-test", "stop-backends"], first.data["completedSteps"])
        self.app.unit_service.confirm_unassigned_subjects.side_effect = None
        self.assertEqual("RETIRED", self.workflow.retire().data["phase"])

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
        self.assertEqual(["vm.stop:test", "unit.deprovision:test", "unit.delete:test", "data-and-overlay"], order)
        self.assertEqual({"production": dict(unitId="preserved")}, self.read()["vehicles"])
        self.assertNotIn("demoLifecycle", self.read())

    def test_retire_partial_local_cleanup_does_not_replay_completed_cloud_mutations(self):
        self.provisioned()
        self.environment.retire_test = Mock(side_effect=[EnvironmentError("DATA_CLEANUP_PENDING"), dict(removed=[])])
        result = self.workflow.retire()
        self.assertEqual(OperationState.PARTIAL, result.state)
        self.assertEqual("test-unit", self.read()["vehicles"]["test"]["unitId"])
        self.app.execute.reset_mock()
        resumed = self.workflow.retire()
        self.assertEqual(OperationState.COMPLETED, resumed.state)
        self.assertNotIn("reason", resumed.data)
        self.app.execute.assert_not_called()
        self.assertEqual(2, self.environment.retire_test.call_count)

    def test_cloud_only_finish_resumes_each_failed_phase_without_replaying_completed_steps(self):
        initial = copy.deepcopy(self.state)
        phases = ["stop-simulation", "stop-test", "stop-backends", "reconcile-subjects", "deprovision-test", "delete-test",
            "start-cleanup-backends", "bind-cleanup-context", "local-cleanup"]
        for failed_phase in phases:
            with self.subTest(phase=failed_phase):
                self.state = copy.deepcopy(initial)
                self.cloud_only_update()
                self.state["vehicles"]["test"]["systemUid"] = "test-uid"
                self.write()
                calls = []
                def step(phase):
                    calls.append(phase)
                    if phase == failed_phase and calls.count(phase) == 1:
                        raise EnvironmentError("INJECTED_PARTIAL_" + phase)
                def source(action, target, **kwargs):
                    step("stop-simulation")
                    return self.simulation(action, target)
                def backend():
                    step("start-cleanup-backends")
                    return dict(state="RUNNING")
                def command(request):
                    step({"deprovision": "deprovision-test", "delete": "delete-test", "stop": "stop-test"}[request.action])
                    self.assertEqual("test", request.target.value)
                    return completed()
                def local(**kwargs):
                    step("local-cleanup")
                    current = self.read()
                    current["vehicles"].pop("test")
                    atomic_json(self.root / JOURNAL, current)
                    return dict(removed=["owned-test-overlay"])
                self.app.source_service.simulation.side_effect = source
                self.app.unit_service.confirm_unassigned_subjects.side_effect = lambda state: step("reconcile-subjects") or True
                self.backends.start_stack.side_effect = backend
                self.backends.stop_stack.side_effect = lambda: step("stop-backends") or dict(state="STOPPED")
                self.app.execute.side_effect = command
                self.environment.retire_test.side_effect = local
                with patch("aosedge_demo_orchestrator.backend_context.sync_context",
                        side_effect=lambda *args: step("bind-cleanup-context")):
                    first = self.workflow.retire()
                    self.assertEqual(OperationState.PARTIAL, first.state)
                    self.assertIn("test", self.read()["vehicles"])
                    second = self.workflow.retire()
                self.assertEqual(OperationState.COMPLETED, second.state)
                index = phases.index(failed_phase)
                self.assertEqual(phases[:index + 1] + phases[index:], calls)
                self.assertEqual(initial["vehicles"]["production"], self.read()["vehicles"]["production"])
                self.assertNotIn("demoLifecycle", self.read())

    def test_never_provisioned_retire_does_not_call_cloud(self):
        self.environment.retire_test = Mock(return_value=dict(removed=[]))
        self.workflow.retire()
        request = self.app.execute.call_args.args[0]
        self.assertEqual(("vm", "stop"), (request.domain, request.action))
        self.app.execute.assert_called_once()
        self.app.unit_service.observe.assert_not_called()

    def test_retire_preserves_exact_leaf_reason_for_ui_continuation(self):
        self.provisioned()
        failure = OperationResult("unit.deprovision", OperationState.PARTIAL,
            "Current-run Unit operation", data=dict(vehicles=dict(test=dict(
                state="BLOCKED", reason="UNIT_WAIT_TIMEOUT:CLOUD_OFFLINE"))))
        self.app.execute.side_effect = lambda req: failure if req.action == "deprovision" else completed()
        result = self.workflow.retire()
        self.assertEqual("deprovision-test", result.data["phase"])
        self.assertEqual("UNIT_WAIT_TIMEOUT:CLOUD_OFFLINE", result.data["reason"])
        self.assertEqual(result.data["reason"], self.read()["demoLifecycle"]["reason"])

    def test_pending_update_does_not_block_terminal_retirement(self):
        self.provisioned()
        self.observed["components"]["value"] = [dict(pending_component=dict(version="next"))]
        self.environment.retire_test = Mock(return_value=dict(removed=[]))
        self.assertEqual("RETIRED", self.workflow.retire().data["phase"])
        self.app.source_service.simulation.assert_called_once_with("stop", target="test", retiring=True)
        self.app.unit_service.observe.assert_not_called()

    def cloud_only_update(self):
        self.provisioned()
        self.observed["components"]["value"] = [dict(type=COMPONENT,
            installed_component=dict(version="0.0.0"), pending_component=dict(version="37.0.0"),
            pending_component_status="to be installed", pending_component_error=None)]
        self.state["componentOperations"] = {"37.0.0": dict(upload=dict(attemptStarted=True),
            deploymentId="existing-bundle", publication=dict(stage="READY"))}
        self.write()
        self.environment.retire_test = Mock(return_value=dict(removed=[]))

    def test_retire_cloud_only_update_preserves_release_and_production(self):
        self.cloud_only_update()
        result = self.workflow.retire()
        self.assertEqual("RETIRED", result.data["phase"])
        self.cm_status.assert_not_called()
        self.app.source_service.observe.assert_not_called()
        self.app.source_service.simulation.assert_called_once_with("stop", target="test", retiring=True)
        requests = [call.args[0] for call in self.app.execute.call_args_list]
        self.assertEqual([("vm", "stop"), ("unit", "deprovision"), ("unit", "delete")],
            [(r.domain, r.action) for r in requests])
        self.assertTrue(all(r.target.value == "test" for r in requests))
        self.assertEqual(self.state["componentOperations"], self.read()["componentOperations"])
        self.assertEqual(self.state["vehicles"]["production"], self.read()["vehicles"]["production"])

    def test_park_still_refuses_the_same_cloud_only_update(self):
        self.cloud_only_update()
        with self.assertRaisesRegex(EnvironmentError, "COMPONENT_UPDATE_PENDING"):
            self.workflow.park()
        self.cm_status.assert_not_called()
        self.app.execute.assert_not_called()

    def test_retire_pending_failure_other_component_and_unknown_status_do_not_gate_shutdown(self):
        for changes in (dict(pending_component_error="failed"), dict(type="rootfs"),
                        dict(pending_component_status="installing"), dict(pending_component_status=None)):
            with self.subTest(changes=changes):
                self.cloud_only_update()
                self.observed["components"]["value"][0].update(changes)
                self.assertEqual("RETIRED", self.workflow.retire().data["phase"])
        self.cm_status.assert_not_called()
        self.app.unit_service.observe.assert_not_called()

    def test_retire_does_not_depend_on_monitoring_or_service_readiness(self):
        self.cloud_only_update()
        self.observed["components"]["state"] = "STALE"
        self.assertEqual("RETIRED", self.workflow.retire().data["phase"])
        self.observed["components"]["state"] = "CURRENT"
        self.observed["services"]["value"] = [dict(service_versions=dict(pending_service_version_id="next"))]
        self.assertEqual("RETIRED", self.workflow.retire().data["phase"])
        self.cm_status.assert_not_called()
        self.app.unit_service.observe.assert_not_called()

    def test_retire_native_active_unknown_or_already_received_does_not_block(self):
        self.cloud_only_update()
        desired = self.cm_status.return_value["delivery"]["storedDesired"]
        for phase in ("downloading", "pending", "installing", "launching", "activating", "finalizing", "UNKNOWN", "UNAVAILABLE"):
            with self.subTest(phase=phase):
                desired["state"] = phase
                self.assertEqual("RETIRED", self.workflow.retire().data["phase"])
        desired["state"] = "none"
        for payload in ({}, dict(itemsCount=1, items=[]), dict(itemsCount=1, items=[{}]),
                        dict(itemsCount=1, items=[dict(version="37.0.0")])):
            with self.subTest(payload=payload):
                desired["payload"] = payload
                self.assertEqual("RETIRED", self.workflow.retire().data["phase"])
        self.cm_status.assert_not_called()
        self.assertNotIn("demoLifecycle", self.read())

    def test_retire_pending_unavailable_guest_or_inactive_cm_needs_no_cm_probe(self):
        self.cloud_only_update()
        self.cm_status.side_effect = EnvironmentError("SOURCE_GUEST_UNAVAILABLE:test")
        self.assertEqual("RETIRED", self.workflow.retire().data["phase"])
        self.cm_status.side_effect = None
        self.cm_status.return_value["service"]["ActiveState"] = "inactive"
        self.assertEqual("RETIRED", self.workflow.retire().data["phase"])
        self.cm_status.assert_not_called()

    def test_retire_can_destroy_simulator_from_any_driving_mode(self):
        self.cloud_only_update()
        for frame in (dict(activeMode="AUTOPILOT", speedKmh=20, brake=0),
                      dict(activeMode="MANUAL", speedKmh=0, brake=1),
                      dict(activeMode="SAFE_STOP", speedKmh=2, brake=1), {}):
            with self.subTest(frame=frame):
                self.app.source_service.observe.return_value = dict(selectedVehicle="test",
                    controller=dict(fresh=True, frame=frame))
                self.assertEqual("RETIRED", self.workflow.retire().data["phase"])
        self.app.source_service.observe.assert_not_called()

    def test_retire_pending_allows_detached_source_without_new_safe_stop_probe(self):
        self.cloud_only_update()
        self.state["currentVehicle"] = None
        self.write()
        self.assertEqual("RETIRED", self.workflow.retire().data["phase"])
        self.app.source_service.observe.assert_not_called()

    def test_retire_pending_can_have_previous_installed_desired_items(self):
        self.cloud_only_update()
        self.cm_status.return_value["delivery"]["storedDesired"]["payload"] = dict(itemsCount=1,
            items=[dict(itemId=COMPONENT, version="36.0.0")])
        self.assertEqual("RETIRED", self.workflow.retire().data["phase"])

    def test_retire_pending_partial_source_stop_resumes_despite_native_failure(self):
        self.cloud_only_update()
        self.app.source_service.simulation.side_effect = EnvironmentError("SOURCE_STOP_INCOMPLETE")
        self.assertEqual(OperationState.PARTIAL, self.workflow.retire().state)
        self.cm_status.return_value["delivery"]["storedDesired"]["state"] = "installing"
        self.assertEqual(OperationState.PARTIAL, self.workflow.retire().state)
        self.assertEqual(2, self.app.source_service.simulation.call_count)
        self.app.execute.assert_not_called()
        self.cm_status.return_value["delivery"]["storedDesired"]["state"] = "none"
        self.app.source_service.simulation.side_effect = self.simulation
        self.assertEqual("RETIRED", self.workflow.retire().data["phase"])
        self.cm_status.assert_not_called()

    def test_retire_does_not_wait_for_successful_publication(self):
        for stage in ("ACCEPTED", "PROCESSING", "ERROR", "UNKNOWN"):
            with self.subTest(stage=stage), patch.object(ComponentService, "cloud_status") as probe:
                self.cloud_only_update()
                self.state["componentOperations"]["37.0.0"]["publication"]["stage"] = stage
                self.write()
                self.assertEqual("RETIRED", self.workflow.retire().data["phase"])
                probe.assert_not_called()

    def test_retire_preserves_selected_production(self):
        self.provisioned()
        self.state["currentVehicle"] = "production"
        self.write()
        with self.assertRaisesRegex(EnvironmentError, "PRESERVES_SELECTED_PRODUCTION"):
            self.workflow.retire()
        self.app.execute.assert_not_called()
        self.app.source_service.simulation.assert_not_called()
