# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Bounded Test-only SM qualification operations owned by Demo Control."""

import contextlib
import base64
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

from .environment import EnvironmentError

SOURCE = Path.home() / "OpenAI/aos-vehicle-platform"
SM_REVISION = "0e645a549b299dfa88ae7fc3725a1c1dee2bf3a1"
SM_TEST_VM = "d53d05cd-4c46-49c9-a896-534b23b88273"
SM_TEST_UNIT = "2a29c145-bbd1-4494-a0e5-d4b79e6a9db5"
FACTORY_SOURCE = Path.home() / "OpenAI/aos-vehicle-platform"
FACTORY_VERSION = "6.1.1-maninblack.31"
FACTORY_REVISION = "0bed8b3769b09fbe685ed599ca8d10e6594fbe53"
RELATIVE = "meta-aos-vehicle-platform/recipes-aos/aos-servicemanager/files/systemd-slot-component"
BUILDER_PROJECT = "/home/yocto/r61-build/project/yocto"
ARTIFACT = Path.home() / "OpenAI/demo-artifacts/aosedge-sdv-demo/runtime-proofs/sm-demo-clock-skew"
FILES = ("config.hpp", "config.cpp", "safestop.hpp", "safestop.cpp", "runtime.hpp", "runtime.cpp",
         "tests/safestop.cpp", "tests/runtime.cpp")


def factory_component_support(revision):
    """Producer metadata for the exact supported source, not live qualification."""
    from .components import COMPONENT
    if revision != FACTORY_REVISION:
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


