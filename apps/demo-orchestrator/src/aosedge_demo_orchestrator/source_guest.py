# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Fixed guest-side local-demo source operations, transported over pinned SSH.

No Cloud credentials, client keys, image modification or arbitrary commands.
Separate owned tables select the VISS source and fault the external uplink.
"""

import json
import base64
import datetime
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
VSS_ADVISORY_TYPES = tuple(("Vehicle.OEM." + team + ".Advisory." + leaf, kind)
    for team in ("BrakeHealth", "TireHealth")
    for leaf, kind in (("Request", "actuator"), ("GatewayStatus", "sensor"), ("Readiness", "actuator")))
VSS_PROOF_PATHS = VSS_PATHS + tuple(name for name, _ in VSS_ADVISORY_TYPES)


def advisory_configuration_observation(capability):
    """Manifest configuration only, never an application acknowledgement."""
    if not capability.get("advisoryEndpoints"):
        return "NOT_APPLICABLE"
    expected = dict(contractId="aosedge-demo-typed-qm-advisory", contractVersion="1.1.0",
        sha256="343e128bf9a0cac60a4f1b573315716f440accef17933fbcd9f6af49bc88300c")
    contract = capability.get("contracts", {}).get("typedQmAdvisory")
    return "CONFIGURED_NOT_APPLICATION_PROOF" if contract == expected else "DEFERRED"


def advisory_log_observation(raw):
    """Fixed endpoint/result projection; do not return unrestricted messages."""
    result = []
    for line in raw.splitlines():
        item = json.loads(line)
        message = item.get("MESSAGE", "")
        if not isinstance(message, str):
            continue
        match = re.search(r"QM_ADVISORY endpoint=(transport|Vehicle\.OEM\.(?:BrakeHealth|TireHealth)\.Advisory\.(?:Request|GatewayStatus|Availability)) result=([A-Z_]{1,64})$", message)
        if match and match[2] in {
            "KUKSA_TARGETS_READY", "KUKSA_TARGETS_UNAVAILABLE", "VISS_RESPONSE_TIMEOUT",
            "VISS_SET_ACCEPTED", "VISS_SET_REJECTED", "FORWARDED_TO_GATEWAY",
            "GATEWAY_STATUS_PUBLISHED", "UNAUTHORIZED_PATH", "UNAUTHORIZED_SOURCE",
            "INVALID_SCHEMA", "INVALID_VALUE", "STALE_REQUEST", "IDEMPOTENT_NO_NEW_EFFECT",
            "REPLAY_DETECTED", "SEQUENCE_ROLLBACK", "RATE_LIMITED", "INTERNAL_ERROR",
        }:
            result.append(dict(time=item.get("__REALTIME_TIMESTAMP"), endpoint=match[1], result=match[2]))
    return result[-40:]


def cm_payload_observation(payload):
    """Protocol shape and public deployment identities, never transport secrets."""
    if not isinstance(payload, dict):
        return {}
    result = {"fields": sorted(key for key in payload if re.fullmatch(r"[A-Za-z]{1,40}", key))}
    for key in ("messageType", "state", "updateState"):
        value = payload.get(key)
        if isinstance(value, str) and re.fullmatch(r"[A-Za-z]{1,40}", value):
            result[key] = value
    if type(payload.get("isDeltaInfo")) is bool:
        result["isDeltaInfo"] = payload["isDeltaInfo"]
    for group in ("items", "instances", "nodes", "subjects", "services"):
        rows = payload.get(group)
        if not isinstance(rows, list):
            continue
        result[group + "Count"] = len(rows)
        projected = []
        for row in rows[:64]:
            if not isinstance(row, dict):
                continue
            value = {}
            for obj in (row, row.get("item", {}), row.get("instance", {})):
                if not isinstance(obj, dict):
                    continue
                for key in ("id", "itemId", "serviceId", "subjectId", "nodeId", "version", "type", "state", "status", "runState"):
                    field = obj.get(key)
                    if isinstance(field, str) and re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", field):
                        value[key] = field
                for key in ("instance", "numInstances"):
                    if type(obj.get(key)) is int:
                        value[key] = obj[key]
            if value:
                projected.append(value)
        result[group] = projected
    return result


def cm_delivery_observation(pid, proc=Path("/proc")):
    """Read existing filtered journal and CM SQLite state; never enable logging."""
    if not str(pid).isdigit() or int(pid) <= 0:
        return dict(state="UNAVAILABLE")
    result = dict(mutation=False)
    # The factory journalctl has no PCRE2: filter after reading bounded rows,
    # rather than depending on journalctl --grep.
    journal = command(["journalctl", "-b", "-u", "aos-cm.service", "_PID=" + str(pid),
        "-n", "30000", "-o", "json", "--output-fields=MESSAGE,__REALTIME_TIMESTAMP", "--no-pager"])
    if journal.returncode or len(journal.stdout) > 67108864:
        result["journal"] = dict(state="UNAVAILABLE_OR_TOO_LARGE", exitCode=journal.returncode,
            bytes=len(journal.stdout), diagnostic=journal.stderr.strip()[:300])
    else:
        lines = journal.stdout.splitlines()
        events, counts, latest, responses, launcher_events = [], {}, {}, {}, []
        for line in lines:
            record = json.loads(line)
            message = record.get("MESSAGE", "")
            if isinstance(message, list):
                message = bytes(message).decode("utf-8", errors="replace")
            if not isinstance(message, str):
                continue
            message = re.sub(r"\x1b\[[0-9;]*m", "", message)
            wire = re.search(r"\(communication\) (Received message|Sent message|Handle cloud message):.*?message=(\{.*)", message)
            entry = dict(time=record.get("__REALTIME_TIMESTAMP"))
            if wire:
                try:
                    envelope, _ = json.JSONDecoder().raw_decode(wire[2])
                except (ValueError, TypeError) as error:
                    counts["unparsedWire"] = counts.get("unparsedWire", 0) + 1
                    kind = re.search(r'"messageType"\s*:\s*"([A-Za-z]{1,40})"', wire[2])
                    key = "incomplete:" + wire[1] + ":" + (kind[1] if kind else "UNKNOWN")
                    counts[key] = counts.get(key, 0) + 1
                    incomplete = dict(time=entry["time"], stage=wire[1], incomplete=True,
                        messageType=kind[1] if kind else None, length=len(wire[2]),
                        errorOffset=getattr(error, "pos", None), lineCount=wire[2].count("\n") + 1)
                    flag = re.search(r'"isDeltaInfo"\s*:\s*(true|false)', wire[2])
                    if flag:
                        incomplete["isDeltaInfo"] = flag[1] == "true"
                    latest[key] = incomplete
                    if kind and kind[1] not in ("monitoringData", "ack"):
                        events.append(incomplete)
                    continue
                payload = envelope.get("data", {})
                entry.update(stage=wire[1], payload=cm_payload_observation(payload))
                header = envelope.get("header", {})
                for key in ("txn", "systemId", "createdAt"):
                    value = header.get(key)
                    if isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9_.:+-]{1,128}", value):
                        entry[key] = value
                if payload.get("messageType") in ("ack", "nack"):
                    responses[header.get("txn")] = payload["messageType"]
            else:
                # Only the fixed native log heading, never free-form error/body.
                stage = re.search(r"\(([a-z_]{1,30})\) ([A-Za-z][A-Za-z '-]{1,100})(?=:|$)", message)
                if not stage:
                    continue
                if stage[1] == "launcher":
                    observed = dict(time=entry["time"], module=stage[1], stage=stage[2])
                    for field in ("instances", "numRequests", "numInstances", "stopInstances", "startInstances"):
                        count = re.search(r"\b" + field + r"=([0-9]{1,8})(?=,|\s|$)", message)
                        if count:
                            observed[field] = int(count[1])
                    launcher_events.append(observed)
                if not re.search(r"connect|Update state|Failed|ERROR|nack|full unit status|delta unit status", message, re.I):
                    continue
                entry.update(module=stage[1], stage=stage[2])
                phase = re.search(r"\bstate=([a-zA-Z]{1,32})", message)
                if phase:
                    entry["phase"] = phase[1]
            label = entry["stage"] + ":" + entry.get("payload", {}).get("messageType", "")
            counts[label] = counts.get(label, 0) + 1
            latest[label] = entry
            if entry.get("payload", {}).get("messageType") not in ("monitoringData", "ack"):
                events.append(entry)
        for entry in events:
            if entry.get("txn") in responses and entry.get("stage") == "Sent message":
                entry["response"] = responses[entry["txn"]]
        result["journal"] = dict(state="CURRENT", records=len(lines), limitReached=len(lines) >= 30000,
            firstTime=json.loads(lines[0]).get("__REALTIME_TIMESTAMP") if lines else None,
            lastTime=json.loads(lines[-1]).get("__REALTIME_TIMESTAMP") if lines else None,
            counts=counts, latest=list(latest.values()), events=events[-100:])
        result["launcherEvents"] = launcher_events[:120]
    try:
        import sqlite3
        root = proc / str(pid) / "root"
        config = json.loads((root / "etc/aos/cm.cfg").read_text())
        from urllib.parse import urlsplit
        discovery = urlsplit(config.get("serviceDiscoveryUrl", ""))
        hostname = discovery.hostname or ""
        result["cloudEndpoint"] = dict(
            host=hostname if re.fullmatch(r"[a-z0-9.-]{1,253}", hostname) else "UNAVAILABLE",
            https=discovery.scheme == "https",
            runtimeProjectionPresent=(root / "run/democtl-cloud/cm.cfg").is_file())
        directory = config.get("workingDir", "")
        if not isinstance(directory, str) or not directory.startswith("/var/aos/") or ".." in Path(directory).parts:
            raise ValueError("UNSUPPORTED_CM_WORKING_DIRECTORY")
        database = root / directory.lstrip("/") / "cm.db"
        with sqlite3.connect(database.as_uri() + "?mode=ro", uri=True, timeout=1) as connection:
            row = connection.execute("SELECT updateState, desiredStatus FROM updatemanager LIMIT 1").fetchone()
            result["launcherStorage"] = {}
            for table, columns in (
                    ("launcher_run_requests", ("itemID", "type", "version", "subjectType", "isUnitSubject", "numInstances")),
                    ("launcher_instances", ("itemID", "type", "version", "subjectType", "isUnitSubject", "state", "preinstalled"))):
                try:
                    rows = connection.execute("SELECT " + ",".join(columns) + " FROM " + table + " LIMIT 129").fetchall()
                    result["launcherStorage"][table] = dict(truncated=len(rows) > 128, rows=[
                        {key: value if isinstance(value, (int, bool)) or (isinstance(value, str)
                            and re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", value)) else "UNAVAILABLE"
                         for key, value in zip(columns, values)} for values in rows[:128]])
                except sqlite3.Error:
                    result["launcherStorage"][table] = dict(state="UNAVAILABLE")
        result["storedDesired"] = dict(state=row[0] if re.fullmatch(r"[A-Za-z]{1,40}", row[0] or "") else "UNKNOWN",
            payload=cm_payload_observation(json.loads(row[1]))) if row else dict(state="EMPTY")
        result["wireLogConfigured"] = bool(config.get("cloudMessageLog"))
    except ImportError:
        result["storedDesired"] = dict(state="SQLITE_READER_UNAVAILABLE")
    except (OSError, ValueError, sqlite3.Error):
        result["storedDesired"] = dict(state="UNAVAILABLE")
    return result


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
        telemetry = dict(state="PROCESS_UNAVAILABLE")
        if pid.isdigit() and int(pid) > 0 and (proc / pid).is_dir():
            token_root = proc / pid / "root/run/aosedge/secrets/kuksa"
            tokens = []
            if token_root.is_dir():
                for session in list(token_root.iterdir())[:16]:
                    if not session.name.startswith("session-") or session.is_symlink() or not session.is_dir():
                        continue
                    token = session / "token.jwt"
                    if token.exists() or token.is_symlink():
                        info = token.lstat()
                        tokens.append(dict(regular=stat.S_ISREG(info.st_mode), uid=info.st_uid,
                            mode=oct(stat.S_IMODE(info.st_mode)), modifiedEpoch=int(info.st_mtime)))
            children_file = proc / pid / "task" / pid / "children"
            children = children_file.read_text().split() if children_file.is_file() else []
            pids = [pid] + [child for child in children[:8] if child.isdigit()]
            uid = process.get("user", {}).get("uid")
            # Namespace-visible children may be owned by another thread.
            # Match this native UID and our exact executable names only.
            if type(uid) is int and uid > 0:
                names = {teams[0] + "-health-bootstrap", teams[0] + "-health-service"}
                for candidate in list(proc.iterdir())[:4096]:
                    if not candidate.name.isdigit() or candidate.name in pids:
                        continue
                    try:
                        fields = dict(line.split(":", 1) for line in (candidate / "status").read_text().splitlines() if ":" in line)
                        if int(fields.get("Uid", "-1").split()[0]) == uid and Path(os.readlink(candidate / "exe")).name in names:
                            pids.append(candidate.name)
                    except (OSError, ValueError):
                        continue
                    if len(pids) >= 16:
                        break
            process_facts = []
            for child in pids:
                try:
                    raw_status = (proc / child / "status").read_text()
                    fields = dict(line.split(":", 1) for line in raw_status.splitlines() if ":" in line)
                    process_facts.append({key: fields[key].strip() for key in ("Name", "State", "Threads", "VmRSS") if key in fields})
                except OSError:
                    pass
            transport = dict(state="NOT_PROBED")
            # Credential-free TLS only, from the same network namespace.
            # This is not a service-identity or authorized RPC success claim.
            ca_index = args.index("--ca-file") + 1 if "--ca-file" in args else len(args)
            ca_path = args[ca_index] if ca_index < len(args) else ""
            if ca_path.startswith("/run/aosedge/platform/service-inputs/") and ".." not in Path(ca_path).parts:
                ca = proc / pid / "root" / ca_path.lstrip("/")
                probe = """import ctypes, json, os, socket, ssl, sys
result = {"state": "FAILED", "stage": "namespace", "serviceIdentity": False}
try:
    fd = os.open('/proc/' + sys.argv[2] + '/ns/net', os.O_RDONLY)
    try:
        libc = ctypes.CDLL(None, use_errno=True)
        if libc.setns(fd, 0x40000000):
            raise OSError(ctypes.get_errno(), 'namespace unavailable')
    finally:
        os.close(fd)
    result['stage'] = 'trust'
    context = ssl.create_default_context(cafile=sys.argv[1])
    result['stage'] = 'tcp'
    with socket.create_connection(('10.0.0.100', 55555), timeout=2) as raw:
        result['stage'] = 'tls'
        with context.wrap_socket(raw, server_hostname='Server'):
            result.update(state='TLS_VERIFIED', stage='complete')
except Exception as error:
    result['errorType'] = type(error).__name__
    if isinstance(error, ssl.SSLCertVerificationError):
        result['verifyCode'] = error.verify_code
    elif isinstance(error, OSError):
        result['errno'] = error.errno
