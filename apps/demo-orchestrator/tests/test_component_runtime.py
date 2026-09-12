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
from aosedge_demo_orchestrator.source_guest import execute, process_wait_observation, container_runtime_observation, sm_saved_test_release, sm_recover_test, sm_apply_service_update, cm_apply_service_update, cm_restart_factory32_control


class Factory32CMControlTests(unittest.TestCase):
    def setUp(self):
        self.request = dict(action="component-cm-apply", proof="factory32-delivery-control", target="test", restartCm=True,
            vehicle=dict(localVmId="5aa1f8e4-a111-4467-a6cc-fb269c62a7a8", unitId="923b9820-999b-41bb-91db-b2a2c469e743"))
        self.cm = dict(binarySha256="85e03a5206576c71a571a46ef90345d43037ea71b2e00c77181d247be533028d",
            executable="/usr/bin/aos_cm_app", service=dict(MainPID="10", ActiveState="active"))
        self.after = dict(self.cm, service=dict(MainPID="11", ActiveState="active"))
        self.sm = dict(binarySha256="936fbd563f7e9d54651504f5aeba84fee0f3736861d30c2efb60eb564e039783",
            service=dict(MainPID="20", ActiveState="active"))

    def test_only_cm_restarts_with_no_file_or_config_mutations(self):
        with patch("aosedge_demo_orchestrator.source_guest.execute", side_effect=[self.cm, self.sm, self.after, self.sm]), \
                patch("aosedge_demo_orchestrator.source_guest.subprocess.run") as process, \
                patch("aosedge_demo_orchestrator.source_guest.command") as command:
            result = cm_restart_factory32_control(self.request)
        self.assertTrue(result["binaryUnchanged"])
        self.assertTrue(result["smPidPreserved"])
        self.assertEqual("10", result["previousPid"])
        process.assert_called_once_with(["systemctl", "restart", "aos-cm"], capture_output=True, text=True, timeout=25, check=True)
        command.assert_not_called()

    def test_wrong_target_and_missing_flag_rejected(self):
        with patch("aosedge_demo_orchestrator.source_guest.execute") as observe:
            for changes in (dict(target="production"), dict(restartCm=False), dict(vehicle={})):
                with self.assertRaisesRegex(ValueError, "AUTHORIZED_TEST_32"):
                    cm_restart_factory32_control(dict(self.request, **changes))
            observe.assert_not_called()

    def test_wrong_binary_never_restarts(self):
        with patch("aosedge_demo_orchestrator.source_guest.execute", side_effect=[dict(self.cm, binarySha256="other"), self.sm]), \
                patch("aosedge_demo_orchestrator.source_guest.subprocess.run") as process:
            with self.assertRaisesRegex(ValueError, "FACTORY_BINARIES"):
                cm_restart_factory32_control(self.request)
            process.assert_not_called()

    def test_timeout_never_retries(self):
        with patch("aosedge_demo_orchestrator.source_guest.execute", side_effect=[self.cm, self.sm]), \
                patch("aosedge_demo_orchestrator.source_guest.subprocess.run", side_effect=subprocess.TimeoutExpired("systemctl", 25)) as process:
            with self.assertRaises(subprocess.TimeoutExpired):
                cm_restart_factory32_control(self.request)
            process.assert_called_once()

    def test_changed_sm_is_not_reported_as_success(self):
        changed = dict(self.sm, service=dict(MainPID="21", ActiveState="active"))
        with patch("aosedge_demo_orchestrator.source_guest.execute", side_effect=[self.cm, self.sm, self.after, changed]), \
                patch("aosedge_demo_orchestrator.source_guest.subprocess.run"):
            with self.assertRaisesRegex(ValueError, "RESTART_UNCONFIRMED"):
                cm_restart_factory32_control(self.request)

    def test_host_repeat_and_uncertain_attempt_do_not_restart(self):
        from contextlib import nullcontext
        vehicle = dict(self.request["vehicle"], factory=dict(format="raw", path=".local/factory/test-factory.img",
            manifestPath=".local/factory/test-factory.manifest.json",
            sha256="f56e037ff6ce11d1dea769055dc160a5a9a8061bbdd2d67745a3042181be2f14"))
        state = dict(vehicles=dict(test=vehicle))
        environment = SimpleNamespace(root=Path("/fixture"), _writer=nullcontext)
        with patch("aosedge_demo_orchestrator.status.read_json", return_value=state), \
                patch("aosedge_demo_orchestrator.environment.atomic_json"), \
                patch("aosedge_demo_orchestrator.source.SourceDriver") as driver, \
                patch("aosedge_demo_orchestrator.vm.VMService"):
            driver.return_value.guest.return_value = dict(state="RESTARTED")
            apply_test(environment, "test", manager="cm", restart_cm=True)
            self.assertTrue(apply_test(environment, "test", manager="cm", restart_cm=True)["noOp"])
            driver.return_value.guest.assert_called_once()
            state["cmServiceUpdateProof"]["state"] = "RECONCILIATION_REQUIRED"
            with self.assertRaisesRegex(EnvironmentError, "PREVIOUS_ATTEMPT"):
                apply_test(environment, "test", manager="cm", restart_cm=True)
            driver.return_value.guest.assert_called_once()


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

    def test_container_observation_exposes_limits_not_secrets_or_arbitrary_argv(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            entry = root / "run/aos/runtime/11111111-1111-4111-8111-111111111111"
            entry.mkdir(parents=True)
            (entry / "config.json").write_text(json.dumps(dict(process=dict(
                args=["/usr/bin/tire-health-bootstrap", "SECRET-ARG"],
                env=["AOS_SECRET=SECRET-VALUE", "AOS_ITEM_ID=PUBLIC-ID"],
                rlimits=[dict(type="RLIMIT_NOFILE", soft=32, hard=32)]))))
            (entry / ".pid").write_text("42")
            config = dict(runtimes=[dict(plugin="container")])
            value = container_runtime_observation(root, config, root / "proc")
            row = value["containers"][0]
            self.assertEqual(32, row["rlimits"][0]["soft"])
            self.assertTrue(row["nativeEnvPresent"]["AOS_SECRET"])
            self.assertFalse(row["processAlive"])
            self.assertNotIn("SECRET-VALUE", json.dumps(value))
            self.assertNotIn("SECRET-ARG", json.dumps(value))
            config["runtimes"][0]["config"] = dict(runtimeDir="/run/../private")
            self.assertEqual("UNSUPPORTED_RUNTIME_PATH", container_runtime_observation(root, config)["state"])

    def test_factory_build_cli_and_api_use_the_same_exact_release(self):
        request = request_from_arguments(build_parser().parse_args(["image", "build", "6.1.1-maninblack.31"]))
        app = Mock()
        execute_operation(dict(domain="image", action="build", image="6.1.1-maninblack.31"), app)
        self.assertEqual(request, app.execute.call_args.args[0])
        with self.assertRaises(ValueError):
            execute_operation(dict(domain="image", action="build", image="6.1.1-maninblack.29"), app)
        request = request_from_arguments(build_parser().parse_args(["image", "build", "6.1.1-maninblack.32"]))
        execute_operation(dict(domain="image", action="build", image="6.1.1-maninblack.32"), app)
        self.assertEqual(request, app.execute.call_args.args[0])

    def test_factory_projector_is_the_same_source_as_demo_control(self):
        from aosedge_demo_orchestrator import service_inputs_guest
        from aosedge_demo_orchestrator.component_runtime import FACTORY_SOURCE
        packaged = FACTORY_SOURCE / "meta-aos-vehicle-platform/recipes-aos/aos-servicemanager/files/aos-demo-service-inputs.py"
        if not packaged.exists():
            self.skipTest("Sibling Platform source is not present in this workspace")
        self.assertEqual(Path(service_inputs_guest.__file__).read_bytes(), packaged.read_bytes())

    def test_cli_and_api_share_test_only_operations(self):
        for action in ("sm-builder-start", "sm-builder-stop", "sm-build", "sm-test", "sm-apply", "sm-status", "cm-build", "cm-test", "cm-apply", "cm-status"):
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
            for proof in ("stop-start", "factory-placeholder", "demo-clock-skew", "queued-recovery", "service-update-teardown"):
                with self.assertRaises(ValueError):
                    execute(dict(action="component-sm-apply", proof=proof, target="test", vehicle={"localVmId": "another-vm"}))
            command.assert_not_called()


class CMServiceUpdateApplyTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.raw = b"\x7fELF\x02" + b"\0" * 13 + b"\xb7\x00" + b"cm-fixture"
        self.digest = hashlib.sha256(self.raw).hexdigest()
        self.request = dict(action="component-cm-apply", proof="service-snapshot-reconciliation", target="test",
            vehicle=dict(localVmId="d53d05cd-4c46-49c9-a896-534b23b88273", unitId="2a29c145-bbd1-4494-a0e5-d4b79e6a9db5"),
            sha256=self.digest, binary=base64.b64encode(gzip.compress(self.raw)).decode())
        self.before = dict(binarySha256="8432c0ca62b3b7bebf0e20f3ae3f82d412429be44fadcd00d914dbf1170f48bc",
                           service=dict(ActiveState="active", MainPID="10"), mutation=False)
        self.after = dict(self.before, binarySha256=self.digest)
        self.sm = dict(binarySha256="3e244f438b6f2a8b9dcd08fb4f4be80b21771278e89a0cf6706d87cdec0b2b21",
                       service=dict(ActiveState="active", MainPID="20"))
        self.addCleanup(patch.stopall)
        patch("aosedge_demo_orchestrator.source_guest.Path", side_effect=lambda p: self.root / str(p).lstrip("/")).start()
        patch("aosedge_demo_orchestrator.source_guest.FACTORY_INPUTS", self.root / "factory/inputs").start()
        (self.root / "run").mkdir()
        self.observe = patch("aosedge_demo_orchestrator.source_guest.execute", side_effect=[self.before, self.sm, self.after, self.sm]).start()
        patch("aosedge_demo_orchestrator.source_guest.sm_saved_test_release", return_value={"version": "18.0.0"}).start()
        self.commands = patch("aosedge_demo_orchestrator.source_guest.command").start()
        self.process = patch("aosedge_demo_orchestrator.source_guest.subprocess.run").start()

    def test_cm_apply_restarts_only_cm_once_and_preserves_sm(self):
        result = cm_apply_service_update(self.request)
        self.assertTrue(result["smPidPreserved"])
        self.process.assert_called_once()
        self.assertEqual(["systemctl", "restart", "aos-cm"], self.process.call_args.args[0])

    def test_cm_timeout_has_no_automatic_retry(self):
        self.process.side_effect = subprocess.TimeoutExpired("systemctl", 25)
        with self.assertRaises(subprocess.TimeoutExpired):
            cm_apply_service_update(self.request)
        self.process.assert_called_once()

    def test_cm_repeat_is_noop(self):
        self.observe.side_effect = [self.after]
        self.assertTrue(cm_apply_service_update(self.request)["noOp"])
        self.process.assert_not_called()

    def test_explicit_cm_restart_preserves_existing_files_and_sm(self):
        cm_apply_service_update(self.request)
        before = {path: path.read_bytes() for path in self.root.rglob("*") if path.is_file()}
        self.process.reset_mock()
        self.commands.reset_mock()
        self.observe.side_effect = [self.after, self.sm, self.after, self.sm]
        result = cm_apply_service_update(dict(self.request, restartCm=True))
        self.assertTrue(result["explicitRestart"])
        self.assertTrue(result["smPidPreserved"])
        self.process.assert_called_once()
        self.assertEqual(["systemctl", "restart", "aos-cm"], self.process.call_args.args[0])
        self.commands.assert_not_called()
        self.assertEqual(before, {path: path.read_bytes() for path in before})

    def test_explicit_cm_restart_rejects_factory_and_foreign_dropin(self):
        self.observe.side_effect = [self.before]
        with self.assertRaisesRegex(ValueError, "ALREADY_APPLIED"):
            cm_apply_service_update(dict(self.request, restartCm=True))
        self.observe.side_effect = [self.after, self.sm]
        with self.assertRaisesRegex(ValueError, "TRANSIENT_STATE"):
            cm_apply_service_update(dict(self.request, restartCm=True))
        self.process.assert_not_called()

    def test_explicit_cm_restart_is_cli_scoped(self):
        request = request_from_arguments(build_parser().parse_args(["component", "cm-apply", "test", "--restart-cm"]))
        self.assertTrue(request.restart_cm)
        self.assertIsNone(request.selection_error())
        self.assertIsNotNone(type(request)("component", "sm-apply", request.target, restart_cm=True).selection_error())
        with self.assertRaises(ValueError):
            execute_operation(dict(domain="component", action="cm-apply", target="test", restart_cm=True), Mock())

    def test_cm_wrong_sm_or_target_never_restarts(self):
        self.observe.side_effect = [self.before, dict(self.sm, binarySha256="unexpected")]
        with self.assertRaisesRegex(ValueError, "REQUIRES_QUALIFIED_SM"):
            cm_apply_service_update(self.request)
        with self.assertRaisesRegex(ValueError, "AUTHORIZED_TEST"):
            cm_apply_service_update(dict(self.request, target="production"))
        self.process.assert_not_called()


class ServiceUpdateApplyTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.previous = "cf251da44d30aec38bd015210f08e284eb121aaff8f00feca2d74b75291a3dee"
        self.raw = b"\x7fELF\x02" + b"\0" * 13 + b"\xb7\x00" + b"test-only"
        self.digest = hashlib.sha256(self.raw).hexdigest()
        self.request = dict(action="component-sm-apply", proof="service-update-teardown", target="test",
            vehicle=dict(localVmId="d53d05cd-4c46-49c9-a896-534b23b88273", unitId="2a29c145-bbd1-4494-a0e5-d4b79e6a9db5"),
            sha256=self.digest, binary=base64.b64encode(gzip.compress(self.raw)).decode())
        self.dropin = self.root / "run/systemd/system/aos-sm.service.d/92-democtl-sm-queued-recovery.conf"
        self.dropin.parent.mkdir(parents=True)
        self.old_text = "[Service]\nBindReadOnlyPaths=/run/democtl-sm-queued-recovery/aos_sm_app:/usr/bin/aos_sm_app\n"
        self.dropin.write_text(self.old_text)
        self.before = dict(binarySha256=self.previous, service=dict(ActiveState="active"), freshnessProfile="demo-5s")
        self.after = dict(self.before, binarySha256=self.digest)
        self.addCleanup(patch.stopall)
        patch("aosedge_demo_orchestrator.source_guest.Path", side_effect=lambda path: self.root / str(path).lstrip("/")).start()
        patch("aosedge_demo_orchestrator.source_guest.FACTORY_INPUTS", self.root / "factory/inputs").start()
        self.observe = patch("aosedge_demo_orchestrator.source_guest.execute", side_effect=[self.before, self.after]).start()
        self.saved = patch("aosedge_demo_orchestrator.source_guest.sm_saved_test_release", return_value={"version": "18.0.0"}).start()
        self.command = patch("aosedge_demo_orchestrator.source_guest.command").start()
        self.process = patch("aosedge_demo_orchestrator.source_guest.subprocess.run").start()

    def test_apply_stops_and_starts_once_without_deleting_native_state(self):
        value = sm_apply_service_update(self.request)
        self.assertTrue(value["durableRecordsPreserved"])
        self.assertEqual([["systemctl", "stop", "aos-sm"], ["systemctl", "start", "aos-sm"]],
            [call.args[0] for call in self.process.call_args_list])
        self.assertIn("democtl-sm-service-update", self.dropin.read_text())

    def test_changed_baseline_does_not_stop_sm(self):
        self.before["binarySha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "BASE_MISMATCH"):
            sm_apply_service_update(self.request)
        self.process.assert_not_called()
        self.assertEqual(self.old_text, self.dropin.read_text())

    def test_rebooted_exact_factory_can_restore_directly_once(self):
        self.before["binarySha256"] = "df141e0df7ed9dac6e74ef055e7b31994b501f9d26e1f34d50326c0f76839f86"
        self.dropin.unlink()
        result = sm_apply_service_update(self.request)
        self.assertEqual(self.before["binarySha256"], result["previousBinarySha256"])
        self.assertEqual(2, self.process.call_count)

    def test_factory_restore_rejects_a_conflicting_dropin(self):
        self.before["binarySha256"] = "df141e0df7ed9dac6e74ef055e7b31994b501f9d26e1f34d50326c0f76839f86"
        with self.assertRaisesRegex(ValueError, "BASE_MISMATCH"):
            sm_apply_service_update(self.request)
        self.process.assert_not_called()

    def test_preparation_fix_replaces_exact_teardown_patch_once(self):
        self.before["binarySha256"] = "3e244f438b6f2a8b9dcd08fb4f4be80b21771278e89a0cf6706d87cdec0b2b21"
        self.dropin.write_text("[Service]\nBindReadOnlyPaths=/run/democtl-sm-service-update/aos_sm_app:/usr/bin/aos_sm_app\n")
        result = sm_apply_service_update(self.request)
        self.assertEqual(self.before["binarySha256"], result["previousBinarySha256"])
        self.assertEqual(2, self.process.call_count)
        self.assertIn("democtl-sm-service-prepare", self.dropin.read_text())

    def test_stop_failure_is_not_retried(self):
        self.process.side_effect = subprocess.TimeoutExpired("stop", 20)
        with self.assertRaises(subprocess.TimeoutExpired):
            sm_apply_service_update(self.request)
        self.assertEqual(1, self.process.call_count)
        self.assertEqual(self.old_text, self.dropin.read_text())

    def test_matching_live_binary_is_noop(self):
        self.observe.side_effect = [self.after]
        self.assertTrue(sm_apply_service_update(self.request)["noOp"])
        self.process.assert_not_called()


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

    def committed18(self):
        (self.root / "state/transaction.json").unlink()
        (self.root / "slots/b").rename(self.root / "slots/a")
        for path in self.root.rglob("*.json"):
            value = json.loads(path.read_text())
            for key in ("Version", "version", "semanticVersion"):
                if key in value:
                    value[key] = "18.0.0"
            if "slot" in value:
                value["slot"] = "a"
            path.write_text(json.dumps(value))
        cap = hashlib.sha256((self.root / "slots/a/config/capability-manifest.json").read_bytes()).hexdigest()
        self.write("slots/a/config/provider.json", dict(semanticVersion="18.0.0", capabilityManifestSha256=cap))
        patch("aosedge_demo_orchestrator.source_guest.SM_COMMITTED_CAP_SHA", cap).start()
        (self.root / "active").symlink_to("slots/a")

    def test_committed18_reapply_preserves_all_records_and_requires_existing_selector(self):
        self.committed18()
        before = {p: p.read_bytes() for p in self.root.rglob("*.json")}
        self.assertEqual("18.0.0", sm_saved_test_release(self.root, committed=True)["version"])
        self.assertEqual(before, {p: p.read_bytes() for p in self.root.rglob("*.json")})
        (self.root / "active").unlink()
        with self.assertRaisesRegex(ValueError, "SELECTOR_CONFLICT"):
            sm_saved_test_release(self.root, committed=True)

    def test_committed18_reapply_refuses_pending_or_intentionally_stopped_state(self):
        self.committed18()
        self.write("state/transaction.json", {})
        with self.assertRaisesRegex(ValueError, "TRANSACTION_PRESENT"):
            sm_saved_test_release(self.root, committed=True)
        (self.root / "state/transaction.json").unlink()
        self.write("state/stopped.json", {})
        with self.assertRaisesRegex(ValueError, "SAVED_TEST_18"):
            sm_saved_test_release(self.root, committed=True)

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
