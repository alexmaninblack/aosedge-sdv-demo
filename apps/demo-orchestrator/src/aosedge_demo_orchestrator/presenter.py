# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Loopback Presenter backend; protected operations use the private session."""

import hashlib
import json
import mimetypes
import re
import threading
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .api import execute_operation
from .status import project_root, now

ADDRESS = ("127.0.0.1", 18080)


def stop():
    """Explicit CLI-only idle server shutdown; never signal a port alone."""
    import os
    import signal
    import subprocess
    import urllib.request
    try:
        result = subprocess.run(["/usr/sbin/lsof", "-t", "-nP", "-iTCP:18080", "-sTCP:LISTEN"],
            capture_output=True, text=True, timeout=3)
        pids = result.stdout.split()
        if not pids:
            print("OBSERVED ui.stop — UI server is not running; no system action")
            return 0
        if len(set(pids)) != 1 or not pids[0].isdigit():
            raise ValueError()
        pid = int(pids[0])
        expected = str(project_root() / "apps/demo-orchestrator/.venv/bin/democtl") + " ui serve"
        def owner():
            value = subprocess.run(["/bin/ps", "-p", str(pid), "-o", "uid=,command="], capture_output=True, text=True, timeout=3).stdout.strip()
            uid, command = value.split(None, 1)
            if int(uid) != os.getuid():
                return False
            if command.endswith(" " + expected):
                return True
            # The documented terminal command can use a relative venv path.
            # Accept it only with the exact canonical process working directory.
            if not command.endswith(" .venv/bin/democtl ui serve"):
                return False
            cwd = subprocess.run(["/usr/sbin/lsof", "-a", "-p", str(pid), "-d", "cwd", "-Fn"],
                capture_output=True, text=True, timeout=3)
            return (cwd.returncode == 0 and
                    [line[1:] for line in cwd.stdout.splitlines() if line.startswith("n")] ==
                    [str(project_root() / "apps/demo-orchestrator")])
        if not owner():
            raise ValueError()
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open("http://127.0.0.1:18080/api/presenter/operations", timeout=3) as response:
            state = json.loads(response.read(262145))
        if (not isinstance(state.get("sessionId"), str) or state.get("active") or state.get("uncertain")
                or not owner()):
            raise ValueError()
        os.kill(pid, signal.SIGINT)
        print("COMPLETED ui.stop — idle UI server stopped; VMs, Cloud and simulation unchanged")
        return 0
    except (OSError, ValueError, KeyError, subprocess.TimeoutExpired):
        print("BLOCKED ui.stop — UI ownership, idle state or outcome could not be established; nothing else stopped")
        return 1


