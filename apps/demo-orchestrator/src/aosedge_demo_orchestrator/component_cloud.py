# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Bounded Aos deployment-bundle API adapter, owned by Demo Control."""

import json
import urllib.request
import urllib.error
from pathlib import Path
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlencode

from .components import COMPONENT, VERSION
from .unit_cloud import Cloud, CloudFailure
from .status import object_id

COMPONENT_ID = "c33bc994-460b-476f-8000-934b55a70455"


def guard(value):
    if value.get("preProvisioning"):
        if (value.get("remainingUnits") != [] or value["test"].get("members") != []
                or value["production"].get("members") != []
                or value["testSet"]["is_validation_set"] is not True
                or value["productionSet"]["is_validation_set"] is not False
                or not value["testSet"].get("fleet")
                or value["testSet"]["fleet"] != value["productionSet"]["fleet"]
                or value["testSet"]["id"] == value["productionSet"]["id"]):
            raise CloudFailure("COMPONENT_EMPTY_CLOUD_SCOPE_NOT_PROVEN")
        return
    if (value["testSet"]["is_validation_set"] is not True
            or value["productionSet"]["is_validation_set"] is not False
            or value["test"]["fleet"] != value["production"]["fleet"]
            or value["test"]["id"] == value["production"]["id"]
            or value["test"]["online_status"] != "Online"):
        raise CloudFailure("COMPONENT_TEST_ONLY_SCOPE_NOT_PROVEN")


def batch_guard(value, request, owner):
    entries = value.get("update_items") or []
    if (value.get("oem_id") != owner or value.get("architectures") != ["arm64"]
            or len(entries) != 1 or entries[0].get("identity_id") != COMPONENT_ID
            or entries[0].get("codename") != COMPONENT or entries[0].get("version") != request["version"]):
        raise CloudFailure("COMPONENT_VERIFICATION_BATCH_SCOPE_MISMATCH")


def upload(cloud, request):
    from .component_worker import verify
    cloud.require("deployment_bundles_create")
    path = Path(request["bundle"])
    verify(path, Path(request["credential"]), request["expectedSha256"])
    boundary = "democtl-" + uuid4().hex
    raw = path.read_bytes()
    # Exactly the official uploader endpoint and multipart field, with a
    # bounded timeout and no retry, redirect or TLS verification fallback.
    body = ('--' + boundary + '\r\nContent-Disposition: form-data; name="file"; filename="'
        + path.name + '"\r\nContent-Type: application/gzip\r\n\r\n').encode() + raw + ('\r\n--' + boundary + '--\r\n').encode()
    req = urllib.request.Request(cloud.base + "deployment-bundles/upload/", data=body, method="POST",
        headers={"Accept": "application/json", "Content-Type": "multipart/form-data; boundary=" + boundary})
    try:
        with cloud.opener.open(req, timeout=45) as response:
            if response.status != 201:
                raise CloudFailure("COMPONENT_UPLOAD_RESPONSE_UNCERTAIN")
            raw = response.read(1048577)
            if len(raw) > 1048576:
                raise CloudFailure("COMPONENT_UPLOAD_RESPONSE_UNCERTAIN")
            result = json.loads(raw)
    except urllib.error.HTTPError as error:
        raise CloudFailure("COMPONENT_UPLOAD_HTTP_" + str(error.code)) from None
    from .cloud_observation import pick
    public = pick(result, ("state", "build_info"))
    return dict(deploymentId=object_id(result["id"]), state=public["state"],
                buildInfo=public["build_info"], httpStatus=201)


def project(value, keys):
    return {key: value.get(key) for key in keys}


def send_observed(value, component_id):
    for item in value["test"].get("components", []):
        for field in ("installed_component", "pending_component"):
            if (item.get(field) or {}).get("id") == component_id:
                return field.upper()
    if any(item.get("component_type") == COMPONENT and item.get("update_component") == component_id
           for item in value.get("testSendRequests", [])):
        return "REQUEST_LISTED"
    return None


