# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Transport-neutral request and result models."""

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Dict, Optional


class VehicleTarget(str, Enum):
    """Audience-facing selectors accepted by both CLI and API adapters."""

    TEST = "test"
    PRODUCTION = "production"
    ALL = "all"

    @property
    def technical_role(self) -> Optional[str]:
        return {
            VehicleTarget.TEST: "VALIDATION",
            VehicleTarget.PRODUCTION: "PRODUCTION",
            VehicleTarget.ALL: None,
        }[self]


class OperationState(str, Enum):
    READY = "READY"
    OBSERVED = "OBSERVED"
    PARTIAL = "PARTIAL"
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"
    COMPLETED = "COMPLETED"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class OperationRequest:
    domain: str
    action: str
    target: Optional[VehicleTarget] = None
    guest: bool = False
    cloud: bool = False
    timeout: float = 8.0
    profile: Optional[str] = None
    image: Optional[str] = None
    image_path: Optional[str] = None
    current: Optional[str] = None
    component_version: Optional[str] = None
    content_profile: Optional[str] = None
    team: Optional[str] = None
    service_id: Optional[str] = None
    service_version_id: Optional[str] = None
    service_release: Optional[str] = None
    metadata_only: bool = False
    restart_project: Optional[str] = None
    without_permissions: bool = False
    demo_no_telemetry: bool = False
    demo_mocked_data: bool = False
    restart_sm: bool = False
    kac_only: bool = False
    kac_time_read_proof: bool = False
    kac_data_proof: bool = False
    kac_recovery: bool = False
    kac_recovery_remove: bool = False
    iam_response_capacity: bool = False
    restart_cm: bool = False
    startup_reconcile: bool = False
    restart_guest_resolver: bool = False
    confirm_bind_not_submitted_at: Optional[str] = None
    certificate: Optional[str] = None
    expected_domain: Optional[str] = None
    window_id: Optional[str] = None

    def selection_error(self) -> Optional[str]:
        """Validate agreed selectors before any lifecycle adapter is called."""
        if self.window_id is not None and ((self.domain, self.action, self.team) != ("backend", "window-detail", "brake")):
            return "WINDOW_DETAIL_USES_BRAKE_BACKEND_ONLY"
        if type(self.startup_reconcile) is not bool or (self.startup_reconcile and
                (self.domain != "component" or self.action not in ("cm-test", "cm-build", "cm-apply")
                 or self.target != VehicleTarget.TEST)):
            return "CM_STARTUP_RECONCILIATION_TEST_ONLY"
        if type(self.restart_guest_resolver) is not bool or (self.restart_guest_resolver and
                ((self.domain, self.action) != ("vm", "refresh-dns") or self.target != VehicleTarget.TEST)):
            return "DNS_RECOVERY_TEST_ONLY"
        if type(self.iam_response_capacity) is not bool or (self.iam_response_capacity and
                (self.domain != "component" or self.action not in ("core-permissions-build", "core-permissions-apply"))):
            return "IAM_RESPONSE_CAPACITY_OPERATION_REQUIRED"
        if type(self.kac_recovery_remove) is not bool or (self.kac_recovery_remove and
                (not self.kac_only or self.kac_recovery or self.kac_data_proof or self.kac_time_read_proof)):
            return "KAC_RECOVERY_REMOVE_REQUIRES_EXCLUSIVE_KAC_ONLY"
        if type(self.kac_recovery) is not bool or (self.kac_recovery and
                (not self.kac_only or self.kac_data_proof or self.kac_time_read_proof)):
            return "KAC_RECOVERY_REQUIRES_EXCLUSIVE_KAC_ONLY"
        if type(self.kac_time_read_proof) is not bool or (self.kac_time_read_proof and not self.kac_only):
            return "KAC_TIME_READ_PROOF_REQUIRES_KAC_ONLY"
        if type(self.kac_data_proof) is not bool or (self.kac_data_proof and (not self.kac_only or self.kac_time_read_proof)):
            return "KAC_DATA_PROOF_REQUIRES_EXCLUSIVE_KAC_ONLY"
        if type(self.kac_only) is not bool or (self.kac_only and
                ((self.domain, self.action) != ("service", "runtime-activate")
                 or self.target != VehicleTarget.TEST or self.restart_sm)):
            return "KAC_ONLY_USES_TEST_RUNTIME_ACTIVATE_WITHOUT_SM_RESTART"
        if (self.certificate is not None or self.expected_domain is not None) and self.domain != "cloud":
            return "CERTIFICATE_SELECTION_USES_CLOUD_ONLY"
        if self.confirm_bind_not_submitted_at is not None and (
                not isinstance(self.confirm_bind_not_submitted_at, str)
                or (self.domain, self.action) != ("service", "assign")
                or self.target != VehicleTarget.TEST):
            return "BIND_NON_SUBMISSION_CONFIRMATION_USES_TEST_ASSIGN_ONLY"
        if type(self.restart_cm) is not bool or (self.restart_cm and
                ((self.domain, self.action) != ("component", "cm-apply") or self.target != VehicleTarget.TEST)):
            return "RESTART_CM_USES_TEST_CM_APPLY_ONLY"
        if type(self.demo_mocked_data) is not bool or (self.demo_mocked_data and
                ((self.domain, self.action) != ("service", "prepare") or not self.without_permissions or self.demo_no_telemetry)):
            return "DEMO_MOCK_REQUIRES_EXCLUSIVE_PERMISSION_FREE_SERVICE_PREPARE"
        if type(self.restart_sm) is not bool or (self.restart_sm and
                ((self.domain, self.action) != ("service", "runtime-activate") or self.target != VehicleTarget.TEST)):
            return "RESTART_SM_USES_TEST_RUNTIME_ACTIVATE_ONLY"
        if type(self.demo_no_telemetry) is not bool or (self.demo_no_telemetry and
                ((self.domain, self.action) != ("service", "prepare") or not self.without_permissions)):
            return "DEMO_NO_TELEMETRY_REQUIRES_PERMISSION_FREE_SERVICE_PREPARE"
        if type(self.without_permissions) is not bool or (self.without_permissions and
                (self.domain, self.action) != ("service", "prepare")):
            return "WITHOUT_PERMISSIONS_USES_SERVICE_PREPARE_ONLY"
        if self.service_release is not None and (self.domain != "service" or self.action not in ("sign", "upload", "cloud-status")):
            return "SERVICE_RELEASE_SELECTOR_INVALID"
        if self.service_version_id is not None and (self.domain, self.action) != ("service", "inspect"):
            return "SERVICE_VERSION_SELECTOR_USES_INSPECT_ONLY"
        if self.domain == "environment" and self.action == "prepare":
            if not isinstance(self.target, VehicleTarget):
                return "PREPARE_TARGET_REQUIRED"
            if self.current is None:
                return "CURRENT_VEHICLE_REQUIRED"
            if self.current not in ("test", "production"):
                return "CURRENT_VEHICLE_MUST_BE_SINGLE_ROLE"
            if self.target != VehicleTarget.ALL and self.current != self.target.value:
                return "CURRENT_VEHICLE_NOT_IN_TARGET"
        if self.domain == "vehicle" and self.action == "select":
            if not isinstance(self.target, VehicleTarget) or self.target not in (VehicleTarget.TEST, VehicleTarget.PRODUCTION):
                return "CURRENT_VEHICLE_MUST_BE_SINGLE_ROLE"
            if self.current is not None:
                return "VEHICLE_SELECT_USES_TARGET_ONLY"
        return None


@dataclass(frozen=True)
class OperationResult:
    operation: str
    state: OperationState
    message: str
    target: Optional[str] = None
    technical_role: Optional[str] = None
    status: Optional[Dict[str, Any]] = None
    data: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        document = asdict(self)
        document["state"] = self.state.value
        return {key: value for key, value in document.items() if value is not None}
