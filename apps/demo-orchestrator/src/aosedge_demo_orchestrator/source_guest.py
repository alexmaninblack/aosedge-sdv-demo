# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Fixed guest-side local-demo source operations, transported over pinned SSH.

No Cloud credentials, client keys, image modification or arbitrary commands.
Separate owned tables select the VISS source and fault the external uplink.
"""

import json
import base64
import gzip
import io
import hashlib
import os
import re
import socket
import ssl
import stat
import subprocess
import sys
import time
from pathlib import Path

TABLE = "democtl_source"
EXTERNAL_TABLE = "democtl_external"
PROFILE = "LTVP_VISS_SERVER_AUTH_TEST_ONLY"
ROOT = Path("/run/democtl-source")
PROVISION_STATE = Path("/var/aos/.provisionstate")
FACTORY_INPUTS_MARKER = Path("/usr/share/aos-vehicle-platform/demo-runtime-inputs-v1")
FACTORY_INPUTS = Path("/var/aos/workdirs/sm/runtimes/systemd-slot-component/demo-inputs")
FACTORY_ROLE_DROPIN = Path("/run/systemd/system/aos-sm.service.d/20-democtl-role.conf")
SM_RECOVERY_CAP_SHA = "83e705f3f49bea3fb32a37d485da16765f7266d5ba6984631c2459b3e65c7eb6"
SM_COMMITTED_CAP_SHA = "ef96d8e18c018daf6dba9f6a928ace0a9a1a6c9ea96cd37810c2461fc483fb09"
VSS_BASE = Path("/usr/share/vss/vss.json")
VSS_TEMP = Path("/run/democtl-vss/vss.json")
VSS_DROPIN = Path("/run/systemd/system/kuksa-databroker.service.d/90-democtl-vss.conf")
VSS_PATHS = tuple("Vehicle.CarlaSimulation.ChaosWheel." + row + "." + side + "." + leaf
    for leaf in ("LongitudinalSlip", "LateralSlipAngle")
    for row in ("Row1", "Row2") for side in ("Left", "Right"))


def process_wait_observation(pid, proc=Path("/proc")):
    """Bounded wait/resource facts only: no argv, environment or file targets."""
    if not str(pid).isdigit() or int(pid) <= 0:
        return dict(state="UNAVAILABLE")
    root = proc / str(pid)
    result = dict(state="CURRENT", waits={}, threads=[])
    try:
        tasks = sorted(root.joinpath("task").iterdir(), key=lambda path: int(path.name))
        result["threadCount"] = len(tasks)
        result["complete"] = len(tasks) <= 64
        result["openDescriptorCount"] = len(list(root.joinpath("fd").iterdir()))
        for task in tasks[:64]:
            try:
                wait = task.joinpath("wchan").read_text().strip()
                if not re.fullmatch(r"[A-Za-z0-9_]{1,100}", wait):
                    wait = "UNAVAILABLE"
                result["waits"][wait] = result["waits"].get(wait, 0) + 1
                result["threads"].append(dict(id=int(task.name), wait=wait))
            except OSError:
                result["complete"] = False
        for line in root.joinpath("status").read_text().splitlines():
            if line.startswith(("VmRSS:", "VmSize:", "FDSize:")):
                key, value = line.split(":", 1)
                if re.fullmatch(r"\s*\d+(?:\s+kB)?\s*", value):
                    result[key] = value.strip()
    except OSError:
        result.update(state="PARTIAL", complete=False)
    return result


def container_runtime_observation(root, cfg, proc=Path("/proc")):
    """Read native OCI launch facts for our two bootstraps, never env values."""
    runtimes = [row for row in cfg.get("runtimes", []) if row.get("plugin") == "container"]
    if len(runtimes) != 1:
        return dict(state="UNAVAILABLE")
    directory = runtimes[0].get("config", {}).get("runtimeDir", "/run/aos/runtime")
    if not isinstance(directory, str) or not directory.startswith("/run/") or ".." in Path(directory).parts:
        return dict(state="UNSUPPORTED_RUNTIME_PATH")
    path = root / directory.lstrip("/")
    rows = []
    for entry in sorted(path.iterdir())[:16]:
        if not re.fullmatch(r"[0-9a-f-]{36}", entry.name) or entry.is_symlink():
            continue
        file = entry / "config.json"
        if file.is_symlink() or not file.is_file() or file.stat().st_size > 262144:
            continue
        config = json.loads(file.read_text())
        process = config.get("process", {})
        args = process.get("args", [])
        teams = [team for team in ("brake", "tire") if args and args[0] == "/usr/bin/" + team + "-health-bootstrap"]
        if len(teams) != 1:
            continue
        env = {value.split("=", 1)[0] for value in process.get("env", []) if isinstance(value, str)}
        pid_file = entry / ".pid"
        pid = pid_file.read_text().strip() if pid_file.is_file() and pid_file.stat().st_size < 32 else "0"
        rows.append(dict(team=teams[0], containerId=entry.name,
            argumentCount=len(args), executable=args[0],
            nativeEnvPresent={key: key in env for key in (
                "AOS_ITEM_ID", "AOS_SUBJECT_ID", "AOS_INSTANCE_INDEX", "AOS_INSTANCE_ID", "AOS_SECRET")},
            rlimits=[{key: row.get(key) for key in ("type", "soft", "hard")}
                for row in process.get("rlimits", [])],
            user={key: process.get("user", {}).get(key) for key in ("uid", "gid", "additionalGids")},
            linuxResources=config.get("linux", {}).get("resources"),
            processAlive=pid.isdigit() and int(pid) > 0 and (proc / pid).is_dir()))
    return dict(state="CURRENT", runtimeDir=directory, containers=rows)


def vss_supplement(schema):
    """Only append the eight accepted v3 sensor leaves; preserve the base tree."""
    result = json.loads(json.dumps(schema))
    for name in VSS_PATHS:
        current = result
        parts = name.split(".")
        for part in parts[:-1]:
            branch = current.setdefault(part, dict(type="branch", description=part, children={}))
            if not isinstance(branch, dict) or branch.get("type") != "branch" or not isinstance(branch.get("children"), dict):
                raise ValueError("COMPONENT_VSS_BRANCH_CONFLICT")
            current = branch["children"]
        leaf = parts[-1]
        expected = dict(type="sensor", datatype="float", description=(
            "CARLA Chaos wheel lateral slip angle in degrees." if leaf == "LateralSlipAngle" else
            "CARLA Chaos wheel dimensionless longitudinal slip ratio."))
        if leaf == "LateralSlipAngle":
            expected["unit"] = "degrees"
        if leaf in current and (current[leaf].get("type") != "sensor" or current[leaf].get("datatype") != "float"):
            raise ValueError("COMPONENT_VSS_LEAF_CONFLICT")
        current.setdefault(leaf, expected)
    return result


def vss_override_text(identity):
    return "# democtl-owner=" + identity + "\n[Service]\nBindReadOnlyPaths=" + str(VSS_TEMP) + ":" + str(VSS_BASE) + "\n"


def vss_restart(expected_sha):
    if command(["systemctl", "daemon-reload"]).returncode or command(["systemctl", "restart", "--no-block", "kuksa-databroker"]).returncode:
        raise ValueError("COMPONENT_VSS_RESTART_FAILED")
    deadline = time.monotonic() + 6
    while time.monotonic() < deadline:
        info = command(["systemctl", "show", "kuksa-databroker", "--property=MainPID,ActiveState,SubState"])
        values = dict(line.split("=", 1) for line in info.stdout.splitlines() if "=" in line)
        pid = values.get("MainPID", "0")
        path = Path("/proc") / pid / "root/usr/share/vss/vss.json"
        if values.get("SubState") == "running" and pid.isdigit() and int(pid) > 0:
            try:
                if hashlib.sha256(path.read_bytes()).hexdigest() == expected_sha:
                    return int(pid)
            except OSError:
                pass
        time.sleep(0.15)
    raise ValueError("COMPONENT_VSS_RESTART_NOT_CONFIRMED")


def vss_change(request):
    if request.get("target") != "test" or tuple(request.get("additionalPaths", [])) != VSS_PATHS:
        raise ValueError("COMPONENT_VSS_TEST_CONTRACT_ONLY")
    identity = request["vehicle"]["localVmId"]
    if not re.fullmatch(r"[a-f0-9-]{36}", identity):
        raise ValueError("COMPONENT_VSS_OWNER_INVALID")
    for path in (VSS_BASE, VSS_TEMP, VSS_DROPIN):
        if any(p.is_symlink() for p in (path,) + tuple(path.parents)):
            raise ValueError("COMPONENT_VSS_PATH_UNSAFE")
    base = VSS_BASE.read_bytes()
    if len(base) > 16777216:
        raise ValueError("COMPONENT_VSS_SCHEMA_UNSAFE")
    base_sha = hashlib.sha256(base).hexdigest()
    expected = (json.dumps(vss_supplement(json.loads(base)), sort_keys=True) + "\n").encode()
    expected_sha = hashlib.sha256(expected).hexdigest()
    text = vss_override_text(identity)
    present = VSS_DROPIN.exists()
    if present and VSS_DROPIN.read_text() != text:
        raise ValueError("COMPONENT_VSS_OVERRIDE_OWNER_CONFLICT")
    if present and not VSS_TEMP.exists() and request["action"] != "component-schema-remove":
        raise ValueError("COMPONENT_VSS_RECONCILIATION_REQUIRED")
    if VSS_TEMP.exists() and VSS_TEMP.read_bytes() != expected:
        raise ValueError("COMPONENT_VSS_CONTENT_CONFLICT")
    remove = request["action"] == "component-schema-remove"
    result = dict(baseSha256=base_sha, temporarySchema=str(VSS_TEMP), dropIn=str(VSS_DROPIN),
                  temporary=True, rebootRestoresBase=True, productionChanged=False)
    if remove:
        if not present and not VSS_TEMP.exists():
            return dict(result, state="ABSENT", noOp=True)
        if present:
            VSS_DROPIN.unlink()
        pid = vss_restart(base_sha)
        VSS_TEMP.unlink(missing_ok=True)
        return dict(result, state="REMOVED", servicePid=pid)
    if present:
        observed = execute(dict(request, action="component-diagnose", readPaths=list(VSS_PATHS)))
        if observed["schemaLoadedByService"] and observed["schemaSha256"] == expected_sha:
            return dict(result, state="APPLIED", schemaSha256=expected_sha, noOp=True)
        # Do not blindly restart an uncertain prior attempt.
        raise ValueError("COMPONENT_VSS_RECONCILIATION_REQUIRED")
    write_public(VSS_TEMP, expected.decode())
    # Copy the exact base file label, not a broader permission or policy rule.
    label = command(["stat", "-c", "%C", str(VSS_BASE)]).stdout.strip()
    if label not in ("", "?") and command(["chcon", "--reference=" + str(VSS_BASE), str(VSS_TEMP)]).returncode:
        raise ValueError("COMPONENT_VSS_FILE_CONTEXT_FAILED")
    try:
        write_public(VSS_DROPIN, text)
        pid = vss_restart(expected_sha)
    except (ValueError, OSError, subprocess.SubprocessError):
        if VSS_DROPIN.exists() and VSS_DROPIN.read_text() == text:
            VSS_DROPIN.unlink()
        try:
            vss_restart(base_sha)
        except (ValueError, OSError, subprocess.SubprocessError):
            raise ValueError("COMPONENT_VSS_ROLLBACK_UNCONFIRMED") from None
        VSS_TEMP.unlink(missing_ok=True)
        raise ValueError("COMPONENT_VSS_APPLY_FAILED_BASE_RESTORED") from None
    return dict(result, state="APPLIED", schemaSha256=expected_sha, servicePid=pid, addedPaths=list(VSS_PATHS))


def command(args, **kwargs):
    return subprocess.run(args, capture_output=True, text=True, timeout=8, **kwargs)


def external_rules(interface="eth0"):
    """Only the owned SSH control path and in-vehicle VISS cross the uplink offline.

    Include forwarding for service namespaces, and drop IPv6 as well as IPv4.
    Accept in this table does not bypass the platform's other base chains.
    """
    result = []
    for chain, direction in (("output", "out"), ("input", "in"),
                             ("forward", "out"), ("forward", "in")):
        outbound = direction == "out"
        uplink = {"match": {"op": "==", "left": {"meta": {"key": "oifname" if outbound else "iifname"}}, "right": interface}}
        host = {"match": {"op": "==", "left": {"payload": {"protocol": "ip", "field": "daddr" if outbound else "saddr"}}, "right": "10.0.0.1"}}
        ports = [("dport" if outbound else "sport", p) for p in (6443, 16443)]
        if chain != "forward":
            ports.append(("sport" if outbound else "dport", 22))
        for field, port in ports:
            result.append(dict(family="inet", table=EXTERNAL_TABLE, chain=chain, expr=[
                uplink, host, {"match": {"op": "==", "left": {"payload": {"protocol": "tcp", "field": field}}, "right": port}}, {"accept": None}]))
        result.append(dict(family="inet", table=EXTERNAL_TABLE, chain=chain, expr=[uplink, {"drop": None}]))
    return result


def external_state(identity, interface="eth0"):
    listed = command(["nft", "-j", "list", "tables"])
    if listed.returncode:
        raise ValueError("EXTERNAL_LINK_UNOBSERVABLE")
    if not any(x.get("table", {}).get("name") == EXTERNAL_TABLE for x in json.loads(listed.stdout)["nftables"]):
        return "ON"
    listed = command(["nft", "-j", "list", "table", "inet", EXTERNAL_TABLE])
    if listed.returncode:
        raise ValueError("EXTERNAL_LINK_UNOBSERVABLE")
    actual = json.loads(listed.stdout)["nftables"]
    tables = [x["table"] for x in actual if "table" in x]
    chains = [{k: v for k, v in x["chain"].items() if k != "handle"} for x in actual if "chain" in x]
    rules_seen = [{k: v for k, v in x["rule"].items() if k != "handle"} for x in actual if "rule" in x]
    expected_chains = [dict(family="inet", table=EXTERNAL_TABLE, name=name,
        type="filter", hook=name, prio=-190, policy="accept") for name in ("output", "input", "forward")]
    expected_rules = external_rules(interface)
    # nft lists rules grouped by chain; compare that same stable ordering.
    expected_rules = [r for c in expected_chains for r in expected_rules if r["chain"] == c["name"]]
    if (len(tables) != 1 or tables[0].get("comment") != "democtl:" + identity
            or chains != expected_chains or rules_seen != expected_rules):
        raise ValueError("EXTERNAL_LINK_OWNER_OR_RULES_CONFLICT")
    return "OFF"


def external_profile():
    routes = []
    for line in Path("/proc/net/route").read_text().splitlines()[1:]:
        fields = line.split()
        if len(fields) >= 8 and fields[1] == "00000000" and fields[7] == "00000000":
            routes.append(dict(interface=fields[0], gateway=socket.inet_ntoa(bytes.fromhex(fields[2])[::-1]),
                mac=(Path("/sys/class/net") / fields[0] / "address").read_text().strip()))
    connection = os.environ.get("SSH_CONNECTION", "").split()
    return dict(defaultRoutes=routes, maintenancePeer=connection[0] if len(connection) == 4 else None,
        maintenanceAddress=connection[2] if len(connection) == 4 else None,
        maintenancePort=connection[3] if len(connection) == 4 else None)


def external_connectivity(request):
    identity = request["vehicle"]["localVmId"]
    if not re.fullmatch(r"[a-f0-9-]{36}", identity):
        raise ValueError("EXTERNAL_LINK_OWNER_INVALID")
    profile = external_profile()
    routes = profile["defaultRoutes"]
    if (len(routes) != 1 or routes[0].get("gateway") != "10.0.0.1"
            or routes[0].get("mac") != request["vehicle"].get("mac")
            or not re.fullmatch(r"[a-zA-Z0-9_.:-]{1,15}", routes[0].get("interface", ""))
            or profile.get("maintenancePeer") != "10.0.0.1"
            or profile.get("maintenanceAddress") != "10.0.0.100"
            or profile.get("maintenancePort") != "22"):
        raise ValueError("EXTERNAL_LINK_LOCAL_PATH_NOT_SUPPORTED")
    interface = routes[0]["interface"]
    before = external_state(identity, interface)
    action = request["action"].removeprefix("connectivity-")
    if action not in ("on", "off", "status"):
        raise ValueError("EXTERNAL_LINK_ACTION_INVALID")
    result = dict(state=before, evidence="OWNED_GUEST_PACKET_FILTER", noOp=True,
                  cloudState="NOT_OBSERVED", inVehiclePath="PRESERVED_BY_POLICY",
                  rebootRestoresConnectivity=True, networkProfile=profile)
    if action == "status" or before == action.upper():
        return result
    if action == "off":
        entries = [{"add": {"table": {"family": "inet", "name": EXTERNAL_TABLE, "comment": "democtl:" + identity}}}]
        entries.extend({"add": {"chain": dict(family="inet", table=EXTERNAL_TABLE, name=name,
            type="filter", hook=name, prio=-190, policy="accept")}} for name in ("output", "input", "forward"))
        entries.extend({"add": {"rule": rule}} for rule in external_rules(interface))
    else:
        entries = [{"delete": {"table": {"family": "inet", "name": EXTERNAL_TABLE}}}]
    applied = command(["nft", "-j", "-f", "-"], input=json.dumps({"nftables": entries}))
    if applied.returncode or external_state(identity, interface) != action.upper():
        raise ValueError("EXTERNAL_LINK_APPLY_NOT_CONFIRMED")
    return dict(result, state=action.upper(), noOp=False)


def rules(blocked):
    result = []
    if blocked:
        for chain, field, port in (("output", "daddr", "dport"), ("input", "saddr", "sport")):
            result.append({"family": "inet", "table": TABLE, "chain": chain, "expr": [
                {"match": {"op": "==", "left": {"payload": {"protocol": "ip", "field": field}}, "right": "10.0.0.1"}},
                {"match": {"op": "==", "left": {"payload": {"protocol": "tcp", "field": port}}, "right": 6443}},
                {"drop": None}]})
    else:
        result.append({"family": "inet", "table": TABLE, "chain": "route", "expr": [
            {"match": {"op": "==", "left": {"payload": {"protocol": "ip", "field": "daddr"}}, "right": "10.0.0.1"}},
            {"match": {"op": "==", "left": {"payload": {"protocol": "tcp", "field": "dport"}}, "right": 6443}},
            {"dnat": {"family": "ip", "addr": "10.0.0.1", "port": 16443}}]})
    return result


def gate_state(identity):
    listed = command(["nft", "-j", "list", "tables"])
    if listed.returncode:
        raise ValueError("SOURCE_GATE_UNOBSERVABLE")
    tables = json.loads(listed.stdout)["nftables"]
    if not any(x.get("table", {}).get("name") == TABLE for x in tables):
        return "ABSENT"
    result = command(["nft", "-j", "list", "table", "inet", TABLE])
    if result.returncode:
        raise ValueError("SOURCE_GATE_UNOBSERVABLE")
    actual = json.loads(result.stdout)["nftables"]
    table = [x["table"] for x in actual if "table" in x]
    chains = [x["chain"] for x in actual if "chain" in x]
    actual_rules = [{k: v for k, v in x["rule"].items() if k != "handle"} for x in actual if "rule" in x]
    if len(table) != 1 or table[0].get("comment") != "democtl:" + identity or len(chains) != 3:
        raise ValueError("SOURCE_GATE_OWNER_OR_RULES_CONFLICT")
    for name in ("input", "output", "route"):
        expected = dict(family="inet", table=TABLE, name=name, type="nat" if name == "route" else "filter",
            hook="output" if name == "route" else name, prio=-100 if name == "route" else -200, policy="accept")
        if [{k: v for k, v in c.items() if k != "handle"} for c in chains if c["name"] == name] != [expected]:
            raise ValueError("SOURCE_GATE_OWNER_OR_RULES_CONFLICT")
    if actual_rules == rules(True):
        return "BLOCKED"
    if actual_rules == rules(False):
        return "OPEN"
    raise ValueError("SOURCE_GATE_OWNER_OR_RULES_CONFLICT")


def set_gate(identity, blocked):
    state = gate_state(identity)
    desired = "BLOCKED" if blocked else "OPEN"
    if state == desired:
        return state
    entries = []
    if state != "ABSENT":
        entries.append({"delete": {"table": {"family": "inet", "name": TABLE}}})
    entries.append({"add": {"table": {"family": "inet", "name": TABLE, "comment": "democtl:" + identity}}})
    for name in ("output", "input", "route"):
        entries.append({"add": {"chain": dict(family="inet", table=TABLE, name=name,
            type="nat" if name == "route" else "filter", hook="output" if name == "route" else name,
            prio=-100 if name == "route" else -200, policy="accept")}})
    entries.extend({"add": {"rule": rule}} for rule in rules(blocked))
    result = command(["nft", "-j", "-f", "-"], input=json.dumps({"nftables": entries}))
    if result.returncode or gate_state(identity) != desired:
        raise ValueError("SOURCE_GATE_CHANGE_NOT_CONFIRMED")
    return desired


def write_public(path, data, mode=0o644):
    if path.is_symlink():
        raise ValueError("SOURCE_INPUT_SYMLINK")
    path.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
    content = data if isinstance(data, str) else json.dumps(data, sort_keys=True)
    if path.exists() and path.read_text() == content:
        return False
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, mode)
    with os.fdopen(fd, "w") as stream:
        stream.write(content)
    os.chmod(path, mode)
    return True


def sm_public_inputs(pid, runtime):
    host = Path("/run/credentials/aos-sm.service")
    if runtime.get("demoLocalSourceInputs") is True:
        host = FACTORY_INPUTS
    namespace = Path("/proc") / pid / "root" / host.relative_to("/")
    profile = runtime.get("safeStopFreshnessProfile", "standard")
    if runtime.get("demoLocalSourceInputs") is True:
        role = namespace / "role"
        profile = "demo-5s" if role.is_file() and role.read_text() == "test\n" else "standard"
    return host, namespace, profile


def initialize_factory_role(request):
    if not FACTORY_INPUTS_MARKER.is_file():
        return dict(state="NOT_APPLICABLE")
    role = request.get("role")
    if role not in ("test", "production"):
        raise ValueError("SOURCE_ROLE_INVALID")
    if any(path.is_symlink() for path in (FACTORY_INPUTS,) + tuple(FACTORY_INPUTS.parents)):
        raise ValueError("SOURCE_INPUT_SYMLINK")
    store = FACTORY_INPUTS.parent
    mounted = os.path.ismount(store)
    path = FACTORY_INPUTS / "role"
    if path.is_symlink():
        raise ValueError("SOURCE_INPUT_SYMLINK")
    if mounted and path.exists():
        if path.read_text() != role + "\n":
            raise ValueError("SOURCE_FACTORY_ROLE_CONFLICT")
        return dict(state="INITIALIZED", role=role, noOp=True)
    state = command(["systemctl", "show", "aos-sm", "--property=ActiveState", "--value"])
    if state.returncode or state.stdout.strip() != "inactive":
        raise ValueError("SOURCE_FACTORY_ROLE_REQUIRES_UNPROVISIONED_VM")
    # Before provisioning the final store need not be mounted yet. Stage the
    # role in SM's existing start sequence, AFTER its bootstrap/mount dependency.
    # No early directory write, mount, SM start/restart or second persistent store.
    # No shell/systemd variable interpolation or escaped newline literals.
    script = ("from pathlib import Path; import os,sys; p=Path(" + json.dumps(str(path)) + "); "
        "r=bytes(" + repr(list((role + "\n").encode())) + "); "
        "os.path.ismount(p.parent.parent) or sys.exit(\"VDP_STORE_NOT_MOUNTED\"); "
        "(not p.is_symlink() and not p.parent.is_symlink()) or sys.exit(\"VDP_ROLE_SYMLINK\"); "
        "p.parent.mkdir(mode=0o755, parents=True, exist_ok=True); "
        "(not p.exists() or p.read_bytes()==r) or sys.exit(\"VDP_ROLE_CONFLICT\"); "
        "p.write_bytes(r) if not p.exists() else None; p.chmod(0o644)")
    dropin = "# democtl factory role: " + role + "\n[Service]\nExecStartPre=/usr/bin/python3 -c '" + script + "'\n"
    if FACTORY_ROLE_DROPIN.exists() and FACTORY_ROLE_DROPIN.read_text() != dropin:
        raise ValueError("SOURCE_FACTORY_ROLE_CONFLICT")
    if write_public(FACTORY_ROLE_DROPIN, dropin) and command(["systemctl", "daemon-reload"]).returncode:
        raise ValueError("SOURCE_FACTORY_ROLE_RELOAD_FAILED")
    if mounted:
        write_public(path, role + "\n")
    return dict(state="INITIALIZED" if mounted else "STAGED_BEFORE_SM", role=role,
                storeMounted=mounted, noOp=False)


def configure(request):
    item = request["vehicle"]
    if not item.get("unitId"):
        if (request.get("role") != "test" or item.get("cloud") or PROVISION_STATE.exists()
                or not FACTORY_INPUTS_MARKER.is_file()):
            raise ValueError("SOURCE_CLOUD_BINDING_INCOMPLETE")
        initialize_factory_role(request)
        # The local Gateway connection exists before the Cloud identity and
        # before SM mounts its store. Stage only public TLS trust in /run;
        # never invent Unit/Node IDs or write under the unmounted SM store.
        write_public(ROOT / "ca.pem", request["ca"])
        return dict(configured=True, preProvision=True, smRestarted=False,
                    runtimeBinding="DEFERRED_UNTIL_PROVISION")
    generation = request["generation"]
    sm = dict(schemaVersion=2, profile=PROFILE, unitId=item["unitId"],
        nodeId=item["cloud"]["identity"]["nodeHardwareId"], assignmentGeneration=generation,
        endpoint="wss://10.0.0.1:6443", tlsServerName="127.0.0.1", pathSet="PLATFORM_FOTA_SAFE_STOP_1_1_1")
    vdp = dict(schemaVersion=3, profile=PROFILE,
        viss=dict(uri="wss://10.0.0.1:6443", tlsServerName="127.0.0.1"),
        selectedSource=dict(unitId=item["unitId"], nodeId=item["nodeId"],
            assignmentGeneration=generation, pathSet="VDP_V1"))
    # The Factory owns this opt-in. Never retrofit an older immutable image.
    if FACTORY_INPUTS_MARKER.is_file():
        role = request.get("role")
        if role not in ("test", "production"):
            raise ValueError("SOURCE_ROLE_INVALID")
        if any(path.is_symlink() for path in (FACTORY_INPUTS,) + tuple(FACTORY_INPUTS.parents)):
            raise ValueError("SOURCE_INPUT_SYMLINK")
        role_path = FACTORY_INPUTS / "role"
        if role_path.is_symlink() or not role_path.is_file() or role_path.read_text() != role + "\n":
            raise ValueError("SOURCE_FACTORY_ROLE_NOT_INITIALIZED")
        changed = write_public(FACTORY_INPUTS / "viss-update-ca", request["ca"])
        changed = write_public(FACTORY_INPUTS / "selected.json", vdp) or changed
        write_public(FACTORY_INPUTS / "viss-update-binding", sm)
        active = command(["systemctl", "show", "aos-vehicle-data-provider", "--property=ActiveState", "--value"]).stdout.strip()
        if changed and active in ("active", "activating", "failed"):
            if command(["systemctl", "restart", "aos-vehicle-data-provider"]).returncode:
                raise ValueError("VDP_CONFIGURATION_RESTART_FAILED")
        return dict(configured=True, persistent=True, role=role, smRestarted=False)
    # These are public trust/configuration inputs, never client authentication.
    write_public(ROOT / "ca.pem", request["ca"])
    write_public(ROOT / "selected.json", vdp)
    write_public(Path("/run/credentials/aos-sm.service/viss-update-ca"), request["ca"])
    write_public(Path("/run/credentials/aos-sm.service/viss-update-binding"), sm)
    dropin = Path("/run/systemd/system/aos-vehicle-data-provider.service.d/50-democtl-source.conf")
    changed = write_public(dropin, "[Service]\nLoadCredential=viss-server-ca.pem:/run/democtl-source/ca.pem\n"
        "LoadCredential=viss-selected-source.json:/run/democtl-source/selected.json\n")
    if changed and command(["systemctl", "daemon-reload"]).returncode:
        raise ValueError("SOURCE_CREDENTIAL_RELOAD_FAILED")
    # Never enable/install a component or bypass SM's active-slot decision.
    active = command(["systemctl", "show", "aos-vehicle-data-provider", "--property=ActiveState", "--value"]).stdout.strip()
    if active in ("active", "activating", "failed") and changed:
        if command(["systemctl", "restart", "aos-vehicle-data-provider"]).returncode:
            raise ValueError("VDP_CONFIGURATION_RESTART_FAILED")
    return {"configured": True}


def probe(safe_stop=False, preprovision=False):
    # A real server-authenticated WebSocket read from this guest. No KUKSA or
    # mTLS success is inferred from it.
    def receive(stream, length):
        data = b""
        while len(data) < length:
            chunk = stream.recv(length - len(data))
            if not chunk:
                raise ValueError("VISS_PROBE_EOF")
            data += chunk
        return data

    def send(stream, data, opcode=1):
        mask = os.urandom(4)
        if len(data) >= 65536:
            raise ValueError("VISS_PROBE_REQUEST_TOO_LARGE")
        length = bytes([0x80 | len(data)]) if len(data) < 126 else bytes([0xfe]) + len(data).to_bytes(2, "big")
        stream.sendall(bytes([0x80 | opcode]) + length + mask
            + bytes(value ^ mask[index % 4] for index, value in enumerate(data)))

    def frame(stream):
        for _ in range(8):
            first, second = receive(stream, 2)
            if not first & 0x80 or first & 0x70 or second & 0x80:
                raise ValueError("VISS_PROBE_FRAME_UNSUPPORTED")
            length = second & 127
            if length in (126, 127):
                length = int.from_bytes(receive(stream, 2 if length == 126 else 8), "big")
            if length > 65536:
                raise ValueError("VISS_PROBE_RESPONSE_TOO_LARGE")
            data = receive(stream, length)
            opcode = first & 15
            if opcode == 9:
                send(stream, data, 10)
            elif opcode == 1:
                return json.loads(data)
            else:
                raise ValueError("VISS_PROBE_FRAME_UNEXPECTED")
        raise ValueError("VISS_PROBE_CONTROL_LIMIT")

    def read():
        if preprovision and PROVISION_STATE.exists():
            raise ValueError("SOURCE_PROVISIONED_IDENTITY_REQUIRED")
        ca = (FACTORY_INPUTS / "viss-update-ca" if FACTORY_INPUTS_MARKER.is_file()
              and not preprovision else ROOT / "ca.pem")
        started = time.monotonic()
        context = ssl.create_default_context(cafile=str(ca))
        with socket.create_connection(("10.0.0.1", 6443), 3) as raw:
            with context.wrap_socket(raw, server_hostname="127.0.0.1") as client:
                key = base64.b64encode(os.urandom(16)).decode()
                client.sendall(("GET / HTTP/1.1\r\nHost: 127.0.0.1:6443\r\nUpgrade: websocket\r\n"
                    "Connection: Upgrade\r\nSec-WebSocket-Protocol: VISSv3\r\n"
                    "Sec-WebSocket-Version: 13\r\nSec-WebSocket-Key: " + key + "\r\n\r\n").encode())
                header = b""
                while not header.endswith(b"\r\n\r\n"):
                    header += receive(client, 1)
                    if len(header) > 8192:
                        raise ValueError("VISS_PROBE_HEADER_TOO_LARGE")
                lines = header.decode("ascii").split("\r\n")
                fields = {line.split(":", 1)[0].lower(): line.split(":", 1)[1].strip()
                    for line in lines[1:] if ":" in line}
                expected = base64.b64encode(hashlib.sha1((key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode()).digest()).decode()
                if (lines[0].split()[1] != "101" or fields.get("sec-websocket-accept") != expected
                        or fields.get("sec-websocket-protocol") != "VISSv3"):
                    raise ValueError("VISS_PROBE_UPGRADE_INVALID")
                samples = []
                acquired = []
                elapsed = []
                for _ in range(2):
                    query = dict(action="get", path="Vehicle.CarlaSimulation.FrameId", requestId="democtl")
                    if safe_stop:
                        query.update(path="Vehicle", filter=dict(variant="paths", parameter=[
                            "CarlaSimulation.FrameId", "CarlaSimulation.Control.ActiveMode",
                            "CarlaSimulation.Control.TransitionState", "CarlaSimulation.Control.Generation",
                            "CarlaSimulation.Reset.Generation", "CarlaSimulation.Reset.InProgress",
                            "CarlaSimulation.Reset.Discontinuity", "Speed",
                            "Chassis.Accelerator.PedalPosition", "Chassis.Brake.PedalPosition"]))
                    send(client, json.dumps(query, separators=(",", ":")).encode())
                    response = frame(client)
                    acquired.append(int(time.time() * 1000))
                    elapsed.append(round((time.monotonic() - started) * 1000, 3))
                    if "error" in response or response.get("requestId") != "democtl" or "data" not in response:
                        raise ValueError("VISS_FRAME_UNAVAILABLE")
                    samples.append(response["data"])
                    time.sleep(.1)
                if safe_stop:
                    return dict(serverTls=True, snapshots=samples, guestEpochMilliseconds=int(time.time() * 1000),
                        snapshotAcquiredEpochMilliseconds=acquired,
                        snapshotElapsedMilliseconds=elapsed,
                        evidence="ROOT_NETWORK_PROBE_NOT_SM_PROCESS_OBSERVATION")
                ids = []
                for sample in samples:
                    if sample.get("path") != "Vehicle.CarlaSimulation.FrameId":
                        raise ValueError("VISS_PROBE_FRAME_PATH_MISMATCH")
                    value = sample["dp"]["value"]
                    if not isinstance(value, str) or not value.isdigit():
                        raise ValueError("VISS_PROBE_FRAME_ID_INVALID")
                    ids.append(int(value))
                if ids[1] <= ids[0]:
                    raise ValueError("VISS_FRAME_NOT_ADVANCING")
                return {"serverTls": True, "advancingVissFrames": True, "frames": samples}
    try:
        return read()
    except Exception as error:
        return {"serverTls": False, "reason": str(error) if isinstance(error, ValueError)
                else "VISS_GUEST_READ_UNAVAILABLE:" + type(error).__name__}


def clock_status():
    """Read native time synchronization; never adjust clocks or restart a service."""
    result = dict(guestEpochMilliseconds=int(time.time() * 1000))
    allowed = {"NTP", "CanNTP", "NTPSynchronized", "Timezone", "LocalRTC", "LinkNTPServers",
        "SystemNTPServers", "RuntimeNTPServers", "FallbackNTPServers", "ServerName", "ServerAddress",
        "RootDistanceMaxUSec", "PollIntervalMinUSec", "PollIntervalMaxUSec", "PollIntervalUSec",
        "NTPMessage", "Frequency", "Id", "LoadState", "ActiveState", "SubState", "NRestarts", "Result"}
    for label, argv in (
        ("settings", ["timedatectl", "show", "--property=NTP", "--property=CanNTP", "--property=NTPSynchronized", "--property=Timezone", "--property=LocalRTC"]),
        ("synchronization", ["timedatectl", "show-timesync", "--all"]),
        ("services", ["systemctl", "show", "systemd-timesyncd.service", "chronyd.service", "ntpd.service",
                      "--property=Id,LoadState,ActiveState,SubState,NRestarts,Result"]),
    ):
        try:
            observed = command(argv)
            result[label] = dict(exitCode=observed.returncode, fields=[line for line in observed.stdout.splitlines()
                if line.split("=", 1)[0] in allowed and len(line) < 2048
                and re.fullmatch(r"[A-Za-z][A-Za-z0-9]*=[A-Za-z0-9 .,:;_/@=+(){}%\\-]*", line)][:40])
        except FileNotFoundError:
            result[label] = dict(state="TOOL_NOT_INSTALLED")
    return result


def sm_load_public_credentials(root, dropin, request):
    """Use systemd's per-service credential view, never expose its masked parent."""
    ca = ROOT / "ca.pem"
    host = Path("/run/credentials/aos-sm.service/viss-update-binding")
    binding = json.loads(host.read_text())
    expected = dict(schemaVersion=2, profile=PROFILE, unitId=request["vehicle"]["unitId"],
        nodeId=request["vehicle"]["cloud"]["identity"]["nodeHardwareId"], assignmentGeneration=1,
        endpoint="wss://10.0.0.1:6443", tlsServerName="127.0.0.1", pathSet="PLATFORM_FOTA_SAFE_STOP_1_1_1")
    if binding != expected or not ca.is_file() or dropin.is_symlink() or root.is_symlink():
        raise ValueError("SM_PUBLIC_BINDING_NOT_AUTHORIZED_TEST_ASSIGNMENT")
    content = dropin.read_text()
    if "LoadCredential=viss-update-binding:" in content:
        raise ValueError("SM_CREDENTIAL_LOAD_ALREADY_ATTEMPTED_RECONCILE")
    write_public(root / "viss-update-binding", binding)
    dropin.write_text(content + "LoadCredential=viss-update-ca:" + str(ca) + "\n"
        "LoadCredential=viss-update-binding:" + str(root / "viss-update-binding") + "\n")


