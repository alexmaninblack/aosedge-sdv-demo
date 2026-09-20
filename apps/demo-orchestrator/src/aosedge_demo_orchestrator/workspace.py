# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Built-in-display composition only. No VM, Cloud, vehicle or release actions."""
import json
import os
import re
import shlex
import signal
import subprocess
import time
import threading
from datetime import datetime, timezone
from pathlib import Path

from .environment import EnvironmentError, JOURNAL, atomic_json
from .status import read_json, now


def geometry(screen, combined=False):
    x, y, width, height = (int(screen[k]) for k in ("x", "y", "width", "height"))
    if width < 1440 or height < 900:
        raise EnvironmentError("WORKSPACE_DISPLAY_TOO_SMALL")
    gap, margin, header = 8, 8, 76
    usable = width - 2 * margin
    # The accepted compact profile matches CARLA's 914px width on the
    # built-in 2056px display. Preserve dashboard width; give space reclaimed
    # from the Controller to the Platform panel, not to another empty gutter.
    previous_left = (usable - gap) // 2
    left = round((usable - gap) * .45)
    top = y + margin + header + gap
    body = height - 2 * margin - header - gap
    carla = round((body - gap) * .55)
    lower = body - carla - gap
    dashboard = (previous_left - gap) // 2
    controller = max(360, left - gap - dashboard)
    dashboard = left - gap - controller
    result = dict(backdrop=[x, y, width, height], header=[x + margin, y + margin, usable, header],
        browser=[x + margin + left + gap, top, usable - left - gap, body],
        carla=[x + margin, top, left, carla],
        controller=[x + margin, top + carla + gap, controller, lower],
        dashboard=[x + margin + controller + gap, top + carla + gap, dashboard, lower])
    if combined:
        result["controller"][2] = left
        del result["dashboard"]
    return result


def applescript(script, timeout=15):
    result = subprocess.run(["/usr/bin/osascript", "-e", script], capture_output=True, text=True, timeout=timeout)
    if result.returncode:
        code = re.search(r"\((-?\d+)\)\s*$", result.stderr.strip())
        reason = "WORKSPACE_ACCESSIBILITY_REQUIRED" if ("assistive access" in result.stderr or "-25211" in result.stderr) else "WORKSPACE_AUTOMATION_REQUIRED" if "-1743" in result.stderr else "WORKSPACE_WINDOW_OPERATION_FAILED" + (":" + code[1] if code else "")
        if "WINDOW_NOT_UNIQUE:" in result.stderr:
            count = re.search(r"WINDOW_NOT_UNIQUE:(\d+)", result.stderr)
            reason = "WORKSPACE_WINDOW_COUNT:" + (count[1] if count else "unknown")
        raise EnvironmentError(reason)
    return result.stdout.strip()


def window(pid, rectangle=None, title=None):
    if not isinstance(pid, int) or pid <= 0:
        raise EnvironmentError("WORKSPACE_WINDOW_OWNER_INVALID")
    action = ""
    if rectangle:
        x, y, width, height = map(int, rectangle)
        action = f'''set value of attribute "AXMinimized" of w to false
set size of w to {{{width}, {height}}}
set position of w to {{{x}, {y}}}
perform action "AXRaise" of w'''
    selector = "windows of p" if title is None else f"(windows of p whose name is {json.dumps(title, ensure_ascii=False)})"
    value = applescript(f'''tell application "System Events"
set p to first application process whose unix id is {pid}
set ws to {selector}
if (count ws) is not 1 then error "WINDOW_NOT_UNIQUE:" & (count ws)
set w to item 1 of ws
{action}
return {{position, size}} of w
end tell''', timeout=3)
    rectangle = [int(part.strip()) for part in value.split(",")]
    if len(rectangle) != 4 or rectangle[2] <= 0 or rectangle[3] <= 0:
        raise EnvironmentError("WORKSPACE_GEOMETRY_INVALID")
    return rectangle


