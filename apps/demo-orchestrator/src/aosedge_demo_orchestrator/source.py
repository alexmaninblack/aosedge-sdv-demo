# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Local-demo source lifecycle; one existing Controller owns every CARLA tick."""

import json
import os
import re
import signal
import socket
import stat
import subprocess
import sys
import time
import tempfile
from contextlib import contextmanager
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4

from .environment import EnvironmentError, JOURNAL, atomic_json
from .guest_access import ssh_command
from .status import read_json, now
from .vm import access_path

TRUST = {"trustProfile": "LOCAL_DEMO_SERVER_TLS", "perUnitMtls": "DEFERRED"}
TRAFFIC_MANAGER_PORT = 18000


class SourceDriver:
    def __init__(self, vm):
        self.vm, self.root = vm, vm.root
        self.progress = vm.progress
        self._session = None
        self._deadline = None
        self._connections = {}

    @contextmanager
    def operation(self, timeout=None):
        # Short, owner-only sockets; reused only in this invocation. Abrupt
        # termination also expires idle masters, never a persistent service.
        with tempfile.TemporaryDirectory(prefix="democtl-ssh-", dir="/tmp") as directory:
            self._session = Path(directory)
            self._deadline = time.monotonic() + timeout if timeout else None
            try:
                yield
            finally:
                for command in self._connections.values():
                    try:
                        subprocess.run(command[:-3] + ["-O", "exit", command[-3]],
                            capture_output=True, timeout=2)
                    except (OSError, subprocess.TimeoutExpired):
                        pass
                self._connections.clear()
                self._session = self._deadline = None

    def budget(self, limit):
        remaining = limit if self._deadline is None else min(limit, self._deadline - time.monotonic())
        if remaining <= 0:
            raise EnvironmentError("SOURCE_READ_TIMEOUT")
        return remaining

    def assets(self):
        manifest = read_json(self.root / "workspace/repositories.json")
        paths = {entry["id"]: ((self.root.parent if entry["base"] == "workspace" else Path.home()) / entry["path"])
                 for entry in manifest["launcherPaths"]}
        paths.update(project=paths["carla-root"] / "Unreal/CarlaUnreal/CarlaUnreal.uproject",
            config=paths["runtime-root"] / "config/m6_2_town10hd_handover.json",
            runner=paths["runtime-root"] / "tools/run_m6_interactive.py",
            keyboard=paths["keyboard-app"] / "Contents/MacOS/KeyboardControl",
            runtime=paths["runtime-build"] / "carla-ego-runtime",
            client=paths["runtime-build"] / "carla-viss-client",
            ca=paths["tls"] / "server-cert.pem", key=paths["tls"] / "server-key.pem")
        for key in ("python", "unreal-editor", "project", "config", "runner", "keyboard", "runtime", "client", "ca", "key"):
            if not paths[key].is_file():
                raise EnvironmentError("SOURCE_ASSET_UNAVAILABLE:" + key)
        return paths

    def guest(self, state, role, action, **extra):
        from . import source_guest
        worker = source_guest
        if action == "service-runtime-prepare":
            from . import service_inputs_guest
            worker = service_inputs_guest
        elif action == "service-runtime-activate":
            from . import service_activation_guest
            worker = service_activation_guest
        code = Path(worker.__file__).read_text()
        vehicle = dict(state["vehicles"][role], sourceProbeSelected=state.get("currentVehicle") == role)
        request = dict(action=action, vehicle=vehicle, role=role, **extra)
        script = "python3 - <<'DEMOCTL_SOURCE_PY'\n" + code + "\nmain(" + repr(request) + ")\nDEMOCTL_SOURCE_PY\n"
        try:
            timeout = self.budget(110 if action == "service-runtime-activate" else 60 if action in ("component-sm-apply", "component-cm-apply") else 25)
            command = ssh_command(access_path(self.root, role), state["vehicles"][role]["sshPort"], min(5, timeout))
            if self._session:
                command = ["ControlMaster=auto" if arg == "ControlMaster=no" else
                    "ControlPath=" + str(self._session / role) if arg == "ControlPath=none" else arg
                    for arg in command]
                command[1:1] = ["-o", "ControlPersist=10"]
                self._connections[role] = command
            result = subprocess.run(command, input=script, text=True, capture_output=True, timeout=timeout)
            if result.returncode or len(result.stdout) > 65536:
                raise EnvironmentError("SOURCE_GUEST_UNAVAILABLE:" + role)
            value = json.loads(result.stdout)
            if not value.get("ok"):
                raise EnvironmentError(value.get("reason", "SOURCE_GUEST_FAILED") + ":" + role)
            return value["data"]
        except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError):
            raise EnvironmentError("SOURCE_GUEST_UNAVAILABLE:" + role) from None

    def guests(self, state, action, configure_role=None, roles=None):
        roles = list(state["vehicles"]) if roles is None else list(roles)
        if not roles or set(roles) - set(state["vehicles"]):
            raise EnvironmentError("SOURCE_GUEST_SCOPE_INVALID")
        def read(role):
            command = self.vm._command(state, role)
            if not self.vm._owned_pid(command, "democtl-" + role + "-" + state["vehicles"][role]["localVmId"]):
                return dict(gate="BLOCKED", gateEvidence="VM_PROCESS_ABSENT", vdpProcess="VM_STOPPED",
                    vdpData="NOT_OBSERVED", serverTls=False)
            if role == configure_role:
                return self.guest(state, role, "configure_status", generation=1, ca=self.assets()["ca"].read_text())
            return self.guest(state, role, action)
        with ThreadPoolExecutor(max_workers=2) as pool:
            jobs = {role: pool.submit(read, role) for role in roles}
            return {role: job.result() for role, job in jobs.items()}

    def rpc(self, source, operation, identity):
        directory = self.root / source["controlDirectory"]
        token = directory / "control.token"
        info = token.lstat()
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()
                or info.st_mode & 0o077 or info.st_nlink != 1):
            raise EnvironmentError("SOURCE_CONTROL_TOKEN_UNSAFE")
        request_id = str(uuid4())
        request = dict(version=3, action="orchestrate", requestId=request_id,
            token=token.read_text().strip(), operation=operation, operationId=identity)
        with socket.socket(socket.AF_UNIX) as client:
            client.settimeout(self.budget(3))
            client.connect(str(directory / "control.sock"))
            client.sendall((json.dumps(request) + "\n").encode())
            with client.makefile("rb") as stream:
                raw = stream.readline(16385)
            if len(raw) > 16384:
                raise EnvironmentError("SOURCE_CONTROL_RESPONSE_INVALID")
            value = json.loads(raw)
        if value.get("requestId") != request_id or value.get("status") != "ok":
            raise EnvironmentError("SOURCE_CONTROL_REJECTED:" + str(value.get("error", {}).get("code", "UNKNOWN")))
        frame = value.get("frame")
        if frame and frame.get("runId") != source["runId"]:
            raise EnvironmentError("SOURCE_CONTROL_RUN_MISMATCH")
        return value

    def wait(self, source, identity, phase, timeout=20):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            value = self.rpc(source, "status", identity)
            frame = value.get("frame") or {}
            stopped = (frame.get("activeMode") == ("MANUAL" if phase == "MANUAL_READY" else "SAFE_STOP") and frame.get("speedKmh", float("inf")) <= .5
                       and frame.get("brake", -1) >= .99)
            if value.get("operationId") == identity and value.get("phase") == phase and value.get("fresh") and stopped:
                return value
            time.sleep(.1)
        raise EnvironmentError("SOURCE_COMPLETED_FRAME_TIMEOUT:" + phase)

    def live_process(self, command):
        # Framework Python can re-exec Python.app. The exact script/arguments
        # and unique owned run path remain the process discriminator.
        suffix = " ".join(command[1:])
        matches = [(pid, args) for pid, args in self.vm._processes() if args.endswith(" " + suffix)]
        if len(matches) > 1:
            raise EnvironmentError("SOURCE_PROCESS_OWNER_AMBIGUOUS")
        return matches[0][0] if matches else None

    def spawn(self, command, log):
        fd = os.open(log, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, "w") as stream:
            process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=stream, stderr=stream,
                start_new_session=True, close_fds=True)
        self.vm.children.append(process)
        return process.pid

    def ready(self, state):
        source = state.get("source")
        if not source or not self.live_process(source["simulatorCommand"]):
            raise EnvironmentError("SIMULATION_NOT_RUNNING")
        if source["state"] != "RUNNING" or not self.live_process(source["runnerCommand"]):
            raise EnvironmentError("SIMULATION_NOT_READY")
        try:
            frame = self.rpc(source, "status", str(uuid4()))
            with socket.create_connection(("127.0.0.1", 16443), timeout=self.budget(.3)):
                pass
            if not frame.get("fresh"):
                raise ValueError("stale")
            return frame
        except (OSError, ValueError):
            raise EnvironmentError("SIMULATION_NOT_READY") from None

    def stop(self, source):
        for key in ("runnerCommand", "simulatorCommand"):
            command = source[key]
            pid = self.live_process(command)
            if not pid:
                continue
            self.progress("Simulation: stopping " + ("Controller/Gateway/UI" if key == "runnerCommand" else "CARLA"))
            os.kill(pid, signal.SIGTERM)
            deadline = time.monotonic() + 30
            while self.live_process(command):
                if time.monotonic() >= deadline:
                    raise EnvironmentError("SIMULATION_STOP_TIMEOUT:" + key)
                time.sleep(.2)
        # The runner owns its children and performs their normal cleanup.
        # Do not mark stopped while a listener/control endpoint is left behind.
        for port in (2000, 16443):
            self.vm._free_port(port)
        if (self.root / source["controlDirectory"] / "control.sock").exists():
            raise EnvironmentError("SIMULATION_CONTROL_CLEANUP_INCOMPLETE")
        from .workspace import close_terminal
        try:
            close_terminal(source)
        except (EnvironmentError, OSError, subprocess.SubprocessError):
            self.progress("Simulation stopped; its inactive dashboard window could not be closed")

    def start(self, state):
        previous = None
        if state.get("source"):
            source = state["source"]
            if self.live_process(source["runnerCommand"]):
                self.ready(state)
                return source
            previous = source
            if source["state"] == "STOPPED":
                if state.get("currentVehicle") or source.get("operation") or self.live_process(source["simulatorCommand"]):
                    raise EnvironmentError("SOURCE_STOPPED_STATE_CONTRADICTORY")
            else:
                manifest = read_json(self.root / source["runDirectory"] / "manifest.json")
                if (source["state"] != "STARTING" or source["assignmentGeneration"] != 0
                    or source.get("operation") or state.get("currentVehicle") is not None
                    or manifest.get("status") != "failed"
                    or (self.root / source["controlDirectory"] / "control.sock").exists()
                    or any(v["gate"] != "BLOCKED" for v in self.guests(state, "status").values())):
                    raise EnvironmentError("SOURCE_PREVIOUS_RUN_NOT_RUNNING_RECONCILE_REQUIRED")
        paths = self.assets()
        from .workspace import prepare_controller
        prepare_controller(paths, self.progress)
        # The fixed .28 client URI has no host listener. Without its owned
        # redirect (including after reboot) it cannot reach the Gateway.
        self.vm._free_port(6443)
        self.vm._free_port(16443)
        # The generic CARLA sample's 8000 conflicts with unrelated local web
        # applications. This demo owns one explicit TM endpoint, never adopts
        # or stops another port owner and never searches for a random port.
        try:
            self.vm._free_port(TRAFFIC_MANAGER_PORT)
        except EnvironmentError:
            raise EnvironmentError("SOURCE_TRAFFIC_MANAGER_PORT_IN_USE") from None
        if not previous:
            self.vm._free_port(2000)
        identity = str(uuid4())
        run = self.root / ".run/demo-current/source" / identity
        control = self.root / ".run/demo-current/control"
        self.vm.environment._directory(str(run.relative_to(self.root)))
        self.vm.environment._directory(str(control.relative_to(self.root)))
        if len(os.fsencode(control / "control.sock")) >= 104:
            raise EnvironmentError("SOURCE_CONTROL_PATH_TOO_LONG")
        config = read_json(paths["config"])
        config["controller"]["autopilot"]["traffic_manager_port"] = TRAFFIC_MANAGER_PORT
        config["simulation"]["fixed_delta_seconds"] = .05
        config["runtime"].update(viss_port=16443, chase_camera_update_hz=20)
        atomic_json(run / "input.json", config)
        simulator = [str(paths["unreal-editor"]), str(paths["project"]), "/Game/Carla/Maps/Town10HD_Opt",
            "-game", "-windowed", "-ResX=1100", "-ResY=700", "-WinX=20", "-WinY=70",
            "-quality-level=Low", "-nosound", "-carla-rpc-port=2000"]
        runner = [str(paths["python"]), str(paths["runner"]), "--config", str(run / "input.json"),
            "--runtime", str(paths["runtime"]), "--viss-client", str(paths["client"]),
            "--python", str(paths["python"]), "--python-api-root", str(paths["carla-root"] / "PythonAPI/carla"),
            "--certificate", str(paths["ca"]), "--private-key", str(paths["key"]),
            "--keyboard-ui", str(paths["keyboard"]), "--run-directory", str(run),
            "--control-directory", str(control), "--started-timestamp", str(time.time()),
            "--demo-journal", str(self.root / JOURNAL),
            "--connectivity-command", json.dumps([sys.executable, "-m", "aosedge_demo_orchestrator",
                "--output", "json", "vehicle", "connectivity"])]
        runner.append("--viss-development")
        source = dict(runId=identity, controlDirectory=str(control.relative_to(self.root)),
            runDirectory=str(run.relative_to(self.root)), simulatorCommand=simulator, runnerCommand=runner,
            state="STARTING", assignmentGeneration=0, operation=None, nativeTelemetry=True)
        state["source"] = source
        self.vm._save(state)
        if previous and previous["simulatorCommand"] != simulator:
            raise EnvironmentError("SOURCE_SIMULATOR_OWNER_CHANGED")
        if previous and self.live_process(simulator):
            self.progress("CARLA: reusing the exact owned simulator after reconciled startup failure")
        else:
            self.vm._free_port(2000)
            self.progress("CARLA: starting the owned simulator")
            self.spawn(simulator, run / "simulator.log")
        deadline = time.monotonic() + 120
        probe_code = "import sys; sys.path.insert(0,sys.argv[1]); import carla; c=carla.Client('127.0.0.1',2000); c.set_timeout(2); print(c.get_world().get_map().name)"
        while time.monotonic() < deadline:
            if not self.live_process(simulator):
                raise EnvironmentError("SOURCE_SIMULATOR_EXITED")
            probe = subprocess.run([str(paths["python"]), "-c", probe_code,
                str(paths["carla-root"] / "PythonAPI/carla")], capture_output=True, text=True, timeout=6)
            if probe.returncode == 0 and probe.stdout.strip() == config["carla"]["expected_map"]:
                break
            time.sleep(1)
        else:
            raise EnvironmentError("SOURCE_SIMULATOR_READY_TIMEOUT")
        self.progress("CARLA: starting Controller, Gateway and keyboard UI")
        self.spawn(runner, run / "runner.log")
        self.vm._save(state)
        return self.finish_start(state)

    def finish_start(self, state):
        source = state["source"]
        runner = source["runnerCommand"]
        run = self.root / source["runDirectory"]
        deadline = time.monotonic() + 90
        launch_deadline = time.monotonic() + 5
        seen = False
        while time.monotonic() < deadline:
            if not self.live_process(runner):
                # Process appearance is startup observation, not a second
                # launch or a retry.
                if not seen and time.monotonic() < launch_deadline:
                    time.sleep(.1)
                    continue
                raise EnvironmentError("SOURCE_RUNNER_EXITED")
            seen = True
            try:
                value = self.rpc(source, "status", str(uuid4()))
                timeline = read_json(run / "startup-timeline.json")
                if value.get("fresh") and any(s.get("stage") == "keyboard_ready" for s in timeline.get("stages", [])):
                    source["state"] = "RUNNING"
                    self.vm._save(state)
                    return source
            except (OSError, ValueError):
                pass
            time.sleep(.25)
        raise EnvironmentError("SOURCE_READY_TIMEOUT")

    def startup_diagnostic(self, source):
        """Fixed startup facts only; never expose runner payloads or paths."""
        base = self.root / ".run/demo-current/source"
        run = self.root / source.get("runDirectory", "")
        if run.is_symlink() or run.parent.resolve() != base.resolve():
            return {"reason": "SOURCE_DIAGNOSTIC_PATH_UNSAFE"}
        observed = []
        for name in ("startup-timeline.json", "controller-status.json", "manifest.json", "runner.log", "events.jsonl"):
            path = run / name
            try:
                if path.is_symlink() or not path.is_file():
                    continue
                with path.open("rb") as stream:
                    stream.seek(max(0, path.stat().st_size - 65536))
                    observed.append(stream.read(65536).decode("utf-8", errors="replace"))
            except OSError:
                continue
        text = "\n".join(observed)
        stages = [stage for stage in ("interactive_orchestrator_started", "vehicle_ready",
            "first_vss_frame", "viss_verified", "keyboard_ready", "interactive_failed",
            "interactive_cleanup_complete") if '"stage": "' + stage + '"' in text
            or '"stage":"' + stage + '"' in text]
        failures = [code for needle, code in (
            ("ModuleNotFoundError", "PYTHON_MODULE_MISSING"),
            ("ImportError", "PYTHON_IMPORT_FAILED"),
            ("Permission denied", "PERMISSION_DENIED"),
            ("Operation not permitted", "OPERATION_NOT_PERMITTED"),
            ("Address already in use", "ADDRESS_IN_USE"),
            ("No such file or directory", "FILE_NOT_FOUND"),
            ("File exists", "FILE_EXISTS"),
            ("std::exception", "CARLA_NATIVE_EXCEPTION"),
            ("local control server failed to start", "CONTROL_SOCKET_START_FAILED"),
            ("timed out", "TIMEOUT"),
            ("external controller did not become ready", "CONTROLLER_NOT_READY"),
            ("independent VISS start probe failed", "VISS_PROBE_FAILED"),
            ("before the keyboard-control window", "NATIVE_CONTROL_EXITED"),
            ("before the first VSS frame", "TELEMETRY_EXITED"),
            ("run directory is already in use", "RUN_DIRECTORY_IN_USE"),
            ("SyntaxError", "PYTHON_SYNTAX_ERROR"),
            ("configured vehicle blueprint lacks required control attributes", "VEHICLE_BLUEPRINT_INVALID"),
            ("CARLA client/server version mismatch", "CARLA_VERSION_MISMATCH"),
            ("an existing hero vehicle already exists", "EXISTING_HERO_VEHICLE"),
            ("an existing brake-event obstacle already exists", "EXISTING_BRAKE_OBSTACLE"),
            ("external-control spawn point is unavailable", "SPAWN_POINT_UNAVAILABLE"),
            ("is occupied", "SPAWN_POINT_OCCUPIED"),
            ("the scenario start is not on a driving lane", "SCENARIO_START_NOT_DRIVING_LANE"),
        ) if needle in text]
        lines = re.findall(r'"controller_line"\s*:\s*([0-9]{1,5})\b', text)
        listener = {"state": "NOT_OBSERVED"}
        try:
            config = run / "input.json"
            if config.is_symlink() or config.stat().st_size > 65536:
                raise ValueError()
            port = read_json(config)["controller"]["autopilot"]["traffic_manager_port"]
            if type(port) is not int or not 1024 <= port <= 65535:
                raise ValueError()
            result = subprocess.run(["lsof", "-nP", "-iTCP:" + str(port), "-sTCP:LISTEN", "-Fpc"],
                                    capture_output=True, text=True, timeout=3)
            listener = dict(port=port, state="LISTENING" if result.returncode == 0 else
                "NO_LISTENER" if result.returncode == 1 else "UNAVAILABLE",
                dockerOwner=any(line.startswith("ccom.docker") for line in result.stdout.splitlines()))
        except (OSError, ValueError, KeyError, subprocess.SubprocessError):
            pass
        return dict(stages=stages, failures=failures, controllerLine=int(lines[-1]) if lines else None,
                    trafficManager=listener,
                    evidence="BOUNDED_LOCAL_STARTUP_RECORDS",
                    rawOutputExposed=False)