def unit_view(cloud, identity, strict=False):
    from .cloud_observation import pick
    value = cloud.call("units/" + object_id(identity["unitId"]) + "/")
    if value["system_uid"] != identity["systemUid"] or (strict and value.get("id") != identity["unitId"]):
        raise CloudFailure("COMPONENT_UNIT_IDENTITY_CHANGED")
    result = project(value, ("id", "status", "online_status", "fleet", "update_strategy", "fota_blocked"))
    if strict:
        result = pick(value, ("id", "status", "online_status", "fleet", "update_strategy", "fota_blocked"))
    result["unitSets"] = [object_id(item["id"]) for item in value.get("unit_sets") or []]
    if identity["unitSetId"] not in result["unitSets"]:
        raise CloudFailure("COMPONENT_ROLE_UNIT_SET_MISSING")
    result["components"] = []
    if strict and not isinstance(value.get("unit_update_components"), list):
        result["components"] = None
        return result
    for item in value.get("unit_update_components") or []:
        if item.get("type") != COMPONENT:
            continue
        row = project(item, ("type", "pending_component_status", "pending_validation_batch_id", "installed_component_id"))
        if strict:
            row = pick(item, ("type", "pending_component_status", "pending_validation_batch_id", "installed_component_id"))
        row.update(pick(item, ("pending_component_error",)))
        for name in ("installed_component", "pending_component"):
            row[name] = project(item[name], ("id", "version", "state", "is_fake")) if item.get(name) else None
            if strict and row[name] is not None:
                row[name] = pick(item[name], ("id", "version", "state"), booleans=("is_fake",))
        result["components"].append(row)
    return result


