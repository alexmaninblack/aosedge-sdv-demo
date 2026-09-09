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
    metadata_only: bool = False

    def selection_error(self) -> Optional[str]:
        """Validate agreed selectors before any lifecycle adapter is called."""
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
