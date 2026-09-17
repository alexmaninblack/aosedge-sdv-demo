# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Owned VISS client credentials and the existing Gateway assignment protocol.

Not Cloud credentials. No secret material is returned to a presenter, journal
or exception. The caller holds the environment writer lock and owns teardown.
"""

import hashlib
import json
import os
import re
import socket
import stat
import subprocess
import tempfile
from pathlib import Path
from uuid import UUID, uuid4

from .environment import EnvironmentError, atomic_json

PROFILE = "SELECTED_UNIT_MUTUAL_TLS"
FILES = frozenset({"ca.pem", "ca-key.pem", "dashboard.pem", "dashboard-key.pem",
    "vdp.pem", "vdp-key.pem", "runtime.pem", "runtime-key.pem", "identity.json"})
LOCAL_FILES = FILES - {"vdp.pem", "vdp-key.pem", "runtime.pem", "runtime-key.pem"}
OPENSSL = "/opt/homebrew/opt/openssl@3/bin/openssl"
URN = "urn:aosedge:demo:viss-client:v1:"


def canonical_uuid(value):
    if not isinstance(value, str) or str(UUID(value)) != value:
        raise EnvironmentError("SOURCE_TRUST_IDENTITY_INVALID")
    return value


def identity(vehicle):
    """Use the provisioning receipt's distinct Cloud and native identities."""
    unit, node = (canonical_uuid(vehicle.get(key)) for key in ("unitId", "nodeId"))
    hardware = (vehicle.get("cloud", {}).get("identity") or {}).get("nodeHardwareId")
    local = canonical_uuid(vehicle.get("localVmId"))
    if (hardware != UUID(local).hex or vehicle.get("cloud", {}).get("lifecycle") != "ONLINE"):
        raise EnvironmentError("SOURCE_TRUST_PROVISIONING_BINDING_REQUIRED")
    return dict(schemaVersion=1, unitId=unit, nodeId=node, localVmId=local, nodeHardwareId=hardware)