class StudioCloudReader:
    """Reuse the normalized CLI reader and its exact-Unit stale cache."""

    def __init__(self):
        from .application import DemoOrchestrator
        self.application = DemoOrchestrator()
        self.pool = ThreadPoolExecutor(max_workers=3, thread_name_prefix="presenter-read")
        self.publication_reads = {}
        from .component_profile import InstalledProfileResolver
        from .components import ComponentService
        self.profile_resolver = InstalledProfileResolver(lambda: ComponentService(self.application.environment_service))

    def publication_read(self, kind, key, request, start_only=False):
        """At most one bounded read per publication kind, never a polling loop.

        A slow publication must not hold the Unit inventory response. Results
        from another run/release are discarded, never relabelled as current.
        """
        flight = self.publication_reads.get(kind)
        if flight and flight[0] != key:
            if not flight[1].done():
                return None
            flight = None
        if flight is None:
            flight = (key, self.pool.submit(execute_operation, request, self.application))
            self.publication_reads[kind] = flight
        if start_only:
            return None
        try:
            result = flight[1].result(timeout=0.05)
        except FutureTimeout:
            return None
        except Exception:
            result = {}
        self.publication_reads.pop(kind, None)
        return result

    def __call__(self):
        from .components import COMPONENT
        from .environment import JOURNAL
        from .status import read_json
        # Current-run receipts select a release; they are not installation facts.
        path = self.application.environment_service.root / JOURNAL
        journal = read_json(path) if path.is_file() else {}
        from .cloud_connection import cloud_binding, selected_domain
        context = (selected_domain(journal), cloud_binding(journal).get("ownerId"),
                   journal.get("vehicles", {}).get("test", {}).get("localVmId"),
                   journal.get("vehicles", {}).get("test", {}).get("unitId"))
        if getattr(self, "publication_context", None) != context:
            self.publications = {}
            self.last_component_publication = None
            self.installed_versions_hint = set()
            self.publication_context = context
        owned = [(version, row) for version, row in journal.get("componentOperations", {}).items()
                 if row.get("deploymentId") and re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version)]
        publication = None
        cache = getattr(self, "publications", {})
        cache = {key: value for key, value in cache.items() if any(key == (version, row["deploymentId"]) for version, row in owned)}
        unresolved = [(version, record) for version, record in owned
                      if cache.get((version, record["deploymentId"]), {}).get("stage") not in ("READY", "ERROR", "FAILED")]
        releases_read = execute_operation(dict(domain="service", action="releases"), self.application)
        service_releases = (releases_read.get("data") or {}).get("releases", [])
        run_id = journal.get("vehicles", {}).get("test", {}).get("localVmId")
        unresolved_services = [row for row in service_releases if run_id and row.get("runId") == run_id
            and row.get("submitted") and row.get("publication", {}).get("stage") not in ("READY", "ERROR", "FAILED")]
        # Independent read-only Cloud boundaries: do not add their latencies.
        # Only the main thread merges projections; mutation plans remain serial.
        unit_read = self.pool.submit(execute_operation, dict(domain="unit", action="cloud-status", target="test"), self.application)
        if unresolved_services:
            selected = max(unresolved_services, key=lambda row: row.get("preparedAt") or "")
            self.publication_read("service", (context, selected["releaseHandle"]), dict(domain="service", action="cloud-status", service_release=selected["releaseHandle"]), start_only=True)
        if unresolved:
            # The last inventory is only a scheduling hint; installation and
            # profile below always use this invocation's exact Cloud result.
            # Preserve concurrent reads and consume an existing flight before
            # giving the installed receipt priority over a processing successor.
            flight = self.publication_reads.get("component")
            continuing = [item for item in unresolved if flight and flight[0] == (context, (item[0], item[1]["deploymentId"]))]
            version, record = continuing[0] if continuing else max(unresolved, key=lambda item: (
                item[0] in self.installed_versions_hint and (item[0], item[1]["deploymentId"]) != self.last_component_publication,
                tuple(map(int, item[0].split(".")))))
            identity = (version, record["deploymentId"])
            component_result = self.publication_read("component", (context, identity), dict(domain="component", action="cloud-status", component_version=version))
            if component_result is not None:
                self.last_component_publication = identity
                raw = (component_result.get("data") or {}).get("publication")
                cache[identity] = ({key: raw.get(key) for key in ("stage", "deploymentId", "bundleState", "versionState", "versionId", "observedAt", "reason")}
                                   if raw else dict(stage="UNKNOWN", reason="PUBLICATION_NOT_OBSERVED"))
                cache[identity]["version"] = version
        if unresolved_services:
            selected = max(unresolved_services, key=lambda row: row.get("preparedAt") or "")
            service_result = self.publication_read("service", (context, selected["releaseHandle"]), dict(domain="service", action="cloud-status", service_release=selected["releaseHandle"]))
            if service_result is not None:
                raw = service_result.get("data") or {}
                selected["publication"] = {key: raw.get(key) for key in ("stage", "serviceId", "versionId", "observedAt", "reason")}
                selected["serviceId"] = raw.get("serviceId") or selected.get("serviceId")
        result = unit_read.result()
        component_rows = ((result.get("data") or {}).get("components") or {}).get("value") or []
        self.installed_versions_hint = {(item.get("installed_component") or {}).get("version") for item in component_rows
                                       if item.get("reported_component_id") == COMPONENT or item.get("type") == COMPONENT}
        self.publications = cache
        if owned:
            version, record = max(owned, key=lambda item: tuple(map(int, item[0].split("."))))
            publication = cache.get((version, record["deploymentId"]))
        data = result.get("data") or {}
        # The list endpoint is an aggregate. Per-Subject detail owns instance
        # versions/statuses; do not silently turn a failed detail into absence.
        service_list = data.get("services") or {}
        details = data.get("serviceDetails") or {}
        identifiers = {row.get("service", {}).get("id") for row in service_list.get("value") or [] if row.get("service")}
        if identifiers:
            sections = [details.get(identifier) or {} for identifier in identifiers]
            complete = service_list.get("state") == "CURRENT" and all(section.get("state") == "CURRENT" and isinstance(section.get("value"), list) for section in sections)
            data = dict(data, services=dict(service_list, state="CURRENT" if complete else "INCOMPLETE",
                reason=None if complete else "CLOUD_SERVICE_DETAILS_NOT_CURRENT",
                value=[dict(row, reportReadCompletedAt=section.get("lastKnownReadCompletedAt") or section.get("readCompletedAt"))
                       for section in sections for row in section.get("value") or []] or ( [] if complete else None)))
        data["teamServiceIds"] = {record["team"]: identifier for identifier, record in journal.get("serviceOperations", {}).items()
            if record.get("team") in ("brake", "tire") and record.get("test", {}).get("unitId") == data.get("unitId")}
        section = data.get("unit") or {}
        unit = section.get("value") or {}
        rows = (data.get("components") or {}).get("value")
        matches = [row for row in rows or [] if row.get("reported_component_id") == COMPONENT or row.get("type") == COMPONENT]
        row = matches[0] if len(matches) == 1 else {}
        installed_profile = self.profile_resolver.resolve(journal, data, row, cache)
        if row:
            row["installedProfile"] = installed_profile
        return dict(state="CURRENT" if section.get("state") == "CURRENT" else "UNAVAILABLE",
            bindingKey=":".join(str(journal.get("vehicles", {}).get("test", {}).get(key) or "none") for key in ("localVmId", "unitId")),
            observedAt=data.get("readCompletedAt") or now(), reason=section.get("reason") or (None if unit else "TEST_CLOUD_BINDING_NOT_OBSERVED"),
            value=dict(target="test", source="Aos Cloud", online=unit.get("connectivity"), lifecycle=unit.get("status"),
                installedVersion=(row.get("installed_component") or {}).get("version"),
                installedProfile=installed_profile,
                pendingVersion=(row.get("pending_component") or {}).get("version"), updateStatus=row.get("pending_component_status"),
                latestPublishedVersion=None, releases=[], runtimeState="NOT_REPORTED_BY_CLOUD", dataReadiness="NOT_REPORTED_BY_CLOUD",
                inventory=data, publication=publication) if unit else None,
            publication=publication, publications=list(cache.values()), serviceReleases=service_releases,
            serviceReleasesState="CURRENT" if releases_read.get("state") == "OBSERVED" else "UNAVAILABLE")

    def monitoring(self):
        result = execute_operation(dict(domain="unit", action="monitoring", target="test"), self.application)
        return result.get("data") or dict(state="UNAVAILABLE", reason="CLOUD_MONITORING_NOT_OBSERVED", readCompletedAt=now())

    def monitoring_history(self):
        result = execute_operation(dict(domain="unit", action="monitoring-history", target="test"), self.application)
        return result.get("data") or dict(state="UNAVAILABLE", reason="CLOUD_HISTORY_NOT_OBSERVED", readCompletedAt=now())

    def backend(self, team):
        if team not in ("brake", "tire"):
            raise ValueError("BACKEND_TEAM_INVALID")
        result = execute_operation(dict(domain="backend", action="inspect", team=team), self.application)
        data = result.get("data") or {}
        # Separate product evidence, never a Cloud/runtime authority or guest read.
        if data.get("source") != "REAL_BACKEND_HTTP":
            return dict(state="UNAVAILABLE", team=team, observedAt=now(), reason="BACKEND_NOT_OBSERVED")
        return {key: data[key] for key in ("state", "team", "source", "cloudAuthority", "vehicleTelemetry", "observedAt", "observations") if key in data}

    def brake_window(self, event_id):
        result = execute_operation(dict(domain="backend", action="window-detail", team="brake", window_id=event_id), self.application)
        if result.get("state") != "OBSERVED" or not isinstance(result.get("data"), dict):
            raise ValueError("BACKEND_WINDOW_DETAIL_UNAVAILABLE")
        return result["data"]


