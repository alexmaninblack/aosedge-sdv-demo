# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Bounded Test-only SM qualification operations owned by Demo Control."""

import contextlib
import base64
import gzip
import importlib.machinery
import importlib.util
import os
import hashlib
import io
import json
import subprocess
import tarfile
import shlex
import shutil
from pathlib import Path
import sys
import time
import runpy
import re
import stat
import tempfile

from .environment import EnvironmentError

SOURCE = Path.home() / "OpenAI/aos-vehicle-platform"
SM_REVISION = "b66ab25979e53b997005c0519eda9c869b111d8b"
CM_REVISION = "1c901cf75fb834b5c93224d846660b91137dd126"
SM_TEST_VM = "d53d05cd-4c46-49c9-a896-534b23b88273"
SM_TEST_UNIT = "2a29c145-bbd1-4494-a0e5-d4b79e6a9db5"
FACTORY_SOURCE = Path.home() / "OpenAI/aos-vehicle-platform"
FACTORY_VERSION = "6.1.1-maninblack.31"
FACTORY_REVISION = "0bed8b3769b09fbe685ed599ca8d10e6594fbe53"
FACTORY_RELEASES = {
    FACTORY_VERSION: FACTORY_REVISION,
    "6.1.1-maninblack.32": "04fc8270c55ff5c35f1e98af534a5efccb035464",
    "6.1.1-maninblack.33": "f7922b02b15f6cf816f181e1bf97572b61859aea",
    "6.1.1-maninblack.34": "81e7e1fda991c133a7dc83188c1dcf0f966fd62e",
    "6.1.1-maninblack.35": "bb691efcbf19f1bebd74fd2ef3ae9ff0aee2bf74",
    "6.1.1-maninblack.36": "a0f88d8fc47d5e84df874883cb01872e25516fd5",
    "6.1.1-maninblack.37": "77d99770a3d9476736da55c3e2196396899bc563",
    "6.1.1-maninblack.38": "378c00efad0ec67b2fb0c90328b68c4e8970b511",
}
RELATIVE = "meta-aos-vehicle-platform/recipes-aos/aos-servicemanager/files/systemd-slot-component"
BUILDER_PROJECT = "/home/yocto/r61-build/project/yocto"
ARTIFACT = Path.home() / "OpenAI/demo-artifacts/aosedge-sdv-demo/runtime-proofs/sm-service-prepare-recovery"
SM_PATCHES = ("0002-idempotent-service-container-teardown.patch", "0003-preserve-failed-service-replacement.patch",
              "0004-retry-failed-service-preparation.patch")
FILES = ("config.hpp", "config.cpp", "safestop.hpp", "safestop.cpp", "runtime.hpp", "runtime.cpp",
         "tests/safestop.cpp", "tests/runtime.cpp")


def factory_component_support(revision):
    """Producer metadata for the exact supported source, not live qualification."""
    from .components import COMPONENT
    if revision not in FACTORY_RELEASES.values():
        raise EnvironmentError("FACTORY_SOURCE_REVISION_MISMATCH")
    schema = runpy.run_path(str(FACTORY_SOURCE /
        "meta-aos-vehicle-platform/recipes-support/vss/files/vdp_vss_schema.py"))
    paths = list(schema["BASE_PATHS"] + schema["WHEEL_PATHS"] + schema["SLIP_PATHS"])
    if (len(paths) != 23 or any(not isinstance(path, str)
            or not re.fullmatch(r"Vehicle(?:\.[A-Za-z][A-Za-z0-9_]*)+", path) for path in paths)
            or len(set(paths)) != 23):
        raise EnvironmentError("FACTORY_VDP_SCHEMA_DECLARATION_MISMATCH")
    return dict(schemaVersion=1, runtimeProfile="aos-main-qemuarm64-v1", componentType=COMPONENT,
                supportedReadPaths=paths, sourceRevision=revision)


def builder_ssh():
    return ["ssh", "-p", "10024", "-o", "HostKeyAlias=[127.0.0.1]:10023",
            "-o", "BatchMode=yes", "-o", "IdentitiesOnly=yes",
            "-i", str(Path.home() / ".ssh/id_ed25519"), "-o", "StrictHostKeyChecking=yes",
            "-o", 'UserKnownHostsFile="' + str(Path.home() / "Library/Application Support/CarlaAosEdge/YoctoBuilder/local/known_hosts") + '"',
            "-o", "ConnectTimeout=5", "yocto@127.0.0.1"]


def apply_test(environment, target, manager="sm", restart_cm=False):
    from .environment import JOURNAL, atomic_json
    from .status import read_json, now
    from .vm import VMService
    from .source import SourceDriver
    if target != "test" or manager not in ("sm", "cm"):
        raise EnvironmentError("SM_QUALIFICATION_TEST_ONLY")
    if type(restart_cm) is not bool or (restart_cm and manager != "cm"):
        raise EnvironmentError("RESTART_CM_USES_TEST_CM_APPLY_ONLY")
    if manager == "cm" and restart_cm:
        current = read_json(environment.root / JOURNAL)
        authorized_controls = {
            "5aa1f8e4-a111-4467-a6cc-fb269c62a7a8": "923b9820-999b-41bb-91db-b2a2c469e743",
            "c7b8f9d8-68ea-4b65-b444-8b01595eb110": "d90798f6-a32c-40cc-8129-26a0f1343a67",
        }
        if current.get("vehicles", {}).get("test", {}).get("localVmId") in authorized_controls:
            with environment._writer():
                state = read_json(environment.root / JOURNAL)
                from .environment import factory_for
                vehicle = state.get("vehicles", {}).get("test", {})
                if (vehicle.get("localVmId") not in authorized_controls
                        or vehicle.get("unitId") != authorized_controls.get(vehicle.get("localVmId"))
                        or factory_for(state, "test").get("sha256") !=
                        "f56e037ff6ce11d1dea769055dc160a5a9a8061bbdd2d67745a3042181be2f14"):
                    raise EnvironmentError("CM_CONTROL_REQUIRES_AUTHORIZED_TEST_32")
                record = state.get("cmServiceUpdateProof", {})
                if record:
                    if record.get("proof") == "factory32-delivery-control" and record.get("state") == "COMPLETED":
                        return dict(record["result"], noOp=True)
                    raise EnvironmentError("CM_CONTROL_PREVIOUS_ATTEMPT_REQUIRES_RECONCILIATION")
                record = dict(proof="factory32-delivery-control", state="ATTEMPT_STARTED", startedAt=now())
                state["cmServiceUpdateProof"] = record
                atomic_json(environment.root / JOURNAL, state)
                try:
                    driver = SourceDriver(VMService(environment))
                    with driver.operation(timeout=60):
                        result = driver.guest(state, "test", "component-cm-apply", target="test",
                            proof=record["proof"], restartCm=True)
                except (EnvironmentError, OSError, ValueError, subprocess.SubprocessError):
                    record["state"] = "RECONCILIATION_REQUIRED"
                    atomic_json(environment.root / JOURNAL, state)
                    raise EnvironmentError("CM_CONTROL_RESTART_REQUIRES_RECONCILIATION") from None
                record.update(state="COMPLETED", result=result, confirmedAt=now())
                atomic_json(environment.root / JOURNAL, state)
                return result
    artifact = ARTIFACT if manager == "sm" else ARTIFACT.with_name("cm-service-update-reconcile")
    manifest = read_json(artifact / "manifest.json")
    raw = (artifact / ("aos-" + manager)).read_bytes()
    if (not manifest.get("testsPassed")
            or (manager == "sm" and (manifest.get("profile") != "demo-5s" or manifest.get("proof") != "service-update-teardown"
                                    or manifest.get("serviceUpdateRegressionSuites") != 3))
            or (manager == "cm" and manifest.get("proof") != "service-snapshot-reconciliation")
            or manifest.get("sourceRevision") != (SM_REVISION if manager == "sm" else CM_REVISION)
            or hashlib.sha256(raw).hexdigest() != manifest["executableSha256"]
            or len(raw) > 256 * 1024 * 1024):
        raise EnvironmentError("SM_QUALIFIED_ARTIFACT_REQUIRED")
    with environment._writer():
        state = read_json(environment.root / JOURNAL)
        vehicle = state["vehicles"].get("test", {})
        if (vehicle.get("localVmId") != SM_TEST_VM or vehicle.get("unitId") != SM_TEST_UNIT
                or state.get("factory", {}).get("sha256") !=
                "a9019f4adfe70499bde339c8e9d95eb8568736b73dc218f6c0e390fbcd28ddf4"):
            raise EnvironmentError("SM_PROOF_REQUIRES_AUTHORIZED_TEST_31")
        record = state.setdefault("smServiceUpdateProof" if manager == "sm" else "cmServiceUpdateProof", {})
        record.update(state="ATTEMPT_STARTED", startedAt=now(), binarySha256=manifest["executableSha256"])
        atomic_json(environment.root / JOURNAL, state)
        driver = SourceDriver(VMService(environment))
        try:
            with driver.operation(timeout=60):
                result = driver.guest(state, "test", "component-" + manager + "-apply", target="test",
                    proof=manifest["proof"],
                    restartCm=restart_cm,
                    binary=base64.b64encode(gzip.compress(raw, compresslevel=1, mtime=0)).decode(),
                    sha256=manifest["executableSha256"])
                # systemd clears service credentials on restart. Restore only
                # the already selected Test's public trust/binding inputs.
                if manager == "sm" and not result.get("persistentFactoryInputs") and not result.get("noOp") and state.get("currentVehicle") == "test":
                    driver.guest(state, "test", "configure",
                        generation=state["source"]["assignmentGeneration"],
                        ca=driver.assets()["ca"].read_text())
                    result["selectedTestBindingRestored"] = True
        except EnvironmentError:
            record.update(state="RECONCILIATION_REQUIRED")
            atomic_json(environment.root / JOURNAL, state)
            raise
        record.update(state=result["state"], result=result, confirmedAt=now())
        atomic_json(environment.root / JOURNAL, state)
        return result


