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