print(json.dumps(result))
"""
                checked = command(["/usr/bin/python3", "-c", probe, str(ca), pid])
                if checked.returncode == 0:
                    transport = json.loads(checked.stdout)
                else:
                    transport = dict(state="PROBE_UNAVAILABLE", returnCode=checked.returncode)
            filters = ["_PID=" + child for child in pids]
            uid = process.get("user", {}).get("uid")
            if type(uid) is int and uid > 0:
                # The native service UID changes on update. Do not mix old
                # release outcomes into the current instance observation.
                filters += ["+", "_EXE=/usr/bin/" + teams[0] + "-health-service", "_UID=" + str(uid)]
            logs = command(["journalctl", "-b", "-n", "200", "-o", "json", "--no-pager", *filters])
            events = []
            failures = {key: 0 for key in ("pthread_create failed", "Could not create", "Resource temporarily unavailable",
                "bad_alloc", "Cannot allocate memory", "std::system_error")}
            if logs.returncode == 0 and len(logs.stdout) <= 1048576:
                for line in logs.stdout.splitlines():
                    try:
                        record = json.loads(line)
                        message = record.get("MESSAGE", "")
                        if isinstance(message, str):
                            for key in failures:
                                failures[key] += message.count(key)
                        event = json.loads(message)
                    except (ValueError, TypeError):
                        continue
                    if not isinstance(event, dict) or event.get("eventType") not in (
                            "KUKSA_AUTH_CHANGED", "KUKSA_CONNECTION_CHANGED", "KUKSA_SUBSCRIPTION_CHANGED", "BACKEND_SYNC_CHANGED",
                            "READINESS_CHANGED", "WINDOW_TRIGGERED", "WINDOW_COMPLETED", "SERVICE_STARTED", "SERVICE_STOPPED",
                            "VDP_CONTRACT_ACCEPTED", "KUKSA_INPUT_REJECTED", "KUKSA_INPUT_TIMING", "ASSESSMENT_CREATED",
                            "ADVISORY_REQUESTED", "ADVISORY_GATEWAY_STATUS",
                            "EXERCISE_COMPLETED", "EXERCISE_SKIPPED",
                            "ASSESSMENT_SKIPPED_INPUT_QUALITY", "CONDITION_BAND_CHANGED", "DERIVED_OUTBOX_FULL"):
                        continue
                    fields = {key: value for key, value in event.items() if key in ("eventType", "currentState", "reasonCode")
                        and isinstance(value, str) and re.fullmatch(r"[A-Z0-9_]{1,64}", value)}
                    timestamp = record.get("__REALTIME_TIMESTAMP", "")
                    if isinstance(timestamp, str) and re.fullmatch(r"[0-9]{1,20}", timestamp):
                        fields["observedEpochMicros"] = timestamp
                    events.append(fields)
            cgroup = {}
            try:
                for line in (proc / pid / "cgroup").read_text().splitlines():
                    hierarchy, controllers, relative = line.split(":", 2)
                    if not re.fullmatch(r"/[A-Za-z0-9_./:-]{1,512}", relative) or ".." in Path(relative).parts:
                        continue
                    names = ("pids.current", "pids.max", "pids.events", "memory.current", "memory.events") if hierarchy == "0" else (
                        ("pids.current", "pids.max", "pids.events") if controllers == "pids" else ())
                    cgroot = Path("/sys/fs/cgroup") / ("" if hierarchy == "0" else "pids") / relative.lstrip("/")
                    for name in names:
                        try:
                            text = (cgroot / name).read_text().strip()
                        except OSError:
                            continue
                        if len(text) <= 1024 and re.fullmatch(r"[a-z0-9_ \n]+", text):
                            cgroup[name] = text
            except (OSError, ValueError):
                pass
            telemetry = dict(state="OBSERVED", tokens=tokens, processes=process_facts, transport=transport, events=events[-20:],
                runtimeFailureCounts=failures, cgroup=cgroup,
                modelEvents=[event for event in events if event.get("eventType") in (
                    "ASSESSMENT_CREATED", "ASSESSMENT_SKIPPED_INPUT_QUALITY", "CONDITION_BAND_CHANGED", "DERIVED_OUTBOX_FULL",
                    "EXERCISE_COMPLETED", "EXERCISE_SKIPPED")][-8:],
                inputTiming=[event for event in events if event.get("eventType")=="KUKSA_INPUT_TIMING"][-8:],
                inputRejections=[event for event in events if event.get("eventType")=="KUKSA_INPUT_REJECTED"][-8:],
                captureEvents=[event for event in events if event.get("eventType") in ("WINDOW_TRIGGERED", "WINDOW_COMPLETED")][-8:],
                advisoryEvents=[event for event in events if event.get("eventType") in ("ADVISORY_REQUESTED", "ADVISORY_GATEWAY_STATUS")][-8:],
                journalState="CURRENT" if logs.returncode == 0 else "UNAVAILABLE")
        rows.append(dict(team=teams[0], containerId=entry.name,
            argumentCount=len(args), executable=args[0],
            nativeEnvPresent={key: key in env for key in (
                "AOS_ITEM_ID", "AOS_SUBJECT_ID", "AOS_INSTANCE_INDEX", "AOS_INSTANCE_ID", "AOS_SECRET")},
            rlimits=[{key: row.get(key) for key in ("type", "soft", "hard")}
                for row in process.get("rlimits", [])],
            user={key: process.get("user", {}).get(key) for key in ("uid", "gid", "additionalGids")},
            linuxResources=config.get("linux", {}).get("resources"),
            processAlive=pid.isdigit() and int(pid) > 0 and (proc / pid).is_dir(), telemetry=telemetry))
    return dict(state="CURRENT", runtimeDir=directory, containers=rows)


def advisory_schema_observation(lookup):
    """Read six fixed contract leaves, without adding schema or authority."""
    rows = []
    for team in ("BrakeHealth", "TireHealth"):
        for leaf, expected_type in (("Request", "actuator"), ("GatewayStatus", "sensor"), ("Readiness", "actuator")):
            name = "Vehicle.OEM." + team + ".Advisory." + leaf
            value = lookup(name)
            present = isinstance(value, dict)
            rows.append(dict(path=name, present=present,
                type=value.get("type") if present else None,
                datatype=value.get("datatype") if present else None,
                matchesContract=present and value.get("type") == expected_type and value.get("datatype") == "string"))
    return dict(leaves=rows, matchesContract=all(row["matchesContract"] for row in rows),
        permissionProbe="NOT_PERFORMED", transportProbe="NOT_PERFORMED")


def vss_supplement(schema, *, advisory=True, readiness=True):
    """Append fixed V3 telemetry and D4-008 leaves; never grant permissions."""
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
    for name, kind in VSS_ADVISORY_TYPES if advisory else ():
        if not readiness and name.endswith(".Readiness"):
            continue
        current = result
        parts = name.split(".")
        for part in parts[:-1]:
            branch = current.setdefault(part, dict(type="branch", description=part, children={}))
            if not isinstance(branch, dict) or branch.get("type") != "branch" or not isinstance(branch.get("children"), dict):
                raise ValueError("COMPONENT_VSS_BRANCH_CONFLICT")
            current = branch["children"]
        expected = dict(type=kind, datatype="string", description="Typed D4-008 QM advisory " + parts[-1] + ".")
        old = current.get(parts[-1])
        if old is not None and (not isinstance(old, dict) or old.get("type") != kind or old.get("datatype") != "string"):
            raise ValueError("COMPONENT_VSS_LEAF_CONFLICT")
        current.setdefault(parts[-1], expected)
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
    if request.get("target") != "test" or tuple(request.get("additionalPaths", [])) != VSS_PROOF_PATHS:
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
    remove = request["action"] == "component-schema-remove"
    if VSS_TEMP.exists() and VSS_TEMP.read_bytes() != expected:
        legacy = (json.dumps(vss_supplement(json.loads(base), advisory=False), sort_keys=True) + "\n").encode()
        previous = (json.dumps(vss_supplement(json.loads(base), readiness=False), sort_keys=True) + "\n").encode()
        if not (remove and present and VSS_TEMP.read_bytes() in (legacy, previous)):
            raise ValueError("COMPONENT_VSS_CONTENT_CONFLICT")
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
        observed = execute(dict(request, action="component-diagnose", readPaths=list(VSS_PROOF_PATHS)))
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
    return dict(result, state="APPLIED", schemaSha256=expected_sha, servicePid=pid, addedPaths=list(VSS_PROOF_PATHS))


def command(args, **kwargs):
    return subprocess.run(args, capture_output=True, text=True, timeout=8, **kwargs)


def kuksa_authorization_observation():
    """Fixed read-only startup evidence; never credential or journal payloads."""
    import shutil
    units = ("aos-kuksa-substrate.target", "aos-kuksa-tls-prepare.service",
             "aos-kuksa-verifier-prepare.service", "aos-kuksa-provider-prepare.service",
             "aos-kuksa-auth-compat.service", "kuksa-databroker.service",
             "systemd-timesyncd.service", "systemd-time-wait-sync.service")
    properties = ("Id", "LoadState", "ActiveState", "SubState", "Result", "MainPID",
                  "NRestarts", "ExecMainCode", "ExecMainStatus", "ConditionResult", "ConditionTimestampMonotonic",
                  "ActiveEnterTimestampMonotonic", "InactiveEnterTimestampMonotonic")
    response = command(["systemctl", "show", *units, "--property=" + ",".join(properties)])
    services = {}
    if len(response.stdout) <= 65536:
        for block in response.stdout.split("\n\n"):
            row = dict(line.split("=", 1) for line in block.splitlines() if "=" in line)
            if row.get("Id") in units:
                services[row["Id"]] = {key: value for key, value in row.items()
                    if key in properties and re.fullmatch(r"[A-Za-z0-9_.@:-]{0,128}", value)}
    inputs = {}
    for name, path in (("provisioned", "/var/aos/.provisionstate"),
                       ("timeSynchronized", "/run/systemd/timesync/synchronized"),
                       ("signingPin", "/var/aos/iam/.kuksa-jwt-pin"),
                       ("verifier", "/run/aos-kuksa-verifier/kuksa-jwt-public.pem"),
                       ("requestDirectory", "/run/aos-kuksa-auth-compat"),
                       ("requestSocket", "/run/aos-kuksa-auth-compat/request.sock")):
        try:
            info = Path(path).lstat()
            inputs[name] = dict(present=True, uid=info.st_uid, gid=info.st_gid,
                mode=oct(stat.S_IMODE(info.st_mode)), symlink=stat.S_ISLNK(info.st_mode), modifiedEpoch=int(info.st_mtime))
        except FileNotFoundError:
            inputs[name] = dict(present=False)
    args = ["journalctl", "-b", "-n", "400", "-o", "json", "--no-pager"]
    for unit in units:
        args += ["-u", unit]
    journal = command(args)
    events, records = [], 0
    if journal.returncode == 0 and len(journal.stdout) <= 2097152:
        for line in journal.stdout.splitlines():
            try:
                record = json.loads(line)
            except ValueError:
                continue
            records += 1
            message = record.get("MESSAGE")
            unit = record.get("UNIT") or record.get("_SYSTEMD_UNIT")
            if unit not in units or not isinstance(message, str):
                continue
            match = re.fullmatch(r"(?:aos-kuksa-auth-compat: startup|aos-kuksa-verifier-prepare:|verifier-prepare:|provider-prepare:) ?stage=([a-z0-9-]{1,48})(?: failed errno=([0-9]{1,5})| rv=(0x[0-9a-f]{1,16})| result=([0-9]{1,3}))?", message)
            skipped = "condition" in message.lower() and "skipped" in message.lower()
            failed_step = re.search(r'Failed at step ([A-Z_]+) spawning', message)
            systemd_exit = re.search(r'status=([0-9]{1,3})/([A-Z_]+)', message)
            if failed_step or systemd_exit:
                events.append(dict(unit=unit, time=record.get("__REALTIME_TIMESTAMP"),
                    stage="systemd-" + (failed_step[1] if failed_step else systemd_exit[2]).lower(),
                    result=int(systemd_exit[1]) if systemd_exit else None))
            if match or skipped:
                stamp = record.get("__REALTIME_TIMESTAMP", "")
                events.append(dict(unit=unit, time=stamp if re.fullmatch(r"[0-9]{1,20}", stamp) else None,
                    context=record.get("_SELINUX_CONTEXT") if re.fullmatch(r'[A-Za-z0-9_:,.-]{1,160}', str(record.get("_SELINUX_CONTEXT", ""))) else None,
                    stage=match[1] if match else "condition-skipped",
                    errno=int(match[2]) if match and match[2] else None, rv=match[3] if match else None,
                    result=int(match[4]) if match and match[4] else None))
    status = dict(state="SOCKET_ABSENT")
    time_access = {}
    kac_pid = services.get("aos-kuksa-auth-compat.service", {}).get("MainPID", "0")
    if kac_pid.isdigit() and int(kac_pid) > 0:
        process_root = Path("/proc") / kac_pid
        time_access["process"] = dict(fdCount=len(list((process_root / "fd").iterdir())),
            context=(process_root / "attr/current").read_text().strip().strip("\0"))
        time_access["tools"] = {name: bool(shutil.which(name)) for name in ("sesearch", "checkmodule", "semodule_package", "semodule", "checkpolicy", "strace")}
        policy_type = next((line.split("=", 1)[1].strip() for line in Path("/etc/selinux/config").read_text().splitlines()
            if line.startswith("SELINUXTYPE=")), "")
        if re.fullmatch(r"[a-z]{1,32}", policy_type):
            time_access["policyType"] = policy_type
            time_access["policyPaths"] = {path: dict(present=Path(path).exists(), symlink=Path(path).is_symlink())
                for path in ("/var/lib/selinux/" + policy_type, "/etc/selinux/" + policy_type)}
        if shutil.which("sesearch"):
            policy = command(["sesearch", "-A", "-s", "aos_kuksa_auth_compat_t", "-t", "ntpd_pid_t"])
            time_access["policy"] = dict(returnCode=policy.returncode,
                rules=[line.strip() for line in policy.stdout.splitlines() if re.fullmatch(r"allow [a-z0-9_ :{};]+", line.strip())][:20])
        proof_root = Path("/run/democtl-kac-time-read-proof")
        if proof_root.is_dir() and not proof_root.is_symlink():
            listed = command(["semodule", "-p", str(proof_root), "-S", "/var/lib/selinux", "-s", "aos", "-l"])
            time_access["proofStore"] = dict(returnCode=listed.returncode, diagnostic=listed.stderr[:2048],
                originalPolicyMatches=hashlib.sha256((proof_root / "original.policy").read_bytes()).hexdigest() ==
                    hashlib.sha256(Path("/sys/fs/selinux/policy").read_bytes()).hexdigest(),
                canonicalPolicyMatchesOriginal=hashlib.sha256(Path("/etc/selinux/aos/policy/policy.33").read_bytes()).hexdigest() ==
                    hashlib.sha256((proof_root / "original.policy").read_bytes()).hexdigest(),
                candidateSha256=hashlib.sha256((proof_root / "etc/selinux/aos/policy/policy.33").read_bytes()).hexdigest(),
                files=[str(path.relative_to(proof_root)) for path in proof_root.glob("etc/selinux/aos/policy/*")])
        for name, suffix in (("runSystemd", "run/systemd"), ("timesync", "run/systemd/timesync"),
                             ("synchronized", "run/systemd/timesync/synchronized")):
            path = Path("/proc") / kac_pid / "root" / suffix
            try:
                info = path.stat()
                time_access[name] = dict(present=True, uid=info.st_uid, gid=info.st_gid, mode=oct(stat.S_IMODE(info.st_mode)))
                try:
                    time_access[name]["context"] = os.getxattr(path, "security.selinux").decode().strip("\0")
                except OSError:
                    pass
            except OSError as error:
                time_access[name] = dict(present=False, errno=error.errno)
    if inputs["requestSocket"].get("present"):
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
                client.settimeout(3)
                client.connect("/run/aos-kuksa-auth-compat/request.sock")
                client.sendall(b'{"protocol":"aos-kuksa-auth-compat/v1","operation":"status"}\n')
                raw = b""
                while len(raw) <= 32768 and not raw.endswith(b"\n"):
                    part = client.recv(4096)
                    if not part:
                        break
                    raw += part
                payload = json.loads(raw) if len(raw) <= 32768 else {}
                status = {key: value for key, value in payload.items() if key in ("status", "code", "retryable")
                    and (type(value) is bool or isinstance(value, str) and re.fullmatch(r"[A-Za-z_]{1,64}", value))}
        except (OSError, ValueError, TypeError):
            status = dict(state="UNAVAILABLE")
    kernel = command(["journalctl", "-k", "-b", "-n", "600", "--no-pager", "-o", "json"])
    provider_denials = []
    for line in kernel.stdout.splitlines() if kernel.returncode == 0 else []:
        record = json.loads(line)
        message = str(record.get("MESSAGE", ""))
        if "avc:" not in message or "denied" not in message:
            continue
        fields = {key: (match[1] if (match := re.search(key + r'=([^\s]+)', message)) else None)
            for key in ("scontext", "tcontext", "tclass", "permissive")}
        permission = re.search(r'denied\s+\{([a-z_ ]+)\}', message)
        provider_denials.append(dict(time=record.get("__REALTIME_TIMESTAMP"),
            permissions=permission[1].strip().split() if permission else [], **fields))
    proof = {}
    for name, path in (("binary", Path("/run/democtl-provider-readiness/exec/aos-kuksa-provider-prepare")),
            ("receipt", Path("/run/democtl-provider-readiness/receipt.json")),
            ("dropin", Path("/run/systemd/system/aos-kuksa-provider-prepare.service.d/97-democtl-readiness.conf"))):
        try:
            info = path.lstat()
            proof[name] = dict(present=True, symlink=stat.S_ISLNK(info.st_mode),
                sha256=hashlib.sha256(path.read_bytes()).hexdigest() if stat.S_ISREG(info.st_mode) else None)
        except OSError as error:
            proof[name] = dict(present=False if isinstance(error, FileNotFoundError) else None,
                sha256=None, errno=error.errno)
    provider_unit = command(["systemctl", "show", "aos-kuksa-provider-prepare", "--property=ExecStart,DropInPaths,SELinuxContext,MemoryDenyWriteExecute,NoNewPrivileges"])
    provider_config = {key: value for line in provider_unit.stdout.splitlines() if "=" in line
        for key, value in [line.split("=", 1)]
        if key in ("ExecStart", "DropInPaths", "SELinuxContext", "MemoryDenyWriteExecute", "NoNewPrivileges")}
    # ExecStart arguments are not exposed: only the configured executable.
    configured_exec = re.search(r'path=([^ ;]+)', provider_config.pop("ExecStart", ""))
    provider_config["executable"] = configured_exec[1] if configured_exec else None
    try:
        installed_provider = Path("/usr/libexec/aos-kuksa-provider-prepare").read_bytes()
        provider_config["installedSha256"] = hashlib.sha256(installed_provider).hexdigest()
        provider_config["installedInterfaces"] = {name: name.encode() in installed_provider
            for name in ("OSSL_STORE_load", "OSSL_STORE_close", "C_GetFunctionList")}
    except OSError:
        provider_config["installedSha256"] = None
    provider_config["executionFiles"] = {}
    for name, path in (("installed", Path("/usr/libexec/aos-kuksa-provider-prepare")),
            ("staged", Path("/run/democtl-provider-readiness/exec/aos-kuksa-provider-prepare"))):
        try:
            info = path.stat()
            provider_config["executionFiles"][name] = dict(uid=info.st_uid, gid=info.st_gid,
                mode=oct(stat.S_IMODE(info.st_mode)), size=info.st_size,
                context=os.getxattr(path, "security.selinux").decode().strip("\0"),
                hasFileCapabilities="security.capability" in os.listxattr(path),
                mountOptions=command(["findmnt", "-n", "-o", "OPTIONS", "-T", str(path)]).stdout.strip())
        except OSError:
            provider_config["executionFiles"][name] = dict(state="UNAVAILABLE")
    mount_options = command(["findmnt", "-n", "-o", "OPTIONS", "-T", "/var/aos/workdirs"]).stdout.strip()
    provider_config["stateStoreMountOptions"] = mount_options if re.fullmatch(r"[A-Za-z0-9_,:=.-]{1,512}", mount_options) else "UNAVAILABLE"
    return dict(mutation=False, state="CURRENT" if response.returncode == 0 and len(services) == len(units) else "INCOMPLETE",
        providerConfiguration=provider_config,
        providerDenials=provider_denials[-20:],
        protocolStatus=status,
        timeAccess=time_access, clockSample=dict(realtime=time.time(),
            boottime=time.clock_gettime(time.CLOCK_BOOTTIME) if hasattr(time, "CLOCK_BOOTTIME") else None),
        services=services, inputs=inputs, startupEvents=events[-30:], journalRecords=records,
        providerReadinessProof=proof,
        journalState="CURRENT" if journal.returncode == 0 and len(journal.stdout) <= 2097152 else "UNAVAILABLE")


def activate_kac(request):
    """One unchanged KAC start on the bound Test; no repair of prerequisites."""
    vehicle = request.get("vehicle", {})
    if (request.get("role") != "test" or not vehicle.get("unitId") or os.geteuid() != 0
            or Path("/etc/machine-id").read_text().strip() != vehicle.get("systemUid")):
        raise ValueError("KAC_CURRENT_TEST_IDENTITY_REQUIRED")
    before = kuksa_authorization_observation()
    unit = "aos-kuksa-auth-compat.service"
    props = before.get("services", {}).get(unit, {})
    if props.get("ActiveState") == "active":
        return dict(state="ACTIVE", noOp=True, observation=before)
    if (before.get("state") != "CURRENT" or props.get("ActiveState") != "inactive"
            or props.get("MainPID") != "0" or props.get("NRestarts") != "0"):
        raise ValueError("KAC_START_REQUIRES_INACTIVE_NEVER_RETRIED_UNIT")
    for name in ("provisioned", "signingPin", "verifier", "requestDirectory"):
        if not before["inputs"][name].get("present") or before["inputs"][name].get("symlink"):
            raise ValueError("KAC_START_PREREQUISITE_MISSING")
    if (before["services"]["aos-kuksa-verifier-prepare.service"].get("ActiveState") != "active"
            or command(["systemctl", "is-active", "--quiet", "aos-iam.service"]).returncode):
        raise ValueError("KAC_START_DEPENDENCY_NOT_ACTIVE")
    started = command(["systemctl", "start", unit])
    after = kuksa_authorization_observation()
    active = started.returncode == 0 and after["services"].get(unit, {}).get("ActiveState") == "active"
    return dict(state="ACTIVE" if active else "INCOMPLETE", noOp=False,
        startReturnCode=started.returncode, observation=after)


KAC_TIME_READ_CIL = """(allow aos_kuksa_auth_compat_t ntpd_pid_t (dir (getattr search)))
(allow aos_kuksa_auth_compat_t ntpd_pid_t (file (getattr open read)))
"""


def kac_time_policy_delta(text):
    """Accept only the two reviewed additive rules, no other semantic diff."""
    rules = set()
    for line in text.splitlines():
        line = line.strip()
        if not line or re.fullmatch(r"allow(?: rules)?: 2 added, 0 removed, 0 modified", line, re.I):
            continue
        match = re.fullmatch(r"\+ allow aos_kuksa_auth_compat_t ntpd_pid_t:(dir|file) \{ ([a-z ]+) \};", line)
        if not match:
            return False
        rules.add((match[1], frozenset(match[2].split())))
    return rules == {("dir", frozenset(("getattr", "search"))), ("file", frozenset(("getattr", "open", "read")))}


def kac_policy_structure(path):
    """Compare native statements without expanding attribute-rule products.

    Include attribute membership, permissive flags and condition branches;
    identical names or counts alone are not a policy equivalence proof.
    """
    from collections import Counter
    from setools import SELinuxPolicy
    policy = SELinuxPolicy(str(path))
    result = {}
    for name in ("bools", "bounds", "categories", "classes", "commons", "conditionals",
                 "constraints", "defaults", "devicetreecons", "fs_uses", "genfscons",
                 "ibendportcons", "ibpkeycons", "initialsids", "iomemcons", "ioportcons",
                 "levels", "mlsrules", "netifcons", "nodecons", "pcidevicecons", "pirqcons",
                 "polcaps", "portcons", "rbacrules", "roles", "sensitivities", "terules",
                 "typeattributes", "types", "users"):
        rows = Counter()
        for item in getattr(policy, name)():
            try:
                # A conditional is an expression, not a policy declaration.
                text = str(item) if name == "conditionals" else item.statement()
            except Exception as error:
                raise ValueError(name + ":" + type(error).__name__) from None
            if name == "typeattributes":
                text += " members=" + ",".join(sorted(str(value) for value in item.expand()))
            elif name == "types":
                text += " permissive=" + str(item.ispermissive)
            rows[text] += 1
        result[name] = rows
    result["properties"] = {name: str(getattr(policy, name)) for name in
        ("version", "mls", "handle_unknown", "target_platform")}
    return result


def kac_policy_structure_delta(before, after):
    changed = [name for name in sorted(set(before) | set(after)) if before.get(name) != after.get(name)]
    if changed != ["terules"]:
        return dict(exact=False, changedCategories=changed)
    added, removed = after["terules"] - before["terules"], before["terules"] - after["terules"]
    exact = not removed and sum(added.values()) == 2 and kac_time_policy_delta(
        "\n".join("+ " + rule for rule in added))
    return dict(exact=exact, changedCategories=changed, addedCount=sum(added.values()),
        removedCount=sum(removed.values()), addedRules=list(added)[:4], removedRules=list(removed)[:4])


def arm_kac_policy_rollback(original, load_path, timeout=75, *, leased_policy=False, active_path="/sys/fs/selinux/policy"):
    """Child inherits the proven loader context; EOF/timeout restores stock.

    No systemd exec/domain transition, shell helper, persistent unit or secret.
    The parent disarms only after restoring and checking the original hash.
    """
    import select
    import signal
    read_fd, write_fd = os.pipe()
    pid = os.fork()
    if pid:
        os.close(read_fd)
        return pid, write_fd
    os.close(write_fd)
    try:
        os.setsid()
        signal.signal(signal.SIGHUP, signal.SIG_IGN)
        null = os.open(os.devnull, os.O_RDWR)
        for fd in (0, 1, 2):
            os.dup2(null, fd)
        os.close(null)
        deadline = time.monotonic() + timeout
        available, _, _ = select.select([read_fd], [], [], timeout)
        response = os.read(read_fd, 1) if available else b""
        if response == b"L" and leased_policy:
            expected_sha = os.read(read_fd, 64).decode("ascii")
            if not re.fullmatch(r"[0-9a-f]{64}", expected_sha):
                Path(load_path).write_bytes(original)
                os._exit(1)
            time.sleep(max(0, deadline - time.monotonic()))
            # Do not overwrite a later independently installed policy.
            if hashlib.sha256(Path(active_path).read_bytes()).hexdigest() != expected_sha:
                os._exit(0)
        if response != b"R":
            Path(load_path).write_bytes(original)
    except BaseException:
        os._exit(1)
    os._exit(0)


def kac_recovery(request, *, remove=False):
    """Reuse the exact proven policy for this disposable Test, with a lease.

    Separate from the completed short proofs: no canonical policy store,
    rootfs, manager executable, token lifetime or access scope is changed.
    """
    if (request.get("role") != "test" or os.geteuid() != 0
            or request.get("vehicle", {}).get("unitId") != "42c0bf43-4eb7-44e6-8c74-f60f9959da66"
            or Path("/etc/machine-id").read_text().strip() != request["vehicle"].get("systemUid")
            or Path("/sys/fs/selinux/enforce").read_text().strip() != "1"):
        raise ValueError("KAC_RECOVERY_CURRENT_ENFORCING_TEST_REQUIRED")
    root = Path("/run/democtl-kac-time-read-proof")
    candidate_path = root / "etc/selinux/aos/policy/policy.33"
    original_path = root / "original.policy"
    for path in (candidate_path, original_path):
        if any(parent.is_symlink() for parent in (path,) + tuple(path.parents)):
            raise ValueError("KAC_RECOVERY_POLICY_SYMLINK")
        if path.stat().st_uid != 0:
            raise ValueError("KAC_RECOVERY_POLICY_OWNER")
    candidate, original = candidate_path.read_bytes(), original_path.read_bytes()
    if (hashlib.sha256(candidate).hexdigest() != "bafa843730051d517a53c2d67b4a39a87ecebeba10b77fed7eff63b28a3143c7"
            or hashlib.sha256(original).hexdigest() != "057a7caaa4c7387715af978df163bbc9551bb63033518b0e1265df17c7d61af9"):
        raise ValueError("KAC_RECOVERY_PROVEN_POLICY_MISMATCH")
    receipt = root / "recovery.json"
    if receipt.is_symlink():
        raise ValueError("KAC_RECOVERY_RECEIPT_SYMLINK")
    active = Path("/sys/fs/selinux/policy").read_bytes()
    if remove:
        if not receipt.is_file() or receipt.stat().st_uid != 0 or stat.S_IMODE(receipt.stat().st_mode) != 0o600:
            raise ValueError("KAC_RECOVERY_OWNED_RECEIPT_REQUIRED")
        record = json.loads(receipt.read_text())
        if active != original and hashlib.sha256(active).hexdigest() != record.get("activePolicySha256"):
            raise ValueError("KAC_RECOVERY_ACTIVE_POLICY_CHANGED")
        dropin = Path("/run/systemd/system/aos-vehicle-data-provider.service.d/21-democtl-kac-recovery.conf")
        content = "# democtl current-Test KAC recovery\n[Unit]\nWants=aos-kuksa-auth-compat.service\nAfter=aos-kuksa-auth-compat.service\n"
        if any(path.is_symlink() for path in (dropin,) + tuple(dropin.parents)) or (dropin.exists() and dropin.read_text() != content):
            raise ValueError("KAC_RECOVERY_DROPIN_CONFLICT")
        no_op = active == original and not dropin.exists()
        if active != original:
            Path("/sys/fs/selinux/load").write_bytes(original)
        if Path("/sys/fs/selinux/policy").read_bytes() != original:
            raise ValueError("KAC_RECOVERY_STOCK_POLICY_NOT_RESTORED")
        if dropin.exists():
            dropin.unlink()
            command(["systemctl", "daemon-reload"], check=True)
        # The leased child only restores if its candidate is still active;
        # after this rollback it cannot overwrite any later policy.
        record.update(state="RESTORED", originalPolicyRestored=True, transientDropinRemoved=True)
        write_public(receipt, record, mode=0o600)
        return dict(state="RESTORED", originalPolicyRestored=True, transientDropinRemoved=True,
            canonicalPolicyStoreChanged=False, noOp=no_op)
    if receipt.exists() and hashlib.sha256(active).hexdigest() == json.loads(receipt.read_text()).get("activePolicySha256"):
        record = json.loads(receipt.read_text())
        if record["deadlineEpoch"] <= time.time():
            raise ValueError("KAC_RECOVERY_LEASE_EXPIRED")
        os.kill(record["rollbackPid"], 0)
        return dict(record, noOp=True, authorization=kuksa_authorization_observation())
    if active != original:
        raise ValueError("KAC_RECOVERY_ACTIVE_POLICY_CHANGED")
    dropin = Path("/run/systemd/system/aos-vehicle-data-provider.service.d/21-democtl-kac-recovery.conf")
    content = "# democtl current-Test KAC recovery\n[Unit]\nWants=aos-kuksa-auth-compat.service\nAfter=aos-kuksa-auth-compat.service\n"
    if any(path.is_symlink() for path in (dropin,) + tuple(dropin.parents)) or (dropin.exists() and dropin.read_text() != content):
        raise ValueError("KAC_RECOVERY_DROPIN_CONFLICT")
    changed = write_public(dropin, content)
    if changed:
        command(["systemctl", "daemon-reload"], check=True)
    load_path = Path("/sys/fs/selinux/load")
    load_path.write_bytes(original)
    pid, fd = arm_kac_policy_rollback(original, load_path, timeout=21600, leased_policy=True)
    try:
        load_path.write_bytes(candidate)
        # The kernel serializes a loaded policy differently from the compiled
        # store file. Compare policy semantics, then retain its active digest.
        diff = kac_policy_structure_delta(kac_policy_structure(original_path),
            kac_policy_structure(Path("/sys/fs/selinux/policy")))
        if not diff["exact"]:
            raise ValueError("KAC_RECOVERY_POLICY_NOT_ACTIVE")
        active_sha = hashlib.sha256(Path("/sys/fs/selinux/policy").read_bytes()).hexdigest()
        activation = activate_kac(request)
        if activation.get("state") != "ACTIVE":
            raise ValueError("KAC_RECOVERY_ACTIVATION_FAILED")
        record = dict(state="ACTIVE", deadlineEpoch=int(time.time()) + 21600,
            rollbackPid=pid, activePolicySha256=active_sha, policyDiff=diff, canonicalPolicyStoreChanged=False,
            rebootQualified=False, transientDropin=str(dropin), proofRoot=str(root))
        write_public(receipt, record, mode=0o600)
        os.write(fd, b"L" + active_sha.encode("ascii"))
    except BaseException:
        load_path.write_bytes(original)
        os.write(fd, b"R")
        if changed:
            dropin.unlink()
            command(["systemctl", "daemon-reload"], check=True)
        raise
    finally:
        os.close(fd)
    return dict(record, noOp=False, authorization=kuksa_authorization_observation())


def kac_time_read_proof(request):
    """Explicitly authorized current-Test policy proof, never a durable install."""
    import shutil
    if (request.get("role") != "test" or os.geteuid() != 0
            or request.get("vehicle", {}).get("unitId") != "42c0bf43-4eb7-44e6-8c74-f60f9959da66"
            or Path("/etc/machine-id").read_text().strip() != request["vehicle"].get("systemUid")):
        raise ValueError("KAC_TIME_PROOF_CURRENT_TEST_REQUIRED")
    root = Path("/run/democtl-kac-time-read-proof")
    if root.is_symlink() or Path("/sys/fs/selinux/enforce").read_text().strip() != "1":
        raise ValueError("KAC_TIME_PROOF_REQUIRES_FRESH_ENFORCING_STATE")
    before = kuksa_authorization_observation()
    if (before["timeAccess"].get("policyType") != "aos" or before["protocolStatus"].get("code") != "TIME_UNTRUSTED"
            or before["timeAccess"].get("policy") != dict(returnCode=0, rules=[])):
        raise ValueError("KAC_TIME_PROOF_BASELINE_CHANGED")
    original = Path("/sys/fs/selinux/policy").read_bytes()
    original_sha = hashlib.sha256(original).hexdigest()
    original_file = root / "original.policy"
    cil = root / "democtl_kac_time_read.cil"
    if root.exists():
        if (root.stat().st_uid != 0 or stat.S_IMODE(root.stat().st_mode) != 0o700
                or original_file.is_symlink() or cil.is_symlink() or cil.read_text() != KAC_TIME_READ_CIL
                or hashlib.sha256(original_file.read_bytes()).hexdigest() != original_sha):
            raise ValueError("KAC_TIME_PROOF_STORED_BASELINE_MISMATCH")
    else:
        root.mkdir(mode=0o700)
        original_file.write_bytes(original)
        original_file.chmod(0o600)
        # Dereference into private copies; no link can redirect store writes.
        shutil.copytree("/etc/selinux/aos", root / "etc/selinux/aos")
        shutil.copytree("/var/lib/selinux/aos", root / "var/lib/selinux/aos")
        cil.write_text(KAC_TIME_READ_CIL)
    # libsemanage prefixes store-path with the alternate root itself.
    # Only the copied store's newly-created parents need the corresponding
    # native file labels. Do not change canonical labels or grant new access.
    for source in ("/var/lib/selinux", "/etc/selinux"):
        command(["chcon", "--reference=" + source, str(root / source.lstrip("/"))], check=True)
    command(["chcon", "--reference=/var/lib/selinux/aos", str(cil)], check=True)
    candidates = list((root / "etc/selinux/aos/policy").glob("policy.*"))
    # Reuse the exact candidate produced by the previous successful compile.
    candidate_sha = "bafa843730051d517a53c2d67b4a39a87ecebeba10b77fed7eff63b28a3143c7"
    reused = len(candidates) == 1 and hashlib.sha256(candidates[0].read_bytes()).hexdigest() == candidate_sha
    if reused:
        built = subprocess.CompletedProcess([], 0, "", "")
    else:
        built = subprocess.run(["semodule", "-n", "-p", str(root), "-S", "/var/lib/selinux",
            "-s", "aos", "-i", str(cil)], capture_output=True, text=True, timeout=45)
        candidates = list((root / "etc/selinux/aos/policy").glob("policy.*"))
    unchanged = hashlib.sha256(Path("/sys/fs/selinux/policy").read_bytes()).hexdigest() == original_sha
    if built.returncode or len(candidates) != 1 or not unchanged:
        return dict(state="BUILD_FAILED", returnCode=built.returncode, activePolicyUnchanged=unchanged,
            diagnostic=built.stderr[:2048])
    try:
        diff = kac_policy_structure_delta(kac_policy_structure(original_file), kac_policy_structure(candidates[0]))
    except Exception as error:
        stage = str(error) if re.fullmatch(r"[a-z]+:[A-Za-z]+", str(error)) else None
        return dict(state="DIFF_TOOL_FAILED", errorType=type(error).__name__, stage=stage, activePolicyUnchanged=True)
    if not diff["exact"]:
        return dict(state="DIFF_REVIEW_REQUIRED", policyDiff=diff, activePolicyUnchanged=True)
    # This unchanged reload proves the current execution context can restore.
    load_path = Path("/sys/fs/selinux/load")
    load_path.write_bytes(original)
    if hashlib.sha256(Path("/sys/fs/selinux/policy").read_bytes()).hexdigest() != original_sha:
        raise ValueError("KAC_TIME_PROOF_STOCK_RELOAD_MISMATCH")
    data_proof = request["action"] == "service-kac-data-proof"
    guard_pid, guard_fd = arm_kac_policy_rollback(original, load_path, timeout=240 if data_proof else 75)
    snapshots = []
    restored = False
    try:
        load_path.write_bytes(candidates[0].read_bytes())
        for delay in ((0, 12) + (15,) * 10 if data_proof else (0, 12, 25)):
            if delay:
                time.sleep(delay)
            value = kuksa_authorization_observation()
            snapshots.append(dict(protocolStatus=value["protocolStatus"],
                service=value["services"]["aos-kuksa-auth-compat.service"]))
            if value["protocolStatus"].get("code") not in (None, "TIME_UNTRUSTED"):
                break
        sm = command(["systemctl", "show", "aos-sm", "--property=MainPID", "--value"]).stdout.strip()
        process_root = Path("/proc") / sm / "root"
        containers = container_runtime_observation(process_root, json.loads((process_root / "etc/aos/sm.cfg").read_text()))
    finally:
        load_path.write_bytes(original)
        restored = hashlib.sha256(Path("/sys/fs/selinux/policy").read_bytes()).hexdigest() == original_sha
        if restored:
            os.write(guard_fd, b"R")
        os.close(guard_fd)
        _, guard_status = os.waitpid(guard_pid, 0)
        if guard_status:
            raise ValueError("KAC_TIME_PROOF_ROLLBACK_GUARD_FAILED")
    return dict(state="PROVED" if restored and snapshots[-1]["protocolStatus"].get("status") == "ready" else "INCOMPLETE",
        snapshots=snapshots, nativeContainers=containers, originalPolicyRestored=restored,
        originalPolicySha256=original_sha, proofRoot=str(root), canonicalPolicyStoreChanged=False,
        policyDiff=diff, candidateReused=reused)


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


def probe(safe_stop=False, preprovision=False, mutual_tls=False):
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
        if mutual_tls:
            # Fixed enrolled update-runtime identity only; never a caller path,
            # anonymous fallback or a claim about the SM/VDP process itself.
            base = Path("/var/aos/iam/vehicle-state/platform-update-runtime")
            context.load_cert_chain(str(base / "client.pem"), str(base / "client-key.pem"))
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
                return {"serverTls": True, "mutualTls": mutual_tls,
                    "advancingVissFrames": True, "frames": samples}
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
    previous = observation["binarySha256"]
    dropin = Path("/run/systemd/system/aos-sm.service.d/92-democtl-sm-queued-recovery.conf")
    old_text = "[Service]\nBindReadOnlyPaths=/run/democtl-sm-queued-recovery/aos_sm_app:/usr/bin/aos_sm_app\n"
    predecessor = (previous == "cf251da44d30aec38bd015210f08e284eb121aaff8f00feca2d74b75291a3dee"
        and dropin.is_file() and dropin.read_text() == old_text)
    prepared_predecessor = (previous == "3e244f438b6f2a8b9dcd08fb4f4be80b21771278e89a0cf6706d87cdec0b2b21"
        and dropin.is_file() and dropin.read_text() ==
            "[Service]\nBindReadOnlyPaths=/run/democtl-sm-service-update/aos_sm_app:/usr/bin/aos_sm_app\n")
    rebooted_factory = (previous == "df141e0df7ed9dac6e74ef055e7b31994b501f9d26e1f34d50326c0f76839f86"
        and not dropin.exists())
    if (not (predecessor or prepared_predecessor or rebooted_factory) or observation["service"]["ActiveState"] != "active"
            or dropin.is_symlink()
            or observation["freshnessProfile"] != "demo-5s"):
        raise ValueError("SM_SERVICE_UPDATE_BASE_MISMATCH")
    runtime = FACTORY_INPUTS.parent
    saved = sm_saved_test_release(runtime, committed=True)
    with gzip.GzipFile(fileobj=io.BytesIO(base64.b64decode(request["binary"], validate=True))) as payload:
        raw = payload.read(256 * 1024 * 1024 + 1)
    if (len(raw) > 256 * 1024 * 1024 or hashlib.sha256(raw).hexdigest() != request["sha256"]
            or raw[:5] != b"\x7fELF\x02" or raw[18:20] != b"\xb7\x00"):
        raise ValueError("SM_ARM64_BINARY_SHA_MISMATCH")
    root = Path("/run/democtl-sm-service-prepare" if prepared_predecessor else "/run/democtl-sm-service-update")
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
    dropin.parent.mkdir(parents=True, exist_ok=True)
    dropin.write_text("[Service]\nBindReadOnlyPaths=" + str(binary) + ":/usr/bin/aos_sm_app\n")
    command(["systemctl", "daemon-reload"], check=True)
    subprocess.run(["systemctl", "start", "aos-sm"], capture_output=True, text=True, timeout=25, check=True)
    result = execute(dict(request, action="component-sm-status"))
    if result["binarySha256"] != request["sha256"] or result["service"]["ActiveState"] != "active":
        raise ValueError("SM_TRANSIENT_ACTIVATION_UNCONFIRMED")
    return dict(state="APPLIED", noOp=False, persistentFactoryInputs=True,
                previousBinarySha256=previous, durableRecordsPreserved=True, **dict(result, mutation=True))


def cm_startup_factory34(request):
    """Transient CM-only proof; retain native stores, configuration and peers."""
    expected = "0c491e8a744458b01bf81126f99ecdab3367795f757c419b92ab338b6518da23"
    baseline = "3fffb5b89c742c233a634246c807d74e0bbc206dc143f8222c9b8283e0d78c98"
    vehicle = request.get("vehicle", {})
    if (request.get("target") != "test" or request.get("proof") != "factory34-startup-reconcile"
            or vehicle.get("localVmId") != "363d8b2d-187f-4713-8af1-5cf9aa598177"
            or vehicle.get("unitId") != "db0f8a34-5adf-4dec-b0fb-9c4f5b15c905"
            or request.get("sha256") != expected):
        raise ValueError("CM_STARTUP_REQUIRES_PRESERVED_TEST_34")
    before = execute(dict(request, action="component-cm-status"))
    if before.get("binarySha256") != baseline or before["service"].get("ActiveState") != "active":
        raise ValueError("CM_STARTUP_FACTORY_BASE_REQUIRED")
    state_root = FACTORY_INPUTS.parent / "state"
    installed = state_root / "installed.json"
    transaction = state_root / "transaction.json"
    if (transaction.exists() or transaction.is_symlink() or installed.is_symlink()
            or not installed.is_file() or installed.stat().st_size > 131072):
        raise ValueError("CM_STARTUP_COMPONENT_TRANSACTION_OR_UNSAFE_RECORD")
    saved = installed.read_bytes()
    if json.loads(saved).get("Version") != "73.0.0":
        raise ValueError("CM_STARTUP_EXPECTED_VDP_73")
    peers_args = ["systemctl", "show", "aos-sm", "aos-vehicle-data-provider",
        "--property=Id,MainPID,ActiveState,NRestarts"]
    peers = command(peers_args, check=True).stdout
    root = Path("/run/democtl-cm-startup-20260917")
    dropin = Path("/run/systemd/system/aos-cm.service.d/96-democtl-startup-reconcile.conf")
    if root.exists() or root.is_symlink() or dropin.exists() or dropin.is_symlink():
        raise ValueError("CM_STARTUP_TRANSIENT_ALREADY_EXISTS")
    with gzip.GzipFile(fileobj=io.BytesIO(base64.b64decode(request["binary"], validate=True))) as payload:
        raw = payload.read(16 * 1024 * 1024 + 1)
    if (len(raw) > 16 * 1024 * 1024 or hashlib.sha256(raw).hexdigest() != expected
            or raw[:6] != b"\x7fELF\x02\x01" or raw[18:20] != b"\xb7\x00"):
        raise ValueError("CM_STARTUP_BINARY_DIGEST_MISMATCH")
    root.mkdir(mode=0o700)
    binary = root / "aos_cm_app"
    binary.write_bytes(raw)
    binary.chmod(0o755)
    command(["chcon", "--reference=/usr/bin/aos_cm_app", str(binary)], check=True)
    label = command(["stat", "-c", "%C", "/usr/bin/aos_cm_app"], check=True).stdout.strip()
    if command(["stat", "-c", "%u:%g:%a:%C", str(binary)], check=True).stdout.strip() != "0:0:755:" + label:
        raise ValueError("CM_STARTUP_EXECUTABLE_METADATA_MISMATCH")
    dropin.parent.mkdir(parents=True, exist_ok=True)
    dropin.write_text("[Service]\nBindReadOnlyPaths=" + str(binary) + ":/usr/bin/aos_cm_app\n")
    command(["systemctl", "daemon-reload"], check=True)
    print("Test34: one CM restart with startup reconciliation; native state and SM retained", file=sys.stderr, flush=True)
    subprocess.run(["systemctl", "restart", "aos-cm"], capture_output=True, text=True, timeout=30, check=True)
    after = execute(dict(request, action="component-cm-status"))
    if (after.get("binarySha256") != expected or after["service"].get("ActiveState") != "active"
            or after["service"].get("MainPID") == before["service"].get("MainPID")
            or after["service"].get("NRestarts") != "0"
            or command(peers_args, check=True).stdout != peers
            or transaction.exists() or transaction.is_symlink() or installed.read_bytes() != saved):
        raise ValueError("CM_STARTUP_ACTIVATION_REQUIRES_RECONCILIATION")
    return dict(state="APPLIED", mutation=True, transient=True, binarySha256=expected,
        previousBinarySha256=baseline, service=after["service"], smAndVdpPidsPreserved=True,
        durableRecordsPreserved=True, transientRoot=str(root), dropin=str(dropin),
        launcherEvents=after.get("delivery", {}).get("launcherEvents", []))


def cm_idle_refresh_factory32(request):
    """One transient, CM-only status refresh proof on the authorized .32 Test."""
    if (request.get("target") != "test" or request.get("restartCm") is not True
            or request.get("proof") != "factory32-idle-full-status"
            or request.get("vehicle", {}).get("localVmId") != "c7b8f9d8-68ea-4b65-b444-8b01595eb110"
            or request["vehicle"].get("unitId") != "d90798f6-a32c-40cc-8129-26a0f1343a67"):
        raise ValueError("CM_REFRESH_REQUIRES_CURRENT_TEST_32")
    expected = "e1f06ff8a2bce082a0825c5e4163ba7cedc14e7c0863e9c021fbe85455c1c9fd"
    if request.get("sha256") != expected:
        raise ValueError("CM_REFRESH_QUALIFIED_BINARY_REQUIRED")
    before = execute(dict(request, action="component-cm-status"))
    if (before["binarySha256"] != "85e03a5206576c71a571a46ef90345d43037ea71b2e00c77181d247be533028d"
            or before["service"]["ActiveState"] != "active"):
        raise ValueError("CM_REFRESH_STOCK_BASE_REQUIRED")
    args = (Path("/proc") / before["service"]["MainPID"] / "cmdline").read_bytes().decode().strip("\0").split("\0")
    paths = [args[i+1] for i, arg in enumerate(args[:-1]) if arg in ("-c", "--config")]
    paths += [arg.split("=",1)[1] for arg in args if arg.startswith("--config=")]
    if len(paths) != 1 or not paths[0].startswith("/etc/") or not re.fullmatch(r"/[A-Za-z0-9_./-]+", paths[0]):
        raise ValueError("CM_REFRESH_CONFIG_PATH_UNRESOLVED")
    config_path = Path(paths[0])
    original_config = config_path.read_bytes()
    effective = Path("/proc") / before["service"]["MainPID"] / "root" / str(config_path).lstrip("/")
    if effective.read_bytes() != original_config:
        raise ValueError("CM_REFRESH_EXISTING_CONFIG_OVERRIDE")
    config = json.loads(original_config)
    if config.get("idleFullStatusInterval", "0s") != "0s":
        raise ValueError("CM_REFRESH_INTERVAL_ALREADY_CONFIGURED")
    config["idleFullStatusInterval"] = "60s"
    peers = command(["systemctl", "show", "aos-sm", "aos-vehicle-data-provider",
        "--property=Id,MainPID,ActiveState,NRestarts"]).stdout
    saved = sm_saved_test_release(FACTORY_INPUTS.parent, committed=True)
    root = Path("/run/democtl-cm-idle-full-status-20260913")
    dropin = Path("/run/systemd/system/aos-cm.service.d/95-democtl-idle-full-status.conf")
    if root.exists() or root.is_symlink() or dropin.exists() or dropin.is_symlink():
        raise ValueError("CM_REFRESH_RECONCILE_TRANSIENT_STATE")
    with gzip.GzipFile(fileobj=io.BytesIO(base64.b64decode(request["binary"], validate=True))) as payload:
        raw = payload.read(16 * 1024 * 1024 + 1)
    if (len(raw) > 16 * 1024 * 1024 or hashlib.sha256(raw).hexdigest() != expected
            or raw[:6] != b"\x7fELF\x02\x01" or raw[18:20] != b"\xb7\x00"):
        raise ValueError("CM_REFRESH_BINARY_DIGEST_MISMATCH")
    root.mkdir(mode=0o700)
    binary = root / "aos_cm_app"
    binary.write_bytes(raw)
    binary.chmod(0o755)
    cfg = root / "cm.cfg"
    cfg.write_text(json.dumps(config, indent=2) + "\n")
    cfg.chmod(config_path.stat().st_mode & 0o777)
    os.chown(cfg, config_path.stat().st_uid, config_path.stat().st_gid)
    command(["chcon", "--reference=/usr/bin/aos_cm_app", str(binary)], check=True)
    command(["chcon", "--reference=" + str(config_path), str(cfg)], check=True)
    dropin.parent.mkdir(parents=True, exist_ok=True)
    dropin.write_text("[Service]\nBindReadOnlyPaths=" + str(binary) + ":/usr/bin/aos_cm_app\n"
        "BindReadOnlyPaths=" + str(cfg) + ":" + str(config_path) + "\n")
    command(["systemctl", "daemon-reload"], check=True)
    print("Test32: one CM restart; 60-second idle full status, SM/VDP unchanged", file=sys.stderr, flush=True)
    subprocess.run(["systemctl", "restart", "aos-cm"], capture_output=True, text=True, timeout=30, check=True)
    after = execute(dict(request, action="component-cm-status"))
    peers_after = command(["systemctl", "show", "aos-sm", "aos-vehicle-data-provider",
        "--property=Id,MainPID,ActiveState,NRestarts"]).stdout
    if (after["binarySha256"] != expected or after["service"]["ActiveState"] != "active"
            or before["service"]["MainPID"] == after["service"]["MainPID"]
            or peers_after != peers or sm_saved_test_release(FACTORY_INPUTS.parent, committed=True) != saved
            or config_path.read_bytes() != original_config):
        raise ValueError("CM_REFRESH_ACTIVATION_REQUIRES_RECONCILIATION")
    return dict(state="APPLIED", mutation=True, transient=True, previousPid=before["service"]["MainPID"],
        service=after["service"], binarySha256=expected, idleFullStatusInterval="60s",
        smAndVdpPidsPreserved=True, durableRecordsPreserved=True, baseConfigPreserved=True,
        transientRoot=str(root), dropin=str(dropin), configPath=str(config_path))


def cm_restart_factory32_control(request):
    """User-authorized unchanged-binary control, restricted to one current Test."""
    authorized_controls = {
        "5aa1f8e4-a111-4467-a6cc-fb269c62a7a8": "923b9820-999b-41bb-91db-b2a2c469e743",
        "c7b8f9d8-68ea-4b65-b444-8b01595eb110": "d90798f6-a32c-40cc-8129-26a0f1343a67",
    }
    if (request.get("target") != "test" or request.get("restartCm") is not True
            or request["vehicle"].get("localVmId") not in authorized_controls
            or request["vehicle"].get("unitId") != authorized_controls.get(request["vehicle"].get("localVmId"))):
        raise ValueError("CM_CONTROL_REQUIRES_AUTHORIZED_TEST_32")
    digest = "85e03a5206576c71a571a46ef90345d43037ea71b2e00c77181d247be533028d"
    before = execute(dict(request, action="component-cm-status"))
    sm = execute(dict(request, action="component-sm-status"))
    if (before.get("binarySha256") != digest or before.get("executable") != "/usr/bin/aos_cm_app"
            or before["service"]["ActiveState"] != "active"
            or sm.get("binarySha256") != "936fbd563f7e9d54651504f5aeba84fee0f3736861d30c2efb60eb564e039783"
            or sm["service"]["ActiveState"] != "active"):
        raise ValueError("CM_CONTROL_FACTORY_BINARIES_REQUIRED")
    print("Test32 CM: one restart with unchanged installed binary; SM and VM stay running", file=sys.stderr, flush=True)
    subprocess.run(["systemctl", "restart", "aos-cm"], capture_output=True, text=True, timeout=25, check=True)
    after = execute(dict(request, action="component-cm-status"))
    sm_after = execute(dict(request, action="component-sm-status"))
    if (after.get("binarySha256") != digest or after.get("executable") != before["executable"]
            or after["service"]["ActiveState"] != "active"
            or after["service"]["MainPID"] == before["service"]["MainPID"]
            or sm_after["service"]["MainPID"] != sm["service"]["MainPID"]
            or sm_after.get("binarySha256") != sm["binarySha256"]
            or sm_after["service"]["ActiveState"] != "active"):
        raise ValueError("CM_CONTROL_RESTART_UNCONFIRMED")
    return dict(state="RESTARTED", noOp=False, mutation=True, binaryUnchanged=True,
        previousPid=before["service"]["MainPID"], service=after["service"], binarySha256=digest,
        smPidPreserved=True, smPid=sm["service"]["MainPID"],
        storedDesiredBefore=before.get("delivery", {}).get("storedDesired"),
        storedDesiredAfter=after.get("delivery", {}).get("storedDesired"))


def cm_apply_service_update(request):
    """One Test CM restart; preserve SM, VDP and all native/cloud assignments."""
    if (request.get("target") != "test" or request.get("proof") != "service-snapshot-reconciliation"
            or request["vehicle"].get("localVmId") != "d53d05cd-4c46-49c9-a896-534b23b88273"
            or request["vehicle"].get("unitId") != "2a29c145-bbd1-4494-a0e5-d4b79e6a9db5"):
        raise ValueError("CM_PROOF_REQUIRES_AUTHORIZED_TEST_31")
    previous = "8432c0ca62b3b7bebf0e20f3ae3f82d412429be44fadcd00d914dbf1170f48bc"
    observation = execute(dict(request, action="component-cm-status"))
    restart = request.get("restartCm", False)
    if type(restart) is not bool:
        raise ValueError("CM_RESTART_REQUIRES_BOOLEAN")
    if observation["binarySha256"] == request["sha256"] and observation["service"]["ActiveState"] == "active":
        if not restart:
            return dict(state="APPLIED", noOp=True, **observation)
        previous = request["sha256"]
    elif restart:
        raise ValueError("CM_RESTART_REQUIRES_ALREADY_APPLIED_PATCH")
    if observation["binarySha256"] != previous or observation["service"]["ActiveState"] != "active":
        raise ValueError("CM_SERVICE_UPDATE_BASE_MISMATCH")
    sm = execute(dict(request, action="component-sm-status"))
    if (sm["binarySha256"] not in (
            "3e244f438b6f2a8b9dcd08fb4f4be80b21771278e89a0cf6706d87cdec0b2b21",
            "ae36ada2815700d751549404d5fb93f5a9e1f22890507c14da7f2df1a0c30299")
            or sm["service"]["ActiveState"] != "active"):
        raise ValueError("CM_PROOF_REQUIRES_QUALIFIED_SM_PATCH")
    saved = sm_saved_test_release(FACTORY_INPUTS.parent, committed=True)
    with gzip.GzipFile(fileobj=io.BytesIO(base64.b64decode(request["binary"], validate=True))) as payload:
        raw = payload.read(256 * 1024 * 1024 + 1)
    if (len(raw) > 256 * 1024 * 1024 or hashlib.sha256(raw).hexdigest() != request["sha256"]
            or raw[:5] != b"\x7fELF\x02" or raw[18:20] != b"\xb7\x00"):
        raise ValueError("CM_ARM64_BINARY_SHA_MISMATCH")
    root = Path("/run/democtl-cm-service-update")
    dropin = Path("/run/systemd/system/aos-cm.service.d/93-democtl-service-reconcile.conf")
    binary = root / "aos_cm_app"
    expected_dropin = "[Service]\nBindReadOnlyPaths=" + str(binary) + ":/usr/bin/aos_cm_app\n"
    if restart:
        if (root.is_symlink() or dropin.is_symlink() or binary.is_symlink()
                or not dropin.is_file() or dropin.read_text() != expected_dropin
                or not binary.is_file() or hashlib.sha256(binary.read_bytes()).hexdigest() != request["sha256"]):
            raise ValueError("CM_TRANSIENT_STATE_REQUIRES_RECONCILIATION")
    else:
        if root.exists() or root.is_symlink() or dropin.exists() or dropin.is_symlink():
            raise ValueError("CM_TRANSIENT_STATE_REQUIRES_RECONCILIATION")
        root.mkdir(mode=0o700)
        binary.write_bytes(raw)
        binary.chmod(0o755)
        command(["chcon", "--reference=/usr/bin/aos_cm_app", str(binary)], check=True)
        dropin.parent.mkdir(parents=True, exist_ok=True)
        dropin.write_text(expected_dropin)
        command(["systemctl", "daemon-reload"], check=True)
    print("Test CM: one restart with snapshot reconciliation fix; SM and native databases preserved", file=sys.stderr, flush=True)
    subprocess.run(["systemctl", "restart", "aos-cm"], capture_output=True, text=True, timeout=25, check=True)
    result = execute(dict(request, action="component-cm-status"))
    sm_after = execute(dict(request, action="component-sm-status"))
    if (result["binarySha256"] != request["sha256"] or result["service"]["ActiveState"] != "active"
            or sm_after["service"]["MainPID"] != sm["service"]["MainPID"]
            or sm_saved_test_release(FACTORY_INPUTS.parent, committed=True) != saved):
        raise ValueError("CM_TRANSIENT_ACTIVATION_UNCONFIRMED")
    return dict(state="APPLIED", noOp=False, explicitRestart=restart, previousBinarySha256=previous,
                smPidPreserved=True, durableRecordsPreserved=True, **dict(result, mutation=True))


def cm_compare_factory32(request):
    """Swap only CM under /run, with an eight-minute automatic stock rollback."""
    phase = request.get("phase")
    if (request.get("target") != "test" or phase not in ("without-patch", "restore")
            or request["vehicle"].get("localVmId") != "5aa1f8e4-a111-4467-a6cc-fb269c62a7a8"
            or request["vehicle"].get("unitId") != "923b9820-999b-41bb-91db-b2a2c469e743"):
        raise ValueError("CM_COMPARISON_REQUIRES_AUTHORIZED_TEST_32")
    original = "85e03a5206576c71a571a46ef90345d43037ea71b2e00c77181d247be533028d"
    candidate = "b57ce3b757ef3fbc1d32bdcf22be8d32d72d779d7d59acf03b67211af93aa9de"
    if request.get("sha256") != candidate or hashlib.sha256(Path("/usr/bin/aos_cm_app").read_bytes()).hexdigest() != original:
        raise ValueError("CM_COMPARISON_BINARY_IDENTITY_MISMATCH")
    before = execute(dict(request, action="component-cm-status"))
    sm = execute(dict(request, action="component-sm-status"))
    vdp = command(["systemctl", "show", "aos-vehicle-data-provider", "--property=MainPID", "--value"]).stdout.strip()
    if (sm.get("binarySha256") != "936fbd563f7e9d54651504f5aeba84fee0f3736861d30c2efb60eb564e039783"
            or sm["service"]["ActiveState"] != "active"):
        raise ValueError("CM_COMPARISON_REQUIRES_UNCHANGED_SM")
    root = Path("/run/democtl-cm-comparison-20260912")
    binary = root / "aos_cm_app"
    dropin = Path("/run/systemd/system/aos-cm.service.d/94-democtl-comparison.conf")
    contents = "[Service]\nBindReadOnlyPaths=" + str(binary) + ":/usr/bin/aos_cm_app\n"
    timer = "democtl-cm-comparison-rollback"
    if phase == "without-patch":
        if (before.get("binarySha256") != original or before["service"]["ActiveState"] != "active"
                or root.exists() or root.is_symlink() or dropin.exists() or dropin.is_symlink()):
            raise ValueError("CM_COMPARISON_TRANSIENT_STATE_CONFLICT")
        with gzip.GzipFile(fileobj=io.BytesIO(base64.b64decode(request["binary"], validate=True))) as payload:
            raw = payload.read(8 * 1024 * 1024 + 1)
        if (len(raw) > 8 * 1024 * 1024 or hashlib.sha256(raw).hexdigest() != candidate
                or raw[:6] != b"\x7fELF\x02\x01" or raw[18:20] != b"\xb7\x00"):
            raise ValueError("CM_COMPARISON_ARM64_BINARY_MISMATCH")
        root.mkdir(mode=0o700)
        binary.write_bytes(raw)
        binary.chmod(0o755)
        command(["chcon", "--reference=/usr/bin/aos_cm_app", str(binary)], check=True)
        # Rollback survives host disconnect; it acts only on the exact owned drop-in.
        rollback = ("from pathlib import Path; import subprocess; p=Path(" + repr(str(dropin)) + "); "
            "assert not p.is_symlink() and p.read_text()==" + repr(contents) + "; p.unlink(); "
            "subprocess.run(['systemctl','daemon-reload'],check=True); "
            "subprocess.run(['systemctl','restart','aos-cm'],check=True)")
        command(["systemd-run", "--unit=" + timer, "--on-active=8m", "--timer-property=AccuracySec=1s",
            "/usr/bin/python3", "-c", rollback], check=True)
        dropin.parent.mkdir(parents=True, exist_ok=True)
        dropin.write_text(contents)
        command(["systemctl", "daemon-reload"], check=True)
        expected = candidate
    else:
        if root.is_symlink() or binary.is_symlink() or dropin.is_symlink():
            raise ValueError("CM_COMPARISON_TRANSIENT_STATE_CONFLICT")
        if not binary.is_file() or hashlib.sha256(binary.read_bytes()).hexdigest() != candidate:
            raise ValueError("CM_COMPARISON_TRANSIENT_BINARY_MISMATCH")
        if dropin.exists():
            if dropin.read_text() != contents:
                raise ValueError("CM_COMPARISON_DROPIN_CHANGED")
            dropin.unlink()
            command(["systemctl", "daemon-reload"], check=True)
        elif before.get("binarySha256") != original:
            raise ValueError("CM_COMPARISON_ROLLBACK_REQUIRES_RECONCILIATION")
        command(["systemctl", "stop", timer + ".timer"], check=True)
        expected = original
    already_restored = phase == "restore" and before.get("binarySha256") == original
    if not already_restored:
        subprocess.run(["systemctl", "restart", "aos-cm"], capture_output=True, text=True, timeout=25, check=True)
    after = execute(dict(request, action="component-cm-status"))
    sm_after = execute(dict(request, action="component-sm-status"))
    vdp_after = command(["systemctl", "show", "aos-vehicle-data-provider", "--property=MainPID", "--value"]).stdout.strip()
    if (after.get("binarySha256") != expected or after["service"]["ActiveState"] != "active"
            or sm_after["service"]["MainPID"] != sm["service"]["MainPID"] or vdp_after != vdp):
        raise ValueError("CM_COMPARISON_ACTIVATION_UNCONFIRMED_ROLLBACK_ARMED")
    if phase == "restore":
        binary.unlink()
        root.rmdir()
    return dict(state="APPLIED" if phase == "without-patch" else "RESTORED", phase=phase, mutation=True,
        alreadyRestored=already_restored, service=after["service"], binarySha256=expected,
        smPidPreserved=True, smPid=sm["service"]["MainPID"], vdpPidPreserved=True, vdpPid=vdp,
        transientDropinPresent=dropin.exists(), rollbackMinutes=8 if phase == "without-patch" else None,
        storedDesired=after.get("delivery", {}).get("storedDesired"))


def cm_startup_projection(records):
    """Only public protocol fields and fixed native stages; never raw wire data."""
    events, counts = [], {}
    for record in records:
        message = record.get("MESSAGE", "")
        if isinstance(message, list):
            message = bytes(message).decode("utf-8", errors="replace")
        if not isinstance(message, str):
            continue
        message = re.sub(r"\x1b\[[0-9;]*m", "", message)
        stage = re.search(r"\(([a-z_]{1,30})\) ([A-Za-z][A-Za-z '-]{1,100})(?=:|$)", message)
        if not stage:
            continue
        item = dict(time=record.get("__REALTIME_TIMESTAMP"), pid=record.get("_PID"),
            unit=record.get("_SYSTEMD_UNIT"), module=stage[1], stage=stage[2])
        wire = stage[1] == "communication" and stage[2] in ("Sent message", "Received message", "Handle cloud message")
        if wire:
            kind = re.search(r'"messageType"\s*:\s*"([A-Za-z]{1,40})"', message)
            item["messageType"] = kind[1] if kind else "UNKNOWN"
            for field in ("txn", "systemId", "createdAt"):
                value = re.search(r'"' + field + r'"\s*:\s*"([A-Za-z0-9_.:+-]{0,128})"', message)
                if value:
                    item[field] = value[1]
            for field in ("isDeltaInfo", "isConnected"):
                value = re.search(r'"' + field + r'"\s*:\s*(true|false)', message)
                if value:
                    item[field] = value[1] == "true"
            if item["messageType"] in ("unitStatus", "desiredStatus"):
                item["wireTruncated"] = not message.rstrip().endswith("}}")
        else:
            for field in ("state", "version", "nodeID", "nodeId", "itemID", "id", "isConnected", "connected"):
                value = re.search(r'\b' + field + r'=([A-Za-z0-9_.-]{1,128})', message)
                if value:
                    item[field] = value[1]
            for known in ("systemID mismatch", "node is not connected", "not found", "timeout", "max retries reached"):
                if known.lower() in message.lower():
                    item.setdefault("errors", []).append(known)
        key = item["module"] + ":" + item["stage"] + ":" + item.get("messageType", "")
        counts[key] = counts.get(key, 0) + 1
        if ((wire and item["messageType"] in ("unitStatus", "desiredStatus", "stateRequest", "monitoringData", "ack", "nack"))
                or (not wire and stage[1] in ("app", "communication", "iamclient", "smclient", "smcontroller", "nodeinfoprovider", "updatemanager")
                    and re.search(r"start|connect|pong|unit status|node info|node state|update state|failed|can't load|instances status|update is required", stage[2], re.I))):
            events.append(item)
    events.sort(key=lambda item: int(item["time"] or 0))
    return dict(events=events[:150], eventsTruncated=len(events) > 150, counts=counts)


def cm_startup_comparison(request):
    if (request.get("target") != "test"
            or request["vehicle"].get("localVmId") != "5aa1f8e4-a111-4467-a6cc-fb269c62a7a8"
            or request["vehicle"].get("unitId") != "923b9820-999b-41bb-91db-b2a2c469e743"):
        raise ValueError("CM_STARTUP_READ_REQUIRES_CURRENT_TEST_32")
    windows = {}
    for name, start, end, pid, since_us in (
            ("cold", "05:12:00", "05:16:00", "1057", 1789189933000000),
            ("warm", "10:06:00", "10:10:00", "41710", 1789207564978000),
            ("recurrence", "10:34:00", "10:42:00", "43568", 1789209240000000)):
        result = command(["journalctl", "-b", "--since=2026-09-12 " + start + " UTC",
            "--until=2026-09-12 " + end + " UTC", "-u", "aos-cm.service", "-u", "aos-sm.service",
            "-n", "12000", "-o", "json", "--output-fields=MESSAGE,__REALTIME_TIMESTAMP,_PID,_SYSTEMD_UNIT", "--no-pager"])
        if result.returncode or len(result.stdout) > 32 * 1024 * 1024:
            windows[name] = dict(state="UNAVAILABLE")
            continue
        records = [json.loads(line) for line in result.stdout.splitlines()]
        selected = [row for row in records if row.get("_PID") == pid
            or (row.get("_PID") == "1120" and int(row.get("__REALTIME_TIMESTAMP", "0")) >= since_us)]
        windows[name] = dict(state="CURRENT" if records else "NO_RETAINED_RECORDS", records=len(records),
            journalLimitReached=len(records) >= 12000, **cm_startup_projection(selected))
    properties = command(["systemctl", "show", "aos-cm", "aos-sm", "--property=Id,After,Before,Requires,Wants,Type,ActiveEnterTimestamp,MainPID,NRestarts"])
    return dict(mutation=False, windows=windows, ordering=properties.stdout.splitlines())


def core_permission_status(request):
    if (request.get("target") != "test" or request.get("role") != "test"
            or request.get("vehicle", {}).get("localVmId") != "6fcf5a74-0b74-4ef0-a05d-44bad598ab94"
            or request["vehicle"].get("unitId") != "42c0bf43-4eb7-44e6-8c74-f60f9959da66"):
        raise ValueError("CORE_PERMISSION_AUTHORIZED_TEST_REQUIRED")
    managers = {}
    for name in ("iam", "sm", "cm"):
        result = command(["systemctl", "show", "aos-" + name,
            "--property=MainPID,ActiveState,Result,NRestarts,MemoryCurrent,ActiveEnterTimestamp"])
        props = dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)
        pid = props.get("MainPID", "0")
        binary = Path("/proc") / pid / "exe"
        managers[name] = dict(service=props, binarySha256=hashlib.sha256(binary.read_bytes()).hexdigest() if binary.exists() else None)
        journal = command(["journalctl", "-b", "-u", "aos-" + name, "_PID=" + pid, "-n", "1000", "--no-pager", "-o", "cat"])
        managers[name]["diagnostics"] = {text: journal.stdout.count(text) for text in (
            "permission key parsing error", "permission value parsing error", "Register instance failed",
            "Failed to push back permissions", "Can't schedule instance", "Register instance", "Unregister instance",
            "Failed to get permissions", "not enough memory", "no memory")}
    matched = True
    for name in managers:
        path = Path("/run/democtl-core-permissions-256/aos_" + name + "_app")
        dropin = Path("/run/systemd/system/aos-" + name + ".service.d/96-democtl-permission-capacity.conf")
        alternate = Path("/run/democtl-iam-response-32/aos_iam_app")
        if (name == "iam" and dropin.is_file() and not dropin.is_symlink()
                and dropin.read_text() == "[Service]\nBindReadOnlyPaths=" + str(alternate) + ":/usr/bin/aos_iam_app\n"):
            path = alternate
        expected = "[Service]\nBindReadOnlyPaths=" + str(path) + ":/usr/bin/aos_" + name + "_app\n"
        matched = matched and (not path.is_symlink() and path.is_file() and not dropin.is_symlink()
            and dropin.is_file() and dropin.read_text() == expected
            and hashlib.sha256(path.read_bytes()).hexdigest() == managers[name]["binarySha256"])
    return dict(managers=managers, mutation=False, transientFilesMatchProcesses=matched,
        committedVdp66Sha256=core_permission_vdp_snapshot(),
        selinuxEnforcing=Path("/sys/fs/selinux/enforce").read_text().strip() == "1")


def core_permission_vdp_snapshot(root=FACTORY_INPUTS.parent):
    """Preserve this trial's committed VDP66, not historical VDP17/18 proofs."""
    if any((root / "state" / name).exists() or (root / "state" / name).is_symlink()
            for name in ("transaction.json", "stopped.json")):
        raise ValueError("CORE_PERMISSION_VDP_TRANSACTION_PRESENT")
    installed = root / "state/installed.json"
    if installed.is_symlink() or not installed.is_file() or installed.stat().st_size > 131072:
        raise ValueError("CORE_PERMISSION_VDP_RECORD_INVALID")
    raw = installed.read_bytes()
    value = json.loads(raw)
    slot = value.get("slot")
    if (not isinstance(value.get("Version"), str) or not re.fullmatch(r"[1-9][0-9]*\.0\.0", value["Version"])
            or slot not in ("a", "b") or value.get("schemaVersion") != 1):
        raise ValueError("CORE_PERMISSION_COMMITTED_VDP_REQUIRED")
    active = root / "active"
    record = root / "slots" / slot / ".aos-instance.json"
    if (not active.is_symlink() or os.readlink(active) != "slots/" + slot
            or record.is_symlink() or json.loads(record.read_bytes()) != value):
        raise ValueError("CORE_PERMISSION_VDP_COMMIT_MISMATCH")
    return hashlib.sha256(raw).hexdigest()


