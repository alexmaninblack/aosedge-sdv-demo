# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""The operator's one-action Test-first preparation, shared by CLI and UI."""

from .components import ComponentService, VERSION
from .component_build import version_number
from .environment import EnvironmentError, JOURNAL, atomic_json
from .models import OperationRequest, OperationResult, OperationState, VehicleTarget
from .status import read_json, now
from .vm import access_path
from .releases import ReleaseContinuity
from .backends import BackendService, TEAMS


class DemoPreparation:
    def __init__(self, application, components=None, backends=None):
        self.app = application
        self.environment = application.environment_service
        self.components = components or ComponentService(self.environment)
        self.progress = application.vm_service.progress
        self.backends = backends or BackendService(self.environment, self.progress)

    def plan(self, image, target=VehicleTarget.TEST):
        if target not in (VehicleTarget.TEST, VehicleTarget.ALL):
            raise EnvironmentError("DEMO_TARGET_MUST_INCLUDE_TEST")
        roles = {"test"} if target == VehicleTarget.TEST else {"test", "production"}
        candidate = self.environment.catalog.resolve(image)
        if candidate.problems:
            raise EnvironmentError("DEMO_FACTORY_IMAGE_UNAVAILABLE")
        path = self.environment.root / JOURNAL
        state = read_json(path) if path.exists() else None
        add_test = bool(state and target == VehicleTarget.TEST and set(state["vehicles"]) == {"production"}
                        and state.get("testRetirement") == {"state": "COMPLETED"})
        from .environment import factory_for
        if state and not add_test and ((not roles.issubset(state["vehicles"])) or not state.get("factory")
                or any(factory_for(state, role)["sha256"] != candidate.sha256 for role in roles)):
            raise EnvironmentError("DEMO_EXISTING_ENVIRONMENT_IMAGE_OR_ROLES_CONFLICT")
        record = (state or {}).get("demoPreparation") if not add_test else None
        if record:
            if record["image"] != image or record.get("target", "all") != target.value:
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
        version = max(reusable, key=version_number) if reusable else ReleaseContinuity(self.environment).next("vdp", versions)
        if state and any(item.get("unitId") or item.get("systemUid") for role, item in state["vehicles"].items() if role in roles):
            raise EnvironmentError("DEMO_INITIALIZATION_REQUIRES_UNPROVISIONED_RUN")
        return dict(image=image, target=target.value, version=version, contentProfile="v1", phase="PLANNED", completedSteps=[],
                    existingEnvironment=bool(state and not add_test), originalImagePreserved=True)

    def prepare(self, image, target=VehicleTarget.TEST):
        # Do not publish/provision half a scenario while its startup mode is unavailable.
        if not callable(getattr(self.app.source_service, "initialize_test", None)):
            raise EnvironmentError("DEMO_INITIAL_MANUAL_CHANGE_PENDING_AUTHORIZATION")
        with self.environment._writer():
            record = self.plan(image, target)
            version = record["version"]
            self.progress("Preparing Test demo with VDP v1 / Cloud release " + version)
            if record.get("phase") == "READY_TO_DRIVE":
                from .demo_lifecycle import DemoLifecycle
                readiness = DemoLifecycle(self.app, self.backends).readiness(source=True, cloud=True)
                return OperationResult("demo.prepare", OperationState.OBSERVED if readiness["state"] == "CURRENT" else OperationState.PARTIAL,
                    "Previous preparation retained; one current infrastructure/Cloud observation. No restart, reset or repeat publication; product readiness is separate.",
                    data=dict(record, noOp=True, readiness=readiness))
            for team in TEAMS:
                self.backends._image(self.backends._candidate(team)["imageId"])
            roles = ("test",) if target == VehicleTarget.TEST else ("test", "production")
            if any(not (access_path(self.environment.root, role) / "known_hosts").exists() for role in roles):
                provider = self.app.vm_service.password_provider
                if provider is None or not provider("test"):
                    raise EnvironmentError("DEMO_VM_ACCESS_REQUIRED")
            if not record["existingEnvironment"]:
                result = self.app.execute(OperationRequest("environment", "create", target, image=image))
                if result.state != OperationState.COMPLETED:
                    return OperationResult("demo.prepare", result.state, result.message, data=dict(phase="create"))
            def save():
                state = read_json(self.environment.root / JOURNAL)
                state["demoPreparation"] = record
                atomic_json(self.environment.root / JOURNAL, state)
            ReleaseContinuity(self.environment).remember("vdp", version)
            save()
            steps = [
                ("start-vms", OperationRequest("vm", "start", target, timeout=90)),
                ("start-backends", None),
                ("simulation", OperationRequest("simulation", "start")),
                ("connect-test-manual", OperationRequest("vehicle", "initialize", VehicleTarget.TEST)),
                ("prepare-v1", OperationRequest("component", "prepare", component_version=version, content_profile="v1")),
                ("sign-v1", OperationRequest("component", "sign", component_version=version)),
                ("upload-v1", OperationRequest("component", "upload", component_version=version)),
                ("publication", OperationRequest("component", "cloud-status", component_version=version)),
                ("provision", OperationRequest("unit", "provision", target)),
                ("observe-baseline", OperationRequest("component", "status", VehicleTarget.TEST)),
            ]
            for phase, request in steps:
                if phase in record["completedSteps"]:
                    continue
                record.update(phase=phase, updatedAt=now())
                save()
                self.progress(phase + (" · " + version if request and request.domain == "component" else ""))
                if phase == "start-backends":
                    backend_result = self.backends.start_stack()
                    result = OperationResult("backend.start-stack", OperationState.COMPLETED
                        if backend_result["state"] == "RUNNING" else OperationState.PARTIAL,
                        backend_result.get("reason", "Backend process startup observed"), data=backend_result)
                elif phase == "simulation":
                    simulation = self.app.source_service.simulation("start", target="test" if target == VehicleTarget.TEST else None)
                    result = OperationResult("simulation.start", OperationState.COMPLETED
                        if simulation["state"] == "RUNNING" else OperationState.PARTIAL, "Simulation startup observed", data=simulation)
                elif phase == "prepare-v1" and (self.components._directory(version) / "prepared.json").is_file():
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
                if phase == "publication":
                    if (result.data or {}).get("publication", {}).get("stage") != "READY":
                        record["reason"] = "COMPONENT_PUBLICATION_NOT_READY"
                        save()
                        return OperationResult("demo.prepare", OperationState.PARTIAL,
                            "Cloud processing is not yet confirmed Ready; repeat to observe, without uploading again.", data=record)
                if phase == "observe-baseline" and (result.data or {}).get("activeVersion") not in (None, "0.0.0"):
                    raise EnvironmentError("DEMO_VDP_ACTIVATED_BEFORE_OPERATOR_SAFE_STOP")
                record["completedSteps"].append(phase)
                record.pop("reason", None)
                save()
            record.update(phase="READY_TO_DRIVE", updatedAt=now(), currentVehicle="test")
            save()
            return OperationResult("demo.prepare", OperationState.COMPLETED,
                "Ready. Start Autopilot, then press Safe Stop to activate VDP v1. Installation is observed separately.", data=record)
