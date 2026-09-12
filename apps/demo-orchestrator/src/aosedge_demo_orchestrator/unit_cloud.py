# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Private Aos runtime worker. Only fixed operations and sanitized results cross IPC."""

import json
import os
import re
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    # Workers are launched by filename. Share the canonical module identity
    # with adapters so CloudFailure is not defined twice (__main__ vs import).
    sys.modules["aosedge_demo_orchestrator.unit_cloud"] = sys.modules[__name__]

from aosedge_demo_orchestrator.cloud import NoRedirect, project_user
from aosedge_demo_orchestrator.status import object_id, safe_word


class CloudFailure(Exception):
    pass


class Cloud:
    def __init__(self, request, expected_role="oem"):
        from importlib import resources
        from aos_prov.utils.user_credentials import UserCredentials

        credentials = UserCredentials(pkcs12=request["credential"])
        host = credentials.cloud_url
        if not re.fullmatch(r"(?:[a-z0-9-]+\.)*aoscloud\.io", host):
            raise CloudFailure("CLOUD_TRUST_DOMAIN_INVALID")
        with resources.as_file(resources.files("aos_prov") / "files/1rootCA.crt") as ca:
            context = ssl.create_default_context(cafile=str(ca))
        with credentials.user_credentials as material:
            context.load_cert_chain(material.cert_file_name, material.key_file_name)
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect(),
                                                  urllib.request.HTTPSHandler(context=context))
        self.base = "https://" + host + ":10000/api/v11/"
        if expected_role not in ("oem", "service provider"):
            raise CloudFailure("CLOUD_EXPECTED_ROLE_INVALID")
        self.user = project_user(self.call("users/me/"), expected_role, request.get("ownerId"))
        if (not self.user["roleMatches"] or self.user["ownerMatches"] is False
                or not self.user["ownerId"] or self.user["effectivePermissions"] is None):
            raise CloudFailure("OEM_AUTHORITY_NOT_PROVEN" if expected_role == "oem" else "SP_AUTHORITY_NOT_PROVEN")

    def require(self, *permissions):
        missing = set(permissions) - set(self.user["effectivePermissions"])
        if missing:
            prefix = "SP" if self.user.get("role") == "service provider" else "OEM"
            raise CloudFailure(prefix + "_PERMISSION_MISSING:" + ",".join(sorted(missing)))

    def call(self, path, method="GET", body=None, expected=200, absent=False):
        req = urllib.request.Request(self.base + path, method=method,
            data=None if body is None else json.dumps(body).encode(),
            headers={"Accept": "application/json", "Content-Type": "application/json"})
        try:
            with self.opener.open(req, timeout=12) as response:
                if response.status != expected:
                    raise CloudFailure("CLOUD_UNEXPECTED_HTTP_" + str(response.status))
                raw = response.read(2 * 1024 * 1024 + 1)
                if len(raw) > 2 * 1024 * 1024:
                    raise CloudFailure("CLOUD_RESPONSE_TOO_LARGE")
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as error:
            if absent and error.code == 404:
                return None
            raise CloudFailure("CLOUD_HTTP_" + str(error.code)) from None

    def pages(self, path):
        items = []
        for _ in range(100):
            page = self.call(path + ("&" if "?" in path else "?") +
                             urllib.parse.urlencode({"limit": 100, "offset": len(items)}))
            if not isinstance(page, dict) or not isinstance(page.get("items"), list) or type(page.get("total")) is not int:
                raise CloudFailure("CLOUD_PAGINATION_INVALID")
            items.extend(page["items"])
            if len(items) == page["total"]:
                return items
            if not page["items"] or len(items) > page["total"]:
                break
        raise CloudFailure("CLOUD_PAGINATION_INCOMPLETE")

    def unit(self, identity, nodes=True):
        self.require("units_read", *( ["units_nodes_list"] if nodes else []))
        value = self.call("units/" + identity + "/", absent=True)
        if value is None:
            return None
        result = {key: safe_word(value[key]) for key in ("system_uid", "status", "online_status")}
        result.update(id=object_id(value["id"]), fleet=object_id(value["fleet"]) if value.get("fleet") else None,
                      unit_sets=[object_id(item["id"]) for item in value["unit_sets"]])
        if nodes:
            result["nodes"] = [{key: item.get(key) for key in ("id", "node_id", "node_type", "is_main", "status")}
                               for item in self.pages("units/" + result["id"] + "/nodes/")]
        return result

    def inventory(self, set_ids=None, include_units=True):
        self.require("unit_sets_units_list")
        if set_ids:
            source = [self.call("unit-sets/" + object_id(identity) + "/") for identity in set_ids.values()]
        else:
            self.require("unit_sets_list")
            source = [item for item in self.pages("unit-sets/") if any(
                item["title"] == title or item["title"].endswith(" / " + title)
                for title in ("Test Vehicles", "Production Vehicles"))]
        sets = []
        for item in source:
            sets.append({"id": object_id(item["id"]), "title": safe_word(item["title"]),
                         "fleet": object_id(item["fleet"]) if item.get("fleet") else None,
                         "is_validation_set": item["is_validation_set"],
                         "update_strategy": item.get("update_strategy"),
                         "allow_unknown_components": item.get("allow_unknown_components"),
                         "members": [{"id": object_id(unit["id"]), "system_uid": safe_word(unit["system_uid"])}
                                     for unit in self.pages("unit-sets/" + object_id(item["id"]) + "/units/")]})
        units = []
        if include_units:
            self.require("units_list")
            units = [{key: safe_word(item[key]) for key in ("id", "system_uid", "status", "online_status")}
                     for item in self.pages("units/")]
        return {"ownerId": self.user["ownerId"], "sets": sets, "units": units}


