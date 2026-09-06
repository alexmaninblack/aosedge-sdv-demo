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
from pathlib import Path
import sys

from .environment import EnvironmentError

SOURCE = Path.home() / "OpenAI/CarlaSim/.worktrees/aos-platform-factory-29"
RELATIVE = "meta-aos-vehicle-platform/recipes-aos/aos-servicemanager/files/systemd-slot-component"
BUILDER_PROJECT = "/home/yocto/r61-build/project/yocto"
ARTIFACT = Path.home() / "OpenAI/demo-artifacts/aosedge-sdv-demo/runtime-proofs/sm-demo-5s"
FILES = ("config.hpp", "config.cpp", "safestop.hpp", "safestop.cpp", "runtime.cpp",
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


def build(target):
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
        print("Test SM: executing complete runtime test suite", file=sys.stderr, flush=True)
        result = subprocess.run(ssh + ["sudo -n " + loader + " --library-path " + libs + " " + test],
                                check=True, timeout=240, capture_output=True)
        print(result.stdout.decode(), file=sys.stderr, flush=True)
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
                        offline=True, imageBuild=False, testsPassed=True, guestApplied=False)
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
