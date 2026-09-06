# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Direct, bounded process/QMP and SSH reads; no launcher or repair workflows."""

import json
import math
import os
import re
import shlex
import socket
import stat
import struct
import subprocess
import time
from pathlib import Path

from .status import observation, safe_word, skipped

def host_dns(config, timeout):
    if not config or "dnsPort" not in config:
        return skipped("HOST_DNS", "DNS_PORT_NOT_CONFIGURED")
    transaction = os.urandom(2)
    question = b"".join(bytes([len(s)]) + s.encode("ascii") for s in config["cloudHost"].split(".")) + b"\0\0\1\0\1"
    packet = transaction + struct.pack("!5H", 0x0100, 1, 0, 0, 0) + question
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as connection:
            connection.settimeout(timeout)
            connection.connect(("127.0.0.1", config["dnsPort"]))
            connection.send(packet)
            response = connection.recv(4096)
        if len(response) < 12 or response[:2] != transaction:
            raise ValueError("Invalid DNS response")
        flags, questions, answers, _, _ = struct.unpack("!5H", response[2:12])
        if not flags & 0x8000 or questions != 1 or response[12:12 + len(question)] != question:
            raise ValueError("Invalid DNS question")
        value = {"port": config["dnsPort"], "hostname": config["cloudHost"],
                 "responded": True, "rcode": flags & 15, "hasAnswer": answers > 0}
        return observation("HOST_DNS", value, reason=None if flags & 15 == 0 and answers else "DNS_NO_ANSWER")
    except (OSError, ValueError):
        return observation("HOST_DNS", {"port": config["dnsPort"]},
                           reason="DNS_BRIDGE_UNAVAILABLE", transport="SOURCE_UNAVAILABLE")


def process_snapshot(timeout):
    try:
        result = subprocess.run(["ps", "-axo", "pid=,args="], capture_output=True, text=True, timeout=timeout)
        if result.returncode:
            raise OSError()
        rows = []
        for line in result.stdout.splitlines():
            parts = line.strip().split(None, 1)
            if len(parts) != 2:
                continue
            # Never include raw process arguments in an observation.
            if "qemu-system-" not in parts[1]:
                continue
            try:
                args = shlex.split(parts[1])
                if args and Path(args[0]).name.startswith("qemu-system-"):
                    rows.append((int(parts[0]), args))
            except (ValueError, IndexError):
                continue
        return rows
    except (OSError, subprocess.SubprocessError):
        return None


def owns_overlay(args, overlay):
    for index, arg in enumerate(args[:-1]):
        if arg != "-drive":
            continue
        # ps prints argv without quoting; reconstruct a drive value containing
        # spaces up to the next QEMU option rather than reporting a false STOPPED.
        end = index + 2
        while end < len(args) and not args[end].startswith("-"):
            end += 1
        for item in " ".join(args[index + 1:end]).split(","):
            if item.startswith("file=") and Path(item[5:]).resolve() == overlay.resolve():
                return True
    return False


def qmp_status(path, timeout):
    deadline = time.monotonic() + timeout
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
        def read():
            while True:
                if time.monotonic() >= deadline:
                    raise TimeoutError("QMP deadline")
                connection.settimeout(max(0.001, deadline - time.monotonic()))
                raw = b""
                while not raw.endswith(b"\n"):
                    if time.monotonic() >= deadline:
                        raise TimeoutError("QMP deadline")
                    part = connection.recv(1)
                    if not part or len(raw) >= 16384:
                        raise ValueError("QMP framing")
                    raw += part
                value = json.loads(raw)
                if not isinstance(value, dict):
                    raise ValueError("QMP shape")
                if "event" not in value:
                    return value
        connection.settimeout(timeout)
        connection.connect(str(path))
        if "QMP" not in read():
            raise ValueError("QMP greeting")
        connection.sendall(b'{"execute":"qmp_capabilities","id":"hello"}\r\n')
        if "return" not in read():
            raise ValueError("QMP capabilities")
        connection.sendall(b'{"execute":"query-status","id":"status"}\r\n')
        reply = read()
        data = reply.get("return")
        if reply.get("id") != "status" or not isinstance(data, dict) or type(data.get("running")) is not bool:
            raise ValueError("QMP status")
        return {"running": data["running"], "status": safe_word(data["status"])}


