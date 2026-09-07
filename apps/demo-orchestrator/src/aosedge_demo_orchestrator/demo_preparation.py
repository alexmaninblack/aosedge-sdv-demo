# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""The operator's one-action Test-first preparation, shared by CLI and UI."""

from .components import ComponentService, VERSION
from .component_build import version_number
from .environment import EnvironmentError, JOURNAL, atomic_json
from .models import OperationRequest, OperationResult, OperationState, VehicleTarget
from .status import read_json, now
from .vm import access_path


class DemoPreparation:
    def __init__(self, application, components=None):
        self.app = application
        self.environment = application.environment_service
        self.components = components or ComponentService(self.environment)
        self.progress = application.vm_service.progress

    def plan(self, image):
        candidate = self.environment.catalog.resolve(image)
        if candidate.problems:
            raise EnvironmentError("DEMO_FACTORY_IMAGE_UNAVAILABLE")
        path = self.environment.root / JOURNAL
        state = read_json(path) if path.exists() else None
        if state and (set(state["vehicles"]) != {"test", "production"} or not state.get("factory")
                or state["factory"]["sha256"] != candidate.sha256):
            raise EnvironmentError("DEMO_EXISTING_ENVIRONMENT_IMAGE_OR_ROLES_CONFLICT")
        record = (state or {}).get("demoPreparation")
        if record:
            if record["image"] != image:
                raise EnvironmentError("DEMO_PREPARATION_IMAGE_CHANGED")
            return dict(record, existingEnvironment=True)
        cloud = self.components._worker("release-catalog")
        local = [item["version"] for item in self.components.list()["components"] if VERSION.fullmatch(item["version"])]
        versions = local + cloud["versions"] + ["3.0.0"]
        # Reuse only this owned run's partially/completely published v1 candidate.
        reusable = []
        for version in (state or {}).get("componentOperations", {}):
            prepared = self.components._directory(version) / "prepared.json"
            if prepared.is_file():
                metadata = read_json(prepared)
                if metadata.get("contentProfile") == "v1" and version_number(version) >= version_number(cloud["latest"]):
                    reusable.append(version)
        version = max(reusable, key=version_number) if reusable else str(max(map(version_number, versions))[0] + 1) + ".0.0"
        if state and any(item.get("unitId") or item.get("systemUid") for item in state["vehicles"].values()):
            raise EnvironmentError("DEMO_INITIALIZATION_REQUIRES_UNPROVISIONED_RUN")
        return dict(image=image, version=version, contentProfile="v1", phase="PLANNED", completedSteps=[],
                    existingEnvironment=bool(state), originalImagePreserved=True)

    def prepare(self, image):
        # Do not publish/provision half a scenario while its startup mode is unavailable.
        if not callable(getattr(self.app.source_service, "initialize_test", None)):
            raise EnvironmentError("DEMO_INITIAL_MANUAL_CHANGE_PENDING_AUTHORIZATION")
        with self.environment._writer():
            record = self.plan(image)
            version = record["version"]
            self.progress("Preparing Test demo with VDP v1 / Cloud release " + version)
            if record.get("phase") == "READY_TO_DRIVE":
                return OperationResult("demo.prepare", OperationState.COMPLETED,
                    "This run is already prepared; no restart, reset or repeat publication.", data=dict(record, noOp=True))
            if any(not (access_path(self.environment.root, role) / "known_hosts").exists() for role in ("test", "production")):
                provider = self.app.vm_service.password_provider
                if provider is None or not provider("test"):
                    raise EnvironmentError("DEMO_VM_ACCESS_REQUIRED")
            if not record["existingEnvironment"]:
                result = self.app.execute(OperationRequest("environment", "create", VehicleTarget.ALL, image=image))
                if result.state != OperationState.COMPLETED:
                    return OperationResult("demo.prepare", result.state, result.message, data=dict(phase="create"))
            def save():
                state = read_json(self.environment.root / JOURNAL)
                state["demoPreparation"] = record
                atomic_json(self.environment.root / JOURNAL, state)
            save()
            steps = [
                ("prepare-v1", OperationRequest("component", "prepare", component_version=version, content_profile="v1")),
                ("sign-v1", OperationRequest("component", "sign", component_version=version)),
                ("upload-v1", OperationRequest("component", "upload", component_version=version)),
                ("approve-v1", OperationRequest("component", "approve", component_version=version)),
                ("start-vms", OperationRequest("vm", "start", VehicleTarget.ALL, timeout=90)),
                ("provision", OperationRequest("unit", "provision", VehicleTarget.ALL)),
                ("simulation", OperationRequest("simulation", "start")),
                ("connect-test-manual", OperationRequest("vehicle", "initialize", VehicleTarget.TEST)),
                ("observe-baseline", OperationRequest("component", "status", VehicleTarget.TEST)),
            ]
            for phase, request in steps:
                if phase in record["completedSteps"]:
                    continue
                record.update(phase=phase, updatedAt=now())
                save()
                self.progress(phase + (" · " + version if request.domain == "component" else ""))
                if phase == "prepare-v1" and (self.components._directory(version) / "prepared.json").is_file():
                    metadata = read_json(self.components._directory(version) / "prepared.json")
                    if metadata.get("version") != version or metadata.get("contentProfile") != "v1":
                        raise EnvironmentError("DEMO_REUSED_COMPONENT_PROFILE_CONFLICT")
                    result = self.app.execute(OperationRequest("component", "inspect", component_version=version))
                else:
                    result = self.app.execute(request)
                if result.state not in (OperationState.COMPLETED, OperationState.OBSERVED):
                    record["reason"] = result.message
                    save()
                    return OperationResult("demo.prepare", result.state, result.message, data=record)
                if phase == "observe-baseline" and (result.data or {}).get("activeVersion") not in (None, "0.0.0"):
                    raise EnvironmentError("DEMO_VDP_ACTIVATED_BEFORE_OPERATOR_SAFE_STOP")
                record["completedSteps"].append(phase)
                record.pop("reason", None)
                save()
            record.update(phase="READY_TO_DRIVE", updatedAt=now(), currentVehicle="test")
            save()
            return OperationResult("demo.prepare", OperationState.COMPLETED,
                "Ready. Start Autopilot, then press Safe Stop to activate VDP v1. Installation is observed separately.", data=record)
