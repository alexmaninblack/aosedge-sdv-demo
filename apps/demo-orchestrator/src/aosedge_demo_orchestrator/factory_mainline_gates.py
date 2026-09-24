# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Factory .37/.38 Builder-only gates; no live VM, credentials or Cloud access.

Demo Control exports this committed file to the isolated ARM64 Builder. Tests
use the recipe toolchain/sysroot and synthetic fixtures, not the running Test.
Core unit tests retain upstream's fixture configuration; application compilation
and packaged configuration are checked separately. VM-only cases stay explicit.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import tempfile
import xml.etree.ElementTree as ET


APP = "9d613a46df3c7f550062e2f19ae3406c57715694"
LIB = "5560291ba6914e36a5b841ade4d8fc54134a9e91"
API = "af3552a0a5eb0237eff7f5f183780ca46c339cd3"
MANAGERS = ("aos-communicationmanager", "aos-servicemanager", "aos-iamanager")
SM_LAUNCHER_TEST_COUNTS = {"37": 27, "38": 32}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def variable(data, key):
    values = re.findall(r'^(?:export )?' + re.escape(key) + r'="([^"]*)"$', data, re.M)
    require(len(values) == 1, "effective variable missing or duplicated: " + key)
    return values[0]


def check_effective(data, name):
    for key, value in (("SRCREV", APP), ("SRCREV_default", APP),
                       ("SRCREV_serviceupdatelib", LIB), ("SRCREV_serviceupdateapi", API),
                       ("BB_NO_NETWORK", "1"), ("BB_FETCH_PREMIRRORONLY", "1")):
        require(variable(data, key) == value, name + ": incorrect " + key)
    cmake = variable(data, "EXTRA_OECMAKE")
    require("/ltvp-aos-core" not in cmake and "/service-update-deps" in cmake,
            name + ": recipe-private dependency binding required")
    require(cmake.rfind("-DFETCHCONTENT_FULLY_DISCONNECTED=ON") >
            cmake.rfind("-DFETCHCONTENT_FULLY_DISCONNECTED=OFF"), name + ": offline CMake required")
    check_flags(variable(data, "CXXFLAGS"), name)


def check_flags(flags, name):
    def definitions(key):
        return re.findall(r"-D" + key + r"=([^\s]+)", flags)
    require(definitions("AOS_CONFIG_TYPES_FUNCTION_LEN") == ["256"], name + ": permission-key256 required")
    if name == "aos-iamanager":
        require(definitions("AOS_CONFIG_PKCS11_SESSION_POOL_MAX_SIZE") == ["3"], "IAM cache3 required")
        require("AOS_CONFIG_PKCS11_SESSIONS_PER_LIB" not in flags, "obsolete IAM allocator override")


def preflight(conf):
    for name in MANAGERS:
        data = subprocess.check_output(["bitbake", "-R", str(conf), "-e", name], text=True, timeout=180)
        check_effective(data, name)
        print(name + ": effective mainline pins/offline configuration PASS", flush=True)


def cache(work):
    return dict((line.split(":", 1)[0], line.split("=", 1)[1])
                for line in (work / "build/CMakeCache.txt").read_text().splitlines()
                if ":" in line and "=" in line and not line.startswith(("#", "//")))


def environment(work):
    result = os.environ.copy()
    script = (work / "temp/run.do_compile").read_text()
    result["PATH"] = shlex.split(next(line for line in script.splitlines()
                                    if line.startswith("export PATH=")))[1].split("=", 1)[1]
    return result


def verify_source(work):
    for path, revision in ((work / "git", APP), (work / "service-update-deps/aos_core_lib_cpp", LIB),
                           (work / "service-update-deps/aos_core_api", API)):
        actual = subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"], text=True).strip()
        require(actual == revision, "compiled source revision mismatch: " + str(path))
    require(cache(work)["AOS_CORE_DIR"] == str(work / "service-update-deps"), "compiled dependency mismatch")
    flags = [p.read_text() for p in (work / "build").rglob("flags.make") if "CXX_FLAGS =" in p.read_text()]
    require(bool(flags), "no actual CXX compilation flags")
    for value in flags:
        check_flags(value, work.parent.name)
    print(work.parent.name + ": actual source and compile binding PASS", flush=True)


def unique_binary(root, name):
    candidates = [p for p in root.rglob(name) if p.is_file()]
    require(len(candidates) == 1, "test executable not unique: " + name)
    return candidates[0]


def loader(work):
    return [str(work / "recipe-sysroot/usr/lib/ld-linux-aarch64.so.1"), "--library-path",
            str(work / "recipe-sysroot/lib") + ":" + str(work / "recipe-sysroot/usr/lib")]


