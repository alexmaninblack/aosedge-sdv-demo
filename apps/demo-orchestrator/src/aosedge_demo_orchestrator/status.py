# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Read-only status collection. No lifecycle state or observation cache is written."""

import json
import math
import os
import re
import stat
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
from uuid import UUID


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def observation(source, value=None, reason=None, transport="AVAILABLE", state=None):
    return {
        "value": value,
        "source": source,
        "sourceTimestamp": None,
        "readCompletedAt": now(),
        "state": state or ("CURRENT" if reason is None else "UNKNOWN"),
        "transport": transport,
        "reason": reason,
    }


def skipped(source, reason):
    return observation(source, reason=reason, state="NOT_APPLICABLE")


def safe_word(value, limit=128):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_. :/@+-]{1,%d}" % limit, value):
        raise ValueError("Invalid public field")
    return value


def object_id(value):
    if not isinstance(value, str):
        raise ValueError("Invalid object identity")
    return str(UUID(value))


def read_json(path, limit=65536):
    if path.is_symlink() or not stat.S_ISREG(path.stat().st_mode):
        raise ValueError("Expected a regular file")
    with path.open("rb") as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise ValueError("Input too large")
    return json.loads(data)


def project_root():
    # Editable installation is the supported first-slice deployment.
    return Path(__file__).resolve().parents[4]


def _path(value, root):
    if not isinstance(value, str) or not value or "\x00" in value or "\n" in value:
        raise ValueError("Invalid configured path")
    result = Path(value).expanduser()
    return result if result.is_absolute() else root / result