def apply_test(environment, target):
    from .environment import JOURNAL, atomic_json
    from .status import read_json, now
    from .vm import VMService
    from .source import SourceDriver
    if target != "test":
        raise EnvironmentError("SM_QUALIFICATION_TEST_ONLY")
    manifest = read_json(ARTIFACT / "manifest.json")
    raw = (ARTIFACT / "aos-sm").read_bytes()
    if (not manifest.get("testsPassed") or manifest.get("profile") != "demo-5s"
            or manifest.get("sourceRevision") != SM_REVISION
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
        record = state.setdefault("smDemoProof", {})
        record.update(state="ATTEMPT_STARTED", startedAt=now(), binarySha256=manifest["executableSha256"])
        atomic_json(environment.root / JOURNAL, state)
        driver = SourceDriver(VMService(environment))
        try:
            with driver.operation(timeout=60):
                observed = driver.guest(state, "test", "component-sm-status")
                result = driver.guest(state, "test", "component-sm-apply", target="test",
                    proof="demo-clock-skew",
                    binary="" if observed["binarySha256"] == manifest["executableSha256"] else base64.b64encode(raw).decode(),
                    sha256=manifest["executableSha256"])
                # systemd clears service credentials on restart. Restore only
                # the already selected Test's public trust/binding inputs.
                if not result.get("persistentFactoryInputs") and not result.get("noOp") and state.get("currentVehicle") == "test":
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


def build(target, compile_source=True):
    """Compile the pinned Test timing correction, native-test, export and stop."""
    if target != "test":
        raise EnvironmentError("SM_QUALIFICATION_TEST_ONLY")
    if ARTIFACT.exists():
        raise EnvironmentError("SM_PROOF_ARTIFACT_ALREADY_EXISTS")
    expected = SM_REVISION
    if shutil.disk_usage(ARTIFACT.parent).free < 60 * 1024**3:
        raise EnvironmentError("SM_HOST_FREE_SPACE_BELOW_60_GIB")
    ssh = builder_ssh()
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=SOURCE).decode().strip()
    if revision != expected or subprocess.check_output(["git", "status", "--porcelain"], cwd=SOURCE):
        raise EnvironmentError("SM_PINNED_COMMITTED_SOURCE_REQUIRED")
    try:
        builder("test", "start")
        print("Test SM: waiting for Builder SSH; 90-second boot budget", file=sys.stderr, flush=True)
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
        data = io.BytesIO()
        inputs = {}
        with tarfile.open(fileobj=data, mode="w") as archive:
            for name in FILES:
                path = SOURCE / RELATIVE / name
                inputs[name] = hashlib.sha256(path.read_bytes()).hexdigest()
                archive.add(path, arcname=RELATIVE + "/" + name, recursive=False)
        if compile_source:
            # Isolate proof sources; keep the immutable .31 source snapshot intact.
            identity = hashlib.sha256(json.dumps(inputs, sort_keys=True).encode()).hexdigest()[:40]
            proof_source = BUILDER_PROJECT + "/aos-vehicle-platform-" + identity
            archive = subprocess.check_output(["git", "archive", expected], cwd=SOURCE)
            subprocess.run(ssh + ["mkdir -p " + proof_source], check=True, timeout=15)
            subprocess.run(ssh + ["tar -xf - -C " + proof_source], input=archive, check=True, timeout=30)
            subprocess.run(ssh + ["tar -xf - -C " + proof_source],
                           input=data.getvalue(), check=True, timeout=20, stdout=sys.stderr)
            layer_update = ("from pathlib import Path; import re; p=Path(%r); "
                "s,n=re.subn(r'aos-vehicle-platform(?:-[0-9a-f]{40})?/meta-aos-vehicle-platform', %r, p.read_text()); "
                "assert n == 1; p.write_text(s)") % (BUILDER_PROJECT + "/build-main/conf/bblayers.conf",
                    Path(proof_source).name + "/meta-aos-vehicle-platform")
            subprocess.run(ssh + ["python3 -c " + shlex.quote(layer_update)], check=True, timeout=15)
            print("Test SM: offline recipe compile; no image build", file=sys.stderr, flush=True)
            command = "cd " + BUILDER_PROJECT + "; . poky/oe-init-build-env build-main >/dev/null; bitbake -R " + proof_source + "/qualification/factory-31.conf -c compile aos-servicemanager"
            subprocess.run(ssh + ["bash -lc " + __import__("shlex").quote(command)],
                           check=True, timeout=1200, stdout=sys.stderr)
        work = BUILDER_PROJECT + "/build-main/tmp/work/cortexa57-aos-linux/aos-servicemanager/git"
        test = work + "/build/src/sm/launcher/runtimes/systemd-slot-component/tests/aos_sm_runtimes_systemdslotcomponent_test"
        loader = work + "/recipe-sysroot/usr/lib/ld-linux-aarch64.so.1"
        libs = work + "/recipe-sysroot/lib:" + work + "/recipe-sysroot/usr/lib"
        test_filter = ("SafeStopEvaluatorTest.*:*RequiresTheFixedBootstrapContract:"
            "*AcceptsOnlyExplicitDemoFreshnessProfile:*FactoryDemoInputsRespectPersistentRole:"
            "*StartsWithAnEmptyPersistentStore:*FactoryPlaceholder*:"
            "*StopMakesTheComponentUnavailable:*StopCancellationNeverReturnsSuccess:*StopMissingComponentIsIdempotent")
        print("Test SM: executing native timing, role, physical-gate and stop regressions", file=sys.stderr, flush=True)
        result = subprocess.run(ssh + ["sudo -n " + loader + " --library-path " + libs + " " + test + " --gtest_filter=" + __import__("shlex").quote(test_filter)],
                                timeout=30, capture_output=True)
        print(result.stdout.decode(), file=sys.stderr, flush=True)
        print(result.stderr.decode(), file=sys.stderr, flush=True)
        ARTIFACT.with_suffix(".test.log").write_bytes(result.stdout + result.stderr)
        if result.returncode:
            raise EnvironmentError("SM_TARGETED_TEST_FAILED:" + str(result.returncode))
        required_tests = ("DemoFutureSkewIsBoundedAtAcquisitionAndTheGate",
            "StandardStillRejectsAnyFutureAcquisitionOrGate", "DemoAgeAllowancePreservesOtherGates",
            "FactoryDemoInputsRespectPersistentRole", "StopCancellationNeverReturnsSuccess")
        if not re.search(rb"\[  PASSED  \] [1-9][0-9]* tests\.", result.stdout) or any(
                not re.search(rb"\[       OK \] [^\n]*\." + name.encode() + rb" \(", result.stdout)
                for name in required_tests):
            raise EnvironmentError("SM_REQUIRED_NATIVE_REGRESSIONS_NOT_EXECUTED")
        binaries = subprocess.check_output(ssh + ["find " + work + "/build -type f -name aos_sm_app"], timeout=20).decode().splitlines()
        if len(binaries) != 1:
            raise EnvironmentError("SM_BINARY_IDENTITY_UNRESOLVED")
        binary = subprocess.check_output(ssh + ["cat " + binaries[0]], timeout=30)
        if binary[:5] != b"\x7fELF\x02" or binary[18:20] != b"\xb7\x00":
            raise EnvironmentError("SM_BINARY_NOT_ARM64_ELF")
        ARTIFACT.mkdir(parents=True)
        (ARTIFACT / "aos-sm").write_bytes(binary)
        (ARTIFACT / "aos-sm").chmod(0o444)
        (ARTIFACT / "tests.log").write_bytes(result.stdout)
        manifest = dict(baseRevision=FACTORY_REVISION, sourceRevision=expected, sourceSha256=inputs, executableSha256=hashlib.sha256(binary).hexdigest(),
                        profile="demo-5s", defaultMaximumSourceAgeMs=250, demoMaximumSourceAgeMs=5000,
                        demoMaximumFutureSkewMs=5000, demoReadTimeoutMs=1000, standardReadTimeoutMs=250,
                        offline=True, imageBuild=False, testsPassed=True, testFilter=test_filter, guestApplied=False)
        (ARTIFACT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        return dict(artifact=str(ARTIFACT), **manifest)
    except subprocess.CalledProcessError:
        raise EnvironmentError("SM_BUILD_OR_TEST_FAILED") from None
    finally:
        builder("test", "stop")


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


def build_factory(version, metadata_only=False):
    """The release build is a Demo Control operation, not an operator script.

    Export only committed Platform source, reuse the warm offline build tree,
    gate image construction on the new configuration test and package QA, then
    reuse the existing Rouge disk description. Never alter a published image.
    """
    if version != FACTORY_VERSION:
        raise EnvironmentError("FACTORY_BUILD_NOT_AUTHORIZED")
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=FACTORY_SOURCE):
        raise EnvironmentError("FACTORY_COMMITTED_SOURCE_REQUIRED")
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=FACTORY_SOURCE).decode().strip()
    if revision != FACTORY_REVISION:
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
        print("Factory .31: " + message, file=sys.stderr, flush=True)
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
        flags = " -R " + source + "/qualification/factory-31.conf "
        stage("compile the proven SM correction from committed source (offline)")
        remote(prefix + "bitbake" + flags + "-c compile aos-servicemanager", timeout=1200, capture=False)
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
        stage("package SM with package QA")
        remote(prefix + "bitbake" + flags + "aos-servicemanager", timeout=1200, capture=False)
        stage("construct the Factory filesystem from pinned sources")
        remote(prefix + "bitbake" + flags + "aos-image-vm", timeout=2400, capture=False)
        output = "main-qemuarm64-factory-31.img"
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
        (destination / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        (destination / "configuration-tests.log").write_text(test_log)
        return manifest
    except EnvironmentError:
        raise
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        raise EnvironmentError("FACTORY_BUILD_FAILED:" + type(error).__name__) from None
    finally:
        builder("test", "stop")
