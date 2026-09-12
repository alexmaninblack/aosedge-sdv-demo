# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Engineering public-input preparation, shared Demo Control operation."""

import json
import base64
import hashlib
import re
import subprocess
import tempfile
import time
from pathlib import Path

from .environment import EnvironmentError, JOURNAL
from .guest_access import ssh_command
from .source import SourceDriver
from .status import load_configuration, read_json
from .vm import VMService, access_path


def qualified_reboot_restore(state, item, observed):
    """Only the authorized diagnostic Test after its exact SM reapplication."""
    proof = state.get("smServiceUpdateProof", {})
    result = proof.get("result", {})
    service = observed.get("serviceManager", {})
    return (item.get("localVmId") == "d53d05cd-4c46-49c9-a896-534b23b88273"
        and item.get("unitId") == "2a29c145-bbd1-4494-a0e5-d4b79e6a9db5"
        and state.get("factory", {}).get("sha256") == "a9019f4adfe70499bde339c8e9d95eb8568736b73dc218f6c0e390fbcd28ddf4"
        and proof.get("state") == "APPLIED"
        and result.get("binarySha256") in (
            "3e244f438b6f2a8b9dcd08fb4f4be80b21771278e89a0cf6706d87cdec0b2b21",
            "ae36ada2815700d751549404d5fb93f5a9e1f22890507c14da7f2df1a0c30299")
        and result.get("service", {}).get("MainPID") == service.get("MainPID")
        and service.get("MainPID") not in (None, "0") and service.get("ActiveState") == "active"
        and observed.get("nativeContainers", {}).get("state") == "CURRENT"
        and observed.get("nativeContainers", {}).get("containers") == [])


class ServiceInputs:
    def __init__(self, environment):
        self.environment = environment

    def identity(self, state, endpoint):
        # One short-lived SSH Unix-socket forward to native public IAM. No
        # guest SDK installation, Cloud login, new TCP listener or saved UID.
        if endpoint not in ("main:8090", "aosiam:8090", "10.0.0.100:8090", "127.0.0.1:8090"):
            raise EnvironmentError("SERVICE_NATIVE_IAM_ENDPOINT_UNSUPPORTED")
        config = load_configuration(self.environment.root)
        with tempfile.TemporaryDirectory(prefix="democtl-native-", dir="/tmp") as directory:
            socket = Path(directory) / "iam.sock"
            command = ssh_command(access_path(self.environment.root, "test"), state["vehicles"]["test"]["sshPort"], 5)[:-2]
            command = ["ClearAllForwardings=no" if arg == "ClearAllForwardings=yes" else arg for arg in command]
            # Native KAC uses this same Unit-local IAM endpoint. The SM name
            # 'main' resolves to 127.0.1.1 in the SSH host namespace, not to the
            # listening 127.0.0.1 endpoint. No DNS or guest config is changed.
            command[1:1] = ["-N", "-o", "ExitOnForwardFailure=yes", "-L", str(socket) + ":127.0.0.1:8090"]
            with subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE) as forward:
                try:
                    deadline = time.monotonic() + 5
                    while not socket.exists():
                        if forward.poll() is not None or time.monotonic() >= deadline:
                            raise EnvironmentError("SERVICE_NATIVE_IAM_FORWARD_UNAVAILABLE")
                        time.sleep(0.05)
                    result = subprocess.run([str(config["cloudPython"]), "-I", "-B",
                        str(Path(__file__).with_name("unit_cloud.py"))],
                        input=json.dumps(dict(action="service-native-identity", address="unix:" + str(socket))),
                        capture_output=True, text=True, timeout=10)
                    if result.returncode or len(result.stdout) > 4096:
                        raise EnvironmentError("SERVICE_NATIVE_IDENTITY_UNAVAILABLE")
                    value = json.loads(result.stdout)
                    if not value.get("ok") and re.fullmatch(r"SERVICE_NATIVE_IAM_RPC_[A-Z_]+", value.get("reason", "")):
                        raise EnvironmentError(value["reason"])
                    uid = value.get("data", {}).get("systemUid")
                    if not value.get("ok") or not isinstance(uid, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}", uid):
                        raise EnvironmentError("SERVICE_NATIVE_IDENTITY_UNAVAILABLE")
                    return uid
                finally:
                    forward.terminate()
                    try:
                        forward.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        forward.kill()
                        forward.wait(timeout=3)
                    diagnostic = forward.stderr.read(8192).lower()
                    if b"administratively prohibited" in diagnostic or b"forwarding disabled" in diagnostic:
                        raise EnvironmentError("SERVICE_NATIVE_IAM_SSH_FORWARDING_DENIED")
                    if b"connect failed" in diagnostic or b"connection refused" in diagnostic:
                        raise EnvironmentError("SERVICE_NATIVE_IAM_SSH_DESTINATION_UNREACHABLE")

    def prepare(self, target, *, activate=False, restart_sm=False):
        if target != "test":
            raise EnvironmentError("SERVICE_INPUTS_TEST_ONLY")
        if type(restart_sm) is not bool or (restart_sm and not activate):
            raise EnvironmentError("SERVICE_RESTART_REQUIRES_ACTIVATION")
        with self.environment._writer():
            state = read_json(self.environment.root / JOURNAL)
            item = state.get("vehicles", {}).get("test", {})
            if (not item.get("unitId") or not item.get("systemUid") or not item.get("localVmId")
                    or item.get("cloud", {}).get("lifecycle") in ("DELETED", "DEPROVISIONED", "DEPROVISIONING")):
                raise EnvironmentError("SERVICE_INPUTS_CURRENT_TEST_BINDING_REQUIRED")
            driver = SourceDriver(VMService(self.environment))
            with driver.operation(timeout=120 if activate else 30):
                observed = driver.guest(state, "test", "service-runtime-inspect")
                if not observed.get("iamLocalEndpoint", {}).get("loopback8090Reachable"):
                    raise EnvironmentError("SERVICE_NATIVE_IAM_NOT_LISTENING")
                uid = self.identity(state, observed.get("iamPublicServerUrl"))
                native_file = observed.get("iamFileIdentifier", {})
                if (uid != item["systemUid"] or native_file.get("plugin") != "fileidentifier"
                        or native_file.get("path") != "/etc/machine-id" or native_file.get("systemUid") != uid):
                    raise EnvironmentError("SERVICE_INPUT_NATIVE_IDENTITY_MISMATCH")
                if activate:
                    names = {resource.get("name") for resource in observed.get("resources", [])}
                    if (not {"brake-runtime-inputs", "tire-runtime-inputs"}.issubset(names)
                            and not qualified_reboot_restore(state, item, observed)):
                        from .units import UnitService
                        cloud = UnitService(VMService(self.environment)).observe("cloud-status", "test")
                        services = cloud.get("services", {})
                        if (services.get("state") != "CURRENT" or services.get("value") != []
                                or not services.get("coverage", {}).get("complete")):
                            raise EnvironmentError("SERVICE_INPUT_MIGRATION_REQUIRES_NO_LEGACY_ASSIGNMENTS")
                    raw = Path(__file__).with_name("service_inputs_guest.py").read_bytes()
                    return driver.guest(state, "test", "service-runtime-activate", nativeSystemUid=uid,
                        program=base64.b64encode(raw).decode(), programSha256=hashlib.sha256(raw).hexdigest(),
                        restartSm=restart_sm)
                return driver.guest(state, "test", "service-runtime-prepare", nativeSystemUid=uid)
