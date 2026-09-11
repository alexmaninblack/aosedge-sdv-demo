# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Fixed engineering projection of public inputs; not a container launcher."""

import hashlib
import json
import os
import re
import ssl
import stat
import subprocess
import tempfile
from pathlib import Path

STORE = Path("/var/aos/workdirs/sm/runtimes/systemd-slot-component")
PUBLIC = Path("/run/aos-demo-service-inputs")
CERTIFICATE = Path("/var/lib/aos-kuksa-tls/server.pem")
OWNER = 0
FILESYSTEM_ROOT = Path("/")
VERSION = re.compile(r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)")


def safe_path(path):
    if not path.is_relative_to(FILESYSTEM_ROOT):
        raise ValueError("SERVICE_INPUT_PATH_OUTSIDE_ROOT")
    for part in (path,) + tuple(path.parents):
        if part.is_symlink():
            raise ValueError("SERVICE_INPUT_SYMLINK")
        if part.exists():
            info = part.stat()
            if info.st_uid != OWNER or info.st_mode & 0o022:
                raise ValueError("SERVICE_INPUT_OWNER_OR_MODE")
        if part == FILESYSTEM_ROOT:
            break


def read_public(path, limit=1048576):
    safe_path(path)
    info = path.stat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_size > limit:
        raise ValueError("SERVICE_INPUT_FILE_UNSAFE")
    return path.read_bytes()


def read_document(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("SERVICE_INPUT_DUPLICATE_FIELD")
            result[key] = value
        return result
    value = json.loads(read_public(path), object_pairs_hook=unique)
    if not isinstance(value, dict):
        raise ValueError("SERVICE_INPUT_OBJECT_REQUIRED")
    return value


def provider_process():
    result = subprocess.run(["systemctl", "show", "aos-vehicle-data-provider",
        "--property=MainPID,ActiveState,Result,ExecMainStatus"], capture_output=True, text=True, timeout=5, check=True)
    values = dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)
    pid = values.get("MainPID", "0")
    if (values.get("ActiveState") != "active" or values.get("Result") != "success"
            or values.get("ExecMainStatus") != "0" or not pid.isdigit() or int(pid) <= 0):
        raise ValueError("SERVICE_INPUT_PROVIDER_NOT_RUNNING")
    return pid, (Path("/proc") / pid / "cmdline").read_bytes().split(b"\0")


def snapshot(request):
    uid = request.get("nativeSystemUid")
    if (request.get("role") != "test" or not isinstance(uid, str)
            or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}", uid)
            or uid != request.get("vehicle", {}).get("systemUid")):
        raise ValueError("SERVICE_INPUT_NATIVE_IDENTITY_MISMATCH")
    if read_public(STORE / "demo-inputs/role", 16) != b"test\n":
        raise ValueError("SERVICE_INPUT_ROLE_MISMATCH")
    transaction = STORE / "state/transaction.json"
    if transaction.exists() or transaction.is_symlink():
        raise ValueError("SERVICE_INPUT_COMPONENT_TRANSACTION_ACTIVE")
    installed = read_document(STORE / "state/installed.json")
    if installed.get("schemaVersion") != 1 or installed.get("slot") not in ("a", "b"):
        raise ValueError("SERVICE_INPUT_COMMIT_INVALID")
    active = STORE / "active"
    if not active.is_symlink() or os.readlink(active) != "slots/" + installed["slot"]:
        raise ValueError("SERVICE_INPUT_ACTIVE_COMMIT_MISMATCH")
    slot = STORE / "slots" / installed["slot"]
    slot_record = read_document(slot / ".aos-instance.json")
    for field in ("schemaVersion", "slot", "Version", "ManifestDigest", "ItemId", "SubjectId", "Instance", "RuntimeId", "Preinstalled"):
        if field not in installed or slot_record.get(field) != installed[field]:
            raise ValueError("SERVICE_INPUT_SLOT_RECORD_MISMATCH")
    metadata = read_document(slot / "component.json")
    provider = read_document(slot / "config/provider.json")
    capability_path = slot / "config/capability-manifest.json"
    capability = read_document(capability_path)
    version = installed["Version"]
    if (not isinstance(version, str) or len(version) > 32 or not VERSION.fullmatch(version)
            or metadata.get("version") != version or provider.get("semanticVersion") != version
            or capability.get("semanticVersion") != version
            or provider.get("capabilityManifestSha256") != hashlib.sha256(read_public(capability_path)).hexdigest()):
        raise ValueError("SERVICE_INPUT_CAPABILITY_MISMATCH")
    compatibility = capability.get("contracts", {}).get("vdpCompatibility", {})
    contract_version, contract_sha = compatibility.get("contractVersion"), compatibility.get("sha256")
    if (compatibility.get("contractId") != "aosedge-demo-vdp-compatibility"
            or not isinstance(contract_version, str) or len(contract_version) > 32
            or not VERSION.fullmatch(contract_version) or not isinstance(contract_sha, str)
            or not re.fullmatch(r"[0-9a-f]{64}", contract_sha)):
        raise ValueError("SERVICE_INPUT_VDP_CONTRACT_INVALID")
    pid, argv = provider_process()
    if not any(argv[i:i + 2] == [b"--config", str(slot / "config/provider.json").encode()] for i in range(len(argv))):
        raise ValueError("SERVICE_INPUT_PROCESS_SLOT_MISMATCH")
    public = dict(schemaVersion=2, unitSystemUid=uid, unitRole="validation",
        vdpContractVersion=contract_version, vdpContractSha256=contract_sha)
    return dict(metadata=public, installed=installed, pid=pid, capability=provider["capabilityManifestSha256"])