def provisioning_forward_states(table, port):
    states = []
    for line in table.splitlines():
        if re.search(r"127\.0\.0\.1\s+" + str(port) + r"\s+10\.0\.0\.100\s+8089\b", line):
            match = re.search(r"TCP\[([A-Z_]+)\]", line)
            states.append(match[1] if match else "UNCLASSIFIED")
    return states


def local_vehicle(config, processes, timeout, network=False):
    if config is None:
        return skipped("HOST_QEMU", "TARGET_NOT_CONFIGURED")
    overlay = config["overlay"]
    try:
        exists = overlay.is_file() and not overlay.is_symlink()
        if overlay.exists() and not exists:
            return observation("HOST_FILESYSTEM", reason="OVERLAY_NOT_REGULAR", transport="MALFORMED")
    except OSError:
        return observation("HOST_FILESYSTEM", reason="OVERLAY_UNREADABLE", transport="SOURCE_UNAVAILABLE")
    facts = {
        "overlay": overlay.name, "overlayExists": exists,
        "configuredImageVersion": config.get("imageVersion"),
        "configuredImageSha256": config.get("imageSha256"),
        "imageDigestChecked": False,
    }
    if processes is None:
        return observation("HOST_QEMU", facts, reason="PROCESS_READ_FAILED", transport="SOURCE_UNAVAILABLE")
    matches = [(pid, args) for pid, args in processes if owns_overlay(args, overlay)]
    if not matches:
        facts["processState"] = "STOPPED" if exists else "NOT_CREATED"
        return observation("HOST_QEMU", facts)
    if len(matches) != 1:
        return observation("HOST_QEMU", facts, reason="AMBIGUOUS_QEMU_OWNER", transport="MALFORMED")
    pid, args = matches[0]
    facts.update({"processState": "RUNNING", "pid": pid})
    if not exists:
        return observation("HOST_QEMU", facts, reason="RUNNING_WITH_MISSING_OVERLAY", transport="MALFORMED")
    try:
        start = args.index("-qmp") + 1
        end = start + 1
        while end < len(args) and not args[end].startswith("-"):
            end += 1
        endpoint = " ".join(args[start:end])
        if not endpoint.startswith("unix:"):
            raise ValueError("Non-local QMP")
        path = Path(endpoint[5:].split(",")[0])
        if not path.is_absolute() or path.is_symlink() or not stat.S_ISSOCK(path.stat().st_mode):
            raise ValueError("Invalid socket")
        facts["qmp"] = observation("QMP_QUERY_STATUS", qmp_status(path, timeout))
        if network and config.get("sshPort") in (10022, 10023):
            from .vm import qmp
            port = 18089 if config["sshPort"] == 10022 else 18090
            table = qmp(path, "human-monitor-command", timeout=min(timeout, 3),
                        arguments={"command-line": "info usernet"})
            facts["provisioningForward"] = {"port": port, "connectionStates": provisioning_forward_states(table, port)}
    except (OSError, ValueError, IndexError, KeyError):
        facts["qmp"] = observation("QMP_QUERY_STATUS", reason="QMP_UNAVAILABLE", transport="SOURCE_UNAVAILABLE")
    return observation("HOST_QEMU", facts)


