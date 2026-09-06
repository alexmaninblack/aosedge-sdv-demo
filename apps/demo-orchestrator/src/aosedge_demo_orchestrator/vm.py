# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Owned QEMU/DNS processes; no lifecycle wrappers, Cloud API or forced VM kill."""

import json
import ctypes
import math
import os
import platform
import shutil
import signal
import socket
import stat
import subprocess
import sys
import time
from pathlib import Path
from uuid import uuid4
from uuid import UUID

from .environment import EnvironmentError, EnvironmentService, JOURNAL, OVERLAYS, atomic_json, digest
from .guest_access import enroll_serial, read_guest
from .status import now, object_id, project_root, read_json

PROFILE = "aos-main-qemuarm64-v1"
FIRMWARE = ".cache/aosvm/v6.1.0/qemuarm64/QEMU_EFI.fd"
FIRMWARE_SHA = "30f7042c23b81c28b8196a76f4af6bcf10046f08049c9d78b4387472c5bbcd10"


def access_path(root, role):
    return root / (".run/demo-current/" + role + "-access")


def qmp(path, command, timeout=3, arguments=None):
    if command not in ("query-status", "system_powerdown", "human-monitor-command", "set_link"):
        raise EnvironmentError("QMP_COMMAND_NOT_ALLOWED")
    if command == "set_link" and (not isinstance(arguments, dict) or set(arguments) != {"name", "up"}
                                    or arguments["name"] != "guestnet" or type(arguments["up"]) is not bool):
        raise EnvironmentError("QMP_LINK_ARGUMENTS_INVALID")
    if command == "human-monitor-command":
        allowed = {"info usernet"}
        for port in (18089, 18090):
            allowed.add("hostfwd_add aosnet tcp:127.0.0.1:" + str(port) + "-10.0.0.100:8089")
            allowed.add("hostfwd_remove aosnet tcp:127.0.0.1:" + str(port))
        if not isinstance(arguments, dict) or set(arguments) != {"command-line"} or arguments["command-line"] not in allowed:
            raise EnvironmentError("QMP_FORWARD_ARGUMENTS_INVALID")
    elif command != "set_link" and arguments is not None:
        raise EnvironmentError("QMP_ARGUMENTS_NOT_ALLOWED")
    with socket.socket(socket.AF_UNIX) as client:
        client.settimeout(timeout)
        client.connect(str(path))
        with client.makefile("rb") as reader:
            def response(expected=None):
                for _ in range(32):
                    raw = reader.readline(65537)
                    if not raw or len(raw) > 65536:
                        raise EnvironmentError("QMP_INVALID_RESPONSE")
                    document = json.loads(raw)
                    if expected is None or document.get("id") == expected:
                        return document
                raise EnvironmentError("QMP_EVENT_LIMIT")
            if "QMP" not in response():
                raise EnvironmentError("QMP_INVALID_GREETING")
            for name in ("qmp_capabilities", command):
                request = {"execute": name, "id": name}
                if name == command and arguments is not None:
                    request["arguments"] = arguments
                client.sendall((json.dumps(request) + "\n").encode())
                value = response(name)
                if "return" not in value:
                    raise EnvironmentError("QMP_COMMAND_FAILED")
            return value["return"]


