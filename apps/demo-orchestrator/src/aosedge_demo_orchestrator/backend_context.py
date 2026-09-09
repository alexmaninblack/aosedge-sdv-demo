# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Closed backend input projection; never a Cloud or product readiness cache."""

import re
from .environment import EnvironmentError, atomic_json
from .status import read_json

CONTEXT = ".run/demo-current/backends/context/current-unit-context.json"
UID = re.compile(r"[A-Za-z0-9._:-]{1,128}")
ROLE = {"test": ("testUnit", "VALIDATION", "Test Vehicle"),
        "production": ("productionUnit", "PRODUCTION", "Production Vehicle")}


def project_context(state):
    vehicles = state.get("vehicles")
    if not isinstance(vehicles, dict) or "test" not in vehicles or set(vehicles) - set(ROLE):
        raise EnvironmentError("BACKEND_CURRENT_TEST_CONTEXT_REQUIRED")
    result = dict(schemaVersion=1, contractVersion="1.0.0", source="CURRENT_RUN_PROVISIONING_JOURNAL")
    seen = set()
    for role, vehicle in vehicles.items():
        # Identity comes only from a successfully provisioned current-run item.
        # An interrupted SDK attempt is not silently admitted as a query scope.
        uid = vehicle.get("systemUid")
        if not uid or not vehicle.get("unitId") or not vehicle.get("nodeId"):
            if role == "production":
                continue
            raise EnvironmentError("BACKEND_CURRENT_TEST_CONTEXT_REQUIRED")
        if (not isinstance(uid, str) or not UID.fullmatch(uid) or uid in seen
                or vehicle.get("cloud", {}).get("lifecycle") not in ("ONLINE", "DEPROVISIONED", "DELETED")):
            raise EnvironmentError("BACKEND_CURRENT_UNIT_CONTEXT_INVALID")
        seen.add(uid)
        field, wire_role, label = ROLE[role]
        result[field] = dict(systemUid=uid, unitRole=wire_role, userFacingRole=label)
    return result


def sync_context(environment, state):
    """Called only by owned lifecycle mutations, never by a dashboard read.

    Retire keeps this identity scope through backend cleanup even after the
    Cloud Unit is deleted. Rebinding an existing context is a cleanup gate,
    not permission to erase or orphan the retiring Unit's records.
    """
    with environment._writer():
        value = project_context(state)
        directory = environment._directory(".run/demo-current/backends/context")
        path = directory / "current-unit-context.json"
        if path.is_symlink():
            raise EnvironmentError("BACKEND_CONTEXT_PATH_UNSAFE")
        if path.exists():
            previous = read_json(path)
            if previous == value:
                return dict(state="UNCHANGED", context=value)
            # Permit only adding a just-provisioned peer to this same Test.
            expected_previous = {key: item for key, item in value.items() if key != "productionUnit"}
            if previous != expected_previous:
                raise EnvironmentError("BACKEND_CONTEXT_CLEANUP_REQUIRED_BEFORE_REBIND")
        atomic_json(path, value)
        return dict(state="BOUND", context=value)