def snapshot(cloud, request):
    if request.get("purpose") == "overview":
        cloud.require("units_read")
        with ThreadPoolExecutor(max_workers=2) as pool:
            unit = pool.submit(unit_view, cloud, request["vehicles"]["test"])
            versions = pool.submit(cloud.pages, "components/" + COMPONENT_ID + "/versions/")
            result = dict(test=unit.result(), versions=[project(item, ("version", "state", "is_fake"))
                          for item in versions.result()])
        published = [item["version"] for item in result["versions"] if item.get("is_fake") is False
                     and isinstance(item.get("version"), str) and VERSION.fullmatch(item["version"])]
        result["latestPublishedVersion"] = max(published, key=lambda value: tuple(map(int, value.split("."))), default=None)
        result["source"] = "AOS_CLOUD_ONLY"
        return result
    pre_provisioning = request.get("preProvisioning") is True
    purpose = request.get("purpose", "status")
    confirmation = purpose == "confirm"
    approval = purpose in ("approve", "unapprove")
    if "production" not in request["vehicles"]:
        # A single-role qualification owns no Production VM. Observe exactly
        # the existing member of the provisioner's bound Production set; never
        # adopt it into the local lifecycle journal or mutate it.
        set_id = object_id(request["productionSetId"])
        members = cloud.pages("unit-sets/" + set_id + "/units/")
        if len(members) != 1:
            raise CloudFailure("COMPONENT_PRODUCTION_GUARD_MEMBER_AMBIGUOUS")
        request = dict(request, vehicles=dict(request["vehicles"], production=dict(
            unitId=object_id(members[0]["id"]), systemUid=members[0]["system_uid"], unitSetId=set_id)))
    version = request["version"]
    if not confirmation and not approval:
        component = cloud.call("components/" + COMPONENT_ID + "/")
        if component["codename"] != COMPONENT:
            raise CloudFailure("COMPONENT_CLOUD_IDENTITY_MISMATCH")
    def versions():
        return [project(item, ("id", "version", "state", "file_size", "is_fake"))
                for item in cloud.pages("components/" + COMPONENT_ID + "/versions/")]
    def bundles():
        # v11 exposes GET on the collection only; /{id}/ supports DELETE,
        # not GET. Resolve the exact recorded ID from the documented list.
        return [project(item, ("id", "state", "file_size", "items"))
                for item in cloud.pages("deployment-bundles/")
                if (item["id"] == request["deploymentId"] if request.get("deploymentId") else any(
                    entry.get("codename") == COMPONENT and entry.get("version") == version
                    for entry in item.get("items") or []))]
    def batches():
        if request.get("batchId"):
            detail = cloud.call("verification-batch/" + object_id(request["batchId"]) + "/")
            batch_guard(detail, request, cloud.user["ownerId"])
            return [project(detail, ("id", "state", "oem_id", "architectures", "update_bundle_id", "update_items", "approval_states"))]
        matches = []
        for item in cloud.pages("verification-batch/?" + urlencode({"search": COMPONENT})):
            entries = item.get("update_items") or []
            if any(entry.get("codename") == COMPONENT and entry.get("version") == version for entry in entries):
                detail = cloud.call("verification-batch/" + object_id(item["id"]) + "/")
                matches.append(project(detail, ("id", "state", "oem_id", "architectures", "update_bundle_id", "update_items", "approval_states")))
        return matches
    tasks = {"versions": versions if purpose in ("status", "upload", "send") else lambda: [],
             "deploymentBundles": bundles if ((not confirmation and not (approval and request.get("deploymentId")))
                 or (confirmation and not request.get("batchId"))) else lambda: [],
             "verificationBatches": batches if not confirmation or request.get("batchId") else lambda: [],
             "testSendRequests": lambda: [], "testAvailableComponents": lambda: []}
    if confirmation or (approval and (not pre_provisioning or request.get("roleSetIds"))):
        if pre_provisioning:
            set_id = object_id(request["roleSetIds"]["production"])
            def production():
                details = cloud.call("unit-sets/" + set_id + "/")
                members = cloud.pages("unit-sets/" + set_id + "/units/")
                view = project(details, ("id", "title", "fleet", "is_validation_set", "update_strategy", "allow_unknown_components"))
                return dict(members=[{key: unit[key] for key in ("id", "system_uid")} for unit in members], unitSet=view)
            tasks["production"] = production
        else:
            tasks["production"] = lambda: unit_view(cloud, request["vehicles"]["production"])
    elif pre_provisioning:
        inventory = cloud.inventory()
        from .units import UnitService
        # Same role-set resolution as provisioning; no fabricated Unit identities.
        sets = UnitService._bindings(None, {}, inventory)
        tasks["remainingUnits"] = lambda: [item["id"] for item in inventory["units"]]
        tasks["preProvisioning"] = lambda: True
        tasks["testSendRequests"] = lambda: []
        tasks["testAvailableComponents"] = lambda: []
        for role, value in sets.items():
            view = project(value, ("id", "title", "fleet", "is_validation_set", "update_strategy", "allow_unknown_components"))
            tasks[role + "Set"] = lambda view=view: view
            tasks[role] = lambda value=value, view=view: dict(members=value["members"], unitSet=view)
        # List and detail serializers need not expose the same optional fields.
        # Keep both observations for explicit reconciliation of old list guards.
        tasks["productionDetail"] = lambda: project(cloud.call("unit-sets/" + object_id(sets["production"]["id"]) + "/"),
            ("id", "title", "fleet", "is_validation_set", "update_strategy", "allow_unknown_components"))
    else:
        if purpose in ("status", "send"):
            tasks["testSendRequests"] = lambda: [project(item, ("id", "component_type", "update_component"))
                for item in cloud.call("units/" + object_id(request["vehicles"]["test"]["unitId"])
                                       + "/components/send-requests/") if item.get("component_type") == COMPONENT]
            tasks["testAvailableComponents"] = lambda: [project(item, ("id", "type", "version", "file_size"))
                for item in cloud.call("units/" + object_id(request["vehicles"]["test"]["unitId"]) + "/available-components/")
                if item.get("type") == COMPONENT]
        tasks.update({role: lambda item=item: unit_view(cloud, item) for role, item in request["vehicles"].items()})
        tasks.update({role + "Set": lambda item=item: project(cloud.call("unit-sets/" + object_id(item["unitSetId"]) + "/"),
        ("id", "title", "fleet", "is_validation_set", "update_strategy", "allow_unknown_components"))
        for role, item in request["vehicles"].items()})
    with ThreadPoolExecutor(max_workers=6) as pool:
        pending = {key: pool.submit(job) for key, job in tasks.items()}
        result = {key: job.result() for key, job in pending.items()}
    catalog = result["versions"]
    if pre_provisioning and "productionDetail" in result:
        result["productionListObservation"] = result["production"]
        result["production"] = dict(members=result["production"]["members"], unitSet=result.pop("productionDetail"))
        result["productionSet"] = result["production"]["unitSet"]
    published = [item["version"] for item in catalog if isinstance(item.get("version"), str)
                 and VERSION.fullmatch(item["version"]) and item.get("is_fake") is False]
    result["latestPublishedVersion"] = max(published, key=lambda value: tuple(map(int, value.split("."))), default=None)
    result["versions"] = [item for item in catalog if item.get("version") == version]
    result.update(version=version, componentId=COMPONENT_ID, ownerId=cloud.user["ownerId"])
    # Production FOTA is deferred pending the platform release (operator's
    # platform-team report, 2026-09-06). Observe its Unit as a non-target guard,
    # but do not probe fleet validation or campaign APIs during Test status.
    return result


