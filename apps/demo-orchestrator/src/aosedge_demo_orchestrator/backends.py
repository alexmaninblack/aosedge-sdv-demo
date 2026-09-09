# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Owned functional backend containers; no Cloud, VM or product-state claims."""

import json
import re
import shutil
import subprocess
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
        if team not in TEAMS or action not in ("build", "start", "stop", "status"):
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
            if observed is not None:
                labels = observed.get("Config", {}).get("Labels") or {}
                if labels.get("tech.aosedge.demo.owner") != owner or labels.get("tech.aosedge.demo.team") != team:
                    raise EnvironmentError("BACKEND_FOREIGN_CONTAINER")
                if record is None or observed.get("Image") != record.get("imageId"):
                    raise EnvironmentError("BACKEND_CONTAINER_RECONCILIATION_REQUIRED")
            if action == "status":
                runtime = (observed or {}).get("State", {})
                return dict(team=team, state="RUNNING" if runtime.get("Running") else "STOPPED",
                    processHealth=(runtime.get("Health") or {}).get("Status", "NOT_OBSERVED"),
                    contextReadiness="NOT_OBSERVED", productReadiness="NOT_OBSERVED", source="DOCKER_PROCESS_ONLY")
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
                candidate = self._candidate(team)
                if record and record.get("imageId") != candidate["imageId"]:
                    raise EnvironmentError("BACKEND_IMAGE_CHANGE_REQUIRES_RETIRE")
                self._image(candidate["imageId"])
                if observed and observed.get("State", {}).get("Running"):
                    healthy = observed.get("State", {}).get("Health", {}).get("Status") == "healthy"
                    return dict(team=team, state="RUNNING" if healthy else "STARTING", noOp=True, processHealthy=healthy)
                spec = self._spec(state, team, candidate["imageId"])
                for kind, group in (("volume", spec["volumes"]), ("network", spec["networks"])):
                    resource = self._inspect(kind, next(iter(group)))
                    if resource and (resource.get("Labels") or {}).get("tech.aosedge.demo.owner") != owner:
                        raise EnvironmentError("BACKEND_FOREIGN_" + kind.upper())
                directory = self.environment._directory(".run/demo-current/backends")
                self.environment._directory(".run/demo-current/backends/context")
                path = directory / (team + "-compose.json")
                atomic_json(path, spec)
                record = dict(imageId=candidate["imageId"], sourceRevision=candidate["sourceRevision"], composePath=str(path.relative_to(self.root)),
                              containerName=name, owner=owner, state="UNCERTAIN", action="start", startedAt=now())
                state.setdefault("backends", {})[team] = record
                atomic_json(self.root / JOURNAL, state)
                self.progress("Starting " + team + " backend; process readiness only, current Unit may not yet exist")
                self._docker("compose", "--file", str(path), "up", "--detach", "--no-build", "--pull", "never", "--wait", "--wait-timeout", "60", timeout=75)
                observed = self._inspect("container", name)
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
                if observed and observed.get("State", {}).get("Running"):
                    raise EnvironmentError("BACKEND_STOP_NOT_CONFIRMED")
                record.update(state="STOPPED", confirmedAt=now())
            atomic_json(self.root / JOURNAL, state)
            return dict(team=team, state=record["state"], noOp=False, dataPreserved=True)