def build(target, compile_source=True, manager="sm"):
    """Qualify the pinned Test service teardown fix, export SM and stop Builder."""
    if target != "test" or manager not in ("sm", "cm"):
        raise EnvironmentError("SM_QUALIFICATION_TEST_ONLY")
    artifact = ARTIFACT if manager == "sm" else ARTIFACT.with_name("cm-service-update-reconcile")
    recipe = "aos-servicemanager" if manager == "sm" else "aos-communicationmanager"
    patch_root = SOURCE / "meta-aos-vehicle-platform/recipes-aos" / recipe / "files"
    if artifact.exists():
        raise EnvironmentError("SM_PROOF_ARTIFACT_ALREADY_EXISTS")
    expected = SM_REVISION if manager == "sm" else CM_REVISION
    if shutil.disk_usage(artifact.parent).free < 60 * 1024**3:
        raise EnvironmentError("SM_HOST_FREE_SPACE_BELOW_60_GIB")
    ssh = builder_ssh()
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=SOURCE).decode().strip()
    if revision != expected or subprocess.check_output(["git", "status", "--porcelain"], cwd=SOURCE):
        raise EnvironmentError("SM_PINNED_COMMITTED_SOURCE_REQUIRED")
    try:
        builder("test", "start")
        print(f"Test {manager.upper()}: waiting for Builder SSH; 90-second boot budget", file=sys.stderr, flush=True)
        deadline = time.monotonic() + 90
        while True:
            try:
                ready = subprocess.run(ssh + ["true"], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=7)
            except subprocess.TimeoutExpired:
                ready = subprocess.CompletedProcess(ssh, 255, stderr=b"SSH boot probe timed out")
            if ready.returncode == 0:
                break
            if b"Host key verification failed" in ready.stderr or b"Permission denied" in ready.stderr:
                raise EnvironmentError("SM_BUILDER_SSH_TRUST_OR_AUTH_FAILED")
            if time.monotonic() >= deadline:
                raise EnvironmentError("SM_BUILDER_SSH_BOOT_TIMEOUT")
            time.sleep(1)
        work = BUILDER_PROJECT + "/build-main/tmp/work/cortexa57-aos-linux/" + recipe + "/git"
        if not compile_source:
            compile_log = subprocess.check_output(ssh + ["cat " + work + "/temp/log.do_compile"], timeout=20).decode()
            errors = [line for line in compile_log.splitlines() if "error:" in line or "fatal error:" in line]
            if errors:
                print("\n".join(errors[:20]), file=sys.stderr, flush=True)
                raise EnvironmentError("SM_COMPILE_INCOMPLETE")
            if manager in ("sm", "cm"):
                # Test-only correction: reuse the completed binary when the only
                # changed production translation unit is byte-identical.
                local_lib = SOURCE / "build/aos_core_lib_cpp"
                runtime_file = ("src/core/cm/launcher/instancemanager.cpp" if manager == "cm"
                    else "src/core/sm/launcher/launcher.cpp")
                remote_lib = work + "/service-update-deps/aos_core_lib_cpp/"
                compiled_source = subprocess.check_output(ssh + ["cat " + remote_lib + runtime_file], timeout=15)
                if compiled_source != (local_lib / runtime_file).read_bytes():
                    raise EnvironmentError(manager.upper() + "_PRODUCTION_SOURCE_CHANGED_REBUILD_REQUIRED")
                test_file = "src/core/" + manager + "/launcher/tests/launcher.cpp"
                refresh = "from pathlib import Path; import sys; Path(" + repr(remote_lib + test_file) + ").write_bytes(sys.stdin.buffer.read())"
                subprocess.run(ssh + ["python3 -c " + shlex.quote(refresh)],
                    input=(local_lib / test_file).read_bytes(), check=True, timeout=15)
        data = io.BytesIO()
        inputs = {}
        with tarfile.open(fileobj=data, mode="w") as archive:
            for name in (FILES if manager == "sm" else ()):
                path = SOURCE / RELATIVE / name
                inputs[name] = hashlib.sha256(path.read_bytes()).hexdigest()
                archive.add(path, arcname=RELATIVE + "/" + name, recursive=False)
        for name in (SM_PATCHES if manager == "sm" else ("0001-serialize-sm-stream-writes.patch", "0002-reconcile-stale-instance-snapshot.patch")):
            inputs[name] = hashlib.sha256((patch_root / name).read_bytes()).hexdigest()
        inputs["recipe"] = hashlib.sha256((patch_root.parent / (recipe + "_git.bbappend")).read_bytes()).hexdigest()
        if compile_source:
            # Isolate proof sources; keep the immutable .31 source snapshot intact.
            identity = hashlib.sha256(json.dumps(inputs, sort_keys=True).encode()).hexdigest()[:40]
            proof_source = BUILDER_PROJECT + "/aos-vehicle-platform-" + identity
            archive = subprocess.check_output(["git", "archive", expected], cwd=SOURCE)
            subprocess.run(ssh + ["mkdir -p " + proof_source], check=True, timeout=15)
            subprocess.run(ssh + ["tar -xf - -C " + proof_source], input=archive, check=True, timeout=30)
            subprocess.run(ssh + ["tar -xf - -C " + proof_source],
                           input=data.getvalue(), check=True, timeout=20, stdout=sys.stderr)
            # Populate only absent, exact-revision public Git fetch caches.
            # Keep BitBake offline and never modify an existing cache checkout.
            for repository, pinned in (("aos_core_lib_cpp", "60cb83535f773762c61ac5f544b31b7b88c502e3"),
                                       ("aos_core_api", "af3552a0a5eb0237eff7f5f183780ca46c339cd3")):
                local = SOURCE / "build" / repository
                cache = "/home/yocto/yocto-cache/downloads/git2/github.com.aosedge." + repository + ".git"
                available = subprocess.run(ssh + ["git -C " + cache + " cat-file -e " + pinned + "^{commit}"],
                    capture_output=True, timeout=15)
                if available.returncode == 0:
                    continue
                subprocess.run(["git", "cat-file", "-e", pinned + "^{commit}"], cwd=local, check=True)
                with tempfile.TemporaryDirectory(prefix="democtl-sm-source-") as temporary:
                    bundle = Path(temporary) / (repository + ".bundle")
                    subprocess.run(["git", "bundle", "create", str(bundle), "--all"], cwd=local, check=True)
                    transfer = io.BytesIO()
                    with tarfile.open(fileobj=transfer, mode="w") as archive:
                        archive.add(bundle, arcname=bundle.name)
                    subprocess.run(ssh + ["tar -xf - -C " + proof_source], input=transfer.getvalue(), check=True, timeout=30)
                subprocess.run(ssh + ["test ! -e " + cache + " && git clone --mirror " + proof_source + "/"
                    + repository + ".bundle " + cache + " && git -C " + cache + " cat-file -e " + pinned + "^{commit}"],
                    check=True, timeout=30, stdout=sys.stderr)
            layer_update = ("from pathlib import Path; import re; p=Path(%r); "
                "s,n=re.subn(r'aos-vehicle-platform(?:-[0-9a-f]{40})?/meta-aos-vehicle-platform', %r, p.read_text()); "
                "assert n == 1; p.write_text(s)") % (BUILDER_PROJECT + "/build-main/conf/bblayers.conf",
                    Path(proof_source).name + "/meta-aos-vehicle-platform")
            subprocess.run(ssh + ["python3 -c " + shlex.quote(layer_update)], check=True, timeout=15)
            print(f"Test {manager.upper()}: offline recipe compile; no image build", file=sys.stderr, flush=True)
            command = "cd " + BUILDER_PROJECT + "; . poky/oe-init-build-env build-main >/dev/null; bitbake -R " + proof_source + "/qualification/factory-31.conf -c compile " + recipe
            compile_result = subprocess.run(ssh + ["bash -lc " + shlex.quote(command)],
                           timeout=1200, capture_output=True)
            compile_text = (compile_result.stdout + compile_result.stderr).decode()
            artifact.with_suffix(".compile.log").write_text(compile_text)
            print("\n".join(line for line in compile_text.splitlines()
                if "error:" in line or line.startswith(("ERROR:", "NOTE: Running task", "NOTE: Tasks Summary", "Summary:"))),
                file=sys.stderr, flush=True)
            if compile_result.returncode:
                raise EnvironmentError("SM_BUILD_OR_TEST_FAILED")
        work = BUILDER_PROJECT + "/build-main/tmp/work/cortexa57-aos-linux/" + recipe + "/git"
        test = work + "/build/src/sm/launcher/runtimes/systemd-slot-component/tests/aos_sm_runtimes_systemdslotcomponent_test"
        loader = work + "/recipe-sysroot/usr/lib/ld-linux-aarch64.so.1"
        libs = work + "/recipe-sysroot/lib:" + work + "/recipe-sysroot/usr/lib"
        test_filter = ("SafeStopEvaluatorTest.*:*RequiresTheFixedBootstrapContract:"
            "*AcceptsOnlyExplicitDemoFreshnessProfile:*FactoryDemoInputsRespectPersistentRole:"
            "*StartsWithAnEmptyPersistentStore:*FactoryPlaceholder*:"
            "*StopMakesTheComponentUnavailable:*StopCancellationNeverReturnsSuccess:*StopMissingComponentIsIdempotent:"
            "*SystemdSlotComponentWaitingRecoveryTest.*:*IntentionallyStoppedPreviousRemainsStopped")
        candidates = subprocess.check_output(ssh + ["find " + work + "/build -type f -name '*_test'"], timeout=20).decode().splitlines()
        # The native app disables external library tests. Qualify the exact
        # recipe-patched library separately, reusing its Yocto toolchain.
        library_test = f"""import os, pathlib, shlex, subprocess
work = pathlib.Path({work!r})
environment = os.environ.copy()
path_export = next(line for line in (work / 'temp/run.do_compile').read_text().splitlines() if line.startswith('export PATH='))
environment['PATH'] = shlex.split(path_export)[1].split('=', 1)[1]
cache = dict((line.split(':', 1)[0], line.split('=', 1)[1]) for line in (work / 'build/CMakeCache.txt').read_text().splitlines() if ':' in line and '=' in line and not line.startswith(('#', '//')))
subprocess.run([cache['CMAKE_COMMAND'], '-S', str(work / 'service-update-deps/aos_core_lib_cpp'), '-B', str(work / 'service-update-launcher-tests'), '-G', cache['CMAKE_GENERATOR'], '-DCMAKE_MAKE_PROGRAM=' + cache['CMAKE_MAKE_PROGRAM'], '-DWITH_TEST=ON', '-DWITH_MBEDTLS=OFF', '-DWITH_OPENSSL=OFF', '-DFETCHCONTENT_FULLY_DISCONNECTED=ON', '-DCMAKE_GTEST_DISCOVER_TESTS_DISCOVERY_MODE=PRE_TEST', '-DCMAKE_TOOLCHAIN_FILE=' + str(work / 'toolchain.cmake')], env=environment, check=True)
subprocess.run([cache['CMAKE_COMMAND'], '--build', str(work / 'service-update-launcher-tests'), '--target', {'aos_core_' + manager + '_launcher_test'!r}, '--parallel', '10'], env=environment, check=True)
"""
        print(f"Test {manager.upper()}: build only the shared-library launcher regression target", file=sys.stderr, flush=True)
        library_result = subprocess.run(ssh + ["python3 -c " + shlex.quote(library_test)],
                                        timeout=240, capture_output=True)
        artifact.with_suffix(".library-test-build.log").write_bytes(library_result.stdout + library_result.stderr)
        if library_result.returncode:
            print((library_result.stdout + library_result.stderr).decode()[-10000:], file=sys.stderr, flush=True)
            raise EnvironmentError("SM_LIBRARY_TEST_BUILD_FAILED")
        candidates += subprocess.check_output(ssh + ["find " + work + "/service-update-launcher-tests -type f -name '*_test'"], timeout=20).decode().splitlines()
        native_results = []
        suites = (("/core/cm/launcher/tests/", "CMLauncherTest.ServiceUpdate:CMLauncherTest.ResendInstancesOnMismatchedNodeStatus:ServiceReconciliation/*"),) if manager == "cm" else (
            ("/core/sm/launcher/tests/", "LauncherTest.*:ServiceUpdate/*:ServicePreparation/*"),
            ("/sm/launcher/runtimes/container/tests/", "ContainerCleanupErrorTest.*:ContainerRunnerTest.*:ContainerRuntimeTest.StopInstance"),
            ("/sm/networkmanager/tests/", "BridgeNetworkTest.*:NamespaceCleanupTest.*"),
        )
        for marker, selected in suites:
            matches = [candidate for candidate in candidates if marker in candidate
                       and (marker.startswith("/core/") or "/core/" not in candidate)]
            if len(matches) != 1:
                raise EnvironmentError("SM_NATIVE_TEST_TARGET_UNRESOLVED:" + marker)
            print(f"Test {manager.upper()}: native service regression " + selected, file=sys.stderr, flush=True)
            native = subprocess.run(ssh + ["sudo -n " + loader + " --library-path " + libs + " " + matches[0]
                + " --gtest_filter=" + shlex.quote(selected)], timeout=60, capture_output=True)
            print(native.stdout.decode(), file=sys.stderr, flush=True)
            print(native.stderr.decode(), file=sys.stderr, flush=True)
            native_results.append(native.stdout + native.stderr)
            artifact.with_suffix(".native-tests.log").write_bytes(b"\n".join(native_results))
            if native.returncode or b"[  PASSED  ]" not in native.stdout or b"[  SKIPPED ]" in native.stdout:
                raise EnvironmentError("SM_SERVICE_REGRESSION_FAILED:" + marker)
        if manager == "cm":
            required = ("ServiceReconciliation/CMStaleSnapshotTest.OldVersionTriggersResendWithoutChangingDesiredVersion/0",
                        "ServiceReconciliation/CMStaleSnapshotTest.OldVersionTriggersResendWithoutChangingDesiredVersion/1")
            combined = b"\n".join(native_results)
            if any(("[       OK ] " + name).encode() not in combined for name in required):
                raise EnvironmentError("CM_REQUIRED_REGRESSIONS_NOT_EXECUTED")
            binaries = subprocess.check_output(ssh + ["find " + work + "/build -type f -name aos_cm_app"], timeout=20).decode().splitlines()
            if len(binaries) != 1:
                raise EnvironmentError("CM_BINARY_IDENTITY_UNRESOLVED")
            binary = subprocess.check_output(ssh + ["cat " + binaries[0]], timeout=30)
            if binary[:5] != b"\x7fELF\x02" or binary[18:20] != b"\xb7\x00":
                raise EnvironmentError("CM_BINARY_NOT_ARM64_ELF")
            artifact.mkdir()
            (artifact / "aos-cm").write_bytes(binary)
            (artifact / "aos-cm").chmod(0o444)
            (artifact / "tests.log").write_bytes(combined)
            manifest = dict(sourceRevision=expected, sourceSha256=inputs, executableSha256=hashlib.sha256(binary).hexdigest(),
                testsPassed=True, proof="service-snapshot-reconciliation", testFilter=suites[0][1], imageBuild=False, offline=True)
            (artifact / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
            return dict(artifact=str(artifact), **manifest)
        print(f"Test {manager.upper()}: executing native timing, role, physical-gate and stop regressions", file=sys.stderr, flush=True)
        result = subprocess.run(ssh + ["sudo -n " + loader + " --library-path " + libs + " " + test + " --gtest_filter=" + __import__("shlex").quote(test_filter)],
                                timeout=30, capture_output=True)
        print(result.stdout.decode(), file=sys.stderr, flush=True)
        print(result.stderr.decode(), file=sys.stderr, flush=True)
        artifact.with_suffix(".test.log").write_bytes(result.stdout + result.stderr)
        if result.returncode:
            raise EnvironmentError("SM_TARGETED_TEST_FAILED:" + str(result.returncode))
        required_tests = ("DemoFutureSkewIsBoundedAtAcquisitionAndTheGate",
            "StandardStillRejectsAnyFutureAcquisitionOrGate", "DemoAgeAllowancePreservesOtherGates",
            "FactoryDemoInputsRespectPersistentRole", "StopCancellationNeverReturnsSuccess",
            "ColdBootStartsInactiveCommittedPrevious/0", "ColdBootStartsInactiveCommittedPrevious/1",
            "HealthyPreviousDoesNotRestart/0", "HealthyPreviousDoesNotRestart/1",
            "StartFailurePreservesWaitingState/0", "StartFailurePreservesWaitingState/1",
            "HealthRecheckFailurePreservesWaitingState/0", "HealthRecheckFailurePreservesWaitingState/1",
            "MissingActiveIsNotRecreated/0", "MissingActiveIsNotRecreated/1",
            "IntentionallyStoppedPreviousRemainsStopped")
        if not re.search(rb"\[  PASSED  \] [1-9][0-9]* tests\.", result.stdout) or any(
                not re.search(rb"\[       OK \] [^\n]*\." + re.escape(name.encode()) + rb" \(", result.stdout)
                for name in required_tests):
            raise EnvironmentError("SM_REQUIRED_NATIVE_REGRESSIONS_NOT_EXECUTED")
        binaries = subprocess.check_output(ssh + ["find " + work + "/build -type f -name aos_sm_app"], timeout=20).decode().splitlines()
        if len(binaries) != 1:
            raise EnvironmentError("SM_BINARY_IDENTITY_UNRESOLVED")
        binary = subprocess.check_output(ssh + ["cat " + binaries[0]], timeout=30)
        if binary[:5] != b"\x7fELF\x02" or binary[18:20] != b"\xb7\x00":
            raise EnvironmentError("SM_BINARY_NOT_ARM64_ELF")
        artifact.mkdir(parents=True)
        (artifact / "aos-sm").write_bytes(binary)
        (artifact / "aos-sm").chmod(0o444)
        (artifact / "tests.log").write_bytes(b"\n".join(native_results) + result.stdout)
        manifest = dict(baseRevision=FACTORY_REVISION, sourceRevision=expected, sourceSha256=inputs, executableSha256=hashlib.sha256(binary).hexdigest(),
                        profile="demo-5s", defaultMaximumSourceAgeMs=250, demoMaximumSourceAgeMs=5000,
                        demoMaximumFutureSkewMs=5000, demoReadTimeoutMs=1000, standardReadTimeoutMs=250,
                        offline=True, imageBuild=False, testsPassed=True, testFilter=test_filter,
                        serviceUpdateRegressionSuites=3, proof="service-update-teardown", guestApplied=False)
        (artifact / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        return dict(artifact=str(artifact), **manifest)
    except subprocess.CalledProcessError:
        raise EnvironmentError("SM_BUILD_OR_TEST_FAILED") from None
    finally:
        builder("test", "stop")


PERMISSION_RECIPES = {"iam": "aos-iamanager", "sm": "aos-servicemanager", "cm": "aos-communicationmanager"}
PERMISSION_ARTIFACT = ARTIFACT.with_name("core-permission-keys-256")
PERMISSION_VM = "6fcf5a74-0b74-4ef0-a05d-44bad598ab94"
PERMISSION_UNIT = "42c0bf43-4eb7-44e6-8c74-f60f9959da66"


def permission_recipe_inputs(iam_response_capacity=False):
    """Only capacity may differ from the accepted .33 manager recipes."""
    base = FACTORY_RELEASES["6.1.1-maninblack.33"]
    files = {}
    for recipe in PERMISSION_RECIPES.values():
        name = f"meta-aos-vehicle-platform/recipes-aos/{recipe}/{recipe}_git.bbappend"
        raw = (SOURCE / name).read_bytes()
        previous = subprocess.check_output(["git", "show", base + ":" + name], cwd=SOURCE)
        code = lambda value: [line for line in value.decode().splitlines()
            if line.strip() and not line.lstrip().startswith("#")]
        lines = code(raw)
        reply_patch = 'SRC_URI += "file://0001-use-function-count-for-permission-response.patch"'
        if recipe == "aos-iamanager" and reply_patch in lines:
            if not iam_response_capacity or lines.count(reply_patch) != 1:
                raise EnvironmentError("CORE_PERMISSION_IAM_RESPONSE_FIX_REQUIRES_SELECTION")
            lines.remove(reply_patch)
            patch_name = "meta-aos-vehicle-platform/recipes-aos/aos-iamanager/files/0001-use-function-count-for-permission-response.patch"
            patch = (SOURCE / patch_name).read_bytes()
            removed = [line for line in patch.decode().splitlines() if line.startswith("-") and not line.startswith("---")]
            added = [line for line in patch.decode().splitlines() if line.startswith("+") and not line.startswith("+++")]
            if removed != ['-    auto          aosInstancePerm = std::make_unique<StaticArray<FunctionPermissions, cFuncServiceMaxCount>>();'] or added != ['+    auto          aosInstancePerm = std::make_unique<StaticArray<FunctionPermissions, cFunctionsMaxCount>>();']:
                raise EnvironmentError("CORE_PERMISSION_IAM_RESPONSE_PATCH_NOT_EXACT")
            files[patch_name] = patch
        flag = 'CXXFLAGS:append = " -DAOS_CONFIG_TYPES_FUNCTION_LEN=256"'
        if lines.count(flag) != 1 or [line for line in lines if line != flag] != code(previous):
            raise EnvironmentError("CORE_PERMISSION_RECIPE_DELTA_NOT_CAPACITY_ONLY")
        files[name] = raw
    return files


def build_permissions(target, iam_response_capacity=False):
    """Compile three .33 managers with one capacity delta, then stop Builder."""
    from .environment import atomic_json
    if target != "test":
        raise EnvironmentError("CORE_PERMISSION_TEST_ONLY")
    files = permission_recipe_inputs(iam_response_capacity)
    base = FACTORY_RELEASES["6.1.1-maninblack.33"]
    artifact = PERMISSION_ARTIFACT.with_name("core-permission-iam-response-32") if iam_response_capacity else PERMISSION_ARTIFACT
    recipes = {"iam": PERMISSION_RECIPES["iam"]} if iam_response_capacity else PERMISSION_RECIPES
    source_hashes = {name: hashlib.sha256(raw).hexdigest() for name, raw in files.items()}
    identity = hashlib.sha256(json.dumps(source_hashes, sort_keys=True).encode()).hexdigest()
    if artifact.exists():
        previous = json.loads((artifact / "manifest.json").read_text())
        if (not iam_response_capacity or previous.get("state") != "BUILD_FAILED_RECONCILE"
                or previous.get("binaries") or previous.get("sourceIdentity") == identity
                or not re.fullmatch(r"[0-9a-f]{64}", previous.get("sourceIdentity", ""))):
            raise EnvironmentError("CORE_PERMISSION_ARTIFACT_EXISTS_RECONCILE")
        failed = artifact.with_name(artifact.name + "-failed-" + previous["sourceIdentity"][:12])
        if failed.exists() or failed.is_symlink():
            raise EnvironmentError("CORE_PERMISSION_FAILURE_EVIDENCE_EXISTS")
        artifact.rename(failed)
    if shutil.disk_usage(artifact.parent).free < 60 * 1024**3:
        raise EnvironmentError("CORE_PERMISSION_HOST_FREE_SPACE_BELOW_60_GIB")
    source = BUILDER_PROJECT + "/aos-vehicle-platform-" + identity[:40]
    ssh = builder_ssh()
    def remote(command, timeout=30, data=None):
        return subprocess.run(ssh + [command], input=data, capture_output=True, timeout=timeout, check=True).stdout
    old_layers = None
    layers = BUILDER_PROJECT + "/build-main/conf/bblayers.conf"
    artifact.mkdir(mode=0o700)
    manifest = dict(state="BUILD_STARTED", capacity=256, baseRevision=base,
        recipeSha256=source_hashes, sourceIdentity=identity, builderSource=source, binaries={},
        iamResponseCapacity=32 if iam_response_capacity else None)
    atomic_json(artifact / "manifest.json", manifest)
    try:
        builder("test", "start")
        deadline = time.monotonic() + 90
        while True:
            try:
                remote("true", timeout=7)
                break
            except (subprocess.SubprocessError, OSError):
                if time.monotonic() >= deadline:
                    raise EnvironmentError("CORE_PERMISSION_BUILDER_SSH_TIMEOUT") from None
                time.sleep(1)
        if int(remote("df -Pk " + BUILDER_PROJECT + " | tail -1 | awk '{print $4}'")) * 1024 < 60 * 1024**3:
            raise EnvironmentError("CORE_PERMISSION_BUILDER_FREE_SPACE_BELOW_60_GIB")
        archive = subprocess.check_output(["git", "archive", base], cwd=SOURCE)
        remote("mkdir -p " + source)
        remote("tar -xf - -C " + source, data=archive)
        data = io.BytesIO()
        with tarfile.open(fileobj=data, mode="w") as tar:
            for name, raw in files.items():
                info = tarfile.TarInfo(name)
                info.size, info.mode = len(raw), 0o644
                tar.addfile(info, io.BytesIO(raw))
        remote("tar -xf - -C " + source, data=data.getvalue())
        old_layers = remote("cat " + layers)
        replaced, count = re.subn(rb'aos-vehicle-platform(?:-[0-9a-f]{40})?/meta-aos-vehicle-platform',
            (Path(source).name + "/meta-aos-vehicle-platform").encode(), old_layers)
        if count != 1:
            raise EnvironmentError("CORE_PERMISSION_BUILDER_LAYER_NOT_UNIQUE")
        # Existing private Builder transport; restore its configuration in finally.
        writer = "python3 -c " + shlex.quote("import sys; from pathlib import Path; Path(" + repr(layers) + ").write_bytes(sys.stdin.buffer.read())")
        remote(writer, data=replaced)
        command = "cd " + BUILDER_PROJECT + "; . poky/oe-init-build-env build-main >/dev/null; bitbake -R " + source + "/qualification/factory-33.conf -c compile " + " ".join(recipes.values())
        print("Test: compile " + ", ".join(recipes).upper() + "; permission keys 256; offline, no image build", file=sys.stderr, flush=True)
        with (artifact / "compile.log").open("wb") as log:
            result = subprocess.run(ssh + ["bash -lc " + shlex.quote(command)], stdout=log, stderr=subprocess.STDOUT, timeout=1800)
        if result.returncode:
            raise EnvironmentError("CORE_PERMISSION_COMPILE_FAILED_SEE_ARTIFACT_LOG")
        for manager, recipe in recipes.items():
            work = BUILDER_PROJECT + "/build-main/tmp/work/cortexa57-aos-linux/" + recipe + "/git"
            # Both application and embedded library must have identical layouts.
            check = "from pathlib import Path; root=Path(" + repr(work + "/build") + "); files=list(root.rglob('flags.make')); checked=[p for p in files if 'CXX_FLAGS =' in p.read_text()]; assert checked; assert all('-DAOS_CONFIG_TYPES_FUNCTION_LEN=256' in p.read_text() for p in checked); print(len(checked))"
            checked = int(remote("python3 -c " + shlex.quote(check)))
            paths = remote("find " + work + "/build -type f -name aos_" + manager + "_app").decode().splitlines()
            if len(paths) != 1:
                raise EnvironmentError("CORE_PERMISSION_EXECUTABLE_NOT_UNIQUE:" + manager)
            raw = remote("cat " + paths[0], timeout=60)
            if raw[:6] != b"\x7fELF\x02\x01" or raw[18:20] != b"\xb7\x00" or len(raw) > 256 * 1024**2:
                raise EnvironmentError("CORE_PERMISSION_ARM64_EXECUTABLE_REQUIRED")
            binary = artifact / ("aos_" + manager + "_app")
            binary.write_bytes(raw)
            binary.chmod(0o755)
            manifest["binaries"][manager] = dict(sha256=hashlib.sha256(raw).hexdigest(), size=len(raw), checkedCppTargets=checked)
            print(manager.upper() + ": compiled ARM64 executable exported", file=sys.stderr, flush=True)
        manifest["state"] = "BUILT"
        atomic_json(artifact / "manifest.json", manifest)
        return dict(manifest, artifact=str(artifact), imageBuilt=False)
    except Exception:
        manifest["state"] = "BUILD_FAILED_RECONCILE"
        atomic_json(artifact / "manifest.json", manifest)
        raise
    finally:
        try:
            if old_layers is not None:
                remote("python3 -c " + shlex.quote("import sys; from pathlib import Path; Path(" + repr(layers) + ").write_bytes(sys.stdin.buffer.read())"), data=old_layers)
        finally:
            builder("test", "stop")


READINESS_REVISION = "b308a64a637913c493a0ac98b4f8a4acaae53643"
READINESS_ARTIFACT = ARTIFACT.with_name("provider-advisory-readiness-" + READINESS_REVISION[:12])


def build_readiness(target):
    """Warm compile of the fixed Provider only; no Factory or manager build."""
    from .environment import atomic_json
    if target != "test":
        raise EnvironmentError("READINESS_TEST_ONLY")
    artifact = READINESS_ARTIFACT
    if artifact.exists():
        value = json.loads((artifact / "manifest.json").read_text())
        if (value.get("state") == "BUILT" and value.get("sourceRevision") == READINESS_REVISION
                and hashlib.sha256((artifact / "aos-kuksa-provider-prepare").read_bytes()).hexdigest() == value.get("sha256")):
            return dict(value, noOp=True)
        raise EnvironmentError("READINESS_BUILD_RECONCILIATION_REQUIRED")
    if shutil.disk_usage(artifact.parent).free < 60 * 1024**3:
        raise EnvironmentError("READINESS_BUILD_FREE_SPACE_BELOW_60_GIB")
    source = BUILDER_PROJECT + "/aos-vehicle-platform-" + READINESS_REVISION
    ssh = builder_ssh()
    def remote(command, timeout=30, data=None):
        return subprocess.run(ssh + [command], input=data, capture_output=True, timeout=timeout, check=True).stdout
    layers = BUILDER_PROJECT + "/build-main/conf/bblayers.conf"
    old_layers = None
    artifact.mkdir(mode=0o700)
    result = dict(state="BUILD_STARTED", sourceRevision=READINESS_REVISION)
    atomic_json(artifact / "manifest.json", result)
    try:
        builder("test", "start")
        deadline = time.monotonic() + 90
        while True:
            try:
                remote("true", timeout=7)
                break
            except (subprocess.SubprocessError, OSError):
                if time.monotonic() >= deadline:
                    raise EnvironmentError("READINESS_BUILDER_SSH_TIMEOUT") from None
                time.sleep(1)
        archive = subprocess.check_output(["git", "archive", READINESS_REVISION], cwd=SOURCE)
        remote("mkdir -p " + source)
        remote("tar -xf - -C " + source, data=archive)
        old_layers = remote("cat " + layers)
        replaced, count = re.subn(rb'aos-vehicle-platform(?:-[0-9a-f]{40})?/meta-aos-vehicle-platform',
            (Path(source).name + "/meta-aos-vehicle-platform").encode(), old_layers)
        if count != 1:
            raise EnvironmentError("READINESS_BUILDER_LAYER_NOT_UNIQUE")
        writer = "python3 -c " + shlex.quote("import sys; from pathlib import Path; Path(" + repr(layers) + ").write_bytes(sys.stdin.buffer.read())")
        remote(writer, data=replaced)
        command = "cd " + BUILDER_PROJECT + "; . poky/oe-init-build-env build-main >/dev/null; bitbake -R " + source + "/qualification/factory-33.conf -c compile aos-kuksa-auth-compat"
        print("Test: compile KUKSA Provider readiness scope; warm cache, no image or manager build", file=sys.stderr, flush=True)
        with (artifact / "compile.log").open("wb") as log:
            built = subprocess.run(ssh + ["bash -lc " + shlex.quote(command)], stdout=log, stderr=subprocess.STDOUT, timeout=1200)
        if built.returncode:
            raise EnvironmentError("READINESS_COMPILE_FAILED_SEE_ARTIFACT_LOG")
        work = BUILDER_PROJECT + "/build-main/tmp/work/cortexa57-aos-linux/aos-kuksa-auth-compat"
        paths = remote("find " + work + " -path '*/build/aos-kuksa-provider-prepare' -type f").decode().splitlines()
        if len(paths) != 1:
            raise EnvironmentError("READINESS_EXECUTABLE_NOT_UNIQUE")
        raw = remote("cat " + paths[0], timeout=30)
        if raw[:6] != b"\x7fELF\x02\x01" or raw[18:20] != b"\xb7\x00" or len(raw) > 32*1024**2:
            raise EnvironmentError("READINESS_ARM64_EXECUTABLE_REQUIRED")
        (artifact / "aos-kuksa-provider-prepare").write_bytes(raw)
        result.update(state="BUILT", sha256=hashlib.sha256(raw).hexdigest(), size=len(raw))
        atomic_json(artifact / "manifest.json", result)
        return result
    except Exception:
        result["state"] = "BUILD_FAILED_RECONCILE"
        atomic_json(artifact / "manifest.json", result)
        raise
    finally:
        try:
            if old_layers is not None:
                remote("python3 -c " + shlex.quote("import sys; from pathlib import Path; Path(" + repr(layers) + ").write_bytes(sys.stdin.buffer.read())"), data=old_layers)
        finally:
            builder("test", "stop")


def apply_readiness(environment, target):
    from .environment import JOURNAL, atomic_json
    from .status import read_json
    from .vm import VMService
    from .source import SourceDriver
    if target != "test":
        raise EnvironmentError("READINESS_TEST_ONLY")
    with environment._writer():
        state = read_json(environment.root / JOURNAL)
        item = state.get("vehicles", {}).get("test", {})
        if item.get("localVmId") != PERMISSION_VM or item.get("unitId") != PERMISSION_UNIT:
            raise EnvironmentError("READINESS_PRESERVED_TEST_REQUIRED")
        manifest = read_json(READINESS_ARTIFACT / "manifest.json")
        raw = (READINESS_ARTIFACT / "aos-kuksa-provider-prepare").read_bytes()
        if manifest.get("state") != "BUILT" or manifest.get("sourceRevision") != READINESS_REVISION or hashlib.sha256(raw).hexdigest() != manifest.get("sha256"):
            raise EnvironmentError("READINESS_BUILT_SOURCE_REQUIRED")
        driver = SourceDriver(VMService(environment))
        with driver.operation(timeout=100):
            result = driver.guest(state, "test", "provider-readiness-apply", binary=dict(sha256=manifest["sha256"],
                data=base64.b64encode(gzip.compress(raw, compresslevel=1, mtime=0)).decode()))
        state["providerReadinessProof"] = dict(sourceRevision=READINESS_REVISION, result=result)
        atomic_json(environment.root / JOURNAL, state)
        return result


def apply_permissions(environment, target, observe=False, iam_response_capacity=False):
    from .environment import JOURNAL, atomic_json, factory_for
    from .status import read_json, now
    from .vm import VMService
    from .source import SourceDriver
    if target != "test":
        raise EnvironmentError("CORE_PERMISSION_TEST_ONLY")
    with environment._writer():
        state = read_json(environment.root / JOURNAL)
        vehicle = state.get("vehicles", {}).get("test", {})
        if (vehicle.get("localVmId") != PERMISSION_VM or vehicle.get("unitId") != PERMISSION_UNIT
                or factory_for(state, "test").get("sha256") !=
                "a302b2f2e2f238b361682ab8a529ec036ff260e00b2fb9a4d21db325d8d45761"):
            raise EnvironmentError("CORE_PERMISSION_AUTHORIZED_TEST_33_REQUIRED")
        driver = SourceDriver(VMService(environment))
        if observe:
            with driver.operation(timeout=45):
                return driver.guest(state, "test", "core-permissions-status", target="test")
        if iam_response_capacity:
            return apply_iam_response_capacity(environment, state, driver)
        manifest = read_json(PERMISSION_ARTIFACT / "manifest.json")
        if (manifest.get("state") != "BUILT" or manifest.get("capacity") != 256
                or manifest.get("baseRevision") != FACTORY_RELEASES["6.1.1-maninblack.33"]
                or set(manifest.get("binaries", {})) != set(PERMISSION_RECIPES)):
            raise EnvironmentError("CORE_PERMISSION_QUALIFIED_BINARIES_REQUIRED")
        payload = {}
        for manager, info in manifest["binaries"].items():
            raw = (PERMISSION_ARTIFACT / ("aos_" + manager + "_app")).read_bytes()
            if hashlib.sha256(raw).hexdigest() != info["sha256"] or len(raw) != info["size"]:
                raise EnvironmentError("CORE_PERMISSION_BINARY_DIGEST_MISMATCH")
            payload[manager] = dict(sha256=info["sha256"], data=base64.b64encode(gzip.compress(raw, compresslevel=1, mtime=0)).decode())
        record = state.get("corePermissionCapacityProof", {})
        with driver.operation(timeout=150):
            before = driver.guest(state, "test", "core-permissions-status", target="test")
            if all(before["managers"][name].get("binarySha256") == value["sha256"]
                    and before["managers"][name]["service"].get("ActiveState") == "active" for name, value in payload.items()):
                if not before.get("committedVdp66Sha256") or not before.get("transientFilesMatchProcesses"):
                    raise EnvironmentError("CORE_PERMISSION_POST_READ_INCOMPLETE")
                record.update(state="APPLIED", result=before, confirmedAt=now(), reconciledByPostRead=True)
                state["corePermissionCapacityProof"] = record
                atomic_json(environment.root / JOURNAL, state)
                return dict(before, noOp=True, reconciledByPostRead=True)
            if record.get("state") in ("ATTEMPT_STARTED", "RECONCILIATION_REQUIRED"):
                raise EnvironmentError("CORE_PERMISSION_PREVIOUS_ATTEMPT_REQUIRES_RECONCILIATION")
            record = dict(state="ATTEMPT_STARTED", startedAt=now(), before=before, binaries=manifest["binaries"])
            state["corePermissionCapacityProof"] = record
            atomic_json(environment.root / JOURNAL, state)
            try:
                result = driver.guest(state, "test", "core-permissions-apply", target="test", binaries=payload,
                    previous={name: value["binarySha256"] for name, value in before["managers"].items()})
            except EnvironmentError:
                record["state"] = "RECONCILIATION_REQUIRED"
                atomic_json(environment.root / JOURNAL, state)
                raise
        record.update(state="APPLIED", result=result, confirmedAt=now())
        atomic_json(environment.root / JOURNAL, state)
        return result


def apply_iam_response_capacity(environment, state, driver):
    """One bounded IAM replacement, retaining the existing CM/SM bytes."""
    from .environment import JOURNAL, atomic_json
    from .status import read_json, now
    artifact = PERMISSION_ARTIFACT.with_name("core-permission-iam-response-32")
    manifest = read_json(artifact / "manifest.json")
    original = read_json(PERMISSION_ARTIFACT / "manifest.json")
    if (manifest.get("state") != "BUILT" or manifest.get("capacity") != 256
            or manifest.get("iamResponseCapacity") != 32 or set(manifest.get("binaries", {})) != {"iam"}
            or manifest.get("baseRevision") != FACTORY_RELEASES["6.1.1-maninblack.33"]):
        raise EnvironmentError("IAM_RESPONSE_BUILD_REQUIRED")
    raw = (artifact / "aos_iam_app").read_bytes()
    info = manifest["binaries"]["iam"]
    if hashlib.sha256(raw).hexdigest() != info["sha256"] or len(raw) != info["size"]:
        raise EnvironmentError("IAM_RESPONSE_BINARY_DIGEST_MISMATCH")
    expected = {name: value["sha256"] for name, value in original["binaries"].items()}
    record = state.get("iamResponseCapacityProof", {})
    with driver.operation(timeout=150):
        before = driver.guest(state, "test", "core-permissions-status", target="test")
        if (before["managers"]["iam"]["binarySha256"] == info["sha256"]
                and all(before["managers"][name]["service"].get("ActiveState") == "active" for name in expected)
                and all(before["managers"][name]["binarySha256"] == expected[name] for name in ("sm", "cm"))
                and before.get("transientFilesMatchProcesses")):
            record.update(state="APPLIED", result=before, confirmedAt=now(), reconciledByPostRead=True)
            state["iamResponseCapacityProof"] = record
            atomic_json(environment.root / JOURNAL, state)
            return dict(before, noOp=True)
        if record.get("state") in ("ATTEMPT_STARTED", "RECONCILIATION_REQUIRED"):
            raise EnvironmentError("IAM_RESPONSE_RECONCILIATION_REQUIRED")
        if not before.get("transientFilesMatchProcesses") or any(before["managers"][name]["binarySha256"] != expected[name] for name in expected):
            raise EnvironmentError("IAM_RESPONSE_PREVIOUS_BINARY_CHANGED")
        record = dict(state="ATTEMPT_STARTED", startedAt=now(), before=before, sha256=info["sha256"])
        state["iamResponseCapacityProof"] = record
        atomic_json(environment.root / JOURNAL, state)
        try:
            result = driver.guest(state, "test", "core-permissions-iam-response-apply", target="test", previous=expected,
                binary=dict(sha256=info["sha256"], data=base64.b64encode(gzip.compress(raw, compresslevel=1, mtime=0)).decode()))
        except EnvironmentError:
            record["state"] = "RECONCILIATION_REQUIRED"
            atomic_json(environment.root / JOURNAL, state)
            raise
    record.update(state="APPLIED", confirmedAt=now(), result=result)
    atomic_json(environment.root / JOURNAL, state)
    return result


def qualify_cm_startup(target, compile_binary=False):
    """Red/green startup proof on the warm .34 CM; restore Builder sources/cache."""
    from .environment import atomic_json
    if target != "test":
        raise EnvironmentError("CM_STARTUP_RECONCILIATION_TEST_ONLY")
    root = SOURCE / "build/aos_core_lib_cpp"
    relative = "src/core/cm/launcher/launcher.cpp"
    test_relative = "src/core/cm/launcher/tests/launcher.cpp"
    before = subprocess.check_output(["git", "show", "HEAD:" + relative], cwd=root).decode()
    old = "            Tie(doRebalance, err) = mInstanceManager.SetSubjects(mNewSubjects.GetValue());"
    new = ("            bool subjectsChanged = false;\n"
           "            Tie(subjectsChanged, err) = mInstanceManager.SetSubjects(mNewSubjects.GetValue());\n"
           "            doRebalance = doRebalance || subjectsChanged;")
    if before.count(old) != 1 or (root / relative).read_text() not in (before, before.replace(old, new)):
        raise EnvironmentError("CM_STARTUP_BASELINE_REQUIRES_RECONCILIATION")
    tests = subprocess.check_output(["git", "show", "HEAD:" + test_relative], cwd=root).decode()
    start = tests.index("TEST_F(CMLauncherTest, RebalancingWithStoredNotScheduledInstances)")
    end = tests.index("\nTEST_F(", start + 1)
    original = tests[start:end]
    needle = "    mInstanceRunner.SendInitialStatuses(cNodeIDRemoteSM1);"
    replacement = '''    // SM may already run an instance whose stored CM scheduling was incomplete.
    // Startup reconciliation must restore the plan before sending a stop request.
    std::vector<InstanceStatus> running = {CreateInstanceStatus(
        CreateInstanceIdent(cService2, cSubject1, 0), cNodeIDRemoteSM1, cRunnerRunc,
        aos::InstanceStateEnum::eActive, ErrorEnum::eNone, "", false, digest2.CStr())};
    static_cast<InstanceStatusReceiverItf&>(mLauncher).OnNodeInstancesStatusesReceived(cNodeIDRemoteSM1,
        Array<InstanceStatus>(running.data(), running.size()));'''
    if original.count(needle) != 1:
        raise EnvironmentError("CM_STARTUP_REGRESSION_FIXTURE_CHANGED")
    fixture = original.replace(needle, replacement).replace(
        "    ASSERT_TRUE(mLauncher.Start().IsNone());",
        '''    EXPECT_CALL(mInstanceRunner, OnRunRequest()).WillRepeatedly([this]() {
        for (const auto& [node, request] : mInstanceRunner.GetRunRequests()) {
            EXPECT_TRUE(request.mStopInstances.empty()) << "unexpected startup stop: " << node;
        }
    });
    ASSERT_TRUE(mLauncher.Start().IsNone());''')
    test_after = tests[:start] + fixture + tests[end:]
    if (root / test_relative).read_text() not in (tests, test_after):
        raise EnvironmentError("CM_STARTUP_LOCAL_TEST_SOURCE_CHANGED")
    proof_root = ARTIFACT.with_name("cm-startup-reconcile-20260917")
    proof_root.mkdir(mode=0o700, exist_ok=True)
    attempt = Path(tempfile.mkdtemp(prefix="proof-", dir=proof_root))
    payload = dict(work=BUILDER_PROJECT + "/build-main/tmp/work/cortexa57-aos-linux/aos-communicationmanager/git",
        output=BUILDER_PROJECT + "/cm-startup-reconcile-" + attempt.name,
        relative=relative, testRelative=test_relative, before=before, after=before.replace(old, new),
        testBefore=tests, testAfter=test_after, compileBinary=compile_binary)
    atomic_json(attempt / "intent.json", dict(state="STARTED", startedAt=time.time(),
        sourceSha256=hashlib.sha256(before.encode()).hexdigest(), compileBinary=compile_binary))
    script = r'''
import hashlib,json,os,shlex,shutil,subprocess,sys
from pathlib import Path
c=json.load(sys.stdin); p=Path(c['work']); out=Path(c['output'])
assert not out.exists(), 'attempt exists; reconcile'
assert hashlib.sha256((p/'package/usr/bin/aos_cm_app').read_bytes()).hexdigest() == '3fffb5b89c742c233a634246c807d74e0bbc206dc143f8222c9b8283e0d78c98', 'warm Factory .34 package mismatch'
lib=p/'service-update-deps/aos_core_lib_cpp'
src=lib/c['relative']; test=lib/c['testRelative']
assert src.read_text()==c['before'], 'warm source mismatch'
assert test.read_text()==c['testBefore'], 'warm test baseline mismatch'
out.mkdir(mode=0o700)
cache=dict((x.split(':',1)[0],x.split('=',1)[1]) for x in (p/'build/CMakeCache.txt').read_text().splitlines() if ':' in x and '=' in x and not x.startswith(('#','//')))
run=(p/'temp/run.do_compile').read_text(); assert run.count('\ndo_compile\n')==1
env=os.environ.copy()
env['PATH']=shlex.split(next(x for x in run.splitlines() if x.startswith('export PATH=')))[1].split('=',1)[1]
testbuild=p/'service-update-launcher-tests'
def logged(name,args,allowed=(0,),**kw):
 with (out/(name+'.log')).open('wb') as log:
  result=subprocess.run(args,stdout=log,stderr=subprocess.STDOUT,timeout=300,env=env,**kw)
 if result.returncode not in allowed:
  print(json.dumps(dict(state='FAILED',stage=name,tail=(out/(name+'.log')).read_text()[-5000:])),flush=True)
  raise RuntimeError('stage failed: '+name)
 return result.returncode
def compile_test(name):
 logged(name,[cache['CMAKE_COMMAND'],'--build',str(testbuild),'--target','aos_core_cm_launcher_test','--parallel','6'])
def native(name,filters,allowed=(0,)):
 matches=list(testbuild.rglob('aos_core_cm_launcher_test')); assert len(matches)==1
 return logged(name,['sudo','-n',str(p/'recipe-sysroot/usr/lib/ld-linux-aarch64.so.1'),'--library-path',str(p/'recipe-sysroot/lib')+':'+str(p/'recipe-sysroot/usr/lib'),str(matches[0]),'--gtest_filter='+filters],allowed)
app_script=run.replace('\ndo_compile\n','\ncmake --build '+str(p/'build')+' --target aos_cm_app -- -j6\n')
binary_touched=False
try:
 test.write_text(c['testAfter'])
 logged('configure-tests',[cache['CMAKE_COMMAND'],'-S',str(lib),'-B',str(testbuild),'-G',cache['CMAKE_GENERATOR'],'-DCMAKE_MAKE_PROGRAM='+cache['CMAKE_MAKE_PROGRAM'],'-DWITH_TEST=ON','-DWITH_MBEDTLS=OFF','-DWITH_OPENSSL=OFF','-DFETCHCONTENT_FULLY_DISCONNECTED=ON','-DCMAKE_GTEST_DISCOVER_TESTS_DISCOVERY_MODE=PRE_TEST','-DCMAKE_TOOLCHAIN_FILE='+str(p/'toolchain.cmake')])
 compile_test('baseline-build')
 red=native('baseline-test','CMLauncherTest.RebalancingWithStoredNotScheduledInstances',(0,1))
 assert red==1 and 'unexpected startup stop:' in (out/'baseline-test.log').read_text(), 'exact startup fault not reproduced; stop proof'
 src.write_text(c['after'])
 compile_test('candidate-build')
 native('candidate-test','CMLauncherTest.*:ServiceReconciliation/*')
 manifest=dict(state='REGRESSION_PASSED',tests=[line for line in (out/'candidate-test.log').read_text().splitlines() if '[  PASSED  ]' in line],baselineFailsOnUnexpectedStop=True)
 if c['compileBinary']:
  binary_touched=True
  logged('cm-build',['bash','-s'],input=app_script.encode())
  binary=out/'aos_cm_app'; shutil.copyfile(p/'build/src/cm/app/aos_cm_app',binary)
  subprocess.run([cache['CMAKE_STRIP'],'--strip-unneeded',str(binary)],check=True,capture_output=True,env=env)
  raw=binary.read_bytes(); assert raw[:6]==b'\x7fELF\x02\x01' and raw[18:20]==b'\xb7\x00'
  manifest.update(state='BUILT_TESTED',sha256=hashlib.sha256(raw).hexdigest(),size=len(raw))
finally:
 src.write_text(c['before']); test.write_text(c['testBefore'])
 if binary_touched: logged('restore-cm-cache',['bash','-s'],input=app_script.encode())
manifest.update(warmSourcesRestored=True,imageBuilt=False)
(out/'manifest.json').write_text(json.dumps(manifest))
print(json.dumps(manifest),flush=True)
'''
    try:
        builder("test", "start")
        ssh = builder_ssh()
        deadline = time.monotonic() + 90
        while subprocess.run(ssh + ["true"], capture_output=True, timeout=8).returncode:
            if time.monotonic() > deadline:
                raise EnvironmentError("CM_STARTUP_BUILDER_BOOT_TIMEOUT")
            time.sleep(1)
        print("Test: targeted native CM startup red/green test; VM and Cloud unchanged", file=sys.stderr, flush=True)
        result = subprocess.run(ssh + ["python3 -c " + shlex.quote(script)], input=json.dumps(payload).encode(),
            capture_output=True, timeout=1500)
        (attempt / "build.log").write_bytes(result.stdout + result.stderr)
        if result.returncode:
            raise EnvironmentError("CM_STARTUP_PROOF_FAILED:" + str(attempt / "build.log"))
        manifest = json.loads(result.stdout)
        for name in ("baseline-test.log", "candidate-test.log"):
            raw = subprocess.check_output(ssh + ["cat " + payload["output"] + "/" + name], timeout=20)
            (attempt / name).write_bytes(raw)
        if compile_binary:
            raw = subprocess.check_output(ssh + ["cat " + payload["output"] + "/aos_cm_app"], timeout=30)
            if hashlib.sha256(raw).hexdigest() != manifest["sha256"]:
                raise EnvironmentError("CM_STARTUP_TRANSFER_DIGEST_MISMATCH")
            (attempt / "aos_cm_app").write_bytes(raw)
        atomic_json(attempt / "manifest.json", manifest)
        return dict(manifest, artifact=str(attempt))
    finally:
        builder("test", "stop")


def apply_cm_startup(environment, target):
    """One reversible binary replacement on the preserved, explicitly owned Test."""
    from .environment import JOURNAL, atomic_json, factory_for
    from .status import read_json, now
    from .source import SourceDriver
    from .vm import VMService
    if target != "test":
        raise EnvironmentError("CM_STARTUP_RECONCILIATION_TEST_ONLY")
    artifact = ARTIFACT.with_name("cm-startup-reconcile-20260917") / "proof-wfi3wx05"
    expected = "0c491e8a744458b01bf81126f99ecdab3367795f757c419b92ab338b6518da23"
    manifest = read_json(artifact / "manifest.json")
    raw = (artifact / "aos_cm_app").read_bytes()
    if (manifest.get("state") != "BUILT_TESTED" or not manifest.get("baselineFailsOnUnexpectedStop")
            or manifest.get("sha256") != expected or hashlib.sha256(raw).hexdigest() != expected):
        raise EnvironmentError("CM_STARTUP_QUALIFIED_BINARY_REQUIRED")
    with environment._writer():
        state = read_json(environment.root / JOURNAL)
        vehicle = state.get("vehicles", {}).get("test", {})
        if (vehicle.get("localVmId") != "363d8b2d-187f-4713-8af1-5cf9aa598177"
                or vehicle.get("unitId") != "db0f8a34-5adf-4dec-b0fb-9c4f5b15c905"
                or factory_for(state, "test").get("sha256") !=
                "fac0cccfd5c4ededaf068bbd574b0f0a83b9af1b94f1df94022fa0ca5893eeeb"):
            raise EnvironmentError("CM_STARTUP_REQUIRES_PRESERVED_TEST_34")
        if state.get("cmStartupProof"):
            raise EnvironmentError("CM_STARTUP_EXISTING_ATTEMPT_RECONCILE")
        record = dict(state="STARTED", startedAt=now(), sha256=expected)
        state["cmStartupProof"] = record
        atomic_json(environment.root / JOURNAL, state)
        driver = SourceDriver(VMService(environment))
        try:
            with driver.operation(timeout=65):
                result = driver.guest(state, "test", "component-cm-apply", target="test",
                    proof="factory34-startup-reconcile", sha256=expected,
                    binary=base64.b64encode(gzip.compress(raw, mtime=0)).decode())
        except (OSError, ValueError, EnvironmentError, subprocess.SubprocessError):
            record.update(state="RECONCILIATION_REQUIRED")
            atomic_json(environment.root / JOURNAL, state)
            raise EnvironmentError("CM_STARTUP_ATTEMPT_RECONCILIATION_REQUIRED") from None
        record.update(state="COMPLETED", result=result, confirmedAt=now())
        atomic_json(environment.root / JOURNAL, state)
        return result


def builder(target, action):
    """Reuse the established Builder lifecycle, not another shell helper."""
    if target != "test" or action not in ("start", "stop"):
        raise EnvironmentError("SM_QUALIFICATION_TEST_ONLY")
    script = Path.home() / "OpenAI/aosedge-sdv-demo/scripts/r6-1-builder"
    # 10023 belongs to Production; the dedicated Builder port is 10024.
    with contextlib.ExitStack() as stack:
        previous = os.environ.get("R61_BUILDER_SSH_PORT")
        os.environ["R61_BUILDER_SSH_PORT"] = "10024"
        stack.callback(lambda: os.environ.pop("R61_BUILDER_SSH_PORT", None)
                       if previous is None else os.environ.__setitem__("R61_BUILDER_SSH_PORT", previous))
        loader = importlib.machinery.SourceFileLoader("democtl_builder_adapter", str(script))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        module = importlib.util.module_from_spec(spec)
        loader.exec_module(module)
        try:
            with contextlib.redirect_stdout(sys.stderr):
                module.start(False) if action == "start" else module.stop()
        except module.BuilderError as error:
            raise EnvironmentError("SM_BUILDER:" + str(error)) from None
    return dict(target=target, builder="STARTED" if action == "start" else "STOPPED",
                sshPort=10024, demoVmMutation=False, cloudMutation=False)


def register_factory_support(destination, version, compatibility):
    """Annotate an existing producer manifest, never touch immutable image bytes."""
    from .environment import atomic_json
    from .images import ImageCatalog
    from .status import read_json
    try:
        manifest_path = destination / "manifest.json"
        info = manifest_path.lstat()
        if (destination.is_symlink() or not stat.S_ISREG(info.st_mode)
                or info.st_nlink != 1 or info.st_uid != os.getuid()):
            raise EnvironmentError("FACTORY_EXISTING_MANIFEST_NOT_OWNED")
        catalog = ImageCatalog(root=destination.parents[2], workspace=FACTORY_SOURCE.parent)
        record = catalog.resolve(version + "/main-qemuarm64")
        if (record.path.resolve() != (destination / "main-qemuarm64.img").resolve() or record.image_format != "raw"
                or record.path.stat().st_uid != os.getuid()):
            raise EnvironmentError("FACTORY_EXISTING_IMAGE_BINDING_MISMATCH")
        manifest = read_json(manifest_path, limit=262144)
        if manifest.get("source") != dict(repository="aos-vehicle-platform", revision=compatibility["sourceRevision"]):
            raise EnvironmentError("FACTORY_EXISTING_SOURCE_BINDING_MISMATCH")
        for source in record.metadata_sources:
            producer = catalog.root / source
            if producer.is_symlink():
                raise EnvironmentError("FACTORY_EXISTING_MANIFEST_NOT_OWNED")
            metadata = read_json(producer, limit=262144)
            declared = metadata.get("demoCompatibility")
            if declared is not None and (declared != compatibility or metadata.get("source") != manifest["source"]):
                raise EnvironmentError("FACTORY_EXISTING_COMPATIBILITY_CONFLICT")
        no_op = manifest.get("demoCompatibility") == compatibility
        if not no_op:
            manifest["demoCompatibility"] = compatibility
            atomic_json(manifest_path, manifest)
            manifest_path.chmod(stat.S_IMODE(info.st_mode))
        catalog.component_support(record.selector, record.sha256,
            compatibility["componentType"], compatibility["supportedReadPaths"])
        return dict(metadataOnly=True, noOp=no_op, rebuilt=False, imageBytesChanged=False,
            digestChecked=False, image=record.selector, sha256=record.sha256,
            qualificationState=manifest.get("state"), demoCompatibility=compatibility)
    except EnvironmentError:
        raise
    except (OSError, ValueError, KeyError, TypeError):
        raise EnvironmentError("FACTORY_EXISTING_METADATA_UNAVAILABLE") from None


def stage_mainline_factory_gates(ssh, remote, project, source, suffix="37"):
    """Export committed test tooling separately from the immutable Platform pin."""
    if suffix not in ("37", "38"):
        raise EnvironmentError("FACTORY_MAINLINE_GATE_VERSION_UNSUPPORTED")
    solution = Path(__file__).resolve().parents[4]
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=solution):
        raise EnvironmentError("FACTORY_COMMITTED_QUALIFICATION_TOOLS_REQUIRED")
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=solution).decode().strip()
    script = "apps/demo-orchestrator/src/aosedge_demo_orchestrator/factory_mainline_gates.py"
    harness = "tests/upstream/cm-lock-harness"
    root = project + "/factory" + suffix + "-gates-" + revision
    archive = subprocess.check_output(["git", "archive", revision, script,
                                      harness + "/CMakeLists.txt", harness + "/probe.cpp"], cwd=solution)
    remote("mkdir -p " + shlex.quote(root))
    subprocess.run(ssh + ["tar -xf - -C " + shlex.quote(root)], input=archive, check=True, timeout=30)
    conf = root + "/build.conf"
    text = ('require ' + source + '/qualification/factory-' + suffix + '.conf\n'
            'BB_NUMBER_THREADS = "2"\nPARALLEL_MAKE = "-j 4"\n')
    remote("python3 -c " + shlex.quote("from pathlib import Path; Path(%r).write_text(%r)" % (conf, text)))
    evidence = root + "/evidence-" + str(time.time_ns())
    return dict(command="python3 " + shlex.quote(root + "/" + script), conf=conf,
                harness=root + "/" + harness, evidence=evidence, solutionRevision=revision)


