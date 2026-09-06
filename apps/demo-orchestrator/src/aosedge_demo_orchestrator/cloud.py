# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Allowlisted Cloud GETs using the already installed Aos credential runtime."""

import json
import os
import re
import signal
import socket
import ssl
import stat
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from aosedge_demo_orchestrator.status import observation, object_id, safe_word, skipped


def local_profile(name, profile):
    try:
        path = profile["credential"]
        present = path.is_file() and not path.is_symlink()
        usable_mode = present and path.stat().st_mode & 0o077 == 0
        credential = observation("LOCAL_CREDENTIAL:" + name, {"present": present, "privateMode": bool(usable_mode)})
    except OSError:
        credential = observation("LOCAL_CREDENTIAL:" + name, reason="CREDENTIAL_STAT_FAILED")
    return {"credential": credential, "access": skipped("AOSCLOUD:" + name, "NOT_REQUESTED"), "units": {}}


def cloud_status(name, profile, vehicles, interpreter, timeout):
    result = local_profile(name, profile)
    source = "AOSCLOUD:" + name
    local = result["credential"].get("value") or {}
    if not local.get("present") or not local.get("privateMode"):
        result["access"] = observation(source, reason="CREDENTIAL_MISSING_OR_UNSAFE")
        return result
    if not interpreter.is_file():
        result["access"] = observation(source, reason="AOS_PYTHON_UNAVAILABLE")
        return result
    # Only explicit OEM delivery reads Unit state. Publication/SP profiles do not
    # acquire delivery authority just because their certificate can do a GET.
    targets = {}
    if name == "oem-delivery":
        targets = {role: {k: item[k] for k in ("unitId", "unitSetId", "systemUid", "cloudLifecycle") if k in item}
                   for role, item in vehicles.items() if item is not None}
    request = {"name": name, "credential": str(profile["credential"]),
               "expectedRole": profile["expectedRole"], "expectedOwnerId": profile.get("expectedOwnerId"),
               "vehicles": targets, "timeout": timeout}
    process = None
    try:
        process = subprocess.Popen(
            [str(interpreter), "-I", "-B", str(Path(__file__).resolve())],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, env={"PATH": os.defpath},
        )
        try:
            output, _ = process.communicate(json.dumps(request), timeout=timeout + 0.5)
        except subprocess.TimeoutExpired:
            # Give the worker's SIGTERM handler time to close credential contexts.
            process.terminate()
            try:
                process.communicate(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.communicate()
            result["access"] = observation(source, reason="CLOUD_TIMEOUT", transport="SOURCE_UNAVAILABLE")
            return result
        if process.returncode or len(output) > 131072:
            raise ValueError("Cloud reader failed")
        payload = json.loads(output)
        if not isinstance(payload, dict) or set(payload) != {"access", "units", "certificate"}:
            raise ValueError("Cloud reader shape")
        result.update(payload)
        return result
    except (OSError, ValueError):
        result["access"] = observation(source, reason="CLOUD_READER_UNAVAILABLE", transport="SOURCE_UNAVAILABLE")
        return result


def project_user(payload, expected_role, expected_owner=None):
    if not isinstance(payload, dict):
        raise ValueError("User shape")
    user_id = object_id(payload["id"])
    role = safe_word(payload["role"])
    owner_key = "oem" if role == "oem" else "service_provider" if role == "service provider" else None
    owner_payload = payload.get(owner_key) if owner_key else None
    owner_id = object_id(owner_payload["id"]) if isinstance(owner_payload, dict) and owner_payload.get("id") else None
    permissions = payload.get("effective_permissions")
    if permissions is not None:
        if not isinstance(permissions, list) or len(permissions) > 4096:
            raise ValueError("Permission shape")
        permissions = [safe_word(p) for p in permissions]
    # Never return the raw user object: it includes a reusable token.
    return {"userId": user_id, "role": role, "expectedRole": expected_role, "roleMatches": role == expected_role,
            "ownerId": owner_id, "expectedOwnerId": expected_owner,
            "ownerMatches": owner_id == expected_owner if expected_owner else None,
            "effectivePermissions": permissions, "mutationAuthority": "NOT_EVALUATED"}


def project_unit(payload, configured):
    if not isinstance(payload, dict) or object_id(payload["id"]) != configured["unitId"]:
        raise ValueError("Unit identity mismatch")
    sets = payload.get("unit_sets")
    if sets is not None and not isinstance(sets, list):
        raise ValueError("Unit Set shape")
    memberships = None if sets is None else [{"id": object_id(s["id"])} for s in sets]
    expected_set = configured.get("unitSetId")
    return {"id": payload["id"], "systemUid": safe_word(payload["system_uid"]),
            "status": safe_word(payload["status"]), "onlineStatus": safe_word(payload["online_status"]),
            "fleetId": object_id(payload["fleet"]) if payload.get("fleet") else None,
            "unitSets": memberships, "expectedUnitSetId": expected_set,
            "expectedMembershipPresent": any(s["id"] == expected_set for s in memberships)
            if expected_set and memberships is not None else None}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def get_json(opener, url, deadline, source):
    try:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError()
        with opener.open(urllib.request.Request(url, method="GET", headers={"Accept": "application/json"}),
                         timeout=remaining) as response:
            data = response.read(524289)
        if len(data) > 524288:
            raise ValueError("Response too large")
        return json.loads(data), None
    except urllib.error.HTTPError as error:
        code = error.code
        transport = {401: "UNAUTHENTICATED", 403: "FORBIDDEN", 404: "NOT_FOUND_OR_INACCESSIBLE",
                     400: "REJECTED", 422: "SCHEMA_INVALID"}.get(code, "SOURCE_UNAVAILABLE")
        return None, observation(source, reason="HTTP_" + str(code), transport=transport)
    except (TimeoutError, socket.timeout):
        return None, observation(source, reason="CLOUD_TIMEOUT", transport="SOURCE_UNAVAILABLE")
    except (OSError, urllib.error.URLError) as error:
        reason = "TLS_FAILED" if isinstance(getattr(error, "reason", error), ssl.SSLError) else "CLOUD_UNREACHABLE"
        return None, observation(source, reason=reason, transport="SOURCE_UNAVAILABLE")
    except (ValueError, UnicodeError):
        return None, observation(source, reason="RESPONSE_MALFORMED", transport="MALFORMED")


def read_cloud(request):
    source = "AOSCLOUD:" + request["name"]
    result = {"access": observation(source, reason="CREDENTIAL_UNAVAILABLE"), "units": {},
              "certificate": observation("LOCAL_CERTIFICATE", reason="CERTIFICATE_NOT_READ")}
    deadline = time.monotonic() + request["timeout"]
    try:
        from importlib import resources
        from aos_prov.utils.user_credentials import UserCredentials
        from cryptography.hazmat.primitives.serialization.pkcs12 import load_key_and_certificates

        _, cert, _ = load_key_and_certificates(Path(request["credential"]).read_bytes(), None)
        from datetime import datetime, timezone
        expires = getattr(cert, "not_valid_after_utc", None)
        starts = getattr(cert, "not_valid_before_utc", None)
        if expires is None:
            expires = cert.not_valid_after.replace(tzinfo=timezone.utc)
            starts = cert.not_valid_before.replace(tzinfo=timezone.utc)
        result["certificate"] = observation("LOCAL_CERTIFICATE", {
            "validFrom": starts.isoformat(), "validUntil": expires.isoformat(),
            "timeValid": starts <= datetime.now(timezone.utc) <= expires,
        })
        credentials = UserCredentials(pkcs12=request["credential"])
        hostname = credentials.cloud_url
        if not isinstance(hostname, str) or not re.fullmatch(r"(?:[a-z0-9-]+\.)*aoscloud\.io", hostname):
            raise ValueError("Unconfigured Cloud trust domain")
        ca = resources.files("aos_prov") / "files/1rootCA.crt"
        with resources.as_file(ca) as ca_file:
            context = ssl.create_default_context(cafile=str(ca_file))
        with credentials.user_credentials as material:
            context.load_cert_chain(material.cert_file_name, material.key_file_name)
        # Temporary SDK key/certificate files have been deleted before any network wait.
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect(),
                                             urllib.request.HTTPSHandler(context=context))
        base = "https://" + hostname + ":10000/api/v11/"
    except ImportError:
        result["access"] = observation(source, reason="AOS_DEPENDENCIES_UNAVAILABLE")
        return result
    except (OSError, ValueError, IndexError, AttributeError):
        result["access"] = observation(source, reason="CREDENTIAL_UNUSABLE")
        return result
    payload, failure = get_json(opener, base + "users/me/", deadline, source)
    if failure:
        result["access"] = failure
        return result
    try:
        user = project_user(payload, request["expectedRole"], request.get("expectedOwnerId"))
        mismatch = not user["roleMatches"] or user["ownerMatches"] is False
        missing = user["ownerId"] is None or user["effectivePermissions"] is None
        reason = "ROLE_OR_OWNER_MISMATCH" if mismatch else "OWNER_OR_PERMISSIONS_UNOBSERVED" if missing else None
        result["access"] = observation(source, user, reason=reason)
        if mismatch:
            return result
    except (ValueError, KeyError, TypeError):
        result["access"] = observation(source, reason="USER_RESPONSE_MALFORMED", transport="MALFORMED")
        return result
    for role, configured in request["vehicles"].items():
        unit_source = source + ":UNIT:" + role
        if not configured.get("unitId"):
            result["units"][role] = skipped(unit_source, "UNIT_ID_NOT_CONFIGURED")
            continue
        payload, failure = get_json(opener, base + "units/" + configured["unitId"] + "/", deadline, unit_source)
        if failure:
            if configured.get("cloudLifecycle") == "DELETED" and failure.get("reason") == "HTTP_404":
                inventory, inventory_failure = get_json(opener, base + "units/?" + urllib.parse.urlencode(
                    {"system_uid": configured["systemUid"]}), deadline, unit_source)
                if not inventory_failure and isinstance(inventory, dict) and inventory.get("total") == 0 and inventory.get("items") == []:
                    result["units"][role] = observation(unit_source, {
                        "id": configured["unitId"], "systemUid": configured["systemUid"], "status": "deleted",
                        "onlineStatus": "NOT_APPLICABLE", "fleetId": None, "unitSets": [],
                        "expectedUnitSetId": configured.get("unitSetId"), "expectedMembershipPresent": None,
                        "absenceConfirmed": True})
                    continue
            result["units"][role] = failure
            continue
        try:
            unit = project_unit(payload, configured)
            result["units"][role] = observation(unit_source, unit,
                reason="UNIT_SET_MISMATCH" if unit["expectedMembershipPresent"] is False else None)
        except (ValueError, KeyError, TypeError):
            result["units"][role] = observation(unit_source, reason="UNIT_RESPONSE_MALFORMED", transport="MALFORMED")
    return result


def worker_main():
    def interrupted(signum, frame):
        raise TimeoutError()
    signal.signal(signal.SIGTERM, interrupted)
    try:
        request = json.loads(sys.stdin.read(65537))
        result = read_cloud(request)
    except Exception:
        result = {"access": observation("AOSCLOUD", reason="CLOUD_READ_FAILED", transport="SOURCE_UNAVAILABLE"),
                  "units": {}, "certificate": skipped("LOCAL_CERTIFICATE", "UNAVAILABLE")}
    print(json.dumps(result, separators=(",", ":")))


if __name__ == "__main__":
    worker_main()