class SourceService:
    def __init__(self, vm, units, driver=None):
        self.vm, self.units = vm, units
        self.environment, self.root = vm.environment, vm.root
        self.driver = driver or SourceDriver(vm)
        self.progress = vm.progress

    def cloud(self, state, roles):
        self.units.owner_id = state["cloudBinding"]["ownerId"]
        inventory = self.units._cloud("inventory")
        sets = self.units._bindings(state, inventory)
        result = {}
        for role in roles:
            item = state["vehicles"][role]
            units = [u for u in inventory["units"] if u["id"] == item.get("unitId")]
            if len(units) != 1 or units[0]["online_status"] != "Online" or units[0]["status"] != "provisioned":
                raise EnvironmentError("SOURCE_UNIT_NOT_ONLINE:" + role)
            if {u["id"] for u in sets[role]["members"]} != {item["unitId"]}:
                raise EnvironmentError("SOURCE_UNIT_SET_MISMATCH:" + role)
            result[role] = "Online"
        return result

    def prepare(self, target, current):
        with self.environment._writer():
            state = read_json(self.root / JOURNAL)
            roles = list(state["vehicles"]) if target == "all" else [target]
            self.vm._validate(state, "start", roles)
            self.driver.assets()  # small path/config preflight, never image hashes
            started = self.vm.execute("start", target, 90)
            if any(x["state"] != "COMPLETED" for x in started["vehicles"].values()):
                raise EnvironmentError("SOURCE_VM_START_INCOMPLETE")
            provisioned = self.units.execute("provision", target)
            if any(x["state"] != "COMPLETED" for x in provisioned["vehicles"].values()):
                raise EnvironmentError("SOURCE_UNIT_PROVISION_INCOMPLETE")
            self.simulation("start")
            return self.select(current)

    def _detach(self, state, target=None):
        if target is None:
            return self.driver.guests(state, "block")
        # Studio may retain a running Production VM. Read its existing gate,
        # never rewrite it to satisfy a Test-only operation.
        views = self.driver.guests(state, "status")
        if any(view.get("gate") != "BLOCKED" for role, view in views.items() if role != target):
            raise EnvironmentError("SOURCE_PRESERVED_PEER_NOT_DETACHED")
        selected = self.driver.guests(state, "block", roles=[target])
        views.update(selected)
        return views

    def simulation(self, action, target=None):
        with self.environment._writer(), self.driver.operation():
            state = read_json(self.root / JOURNAL)
            if target is not None and (target != "test" or target not in state["vehicles"]
                    or state.get("currentVehicle") not in (None, target)):
                raise EnvironmentError("SOURCE_TEST_SCOPE_CONFLICT")
            source = state.get("source")
            if target is not None and action == "stop" and source and source.get("state") != "STOPPED":
                peer_views = self.driver.guests(state, "status")
                if any(view.get("gate") != "BLOCKED" for role, view in peer_views.items() if role != target):
                    raise EnvironmentError("SOURCE_PRESERVED_PEER_NOT_DETACHED")
            if action == "start":
                if source and (source.get("operation") or source.get("stopOperation")):
                    raise EnvironmentError("SOURCE_OPERATION_RECONCILIATION_REQUIRED")
                if source and self.driver.live_process(source["runnerCommand"]):
                    if source["state"] == "STARTING":
                        self.driver.finish_start(state)
                    frame = self.driver.ready(state)
                    if frame.get("held"):
                        raise EnvironmentError("SIMULATION_NOT_READY")
                    return dict(state="RUNNING", noOp=True, currentVehicle=state.get("currentVehicle"), controller=frame)
                if source and source["state"] not in ("STOPPED", "STARTING"):
                    raise EnvironmentError("SIMULATION_NOT_READY:run simulation stop to reconcile the previous session")
                views = self._detach(state, target)
                if any(v["gate"] != "BLOCKED" for v in views.values()):
                    raise EnvironmentError("SOURCE_DETACH_NOT_CONFIRMED")
                source = self.driver.start(state)
                result = dict(state="RUNNING", noOp=False, currentVehicle=None, runId=source["runId"])
                if (state.get("workspace") or {}).get("profile") == "builtin-v1":
                    from .workspace import WorkspaceService
                    try:
                        result["workspace"] = WorkspaceService(self.environment, self.driver).execute("restore")
                    except (EnvironmentError, OSError, ValueError, subprocess.SubprocessError):
                        result["workspace"] = dict(state="INCOMPLETE", problems=["Run democtl workspace restore"])
                return result
            if action != "stop":
                raise EnvironmentError("SIMULATION_ACTION_INVALID")
            if not source:
                return dict(state="STOPPED", noOp=True, currentVehicle=None)
            if source.get("operation"):
                pending = source["operation"]
                if (not pending.get("initialManual") or state.get("currentVehicle") is not None
                        or source.get("assignmentGeneration") != 0):
                    raise EnvironmentError("SOURCE_OPERATION_RECONCILIATION_REQUIRED")
                observed = self.driver.rpc(source, "status", pending["id"])
                frame = observed.get("frame") or {}
                if (observed.get("operationId") != pending["id"] or not observed.get("held")
                        or not observed.get("fresh") or frame.get("activeMode") != "SAFE_STOP"
                        or frame.get("speedKmh", float("inf")) > .5 or frame.get("brake", 0) < .99):
                    raise EnvironmentError("SOURCE_INITIALIZATION_CANCEL_REQUIRES_SAFE_STOP")
                self.progress("Simulation: interrupted initialization is physically stopped; detaching both paths")
                views = self._detach(state, target)
                if any(v["gate"] != "BLOCKED" for v in views.values()):
                    raise EnvironmentError("SOURCE_DETACH_NOT_CONFIRMED")
                source["stopOperation"] = dict(id=pending["id"], phase="DETACHED", physicalStop="CONFIRMED")
                source["operation"] = None
                source["state"] = "STOPPING"
                self.vm._save(state)
            if source["state"] == "STOPPED":
                if state.get("currentVehicle") or source.get("stopOperation"):
                    raise EnvironmentError("SOURCE_STOPPED_STATE_CONTRADICTORY")
                if any(self.driver.live_process(source[key]) for key in ("runnerCommand", "simulatorCommand")):
                    raise EnvironmentError("SOURCE_STOPPED_STATE_CONTRADICTORY")
                return dict(state="STOPPED", noOp=True, currentVehicle=None)
            operation = source.setdefault("stopOperation", dict(id=str(uuid4()), phase="SAFE_STOP_REQUESTED"))
            self.vm._save(state)
            physical = operation.get("physicalStop", "NOT_OBSERVED")
            if operation["phase"] == "SAFE_STOP_REQUESTED":
                controller_absent_during_start = (source["state"] == "STARTING"
                    and state.get("currentVehicle") is None
                    and not (self.root / source["controlDirectory"] / "control.sock").exists())
                if self.driver.live_process(source["runnerCommand"]) and not controller_absent_during_start:
                    self.progress("Simulation: Safe Stop; confirming physical stop before detach")
                    self.driver.rpc(source, "safe_stop", operation["id"])
                    self.driver.wait(source, operation["id"], "SAFE_STOP")
                    physical = "CONFIRMED"
                else:
                    self.progress("Simulation: Controller absent; physical stop not observed")
                views = self._detach(state, target)
                if any(v["gate"] != "BLOCKED" for v in views.values()):
                    raise EnvironmentError("SOURCE_DETACH_NOT_CONFIRMED")
                state["currentVehicle"] = None
                source.pop("lastConnectionConfirmation", None)
                operation.update(phase="DETACHED", physicalStop=physical)
                source["state"] = "STOPPING"
                self.vm._save(state)
            self.driver.stop(source)
            source.update(state="STOPPED", stoppedAt=now())
            source.pop("stopOperation", None)
            self.vm._save(state)
            return dict(state="STOPPED", noOp=False, currentVehicle=None, physicalStop=physical)

    def initialize_test(self):
        return self.select("test", initial_manual=True)

    def select(self, role, initial_manual=False):
        with self.environment._writer(), self.driver.operation():
            state = read_json(self.root / JOURNAL)
            previous = state.get("currentVehicle")
            if previous and previous != role and (state["vehicles"][previous].get("runtime", {}).get("externalConnectivity") or {}).get("state") not in (None, "ON"):
                raise EnvironmentError("RESTORE_CURRENT_VEHICLE_CONNECTIVITY_BEFORE_HANDOVER")
            self.driver.ready(state)  # fail promptly, before VM/Cloud/guest work
            self.vm._validate(state, "start", [role])
            if state["source"].get("stopOperation"):
                raise EnvironmentError("SIMULATION_NOT_READY")
            item = state["vehicles"][role]
            if not initial_manual and (item.get("cloud", {}).get("lifecycle") != "ONLINE"
                    or not all(item.get(key) for key in ("unitId", "nodeId", "unitSetId"))):
                raise EnvironmentError("SOURCE_UNIT_PROVISION_REQUIRED:" + role)
            return self._select(state, role, configure=True, initial_manual=initial_manual)

    def _select(self, state, role, configure=False, initial_manual=False):
        source = state["source"]
        pending = source.get("operation")
        if pending and pending["target"] != role:
            raise EnvironmentError("SOURCE_OPERATION_RECONCILIATION_REQUIRED")
        self.driver.vm._free_port(6443)
        views = (self.driver.guests(state, "status", configure_role=role) if configure
                 else self.driver.guests(state, "status"))
        old = state.get("currentVehicle")
        if initial_manual and (role != "test" or (old is not None and old != role)
                or (old is None and source.get("assignmentGeneration", 0) != 0)):
            raise EnvironmentError("INITIAL_MANUAL_REQUIRES_FIRST_TEST_CONNECTION")
        if pending and bool(pending.get("initialManual")) != initial_manual:
            raise EnvironmentError("SOURCE_OPERATION_MODE_CHANGED")
        expected = {r: "OPEN" if r == old else "BLOCKED" for r in state["vehicles"]}
        if not pending and any(v["gate"] != expected[r] for r, v in views.items()):
            raise EnvironmentError("SOURCE_LIVE_ASSIGNMENT_CONTRADICTORY")
        if old == role and not pending:
            frame = self.driver.rpc(source, "status", str(uuid4()))
            data = self.driver.guest(state, role, "probe")
            if not frame.get("fresh") or frame.get("held") or not data.get("serverTls"):
                raise EnvironmentError("SOURCE_EXISTING_ASSIGNMENT_NOT_READY")
            return dict(TRUST, currentVehicle=role, noOp=True, vehicles=views, controller=frame,
                connection=data, assignmentGeneration=source["assignmentGeneration"])
        identity = pending["id"] if pending else str(uuid4())
        phase = None
        if pending:
            observed = self.driver.rpc(source, "status", identity)
            if observed.get("operationId") == identity:
                phase = observed["phase"]
            elif pending["phase"] != "SAFE_STOP_REQUESTED" or observed.get("held"):
                raise EnvironmentError("SOURCE_OPERATION_OWNER_MISMATCH")
            self.progress("Source: reconciling the same operation from Controller and guest gates")
        else:
            source["operation"] = dict(id=identity, target=role, previous=old, phase="SAFE_STOP_REQUESTED", initialManual=initial_manual)
            self.vm._save(state)
        if phase not in ("RESETTING", "RESET", "MANUAL_PREPARING", "MANUAL_READY", "RELEASED"):
            self.progress("Source: Safe Stop; waiting for a completed stopped frame")
            self.driver.rpc(source, "safe_stop", identity)
            self.driver.wait(source, identity, "SAFE_STOP")
            blocked = self._detach(state, "test" if initial_manual else None)
            for r, result in blocked.items():
                views[r].update(result)  # action includes verified nft readback
            if any(v["gate"] != "BLOCKED" for v in views.values()):
                raise EnvironmentError("SOURCE_DETACH_NOT_CONFIRMED")
            state["currentVehicle"] = None
            source["operation"]["phase"] = "DETACHED"
            self.vm._save(state)
            self.progress("Source: both data paths blocked; resetting the CARLA scene")
            self.driver.rpc(source, "reset", identity)
        elif any(v["gate"] != "BLOCKED" for r, v in views.items() if r != role):
            raise EnvironmentError("SOURCE_PEER_NOT_DETACHED")
        if phase == "RESETTING" and any(v["gate"] != "BLOCKED" for v in views.values()):
            raise EnvironmentError("SOURCE_RESET_WITH_OPEN_PATH")
        if phase == "RELEASED":
            if state.get("currentVehicle") != role or views[role]["gate"] != "OPEN":
                raise EnvironmentError("SOURCE_RELEASED_ASSIGNMENT_CONTRADICTORY")
            frame = observed
        else:
            if phase not in ("MANUAL_PREPARING", "MANUAL_READY"):
                frame = self.driver.wait(source, identity, "RESET")
            if initial_manual:
                self.driver.rpc(source, "manual_ready", identity)
                frame = self.driver.wait(source, identity, "MANUAL_READY")
            source["operation"]["phase"] = "RESET_CONFIRMED"
            self.vm._save(state)
            views[role].update(self.driver.guest(state, role, "allow"))
        if any(v["gate"] != ("OPEN" if r == role else "BLOCKED") for r, v in views.items()):
            raise EnvironmentError("SOURCE_ATTACHMENT_NOT_EXCLUSIVE")
        try:
            data = self.driver.guest(state, role, "probe")
        except (OSError, ValueError, subprocess.SubprocessError):
            self.driver.guest(state, role, "block")
            raise
        if not data.get("serverTls"):
            self.driver.guest(state, role, "block")
            raise EnvironmentError("SOURCE_SELECTED_DATA_NOT_READY:" + data.get("reason", "UNKNOWN"))
        source["operation"]["phase"] = "ATTACHED"
        state["currentVehicle"] = role
        self.vm._save(state)
        released = self.driver.rpc(source, "release_manual" if initial_manual else "release", identity)
        if released.get("held") or released.get("phase") != "RELEASED":
            raise EnvironmentError("SOURCE_HOLD_RELEASE_UNCONFIRMED")
        source.update(assignmentGeneration=source["assignmentGeneration"] + 1, operation=None,
            lastConnectionConfirmation=dict(role=role, confirmedAt=now(), runId=source.get("runId"),
                serverTls=True, initialManual=initial_manual, advancingVissFrames=data.get("advancingVissFrames", False)))
        self.vm._save(state)
        self.progress("Source: " + role + (" connected in stationary Manual; ready for Autopilot then Safe Stop" if initial_manual else " connected; car remains in Safe Stop"))
        return dict(TRUST, currentVehicle=role, noOp=False, vehicles=views,
            controller=frame, connection=data, assignmentGeneration=source["assignmentGeneration"])

    def observe(self, guest=False, timeout=8):
        with self.driver.operation(timeout=timeout):
            return self._observe(guest)

    def _observe(self, guest):
        state = read_json(self.root / JOURNAL)
        if not state.get("source"):
            return dict(TRUST, state="NOT_PREPARED", currentVehicle=None)
        source = state["source"]
        value = dict(TRUST, state="UNKNOWN", journalCurrentVehicle=state.get("currentVehicle"),
            selectedVehicle=state.get("currentVehicle"), lastConnectionConfirmation=source.get("lastConnectionConfirmation"),
            connectionObservation="LIVE_REQUESTED" if guest else "NOT_REQUESTED",
            operation=source.get("operation") or source.get("stopOperation"),
            assignmentGeneration=source["assignmentGeneration"], readCompletedAt=now())
        try:
            value["controller"] = self.driver.ready(state)
            if not guest:
                value.update(state="SELECTED_NOT_PROBED" if state.get("currentVehicle") else "RUNNING_UNASSIGNED")
                return value
            views = self.driver.guests(state, "observe")
            value["vehicles"] = views
            opened = [r for r, v in views.items() if v["gate"] == "OPEN"]
            if (len(opened) == 1 and opened[0] == state.get("currentVehicle")
                    and all(v["gate"] in ("OPEN", "BLOCKED") for v in views.values())):
                value["connection"] = views[opened[0]].get("connection", {})
                if value["connection"].get("serverTls") and value["controller"].get("fresh") and not source.get("operation"):
                    value["currentVehicle"] = opened[0]
                    value["state"] = "CONNECTED"
            elif not opened and all(v["gate"] == "BLOCKED" for v in views.values()):
                value.update(state="DETACHED", currentVehicle=None)
        except EnvironmentError as error:
            value["reason"] = str(error)
            if str(error) in ("SIMULATION_NOT_READY", "SIMULATION_NOT_RUNNING"):
                value["startupDiagnostic"] = self.driver.startup_diagnostic(source)
            if str(error) == "SIMULATION_NOT_RUNNING":
                value["state"] = "STOPPED" if source["state"] == "STOPPED" else "NOT_RUNNING"
        except (OSError, ValueError, subprocess.SubprocessError):
            value["reason"] = "SOURCE_LIVE_OBSERVATION_UNAVAILABLE"
        finally:
            value["readCompletedAt"] = now()
        return value