def _guest_script(config):
    services = " ".join(shlex.quote(s) for s in config["services"])
    host = shlex.quote(config["cloudHost"])
    return (
        "printf '__DEMO_RELEASE__\\n'\n"
        "sed -n 's/^VERSION_ID=//p' /etc/os-release\n"
        "printf '__DEMO_SERVICES__\\n'\n"
        "systemctl show --no-pager --property=Id,LoadState,ActiveState,SubState,Result,NRestarts " + services + "\n"
        "rc=$?; printf '__DEMO_SYSTEMCTL_RC__=%s\\n' \"$rc\"\n"
        "printf '__DEMO_BOOT__\\n'\n"
        "systemctl show -p UserspaceTimestampMonotonic -p FinishTimestampMonotonic\n"
        "systemctl show serial-getty@ttyAMA0.service -p ActiveEnterTimestampMonotonic\n"
        "systemd-analyze time 2>/dev/null | sed 's/^/summary=/'\n"
        "systemd-analyze blame --no-pager 2>/dev/null | head -5 | sed 's/^/slowUnit=/'\n"
        "printf '__DEMO_DNS_CONFIG__\\n'\n"
        "sed -n 's/^nameserver[[:space:]]*/nameserver=/p' /etc/resolv.conf\n"
        "sed -n 's/^server=/upstream=/p' /var/aos/dns/dnsmasq.conf 2>/dev/null\n"
        "ip -4 route show default | sed 's/^/route=/'\n"
        "printf 'dnsmasq='; systemctl is-active dnsmasq.service 2>/dev/null\n"
        "sed -n 's/^server=10\\.0\\.0\\.1#/hostDnsPort=/p' /var/aos/dns/dnsmasq.conf 2>/dev/null\n"
        "timeout 2 busybox nslookup " + host + " >/dev/null 2>&1\n"
        "rc=$?; printf '__DEMO_DNS_RC__=%s\\n' \"$rc\"\n"
        "printf '__DEMO_CM_LOG__\\n'\n"
        "journalctl -u aos-cm.service -n 200 --no-pager -o cat 2>/dev/null\n"
        "printf '__DEMO_CM_PROCESS_LOG__\\n'\n"
        "p=$(systemctl show aos-cm.service -p ExecMainPID --value); case \"$p\" in ''|0|*[!0-9]*) ;; *) journalctl _PID=\"$p\" -n 60 --no-pager -o cat 2>/dev/null;; esac\n"
        "printf '__DEMO_CM_DETAILS__\\n'\n"
        "systemctl show aos-cm.service -p StandardOutput -p StandardError -p SyslogIdentifier -p TimeoutStopUSec -p KillMode -p SendSIGKILL\n"
        "printf '__DEMO_CM_FAILURES__\\n'\n"
        "journalctl -b -u aos-cm.service --no-pager -o cat 2>/dev/null | head -n 500 | grep -E 'Main process exited|Scheduled restart|Failed with result|[Ee]rror|[Ff]ailed|[Pp]anic|terminate|what|[Aa]ssert|[Ee]xception' | tail -n 30\n"
        "printf '__DEMO_CM_CORE__\\n'\n"
        "if command -v coredumpctl >/dev/null 2>&1; then printf 'tool=AVAILABLE\\n'; coredumpctl --no-pager info COREDUMP_UNIT=aos-cm.service 2>/dev/null | head -n 100; else printf 'tool=UNAVAILABLE\\n'; fi\n"
        "printf '__DEMO_CM_START_CONTEXT__\\n'\n"
        "journalctl -b -u aos-cm.service --no-pager -o short-monotonic 2>/dev/null | head -n 500 | awk '{print} /Main process exited/{exit}' | tail -n 80\n"
        "printf '__DEMO_CM_VERSION__\\n'\n"
        "demo_cm_pid=$(systemctl show aos-cm.service -p MainPID --value); case \"$demo_cm_pid\" in ''|0|*[!0-9]*) ;; *) demo_cm_exec=$(readlink /proc/\"$demo_cm_pid\"/exe); case \"$demo_cm_exec\" in */aos_cm_app) timeout 2 \"$demo_cm_exec\" --version 2>/dev/null; sha256sum \"$demo_cm_exec\" | cut -d ' ' -f 1;; esac;; esac\n"
        "printf '__DEMO_SECURITY__\\n'\n"
        "printf 'selinux='; getenforce 2>/dev/null || printf 'UNKNOWN\\n'\n"
        "demo_kernel=$(journalctl -k -b --no-pager -o cat 2>/dev/null); demo_kernel_rc=$?\n"
        "printf 'kernelReadExit=%s\\n' \"$demo_kernel_rc\"\n"
        "printf '%s\\n' \"$demo_kernel\" | awk 'NF && !/^--/ {n++} /avc:[[:space:]]*denied/ {d++} END {printf \"kernelRecords=%d\\nkernelAvcDenials=%d\\n\", n, d}'\n"
        "unset demo_kernel\n"
        "printf '__DEMO_END__\\n'\n"
    )


