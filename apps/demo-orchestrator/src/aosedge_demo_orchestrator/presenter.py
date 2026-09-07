# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Loopback Presenter backend; protected operations use the private session."""

import json
import mimetypes
import re
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .api import execute_operation
from .status import project_root, now

ADDRESS = ("127.0.0.1", 18080)


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
        preparation=(snapshot.get("journal", {}).get("value") or {}).get("preparation"),
        result=status["state"], vehicles=vehicles,
        source={key: snapshot["source"].get(key) for key in ("state", "currentVehicle", "selectedVehicle", "reason")},
        images=[{key: image.get(key) for key in ("selector", "version", "architecture", "state", "problems")}
                for image in catalog["data"]["images"]],
        access={name: dict(present=(profile.get("credential", {}).get("value") or {}).get("present", False),
                          state="NOT_REQUESTED") for name, profile in snapshot["cloud"].items()})


def make_server(static_root, address=ADDRESS, reader=read_snapshot, native=None, platform_reader=read_platform):
    root = Path(static_root).resolve(strict=True)
    if not (root / "index.html").is_file():
        raise ValueError("PRESENTER_BUILD_REQUIRED")
    platform_lock = threading.Lock()
    platform_result = None
    platform_finished = 0.0

    def platform_once():
        nonlocal platform_result, platform_finished
        # Collapse overlapping windows/StrictMode reads, not a polling service
        # or persisted source of truth. Original observation time is retained.
        with platform_lock:
            if platform_result is None or time.monotonic() - platform_finished > 1:
                platform_result = platform_reader()
                platform_finished = time.monotonic()
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
    try:
        native = NativeSession()
        server = make_server(project_root() / "apps/presenter-ui/dist", native=native)
    except (OSError, ValueError):
        if native:
            native.close()
        print("BLOCKED ui.serve: build Presenter UI first; ports 18080/18600 must be available", flush=True)
        return 1
    print("Presenter UI: http://127.0.0.1:18080/", flush=True)
    print("Actions require UI confirmation. VM access uses a native macOS dialog or Keychain, never a hidden terminal prompt.", flush=True)
    print("Ctrl+C closes this UI session; it does not reset VMs or Cloud Units.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        native.close()
    return 0