def sm_saved_test_release(root, committed=False):
    """Validate the authorized Test17 repair or committed18 proof reapply.

    The native runtime still validates the payload before starting it. This
    bounded repair must not become an automatic missing-selector fallback.
    """
    def read(relative):
        path = root / relative
        current = path
        while current != root.parent:
            if current.is_symlink():
                raise ValueError("SM_RECOVERY_UNSAFE_PATH")
            current = current.parent
        if not path.is_file() or path.stat().st_size > 131072:
            raise ValueError("SM_RECOVERY_UNSAFE_RECORD")
        return json.loads(path.read_bytes())

    version, slot = ("18.0.0", "a") if committed else ("17.0.0", "b")
    installed = read("state/installed.json")
    transaction_path = root / "state/transaction.json"
    if committed and (transaction_path.exists() or transaction_path.is_symlink()):
        raise ValueError("SM_RESUME_TRANSACTION_PRESENT")
    transaction = {} if committed else read("state/transaction.json")
    stored = read("slots/" + slot + "/.aos-instance.json")
    stopped = root / "state/stopped.json"
    active = root / "active"
    if (stopped.exists() or stopped.is_symlink()
            or installed.get("schemaVersion") != 1 or installed.get("Version") != version
            or installed.get("slot") != slot or installed != stored):
        raise ValueError("SM_RECOVERY_SAVED_TEST_" + ("18" if committed else "17") + "_MISMATCH")
    if not committed and (transaction.get("schemaVersion") != 2 or transaction.get("operation") != "remove"
            or transaction.get("phase") != "waiting-for-safe-stop" or transaction.get("hasPrevious") is not True
            or transaction.get("previousSlot") != "b" or transaction.get("candidateSlot") != "b"):
        raise ValueError("SM_RECOVERY_SAVED_TEST_17_MISMATCH")
    fields = ("ItemId", "SubjectId", "Instance", "Version", "ManifestDigest", "RuntimeId", "Preinstalled")
    if any(key not in installed for key in fields) or (not committed and any(transaction.get(prefix + key) != installed[key]
           for key in fields for prefix in ("previous", "candidate"))):
        raise ValueError("SM_RECOVERY_INSTANCE_MISMATCH")
    if not re.fullmatch(r"(?:sha256:)?[a-f0-9]{64}", installed["ManifestDigest"]):
        raise ValueError("SM_RECOVERY_MANIFEST_DIGEST_INVALID")
    if (committed or active.exists() or active.is_symlink()) and (not active.is_symlink() or os.readlink(active) != "slots/" + slot):
        raise ValueError("SM_RECOVERY_ACTIVE_SELECTOR_CONFLICT")
    prefix = "slots/" + slot + "/"
    metadata = read(prefix + "component.json")
    provider = read(prefix + "config/provider.json")
    capability = read(prefix + "config/capability-manifest.json")
    capability_sha = hashlib.sha256((root / (prefix + "config/capability-manifest.json")).read_bytes()).hexdigest()
    expected_capability = SM_COMMITTED_CAP_SHA if committed else SM_RECOVERY_CAP_SHA
    if (metadata.get("component") != "vehicle-data-provider" or metadata.get("version") != version
            or metadata.get("architecture") != "arm64" or metadata.get("os") != "linux"
            or metadata.get("runtimeInterface") != 1 or metadata.get("entrypoint") != "bin/vehicle-data-provider"
            or metadata.get("configuration") != "config/provider.json"
            or provider.get("semanticVersion") != version or capability.get("semanticVersion") != version
            or provider.get("capabilityManifestSha256") != capability_sha
            or capability_sha != expected_capability):
        raise ValueError("SM_RECOVERY_PAYLOAD_METADATA_MISMATCH")
    # Reject links/special files before restoring a selector; native validation
    # then applies its full payload, permissions and runtime compatibility rules.
    for index, path in enumerate((root / ("slots/" + slot)).rglob("*")):
        mode = path.lstat().st_mode
        if index >= 4096 or not (stat.S_ISREG(mode) or stat.S_ISDIR(mode)):
            raise ValueError("SM_RECOVERY_PAYLOAD_PATH_UNSAFE")
    return dict(version=version, slot=slot, manifestDigest=installed["ManifestDigest"],
                selectorPresent=active.is_symlink())