def parse_guest(stdout, config):
    if len(stdout) > 65536 or "__DEMO_END__" not in stdout:
        raise ValueError("Incomplete guest response")
    release = None
    services = {}
    section = ""
    current = {}
    dns_ok = None
    dns_port = None
    boot = {}
    network = {"nameservers": [], "upstreams": [], "defaultRoutes": [], "queryTool": "busybox nslookup"}
    systemctl_ok = False
    cm_log = []
    cm_process_log = []
    cm_details = {}
    cm_failures = []
    cm_start_context = []
    cm_version = []
    cm_core = {"tool": "NOT_OBSERVED", "frames": []}
    security = {"source": "CURRENT_BOOT_KERNEL_JOURNAL", "selinux": "NOT_OBSERVED"}

    def finish():
        if current.get("Id") in config["services"]:
            services[current["Id"]] = dict(current)
        current.clear()

    for line in stdout.splitlines():
        if line.startswith("__DEMO_"):
            finish()
            section = line
            if line.startswith("__DEMO_DNS_RC__="):
                dns_ok = line == "__DEMO_DNS_RC__=0"
                rc = line.split("=", 1)[1]
                if rc.isdigit():
                    network["queryExit"] = int(rc)
            if line.startswith("__DEMO_SYSTEMCTL_RC__="):
                systemctl_ok = line == "__DEMO_SYSTEMCTL_RC__=0"
            continue
        if section == "__DEMO_RELEASE__" and line:
            release = safe_word(line.strip('"'))
        elif section == "__DEMO_BOOT__" and "=" in line:
            key, value = line.split("=", 1)
            if key in ("UserspaceTimestampMonotonic", "FinishTimestampMonotonic", "ActiveEnterTimestampMonotonic") and value.isdigit():
                boot[key] = int(value) / 1000000
            elif key in ("summary", "slowUnit") and len(value) <= 300 and all(c.isalnum() or c in " .@_-=+()/\\-" for c in value):
                boot.setdefault(key, []).append(value.strip())
        elif section == "__DEMO_SERVICES__":
            if not line:
                finish()
            elif "=" in line:
                key, value = line.split("=", 1)
                if key in ("Id", "LoadState", "ActiveState", "SubState", "Result"):
                    current[key] = safe_word(value) if value else None
                elif key == "NRestarts":
                    current[key] = int(value)
        elif section == "__DEMO_DNS_CONFIG__" and line.startswith("hostDnsPort="):
            dns_port = int(line.split("=", 1)[1])
        elif section == "__DEMO_DNS_CONFIG__" and "=" in line:
            key, value = line.split("=", 1)
            if len(value) <= 200 and all(c.isalnum() or c in " .:/#_-=," for c in value):
                if key in ("nameserver", "upstream", "route"):
                    network[{"nameserver": "nameservers", "upstream": "upstreams", "route": "defaultRoutes"}[key]].append(value)
                elif key == "dnsmasq":
                    network["dnsmasqState"] = value
        elif section == "__DEMO_SECURITY__" and "=" in line:
            key, value = line.split("=", 1)
            if key == "selinux" and value in ("Enforcing", "Permissive", "Disabled", "UNKNOWN"):
                security[key] = value
            elif key in ("kernelReadExit", "kernelRecords", "kernelAvcDenials") and re.fullmatch(r"[0-9]{1,9}", value):
                security[key] = int(value)
        elif section == "__DEMO_CM_LOG__":
            cm_log.append(line)
        elif section == "__DEMO_CM_PROCESS_LOG__":
            cm_process_log.append(line)
        elif section == "__DEMO_CM_FAILURES__":
            cm_failures.append(line)
        elif section == "__DEMO_CM_START_CONTEXT__":
            cm_start_context.append(line)
        elif section == "__DEMO_CM_VERSION__":
            if re.fullmatch(r"(?:Aos CM version:|Aos core library version:) +[A-Za-z0-9_.+-]{1,100}", line) or re.fullmatch(r"[a-f0-9]{64}", line):
                cm_version.append(line)
        elif section == "__DEMO_CM_CORE__":
            if line in ("tool=AVAILABLE", "tool=UNAVAILABLE"):
                cm_core["tool"] = line.split("=", 1)[1]
            frame = re.search(r"#\d+\s+0x[0-9a-f]+\s+([A-Za-z_][A-Za-z0-9_:<>~*., ()&-]{0,180})", line)
            if frame and len(cm_core["frames"]) < 20:
                cm_core["frames"].append(frame[1])
        elif section == "__DEMO_CM_DETAILS__" and "=" in line:
            key, value = line.split("=", 1)
            if key in ("StandardOutput", "StandardError", "SyslogIdentifier", "TimeoutStopUSec", "KillMode", "SendSIGKILL"):
                cm_details[key] = safe_word(value) if value else None
    complete = release is not None and systemctl_ok and set(services) == set(config["services"])
    mode = "UNKNOWN"
    active = lambda name: services.get(name, {}).get("ActiveState") == "active"
    if active("aos-iam-prov.service") and not any(active(s) for s in ("aos-iam.service", "aos-sm.service", "aos-cm.service")):
        mode = "PROVISIONING"
    elif not active("aos-iam-prov.service") and all(active(s) for s in ("aos-iam.service", "aos-sm.service", "aos-cm.service")):
        mode = "NORMAL"
    value = {"ssh": "AUTHENTICATED", "release": release, "mode": mode, "services": services, "bootSeconds": boot,
             "cloudLogObservations": classify_cloud_log("\n".join(cm_log)),
             "cloudProcessLogObservations": classify_cloud_log("\n".join(cm_process_log)),
             "cloudServiceDetails": cm_details,
             "cloudBootFailures": classify_cloud_log("\n".join(cm_failures)),
             "cloudCoreMetadata": cm_core,
             "cloudStartContext": classify_start_context("\n".join(cm_start_context)),
             "cloudBinaryVersion": cm_version, "security": security,
             "dns": {"hostname": config["cloudHost"], "resolved": dns_ok, "guestUpstreamPort": dns_port, **network,
                     "expectedHostPort": config.get("dnsPort"),
                     "portMatches": dns_port == config["dnsPort"] if "dnsPort" in config and dns_port is not None else None},
             "aosCoreConnected": "NOT_OBSERVED"}
    return observation("GUEST_SSH", value, reason=None if complete else "GUEST_FIELDS_INCOMPLETE",
                       state="CURRENT" if complete else "INCOMPLETE")


