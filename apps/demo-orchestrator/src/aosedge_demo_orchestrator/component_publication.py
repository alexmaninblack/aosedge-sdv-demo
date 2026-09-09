# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Verification-Test FOTA publication, using documented v11 collection reads.

This is a domain adapter, not a second upload route. The existing official
deployment-bundle uploader remains the only mutation boundary.
"""

from urllib.parse import urlencode

from .components import COMPONENT, VERSION
from .component_cloud import COMPONENT_ID, unit_view
from .cloud_observation import pick
from .status import now, object_id
from .unit_cloud import CloudFailure


class Reads:
    """Bound both collection coverage and the whole publication observation."""

    def __init__(self, cloud):
        self.cloud, self.remaining = cloud, 24

    def call(self, path):
        if self.remaining <= 0:
            raise CloudFailure("COMPONENT_CLOUD_READ_BUDGET_EXCEEDED")
        self.remaining -= 1
        return self.cloud.call(path)

    def pages(self, path, exact_id=None):
        values, seen = [], set()
        for offset in range(0, 800, 100):
            value = self.call(path + ("&" if "?" in path else "?") + urlencode(dict(limit=100, offset=offset)))
            if (not isinstance(value, dict) or not isinstance(value.get("items"), list)
                    or type(value.get("offset")) is not int or value["offset"] != offset
                    or type(value.get("total")) is not int or value["total"] < 0
                    or len(value["items"]) > 100):
                raise CloudFailure("COMPONENT_CLOUD_COLLECTION_INVALID")
            rows = value["items"]
            for row in rows:
                if not isinstance(row, dict) or not row.get("id") or row["id"] in seen:
                    raise CloudFailure("COMPONENT_CLOUD_COLLECTION_AMBIGUOUS")
                seen.add(row["id"])
            values.extend(rows)
            # The known upload response ID is an API primary key, not a search
            # by a guessed version. Stop when that exact record is observed.
            if exact_id and exact_id in seen:
                return [row for row in rows if row["id"] == exact_id]
            if offset + len(rows) == value["total"]:
                return [] if exact_id else values
            if not rows or offset + len(rows) > value["total"] or len(rows) != 100:
                raise CloudFailure("COMPONENT_CLOUD_COLLECTION_INCOMPLETE")
        raise CloudFailure("COMPONENT_CLOUD_COLLECTION_LIMIT")


def bundle_view(value):
    result = pick(value, ("id", "state", "build_info"), ("file_size",))
    entries = value.get("items")
    if entries is not None and (not isinstance(entries, list) or any(not isinstance(row, dict) for row in entries)):
        raise CloudFailure("COMPONENT_BUNDLE_ITEMS_SCHEMA_INVALID")
    result["items"] = None if entries is None else [
        pick(row, ("id", "type", "codename", "version"))
        for row in entries]
    return result


def publication(version, deployment_id, bundles, versions):
    """Do not conflate HTTP acceptance, bundle parsing and catalog readiness."""
    value = dict(stage="NOT_PUBLISHED", deploymentId=deployment_id, bundleState=None,
                 versionState=None, versionId=None, buildInfo=None, observedAt=now())
    if not deployment_id:
        if bundles or versions:
            value.update(stage="UNKNOWN", reason="COMPONENT_PUBLICATION_NOT_OWNED")
        return value
    if len(bundles) != 1 or bundles[0].get("id") != deployment_id:
        return dict(value, stage="UNKNOWN", reason="COMPONENT_EXACT_BUNDLE_NOT_OBSERVED")
    bundle = bundles[0]
    value.update(bundleState=bundle.get("state"), buildInfo=bundle.get("build_info"))
    if len(versions) == 1:
        value.update(versionState=versions[0].get("state"), versionId=versions[0].get("id"))
    bundle_state = str(bundle.get("state") or "").lower()
    if bundle_state == "error" or any(str(row.get("state") or "").lower() == "error" for row in versions):
        return dict(value, stage="ERROR", reason="COMPONENT_CLOUD_PROCESSING_ERROR")
    if bundle_state in ("uploaded", "processing", "in progress", "pending"):
        return dict(value, stage="PROCESSING")
    if bundle_state != "done":
        return dict(value, stage="UNKNOWN", reason="COMPONENT_BUNDLE_STATE_UNKNOWN")
    items = bundle.get("items")
    if (not isinstance(items, list) or len(items) != 1 or items[0].get("type") != "component"
            or items[0].get("codename") != COMPONENT or items[0].get("version") != version):
        return dict(value, stage="ERROR", reason="COMPONENT_BUNDLE_CONTENT_MISMATCH")
    if len(versions) > 1:
        return dict(value, stage="ERROR", reason="COMPONENT_CATALOG_VERSION_AMBIGUOUS")
    if not versions:
        return dict(value, stage="PROCESSING", reason="COMPONENT_CATALOG_VERSION_NOT_YET_OBSERVED")
    if versions[0].get("state") == "Ready" and versions[0].get("is_fake") is False:
        return dict(value, stage="READY")
    return dict(value, stage="UNKNOWN", reason="COMPONENT_CATALOG_VERSION_NOT_READY")


def recipients(reads, request):
    """All verification members must be exactly the currently owned Test.

    Ordinary Production sets/Units are not recipients of this path. A second
    verification set is harmless only when it contains that same Test; any
    other member blocks publication, without assuming model compatibility.
    """
    sets = reads.pages("unit-sets/?is_validation_set=true")
    current = request.get("vehicles", {}).get("test")
    expected = current.get("unitId") if current else None
    memberships = []
    if len(sets) > 16:
        raise CloudFailure("COMPONENT_VERIFICATION_SET_LIMIT")
    for item in sets:
        if item.get("is_validation_set") is not True:
            raise CloudFailure("COMPONENT_VERIFICATION_SET_FILTER_NOT_PROVEN")
        set_id = object_id(item["id"])
        members = reads.pages("unit-sets/" + set_id + "/units/")
        for member in members:
            if (not expected or member.get("id") != expected
                    or member.get("system_uid") != current.get("systemUid")):
                raise CloudFailure("COMPONENT_UNRELATED_VERIFICATION_RECIPIENT")
        if members:
            memberships.append(set_id)
    if expected and current["unitSetId"] not in memberships:
        raise CloudFailure("COMPONENT_TEST_VERIFICATION_MEMBERSHIP_NOT_PROVEN")
    return dict(complete=True, verificationSetCount=len(sets),
                recipientUnitIds=[expected] if expected else [], verificationMemberships=memberships)


def snapshot(cloud, request):
    cloud.require("deployment_bundles_list")
    reads = Reads(cloud)
    component = reads.call("components/" + COMPONENT_ID + "/")
    if component.get("codename") != COMPONENT or component.get("oem_id") != cloud.user["ownerId"]:
        raise CloudFailure("COMPONENT_CLOUD_IDENTITY_OR_OWNER_MISMATCH")
    version = request["version"]
    if not isinstance(version, str) or not VERSION.fullmatch(version):
        raise CloudFailure("COMPONENT_VERSION_INVALID")
    all_versions = reads.pages("components/" + COMPONENT_ID + "/versions/")
    versions = [pick(row, ("id", "version", "state"), ("file_size",), ("is_fake",))
                for row in all_versions if row.get("version") == version]
    deployment_id = object_id(request["deploymentId"]) if request.get("deploymentId") else None
    bundles = reads.pages("deployment-bundles/", deployment_id)
    prior = request.get("previousPublication")
    previous = None
    if prior:
        if deployment_id:
            raise CloudFailure("COMPONENT_PREVIOUS_PUBLICATION_SCOPE_INVALID")
        prior_id = object_id(prior["deploymentId"])
        previous = publication(prior["version"], prior_id,
            [bundle_view(row) for row in bundles if row["id"] == prior_id],
            [row for row in all_versions if row.get("version") == prior["version"]])
    if not deployment_id:
        bundles = [row for row in bundles if any(isinstance(item, dict) and item.get("codename") == COMPONENT
            and item.get("version") == version for item in row.get("items") or [])]
    result = dict(source="AOS_CLOUD_ONLY", ownerId=cloud.user["ownerId"], versions=versions,
                  deploymentBundles=[bundle_view(row) for row in bundles])
    result["publication"] = publication(version, deployment_id, result["deploymentBundles"], versions)
    if previous:
        result["previousPublication"] = previous
    released = [row["version"] for row in all_versions if row.get("is_fake") is False
                and isinstance(row.get("version"), str) and VERSION.fullmatch(row["version"])]
    result["latestPublishedVersion"] = max(released, key=lambda item: tuple(map(int, item.split("."))), default=None)
    if request.get("purpose") == "upload":
        cloud.require("unit_sets_list", "unit_sets_units_list")
        result["recipientCoverage"] = recipients(reads, request)
    identity = request.get("vehicles", {}).get("test")
    if identity:
        cloud.require("units_read")
        result["test"] = unit_view(reads, identity, strict=True)
        if request.get("purpose") == "upload" and (result["test"].get("status") != "provisioned"
                or result["test"].get("components") is None):
            raise CloudFailure("COMPONENT_CURRENT_TEST_UPDATE_STATE_NOT_PROVEN")
    result["problems"] = [result["publication"]["reason"]] if result["publication"]["stage"] in ("ERROR", "UNKNOWN") else []
    if identity and result["test"].get("components") is None:
        result["problems"].append("COMPONENT_CURRENT_TEST_UPDATE_STATE_NOT_REPORTED")
    return result