def build_factory(version, metadata_only=False):
    """The release build is a Demo Control operation, not an operator script.

    Export only committed Platform source, reuse the warm offline build tree,
    gate image construction on the new configuration test and package QA, then
    reuse the existing Rouge disk description. Never alter a published image.
    """
    if version not in FACTORY_RELEASES:
        raise EnvironmentError("FACTORY_BUILD_NOT_AUTHORIZED")
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=FACTORY_SOURCE):
        raise EnvironmentError("FACTORY_COMMITTED_SOURCE_REQUIRED")
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=FACTORY_SOURCE).decode().strip()
    if revision != FACTORY_RELEASES[version]:
        raise EnvironmentError("FACTORY_SOURCE_REVISION_MISMATCH")
    compatibility = factory_component_support(revision)
    destination = ARTIFACT.parents[1] / "factory-images" / version
    if metadata_only:
        return register_factory_support(destination, version, compatibility)
    if destination.exists():
        raise EnvironmentError("FACTORY_ARTIFACT_EXISTS_RECONCILE_WITHOUT_REBUILD")
    if shutil.disk_usage(destination.parent).free < 60 * 1024**3:
        raise EnvironmentError("FACTORY_HOST_FREE_SPACE_BELOW_60_GIB")
    project = str(Path(BUILDER_PROJECT).parent)
    source = BUILDER_PROJECT + "/aos-vehicle-platform-" + revision
    ssh = builder_ssh()
    def remote(command, timeout=60, capture=True):
        result = subprocess.run(ssh + ["bash -lc " + shlex.quote(command)], timeout=timeout,
                                stdout=subprocess.PIPE if capture else sys.stderr, stderr=sys.stderr, check=True)
        return result.stdout.decode() if capture else ""
    def stage(message):
        print("Factory ." + version.rsplit(".", 1)[1] + ": " + message, file=sys.stderr, flush=True)
    try:
        # The same established Builder adapter owns start/stop and disk guards.
        builder("test", "start")
        stage("waiting for pinned key-only Builder SSH; 90-second boot budget")
        deadline = time.monotonic() + 90
        while True:
            try:
                ready = subprocess.run(ssh + ["true"], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=7)
            except subprocess.TimeoutExpired:
                ready = subprocess.CompletedProcess(ssh, 255, stderr=b"SSH boot probe timed out")
            if ready.returncode == 0:
                break
            if b"Host key verification failed" in ready.stderr or b"Permission denied" in ready.stderr:
                raise EnvironmentError("FACTORY_BUILDER_SSH_TRUST_OR_AUTH_FAILED")
            if time.monotonic() >= deadline:
                raise EnvironmentError("FACTORY_BUILDER_SSH_BOOT_TIMEOUT")
            time.sleep(1)
        free = int(remote("df -Pk " + BUILDER_PROJECT + " | tail -1 | awk '{print $4}'").strip()) * 1024
        if free < 60 * 1024**3:
            raise EnvironmentError("FACTORY_BUILDER_FREE_SPACE_BELOW_60_GIB")
        graph = remote("cd " + project + "; ninja -t commands main-qemuarm64.img")
        assembly = [shlex.split(line) for line in graph.splitlines()
                    if line.strip() and Path(shlex.split(line)[0]).name == "rouge"]
        if len(assembly) != 1 or "main-qemuarm64.img" not in assembly[0]:
            raise EnvironmentError("FACTORY_PINNED_ROUGE_COMMAND_UNRESOLVED")
        archive = subprocess.check_output(["git", "archive", revision], cwd=FACTORY_SOURCE)
        remote("mkdir -p " + source)
        subprocess.run(ssh + ["tar -xf - -C " + source], input=archive, check=True, timeout=30, stdout=sys.stderr)
        # Change only the Platform layer binding. All other layers and caches
        # retain their existing pinned configuration; preserve the old checkout.
        layer_update = "from pathlib import Path\n" + (
            "p=Path(%r); s=p.read_text(); import re\n"
            "s,n=re.subn(r'aos-vehicle-platform(?:-[0-9a-f]{40})?/meta-aos-vehicle-platform', %r, s)\n"
            "assert n == 1, 'Platform layer binding must be unique'\n"
            "p.write_text(s)\n") % (BUILDER_PROJECT + "/build-main/conf/bblayers.conf",
                                    Path(source).name + "/meta-aos-vehicle-platform")
        remote("python3 -c " + shlex.quote(layer_update))
        prefix = "cd " + BUILDER_PROJECT + "; . poky/oe-init-build-env build-main >/dev/null; "
        suffix = version.rsplit(".", 1)[1]
        flags = " -R " + source + "/qualification/factory-" + suffix + ".conf "
        mainline = None
        if suffix in ("37", "38"):
            mainline = stage_mainline_factory_gates(ssh, remote, project, source, suffix)
            flags = " -R " + shlex.quote(mainline["conf"]) + " "
            stage("verify effective mainline pins and offline guards before compilation")
            print(remote(prefix + mainline["command"] + " preflight --conf " +
                         shlex.quote(mainline["conf"]), timeout=600), file=sys.stderr, flush=True)
        managers = "aos-servicemanager" + (" aos-communicationmanager" if suffix in ("32", "33", "34", "35", "36", "37", "38") else "")
        if suffix in ("34", "35", "36", "37", "38"):
            managers += " aos-iamanager"
        targets = managers + (" aos-kuksa-auth-compat" if suffix in ("34", "35", "36", "37", "38") else "")
        if suffix == "38":
            # Compile/package the proven policy delta before image construction.
            targets += " refpolicy-aos"
        stage("compile the proven manager corrections from committed source (offline)")
        remote(prefix + "bitbake" + flags + "-c compile " + targets, timeout=1200, capture=False)
        work = BUILDER_PROJECT + "/build-main/tmp/work/cortexa57-aos-linux/aos-servicemanager/git"
        test = work + "/build/src/sm/launcher/runtimes/systemd-slot-component/tests/aos_sm_runtimes_systemdslotcomponent_test"
        loader = work + "/recipe-sysroot/usr/lib/ld-linux-aarch64.so.1"
        libs = work + "/recipe-sysroot/lib:" + work + "/recipe-sysroot/usr/lib"
        stage("run five factory-placeholder, persistent-input and profile regressions")
        test_log = remote("sudo -n " + loader + " --library-path " + libs + " " + test +
            " --gtest_filter='*FactoryDemoInputs*:*AcceptsOnlyExplicitDemoFreshnessProfile*:*StartsWithAnEmptyPersistentStore:*FactoryPlaceholder*'", timeout=30)
        print(test_log, file=sys.stderr, flush=True)
        if "[  PASSED  ] 5 tests." not in test_log:
            raise EnvironmentError("FACTORY_EXPECTED_FIVE_TESTS_NOT_EXECUTED")
        mainline_root = BUILDER_PROJECT + "/build-main/tmp/work/cortexa57-aos-linux"
        if mainline:
            stage("run production-toolchain mainline lifecycle, crypto, runtime and lock regressions")
            mainline_log = remote(mainline["command"] + " native --root " + shlex.quote(mainline_root)
                + " --evidence " + shlex.quote(mainline["evidence"])
                + " --lock-source " + shlex.quote(mainline["harness"])
                + " --factory-suffix " + suffix, timeout=2400)
            print(mainline_log, file=sys.stderr, flush=True)
            test_log += mainline_log
        if suffix in ("35", "36"):
            stage("compile and run the CM startup, reconciliation and applicable storage regressions")
            cm_work = BUILDER_PROJECT + "/build-main/tmp/work/cortexa57-aos-linux/aos-communicationmanager/git"
            cm_tests = r'''
import os, pathlib, shlex, subprocess
p=pathlib.Path(WORK)
cache=dict((x.split(':',1)[0],x.split('=',1)[1]) for x in (p/'build/CMakeCache.txt').read_text().splitlines() if ':' in x and '=' in x and not x.startswith(('#','//')))
env=os.environ.copy()
run=(p/'temp/run.do_compile').read_text()
env['PATH']=shlex.split(next(x for x in run.splitlines() if x.startswith('export PATH=')))[1].split('=',1)[1]
b=p/'service-update-launcher-tests'
subprocess.run([cache['CMAKE_COMMAND'],'-S',str(p/'service-update-deps/aos_core_lib_cpp'),'-B',str(b),'-G',cache['CMAKE_GENERATOR'],'-DCMAKE_MAKE_PROGRAM='+cache['CMAKE_MAKE_PROGRAM'],'-DWITH_TEST=ON','-DWITH_MBEDTLS=OFF','-DWITH_OPENSSL=OFF','-DFETCHCONTENT_FULLY_DISCONNECTED=ON','-DCMAKE_GTEST_DISCOVER_TESTS_DISCOVERY_MODE=PRE_TEST','-DCMAKE_TOOLCHAIN_FILE='+str(p/'toolchain.cmake')],env=env,check=True)
subprocess.run([cache['CMAKE_COMMAND'],'--build',str(b),'--target','aos_core_cm_launcher_test','--parallel','6'],env=env,check=True)
tests=list(b.rglob('aos_core_cm_launcher_test')); assert len(tests)==1
subprocess.run(['sudo','-n',str(p/'recipe-sysroot/usr/lib/ld-linux-aarch64.so.1'),'--library-path',str(p/'recipe-sysroot/lib')+':'+str(p/'recipe-sysroot/usr/lib'),str(tests[0]),'--gtest_filter=CMLauncherTest.*:ServiceReconciliation/*:CMStorage*.*:MissingImageAndExpiry/*'],env=env,check=True)
'''.replace("WORK", repr(cm_work), 1)
            cm_log = remote("python3 -c " + shlex.quote(cm_tests), timeout=300)
            expected_cm_tests = 45 if suffix == "36" else 19
            if "[  PASSED  ] " + str(expected_cm_tests) + " tests." not in cm_log:
                raise EnvironmentError("FACTORY_CM_STARTUP_REGRESSIONS_INCOMPLETE")
            test_log += cm_log
        if suffix in ("34", "35", "36", "37", "38"):
            stage("verify uniform CM/SM/IAM permission capacity and native KAC/Provider tests")
            for recipe in managers.split():
                manager_build = BUILDER_PROJECT + "/build-main/tmp/work/cortexa57-aos-linux/" + recipe + "/git/build"
                check = ("from pathlib import Path; root=Path(%r); "
                    "files=[p for p in root.rglob('flags.make') if 'CXX_FLAGS =' in p.read_text()]; "
                    "assert files; assert all('-DAOS_CONFIG_TYPES_FUNCTION_LEN=256' in p.read_text() for p in files); "
                    "print('Uniform permission key capacity 256: PASS')") % manager_build
                print(remote("python3 -c " + shlex.quote(check)), file=sys.stderr, flush=True)
            kac_root = BUILDER_PROJECT + "/build-main/tmp/work/cortexa57-aos-linux/aos-kuksa-auth-compat"
            candidates = remote("find " + kac_root + " -path '*/build/provider-tests' -type f").splitlines()
            if len(candidates) != 1:
                raise EnvironmentError("FACTORY_KAC_TEST_BUILD_NOT_UNIQUE")
            kac_work = str(Path(candidates[0]).parents[1])
            kac_loader = kac_work + "/recipe-sysroot/usr/lib/ld-linux-aarch64.so.1"
            kac_libs = kac_work + "/recipe-sysroot/lib:" + kac_work + "/recipe-sysroot/usr/lib"
            for executable in ("kac-tests", "provider-tests", "verifier-prepare-tests"):
                test_log += remote(kac_loader + " --library-path " + kac_libs + " " + kac_work + "/build/" + executable, timeout=60)
        stage("package the managers with package QA")
        remote(prefix + "bitbake" + flags + targets, timeout=1200, capture=False)
        if suffix in ("32", "33", "34", "35", "36", "37", "38"):
            # Verify final package input after native do_update_config, not the
            # intermediate resource file that do_install initially creates.
            package_check = (
                "import json; from pathlib import Path; "
                "root=Path(%r); src=Path(%r); "
                "resources=json.loads((root/'etc/aos/resources.cfg').read_text()); "
                "names=[x['name'] for x in resources]; "
                "assert len(names)==len(set(names)); "
                "assert {'kuksa','kuksa-auth-client','brake-runtime-inputs','tire-runtime-inputs'} <= set(names); "
                "assert (root/'usr/libexec/aos-demo-service-inputs.py').read_bytes()==(src/'aos-demo-service-inputs.py').read_bytes(); "
                "assert (root/'etc/systemd/system/aos-sm.service.d/40-aos-demo-service-inputs.conf').read_bytes()==(src/'40-aos-demo-service-inputs.conf').read_bytes(); "
                "print('Factory service-input package: PASS')"
            ) % (work + "/image", source + "/meta-aos-vehicle-platform/recipes-aos/aos-servicemanager/files")
            print(remote("python3 -c " + shlex.quote(package_check)), file=sys.stderr, flush=True)
        if suffix in ("33", "34", "35", "36", "37", "38"):
            cm_work = BUILDER_PROJECT + "/build-main/tmp/work/cortexa57-aos-linux/aos-communicationmanager/git"
            cm_check = ("import json; from pathlib import Path; "
                "config=json.loads(Path(%r).read_text()); "
                "assert config['idleFullStatusInterval']=='60s'; "
                "print('Factory CM idle full status: 60s, PASS')") % (cm_work + "/image/etc/aos/cm.cfg")
            print(remote("python3 -c " + shlex.quote(cm_check)), file=sys.stderr, flush=True)
        if mainline:
            print(remote(mainline["command"] + " package --root " + shlex.quote(mainline_root)),
                  file=sys.stderr, flush=True)
        stage("construct the Factory filesystem from pinned sources")
        remote(prefix + "bitbake" + flags + "aos-image-vm", timeout=2400, capture=False)
        output = "main-qemuarm64-factory-" + suffix + ".img"
        assembly = [output if item == "main-qemuarm64.img" else item for item in assembly[0]]
        assembly[0] = "/home/yocto/.local/bin/rouge"
        stage("assemble the same six-partition disk layout")
        remote("cd " + project + "; " + shlex.join(assembly), timeout=600, capture=False)
        remote_image = project + "/" + output
        remote_sha = remote("sha256sum " + remote_image, timeout=120).split()[0]
        stage("transfer and freeze the new image; verify the transfer digest once")
        destination.mkdir()
        image = destination / "main-qemuarm64.img"
        digest = hashlib.sha256()
        with image.open("xb") as stream:
            process = subprocess.Popen(ssh + ["cat " + remote_image], stdout=subprocess.PIPE, stderr=sys.stderr)
            with process.stdout:
                while data := process.stdout.read(4 * 1024**2):
                    stream.write(data)
                    digest.update(data)
            if process.wait(timeout=15):
                raise EnvironmentError("FACTORY_TRANSFER_FAILED_PARTIAL_ARTIFACT_RETAINED")
        if digest.hexdigest() != remote_sha:
            raise EnvironmentError("FACTORY_TRANSFER_DIGEST_MISMATCH")
        image.chmod(0o444)
        manifest = dict(schemaVersion=1, state="BUILT_NOT_LIVE_QUALIFIED", demoCompatibility=compatibility,
            source=dict(repository="aos-vehicle-platform", revision=revision),
            factoryImage=dict(version=version, architecture="main-qemuarm64", path="main-qemuarm64.img",
                              byteLength=image.stat().st_size, sha256=remote_sha, format="raw"),
            build=dict(offline=True, targetedTests="PASS", packageQa="PASS", imageQa="PASS",
                       hostTransferSha256Matched=True, builderSource=source, assemblyCommand=assembly))
        if mainline:
            summary = json.loads(remote("cat " + shlex.quote(mainline["evidence"] + "/summary.json")))
            manifest["build"]["mainlineQualification"] = dict(
                solutionRevision=mainline["solutionRevision"], builderEvidence=mainline["evidence"],
                native=summary,
                knownPackageWarnings="buildpaths: recipe-private upstream source paths; no QA bypass")
            # Preserve compact test XML/logs across Builder shutdown without
            # exporting root-owned synthetic fixtures or any runtime state.
            names = remote("python3 -c " + shlex.quote(
                "from pathlib import Path; p=Path(%r); print('\\n'.join(sorted(x.name for x in p.iterdir() "
                "if x.is_file() and x.suffix in ('.xml','.log','.json'))))" % mainline["evidence"])).splitlines()
            evidence_bytes = subprocess.check_output(ssh + ["tar -cf - -C " +
                shlex.quote(mainline["evidence"]) + " " + shlex.join(names)], timeout=60)
            (destination / "mainline-tests.tar").write_bytes(evidence_bytes)
        (destination / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        (destination / "configuration-tests.log").write_text(test_log)
        return manifest
    except EnvironmentError:
        raise
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        raise EnvironmentError("FACTORY_BUILD_FAILED:" + type(error).__name__) from None
    finally:
        builder("test", "stop")
