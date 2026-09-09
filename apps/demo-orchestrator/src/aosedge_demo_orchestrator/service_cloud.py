# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Read-only service ownership/catalog worker. Never exports credentials/config."""

import contextlib
import io
import json
import sys
from pathlib import Path
from urllib.parse import urlencode

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from aosedge_demo_orchestrator.cloud_observation import pick, failed
from aosedge_demo_orchestrator.status import object_id, observation
from aosedge_demo_orchestrator.unit_cloud import Cloud, CloudFailure

PERMISSIONS = ("services_list", "services_read", "services_create", "services_service_versions_list",
               "services_units_list", "deployment_bundles_create", "service_providers_list")


def observed(value=None, **values):
    return observation("AOS_CLOUD_SERVICE_API", value, **values)


def error_observation(error):
    value = failed(error)
    value["source"] = "AOS_CLOUD_SERVICE_API"
    if isinstance(error, CloudFailure) and str(error).startswith("SP_PERMISSION_MISSING:"):
        value["transport"] = "FORBIDDEN"
    if isinstance(error, CloudFailure) and str(error) == "CLOUD_HTTP_422":
        value["transport"] = "SCHEMA_INVALID"
    return value


def service_view(row, user, detail=False):
    value = pick(row, ("title", "codename", "service_provider_title", "created_at"))
    value["id"] = object_id(row["id"])
    owner = row.get("service_provider_id") if detail else row.get("service_provider")
    owner = owner or row.get("service_provider")
    value["serviceProviderId"] = object_id(owner)
    if detail and row.get("service_provider") and object_id(row["service_provider"]) != value["serviceProviderId"]:
        raise CloudFailure("SERVICE_OWNER_FIELDS_CONFLICT")
    if user["role"] == "service provider" and value["serviceProviderId"] != user["ownerId"]:
        raise CloudFailure("SERVICE_SP_OWNERSHIP_MISMATCH")
    value["authorityRelation"] = "OWNED_BY_AUTHENTICATED_SP" if user["role"] == "service provider" else "VISIBLE_TO_OEM_NOT_OEM_OWNED"
    value["latestVersion"] = pick(row, ("latest_version",))["latest_version"] if not detail else None
    return value


def provider_view(row):
    return dict(id=object_id(row["id"]), **pick(row, ("title",)))


def version_view(row):
    return dict(id=object_id(row["id"]), **pick(row, ("version", "container_state", "created_at"), booleans=("is_resource_limits",)))


def unit_view(row):
    value = dict(id=object_id(row["id"]), oemId=object_id(row["oem_id"]), **pick(row, ("system_uid",)))
    subjects = row.get("subjects")
    if subjects is not None and (not isinstance(subjects, list) or len(subjects) > 1000):
        raise ValueError("Service Unit Subject schema")
    value["subjectIds"] = None if subjects is None else [object_id(item) for item in subjects]
    return value


def pages(cloud, path, projector, permission):
    values, seen, total, offset = [], set(), None, 0
    try:
        cloud.require(permission)
        for _ in range(8):
            response = cloud.call(path + ("&" if "?" in path else "?") + urlencode(dict(limit=100, offset=offset)))
            if (not isinstance(response, dict) or type(response.get("total")) is not int or response["total"] < 0
                    or type(response.get("offset")) is not int or response["offset"] != offset
                    or not isinstance(response.get("items"), list) or len(response["items"]) > 100):
                raise ValueError("Service collection schema")
            if total is not None and total != response["total"]:
                return observed(dict(items=values, coverage=dict(total=total, returned=len(values), complete=False)),
                    state="INCOMPLETE", reason="SERVICE_COLLECTION_CHANGED_DURING_READ")
            total = response["total"]
            rows = response["items"]
            for row in rows:
                item = projector(row)
                if item["id"] in seen:
                    raise ValueError("Duplicate service collection identity")
                seen.add(item["id"])
                values.append(item)
            offset += len(rows)
            if offset > total or (not rows and offset < total):
                raise ValueError("Service collection coverage")
            if offset == total:
                return observed(dict(items=values, coverage=dict(total=total, returned=len(values), complete=True)))
        return observed(dict(items=values, coverage=dict(total=total, returned=len(values), complete=False)),
                        state="INCOMPLETE", reason="SERVICE_COLLECTION_PAGE_LIMIT")
    except (CloudFailure, OSError, ValueError, TypeError, KeyError) as error:
        # A failed page is not an empty catalog. Do not forward malformed or
        # foreign-owner rows, even when earlier pages appeared usable.
        return error_observation(error)


def inspect(cloud, request):
    user = cloud.user
    result = dict(authority=observed(dict(role=user["role"], ownerId=user["ownerId"],
        expectedOwnerId=request.get("ownerId"), ownerBinding="MATCHED" if request.get("ownerId") else "NOT_CONFIGURED",
        permissions={name: name in user["effectivePermissions"] for name in PERMISSIONS},
        teamBinding="NOT_CONFIGURED", mutationAuthority="NOT_EVALUATED")))
    if request["action"] == "list":
        # The live v11 SP route rejects the optional service_provider filter
        # (422). Read the ordinary catalog and enforce ownership on every row;
        # never reinterpret an OEM-visible peer as owned by this SP.
        path = "services/"
        result["services"] = pages(cloud, path, lambda row: service_view(row, user), "services_list")
        result["providers"] = (pages(cloud, "service-providers/", provider_view, "service_providers_list")
            if user["role"] == "oem" else observed(None, state="NOT_APPLICABLE", reason="SP_PROFILE_OBSERVES_OWN_SERVICES_ONLY"))
        return result
    identity = object_id(request["serviceId"])
    try:
        cloud.require("services_read")
        detail = service_view(cloud.call("services/" + identity + "/"), user, detail=True)
        if detail["id"] != identity:
            raise CloudFailure("SERVICE_RESPONSE_ID_MISMATCH")
        result["service"] = observed(detail)
    except (CloudFailure, OSError, ValueError, TypeError, KeyError) as error:
        result["service"] = error_observation(error)
        return result
    result["versions"] = pages(cloud, "services/" + identity + "/service-versions/", version_view, "services_service_versions_list")
    result["units"] = pages(cloud, "services/" + identity + "/units/", unit_view, "services_units_list")
    return result


def execute(request):
    if request.get("action") not in ("list", "status") or request.get("expectedRole") not in ("oem", "service provider"):
        raise CloudFailure("SERVICE_READ_ACTION_INVALID")
    try:
        cloud = Cloud(request, expected_role=request["expectedRole"])
        return inspect(cloud, request)
    except (CloudFailure, OSError, ValueError, TypeError, KeyError) as error:
        return dict(authority=error_observation(error))


def main():
    try:
        request = json.loads(sys.stdin.read(65537))
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            result = execute(request)
    except Exception:
        result = dict(authority=observed(None, reason="SERVICE_CLOUD_READER_UNAVAILABLE"))
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
