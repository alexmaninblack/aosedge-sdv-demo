# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Local manufacture only: one byte-for-byte copy, fresh role overlays, no boot."""

import fcntl
import hashlib
import json
import os
import shutil
import stat
import subprocess
import threading
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

from .images import ImageCatalog
from .status import now, object_id, project_root, read_json

OVERLAYS = {"test": ".local/demo-current/validation.qcow2",
            "production": ".local/demo-current/production.qcow2"}
FACTORY = {"raw": ".local/factory/oem-demo-factory.img",
           "qcow2": ".local/factory/oem-demo-factory.qcow2"}
MANIFEST = ".local/factory/oem-demo-factory.manifest.json"
JOURNAL = ".run/demo-current/journal.json"
SOURCE_RUNTIME_FILES = frozenset(("input.json", "configuration.json", "manifest.json",
    "startup-timeline.json", "startup-timeline.json.lock", "start.gate", "events.jsonl",
    "controller-status.json", "simulator.log", "runner.log"))


def cleanup_targets(state):
    from .guest_access import ACCESS_FILES
    roles = [role for role in OVERLAYS if role in state["vehicles"]]
    targets = {role: OVERLAYS[role] for role in roles}
    for relative in state.get("runtimeCleanup", {}).get("files", []):
        targets["runtime:" + relative] = relative
    for role in roles:
        if state["vehicles"][role].get("runtime", {}).get("accessCreated"):
            for name in ACCESS_FILES:
                targets[role + ".access." + name] = ".run/demo-current/" + role + "-access/" + name
    targets.update(factory=state["factory"]["path"], manifest=MANIFEST)
    return targets


