# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import hashlib
import json
import os
import stat
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from aosedge_demo_orchestrator import service_inputs_guest as guest
from aosedge_demo_orchestrator.service_inputs import ServiceInputs, qualified_reboot_restore
from aosedge_demo_orchestrator.environment import EnvironmentService, EnvironmentError, JOURNAL, atomic_json
from aosedge_demo_orchestrator.cli import build_parser, request_from_arguments
from aosedge_demo_orchestrator.api import execute_operation


class KuksaAuthorizationObservationTests(unittest.TestCase):
    def test_recovery_removal_is_exclusive_and_preserves_original_proof(self):
        from dataclasses import replace
        request = request_from_arguments(build_parser().parse_args([
            "service", "runtime-activate", "test", "--kac-only", "--kac-recovery-remove"]))
        self.assertTrue(request.kac_recovery_remove)
        self.assertIsNone(request.selection_error())
        for extra in (dict(kac_only=False), dict(kac_recovery=True), dict(kac_time_read_proof=True),
                      dict(kac_data_proof=True), dict(restart_sm=True)):
            self.assertIsNotNone(replace(request, **extra).selection_error())
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            environment = EnvironmentService(root, catalog=SimpleNamespace(project=root / "catalog"))
            environment._directory(".run/demo-current")
            historical = dict(state="ACTIVE", result=dict(deadlineEpoch=123))
            atomic_json(root / JOURNAL, dict(vehicles=dict(test=dict(unitId="unit", systemUid="native", localVmId="local")),
                kacRecovery=historical))
            with patch("aosedge_demo_orchestrator.service_inputs.SourceDriver") as driver:
                driver.return_value.guest.return_value = dict(state="RESTORED", originalPolicyRestored=True)
                result = ServiceInputs(environment).activate_kac("test", recovery_remove=True)
                self.assertEqual("service-kac-recovery-remove", driver.return_value.guest.call_args.args[2])
            self.assertTrue(result["originalPolicyRestored"])
            self.assertEqual(historical, json.loads((root / JOURNAL).read_text())["kacRecovery"])

    def test_recovery_is_explicit_exclusive_and_test_only(self):
        from dataclasses import replace
        args = build_parser().parse_args(["service", "runtime-activate", "test", "--kac-only", "--kac-recovery"])
        request = request_from_arguments(args)
        self.assertTrue(request.kac_recovery)
        self.assertIsNone(request.selection_error())
        for extra in (dict(kac_only=False), dict(kac_time_read_proof=True),
                      dict(kac_data_proof=True), dict(restart_sm=True)):
            self.assertIsNotNone(replace(request, **extra).selection_error())

    def test_recovery_preserves_completed_proofs_and_reconciles_runtime_on_repeat(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            environment = EnvironmentService(root, catalog=SimpleNamespace(project=root / "catalog"))
            environment._directory(".run/demo-current")
            historical = dict(state="PROVED", result=dict(originalPolicyRestored=True))
            atomic_json(root / JOURNAL, dict(vehicles=dict(test=dict(unitId="unit", systemUid="native", localVmId="local")),
                kacDataSubscriptionProof=historical, kacTimeReadProof=historical))
            with patch("aosedge_demo_orchestrator.service_inputs.SourceDriver") as driver:
                driver.return_value.guest.return_value = dict(state="ACTIVE", noOp=False)
                ServiceInputs(environment).activate_kac("test", recovery=True)
                driver.return_value.guest.return_value = dict(state="ACTIVE", noOp=True)
                result = ServiceInputs(environment).activate_kac("test", recovery=True)
                self.assertEqual(2, driver.return_value.guest.call_count)
                self.assertEqual("service-kac-recovery", driver.return_value.guest.call_args.args[2])
            self.assertTrue(result["noOp"])
            state = json.loads((root / JOURNAL).read_text())
            self.assertEqual(historical, state["kacTimeReadProof"])
            self.assertEqual(historical, state["kacDataSubscriptionProof"])

    def test_data_proof_selector_is_explicit_and_test_only(self):
        from dataclasses import replace
        args = build_parser().parse_args(["service", "runtime-activate", "test", "--kac-only", "--kac-data-proof"])
        request = request_from_arguments(args)
        self.assertTrue(request.kac_data_proof)
        self.assertIsNone(request.selection_error())
        for extra in (dict(kac_only=False), dict(kac_time_read_proof=True), dict(restart_sm=True)):
            self.assertIsNotNone(replace(request, **extra).selection_error())

    def test_completed_policy_proof_never_reapplies_on_repeat(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            environment = EnvironmentService(root, catalog=SimpleNamespace(project=root / "catalog"))
            environment._directory(".run/demo-current")
            atomic_json(root / JOURNAL, dict(vehicles=dict(test=dict(unitId="unit", systemUid="native", localVmId="local")),
                kacTimeReadProof=dict(unitId="unit", state="PROVED", result=dict(state="PROVED", originalPolicyRestored=True))))
            with patch("aosedge_demo_orchestrator.service_inputs.SourceDriver") as driver:
                result = ServiceInputs(environment).activate_kac("test", time_read_proof=True)
                driver.return_value.guest.assert_not_called()
            self.assertTrue(result["noOp"])
            self.assertEqual("RECORDED_COMPLETED_PROOF_NOT_CURRENT_READINESS", result["evidence"])

    def test_completed_subscription_proof_preserves_prior_trial_and_never_reapplies(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            environment = EnvironmentService(root, catalog=SimpleNamespace(project=root / "catalog"))
            environment._directory(".run/demo-current")
            state = dict(vehicles=dict(test=dict(unitId="unit", systemUid="native", localVmId="local")),
                kacDataProof=dict(state="PROVED", result=dict(input="MISSING_VALUE")),
                kacDataSubscriptionProof=dict(unitId="unit", state="PROVED", result=dict(state="PROVED", originalPolicyRestored=True)))
            atomic_json(root / JOURNAL, state)
            with patch("aosedge_demo_orchestrator.service_inputs.SourceDriver") as driver:
                result = ServiceInputs(environment).activate_kac("test", data_proof=True)
                driver.return_value.guest.assert_not_called()
            self.assertTrue(result["noOp"])
            self.assertEqual(state, json.loads((root / JOURNAL).read_text()))

    def test_structural_policy_gate_rejects_unrelated_or_conditional_rules(self):
        from collections import Counter
        from aosedge_demo_orchestrator import source_guest
        before = dict(terules=Counter(), types=Counter(["type old;"]))
        rules = ["allow aos_kuksa_auth_compat_t ntpd_pid_t:dir { getattr search };",
                 "allow aos_kuksa_auth_compat_t ntpd_pid_t:file { getattr open read };"]
        after = dict(before, terules=Counter(rules))
        self.assertTrue(source_guest.kac_policy_structure_delta(before, after)["exact"])
        self.assertFalse(source_guest.kac_policy_structure_delta(before,
            dict(after, types=Counter(["type changed;"])))["exact"])
        self.assertFalse(source_guest.kac_policy_structure_delta(before,
            dict(after, terules=Counter(rules + [rules[0]])))["exact"])
        self.assertFalse(source_guest.kac_policy_structure_delta(before,
            dict(after, terules=Counter([rules[0], rules[1] + " [ enabled ]:True"])))["exact"])

    @unittest.skipUnless(hasattr(os, "fork"), "requires Unix rollback guard")
    def test_leased_guard_restores_only_its_own_active_policy(self):
        from aosedge_demo_orchestrator import source_guest
        with tempfile.TemporaryDirectory() as directory:
            load, active = Path(directory) / "load", Path(directory) / "active"
            for same in (True, False):
                load.write_bytes(b"untouched")
                active.write_bytes(b"candidate" if same else b"later-policy")
                pid, fd = source_guest.arm_kac_policy_rollback(b"stock", load, timeout=0.05,
                    leased_policy=True, active_path=active)
                os.write(fd, b"L" + hashlib.sha256(b"candidate").hexdigest().encode("ascii"))
                os.close(fd)
                _, status = os.waitpid(pid, 0)
                self.assertEqual(0, status)
                self.assertEqual(b"stock" if same else b"untouched", load.read_bytes())

    @unittest.skipUnless(hasattr(os, "fork"), "requires Unix rollback guard")
    def test_rollback_guard_restores_on_eof_and_deadline_and_can_disarm(self):
        from aosedge_demo_orchestrator import source_guest
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "load"
            for mode in ("eof", "deadline", "disarm"):
                path.write_bytes(b"candidate")
                pid, fd = source_guest.arm_kac_policy_rollback(b"stock", path, timeout=0.05)
                if mode == "disarm":
                    os.write(fd, b"R")
                if mode != "deadline":
                    os.close(fd)
                _, status = os.waitpid(pid, 0)
                if mode == "deadline":
                    os.close(fd)
                self.assertEqual(0, status)
                self.assertEqual(b"candidate" if mode == "disarm" else b"stock", path.read_bytes())

    def test_temporary_policy_delta_is_exactly_read_only(self):
        from aosedge_demo_orchestrator import source_guest
        text = "Allow Rules: 2 added, 0 removed, 0 modified\n" + \
            "+ allow aos_kuksa_auth_compat_t ntpd_pid_t:dir { getattr search };\n" + \
            "+ allow aos_kuksa_auth_compat_t ntpd_pid_t:file { getattr open read };\n"
        self.assertTrue(source_guest.kac_time_policy_delta(text))
        for changed in (text.replace("open read", "open read write"), text.replace("ntpd_pid_t", "init_runtime_t"),
                        text + "Types: 1 added, 0 removed, 0 modified\n", text.replace("+ allow", "- allow", 1)):
            self.assertFalse(source_guest.kac_time_policy_delta(changed))

    def test_time_proof_is_explicit_and_excludes_sm_restart(self):
        args = build_parser().parse_args(["service", "runtime-activate", "test", "--kac-only", "--kac-time-read-proof"])
        request = request_from_arguments(args)
        self.assertTrue(request.kac_time_read_proof)
        self.assertIsNone(request.selection_error())
        from dataclasses import replace
        self.assertIsNotNone(replace(request, kac_only=False).selection_error())
        self.assertIsNotNone(replace(request, restart_sm=True).selection_error())

    def test_protocol_probe_sends_status_only_and_drops_payload_secrets(self):
        from aosedge_demo_orchestrator import source_guest
        def run(args):
            return SimpleNamespace(returncode=0, stdout="\n\n".join(
                "Id=" + unit + "\nActiveState=inactive\nMainPID=0" for unit in args[2:-1]) if args[0] == "systemctl" else "")
        def metadata(path):
            if str(path) == "/run/aos-kuksa-auth-compat/request.sock":
                return SimpleNamespace(st_uid=999, st_gid=997, st_mode=stat.S_IFSOCK | 0o660, st_mtime=1)
            raise FileNotFoundError
        with patch.object(source_guest, "command", side_effect=run), patch.object(Path, "lstat", metadata), \
                patch.object(source_guest.socket, "socket") as factory:
            client = factory.return_value.__enter__.return_value
            client.recv.return_value = b'{"status":"ready","jwt":"do-not-export","aosSecret":"do-not-export"}\n'
            result = source_guest.kuksa_authorization_observation()
        self.assertEqual({"status": "ready"}, result["protocolStatus"])
        self.assertNotIn("do-not-export", json.dumps(result))
        client.sendall.assert_called_once_with(b'{"protocol":"aos-kuksa-auth-compat/v1","operation":"status"}\n')

    def test_kac_only_cli_and_incompatible_restart(self):
        args = build_parser().parse_args(["service", "runtime-activate", "test", "--kac-only"])
        request = request_from_arguments(args)
        self.assertTrue(request.kac_only)
        self.assertIsNone(request.selection_error())
        from dataclasses import replace
        self.assertIsNotNone(replace(request, restart_sm=True).selection_error())
        self.assertIsNotNone(replace(request, action="runtime-inspect").selection_error())

    def test_kac_start_and_repeat_touch_no_other_unit(self):
        from aosedge_demo_orchestrator import source_guest
        import copy
        unit = "aos-kuksa-auth-compat.service"
        before = dict(state="CURRENT", services={unit:dict(ActiveState="inactive", MainPID="0", NRestarts="0"),
            "aos-kuksa-verifier-prepare.service":dict(ActiveState="active")},
            inputs={name:dict(present=True, symlink=False) for name in ("provisioned", "signingPin", "verifier", "requestDirectory")})
        after = copy.deepcopy(before)
        after["services"][unit].update(ActiveState="active", MainPID="42")
        request = dict(role="test", vehicle=dict(unitId="unit", systemUid="native"))
        with patch.object(source_guest.os, "geteuid", return_value=0), patch.object(Path, "read_text", return_value="native"), \
                patch.object(source_guest, "kuksa_authorization_observation", side_effect=[before, after, after]), \
                patch.object(source_guest, "command", return_value=SimpleNamespace(returncode=0)) as run:
            self.assertEqual("ACTIVE", source_guest.activate_kac(request)["state"])
            self.assertTrue(source_guest.activate_kac(request)["noOp"])
        self.assertEqual([["systemctl", "is-active", "--quiet", "aos-iam.service"], ["systemctl", "start", unit]],
            [call.args[0] for call in run.call_args_list])
        before["inputs"]["verifier"]["present"] = False
        with patch.object(source_guest.os, "geteuid", return_value=0), patch.object(Path, "read_text", return_value="native"), \
                patch.object(source_guest, "kuksa_authorization_observation", return_value=before), \
                patch.object(source_guest, "command") as run:
            with self.assertRaisesRegex(ValueError, "PREREQUISITE_MISSING"):
                source_guest.activate_kac(request)
            run.assert_not_called()

    def test_startup_probe_is_read_only_and_excludes_secret_messages(self):
        from aosedge_demo_orchestrator import source_guest
        calls = []
        def run(args):
            calls.append(args)
            if args[0] == "systemctl":
                units = args[2:-1]
                return SimpleNamespace(returncode=0, stdout="\n\n".join(
                    "Id=" + unit + "\nActiveState=failed\nExecMainStatus=1\nEnvironment=secret" for unit in units))
            messages = ["aos-kuksa-auth-compat: startup stage=bind failed errno=13",
                        "AOS_SECRET=do-not-export", "verifier-prepare: stage=ready secret=do-not-export"]
            return SimpleNamespace(returncode=0, stdout="\n".join(json.dumps(dict(
                _SYSTEMD_UNIT="aos-kuksa-auth-compat.service", __REALTIME_TIMESTAMP="123", MESSAGE=value))
                for value in messages))
        with patch.object(source_guest, "command", side_effect=run), patch.object(Path, "lstat", side_effect=FileNotFoundError):
            result = source_guest.kuksa_authorization_observation()
        self.assertEqual("CURRENT", result["state"])
        self.assertFalse(result["mutation"])
        self.assertEqual(["systemctl", "show"], calls[0][:2])
        self.assertEqual("journalctl", calls[1][0])
        self.assertEqual(5, len(calls))
        self.assertEqual(["journalctl", "-k"], calls[2][:2])
        self.assertEqual(["systemctl", "show"], calls[3][:2])
        self.assertEqual("findmnt", calls[4][0])
        self.assertEqual(13, result["startupEvents"][0]["errno"])
        self.assertEqual(1, len(result["startupEvents"]))
        self.assertNotIn("do-not-export", json.dumps(result))
        self.assertNotIn("Environment", json.dumps(result))
        self.assertEqual({"present": False}, result["inputs"]["signingPin"])

    def test_failed_reads_are_not_reported_as_current_or_clean(self):
        from aosedge_demo_orchestrator import source_guest
        with patch.object(source_guest, "command", return_value=SimpleNamespace(returncode=1, stdout="")), \
                patch.object(Path, "lstat", side_effect=FileNotFoundError):
            result = source_guest.kuksa_authorization_observation()
        self.assertEqual("INCOMPLETE", result["state"])
        self.assertEqual("UNAVAILABLE", result["journalState"])


class PublicInputTests(unittest.TestCase):
    def test_reboot_restore_requires_exact_test_current_sm_and_empty_containers(self):
        import copy
        item = dict(localVmId="d53d05cd-4c46-49c9-a896-534b23b88273", unitId="2a29c145-bbd1-4494-a0e5-d4b79e6a9db5")
        state = dict(factory=dict(sha256="a9019f4adfe70499bde339c8e9d95eb8568736b73dc218f6c0e390fbcd28ddf4"),
            smServiceUpdateProof=dict(state="APPLIED", result=dict(
                binarySha256="3e244f438b6f2a8b9dcd08fb4f4be80b21771278e89a0cf6706d87cdec0b2b21",
                service=dict(MainPID="123"))))
        observed = dict(serviceManager=dict(MainPID="123", ActiveState="active"),
            nativeContainers=dict(state="CURRENT", containers=[]))
        self.assertTrue(qualified_reboot_restore(state, item, observed))
        for key in item:
            self.assertFalse(qualified_reboot_restore(state, dict(item, **{key: "other"}), observed))
        changed = copy.deepcopy(observed)
        changed["serviceManager"]["MainPID"] = "124"
        self.assertFalse(qualified_reboot_restore(state, item, changed))
        changed = copy.deepcopy(observed)
        changed["nativeContainers"]["containers"] = [dict(id="still-running")]
        self.assertFalse(qualified_reboot_restore(state, item, changed))
        self.assertFalse(qualified_reboot_restore({}, item, observed))

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        for name, value in dict(STORE=self.root / "store", PUBLIC=self.root / "public",
                CERTIFICATE=self.root / "trust.pem", FILESYSTEM_ROOT=self.root, OWNER=os.getuid(),
                IAM_CONFIG=self.root / "iam.cfg", MACHINE_ID=self.root / "machine-id", STARTUP=self.root / "startup").items():
            change = patch.object(guest, name, value)
            change.start()
            self.addCleanup(change.stop)
        self.request = dict(role="test", nativeSystemUid="native-unit", vehicle=dict(systemUid="native-unit"))
        self.record = dict(schemaVersion=1, slot="a", Version="18.0.0", ManifestDigest="sha256:" + "a" * 64,
            ItemId="vdp", SubjectId="unit", Instance=0, RuntimeId="runtime-vdp", Preinstalled=False)
        self.put("demo-inputs/role", b"test\n")
        self.put("state/installed.json", self.record)
        self.put("slots/a/.aos-instance.json", self.record)
        self.put("slots/a/component.json", dict(version="18.0.0"))
        self.capability = dict(semanticVersion="18.0.0", contracts=dict(vdpCompatibility=dict(
            contractId="aosedge-demo-vdp-compatibility", contractVersion="1.0.1", sha256="b" * 64)))
        self.put("slots/a/config/capability-manifest.json", self.capability)
        self.provider = dict(semanticVersion="18.0.0", capabilityManifestSha256=hashlib.sha256(
            (guest.STORE / "slots/a/config/capability-manifest.json").read_bytes()).hexdigest())
        self.put("slots/a/config/provider.json", self.provider)
        (guest.STORE / "active").symlink_to("slots/a")
        self.argv = [b"provider", b"--config", str(guest.STORE / "slots/a/config/provider.json").encode()]
        for name, value in (("provider_process", ("42", self.argv)), ("trust", b"public certificate fixture")):
            change = patch.object(guest, name, return_value=value)
            change.start()
            self.addCleanup(change.stop)
        guest.CERTIFICATE.write_bytes(b"public certificate fixture")
        guest.MACHINE_ID.write_text("native-unit\n")
        identifier = dict(plugin="fileidentifier", params=dict(systemIDPath=str(guest.MACHINE_ID)))
        guest.IAM_CONFIG.write_text(json.dumps(dict(identifier=identifier)))
        guest.STARTUP.mkdir(mode=0o700)

    def put(self, name, value):
        path = guest.STORE / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value if isinstance(value, bytes) else json.dumps(value).encode())

    def test_first_create_exact_five_fields_modes_and_stable_repeat(self):
        previous = os.umask(0o077)
        try:
            result = guest.project(self.request)
        finally:
            os.umask(previous)
        self.assertEqual("PREPARED", result["state"])
        self.assertEqual(4, len(result["changed"]))
        self.assertFalse(result["resourcesActivated"])
        self.assertFalse(result["containerActions"])
        self.assertFalse(result["coldStartQualified"])
        self.assertEqual(dict(schemaVersion=2, unitSystemUid="native-unit", unitRole="validation",
            vdpContractVersion="1.0.1", vdpContractSha256="b" * 64), result["metadata"])
        paths = [guest.PUBLIC / team for team in ("brake", "tire")]
        inodes = [path.stat().st_ino for path in paths]
        files = {str(path): path.stat().st_ino for directory in paths for path in directory.iterdir()}
        for directory in paths:
            self.assertEqual(0o755, directory.stat().st_mode & 0o777)
            for path in directory.iterdir():
                self.assertEqual(0o444, path.stat().st_mode & 0o777)
        with patch.object(guest, "snapshot", wraps=guest.snapshot) as observe, patch.object(guest.os, "fsync") as sync:
            self.assertTrue(guest.project(self.request)["noOp"])
            self.assertEqual(2, observe.call_count)
            sync.assert_not_called()
        self.assertEqual(inodes, [path.stat().st_ino for path in paths])
        self.assertEqual(files, {str(path): path.stat().st_ino for directory in paths for path in directory.iterdir()})

    def test_unchanged_repeat_still_rejects_active_transaction_and_source_race(self):
        guest.project(self.request)
        files = {path: path.read_bytes() for path in guest.PUBLIC.rglob("*") if path.is_file()}
        transaction = guest.STORE / "state/transaction.json"
        transaction.write_text("{}")
        with self.assertRaisesRegex(ValueError, "COMPONENT_TRANSACTION_ACTIVE"):
            guest.project(self.request)
        transaction.unlink()
        original = guest.snapshot(self.request)
        with patch.object(guest, "snapshot", side_effect=[original, dict(original, pid="99")]):
            with self.assertRaisesRegex(ValueError, "SOURCE_CHANGED"):
                guest.project(self.request)
        self.assertEqual(files, {path: path.read_bytes() for path in files})

    def test_committed_refresh_changes_files_not_directories(self):
        guest.project(self.request)
        inode = (guest.PUBLIC / "brake").stat().st_ino
        self.capability["contracts"]["vdpCompatibility"]["contractVersion"] = "1.0.2"
        self.put("slots/a/config/capability-manifest.json", self.capability)
        self.provider["capabilityManifestSha256"] = hashlib.sha256((guest.STORE / "slots/a/config/capability-manifest.json").read_bytes()).hexdigest()
        self.put("slots/a/config/provider.json", self.provider)
        result = guest.project(self.request)
        self.assertEqual(["brake/metadata.json", "tire/metadata.json"], result["changed"])
        self.assertEqual(inode, (guest.PUBLIC / "brake").stat().st_ino)
        self.assertEqual("1.0.2", result["metadata"]["vdpContractVersion"])

    def test_volatile_files_absent_without_provider_do_not_claim_cold_ready(self):
        guest.provider_process.side_effect = ValueError("SERVICE_INPUT_PROVIDER_NOT_RUNNING")
        with self.assertRaisesRegex(ValueError, "PROVIDER_NOT_RUNNING"):
            guest.project(self.request)
        self.assertFalse(guest.PUBLIC.exists())

    def test_identity_role_and_active_transaction_fail_before_writes(self):
        for request in (dict(self.request, role="production"), dict(self.request, nativeSystemUid="other")):
            with self.assertRaisesRegex(ValueError, "IDENTITY_MISMATCH"):
                guest.project(request)
        self.put("demo-inputs/role", b"production\n")
        with self.assertRaisesRegex(ValueError, "ROLE_MISMATCH"):
            guest.project(self.request)
        self.put("demo-inputs/role", b"test\n")
        self.put("state/transaction.json", dict(phase="waiting-for-safe-stop"))
        with self.assertRaisesRegex(ValueError, "TRANSACTION_ACTIVE"):
            guest.project(self.request)
        self.assertFalse(guest.PUBLIC.exists())

    def test_no_intermediate_slot_or_corrupt_manifest_projection(self):
        self.put("slots/a/.aos-instance.json", dict(self.record, Version="19.0.0"))
        with self.assertRaisesRegex(ValueError, "SLOT_RECORD_MISMATCH"):
            guest.project(self.request)
        self.put("slots/a/.aos-instance.json", self.record)
        self.put("slots/a/config/capability-manifest.json", dict(self.capability, semanticVersion="19.0.0"))
        with self.assertRaisesRegex(ValueError, "CAPABILITY_MISMATCH"):
            guest.project(self.request)
        self.assertFalse(guest.PUBLIC.exists())

    def test_wrong_running_slot_and_source_race_fail_closed(self):
        guest.provider_process.return_value = ("42", [b"provider", b"--config", b"wrong-slot"])
        with self.assertRaisesRegex(ValueError, "PROCESS_SLOT_MISMATCH"):
            guest.project(self.request)
        guest.provider_process.return_value = ("42", self.argv)
        original = guest.snapshot(self.request)
        with patch.object(guest, "snapshot", side_effect=[original, dict(original, pid="99")]):
            with self.assertRaisesRegex(ValueError, "SOURCE_CHANGED"):
                guest.project(self.request)
        self.assertFalse(any(guest.PUBLIC.rglob("metadata.json")))
        self.assertFalse(any(guest.PUBLIC.rglob(".democtl-input-*")))

    def test_symlink_extra_files_and_world_writable_paths_refused(self):
        guest.PUBLIC.symlink_to(guest.STORE, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "SYMLINK"):
            guest.project(self.request)
        guest.PUBLIC.unlink()
        (guest.PUBLIC / "tire").mkdir(parents=True)
        (guest.PUBLIC / "tire/token.jwt").write_bytes(b"synthetic forbidden fixture")
        with self.assertRaisesRegex(ValueError, "DIRECTORY_CONFLICT"):
            guest.project(self.request)
        guest.CERTIFICATE.chmod(0o666)
        with self.assertRaisesRegex(ValueError, "OWNER_OR_MODE"):
            guest.read_public(guest.CERTIFICATE)

    def test_projection_failure_never_prints_raw_exception_or_certificate(self):
        with patch.object(guest.os, "geteuid", return_value=0), patch.object(guest, "project", side_effect=ValueError("sensitive fixture")), patch("builtins.print") as output:
            guest.main(dict(self.request, action="service-runtime-prepare"))
        value = json.loads(output.call_args.args[0])
        self.assertEqual(dict(ok=False, reason="SERVICE_INPUT_PREPARATION_FAILED"), value)

    def test_cold_restore_without_provider_then_native_process_verification(self):
        guest.STARTUP.rmdir()  # A clean image has no transient activation files.
        guest.provider_process.side_effect = ValueError("SERVICE_INPUT_PROVIDER_NOT_RUNNING")
        with patch.object(guest.os, "geteuid", return_value=0), patch("builtins.print"):
            cold = guest.startup("cold")
            self.assertEqual("PREPARED", cold["stage"])
            self.assertFalse(cold["processVerified"])
            guest.provider_process.assert_not_called()
            guest.provider_process.side_effect = None
            verified = guest.startup("verify")
            self.assertEqual("VERIFIED", verified["stage"])
            self.assertTrue(verified["processVerified"])

    def test_interrupted_update_withholds_public_data_without_rewriting_recovery(self):
        guest.project(self.request)
        transaction = dict(schemaVersion=2, phase="installing", previous=dict(self.record), candidate=dict(Version="19.0.0"))
        self.put("state/transaction.json", transaction)
        before = (guest.STORE / "state/transaction.json").read_bytes()
        with patch.object(guest.os, "geteuid", return_value=0), patch("builtins.print"):
            deferred = guest.startup("cold")
        self.assertEqual("DEFERRED", deferred["stage"])
        self.assertEqual("SERVICE_INPUT_COMPONENT_TRANSACTION_ACTIVE", deferred["reason"])
        self.assertFalse(any(guest.PUBLIC.rglob("metadata.json")))
        self.assertEqual(before, (guest.STORE / "state/transaction.json").read_bytes())
        self.assertEqual(self.record, json.loads((guest.STORE / "state/installed.json").read_bytes()))

    def test_cold_restore_rejects_non_native_identity_source(self):
        guest.IAM_CONFIG.write_text(json.dumps(dict(identifier=dict(plugin="visidentifier"))))
        with patch.object(guest.os, "geteuid", return_value=0), patch("builtins.print"):
            result = guest.startup("cold")
        self.assertEqual("DEFERRED", result["stage"])
        self.assertEqual("SERVICE_INPUT_NATIVE_IDENTIFIER_UNSUPPORTED", result["reason"])
        self.assertFalse(any(guest.PUBLIC.rglob("metadata.json")))
        self.assertTrue((guest.PUBLIC / "brake").is_dir())

    def test_factory_without_vdp_leaves_empty_mounts_and_does_not_block_sm(self):
        (guest.STORE / "state/installed.json").unlink()
        with patch.object(guest.os, "geteuid", return_value=0), patch("builtins.print"):
            result = guest.startup("cold")
        self.assertEqual("DEFERRED", result["stage"])
        self.assertFalse(result["processVerified"])
        self.assertFalse(any(guest.PUBLIC.rglob("metadata.json")))
        for team in ("brake", "tire"):
            self.assertEqual(0o755, stat.S_IMODE((guest.PUBLIC / team).stat().st_mode))

    def test_post_start_cannot_verify_another_process_slot(self):
        guest.project(self.request, cold=True)
        guest.provider_process.return_value = ("42", [b"provider", b"--config", b"wrong-slot"])
        with patch.object(guest.os, "geteuid", return_value=0), patch("builtins.print"):
            result = guest.startup("verify")
        self.assertEqual("DEFERRED", result["stage"])
        self.assertFalse(result["processVerified"])
        self.assertEqual("SERVICE_INPUT_PROCESS_SLOT_MISMATCH", result["reason"])


class InputBoundaryTests(unittest.TestCase):
    def test_input_preparation_is_fixed_test_step_not_standalone_browser_action(self):
        request = request_from_arguments(build_parser().parse_args(["service", "runtime-prepare", "test"]))
        self.assertEqual("test", request.target.value)
        application = Mock()
        execute_operation(dict(domain="service", action="runtime-prepare", target="test"), application)
        self.assertEqual(request, application.execute.call_args.args[0])
        application.reset_mock()
        for extra in (dict(target="production"), dict(target="all"), dict(target=None),
                dict(restart_sm=True), dict(path="/tmp/input"), dict(team="brake")):
            with self.assertRaises(ValueError):
                execute_operation(dict(dict(domain="service", action="runtime-prepare", target="test"), **extra), application)
        for action in ("runtime-activate", "runtime-inspect"):
            with self.assertRaises(ValueError):
                execute_operation(dict(domain="service", action=action, target="test"), application)
        application.execute.assert_not_called()
        from aosedge_demo_orchestrator.presenter_operations import operation_plan
        from uuid import uuid4
        with self.assertRaises(ValueError):
            operation_plan(dict(requestId=str(uuid4()), sessionId=str(uuid4()), action="runtime-prepare"))

    def test_host_reconciles_native_identity_before_guest_write_no_cloud(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            environment = EnvironmentService(root, catalog=SimpleNamespace(project=root / "catalog"))
            state = dict(vehicles=dict(test=dict(unitId="cloud-unit", systemUid="native-unit", localVmId="local-vm", sshPort=2222)))
            (root / JOURNAL).parent.mkdir(parents=True, mode=0o700)
            atomic_json(root / JOURNAL, state)
            service = ServiceInputs(environment)
            service.identity = Mock(return_value="other")
            with patch("aosedge_demo_orchestrator.service_inputs.SourceDriver") as driver:
                driver.return_value.guest.return_value = dict(iamPublicServerUrl="main:8090", iamLocalEndpoint=dict(loopback8090Reachable=True),
                    iamFileIdentifier=dict(plugin="fileidentifier", path="/etc/machine-id", systemUid="native-unit"))
                with self.assertRaisesRegex(EnvironmentError, "IDENTITY_MISMATCH"):
                    service.prepare("test")
                self.assertEqual(1, driver.return_value.guest.call_count)
                self.assertEqual({"identityOnly": True}, driver.return_value.guest.call_args.kwargs)
                service.identity.return_value = "native-unit"
                service.prepare("test")
                self.assertEqual("service-runtime-prepare", driver.return_value.guest.call_args.args[2])
            with self.assertRaisesRegex(EnvironmentError, "TEST_ONLY"):
                service.prepare("production")

    def test_activation_keeps_full_runtime_inspection(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        environment = EnvironmentService(root, catalog=SimpleNamespace(project=root / "catalog"))
        environment._directory(".run/demo-current")
        atomic_json(root / JOURNAL, dict(vehicles=dict(test=dict(unitId="cloud-unit", systemUid="native-unit", localVmId="local-vm"))))
        service = ServiceInputs(environment)
        service.identity = Mock(return_value="native-unit")
        with patch("aosedge_demo_orchestrator.service_inputs.SourceDriver") as driver:
            driver.return_value.guest.return_value = dict(iamPublicServerUrl="main:8090", iamLocalEndpoint=dict(loopback8090Reachable=True),
                iamFileIdentifier=dict(plugin="fileidentifier", path="/etc/machine-id", systemUid="native-unit"),
                resources=[dict(name=name) for name in ("brake-runtime-inputs", "tire-runtime-inputs")])
            service.prepare("test", activate=True)
            self.assertEqual({"identityOnly": False}, driver.return_value.guest.call_args_list[0].kwargs)
            self.assertEqual("service-runtime-activate", driver.return_value.guest.call_args.args[2])