def reconcile_list_guard(record, observed):
    """Migrate only the proven empty-set list/detail serializer discrepancy."""
    previous = record.get("productionBefore")
    listed = observed.get("productionListObservation")
    current = observed.get("production")
    if previous == current or previous is None:
        return False
    upload = record.get("upload", {})
    if (not observed.get("preProvisioning") or previous != listed or listed.get("members") != []
            or current.get("members") != [] or upload.get("state") != "RESPONDED"
            or (upload.get("response") or {}).get("httpStatus") != 201 or record.get("approve")):
        return False
    old_set, new_set = previous["unitSet"], current["unitSet"]
    changed = {key for key in set(old_set) | set(new_set) if old_set.get(key) != new_set.get(key)}
    if changed != {"update_strategy"} or old_set.get("update_strategy") is not None or not isinstance(new_set.get("update_strategy"), str):
        return False
    record["guardReconciliation"] = dict(reason="EMPTY_SET_LIST_DETAIL_SERIALIZER", previous=previous, canonical=current)
    record["productionBefore"] = current
    return True


def execute(request):
    cloud = Cloud(request)
    if request["action"] == "release-catalog":
        if cloud.call("components/" + COMPONENT_ID + "/")["codename"] != COMPONENT:
            raise CloudFailure("COMPONENT_CLOUD_IDENTITY_MISMATCH")
        versions = [item["version"] for item in cloud.pages("components/" + COMPONENT_ID + "/versions/")
                    if item.get("is_fake") is False and isinstance(item.get("version"), str) and VERSION.fullmatch(item["version"])]
        return dict(versions=versions, latest=max(versions, key=lambda value: tuple(map(int, value.split("."))), default="0.0.0"))
    if request["action"] == "cloud-status":
        if request.get("verificationTest") is True:
            from .component_publication import snapshot as publication_snapshot
            return publication_snapshot(cloud, request)
        return snapshot(cloud, request)
    if request["action"] == "upload":
        return upload(cloud, request)
    if request["action"] == "send":
        cloud.require("units_components_send_requests_create", "units_components_send_requests_list")
        identity = request["vehicles"]["test"]
        if request["unitId"] != identity["unitId"]:
            raise CloudFailure("COMPONENT_SEND_IDENTITY_CHANGED")
        unit_view(cloud, identity)
        component_id = object_id(request["updateComponentId"])
        result = cloud.call("units/" + object_id(identity["unitId"]) + "/components/send-requests/",
                            "POST", {"update_component_ids": [component_id]}, expected=201)
        if (not isinstance(result, list) or len(result) != 1
                or result[0].get("component_type") != COMPONENT
                or result[0].get("update_component") != component_id):
            raise CloudFailure("COMPONENT_SEND_RESPONSE_UNCERTAIN")
        return dict(unitId=identity["unitId"], updateComponentId=component_id,
                    requestId=object_id(result[0]["id"]), requestAccepted=True, httpStatus=201)
    if request["action"] in ("approve", "unapprove"):
        cloud.require("verification_batch_approval")
        path = "verification-batch/" + object_id(request["batchId"]) + "/"
        current = cloud.call(path)
        batch_guard(current, request, cloud.user["ownerId"])
        desired = request["action"] == "approve"
        if (current.get("approval_states") or {}).get("arm64", {}).get("is_approved") is desired:
            return dict(batchId=current["id"], approved=desired, noOp=True)
        cloud.call(path, "PATCH", [{"architecture": "arm64", "is_approved": desired}])
        # The caller's exact post-read confirms the persisted approval. Do not
        # fetch the same batch twice after this PATCH.
        return dict(batchId=current["id"], approved=desired, httpStatus=200)
    raise CloudFailure("COMPONENT_CLOUD_ACTION_INVALID")