def trust():
    raw = read_public(CERTIFICATE, 32768)
    if (raw.count(b"-----BEGIN CERTIFICATE-----") != 1 or b"PRIVATE KEY" in raw
            or not raw.strip().endswith(b"-----END CERTIFICATE-----")):
        raise ValueError("SERVICE_INPUT_PUBLIC_CERTIFICATE_REQUIRED")
    ssl.create_default_context(cadata=raw.decode("ascii"))
    checked = subprocess.run(["openssl", "x509", "-in", str(CERTIFICATE), "-noout", "-checkhost", "Server"],
        capture_output=True, timeout=5)
    if checked.returncode or checked.stdout.strip() != b"Hostname Server does match certificate":
        raise ValueError("SERVICE_INPUT_CERTIFICATE_HOST_MISMATCH")
    return raw


def project(request):
    before = snapshot(request)
    certificate = trust()
    metadata = (json.dumps(before["metadata"], sort_keys=True, indent=2) + "\n").encode()
    contents = {"metadata.json": metadata, "kuksa-ca.pem": certificate}
    safe_path(PUBLIC)
    paths = [PUBLIC / team for team in ("brake", "tire")]
    for directory in paths:
        safe_path(directory)
        if directory.exists() and (not directory.is_dir() or set(p.name for p in directory.iterdir()) - set(contents)):
            raise ValueError("SERVICE_INPUT_DIRECTORY_CONFLICT")
        for name in contents:
            path = directory / name
            if path.exists() or path.is_symlink():
                read_public(path)
    staged = []
    changed = []
    try:
        if not PUBLIC.exists():
            PUBLIC.mkdir(mode=0o755)
            PUBLIC.chmod(0o755)
        for directory in paths:
            if not directory.exists():
                directory.mkdir(mode=0o755)
                directory.chmod(0o755)
            if stat.S_IMODE(directory.stat().st_mode) != 0o755:
                raise ValueError("SERVICE_INPUT_DIRECTORY_MODE")
            for name, content in contents.items():
                target = directory / name
                if target.exists() and target.read_bytes() == content and stat.S_IMODE(target.stat().st_mode) == 0o444:
                    continue
                descriptor, temporary = tempfile.mkstemp(prefix=".democtl-input-", dir=directory)
                staged.append((Path(temporary), target))
                with os.fdopen(descriptor, "wb") as output:
                    output.write(content)
                    os.fchmod(output.fileno(), 0o444)
                    os.fsync(output.fileno())
        if snapshot(request) != before or read_public(CERTIFICATE, 32768) != certificate:
            raise ValueError("SERVICE_INPUT_SOURCE_CHANGED")
        for temporary, target in staged:
            os.replace(temporary, target)
            changed.append(str(target.relative_to(PUBLIC)))
        for directory in paths:
            descriptor = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
        if snapshot(request) != before:
            raise ValueError("SERVICE_INPUT_POST_WRITE_RECONCILIATION_REQUIRED")
        return dict(state="PREPARED", noOp=not changed, changed=changed,
            metadata=before["metadata"], vdpVersion=before["installed"]["Version"],
            sources={team: str(PUBLIC / team) for team in ("brake", "tire")},
            resourcesActivated=False, containerActions=False, coldStartQualified=False)
    finally:
        for temporary, _ in staged:
            if temporary.exists():
                temporary.unlink()


def main(request):
    try:
        if request.get("action") != "service-runtime-prepare" or os.geteuid() != 0:
            raise ValueError("SERVICE_INPUT_OPERATION_INVALID")
        value = dict(ok=True, data=project(request))
    except Exception as error:
        reason = str(error)
        value = dict(ok=False, reason=reason if re.fullmatch(r"SERVICE_INPUT_[A-Z_]+", reason)
                     else "SERVICE_INPUT_PREPARATION_FAILED")
    print(json.dumps(value))
