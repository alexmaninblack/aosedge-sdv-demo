# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Private, bounded Presenter identity projection; never a lifecycle authority.

Exact joins/validation use the original server-side observations. References
are process-scoped fingerprints, not credentials or authorization. No mapping
or salt is written to disk. Unknown/stale selectors never become native IDs.
"""

import hashlib
import hmac
import re
import secrets
import threading


UUID_TEXT = re.compile(r"(?i)(?<![0-9a-f])[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}(?![0-9a-f])")
REFERENCE = re.compile(r"ref_[0-9a-f]{32}\Z")
IDENTITY_KEYS = frozenset((
    "unitid", "nodeid", "systemuid", "unitsystemuid", "localvmid", "runid",
    "serviceid", "serviceproviderid", "subjectid", "subject", "instanceid",
    "ownerid", "deploymentid", "versionid",
))


class BrowserProjection:
    def __init__(self, limit=16384):
        self._key = secrets.token_bytes(32)
        self._references = {}
        self._identities = {}
        self._lock = threading.RLock()
        self._limit = limit

    def _reference(self, identity):
        if identity in self._identities:
            return self._identities[identity]
        if len(self._identities) >= self._limit:
            raise ValueError("BROWSER_REFERENCE_CAPACITY")
        reference = "ref_" + hmac.new(self._key, identity.encode(), hashlib.sha256).hexdigest()[:32]
        if reference in self._references:
            raise ValueError("BROWSER_REFERENCE_COLLISION")
        self._identities[identity] = reference
        self._references[reference] = identity
        return reference

    @staticmethod
    def _public_protocol_field(path, parent):
        # These are explicitly public UI generation/request IDs, not Cloud
        # objects. Preserve at-most-once request reconciliation and idle stop.
        return (path in (("sessionId",), ("active",))
                or path[:1] == ("recordedRequestIds",)
                or path[-1:] == ("id",) and isinstance(parent, dict)
                and "action" in parent and "startedAt" in parent)

    def _collect(self, value, path=(), parent=None, protocol=False):
        if protocol and self._public_protocol_field(path, parent):
            return
        if isinstance(value, dict):
            for key, child in value.items():
                self._collect(key)
                self._collect(child, path + (key,), value, protocol)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                self._collect(child, path + (index,), value, protocol)
        elif isinstance(value, str):
            key = re.sub(r"[_-]", "", str(path[-1])).lower() if path else ""
            if key in IDENTITY_KEYS and value:
                self._reference(value)
            for match in UUID_TEXT.finditer(value):
                self._reference(match.group())

    def project(self, value, private_context=None, protocol=False):
        with self._lock:
            # Collect before rendering, including identities inside object
            # keys/composite binding keys. A later field must not leak earlier.
            self._collect(private_context)
            self._collect(value, protocol=protocol)
            identities = sorted(self._identities, key=len, reverse=True)
            pattern = re.compile("|".join(re.escape(item) for item in identities)) if identities else None

            def render(item, path=(), parent=None):
                if protocol and self._public_protocol_field(path, parent):
                    return item
                if isinstance(item, dict):
                    # Schema property names are not identity values. Dynamic
                    # service-detail keys and UUID keys are private selectors.
                    def public_key(key):
                        if path[-1:] == ("serviceDetails",) and key in self._identities:
                            return self._identities[key]
                        return UUID_TEXT.sub(lambda match: self._identities[match.group()], key)
                    return {public_key(key): render(child, path + (key,), item) for key, child in item.items()}
                if isinstance(item, list):
                    return [render(child, path + (index,), item) for index, child in enumerate(item)]
                if isinstance(item, str) and pattern:
                    key = re.sub(r"[_-]", "", str(path[-1])).lower() if path else ""
                    if key in IDENTITY_KEYS or key == "id" and item in self._identities:
                        return self._identities.get(item, item)
                    if item in self._identities:
                        return self._identities[item]
                    if (key == "bindingkey" or key.endswith(("message", "reason", "detail", "title", "name", "description"))
                            or "progress" in path):
                        return pattern.sub(lambda match: self._identities[match.group()], item)
                    return UUID_TEXT.sub(lambda match: self._identities[match.group()], item)
                return item

            return render(value)

    def resolve(self, reference):
        with self._lock:
            if not isinstance(reference, str) or not REFERENCE.fullmatch(reference) or reference not in self._references:
                raise ValueError("BROWSER_REFERENCE_UNKNOWN")
            return self._references[reference]

    def operation(self, payload):
        # Only this fixed native selector crosses back. Other operation input
        # remains closed/validated by operation_plan and native ownership guards.
        if isinstance(payload, dict) and payload.get("action") == "service-assign":
            return dict(payload, serviceId=self.resolve(payload.get("serviceId")))
        return payload