def prepare_controller(paths, progress):
    source = paths["runtime-root"] / "tools/KeyboardControl.swift"
    if paths["keyboard"].stat().st_mtime >= source.stat().st_mtime:
        return
    progress("Workspace: compiling the changed native Controller only")
    result = subprocess.run(["/usr/bin/xcrun", "swiftc", "-O", str(source), "-o", str(paths["keyboard"]),
                             "-framework", "AppKit"], capture_output=True, timeout=60)
    if result.returncode:
        raise EnvironmentError("WORKSPACE_CONTROLLER_BUILD_FAILED")
    signed = subprocess.run(["/usr/bin/codesign", "--force", "--deep", "--sign", "-", str(paths["keyboard-app"])],
                            capture_output=True, timeout=15)
    if signed.returncode:
        raise EnvironmentError("WORKSPACE_CONTROLLER_SIGN_FAILED")


def launch_terminal(command, log, run_id):
    # The existing runner and its ONE dashboard render directly in a native PTY.
    # Only stderr is captured; live terminal output is not copied to a log file.
    fd = os.open(log, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    os.close(fd)
    shell = "exec " + shlex.join(command) + " 2>" + shlex.quote(str(log))
    title = "Engineering Telematics — " + run_id[:8]
    value = applescript(f'''tell application "Terminal"
set t to do script {json.dumps(shell, ensure_ascii=False)}
set custom title of t to {json.dumps(title, ensure_ascii=False)}
set title displays custom title of t to true
set font name of t to "Menlo"
set font size of t to 12
set w to front window
if custom title of selected tab of w is not {json.dumps(title, ensure_ascii=False)} then error "OWNED_TERMINAL_NOT_FOUND"
return id of w
end tell''')
    return int(value)


def close_terminal(source):
    terminal = source.get("terminalWindowId")
    if not isinstance(terminal, int) or terminal <= 0:
        return
    title = "Engineering Telematics — " + source["runId"][:8]
    applescript(f'''tell application "Terminal"
if not (exists window id {terminal}) then return
set w to window id {terminal}
if (count tabs of w) is not 1 then return
if custom title of selected tab of w is not {json.dumps(title, ensure_ascii=False)} then return
if busy of selected tab of w then return
close w
end tell''')


class WorkspaceService:
    def __init__(self, environment, driver):
        self.environment, self.driver = environment, driver
        self.root = environment.root
        self.directory = self.root / ".local/demo-control/workspace"
        self.binary = self.directory / "Demo Presenter"

    def build(self):
        source = Path(__file__).parent / "native/PresenterWorkspace.swift"
        self.directory.mkdir(parents=True, exist_ok=True)
        if self.binary.exists() and self.binary.stat().st_mtime >= source.stat().st_mtime:
            return
        self.driver.progress("Workspace: compiling the native Presenter window host")
        result = subprocess.run(["/usr/bin/xcrun", "swiftc", "-O", str(source), "-o", str(self.binary),
            "-framework", "AppKit", "-framework", "WebKit"], capture_output=True, timeout=60)
        if result.returncode:
            raise EnvironmentError("WORKSPACE_PRESENTER_BUILD_FAILED")

    def cached(self):
        path = self.root / JOURNAL
        state = read_json(path) if path.exists() else {}
        placement = (state.get("workspace") or {}).get("placement") or {}
        if placement.get("runId") != (state.get("source") or {}).get("runId"):
            return {}
        result = {key: placement[key] for key in ("state", "observedAt", "retryPending", "problems") if key in placement}
        if placement.get("orderingGeneration"):
            result["zOrder"] = self.ordering(placement["orderingGeneration"], placement.get("hostPid"))
            if result.get("state") == "PLACED_AWAITING_VISUAL_REVIEW" and result["zOrder"]["state"] != "VERIFIED":
                result.update(state="INCOMPLETE", problems=["WORKSPACE_Z_ORDER_NOT_VERIFIED"])
        return result

    def ordering(self, generation, pid):
        path = self.directory / "ordering.json"
        try:
            value = read_json(path) if path.exists() else {}
            stamp = datetime.fromisoformat(value["observedAt"].replace("Z", "+00:00"))
            age = (datetime.now(timezone.utc) - stamp).total_seconds()
            if value.get("generation") != generation or value.get("presenterPid") != pid or not 0 <= age <= 15:
                raise ValueError("STALE_ORDERING")
            if value.get("state") not in ("VERIFIED", "UNAVAILABLE", "BACKGROUND_ABOVE_DEMO", "WAITING_FOR_UNLOCK"):
                raise ValueError("INVALID_ORDERING")
            return {key: value[key] for key in ("state", "observedAt", "repairs") if key in value}
        except (OSError, ValueError, KeyError, TypeError):
            return dict(state="UNAVAILABLE")

    def record(self, state, result, attempt, pending):
        result.update(observedAt=now(), retryPending=pending)
        record = state.setdefault("workspace", {})
        record["placement"] = dict(result, attempt=attempt, runId=(state.get("source") or {}).get("runId"))
        atomic_json(self.root / JOURNAL, state)
        return result

    def execute(self, action, *, recovery=False):
        if action not in ("restore", "status", "close"):
            raise EnvironmentError("WORKSPACE_ACTION_INVALID")
        with self.environment._writer():
            state = read_json(self.root / JOURNAL) if (self.root / JOURNAL).exists() else {}
            source = state.get("source") or {}
            previous = (state.get("workspace") or {}).get("placement") or {}
            attempt = previous.get("attempt", 0) + 1 if recovery else 0
            if recovery and (not previous.get("retryPending") or previous.get("runId") != source.get("runId")
                             or (state.get("workspace") or {}).get("profile") != "builtin-v1"):
                return self.cached()
            if action == "close":
                command = [str(self.binary), "present", str(self.directory / "layout.json")]
                pid = self.driver.live_process(command)
                if pid:
                    os.kill(pid, signal.SIGTERM)
                    deadline = time.monotonic() + 3
                    while self.driver.live_process(command):
                        if time.monotonic() >= deadline:
                            raise EnvironmentError("WORKSPACE_PRESENTER_CLOSE_TIMEOUT")
                        time.sleep(.1)
                result = dict(state="CLOSED", noOp=not bool(pid), problems=[], surfaces={}, lifecycleChanged=False)
                return self.record(state, result, 0, False) if state else result
            if action == "restore":
                self.build()
            elif not self.binary.exists():
                return dict(state="NOT_PREPARED", problems=["Run democtl workspace restore"], surfaces={})
            result = subprocess.run([str(self.binary), "screen"], capture_output=True, text=True, timeout=5)
            if result.returncode:
                raise EnvironmentError("WORKSPACE_BUILTIN_DISPLAY_UNAVAILABLE")
            screen = json.loads(result.stdout)
            if screen.get("desktopState") != "UNLOCKED":
                pending = screen.get("desktopState") in ("LOCKED", "INACTIVE")
                outcome = dict(state="WAITING_FOR_UNLOCK" if pending else "INCOMPLETE",
                    problems=["WORKSPACE_DESKTOP_LOCKED" if pending else "WORKSPACE_DESKTOP_STATE_UNKNOWN"],
                    surfaces={}, lifecycleChanged=False)
                if action == "status":
                    return outcome
                if recovery and previous.get("state") == outcome["state"]:
                    return self.cached()  # Waiting consumes no readiness attempt and no journal writes.
                return self.record(state, outcome, previous.get("attempt", 0) if recovery else 0, pending)
            combined = source.get("nativeTelemetry") is True
            layout = geometry(screen, combined=combined)
            record = state.get("workspace") or {}
            surfaces, problems, foreground_pids = {}, [], []
            retryable = True
            host_command = [str(self.binary), "present", str(self.directory / "layout.json")]
            if recovery and not self.driver.live_process(host_command):
                return self.record(state, dict(state="INCOMPLETE", problems=["WORKSPACE_PRESENTER_CLOSED"],
                    surfaces={}, lifecycleChanged=False), attempt, False)
            processes = self.driver.vm._processes()
            for name in ("carla", "controller"):
                if name == "carla":
                    pid = self.driver.live_process(source["simulatorCommand"]) if source.get("simulatorCommand") else None
                else:
                    control = str(self.root / source.get("controlDirectory", "missing"))
                    runner = source.get("runnerCommand") or []
                    keyboard = runner[runner.index("--keyboard-ui") + 1] if "--keyboard-ui" in runner else None
                    matches = [pid for pid, args in processes if keyboard and args.startswith(keyboard + " ") and control in args]
                    pid = matches[0] if len(matches) == 1 else None
                    if len(matches) > 1:
                        retryable = False
                if not pid:
                    problems.append(name + ": window owner absent or ambiguous")
                    continue
                foreground_pids.append(pid)
                try:
                    actual = window(pid, layout[name] if action == "restore" else None,
                                    title=("CARLA — Driving Control & Telemetry" if combined else "CARLA — Live Driving Control") if name == "controller" else None)
                    surfaces[name] = dict(actual=actual, expected=layout[name])
                    if any(abs(a - b) > 3 for a, b in zip(actual, layout[name])):
                        problems.append(name + ": geometry differs")
                except EnvironmentError as error:
                    problems.append(name + ": " + str(error))
                    if str(error) != "WORKSPACE_WINDOW_COUNT:0":
                        retryable = False
                except subprocess.TimeoutExpired:
                    problems.append(name + ": window observation timed out")
                    retryable = False
            terminal = source.get("terminalWindowId")
            if combined:
                surfaces["dashboard"] = dict(embeddedIn="controller", dataEvidence="NOT_PROBED_BY_LAYOUT")
            elif isinstance(terminal, int):
                r = layout["dashboard"]
                title = "Engineering Telematics — " + source["runId"][:8]
                setting = f"set bounds of w to {{{r[0]}, {r[1]}, {r[0]+r[2]}, {r[1]+r[3]}}}" if action == "restore" else ""
                try:
                    value = applescript(f'''tell application "Terminal"
set w to window id {terminal}
if custom title of selected tab of w is not {json.dumps(title, ensure_ascii=False)} then error "OWNER_CHANGED"
{setting}
return bounds of w
end tell''')
                    b = [int(x.strip()) for x in value.split(",")]
                    surfaces["dashboard"] = dict(actual=[b[0], b[1], b[2]-b[0], b[3]-b[1]], expected=r)
                    if any(abs(a - e) > 3 for a, e in zip(surfaces["dashboard"]["actual"], r)):
                        problems.append("dashboard: geometry differs")
                except EnvironmentError as error:
                    problems.append("dashboard: " + str(error))
                    retryable = False
            else:
                problems.append("dashboard: visible Terminal absent; restart simulation through democtl")
            command = [str(self.binary), "present", str(self.directory / "layout.json")]
            pid = self.driver.live_process(command)
            generation = record.get("orderingGeneration")
            if action == "restore":
                generation = time.time_ns()
                atomic_json(self.directory / "layout.json", dict(layout,
                    _generation=[generation],
                    _foregroundPids=foreground_pids,
                    _terminalWindows=[terminal] if isinstance(terminal, int) else []))
                build_identity = self.binary.stat().st_mtime_ns
                if pid and record.get("presenterBuild") != build_identity:
                    self.driver.progress("Workspace: reloading Presenter windows only")
                    os.kill(pid, signal.SIGTERM)
                    deadline = time.monotonic() + 3
                    while self.driver.live_process(command):
                        if time.monotonic() >= deadline:
                            raise EnvironmentError("WORKSPACE_PRESENTER_RELOAD_TIMEOUT")
                        time.sleep(.1)
                    pid = None
                if pid:
                    os.kill(pid, signal.SIGUSR1)
                else:
                    child = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL, start_new_session=True)
                    self.driver.vm.children.append(child)
                    pid = child.pid
                record.update(profile="builtin-v1", presenterCommand=command, presenterBuild=build_identity,
                              orderingGeneration=generation, restoredAt=now())
                state["workspace"] = record
                atomic_json(self.root / JOURNAL, state)
            if not pid:
                problems.append("presenter: window host absent")
            else:
                for name, title in (("header", "Demo Presenter — Header"), ("browser", "Demo Presenter — Platform"),
                                    ("backdrop", "Demo Presenter — Background")):
                    try:
                        actual = window(pid, title=title)
                        surfaces[name] = dict(pid=pid, actual=actual, expected=layout[name])
                        if any(abs(a - b) > 3 for a, b in zip(actual, layout[name])):
                            problems.append(name + ": geometry differs")
                    except (EnvironmentError, subprocess.TimeoutExpired) as error:
                        problems.append(name + ": geometry observation unavailable")
                        if str(error) != "WORKSPACE_WINDOW_COUNT:0":
                            retryable = False
            order = self.ordering(generation, pid)
            if action == "restore" and pid:
                deadline = time.monotonic() + 2
                while order["state"] == "UNAVAILABLE" and time.monotonic() < deadline:
                    time.sleep(.1)
                    order = self.ordering(generation, pid)
            if order["state"] != "VERIFIED":
                problems.append("WORKSPACE_Z_ORDER_NOT_VERIFIED")
            outcome = dict(state="INCOMPLETE" if problems else "PLACED_AWAITING_VISUAL_REVIEW", profile="builtin-v1",
                display=screen, surfaces=surfaces, problems=problems,
                zOrder=order, orderingGeneration=generation, hostPid=pid,
                lifecycleChanged=False, readability="OPERATOR_REVIEW_REQUIRED")
            pending = bool(problems) and retryable and attempt < 3
            if pending and action == "restore":
                outcome["state"] = "WAITING_FOR_WINDOWS"
            return self.record(state, outcome, attempt, pending) if action == "restore" else outcome


