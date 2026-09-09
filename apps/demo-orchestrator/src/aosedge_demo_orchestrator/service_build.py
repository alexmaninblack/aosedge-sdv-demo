# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Explicit development build of the real ARM64 service; no publication."""

import re
import shutil
import subprocess

from .backends import BackendService
from .environment import EnvironmentError, atomic_json, digest
from .status import now, read_json


class ServiceBuilder:
    def __init__(self, environment, progress=None):
        self.environment = environment
        self.progress = progress or (lambda message: None)
        self.commands = BackendService(environment, self.progress)

    def _build(self, arguments):
        self.progress("Building pinned ARM64 Brake runtime and tests; no VM or Cloud action")
        try:
            process = subprocess.Popen(arguments, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True)
        except OSError:
            raise EnvironmentError("SERVICE_BUILD_TOOL_UNAVAILABLE") from None
        # communicate drains the compiler output; only fixed non-secret stage
        # diagnostics are emitted. Repeated waits observe this same process.
        output = ""
        try:
            for _ in range(120):
                try:
                    output, _ = process.communicate(timeout=15)
                    break
                except subprocess.TimeoutExpired:
                    self.progress("ARM64 service build running; dependency cache retained")
            else:
                process.terminate()
                try:
                    process.communicate(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.communicate()
                raise EnvironmentError("SERVICE_BUILD_TIME_BUDGET_EXCEEDED")
        except KeyboardInterrupt:
            process.terminate()
            raise
        if process.returncode:
            reason = "SERVICE_BUILD_FAILED"
            lowered = output.lower()
            for marker, code in (("no space left on device", "SERVICE_BUILD_STORAGE_EXHAUSTED"),
                    ("cannot connect to the docker daemon", "SERVICE_BUILD_DOCKER_UNAVAILABLE"),
                    ("failed to resolve source metadata", "SERVICE_BUILD_BASE_UNAVAILABLE"),
                    ("could not resolve host", "SERVICE_BUILD_DEPENDENCY_NETWORK_UNAVAILABLE"),
                    ("fatal error:", "SERVICE_BUILD_COMPILE_FAILED"),
                    ("tests failed", "SERVICE_BUILD_TEST_FAILED")):
                if marker in lowered:
                    reason = code
                    break
            raise EnvironmentError(reason)

    def execute(self, team):
        if team != "brake":
            raise EnvironmentError("SERVICE_PRODUCT_BUILD_NOT_IMPLEMENTED")
        repository = self.environment.root.parent / "brake-health-service"
        with self.environment._writer():
            revision = self.commands._run(["git", "rev-parse", "HEAD"], cwd=repository).strip()
            if not re.fullmatch(r"[0-9a-f]{40}", revision) or self.commands._run(
                    ["git", "status", "--porcelain"], cwd=repository).strip():
                raise EnvironmentError("SERVICE_COMMITTED_SOURCE_REQUIRED")
            if not (repository / "Dockerfile").is_file():
                raise EnvironmentError("SERVICE_PRODUCT_RECIPE_REQUIRED")
            catalog = self.environment.catalog.project / "services" / team / "builds"
            directory = catalog / revision
            if directory.is_symlink() or not directory.resolve().is_relative_to(self.environment.catalog.project.resolve()):
                raise EnvironmentError("SERVICE_BUILD_PATH_UNSAFE")
            receipt = directory / "build.json"
            if receipt.exists():
                value = read_json(receipt)
                if value.get("sourceRevision") != revision or value.get("state") != "BUILT":
                    raise EnvironmentError("SERVICE_BUILD_RECEIPT_INVALID")
                for relative, expected in value["binaries"].items():
                    path = directory / "output" / relative
                    if not path.is_file() or path.is_symlink() or digest(path) != expected:
                        raise EnvironmentError("SERVICE_BUILD_ARTIFACT_CHANGED")
                return dict(value, noOp=True)
            output = directory / "output"
            if output.exists():
                raise EnvironmentError("SERVICE_BUILD_INCOMPLETE_OUTPUT_RECONCILIATION_REQUIRED")
            executable = shutil.which("docker")
            if not executable:
                raise EnvironmentError("SERVICE_BUILD_DOCKER_REQUIRED")
            epoch = self.commands._run(["git", "show", "-s", "--format=%ct", "HEAD"], cwd=repository).strip()
            if not epoch.isdigit():
                raise EnvironmentError("SERVICE_BUILD_SOURCE_TIME_INVALID")
            directory.mkdir(parents=True, exist_ok=True, mode=0o700)
            self._build([executable, "buildx", "build", "--platform", "linux/arm64", "--pull=false",
                "--target", "export", "--output", "type=local,dest=" + str(output),
                "--build-arg", "SOURCE_REVISION=" + revision, "--build-arg", "SOURCE_DATE_EPOCH=" + epoch,
                "--file", str(repository / "Dockerfile"), str(repository)])
            product = read_json(output / "product-build.json")
            if (product.get("schemaVersion") != 1 or product.get("kind") != "brake-health-linux-arm64-product"
                    or product.get("sourceRevision") != revision or product.get("sourceDateEpoch") != int(epoch)
                    or product.get("architecture") != "arm64" or product.get("os") != "linux"
                    or product.get("productTarget") != "BHS_BUILD_KUKSA_RUNTIME=ON"
                    or product.get("tests", {}).get("ctest") != "passed"):
                raise EnvironmentError("SERVICE_PRODUCT_BUILD_PROOF_INVALID")
            binaries = {}
            for name in ("brake-health-bootstrap", "brake-health-service"):
                path = output / "rootfs/usr/bin" / name
                if not path.is_file() or path.is_symlink():
                    raise EnvironmentError("SERVICE_PRODUCT_BINARY_MISSING")
                with path.open("rb") as stream:
                    header = stream.read(20)
                if header[:6] != b"\x7fELF\x02\x01" or header[18:20] != b"\xb7\x00" or not path.stat().st_mode & 0o111:
                    raise EnvironmentError("SERVICE_PRODUCT_ARM64_ELF_REQUIRED")
                binaries[str(path.relative_to(output))] = digest(path)
            recorded = {item["path"]: item["sha256"] for item in product.get("binaries", [])}
            if recorded != binaries:
                raise EnvironmentError("SERVICE_PRODUCT_BUILD_PROOF_MISMATCH")
            value = dict(schemaVersion=1, team=team, state="BUILT", sourceRevision=revision,
                builtAt=now(), qualification="BUILT_NOT_LIVE_QUALIFIED", binaries=binaries,
                outputPath=str(output))
            atomic_json(receipt, value)
            return dict(value, noOp=False)
