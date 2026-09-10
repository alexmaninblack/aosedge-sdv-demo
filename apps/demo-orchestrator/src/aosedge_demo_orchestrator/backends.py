# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Owned functional backend containers; no Cloud, VM or product-state claims."""

import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

from .environment import EnvironmentError, JOURNAL, atomic_json
from .status import read_json, now, object_id

TEAMS = ("brake", "tire")
DIGEST = re.compile(r"sha256:[0-9a-f]{64}")


class BackendService:
    def __init__(self, environment, progress=None):
        self.environment = environment
        self.root = environment.root
        self.catalog = environment.catalog.project / "backends"
        self.progress = progress or (lambda value: None)

    def _run(self, arguments, timeout=12, cwd=None):
        try:
            result = subprocess.run(arguments, cwd=cwd, text=True, capture_output=True, timeout=timeout)
        except (OSError, subprocess.TimeoutExpired):
            raise EnvironmentError("BACKEND_COMMAND_UNAVAILABLE_OR_UNCERTAIN") from None
        if result.returncode:
            # Docker/registry/tool output is not a public diagnostic envelope.
            error = result.stderr.lower()
            if any(marker in error for marker in ("cannot connect to the docker daemon",
                    "is the docker daemon running", "failed to connect to the docker api",
                    "dial unix", "error during connect")):
                raise EnvironmentError("BACKEND_DOCKER_ENGINE_UNAVAILABLE")
            if "no space left on device" in error:
                raise EnvironmentError("BACKEND_BUILD_STORAGE_EXHAUSTED")
            if "failed to resolve source metadata" in error or "failed to fetch" in error:
                raise EnvironmentError("BACKEND_PINNED_BUILD_INPUT_UNAVAILABLE")
            raise EnvironmentError("BACKEND_COMMAND_FAILED")
        if len(result.stdout) > 1048576:
            raise EnvironmentError("BACKEND_RESPONSE_TOO_LARGE")
        return result.stdout

    def _docker(self, *arguments, timeout=12):
        executable = shutil.which("docker")
        if executable is None:
            raise EnvironmentError("BACKEND_DOCKER_REQUIRED")
        return self._run([executable, *arguments], timeout)

    def _inspect(self, kind, name):
        # A list distinguishes absence from an unreachable engine. No error
        # string, empty socket response or read failure is treated as absence.
        if kind == "container":
            listed = self._docker("container", "ls", "--all", "--filter", "name=^/" + name + "$", "--format", "{{.ID}}")
        elif kind in ("volume", "network"):
            listed = self._docker(kind, "ls", "--filter", "name=" + name, "--format", "{{.Name}}")
            listed = "\n".join(item for item in listed.splitlines() if item == name)
        else:
            raise EnvironmentError("BACKEND_INSPECTION_KIND_INVALID")
        matches = listed.split()
        if not matches:
            return None
        if len(matches) != 1:
            raise EnvironmentError("BACKEND_RESOURCE_AMBIGUOUS")
        value = json.loads(self._docker(kind, "inspect", matches[0]))
        if not isinstance(value, list) or len(value) != 1:
            raise EnvironmentError("BACKEND_RESOURCE_AMBIGUOUS")
        return value[0]

    def build(self, team):
        """Explicit development build. Never called by start/navigation."""
        if team not in TEAMS:
            raise EnvironmentError("BACKEND_TEAM_INVALID")
        with self.environment._writer():
            repository = self.root.parent / (team + "-health-cloud")
            if not (repository / "Dockerfile").is_file():
                raise EnvironmentError("BACKEND_DOCKERFILE_NOT_IMPLEMENTED:" + team)
            revision = self._run(["git", "rev-parse", "HEAD"], cwd=repository).strip()
            if not re.fullmatch(r"[0-9a-f]{40}", revision) or self._run(["git", "status", "--porcelain"], cwd=repository).strip():
                raise EnvironmentError("BACKEND_COMMITTED_SOURCE_REQUIRED")
            directory = self.catalog / team / revision
            if directory.is_symlink() or not directory.resolve().is_relative_to(self.catalog.resolve()):
                raise EnvironmentError("BACKEND_CATALOG_PATH_UNSAFE")
            manifest = directory / "manifest.json"
            if manifest.is_file():
                value = read_json(manifest)
                self._image(value["imageId"])
                return dict(value, noOp=True)
            tag = "democtl/" + team + "-backend:" + revision
            self.progress("Building " + team + " backend from committed source; runtime start will not build or pull")
            self._docker("build", "--platform", "linux/arm64", "--pull=false", "--label", "tech.aosedge.demo.team=" + team,
                "--label", "org.opencontainers.image.revision=" + revision, "--tag", tag, str(repository), timeout=600)
            image = json.loads(self._docker("image", "inspect", tag))[0]
            self._image(image["Id"])
            value = dict(schemaVersion=1, team=team, sourceRevision=revision, imageId=image["Id"],
                         builtAt=now(), qualification="BUILT_NOT_LIVE_QUALIFIED")
            directory.mkdir(parents=True, mode=0o700, exist_ok=True)
            atomic_json(manifest, value)
            return value

    def _image(self, identity):
        if not isinstance(identity, str) or not DIGEST.fullmatch(identity):
            raise EnvironmentError("BACKEND_IMMUTABLE_IMAGE_REQUIRED")
        values = json.loads(self._docker("image", "inspect", identity))
        if len(values) != 1 or values[0].get("Id") != identity or values[0].get("Architecture") != "arm64":
            raise EnvironmentError("BACKEND_ARM64_IMAGE_NOT_AVAILABLE")
        return values[0]

    def _context_handles(self):
        """Bounded diagnostic for the one owned context, not process arguments."""
        path = self.root / ".run/demo-current/backends/context/current-unit-context.json"
        if not path.exists():
            return dict(state="ABSENT", owners=[])
        self.environment._owned_file(path)
        executable = shutil.which("lsof")
        if not executable:
            return dict(state="UNKNOWN", owners=[])
        try:
            result = subprocess.run([executable, "-F", "pc", "--", str(path)],
                capture_output=True, text=True, timeout=8, check=False)
        except (OSError, subprocess.TimeoutExpired):
            return dict(state="UNKNOWN", owners=[])
        if result.stderr or result.returncode not in (0, 1) or len(result.stdout) > 8192:
            return dict(state="UNKNOWN", owners=[])
        owners = []
        for line in result.stdout.splitlines():
            if re.fullmatch(r"p[0-9]{1,10}", line):
                owners.append(dict(pid=int(line[1:]), processClass="OTHER"))
            elif line.startswith("c") and owners:
                name = line[1:].lower()
                if "virtualization" in name or name in ("qemu-system-aarch64", "qemu-system-x86_64"):
                    owners[-1]["processClass"] = "VIRTUAL_MACHINE"
                elif "docker" in name:
                    owners[-1]["processClass"] = "DOCKER_DESKTOP"
        return dict(state="HELD" if owners else "CLEAR" if result.returncode == 1 and not result.stdout else "UNKNOWN", owners=owners)

    def _restore_fingerprint(self, container):
        return dict(id=container["Id"], image=container["Image"], mounts=[
            {key: mount.get(key) for key in ("Type", "Name", "Source", "Destination", "RW")}
            for mount in container.get("Mounts", [])])

    def _same_restore_binding(self, actual, expected):
        return (actual["id"] == expected["id"] and actual["image"] == expected["image"]
            and sorted(actual["mounts"], key=lambda mount: mount["Destination"]) ==
                sorted(expected["mounts"], key=lambda mount: mount["Destination"]))

    def _restore_project(self, state, recovery):
        restored = []
        for record in recovery.get("containers", []):
            observed = self._inspect("container", record["name"])
            if not observed or not self._same_restore_binding(self._restore_fingerprint(observed), record["binding"]):
                raise EnvironmentError("BACKEND_RECOVERY_CONTAINER_OR_DATA_BINDING_CHANGED")
            if not observed.get("State", {}).get("Running"):
                if record.get("restoreAttemptStarted"):
                    raise EnvironmentError("BACKEND_RECOVERY_CONTAINER_START_UNCONFIRMED")
                record["restoreAttemptStarted"] = True
                atomic_json(self.root / JOURNAL, state)
                self._docker("container", "start", record["binding"]["id"], timeout=25)
            deadline = time.monotonic() + 60
            while True:
                observed = self._inspect("container", record["name"])
                if not observed or not self._same_restore_binding(self._restore_fingerprint(observed), record["binding"]):
                    raise EnvironmentError("BACKEND_RECOVERY_CONTAINER_OR_DATA_BINDING_CHANGED")
                runtime = observed.get("State", {})
                healthy = (runtime.get("Health") or {}).get("Status")
                if runtime.get("Running") and (not record["wasHealthy"] or healthy == "healthy"):
                    break
                if time.monotonic() >= deadline or healthy == "unhealthy":
                    raise EnvironmentError("BACKEND_RECOVERY_CONTAINER_READINESS_UNCONFIRMED")
                time.sleep(2)
            record["restored"] = True
            atomic_json(self.root / JOURNAL, state)
            restored.append(record["name"])
            self.progress("Restored existing container " + record["name"] + "; image and data mounts unchanged")
        return restored

    def recover_file_sharing(self, restart_project=None):
        """Explicit local recovery, never automatic in ordinary demo actions."""
        with self.environment._writer():
            state = read_json(self.root / JOURNAL)
            lifecycle = state.get("demoLifecycle") or {}
            if restart_project not in (None, "watt-the-app"):
                raise EnvironmentError("BACKEND_RECOVERY_PROJECT_NOT_AUTHORIZED")
            if (sys.platform != "darwin" or lifecycle.get("action") != "retire"
                    or lifecycle.get("state") != "PARTIAL" or lifecycle.get("reason") != "CLEANUP_FILE_IN_USE"
                    or lifecycle.get("phase") != "retire-test-data-and-overlay"):
                raise EnvironmentError("BACKEND_FILE_SHARING_RECOVERY_NOT_APPLICABLE")
            for team in TEAMS:
                record = state.get("backends", {}).get(team, {})
                if (record.get("state") != "STOPPED" or record.get("cleanup", {}).get("containerRemoval") != "REMOVED"
                        or self._inspect("container", "aosedge-demo-" + team + "-cloud") is not None):
                    raise EnvironmentError("BACKEND_FILE_SHARING_CONTAINERS_NOT_RELEASED")
            recovery = lifecycle.get("fileSharingRecovery") or {}
            if recovery.get("attemptStarted"):
                # Reconcile an interrupted restore; never replay the restart.
                if recovery.get("project") != restart_project:
                    raise EnvironmentError("BACKEND_RECOVERY_PROJECT_BINDING_CHANGED")
                self._docker("info", "--format", "{{.ServerVersion}}")
                restored = self._restore_project(state, recovery)
                observation = self._context_handles()
                recovery.update(state="COMPLETED" if observation["state"] == "CLEAR" else "PARTIAL", checkedAt=now())
                atomic_json(self.root / JOURNAL, state)
                return dict(state=recovery["state"], noOp=True, dataPreserved=True,
                    restoredContainers=restored, contextOpenHandles=observation)
            handles = self._context_handles()
            if handles["state"] == "CLEAR":
                return dict(state="COMPLETED", noOp=True, dataPreserved=True)
            if handles["state"] != "HELD" or any(owner["processClass"] != "VIRTUAL_MACHINE" for owner in handles["owners"]):
                raise EnvironmentError("BACKEND_FILE_SHARING_HOLDER_NOT_RECOGNIZED")
            disk = Path.home() / "Library/Containers/com.docker.docker/Data/vms/0/data/Docker.raw"
            lsof = shutil.which("lsof")
            if not disk.is_file():
                raise EnvironmentError("BACKEND_FILE_SHARING_DOCKER_DISK_NOT_FOUND")
            if not lsof:
                raise EnvironmentError("BACKEND_FILE_SHARING_LSOF_UNAVAILABLE")
            for holder in handles["owners"]:
                evidence = self._run([lsof, "-a", "-p", str(holder["pid"]), "-F", "p", "--", str(disk)])
                if {line for line in evidence.splitlines() if re.fullmatch(r"p[0-9]+", line)} != {"p" + str(holder["pid"])}:
                    raise EnvironmentError("BACKEND_FILE_SHARING_DOCKER_VM_UNPROVEN")
            running = self._docker("container", "ls", "--quiet").split()
            containers = []
            if running:
                if restart_project != "watt-the-app":
                    raise EnvironmentError("BACKEND_FILE_SHARING_OTHER_CONTAINER_RUNNING")
                for service in ("db", "redis", "api", "admin", "tunnel"):
                    name = "watt-the-app-" + service + "-1"
                    value = self._inspect("container", name)
                    labels = (value or {}).get("Config", {}).get("Labels") or {}
                    if (not value or not value.get("State", {}).get("Running")
                            or labels.get("com.docker.compose.project") != "watt-the-app"
                            or labels.get("com.docker.compose.service") != service):
                        raise EnvironmentError("BACKEND_RECOVERY_WATT_SCOPE_CHANGED")
                    containers.append(dict(name=name, binding=self._restore_fingerprint(value),
                        wasHealthy=(value.get("State", {}).get("Health") or {}).get("Status") == "healthy"))
                if len(running) != 5 or any(len(item) < 12 or sum(record["binding"]["id"].startswith(item)
                        for record in containers) != 1 for item in running):
                    raise EnvironmentError("BACKEND_FILE_SHARING_OTHER_CONTAINER_RUNNING")
            processes = self._run(["/bin/ps", "-axo", "comm="])
            if any(Path(line.strip()).name in ("docker-buildx", "buildctl") for line in processes.splitlines()):
                raise EnvironmentError("BACKEND_FILE_SHARING_BUILD_RUNNING")
            recovery = dict(attemptStarted=True, startedAt=now(), state="UNCERTAIN",
                project=restart_project, containers=containers)
            lifecycle["fileSharingRecovery"] = recovery
            atomic_json(self.root / JOURNAL, state)
            self.progress("Restarting Docker Desktop once; restoring the recorded containers without changing images or data")
            self._docker("desktop", "restart", "--timeout", "120", timeout=125)
            self._docker("info", "--format", "{{.ServerVersion}}")
            restored = self._restore_project(state, recovery)
            observation = self._context_handles()
            lifecycle["fileSharingRecovery"].update(state="COMPLETED" if observation["state"] == "CLEAR" else "PARTIAL", checkedAt=now())
            atomic_json(self.root / JOURNAL, state)
            return dict(state=lifecycle["fileSharingRecovery"]["state"], noOp=False, dataPreserved=True,
                restoredContainers=restored, contextOpenHandles=observation)

    def _candidate(self, team):
        values = []
        for path in (self.catalog / team).glob("*/manifest.json"):
            if path.is_symlink() or not path.resolve().is_relative_to(self.catalog.resolve()):
                raise EnvironmentError("BACKEND_CATALOG_PATH_UNSAFE")
            value = read_json(path)
            if value.get("schemaVersion") == 1 and value.get("team") == team and DIGEST.fullmatch(value.get("imageId", "")):
                values.append(value)
        if not values:
            raise EnvironmentError("BACKEND_BUILD_REQUIRED:" + team)
        return max(values, key=lambda value: value["builtAt"])

    def observe_stack(self):
        """Focused process read; no storage forensics, image checks or mutation."""
        state = read_json(self.root / JOURNAL)
        owner = object_id(state["operations"][0]["id"])
        results = {}
        for team in TEAMS:
            try:
                container = self._inspect("container", "aosedge-demo-" + team + "-cloud")
                self._owned_container(container, owner, team, (state.get("backends", {}).get(team) or {}).get("imageId"))
                runtime = (container or {}).get("State", {})
                health = (runtime.get("Health") or {}).get("Status", "NOT_OBSERVED")
                results[team] = dict(state="RUNNING" if runtime.get("Running") else "STOPPED", processHealth=health)
            except EnvironmentError as error:
                results[team] = dict(state="UNKNOWN", reason=str(error))
        return dict(state="CURRENT" if all(item["state"] == "RUNNING" and item.get("processHealth") == "healthy"
            for item in results.values()) else "UNKNOWN", teams=results, readCompletedAt=now(),
            productReadiness="NOT_OBSERVED", source="DOCKER_PROCESS_ONLY")

    def start_stack(self):
        """Compose existing team operations; undo only this start attempt."""
        with self.environment._writer():
            before = {team: self.execute("status", team) for team in TEAMS}
            state = read_json(self.root / JOURNAL)
            # Both immutable candidates must exist before starting the first team.
            for team in TEAMS:
                self._image(self._runtime_candidate(state, team)["imageId"])
            attempted = []
            results = {}
            try:
                for team in TEAMS:
                    if before[team]["state"] == "STOPPED":
                        attempted.append(team)
                    results[team] = self.execute("start", team)
                    if results[team]["state"] != "RUNNING":
                        raise EnvironmentError("BACKEND_STACK_NOT_READY:" + team)
            except EnvironmentError as error:
                cleanup = {}
                for team in reversed(attempted):
                    try:
                        cleanup[team] = self.execute("stop", team)
                    except EnvironmentError as stop_error:
                        cleanup[team] = dict(state="UNKNOWN", reason=str(stop_error))
                return dict(state="PARTIAL", reason=str(error), teams=results,
                    partialStartupCleanup=cleanup, dataPreserved=True)
            return dict(state="RUNNING", teams=results, dataPreserved=True)

    def stop_stack(self):
        """Normal shutdown retains both function volumes and current context."""
        with self.environment._writer():
            results = {}
            for team in reversed(TEAMS):
                try:
                    results[team] = self.execute("stop", team)
                except EnvironmentError as error:
                    results[team] = dict(state="UNKNOWN", reason=str(error))
            return dict(state="STOPPED" if all(value["state"] == "STOPPED"
                for value in results.values()) else "PARTIAL", teams=results, dataPreserved=True)

    def _runtime_candidate(self, state, team):
        record = state.get("backends", {}).get(team)
        return {key: record[key] for key in ("imageId", "sourceRevision")} if record else self._candidate(team)

    def _activate(self, state, team, record, observed, owner):
        if not record or (observed and observed.get("State", {}).get("Running")):
            raise EnvironmentError("BACKEND_ACTIVATION_REQUIRES_OWNED_STOPPED_CONTAINER")
        if record.get("state") != "STOPPED" and record.get("action") != "activate":
            raise EnvironmentError("BACKEND_OPERATION_RECONCILIATION_REQUIRED")
        candidate = self._candidate(team)
        self._image(candidate["imageId"])
        if record.get("imageId") == candidate["imageId"]:
            return dict(team=team, state="STOPPED", noOp=True, dataPreserved=True)
        if record.get("replacementImageId") not in (None, candidate["imageId"]):
            raise EnvironmentError("BACKEND_ACTIVATION_CANDIDATE_CHANGED")
        old_spec = self._spec(state, team, record["imageId"])
        spec = self._spec(state, team, candidate["imageId"])
        for kind, group in (("volume", spec["volumes"]), ("network", spec["networks"])):
            resource = self._inspect(kind, next(iter(group)))
            labels = (resource or {}).get("Labels") or {}
            if resource and (labels.get("tech.aosedge.demo.owner") != owner or labels.get("tech.aosedge.demo.team") != team):
                raise EnvironmentError("BACKEND_FOREIGN_" + kind.upper())
        path = self.root / ".run/demo-current/backends" / (team + "-compose.json")
        if path.is_symlink() or record.get("composePath") != str(path.relative_to(self.root)) or read_json(path) not in (old_spec, spec):
            raise EnvironmentError("BACKEND_COMPOSE_RECONCILIATION_REQUIRED")
        record.update(state="UNCERTAIN", action="activate", replacementImageId=candidate["imageId"])
        atomic_json(self.root / JOURNAL, state)
        if observed is not None:
            self._docker("container", "rm", record["containerName"])
        if self._inspect("container", record["containerName"]) is not None:
            raise EnvironmentError("BACKEND_ACTIVATION_REMOVAL_UNCONFIRMED")
        atomic_json(path, spec)
        record.update(imageId=candidate["imageId"], sourceRevision=candidate["sourceRevision"],
            state="STOPPED", confirmedAt=now())
        record.pop("replacementImageId", None)
        atomic_json(self.root / JOURNAL, state)
        return dict(team=team, state="STOPPED", noOp=False, dataPreserved=True)

    def _owned_container(self, observed, owner, team, image):
        if observed is None:
            return
        labels = observed.get("Config", {}).get("Labels") or {}
        if labels.get("tech.aosedge.demo.owner") != owner or labels.get("tech.aosedge.demo.team") != team:
            raise EnvironmentError("BACKEND_FOREIGN_CONTAINER")
        if observed.get("Image") != image:
            raise EnvironmentError("BACKEND_CONTAINER_RECONCILIATION_REQUIRED")

    def _spec(self, state, team, image):
        owner = object_id(state["operations"][0]["id"])
        port = 18091 if team == "brake" else 18092
        name = "aosedge-demo-" + team + "-cloud"
        volume = "aosedge_demo_" + team + "_cloud_v1"
        network = name + "-v1"
        labels = {"tech.aosedge.demo.owner": owner, "tech.aosedge.demo.team": team}
        context = str(self.root / ".run/demo-current/backends/context")
        return dict(name=name, services={team: dict(image=image, container_name=name, labels=labels,
            command=["--runtime-mode", "container", "--port", str(port), "--database-path", "/data/" + team + "-health.sqlite",
                     "--admin-socket-path", "/tmp/demo-backend/admin.sock", "--context-path",
                     "/run/demo-control/context/current-unit-context.json"],
            ports=["127.0.0.1:" + str(port) + ":" + str(port)],
            volumes=[volume + ":/data", dict(type="bind", source=context, target="/run/demo-control/context", read_only=True)],
            networks=[network], restart="unless-stopped", security_opt=["no-new-privileges:true"])},
            volumes={volume: dict(name=volume, labels=labels)}, networks={network: dict(name=network, labels=labels)})

    def execute(self, action, team):
        if team not in TEAMS or action not in ("build", "activate", "start", "stop", "status"):
            raise EnvironmentError("BACKEND_OPERATION_INVALID")
        if action == "build":
            return self.build(team)
        with self.environment._writer():
            state = read_json(self.root / JOURNAL)
            if (state.get("kind") != "democtl.current-run" or "test" not in state.get("vehicles", {})
                    or not state.get("operations") or state["operations"][0].get("class") != "LOCAL_CREATE"
                    or state["operations"][0].get("state") != "COMPLETED"):
                raise EnvironmentError("BACKEND_CURRENT_TEST_RUN_REQUIRED")
            owner = object_id(state["operations"][0]["id"])
            name = "aosedge-demo-" + team + "-cloud"
            record = state.get("backends", {}).get(team)
            observed = self._inspect("container", name)
            self._owned_container(observed, owner, team, (record or {}).get("imageId"))
            if action == "activate":
                return self._activate(state, team, record, observed, owner)
            if action == "status":
                runtime = (observed or {}).get("State", {})
                restore_status = []
                for saved in ((state.get("demoLifecycle") or {}).get("fileSharingRecovery") or {}).get("containers", []):
                    current = self._inspect("container", saved["name"])
                    actual = self._restore_fingerprint(current) if current else {}
                    expected = saved["binding"]
                    restore_status.append(dict(name=saved["name"], present=current is not None,
                        running=bool((current or {}).get("State", {}).get("Running")),
                        idMatches=actual.get("id") == expected["id"], imageMatches=actual.get("image") == expected["image"],
                        mountsMatchOrdered=actual.get("mounts") == expected["mounts"],
                        mountsMatchUnordered=sorted(actual.get("mounts", []), key=lambda item: item.get("Destination", "")) ==
                            sorted(expected["mounts"], key=lambda item: item.get("Destination", ""))))
                handles = self._context_handles()
                active = []
                if handles["state"] == "HELD":
                    for line in self._docker("container", "ls", "--format", "{{json .}}").splitlines():
                        item = json.loads(line)
                        name = item.get("Names", "")
                        active.append(dict(name=name if re.fullmatch(r"[a-zA-Z0-9_.-]{1,128}", name) else "UNNAMED",
                            currentRunOwned=("tech.aosedge.demo.owner=" + owner) in item.get("Labels", "").split(",")))
                context_path = str(self.root / ".run/demo-current/backends/context")
                mounts = (observed or {}).get("Mounts") or []
                binding = {"dataMountCount": sum(mount.get("Destination") == "/data" for mount in mounts),
                           "contextMountCount": sum(mount.get("Destination") == "/run/demo-control/context" for mount in mounts)}
                for mount in mounts:
                    if mount.get("Destination") == "/run/demo-control/context":
                        binding.update(contextReadOnly=mount.get("RW") is False,
                            contextIsBind=mount.get("Type") == "bind", contextSource=(
                                "HOST_PATH" if mount.get("Source") == context_path else
                                "DOCKER_DESKTOP_HOST_MOUNT" if mount.get("Source") == "/host_mnt" + context_path else "UNRECOGNIZED"))
                    if mount.get("Destination") == "/data":
                        binding.update(dataWritable=mount.get("RW") is True, dataIsVolume=mount.get("Type") == "volume",
                            dataVolumeMatches=mount.get("Name") == "aosedge_demo_" + team + "_cloud_v1")
                return dict(team=team, state="RUNNING" if runtime.get("Running") else "STOPPED",
                    processHealth=(runtime.get("Health") or {}).get("Status", "NOT_OBSERVED"),
                    contextReadiness="NOT_OBSERVED", productReadiness="NOT_OBSERVED", source="DOCKER_PROCESS_ONLY", storageBinding=binding,
                    contextOpenHandles=handles, engineRunningContainers=active,
                    engineRunningContainersObserved=handles["state"] == "HELD", recoveryContainers=restore_status)
            if action == "stop" and (observed is None or not observed.get("State", {}).get("Running")):
                if record:
                    record.update(state="STOPPED", confirmedAt=now(), reconciliation="OBSERVED_NOT_RUNNING")
                    atomic_json(self.root / JOURNAL, state)
                return dict(team=team, state="STOPPED", noOp=True, dataPreserved=True)
            if record and record.get("state") == "UNCERTAIN":
                if action == "start" and observed and observed.get("State", {}).get("Health", {}).get("Status") == "healthy":
                    record.update(state="RUNNING", confirmedAt=now(), reconciliation="OBSERVED_HEALTHY")
                    atomic_json(self.root / JOURNAL, state)
                    return dict(team=team, state="RUNNING", noOp=True, processHealthy=True)
                if action != "stop":
                    raise EnvironmentError("BACKEND_OPERATION_RECONCILIATION_REQUIRED")
            if action == "start":
                candidate = self._runtime_candidate(state, team)
                self._image(candidate["imageId"])
                if observed and observed.get("State", {}).get("Running"):
                    healthy = observed.get("State", {}).get("Health", {}).get("Status") == "healthy"
                    return dict(team=team, state="RUNNING" if healthy else "STARTING", noOp=True, processHealthy=healthy)
                spec = self._spec(state, team, candidate["imageId"])
                for kind, group in (("volume", spec["volumes"]), ("network", spec["networks"])):
                    resource = self._inspect(kind, next(iter(group)))
                    labels = (resource or {}).get("Labels") or {}
                    if resource and (labels.get("tech.aosedge.demo.owner") != owner
                            or labels.get("tech.aosedge.demo.team") != team):
                        raise EnvironmentError("BACKEND_FOREIGN_" + kind.upper())
                directory = self.environment._directory(".run/demo-current/backends")
                from .backend_context import export_directory
                export_directory(self.environment)
                path = directory / (team + "-compose.json")
                if path.is_symlink() or (path.exists() and (record is None or read_json(path) != spec)):
                    raise EnvironmentError("BACKEND_COMPOSE_RECONCILIATION_REQUIRED")
                atomic_json(path, spec)
                record = dict(imageId=candidate["imageId"], sourceRevision=candidate["sourceRevision"], composePath=str(path.relative_to(self.root)),
                              containerName=name, owner=owner, state="UNCERTAIN", action="start", startedAt=now())
                state.setdefault("backends", {})[team] = record
                atomic_json(self.root / JOURNAL, state)
                self.progress("Starting " + team + " backend; process readiness only, current Unit may not yet exist")
                self._docker("compose", "--file", str(path), "up", "--detach", "--no-build", "--pull", "never", "--wait", "--wait-timeout", "60", timeout=75)
                observed = self._inspect("container", name)
                self._owned_container(observed, owner, team, record["imageId"])
                if not observed or observed.get("State", {}).get("Health", {}).get("Status") != "healthy":
                    raise EnvironmentError("BACKEND_START_NOT_CONFIRMED")
                record.update(state="RUNNING", confirmedAt=now())
            else:
                path = self.root / record["composePath"]
                if path != self.root / ".run/demo-current/backends" / (team + "-compose.json") or path.is_symlink():
                    raise EnvironmentError("BACKEND_COMPOSE_PATH_UNSAFE")
                record.update(state="UNCERTAIN", action="stop", startedAt=now())
                atomic_json(self.root / JOURNAL, state)
                self._docker("compose", "--file", str(path), "stop", "--timeout", "10", timeout=20)
                observed = self._inspect("container", name)
                self._owned_container(observed, owner, team, record["imageId"])
                if observed and observed.get("State", {}).get("Running"):
                    raise EnvironmentError("BACKEND_STOP_NOT_CONFIRMED")
                record.update(state="STOPPED", confirmedAt=now())
            atomic_json(self.root / JOURNAL, state)
            return dict(team=team, state=record["state"], noOp=False, dataPreserved=True)