class WorkspaceRecovery:
    """Continue only an explicitly requested pending layout, never a lifecycle.

    The Presenter owns the worker. Its existing action lock and the journal
    writer prevent overlap; exact current-run process ownership is re-read.
    """
    def __init__(self, service, operations):
        self.service, self.operations = service, operations
        self.stopped = threading.Event()
        self.thread = threading.Thread(target=self.run, name="workspace-recovery", daemon=True)

    def tick(self):
        with self.operations.lock:
            if self.operations.active or self.operations.uncertain or not self.service.cached().get("retryPending"):
                return
            self.operations.workspace_busy = True
        try:
            self.service.execute("restore", recovery=True)
        except EnvironmentError as error:
            if str(error) != "CURRENT_RUN_BUSY":
                self.fail()
        except (OSError, ValueError, KeyError, subprocess.SubprocessError):
            self.fail()
        finally:
            with self.operations.lock:
                self.operations.workspace_busy = False

    def fail(self):
        # Never retry an unclassified failure forever or expose a raw OS error.
        with self.service.environment._writer():
            state = read_json(self.service.root / JOURNAL)
            self.service.record(state, dict(state="INCOMPLETE", problems=["WORKSPACE_RECOVERY_FAILED"],
                surfaces={}, lifecycleChanged=False), 3, False)

    def run(self):
        while not self.stopped.wait(2):
            try:
                self.tick()
            except (EnvironmentError, OSError, ValueError):
                pass  # A concurrent journal writer is not permission to retry a lifecycle.

    def close(self):
        self.stopped.set()
        if self.thread.is_alive():
            self.thread.join(timeout=20)
