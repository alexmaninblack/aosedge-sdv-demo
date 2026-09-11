# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from aosedge_demo_orchestrator import service_inputs_guest as guest
from aosedge_demo_orchestrator.service_inputs import ServiceInputs
from aosedge_demo_orchestrator.environment import EnvironmentService, EnvironmentError, JOURNAL, atomic_json
from aosedge_demo_orchestrator.cli import build_parser, request_from_arguments
from aosedge_demo_orchestrator.api import execute_operation


class PublicInputTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        for name, value in dict(STORE=self.root / "store", PUBLIC=self.root / "public",
                CERTIFICATE=self.root / "trust.pem", FILESYSTEM_ROOT=self.root, OWNER=os.getuid()).items():
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
        self.assertTrue(guest.project(self.request)["noOp"])
        self.assertEqual(inodes, [path.stat().st_ino for path in paths])
        self.assertEqual(files, {str(path): path.stat().st_ino for directory in paths for path in directory.iterdir()})

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


class InputBoundaryTests(unittest.TestCase):
    def test_cli_engineering_mutation_not_browser_dashboard(self):
        request = request_from_arguments(build_parser().parse_args(["service", "runtime-prepare", "test"]))
        self.assertEqual("test", request.target.value)
        with self.assertRaises(ValueError):
            execute_operation(dict(domain="service", action="runtime-prepare", target="test"), Mock())

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
                driver.return_value.guest.return_value = dict(iamPublicServerUrl="main:8090", iamLocalEndpoint=dict(loopback8090Reachable=True))
                with self.assertRaisesRegex(EnvironmentError, "IDENTITY_MISMATCH"):
                    service.prepare("test")
                self.assertEqual(1, driver.return_value.guest.call_count)
                service.identity.return_value = "native-unit"
                service.prepare("test")
                self.assertEqual("service-runtime-prepare", driver.return_value.guest.call_args.args[2])
            with self.assertRaisesRegex(EnvironmentError, "TEST_ONLY"):
                service.prepare("production")
