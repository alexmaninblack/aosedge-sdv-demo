# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""One official protocol-v6 SDK attempt; credentials stay inside its process."""

import contextlib
import importlib.machinery
import importlib.util
import os
import signal
import sys
from pathlib import Path

from .unit_cloud import CloudFailure
from .status import safe_word


def identity(address):
    import grpc
    from google.protobuf.empty_pb2 import Empty
    from aos_prov.communication.unit.v6.generated import iamanager_pb2 as msg
    from aos_prov.communication.unit.v6.generated import iamanager_pb2_grpc as rpc
    from aos_prov.communication.unit.version.generated.version_pb2_grpc import IAMVersionServiceStub

    with grpc.insecure_channel(address) as channel:
        if IAMVersionServiceStub(channel).GetAPIVersion(Empty(), timeout=5).version != 6:
            raise CloudFailure("UNIT_PROTOCOL_NOT_V6")
        info = rpc.IAMPublicIdentityServiceStub(channel).GetSystemInfo(Empty(), timeout=5)
        nodes = rpc.IAMPublicNodesServiceStub(channel).GetAllNodeIDs(Empty(), timeout=5)
        if len(nodes.ids) != 1:
            raise CloudFailure("UNIT_MUST_HAVE_ONE_NODE")
        node = rpc.IAMPublicNodesServiceStub(channel).GetNodeInfo(msg.GetNodeInfoRequest(node_id=nodes.ids[0]), timeout=5)
        if not any(attr.name == "MainNode" for attr in node.attrs):
            raise CloudFailure("UNIT_MAIN_NODE_NOT_PROVEN")
        return {"systemUid": safe_word(info.system_id), "model": safe_word(info.unit_model),
                "modelVersion": safe_word(info.version), "nodeHardwareId": safe_word(nodes.ids[0]),
                "nodeType": safe_word(node.node_type)}


def provision(request, cloud):
    from aos_prov.commands.provision_v6 import run_provision_v6
    from aos_prov.utils.config import Config
    from importlib.metadata import version
    from packaging.version import Version

    address = request["address"]
    actual = identity(address)
    if actual != request["identity"]:
        raise CloudFailure("PROVISIONING_GUEST_IDENTITY_CHANGED")
    cloud.require("units_provisioning_create", "units_provisioning_supported_software")
    supported = cloud.call("units/provisioning/supported-software/")
    if not any(item.get("name") == "aos-provisioning" and item.get("min_version")
               and Version(version("aos-prov")) > Version(item["min_version"])
               for item in supported.get("software", [])):
        raise CloudFailure("SDK_VERSION_NOT_SUPPORTED_BY_CLOUD")
    if cloud.pages("units/?system_uid=" + actual["systemUid"]):
        raise CloudFailure("PROVISIONING_IDENTITY_ALREADY_EXISTS")
    # Reuse the already qualified narrow SDK transition correction as a
    # library. No old VM/checkpoint/provisioning workflow is invoked.
    scripts = Path(__file__).resolve().parents[4] / "scripts/host"
    sys.path.insert(0, str(scripts))
    from aos_prov_5_4_2_guard import verify
    verify()
    loader = importlib.machinery.SourceFileLoader("democtl_sdk_transition", str(scripts / "aos-prov-5-4-2-compat"))
    module = importlib.util.module_from_spec(importlib.util.spec_from_loader(loader.name, loader))
    loader.exec_module(module)
    module.install_compatibility()
    config = Config()
    config.reset_secure_data()
    config.system_id = actual["systemUid"]
    config.set_model(actual["model"] + ";" + actual["modelVersion"])

    class Registration:
        def register_device(self, payload):
            if payload["system_uid"] != actual["systemUid"] or len(payload["nodes"]) != 1:
                raise CloudFailure("SDK_REGISTRATION_IDENTITY_INVALID")
            return cloud.call("units/provisioning/", "POST", payload, 201)

        def get_unit_link_by_system_uid(self, uid):
            return None

    # The SDK prints CSR/identity/error payloads. Discard its stdout/stderr,
    # never persist a raw transcript or return exception text through IPC.
    def expired(signum, frame):
        raise CloudFailure("SDK_ATTEMPT_TIMEOUT_RECONCILE_REQUIRED")
    signal.signal(signal.SIGALRM, expired)
    signal.alarm(180)
    try:
        with open(os.devnull, "w") as sink, contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
            run_provision_v6(config, address, Registration(), nodes_count=1)
    finally:
        signal.alarm(0)
    return {"sdkCompleted": True, "identity": actual}