def read_platform():
    """Cloud-only public projection of democtl component cloud-status."""
    result = execute_operation(dict(domain="component", action="cloud-status"))
    stamp = now()
    if result.get("state") != "OBSERVED":
        return dict(state="UNAVAILABLE", observedAt=stamp, value=None, reason="AOS_CLOUD_STATE_UNAVAILABLE")
    data = result["data"]
    unit = data.get("test") or {}
    rows = unit.get("components") or []
    row = rows[0] if len(rows) == 1 else {}
    def version(value):
        return value if isinstance(value, str) and len(value) <= 32 and re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", value) else None
    def word(value):
        return value if isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9 _-]{1,64}", value) else None
    return dict(state="CURRENT", observedAt=stamp, reason=None, value=dict(
        target="test", source="Aos Cloud", online=word(unit.get("online_status")), lifecycle=word(unit.get("status")),
        installedVersion=version((row.get("installed_component") or {}).get("version")),
        pendingVersion=version((row.get("pending_component") or {}).get("version")),
        updateStatus=word(row.get("pending_component_status")), latestPublishedVersion=version(data.get("latestPublishedVersion")),
        releases=[dict(version=version(item.get("version")), state=word(item.get("state")))
                  for item in data.get("versions", []) if item.get("is_fake") is False and version(item.get("version"))],
        runtimeState="NOT_REPORTED_BY_CLOUD", dataReadiness="NOT_REPORTED_BY_CLOUD"))


