# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Demo Control-owned migration of the preserved staging Test to VISS mTLS."""
import json
import subprocess
import time
from pathlib import Path

from .environment import EnvironmentError, JOURNAL
from .status import read_json
from . import source_trust as trust

BUILD = ".local/build/viss-mtls"
DIRECTORY = ".run/demo-current/control/viss-trust"
SOCKET = ".run/demo-current/control/viss.sock"


def enabled(state):
    return ((state.get("source") or {}).get("trust") or {}).get("enabled") is True


def configuration(driver, state):
    record = state["source"]["trust"]
    if record.get("profile") != trust.PROFILE or record.get("target") != "test":
        raise EnvironmentError("SOURCE_TRUST_PROFILE_INVALID")
    # Always check the existing identity/material; never generate on restart.
    directory = driver.root / DIRECTORY
    if not directory.is_dir():
        raise EnvironmentError("SOURCE_TRUST_MATERIAL_MISSING")
    value = trust.prepare(directory, state["vehicles"]["test"])
    if value["fingerprints"] != record["fingerprints"]:
        raise EnvironmentError("SOURCE_TRUST_ENROLLMENT_CHANGED")
    return value


def runner_options(driver, state):
    public = configuration(driver, state)
    directory = driver.root / DIRECTORY
    return ["--viss-client-ca", str(directory / "ca.pem"),
        "--viss-assignment-socket", str(driver.root / SOCKET),
        "--viss-assignment-generation", str(state["source"]["assignmentGeneration"]),
        "--dashboard-certificate", str(directory / "dashboard.pem"),
        "--dashboard-private-key", str(directory / "dashboard-key.pem"),
        "--dashboard-certificate-sha256", public["fingerprints"]["dashboard"]]


def observe(driver):
    value = trust.assignment(driver.root / SOCKET, "status", timeout=driver.budget(3))
    if value.get("result") != "ACCEPTED":
        raise EnvironmentError("SOURCE_TRUST_ASSIGNMENT_UNAVAILABLE")
    return value


def selection(state):
    item = state["vehicles"]["test"]
    fingerprints = state["source"]["trust"]["fingerprints"]
    return dict(unitId=item["unitId"], nodeId=item["nodeId"],
        selectedPlatformUnitCertificateSha256=fingerprints["vdp"],
        platformUpdateRuntimeCertificateSha256=fingerprints["runtime"])


def detach(driver, state):
    current = observe(driver)
    pending = state["source"]["trust"].get("pending")
    if pending:
        before = pending["generation"]
        applied = (current["assignmentGeneration"] == before + 1 and
            ((pending["action"] == "detach" and current["state"] == "DETACHED") or
             (pending["action"] == "select" and current.get("selectedSource") == selection(state))))
        if applied:
            state["source"]["assignmentGeneration"] = current["assignmentGeneration"]
        elif current["assignmentGeneration"] != before:
            raise EnvironmentError("SOURCE_TRUST_PENDING_ASSIGNMENT_CONFLICT")
        state["source"]["trust"].pop("pending")
        driver.vm._save(state)
    if current["assignmentGeneration"] != state["source"]["assignmentGeneration"]:
        raise EnvironmentError("SOURCE_TRUST_ASSIGNMENT_GENERATION_CONFLICT")
    if current["state"] == "SELECTED":
        if current.get("selectedSource") != selection(state):
            raise EnvironmentError("SOURCE_TRUST_ASSIGNMENT_OWNER_CONFLICT")
        identity = {key: current["selectedSource"][key] for key in ("unitId", "nodeId")}
        # Journal the exact intent before the single CAS mutation.
        state["source"]["trust"]["pending"] = dict(action="detach", generation=current["assignmentGeneration"])
        driver.vm._save(state)
        result = trust.assignment(driver.root / SOCKET, "detach", current["assignmentGeneration"], identity)
        if result.get("result") != "ACCEPTED":
            raise EnvironmentError("SOURCE_TRUST_DETACH_REJECTED")
        current = observe(driver)
        if current["state"] != "DETACHED" or current["assignmentGeneration"] != state["source"]["assignmentGeneration"] + 1:
            raise EnvironmentError("SOURCE_TRUST_DETACH_UNCONFIRMED")
        if any(current.get("activeRoleCounts", {}).get(role, 1) != 0 for role in ("selectedPlatformUnit", "platformUpdateRuntime")):
            raise EnvironmentError("SOURCE_TRUST_DETACH_SESSIONS_REMAIN")
        state["source"]["assignmentGeneration"] = current["assignmentGeneration"]
        state["source"]["trust"].pop("pending", None)
        driver.vm._save(state)


def attach(driver, state, role):
    if role != "test":
        raise EnvironmentError("SOURCE_TRUST_TEST_ONLY")
    public = configuration(driver, state)
    current = observe(driver)
    expected = selection(state)
    source = state["source"]
    if current["state"] == "DETACHED":
        if current["assignmentGeneration"] != source["assignmentGeneration"]:
            raise EnvironmentError("SOURCE_TRUST_ASSIGNMENT_GENERATION_CONFLICT")
        source["trust"]["pending"] = dict(action="select", generation=current["assignmentGeneration"])
        driver.vm._save(state)
        result = trust.assignment(driver.root / SOCKET, "select", current["assignmentGeneration"], expected)
        if result.get("result") != "ACCEPTED":
            raise EnvironmentError("SOURCE_TRUST_SELECT_REJECTED")
        current = observe(driver)
    pending = source["trust"].get("pending")
    expected_generation = source["assignmentGeneration"] + (1 if pending and pending["action"] == "select" else 0)
    if (current["state"] != "SELECTED" or current.get("selectedSource") != expected
            or current["assignmentGeneration"] != expected_generation):
        raise EnvironmentError("SOURCE_TRUST_SELECT_UNCONFIRMED")
    source["assignmentGeneration"] = current["assignmentGeneration"]
    source["trust"].pop("pending", None)
    driver.vm._save(state)
    base = driver.root / DIRECTORY
    material = dict(ca=driver.assets()["ca"].read_text(), vdpCertificate=(base / "vdp.pem").read_text(),
        vdpKey=(base / "vdp-key.pem").read_text(), runtimeCertificate=(base / "runtime.pem").read_text(),
        runtimeKey=(base / "runtime-key.pem").read_text())
    return driver.guest(state, role, "trust-configure", generation=current["assignmentGeneration"],
        material=material, fingerprints={key: public["fingerprints"][key] for key in ("vdp", "runtime")})