class EnvironmentError(ValueError):
    pass


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def sync_directory(path):
    fd = os.open(str(path), os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def atomic_json(path, document):
    # A same-directory unfinished write is recovery material, not a backup.
    temporary = path.with_name(path.name + ".pending")
    fd = os.open(str(temporary), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(encoded(document))
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(str(temporary), str(path))
    sync_directory(path.parent)


class EnvironmentService:
    def __init__(self, root=None, catalog=None, qemu_img=None):
        self.root = (Path(root) if root else project_root()).resolve()
        self.catalog = catalog or ImageCatalog()
        self.qemu_img = qemu_img or shutil.which("qemu-img")
        self._writer_thread = threading.local()

    def _directory(self, relative):
        current = self.root
        for part in Path(relative).parts:
            current = current / part
            if not current.exists() and not current.is_symlink():
                current.mkdir(mode=0o700)
            info = current.lstat()
            if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o022:
                raise EnvironmentError("LOCAL_DIRECTORY_NOT_OWNED")
        if relative == ".run/demo-current" and stat.S_IMODE(current.stat().st_mode) != 0o700:
            raise EnvironmentError("JOURNAL_DIRECTORY_MODE_INVALID")
        return current

    @contextmanager
    def _writer(self):
        # Composite operations use the same service and retain the outer flock.
        # Other threads/processes still fail closed at the original lock.
        if getattr(self._writer_thread, "held", False):
            yield
            return
        directory = self._directory(".run/demo-current")
        fd = os.open(str(directory / "writer.lock"), os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_uid != os.getuid():
                raise EnvironmentError("JOURNAL_LOCK_INVALID")
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise EnvironmentError("CURRENT_RUN_BUSY") from None
            self._writer_thread.held = True
            try:
                yield
            finally:
                self._writer_thread.held = False
        finally:
            os.close(fd)

    def _command(self, arguments):
        try:
            result = subprocess.run([self.qemu_img] + arguments, capture_output=True,
                                    timeout=30, check=False)
        except (OSError, subprocess.TimeoutExpired):
            raise EnvironmentError("QEMU_IMG_UNAVAILABLE_OR_TIMEOUT") from None
        if result.returncode:
            raise EnvironmentError("QEMU_IMG_FAILED")
        return result.stdout

    def _info(self, path):
        try:
            info = json.loads(self._command(["info", "--output=json", str(path)]))
        except (ValueError, TypeError):
            raise EnvironmentError("IMAGE_INFO_UNAVAILABLE") from None
        if not isinstance(info, dict):
            raise EnvironmentError("IMAGE_INFO_INVALID")
        return info

    def _standalone(self, path, expected_format):
        info = self._info(path)
        specific = info.get("format-specific", {}).get("data", {})
        if (info.get("format") != expected_format or info.get("backing-filename")
                or info.get("snapshots") or info.get("encrypted") or specific.get("data-file")
                or type(info.get("virtual-size")) is not int or info["virtual-size"] <= 0):
            raise EnvironmentError("IMAGE_NOT_STANDALONE_FACTORY")
        return info["virtual-size"]

    def _regular_readonly(self, path, size):
        info = path.lstat()
        if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_mode & 0o222
                or info.st_size != size or path.resolve() != path):
            raise EnvironmentError("FACTORY_FILE_INVALID")
        return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)

    def _copy_factory(self, image, journal):
        destination = self.root / FACTORY[image.image_format]
        manifest = self.root / MANIFEST
        self._directory(".local/factory")
        original_identity = self._regular_readonly(image.path, image.size)
        virtual_size = self._standalone(image.path, image.image_format)
        alternate = self.root / FACTORY["qcow2" if image.image_format == "raw" else "raw"]
        if alternate.exists() or alternate.is_symlink():
            raise EnvironmentError("DIFFERENT_LOCAL_FACTORY_PRESENT")
        metadata = {"schemaVersion": 1, "kind": "democtl.factory-copy",
                    "runtimeProfile": "aos-main-qemuarm64-v1" if image.architecture == "main-qemuarm64" else None,
                    "image": {"path": FACTORY[image.image_format], "format": image.image_format,
                              "version": image.version, "sha256": image.sha256,
                              "sizeBytes": image.size, "virtualSizeBytes": virtual_size},
                    "sourceSelector": image.selector,
                    "qualification": "INHERITED_FROM_SOURCE_NOT_PROMOTED_BY_COPY"}
        if destination.exists() or destination.is_symlink() or manifest.exists() or manifest.is_symlink():
            self._regular_readonly(destination, image.size)
            if read_json(manifest) != metadata or digest(destination) != image.sha256:
                raise EnvironmentError("LOCAL_FACTORY_CONFLICT")
            self._standalone(destination, image.image_format)
        else:
            temporary = destination.with_name(destination.name + ".pending")
            fd = os.open(str(temporary), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            copied = hashlib.sha256()
            with image.path.open("rb") as source, os.fdopen(fd, "wb") as output:
                for chunk in iter(lambda: source.read(4 * 1024 * 1024), b""):
                    output.write(chunk)
                    copied.update(chunk)
                output.flush()
                os.fsync(output.fileno())
                os.fchmod(output.fileno(), 0o444)
            if (copied.hexdigest() != image.sha256 or
                    self._regular_readonly(image.path, image.size) != original_identity):
                raise EnvironmentError("SOURCE_DIGEST_OR_IDENTITY_CHANGED")
            self._regular_readonly(temporary, image.size)
            os.rename(str(temporary), str(destination))
            sync_directory(destination.parent)
            atomic_json(manifest, metadata)
        journal["factory"] = {"path": FACTORY[image.image_format], "format": image.image_format,
                              "version": image.version, "sha256": image.sha256,
                              "manifestPath": MANIFEST, "manifestSha256": digest(manifest)}
        atomic_json(self.root / JOURNAL, journal)
        return destination, virtual_size

    def create(self, target, selector=None, image_path=None):
        if target not in ("test", "production", "all"):
            raise EnvironmentError("INVALID_TARGET")
        if not self.qemu_img:
            raise EnvironmentError("QEMU_IMG_NOT_INSTALLED")
        image = self.catalog.resolve(selector, image_path)
        # Reject known capacity failures before recording a new current run.
        # This is the repository's existing image-work guard, not a Builder run.
        if (not (self.root / FACTORY[image.image_format]).exists()
                and shutil.disk_usage(self.root).free < max(60 * 1024**3, image.size)):
            raise EnvironmentError("FACTORY_COPY_REQUIRES_60_GIB_FREE")
        roles = tuple(OVERLAYS) if target == "all" else (target,)
        with self._writer():
            # Any retained current state, including a failed atomic write, blocks
            # a new manufacture. Never truncate or remove it automatically.
            directory = self.root / ".run/demo-current"
            if any(p.name != "writer.lock" for p in directory.iterdir()):
                raise EnvironmentError("CURRENT_RUN_EXISTS_RECOVERY_OR_RETIREMENT_REQUIRED")
            overlay_root = self.root / ".local/demo-current"
            if overlay_root.exists() and (overlay_root.is_symlink() or any(overlay_root.iterdir())):
                raise EnvironmentError("CURRENT_OVERLAYS_EXIST")
            self._directory(".local/demo-current")
            operation = {"id": str(uuid4()), "team": "DEMO_SOLUTION", "class": "LOCAL_CREATE",
                         "authority": "LOCAL_OPERATOR", "target": list(roles),
                         "requestFingerprint": hashlib.sha256(encoded([image.sha256, target])).hexdigest(),
                         "resourceKeys": ["CANDIDATE_DIGEST:" + image.sha256], "knownExternalIds": {},
                         "state": "SUBMITTING", "reconciliation": "UNOBSERVABLE", "lastRead": None}
            journal = {"schemaVersion": 1, "kind": "democtl.current-run", "startedAt": now(),
                       "stage": "CREATING", "scope": "DUAL_ROLE" if target == "all" else "SINGLE_ROLE_ENGINEERING",
                       "factory": None, "currentVehicle": None, "vehicles": {}, "operations": [operation]}
            for role in roles:
                identity = uuid4()
                journal["vehicles"][role] = {
                    "overlay": OVERLAYS[role], "localVmId": str(identity),
                    "mac": "02:" + ":".join("%02x" % b for b in identity.bytes[:5]),
                    "sshPort": 10022 if role == "test" else 10023,
                    "state": "PLANNED", "unitId": None, "nodeId": None, "unitSetId": None}
            atomic_json(self.root / JOURNAL, journal)
            try:
                backing, virtual_size = self._copy_factory(image, journal)
                for role in roles:
                    overlay = self.root / OVERLAYS[role]
                    # Reserve exactly this new target before qemu-img touches it.
                    fd = os.open(str(overlay), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                    os.close(fd)
                    self._command(["create", "-f", "qcow2", "-F", image.image_format,
                                   "-b", str(backing), str(overlay)])
                    info = self._info(overlay)
                    if (info.get("format") != "qcow2" or info.get("backing-filename") != str(backing)
                            or info.get("backing-filename-format") != image.image_format
                            or info.get("virtual-size") != virtual_size):
                        raise EnvironmentError("OVERLAY_BACKING_MISMATCH")
                    if stat.S_IMODE(overlay.stat().st_mode) != 0o600:
                        raise EnvironmentError("OVERLAY_MODE_INVALID")
                    journal["vehicles"][role]["state"] = "MANUFACTURED"
                    atomic_json(self.root / JOURNAL, journal)
                journal["stage"] = "MANUFACTURED"
                operation.update(state="COMPLETED", reconciliation="APPLIED",
                                 lastRead={"source": "LOCAL_QEMU_IMG", "readCompletedAt": now(),
                                           "roles": list(roles), "backingVerified": True})
                atomic_json(self.root / JOURNAL, journal)
                return journal
            except (OSError, ValueError) as error:
                journal["stage"] = "RECOVERY_REQUIRED"
                operation.update(state="UNCERTAIN", reconciliation="UNOBSERVABLE")
                reason = str(error) if isinstance(error, EnvironmentError) else "LOCAL_CREATE_IO_ERROR"
                operation["lastRead"] = {"reason": reason, "readCompletedAt": now()}
                # Preserve a pending atomic write if that was the failing step.
                if not (self.root / (JOURNAL + ".pending")).exists():
                    atomic_json(self.root / JOURNAL, journal)
                raise EnvironmentError(reason) from None

    def _owned_file(self, path):
        info = path.lstat()
        if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1
                or info.st_uid != os.getuid() or path.resolve() != path):
            raise EnvironmentError("CLEANUP_FILE_NOT_OWNED")
        return [info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns]

    def _assert_unheld(self, path):
        executable = shutil.which("lsof")
        if not executable:
            raise EnvironmentError("OPEN_HANDLE_CHECK_UNAVAILABLE")
        try:
            result = subprocess.run([executable, "-F", "p", "--", str(path)],
                                    capture_output=True, timeout=8, check=False)
        except (OSError, subprocess.TimeoutExpired):
            raise EnvironmentError("OPEN_HANDLE_CHECK_UNAVAILABLE") from None
        # lsof returns 1 with empty output for a successfully observed empty set.
        # Warnings, denied visibility and all positive results fail closed.
        if result.stderr or result.returncode not in (0, 1):
            raise EnvironmentError("OPEN_HANDLE_CHECK_UNAVAILABLE")
        if result.stdout or result.returncode == 0:
            raise EnvironmentError("CLEANUP_FILE_IN_USE")

    def _untouched_overlay(self, path, factory, virtual_size, runtime=None, cloud_retired=False):
        identity = self._owned_file(path)
        self._assert_unheld(path)
        info = self._info(path)
        if (info.get("format") != "qcow2" or info.get("snapshots")
                or info.get("backing-filename") != str(self.root / factory["path"])
                or info.get("backing-filename-format") != factory["format"]
                or info.get("virtual-size") != virtual_size):
            raise EnvironmentError("CLEANUP_OVERLAY_BINDING_MISMATCH")
        if cloud_retired:
            if not runtime or runtime.get("state") != "STOPPED" or runtime.get("pid") is not None:
                raise EnvironmentError("VM_MUST_BE_STOPPED_BEFORE_RETIRE")
            return identity
        if runtime and runtime.get("everStarted"):
            proof = runtime.get("stopProof") or {}
            if (runtime.get("state") != "STOPPED" or proof.get("unprovisioned") is not True
                    or digest(path) != proof.get("overlaySha256")):
                raise EnvironmentError("STOPPED_UNPROVISIONED_PROOF_REQUIRED")
            if self._owned_file(path) != identity:
                raise EnvironmentError("CLEANUP_TARGET_CHANGED")
            return identity
        # A stale MANUFACTURED journal alone is insufficient: a VM might have
        # been booted/provisioned outside democtl. Require no guest-owned extents.
        extents = json.loads(self._command(["map", "--output=json", str(path)]))
        offset = 0
        if not isinstance(extents, list) or not extents:
            raise EnvironmentError("OVERLAY_CONTENT_STATE_UNKNOWN")
        for extent in extents:
            if (not isinstance(extent, dict) or extent.get("start") != offset
                    or type(extent.get("length")) is not int or extent["length"] <= 0
                    or type(extent.get("depth")) is not int or extent["depth"] < 1):
                raise EnvironmentError("OVERLAY_MODIFIED_FULL_RETIREMENT_REQUIRED")
            offset += extent["length"]
        if offset != virtual_size or self._owned_file(path) != identity:
            raise EnvironmentError("OVERLAY_CONTENT_STATE_UNKNOWN")
        return identity

    def _local_retirement_state(self, state):
        if (not isinstance(state, dict) or type(state.get("schemaVersion")) is not int
                or state["schemaVersion"] != 1 or state.get("kind") != "democtl.current-run"
                or set(state) - {"schemaVersion", "kind", "startedAt", "stage", "scope", "factory",
                                 "currentVehicle", "vehicles", "operations", "retirement", "shared", "cloudBinding",
                                 "source", "componentOperations", "componentSchema", "smDemoProof", "runtimeCleanup", "demoPreparation"}
                or state.get("stage") not in ("MANUFACTURED", "LOCAL_STOPPED", "RETIRING_LOCAL")
                or state.get("currentVehicle") is not None):
            raise EnvironmentError("LOCAL_RETIRE_REQUIRES_UNUSED_MANUFACTURED_ENVIRONMENT")
        vehicles = state.get("vehicles")
        factory_only = state.get("scope") == "FACTORY_COPY_ONLY"
        if (not isinstance(vehicles, dict) or set(vehicles) - set(OVERLAYS)
                or (not vehicles and not factory_only) or (vehicles and factory_only)):
            raise EnvironmentError("CLEANUP_JOURNAL_INVALID")
        for role, item in vehicles.items():
            if (not isinstance(item, dict) or set(item) - {"runtime", "cloud", "systemUid"} != {
                    "overlay", "localVmId", "mac", "sshPort", "state", "unitId", "nodeId", "unitSetId"}
                    or item["overlay"] != OVERLAYS[role] or item["state"] != "MANUFACTURED"):
                raise EnvironmentError("LOCAL_RETIRE_REQUIRES_UNUSED_MANUFACTURED_ENVIRONMENT")
            cloud = item.get("cloud")
            if cloud is not None:
                if (not isinstance(cloud, dict) or cloud.get("lifecycle") != "DELETED"
                        or cloud.get("absenceConfirmed") is not True
                        or not item.get("systemUid") or not item.get("runtime")
                        or item["runtime"].get("pid") is not None):
                    raise EnvironmentError("CLOUD_RETIREMENT_PROOF_REQUIRED")
                for key in ("unitId", "nodeId", "unitSetId"):
                    if not item.get(key):
                        raise EnvironmentError("CLOUD_RETIREMENT_IDENTITY_REQUIRED")
                    object_id(item[key])
            elif any(item.get(key) is not None for key in ("unitId", "nodeId", "unitSetId", "systemUid")):
                raise EnvironmentError("LOCAL_RETIRE_REQUIRES_UNUSED_MANUFACTURED_ENVIRONMENT")
            object_id(item["localVmId"])
            if "runtime" in item and (not isinstance(item["runtime"], dict)
                    or item["runtime"].get("state") != "STOPPED"):
                raise EnvironmentError("VM_MUST_BE_STOPPED_BEFORE_RETIRE")
        dns = state.get("shared", {}).get("dns")
        if dns and dns.get("ownership") == "EXTERNAL_DEPENDENCY":
            # Retiring a stopped borrower neither owns nor stops the shared bridge.
            if (state.get("scope") != "SINGLE_ROLE_ENGINEERING" or set(vehicles) != {"test"}
                    or not Path(dns.get("ownerRoot", "")).is_absolute()
                    or Path(dns["ownerRoot"]).resolve() == self.root):
                raise EnvironmentError("DNS_DEPENDENCY_BINDING_INVALID")
            object_id(dns.get("ownerId"))
        elif dns and (dns.get("state") != "STOPPED" or dns.get("pid") is not None):
            raise EnvironmentError("DNS_MUST_BE_STOPPED_BEFORE_RETIRE")
        operations = state.get("operations")
        if not isinstance(operations, list) or not 1 <= len(operations) <= 2:
            raise EnvironmentError("CLEANUP_JOURNAL_INVALID")
        create = operations[0]
        if not factory_only and (not isinstance(create, dict) or create.get("class") != "LOCAL_CREATE"
                or create.get("state") != "COMPLETED" or create.get("knownExternalIds") != {}
                or create.get("reconciliation") != "APPLIED"):
            raise EnvironmentError("CLEANUP_PRIOR_OPERATION_UNRESOLVED")
        resuming = state["stage"] == "RETIRING_LOCAL"
        if not resuming and (len(operations) != 1 or "retirement" in state):
            raise EnvironmentError("CLEANUP_JOURNAL_INVALID")
        if resuming:
            if (len(operations) != (1 if factory_only else 2) or not isinstance(operations[-1], dict)
                    or operations[-1].get("class") != "LOCAL_RETIRE"
                    or operations[-1].get("knownExternalIds") != {}
                    or operations[-1].get("state") != "SUBMITTING"
                    or not isinstance(state.get("retirement"), dict)
                    or set(state["retirement"]) != set(cleanup_targets(state))):
                raise EnvironmentError("CLEANUP_JOURNAL_INVALID")
            for item in state["retirement"].values():
                if (not isinstance(item, dict) or set(item) != {"identity", "state"}
                        or item["state"] not in ("READY", "REMOVE_PENDING", "REMOVED")
                        or not isinstance(item["identity"], list) or len(item["identity"]) != 4
                        or any(type(n) is not int for n in item["identity"])):
                    raise EnvironmentError("CLEANUP_JOURNAL_INVALID")
        return resuming

    def _runtime_cleanup(self, state):
        """Plan only fixed Demo Control source outputs; never recursive deletion."""
        source = state.get("source")
        base = ".run/demo-current/source"
        control = ".run/demo-current/control"
        if source:
            run_id = object_id(source.get("runId"))
            if (source.get("state") != "STOPPED" or source.get("operation") or source.get("stopOperation")
                    or source.get("runDirectory") != base + "/" + run_id
                    or source.get("controlDirectory") != control):
                raise EnvironmentError("SIMULATION_MUST_BE_STOPPED_BEFORE_RETIRE")
            from .source import SourceDriver
            from .vm import VMService
            driver = SourceDriver(VMService(self))
            if any(driver.live_process(source[key]) for key in ("runnerCommand", "simulatorCommand")):
                raise EnvironmentError("SIMULATION_MUST_BE_STOPPED_BEFORE_RETIRE")
            if any(str(self.root / base) in args or str(self.root / control) in args
                   for _, args in driver.vm._processes()):
                raise EnvironmentError("SOURCE_RUNTIME_STILL_IN_USE")
        elif any((self.root / p).exists() or (self.root / p).is_symlink() for p in (base, control)):
            raise EnvironmentError("SOURCE_RUNTIME_OWNERSHIP_MISSING")
        for record in state.get("componentOperations", {}).values():
            for action in ("upload", "approve", "unapprove", "send"):
                attempt = record.get(action)
                if isinstance(attempt, dict) and attempt.get("attemptStarted") and attempt.get("state") != "CONFIRMED":
                    # A Unit-scoped send cannot survive authoritative deletion
                    # of that exact target. This is not proof of delivery; the
                    # fresh cloud_check is still mandatory before unlink.
                    if action == "send" and any(attempt.get("unitId") == item.get("unitId")
                            and item.get("cloud", {}).get("lifecycle") == "DELETED"
                            and item.get("cloud", {}).get("absenceConfirmed") is True
                            for item in state["vehicles"].values()):
                        continue
                    raise EnvironmentError("COMPONENT_OPERATION_RECONCILIATION_REQUIRED")
        plan = state.get("runtimeCleanup")
        if plan is None:
            plan = {"files": [], "directories": []}
            root = self.root / base
            if root.exists() or root.is_symlink():
                self._directory(base)
                for run in sorted(root.iterdir()):
                    object_id(run.name)
                    relative = base + "/" + run.name
                    self._directory(relative)
                    manifest = run / "manifest.json"
                    self._owned_file(manifest)
                    receipt = read_json(manifest)
                    if receipt.get("run_id") != run.name or receipt.get("status") not in ("completed", "failed"):
                        raise EnvironmentError("SOURCE_RUNTIME_RECEIPT_INVALID")
                    for path in sorted(run.iterdir()):
                        if path.name not in SOURCE_RUNTIME_FILES:
                            raise EnvironmentError("UNTRACKED_SOURCE_RUNTIME_FILE")
                        plan["files"].append(relative + "/" + path.name)
                    plan["directories"].append(relative)
                plan["directories"].append(base)
            if (self.root / control).exists() or (self.root / control).is_symlink():
                self._directory(control)
                if any((self.root / control).iterdir()):
                    raise EnvironmentError("SOURCE_CONTROL_CLEANUP_INCOMPLETE")
                plan["directories"].append(control)
        if (not isinstance(plan, dict) or set(plan) != {"files", "directories"}
                or any(not isinstance(plan[k], list) or len(plan[k]) != len(set(plan[k])) for k in plan)):
            raise EnvironmentError("RUNTIME_CLEANUP_PLAN_INVALID")
        for relative in plan["directories"]:
            parts = Path(relative).parts
            if relative not in (base, control):
                if len(parts) != 4 or parts[:3] != Path(base).parts:
                    raise EnvironmentError("RUNTIME_CLEANUP_PLAN_INVALID")
                object_id(parts[3])
            path = self.root / relative
            if path.exists() or path.is_symlink():
                self._directory(relative)
                allowed = set(plan["directories"]) | set(plan["files"])
                if any(str(p.relative_to(self.root)) not in allowed for p in path.iterdir()):
                    raise EnvironmentError("UNTRACKED_SOURCE_RUNTIME_FILE")
        for relative in plan["files"]:
            parts = Path(relative).parts
            if (len(parts) != 5 or parts[:3] != Path(base).parts or parts[4] not in SOURCE_RUNTIME_FILES
                    or str(Path(relative).parent) not in plan["directories"]):
                raise EnvironmentError("RUNTIME_CLEANUP_PLAN_INVALID")
            object_id(parts[3])
        return plan

    def _unlink_owned(self, path, identity):
        # Reconcile this exact inode and its users immediately before deletion.
        if self._owned_file(path) != identity:
            raise EnvironmentError("CLEANUP_TARGET_CHANGED")
        self._assert_unheld(path)
        if self._owned_file(path) != identity:
            raise EnvironmentError("CLEANUP_TARGET_CHANGED")
        path.unlink()
        sync_directory(path.parent)

    def retire(self, cloud_check=None):
        """Dispose unused or authoritatively Cloud-retired CLI output; not scenario R0."""
        with self._writer():
            run_root = self.root / ".run/demo-current"
            if any(p.name not in ("writer.lock", "journal.json", "test-access", "production-access", "source", "control") for p in run_root.iterdir()):
                raise EnvironmentError("CURRENT_RUN_RECOVERY_REQUIRED")
            overlay_root = self.root / ".local/demo-current"
            if overlay_root.exists() or overlay_root.is_symlink():
                self._directory(".local/demo-current")
            journal_path = self.root / JOURNAL
            factory_root = self.root / ".local/factory"
            if not journal_path.exists() and not journal_path.is_symlink():
                if any((run_root / name).exists() or (run_root / name).is_symlink() for name in ("source", "control")):
                    raise EnvironmentError("SOURCE_RUNTIME_OWNERSHIP_MISSING")
                if any((run_root / (role + "-access")).exists() for role in OVERLAYS):
                    raise EnvironmentError("ORPHAN_ACCESS_MATERIAL_REQUIRES_RECONCILIATION")
                if overlay_root.exists() and any(overlay_root.iterdir()):
                    raise EnvironmentError("ORPHAN_OVERLAYS_REQUIRE_RECONCILIATION")
                if not factory_root.exists() and not factory_root.is_symlink():
                    return {"scope": "UNUSED_LOCAL_CREATE", "removed": [],
                            "outcome": "NO_CURRENT_ENVIRONMENT", "cloudActions": False}
                self._directory(".local/factory")
                if not any(factory_root.iterdir()):
                    return {"scope": "UNUSED_LOCAL_CREATE", "removed": [],
                            "outcome": "NO_CURRENT_ENVIRONMENT", "cloudActions": False}
                # Compatibility with the former retire, which kept this copy
                # but removed its run journal. Require the exact producer binding.
                manifest_path = self.root / MANIFEST
                self._owned_file(manifest_path)
                retained = read_json(manifest_path)
                if retained.get("kind") != "democtl.factory-copy" or retained.get("schemaVersion") != 1:
                    raise EnvironmentError("UNOWNED_FACTORY_COPY")
                source = self.catalog.resolve(selector=retained["sourceSelector"])
                image = retained["image"]
                if any(image[key] != expected for key, expected in {
                    "path": FACTORY[source.image_format], "format": source.image_format,
                    "version": source.version, "sha256": source.sha256, "sizeBytes": source.size}.items()):
                    raise EnvironmentError("CLEANUP_FACTORY_BINDING_INVALID")
                state = {"schemaVersion": 1, "kind": "democtl.current-run", "startedAt": now(),
                         "scope": "FACTORY_COPY_ONLY", "stage": "MANUFACTURED", "vehicles": {},
                         "currentVehicle": None, "operations": [], "factory": {
                             **image, "manifestPath": MANIFEST, "manifestSha256": digest(manifest_path)}}
                resuming = False
            else:
                self._owned_file(journal_path)
                state = read_json(journal_path)
                resuming = self._local_retirement_state(state)
            factory = state.get("factory")
            if (not isinstance(factory, dict) or factory.get("format") not in FACTORY
                    or factory.get("path") != FACTORY[factory["format"]]
                    or factory.get("manifestPath") != MANIFEST):
                raise EnvironmentError("CLEANUP_FACTORY_BINDING_INVALID")
            if factory_root.exists() or factory_root.is_symlink():
                self._directory(".local/factory")
                if any(p.name not in (Path(factory["path"]).name, Path(MANIFEST).name)
                       for p in factory_root.iterdir()):
                    raise EnvironmentError("UNTRACKED_FACTORY_FILES_PRESENT")
            manifest_path = self.root / MANIFEST
            if manifest_path.exists() or manifest_path.is_symlink():
                self._owned_file(manifest_path)
                if digest(manifest_path) != factory.get("manifestSha256"):
                    raise EnvironmentError("CLEANUP_FACTORY_MANIFEST_CHANGED")
                metadata = read_json(manifest_path)["image"]
                if any(metadata[key] != factory[key] for key in ("path", "format", "version", "sha256")):
                    raise EnvironmentError("CLEANUP_FACTORY_BINDING_INVALID")
                factory.update(sizeBytes=metadata["sizeBytes"], virtualSizeBytes=metadata["virtualSizeBytes"])
            roles = [role for role in OVERLAYS if role in state["vehicles"]]
            cloud_retired = any(state["vehicles"][role].get("cloud") for role in roles)
            if cloud_retired:
                if cloud_check is None:
                    raise EnvironmentError("FRESH_CLOUD_RETIREMENT_CHECK_REQUIRED")
                # Every invocation, including interrupted-unlink recovery, gets
                # new read-only Cloud proof under this same writer lock.
                if cloud_check(state) is not True:
                    raise EnvironmentError("FRESH_CLOUD_RETIREMENT_CHECK_FAILED")
            # The read-only Cloud gate also reconciles recorded upload responses
            # before unresolved global operations can block local disposal.
            state["runtimeCleanup"] = self._runtime_cleanup(state)
            targets = cleanup_targets(state)
            from .guest_access import ACCESS_FILES
            for role in OVERLAYS:
                access = run_root / (role + "-access")
                if access.exists() or access.is_symlink():
                    if (role not in roles or not state["vehicles"][role].get("runtime", {}).get("accessCreated")
                            or access.is_symlink() or not access.is_dir()
                            or any(p.name not in ACCESS_FILES for p in access.iterdir())):
                        raise EnvironmentError("UNTRACKED_ACCESS_MATERIAL_PRESENT")
            expected_names = {Path(OVERLAYS[role]).name for role in roles}
            if overlay_root.exists() and any(p.name not in expected_names for p in overlay_root.iterdir()):
                raise EnvironmentError("UNTRACKED_RUNTIME_FILES_PRESENT")
            identities = {}
            # Validate every remaining target before deleting the first one.
            for role, relative in targets.items():
                path = self.root / relative
                previous = state.get("retirement", {}).get(role, {})
                if not path.exists() and not path.is_symlink():
                    if not resuming or previous.get("state") not in ("REMOVE_PENDING", "REMOVED"):
                        raise EnvironmentError("CLEANUP_FILE_MISSING")
                    # The factory cannot already be gone while a child remains.
                    if role in ("factory", "manifest") and identities:
                        raise EnvironmentError("CLEANUP_ORDER_CONTRADICTORY")
                    continue
                if role in roles:
                    identity = self._untouched_overlay(path, factory, factory["virtualSizeBytes"],
                                                       state["vehicles"][role].get("runtime"),
                                                       bool(state["vehicles"][role].get("cloud")))
                else:
                    identity = self._owned_file(path)
                    if role == "factory":
                        self._regular_readonly(path, factory["sizeBytes"])
                    self._assert_unheld(path)
                if resuming and (previous["state"] == "REMOVED" or identity != previous["identity"]):
                    raise EnvironmentError("CLEANUP_TARGET_CHANGED")
                identities[role] = identity
            if not resuming:
                state["stage"] = "RETIRING_LOCAL"
                state["retirement"] = {role: {"identity": identities[role], "state": "READY"} for role in targets}
                state["operations"].append({"id": str(uuid4()), "team": "DEMO_SOLUTION",
                    "class": "LOCAL_RETIRE", "authority": "LOCAL_OPERATOR", "target": list(targets),
                    "requestFingerprint": hashlib.sha256(encoded(identities)).hexdigest(),
                    "resourceKeys": ["CANDIDATE_DIGEST:" + factory["sha256"]], "knownExternalIds": {},
                    "state": "SUBMITTING", "reconciliation": "UNOBSERVABLE", "lastRead": None})
                atomic_json(journal_path, state)
            for role, relative in targets.items():
                progress = state["retirement"][role]
                if role in identities:
                    if role == "factory" and overlay_root.exists() and any(overlay_root.iterdir()):
                        raise EnvironmentError("CHILD_OVERLAYS_STILL_PRESENT")
                    progress["state"] = "REMOVE_PENDING"
                    atomic_json(journal_path, state)
                    self._unlink_owned(self.root / relative, identities[role])
                progress["state"] = "REMOVED"
                atomic_json(journal_path, state)
            if overlay_root.exists():
                overlay_root.rmdir()  # Empty directory only, never recursive removal.
                sync_directory(overlay_root.parent)
            if factory_root.exists():
                factory_root.rmdir()
                sync_directory(factory_root.parent)
            for role in roles:
                access = run_root / (role + "-access")
                if access.exists():
                    access.rmdir()
            for relative in state["runtimeCleanup"]["directories"]:
                path = self.root / relative
                if path.exists():
                    path.rmdir()  # Empty, validated exact directory only.
            journal_path.unlink()  # Last recovery record; all exact targets are absent.
            sync_directory(run_root)
            # Keep the lock inode stable for waiting/current/future writers.
            return {"scope": "CLOUD_RETIRED_CLI_RUN" if cloud_retired else "UNUSED_LOCAL_CREATE", "outcome": "REMOVED",
                    "removed": list(targets.values()) + state["runtimeCleanup"]["directories"] + [JOURNAL],
                    "preserved": ["demo-artifacts source image and published manifests"], "cloudActions": False,
                    "cloudReadsPerformed": cloud_retired, "recoverable": False}