def read_snapshot():
    status = execute_operation(dict(domain="orchestrator", action="status", target="all"))
    catalog = execute_operation(dict(domain="image", action="list"))
    releases = execute_operation(dict(domain="service", action="releases"))
    snapshot = status["status"]
    vehicles = {}
    for role, item in snapshot["vehicles"].items():
        local = item["local"]
        value = local.get("value") or {}
        vehicles[role] = dict(state=local["state"], reason=local.get("reason"),
            process=value.get("processState"), imageVersion=value.get("configuredImageVersion"),
            overlayExists=value.get("overlayExists"))
    # A fixed public projection, never raw configuration, credentials or paths.
    return dict(mode="LOCAL_READ_ONLY", observedAt=snapshot["readCompletedAt"],
        serviceReleases=(releases.get("data") or {}).get("releases", []),
        serviceReleasesState="CURRENT" if releases.get("state") == "OBSERVED" else "UNAVAILABLE",
        preparation=(snapshot.get("journal", {}).get("value") or {}).get("preparation"),
        candidates=(snapshot.get("journal", {}).get("value") or {}).get("candidates", []),
        runId=(snapshot.get("journal", {}).get("value") or {}).get("runId"),
        registrationStarted=(snapshot.get("journal", {}).get("value") or {}).get("registrationStarted", False),
        registrationComplete=(snapshot.get("journal", {}).get("value") or {}).get("registrationComplete", False),
        lifecycle=(snapshot.get("journal", {}).get("value") or {}).get("lifecycle"),
        result=status["state"], vehicles=vehicles,
        source={key: snapshot["source"].get(key) for key in ("state", "currentVehicle", "selectedVehicle", "reason")},
        images=[{key: image.get(key) for key in ("selector", "version", "architecture", "state", "problems")}
                for image in catalog["data"]["images"]],
        access={name: dict(present=(profile.get("credential", {}).get("value") or {}).get("present", False),
                          state="NOT_REQUESTED") for name, profile in snapshot["cloud"].items()})


