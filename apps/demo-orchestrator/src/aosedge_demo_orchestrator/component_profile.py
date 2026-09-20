# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Installed VDP description, not runtime or telemetry readiness.

Cloud owns installation. An exact publication receipt binds its version UUID
to an inspected local artifact. No guest access, new store or network call.
"""

import re

from .cloud_connection import cloud_binding, selected_domain
from .environment import EnvironmentError


class InstalledProfileResolver:
    def __init__(self, components_factory):
        self.components_factory = components_factory
        self.inspection = None

    def resolve(self, journal, inventory, row, publications):
        installed = row.get("installed_component") or {}
        version, version_id = installed.get("version"), installed.get("id")
        result = dict(state="UNKNOWN", profile=None, releaseVersion=version,
                      cloudVersionId=version_id, source="CLOUD_INSTALLATION_AND_PACKAGE",
                      reason="INSTALLED_PROFILE_NOT_CONFIRMED")
        if not version_id or not isinstance(version, str) or not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version):
            return result
        identity = journal.get("vehicles", {}).get("test", {})
        unit = (inventory.get("unit") or {}).get("value") or {}
        record = journal.get("componentOperations", {}).get(version) or {}
        owner = cloud_binding(journal).get("ownerId")
        if (not owner or record.get("ownerId") != owner or unit.get("oem") != owner
                or record.get("cloudDomain") != selected_domain(journal)
                or not identity.get("unitId") or identity["unitId"] != inventory.get("unitId")
                or not identity.get("systemUid") or identity["systemUid"] != inventory.get("systemUid")):
            result["reason"] = "INSTALLED_PROFILE_CONTEXT_NOT_CONFIRMED"
            return result
        publication = publications.get((version, record.get("deploymentId"))) or {}
        upload = record.get("upload") or {}
        receipt = upload.get("response") or {}
        if (publication.get("stage") != "READY" or publication.get("versionId") != version_id
                or not record.get("deploymentId") or publication.get("deploymentId") != record["deploymentId"]
                or upload.get("state") != "RESPONDED" or receipt.get("httpStatus") != 201
                or receipt.get("deploymentId") != record["deploymentId"]):
            result["reason"] = "INSTALLED_PROFILE_PUBLICATION_NOT_CONFIRMED"
            return result
        prepared = record.get("prepare") or {}
        expected_sha = record.get("preparedSha256")
        signed = record.get("signed") or {}
        if (prepared.get("state") != "COMPLETED" or prepared.get("contentProfile") not in ("v1", "v2", "v3")
                or not isinstance(expected_sha, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_sha)
                or prepared.get("sha256") != expected_sha or signed.get("state") != "COMPLETED"
                or signed.get("cloudDomain") != selected_domain(journal)
                or not record.get("sha256") or signed.get("sha256") != record["sha256"]):
            result["reason"] = "INSTALLED_PROFILE_ARTIFACT_NOT_CONFIRMED"
            return result
        try:
            components = self.components_factory()
            path = components._bundle(version)
            stamp = path.stat()
            key = (str(path), stamp.st_dev, stamp.st_ino, stamp.st_size, stamp.st_mtime_ns, stamp.st_ctime_ns)
            if self.inspection is None or self.inspection[0] != key:
                inspected = components.inspect(version)
                after = path.stat()
                if key != (str(path), after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns):
                    raise EnvironmentError("COMPONENT_CHANGED_DURING_INSPECTION")
                self.inspection = (key, inspected)
            inspected = self.inspection[1]
            if (inspected.get("problems") or inspected.get("version") != version
                    or inspected.get("unsignedBundleSha256") != expected_sha
                    or inspected.get("contentProfile") != prepared["contentProfile"]):
                raise EnvironmentError("COMPONENT_PROFILE_BINDING_INVALID")
        except (EnvironmentError, OSError, ValueError, KeyError, TypeError):
            result["reason"] = "INSTALLED_PROFILE_ARTIFACT_NOT_CONFIRMED"
            return result
        current = all((inventory.get(section) or {}).get("state") == "CURRENT" for section in ("unit", "components"))
        result.update(state="CURRENT" if current else "STALE", profile=inspected["contentProfile"],
                      reason=None if current else "LAST_KNOWN_CLOUD_INSTALLATION")
        return result