def classify_start_context(text):
    """Project journal backtrace symbols/stages only; never core memory or payloads."""
    records = text.splitlines()
    lines = [line for line in records if not re.search(r"(?i)(content=|message=|payload=|[{}])", line)]
    text = "\n".join(lines)
    result = {"recordsObserved": len(records), "payloadRecordsExcluded": len(records) - len(lines), "frames": [], "stages": [],
              "terminationWithoutException": "terminate called without an active exception" in text,
              "grpcCallErrors": sorted(set(re.findall(r"\bGRPC_CALL_ERROR_[A-Z_]{1,60}\b", text))),
              "grpcAssertionLocations": sorted(set(re.findall(r"\b(call_op_set\.h:\d+)", text))),
              "assertionFailedFalse": "assertion failed: false" in text.lower()}
    for line in text.splitlines():
        prefix = re.split(r"(?i)content=|message=|payload=|[{}]", line, maxsplit=1)[0]
        frame = re.search(r"/(?:[^\s()]*/)*((?:aos[-_]cm(?:_app)?|lib[A-Za-z0-9_.+-]+))\(([A-Za-z0-9_+:.<>~*-]{0,200})\)\s*\[0x[0-9a-f]+\]", prefix)
        if frame and len(result["frames"]) < 32:
            result["frames"].append({"module": frame[1], "symbolOffset": frame[2]})
        # Only a static logger stage preceding ':'; field values never enter output.
        stage = re.search(r"\(([a-z][a-z0-9_]{1,30})\) ([A-Za-z][A-Za-z '-]{1,75})(?=:|$)", prefix)
        if stage and re.match(r"(?i)(init|initialization|start|stop|create|close|get|read|load|connect|disconnect|send|receive|wait|can't|failed|error|update|register|subscribe)\b", stage[2]):
            item = {"module": stage[1], "stage": stage[2]}
            stamp = re.search(r"\[\s*(\d+\.\d+)\]", line)
            if stamp:
                item["bootSeconds"] = float(stamp[1])
            source = re.search(r"\(([A-Za-z0-9_]+\.cpp):(\d+)\)", line)
            if source:
                item["source"] = source[1] + ":" + source[2]
            result["stages"].append(item)
    result["stages"] = result["stages"][-40:]
    return result


