# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Test-only local lifecycle: preserve the peer and every shared resource.

The Cloud callback receives the *full* journal and must prove only Test's
authoritative absence. Backend cleanup also receives the full journal and must
return literal True after exact Test data/context cleanup. Neither callback may
erase Production state. Both are repeated before resumed local cleanup.
"""

import copy
import hashlib
import os
import stat
from pathlib import Path
from uuid import UUID, uuid4

from .environment import (EnvironmentError, FACTORY, JOURNAL, MANIFEST, OVERLAYS,
                          TEST_MANIFEST, factory_for, atomic_json, digest, encoded, sync_directory)
from .guest_access import ACCESS_FILES
from .status import object_id, read_json

ROOT_FIELDS = {"schemaVersion", "kind", "startedAt", "stage", "scope", "factory",
    "currentVehicle", "vehicles", "operations", "shared", "cloudBinding", "source",
    "componentOperations", "componentSchema", "smDemoProof", "demoPreparation",
    "backends", "demoLifecycle", "testRetirement", "workspace", "demoSubjects", "serviceOperations",
    "smServiceUpdateProof", "cmServiceUpdateProof"}

TEST_RECEIPTS = ("componentOperations", "componentSchema", "smDemoProof", "demoPreparation",
                 "serviceOperations", "smServiceUpdateProof", "cmServiceUpdateProof")


def _state(environment):
    environment._owned_file(environment.root / JOURNAL)
    value = read_json(environment.root / JOURNAL)
    if (not isinstance(value, dict) or set(value) - ROOT_FIELDS
            or type(value.get("schemaVersion")) is not int or value["schemaVersion"] != 1
            or value.get("kind") != "democtl.current-run"
            or value.get("stage") not in ("MANUFACTURED", "LOCAL_ACTIVE", "LOCAL_STOPPED", "RETIRING_LOCAL")
            or not isinstance(value.get("vehicles"), dict)
            or not value["vehicles"] or set(value["vehicles"]) - set(OVERLAYS)):
        raise EnvironmentError("TEST_LIFECYCLE_JOURNAL_INVALID")
    operations = value.get("operations")
    if (not isinstance(operations, list) or not operations or len(operations) > 2
            or any(not isinstance(operation, dict) for operation in operations)
            or operations[0].get("class") != "LOCAL_CREATE"
            or operations[0].get("state") != "COMPLETED"
            or operations[0].get("reconciliation") != "APPLIED"):
        raise EnvironmentError("TEST_LIFECYCLE_PRIOR_OPERATION_UNRESOLVED")
    for role, item in value["vehicles"].items():
        if not isinstance(item, dict):
            raise EnvironmentError("TEST_LIFECYCLE_VEHICLE_BINDING_INVALID")
        identity = UUID(object_id(item.get("localVmId")))
        if (item.get("overlay") != OVERLAYS[role] or item.get("state") != "MANUFACTURED"
                or item.get("sshPort") != (10022 if role == "test" else 10023)
                or item.get("mac") != "02:" + ":".join("%02x" % b for b in identity.bytes[:5])):
            raise EnvironmentError("TEST_LIFECYCLE_VEHICLE_BINDING_INVALID")
    return value


def _layout(environment, state):
    allowed = {"writer.lock", "journal.json", "test-access", "production-access", "source", "control", "backends",
               "production.qmp", "production.serial"}
    directory = environment.root / ".run/demo-current"
    if any(path.name not in allowed for path in directory.iterdir()):
        raise EnvironmentError("TEST_LIFECYCLE_UNTRACKED_RUNTIME_FILE")
    overlays = environment._directory(".local/demo-current")
    names = {Path(OVERLAYS[role]).name for role in state["vehicles"]}
    if any(path.name not in names for path in overlays.iterdir()):
        raise EnvironmentError("UNTRACKED_RUNTIME_FILES_PRESENT")


def _factory(environment, state, role="test"):
    factory = factory_for(state, role)
    manifest = environment.root / factory["manifestPath"]
    receipts = state.get("testRetirement", {}).get("targets", {})
    def removed(key, path):
        receipt = receipts.get(key, {})
        return (role == "test" and state["stage"] == "RETIRING_LOCAL"
            and receipt.get("path") == str(path.relative_to(environment.root))
            and receipt.get("state") in ("REMOVE_PENDING", "REMOVED")
            and not (environment.root / OVERLAYS["test"]).exists())
    if not manifest.exists() and not manifest.is_symlink() and removed("manifest", manifest):
        return {"image": {}}  # Child already absent; per-file receipts are checked below.
    environment._owned_file(manifest)
    if digest(manifest) != factory.get("manifestSha256"):
        raise EnvironmentError("CLEANUP_FACTORY_MANIFEST_CHANGED")
    metadata = read_json(manifest)
    image = metadata.get("image", {})
    if any(image.get(key) != factory.get(key) for key in ("path", "format", "version", "sha256")):
        raise EnvironmentError("CLEANUP_FACTORY_BINDING_INVALID")
    backing = environment.root / factory["path"]
    if not (not backing.exists() and not backing.is_symlink() and removed("factory", backing)):
        environment._regular_readonly(backing, image["sizeBytes"])
    # The peer may hold the immutable backing. No lsof/rehash of that large file.
    return metadata


def _terminal_receipts(state):
    """Do not make a new run inherit an old Test publication or uncertain call."""
    from .service_assignment import retirement_subjects
    retirement_subjects(state)
    for key in ("smServiceUpdateProof", "cmServiceUpdateProof"):
        if state.get(key) and state[key].get("state") != "APPLIED":
            raise EnvironmentError("TEST_RUNTIME_PROOF_RECONCILIATION_REQUIRED")
    records = state.get("componentOperations", {})
    if not isinstance(records, dict):
        raise EnvironmentError("COMPONENT_OPERATION_RECONCILIATION_REQUIRED")
    test_id = state["vehicles"]["test"].get("unitId")
    for record in records.values():
        if not isinstance(record, dict):
            raise EnvironmentError("COMPONENT_OPERATION_RECONCILIATION_REQUIRED")
        for action in ("upload", "approve", "unapprove", "send"):
            attempt = record.get(action)
            if not isinstance(attempt, dict) or not attempt.get("attemptStarted"):
                continue
            if attempt.get("state") == "CONFIRMED":
                continue
            if (action == "send" and test_id and attempt.get("unitId") == test_id
                    and state["vehicles"]["test"].get("cloud", {}).get("lifecycle") == "DELETED"):
                continue
            raise EnvironmentError("COMPONENT_OPERATION_RECONCILIATION_REQUIRED")
        # These are current-run VDP records, not the durable release ledger.
        # A peer-targeted send must not be discarded as a Test receipt.
        send = record.get("send") or {}
        if send.get("unitId") not in (None, test_id):
            raise EnvironmentError("COMPONENT_PEER_RECEIPTS_REQUIRE_RECONCILIATION")


def _targets(environment, state):
    targets = {"overlay": OVERLAYS["test"]}
    item = state["vehicles"]["test"]
    access = environment.root / ".run/demo-current/test-access"
    if access.exists() or access.is_symlink():
        environment._directory(".run/demo-current/test-access")
        if (not item.get("runtime", {}).get("accessCreated")
                or any(p.name not in ACCESS_FILES for p in access.iterdir())):
            raise EnvironmentError("UNTRACKED_ACCESS_MATERIAL_PRESENT")
        for name in ACCESS_FILES:
            path = access / name
            if path.exists() or path.is_symlink():
                targets["access:" + name] = str(path.relative_to(environment.root))
    if item.get("factory") is not None:
        factory = factory_for(state, "test")
        targets.update(factory=factory["path"], manifest=factory["manifestPath"])
    return targets


def retire_test(environment, cloud_check, backend_check):
    with environment._writer():
        if not (environment.root / JOURNAL).exists():
            return environment.retire(cloud_check=cloud_check)
        state = _state(environment)
        if "production" not in state["vehicles"]:
            if state.get("backends") and (backend_check is None or backend_check(state) is not True):
                raise EnvironmentError("TEST_BACKEND_CLEANUP_PROOF_REQUIRED")
            # The composer removes stopped/clean backend ownership and paths.
            # Existing retire still rejects any unhandled backend state.
            return environment.retire(cloud_check=cloud_check)
        if "test" not in state["vehicles"]:
            if state.get("testRetirement") != {"state": "COMPLETED"}:
                raise EnvironmentError("TEST_TARGET_NOT_CREATED")
            _layout(environment, state)
            access = environment.root / ".run/demo-current/test-access"
            if access.exists() or access.is_symlink():
                raise EnvironmentError("ORPHAN_ACCESS_MATERIAL_REQUIRES_RECONCILIATION")
            return dict(scope="TEST_ONLY", outcome="NO_CURRENT_TEST", removed=[], cloudActions=False)
        _layout(environment, state)
        metadata = _factory(environment, state)
        item = state["vehicles"]["test"]
        runtime = item.get("runtime") or {}
        if state.get("currentVehicle") == "test" or state.get("source", {}).get("operation"):
            raise EnvironmentError("CURRENT_VEHICLE_REQUIRES_PARK_OR_DETACH")
        if runtime and (runtime.get("state") != "STOPPED" or runtime.get("pid") is not None):
            raise EnvironmentError("VM_MUST_BE_STOPPED_BEFORE_RETIRE")
        cloud = item.get("cloud")
        protected = {key: copy.deepcopy(state.get(key)) for key in ("factory", "shared", "currentVehicle")}
        protected["production"] = copy.deepcopy(state["vehicles"]["production"])
        if cloud:
            if (cloud.get("lifecycle") != "DELETED" or cloud.get("absenceConfirmed") is not True
                    or any(not item.get(key) for key in ("unitId", "nodeId", "systemUid", "unitSetId"))):
                raise EnvironmentError("CLOUD_RETIREMENT_PROOF_REQUIRED")
            for key in ("unitId", "nodeId", "unitSetId"):
                object_id(item[key])
            if cloud_check is None or cloud_check(state) is not True:
                raise EnvironmentError("FRESH_CLOUD_RETIREMENT_CHECK_REQUIRED")
        elif any(item.get(key) is not None for key in ("unitId", "nodeId", "systemUid", "unitSetId")):
            raise EnvironmentError("CLOUD_RETIREMENT_PROOF_REQUIRED")
        if state.get("backends") and (backend_check is None or backend_check(state) is not True):
            raise EnvironmentError("TEST_BACKEND_CLEANUP_PROOF_REQUIRED")
        if (any(state.get(key) != value for key, value in protected.items() if key != "production")
                or state["vehicles"].get("production") != protected["production"]):
            raise EnvironmentError("TEST_RETIREMENT_PEER_CHANGED")
        _terminal_receipts(state)
        previous = state.get("testRetirement")
        resuming = state["stage"] == "RETIRING_LOCAL"
        if not resuming and (len(state["operations"]) != 1 or previous):
            raise EnvironmentError("TEST_LIFECYCLE_PRIOR_OPERATION_UNRESOLVED")
        targets = _targets(environment, state)
        if resuming:
            if (not isinstance(previous, dict) or set(previous) != {"state", "targets", "restoreStage"}
                    or previous["state"] != "SUBMITTING" or len(state["operations"]) != 2
                    or previous["restoreStage"] not in ("MANUFACTURED", "LOCAL_ACTIVE", "LOCAL_STOPPED")
                    or not isinstance(previous["targets"], dict)
                    or state["operations"][-1].get("class") != "LOCAL_RETIRE"
                    or state["operations"][-1].get("state") != "SUBMITTING"
                    or state["operations"][-1].get("knownExternalIds") != {}
                    or state["operations"][-1].get("target") != ["test"]):
                raise EnvironmentError("TEST_RETIREMENT_JOURNAL_INVALID")
            # Missing access files remain explicit intent, not newly guessed paths.
            for key, receipt in previous["targets"].items():
                expected = (factory_for(state, "test")["path"] if key == "factory" and item.get("factory") else
                    TEST_MANIFEST if key == "manifest" and item.get("factory") else
                    OVERLAYS["test"] if key == "overlay" else (
                    ".run/demo-current/test-access/" + key[7:] if key.startswith("access:") and key[7:] in ACCESS_FILES else None)
                    )
                if (not isinstance(receipt, dict) or set(receipt) != {"path", "identity", "state"}
                        or not expected or receipt.get("path") != expected or receipt.get("state") not in ("READY", "REMOVE_PENDING", "REMOVED")
                        or not isinstance(receipt.get("identity"), list) or len(receipt["identity"]) != 4
                        or any(type(value) is not int for value in receipt["identity"])):
                    raise EnvironmentError("TEST_RETIREMENT_JOURNAL_INVALID")
                targets[key] = expected
            if set(targets) != set(previous["targets"]):
                raise EnvironmentError("TEST_RETIREMENT_JOURNAL_INVALID")
        identities = {}
        for key, relative in targets.items():
            path = environment.root / relative
            receipt = previous["targets"][key] if resuming else {}
            if not path.exists() and not path.is_symlink():
                if not resuming or receipt["state"] not in ("REMOVE_PENDING", "REMOVED"):
                    raise EnvironmentError("CLEANUP_FILE_MISSING")
                continue
            if key == "overlay":
                identity = environment._untouched_overlay(path, factory_for(state, "test"), metadata["image"]["virtualSizeBytes"], runtime, bool(cloud))
            else:
                identity = environment._owned_file(path)
                environment._assert_unheld(path)
            if resuming and (receipt["state"] == "REMOVED" or receipt["identity"] != identity):
                raise EnvironmentError("CLEANUP_TARGET_CHANGED")
            identities[key] = identity
        if not resuming:
            state["testRetirement"] = dict(state="SUBMITTING", restoreStage=state["stage"], targets={
                key: dict(path=relative, identity=identities[key], state="READY") for key, relative in targets.items()})
            state["stage"] = "RETIRING_LOCAL"
            state["operations"].append(dict(id=str(uuid4()), team="DEMO_SOLUTION", authority="LOCAL_OPERATOR",
                **{"class": "LOCAL_RETIRE"}, target=["test"], state="SUBMITTING", knownExternalIds={},
                resourceKeys=["UNIT_LOCAL:" + item["localVmId"]], reconciliation="UNOBSERVABLE",
                requestFingerprint=hashlib.sha256(encoded(targets)).hexdigest(), lastRead=None))
            atomic_json(environment.root / JOURNAL, state)
        for key, relative in targets.items():
            receipt = state["testRetirement"]["targets"][key]
            if key in identities:
                receipt["state"] = "REMOVE_PENDING"
                atomic_json(environment.root / JOURNAL, state)
                environment._unlink_owned(environment.root / relative, identities[key])
            receipt["state"] = "REMOVED"
            atomic_json(environment.root / JOURNAL, state)
        access = environment.root / ".run/demo-current/test-access"
        if access.exists():
            access.rmdir()
            sync_directory(access.parent)
        state["stage"] = state["testRetirement"]["restoreStage"]
        state["testRetirement"] = dict(state="COMPLETED")
        state["vehicles"].pop("test")
        state["operations"] = state["operations"][:1]
        for key in TEST_RECEIPTS:
            state.pop(key, None)
        # demoLifecycle is the caller's in-progress orchestration receipt.
        atomic_json(environment.root / JOURNAL, state)
        return dict(scope="TEST_ONLY", outcome="REMOVED", removed=list(targets.values()),
            preserved=["production", "factory", "shared DNS", "source", "release continuity", "Cloud releases"],
            cloudActions=False, cloudReadsPerformed=bool(cloud), recoverable=False)


def add_test(environment, image):
    state = _state(environment)
    if (set(state["vehicles"]) != {"production"} or len(state["operations"]) != 1
            or state["stage"] == "RETIRING_LOCAL"):
        raise EnvironmentError("CURRENT_RUN_EXISTS_RECOVERY_OR_RETIREMENT_REQUIRED")
    _layout(environment, state)
    access = environment.root / ".run/demo-current/test-access"
    if access.exists() or access.is_symlink():
        raise EnvironmentError("ORPHAN_ACCESS_MATERIAL_REQUIRES_RECONCILIATION")
    metadata = _factory(environment, state, "production")
    separate_factory = (image.sha256 != state["factory"]["sha256"] or image.selector != metadata.get("sourceSelector")
            or image.image_format != state["factory"]["format"])
    for key in TEST_RECEIPTS:
        if state.get(key):
            raise EnvironmentError("TEST_RECREATE_OLD_RECEIPTS_PRESENT")
    if state.get("testRetirement") not in (None, {"state": "COMPLETED"}):
        raise EnvironmentError("TEST_RETIREMENT_JOURNAL_INVALID")
    identity = uuid4()
    item = dict(overlay=OVERLAYS["test"], localVmId=str(identity),
        mac="02:" + ":".join("%02x" % b for b in identity.bytes[:5]), sshPort=10022,
        state="PLANNED", unitId=None, nodeId=None, unitSetId=None)
    operation = dict(id=str(uuid4()), team="DEMO_SOLUTION", authority="LOCAL_OPERATOR", target=["test"],
        **{"class": "LOCAL_ADD_TEST"}, state="SUBMITTING", reconciliation="UNOBSERVABLE",
        knownExternalIds={}, resourceKeys=["UNIT_LOCAL:" + str(identity)], lastRead=None,
        requestFingerprint=hashlib.sha256(encoded([image.sha256, "test"])).hexdigest())
    prior_stage = state["stage"]
    state["vehicles"]["test"] = item
    state["operations"].append(operation)
    state["stage"] = "CREATING"
    atomic_json(environment.root / JOURNAL, state)
    overlay = environment.root / OVERLAYS["test"]
    try:
        if separate_factory:
            backing, virtual_size = environment._copy_factory(image, state, "test")
        else:
            backing = environment.root / state["factory"]["path"]
            virtual_size = metadata["image"]["virtualSizeBytes"]
        fd = os.open(str(overlay), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        os.close(fd)
        environment._command(["create", "-f", "qcow2", "-F", image.image_format, "-b", str(backing), str(overlay)])
        info = environment._info(overlay)
        if (info.get("format") != "qcow2" or info.get("backing-filename") != str(backing)
                or info.get("backing-filename-format") != image.image_format
                or info.get("virtual-size") != virtual_size
                or stat.S_IMODE(overlay.stat().st_mode) != 0o600):
            raise EnvironmentError("OVERLAY_BACKING_MISMATCH")
        item["state"] = "MANUFACTURED"
        state["operations"] = state["operations"][:1]
        state["stage"] = prior_stage
        state["scope"] = "DUAL_ROLE"
        state.pop("testRetirement", None)
        atomic_json(environment.root / JOURNAL, state)
        return state
    except (OSError, ValueError) as error:
        state["stage"] = "RECOVERY_REQUIRED"
        operation.update(state="UNCERTAIN", reconciliation="UNOBSERVABLE", lastRead={"reason": "LOCAL_ADD_TEST_FAILED"})
        if not (environment.root / (JOURNAL + ".pending")).exists():
            atomic_json(environment.root / JOURNAL, state)
        raise EnvironmentError(str(error) if isinstance(error, EnvironmentError) else "LOCAL_ADD_TEST_IO_ERROR") from None
