# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Service inspection shared by CLI/API; credentials stay in SDK workers."""

import json
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .environment import EnvironmentError
from .status import load_configuration, object_id, now
from .service_cloud import observed


class ServiceCatalog:
    def __init__(self, environment):
        self.environment = environment

    def release_versions(self, team, profile="service-provider"):
        """One SP read session; no Unit scan, assignment or OCI manifest lookup."""
        from .releases import number
        if team not in ("brake", "tire"):
            raise EnvironmentError("SERVICE_TEAM_INVALID")
        config = load_configuration(self.environment.root)
        entry = config["cloudProfiles"].get(profile)
        if not entry or entry["expectedRole"] != "service provider":
            raise EnvironmentError("SERVICE_PUBLICATION_REQUIRES_CONFIGURED_SP")
        codename = team + "-health-service"
        result = self._read(profile, entry, config, "release-catalog", codename)
        if any(result.get(key, {}).get("state") != "CURRENT" for key in ("authority", "services", "versions")):
            raise EnvironmentError("SERVICE_RELEASE_CATALOG_UNAVAILABLE")
        authority = result["authority"]["value"]
        if authority.get("role") != "service provider":
            raise EnvironmentError("SERVICE_PUBLICATION_REQUIRES_SP")
        for key in ("services", "versions"):
            value = result[key]["value"]
            if value.get("coverage", {}).get("complete") is not True or value["coverage"]["returned"] != len(value["items"]):
                raise EnvironmentError("SERVICE_RELEASE_CATALOG_INCOMPLETE")
        matches = result["services"]["value"]["items"]
        owner = object_id(authority["ownerId"])
        if len(matches) > 1 or any(row.get("codename") != codename or row.get("serviceProviderId") != owner for row in matches):
            raise EnvironmentError("SERVICE_RELEASE_BINDING_INVALID")
        versions = [row["version"] for row in result["versions"]["value"]["items"]]
        if not matches and versions:
            raise EnvironmentError("SERVICE_RELEASE_BINDING_INVALID")
        # Failed/pending versions also consume numbers. Unknown version syntax
        # is not silently skipped and never interpreted as an empty catalog.
        for version in versions:
            number(version)
        return dict(serviceId=object_id(matches[0]["id"]) if matches else None,
            ownerId=owner, codename=codename, versions=versions, cloudProfile=profile)

    def _read(self, name, profile, config, action, service_id, version_id=None):
        credential = profile["credential"]
        try:
            usable = not credential.is_symlink() and credential.is_file() and credential.stat().st_mode & 0o077 == 0
        except OSError:
            usable = False
        if not usable:
            return dict(authority=observed(None, reason="SERVICE_CREDENTIAL_MISSING_OR_UNSAFE"))
        request = dict(action=action, serviceId=service_id, expectedRole=profile["expectedRole"],
            ownerId=profile.get("expectedOwnerId"), credential=str(credential))
        if version_id is not None:
            request["versionId"] = version_id
        try:
            response = subprocess.run([str(config["cloudPython"]), "-I", "-B",
                str(Path(__file__).with_name("service_cloud.py"))], input=json.dumps(request),
                text=True, capture_output=True, timeout=60, env={"PATH": os.defpath})
            if response.returncode or len(response.stdout) > 262144:
                raise ValueError("Service observation unavailable")
            value = json.loads(response.stdout)
            if (not isinstance(value, dict) or "authority" not in value
                    or set(value) - {"authority", "services", "providers", "service", "versions", "version", "units"}):
                raise ValueError("Service observation shape")
            return value
        except (OSError, ValueError, subprocess.TimeoutExpired):
            return dict(authority=observed(None, reason="SERVICE_CLOUD_READER_UNAVAILABLE"))

    def execute(self, action, service_id=None, profile=None, version_id=None):
        if (action not in ("list", "status", "inspect") or (action == "list" and service_id is not None)
                or (action != "inspect" and version_id is not None)):
            raise EnvironmentError("SERVICE_READ_ACTION_INVALID")
        if action in ("status", "inspect"):
            try:
                service_id = object_id(service_id)
            except ValueError:
                raise EnvironmentError("SERVICE_ID_FROM_CATALOG_REQUIRED") from None
        if action == "inspect":
            try:
                version_id = object_id(version_id)
            except (ValueError, TypeError):
                raise EnvironmentError("SERVICE_VERSION_ID_FROM_CATALOG_REQUIRED") from None
        config = load_configuration(self.environment.root)
        profiles = config["cloudProfiles"]
        if profile is not None:
            if profile not in profiles:
                raise EnvironmentError("SERVICE_CLOUD_PROFILE_NOT_CONFIGURED")
            profiles = {profile: profiles[profile]}
        result = dict(schemaVersion=1, source="AOS_CLOUD_ONLY", action=action, serviceId=service_id,
                      readCompletedAt=None, profiles={}, problems=[])
        with ThreadPoolExecutor(max_workers=4) as pool:
            pending = {name: pool.submit(self._read, name, entry, config, action, service_id, version_id)
                       for name, entry in profiles.items()}
            for name, future in pending.items():
                result["profiles"][name] = future.result()
                for section, value in result["profiles"][name].items():
                    if value.get("state") not in ("CURRENT", "NOT_APPLICABLE"):
                        result["problems"].append(dict(profile=name, section=section, reason=value.get("reason")))
        if not profiles:
            result["problems"].append(dict(reason="SERVICE_CLOUD_PROFILES_NOT_CONFIGURED"))
        result["readCompletedAt"] = now()
        return result
