# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Test-only transient native resource/startup configuration, not SM code."""

import base64
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import types

ROOT = Path("/run/democtl-service-inputs")
DROPIN = Path("/run/systemd/system/aos-sm.service.d/96-democtl-service-inputs.conf")
RESOURCE = Path("/etc/aos/resources.cfg")
PROGRAM = ROOT / "inputs.py"


def command(arguments, timeout=10):
    return subprocess.run(arguments, capture_output=True, text=True, timeout=timeout, check=True)


def service():
    text = command(["systemctl", "show", "aos-sm", "--property=ActiveState,MainPID,Result,NRestarts,User"]).stdout
    return dict(line.split("=", 1) for line in text.splitlines() if "=" in line)


def compose(original):
    result = copy.deepcopy(original)
    if not isinstance(result, list) or any(not isinstance(row, dict) for row in result):
        raise ValueError("SERVICE_ACTIVATION_RESOURCE_SHAPE")
    names = [row.get("name") for row in result]
    if len(names) != len(set(names)) or "kuksa-auth-client" not in names or "kuksa" not in names:
        raise ValueError("SERVICE_ACTIVATION_BASE_RESOURCES_REQUIRED")
    kac = next(row for row in result if row["name"] == "kuksa-auth-client")
    mounts = [row for row in kac.get("mounts", []) if row.get("destination") == "/run/aosedge/secrets/kuksa"]
    if len(mounts) != 1 or mounts[0].get("type") != "tmpfs" or mounts[0].get("source") != "tmpfs":
        raise ValueError("SERVICE_ACTIVATION_TOKEN_MOUNT_MISMATCH")
    expected = {"rw", "nosuid", "nodev", "noexec", "size=65536"}
    options = set(mounts[0].get("options", []))
    if options not in (expected | {"mode=0700"}, expected | {"mode=1777"}):
        raise ValueError("SERVICE_ACTIVATION_TOKEN_OPTIONS_MISMATCH")
    mounts[0]["options"] = ["rw", "nosuid", "nodev", "noexec", "mode=1777", "size=65536"]
    for team in ("brake", "tire"):
        resource = dict(name=team + "-runtime-inputs", mounts=[dict(
            destination="/run/aosedge/platform/service-inputs", type="bind",
            source="/run/aos-demo-service-inputs/" + team,
            options=["bind", "ro", "nosuid", "nodev", "noexec"])])
        existing = [row for row in result if row["name"] == resource["name"]]
        if existing and existing != [resource]:
            raise ValueError("SERVICE_ACTIVATION_RESOURCE_CONFLICT")
        if not existing:
            result.append(resource)
    return result


def dropin_content():
    return ("# democtl-owned Test service inputs; no SM executable override\n[Service]\n"
        "BindReadOnlyPaths=" + str(ROOT / "resources.cfg") + ":" + str(RESOURCE) + "\n"
        "ExecStartPre=/usr/bin/python3 -B " + str(PROGRAM) + " cold\n"
        "ExecStartPost=/usr/bin/python3 -B " + str(PROGRAM) + " verify\n")


def restart_existing_sm(before, binary):
    # The explicit existing-state branch never writes configuration or retries.
    # On a lost response, observe systemd/native state before another decision.
    try:
        command(["systemctl", "restart", "aos-sm"], timeout=45)
        after = service()
        pid = after.get("MainPID", "0")
        if after.get("ActiveState") != "active" or not pid.isdigit() or int(pid) < 1 or pid == before["MainPID"]:
            raise ValueError("SERVICE_ACTIVATION_RESTART_UNCONFIRMED")
        if hashlib.sha256((Path("/proc") / pid / "exe").read_bytes()).hexdigest() != binary:
            raise ValueError("SERVICE_ACTIVATION_RESTART_BINARY_MISMATCH")
        return dict(state="ACTIVE", noOp=False, restarted=True, previousMainPID=before["MainPID"],
            serviceManager=after, smBinarySha256=binary,
            cold=json.loads((ROOT / "cold.json").read_bytes()),
            verification=json.loads((ROOT / "verify.json").read_bytes()),
            rebootQualified=False, transient=True, currentProcessVerified=True)
    except (OSError, subprocess.SubprocessError):
        raise ValueError("SERVICE_ACTIVATION_RESTART_UNCONFIRMED") from None