def core_permission_apply(request):
    before = core_permission_status(request)
    if set(request.get("binaries", {})) != {"iam", "sm", "cm"}:
        raise ValueError("CORE_PERMISSION_ALL_THREE_BINARIES_REQUIRED")
    root = Path("/run/democtl-core-permissions-256")
    if root.exists() or root.is_symlink():
        raise ValueError("CORE_PERMISSION_TRANSIENT_STATE_REQUIRES_RECONCILIATION")
    binaries, dropins = {}, {}
    for name in ("iam", "sm", "cm"):
        props = before["managers"][name]
        if props["service"].get("ActiveState") != "active" or props["binarySha256"] != request.get("previous", {}).get(name):
            raise ValueError("CORE_PERMISSION_PREVIOUS_PROCESS_CHANGED")
        # Do not stack this proof on another binary override.
        installed = Path("/usr/bin/aos_" + name + "_app")
        if hashlib.sha256(installed.read_bytes()).hexdigest() != props["binarySha256"]:
            raise ValueError("CORE_PERMISSION_STOCK_33_PROCESS_REQUIRED")
        info = request["binaries"][name]
        with gzip.GzipFile(fileobj=io.BytesIO(base64.b64decode(info["data"], validate=True))) as stream:
            raw = stream.read(256 * 1024**2 + 1)
        if (len(raw) > 256 * 1024**2 or raw[:6] != b"\x7fELF\x02\x01" or raw[18:20] != b"\xb7\x00"
                or hashlib.sha256(raw).hexdigest() != info["sha256"]):
            raise ValueError("CORE_PERMISSION_ARM64_DIGEST_INVALID")
        binaries[name] = raw
        dropins[name] = Path("/run/systemd/system/aos-" + name + ".service.d/96-democtl-permission-capacity.conf")
        if dropins[name].exists() or dropins[name].is_symlink() or dropins[name].parent.is_symlink():
            raise ValueError("CORE_PERMISSION_DROPIN_CONFLICT")
    saved = core_permission_vdp_snapshot()
    root.mkdir(mode=0o700)
    for name, raw in binaries.items():
        binary = root / ("aos_" + name + "_app")
        binary.write_bytes(raw)
        binary.chmod(0o755)
        command(["chcon", "--reference=/usr/bin/aos_" + name + "_app", str(binary)], check=True)
    written = []
    try:
        for name, dropin in dropins.items():
            dropin.parent.mkdir(parents=True, exist_ok=True)
            dropin.write_text("[Service]\nBindReadOnlyPaths=" + str(root / ("aos_" + name + "_app")) + ":/usr/bin/aos_" + name + "_app\n")
            written.append(dropin)
        command(["systemctl", "daemon-reload"], check=True)
        # Stop consumers first; initialize IAM before registrations are replayed.
        for name in ("cm", "sm", "iam"):
            subprocess.run(["systemctl", "stop", "aos-" + name], capture_output=True, timeout=25, check=True)
        for name in ("iam", "sm", "cm"):
            subprocess.run(["systemctl", "start", "aos-" + name], capture_output=True, timeout=25, check=True)
        after = core_permission_status(request)
        if any(after["managers"][name]["binarySha256"] != request["binaries"][name]["sha256"]
                or after["managers"][name]["service"].get("ActiveState") != "active" for name in binaries):
            raise ValueError("CORE_PERMISSION_ACTIVATION_UNCONFIRMED")
        if core_permission_vdp_snapshot() != saved:
            raise ValueError("CORE_PERMISSION_COMMITTED_VDP_CHANGED")
    except Exception:
        # Restore original packaged bytes, never alter durable identity/databases.
        for dropin in written:
            dropin.unlink()
        command(["systemctl", "daemon-reload"], check=True)
        subprocess.run(["systemctl", "stop", "aos-cm", "aos-sm", "aos-iam"], capture_output=True, timeout=35)
        for name in ("iam", "sm", "cm"):
            subprocess.run(["systemctl", "start", "aos-" + name], capture_output=True, timeout=25)
        raise
    return dict(after, mutation=True, state="APPLIED", capacity=256, durableVdpPreserved=True,
        transientRoot=str(root), originalBinariesPreserved=True)


