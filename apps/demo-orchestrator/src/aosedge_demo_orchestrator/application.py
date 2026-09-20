# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Application boundary used by every external adapter."""

from subprocess import SubprocessError

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
        if request.domain == "cloud" and request.action in ("check", "prepare"):
            if any((request.target, request.certificate, request.image, request.profile, request.expected_domain)):
                return OperationResult(operation, OperationState.BLOCKED, "CLOUD_SETUP_USES_CONFIGURED_TEST_CONTEXT")
            from .cloud_setup import CloudSetup
            try:
                setup = CloudSetup(self.unit_service)
                data = setup.prepare() if request.action == "prepare" else setup.check()
                result_state = (OperationState.OBSERVED if request.action == "check" else
                    OperationState.COMPLETED if data["stage"] == "READY" else OperationState.BLOCKED)
                return OperationResult(operation, result_state,
                    "Test Cloud prerequisites; no provisioning, publication, Subject assignment or Production change.", data=data)
            except EnvironmentError as error:
                return OperationResult(operation, OperationState.BLOCKED, str(error))
            except (OSError, ValueError, TypeError, KeyError):
                return OperationResult(operation, OperationState.BLOCKED, "CLOUD_SETUP_UNAVAILABLE")
        if request.domain == "cloud" and request.action in ("inspect", "select"):
            from .cloud_connection import CloudConnection
            try:
                connection = CloudConnection(self.environment_service)
                data = (connection.select(request.certificate, request.expected_domain) if request.action == "select"
                        else connection.inspect(request.certificate))
                return OperationResult(operation, OperationState.COMPLETED if request.action == "select" else OperationState.OBSERVED,
                    "Certificate-derived Test Cloud selection; no Cloud mutation, VM restart or provisioning.", data=data)
            except EnvironmentError as error:
                return OperationResult(operation, OperationState.BLOCKED, str(error))
            except (OSError, ValueError, TypeError, KeyError):
                return OperationResult(operation, OperationState.BLOCKED, "CLOUD_CONNECTION_UNAVAILABLE")
        if operation in ("service.runtime-prepare", "service.runtime-activate"):
            if (request.target != VehicleTarget.TEST or request.current or request.image or request.image_path
                    or request.profile or request.team or request.service_id or request.content_profile or request.component_version):
                return OperationResult(operation, OperationState.BLOCKED, "SERVICE_INPUTS_TEST_ONLY")
            try:
                from .service_inputs import ServiceInputs
                activating = request.action == "runtime-activate"
                if request.kac_only:
                    if request.kac_recovery_remove:
                        data = ServiceInputs(self.environment_service).activate_kac("test", recovery_remove=True)
                        return OperationResult(operation, OperationState.COMPLETED if data.get("originalPolicyRestored") else OperationState.PARTIAL,
                            "Exact stock policy restored; owned transient KAC recovery removed. No VM, manager or container restart.", data=data)
                    if request.kac_recovery:
                        self.vm_service.progress("Test: proven KAC recovery for bounded qualification; no manager or container restart")
                        data = ServiceInputs(self.environment_service).activate_kac("test", recovery=True)
                        return OperationResult(operation, OperationState.COMPLETED if data.get("state") == "ACTIVE" else OperationState.PARTIAL,
                            "Transient six-hour KAC recovery with automatic stock-policy rollback; not Factory/reboot qualification.", data=data)
                    policy_proof = request.kac_time_read_proof or request.kac_data_proof
                    self.vm_service.progress("Test: bounded KAC permission/data proof, with stock-policy rollback" if policy_proof
                        else "Test: start existing KAC only; no VM, manager or container restart")
                    data = ServiceInputs(self.environment_service).activate_kac("test", time_read_proof=request.kac_time_read_proof, data_proof=request.kac_data_proof)
                    return OperationResult(operation, OperationState.COMPLETED if data.get("state") in ("ACTIVE", "PROVED") else OperationState.PARTIAL,
                        "Temporary KAC permission proof; inspect originalPolicyRestored. Not persistent telemetry readiness." if policy_proof
                        else "KAC-only activation; real token issuance and telemetry require independent observation.", data=data)
                if activating:
                    self.vm_service.progress("Test: native resource/startup activation; one SM restart, unchanged executable")
                data = ServiceInputs(self.environment_service).prepare("test", activate=activating, restart_sm=request.restart_sm)
                if activating:
                    complete = data.get("state") == "ACTIVE" and data.get("verification", {}).get("stage") == "VERIFIED"
                    configuration = "Packaged factory configuration reused" if data.get("factoryConfiguration") else "Transient native configuration"
                    return OperationResult(operation, OperationState.COMPLETED if complete else OperationState.PARTIAL,
                        configuration + "; no SM code change, service assignment or VM reboot qualification.", data=data)
                return OperationResult(operation, OperationState.COMPLETED,
                    "Public inputs prepared; no SM activation, container launch, assignment or cold-start qualification.", data=data)
            except EnvironmentError as error:
                return OperationResult(operation, OperationState.BLOCKED, str(error))
            except (OSError, ValueError, KeyError, TypeError, SubprocessError):
                return OperationResult(operation, OperationState.BLOCKED, "SERVICE_INPUT_PREPARATION_UNAVAILABLE")
        if operation == "service.runtime-inspect":
            if request.target != VehicleTarget.TEST or request.current or request.image or request.profile or request.team or request.service_id:
                return OperationResult(operation, OperationState.BLOCKED, "SERVICE_RUNTIME_INSPECTION_USES_TEST_ONLY")
            try:
                from .components import ComponentService
                data = ComponentService(self.environment_service).status("test", action="service-runtime-inspect")
                return OperationResult(operation, OperationState.OBSERVED,
                    "Engineering guest observation only; no restart, provisioning, assignment or credential content.", data=data)
            except EnvironmentError as error:
                return OperationResult(operation, OperationState.BLOCKED, str(error))
            except (OSError, ValueError, KeyError, TypeError):
                return OperationResult(operation, OperationState.BLOCKED, "SERVICE_RUNTIME_INSPECTION_UNAVAILABLE")
        if operation in ("service.build", "service.build-status"):
            from .service_build import ServiceBuilder
            if request.target or request.current or request.image or request.image_path or request.profile or request.service_id or request.component_version:
                return OperationResult(operation, OperationState.BLOCKED, "SERVICE_BUILD_USES_FIXED_TEAM_ONLY")
            try:
                builder = ServiceBuilder(self.environment_service, self.vm_service.progress)
                if request.action == "build-status":
                    data = builder.status(request.team)
                    return OperationResult(operation, OperationState.OBSERVED,
                        "Read-only repository build history; no retry or runtime action.", data=data)
                data = builder.execute(request.team, request.content_profile or "v1")
                return OperationResult(operation, OperationState.COMPLETED,
                    "Real ARM64 development build; no Cloud publication, guest installation or runtime qualification.", data=data)
            except EnvironmentError as error:
                return OperationResult(operation, OperationState.BLOCKED, str(error))
            except (OSError, ValueError, KeyError, TypeError, SubprocessError):
                return OperationResult(operation, OperationState.BLOCKED, "SERVICE_BUILD_UNAVAILABLE")
        if request.domain == "service" and request.action in ("sign", "upload", "cloud-status"):
            from .service_packages import ServicePackages
            if (request.target or request.current or request.image or request.image_path or request.service_id
                    or request.component_version or request.content_profile or request.team or request.profile):
                return OperationResult(operation, OperationState.BLOCKED, "SERVICE_PUBLICATION_USES_PREPARED_HANDLE_ONLY")
            try:
                packages = ServicePackages(self.environment_service, self.vm_service.progress)
                data = getattr(packages, request.action.replace("-", "_"))(request.service_release)
                state = (OperationState.COMPLETED if request.action == "sign" else OperationState.PARTIAL
                    if data.get("stage") in ("ERROR", "UNCERTAIN", "UNKNOWN", "ATTEMPTING") else OperationState.BLOCKED
                    if data.get("stage") == "BLOCKED" else OperationState.OBSERVED)
                return OperationResult(operation, state,
                    "Service bundle operation only; acceptance/readiness is not assignment, installation or function health.", data=data)
            except EnvironmentError as error:
                return OperationResult(operation, OperationState.BLOCKED, str(error))
            except (OSError, ValueError, KeyError, TypeError):
                return OperationResult(operation, OperationState.BLOCKED, "SERVICE_PUBLICATION_UNAVAILABLE")
        if operation == "service.releases":
            from .service_packages import ServicePackages
            try:
                return OperationResult(operation, OperationState.OBSERVED,
                    "Prepared release receipts; no payload hashing, Cloud read or mutation.",
                    data=ServicePackages(self.environment_service).receipts())
            except (EnvironmentError, OSError, ValueError, KeyError, TypeError):
                return OperationResult(operation, OperationState.BLOCKED, "SERVICE_RECEIPTS_UNAVAILABLE")
        if operation == "service.prepare":
            from .service_packages import ServicePackages
            import subprocess
            if request.target or request.current or request.image or request.image_path or request.service_id or request.component_version:
                return OperationResult(operation, OperationState.BLOCKED, "SERVICE_PREPARE_USES_TEAM_AND_PROFILE_ONLY")
            try:
                data = ServicePackages(self.environment_service, self.vm_service.progress).prepare(
                    request.team, request.content_profile, request.profile or "service-provider",
                    without_permissions=request.without_permissions, demo_no_telemetry=request.demo_no_telemetry,
                    demo_mocked_data=request.demo_mocked_data)
                return OperationResult(operation, OperationState.COMPLETED,
                    "Unsigned service package prepared; no VM action, signing, Cloud mutation or runtime qualification.", data=data)
            except EnvironmentError as error:
                return OperationResult(operation, OperationState.BLOCKED, str(error))
            except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
                return OperationResult(operation, OperationState.BLOCKED, "SERVICE_PACKAGE_PREPARATION_FAILED_VERSION_RETAINED")
        if operation == "service.assign":
            if (request.target != VehicleTarget.TEST or request.current or request.image or request.image_path
                    or request.profile or request.team or request.content_profile or request.component_version
                    or request.service_release or request.service_version_id):
                return OperationResult(operation, OperationState.BLOCKED, "SERVICE_ASSIGNMENT_USES_CATALOG_ID_AND_TEST_ONLY")
            try:
                from .service_assignment import ServiceAssignment
                assign = ServiceAssignment(self.environment_service, self.unit_service).assign
                data = (assign(request.service_id, request.confirm_bind_not_submitted_at)
                    if request.confirm_bind_not_submitted_at is not None else assign(request.service_id))
                return OperationResult(operation, OperationState.COMPLETED if data["state"] == "ASSIGNED" else
                    OperationState.BLOCKED if data["state"] == "BLOCKED" else OperationState.PARTIAL,
                    "OEM desired assignment only; Cloud runtime and product readiness remain separate.", target="test", data=data)
            except EnvironmentError as error:
                return OperationResult(operation, OperationState.BLOCKED, str(error), target="test")
            except (OSError, ValueError, TypeError, KeyError):
                return OperationResult(operation, OperationState.BLOCKED, "SERVICE_ASSIGNMENT_INPUT_OR_STATE_UNAVAILABLE", target="test")
        if request.domain == "service":
            from .services import ServiceCatalog
            if request.target or request.current or request.image or request.image_path or request.team or request.component_version or request.content_profile:
                return OperationResult(operation, OperationState.BLOCKED, "SERVICE_READ_SELECTOR_INVALID")
            try:
                catalog = ServiceCatalog(self.environment_service)
                data = (catalog.execute(request.action, request.service_id, request.profile, request.service_version_id)
                    if request.action == "inspect" else catalog.execute(request.action, request.service_id, request.profile))
                return OperationResult(operation, OperationState.PARTIAL if data["problems"] else OperationState.OBSERVED,
                    "Read-only per-profile Cloud catalog/ownership; not team authority assignment or runtime health.", data=data)
            except EnvironmentError as error:
                return OperationResult(operation, OperationState.BLOCKED, str(error))
            except (OSError, ValueError, KeyError, TypeError):
                return OperationResult(operation, OperationState.BLOCKED, "SERVICE_CLOUD_CONFIGURATION_UNAVAILABLE")
        if request.domain == "backend":
            from .backends import BackendService
            reset_action = request.action in ("reset-scenario", "reset-status")
            if ((request.target != VehicleTarget.TEST if reset_action else bool(request.target))
                    or request.current or request.image or request.image_path or request.profile):
                return OperationResult(operation, OperationState.BLOCKED, "BACKEND_USES_FIXED_TEAM_ONLY")
            try:
                backend = BackendService(self.environment_service, self.vm_service.progress)
                if request.action == "recover-file-sharing":
                    if request.team:
                        raise EnvironmentError("BACKEND_RECOVERY_USES_CURRENT_CLEANUP_ONLY")
                    data = backend.recover_file_sharing(request.restart_project)
                    return OperationResult(operation, OperationState.COMPLETED if data["state"] == "COMPLETED" else OperationState.PARTIAL,
                        "Explicit Docker Desktop recovery; no pruning, Cloud mutation or QEMU VM restart.", data=data)
                data = (backend.execute(request.action, request.team, window_id=request.window_id)
                    if request.action == "window-detail" else backend.execute(request.action, request.team))
                state = (OperationState.PARTIAL if request.action == "inspect" and data.get("state") == "PARTIAL" else OperationState.OBSERVED if request.action in ("status", "inspect", "reset-status", "window-detail") else OperationState.PARTIAL
                    if request.action == "start" and data.get("state") != "RUNNING" else OperationState.COMPLETED)
                message = ("Reset request accepted; only a matching Gateway CLEARED acknowledgement confirms completion."
                    if request.action == "reset-scenario" else "Backend process/storage operation; not Cloud or in-vehicle function readiness.")
                return OperationResult(operation, state, message, data=data)
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
        if operation in ("demo.create", "demo.retire", "environment.park", "environment.resume"):
            from .demo_lifecycle import DemoLifecycle
            if (request.target not in (None, VehicleTarget.TEST) or request.current or request.image_path
                    or request.profile or request.component_version or request.content_profile or request.team
                    or request.service_id or (bool(request.image) != (request.action == "create"))):
                return OperationResult(operation, OperationState.BLOCKED, "DEMO_LIFECYCLE_USES_OWNED_TEST_ONLY")
            try:
                workflow = DemoLifecycle(self)
                return workflow.create(request.image) if request.action == "create" else getattr(workflow, request.action)()
            except (EnvironmentError, ImageError) as error:
                return OperationResult(operation, OperationState.BLOCKED, str(error), target="test")
            except (OSError, ValueError, KeyError, TypeError):
                return OperationResult(operation, OperationState.PARTIAL, "DEMO_LIFECYCLE_UNAVAILABLE_STATE_RETAINED", target="test")
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
        if operation == "vehicle.build-runtime":
            from .source_authentication import build
            if request.target != VehicleTarget.TEST:
                return OperationResult(operation, OperationState.BLOCKED, "SOURCE_TRUST_TEST_ONLY")
            try:
                data = build(self.source_service.driver)
                return OperationResult(operation, OperationState.COMPLETED, "Gateway/client built; running processes unchanged.", data=data)
            except EnvironmentError as error:
                return OperationResult(operation, OperationState.BLOCKED, str(error))
        if operation == "vehicle.authenticate":
            from .source_authentication import authenticate
            import subprocess
            try:
                data = authenticate(self.source_service, request.target.value if request.target else None)
                return OperationResult(operation, OperationState.COMPLETED,
                    "Test Gateway mTLS onboarding; VM/Cloud identity preserved, Production unchanged.", data=data)
            except EnvironmentError as error:
                return OperationResult(operation, OperationState.BLOCKED, str(error))
            except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
                return OperationResult(operation, OperationState.PARTIAL, "SOURCE_TRUST_RECONCILIATION_REQUIRED")
        if operation == "vehicle.initialize":
            import subprocess
            initialize = getattr(self.source_service, "initialize_test", None)
            if request.target != VehicleTarget.TEST or not callable(initialize):
                return OperationResult(operation, OperationState.BLOCKED, "INITIAL_MANUAL_REQUIRES_TEST")
            try:
                data = initialize()
                return OperationResult(operation, OperationState.COMPLETED,
                    "Existing Test connection confirmed; driving mode unchanged." if data.get("noOp")
                    else "Initial Test connection in stationary Manual.", data=data)
            except EnvironmentError as error:
                return OperationResult(operation, OperationState.BLOCKED, str(error))
            except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
                return OperationResult(operation, OperationState.BLOCKED, "SOURCE_STATE_OR_RUNTIME_UNAVAILABLE")
        if request.domain == "component" and request.action.startswith("cm-compare-"):
            from .cm_comparison import compare
            try:
                data = compare(self.environment_service, request.target.value if request.target else None,
                    request.action.removeprefix("cm-compare-"))
                return OperationResult(operation, OperationState.COMPLETED,
                    "Authorized Test CM comparison only; SM, VM, Cloud assignments and Production unchanged.", data=data)
            except EnvironmentError as error:
                return OperationResult(operation, OperationState.BLOCKED, str(error))
        if request.domain == "component" and request.action in ("readiness-build", "readiness-apply"):
            from .component_runtime import build_readiness, apply_readiness
            try:
                target = request.target.value if request.target else None
                data = build_readiness(target) if request.action == "readiness-build" else apply_readiness(self.environment_service, target)
                return OperationResult(operation, OperationState.COMPLETED, "Exact Provider readiness read-scope proof; Factory and Aos managers unchanged.", data=data)
            except EnvironmentError as error:
                return OperationResult(operation, OperationState.BLOCKED, str(error))
        if request.domain == "component" and request.action in ("core-permissions-build", "core-permissions-apply", "core-permissions-status"):
            from .component_runtime import build_permissions, apply_permissions
            try:
                target = request.target.value if request.target else None
                data = (build_permissions(target, iam_response_capacity=request.iam_response_capacity) if request.action == "core-permissions-build" else
                    apply_permissions(self.environment_service, target, observe=request.action == "core-permissions-status",
                        iam_response_capacity=request.iam_response_capacity))
                return OperationResult(operation, OperationState.COMPLETED,
                    "Authorized Test-only permission capacity proof; immutable image and Production unchanged.", data=data)
            except EnvironmentError as error:
                return OperationResult(operation, OperationState.BLOCKED, str(error))
        if request.domain == "component" and request.action in ("sm-builder-start", "sm-builder-stop", "sm-build", "sm-test", "sm-apply", "cm-build", "cm-test", "cm-apply"):
            from .component_runtime import builder, build, apply_test
            try:
                target = request.target.value if request.target else None
                if request.startup_reconcile:
                    from .component_runtime import qualify_cm_startup, apply_cm_startup
                    data = (apply_cm_startup(self.environment_service, target) if request.action == "cm-apply"
                        else qualify_cm_startup(target, compile_binary=request.action == "cm-build"))
                    return OperationResult(operation, OperationState.COMPLETED,
                        "Bounded Test-only CM startup proof; identity, SM, Cloud assignments and image unchanged.", data=data)
                manager = "cm" if request.action.startswith("cm-") else "sm"
                data = (apply_test(self.environment_service, target, manager=manager, restart_cm=request.restart_cm) if request.action.endswith("-apply") else
                        build(target, compile_source=request.action.endswith("-build"), manager=manager) if request.action in ("sm-build", "sm-test", "cm-build", "cm-test") else builder(target, request.action.rsplit("-", 1)[1]))
                return OperationResult(operation, OperationState.COMPLETED,
                    "Test-only AosCore runtime operation; immutable image and Production unchanged; no direct Cloud mutation." if request.action.endswith("-apply") else
                    "Dedicated Builder only; no demo VM or Cloud mutation.", data=data)
            except EnvironmentError as error:
                return OperationResult(operation, OperationState.BLOCKED, str(error))
        if request.domain == "component" and request.action in ("list", "inspect", "unpack", "prepare", "verify", "sign", "cloud-status", "upload", "approve", "unapprove", "send", "status", "logs", "diagnose", "schema-apply", "schema-remove", "sm-status", "cm-status"):
            from .components import ComponentService
            guest_actions = ("status", "logs", "diagnose", "schema-apply", "schema-remove", "sm-status", "cm-status")
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
                "Read-only guest component observation; no restart or update." if request.action in ("status", "logs", "diagnose", "sm-status", "cm-status") else
                "Local component artifact operation; no Cloud or VM mutation.", data=data)
        if operation == "vm.sync-time":
            if request.target != VehicleTarget.TEST:
                return OperationResult(operation, OperationState.BLOCKED, "TIME_RECOVERY_TEST_ONLY")
            try:
                data = self.vm_service.sync_time()
            except EnvironmentError as error:
                return OperationResult(operation, OperationState.BLOCKED, str(error))
            except (OSError, ValueError, KeyError, TypeError):
                return OperationResult(operation, OperationState.PARTIAL, "TIME_RECOVERY_UNCONFIRMED")
            return OperationResult(operation, OperationState.COMPLETED if data["state"] == "READY" else OperationState.PARTIAL,
                "Only Test systemd-timesyncd restarted; no VM, simulator or Aos service restart. Pending updates may proceed if Safe Stop is already active.", data=data)
        if operation == "vm.refresh-dns":
            if request.target != VehicleTarget.TEST:
                return OperationResult(operation, OperationState.BLOCKED, "DNS_RECOVERY_TEST_ONLY")
            try:
                data = self.vm_service.refresh_dns(restart_guest_resolver=request.restart_guest_resolver)
            except EnvironmentError as error:
                return OperationResult(operation, OperationState.BLOCKED, str(error))
            except (OSError, ValueError, KeyError, TypeError):
                return OperationResult(operation, OperationState.PARTIAL, "DNS_RECOVERY_UNCONFIRMED")
            return OperationResult(operation, OperationState.COMPLETED if data["state"] == "READY" else OperationState.PARTIAL,
                "Owned DNS recovery only; VM, CM, SM, VDP, containers and Cloud configuration unchanged.", data=data)
        if operation in ("simulation.exercise", "simulation.return-to-road"):
            recovery=operation=="simulation.return-to-road"
            if request.target != VehicleTarget.TEST or (not recovery and request.team not in ("brake", "tire")):
                return OperationResult(operation, OperationState.BLOCKED, "SIMULATION_EXERCISE_TEST_ONLY")
            try:
                data = self.source_service.exercise("return_to_road" if recovery else request.team)
            except EnvironmentError as error:
                return OperationResult(operation, OperationState.BLOCKED, str(error))
            except (OSError, ValueError, KeyError, TypeError):
                return OperationResult(operation, OperationState.PARTIAL,
                    "SIMULATION_EXERCISE_UNCONFIRMED; control lease expires to Safe Stop; reconcile the same command")
            return OperationResult(operation,
                OperationState.COMPLETED if data["state"] == "COMPLETED" else OperationState.PARTIAL,
                "Real CARLA maneuver only; observe service/backend/advisory results separately. VM and Cloud identities unchanged.", data=data)
        if operation == "simulation.prepare-cache":
            try:
                data = self.source_service.prepare_cache()
            except EnvironmentError as error:
                return OperationResult(operation, OperationState.BLOCKED, str(error))
            except (OSError, ValueError, KeyError, TypeError, SubprocessError):
                return OperationResult(operation, OperationState.PARTIAL, "SIMULATION_CACHE_PREPARATION_UNCONFIRMED")
            return OperationResult(operation, OperationState.COMPLETED,
                "Local Unreal map cache prepared; VM, Cloud and image unchanged. Driving verification is separate.", data=data)
        if operation in ("simulation.start", "simulation.stop"):
            import subprocess
            if request.target not in (None, VehicleTarget.TEST) or request.current or request.image or request.image_path:
                return OperationResult(operation, OperationState.BLOCKED, "SIMULATION_USES_CURRENT_ENVIRONMENT")
            try:
                data = (self.source_service.simulation(request.action, target="test") if request.target
                        else self.source_service.simulation(request.action))
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
                "One VM connected to the local source. The active TLS profile and VDP/KUKSA readiness are reported separately.",
                target=request.target.value, data=data)
        if request.domain == "unit" and request.action in ("cloud-status", "monitoring", "monitoring-history"):
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
                ("Current-run Unit provisioning; attach the protected Gateway after Cloud Online without restarting the simulator. No image rebuild or local disk deletion."
                 if request.action == "provision" else
                 "Current-run Unit operation; no CARLA, image rebuild or local disk deletion."), target=request.target.value, data=data)
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
