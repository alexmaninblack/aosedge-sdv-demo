# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""One-shot Cloud-only Unit observations; no guest reads or lifecycle writes.

Field projections follow public API v11 / OpenAPI 6.1.53. The source names
remain intact: installed version, pending state and instance run_state are
different facts. Read time is never substituted for a device report time.
"""

import re
from copy import deepcopy
from concurrent.futures import Future, ThreadPoolExecutor
from threading import Lock

from .status import now, object_id, observation, safe_word
from .unit_cloud import CloudFailure

PAGE_LIMIT = 100
SERVICE_DETAIL_LIMIT = 8
METRICS = ("cpu", "ram", "usedDisk", "disk", "inTraffic", "outTraffic")
SOURCE = "AOSCLOUD_OEM"
SECTIONS = ("unit", "components", "nodes", "layers", "assignedSubjects", "reportedSubjects", "services")


def public_text(value):
    if not isinstance(value, str) or len(value) > 4096:
        raise ValueError("Invalid Cloud text")
    # Error messages can contain arbitrary backend output. Never forward
    # credential-looking material, URLs, PEM blocks or control characters.
    if re.search(r"(?i)(?:bearer\s|-----BEGIN|eyJ[A-Za-z0-9_-]+\.|https?://|(?:password|secret|token|pin|private.?key)\s*[:=])", value):
        return "[REDACTED]"
    return " ".join(value.split())[:1024]


def pick(value, strings=(), integers=(), booleans=()):
    if not isinstance(value, dict):
        raise ValueError("Cloud object required")
    result = {}
    for key in strings + integers + booleans:
        item = value.get(key)
        if item is not None:
            if key in strings:
                item = public_text(item)
            elif type(item) is not (int if key in integers else bool):
                raise ValueError("Cloud scalar type mismatch")
        result[key] = item
    return result


def observed(value, **kwargs):
    return observation(SOURCE, value, **kwargs)


def failed(error):
    reason = str(error) if isinstance(error, CloudFailure) else (
        "CLOUD_SOURCE_UNAVAILABLE" if isinstance(error, OSError) else "CLOUD_RESPONSE_SCHEMA_INVALID")
    if not re.fullmatch(r"[A-Za-z0-9_:,]+", reason):
        reason = "CLOUD_SOURCE_UNAVAILABLE"
    transport = {"CLOUD_HTTP_401": "UNAUTHENTICATED", "CLOUD_HTTP_403": "FORBIDDEN",
                 "CLOUD_HTTP_404": "NOT_FOUND_OR_INACCESSIBLE"}.get(reason)
    if reason.startswith("OEM_PERMISSION_MISSING:"):
        transport = "FORBIDDEN"
    if transport is None:
        transport = "SCHEMA_INVALID" if isinstance(error, (ValueError, TypeError, KeyError)) else "SOURCE_UNAVAILABLE"
    return observed(None, reason=reason, transport=transport)


def unavailable(identity, action, reason):
    result = base(identity)
    keys = ("monitoring",) if action == "monitoring" else SECTIONS
    result.update({key: failed(CloudFailure(reason)) for key in keys})
    return finish(result)


def collection(value, projector):
    if value is None:
        return observed(None, reason="NOT_REPORTED")
    if not isinstance(value, list) or len(value) > 1000:
        raise ValueError("Invalid Cloud collection")
    return observed([projector(item) for item in value])


def node(value):
    return pick(value, ("node_id", "node_type", "name", "status", "os_type", "error_message"),
                ("num_cpus", "total_ram", "max_dmips", "error_aos_code", "error_exit_code"))


def release(value, component=False):
    if value is None:
        return None
    return pick(value, ("id", "version", "created_at", "updated_at") +
                (("type", "state", "checksum_sha256") if component else
                 ("service_id", "container_state", "container_build_info")),
                ("file_size", "failed_install_count") if component else ("min_num_instances",),
                ("is_fake",) if component else ())


def component(value):
    result = pick(value, ("type", "reported_component_id", "installed_component_id",
                         "pending_component_status", "pending_validation_batch_id", "pending_component_error"))
    for key in ("installed_component", "pending_component"):
        result[key] = release(value.get(key), component=True)
    # API UnitUpdateComponentSchema exposes installation, not version-bound
    # component process health. This is not a stopped/failed assertion.
    result["runtimeState"] = "NOT_REPORTED_BY_CLOUD"
    return result


def service_identity(value):
    return None if value is None else pick(value, ("id", "title", "service_provider_id", "service_provider_title"))


def subject(value):
    result = pick(value, ("id", "label"), booleans=("is_group", "is_protected"))
    result["services"] = collection(value.get("services"), service_identity)
    return result


def instance(value):
    result = pick(value, ("version", "version_id", "run_state", "error_message"),
                  ("instance_id", "error_aos_code", "error_exit_code"))
    result["node"] = node(value["node"]) if value.get("node") is not None else None
    result["sourceTimestamp"] = None
    return result


def service_subject_id(value):
    # OpenAPI: list rows contain a UUID; detail rows contain SubjectInfoSchema.
    if value is None:
        return None
    return object_id(value["id"] if isinstance(value, dict) else value)


def service(value):
    result = pick(value, ("error_message",),
                  ("num_instance", "pending_num_instance", "priority", "error_aos_code", "error_exit_code"))
    result["subject"] = service_subject_id(value.get("subject"))
    result["service"] = service_identity(value.get("service"))
    versions = value.get("service_versions")
    result["service_versions"] = None if versions is None else pick(versions,
        ("pending_service_version_status", "pending_validation_batch_id", "pending_verification_batch_id",
         "pending_service_version_id", "installed_service_version_id"))
    if versions is not None:
        for key in ("installed_service_version", "pending_service_version"):
            result["service_versions"][key] = release(versions.get(key))
    result["instances"] = collection(value.get("instances"), instance)
    return result


def page(cloud, path, projector):
    raw = cloud.call(path + "?limit=" + str(PAGE_LIMIT) + "&offset=0")
    if (not isinstance(raw, dict) or type(raw.get("total")) is not int or raw["total"] < 0
            or type(raw.get("offset")) is not int or raw["offset"] != 0 or not isinstance(raw.get("items"), list)
            or len(raw["items"]) > min(PAGE_LIMIT, raw["total"])):
        raise ValueError("Invalid Cloud page")
    result = collection(raw["items"], projector)
    complete = len(raw["items"]) == raw["total"]
    result["coverage"] = dict(offset=0, returned=len(raw["items"]), total=raw["total"], complete=complete)
    if not complete:
        result.update(state="INCOMPLETE", reason="CLOUD_PAGE_INCOMPLETE")
    return result


def base(identity):
    return dict(schemaVersion=1, source="AOS_CLOUD_ONLY", target="test",
                unitId=object_id(identity["unitId"]), systemUid=safe_word(identity["systemUid"], 256),
                serviceDetails={})


def finish(result):
    problems = []

    def inspect(value, path):
        if isinstance(value, dict):
            if "transport" in value and value.get("state") != "CURRENT":
                problems.append(dict(section=path, state=value["state"], reason=value.get("reason")))
            for key, child in value.items():
                inspect(child, path + "." + key)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                inspect(child, path + "." + str(index))

    inspect(result, "snapshot")
    result.update(problems=problems, readCompletedAt=now())
    return result


def unit_read(cloud, identity):
    cloud.require("units_read")
    value = cloud.call("units/" + object_id(identity["unitId"]) + "/")
    if (not isinstance(value, dict) or value.get("id") != identity["unitId"]
            or value.get("system_uid") != identity["systemUid"]):
        raise CloudFailure("CLOUD_UNIT_IDENTITY_MISMATCH")
    return value


def inventory(cloud, identity):
    result = base(identity)
    try:
        raw = unit_read(cloud, identity)
        value = pick(raw, ("id", "system_uid", "status", "online_status", "fleet", "oem",
            "updated_at", "last_online_changed_at", "update_strategy", "fota_blocked", "last_update_info"))
        value["connectivity"] = {"Online": "ONLINE", "Offline": "OFFLINE", "Connected": "CONNECTED"}.get(
            value["online_status"], "UNKNOWN")
        config = raw.get("installed_unit_config")
        value["installedUnitConfig"] = None if config is None else pick(config, ("unit_model", "version"))
        value["unitSets"] = collection(raw.get("unit_sets"), lambda item: pick(item, ("id", "title")))
        result["unit"] = observed(value)
    except (CloudFailure, OSError, ValueError, TypeError, KeyError) as error:
        result.update({key: failed(error) for key in SECTIONS})
        return finish(result)
    for key, field, mapper in (
        ("components", "unit_update_components", component), ("nodes", "nodes", node),
        ("layers", "layers", lambda item: pick(item, ("layer_id", "layer_uid", "layer_version_id",
            "layer_version_version", "status", "error"))),
        ("assignedSubjects", "assigned_subjects", subject), ("reportedSubjects", "reported_subjects", subject)):
        try:
            result[key] = collection(raw.get(field), mapper)
        except (ValueError, TypeError, KeyError) as error:
            result[key] = failed(error)
    try:
        cloud.require("units_subjects_services_list")
        result["services"] = page(cloud, "units/" + identity["unitId"] + "/subjects-services/", service)
    except (CloudFailure, OSError, ValueError, TypeError, KeyError) as error:
        result["services"] = failed(error)
    identifiers = sorted({row["service"]["id"] for row in result["services"].get("value") or []
                          if row.get("service") and row["service"].get("id")})
    if len(identifiers) > SERVICE_DETAIL_LIMIT:
        result["services"].update(state="INCOMPLETE", reason="CLOUD_SERVICE_DETAIL_LIMIT")
    def detail(identifier):
        try:
            identifier = object_id(identifier)
            cloud.require("units_subjects_services_read")
            value = page(cloud, "units/" + identity["unitId"] + "/subjects-services/" + identifier + "/", service)
            if any(not row.get("service") or row["service"].get("id") != identifier for row in value["value"]):
                raise CloudFailure("CLOUD_SERVICE_IDENTITY_MISMATCH")
            return value
        except (CloudFailure, OSError, ValueError, TypeError, KeyError) as error:
            return failed(error)
    # Different, exact read endpoints; each requested once and bounded. No
    # repeated polls, tenant-wide scan, missing-detail fallback or mutation.
    with ThreadPoolExecutor(max_workers=SERVICE_DETAIL_LIMIT) as pool:
        pending = {identifier: pool.submit(detail, identifier) for identifier in identifiers[:SERVICE_DETAIL_LIMIT]}
        result["serviceDetails"] = {identifier: future.result() for identifier, future in pending.items()}
    return finish(result)


def retain_last_known(current, previous):
    """Keep observations only within the same exact Unit/source binding."""
    current = deepcopy(current)
    if not previous or any(current.get(key) != previous.get(key) for key in ("source", "unitId", "systemUid")):
        return current
    if "services" in current and current["services"].get("value") is None and previous.get("serviceDetails"):
        # A failed list/Unit read cannot establish that previously observed
        # service details disappeared. Explicit successful empty lists can.
        current["serviceDetails"] = {key: deepcopy(current["services"])
                                     for key in previous["serviceDetails"]}
    def merge(value, old):
        if not isinstance(value, dict) or not isinstance(old, dict):
            return
        if ("transport" in value and value.get("value") is None and old.get("value") is not None
                and value.get("state") == "UNKNOWN"):
            value.update(value=deepcopy(old["value"]), state="STALE", sourceTimestamp=old.get("sourceTimestamp"),
                         lastKnownReadCompletedAt=old.get("lastKnownReadCompletedAt", old.get("readCompletedAt")))
            return
        for key, child in value.items():
            merge(child, old.get(key))
    merge(current, previous)
    return finish(current)


class SharedCloudObserver:
    """Process-local read sharing only; no journal, polling or mutation store."""

    def __init__(self):
        self.lock = Lock()
        self.in_flight = {}
        self.last_known = {}

    def read(self, key, fetch):
        with self.lock:
            existing = self.in_flight.get(key)
            future = existing or Future()
            if existing is None:
                self.in_flight[key] = future
        if existing is not None:
            return deepcopy(future.result())
        try:
            value = fetch()
            with self.lock:
                value = retain_last_known(value, self.last_known.get(key))
                self.last_known[key] = deepcopy(value)
            future.set_result(value)
            return deepcopy(value)
        except BaseException as error:
            future.set_exception(error)
            raise
        finally:
            with self.lock:
                self.in_flight.pop(key, None)


def monitoring(cloud, identity):
    result = base(identity)
    try:
        unit_read(cloud, identity)
        cloud.require("units_monitoring_list")
        raw = cloud.call("units/" + identity["unitId"] + "/monitoring/?datetime_from=latest")
        if not isinstance(raw, list) or len(raw) > 1000:
            raise ValueError("Invalid Cloud monitoring array")
        metrics = {}
        for key in METRICS:
            samples = []
            reported = not raw  # An explicitly empty response is not missing.
            missing = False
            for group in raw:
                if not isinstance(group, dict):
                    raise ValueError("Invalid monitoring group")
                values = group.get(key)
                if values is None:
                    missing = True
                    continue
                if not isinstance(values, list) or len(values) > 1000:
                    raise ValueError("Invalid metric samples")
                reported = True
                for value in values:
                    sample = pick(value, ("parameter", "partition", "system_uid", "time", "measurementType",
                                          "serviceId", "subjectId", "nodeId"), ("value", "instance"))
                    if sample["system_uid"] not in (None, identity["systemUid"]):
                        raise CloudFailure("CLOUD_METRIC_UNIT_IDENTITY_MISMATCH")
                    sample["sourceTimestamp"] = sample["time"]
                    sample["state"] = "CURRENT" if sample["value"] is not None and sample["time"] is not None else "UNKNOWN"
                    samples.append(sample)
            metric = observed(samples if reported else None, reason=None if reported else "NOT_REPORTED")
            if reported and missing:
                metric.update(state="INCOMPLETE", reason="METRIC_GROUP_NOT_REPORTED")
            if any(sample["state"] != "CURRENT" for sample in samples):
                metric.update(state="INCOMPLETE", reason="METRIC_VALUE_OR_TIME_NOT_REPORTED")
            # CPU is explicitly documented in Cloud DMIPS. The REST schema
            # does not specify storage/memory/traffic scaling: preserve raw
            # values without guessing bytes, KiB, rates or percentages.
            metric.update(unit="DMIPS" if key == "cpu" else None,
                          unitEvidence="CLOUD_DMIPS_DOCUMENTATION" if key == "cpu" else "UNIT_NOT_VERIFIED")
            metrics[key] = metric
        result["monitoring"] = observed(metrics)
    except (CloudFailure, OSError, ValueError, TypeError, KeyError) as error:
        result["monitoring"] = failed(error)
    return finish(result)