def check_gtest(path, executed, skipped=0, disabled=0):
    root = ET.parse(path).getroot()
    require(int(root.get("tests", -1)) == executed + disabled, "unexpected registered test count")
    require(int(root.get("disabled", 0)) == disabled, "unexpected disabled test count")
    require(int(root.get("failures", -1)) == 0 and int(root.get("errors", 0)) == 0, "native test failure")
    require(sum(int(s.get("skipped", 0)) for s in root.findall("testsuite")) == skipped, "unexpected skipped tests")
    cases = root.findall(".//testcase")
    require(len(cases) == executed + disabled, "incomplete native test report")
    if disabled:
        # These two cases are disabled upstream, not converted to a passing gate.
        names = {case.get("name") for case in cases if case.get("status") == "notrun"}
        require(names == {"DISABLED_PopulateHostDevices", "DISABLED_PopulateHostDevicesSymlink"},
                "unexpected upstream-disabled tests")
    return dict(passed=executed - skipped, skipped=skipped, disabled=disabled)


class NativeGates:
    def __init__(self, root, evidence, factory_suffix="37"):
        require(factory_suffix in SM_LAUNCHER_TEST_COUNTS, "unsupported Factory native matrix")
        self.factory_suffix = factory_suffix
        self.root, self.evidence = root, evidence
        # Never overwrite/re-run an uncertain attempt. Keep root-owned synthetic
        # fixtures; an evidence cleanup error must not masquerade as test failure.
        evidence.mkdir(exist_ok=False)
        self.results = {}

    def execute(self, command, label, env=None, cwd=None, timeout=600):
        path = self.evidence / (label + ".log")
        with path.open("x") as stream:
            result = subprocess.run(command, env=env, cwd=cwd, stdout=stream,
                                    stderr=subprocess.STDOUT, timeout=timeout)
        if result.returncode:
            print(path.read_text()[-8000:], flush=True)
            raise RuntimeError(label + ": exit " + str(result.returncode))

    def test(self, work, executable, label, executed, skipped=0, disabled=0):
        xml = self.evidence / (label + ".xml")
        cwd = tempfile.mkdtemp(prefix="fixture-", dir=self.evidence)
        self.execute(["sudo", "-n", *loader(work), str(executable), "--gtest_output=xml:" + str(xml)],
                     label, cwd=cwd, timeout=180)
        self.results[label] = check_gtest(xml, executed, skipped, disabled)
        print(label + ": " + json.dumps(self.results[label]), flush=True)

    def core(self, work, suite):
        values, env = cache(work), environment(work)
        build = work / "mainline-native-tests"
        self.execute([values["CMAKE_COMMAND"], "-S", str(work / "service-update-deps/aos_core_lib_cpp"),
                      "-B", str(build), "-G", values["CMAKE_GENERATOR"],
                      "-DCMAKE_MAKE_PROGRAM=" + values["CMAKE_MAKE_PROGRAM"],
                      "-DCMAKE_TOOLCHAIN_FILE=" + str(work / "toolchain.cmake"),
                      "-DCMAKE_CXX_FLAGS=" + values["CMAKE_CXX_FLAGS"], "-DWITH_TEST=ON",
                      "-DWITH_MBEDTLS=OFF", "-DWITH_OPENSSL=ON", "-DFETCHCONTENT_FULLY_DISCONNECTED=ON",
                      "-DCMAKE_GTEST_DISCOVER_TESTS_DISCOVERY_MODE=PRE_TEST"],
                     work.parent.name + "-core-configure", env)
        self.execute([values["CMAKE_COMMAND"], "--build", str(build), "--target", *[s[0] for s in suite],
                      "--parallel", "4"], work.parent.name + "-core-build", env, timeout=900)
        for target, label, count in suite:
            self.test(work, unique_binary(build, target), label, count)

    def lock(self, work, source):
        values, env = cache(work), environment(work)
        # CMake binds a build directory to one source directory. Keep the warm
        # cache per committed tooling export without deleting a previous proof.
        identity = hashlib.sha256(str(source).encode()).hexdigest()[:12]
        build = work / ("mainline-lock-tests-" + identity)
        self.execute([values["CMAKE_COMMAND"], "-S", str(source), "-B", str(build),
                      "-G", values["CMAKE_GENERATOR"], "-DCMAKE_MAKE_PROGRAM=" + values["CMAKE_MAKE_PROGRAM"],
                      "-DCMAKE_TOOLCHAIN_FILE=" + str(work / "toolchain.cmake"),
                      "-DCMAKE_CXX_FLAGS=" + values["CMAKE_CXX_FLAGS"], "-DCPP=" + str(work / "git"),
                      "-DCORE=" + str(work / "service-update-deps/aos_core_lib_cpp"),
                      "-DCMAKE_CROSSCOMPILING_EMULATOR=" + ";".join(loader(work))], "lock-configure", env)
        self.execute([values["CMAKE_COMMAND"], "--build", str(build), "--parallel", "4"],
                     "lock-build", env, timeout=900)
        xml = self.evidence / "cm-lock.xml"
        self.execute(["/usr/bin/ctest", "--test-dir", str(build), "--output-on-failure",
                      "--output-junit", str(xml)], "cm-lock", env, timeout=300)
        root = ET.parse(xml).getroot()
        require(len(root.findall("testcase")) == 17 and not root.findall(".//failure")
                and not root.findall(".//skipped"), "CM lock regression incomplete")
        self.results["cm-lock"] = dict(passed=17, skipped=0, disabled=0)

    def run(self, lock_source):
        cm, sm, iam = (self.root / name / "git" for name in MANAGERS)
        for work in (cm, sm, iam):
            verify_source(work)
        self.core(cm, [("aos_core_cm_launcher_test", "cm-launcher", 47),
                       ("aos_core_cm_updatemanager_test", "cm-idle", 11),
                       ("aos_core_cm_storagestate_test", "cm-storage", 15)])
        self.core(sm, [("aos_core_sm_launcher_test", "sm-replacement",
                       SM_LAUNCHER_TEST_COUNTS[self.factory_suffix])])
        self.core(iam, [("aos_core_iam_permhandler_test", "iam-permissions", 7),
                        ("aos_core_common_pkcs11_test", "iam-pkcs11", 14)])
        for work, name, label, count, skipped, disabled in (
            (sm, "aos_sm_runtimes_systemdslotcomponent_test", "vdp", 83, 2, 0),
            (sm, "aos_sm_runtimes_container_test", "container", 42, 0, 2),
            (sm, "aos_sm_runtimes_crunadapter_test", "crun-adapter", 5, 0, 0),
            (sm, "aos_sm_networkmanager_test", "sm-network", 97, 0, 0),
            (iam, "aos_iam_iamserver_test", "iam-server", 61, 0, 0)):
            self.test(work, unique_binary(work / "build", name), label, count, skipped, disabled)
        self.lock(cm, lock_source)
        kac = unique_binary(self.root / "aos-kuksa-auth-compat", "provider-tests").parents[1]
        for name in ("kac-tests", "provider-tests", "verifier-prepare-tests"):
            cwd = tempfile.mkdtemp(prefix="fixture-kac-", dir=self.evidence)
            self.execute([*loader(kac), str(kac / "build" / name)], name, cwd=cwd, timeout=60)
            self.results[name] = dict(exitCode=0)
        result = dict(state="NATIVE_GATES_PASS_NOT_LIVE_QUALIFIED", app=APP, lib=LIB, api=API,
                      factorySuffix=self.factory_suffix,
                      tests=self.results)
        (self.evidence / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result, indent=2), flush=True)