class VMService:
    def __init__(self, environment=None, password_provider=None, progress=None, assets_root=None):
        self.environment = environment or EnvironmentService()
        self.root = self.environment.root
        self.assets = Path(assets_root) if assets_root else project_root()
        self.password_provider = password_provider
        self.progress = progress or (lambda message: None)
        self.children = []

    def _paths(self, role):
        directory = self.root / ".run/demo-current"
        return directory / (role + ".qmp"), directory / (role + ".serial")

    def _command(self, state, role):
        item = state["vehicles"][role]
        monitor, serial = self._paths(role)
        if len(os.fsencode(serial)) >= 104 or any(
                any(c in str(p) for c in (",", "\n")) for p in (self.root, self.assets)):
            raise EnvironmentError("VM_PATH_NOT_SUPPORTED_BY_QEMU")
        executable = shutil.which("qemu-system-aarch64")
        if not executable:
            raise EnvironmentError("QEMU_NOT_INSTALLED")
        return [executable, "-name", "democtl-" + role + "-" + item["localVmId"],
                "-machine", "virt-11.0,accel=hvf", "-cpu", "host", "-smp", "2", "-m", "2048",
                "-nodefaults", "-bios", str(self.assets / FIRMWARE), "-uuid", item["localVmId"],
                "-drive", "file=" + str(self.root / item["overlay"]) + ",if=none,id=aos-image,format=qcow2,cache=writeback",
                "-device", "virtio-scsi-pci,id=scsi", "-device", "scsi-hd,drive=aos-image,bootindex=0",
                "-netdev", "user,id=aosnet,net=10.0.0.0/24,host=10.0.0.1,dns=10.0.0.2,restrict=off,hostfwd=tcp:127.0.0.1:"
                + str(item["sshPort"]) + "-10.0.0.100:22",
                "-device", "virtio-net-pci,id=guestnet,netdev=aosnet,mac=" + item["mac"],
                "-chardev", "socket,id=serial0,path=" + str(serial) + ",server=on,wait=off",
                "-serial", "chardev:serial0", "-qmp", "unix:" + str(monitor) + ",server=on,wait=off",
                "-monitor", "none", "-display", "none"]

    def _processes(self):
        result = subprocess.run(["ps", "-axo", "pid=,stat=,args="], capture_output=True, text=True, timeout=5)
        if result.returncode:
            raise EnvironmentError("PROCESS_OBSERVATION_UNAVAILABLE")
        rows = []
        for line in result.stdout.splitlines():
            parts = line.strip().split(None, 2)
            if len(parts) == 3 and parts[0].isdigit() and not parts[1].startswith("Z"):
                rows.append((int(parts[0]), parts[2]))
        return rows

    def _owned_pid(self, command, discriminator):
        rows = [(pid, args) for pid, args in self._processes() if discriminator in args]
        accepted = {" ".join(command)}
        if platform.system() == "Darwin" and command[0] == sys.executable and "--owner-id" in command:
            # Framework Python re-execs Python.app on macOS. Resolve this
            # interpreter's native executable, not an arbitrary observed prefix.
            size = ctypes.c_uint32(4096)
            path = ctypes.create_string_buffer(size.value)
            executable_path = ctypes.CDLL(None)._NSGetExecutablePath
            executable_path.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint32)]
            executable_path.restype = ctypes.c_int
            if executable_path(path, ctypes.byref(size)) == 0:
                accepted.add(" ".join([os.path.realpath(os.fsdecode(path.value))] + command[1:]))
        if len(rows) > 1 or (rows and rows[0][1] not in accepted):
            raise EnvironmentError("VM_PROCESS_OWNER_CONTRADICTORY")
        return rows[0][0] if rows else None

    def _spawn(self, command):
        child = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL, start_new_session=True, close_fds=True)
        self.children.append(child)
        return child.pid

    def _save(self, state):
        atomic_json(self.root / JOURNAL, state)

    def _validate(self, state, action, roles):
        if (state.get("kind") != "democtl.current-run" or state.get("schemaVersion") != 1
                or state.get("stage") not in ("MANUFACTURED", "LOCAL_ACTIVE", "LOCAL_STOPPED")
                or not isinstance(state.get("vehicles"), dict)):
            raise EnvironmentError("VM_CURRENT_RUN_UNSUPPORTED")
        if any(role not in state["vehicles"] for role in roles):
            raise EnvironmentError("VM_TARGET_NOT_CREATED")
        if action == "stop" and state.get("currentVehicle") in roles:
            raise EnvironmentError("CURRENT_VEHICLE_REQUIRES_PARK_OR_DETACH")
        if action == "stop" and state.get("source", {}).get("operation"):
            raise EnvironmentError("SOURCE_OPERATION_RECONCILIATION_REQUIRED")
        operations = state.get("operations", [])
        if (not operations or operations[0].get("class") != "LOCAL_CREATE"
                or operations[0].get("state") != "COMPLETED"
                or any(op.get("class") not in ("LOCAL_CREATE", "VM_START", "VM_STOP", "UNIT_LIFECYCLE") for op in operations)):
            raise EnvironmentError("VM_OPERATION_RECONCILIATION_REQUIRED")
        for role, item in state["vehicles"].items():
            if role not in OVERLAYS or item.get("overlay") != OVERLAYS[role]:
                raise EnvironmentError("VM_OVERLAY_BINDING_INVALID")
            object_id(item["localVmId"])
            expected_mac = "02:" + ":".join("%02x" % b for b in UUID(item["localVmId"]).bytes[:5])
            if item.get("mac") != expected_mac:
                raise EnvironmentError("VM_MAC_BINDING_INVALID")
            if item.get("sshPort") != (10022 if role == "test" else 10023):
                raise EnvironmentError("VM_SSH_BINDING_INVALID")
        descriptor = read_json(self.root / state["factory"]["manifestPath"])
        if digest(self.root / state["factory"]["manifestPath"]) != state["factory"]["manifestSha256"]:
            raise EnvironmentError("VM_FACTORY_MANIFEST_CHANGED")
        # The initial profile is a variant binding, not a version selector.
        if not descriptor.get("sourceSelector", "").endswith("/main-qemuarm64"):
            raise EnvironmentError("VM_RUNTIME_PROFILE_UNSUPPORTED")
        for role in roles:
            item = state["vehicles"][role]
            if action == "start" and item.get("cloud", {}).get("lifecycle") in ("DEPROVISIONED", "DELETED"):
                raise EnvironmentError("RETIRED_VM_REQUIRES_FRESH_FACTORY_OVERLAY")
            self.environment._owned_file(self.root / item["overlay"])
            item.setdefault("runtime", {"profile": PROFILE, "state": "STOPPED", "everStarted": False,
                                        "accessCreated": False, "stopProof": None})
            if item["runtime"].get("profile") != PROFILE:
                raise EnvironmentError("VM_RUNTIME_PROFILE_UNSUPPORTED")
            self._command(state, role)

    def _host_profile(self):
        if platform.system() != "Darwin" or platform.machine() != "arm64":
            raise EnvironmentError("VM_REQUIRES_MACOS_ARM64_HVF")
        firmware = self.assets / FIRMWARE
        if firmware.is_symlink() or not firmware.is_file() or digest(firmware) != FIRMWARE_SHA:
            raise EnvironmentError("PINNED_QEMU_FIRMWARE_UNAVAILABLE")
        binary = shutil.which("qemu-system-aarch64")
        if not binary:
            raise EnvironmentError("QEMU_NOT_INSTALLED")
        version = subprocess.run([binary, "--version"], capture_output=True, text=True, timeout=3)
        if not any(version.stdout.startswith("QEMU emulator version " + value + "\n")
                   for value in ("11.0.3", "11.1.0")):
            raise EnvironmentError("QEMU_VERSION_OUTSIDE_ACCEPTED_PROFILE")

    def _free_port(self, port, udp=False):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM if udp else socket.SOCK_STREAM) as probe:
            if not udp:
                # Match QEMU's reusable TCP listener. TIME_WAIT from the last
                # SSH session is not a live owner; an active listener still blocks.
                probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                probe.bind(("127.0.0.1", port))
            except OSError:
                raise EnvironmentError("VM_OR_DNS_PORT_IN_USE") from None

    def _dns_command(self, state):
        return [sys.executable, str(self.assets / "scripts/host/aosvm-dns-bridge"),
                "--listen-port", "18053", "--owner-id", state["shared"]["dns"]["ownerId"]]

    def _start_dns(self, state):
        # The isolated single-Test Factory qualification retains the canonical
        # Production runtime. Reuse its exact, byte-matched bridge as a read-only
        # dependency; never claim ownership or accept an arbitrary port listener.
        owner_root = self.root.parent / "aosedge-sdv-demo"
        owner_journal = owner_root / JOURNAL
        if (self.root != owner_root and self.root.name.startswith("aosedge-sdv-demo-qual-")
                and state.get("scope") == "SINGLE_ROLE_ENGINEERING"
                and set(state["vehicles"]) == {"test"} and owner_journal.is_file()):
            owner = read_json(owner_journal)
            reference = owner.get("shared", {}).get("dns", {})
            script = owner_root / "scripts/host/aosvm-dns-bridge"
            if (owner.get("kind") != "democtl.current-run" or reference.get("state") != "RUNNING"
                    or reference.get("ownership") == "EXTERNAL_DEPENDENCY" or script.is_symlink()
                    or digest(script) != digest(self.assets / "scripts/host/aosvm-dns-bridge")):
                raise EnvironmentError("QUALIFICATION_DNS_OWNER_NOT_PROVEN")
            identity = object_id(reference["ownerId"])
            command = [sys.executable, str(script), "--listen-port", "18053", "--owner-id", identity]
            pid = self._owned_pid(command, identity)
            if pid is None or pid != reference.get("pid"):
                raise EnvironmentError("QUALIFICATION_DNS_OWNER_NOT_RUNNING")
            state.setdefault("shared", {})["dns"] = dict(ownerId=identity, state="RUNNING", pid=pid,
                ownership="EXTERNAL_DEPENDENCY", ownerRoot=str(owner_root))
            self._save(state)
            self.progress("DNS: using the existing canonical bridge; its owner and Production are unchanged")
            return
        dns = state.setdefault("shared", {}).setdefault("dns", {"ownerId": str(uuid4()), "state": "STOPPED"})
        if dns.get("ownership") == "EXTERNAL_DEPENDENCY":
            raise EnvironmentError("QUALIFICATION_DNS_OWNER_NOT_PROVEN")
        command = self._dns_command(state)
        pid = self._owned_pid(command, dns["ownerId"])
        if pid is None:
            self._free_port(18053)
            self._free_port(18053, udp=True)
            dns["state"] = "STARTING"
            self._save(state)
            pid = self._spawn(command)
        dns.update(state="RUNNING", pid=pid)
        self._save(state)

    def _stop_dns(self, state):
        dns = state.get("shared", {}).get("dns")
        if not dns:
            return
        if dns.get("ownership") == "EXTERNAL_DEPENDENCY":
            return
        for role in state["vehicles"]:
            if self._owned_pid(self._command(state, role), str(self.root / OVERLAYS[role])):
                return
        command = self._dns_command(state)
        pid = self._owned_pid(command, dns["ownerId"])
        if pid:
            os.kill(pid, signal.SIGTERM)
            deadline = time.monotonic() + 5
            while self._owned_pid(command, dns["ownerId"]):
                if time.monotonic() >= deadline:
                    raise EnvironmentError("DNS_STOP_TIMEOUT")
                time.sleep(0.1)
        dns.update(state="STOPPED", pid=None)
        self._save(state)

    def _remove_sockets(self, role):
        for path in self._paths(role):
            if path.exists() or path.is_symlink():
                if not stat.S_ISSOCK(path.lstat().st_mode) or path.stat().st_uid != os.getuid():
                    raise EnvironmentError("VM_SOCKET_NOT_OWNED")
                path.unlink()

    def execute(self, action, target, timeout=90):
        if action not in ("start", "stop") or target not in ("test", "production", "all"):
            raise EnvironmentError("VM_ACTION_INVALID")
        if not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or not 0 < timeout <= 300:
            raise EnvironmentError("VM_TIMEOUT_INVALID")
        results = {}
        infrastructure = {"state": "COMPLETED"}
        with self.environment._writer():
            state = read_json(self.root / JOURNAL)
            roles = tuple(role for role in OVERLAYS if role in state.get("vehicles", {})) if target == "all" else (target,)
            if not roles:
                raise EnvironmentError("VM_TARGET_NOT_CREATED")
            self._validate(state, action, roles)
            for operation in state["operations"][1:]:
                if operation.get("class") == "UNIT_LIFECYCLE":
                    raise EnvironmentError("UNIT_OPERATION_RECONCILIATION_REQUIRED")
                previous = operation.get("target", [])
                if not previous or any(role not in roles for role in previous):
                    raise EnvironmentError("VM_PREVIOUS_TARGETS_REQUIRE_RECONCILIATION")
                for role in previous:
                    self._owned_pid(self._command(state, role), str(self.root / OVERLAYS[role]))
            passwords = {}
            if action == "start":
                self._host_profile()
                for role in roles:
                    if not (access_path(self.root, role) / "known_hosts").exists() and self.password_provider:
                        passwords[role] = self.password_provider(role)
            state["operations"] = state["operations"][:1] + [{
                "id": str(uuid4()), "class": "VM_" + action.upper(), "team": "DEMO_SOLUTION",
                "authority": "LOCAL_OPERATOR", "target": list(roles), "knownExternalIds": {},
                "requestFingerprint": action + ":" + target, "resourceKeys": ["CURRENT_RUN"],
                "state": "SUBMITTING", "reconciliation": "UNOBSERVABLE", "lastRead": None}]
            self._save(state)
            launch_errors = {}
            started_at = {}
            if action == "start":
                # One journal writer launches both independent VMs first;
                # they boot concurrently while readiness is observed in order.
                for role in roles:
                    started_at[role] = time.monotonic()
                    try:
                        self._launch(state, role)
                    except (OSError, ValueError, subprocess.SubprocessError) as error:
                        launch_errors[role] = error
            for role in roles:
                started = started_at.get(role, time.monotonic())
                try:
                    if role in launch_errors:
                        raise launch_errors[role]
                    result = self._start(state, role, timeout, passwords.get(role)) if action == "start" else self._stop(state, role, timeout)
                except (OSError, ValueError, subprocess.SubprocessError) as error:
                    result = {"state": "BLOCKED", "processState": state["vehicles"][role]["runtime"]["state"],
                              "reason": str(error) if isinstance(error, EnvironmentError) else "VM_OPERATION_UNAVAILABLE"}
                result["durationSeconds"] = round(time.monotonic() - started, 2)
                results[role] = result
                self._save(state)
            if action == "stop":
                try:
                    self._stop_dns(state)
                except (OSError, ValueError, subprocess.SubprocessError) as error:
                    infrastructure = {"state": "BLOCKED", "reason": str(error) if isinstance(error, EnvironmentError) else "DNS_STOP_UNAVAILABLE"}
            state["stage"] = "LOCAL_ACTIVE" if any(
                item.get("runtime", {}).get("state") in ("RUNNING", "STARTING", "STOPPING") for item in state["vehicles"].values()
            ) else "LOCAL_STOPPED"
            if infrastructure["state"] == "COMPLETED" and all(item["state"] == "COMPLETED" for item in results.values()):
                state["operations"] = state["operations"][:1]
            else:
                state["operations"][-1]["state"] = "UNCERTAIN"
            self._save(state)
        return {"vehicles": results, "infrastructure": infrastructure, "cloudActions": False, "currentVehicleChanged": False}

    def _launch(self, state, role):
        item = state["vehicles"][role]
        runtime = item["runtime"]
        command = self._command(state, role)
        pid = self._owned_pid(command, str(self.root / item["overlay"]))
        if pid is None:
            self.environment._assert_unheld(self.root / item["overlay"])
            info = self.environment._info(self.root / item["overlay"])
            if info.get("backing-filename") != str(self.root / state["factory"]["path"]):
                raise EnvironmentError("VM_OVERLAY_BACKING_CHANGED")
            self._free_port(item["sshPort"])
            self._remove_sockets(role)
            self._start_dns(state)
            runtime.update(state="STARTING", stopProof=None)
            state["stage"] = "LOCAL_ACTIVE"
            self._save(state)
            pid = self._spawn(command)
        else:
            self._start_dns(state)
        runtime.update(state="RUNNING", pid=pid, everStarted=True, stopProof=None)
        self._save(state)
        self.progress(role + ": VM process running")

    def _initialize_factory_role(self, state, role):
        from .source import SourceDriver
        driver = SourceDriver(self)
        with driver.operation(timeout=10):
            return driver.guest(state, role, "factory-role")

    def _start(self, state, role, timeout, password):
        item = state["vehicles"][role]
        runtime = item["runtime"]
        command = self._command(state, role)
        self.progress(role + ": VM process running; waiting for console/SSH/DNS readiness")
        deadline = time.monotonic() + timeout
        monitor, serial = self._paths(role)
        guest = {"guestReady": False, "guestDnsReady": False}
        while time.monotonic() < deadline:
            if self._owned_pid(command, str(self.root / item["overlay"])) is None:
                raise EnvironmentError("VM_EXITED_DURING_START")
            try:
                running = qmp(monitor, "query-status")["status"] == "running"
                access = access_path(self.root, role)
                if running and password is not None and not (access / "known_hosts").exists() and serial.exists():
                    self.environment._directory(str(access.relative_to(self.root)))
                    runtime["accessCreated"] = True
                    self._save(state)
                    enroll_serial(serial, access, item["sshPort"], deadline, password,
                                  progress=lambda stage: self.progress(role + ": " + stage))
                if (access / "known_hosts").exists():
                    guest = read_guest(access, item["sshPort"], min(5, max(1, deadline - time.monotonic())))
                elif running and password is None:
                    return {"state": "PARTIAL", "processState": "RUNNING", "reason": "SSH_ENROLLMENT_REQUIRES_INTERACTIVE_PASSWORD",
                            "sshPort": item["sshPort"]}
                if guest["guestReady"] and guest["guestDnsReady"]:
                    if guest.get("unprovisioned"):
                        guest["factoryRole"] = self._initialize_factory_role(state, role)
                    return {"state": "COMPLETED", "processState": "RUNNING", **guest,
                            "sshPort": item["sshPort"], "access": str(access.relative_to(self.root))}
            except EnvironmentError:
                raise
            except (OSError, ValueError):
                pass
            time.sleep(0.25)
        return {"state": "PARTIAL", "processState": "RUNNING", **guest, "reason": "GUEST_OR_DNS_NOT_READY", "sshPort": item["sshPort"]}

    def _stop(self, state, role, timeout):
        item = state["vehicles"][role]
        runtime = item["runtime"]
        command = self._command(state, role)
        pid = self._owned_pid(command, str(self.root / item["overlay"]))
        if pid is None:
            self.environment._assert_unheld(self.root / item["overlay"])
            runtime.update(state="STOPPED", pid=None)
            self._remove_sockets(role)
            return {"state": "COMPLETED", "processState": "STOPPED", "alreadyStopped": True}
        runtime.update(state="STOPPING", everStarted=True, stopProof=None)
        self._save(state)
        self.progress(role + ": requesting graceful shutdown")
        guest = read_guest(access_path(self.root, role), item["sshPort"], min(8, timeout), shutdown=True)
        runtime["shutdownUnprovisioned"] = guest["guestReady"] and guest["unprovisioned"]
        self._save(state)
        if not guest["guestReady"]:
            qmp(self._paths(role)[0], "system_powerdown")
        deadline = time.monotonic() + timeout
        while self._owned_pid(command, str(self.root / item["overlay"])):
            if time.monotonic() >= deadline:
                raise EnvironmentError("VM_STOP_TIMEOUT_NO_FORCE_USED")
            time.sleep(0.25)
        self.environment._assert_unheld(self.root / item["overlay"])
        runtime.update(state="STOPPED", pid=None)
        if runtime["shutdownUnprovisioned"]:
            runtime["stopProof"] = {"unprovisioned": True, "readCompletedAt": now(),
                                    "overlaySha256": digest(self.root / item["overlay"])}
        self._remove_sockets(role)
        return {"state": "COMPLETED", "processState": "STOPPED", "unprovisionedProof": runtime["stopProof"] is not None}