def classify_cloud_log(text):
    """Fixed categories only: never expose URLs, identity, payloads or raw logs."""
    records = text.splitlines()
    lines = [line for line in records if not re.search(r"(?i)(content=|message=|payload=|[{}])", line)]
    text = "\n".join(lines)
    signatures = {
        "AUTHORIZATION_REJECTED": r"(?i)(unauthori[sz]ed|access.?refused|access denied|forbidden)",
        "CERTIFICATE_REJECTED": r"(?i)(bad certificate|certificate (?:revoked|rejected|not found|has expired))",
        "UNIT_NOT_REGISTERED": r"(?i)(not (?:provisioned|registered)|unit (?:is )?not found)",
        "HTTP_401": r"(?i)(?:status|response|http)[^\n]{0,40}\b401\b",
        "HTTP_403": r"(?i)(?:status|response|http)[^\n]{0,40}\b403\b",
        "HTTP_404": r"(?i)(?:status|response|http)[^\n]{0,40}\b404\b",
        "HTTP_500": r"(?i)(?:status|response|http)[^\n]{0,40}\b500\b",
        "CONNECTION_REFUSED": r"(?i)connection refused",
        "CONNECTION_TIMEOUT": r"(?i)(i/o timeout|deadline exceeded|timed out)",
        "TLS_ERROR": r"(?i)(tls:|x509:)",
        "CONNECTION_FAILED": r"(?i)(can't connect|cannot connect|failed to connect|connection failed)",
        "CERTIFICATE_NOT_AVAILABLE": r"(?i)(certificate not available|no certificate|certificate not valid)",
        "SERVICE_STOP": r"(?i)(stopping|stopped|terminat|sigterm)",
        "RUNTIME_TERMINATION": r"(?i)(terminate called|what\(\)|assertion.*failed)",
        "WEBSOCKET_UPGRADE_REJECTED": r"Cannot upgrade to WebSocket connection:",
        "AMQP_AUTH_403": r"(?i)exception\s*\(403\)",
        "AUTHENTICATION_FAILED": r"(?i)(authentication failed|invalid credentials|bad username or password)",
    }
    result = {name: len(re.findall(pattern, text)) for name, pattern in signatures.items() if re.search(pattern, text)}
    result["recordsObserved"] = len(records)
    result["payloadRecordsExcluded"] = len(records) - len(lines)
    result["serviceExits"] = re.findall(r"Main process exited, code=([a-z-]+), status=([0-9]+/[A-Z]+)", text)
    result["serviceExitContexts"] = [{
        "embeddedPayload": bool(re.search(r"(?i)(content=|message=|payload=|[{}])", line)),
        "systemdCmExitLine": bool(re.match(r"^aos-cm\.service: Main process exited,", line))
    } for line in text.splitlines() if "Main process exited, code=" in line][:8]
    result["exceptionTypes"] = sorted(set(re.findall(r"throwing an instance of '([A-Za-z_][A-Za-z0-9_:]*)'", text)))
    # assert() prints the compile-time expression, not object/credential values.
    result["assertionExpressions"] = [expr for expr in re.findall(r"Assertion [`']([^'`\n]+)['`] failed", text)
        if re.fullmatch(r"[A-Za-z0-9_ .:<>!=&|*()+/\[\]-]{1,180}", expr)][:4]
    stages = []
    for message in re.findall(r'\bmsg="([^"\n]+)"', text):
        # Only short static English stage labels, not error/URL/key fields.
        if (re.fullmatch(r"[A-Za-z][A-Za-z .,!?:;()'-]{2,90}", message)
                and re.match(r"(?i)(create|close|start|stop|connect|disconnect|failed|can't|error|receive|send|read|get|set|update|process|init|wait)\b", message)
                and message not in stages):
            stages.append(message)
    result["stageLabels"] = stages[:12]
    result["rpcCodes"] = sorted(set(re.findall(r"code = (Unavailable|Unauthenticated|PermissionDenied|Unimplemented|Internal|Unknown|DeadlineExceeded)\b", text)))
    excerpts = []
    for line in text.splitlines():
        if re.search(r"(?i)(content=|message=|payload=|[{}])", line):
            continue
        if not re.search(r"(?i)(error|fail|connect|discovery|reconnect|stop|start|terminate|what\(\)|assert)", line):
            continue
        if re.search(r"(?i)(password|private|certificate|\bpin\b|\btoken\b|\bkey\b|subject|authorization|-----)", line):
            continue
        line = re.sub(r"https?://\S+|/[A-Za-z0-9_.~/%?=&:+-]+", "[location]", line)
        line = re.sub(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}(?::[0-9]+)?\b", "[host]", line)
        line = re.sub(r"[A-Za-z0-9+/_=-]{16,}|\b[0-9]{4,}\b", "[redacted]", line)
        line = re.sub(r"[^\x20-\x7e]", "", line)
        excerpts.append(line[:220])
    errors = [line for line in excerpts if re.search(r"(?i)(error|fail|terminate|what\(\)|assert)", line)]
    result["redactedConnectionEvents"] = (errors[-8:] if errors else excerpts[-8:])
    return result