def core_iam_response_apply(request):
    before = core_permission_status(request)
    if (not before.get("transientFilesMatchProcesses") or any(
            row["service"].get("ActiveState") != "active" or row["binarySha256"] != request.get("previous", {}).get(name)
            for name, row in before["managers"].items())):
        raise ValueError("IAM_RESPONSE_PREVIOUS_PROCESS_CHANGED")
    root = Path("/run/democtl-iam-response-32")
    dropin = Path("/run/systemd/system/aos-iam.service.d/96-democtl-permission-capacity.conf")
    old_text = "[Service]\nBindReadOnlyPaths=/run/democtl-core-permissions-256/aos_iam_app:/usr/bin/aos_iam_app\n"
    if root.exists() or root.is_symlink() or dropin.is_symlink() or dropin.read_text() != old_text:
        raise ValueError("IAM_RESPONSE_TRANSIENT_CONFLICT")
    info = request.get("binary", {})
    with gzip.GzipFile(fileobj=io.BytesIO(base64.b64decode(info.get("data", ""), validate=True))) as stream:
        raw = stream.read(256 * 1024**2 + 1)
    if (len(raw) > 256 * 1024**2 or raw[:6] != b"\x7fELF\x02\x01" or raw[18:20] != b"\xb7\x00"
            or hashlib.sha256(raw).hexdigest() != info.get("sha256")):
        raise ValueError("IAM_RESPONSE_ARM64_DIGEST_INVALID")
    saved = core_permission_vdp_snapshot()
    root.mkdir(mode=0o700)
    binary = root / "aos_iam_app"
    binary.write_bytes(raw)
    binary.chmod(0o755)
    command(["chcon", "--reference=/usr/bin/aos_iam_app", str(binary)], check=True)
    try:
        dropin.write_text("[Service]\nBindReadOnlyPaths=" + str(binary) + ":/usr/bin/aos_iam_app\n")
        command(["systemctl", "daemon-reload"], check=True)
        # IAM registrations are volatile: stop/start SM with IAM so native
        # instance registration is replayed. CM, VDP, VM and databases stay.
        for name in ("sm", "iam"):
            subprocess.run(["systemctl", "stop", "aos-" + name], capture_output=True, timeout=30, check=True)
        for name in ("iam", "sm"):
            subprocess.run(["systemctl", "start", "aos-" + name], capture_output=True, timeout=30, check=True)
        after = core_permission_status(request)
        if (after["managers"]["iam"]["binarySha256"] != info["sha256"]
                or any(after["managers"][name]["service"].get("ActiveState") != "active" for name in ("iam", "sm", "cm"))
                or any(after["managers"][name]["binarySha256"] != request["previous"][name] for name in ("sm", "cm"))
                or after["managers"]["cm"]["service"]["MainPID"] != before["managers"]["cm"]["service"]["MainPID"]
                or not after["transientFilesMatchProcesses"] or core_permission_vdp_snapshot() != saved):
            raise ValueError("IAM_RESPONSE_ACTIVATION_UNCONFIRMED")
    except Exception:
        dropin.write_text(old_text)
        command(["systemctl", "daemon-reload"], check=True)
        subprocess.run(["systemctl", "stop", "aos-sm", "aos-iam"], capture_output=True, timeout=35)
        for name in ("iam", "sm"):
            subprocess.run(["systemctl", "start", "aos-" + name], capture_output=True, timeout=30)
        raise
    return dict(after, mutation=True, state="APPLIED", responseCapacity=32, cmPreserved=True, durableVdpPreserved=True)