def owned(path, directory=False):
    info = path.lstat()
    kind = stat.S_ISDIR if directory else stat.S_ISREG
    if (not kind(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077
            or (not directory and info.st_nlink != 1)):
        raise EnvironmentError("SOURCE_TRUST_FILE_UNSAFE")


def openssl(arguments, input_data=None):
    try:
        result = subprocess.run([OPENSSL, *map(str, arguments)], input=input_data,
            capture_output=True, timeout=10, umask=0o077)
        if result.returncode:
            raise EnvironmentError("SOURCE_TRUST_CERTIFICATE_INVALID")
        return result.stdout
    except (OSError, subprocess.TimeoutExpired):
        raise EnvironmentError("SOURCE_TRUST_CRYPTO_UNAVAILABLE") from None


def fingerprint(certificate):
    return hashlib.sha256(openssl(["x509", "-in", certificate, "-outform", "DER"])).hexdigest()


def write_private(path, data):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(data)


def verify_pair(directory, role, uri=None):
    cert, key = directory / (role + ".pem"), directory / (role + "-key.pem")
    certificate_key = openssl(["x509", "-in", cert, "-noout", "-pubkey"])
    if certificate_key != openssl(["pkey", "-in", key, "-pubout"]):
        raise EnvironmentError("SOURCE_TRUST_KEY_MISMATCH")
    # Verification includes validity, clientAuth purpose and the private CA.
    openssl(["verify", "-purpose", "sslclient" if uri else "any", "-CAfile", directory / "ca.pem", cert])
    if uri:
        san = openssl(["x509", "-in", cert, "-noout", "-ext", "subjectAltName"]).decode().splitlines()
        if len(san) != 2 or san[1].strip() != "URI:" + uri:
            raise EnvironmentError("SOURCE_TRUST_CERTIFICATE_IDENTITY_MISMATCH")


def issue(stage, authority, role, uri):
    openssl(["req", "-new", "-newkey", "rsa:2048", "-nodes", "-sha256",
        "-subj", "/CN=AosEdge VISS " + role, "-keyout", stage / (role + "-key.pem"),
        "-out", stage / "request.pem"])
    write_private(stage / "extensions", ("basicConstraints=critical,CA:FALSE\n"
        "keyUsage=critical,digitalSignature\nextendedKeyUsage=clientAuth\n"
        "subjectAltName=URI:" + uri + "\n").encode())
    openssl(["x509", "-req", "-in", stage / "request.pem", "-CA", authority / "ca.pem",
        "-CAkey", authority / "ca-key.pem", "-set_serial", "0x" + os.urandom(16).hex(),
        "-days", "7", "-sha256", "-extfile", stage / "extensions", "-out", stage / (role + ".pem")])
    (stage / "request.pem").unlink()
    (stage / "extensions").unlink()


def prepare_local(directory):
    """Local dashboard/CA only. No Cloud identity and no guest authority."""
    owned(directory.parent, directory=True)
    if not directory.exists() and not directory.is_symlink():
        with tempfile.TemporaryDirectory(prefix=".viss-issue-", dir=directory.parent) as temporary:
            stage = Path(temporary)
            openssl(["req", "-x509", "-newkey", "rsa:2048", "-nodes", "-sha256", "-days", "30",
                "-subj", "/CN=AosEdge local demo VISS client CA", "-keyout", stage / "ca-key.pem",
                "-out", stage / "ca.pem", "-addext", "basicConstraints=critical,CA:TRUE,pathlen:0",
                "-addext", "keyUsage=critical,keyCertSign,cRLSign"])
            issue(stage, stage, "dashboard", URN + "engineering-dashboard")
            write_private(stage / "identity.json", b'{"schemaVersion":1}')
            inspect_local(stage)
            if directory.exists() or directory.is_symlink():
                raise EnvironmentError("SOURCE_TRUST_CREATION_CONFLICT")
            os.rename(stage, directory)
    return inspect_local(directory)


def inspect_local(directory):
    owned(directory, directory=True)
    files = {p.name for p in directory.iterdir()}
    if files not in (LOCAL_FILES, FILES):
        raise EnvironmentError("SOURCE_TRUST_MATERIAL_INCOMPLETE")
    for name in files:
        owned(directory / name)
    expected = json.loads((directory / "identity.json").read_text())
    if files == LOCAL_FILES and expected != dict(schemaVersion=1):
        raise EnvironmentError("SOURCE_TRUST_IDENTITY_CONFLICT")
    verify_pair(directory, "ca")
    verify_pair(directory, "dashboard", URN + "engineering-dashboard")
    return dict(expected, trustProfile=PROFILE, fingerprints=dict(dashboard=fingerprint(directory / "dashboard.pem")))


def prepare(directory, vehicle):
    """First create or validate the SAME identities; never rotate on a retry."""
    expected = identity(vehicle)
    owned(directory.parent, directory=True)
    uris = dict(dashboard=URN + "engineering-dashboard",
        vdp=URN + "selected-platform-unit:" + expected["unitId"] + ":" + expected["nodeId"],
        runtime=URN + "platform-update-runtime:" + expected["unitId"] + ":" + expected["nodeId"])
    prepare_local(directory)
    if {p.name for p in directory.iterdir()} == LOCAL_FILES:
        # The running Gateway keeps this CA and dashboard identity. Only the
        # now-provisioned Unit's leaves are added; no process is restarted.
        with tempfile.TemporaryDirectory(prefix=".viss-issue-", dir=directory.parent) as temporary:
            stage = Path(temporary)
            for name in LOCAL_FILES - {"identity.json"}:
                write_private(stage / name, (directory / name).read_bytes())
            for role in ("vdp", "runtime"):
                issue(stage, stage, role, uris[role])
            write_private(stage / "identity.json", json.dumps(expected).encode())
            inspect(stage, expected, uris)
            for name in FILES - LOCAL_FILES:
                # Exclusive publication; an interrupted partial enrollment is
                # rejected on retry, never silently reissued or rotated.
                os.link(stage / name, directory / name)
                (stage / name).unlink()
            atomic_json(directory / "identity.json", expected)
    return inspect(directory, expected, uris)


def inspect(directory, expected, uris):
    owned(directory, directory=True)
    if {p.name for p in directory.iterdir()} != FILES:
        raise EnvironmentError("SOURCE_TRUST_MATERIAL_INCOMPLETE")
    for name in FILES:
        owned(directory / name)
    if json.loads((directory / "identity.json").read_text()) != expected:
        raise EnvironmentError("SOURCE_TRUST_IDENTITY_CONFLICT")
    verify_pair(directory, "ca")
    for role, uri in uris.items():
        verify_pair(directory, role, uri)
    return dict(expected, trustProfile=PROFILE, fingerprints={role: fingerprint(directory / (role + ".pem"))
        for role in uris})


def assignment(socket_path, action, generation=None, selected=None, timeout=3):
    """Exactly one bounded CAS attempt. A caller reconciles response loss."""
    if action not in ("status", "select", "detach"):
        raise EnvironmentError("SOURCE_TRUST_ASSIGNMENT_ACTION_INVALID")
    owned(socket_path.parent, directory=True)
    info = socket_path.lstat()
    if not stat.S_ISSOCK(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise EnvironmentError("SOURCE_TRUST_SOCKET_UNSAFE")
    request = dict(schemaVersion=1, action=action, requestId=str(uuid4()))
    if action != "status":
        if type(generation) is not int or not 0 <= generation < 2**63 - 1:
            raise EnvironmentError("SOURCE_TRUST_GENERATION_INVALID")
        keys = {"unitId", "nodeId"}
        if action == "select":
            keys |= {"selectedPlatformUnitCertificateSha256", "platformUpdateRuntimeCertificateSha256"}
        if not isinstance(selected, dict) or set(selected) != keys:
            raise EnvironmentError("SOURCE_TRUST_ASSIGNMENT_IDENTITY_INVALID")
        for key in ("unitId", "nodeId"):
            canonical_uuid(selected[key])
        for key in keys - {"unitId", "nodeId"}:
            if not isinstance(selected[key], str) or not re.fullmatch("[0-9a-f]{64}", selected[key]):
                raise EnvironmentError("SOURCE_TRUST_FINGERPRINT_INVALID")
        request.update(expectedAssignmentGeneration=generation, selectedSource=selected)
    try:
        with socket.socket(socket.AF_UNIX) as client:
            client.settimeout(timeout)
            client.connect(str(socket_path))
            client.sendall((json.dumps(request, separators=(",", ":")) + "\n").encode())
            with client.makefile("rb") as stream:
                raw = stream.readline(4097)
            if len(raw) > 4096 or not raw.endswith(b"\n"):
                raise ValueError("response")
            def unique(pairs):
                result = {}
                for key, item in pairs:
                    if key in result:
                        raise ValueError("duplicate member")
                    result[key] = item
                return result
            value = json.loads(raw, object_pairs_hook=unique)
            if (not isinstance(value, dict) or value.get("requestId") != request["requestId"]
                    or value.get("schemaVersion") != 1 or value.get("result") not in ("ACCEPTED", "REJECTED")
                    or value.get("state") not in ("SELECTED", "DETACHED")
                    or type(value.get("assignmentGeneration")) is not int
                    or not 0 <= value["assignmentGeneration"] < 2**63):
                raise ValueError("request")
            return value
    except (OSError, ValueError):
        raise EnvironmentError("SOURCE_TRUST_ASSIGNMENT_RECONCILIATION_REQUIRED") from None
