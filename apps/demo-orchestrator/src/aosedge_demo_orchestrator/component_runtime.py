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

from .environment import EnvironmentError

SOURCE = Path.home() / "OpenAI/CarlaSim/.worktrees/aos-platform-factory-29"
RELATIVE = "meta-aos-vehicle-platform/recipes-aos/aos-servicemanager/files/systemd-slot-component"
BUILDER_PROJECT = "/home/yocto/r61-build/project/yocto"
ARTIFACT = Path.home() / "OpenAI/demo-artifacts/aosedge-sdv-demo/runtime-proofs/sm-stop-start"
FILES = ("config.hpp", "config.cpp", "safestop.hpp", "safestop.cpp", "runtime.hpp", "runtime.cpp",
         "tests/safestop.cpp", "tests/runtime.cpp")


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
            or hashlib.sha256(raw).hexdigest() != manifest["executableSha256"]
            or len(raw) > 256 * 1024 * 1024):
        raise EnvironmentError("SM_QUALIFIED_ARTIFACT_REQUIRED")
    with environment._writer():
        state = read_json(environment.root / JOURNAL)
        vehicle = state["vehicles"].get("test", {})
        if vehicle.get("localVmId") != "540cdea7-3fb8-4554-93aa-75cdf0ed577d":
            raise EnvironmentError("SM_PROOF_REQUIRES_AUTHORIZED_TEST_29")
        record = state.setdefault("smDemoProof", {})
        record.update(state="ATTEMPT_STARTED", startedAt=now(), binarySha256=manifest["executableSha256"])
        atomic_json(environment.root / JOURNAL, state)
        driver = SourceDriver(VMService(environment))
        try:
            with driver.operation(timeout=60):
                observed = driver.guest(state, "test", "component-sm-status")
                result = driver.guest(state, "test", "component-sm-apply", target="test",
                    proof="stop-start",
                    binary="" if observed["binarySha256"] == manifest["executableSha256"] else base64.b64encode(raw).decode(),
                    sha256=manifest["executableSha256"])
                # systemd clears service credentials on restart. Restore only
                # the already selected Test's public trust/binding inputs.
                if not result.get("noOp") and state.get("currentVehicle") == "test":
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
    """Compile only the accepted .29 SM recipe, run its suite, export, stop."""
    if target != "test":
        raise EnvironmentError("SM_QUALIFICATION_TEST_ONLY")
    if ARTIFACT.exists():
        raise EnvironmentError("SM_PROOF_ARTIFACT_ALREADY_EXISTS")
    expected = "45dfa22fce9b0b0fa636f1ca2dce876482ca5f68"
    ssh = builder_ssh()
    try:
        revision = subprocess.check_output(ssh + ["git -C " + BUILDER_PROJECT + "/aos-vehicle-platform rev-parse HEAD"], timeout=15).decode().strip()
        if revision != expected:
            raise EnvironmentError("SM_BUILDER_BASE_REVISION_MISMATCH")
        data = io.BytesIO()
        inputs = {}
        with tarfile.open(fileobj=data, mode="w") as archive:
            for name in FILES:
                path = SOURCE / RELATIVE / name
                inputs[name] = hashlib.sha256(path.read_bytes()).hexdigest()
                archive.add(path, arcname=RELATIVE + "/" + name, recursive=False)
        if compile_source:
            subprocess.run(ssh + ["tar -xf - -C " + BUILDER_PROJECT + "/aos-vehicle-platform"],
                           input=data.getvalue(), check=True, timeout=20, stdout=sys.stderr)
            print("Test SM: offline recipe compile; no image build", file=sys.stderr, flush=True)
            command = "cd " + BUILDER_PROJECT + "; . poky/oe-init-build-env build-main >/dev/null; BB_NO_NETWORK=1 BB_FETCH_PREMIRRORONLY=1 bitbake -c compile aos-servicemanager"
            subprocess.run(ssh + ["bash -lc " + __import__("shlex").quote(command)],
                           check=True, timeout=1200, stdout=sys.stderr)
        work = BUILDER_PROJECT + "/build-main/tmp/work/cortexa57-aos-linux/aos-servicemanager/git"
        test = work + "/build/src/sm/launcher/runtimes/systemd-slot-component/tests/aos_sm_runtimes_systemdslotcomponent_test"
        loader = work + "/recipe-sysroot/usr/lib/ld-linux-aarch64.so.1"
        libs = work + "/recipe-sysroot/lib:" + work + "/recipe-sysroot/usr/lib"
        test_filter = "*StopStart*:*StopMakes*:*StopMissing*:*StopCancellation*"
        print("Test SM: executing targeted native Stop/Start regression tests", file=sys.stderr, flush=True)
        result = subprocess.run(ssh + ["sudo -n " + loader + " --library-path " + libs + " " + test + " --gtest_filter=" + __import__("shlex").quote(test_filter)],
                                timeout=240, capture_output=True)
        print(result.stdout.decode(), file=sys.stderr, flush=True)
        print(result.stderr.decode(), file=sys.stderr, flush=True)
        ARTIFACT.with_suffix(".test.log").write_bytes(result.stdout + result.stderr)
        if result.returncode:
            raise EnvironmentError("SM_TARGETED_TEST_FAILED:" + str(result.returncode))
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
        manifest = dict(baseRevision=expected, sourceSha256=inputs, executableSha256=hashlib.sha256(binary).hexdigest(),
                        profile="demo-5s", defaultMaximumSourceAgeMs=250, demoMaximumSourceAgeMs=5000,
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


def build_factory(version):
    """The release build is a Demo Control operation, not an operator script.

    Export only committed Platform source, reuse the warm offline build tree,
    gate image construction on the new configuration test and package QA, then
    reuse the existing Rouge disk description. Never alter a published image.
    """
    if version != "6.1.1-maninblack.30":
        raise EnvironmentError("FACTORY_BUILD_NOT_AUTHORIZED")
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=SOURCE):
        raise EnvironmentError("FACTORY_COMMITTED_SOURCE_REQUIRED")
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=SOURCE).decode().strip()
    destination = ARTIFACT.parents[1] / "factory-images" / version
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
        print("Factory .30: " + message, file=sys.stderr, flush=True)
    try:
        # The same established Builder adapter owns start/stop and disk guards.
        builder("test", "start")
        free = int(remote("df -Pk " + BUILDER_PROJECT + " | tail -1 | awk '{print $4}'").strip()) * 1024
        if free < 60 * 1024**3:
            raise EnvironmentError("FACTORY_BUILDER_FREE_SPACE_BELOW_60_GIB")
        graph = remote("cd " + project + "; ninja -t commands main-qemuarm64.img")
        assembly = [shlex.split(line) for line in graph.splitlines()
                    if line.strip() and Path(shlex.split(line)[0]).name == "rouge"]
        if len(assembly) != 1 or "main-qemuarm64.img" not in assembly[0]:
            raise EnvironmentError("FACTORY_PINNED_ROUGE_COMMAND_UNRESOLVED")
        archive = subprocess.check_output(["git", "archive", revision], cwd=SOURCE)
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
        flags = " -R " + source + "/qualification/factory-30.conf "
        stage("compile the changed SM configuration (offline)")
        remote(prefix + "bitbake" + flags + "-c compile aos-servicemanager", timeout=1200, capture=False)
        work = BUILDER_PROJECT + "/build-main/tmp/work/cortexa57-aos-linux/aos-servicemanager/git"
        test = work + "/build/src/sm/launcher/runtimes/systemd-slot-component/tests/aos_sm_runtimes_systemdslotcomponent_test"
        loader = work + "/recipe-sysroot/usr/lib/ld-linux-aarch64.so.1"
        libs = work + "/recipe-sysroot/lib:" + work + "/recipe-sysroot/usr/lib"
        stage("run only the new persistent-input and profile tests")
        test_log = remote("sudo -n " + loader + " --library-path " + libs + " " + test +
            " --gtest_filter='*FactoryDemoInputs*:*AcceptsOnlyExplicitDemoFreshnessProfile*'", timeout=60)
        print(test_log, file=sys.stderr, flush=True)
        stage("package SM with package QA")
        remote(prefix + "bitbake" + flags + "aos-servicemanager", timeout=1200, capture=False)
        stage("construct the Factory filesystem from pinned sources")
        remote(prefix + "bitbake" + flags + "aos-image-vm", timeout=2400, capture=False)
        output = "main-qemuarm64-factory-30.img"
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
        manifest = dict(schemaVersion=1, state="BUILT_NOT_LIVE_QUALIFIED",
            source=dict(repository="aos-vehicle-platform", revision=revision),
            factoryImage=dict(version=version, architecture="main-qemuarm64", path="main-qemuarm64.img",
                              byteLength=image.stat().st_size, sha256=remote_sha, format="raw"),
            build=dict(offline=True, targetedTests="PASS", packageQa="PASS", imageQa="PASS",
                       hostTransferSha256Matched=True, builderSource=source, assemblyCommand=assembly))
        (destination / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        (destination / "configuration-tests.log").write_text(test_log)
        return manifest
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        raise EnvironmentError("FACTORY_BUILD_FAILED:" + type(error).__name__) from None
    finally:
        builder("test", "stop")