def resume_readiness_provider():
    """Resume only the preserved committed VDP69 stopped by its Requires edge.

    This is a current-Test proof repair, not a general component-start fallback.
    No selector, transaction or installed metadata is changed.
    """
    root = FACTORY_INPUTS.parent
    if any((root / "state" / name).exists() for name in ("transaction.json", "stopped.json")):
        raise ValueError("READINESS_PROVIDER_TRANSACTION_REQUIRES_RECONCILIATION")
    active = root / "active"
    installed = json.loads((root / "state/installed.json").read_text())
    if (not active.is_symlink() or os.readlink(active) not in ("slots/a", "slots/b")
            or installed.get("Version") != "69.0.0"
            or installed.get("slot") != Path(os.readlink(active)).name
            or json.loads((active / ".aos-instance.json").read_text()) != installed):
        raise ValueError("READINESS_PROVIDER_COMMITTED_BASELINE_MISMATCH")
    subprocess.run(["systemctl", "start", "aos-vehicle-data-provider"], capture_output=True, timeout=25, check=True)


def provider_readiness_apply(request):
    """One transient fixed Provider update; retain the private old token for rollback."""
    if (request.get("role") != "test" or os.geteuid() != 0
            or request.get("vehicle", {}).get("unitId") != "42c0bf43-4eb7-44e6-8c74-f60f9959da66"
            or Path("/etc/machine-id").read_text().strip() != request["vehicle"].get("systemUid")
            or Path("/sys/fs/selinux/enforce").read_text().strip() != "1"):
        raise ValueError("READINESS_CURRENT_ENFORCING_TEST_REQUIRED")
    root = Path("/run/democtl-provider-readiness")
    dropin = Path("/run/systemd/system/aos-kuksa-provider-prepare.service.d/97-democtl-readiness.conf")
    token = Path("/var/lib/aos-kuksa-provider/kuksa-token")
    installed = Path("/usr/libexec/aos-kuksa-provider-prepare")
    for path in (root, dropin, token, installed):
        if any(part.is_symlink() for part in (path,) + tuple(path.parents)):
            raise ValueError("READINESS_PATH_UNSAFE")
    info = request["binary"]
    with gzip.GzipFile(fileobj=io.BytesIO(base64.b64decode(info["data"], validate=True))) as stream:
        raw = stream.read(32*1024**2+1)
    if (len(raw)>32*1024**2 or raw[:6] != b"\x7fELF\x02\x01" or raw[18:20] != b"\xb7\x00"
            or hashlib.sha256(raw).hexdigest() != info["sha256"]):
        raise ValueError("READINESS_BINARY_INVALID")
    def scopes():
        if not stat.S_ISREG(token.stat().st_mode) or token.stat().st_uid != 0 or stat.S_IMODE(token.stat().st_mode) != 0o600:
            raise ValueError("READINESS_CREDENTIAL_UNSAFE")
        parts = token.read_bytes().split(b".")
        if len(parts) != 3:
            raise ValueError("READINESS_CREDENTIAL_INVALID")
        payload = json.loads(base64.urlsafe_b64decode(parts[1] + b"="*(-len(parts[1])%4)))
        return set(payload["scope"].split())
    additions = {"read:Vehicle.OEM." + team + ".Advisory.Readiness" for team in ("BrakeHealth", "TireHealth")}
    previous_binary = root / installed.name
    execution = root / "exec"
    binary = execution / installed.name
    receipt = root / "receipt.json"
    backup = root / "previous-token"
    reconciled = False
    if root.exists():
        if receipt.is_file() and binary.is_file() and hashlib.sha256(binary.read_bytes()).hexdigest() == info["sha256"]:
            saved = json.loads(receipt.read_text())
            if dropin.read_text() == saved["dropin"] and scopes() == set(saved["scopes"]):
                # Recover the exact first proof, which omitted the Requires=
                # dependent restart. Persist once; later repeats cannot start
                # an intentionally stopped provider.
                if not saved.get("providerResumeReconciled"):
                    resume_readiness_provider()
                    saved["providerResumeReconciled"] = True
                    write_public(receipt, json.dumps(saved), mode=0o600)
                return dict(state="APPLIED", noOp=True, scopeCount=len(scopes()), binarySha256=info["sha256"], transient=True)
        # One classified, rolled-back proof may be replaced by its diagnostic
        # successor. Compare private credentials locally; return no contents.
        reconciled = (not receipt.exists() and not dropin.exists() and not backup.is_symlink()
            and backup.is_file() and previous_binary.is_file() and not previous_binary.is_symlink()
            and not execution.exists()
            and hashlib.sha256(previous_binary.read_bytes()).hexdigest() in (
                "d8e68eaa32d1e9dca0f125a5d51deb423fb8f839814344a5807142e82e8165c5",
                "5bd605eccb9cd2347687f8176cb2d94ad1288c819e592a48fa69983f87d0c5f1",
                "7dc4a24b6bed3cc58a71ebeccb41914be2aabddd86c540ba24104d65bde89b74",
                "4d5f955da62039975ce8c47486282140368288b38906070fca34294d82a6a297",
                "1565ef029b585348c8189df87fb7ea6879d659b4beca7806745bf7caabd021b3",
                "d5e11fe5cb348a48e367523df778933597a6da785cdc2b51192d03e2b084da25")
            and backup.read_bytes() == token.read_bytes())
        if not reconciled:
            raise ValueError("READINESS_PREVIOUS_ATTEMPT_REQUIRES_RECONCILIATION")
    if dropin.exists():
        raise ValueError("READINESS_DROPIN_CONFLICT")
    # The unchanged native preparer validates/reuses (or renews) the exact
    # signed old credential before migration; no token is returned to the host.
    provider_was_active = command(["systemctl", "is-active", "aos-vehicle-data-provider"]).stdout.strip() == "active"
    subprocess.run(["systemctl", "restart", "aos-kuksa-provider-prepare"], capture_output=True, timeout=25, check=True)
    before = scopes()
    if before & additions:
        raise ValueError("READINESS_OLD_SCOPE_NOT_BASELINE")
    if not reconciled:
        root.mkdir(mode=0o700)
    backup.write_bytes(token.read_bytes()); backup.chmod(0o600)
    # /run is nosuid and suppresses the native SELinux transition. Use one
    # private root-only filesystem, read-only at execution time, with no
    # setuid bits/file capabilities. Keep /run flags, NNP and policy unchanged.
    execution.mkdir(mode=0o700)
    command(["mount", "-t", "tmpfs", "-o", "size=8m,mode=0700,nodev", "democtl-provider-proof", str(execution)], check=True)
    original = installed.read_bytes()
    binary.write_bytes(original); binary.chmod(0o755)
    command(["chcon", "--reference=" + str(installed), str(binary)], check=True)
    text = "[Service]\nBindReadOnlyPaths=" + str(binary) + ":" + str(installed) + "\n"
    try:
        command(["mount", "-o", "remount,ro,nodev", str(execution)], check=True)
        dropin.parent.mkdir(parents=True, exist_ok=True)
        dropin.write_text(text)
        command(["systemctl", "daemon-reload"], check=True)
        baseline = subprocess.run(["systemctl", "restart", "aos-kuksa-provider-prepare"], capture_output=True, timeout=25)
        if baseline.returncode or scopes() != before:
            raise ValueError("READINESS_BIND_BASELINE_FAILED")
        command(["mount", "-o", "remount,rw,nodev", str(execution)], check=True)
        binary.write_bytes(raw)
        command(["mount", "-o", "remount,ro,nodev", str(execution)], check=True)
        token.unlink()
        subprocess.run(["systemctl", "restart", "aos-kuksa-provider-prepare"], capture_output=True, timeout=25, check=True)
        if scopes() != before | additions:
            raise ValueError("READINESS_SCOPE_DELTA_MISMATCH")
        if provider_was_active:
            resume_readiness_provider()
        write_public(receipt, json.dumps(dict(dropin=text, scopes=sorted(scopes()), providerResumeReconciled=True)), mode=0o600)
    except BaseException:
        if dropin.exists():
            dropin.unlink()
        token.write_bytes(backup.read_bytes()); token.chmod(0o600)
        command(["restorecon", str(token)], check=True)
        command(["systemctl", "daemon-reload"], check=True)
        subprocess.run(["systemctl", "restart", "aos-kuksa-provider-prepare"], capture_output=True, timeout=25)
        if provider_was_active:
            resume_readiness_provider()
        if os.path.ismount(execution):
            command(["umount", str(execution)], check=True)
        execution.rmdir()
        raise
    return dict(state="APPLIED", noOp=False, scopeCount=len(scopes()), binarySha256=info["sha256"], transient=True,
                vdpReload="NEXT_COMPONENT_ACTIVATION", managersChanged=False)


