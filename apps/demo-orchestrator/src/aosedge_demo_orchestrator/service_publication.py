# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""SP service publication; no OEM assignment, approval or guest operations."""

from .component_cloud import upload_bundle
from .component_publication import Reads, bundle_view
from .releases import number
from .service_cloud import service_view, version_view, unit_view
from .status import now, object_id
from .unit_cloud import Cloud, CloudFailure


def snapshot(cloud, request, preflight=False):
    cloud.require("services_list", "deployment_bundles_list")
    if cloud.user["role"] != "service provider" or cloud.user["ownerId"] != request["ownerId"]:
        raise CloudFailure("SERVICE_SP_BINDING_CHANGED")
    codename, version = request["team"] + "-health-service", request["version"]
    if request["team"] not in ("brake", "tire"):
        raise CloudFailure("SERVICE_TEAM_INVALID")
    number(version)
    reads = Reads(cloud)
    services = [service_view(row, cloud.user) for row in reads.pages("services/")]
    matches = [row for row in services if row["codename"] == codename]
    if len(matches) > 1 or (request.get("serviceId") and (not matches or matches[0]["id"] != request["serviceId"])):
        raise CloudFailure("SERVICE_CLOUD_BINDING_CHANGED")
    service_id = matches[0]["id"] if matches else None
    versions = []
    if service_id:
        cloud.require("services_service_versions_list")
        versions = [version_view(row) for row in reads.pages("services/" + service_id + "/service-versions/")]
    deployment_id = object_id(request["deploymentId"]) if request.get("deploymentId") else None
    bundles = reads.pages("deployment-bundles/", exact_id=deployment_id)
    if not deployment_id:
        bundles = [row for row in bundles if any(isinstance(item, dict) and item.get("codename") == codename
            and item.get("version") == version for item in row.get("items") or [])]
    bundles = [bundle_view(row) for row in bundles]
    selected_versions = [row for row in versions if row["version"] == version]
    if preflight:
        cloud.require("deployment_bundles_create")
        if bundles or any(number(row["version"]) >= number(version) for row in versions):
            raise CloudFailure("SERVICE_RELEASE_ALREADY_PRESENT_OR_SUPERSEDED")
        # Native SOTA can affect existing assignments after upload. Restrict
        # them to the current owned Test; no guessed OEM/set/Subject mutation.
        if service_id:
            cloud.require("services_units_list")
            units = [unit_view(row) for row in reads.pages("services/" + service_id + "/units/")]
            current = request.get("test")
            if any(not current or row["id"] != current["unitId"] or row["system_uid"] != current["systemUid"] for row in units):
                raise CloudFailure("SERVICE_NON_TEST_ASSIGNMENT_PRESENT")
        return dict(serviceId=service_id, ownerId=cloud.user["ownerId"], recipientScope="CURRENT_TEST_OR_UNASSIGNED")
    result = dict(stage="UNCERTAIN" if not deployment_id else "UNKNOWN", deploymentId=deployment_id,
        serviceId=service_id, version=version, versionId=None, bundleState=None, versionState=None,
        buildInfo=None, observedAt=now(), source="AOS_CLOUD_ONLY")
    if not deployment_id:
        # The API does not expose the uploaded signed digest. A similarly
        # named release is not sufficient proof to adopt a lost upload ID.
        return dict(result, reason="SERVICE_UPLOAD_ID_NOT_RECORDED", candidateBundleIds=[row["id"] for row in bundles])
    if len(bundles) != 1 or bundles[0]["id"] != deployment_id:
        return dict(result, reason="SERVICE_EXACT_BUNDLE_NOT_OBSERVED")
    bundle = bundles[0]
    result.update(bundleState=bundle["state"], buildInfo=bundle["build_info"])
    state = str(bundle["state"] or "").lower()
    if state == "error" or any(str(row.get("container_state") or "").lower() in ("error", "failed") for row in selected_versions):
        return dict(result, stage="ERROR", reason="SERVICE_CLOUD_PROCESSING_ERROR")
    if state in ("uploaded", "pending", "processing", "in progress"):
        return dict(result, stage="PROCESSING")
    if state != "done":
        return dict(result, reason="SERVICE_BUNDLE_STATE_UNKNOWN")
    items = bundle.get("items")
    if (not isinstance(items, list) or len(items) != 1 or items[0].get("type") != "service"
            or items[0].get("codename") != codename or items[0].get("version") != version):
        return dict(result, stage="ERROR", reason="SERVICE_BUNDLE_CONTENT_MISMATCH")
    if len(selected_versions) > 1:
        return dict(result, stage="ERROR", reason="SERVICE_CATALOG_VERSION_AMBIGUOUS")
    if not selected_versions:
        return dict(result, stage="PROCESSING", reason="SERVICE_VERSION_NOT_YET_OBSERVED")
    current = selected_versions[0]
    result.update(versionId=current["id"], versionState=current.get("container_state"))
    if str(current.get("container_state") or "").lower() == "ready":
        return dict(result, stage="READY")
    return dict(result, stage="PROCESSING" if str(current.get("container_state") or "").lower() in
                ("pending", "processing", "building", "uploaded") else "UNKNOWN", reason="SERVICE_VERSION_NOT_READY")


def execute(request):
    if request["action"] == "service-cloud-status":
        return snapshot(Cloud(request, expected_role="service provider"), request)
    if request["action"] != "service-upload":
        raise CloudFailure("SERVICE_PUBLICATION_ACTION_INVALID")
    # A single authenticated worker owns preflight and exactly one POST.
    try:
        from .component_worker import verify_service
        cloud = Cloud(request, expected_role="service provider")
        before = snapshot(cloud, request, preflight=True)
        verify_service(request)
    except CloudFailure as error:
        return dict(stage="BLOCKED", attempted=False, reason=str(error))
    except Exception:
        # The parent retains an ATTEMPTING intent if this worker disappears.
        # Only an explicit response can prove that no POST was attempted.
        return dict(stage="BLOCKED", attempted=False, reason="SERVICE_UPLOAD_PREFLIGHT_FAILED")
    try:
        from pathlib import Path
        response = upload_bundle(cloud, Path(request["bundle"]), prefix="SERVICE")
    except Exception:
        return dict(stage="UNCERTAIN", attempted=True, reason="SERVICE_UPLOAD_RESPONSE_UNCERTAIN", serviceId=before["serviceId"])
    return dict(response, stage="ERROR" if str(response.get("state") or "").lower() == "error" else "ACCEPTED",
        attempted=True, serviceId=before["serviceId"], requestAccepted=True)
