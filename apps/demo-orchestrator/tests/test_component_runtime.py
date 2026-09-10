# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import unittest
import base64
import gzip
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from aosedge_demo_orchestrator.api import execute_operation
from aosedge_demo_orchestrator.cli import build_parser, request_from_arguments
from aosedge_demo_orchestrator.component_runtime import apply_test, build, builder, build_factory, FACTORY_VERSION, FACTORY_REVISION, SM_REVISION
from aosedge_demo_orchestrator.environment import EnvironmentError
from aosedge_demo_orchestrator.source_guest import execute, process_wait_observation, sm_saved_test_release, sm_recover_test


class RuntimeProofBoundaryTests(unittest.TestCase):
    def test_sm_compile_failure_stops_builder_without_image_build_or_guest_apply(self):
        with tempfile.TemporaryDirectory() as directory, \
                patch("aosedge_demo_orchestrator.component_runtime.ARTIFACT", Path(directory) / "proof"), \
                patch("aosedge_demo_orchestrator.component_runtime.builder") as lifecycle, \
                patch("aosedge_demo_orchestrator.component_runtime.shutil.disk_usage", return_value=SimpleNamespace(free=80*1024**3)), \
                patch("aosedge_demo_orchestrator.component_runtime.subprocess.check_output", side_effect=[SM_REVISION.encode(), b""]), \
                patch("aosedge_demo_orchestrator.component_runtime.subprocess.run", return_value=subprocess.CompletedProcess([], 255, stderr=b"Permission denied")):
            with self.assertRaisesRegex(EnvironmentError, "SM_BUILDER_SSH_TRUST_OR_AUTH_FAILED"):
                build("test")
            self.assertEqual([("test", "start"), ("test", "stop")], [call.args for call in lifecycle.call_args_list])

    def test_process_wait_observation_excludes_secret_bearing_process_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            proc = Path(directory)
            root = proc / "12"
            (root / "task/12").mkdir(parents=True)
            (root / "fd").mkdir()
            (root / "task/12/wchan").write_text("futex_wait_queue\n")
            (root / "status").write_text("VmRSS:\t1024 kB\nFDSize:\t64\nName:\tSECRET\n")
            (root / "cmdline").write_text("SECRET")
            (root / "fd/3").symlink_to("/secret/key")
            value = process_wait_observation("12", proc)
            self.assertEqual({"futex_wait_queue": 1}, value["waits"])
            self.assertEqual(1, value["openDescriptorCount"])
            self.assertNotIn("SECRET", str(value))
            self.assertNotIn("/secret", str(value))
            self.assertEqual("UNAVAILABLE", process_wait_observation("0", proc)["state"])

    def test_factory_cold_boot_waits_for_ssh_before_build_reads(self):
        with tempfile.TemporaryDirectory() as directory, \
                patch("aosedge_demo_orchestrator.component_runtime.ARTIFACT", Path(directory) / "runtime-proofs" / "proof"), \
                patch("aosedge_demo_orchestrator.component_runtime.builder") as lifecycle, \
                patch("aosedge_demo_orchestrator.component_runtime.factory_component_support", return_value={}), \
                patch("aosedge_demo_orchestrator.component_runtime.time.sleep"), \
                patch("aosedge_demo_orchestrator.component_runtime.shutil.disk_usage", return_value=SimpleNamespace(free=80*1024**3)), \
                patch("aosedge_demo_orchestrator.component_runtime.subprocess.check_output", side_effect=[b"", FACTORY_REVISION.encode()]), \
                patch("aosedge_demo_orchestrator.component_runtime.subprocess.run", side_effect=[
                    subprocess.CompletedProcess([], 255, stderr=b"Connection refused"),
                    subprocess.CompletedProcess([], 0, stderr=b""),
                    subprocess.CompletedProcess([], 0, stdout=b"0\n")]) as process:
            with self.assertRaisesRegex(EnvironmentError, "BUILDER_FREE_SPACE_BELOW"):
                build_factory(FACTORY_VERSION)
            self.assertEqual(["true", "true"], [call.args[0][-1] for call in process.call_args_list[:2]])
            self.assertIn("df -Pk", process.call_args_list[2].args[0][-1])
            self.assertEqual([("test", "start"), ("test", "stop")], [call.args for call in lifecycle.call_args_list])

    def test_factory_build_cli_and_api_use_the_same_exact_release(self):
        request = request_from_arguments(build_parser().parse_args(["image", "build", "6.1.1-maninblack.31"]))
        app = Mock()
        execute_operation(dict(domain="image", action="build", image="6.1.1-maninblack.31"), app)
        self.assertEqual(request, app.execute.call_args.args[0])
        with self.assertRaises(ValueError):
            execute_operation(dict(domain="image", action="build", image="6.1.1-maninblack.29"), app)

    def test_cli_and_api_share_test_only_operations(self):
        for action in ("sm-builder-start", "sm-builder-stop", "sm-build", "sm-test", "sm-apply", "sm-status"):
            request = request_from_arguments(build_parser().parse_args(["component", action, "test"]))
            self.assertEqual("test", request.target.value)
            app = Mock()
            execute_operation(dict(domain="component", action=action, target="test"), app)
            self.assertEqual(request, app.execute.call_args.args[0])
            for extra in ({"target": "production"}, {"binary": "/tmp/arbitrary"}):
                with self.assertRaises(ValueError):
                    execute_operation(dict(dict(domain="component", action=action, target="test"), **extra), app)

    def test_production_rejected_before_any_host_or_guest_access(self):
        for function, args in ((builder, ("production", "start")), (build, ("production",)),
                               (apply_test, (None, "production"))):
            with self.assertRaises(EnvironmentError):
                function(*args)
        with patch("aosedge_demo_orchestrator.source_guest.command") as command:
            with self.assertRaises(ValueError):
                execute(dict(action="component-sm-apply", target="production", vehicle={}))
            command.assert_not_called()

    def test_wrong_test_vm_is_rejected_before_guest_commands(self):
        with patch("aosedge_demo_orchestrator.source_guest.command") as command:
            for proof in ("stop-start", "factory-placeholder", "demo-clock-skew", "queued-recovery"):
                with self.assertRaises(ValueError):
                    execute(dict(action="component-sm-apply", proof=proof, target="test", vehicle={"localVmId": "another-vm"}))
            command.assert_not_called()


class QueuedRecoveryBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name) / "runtime"
        (self.root / "state").mkdir(parents=True)
        (self.root / "slots/b/config").mkdir(parents=True)
        self.installed = dict(schemaVersion=1, slot="b", ItemId="component", SubjectId="aos-vm-main",
            Instance=0, Version="17.0.0", ManifestDigest="a"*64, RuntimeId="runtime", Preinstalled=False)
        self.transaction = dict(schemaVersion=2, operation="remove", phase="waiting-for-safe-stop",
            hasPrevious=True, candidateSlot="b", previousSlot="b")
        for prefix in ("candidate", "previous"):
            self.transaction.update({prefix + key: value for key, value in self.installed.items()
                if key not in ("schemaVersion", "slot")})
        self.write("state/installed.json", self.installed)
        self.write("slots/b/.aos-instance.json", self.installed)
        self.write("state/transaction.json", self.transaction)
        self.write("slots/b/component.json", dict(schemaVersion=1, component="vehicle-data-provider", version="17.0.0",
            architecture="arm64", os="linux", runtimeInterface=1, entrypoint="bin/vehicle-data-provider", configuration="config/provider.json"))
        self.write("slots/b/config/capability-manifest.json", dict(semanticVersion="17.0.0"))
        self.cap_sha = hashlib.sha256((self.root / "slots/b/config/capability-manifest.json").read_bytes()).hexdigest()
        self.write("slots/b/config/provider.json", dict(semanticVersion="17.0.0", capabilityManifestSha256=self.cap_sha))
        self.addCleanup(patch.stopall)
        patch("aosedge_demo_orchestrator.source_guest.SM_RECOVERY_CAP_SHA", self.cap_sha).start()

    def write(self, relative, value):
        (self.root / relative).write_text(json.dumps(value))

    def test_valid_missing_selector_is_read_only_and_does_not_rewrite_intent(self):
        before = {p: p.read_bytes() for p in self.root.rglob("*.json")}
        result = sm_saved_test_release(self.root)
        self.assertEqual("17.0.0", result["version"])
        self.assertFalse(result["selectorPresent"])
        self.assertFalse((self.root / "active").is_symlink())
        self.assertEqual(before, {p: p.read_bytes() for p in self.root.rglob("*.json")})

    def test_wrong_phase_operation_version_slot_and_digest_are_rejected(self):
        for key, value in (("phase", "stopping"), ("operation", "install-or-replace"),
                ("previousVersion", "18.0.0"), ("candidateSlot", "a"), ("previousManifestDigest", "b"*64)):
            with self.subTest(key=key):
                self.write("state/transaction.json", dict(self.transaction, **{key: value}))
                with self.assertRaisesRegex(ValueError, "SM_RECOVERY"):
                    sm_saved_test_release(self.root)
        self.write("state/transaction.json", self.transaction)

    def test_stopped_predecessor_and_foreign_selector_are_never_restored(self):
        self.write("state/stopped.json", self.installed)
        with self.assertRaisesRegex(ValueError, "SAVED_TEST_17"):
            sm_saved_test_release(self.root)
        (self.root / "state/stopped.json").unlink()
        (self.root / "active").symlink_to("slots/a")
        with self.assertRaisesRegex(ValueError, "SELECTOR_CONFLICT"):
            sm_saved_test_release(self.root)
        self.assertEqual("slots/a", (self.root / "active").readlink().as_posix())

    def test_correct_existing_selector_is_preserved(self):
        (self.root / "active").symlink_to("slots/b")
        self.assertTrue(sm_saved_test_release(self.root)["selectorPresent"])

    def test_slot_record_and_symlink_payload_are_rejected(self):
        self.write("slots/b/.aos-instance.json", dict(self.installed, ManifestDigest="c"*64))
        with self.assertRaisesRegex(ValueError, "SAVED_TEST_17"):
            sm_saved_test_release(self.root)
        self.write("slots/b/.aos-instance.json", self.installed)
        (self.root / "slots/b/foreign").symlink_to("/etc/passwd")
        with self.assertRaisesRegex(ValueError, "PAYLOAD_PATH_UNSAFE"):
            sm_saved_test_release(self.root)

    def test_wrong_capability_hash_is_rejected(self):
        self.write("slots/b/config/provider.json", dict(semanticVersion="17.0.0", capabilityManifestSha256="0"*64))
        with self.assertRaisesRegex(ValueError, "PAYLOAD_METADATA_MISMATCH"):
            sm_saved_test_release(self.root)

    def test_apply_stops_owner_restores_only_selector_then_starts_once_and_repeat_is_noop(self):
        module = "aosedge_demo_orchestrator.source_guest."
        raw = b"\x7fELF\x02" + b"\0"*13 + b"\xb7\x00" + b"test"
        digest = hashlib.sha256(raw).hexdigest()
        request = dict(target="test", sha256=digest, binary=base64.b64encode(gzip.compress(raw)).decode(), vehicle=dict(
            localVmId="d53d05cd-4c46-49c9-a896-534b23b88273", unitId="2a29c145-bbd1-4494-a0e5-d4b79e6a9db5"))
        marker = self.root / "factory-marker"
        marker.touch()
        inputs = self.root / "demo-inputs"
        inputs.mkdir()
        (inputs / "role").write_text("test\n")
        stock = self.root / "stock"
        stock.write_bytes(b"stock")
        proof = self.root / "proof"
        dropin = self.root / "dropin/proof.conf"
        paths = {"/usr/bin/aos_sm_app": stock, "/run/democtl-sm-queued-recovery": proof,
            "/run/systemd/system/aos-sm.service.d/92-democtl-sm-queued-recovery.conf": dropin}
        original_sha = hashlib.sha256
        baseline = "df141e0df7ed9dac6e74ef055e7b31994b501f9d26e1f34d50326c0f76839f86"
        observed = dict(binarySha256=None, freshnessProfile="standard", service={"ActiveState": "activating"})
        active = dict(observed, binarySha256=digest, freshnessProfile="demo-5s", service={"ActiveState": "active"})
        before = {p: p.read_bytes() for p in self.root.rglob("*.json")}
        def operation(argv, **kwargs):
            if argv[1] == "stop":
                self.assertFalse((self.root / "active").is_symlink())
            else:
                self.assertEqual("slots/b", (self.root / "active").readlink().as_posix())
            return subprocess.CompletedProcess(argv, 0)
        with patch(module + "Path", side_effect=lambda path: paths[path]), \
                patch(module + "FACTORY_INPUTS", inputs), patch(module + "FACTORY_INPUTS_MARKER", marker), \
                patch(module + "os.path.ismount", return_value=True), \
                patch(module + "hashlib.sha256", side_effect=lambda data: SimpleNamespace(hexdigest=lambda: baseline)
                    if data == b"stock" else original_sha(data)), \
                patch(module + "execute", side_effect=[observed, active, active]), \
                patch(module + "command"), patch(module + "subprocess.run", side_effect=operation) as run:
            result = sm_recover_test(request)
            self.assertTrue(result["restoredSelector"])
            self.assertTrue(result["durableRecordsPreserved"])
            self.assertTrue(sm_recover_test(request)["noOp"])
        self.assertEqual([["systemctl", "stop", "aos-sm"], ["systemctl", "start", "aos-sm"]],
            [call.args[0] for call in run.call_args_list])
        self.assertEqual(before, {p: p.read_bytes() for p in before})