def execute(request):
    if request["action"] == "provider-readiness-apply":
        return provider_readiness_apply(request)
    if request["action"] == "core-permissions-iam-response-apply":
        return core_iam_response_apply(request)
    if request["action"] == "service-kac-recovery":
        return kac_recovery(request)
    if request["action"] == "service-kac-recovery-remove":
        return kac_recovery(request, remove=True)
    if request["action"] in ("service-kac-time-proof", "service-kac-data-proof"):
        return kac_time_read_proof(request)
    if request["action"] == "service-kac-activate":
        return activate_kac(request)
    if request["action"] == "core-permissions-status":
        return core_permission_status(request)
    if request["action"] == "core-permissions-apply":
        return core_permission_apply(request)
    if request["action"] == "component-cm-startup":
        return cm_startup_comparison(request)
    if request["action"] == "component-cm-apply":
        if request.get("proof") == "factory34-startup-reconcile":
            return cm_startup_factory34(request)
        if request.get("proof") == "factory32-idle-full-status":
            return cm_idle_refresh_factory32(request)
        if request.get("proof") == "factory32-cm-comparison":
            return cm_compare_factory32(request)
        if request.get("proof") == "factory32-delivery-control":
            return cm_restart_factory32_control(request)
        return cm_apply_service_update(request)
    if request["action"] == "component-cm-status":
        props = command(["systemctl", "show", "aos-cm", "--property=MainPID,ActiveState,Result,NRestarts,FragmentPath"]).stdout
        service = dict(line.split("=", 1) for line in props.splitlines() if "=" in line)
        pid = service.get("MainPID", "0")
        binary = Path("/proc") / pid / "exe"
        digest = hashlib.sha256(binary.read_bytes()).hexdigest() if pid.isdigit() and int(pid) > 0 else None
        return dict(mutation=False, service=service, binarySha256=digest,
                    executable=os.readlink(binary) if digest else None,
                    processWaits=process_wait_observation(pid) if digest else None,
                    delivery=cm_delivery_observation(pid) if digest else None)
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
        # Preparation needs native identity, not container/process forensics.
        # Explicit engineering inspection and migration retain the full view.
        if request.get("identityOnly") is True:
            identifier = json.loads(Path("/etc/aos/iam.cfg").read_text()).get("identifier", {})
            identifier_path = identifier.get("params", {}).get("systemIDPath")
            native_file = None
            if identifier.get("plugin") == "fileidentifier" and identifier_path == "/etc/machine-id":
                candidate = Path(identifier_path).read_text().strip()
                if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}", candidate):
                    native_file = candidate
            try:
                with socket.create_connection(("127.0.0.1", 8090), timeout=1):
                    iam_loopback = True
            except OSError:
                iam_loopback = False
            return dict(iamPublicServerUrl=cfg.get("iamPublicServerUrl"),
                iamLocalEndpoint=dict(loopback8090Reachable=iam_loopback),
                iamFileIdentifier=dict(plugin=identifier.get("plugin"),
                    path=identifier_path if identifier_path == "/etc/machine-id" else "UNSUPPORTED",
                    systemUid=native_file))
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
            kuksaAuthorization=kuksa_authorization_observation(),
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
                    mutualTlsCredentialProjection={
                        "smDropInPresent": Path("/run/systemd/system/aos-sm.service.d/85-democtl-viss-mtls.conf").is_file(),
                        "vdpDropInPresent": Path("/run/systemd/system/aos-vehicle-data-provider.service.d/85-democtl-viss-mtls.conf").is_file(),
                        "runtimeLeafPresent": Path("/var/aos/iam/vehicle-state/platform-update-runtime/client.pem").is_file(),
                        "vdpLeafPresent": Path("/var/aos/iam/vehicle-state/selected-platform-unit/client.pem").is_file()},
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
    if action in ("time-sync", "time-status"):
        if request.get("role") != "test":
            raise ValueError("TIME_RECOVERY_TEST_ONLY")
        if action == "time-status":
            return clock_status()
        before = clock_status()
        result = command(["systemctl", "restart", "systemd-timesyncd.service"])
        deadline = time.monotonic() + 15
        synchronized = False
        while result.returncode == 0:
            message = command(["timedatectl", "show-timesync", "--property=NTPMessage", "--value"]).stdout.strip()
            # A marker or NTPSynchronized=yes can survive suspend/restart. Require
            # a new successful response from this timesyncd process instead.
            synchronized = ("Ignored=no" in message and re.search(r"PacketCount=[1-9][0-9]*\b", message) is not None)
            if synchronized or time.monotonic() >= deadline:
                break
            time.sleep(.5)
        after = clock_status()
        return dict(state="SYNCHRONIZED" if result.returncode == 0 and synchronized else "UNCONFIRMED",
            before=before, after=after, restartExitCode=result.returncode)
    if action == "dns-restart":
        if request.get("role") != "test":
            raise ValueError("DNS_RECOVERY_TEST_ONLY")
        config = Path("/var/aos/dns/dnsmasq.conf")
        if config.is_symlink() or "server=10.0.0.1#18053" not in config.read_text().splitlines():
            raise ValueError("DNS_RECOVERY_BRIDGE_CONFIG_MISMATCH")
        before = command(["systemctl", "show", "dnsmasq.service", "--property=MainPID", "--value"]).stdout.strip()
        result = command(["systemctl", "restart", "dnsmasq.service"])
        after = command(["systemctl", "show", "dnsmasq.service", "--property=MainPID", "--value"]).stdout.strip()
        active = command(["systemctl", "is-active", "dnsmasq.service"]).stdout.strip()
        return dict(state="ACTIVE" if result.returncode == 0 and active == "active" else "UNCONFIRMED",
            previousPid=before, pid=after)
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
            advisorySchema=advisory_schema_observation(node),
            permissionProbe="NOT_PERFORMED", mutation=False)
    if action == "component-logs":
        services = command(["systemctl", "show", "aos-sm", "aos-cm", "aos-vehicle-data-provider",
                            "--property=Id,Names,ActiveState,Result,NRestarts"])
        ids = [line[3:] for line in services.stdout.splitlines() if line.startswith("Id=")]
        streams = []
        for unit in ids + ["kuksa-databroker.service", "aos-vehicle-data-provider-selftest@a.service", "aos-vehicle-data-provider-selftest@b.service"]:
            result = command(["journalctl", "-b", "-n", "6000" if unit == "aos-sm.service" else "600" if unit in ("aos-cm.service", "aos-vehicle-data-provider.service") else "80",
                              "-o", "json", "--no-pager", "-u", unit])
            if result.returncode or len(result.stdout) > (8388608 if unit in ("aos-cm.service", "aos-sm.service") else 2097152):
                raise ValueError("COMPONENT_JOURNAL_UNAVAILABLE")
            streams.extend((unit, line) for line in result.stdout.splitlines())
        entries, structures, ready_events, cm_transport = [], set(), 0, []
        update_errors = []
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
                    if re.search(r"err=command `/usr/libexec/aos-vehicle-data-provider-health unavailab", message):
                        native_fields["runtimeError"] = "PROVIDER_MARK_UNAVAILABLE_FAILED"
                    native_fields["errorLocations"].extend(re.findall(r"\bproviderprofile\.cpp:[0-9]{1,5}\b", message))
            # Preserve only known fixed runtime failure labels before removing
            # instance bodies, which otherwise also hide the trailing error.
            diagnostic = next((label for label in (
                "a different component transaction is already active",
                "component runtime is not ready",
                "safe stop wait canceled", "safe_stop_timeout", "safe_stop_lost_during_apply",
                "failed to start provider", "cannot start provider",
            ) if label in message), None)
            # No message payloads, transport bodies, auth material or telemetry.
            if "{" in message:
                message = message.split("{", 1)[0] + "[BODY_REDACTED]"
            if (re.search(r"token|password|private.?key|certificate|authorization|jwt|https?://|wss?://", message, re.I)
                    or "-----BEGIN" in message or re.search(r"eyJ[A-Za-z0-9_-]+\.", message)):
                continue
            if not re.search(r"fail|error|cannot|could not|stop|start|health|slot|component|provider|safe.?stop|desired.?status|run.?instances|wait.*active|wait.*node|node.?status|instance.?status|instances.?statuses|Update state changed|Current update canceled|instance network", message, re.I):
                continue
            message = re.sub(r"[A-Za-z0-9_+/=-]{48,}", "[REDACTED_LONG_VALUE]", message)
            message = re.sub(r"[\x00-\x1f\x7f]", " ", message)[:600]
            entry = dict(time=item.get("__REALTIME_TIMESTAMP"), unit=item.get("_SYSTEMD_UNIT"), message=message)
            if diagnostic:
                entry["diagnostic"] = diagnostic
            if native_fields:
                entry["nativeInstance"] = native_fields
            if (requested_unit in ("aos-sm.service", "aos-cm.service")
                    and re.search(r"fail|error", message, re.I)
                    and "monitoring" not in message.lower()):
                update_errors.append(entry)
            entries.append(entry)
        # Use the existing fixed Python projection, not optional journalctl
        # PCRE support. A grep failure must not masquerade as an empty journal.
        advisory_log = command(["journalctl", "-b", "-n", "600", "-o", "json", "--no-pager",
            "-u", "aos-vehicle-data-provider.service"])
        if advisory_log.returncode != 0 or len(advisory_log.stdout) > 2097152:
            raise ValueError("COMPONENT_ADVISORY_JOURNAL_UNAVAILABLE")
        # Transport readiness emits only on a changed result. Include the
        # bounded current-process startup window, not an unbounded boot log.
        started = command(["systemctl", "show", "aos-vehicle-data-provider.service", "--property=ActiveEnterTimestamp", "--value"])
        advisory_startup = []
        try:
            start = datetime.datetime.strptime(started.stdout.strip(), "%a %Y-%m-%d %H:%M:%S UTC").replace(tzinfo=datetime.timezone.utc)
            startup = command(["journalctl", "-b", "-n", "600", "-o", "json", "--no-pager", "-u", "aos-vehicle-data-provider.service",
                "--since", "@" + str(int(start.timestamp())), "--until", "@" + str(int(start.timestamp()) + 10)])
            if startup.returncode == 0 and len(startup.stdout) <= 2097152:
                advisory_startup = advisory_log_observation(startup.stdout)
        except (ValueError, OverflowError):
            pass
        entries.sort(key=lambda entry: int(entry["time"] or 0))
        return dict(entries=entries[-100:], scannedEntries=len(streams), providerReadyEvents=ready_events, structuredFields=sorted(structures),
                    reconciliationEvents=[entry for entry in entries
                        if entry["unit"] in ("aos-sm.service", "aos-cm.service")
                        and re.search(r"Run instances|Run instance request|Stop instance:|Start instance:|Node instances statuses received|Node instance status received|Failed to process message", entry["message"])][-80:],
                    advisoryEvents=advisory_log_observation(advisory_log.stdout), advisoryStartupEvents=advisory_startup,
                    advisoryJournal=dict(records=len(advisory_log.stdout.splitlines()), returnCode=advisory_log.returncode),
                    smNetworkEvents=[entry for entry in entries if entry["unit"] == "aos-sm.service"
                        and ("network" in entry["message"].lower() or
                             entry.get("nativeInstance", {}).get("errorLocations") or
                             "Failed to get instance configs" in entry["message"])][-40:],
                    cmJournal=dict(cm_journal, stages=cm_journal["stages"][-15:]),
                    cmTransportEvents=cm_transport[-20:],
                    cmEvents=[entry for entry in entries if entry["unit"] == "aos-cm.service"][-20:],
                    services=services.stdout.strip().splitlines(), guestEpoch=int(time.time()),
                    smStartupFailures=[entry for entry in entries if entry["unit"] == "aos-sm.service"
                        and "can't start launcher" in entry["message"]][:12],
                    cmUpdatePhases=[entry for entry in entries if entry["unit"] == "aos-cm.service" and
                        re.search(r"Update state changed|Current update canceled|Cancel current update|Failed to process desired status", entry["message"])][-20:],
                    updateErrors=update_errors[-30:],
                    window="Current boot: last 600 CM / 6000 SM / 600 VDP / 80 other service events", projection="BOUNDED_REDACTED_SERVICE_EVENTS")
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
            if isinstance(message, str) and re.fullmatch(r"[a-zA-Z0-9_ :.,()\[\]-]{1,200}", message):
                row["reason"] = message
            elif isinstance(message, str) and message:
                # Fixed public runtime error labels, not arbitrary exception
                # text (which can contain credential paths or transport data).
                row["reasonLabels"] = [label for label in (
                    "safe stop wait canceled", "safe_stop_timeout", "safe_stop_lost_during_apply",
                    "systemd credential is unavailable", "binding credential is inconsistent",
                    "binding credential is unavailable", "component runtime is not ready",
                    "systemctl stop failed", "systemctl start failed", "Permission denied",
                    "Device or resource busy", "No such file or directory", "Invalid argument",
                    "timeout", "canceled", "not found", "failed", "unavailable",
                ) if label in message]
                row["reasonLocations"] = re.findall(r"\b[a-z]+\.cpp:[0-9]{1,5}\b", message)
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
            advisory=advisory_configuration_observation(capability))
        # Fixed public source bytes, not arbitrary guest file inspection. This
        # distinguishes installed transport code from a manifest-only claim.
        result["advisoryRuntimeFiles"] = {}
        for name in ("runtime.py", "advisory.py", "advisory_transport.py", "manifest.py"):
            path = target / "python/carla_viss_kuksa_provider" / name
            if not path.exists():
                continue
            if path.is_symlink() or path.stat().st_size > 131072:
                raise ValueError("COMPONENT_RUNTIME_MODULE_UNSAFE")
            result["advisoryRuntimeFiles"][name] = hashlib.sha256(path.read_bytes()).hexdigest()
        if result["advisory"] == "CONFIGURED_NOT_APPLICATION_PROOF":
            configuration_probe = command(["/usr/bin/python3", "-I", "-B", "-c",
                "import sys,json; from pathlib import Path; p=Path(sys.argv[1]); "
                "sys.path[:0]=[str(p/'python'),str(p/'python/site-packages')]; "
                "from carla_viss_kuksa_provider.runtime import load_payload_configuration; "
                "c=load_payload_configuration(p/'config/provider.json'); "
                "print(json.dumps(dict(advisoryEnabled=c.advisory_enabled,version=c.semantic_version)))",
                str(target)])
            if configuration_probe.returncode == 0 and len(configuration_probe.stdout) <= 512:
                parsed = json.loads(configuration_probe.stdout)
                if (set(parsed) == {"advisoryEnabled", "version"}
                        and type(parsed["advisoryEnabled"]) is bool and parsed["version"] == metadata["version"]):
                    result["advisoryConfiguration"] = dict(parsed, evidence="READ_ONLY_CONFIGURATION_LOAD_NOT_PROCESS_STATE")
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
    if action == "trust-probe":
        if request["role"] != "test" or not request["vehicle"].get("unitId"):
            raise ValueError("SOURCE_TRUST_TEST_IDENTITY_REQUIRED")
        return probe(mutual_tls=True)
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