def activate(request):
    if (os.geteuid() != 0 or request.get("role") != "test"
            or request.get("action") != "service-runtime-activate"):
        raise ValueError("SERVICE_ACTIVATION_TEST_ONLY")
    if type(request.get("restartSm", False)) is not bool:
        raise ValueError("SERVICE_ACTIVATION_RESTART_FLAG_INVALID")
    raw = base64.b64decode(request["program"], validate=True)
    if len(raw) > 65536 or hashlib.sha256(raw).hexdigest() != request["programSha256"]:
        raise ValueError("SERVICE_ACTIVATION_PROGRAM_MISMATCH")
    before = service()
    if before.get("ActiveState") != "active" or not before.get("MainPID", "0").isdigit() or int(before["MainPID"]) < 1:
        raise ValueError("SERVICE_ACTIVATION_RUNNING_SM_REQUIRED")
    if before.get("User") not in ("", "root", "0"):
        raise ValueError("SERVICE_ACTIVATION_SM_IDENTITY_UNSUPPORTED")
    process = Path("/proc") / before["MainPID"]
    binary = hashlib.sha256((process / "exe").read_bytes()).hexdigest()
    cfg = json.loads((process / "root/etc/aos/sm.cfg").read_bytes())
    if cfg.get("resourcesConfigFile", str(RESOURCE)) != str(RESOURCE):
        raise ValueError("SERVICE_ACTIVATION_RESOURCE_PATH_UNSUPPORTED")
    original = json.loads((process / "root" / str(RESOURCE).lstrip("/")).read_bytes())
    resources = (json.dumps(compose(original), sort_keys=True, indent=2) + "\n").encode()
    if ROOT.is_symlink() or DROPIN.is_symlink():
        raise ValueError("SERVICE_ACTIVATION_PATH_UNSAFE")
    # Execute only the exact transported repository module; validate all
    # inputs before creating staging files or changing configuration.
    inputs = types.ModuleType("public_inputs")
    exec(compile(raw, str(PROGRAM), "exec"), inputs.__dict__)
    uid = inputs.native_identity()
    if uid != request["vehicle"].get("systemUid") or uid != request.get("nativeSystemUid"):
        raise ValueError("SERVICE_ACTIVATION_NATIVE_IDENTITY_MISMATCH")
    inputs.snapshot(dict(request, nativeSystemUid=uid))
    if DROPIN.exists():
        if (DROPIN.read_text() != dropin_content() or PROGRAM.read_bytes() != raw
                or (ROOT / "resources.cfg").read_bytes() != resources):
            raise ValueError("SERVICE_ACTIVATION_EXISTING_STATE_RECONCILE")
        for team in ("brake", "tire"):
            if inputs.read_document(inputs.PUBLIC / team / "metadata.json") != inputs.snapshot(request)["metadata"]:
                raise ValueError("SERVICE_ACTIVATION_PUBLIC_INPUT_MISMATCH")
        if request.get("restartSm"):
            return restart_existing_sm(before, binary)
        return dict(state="ACTIVE", noOp=True, serviceManager=before, smBinarySha256=binary,
            cold=json.loads((ROOT / "cold.json").read_bytes()), verification=json.loads((ROOT / "verify.json").read_bytes()),
            rebootQualified=False, transient=True, currentProcessVerified=True)
    if request.get("restartSm"):
        raise ValueError("SERVICE_ACTIVATION_RESTART_REQUIRES_EXISTING_CONFIGURATION")
    if ROOT.exists():
        raise ValueError("SERVICE_ACTIVATION_STAGING_RECONCILE")
    ROOT.mkdir(mode=0o700)
    PROGRAM.write_bytes(raw)
    PROGRAM.chmod(0o444)
    # Prepare data before the first assignment. The same source is restored
    # by systemd before native SM starts during the reinitialization proof.
    inputs.project(dict(request, nativeSystemUid=uid))
    resource_file = ROOT / "resources.cfg"
    resource_file.write_bytes(resources)
    resource_file.chmod(0o444)
    command(["chcon", "--reference=" + str(RESOURCE), str(resource_file)])
    command(["chcon", "--reference=/usr/libexec/aos-vehicle-data-provider-store-check", str(PROGRAM)])
    DROPIN.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
    DROPIN.write_text(dropin_content())
    DROPIN.chmod(0o644)
    command(["systemctl", "daemon-reload"])
    # One controlled restart; never replace SM or its existing drop-ins.
    # If the start fails, remove only this exact transient configuration and
    # restore the unchanged native configuration once.
    try:
        command(["systemctl", "restart", "aos-sm"], timeout=45)
        after = service()
        new_binary = hashlib.sha256((Path("/proc") / after["MainPID"] / "exe").read_bytes()).hexdigest()
        if after.get("ActiveState") != "active" or new_binary != binary:
            raise ValueError("SERVICE_ACTIVATION_SM_STATE_MISMATCH")
    except (OSError, ValueError, subprocess.SubprocessError):
        DROPIN.unlink()
        command(["systemctl", "daemon-reload"])
        command(["systemctl", "restart", "aos-sm"], timeout=45)
        return dict(state="ROLLED_BACK", reason="SERVICE_ACTIVATION_START_FAILED",
            serviceManager=service(), transient=True, rebootQualified=False)
    return dict(state="ACTIVE", noOp=False, serviceManager=after, smBinarySha256=new_binary,
        cold=json.loads((ROOT / "cold.json").read_bytes()), verification=json.loads((ROOT / "verify.json").read_bytes()),
        transient=True, rebootQualified=False)


def main(request):
    try:
        result = dict(ok=True, data=activate(request))
    except Exception as error:
        reason = str(error)
        result = dict(ok=False, reason=reason if re.fullmatch(r"SERVICE_ACTIVATION_[A-Z_]+", reason)
            else "SERVICE_ACTIVATION_UNAVAILABLE_" + type(error).__name__)
    print(json.dumps(result), flush=True)