def execute(request):
    action = request["action"]
    if action == "service-native-identity":
        address = request.get("address", "")
        if not re.fullmatch(r"unix:/tmp/democtl-native-[A-Za-z0-9_-]+/iam.sock", address):
            raise CloudFailure("SERVICE_NATIVE_IDENTITY_SOCKET_INVALID")
        import grpc
        from importlib.resources import files
        from google.protobuf.empty_pb2 import Empty
        from aos_prov.communication.unit.v6.generated.iamanager_pb2_grpc import IAMPublicIdentityServiceStub
        try:
            # Same server-authenticated native IAM model as the existing KAC:
            # Aos trust root and fixed server name main; never plaintext/TOFU.
            ca = files("aos_prov").joinpath("files/1rootCA.crt").read_bytes()
            options = (("grpc.ssl_target_name_override", "main"), ("grpc.default_authority", "main"),
                ("grpc.enable_http_proxy", 0), ("grpc.max_receive_message_length", 65536))
            with grpc.secure_channel(address, grpc.ssl_channel_credentials(root_certificates=ca), options=options) as channel:
                value = IAMPublicIdentityServiceStub(channel).GetSystemInfo(Empty(), timeout=5)
        except grpc.RpcError as error:
            details = (error.details() or "").lower()
            stage = next((name for needle, name in (("socket closed", "SOCKET_CLOSED"),
                ("connection refused", "CONNECTION_REFUSED"), ("permission denied", "PERMISSION_DENIED"),
                ("protocol error", "PROTOCOL_ERROR"), ("no such file", "SOCKET_ABSENT")) if needle in details), None)
            raise CloudFailure("SERVICE_NATIVE_IAM_RPC_" + error.code().name + ("_" + stage if stage else "")) from None
        uid = value.system_id
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}", uid):
            raise CloudFailure("SERVICE_NATIVE_IDENTITY_INVALID")
        return dict(systemUid=uid, source="IAM_V6_GET_SYSTEM_INFO")
    # IAM identity is guest-local; it needs no OEM request or Cloud connection.
    if action == "identity":
        if request.get("address") not in ("127.0.0.1:18089", "127.0.0.1:18090"):
            raise CloudFailure("SDK_ADDRESS_NOT_OWNED_LOOPBACK")
        from aosedge_demo_orchestrator.unit_sdk import identity
        return identity(request["address"])
    cloud = Cloud(request)
    if action in ("service-assignment-observe", "service-assignment-step"):
        from aosedge_demo_orchestrator.service_assignment import execute as service_assignment
        return service_assignment(cloud, request)
    if action == "observe":
        from aosedge_demo_orchestrator.cloud_observation import inventory, monitoring
        if request.get("observation") not in ("cloud-status", "monitoring"):
            raise CloudFailure("UNIT_OBSERVATION_INVALID")
        return (monitoring if request["observation"] == "monitoring" else inventory)(cloud, request)
    if action == "reconcile-uploads":
        from aosedge_demo_orchestrator.component_cloud import batch_guard
        from aosedge_demo_orchestrator.components import COMPONENT, VERSION
        uploads = request["uploads"]
        if not isinstance(uploads, list) or not uploads or len(uploads) > 16:
            raise CloudFailure("COMPONENT_RECONCILIATION_SCOPE_INVALID")
        cloud.require("deployment_bundles_list")
        bundles = None
        for entry in request["uploads"]:
            deployment_id = object_id(entry["deploymentId"])
            if not VERSION.fullmatch(entry["version"]):
                raise CloudFailure("COMPONENT_OPERATION_RECONCILIATION_REQUIRED")
            if entry.get("verificationTest") is True:
                from aosedge_demo_orchestrator.component_publication import snapshot
                observed = snapshot(cloud, dict(entry, vehicles={}, purpose="retirement"))
                if observed["publication"]["stage"] != "READY":
                    raise CloudFailure("COMPONENT_OPERATION_RECONCILIATION_REQUIRED")
                continue
            cloud.require("verification_batch_read")
            if bundles is None:
                bundles = cloud.pages("deployment-bundles/")
            matches = [bundle for bundle in bundles if bundle.get("id") == deployment_id]
            if len(matches) != 1 or matches[0].get("state") != "done":
                raise CloudFailure("COMPONENT_OPERATION_RECONCILIATION_REQUIRED")
            items = matches[0].get("items") or []
            if len(items) != 1 or items[0].get("codename") != COMPONENT or items[0].get("version") != entry["version"]:
                raise CloudFailure("COMPONENT_OPERATION_RECONCILIATION_REQUIRED")
            batch_id = object_id(entry["batchId"])
            batch = cloud.call("verification-batch/" + batch_id + "/")
            if batch.get("id") != batch_id:
                raise CloudFailure("COMPONENT_OPERATION_RECONCILIATION_REQUIRED")
            batch_guard(batch, entry, cloud.user["ownerId"])
        return {"confirmedUploads": request["uploads"]}
    if action == "inventory":
        return cloud.inventory(request.get("setIds"), request.get("includeUnits", True))
    if action in ("identity", "provision"):
        if request.get("address") not in ("127.0.0.1:18089", "127.0.0.1:18090"):
            raise CloudFailure("SDK_ADDRESS_NOT_OWNED_LOOPBACK")
        from aosedge_demo_orchestrator.unit_sdk import identity, provision
        return identity(request["address"]) if action == "identity" else provision(request, cloud)
    if action == "find":
        cloud.require("units_list")
        uid = safe_word(request["systemUid"])
        matches = cloud.pages("units/?" + urllib.parse.urlencode({"system_uid": uid}))
        if len(matches) > 1 or any(item["system_uid"] != uid for item in matches):
            raise CloudFailure("CLOUD_IDENTITY_AMBIGUOUS")
        return {"unit": cloud.unit(object_id(matches[0]["id"])) if matches else None}
    if action == "wait":
        label = request["label"]
        checks = {
            "CLOUD_ONLINE": lambda unit: unit["status"] == "provisioned" and unit["online_status"] == "Online",
            "CLOUD_OFFLINE": lambda unit: unit["online_status"] == "Offline",
            "CLOUD_DEPROVISIONED": lambda unit: unit["status"] == "new" and unit["online_status"] == "Offline",
            "ROLE_UNIT_SET": lambda unit: request["unitSetId"] in unit["unit_sets"],
            "MEMBERSHIP_REMOVED": lambda unit: request["unitSetId"] not in unit["unit_sets"],
        }
        if label not in checks:
            raise CloudFailure("UNIT_WAIT_LABEL_INVALID")
        identity = object_id(request["unitId"]) if request.get("unitId") else None
        node_data = None if request.get("needNodes") else []
        deadline = time.monotonic() + min(90, request.get("timeout", 90))
        while time.monotonic() < deadline:
            if identity is None:
                cloud.require("units_list")
                matches = cloud.pages("units/?" + urllib.parse.urlencode({"system_uid": request["systemUid"]}))
                if len(matches) > 1 or any(item["system_uid"] != request["systemUid"] for item in matches):
                    raise CloudFailure("CLOUD_IDENTITY_AMBIGUOUS")
                if matches:
                    identity = object_id(matches[0]["id"])
            unit = cloud.unit(identity, nodes=node_data is None) if identity else None
            if unit:
                if unit["system_uid"] != request["systemUid"]:
                    raise CloudFailure("UNIT_IDENTITY_MISMATCH")
                if unit.get("nodes"):
                    node_data = unit["nodes"]
                if checks[label](unit) and (not request.get("needNodes") or node_data):
                    if request.get("needNodes"):
                        unit["nodes"] = node_data
                    return {"unit": unit}
            time.sleep(2)
        raise CloudFailure("UNIT_WAIT_TIMEOUT:" + label)
    identity = object_id(request["unitId"])
    if action == "read":
        return {"unit": cloud.unit(identity, nodes=request.get("nodes", True))}
    if action == "absence":
        cloud.require("units_list", "units_nodes_read")
        inventory = cloud.inventory()
        unit = cloud.unit(identity)
        node = cloud.call("units/" + identity + "/nodes/" + object_id(request["nodeId"]) + "/", absent=True)
        result = {"absent": unit is None and node is None and all(item["id"] != identity for item in inventory["units"]),
                  "inventory": inventory}
        if request.get("retainedSubjects"):
            from aosedge_demo_orchestrator.service_assignment import confirm_retired_subjects
            result["subjectsRetainedUnbound"] = result["absent"] and confirm_retired_subjects(cloud, request)
        return result
    if action in ("assign", "remove"):
        permission = "unit_sets_units_create" if action == "assign" else "unit_sets_units_remove"
        cloud.require(permission)
        path = "unit-sets/" + object_id(request["unitSetId"]) + "/units/"
        uid = safe_word(request["systemUid"])
        unit = cloud.unit(identity)
        if not unit or unit["system_uid"] != uid:
            raise CloudFailure("UNIT_IDENTITY_MISMATCH")
        cloud.call(path if action == "assign" else path + "remove/",
                   "POST" if action == "assign" else "DELETE", {"system_uids": [uid]},
                   201 if action == "assign" else 204)
        return {"httpStatus": 201 if action == "assign" else 204}
    if action in ("deprovision", "delete"):
        cloud.require("units_" + action)
        unit = cloud.unit(identity)
        if not unit or unit["system_uid"] != request["systemUid"]:
            raise CloudFailure("UNIT_IDENTITY_MISMATCH")
        if unit["online_status"] != "Offline":
            raise CloudFailure("UNIT_MUST_BE_OFFLINE")
        if action == "delete" and unit["status"] != "new":
            raise CloudFailure("UNIT_MUST_BE_DEPROVISIONED")
        cloud.call("units/" + identity + ("/deprovision/" if action == "deprovision" else "/"),
                   "DELETE", expected=204)
        return {"httpStatus": 204}
    raise CloudFailure("UNIT_WORKER_ACTION_INVALID")


def main():
    try:
        request = json.loads(sys.stdin.read(65537))
        result = {"ok": True, "data": execute(request)}
    except CloudFailure as error:
        result = {"ok": False, "reason": str(error)}
    except Exception as error:
        result = {"ok": False, "reason": "UNIT_CLOUD_UNAVAILABLE_" + type(error).__name__}
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
