# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""One selected-vehicle external-link fault, independent of driving and Cloud APIs."""

from .environment import EnvironmentError, JOURNAL
from .status import read_json, now, object_id
from contextlib import nullcontext


class ConnectivityService:
    def __init__(self, source):
        self.source = source
        self.vm, self.environment, self.driver = source.vm, source.environment, source.driver

    def execute(self, action, target=None):
        if action not in ("on", "off", "status") or target not in (None, "test", "production"):
            raise EnvironmentError("EXTERNAL_LINK_SELECTION_INVALID")
        with (nullcontext() if action == "status" else self.environment._writer()), self.driver.operation(timeout=10):
            state = read_json(self.environment.root / JOURNAL)
            current = state.get("currentVehicle")
            role = target or current
            if role not in ("test", "production") or role not in state.get("vehicles", {}):
                raise EnvironmentError("EXTERNAL_LINK_CURRENT_VEHICLE_REQUIRED")
            source = state.get("source") or {}
            isolated = self.environment.factory31_comparison is True
            if isolated:
                self.vm._validate(state, "start", [role])
                if current is not None or source:
                    raise EnvironmentError("FACTORY31_COMPARISON_SOURCE_MUST_REMAIN_DETACHED")
            if (source.get("operation") or source.get("stopOperation")
                    or (action == "on" and current is not None and role != current)
                    or (action == "off" and not isolated and (role != current or source.get("state") != "RUNNING"))):
                raise EnvironmentError("EXTERNAL_LINK_REQUIRES_CURRENT_VEHICLE")
            item = state["vehicles"][role]
            object_id(item["localVmId"])
            if (item.get("sshPort") != self.environment.ssh_port(role)
                    or item.get("runtime", {}).get("state") != "RUNNING"):
                raise EnvironmentError("EXTERNAL_LINK_RUNNING_VM_REQUIRED")
            observed = self.driver.guest(state, role, "connectivity-status")
            if action == "status":
                return dict(observed, currentVehicle=current, target=role, readCompletedAt=now())
            desired = action.upper()
            record = dict(state="SUBMITTING", desired=desired, previous=observed["state"], observedAt=now())
            item["runtime"]["externalConnectivity"] = record
            self.vm._save(state)
            try:
                result = observed if observed["state"] == desired else self.driver.guest(state, role, "connectivity-" + action)
                record.update(state=result["state"], observedAt=now())
                self.vm._save(state)
                return dict(result, currentVehicle=current, target=role, readCompletedAt=now())
            except Exception:
                record["state"] = "UNCERTAIN"
                self.vm._save(state)
                raise