def client_state(root, native):
    """Small local build identity; never consult a VM or Cloud for refresh."""
    index = root / "index.html"
    if index.is_symlink() or index.stat().st_size > 1_048_576:
        raise ValueError("PRESENTER_ENTRY_INVALID")
    code, session = native.call() if native else (503, {})
    return dict(buildId=hashlib.sha256(index.read_bytes()).hexdigest(),
                sessionId=session.get("sessionId") if code == 200 else None,
                canReload=code == 200 and isinstance(session.get("sessionId"), str)
                and not session.get("active") and not session.get("uncertain"))


def make_server(static_root, address=ADDRESS, reader=read_snapshot, native=None, platform_reader=None):
    root = Path(static_root).resolve(strict=True)
    if not (root / "index.html").is_file():
        raise ValueError("PRESENTER_BUILD_REQUIRED")
    cloud_reader = StudioCloudReader()
    platform_reader = platform_reader or cloud_reader
    platform_lock = threading.Lock()
    platform_result = None
    platform_generation = 0

    def platform_once():
        nonlocal platform_result, platform_generation
        # Collapse overlapping windows/StrictMode reads, not a polling service
        # or persisted source of truth. Original observation time is retained.
        generation = platform_generation
        with platform_lock:
            if platform_result is None or generation == platform_generation:
                platform_result = platform_reader()
                platform_generation += 1
            return platform_result

    class Handler(BaseHTTPRequestHandler):
        def setup(self):
            super().setup()
            self.connection.settimeout(10)

        def log_message(self, *_):
            pass  # Do not log request URLs/headers.

        def reply(self, code, body, content_type="application/json"):
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Content-Security-Policy", "default-src 'self'; connect-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            expected = "127.0.0.1:" + str(self.server.server_port)
            if self.headers.get("Host") != expected:
                self.reply(403, b'{"error":"LOCAL_HOST_REQUIRED"}')
                return
            origin = self.headers.get("Origin")
            if origin and origin != "http://" + expected:
                self.reply(403, b'{"error":"SAME_ORIGIN_REQUIRED"}')
                return
            if self.path == "/api/presenter/client-state":
                try:
                    self.reply(200, json.dumps(client_state(root, native)).encode())
                except Exception:
                    self.reply(503, b'{"error":"CLIENT_STATE_UNAVAILABLE"}')
                return
            if self.path == "/api/presenter/snapshot":
                try:
                    self.reply(200, json.dumps(reader()).encode())
                except Exception:
                    self.reply(503, b'{"error":"LOCAL_OBSERVATION_UNAVAILABLE"}')
                return
            if self.path == "/api/presenter/platform":
                try:
                    self.reply(200, json.dumps(platform_once()).encode())
                except Exception:
                    self.reply(503, b'{"error":"AOS_CLOUD_STATE_UNAVAILABLE"}')
                return
            if self.path in ("/api/presenter/monitoring", "/api/presenter/monitoring-history"):
                try:
                    resource_read = cloud_reader.monitoring_history if self.path.endswith("monitoring-history") else cloud_reader.monitoring
                    self.reply(200, json.dumps(resource_read()).encode())
                except Exception:
                    self.reply(503, b'{"error":"CLOUD_MONITORING_UNAVAILABLE"}')
                return
            if self.path in ("/api/presenter/backend/brake", "/api/presenter/backend/tire"):
                try:
                    self.reply(200, json.dumps(cloud_reader.backend(self.path.rsplit("/", 1)[-1])).encode())
                except Exception:
                    self.reply(503, b'{"error":"BACKEND_OBSERVATION_UNAVAILABLE"}')
                return
            window_detail = re.fullmatch(r"/api/presenter/backend/brake/windows/([0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12})", self.path)
            if window_detail:
                try:
                    self.reply(200, json.dumps(cloud_reader.brake_window(window_detail[1])).encode())
                except Exception:
                    self.reply(503, b'{"error":"BACKEND_WINDOW_DETAIL_UNAVAILABLE"}')
                return
            if self.path == "/api/presenter/operations" and native:
                try:
                    code, result = native.call()
                    self.reply(code, json.dumps(result).encode())
                except Exception:
                    self.reply(503, b'{"error":"NATIVE_SESSION_UNAVAILABLE_NO_REPLAY"}')
                return
            # Only the built entry point and Vite assets. No filesystem browser,
            # source map, dotfile, arbitrary path, query-driven API or fallback.
            if self.path == "/":
                relative = Path("index.html")
            elif self.path.startswith("/assets/") and all(part not in ("", ".", "..") for part in self.path[1:].split("/")):
                relative = Path(self.path[1:])
            else:
                self.reply(404, b'{"error":"NOT_FOUND"}')
                return
            candidate = root / relative
            if (any(part.is_symlink() for part in (candidate, *candidate.parents) if part != root)
                    or candidate.suffix not in (".html", ".js", ".css", ".png", ".svg", ".woff2", ".ico")
                    or not candidate.is_file()):
                self.reply(404, b'{"error":"NOT_FOUND"}')
                return
            self.reply(200, candidate.read_bytes(), mimetypes.guess_type(str(candidate))[0] or "application/octet-stream")

        def do_POST(self):
            if native is None:
                self.reply(405, b'{"error":"READ_ONLY_PREVIEW"}')
                return
            expected = "127.0.0.1:" + str(self.server.server_port)
            if (self.headers.get("Host") != expected or self.headers.get("Origin") != "http://" + expected
                    or self.headers.get("Content-Type") != "application/json"
                    or self.headers.get("Transfer-Encoding")):
                self.reply(403, b'{"error":"SAME_ORIGIN_JSON_REQUIRED"}')
                return
            if self.path != "/api/presenter/operations":
                self.reply(404, b'{"error":"NOT_FOUND"}')
                return
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 < size <= 4096:
                    raise ValueError("INVALID_REQUEST")
                payload = json.loads(self.rfile.read(size))
                # Validate before crossing into the privileged native boundary.
                from .presenter_operations import operation_plan
                operation_plan(payload)
            except (ValueError, TypeError, AttributeError):
                self.reply(400, b'{"error":"INVALID_OPERATION"}')
                return
            try:
                code, result = native.call(payload)
                self.reply(code, json.dumps(result).encode())
            except Exception:
                self.reply(503, b'{"error":"SUBMISSION_UNCERTAIN_DO_NOT_RESUBMIT"}')

        def do_DELETE(self):
            self.reply(405, b'{"error":"METHOD_NOT_ALLOWED"}')

        do_PUT = do_PATCH = do_DELETE

    return ThreadingHTTPServer(address, Handler)


