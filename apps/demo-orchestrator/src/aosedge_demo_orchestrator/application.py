# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Application boundary used by every external adapter."""

from .models import OperationRequest, OperationResult, OperationState
from .status import StatusService, has_unknown, now
from .images import ImageCatalog, ImageError
from .environment import EnvironmentService, EnvironmentError
from .models import VehicleTarget


class DemoOrchestrator:
    """Dispatch lifecycle operations without binding them to CLI or HTTP."""

    def __init__(self, status_service=None, image_catalog=None, environment_service=None, vm_service=None, unit_service=None, source_service=None):
        self.status_service = status_service or StatusService()
        self.image_catalog = image_catalog or ImageCatalog()
        self.environment_service = environment_service or (vm_service.environment if vm_service else EnvironmentService(catalog=self.image_catalog))
        from .vm import VMService
        self.vm_service = vm_service or VMService(self.environment_service)
        from .units import UnitService
        self.unit_service = unit_service or UnitService(self.vm_service)
        from .source import SourceService
        self.source_service = source_service or SourceService(self.vm_service, self.unit_service)

    def execute(self, request: OperationRequest) -> OperationResult:
        operation = f"{request.domain}.{request.action}"
        selection_error = request.selection_error()
        if selection_error:
            return OperationResult(operation, OperationState.BLOCKED, selection_error)
        if request.domain == "backend":
            from .backends import BackendService
            if request.target or request.current or request.image or request.image_path or request.profile:
                return OperationResult(operation, OperationState.BLOCKED, "BACKEND_USES_FIXED_TEAM_ONLY")
            try:
                data = BackendService(self.environment_service, self.vm_service.progress).execute(request.action, request.team)
                state = (OperationState.OBSERVED if request.action == "status" else OperationState.PARTIAL
                    if request.action == "start" and data.get("state") != "RUNNING" else OperationState.COMPLETED)
                return OperationResult(operation, state, "Backend process/storage operation; not Cloud or in-vehicle function readiness.", data=data)
            except EnvironmentError as error:
                return OperationResult(operation, OperationState.BLOCKED, str(error))
            except (OSError, ValueError, KeyError, TypeError):
                return OperationResult(operation, OperationState.BLOCKED, "BACKEND_STATE_UNAVAILABLE")
        if request.domain == "vehicle" and request.action in ("connectivity-on", "connectivity-off", "connectivity-status"):
            from .connectivity import ConnectivityService
            import subprocess
            try:
                action = request.action.removeprefix("connectivity-")
                data = ConnectivityService(self.source_service).execute(action, request.target.value if request.target else None)
                return OperationResult(operation, OperationState.OBSERVED if action == "status" else OperationState.COMPLETED,
                    "Selected VM packet filter only; driving, VISS, other VM and Presenter Internet unchanged.", target=data["target"], data=data)
            except EnvironmentError as error:
                return OperationResult(operation, OperationState.BLOCKED, str(error))
            except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
                return OperationResult(operation, OperationState.BLOCKED, "EXTERNAL_LINK_UNAVAILABLE")
        if request.domain == "workspace" and request.action in ("status", "restore", "close"):
            if request.target or request.current or request.image or request.image_path or request.profile or request.component_version or request.content_profile:
                return OperationResult(operation, OperationState.BLOCKED, "WORKSPACE_USES_CURRENT_ENVIRONMENT")
            from .workspace import WorkspaceService
            import subprocess
            try:
                data = WorkspaceService(self.environment_service, self.source_service.driver).execute(request.action)
                return OperationResult(operation, OperationState.PARTIAL if data["problems"] else
                    OperationState.OBSERVED if request.action == "status" else OperationState.COMPLETED,
                    "Local windows only; no Cloud, VM, Current Vehicle or release changes.", data=data)
            except EnvironmentError as error:
                return OperationResult(operation, OperationState.BLOCKED, str(error))
            except (OSError, ValueError, KeyError, subprocess.SubprocessError):
                return OperationResult(operation, OperationState.BLOCKED, "WORKSPACE_OBSERVATION_UNAVAILABLE")
        if request.domain == "demo" and request.action in ("plan", "prepare"):
            from .demo_preparation import DemoPreparation
            if not request.image or request.target not in (None, VehicleTarget.TEST, VehicleTarget.ALL) or request.image_path or request.current or request.profile:
                return OperationResult(operation, OperationState.BLOCKED, "DEMO_REQUIRES_CATALOG_IMAGE_ONLY")
            try:
                workflow = DemoPreparation(self)
                if request.action == "prepare":
                    return workflow.prepare(request.image, request.target or VehicleTarget.TEST)
                return OperationResult(operation, OperationState.OBSERVED, "Read-only preparation plan; no image creation or publication.", data=workflow.plan(request.image, request.target or VehicleTarget.TEST))
            except (EnvironmentError, ImageError) as error:
                return OperationResult(operation, OperationState.BLOCKED, str(error))
            except (OSError, ValueError, KeyError, TypeError):
                return OperationResult(operation, OperationState.BLOCKED, "DEMO_PREPARATION_STATE_UNAVAILABLE")
        if operation == "vehicle.initialize":
            import subprocess
            initialize = getattr(self.source_service, "initialize_test", None)
            if request.target != VehicleTarget.TEST or not callable(initialize):
                return OperationResult(operation, OperationState.BLOCKED, "INITIAL_MANUAL_REQUIRES_TEST")
            try:
                return OperationResult(operation, OperationState.COMPLETED, "Initial Test connection in stationary Manual.", data=initialize())
            except EnvironmentError as error:
                return OperationResult(operation, OperationState.BLOCKED, str(error))
            except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
                return OperationResult(operation, OperationState.BLOCKED, "SOURCE_STATE_OR_RUNTIME_UNAVAILABLE")
        if request.domain == "component" and request.action in ("sm-builder-start", "sm-builder-stop", "sm-build", "sm-test", "sm-apply"):
            from .component_runtime import builder, build, apply_test
            try:
                target = request.target.value if request.target else None
                data = (apply_test(self.environment_service, target) if request.action == "sm-apply" else
                        build(target, compile_source=request.action == "sm-build") if request.action in ("sm-build", "sm-test") else builder(target, request.action.rsplit("-", 1)[1]))
                return OperationResult(operation, OperationState.COMPLETED,
                    "Test-only transient SM profile; immutable image, Cloud and Production unchanged." if request.action == "sm-apply" else
                    "Dedicated Builder only; no demo VM or Cloud mutation.", data=data)
            except EnvironmentError as error:
                return OperationResult(operation, OperationState.BLOCKED, str(error))
        if request.domain == "component" and request.action in ("list", "inspect", "unpack", "prepare", "verify", "sign", "cloud-status", "upload", "approve", "unapprove", "send", "status", "logs", "diagnose", "schema-apply", "schema-remove", "sm-status"):
            from .components import ComponentService
            guest_actions = ("status", "logs", "diagnose", "schema-apply", "schema-remove", "sm-status")
            if ((request.target and request.action not in guest_actions) or request.current or request.image
                    or request.image_path or request.profile or (request.content_profile is not None and request.action != "prepare")):
                return OperationResult(operation, OperationState.BLOCKED, "COMPONENT_USES_CATALOG_VERSION_ONLY")
            try:
                service = ComponentService(self.environment_service)
                data = (getattr(service, request.action.replace("-", "_"))(request.target.value) if request.action in guest_actions and request.target else
                    service.list() if request.action == "list" else
                    service.prepare(request.component_version, request.content_profile) if request.action == "prepare" else
                    getattr(service, request.action.replace("-", "_"))(request.component_version))
            except EnvironmentError as error:
                return OperationResult(operation, OperationState.BLOCKED, str(error))
            except (OSError, ValueError, KeyError, TypeError):
                return OperationResult(operation, OperationState.BLOCKED, "COMPONENT_ARTIFACT_UNAVAILABLE")
            return OperationResult(operation,
                OperationState.PARTIAL if data.get("problems") else
                OperationState.COMPLETED if request.action in ("unpack", "prepare", "sign", "upload", "approve", "unapprove", "send", "schema-apply", "schema-remove") else OperationState.OBSERVED,
                "Test component send request accepted; VM installation/startup is observed separately." if request.action == "send" else
                "Deployment-bundle request accepted or reconciled; inspect publication.stage for processing/Ready. No validation approval or Production promotion." if request.action == "upload" else
                "Explicit engineering batch approval; not part of verification-Test delivery." if request.action in ("approve", "unapprove") else
                "Read-only component Cloud observation." if request.action == "cloud-status" else
                "Temporary Test-only KUKSA schema; no Factory image, credential, Cloud or Production mutation." if request.action in ("schema-apply", "schema-remove") else
                "Read-only guest component observation; no restart or update." if request.action in ("status", "logs", "diagnose", "sm-status") else
                "Local component artifact operation; no Cloud or VM mutation.", data=data)
        if operation in ("simulation.start", "simulation.stop"):
            import subprocess
            if request.target or request.current or request.image or request.image_path:
                return OperationResult(operation, OperationState.BLOCKED, "SIMULATION_USES_CURRENT_ENVIRONMENT")
            try:
                data = self.source_service.simulation(request.action)
            except EnvironmentError as error:
                return OperationResult(operation, OperationState.BLOCKED, str(error))
            except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
                return OperationResult(operation, OperationState.BLOCKED, "SIMULATION_STATE_OR_RUNTIME_UNAVAILABLE")
            return OperationResult(operation, OperationState.COMPLETED,
                "Local simulation group; VMs and Cloud identities unchanged.", data=data)
        if operation in ("environment.prepare", "vehicle.select"):
            import subprocess
            try:
                data = (self.source_service.prepare(request.target.value, request.current)
                        if operation == "environment.prepare" else self.source_service.select(request.target.value))
            except EnvironmentError as error:
                return OperationResult(operation, OperationState.BLOCKED, str(error), target=request.target.value)
            except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
                return OperationResult(operation, OperationState.BLOCKED, "SOURCE_STATE_OR_RUNTIME_UNAVAILABLE", target=request.target.value)
            return OperationResult(operation, OperationState.COMPLETED,
                "One VM connected to the local server-TLS source. VDP/KUKSA readiness is reported separately; mTLS deferred.",
                target=request.target.value, data=data)
        if request.domain == "unit" and request.action in ("cloud-status", "monitoring"):
            if (request.target != VehicleTarget.TEST or request.guest or request.cloud or request.current or request.image
                    or request.image_path or request.profile or request.component_version or request.content_profile):
                return OperationResult(operation, OperationState.BLOCKED, "UNIT_OBSERVATION_REQUIRES_TEST")
            try:
                data = self.unit_service.observe(request.action, "test")
            except EnvironmentError as error:
                return OperationResult(operation, OperationState.BLOCKED, str(error), target="test")
            except (OSError, ValueError, KeyError, TypeError):
                return OperationResult(operation, OperationState.BLOCKED, "UNIT_OBSERVATION_BINDING_UNAVAILABLE", target="test")
            return OperationResult(operation, OperationState.PARTIAL if data["problems"] else OperationState.OBSERVED,
                "Read-only Aos Cloud observation; no guest reads, repairs, logs or update actions.", target="test", data=data)
        if request.domain == "unit" and request.action in ("provision", "deprovision", "delete", "unassign"):
            if request.target is None:
                return OperationResult(operation, OperationState.BLOCKED, "UNIT_TARGET_REQUIRED")
            try:
                data = self.unit_service.execute(request.action, request.target.value)
            except EnvironmentError as error:
                return OperationResult(operation, OperationState.BLOCKED, str(error), target=request.target.value)
            except (OSError, ValueError, KeyError, TypeError):
                return OperationResult(operation, OperationState.BLOCKED, "UNIT_STATE_UNAVAILABLE", target=request.target.value)
            complete = all(item["state"] == "COMPLETED" for item in data["vehicles"].values())
            return OperationResult(operation, OperationState.COMPLETED if complete else OperationState.PARTIAL,
                "Current-run Unit operation; no CARLA, image rebuild or local disk deletion.", target=request.target.value, data=data)
        if request.domain == "vm" and request.action in ("start", "stop"):
            if request.target is None:
                return OperationResult(operation, OperationState.BLOCKED, "VM_TARGET_REQUIRED")
            try:
                data = self.vm_service.execute(request.action, request.target.value, request.timeout)
            except EnvironmentError as error:
                return OperationResult(operation, OperationState.BLOCKED, str(error))
            except (OSError, ValueError, KeyError, TypeError):
                return OperationResult(operation, OperationState.BLOCKED, "VM_STATE_OR_RUNTIME_UNAVAILABLE")
            complete = data["infrastructure"]["state"] == "COMPLETED" and all(
                item["state"] == "COMPLETED" for item in data["vehicles"].values())
            return OperationResult(operation, OperationState.COMPLETED if complete else OperationState.PARTIAL,
                "Local VM operation; no provisioning, Cloud API or CARLA action.", target=request.target.value, data=data)
        if operation == "image.list":
            data = self.image_catalog.list()
            return OperationResult(operation, OperationState.PARTIAL if data["issues"] else OperationState.OBSERVED,
                                   "Published image metadata; image contents were not rehashed.", data=data)
        if operation == "image.build":
            from .component_runtime import build_factory
            try:
                if request.metadata_only:
                    with self.environment_service._writer():
                        data = build_factory(request.image, metadata_only=True)
                else:
                    data = build_factory(request.image)
                return OperationResult(operation, OperationState.COMPLETED,
                    ("Factory compatibility metadata registered; image bytes and qualification unchanged."
                     if request.metadata_only else
                     "Immutable Factory image built; live E2E qualification is not yet performed."), data=data)
            except EnvironmentError as error:
                return OperationResult(operation, OperationState.BLOCKED, str(error))
        if operation == "environment.retire":
            if request.target or request.image or request.image_path or request.current:
                raise ValueError("Local retirement uses the exact current environment only")
            try:
                data = self.environment_service.retire(cloud_check=self.unit_service.confirm_retired)
            except EnvironmentError as error:
                return OperationResult(operation, OperationState.BLOCKED, str(error))
            except (OSError, ValueError, KeyError, TypeError):
                return OperationResult(operation, OperationState.BLOCKED, "LOCAL_RETIRE_UNAVAILABLE_STATE_RETAINED")
            return OperationResult(operation, OperationState.COMPLETED,
                "Local overlays, factory copy and journal removed without backup; source artifact preserved. No Cloud mutations."
                if data["removed"] else "No current local environment to remove. No action was performed.", data=data)
        if operation == "environment.create":
            try:
                data = self.environment_service.create(
                    request.target.value if request.target else "all", request.image, request.image_path)
            except (EnvironmentError, ImageError) as error:
                return OperationResult(operation, OperationState.BLOCKED, str(error))
            except (OSError, ValueError):
                return OperationResult(operation, OperationState.BLOCKED, "LOCAL_CREATE_UNAVAILABLE")
            return OperationResult(operation, OperationState.COMPLETED,
                                   "Local copy and fresh overlays created. VMs not started; no Cloud actions.",
                                   target=request.target.value if request.target else "all", data=data)
        if operation == "orchestrator.status":
            target = request.target.value if request.target else "all"
            snapshot = self.status_service.collect(
                target=target, guest=request.guest, cloud=request.cloud,
                timeout=request.timeout, profile=request.profile,
            )
            try:
                snapshot["source"] = self.source_service.observe(guest=request.guest, timeout=request.timeout)
            except FileNotFoundError:
                snapshot["source"] = {"state": "NOT_PREPARED", "currentVehicle": None}
            except (OSError, ValueError, KeyError, TypeError):
                snapshot["source"] = {"state": "UNKNOWN", "reason": "SOURCE_STATE_UNAVAILABLE"}
            snapshot["readCompletedAt"] = now()
            return OperationResult(
                operation=operation,
                state=OperationState.PARTIAL if has_unknown(snapshot) else OperationState.OBSERVED,
                message="Read-only observations; not demo readiness or mutation authorization.",
                target=target,
                status=snapshot,
            )

        target = request.target.value if request.target is not None else None
        role = request.target.technical_role if request.target is not None else None
        return OperationResult(
            operation=operation,
            state=OperationState.NOT_IMPLEMENTED,
            message="No action was performed.",
            target=target,
            technical_role=role,
        )
