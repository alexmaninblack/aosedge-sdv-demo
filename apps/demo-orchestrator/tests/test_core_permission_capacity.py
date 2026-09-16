# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import base64
import gzip
import hashlib
import json
import tempfile
import unittest
from contextlib import nullcontext
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import patch

from aosedge_demo_orchestrator import component_runtime as runtime
from aosedge_demo_orchestrator import source_guest as guest
from aosedge_demo_orchestrator.api import execute_operation
from aosedge_demo_orchestrator.cli import build_parser, request_from_arguments
from aosedge_demo_orchestrator.environment import EnvironmentError


class PermissionCapacityTests(unittest.TestCase):
    def test_iam_reply_fix_uses_function_capacity_not_resource_capacity(self):
        files = runtime.permission_recipe_inputs(iam_response_capacity=True)
        patches = [data.decode() for name, data in files.items() if name.endswith(".patch")]
        self.assertEqual(1, len(patches))
        self.assertIn("cFunctionsMaxCount", patches[0])
        # Seventeen exact Tire permissions fit the registered native 32-entry
        # map, but do not fit the stock RPC's wrong 16-service count.
        from aosedge_demo_orchestrator.service_packages import package_configuration
        root = Path(__file__).resolve().parents[3]
        permissions = package_configuration(root, "tire", "v1", "99.0.0")["items"][0]["configuration"]["permissions"]["kuksa"]
        self.assertGreater(len(permissions), 16)
        self.assertLessEqual(len(permissions), 32)

    def test_all_current_service_profiles_and_advisory_fit_native_capacity(self):
        from aosedge_demo_orchestrator.service_packages import package_configuration
        root = Path(__file__).resolve().parents[3]
        limits = {( "brake", "v1"): (6, 41), ("brake", "v2"): (12, 50),
                  ("brake", "v3"): (14, 50), ("tire", "v1"): (17, 62)}
        for (team, profile), (count, longest) in limits.items():
            permissions = package_configuration(root, team, profile, "99.0.0")["items"][0]["configuration"]["permissions"]["kuksa"]
            self.assertEqual(count, len(permissions))
            self.assertEqual(longest, max(len(path.encode("utf-8")) for path in permissions))
            self.assertLessEqual(len(permissions), 32)
            self.assertTrue(all(len(path.encode("utf-8")) <= 256 for path in permissions))
            advisory = json.loads((root / "contracts/qm-advisory-profile/qm-advisory-profile.v1.json").read_text())
            if profile == "v3" or team == "tire":
                endpoint = next(item for item in advisory["endpoints"] if item["ownerService"] == team.upper() + "_HEALTH")
                self.assertEqual("rw", permissions[endpoint["requestPath"]])
                self.assertEqual("r", permissions[endpoint["statusPath"]])

    def test_vdp_snapshot_preserves_current_committed_version(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "state").mkdir()
            (root / "slots/a").mkdir(parents=True)
            record = json.dumps(dict(schemaVersion=1, slot="a", Version="66.0.0"))
            (root / "state/installed.json").write_text(record)
            (root / "slots/a/.aos-instance.json").write_text(record)
            (root / "active").symlink_to("slots/a")
            self.assertEqual(hashlib.sha256(record.encode()).hexdigest(), guest.core_permission_vdp_snapshot(root))
            record = json.dumps(dict(schemaVersion=1, slot="a", Version="67.0.0"))
            (root / "state/installed.json").write_text(record)
            (root / "slots/a/.aos-instance.json").write_text(record)
            self.assertEqual(hashlib.sha256(record.encode()).hexdigest(), guest.core_permission_vdp_snapshot(root))
            (root / "state/transaction.json").write_text("{}")
            with self.assertRaisesRegex(ValueError, "TRANSACTION"):
                guest.core_permission_vdp_snapshot(root)

    def test_cli_test_scope_and_no_public_ui_action(self):
        for action in ("core-permissions-build", "core-permissions-apply", "core-permissions-status"):
            args = build_parser().parse_args(["component", action, "test"])
            self.assertEqual(action, request_from_arguments(args).action)
            with self.assertRaises(ValueError):
                execute_operation(dict(domain="component", action=action, target="test"), None)

    def test_recipe_gate_allows_only_capacity_not_unrelated_source_change(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(runtime, "SOURCE", Path(directory)), \
                patch.object(runtime.subprocess, "check_output", return_value=b'BASE = "unchanged"\n'):
            paths = []
            for recipe in runtime.PERMISSION_RECIPES.values():
                path = Path(directory) / f"meta-aos-vehicle-platform/recipes-aos/{recipe}/{recipe}_git.bbappend"
                path.parent.mkdir(parents=True)
                path.write_text('# capacity only\nBASE = "unchanged"\nCXXFLAGS:append = " -DAOS_CONFIG_TYPES_FUNCTION_LEN=256"\n')
                paths.append(path)
            self.assertEqual(3, len(runtime.permission_recipe_inputs()))
            for content in ('BASE = "changed"\n', 'CXXFLAGS:append = " -DAOS_CONFIG_TYPES_FUNCTION_LEN=128"\n'):
                paths[0].write_text(content)
                with self.assertRaises(EnvironmentError):
                    runtime.permission_recipe_inputs()

    def test_build_rejects_wrong_target_without_builder(self):
        with patch.object(runtime, "builder") as builder:
            with self.assertRaises(EnvironmentError):
                runtime.build_permissions("production")
            builder.assert_not_called()

    def test_iam_reply_apply_rejects_changed_process_before_files_or_stop(self):
        observed = dict(transientFilesMatchProcesses=True,
            managers={name: dict(binarySha256="actual", service=dict(ActiveState="active")) for name in ("iam", "sm", "cm")})
        with patch.object(guest, "core_permission_status", return_value=observed), patch.object(guest, "command") as command:
            with self.assertRaisesRegex(ValueError, "PREVIOUS_PROCESS_CHANGED"):
                guest.core_iam_response_apply(dict(previous={name: "wrong" for name in ("iam", "sm", "cm")}))
            command.assert_not_called()

    def test_iam_reply_apply_preserves_cm_vdp_and_original_binary(self):
        raw = b"\x7fELF\x02\x01" + b"\0" * 12 + b"\xb7\x00" + b"fixture"
        digest = hashlib.sha256(raw).hexdigest()
        before = dict(transientFilesMatchProcesses=True,
            managers={name: dict(binarySha256="old-" + name, service=dict(ActiveState="active", MainPID="10")) for name in ("iam", "sm", "cm")})
        after = json.loads(json.dumps(before))
        after["managers"]["iam"]["binarySha256"] = digest
        after["managers"]["iam"]["service"]["MainPID"] = "11"
        request = dict(previous={name: "old-" + name for name in ("iam", "sm", "cm")},
            binary=dict(sha256=digest, data=base64.b64encode(gzip.compress(raw)).decode()))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "run").mkdir()
            dropin = root / "run/systemd/system/aos-iam.service.d/96-democtl-permission-capacity.conf"
            dropin.parent.mkdir(parents=True)
            dropin.write_text("[Service]\nBindReadOnlyPaths=/run/democtl-core-permissions-256/aos_iam_app:/usr/bin/aos_iam_app\n")
            with patch.object(guest, "Path", side_effect=lambda value: root / str(value).lstrip("/")), \
                    patch.object(guest, "core_permission_status", side_effect=[before, after]), \
                    patch.object(guest, "core_permission_vdp_snapshot", return_value="unchanged"), \
                    patch.object(guest, "command"), patch.object(guest.subprocess, "run") as run:
                result = guest.core_iam_response_apply(request)
            self.assertTrue(result["cmPreserved"])
            self.assertTrue(result["durableVdpPreserved"])
            self.assertEqual([['systemctl', 'stop', 'aos-sm'], ['systemctl', 'stop', 'aos-iam'],
                ['systemctl', 'start', 'aos-iam'], ['systemctl', 'start', 'aos-sm']], [call.args[0] for call in run.call_args_list])
            self.assertEqual(raw, (root / "run/democtl-iam-response-32/aos_iam_app").read_bytes())

    def test_uncertain_apply_reconciles_matching_processes_without_restart(self):
        raw = b"fixture ELF"
        sha = hashlib.sha256(raw).hexdigest()
        managers = ("iam", "sm", "cm")
        info = {name: dict(sha256=sha, size=len(raw)) for name in managers}
        manifest = dict(state="BUILT", capacity=256, binaries=info,
            baseRevision=runtime.FACTORY_RELEASES["6.1.1-maninblack.33"])
        state = dict(vehicles=dict(test=dict(localVmId=runtime.PERMISSION_VM, unitId=runtime.PERMISSION_UNIT,
            factory=dict(sha256="a302b2f2e2f238b361682ab8a529ec036ff260e00b2fb9a4d21db325d8d45761"))),
            corePermissionCapacityProof=dict(state="RECONCILIATION_REQUIRED"))
        observed = dict(managers={name: dict(binarySha256=sha, service=dict(ActiveState="active")) for name in managers},
            committedVdp66Sha256="verified", transientFilesMatchProcesses=True)
        with tempfile.TemporaryDirectory() as directory, patch.object(runtime, "PERMISSION_ARTIFACT", Path(directory)), \
                patch("aosedge_demo_orchestrator.status.read_json", side_effect=lambda p: manifest if p.name == "manifest.json" else state), \
                patch("aosedge_demo_orchestrator.environment.factory_for", return_value=state["vehicles"]["test"]["factory"]), \
                patch("aosedge_demo_orchestrator.environment.atomic_json"), \
                patch("aosedge_demo_orchestrator.source.SourceDriver") as driver, \
                patch("aosedge_demo_orchestrator.vm.VMService"):
            for name in managers:
                (Path(directory) / ("aos_" + name + "_app")).write_bytes(raw)
            driver.return_value.guest.return_value = observed
            result = runtime.apply_permissions(SimpleNamespace(root=Path(directory), _writer=nullcontext), "test")
            self.assertTrue(result["noOp"])
            self.assertEqual("APPLIED", state["corePermissionCapacityProof"]["state"])
            driver.return_value.guest.assert_called_once()
            self.assertEqual("core-permissions-status", driver.return_value.guest.call_args.args[2])

    def test_guest_rejects_foreign_identity_before_read_or_write(self):
        for request in ({}, dict(target="production"), dict(target="test", role="test", vehicle={})):
            with patch.object(guest, "command") as command:
                with self.assertRaises(ValueError):
                    guest.core_permission_apply(request)
                command.assert_not_called()

    def test_guest_requires_all_managers_before_touching_files(self):
        with patch.object(guest, "core_permission_status", return_value={}):
            with self.assertRaisesRegex(ValueError, "ALL_THREE"):
                guest.core_permission_apply(dict(binaries={"sm": {}}))

    def test_guest_rejects_corrupt_binary_before_stopping_any_manager(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = b"original"
            sha = hashlib.sha256(original).hexdigest()
            for name in ("iam", "sm", "cm"):
                path = root / f"usr/bin/aos_{name}_app"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(original)
            request = dict(previous={name: sha for name in ("iam", "sm", "cm")},
                binaries={name: dict(data=base64.b64encode(gzip.compress(b"not an ELF")).decode(), sha256=sha)
                          for name in ("iam", "sm", "cm")})
            observation = dict(managers={name: dict(binarySha256=sha, service=dict(ActiveState="active"))
                                        for name in ("iam", "sm", "cm")})
            with patch.object(guest, "Path", side_effect=lambda value: root / str(value).lstrip("/")), \
                    patch.object(guest, "core_permission_status", return_value=observation), \
                    patch.object(guest, "command") as command, patch.object(guest.subprocess, "run") as run:
                with self.assertRaisesRegex(ValueError, "ARM64_DIGEST"):
                    guest.core_permission_apply(request)
                command.assert_not_called()
                run.assert_not_called()
            self.assertFalse((root / "run/democtl-core-permissions-256").exists())


if __name__ == "__main__":
    unittest.main()