def package_config(root):
    iam = json.loads((root / "aos-iamanager/git/image/etc/aos/iam.cfg").read_text())
    require(iam.get("enablePermissionsHandler") is True, "packaged IAM permissions handler disabled")
    modules = iam["certModules"]
    identifiers = [item["id"] for item in modules]
    require(len(identifiers) == len(set(identifiers)), "duplicate IAM module")
    keys = {(item["params"]["library"], item["params"]["tokenLabel"]) for item in modules}
    require(keys == {("/usr/lib/softhsm/libsofthsm2.so", label)
                     for label in ("aoscloud", "aoscore", "aos-kuksa")}, "packaged IAM topology changed")
    kuksa = [item for item in modules if item["id"] == "kuksa-jwt"]
    require(len(kuksa) == 1 and kuksa[0]["selfSigned"] is True
            and kuksa[0]["params"]["tokenLabel"] == "aos-kuksa", "packaged KUKSA module missing")
    print("Mainline packaged IAM permission/cache topology: PASS", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("preflight", "native", "package"))
    parser.add_argument("--conf", type=Path)
    parser.add_argument("--root", type=Path)
    parser.add_argument("--evidence", type=Path)
    parser.add_argument("--lock-source", type=Path)
    parser.add_argument("--factory-suffix", choices=tuple(SM_LAUNCHER_TEST_COUNTS), default="37")
    args = parser.parse_args()
    if args.phase == "preflight":
        require(args.conf is not None, "--conf required")
        preflight(args.conf)
    elif args.phase == "native":
        require(all((args.root, args.evidence, args.lock_source)), "native paths required")
        NativeGates(args.root, args.evidence, args.factory_suffix).run(args.lock_source)
    else:
        require(args.root is not None, "--root required")
        package_config(args.root)


if __name__ == "__main__":
    main()
