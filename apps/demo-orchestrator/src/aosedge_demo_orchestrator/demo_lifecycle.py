# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Studio lifecycle composition over the existing Test-only operations."""

from .backends import BackendService, TEAMS
from .components import COMPONENT, ComponentService
from .environment import EnvironmentError, JOURNAL, atomic_json
from .models import OperationRequest, OperationResult, OperationState, VehicleTarget
from .releases import number
from .status import now, read_json


class DemoLifecycle:
    def __init__(self, application, backends=None):
        self.app = application
        self.environment = application.environment_service
        self.path = self.environment.root / JOURNAL
        self.backends = backends or BackendService(self.environment, application.vm_service.progress)
        self.progress = application.vm_service.progress

    def _state(self):
        state = read_json(self.path)
        if state.get("kind") != "democtl.current-run" or "test" not in state.get("vehicles", {}):
            raise EnvironmentError("DEMO_CURRENT_TEST_REQUIRED")
        if state.get("currentVehicle") not in (None, "test"):
            raise EnvironmentError("DEMO_PRESERVES_SELECTED_PRODUCTION")
        return state

    def _save(self, record):
        state = self._state()
        record["updatedAt"] = now()
        state["demoLifecycle"] = record
        atomic_json(self.path, state)

    def _record(self, action, **values):
        return dict(schemaVersion=1, target="test", action=action, state="IN_PROGRESS",
                    completedSteps=[], **values)

    def _steps(self, record, steps, final):
        for phase, operation in steps:
            if phase in record["completedSteps"]:
                continue
            record.update(phase=phase, state="IN_PROGRESS")
            self._save(record)
            self.progress("Test demo: " + phase)
            try:
                result = operation()
            except EnvironmentError as error:
                record.update(state="PARTIAL", reason=str(error))
                self._save(record)
                return self._result(record)
            if isinstance(result, OperationResult):
                succeeded = result.state in (OperationState.COMPLETED, OperationState.OBSERVED)
                reason = result.message
            else:
                succeeded = result.get("state") in ("RUNNING", "STOPPED", "COMPLETED")
                reason = result.get("reason", "DEMO_STEP_NOT_CONFIRMED")
            if not succeeded:
                record.update(state="PARTIAL", reason=reason)
                self._save(record)
                return self._result(record)
            record["completedSteps"].append(phase)
            record.pop("reason", None)
            self._save(record)
        record.update(state="COMPLETED", phase=final)
        self._save(record)
        return self._result(record)

    def _result(self, record, **extra):
        return OperationResult(("demo." if record["action"] in ("create", "retire") else "environment.") + record["action"],
            OperationState.COMPLETED if record["state"] == "COMPLETED" else OperationState.PARTIAL,
            "Owned Test lifecycle only; Cloud Online, installed software and product readiness are separate observations.",
            target="test", data=dict(record, productionPreserved=True, **extra))

    def _vm(self, action):
        return self.app.execute(OperationRequest("vm", action, VehicleTarget.TEST, timeout=90))

    def readiness(self, source=False, cloud=False):
        """Current evidence, not a replay of a completed preparation journal."""
        values = dict(vm=self.app.vm_service.observe_readiness("test"), backends=self.backends.observe_stack())
        current = all(value.get("state") == "CURRENT" for value in values.values())
        if source:
            # Local controller/selection only. Do not claim a guest connection
            # from a remembered selection or inspect the preserved Production VM.
            values["source"] = self.app.source_service.observe(guest=False, timeout=5)
            current = current and values["source"].get("state") == "SELECTED_NOT_PROBED" and (
                values["source"].get("selectedVehicle") == "test" and
                values["source"].get("controller", {}).get("fresh") is True)
        if cloud:
            values["cloud"] = self.app.unit_service.observe("cloud-status", "test")
            current = current and values["cloud"].get("unit", {}).get("state") == "CURRENT"
        return dict(state="CURRENT" if current else "INCOMPLETE", observedAt=now(), observations=values,
            connection="NOT_RECHECKED", productReadiness="NOT_OBSERVED")

    def create(self, image):
        with self.environment._writer():
            candidate = self.environment.catalog.resolve(image)
            if candidate.problems:
                raise EnvironmentError("DEMO_FACTORY_IMAGE_UNAVAILABLE")
            state = read_json(self.path) if self.path.exists() else None
            record = (state or {}).get("demoLifecycle")
            if state and "test" in state.get("vehicles", {}):
                self._state()
                if state.get("factory", {}).get("sha256") != candidate.sha256:
                    raise EnvironmentError("DEMO_EXISTING_FACTORY_CONFLICT")
                if record and (record.get("action") != "create" or record.get("image") != image):
                    raise EnvironmentError("DEMO_EXISTING_CONTROLLER_USE_RESUME_OR_RETIRE")
                if record and record.get("state") == "COMPLETED":
                    readiness = self.readiness()
                    return OperationResult("demo.create", OperationState.OBSERVED if readiness["state"] == "CURRENT" else OperationState.PARTIAL,
                        "Previous creation retained; one current VM/backend observation, no restart or repeated creation.", target="test",
                        data=dict(record, noOp=True, productionPreserved=True, readiness=readiness))
                if state["vehicles"]["test"].get("unitId"):
                    raise EnvironmentError("DEMO_CREATE_CANNOT_ADOPT_PROVISIONED_TEST")
            # Immutable backend inputs are required before starting any VM.
            for team in TEAMS:
                self.backends._image(self.backends._candidate(team)["imageId"])
            if not state or "test" not in state.get("vehicles", {}):
                self.environment.create("test", image)
                record = None
            record = record or self._record("create", image=image)
            return self._steps(record, [("start-test", lambda: self._vm("start")),
                ("start-backends", self.backends.start_stack)], "CONTROLLER_RUNNING")

    def _park_guard(self, state):
        # This is a one-shot action guard, not polling or a scheduled shutdown.
        pending = state.get("operations", [])[1:]
        previous = state.get("demoLifecycle") or {}
        owned_stop = (previous.get("action") == "park" and previous.get("phase") == "stop-test"
            and previous.get("state") == "PARTIAL" and len(pending) == 1
            and pending[0].get("class") == "VM_STOP" and pending[0].get("target") == ["test"])
        if (pending and not owned_stop) or (state.get("source") or {}).get("operation"):
            raise EnvironmentError("DEMO_CONFLICTING_OPERATION_RECONCILIATION_REQUIRED")
        attempted = [(version, item) for version, item in state.get("componentOperations", {}).items()
                     if item.get("upload", {}).get("attemptStarted")]
        for version, item in attempted:
            if not item.get("deploymentId"):
                raise EnvironmentError("DEMO_PUBLICATION_RECONCILIATION_REQUIRED:" + version)
            if item.get("publication", {}).get("stage") != "READY":
                value = ComponentService(self.environment).cloud_status(version)
                if value.get("publication", {}).get("stage") != "READY":
                    raise EnvironmentError("DEMO_PUBLICATION_NOT_COMPLETE:" + version)
        if not state["vehicles"]["test"].get("unitId"):
            return
        observed = self.app.unit_service.observe("cloud-status", "test")
        sections = [observed.get(key, {}) for key in ("components", "services")]
        sections += list(observed.get("serviceDetails", {}).values())
        if any(section.get("state") != "CURRENT" or not isinstance(section.get("value"), list) for section in sections):
            raise EnvironmentError("DEMO_UPDATE_STATE_NOT_CURRENT")
        components = sections[0]["value"]
        if any(row.get("pending_component") or row.get("pending_component_error") for row in components):
            raise EnvironmentError("DEMO_COMPONENT_UPDATE_PENDING_OR_FAILED")
        for section in sections[1:]:
            for row in section["value"]:
                versions = row.get("service_versions") or {}
                if (versions.get("pending_service_version_id") or versions.get("pending_service_version")
                        or row.get("pending_num_instance") not in (None, row.get("num_instance"))):
                    raise EnvironmentError("DEMO_SERVICE_UPDATE_PENDING")
        if attempted:
            latest = max((version for version, _ in attempted), key=number)
            installed = [row.get("installed_component") or {} for row in components
                         if row.get("type") == COMPONENT]
            if not any(item.get("version") and number(item["version"]) >= number(latest) for item in installed):
                raise EnvironmentError("DEMO_PUBLISHED_COMPONENT_NOT_INSTALLED:" + latest)

    def park(self):
        with self.environment._writer():
            state = self._state()
            self._park_guard(state)  # before Safe Stop, detach, VM or backend stop
            previous = state.get("demoLifecycle") or {}
            if previous.get("action") == "park" and previous.get("state") == "PARTIAL":
                # Existing child primitives reconcile their exact owned state.
                # Re-read rather than trusting a saved stop flag after a break.
                record = dict(previous, completedSteps=[])
            else:
                record = self._record("park", retainedConnection=state.get("currentVehicle"),
                    simulationWasRunning=(state.get("source") or {}).get("state") in ("RUNNING", "STARTING"))
                if previous.get("action") == "park":
                    record.update(retainedConnection=previous.get("retainedConnection"),
                                  simulationWasRunning=previous.get("simulationWasRunning", False))
            return self._steps(record, [
                ("stop-simulation", lambda: self.app.source_service.simulation("stop", target="test")),
                ("stop-test", lambda: self._vm("stop")),
                ("stop-backends", self.backends.stop_stack)], "PARKED")

    def resume(self):
        with self.environment._writer():
            state = self._state()
            previous = state.get("demoLifecycle") or {}
            if previous.get("action") == "resume" and previous.get("state") == "COMPLETED":
                return self._resumed_observation(self._result(previous, noOp=True))
            if previous.get("action") == "resume" and previous.get("state") in ("PARTIAL", "COMPLETED"):
                record = dict(previous, completedSteps=[])
            elif previous.get("action") == "park" and previous.get("state") == "COMPLETED":
                record = self._record("resume", retainedConnection=previous.get("retainedConnection"),
                    simulationWasRunning=previous.get("simulationWasRunning", False))
            else:
                raise EnvironmentError("DEMO_CONFIRMED_PARK_REQUIRED")
            steps = [("start-test", lambda: self._vm("start")), ("start-backends", self.backends.start_stack)]
            if record["simulationWasRunning"]:
                steps.append(("start-simulation", lambda: self.app.source_service.simulation("start", target="test")))
            if record["retainedConnection"] == "test":
                steps.append(("restore-test-connection", lambda: self.app.execute(
                    OperationRequest("vehicle", "initialize", VehicleTarget.TEST))))
            result = self._steps(record, steps, "RESUMED")
            return self._resumed_observation(result) if result.state == OperationState.COMPLETED else result

    def _resumed_observation(self, result):
        state = self._state()
        if not state["vehicles"]["test"].get("unitId"):
            return result
        cloud = self.app.unit_service.observe("cloud-status", "test")
        # Missing optional layers/subjects are not a failed Resume or evidence
        # of Offline. Preserve their envelopes without blocking local startup.
        current = cloud.get("unit", {}).get("state") == "CURRENT"
        return OperationResult(result.operation, result.state if current else OperationState.PARTIAL,
            "Same Test resumed; one Cloud observation, no provisioning. Unknown Cloud state can be reread without replaying startup.",
            target="test", data=dict(result.data, cloud=cloud))

    def _backend_cleanup(self, state):
        from .backend_retirement import BackendRetirement
        retirement = BackendRetirement(self.backends)
        if state["vehicles"]["test"].get("systemUid"):
            return retirement.confirm_test_cleanup(state)
        return retirement.confirm_unprovisioned_cleanup(state)

    def retire(self):
        with self.environment._writer():
            if not self.path.exists():
                return self._result(dict(action="retire", state="COMPLETED", phase="NO_CURRENT_TEST"), noOp=True)
            state = read_json(self.path)
            if "test" not in state.get("vehicles", {}):
                data = self.environment.retire_test(cloud_check=self.app.unit_service.confirm_test_retired)
                return self._result(dict(action="retire", state="COMPLETED", phase="NO_CURRENT_TEST"), **data)
            state = self._state()
            previous = state.get("demoLifecycle") or {}
            if previous.get("action") == "retire":
                record = previous
            else:
                # Do not turn shutdown into an implicit Safe Stop/update action.
                self._park_guard(state)
                if state.get("serviceOperations") or state.get("demoSubject"):
                    raise EnvironmentError("DEMO_SUBJECT_RETIREMENT_INTEGRATION_REQUIRED")
                record = self._record("retire")
            def context():
                from .backend_context import sync_context
                current = self._state()
                if current["vehicles"]["test"].get("systemUid"):
                    sync_context(self.environment, current)
                return dict(state="COMPLETED")
            def cloud_action(action):
                current = self._state()["vehicles"]["test"]
                if not any(current.get(key) for key in ("unitId", "systemUid", "nodeId")):
                    return completed_no_cloud()
                return self.app.execute(OperationRequest("unit", action, VehicleTarget.TEST))
            prepared = self._steps(record, [
                ("stop-simulation", lambda: self.app.source_service.simulation("stop", target="test")),
                ("start-cleanup-backends", self.backends.start_stack),
                ("bind-cleanup-context", context),
                ("deprovision-test", lambda: cloud_action("deprovision")),
                ("delete-test", lambda: cloud_action("delete")),
                ("stop-test", lambda: self._vm("stop"))], "READY_FOR_LOCAL_RETIREMENT")
            if prepared.state != OperationState.COMPLETED:
                return prepared
            record.update(state="IN_PROGRESS", phase="retire-test-data-and-overlay")
            self._save(record)
            try:
                data = self.environment.retire_test(cloud_check=self.app.unit_service.confirm_test_retired,
                    backend_check=self._backend_cleanup)
            except EnvironmentError as error:
                record.update(state="PARTIAL", reason=str(error))
                self._save(record)
                return self._result(record)
            record.update(state="COMPLETED", phase="RETIRED")
            # Full single-Test retirement deliberately removes the journal;
            # dual-role retirement retains Production, not an old Test dossier.
            if self.path.exists():
                current = read_json(self.path)
                current.pop("demoLifecycle", None)
                atomic_json(self.path, current)
            return self._result(record, cleanup=data)


def completed_no_cloud():
    return OperationResult("unit.retire", OperationState.COMPLETED, "Never provisioned; no Cloud mutation required")
