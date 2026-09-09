# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Exact-Test private backend cleanup, composed by Demo Control only.

No CLI, arbitrary process argument, token persistence or data-store fallback.
Running owned backends are required for first proof. Interrupted cleanup may
reuse an exact UID/image-bound proof only while its containers remain stopped.
Production rows/volumes remain when Production exists; missing context means
NoCurrentTest until normal provisioning publishes the next closed projection.
"""

import json
import re
import shutil
import subprocess
from datetime import datetime, timezone

from .backend_context import CONTEXT, UID, project_context
from .backends import DIGEST, TEAMS
from .environment import EnvironmentError, JOURNAL, atomic_json, encoded, sync_directory
from .status import now, object_id, read_json

COUNTS = {"messages", "windows", "assessments", "events", "advisories", "quarantine"}
SHA = re.compile(r"[a-f0-9]{64}")
PREVIEW = {"schemaVersion", "contractVersion", "systemUids", "recordCounts", "nonmatchingRecordCounts",
           "recordSetSha256", "confirmationToken", "expiresAt"}
RESULT = {"schemaVersion", "contractVersion", "systemUids", "deletedRecordCounts", "remainingMatchingRecordCounts",
          "nonmatchingRecordCounts", "nonmatchingRecordSetSha256", "completedAt"}
FOUNDATION = dict(scope="FOUNDATION_ONLY", productIngestion=False, schemaVersion=1,
                  noProductTablesOrRecords=True, unknownTables=False, removalEligible=True)


def _counts(value):
    if (not isinstance(value, dict) or set(value) != COUNTS
            or any(type(count) is not int or count < 0 for count in value.values())):
        raise EnvironmentError("BACKEND_CLEANUP_COUNTS_INVALID")
    return value


def _timestamp(value):
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if result.tzinfo is None:
            raise ValueError()
        return result
    except (AttributeError, ValueError, TypeError):
        raise EnvironmentError("BACKEND_CLEANUP_RESPONSE_INVALID") from None


class BackendRetirement:
    def __init__(self, service):
        self.service = service
        self.environment = service.environment
        self.root = service.root

    def _save(self, state):
        atomic_json(self.root / JOURNAL, state)

    def _owned(self, state, team, running=False):
        owner = object_id(state["operations"][0]["id"])
        record = state["backends"][team]
        name = "aosedge-demo-" + team + "-cloud"
        if (not isinstance(record, dict) or record.get("owner") != owner or record.get("containerName") != name
                or not isinstance(record.get("imageId"), str) or not DIGEST.fullmatch(record["imageId"])
                or record.get("composePath") != ".run/demo-current/backends/" + team + "-compose.json"):
            raise EnvironmentError("BACKEND_CLEANUP_OWNERSHIP_INVALID")
        observed = self.service._inspect("container", name)
        self.service._owned_container(observed, owner, team, record["imageId"])
        if observed:
            mounts = observed.get("Mounts") or []
            volume = "aosedge_demo_" + team + "_cloud_v1"
            data = [mount for mount in mounts if mount.get("Destination") == "/data"]
            context = [mount for mount in mounts if mount.get("Destination") == "/run/demo-control/context"]
            if (len(data) != 1 or data[0].get("Type") != "volume" or data[0].get("Name") != volume
                    or data[0].get("RW") is not True or len(context) != 1
                    or context[0].get("Type") != "bind" or context[0].get("RW") is not False
                    or context[0].get("Source") != str((self.root / CONTEXT).parent)):
                raise EnvironmentError("BACKEND_CLEANUP_MOUNT_BINDING_INVALID")
        if running and (not observed or observed.get("State", {}).get("Running") is not True
                or observed.get("State", {}).get("Health", {}).get("Status") != "healthy"):
            raise EnvironmentError("BACKEND_CLEANUP_REQUIRES_RUNNING_BACKEND:" + team)
        return observed

    def _resource(self, state, team, kind, name):
        value = self.service._inspect(kind, name)
        if value:
            labels = value.get("Labels") or {}
            if (labels.get("tech.aosedge.demo.owner") != state["backends"][team]["owner"]
                    or labels.get("tech.aosedge.demo.team") != team):
                raise EnvironmentError("BACKEND_FOREIGN_" + kind.upper())
        return value

    def _private(self, team, container_id, operation, payload=None):
        if (team, operation) not in (("brake", "preview"), ("brake", "execute"), ("brake", "empty-proof"), ("tire", "foundation-proof")):
            raise EnvironmentError("BACKEND_PRIVATE_OPERATION_INVALID")
        if not isinstance(container_id, str) or not SHA.fullmatch(container_id):
            raise EnvironmentError("BACKEND_CONTAINER_ID_INVALID")
        executable = shutil.which("docker")
        if executable is None:
            raise EnvironmentError("BACKEND_DOCKER_REQUIRED")
        body = encoded(payload or {}).decode()
        if len(body.encode()) > 4096:
            raise EnvironmentError("BACKEND_PRIVATE_REQUEST_TOO_LARGE")
        entry = "/app/out/backend/main.js" if team == "brake" else "/app/src/main.mjs"
        try:
            reply = subprocess.run([executable, "exec", "--interactive", container_id,
                "node", entry, "--admin-operation", operation], input=body,
                capture_output=True, text=True, timeout=12)
        except (OSError, subprocess.TimeoutExpired):
            # Exceptions can contain stdin/stdout; never include them in errors.
            raise EnvironmentError("BACKEND_PRIVATE_RESPONSE_UNCERTAIN") from None
        if reply.returncode or len(reply.stdout.encode()) > 16384:
            raise EnvironmentError("BACKEND_PRIVATE_RESPONSE_FAILED")
        try:
            envelope = json.loads(reply.stdout)
        except (ValueError, TypeError):
            raise EnvironmentError("BACKEND_PRIVATE_RESPONSE_INVALID") from None
        if not isinstance(envelope, dict) or set(envelope) != {"status", "body"} or envelope["status"] != 200:
            raise EnvironmentError("BACKEND_PRIVATE_RESPONSE_REJECTED")
        return envelope["body"]

    def _preview(self, uid, body):
        if (not isinstance(body, dict) or set(body) != PREVIEW or type(body.get("schemaVersion")) is not int or body["schemaVersion"] != 1
                or body.get("contractVersion") != "1.0.0" or body.get("systemUids") != [uid]
                or not SHA.fullmatch(body.get("recordSetSha256", ""))
                or not isinstance(body.get("confirmationToken"), str)
                or not 32 <= len(body["confirmationToken"]) <= 1024):
            raise EnvironmentError("BACKEND_CLEANUP_PREVIEW_INVALID")
        if _timestamp(body["expiresAt"]) <= datetime.now(timezone.utc):
            raise EnvironmentError("BACKEND_CLEANUP_PREVIEW_EXPIRED")
        _counts(body["recordCounts"])
        _counts(body["nonmatchingRecordCounts"])
        return body

    def _brake(self, state, uid, observed):
        record = state["backends"]["brake"]
        previous = record.get("cleanup") or {}
        request = dict(schemaVersion=1, contractVersion="1.0.0", systemUids=[uid])
        preview = self._preview(uid, self._private("brake", observed["Id"], "preview", request))
        if any(preview["recordCounts"].values()):
            if previous.get("systemUid") == uid and previous.get("state") in ("SUBMITTING", "UNCERTAIN", "CONFIRMED"):
                raise EnvironmentError("BACKEND_CLEANUP_UNCERTAIN_OR_NEW_RECORDS_REMAIN")
            record["cleanup"] = dict(systemUid=uid, imageId=record["imageId"], state="SUBMITTING", checkedAt=now())
            self._save(state)
            try:
                result = self._private("brake", observed["Id"], "execute", dict(request, confirmationToken=preview["confirmationToken"]))
                if (not isinstance(result, dict) or set(result) != RESULT or type(result.get("schemaVersion")) is not int or result["schemaVersion"] != 1
                        or result.get("contractVersion") != "1.0.0" or result.get("systemUids") != [uid]
                        or not SHA.fullmatch(result.get("nonmatchingRecordSetSha256", ""))
                        or _counts(result.get("deletedRecordCounts")) != preview["recordCounts"]
                        or any(_counts(result.get("remainingMatchingRecordCounts")).values())):
                    raise EnvironmentError("BACKEND_CLEANUP_RESULT_INVALID")
                _counts(result.get("nonmatchingRecordCounts"))
                _timestamp(result["completedAt"])
                preview = self._preview(uid, self._private("brake", observed["Id"], "preview", request))
                if any(preview["recordCounts"].values()):
                    raise EnvironmentError("BACKEND_CLEANUP_NOT_EMPTY")
            except EnvironmentError:
                record["cleanup"].update(state="UNCERTAIN", checkedAt=now())
                self._save(state)
                raise
        # Zero after unknown response is authoritative absence, not a replay.
        record["cleanup"] = dict(systemUid=uid, imageId=record["imageId"], state="CONFIRMED", checkedAt=now(),
            matchingRecordCounts=preview["recordCounts"], nonmatchingRecordCounts=preview["nonmatchingRecordCounts"],
            scope="EXACT_TEST_PRODUCT_DATA")
        self._save(state)

    def _tire(self, state, uid, observed):
        value = self._private("tire", observed["Id"], "foundation-proof")
        if value != FOUNDATION or any(type(value[key]) is not type(expected) for key, expected in FOUNDATION.items()):
            raise EnvironmentError("TIRE_FOUNDATION_EMPTY_PROOF_UNAVAILABLE")
        record = state["backends"]["tire"]
        record["cleanup"] = dict(systemUid=uid, imageId=record["imageId"], state="CONFIRMED", checkedAt=now(), **FOUNDATION)
        self._save(state)

    def _empty_store(self, state):
        observed = self._owned(state, "brake", running=True)
        body = self._private("brake", observed["Id"], "empty-proof", dict(schemaVersion=1, contractVersion="1.0.0"))
        if (not isinstance(body, dict) or set(body) != {"schemaVersion", "contractVersion", "state", "databaseSchemaVersion", "recordCounts", "observedAt"}
                or type(body.get("schemaVersion")) is not int or body["schemaVersion"] != 1
                or body.get("contractVersion") != "1.0.0" or type(body.get("databaseSchemaVersion")) is not int
                or body["databaseSchemaVersion"] != 2 or body.get("state") not in ("EMPTY", "NONEMPTY")):
            raise EnvironmentError("BACKEND_WHOLE_STORE_EMPTY_PROOF_UNAVAILABLE")
        _timestamp(body["observedAt"])
        if body["state"] != "EMPTY" or any(_counts(body.get("recordCounts")).values()):
            raise EnvironmentError("BACKEND_NONMATCHING_DATA_PRESERVED")
        state["backends"]["brake"]["cleanup"]["wholeStoreEmpty"] = True
        self._save(state)

    def _proofs(self, state, uid):
        for team in TEAMS:
            record = state["backends"][team]
            proof = record.get("cleanup") or {}
            if (proof.get("state") != "CONFIRMED" or proof.get("systemUid") != uid
                    or proof.get("imageId") != record["imageId"]):
                return False
            if team == "brake":
                if any(_counts(proof.get("matchingRecordCounts")).values()):
                    return False
                _counts(proof.get("nonmatchingRecordCounts"))
            elif any(proof.get(key) != value or type(proof.get(key)) is not type(value) for key, value in FOUNDATION.items()):
                return False
        return True

    def _layout(self, state):
        directory = self.root / ".run/demo-current/backends"
        if directory.exists() or directory.is_symlink():
            self.environment._directory(".run/demo-current/backends")
            if any(path.name not in ("brake-compose.json", "tire-compose.json", "context") for path in directory.iterdir()):
                raise EnvironmentError("BACKEND_UNTRACKED_LOCAL_FILE")
        context = self.root / CONTEXT
        if context.parent.exists() or context.parent.is_symlink():
            self.environment._directory(str(context.parent.relative_to(self.root)))
            if any(path.name != "current-unit-context.json" for path in context.parent.iterdir()):
                raise EnvironmentError("BACKEND_UNTRACKED_CONTEXT_FILE")
        for team in TEAMS:
            record = state["backends"][team]
            path = self.root / record["composePath"]
            if path.exists() or path.is_symlink():
                self.environment._owned_file(path)
                if read_json(path) != self.service._spec(state, team, record["imageId"]):
                    raise EnvironmentError("BACKEND_COMPOSE_RECONCILIATION_REQUIRED")
            elif (record.get("cleanup") or {}).get("composeRemoval") not in ("REMOVE_PENDING", "REMOVED"):
                raise EnvironmentError("BACKEND_COMPOSE_MISSING")

    def _stop(self, state):
        for team in TEAMS:
            state["backends"][team]["cleanup"]["stopRequested"] = True
        self._save(state)
        for team in TEAMS:
            observed = self._owned(state, team)
            if observed and observed.get("State", {}).get("Running"):
                self.service.execute("stop", team)
                current = read_json(self.root / JOURNAL)
                state.clear()
                state.update(current)
                if (self._owned(state, team) or {}).get("State", {}).get("Running"):
                    raise EnvironmentError("BACKEND_STOP_NOT_CONFIRMED")

    def _remove_context(self, state):
        path = self.root / CONTEXT
        progress = state["backends"]["brake"]["cleanup"]
        if path.exists() or path.is_symlink():
            identity = self.environment._owned_file(path)
            if read_json(path) != project_context(state):
                raise EnvironmentError("BACKEND_CLEANUP_CONTEXT_CHANGED")
            if progress.get("contextRemoval") == "REMOVED":
                raise EnvironmentError("BACKEND_CLEANUP_CONTEXT_REAPPEARED")
            if progress.get("contextRemoval") == "REMOVE_PENDING" and progress.get("contextIdentity") != identity:
                raise EnvironmentError("BACKEND_CLEANUP_CONTEXT_CHANGED")
            progress.update(contextRemoval="REMOVE_PENDING", contextIdentity=identity)
            self._save(state)
            self.environment._unlink_owned(path, identity)
        elif progress.get("contextRemoval") not in ("REMOVE_PENDING", "REMOVED"):
            raise EnvironmentError("BACKEND_CONTEXT_ABSENCE_NOT_PROVEN")
        progress["contextRemoval"] = "REMOVED"
        self._save(state)

    def _remove_resource(self, state, team, kind, name):
        record = state["backends"][team]
        proof = record["cleanup"]
        field = kind + "Removal"
        observed = self._owned(state, team) if kind == "container" else self._resource(state, team, kind, name)
        if observed:
            if proof.get(field) == "REMOVED" or (kind == "container" and observed.get("State", {}).get("Running")):
                raise EnvironmentError("BACKEND_RESOURCE_REAPPEARED_OR_RUNNING")
            proof[field] = "REMOVE_PENDING"
            self._save(state)
            # Fixed names only; no force, down --volumes or ownership adoption.
            self.service._docker(kind, "rm", observed["Id"] if kind == "container" else name)
            remaining = self.service._inspect(kind, name)
            if remaining is not None:
                raise EnvironmentError("BACKEND_RESOURCE_REMOVAL_UNCONFIRMED")
        elif proof.get(field) not in ("REMOVE_PENDING", "REMOVED"):
            raise EnvironmentError("BACKEND_RESOURCE_ABSENCE_NOT_PROVEN")
        proof[field] = "REMOVED"
        self._save(state)

    def _finish_single(self, state):
        for team in TEAMS:
            self._remove_resource(state, team, "container", "aosedge-demo-" + team + "-cloud")
            self._remove_resource(state, team, "volume", "aosedge_demo_" + team + "_cloud_v1")
            self._remove_resource(state, team, "network", "aosedge-demo-" + team + "-cloud-v1")
        for team in TEAMS:
            record = state["backends"][team]
            progress = record["cleanup"]
            path = self.root / record["composePath"]
            if path.exists() or path.is_symlink():
                identity = self.environment._owned_file(path)
                if (progress.get("composeRemoval") == "REMOVED" or
                        (progress.get("composeRemoval") == "REMOVE_PENDING" and progress.get("composeIdentity") != identity)):
                    raise EnvironmentError("BACKEND_CLEANUP_COMPOSE_CHANGED")
                progress.update(composeRemoval="REMOVE_PENDING", composeIdentity=identity)
                self._save(state)
                self.environment._unlink_owned(path, identity)
            elif progress.get("composeRemoval") not in ("REMOVE_PENDING", "REMOVED"):
                raise EnvironmentError("BACKEND_COMPOSE_ABSENCE_NOT_PROVEN")
            progress["composeRemoval"] = "REMOVED"
            self._save(state)
        for path in ((self.root / CONTEXT).parent, self.root / ".run/demo-current/backends"):
            if path.exists():
                path.rmdir()
                sync_directory(path.parent)
        state.pop("backends")
        self._save(state)

    def confirm_test_cleanup(self, state):
        with self.environment._writer():
            item = state.get("vehicles", {}).get("test", {})
            uid = item.get("systemUid")
            if (not isinstance(uid, str) or not UID.fullmatch(uid)
                    or item.get("cloud", {}).get("lifecycle") != "DELETED"
                    or item.get("cloud", {}).get("absenceConfirmed") is not True
                    or item.get("runtime", {}).get("state") != "STOPPED"
                    or item.get("runtime", {}).get("pid") is not None or state.get("currentVehicle") == "test"):
                raise EnvironmentError("BACKEND_CLEANUP_REQUIRES_RETIRED_STOPPED_TEST")
            records = state.get("backends")
            if not isinstance(records, dict) or set(records) != set(TEAMS):
                raise EnvironmentError("BACKEND_CLEANUP_BOTH_OWNED_BACKENDS_REQUIRED")
            for team in TEAMS:
                self._owned(state, team)
                record = state["backends"][team]
                self.service._image(record["imageId"])
                for kind, name in (("volume", "aosedge_demo_" + team + "_cloud_v1"),
                                   ("network", "aosedge-demo-" + team + "-cloud-v1")):
                    resource = self._resource(state, team, kind, name)
                    if resource is None and (record.get("cleanup") or {}).get(kind + "Removal") not in ("REMOVE_PENDING", "REMOVED"):
                        raise EnvironmentError("BACKEND_CLEANUP_RESOURCE_MISSING")
            self._layout(state)
            context = self.root / CONTEXT
            if context.exists() or context.is_symlink():
                self.environment._owned_file(context)
                if read_json(context) != project_context(state):
                    raise EnvironmentError("BACKEND_CLEANUP_CONTEXT_CHANGED")
                # Re-prove while running. Already stopped proven owners cannot
                # ingest; that exact state supports interrupted local cleanup.
                running = [self._owned(state, team) for team in TEAMS]
                stopping = all((record.get("cleanup") or {}).get("stopRequested") is True for record in records.values())
                if not self._proofs(state, uid) or (not stopping and any(value and value.get("State", {}).get("Running") for value in running)):
                    self._brake(state, uid, self._owned(state, "brake", running=True))
                    self._tire(state, uid, self._owned(state, "tire", running=True))
                    if "production" not in state["vehicles"]:
                        self._empty_store(state)
            elif not self._proofs(state, uid):
                raise EnvironmentError("BACKEND_CONTEXT_ABSENCE_NOT_PROVEN")
            elif any((self._owned(state, team) or {}).get("State", {}).get("Running") for team in TEAMS):
                raise EnvironmentError("BACKEND_CLEANUP_RUNNING_WITHOUT_CONTEXT")
            self._stop(state)
            if "production" not in state["vehicles"]:
                if any(state["backends"]["brake"]["cleanup"]["nonmatchingRecordCounts"].values()):
                    raise EnvironmentError("BACKEND_NONMATCHING_DATA_PRESERVED")
                if state["backends"]["brake"]["cleanup"].get("wholeStoreEmpty") is not True:
                    raise EnvironmentError("BACKEND_WHOLE_STORE_EMPTY_PROOF_UNAVAILABLE")
            self._remove_context(state)
            if "production" not in state["vehicles"]:
                self._finish_single(state)
            return True