def connection(driver, state, role, wait=False):
    if role != "test":
        raise EnvironmentError("SOURCE_TRUST_TEST_ONLY")
    deadline = time.monotonic() + (12 if wait else 0)
    while True:
        current = observe(driver)
        guest = driver.guest(state, role, "trust-status")
        good = (current["state"] == "SELECTED" and current.get("selectedSource") == selection(state)
            and current["assignmentGeneration"] == state["source"]["assignmentGeneration"]
            and current.get("activeRoleCounts", {}).get("selectedPlatformUnit") == 1
            and guest["mutualTlsConfigured"] and guest["vdpProcess"] == "active"
            and guest["vdpData"] == "VDP data READY; source LIVE; reason NONE")
        if good or time.monotonic() >= deadline:
            return dict(serverTls=good, mutualTls=good, gateway=current, guest=guest,
                evidence="GATEWAY_AUTHENTICATED_ROLE_AND_PROVIDER_REPORTED_READY")
        time.sleep(.25)


def build(driver):
    paths = driver.assets()
    build_root = driver.root / BUILD
    driver.vm.environment._directory(BUILD)
    prefix = paths["carla-root"] / "Build-macos-client-v3/install"
    commands = [["/opt/homebrew/bin/cmake", "-S", str(paths["runtime-root"]), "-B", str(build_root),
        "-DCMAKE_BUILD_TYPE=Release", "-DBUILD_TESTING=OFF", "-DFETCHCONTENT_FULLY_DISCONNECTED=ON", "-DCARLA_EGO_WITH_CARLA=ON",
        "-DCARLA_EGO_WITH_VISS=ON", "-DCMAKE_PREFIX_PATH=" + str(prefix) + ";/opt/homebrew/opt/openssl@3"],
        ["/opt/homebrew/bin/cmake", "--build", str(build_root), "--target", "carla-ego-runtime", "carla-viss-client", "--parallel", "4"]]
    driver.progress("Gateway: compiling the current reviewed runtime/client only; CARLA and the VM remain running")
    for argv in commands:
        result = subprocess.run(argv, capture_output=True, timeout=360)
        if result.returncode:
            raise EnvironmentError("SOURCE_TRUST_GATEWAY_BUILD_FAILED")
    return dict(state="BUILT", directory=BUILD)


def authenticate(service, role):
    if role != "test":
        raise EnvironmentError("SOURCE_TRUST_TEST_ONLY")
    driver = service.driver
    with service.environment._writer(), driver.operation():
        state = read_json(service.root / JOURNAL)
        service.vm._validate(state, "start", [role])
        trust.identity(state["vehicles"][role])
        source = state.get("source")
        if not source or state.get("currentVehicle") not in (None, "test"):
            raise EnvironmentError("SOURCE_TRUST_CURRENT_TEST_REQUIRED")
        if not enabled(state):
            if source.get("operation") or source.get("stopOperation"):
                raise EnvironmentError("SOURCE_OPERATION_RECONCILIATION_REQUIRED")
            # Read the actual current tenant/Unit once at the trust boundary.
            service.cloud(state, [role])
            build(driver)
            directory = service.root / DIRECTORY
            public = trust.prepare(directory, state["vehicles"][role])
            source["trust"] = dict(profile=trust.PROFILE, target=role,
                fingerprints=public["fingerprints"], enabled=False)
            service.vm._save(state)
            driver.progress("Source: one controlled simulation restart for strict TLS; VM, Cloud Unit and services retained")
            service.simulation("stop", target=role)
            state = read_json(service.root / JOURNAL)
            state["source"]["trust"]["enabled"] = True
            service.vm._save(state)
        service.simulation("start", target=role)
        result = service.select(role)
        state = read_json(service.root / JOURNAL)
        proof = state["source"]["trust"].get("noClientCertificateProof")
        if not proof or proof.get("runId") != state["source"]["runId"]:
            # One anonymous read against the same healthy endpoint. Only an
            # explicit TLS certificate rejection counts, not any connection error.
            paths = driver.assets()
            attempt = subprocess.run([str(service.root / BUILD / "carla-viss-client"),
                "--host", "localhost", "--port", "16443", "--ca", str(paths["ca"]),
                "--messages", "1", "--request", json.dumps(dict(action="get",
                    path="Vehicle.CarlaSimulation.FrameId", requestId="unauthenticated-admission-proof"))],
                capture_output=True, timeout=8)
            output = (attempt.stdout + attempt.stderr).decode(errors="replace").lower()
            if not attempt.returncode or not any(marker in output for marker in
                    ("certificate required", "peer did not return a certificate")):
                raise EnvironmentError("SOURCE_TRUST_NO_CERTIFICATE_REJECTION_UNCONFIRMED")
            proof = dict(runId=state["source"]["runId"], result="TLS_CLIENT_CERTIFICATE_REQUIRED")
            state["source"]["trust"]["noClientCertificateProof"] = proof
            service.vm._save(state)
        result["noClientCertificateProof"] = proof["result"]
        return result