def load_configuration(root, config_path=None):
    path = Path(config_path).expanduser() if config_path else root / ".local/demo-control/status.json"
    if not path.is_absolute():
        path = Path.cwd() / path
    if not path.exists() and config_path is not None:
        raise ValueError("Explicit configuration is missing")
    custom = path.exists()
    data = read_json(path) if custom else {"schemaVersion": 1}
    if not isinstance(data, dict) or type(data.get("schemaVersion")) is not int or data["schemaVersion"] != 1:
        raise ValueError("Unsupported configuration")
    if set(data) - {"schemaVersion", "vehicles", "cloudProfiles", "cloudPython"}:
        raise ValueError("Unknown configuration field")
    journal = skipped("CURRENT_RUN_JOURNAL", "NO_MANAGED_CURRENT_RUN")
    managed_owner = None
    vehicles = data.get("vehicles", {})
    journal_path = root / ".run/demo-current/journal.json"
    if config_path is None and journal_path.with_name("journal.json.pending").exists():
        raise ValueError("Current journal write requires recovery")
    if config_path is None and (journal_path.exists() or journal_path.is_symlink()):
        # Managed manufacture must never inherit Unit IDs or SSH credentials
        # from the retained experimental VM's observation profile.
        state = read_json(journal_path)
        if (not isinstance(state, dict) or type(state.get("schemaVersion")) is not int
                or state["schemaVersion"] != 1 or state.get("kind") != "democtl.current-run"
                or state.get("stage") not in ("CREATING", "MANUFACTURED", "LOCAL_ACTIVE", "LOCAL_STOPPED", "RECOVERY_REQUIRED", "RETIRING_LOCAL")
                or not isinstance(state.get("vehicles"), dict)
                or (not state["vehicles"] and state.get("scope") != "FACTORY_COPY_ONLY")
                or set(state["vehicles"]) - {"test", "production"}):
            raise ValueError("Unsupported current journal")
        if state.get("cloudBinding"):
            managed_owner = object_id(state["cloudBinding"]["ownerId"])
        vehicles = {"test": None, "production": None}
        for role, entry in state["vehicles"].items():
            expected = ".local/demo-current/" + ("validation" if role == "test" else role) + ".qcow2"
            if (not isinstance(entry, dict) or entry.get("overlay") != expected
                    or entry.get("state") not in ("PLANNED", "MANUFACTURED")
                    or (any(entry.get(key) is not None for key in ("unitId", "nodeId", "unitSetId"))
                        and not isinstance(entry.get("cloud"), dict))):
                raise ValueError("Invalid manufactured role")
            object_id(entry.get("localVmId"))
            vehicles[role] = {"overlay": expected}
            for key in ("unitId", "unitSetId"):
                if entry.get(key):
                    vehicles[role][key] = object_id(entry[key])
            if entry.get("cloud") and entry.get("systemUid"):
                vehicles[role]["systemUid"] = safe_word(entry["systemUid"])
                vehicles[role]["cloudLifecycle"] = safe_word(entry["cloud"].get("lifecycle", "UNKNOWN"))
            runtime = entry.get("runtime")
            if runtime:
                if not isinstance(runtime, dict):
                    raise ValueError("Invalid VM runtime")
                vehicles[role].update(sshPort=entry["sshPort"], dnsPort=18053)
                if runtime.get("accessCreated"):
                    vehicles[role]["accessRoot"] = ".run/demo-current/" + role + "-access"
            factory = state.get("factory")
            if factory:
                vehicles[role].update(imageVersion=factory["version"], imageSha256=factory["sha256"])
        journal = observation("CURRENT_RUN_JOURNAL", {"stage": state["stage"],
                              "roles": sorted(state["vehicles"]), "currentVehicle": state.get("currentVehicle")},
                              reason="RECOVERY_REQUIRED" if state["stage"] not in (
                                  "MANUFACTURED", "LOCAL_ACTIVE", "LOCAL_STOPPED") else None)
    if not isinstance(vehicles, dict) or set(vehicles) - {"test", "production"}:
        raise ValueError("Invalid vehicle selectors")
    resolved = {}
    for role, filename in (("test", "validation"), ("production", "production")):
        entry = vehicles.get(role, {"overlay": ".local/demo-current/" + filename + ".qcow2"})
        if entry is None:
            resolved[role] = None
            continue
        if not isinstance(entry, dict) or set(entry) - {
            "overlay", "imageVersion", "imageSha256", "sshPort", "accessRoot",
            "cloudHost", "unitId", "unitSetId", "services", "dnsPort", "systemUid", "cloudLifecycle"
        }:
            raise ValueError("Invalid vehicle configuration")
        item = dict(entry)
        item["overlay"] = _path(item["overlay"], root)
        for key in ("imageVersion",):
            if key in item:
                safe_word(item[key])
        for key in ("systemUid", "cloudLifecycle"):
            if key in item:
                safe_word(item[key])
        if "imageSha256" in item and not re.fullmatch(r"[0-9a-f]{64}", item["imageSha256"]):
            raise ValueError("Invalid digest reference")
        for key in ("unitId", "unitSetId"):
            if key in item:
                item[key] = object_id(item[key])
        for key in ("sshPort", "dnsPort"):
            if key in item and (type(item[key]) is not int or not 1 <= item[key] <= 65535):
                raise ValueError("Invalid port")
        if "accessRoot" in item:
            item["accessRoot"] = _path(item["accessRoot"], root)
        item.setdefault("cloudHost", "aoscloud.io")
        if not isinstance(item["cloudHost"], str) or len(item["cloudHost"]) > 253 or any(
            not re.fullmatch(r"[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?", label)
            for label in item["cloudHost"].split(".")
        ):
            raise ValueError("Invalid DNS name")
        item.setdefault("services", ["aos-iam-prov.service", "aos-iam.service", "aos-sm.service", "aos-cm.service"])
        if not isinstance(item["services"], list) or not 1 <= len(item["services"]) <= 16:
            raise ValueError("Invalid service list")
        if any(not isinstance(s, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.@-]*\.service", s) for s in item["services"]):
            raise ValueError("Invalid service name")
        resolved[role] = item
    defaults = {
        "oem-delivery": {"credential": "~/.aos/security/aos-user-oem.p12", "expectedRole": "oem"},
        "service-provider": {"credential": "~/.aos/security/aos-user-sp.p12", "expectedRole": "service provider"},
    }
    profiles = data.get("cloudProfiles", defaults)
    if not isinstance(profiles, dict) or len(profiles) > 8:
        raise ValueError("Invalid Cloud profiles")
    normalized = {}
    for name, profile in profiles.items():
        if not re.fullmatch(r"[a-z][a-z0-9-]{0,39}", name) or not isinstance(profile, dict):
            raise ValueError("Invalid Cloud profile")
        if set(profile) - {"credential", "expectedRole", "expectedOwnerId"}:
            raise ValueError("Invalid Cloud profile field")
        if profile.get("expectedRole") not in ("oem", "service provider"):
            raise ValueError("Unknown Cloud role")
        normalized[name] = dict(profile, credential=_path(profile["credential"], root))
        if "expectedOwnerId" in profile:
            normalized[name]["expectedOwnerId"] = object_id(profile["expectedOwnerId"])
        if managed_owner and name == "oem-delivery":
            if profile.get("expectedOwnerId") not in (None, managed_owner):
                raise ValueError("Managed OEM owner conflicts with configured profile")
            normalized[name]["expectedOwnerId"] = managed_owner
    return {
        "vehicles": resolved, "cloudProfiles": normalized,
        "cloudPython": _path(data.get("cloudPython", "~/.aos/venv/bin/python3"), root),
        "configuration": "CURRENT_RUN_JOURNAL" if journal["value"] else (
            "LOCAL_PROFILE" if custom else "CANONICAL_LAYOUT_DEFAULTS"),
        "journal": journal,
    }


class StatusService:
    def __init__(self, root=None, config_path=None):
        self.root = Path(root) if root else project_root()
        self.config_path = config_path

    def collect(self, target="all", guest=False, cloud=False, timeout=8.0, profile=None):
        from .probes import process_snapshot, local_vehicle, guest_status, host_dns
        from .cloud import cloud_status, local_profile

        if target not in ("test", "production", "all"):
            raise ValueError("Invalid target")
        if type(guest) is not bool or type(cloud) is not bool:
            raise ValueError("Invalid read mode")
        if isinstance(timeout, bool) or not isinstance(timeout, (float, int)) or not math.isfinite(timeout) or not 0.2 <= timeout <= 30:
            raise ValueError("Timeout must be between 0.2 and 30 seconds")
        if profile and not cloud:
            raise ValueError("Profile requires Cloud mode")
        started = now()
        try:
            config = load_configuration(self.root, self.config_path)
            if profile and profile not in config["cloudProfiles"]:
                raise ValueError("Unknown profile")
        except (OSError, ValueError, KeyError, TypeError):
            return {"schemaVersion": 1, "startedAt": started, "readCompletedAt": now(),
                    "configuration": observation("LOCAL_CONFIG", reason="CONFIG_INVALID", transport="MALFORMED"),
                    "vehicles": {}, "cloud": {}}
        roles = ("test", "production") if target == "all" else (target,)
        processes = process_snapshot(timeout)
        vehicles = {}
        jobs = {}
        with ThreadPoolExecutor(max_workers=10) as pool:
            for role in roles:
                item = config["vehicles"][role]
                local = local_vehicle(item, processes, timeout, network=guest)
                vehicles[role] = {
                    "technicalRole": "VALIDATION" if role == "test" else "PRODUCTION",
                    "local": local,
                    "guest": skipped("GUEST_SSH", "NOT_REQUESTED"),
                    "hostDns": skipped("HOST_DNS", "NOT_REQUESTED"),
                }
                if guest:
                    jobs[("guest", role)] = pool.submit(guest_status, item, local, timeout)
                    jobs[("hostDns", role)] = pool.submit(host_dns, item, min(timeout, 1.0))
            cloud_results = {}
            for name, item in config["cloudProfiles"].items():
                if profile and name != profile:
                    continue
                if cloud:
                    targets = {role: config["vehicles"][role] for role in roles}
                    jobs[("cloud", name)] = pool.submit(cloud_status, name, item, targets, config["cloudPython"], timeout)
                else:
                    cloud_results[name] = local_profile(name, item)
            for (kind, name), future in jobs.items():
                try:
                    result = future.result()
                except Exception:
                    result = observation(kind.upper(), reason="PROBE_FAILED", transport="SOURCE_UNAVAILABLE")
                if kind in ("guest", "hostDns"):
                    vehicles[name][kind] = result
                else:
                    cloud_results[name] = result
        return {
            "schemaVersion": 1, "startedAt": started, "readCompletedAt": now(),
            "configuration": observation("LOCAL_CONFIG", {"source": config["configuration"]}),
            "vehicles": vehicles, "cloud": cloud_results,
            "journal": config["journal"],
            "claim": "Observations only; not demo qualification or mutation authorization.",
        }


def has_unknown(value):
    if isinstance(value, dict):
        return value.get("state") in ("UNKNOWN", "INCOMPLETE", "STALE") or any(has_unknown(v) for v in value.values())
    return isinstance(value, list) and any(has_unknown(v) for v in value)