def sm_recover_test(request):
    """One authorized transient proof; retain durable intent and immutable .31."""
    if (request.get("target") != "test"
            or request["vehicle"].get("localVmId") != "d53d05cd-4c46-49c9-a896-534b23b88273"
            or request["vehicle"].get("unitId") != "2a29c145-bbd1-4494-a0e5-d4b79e6a9db5"):
        raise ValueError("SM_PROOF_REQUIRES_AUTHORIZED_TEST_31")
    observation = execute(dict(request, action="component-sm-status"))
    if observation["binarySha256"] == request["sha256"] and observation["service"]["ActiveState"] == "active":
        return dict(state="APPLIED", noOp=True, persistentFactoryInputs=True, **observation)
    baseline = hashlib.sha256(Path("/usr/bin/aos_sm_app").read_bytes()).hexdigest()
    if (baseline != "df141e0df7ed9dac6e74ef055e7b31994b501f9d26e1f34d50326c0f76839f86"
            or observation["binarySha256"] not in (None, baseline)
            or (observation["binarySha256"] is not None and observation["freshnessProfile"] != "demo-5s")
            or not FACTORY_INPUTS_MARKER.is_file()
            or not os.path.ismount(FACTORY_INPUTS.parent) or (FACTORY_INPUTS / "role").read_text() != "test\n"):
        raise ValueError("SM_FACTORY_31_BASE_MISMATCH")
    runtime = FACTORY_INPUTS.parent
    committed = request.get("resumeCommitted") is True
    saved = sm_saved_test_release(runtime, committed=committed)
    with gzip.GzipFile(fileobj=io.BytesIO(base64.b64decode(request["binary"], validate=True))) as payload:
        raw = payload.read(256 * 1024 * 1024 + 1)
    if len(raw) > 256 * 1024 * 1024:
        raise ValueError("SM_ARM64_BINARY_TOO_LARGE")
    if hashlib.sha256(raw).hexdigest() != request["sha256"] or raw[:5] != b"\x7fELF\x02" or raw[18:20] != b"\xb7\x00":
        raise ValueError("SM_ARM64_BINARY_SHA_MISMATCH")
    root = Path("/run/democtl-sm-queued-recovery")
    dropin = Path("/run/systemd/system/aos-sm.service.d/92-democtl-sm-queued-recovery.conf")
    if root.exists() or root.is_symlink() or dropin.exists() or dropin.is_symlink():
        raise ValueError("SM_TRANSIENT_STATE_REQUIRES_RECONCILIATION")
    root.mkdir(mode=0o700)
    (root / "aos_sm_app").write_bytes(raw)
    (root / "aos_sm_app").chmod(0o755)
    command(["chcon", "--reference=/usr/bin/aos_sm_app", str(root / "aos_sm_app")], check=True)
    print("Test SM: replace transient runtime once; preserve installed component and durable intent", file=sys.stderr, flush=True)
    subprocess.run(["systemctl", "stop", "aos-sm"], capture_output=True, text=True, timeout=20, check=True)
    if sm_saved_test_release(runtime, committed=committed) != saved:
        raise ValueError("SM_RECOVERY_RECORD_CHANGED")
    # Do not overwrite any active path. These durable records were verified
    # both before and after stopping the only runtime writer.
    if not saved["selectorPresent"]:
        (runtime / "active").symlink_to("slots/b")
        descriptor = os.open(runtime, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    dropin.parent.mkdir(parents=True, exist_ok=True)
    dropin.write_text("[Service]\nBindReadOnlyPaths=" + str(root / "aos_sm_app") + ":/usr/bin/aos_sm_app\n")
    command(["systemctl", "daemon-reload"], check=True)
    print("Test SM: start corrected runtime; native runtime owns the unchanged component state", file=sys.stderr, flush=True)
    subprocess.run(["systemctl", "start", "aos-sm"], capture_output=True, text=True, timeout=20, check=True)
    result = execute(dict(request, action="component-sm-status"))
    if (result["binarySha256"] != request["sha256"] or result["service"]["ActiveState"] != "active"
            or result["freshnessProfile"] != "demo-5s"):
        raise ValueError("SM_TRANSIENT_ACTIVATION_UNCONFIRMED")
    return dict(state="APPLIED", noOp=False, persistentFactoryInputs=True,
                restoredSelector=not saved["selectorPresent"], durableRecordsPreserved=True, **dict(result, mutation=True))


def sm_apply_service_update(request):
    """Replace only the authorized Test SM; retain all Cloud/native instance data."""
    if (request.get("target") != "test"
            or request["vehicle"].get("localVmId") != "d53d05cd-4c46-49c9-a896-534b23b88273"
            or request["vehicle"].get("unitId") != "2a29c145-bbd1-4494-a0e5-d4b79e6a9db5"):
        raise ValueError("SM_PROOF_REQUIRES_AUTHORIZED_TEST_31")
    observation = execute(dict(request, action="component-sm-status"))
    if observation["binarySha256"] == request["sha256"] and observation["service"]["ActiveState"] == "active":
        return dict(state="APPLIED", noOp=True, persistentFactoryInputs=True, **observation)
    previous = "cf251da44d30aec38bd015210f08e284eb121aaff8f00feca2d74b75291a3dee"
    dropin = Path("/run/systemd/system/aos-sm.service.d/92-democtl-sm-queued-recovery.conf")
    old_text = "[Service]\nBindReadOnlyPaths=/run/democtl-sm-queued-recovery/aos_sm_app:/usr/bin/aos_sm_app\n"
    if (observation["binarySha256"] != previous or observation["service"]["ActiveState"] != "active"
            or dropin.is_symlink() or dropin.read_text() != old_text
            or observation["freshnessProfile"] != "demo-5s"):
        raise ValueError("SM_SERVICE_UPDATE_BASE_MISMATCH")
    runtime = FACTORY_INPUTS.parent
    saved = sm_saved_test_release(runtime, committed=True)
    with gzip.GzipFile(fileobj=io.BytesIO(base64.b64decode(request["binary"], validate=True))) as payload:
        raw = payload.read(256 * 1024 * 1024 + 1)
    if (len(raw) > 256 * 1024 * 1024 or hashlib.sha256(raw).hexdigest() != request["sha256"]
            or raw[:5] != b"\x7fELF\x02" or raw[18:20] != b"\xb7\x00"):
        raise ValueError("SM_ARM64_BINARY_SHA_MISMATCH")
    root = Path("/run/democtl-sm-service-update")
    if root.exists() or root.is_symlink():
        raise ValueError("SM_TRANSIENT_STATE_REQUIRES_RECONCILIATION")
    root.mkdir(mode=0o700)
    binary = root / "aos_sm_app"
    binary.write_bytes(raw)
    binary.chmod(0o755)
    command(["chcon", "--reference=/usr/bin/aos_sm_app", str(binary)], check=True)
    print("Test SM: one stop/start with service teardown fix; native databases preserved", file=sys.stderr, flush=True)
    subprocess.run(["systemctl", "stop", "aos-sm"], capture_output=True, text=True, timeout=20, check=True)
    if sm_saved_test_release(runtime, committed=True) != saved:
        raise ValueError("SM_COMMITTED_VDP_RECORD_CHANGED")
    dropin.write_text("[Service]\nBindReadOnlyPaths=" + str(binary) + ":/usr/bin/aos_sm_app\n")
    command(["systemctl", "daemon-reload"], check=True)
    subprocess.run(["systemctl", "start", "aos-sm"], capture_output=True, text=True, timeout=25, check=True)
    result = execute(dict(request, action="component-sm-status"))
    if result["binarySha256"] != request["sha256"] or result["service"]["ActiveState"] != "active":
        raise ValueError("SM_TRANSIENT_ACTIVATION_UNCONFIRMED")
    return dict(state="APPLIED", noOp=False, persistentFactoryInputs=True,
                previousBinarySha256=previous, durableRecordsPreserved=True, **dict(result, mutation=True))


def cm_apply_service_update(request):
    """One Test CM restart; preserve SM, VDP and all native/cloud assignments."""
    if (request.get("target") != "test" or request.get("proof") != "service-snapshot-reconciliation"
            or request["vehicle"].get("localVmId") != "d53d05cd-4c46-49c9-a896-534b23b88273"
            or request["vehicle"].get("unitId") != "2a29c145-bbd1-4494-a0e5-d4b79e6a9db5"):
        raise ValueError("CM_PROOF_REQUIRES_AUTHORIZED_TEST_31")
    previous = "8432c0ca62b3b7bebf0e20f3ae3f82d412429be44fadcd00d914dbf1170f48bc"
    observation = execute(dict(request, action="component-cm-status"))
    if observation["binarySha256"] == request["sha256"] and observation["service"]["ActiveState"] == "active":
        return dict(state="APPLIED", noOp=True, **observation)
    if observation["binarySha256"] != previous or observation["service"]["ActiveState"] != "active":
        raise ValueError("CM_SERVICE_UPDATE_BASE_MISMATCH")
    sm = execute(dict(request, action="component-sm-status"))
    if sm["binarySha256"] != "3e244f438b6f2a8b9dcd08fb4f4be80b21771278e89a0cf6706d87cdec0b2b21":
        raise ValueError("CM_PROOF_REQUIRES_QUALIFIED_SM_PATCH")
    saved = sm_saved_test_release(FACTORY_INPUTS.parent, committed=True)
    with gzip.GzipFile(fileobj=io.BytesIO(base64.b64decode(request["binary"], validate=True))) as payload:
        raw = payload.read(256 * 1024 * 1024 + 1)
    if (len(raw) > 256 * 1024 * 1024 or hashlib.sha256(raw).hexdigest() != request["sha256"]
            or raw[:5] != b"\x7fELF\x02" or raw[18:20] != b"\xb7\x00"):
        raise ValueError("CM_ARM64_BINARY_SHA_MISMATCH")
    root = Path("/run/democtl-cm-service-update")
    dropin = Path("/run/systemd/system/aos-cm.service.d/93-democtl-service-reconcile.conf")
    if root.exists() or root.is_symlink() or dropin.exists() or dropin.is_symlink():
        raise ValueError("CM_TRANSIENT_STATE_REQUIRES_RECONCILIATION")
    root.mkdir(mode=0o700)
    binary = root / "aos_cm_app"
    binary.write_bytes(raw)
    binary.chmod(0o755)
    command(["chcon", "--reference=/usr/bin/aos_cm_app", str(binary)], check=True)
    dropin.parent.mkdir(parents=True, exist_ok=True)
    dropin.write_text("[Service]\nBindReadOnlyPaths=" + str(binary) + ":/usr/bin/aos_cm_app\n")
    command(["systemctl", "daemon-reload"], check=True)
    print("Test CM: one restart with snapshot reconciliation fix; SM and native databases preserved", file=sys.stderr, flush=True)
    subprocess.run(["systemctl", "restart", "aos-cm"], capture_output=True, text=True, timeout=25, check=True)
    result = execute(dict(request, action="component-cm-status"))
    sm_after = execute(dict(request, action="component-sm-status"))
    if (result["binarySha256"] != request["sha256"] or result["service"]["ActiveState"] != "active"
            or sm_after["service"]["MainPID"] != sm["service"]["MainPID"]
            or sm_saved_test_release(FACTORY_INPUTS.parent, committed=True) != saved):
        raise ValueError("CM_TRANSIENT_ACTIVATION_UNCONFIRMED")
    return dict(state="APPLIED", noOp=False, previousBinarySha256=previous,
                smPidPreserved=True, durableRecordsPreserved=True, **dict(result, mutation=True))


def execute(request):
    if request["action"] == "component-cm-apply":
        return cm_apply_service_update(request)
    if request["action"] == "component-cm-status":
        props = command(["systemctl", "show", "aos-cm", "--property=MainPID,ActiveState,Result,NRestarts,FragmentPath"]).stdout
        service = dict(line.split("=", 1) for line in props.splitlines() if "=" in line)
        pid = service.get("MainPID", "0")
        binary = Path("/proc") / pid / "exe"
        digest = hashlib.sha256(binary.read_bytes()).hexdigest() if pid.isdigit() and int(pid) > 0 else None
        return dict(mutation=False, service=service, binarySha256=digest,
                    executable=os.readlink(binary) if digest else None,
                    processWaits=process_wait_observation(pid) if digest else None)
    if request["action"] == "component-sm-apply" and request.get("proof") == "service-update-teardown":
        return sm_apply_service_update(request)
    if request["action"] == "service-runtime-inspect":
        import importlib.util
        import shutil
        if request.get("role") != "test":
            raise ValueError("SERVICE_RUNTIME_INSPECTION_USES_TEST_ONLY")
        props = command(["systemctl", "show", "aos-sm", "--property=MainPID,ActiveState,LimitNOFILE,LimitNOFILESoft"]).stdout
        service = dict(line.split("=", 1) for line in props.splitlines() if "=" in line)
        pid = service.get("MainPID", "0")
        if not pid.isdigit() or int(pid) <= 0:
            raise ValueError("SERVICE_MANAGER_NOT_RUNNING")
        root = Path("/proc") / pid / "root"
        cfg = json.loads((root / "etc/aos/sm.cfg").read_text())
        resource_path = cfg.get("resourcesConfigFile", "/etc/aos/resources.cfg")
        if not isinstance(resource_path, str) or not resource_path.startswith("/") or ".." in Path(resource_path).parts:
            raise ValueError("SERVICE_RESOURCE_PATH_INVALID")
        resources = json.loads((root / resource_path.lstrip("/")).read_text())
        if not isinstance(resources, list):
            raise ValueError("SERVICE_RESOURCE_CONFIG_INVALID")
        names = ("kuksa", "kuksa-auth-client", "brake-runtime-inputs", "tire-runtime-inputs")
        selected = []
        for row in resources:
            if row.get("name") in names:
                selected.append({key: row[key] for key in ("name", "sharedCount", "groups", "hosts", "mounts") if key in row})
        def file_fact(path):
            try:
                info = path.stat()
                return dict(present=True, uid=info.st_uid, gid=info.st_gid, mode=oct(stat.S_IMODE(info.st_mode)))
            except FileNotFoundError:
                return dict(present=False)
        try:
            libc = os.confstr("CS_GNU_LIBC_VERSION")
        except (ValueError, OSError):
            libc = None
        try:
            native_iam = socket.create_connection(("127.0.0.1", 8090), timeout=1)
            native_iam.close()
            iam_loopback = True
        except OSError:
            iam_loopback = False
        try:
            iam_main = sorted({item[4][0] for item in socket.getaddrinfo("main", 8090, type=socket.SOCK_STREAM)})
        except OSError:
            iam_main = []
        identifier = json.loads(Path("/etc/aos/iam.cfg").read_text()).get("identifier", {})
        identifier_path = identifier.get("params", {}).get("systemIDPath")
        native_file = None
        if identifier.get("plugin") == "fileidentifier" and identifier_path == "/etc/machine-id":
            candidate = Path(identifier_path).read_text().strip()
            if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}", candidate):
                native_file = candidate
        return dict(mutation=False, source="ENGINEERING_GUEST_ONLY", architecture=os.uname().machine,
            systemdConfigStorage=dict(readOnly=bool(os.statvfs("/etc/systemd/system").f_flag & os.ST_RDONLY),
                mounts=[line for line in Path("/proc/mounts").read_text().splitlines()
                    if line.split()[1] in ("/", "/etc", "/etc/systemd", "/etc/systemd/system", "/var")]),
            iamFileIdentifier=dict(plugin=identifier.get("plugin"),
                path=identifier_path if identifier_path == "/etc/machine-id" else "UNSUPPORTED",
                systemUid=native_file),
            nativeInputTools={name: shutil.which(name) is not None for name in ("grpcurl", "aos-iam-cli")},
            guestGrpcPython=importlib.util.find_spec("grpc") is not None,
            iamPublicServerUrl=cfg.get("iamPublicServerUrl"),
            iamLocalEndpoint=dict(loopback8090Reachable=iam_loopback, mainAddresses=iam_main),
            containerRuntimes=[{key: row[key] for key in ("plugin", "type", "isComponent") if key in row}
                for row in cfg.get("runtimes", [])],
            libc=libc, loader=file_fact(Path("/lib/ld-linux-aarch64.so.1")), serviceManager=service,
            processWaits=process_wait_observation(pid),
            nativeContainers=container_runtime_observation(root, cfg),
            resourcesConfigFile=resource_path, resources=selected,
            publicInputs={name: file_fact(Path(path)) for name, path in (
                ("kuksaTrust", "/var/lib/aos-kuksa-tls/server.pem"),
                ("kacSocket", "/run/aos-kuksa-auth-compat/request.sock"),
                ("brakeMetadata", "/run/aos-demo-service-inputs/brake/metadata.json"),
                ("tireMetadata", "/run/aos-demo-service-inputs/tire/metadata.json"))})
    if request["action"] == "component-sm-apply" and request.get("proof") == "queued-recovery":
        return sm_recover_test(request)
    if request["action"] == "component-sm-apply" and request.get("proof") == "demo-clock-skew":
        if (request.get("target") != "test"
                or request["vehicle"].get("localVmId") != "d53d05cd-4c46-49c9-a896-534b23b88273"
                or request["vehicle"].get("unitId") != "2a29c145-bbd1-4494-a0e5-d4b79e6a9db5"):
            raise ValueError("SM_PROOF_REQUIRES_AUTHORIZED_TEST_31")
        observation = execute(dict(request, action="component-sm-status"))
        if observation["binarySha256"] == request["sha256"]:
            return dict(state="APPLIED", noOp=True, persistentFactoryInputs=True, **observation)
        if (observation["binarySha256"] != "df141e0df7ed9dac6e74ef055e7b31994b501f9d26e1f34d50326c0f76839f86"
                or observation["freshnessProfile"] != "demo-5s" or not FACTORY_INPUTS_MARKER.is_file()):
            raise ValueError("SM_FACTORY_31_BASE_MISMATCH")
        if Path("/var/aos/workdirs/sm/runtimes/systemd-slot-component/state/transaction.json").exists():
            raise ValueError("SM_ACTIVE_TRANSACTION_PRESERVED")
        raw = base64.b64decode(request["binary"], validate=True)
        if hashlib.sha256(raw).hexdigest() != request["sha256"] or raw[:5] != b"\x7fELF\x02" or raw[18:20] != b"\xb7\x00":
            raise ValueError("SM_ARM64_BINARY_SHA_MISMATCH")
        root = Path("/run/democtl-sm-demo-clock-skew")
        dropin = Path("/run/systemd/system/aos-sm.service.d/91-democtl-sm-demo-clock-skew.conf")
        if root.exists() or dropin.exists() or dropin.is_symlink():
            raise ValueError("SM_TRANSIENT_STATE_REQUIRES_RECONCILIATION")
        root.mkdir(mode=0o700)
        (root / "aos_sm_app").write_bytes(raw)
        (root / "aos_sm_app").chmod(0o755)
        command(["chcon", "--reference=/usr/bin/aos_sm_app", str(root / "aos_sm_app")], check=True)
        dropin.parent.mkdir(parents=True, exist_ok=True)
        dropin.write_text("[Service]\nBindReadOnlyPaths=" + str(root / "aos_sm_app") + ":/usr/bin/aos_sm_app\n")
        command(["systemctl", "daemon-reload"], check=True)
        subprocess.run(["systemctl", "restart", "aos-sm"], capture_output=True, text=True, timeout=20, check=True)
        result = execute(dict(request, action="component-sm-status"))
        if (result["binarySha256"] != request["sha256"] or result["freshnessProfile"] != "demo-5s"
                or result["service"]["ActiveState"] != "active"):
            raise ValueError("SM_TRANSIENT_ACTIVATION_UNCONFIRMED")
        return dict(state="APPLIED", noOp=False, persistentFactoryInputs=True, **dict(result, mutation=True))
    if request["action"] == "component-sm-apply":
        if request.get("target") != "test" or request["vehicle"].get("localVmId") != "540cdea7-3fb8-4554-93aa-75cdf0ed577d":
            raise ValueError("SM_PROOF_REQUIRES_AUTHORIZED_TEST_29")
        observation = execute(dict(request, action="component-sm-status"))
        stop_start_proof = request.get("proof") == "stop-start"
        proof_root = Path("/run/democtl-sm-stop-start" if stop_start_proof else "/run/democtl-sm-demo-5s")
        if observation["binarySha256"] == request["sha256"] and observation["freshnessProfile"] == "demo-5s":
            if not observation["publicInputPresence"]["serviceCA"] or not observation["publicInputPresence"]["serviceBinding"]:
                root = proof_root
                dropin = Path("/run/systemd/system/aos-sm.service.d/90-democtl-sm-demo-5s.conf")
                sm_load_public_credentials(root, dropin, request)
                command(["systemctl", "daemon-reload"], check=True)
                subprocess.run(["systemctl", "restart", "aos-sm"], capture_output=True, text=True, timeout=20, check=True)
                observation = execute(dict(request, action="component-sm-status"))
                if not observation["publicInputPresence"]["serviceCA"] or not observation["publicInputPresence"]["serviceBinding"]:
                    raise ValueError("SM_PUBLIC_INPUTS_NOT_VISIBLE")
                return dict(state="APPLIED", noOp=False, sourceCredentialRepair=True, **dict(observation, mutation=True))
            return dict(state="APPLIED", noOp=True, **observation)
        original = (observation["binarySha256"] == "b010fb73a53e6d2f39eb5cf1cfa46b483331187f9c0f67cd9ec13b216f57d5f4"
                    and observation["freshnessProfile"] == "standard")
        preceding_proof = (stop_start_proof and observation["binarySha256"] ==
            "f0e8c3806c95befc880276f7ca1a05de82a9d866abe9bb665ba3ba868aaedde2"
            and observation["freshnessProfile"] == "demo-5s")
        if not (original or preceding_proof):
            raise ValueError("SM_ORIGINAL_BINARY_OR_CONFIG_MISMATCH")
        if original and observation["executable"] != "/usr/bin/aos_sm_app":
            raise ValueError("SM_EXECUTABLE_PATH_MISMATCH")
        transaction = Path("/var/aos/workdirs/sm/runtimes/systemd-slot-component/state/transaction.json")
        if transaction.exists():
            raise ValueError("SM_ACTIVE_TRANSACTION_PRESERVED")
        raw = base64.b64decode(request["binary"], validate=True)
        if hashlib.sha256(raw).hexdigest() != request["sha256"] or raw[:5] != b"\x7fELF\x02" or raw[18:20] != b"\xb7\x00":
            raise ValueError("SM_ARM64_BINARY_SHA_MISMATCH")
        root = proof_root
        dropin = Path("/run/systemd/system/aos-sm.service.d/90-democtl-sm-demo-5s.conf")
        if root.exists() or (dropin.exists() and not preceding_proof) or dropin.is_symlink():
            raise ValueError("SM_TRANSIENT_STATE_REQUIRES_RECONCILIATION")
        config = json.loads(Path("/etc/aos/sm.cfg").read_text())
        matches = [item["config"] for item in config["runtimes"] if item["plugin"] == "systemd-slot-component"]
        if len(matches) != 1:
            raise ValueError("SM_RUNTIME_CONFIG_NOT_UNIQUE")
        matches[0]["safeStopFreshnessProfile"] = "demo-5s"
        root.mkdir(mode=0o700)
        (root / "aos_sm_app").write_bytes(raw)
        (root / "aos_sm_app").chmod(0o755)
        (root / "sm.cfg").write_text(json.dumps(config, indent=2) + "\n")
        (root / "sm.cfg").chmod(0o644)
        command(["chcon", "--reference=/usr/bin/aos_sm_app", str(root / "aos_sm_app")], check=True)
        command(["chcon", "--reference=/etc/aos/sm.cfg", str(root / "sm.cfg")], check=True)
        dropin.parent.mkdir(parents=True, exist_ok=True)
        dropin.write_text("[Service]\nBindReadOnlyPaths=" + str(root / "aos_sm_app") + ":/usr/bin/aos_sm_app\nBindReadOnlyPaths=" + str(root / "sm.cfg") + ":/etc/aos/sm.cfg\n")
        sm_load_public_credentials(root, dropin, request)
        command(["systemctl", "daemon-reload"], check=True)
        subprocess.run(["systemctl", "restart", "aos-sm"], capture_output=True, text=True, timeout=20, check=True)
        result = execute(dict(request, action="component-sm-status"))
        if result["binarySha256"] != request["sha256"] or result["freshnessProfile"] != "demo-5s" or result["service"]["ActiveState"] != "active":
            raise ValueError("SM_TRANSIENT_ACTIVATION_UNCONFIRMED")
        return dict(state="APPLIED", noOp=False, **dict(result, mutation=True))
    if request["action"] == "component-sm-status":
        props = command(["systemctl", "show", "aos-sm", "--property=MainPID,ActiveState,Result,NRestarts,FragmentPath,ExecStart"]).stdout
        service = dict(line.split("=", 1) for line in props.splitlines() if "=" in line)
        launch = service.pop("ExecStart", "")
        launcher = re.search(r"path=([^ ;]+)", launch)
        service["launcherPath"] = launcher.group(1) if launcher else None
        pid = service.get("MainPID", "0")
        try:
            executable = os.readlink("/proc/" + pid + "/exe") if pid.isdigit() and int(pid) > 0 else None
            binary_sha = hashlib.sha256(Path("/proc/" + pid + "/exe").read_bytes()).hexdigest() if executable else None
        except FileNotFoundError:
            # A failed runtime can exit during this read-only observation.
            executable, binary_sha = None, None
        cfg = Path("/etc/aos/sm.cfg")
        effective = Path("/proc") / pid / "root/etc/aos/sm.cfg"
        config = json.loads(effective.read_text() if effective.is_file() else cfg.read_text())
        runtime = next(item["config"] for item in config["runtimes"] if item["plugin"] == "systemd-slot-component")
        host_inputs, service_inputs, profile = sm_public_inputs(pid, runtime)
        started = command(["systemctl", "show", "aos-sm", "--property=ActiveEnterTimestampMonotonic", "--value"])
        kernel = command(["journalctl", "-k", "-b", "-n", "500", "--no-pager", "-o", "json"])
        events = [json.loads(line) for line in kernel.stdout.splitlines()] if kernel.returncode == 0 else []
        since = int(started.stdout.strip() or 0) if started.returncode == 0 else 0
        denied = [item for item in events if int(item.get("__MONOTONIC_TIMESTAMP", 0)) >= since
                  and re.search(r"avc:\s+denied", str(item.get("MESSAGE", "")), re.I)]
        audit = dict(kernelReadExitCode=kernel.returncode, sinceSmStartMonotonicUs=since,
                     scannedEntries=len(events), deniedSinceSmStart=len(denied) if since and kernel.returncode == 0 else None,
                     completeWindow=bool(since and kernel.returncode == 0 and (len(events) < 500 or
                         int(events[0].get("__MONOTONIC_TIMESTAMP", 0)) <= since)),
                     selinuxEnforcing=Path("/sys/fs/selinux/enforce").read_text().strip() == "1")
        return dict(service=service, executable=executable, processWaits=process_wait_observation(pid),
                    binarySha256=binary_sha,
                    configPath=str(cfg), freshnessProfile=profile,
                    factoryRole={"storeMounted": os.path.ismount(FACTORY_INPUTS.parent),
                        "present": (service_inputs / "role").is_file(),
                        "value": (service_inputs / "role").read_text().strip()
                            if (service_inputs / "role").is_file()
                            and (service_inputs / "role").read_text() in ("test\n", "production\n") else None},
                    binaryContext=command(["stat", "-Lc", "%C", "/proc/" + pid + "/exe"]).stdout.strip() if executable else None,
                    configContext=command(["stat", "-c", "%C", str(cfg)]).stdout.strip(),
                    audit=audit,
                    queuedRecoveryProof={
                        "directoryPresent": Path("/run/democtl-sm-queued-recovery").exists(),
                        "dropInPresent": Path("/run/systemd/system/aos-sm.service.d/92-democtl-sm-queued-recovery.conf").exists(),
                        "activeSelector": os.readlink(FACTORY_INPUTS.parent / "active")
                            if (FACTORY_INPUTS.parent / "active").is_symlink() else None},
                    processContext=Path("/proc/" + pid + "/attr/current").read_text().strip() if executable else None,
                    publicInputPresence={"hostCA": (host_inputs / "viss-update-ca").is_file(),
                        "hostBinding": (host_inputs / "viss-update-binding").is_file(),
                        "serviceCA": (service_inputs / "viss-update-ca").is_file(),
                        "serviceBinding": (service_inputs / "viss-update-binding").is_file()},
                    mountObservation=[line for line in Path("/proc/" + pid + "/mountinfo").read_text().splitlines()
                        if any(path in line for path in ("/run/credentials", "/run/democtl-sm", "/etc/aos/sm.cfg", "/usr/bin/aos_sm_app"))][:20] if executable else [],
                    mutation=False)
    action = request["action"]
    if action == "factory-role":
        return initialize_factory_role(request)
    identity = request["vehicle"]["localVmId"]
    if action in ("connectivity-on", "connectivity-off", "connectivity-status"):
        return external_connectivity(request)
    if action in ("component-schema-apply", "component-schema-remove"):
        return vss_change(request)
    if action == "component-diagnose":
        service = command(["systemctl", "show", "kuksa-databroker", "--property=MainPID,ActiveState,Result,BindReadOnlyPaths,ProtectSystem,ProtectHome,InaccessiblePaths,RootDirectory"])
        properties = dict(line.split("=", 1) for line in service.stdout.splitlines() if "=" in line)
        base = Path("/usr/share/vss/vss.json")
        pid = properties.get("MainPID", "0")
        path = Path("/proc") / pid / "root/usr/share/vss/vss.json" if pid.isdigit() and int(pid) > 0 else base
        if path.is_symlink() or path.stat().st_size > 16777216:
            raise ValueError("COMPONENT_VSS_SCHEMA_UNSAFE")
        schema = json.loads(path.read_bytes())
        def node(name):
            if name in schema:
                return schema[name]
            current = schema
            for part in name.split("."):
                if not isinstance(current, dict):
                    return None
                children = current.get("children", current)
                if part not in children:
                    return None
                current = children[part]
            return current
        present, missing = [], []
        for name in request["readPaths"]:
            value = node(name)
            if value is None:
                missing.append(name)
            else:
                present.append(dict(path=name, type=value.get("type"), datatype=value.get("datatype")))
        # The fixed Factory service loads this schema; report that binding,
        # not its complete ExecStart or any credential argument.
        effective = command(["systemctl", "show", "kuksa-databroker", "--property=ExecStart", "--value"])
        context = command(["stat", "-c", "%C", str(base)]).stdout.strip()
        sm = command(["systemctl", "show", "aos-sm.service", "--property=MainPID", "--value"]).stdout.strip()
        safe_stop = dict(servicePid=sm, bindingObservation="SM_MOUNT_NAMESPACE", mutation=False)
        safe_stop["clock"] = clock_status()
        if sm.isdigit() and int(sm) > 0:
            sm_config = json.loads((Path("/proc") / sm / "root/etc/aos/sm.cfg").read_text())
            runtime = next(item["config"] for item in sm_config["runtimes"] if item["plugin"] == "systemd-slot-component")
            host, namespace, profile = sm_public_inputs(sm, runtime)
            safe_stop["freshnessProfile"] = profile
            safe_stop["presence"] = {name: (namespace / name).is_file() for name in (
                "viss-update-ca", "viss-update-binding", "viss-update-certificate", "viss-update-private-key")}
            binding_path = namespace / "viss-update-binding"
            if binding_path.is_file() and binding_path.stat().st_size < 4096:
                binding = json.loads(binding_path.read_text())
                safe_stop.update(bindingKeys=sorted(binding), schemaVersion=binding.get("schemaVersion"),
                    profileMatches=binding.get("profile") == PROFILE,
                    unitMatches=binding.get("unitId") == request["vehicle"].get("unitId"),
                    nodeMatches=binding.get("nodeId") == request["vehicle"].get("cloud", {}).get("identity", {}).get("nodeHardwareId"),
                    generation=binding.get("assignmentGeneration"),
                    endpointMatches=binding.get("endpoint") == "wss://10.0.0.1:6443",
                    serverNameMatches=binding.get("tlsServerName") == "127.0.0.1",
                    pathSetMatches=binding.get("pathSet") == "PLATFORM_FOTA_SAFE_STOP_1_1_1",
                    hostBindingMatches=binding_path.read_bytes() == (host / "viss-update-binding").read_bytes())
        if safe_stop.get("presence", {}).get("viss-update-binding") and gate_state(identity) == "OPEN":
            safe_stop["network"] = probe(safe_stop=True)
        return dict(schemaPath=str(base), schemaLoadedByService=str(base) in effective.stdout and int(pid or 0) > 0,
            schemaObservation="SERVICE_MOUNT_NAMESPACE" if path != base else "BASE_FILE_ONLY",
            schemaSha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            baseSha256=hashlib.sha256(base.read_bytes()).hexdigest(), baseFileContext=context,
            service=properties, present=present, missing=missing, safeStop=safe_stop,
            permissionProbe="NOT_PERFORMED", mutation=False)
    if action == "component-logs":
        services = command(["systemctl", "show", "aos-sm", "aos-cm", "aos-vehicle-data-provider",
                            "--property=Id,Names,ActiveState,Result,NRestarts"])
        ids = [line[3:] for line in services.stdout.splitlines() if line.startswith("Id=")]
        streams = []
        for unit in ids + ["kuksa-databroker.service", "aos-vehicle-data-provider-selftest@a.service", "aos-vehicle-data-provider-selftest@b.service"]:
            result = command(["journalctl", "-b", "-n", "600" if unit in ("aos-cm.service", "aos-sm.service") else "80",
                              "-o", "json", "--no-pager", "-u", unit])
            if result.returncode or len(result.stdout) > (8388608 if unit in ("aos-cm.service", "aos-sm.service") else 2097152):
                raise ValueError("COMPONENT_JOURNAL_UNAVAILABLE")
            streams.extend((unit, line) for line in result.stdout.splitlines())
        entries, structures, ready_events, cm_transport = [], set(), 0, []
        cm_journal = dict(records=0, messageTypes={}, lastEventTime=None, stages=[])
        for requested_unit, line in streams:
            item = json.loads(line)
            item["_SYSTEMD_UNIT"] = requested_unit
            message = item.get("MESSAGE", "")
            if requested_unit == "aos-cm.service":
                cm_journal["records"] += 1
                kind = type(message).__name__
                cm_journal["messageTypes"][kind] = cm_journal["messageTypes"].get(kind, 0) + 1
                cm_journal["lastEventTime"] = item.get("__REALTIME_TIMESTAMP")
            # journalctl JSON encodes messages containing control bytes as a
            # byte array, including the Aos coloured C++ logger output.
            if isinstance(message, list) and all(type(part) is int and 0 <= part < 256 for part in message):
                message = bytes(message).decode("utf-8", errors="replace")
            if not isinstance(message, str):
                continue
            message = re.sub(r"\x1b\[[0-9;]*m", "", message)
            if item.get("_SYSTEMD_UNIT") == "aos-cm.service":
                stage = re.search(r"\(([a-z][a-z0-9_]{1,30})\) ([A-Za-z][A-Za-z '-]{1,75})(?=:|$)", message)
                if stage and stage[1] in ("communication", "monitoring", "updatemanager", "launcher") and stage[2] in (
                    "Send monitoring", "Send monitoring data", "Enqueue message", "Sent message",
                    "WebSocket frame received", "Sent pong frame", "Received message",
                    "Handle cloud message", "Received ack message", "Update state changed",
                    "Current update canceled", "Instance status received",
                ):
                    cm_journal["stages"].append(dict(time=item.get("__REALTIME_TIMESTAMP"), module=stage[1], stage=stage[2]))
                labels = [label for label, pattern in (
                    ("CONNECTION", r"connect"), ("DISCONNECTED", r"disconnect|connection.*closed"),
                    ("DNS_RESOLUTION", r"resolv|name resolution"), ("TLS", r"TLS|SSL|handshake"),
                    ("TIMEOUT", r"timeout|timed out"), ("REFUSED", r"refused"),
                    ("UNREACHABLE", r"unreachable|no route"), ("ERROR", r"fail|error"),
                    ("AMQP", r"amqp")) if re.search(pattern, message, re.I)]
                if labels:
                    cm_transport.append(dict(time=item.get("__REALTIME_TIMESTAMP"), labels=labels))
            if "Selected vehicle data is ready" in message:
                ready_events += 1
                continue
            if message.lstrip().startswith("{"):
                try:
                    structured = json.loads(message)
                    structures.add(tuple(sorted(key for key in structured if re.fullmatch(r"[a-zA-Z_]{1,32}", key))))
                    if (structured.get("eventType") in ("KUKSA_AUTH_CHANGED", "KUKSA_CONNECTION_CHANGED")
                            and structured.get("reasonCode") == "KUKSA_AUTH_UNAVAILABLE"
                            and structured.get("currentState") == "NOT_READY"):
                        executable = item.get("_EXE", "")
                        team = next((name for name in ("brake", "tire") if
                            executable == "/usr/bin/" + name + "-health-bootstrap"), None)
                        entry = dict(time=item.get("__REALTIME_TIMESTAMP"), unit=item.get("_SYSTEMD_UNIT"),
                            message="Service bootstrap error: KUKSA_AUTH_UNAVAILABLE", team=team)
                        entries.append(entry)
                        continue
                    message = structured.get("message", structured.get("msg", structured.get("text", "")))
                    if not isinstance(message, str):
                        continue
                except (ValueError, TypeError):
                    continue
            # Preserve only typed public instance identity/status fields; never
            # return the unrestricted native instance body or error payload.
            native_fields = {}
            native = re.search(r"(?:instance|instanceID|ident)=\{(component|service):([01]):([A-Za-z0-9_.-]{1,128}):([A-Za-z0-9_.-]{1,128}):([0-9]{1,20})\}", message)
            if native:
                native_fields = dict(type=native[1], preinstalled=native[2] == "1",
                    itemId=native[3], subjectId=native[4], instance=int(native[5]))
                for field, pattern in (("version", r"[0-9]+\.[0-9]+\.[0-9]+(?:-[A-Za-z0-9_.-]+)?"),
                                       ("state", r"activating|active|inactive|failed"),
                                       ("runtimeID", r"[0-9a-f-]{36}")):
                    value = re.search(r"\b" + field + "=(" + pattern + r")(?=,|\s|$)", message)
                    if value:
                        native_fields[field] = value[1]
                # Keep fixed errno labels and source locations from a trailing
                # native error without exposing its arbitrary message/body.
                if re.search(r"fail|error", message, re.I):
                    labels = ("Device or resource busy", "Directory not empty",
                        "No such file or directory", "No such process", "Permission denied",
                        "Operation not permitted", "Too many open files", "Invalid argument",
                        "not found", "already exists", "timeout")
                    native_fields["errorLabels"] = [label for label in labels if label.lower() in message.lower()]
                    native_fields["errorLocations"] = re.findall(
                        r"\b(?:instance|container|crunrunner|filesystem|launcher|networkmanager|instancemanager)\.cpp:[0-9]{1,5}\b", message)
            # Preserve only known fixed runtime failure labels before removing
            # instance bodies, which otherwise also hide the trailing error.
            diagnostic = next((label for label in (
                "a different component transaction is already active",
                "component runtime is not ready",
            ) if label in message), None)
            # No message payloads, transport bodies, auth material or telemetry.
            if "{" in message:
                message = message.split("{", 1)[0] + "[BODY_REDACTED]"
            if (re.search(r"token|password|private.?key|certificate|authorization|jwt|https?://|wss?://", message, re.I)
                    or "-----BEGIN" in message or re.search(r"eyJ[A-Za-z0-9_-]+\.", message)):
                continue
            if not re.search(r"fail|error|cannot|could not|stop|start|health|slot|component|provider|safe.?stop|desired.?status|run.?instances|wait.*active|wait.*node|node.?status|instance.?status|instances.?statuses|Update state changed|Current update canceled", message, re.I):
                continue
            message = re.sub(r"[A-Za-z0-9_+/=-]{48,}", "[REDACTED_LONG_VALUE]", message)
            message = re.sub(r"[\x00-\x1f\x7f]", " ", message)[:600]
            entry = dict(time=item.get("__REALTIME_TIMESTAMP"), unit=item.get("_SYSTEMD_UNIT"), message=message)
            if diagnostic:
                entry["diagnostic"] = diagnostic
            if native_fields:
                entry["nativeInstance"] = native_fields
            entries.append(entry)
        entries.sort(key=lambda entry: int(entry["time"] or 0))
        return dict(entries=entries[-100:], scannedEntries=len(streams), providerReadyEvents=ready_events, structuredFields=sorted(structures),
                    cmJournal=dict(cm_journal, stages=cm_journal["stages"][-15:]),
                    cmTransportEvents=cm_transport[-20:],
                    cmEvents=[entry for entry in entries if entry["unit"] == "aos-cm.service"][-20:],
                    services=services.stdout.strip().splitlines(), guestEpoch=int(time.time()),
                    smStartupFailures=[entry for entry in entries if entry["unit"] == "aos-sm.service"
                        and "can't start launcher" in entry["message"]][:12],
                    cmUpdatePhases=[entry for entry in entries if entry["unit"] == "aos-cm.service" and
                        re.search(r"Update state changed|Current update canceled|Cancel current update|Failed to process desired status", entry["message"])][-20:],
                    window="Current boot: last 600 CM / 600 SM / 80 other service events", projection="BOUNDED_REDACTED_SERVICE_EVENTS")
    if action == "component-status":
        result = execute(dict(request, action="status"))
        root = Path("/var/aos/workdirs/sm/runtimes/systemd-slot-component")
        active = root / "active"
        result.update(activeVersion=None, readPathCount=0, evidence="PROVIDER_REPORTED_NOT_INDEPENDENT_CONSUMER")
        result["runtimeState"] = {}
        for name in ("installed.json", "transaction.json", "last-failure.json"):
            path = root / "state" / name
            if path.is_symlink() or not path.exists():
                continue
            if path.stat().st_size > 131072:
                raise ValueError("COMPONENT_STATE_TOO_LARGE")
            value = json.loads(path.read_bytes())
            row = {key: value[key] for key in ("schemaVersion", "Version", "slot", "version", "candidateVersion", "candidateSlot", "previousVersion", "previousSlot", "hasPrevious", "phase", "operation") if key in value}
            message = value.get("message", "")
            if isinstance(message, str) and re.fullmatch(r"[a-zA-Z0-9_ :.,()-]{1,200}", message):
                row["reason"] = message
            row["modifiedEpoch"] = int(path.stat().st_mtime)
            result["runtimeState"][name] = row
        if not active.is_symlink():
            return result
        target = active.resolve()
        if target not in ((root / "slots/a").resolve(), (root / "slots/b").resolve()):
            raise ValueError("COMPONENT_ACTIVE_SLOT_OUTSIDE_RUNTIME")
        def public_json(name):
            path = target / name
            if path.is_symlink() or path.stat().st_size > 1048576:
                raise ValueError("COMPONENT_ACTIVE_METADATA_UNSAFE")
            return json.loads(path.read_bytes())
        metadata = public_json("component.json")
        capability = public_json("config/capability-manifest.json")
        provider = public_json("config/provider.json")
        digest = hashlib.sha256((target / "config/capability-manifest.json").read_bytes()).hexdigest()
        if (metadata["version"] != provider["semanticVersion"] or metadata["version"] != capability["semanticVersion"]
                or provider["capabilityManifestSha256"] != digest):
            raise ValueError("COMPONENT_ACTIVE_METADATA_MISMATCH")
        properties = command(["systemctl", "show", "aos-vehicle-data-provider", "--property=MainPID,Result,ExecMainStatus,ActiveEnterTimestamp"])
        values = dict(line.split("=", 1) for line in properties.stdout.splitlines() if "=" in line)
        pid = values.get("MainPID", "0")
        # The qualified launcher passes the exact slot config; its cwd is '/'.
        # Project only a comparison result, never the raw process arguments.
        argv = (Path("/proc/" + pid + "/cmdline").read_bytes().split(b"\0")
                if pid.isdigit() and pid != "0" else [])
        configured = any(argv[index:index + 2] == [b"--config", str(target / "config/provider.json").encode()]
                         for index in range(len(argv)))
        result.update(activeVersion=metadata["version"], activeSlot=target.name,
            readPathCount=len(capability["readPaths"]), capabilityManifestSha256=digest,
            processSlotMatches=configured, service=values,
            advisory="DEFERRED" if capability.get("advisoryEndpoints") else "NOT_APPLICABLE")
        return result
    if action == "configure_status":
        configure(request)
        return execute(dict(request, action="status"))
    if action in ("block", "allow"):
        return {"gate": set_gate(identity, action == "block")}
    if action == "configure":
        return configure(request)
    if action == "probe":
        return probe(preprovision=True) if not request["vehicle"].get("unitId") else probe()
    if action in ("status", "observe"):
        active = command(["systemctl", "show", "aos-vehicle-data-provider", "--property=ActiveState,StatusText,NRestarts"])
        values = dict(line.split("=", 1) for line in active.stdout.splitlines() if "=" in line)
        text = values.get("StatusText", "")
        data = ("REPORTED_READY" if text == "VDP data READY; source LIVE; reason NONE" else
                "REPORTED_NOT_READY" if text.startswith("VDP data NOT_READY;") else "NOT_OBSERVED")
        result = {"gate": gate_state(identity), "vdpProcess": values.get("ActiveState", "UNKNOWN"),
                "vdpData": data, "vdpStatusText": text, "vdpRestarts": values.get("NRestarts")}
        if action == "observe" and request["vehicle"].get("sourceProbeSelected") and result["gate"] == "OPEN":
            result["connection"] = probe(preprovision=True) if not request["vehicle"].get("unitId") else probe()
        return result
    raise ValueError("SOURCE_GUEST_ACTION_INVALID")


def main(request):
    try:
        print(json.dumps(dict(ok=True, data=execute(request))))
    except Exception as error:
        print(json.dumps(dict(ok=False, reason=str(error) if isinstance(error, ValueError)
            else "SOURCE_GUEST_OPERATION_UNAVAILABLE:" + type(error).__name__)))
