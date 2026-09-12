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
import sys
from datetime import datetime, timezone

from .backend_context import CONTEXT, UID, project_context
from .backends import DIGEST, TEAMS
from .environment import EnvironmentError, JOURNAL, MANIFEST, OVERLAYS, atomic_json, digest, encoded, sync_directory
from .status import now, object_id, read_json

COUNTS = {"messages", "windows", "assessments", "events", "advisories", "quarantine"}
TIRE_COUNTS = {"messages", "assessments", "events", "advisories", "functionStatus", "quarantine"}
SHA = re.compile(r"[a-f0-9]{64}")
PREVIEW = {"schemaVersion", "contractVersion", "systemUids", "recordCounts", "nonmatchingRecordCounts",
           "recordSetSha256", "confirmationToken", "expiresAt"}
RESULT = {"schemaVersion", "contractVersion", "systemUids", "deletedRecordCounts", "remainingMatchingRecordCounts",
          "nonmatchingRecordCounts", "nonmatchingRecordSetSha256", "completedAt"}
FOUNDATION = dict(scope="FOUNDATION_ONLY", productIngestion=False, schemaVersion=1,
                  noProductTablesOrRecords=True, unknownTables=False, removalEligible=True)


def _counts(value, keys=COUNTS):
    if (not isinstance(value, dict) or set(value) != keys
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

    def _test_released(self, state, unprovisioned=False):
        item = state["vehicles"]["test"]
        if item.get("overlay") != OVERLAYS["test"]:
            raise EnvironmentError("BACKEND_TEST_OVERLAY_BINDING_INVALID")
        path = self.root / item["overlay"]
        if path.exists() or path.is_symlink():
            if unprovisioned:
                from .environment import factory_for
                factory = factory_for(state, "test")
                manifest = self.root / factory["manifestPath"]
                self.environment._owned_file(manifest)
                if digest(manifest) != factory.get("manifestSha256"):
                    raise EnvironmentError("VM_FACTORY_MANIFEST_CHANGED")
                metadata = read_json(manifest)
                self.environment._untouched_overlay(path, factory, metadata["image"]["virtualSizeBytes"], item.get("runtime"))
            else:
                self.environment._owned_file(path)
                self.environment._assert_unheld(path)
        else:
            scoped = state.get("testRetirement", {}).get("targets", {}).get("overlay", {})
            legacy = state.get("retirement", {}).get("test", {})
            if not ((scoped.get("path") == OVERLAYS["test"] and scoped.get("state") in ("REMOVE_PENDING", "REMOVED"))
                    or legacy.get("state") in ("REMOVE_PENDING", "REMOVED")):
                raise EnvironmentError("BACKEND_TEST_OVERLAY_ABSENCE_NOT_PROVEN")

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
            if (record.get("state") == "STOPPED" and (record.get("cleanup") or {}).get("stopRequested") is True
                    and observed.get("State", {}).get("Running") is True):
                raise EnvironmentError("BACKEND_CLEANUP_RESTARTED_AFTER_PROOF")
            mounts = observed.get("Mounts") or []
            volume = "aosedge_demo_" + team + "_cloud_v1"
            data = [mount for mount in mounts if mount.get("Destination") == "/data"]
            context = [mount for mount in mounts if mount.get("Destination") == "/run/demo-control/context"]
            host_context = str((self.root / CONTEXT).parent)
            accepted_sources = (host_context, "/host_mnt" + host_context) if sys.platform == "darwin" else (host_context,)
            if (len(data) != 1 or data[0].get("Type") != "volume" or data[0].get("Name") != volume
                    or data[0].get("RW") is not True or len(context) != 1
                    or context[0].get("Type") != "bind" or context[0].get("RW") is not False
                    or context[0].get("Source") not in accepted_sources):
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
        if team not in TEAMS or operation not in ("preview", "execute", "empty-proof", "mock-preview", "mock-execute", "mock-empty-proof", *( ("foundation-proof",) if team == "tire" else ())):
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

    def _brake(self, state, uid, observed, mock=False):
        record = state["backends"]["brake"]
        key = "mockCleanup" if mock else "cleanup"
        prefix = "mock-" if mock else ""
        previous = record.get(key) or {}
        request = dict(schemaVersion=1, contractVersion="1.0.0", systemUids=[uid])
        preview = self._preview(uid, self._private("brake", observed["Id"], prefix + "preview", request))
        if any(preview["recordCounts"].values()):
            if previous.get("systemUid") == uid and previous.get("state") in ("SUBMITTING", "UNCERTAIN", "CONFIRMED"):
                raise EnvironmentError("BACKEND_CLEANUP_UNCERTAIN_OR_NEW_RECORDS_REMAIN")
            record[key] = dict(systemUid=uid, imageId=record["imageId"], state="SUBMITTING", checkedAt=now())
            self._save(state)
            try:
                result = self._private("brake", observed["Id"], prefix + "execute", dict(request, confirmationToken=preview["confirmationToken"]))
                if (not isinstance(result, dict) or set(result) != RESULT or type(result.get("schemaVersion")) is not int or result["schemaVersion"] != 1
                        or result.get("contractVersion") != "1.0.0" or result.get("systemUids") != [uid]
                        or not SHA.fullmatch(result.get("nonmatchingRecordSetSha256", ""))
                        or _counts(result.get("deletedRecordCounts")) != preview["recordCounts"]
                        or any(_counts(result.get("remainingMatchingRecordCounts")).values())):
                    raise EnvironmentError("BACKEND_CLEANUP_RESULT_INVALID")
                _counts(result.get("nonmatchingRecordCounts"))
                _timestamp(result["completedAt"])
                preview = self._preview(uid, self._private("brake", observed["Id"], prefix + "preview", request))
                if any(preview["recordCounts"].values()):
                    raise EnvironmentError("BACKEND_CLEANUP_NOT_EMPTY")
            except EnvironmentError:
                record[key].update(state="UNCERTAIN", checkedAt=now())
                self._save(state)
                raise
        # Zero after unknown response is authoritative absence, not a replay.
        record[key] = dict(systemUid=uid, imageId=record["imageId"], state="CONFIRMED", checkedAt=now(),
            matchingRecordCounts=preview["recordCounts"], nonmatchingRecordCounts=preview["nonmatchingRecordCounts"],
            scope="EXACT_TEST_PRODUCT_DATA")
        self._save(state)

    def _tire(self, state, uid, observed):
        if self._tire_product(state):
            if uid is None:
                record = state["backends"]["tire"]
                record["cleanup"] = dict(imageId=record["imageId"], state="OBSERVING", scope="UNPROVISIONED_STORE_OBSERVATION")
                self._empty_store(state, allow_nonempty="production" in state["vehicles"], team="tire")
                record["cleanup"]["state"] = "CONFIRMED"
                return
            return self._tire_product_cleanup(state, uid, observed)
        value = self._private("tire", observed["Id"], "foundation-proof")
        if value != FOUNDATION or any(type(value[key]) is not type(expected) for key, expected in FOUNDATION.items()):
            raise EnvironmentError("TIRE_FOUNDATION_EMPTY_PROOF_UNAVAILABLE")
        record = state["backends"]["tire"]
        record["cleanup"] = dict(systemUid=uid, imageId=record["imageId"], state="CONFIRMED", checkedAt=now(), **FOUNDATION)
        self._save(state)

    def _tire_product(self, state):
        protocol = state["backends"]["tire"].get("privateCleanupProtocol")
        if protocol not in (None, "tire-product-v1"):
            raise EnvironmentError("BACKEND_CLEANUP_PROTOCOL_UNSUPPORTED")
        return protocol == "tire-product-v1"

    def _tire_product_cleanup(self, state, uid, observed, mock=False):
        record = state["backends"]["tire"]
        key = "mockCleanup" if mock else "cleanup"
        prefix = "mock-" if mock else ""
        previous = record.get(key) or {}
        request = dict(schemaVersion=1, contractVersion="1.0.0", systemUids=[uid])
        def preview():
            body = self._private("tire", observed["Id"], prefix + "preview", request)
            expected = (PREVIEW - {"contractVersion"}) | {"nonmatchingRecordSetSha256"}
            if (not isinstance(body, dict) or set(body) != expected or type(body.get("schemaVersion")) is not int
                    or body["schemaVersion"] != 1 or body.get("systemUids") != [uid]
                    or not all(isinstance(body.get(key), str) and SHA.fullmatch(body[key]) for key in ("recordSetSha256", "nonmatchingRecordSetSha256"))
                    or not isinstance(body.get("confirmationToken"), str) or not 32 <= len(body["confirmationToken"]) <= 1024):
                raise EnvironmentError("TIRE_CLEANUP_PREVIEW_INVALID")
            if _timestamp(body["expiresAt"]) <= datetime.now(timezone.utc):
                raise EnvironmentError("BACKEND_CLEANUP_PREVIEW_EXPIRED")
            _counts(body["recordCounts"], TIRE_COUNTS)
            _counts(body["nonmatchingRecordCounts"], TIRE_COUNTS)
            return body
        before = preview()
        if any(before["recordCounts"].values()):
            if previous.get("systemUid") == uid and previous.get("state") in ("SUBMITTING", "UNCERTAIN", "CONFIRMED"):
                raise EnvironmentError("BACKEND_CLEANUP_UNCERTAIN_OR_NEW_RECORDS_REMAIN")
            record[key] = dict(systemUid=uid, imageId=record["imageId"], state="SUBMITTING", checkedAt=now())
            self._save(state)
            try:
                result = self._private("tire", observed["Id"], prefix + "execute", dict(request, confirmationToken=before["confirmationToken"]))
                expected = (RESULT - {"remainingMatchingRecordCounts"}) | {"remainingRecordCounts", "state"}
                if (not isinstance(result, dict) or set(result) != expected or type(result.get("schemaVersion")) is not int
                        or result["schemaVersion"] != 1 or result.get("contractVersion") != "1.0.0" or result.get("state") != "CLEANED"
                        or result.get("systemUids") != [uid] or _counts(result.get("deletedRecordCounts"), TIRE_COUNTS) != before["recordCounts"]
                        or any(_counts(result.get("remainingRecordCounts"), TIRE_COUNTS).values())
                        or _counts(result.get("nonmatchingRecordCounts"), TIRE_COUNTS) != before["nonmatchingRecordCounts"]
                        or result.get("nonmatchingRecordSetSha256") != before["nonmatchingRecordSetSha256"]):
                    raise EnvironmentError("TIRE_CLEANUP_RESULT_INVALID")
                _timestamp(result["completedAt"])
                after = preview()
                if (any(after["recordCounts"].values()) or after["nonmatchingRecordCounts"] != before["nonmatchingRecordCounts"]
                        or after["nonmatchingRecordSetSha256"] != before["nonmatchingRecordSetSha256"]):
                    raise EnvironmentError("TIRE_CLEANUP_NOT_CONFIRMED")
                before = after
            except EnvironmentError:
                record[key].update(state="UNCERTAIN", checkedAt=now())
                self._save(state)
                raise
        record[key] = dict(systemUid=uid, imageId=record["imageId"], state="CONFIRMED", checkedAt=now(),
            matchingRecordCounts=before["recordCounts"], nonmatchingRecordCounts=before["nonmatchingRecordCounts"],
            nonmatchingRecordSetSha256=before["nonmatchingRecordSetSha256"], scope="EXACT_TEST_PRODUCT_DATA")
        self._save(state)

    def _empty_store(self, state, allow_nonempty=False, team="brake", mock=False):
        observed = self._owned(state, team, running=True)
        body = self._private(team, observed["Id"], "mock-empty-proof" if mock else "empty-proof", dict(schemaVersion=1, contractVersion="1.0.0"))
        # N3 adds Brake projection schema 3; Tire retains schema 2. The admin
        # proof, ownership/selector checks and actual empty-state rules stay intact.
        supported_schema_versions = (2, 3) if team == "brake" else (2,)
        if (not isinstance(body, dict) or set(body) != {"schemaVersion", "contractVersion", "state", "databaseSchemaVersion", "recordCounts", "observedAt"}
                or type(body.get("schemaVersion")) is not int or body["schemaVersion"] != 1
                or body.get("contractVersion") != "1.0.0" or type(body.get("databaseSchemaVersion")) is not int
                or body["databaseSchemaVersion"] not in supported_schema_versions or body.get("state") not in ("EMPTY", "NONEMPTY")):
            raise EnvironmentError("BACKEND_WHOLE_STORE_EMPTY_PROOF_UNAVAILABLE")
        _timestamp(body["observedAt"])
        counts = _counts(body.get("recordCounts"), TIRE_COUNTS if team == "tire" else COUNTS)
        empty = not any(counts.values())
        if (body["state"] == "EMPTY") is not empty:
            raise EnvironmentError("BACKEND_WHOLE_STORE_EMPTY_PROOF_UNAVAILABLE")
        if not empty and not allow_nonempty:
            raise EnvironmentError("BACKEND_NONMATCHING_DATA_PRESERVED")
        state["backends"][team]["mockCleanup" if mock else "cleanup"].update(wholeStoreEmpty=empty, recordCounts=counts)
        self._save(state)

    def _mock_enabled(self, record):
        protocol = record.get("mockCleanupProtocol")
        if protocol not in (None, "isolated-mock-v1"):
            raise EnvironmentError("BACKEND_MOCK_CLEANUP_PROTOCOL_UNSUPPORTED")
        return protocol is not None

    def _mock_cleanup(self, state, uid=None, local_id=None):
        for team in TEAMS:
            record = state["backends"][team]
            if not self._mock_enabled(record):
                continue
            observed = self._owned(state, team, running=True)
            if uid is not None:
                cleanup = self._brake if team == "brake" else self._tire_product_cleanup
                cleanup(state, uid, observed, mock=True)
            else:
                record["mockCleanup"] = dict(localVmId=local_id, imageId=record["imageId"], state="OBSERVING")
            self._empty_store(state, team=team, mock=True, allow_nonempty="production" in state["vehicles"])
            record["mockCleanup"]["state"] = "CONFIRMED"
            self._save(state)

    def _mock_proven(self, state, team, uid=None, local_id=None):
        record = state["backends"][team]
        if not self._mock_enabled(record):
            return True
        proof = record.get("mockCleanup") or {}
        counts = proof.get("recordCounts")
        if (proof.get("state") != "CONFIRMED" or proof.get("imageId") != record["imageId"]
                or proof.get("systemUid") != uid or proof.get("localVmId") != local_id
                or not isinstance(counts, dict)):
            return False
        empty = not any(_counts(counts, TIRE_COUNTS if team == "tire" else COUNTS).values())
        return proof.get("wholeStoreEmpty") is empty and (empty or "production" in state["vehicles"])

    def _proofs(self, state, uid):
        for team in TEAMS:
            if not self._mock_proven(state, team, uid=uid):
                return False
            record = state["backends"][team]
            proof = record.get("cleanup") or {}
            if (proof.get("state") != "CONFIRMED" or proof.get("systemUid") != uid
                    or proof.get("imageId") != record["imageId"]):
                return False
            if team == "brake" or self._tire_product(state):
                keys = TIRE_COUNTS if team == "tire" else COUNTS
                if any(_counts(proof.get("matchingRecordCounts"), keys).values()):
                    return False
                _counts(proof.get("nonmatchingRecordCounts"), keys)
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
                try:
                    self.service.execute("stop", team)
                finally:
                    # The core may have persisted a stopped/uncertain result
                    # before losing its reply. Keep the caller's same object
                    # current so its error receipt cannot overwrite that fact.
                    current = read_json(self.root / JOURNAL)
                    state.clear()
                    state.update(current)
                if (self._owned(state, team) or {}).get("State", {}).get("Running"):
                    raise EnvironmentError("BACKEND_STOP_NOT_CONFIRMED")
            elif state["backends"][team].get("state") != "STOPPED":
                state["backends"][team].update(state="STOPPED", confirmedAt=now())
                self._save(state)

    def _remove_context(self, state):
        # This public projection is not a disk, credential or data store. Once
        # both exact containers are gone, an old Docker filesystem reference
        # must not require restarting the engine (and unrelated applications).
        for team in TEAMS:
            record = state["backends"][team]
            if (record.get("state") != "STOPPED"
                    or record.get("cleanup", {}).get("containerRemoval") != "REMOVED"
                    or self._owned(state, team) is not None):
                raise EnvironmentError("BACKEND_CONTEXT_CONTAINERS_NOT_RELEASED")
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
            # Only this fixed, content-validated projection uses POSIX unlink
            # without the generic zero-open-handles gate. All VM/access/store
            # cleanup continues through EnvironmentService._unlink_owned.
            if self.environment._owned_file(path) != identity:
                raise EnvironmentError("BACKEND_CLEANUP_CONTEXT_CHANGED")
            try:
                path.unlink()
                sync_directory(path.parent)
            except OSError:
                raise EnvironmentError("BACKEND_CONTEXT_UNLINK_UNCONFIRMED") from None
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
        if any(self._mock_enabled(state["backends"][team]) and
                state["backends"][team].get("mockCleanup", {}).get("wholeStoreEmpty") is not True for team in TEAMS):
            raise EnvironmentError("BACKEND_MOCK_WHOLE_STORE_EMPTY_PROOF_UNAVAILABLE")
        if self._tire_product(state) and state["backends"]["tire"]["cleanup"].get("wholeStoreEmpty") is not True:
            raise EnvironmentError("BACKEND_WHOLE_STORE_EMPTY_PROOF_UNAVAILABLE")
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
            self._test_released(state)
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
                    self._mock_cleanup(state, uid=uid)
                    if "production" not in state["vehicles"]:
                        self._empty_store(state)
                        if self._tire_product(state):
                            self._empty_store(state, team="tire")
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
            # Docker Desktop can retain a stopped container's context bind.
            # Release only the exact owned instances; peer storage stays intact.
            for team in TEAMS:
                self._remove_resource(state, team, "container", "aosedge-demo-" + team + "-cloud")
            self._remove_context(state)
            if "production" not in state["vehicles"]:
                self._finish_single(state)
            return True

    def _unprovisioned_proofs(self, state, local_id):
        for team in TEAMS:
            if not self._mock_proven(state, team, local_id=local_id):
                return False
            record = state["backends"][team]
            proof = record.get("cleanup") or {}
            if (proof.get("state") != "CONFIRMED" or proof.get("localVmId") != local_id
                    or proof.get("imageId") != record["imageId"] or "systemUid" in proof):
                return False
            if team == "brake" or self._tire_product(state):
                counts = _counts(proof.get("recordCounts"), TIRE_COUNTS if team == "tire" else COUNTS)
                if proof.get("wholeStoreEmpty") is not (not any(counts.values())):
                    return False
                if proof.get("scope") != "UNPROVISIONED_STORE_OBSERVATION":
                    return False
            elif any(proof.get(key) != value or type(proof.get(key)) is not type(value) for key, value in FOUNDATION.items()):
                return False
        return True

    def confirm_unprovisioned_cleanup(self, state):
        """Cleanup of a stopped, never-Cloud-attempted Test manufacture only.

No UID is invented. Whole-store read proves reset eligibility for single-Test.
With a peer, nonempty product storage is preserved without claiming Test-record
absence. Guest stop/overlay-digest proof is finally enforced by local retire.
"""
        with self.environment._writer():
            item = state.get("vehicles", {}).get("test", {})
            local_id = object_id(item.get("localVmId"))
            runtime = item.get("runtime") or {}
            if (any(item.get(key) is not None for key in ("unitId", "nodeId", "systemUid", "unitSetId", "cloud"))
                    or state.get("currentVehicle") == "test"
                    or (runtime and (runtime.get("state") != "STOPPED" or runtime.get("pid") is not None))
                    or (runtime.get("everStarted") and (runtime.get("stopProof") or {}).get("unprovisioned") is not True)
                    or any(operation.get("class") not in ("LOCAL_CREATE", "LOCAL_RETIRE") for operation in state.get("operations", []))):
                raise EnvironmentError("BACKEND_CLEANUP_REQUIRES_NEVER_PROVISIONED_TEST")
            self._test_released(state, unprovisioned=True)
            context = self.root / CONTEXT
            if context.exists() or context.is_symlink():
                raise EnvironmentError("BACKEND_UNPROVISIONED_CONTEXT_MUST_BE_ABSENT")
            records = state.get("backends")
            if not isinstance(records, dict) or set(records) != set(TEAMS):
                raise EnvironmentError("BACKEND_CLEANUP_BOTH_OWNED_BACKENDS_REQUIRED")
            for team in TEAMS:
                self._owned(state, team)
                record = records[team]
                self.service._image(record["imageId"])
                for kind, name in (("volume", "aosedge_demo_" + team + "_cloud_v1"),
                                   ("network", "aosedge-demo-" + team + "-cloud-v1")):
                    if self._resource(state, team, kind, name) is None and (record.get("cleanup") or {}).get(kind + "Removal") not in ("REMOVE_PENDING", "REMOVED"):
                        raise EnvironmentError("BACKEND_CLEANUP_RESOURCE_MISSING")
            self._layout(state)
            stopping = all((record.get("cleanup") or {}).get("stopRequested") is True for record in records.values())
            if not self._unprovisioned_proofs(state, local_id) or not stopping:
                for team in TEAMS:
                    self._owned(state, team, running=True)
                record = state["backends"]["brake"]
                record["cleanup"] = dict(localVmId=local_id, imageId=record["imageId"], state="OBSERVING", checkedAt=now(),
                    scope="UNPROVISIONED_STORE_OBSERVATION")
                self._save(state)
                self._empty_store(state, allow_nonempty="production" in state["vehicles"])
                record["cleanup"]["state"] = "CONFIRMED"
                self._save(state)
                self._tire(state, None, self._owned(state, "tire", running=True))
                state["backends"]["tire"]["cleanup"].pop("systemUid", None)
                state["backends"]["tire"]["cleanup"]["localVmId"] = local_id
                self._mock_cleanup(state, local_id=local_id)
                self._save(state)
            self._stop(state)
            if "production" not in state["vehicles"]:
                if state["backends"]["brake"]["cleanup"].get("wholeStoreEmpty") is not True:
                    raise EnvironmentError("BACKEND_NONMATCHING_DATA_PRESERVED")
                self._finish_single(state)
            return True