def guest_status(config, local, timeout):
    if config is None:
        return skipped("GUEST_SSH", "TARGET_NOT_CONFIGURED")
    facts = local.get("value") or {}
    if facts.get("processState") in ("STOPPED", "NOT_CREATED"):
        return skipped("GUEST_SSH", "VM_NOT_RUNNING")
    if facts.get("processState") != "RUNNING" or local["state"] != "CURRENT":
        return observation("GUEST_SSH", reason="VM_IDENTITY_UNRESOLVED")
    if "sshPort" not in config or "accessRoot" not in config:
        return observation("GUEST_SSH", reason="SSH_NOT_CONFIGURED")
    key = config["accessRoot"] / "aosvm-host-ed25519"
    known = config["accessRoot"] / "known_hosts"
    try:
        for path in (key, known):
            if path.is_symlink() or not stat.S_ISREG(path.stat().st_mode):
                raise ValueError()
        if key.stat().st_mode & 0o077:
            raise ValueError()
    except (OSError, ValueError):
        return observation("GUEST_SSH", reason="SSH_ACCESS_MATERIAL_UNAVAILABLE")
    command = [
        "ssh", "-F", "/dev/null", "-T", "-o", "BatchMode=yes", "-o", "IdentitiesOnly=yes",
        "-o", "IdentityAgent=none", "-o", "StrictHostKeyChecking=yes",
        "-o", "UpdateHostKeys=no", "-o", "GlobalKnownHostsFile=/dev/null",
        "-o", 'UserKnownHostsFile="' + str(known).replace("\\", "\\\\").replace('"', '\\"') + '"',
        "-o", "ConnectionAttempts=1", "-o", "ConnectTimeout=" + str(max(1, math.ceil(timeout))),
        "-o", "ControlMaster=no", "-o", "ControlPath=none", "-o", "ClearAllForwardings=yes",
        "-i", str(key), "-p", str(config["sshPort"]), "root@127.0.0.1", "sh", "-s",
    ]
    try:
        response = subprocess.run(command, input=_guest_script(config), capture_output=True, text=True, timeout=timeout)
        if response.returncode:
            error = response.stderr.lower()
            reason = "SSH_FAILED"
            for text, code in (("host key", "SSH_HOST_KEY_UNVERIFIED"), ("permission denied", "SSH_AUTHENTICATION_FAILED"),
                               ("connection refused", "SSH_CONNECTION_REFUSED"), ("timed out", "SSH_TIMEOUT")):
                if text in error:
                    reason = code
                    break
            return observation("GUEST_SSH", reason=reason, transport="SOURCE_UNAVAILABLE")
        return parse_guest(response.stdout, config)
    except subprocess.TimeoutExpired:
        return observation("GUEST_SSH", reason="SSH_TIMEOUT", transport="SOURCE_UNAVAILABLE")
    except (OSError, ValueError):
        return observation("GUEST_SSH", reason="GUEST_RESPONSE_UNAVAILABLE", transport="SOURCE_UNAVAILABLE")