def serve():
    from .presenter_operations import NativeSession
    native = None
    recovery = None
    source_recovery = None
    try:
        native = NativeSession()
        server = make_server(project_root() / "apps/presenter-ui/dist", native=native)
        from .application import DemoOrchestrator
        from .workspace import WorkspaceService, WorkspaceRecovery
        layout_app = DemoOrchestrator()
        native.operations.workspace = WorkspaceService(layout_app.environment_service, layout_app.source_service.driver)
        recovery = WorkspaceRecovery(native.operations.workspace, native.operations)
        recovery.thread.start()
        from .source_boot_recovery import SourceBootRecovery
        # Each worker owns its driver/SSH context; only the journal/action
        # interlocks are shared with layout and foreground operations.
        boot_app = DemoOrchestrator()
        source_recovery = SourceBootRecovery(boot_app.source_service, native.operations)
        source_recovery.thread.start()
    except (OSError, ValueError):
        if native:
            native.close()
        print("BLOCKED ui.serve: build Presenter UI first; ports 18080/18600 must be available", flush=True)
        return 1
    print("Presenter UI: http://127.0.0.1:18080/", flush=True)
    print("Protected actions require UI confirmation; backend scenario Reset is one-click. VM access uses a native macOS dialog or Keychain, never a hidden terminal prompt.", flush=True)
    print("Ctrl+C closes this UI session; it does not reset VMs or Cloud Units.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        if source_recovery:
            source_recovery.close()
        if recovery:
            recovery.close()
        server.server_close()
        native.close()
    return 0
