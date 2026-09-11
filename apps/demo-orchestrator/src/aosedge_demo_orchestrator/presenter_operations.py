# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Explicitly authorized, session-scoped Presenter operations over Demo Control.

Only the local UI backend receives the native session capability. Progress
receipts are ephemeral; existing VM/Cloud journals remain authoritative.
"""

import hashlib
import hmac
import json
import os
import secrets
import tempfile
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from uuid import UUID, uuid4

from .api import execute_operation
from .application import DemoOrchestrator
from .components import VERSION
from .status import now
from .vm import VMService
from .environment import EnvironmentError
from .native_access import NativeVMAccess

NATIVE_ADDRESS = ("127.0.0.1", 18600)
READ_ACTIONS = ("inspect", "verify", "cloud-status", "observe-test", "cloud-access")


def operation_plan(payload):
    """Fixed actions/recipients; the caller cannot select native authority."""
    if not isinstance(payload, dict) or not isinstance(payload.get("requestId"), str):
        raise ValueError("INVALID_OPERATION")
    identity = str(UUID(payload["requestId"]))
    action = payload.get("action")
    fields = {"requestId", "action", "sessionId"}
    if action in ("create", "prepare-demo"):
        fields.add("image")
        if not isinstance(payload.get("image"), str) or not 1 <= len(payload["image"]) <= 128:
            raise ValueError("CATALOG_IMAGE_REQUIRED")
        plan = ([dict(domain="demo", action="create", image=payload["image"])] if action == "create"
                else [dict(domain="demo", action="prepare", target="test", image=payload["image"])])
    elif action == "prepare":
        fields.add("profile")
        if payload.get("profile") not in ("v1", "v2", "v3"):
            raise ValueError("CONTENT_PROFILE_REQUIRED")
        # Only Demo Control allocates the release. Browser input cannot reuse
        # an old number or identify functional capability by release major.
        plan = [dict(domain="component", action="prepare", content_profile=payload["profile"])]
    elif action in ("unpack", "sign", "upload", "inspect", "verify", "cloud-status"):
        fields.add("version")
        version = payload.get("version")
        if not isinstance(version, str) or len(version) > 32 or not VERSION.fullmatch(version):
            raise ValueError("COMPONENT_VERSION_REQUIRED")
        request = dict(domain="component", action=action, component_version=version)
        plan = [request]
    elif action in ("start-vms", "stop-vms"):
        plan = [dict(domain="vm", action="start" if action == "start-vms" else "stop", target="test")]
    elif action == "provision":
        plan = [dict(domain="unit", action="provision", target="test")]
    elif action in ("start-simulation", "stop-simulation"):
        plan = [dict(domain="simulation", action="start" if action == "start-simulation" else "stop")]
    elif action == "connect-test":
        plan = [dict(domain="vehicle", action="initialize", target="test")]
    elif action == "reconnect-test":
        plan = [dict(domain="vehicle", action="select", target="test")]
    elif action in ("park", "resume"):
        plan = [dict(domain="environment", action=action)]
    elif action == "observe-test":
        # Preserve old UI clients without retaining their direct guest probe.
        plan = [dict(domain="component", action="cloud-status")]
    elif action == "cloud-access":
        plan = [dict(domain="orchestrator", action="status", target="all", cloud=True)]
    elif action == "reset":
        plan = [dict(domain="demo", action="retire")]
    else:
        raise ValueError("OPERATION_NOT_ALLOWED")
    if set(payload) != fields or not isinstance(payload["sessionId"], str):
        raise ValueError("UNSUPPORTED_OPERATION_FIELD")
    return identity, plan


def public_result(result):
    """Fixed public facts, not an unrestricted worker response."""
    public = {key: result.get(key) for key in ("operation", "state", "message")}
    data = result.get("data") or {}
    allowed = ("activeVersion", "activeSlot", "vdpProcess", "vdpData", "vdpStatusText", "vdpRestarts",
               "processSlotMatches", "readPathCount", "gate", "advisory", "state", "noOp", "currentVehicle",
               "version", "contentProfile", "sha256", "approved", "outcome", "signatureVerified", "phase", "completedSteps", "reason", "image")
    public["facts"] = {key: data[key] for key in allowed if key in data}
    if isinstance(data.get("publication"), dict):
        public["facts"]["publication"] = {key: data["publication"].get(key) for key in
            ("stage", "deploymentId", "bundleState", "versionState", "versionId", "observedAt", "reason")}
    if result.get("operation") == "component.logs":
        # source_guest already strips credential-bearing journal messages.
        public["facts"]["entries"] = [{key: entry[key] for key in ("time", "unit", "message", "diagnostic") if key in entry}
                                     for entry in data.get("entries", [])[-80:]]
        public["facts"]["providerReadyEvents"] = data.get("providerReadyEvents")
    if result.get("operation") == "component.cloud-status":
        public["facts"].update(versions=[{key: item.get(key) for key in ("version", "state")} for item in data.get("versions", [])],
            bundles=[dict(state=item.get("state")) for item in data.get("deploymentBundles", [])],
            batches=[dict(state=item.get("state"), approved=(item.get("approval_states") or {}).get("arm64", {}).get("is_approved")) for item in data.get("verificationBatches", [])])
    if result.get("operation") == "orchestrator.status":
        public["facts"]["cloud"] = {name: dict(state=profile.get("access", {}).get("state"),
            reason=profile.get("access", {}).get("reason"), units={role: {key: (unit.get("value") or {}).get(key) for key in ("onlineStatus", "status")}
            for role, unit in profile.get("units", {}).items()}) for name, profile in result.get("status", {}).get("cloud", {}).items()}
    if isinstance(data.get("vehicles"), dict):
        public["facts"]["vehicles"] = {role: {key: value.get(key) for key in ("state", "reason", "lifecycle", "onlineStatus", "gate", "vdpProcess", "vdpData") if key in value}
            for role, value in data["vehicles"].items()}
    return public


def reset_plan(root, plan):
    """Skip inapplicable stages only; existing core checks still own cleanup."""
    from .environment import JOURNAL
    from .status import read_json
    journal = root / JOURNAL
    if not journal.exists():
        # retire detects orphaned files; absence never authorizes raw deletion.
        return [plan[-1]]
    state = read_json(journal)
    vehicles = state["vehicles"]
    if not vehicles or any(item.get(key) for item in vehicles.values() for key in ("unitId", "nodeId", "systemUid", "cloud")):
        return plan
    return [request for request in plan if request["domain"] != "unit"]


class SessionOperations:
    def __init__(self, executor=None):
        self.executor = executor
        self.session_id = str(uuid4())  # Public generation ID, not a capability.
        self.jobs = {}
        self.lock = threading.RLock()
        self.active = None
        self.uncertain = False

    def submit(self, payload):
        identity, plan = operation_plan(payload)
        fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        with self.lock:
            if payload["sessionId"] != self.session_id:
                raise ValueError("UI_SESSION_CHANGED_NO_REPLAY")
            if identity in self.jobs:
                if self.jobs[identity]["fingerprint"] != fingerprint:
                    raise ValueError("REQUEST_ID_INPUT_CHANGED")
                return self.view(identity)
            if self.active:
                raise ValueError("OPERATION_ALREADY_RUNNING")
            if self.uncertain and payload["action"] not in READ_ACTIONS:
                raise ValueError("UNCERTAIN_OPERATION_REQUIRES_NATIVE_RECONCILIATION")
            if len(self.jobs) >= 128:
                raise ValueError("UI_SESSION_RECEIPT_LIMIT")
            self.jobs[identity] = dict(id=identity, action=payload["action"], version=payload.get("version"), profile=payload.get("profile"),
                fingerprint=fingerprint, state="ACCEPTED", startedAt=now(), progress=[], results=[])
            self.active = identity
            threading.Thread(target=self.run, args=(identity, plan), daemon=True).start()
            return self.view(identity)

    def view(self, identity):
        with self.lock:
            return json.loads(json.dumps({key: value for key, value in self.jobs[identity].items() if key != "fingerprint"}))

    def snapshot(self):
        with self.lock:
            return dict(sessionId=self.session_id, active=self.active, uncertain=self.uncertain,
                        jobs=[self.view(identity) for identity in self.jobs])

    def run(self, identity, plan):
        job = self.jobs[identity]
        def progress(message):
            with self.lock:
                job["progress"] = (job["progress"] + [message])[-40:]
        access = NativeVMAccess(progress=progress)
        try:
            application = None if self.executor else DemoOrchestrator(vm_service=VMService(password_provider=access, progress=progress))
            if application:
                from .environment import JOURNAL
                from .status import read_json
                path = application.environment_service.root / JOURNAL
                if path.is_file():
                    job["runId"] = read_json(path).get("vehicles", {}).get("test", {}).get("localVmId")
            with self.lock:
                job["state"] = "RUNNING"
            for request in plan:
                progress(request["domain"] + "." + request["action"] + (" " + request["target"] if request.get("target") else ""))
                result = self.executor(request) if self.executor else execute_operation(request, application)
                with self.lock:
                    job["results"].append(public_result(result))
                    if payload_version := (result.get("data") or {}).get("version"):
                        job["version"] = payload_version
                        job["profile"] = (result.get("data") or {}).get("contentProfile")
                if result["state"] not in ("COMPLETED", "OBSERVED", "READY"):
                    with self.lock:
                        job["state"] = result["state"]
                    break
            else:
                with self.lock:
                    job["state"] = "COMPLETED"
        except EnvironmentError as error:
            with self.lock:
                job.update(state="BLOCKED", reason=str(error))
        except Exception:
            with self.lock:
                self.uncertain = True
                job.update(state="UNCERTAIN", reason="Result unavailable; reconcile native state before another mutation")
        finally:
            access.clear()
            with self.lock:
                job["finishedAt"] = now()
                self.active = None


class NativeSession:
    def __init__(self, address=NATIVE_ADDRESS, operations=None):
        self.directory = tempfile.TemporaryDirectory(prefix="democtl-ui-session-")
        path = Path(self.directory.name) / "platform-oem"
        self.capability = secrets.token_urlsafe(32)
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o400)
        with os.fdopen(descriptor, "w") as output:
            output.write(self.capability)
        self.operations = operations or SessionOperations()
        owner = self
        class Handler(BaseHTTPRequestHandler):
            def setup(self):
                super().setup()
                self.connection.settimeout(10)
            def log_message(self, *_):
                pass
            def reply(self, code, data):
                body = json.dumps(data).encode()
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            def authorized(self):
                return (self.headers.get("Host") == "127.0.0.1:" + str(self.server.server_port)
                    and not self.headers.get("Origin")
                    and hmac.compare_digest(self.headers.get("Authorization", ""), "Bearer " + owner.capability))
            def do_GET(self):
                if not self.authorized():
                    self.reply(403, {"error": "NATIVE_SESSION_REQUIRED"})
                elif self.path == "/operations":
                    self.reply(200, owner.operations.snapshot())
                else:
                    self.reply(404, {"error": "NOT_FOUND"})
            def do_POST(self):
                if not self.authorized():
                    self.reply(403, {"error": "NATIVE_SESSION_REQUIRED"})
                    return
                try:
                    size = int(self.headers.get("Content-Length", "0"))
                    if self.path != "/operations" or self.headers.get("Transfer-Encoding") or not 0 < size <= 4096:
                        raise ValueError("INVALID_REQUEST")
                    value = json.loads(self.rfile.read(size))
                    self.reply(202, owner.operations.submit(value))
                except (ValueError, TypeError, AttributeError):
                    self.reply(409, {"error": "OPERATION_REJECTED_OR_BUSY"})
        try:
            self.server = ThreadingHTTPServer(address, Handler)
        except Exception:
            self.directory.cleanup()
            raise
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def call(self, payload=None):
        request = urllib.request.Request("http://127.0.0.1:" + str(self.server.server_port) + "/operations",
            data=None if payload is None else json.dumps(payload).encode(),
            headers={"Authorization": "Bearer " + self.capability, "Content-Type": "application/json"})
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        try:
            with opener.open(request, timeout=5) as response:
                return response.status, json.loads(response.read(1024 * 1024))
        except urllib.error.HTTPError as error:
            return error.code, {"error": "OPERATION_REJECTED_OR_BUSY"}

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.directory.cleanup()
