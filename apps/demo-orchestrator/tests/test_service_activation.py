# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import copy
import json
from pathlib import Path
import unittest
from unittest.mock import Mock, patch
import hashlib
import subprocess
import base64

from aosedge_demo_orchestrator.service_activation_guest import compose, dropin_content, restart_existing_sm, activate
from aosedge_demo_orchestrator.api import execute_operation
from aosedge_demo_orchestrator.cli import build_parser, request_from_arguments


class NativeActivationTests(unittest.TestCase):
    def test_factory_activation_result_is_not_described_as_transient(self):
        from aosedge_demo_orchestrator.application import DemoOrchestrator
        request = request_from_arguments(build_parser().parse_args([
            "service", "runtime-activate", "test", "--restart-sm"]))
        orchestrator = DemoOrchestrator(status_service=Mock(), image_catalog=Mock(),
            environment_service=Mock(), vm_service=Mock(), unit_service=Mock(), source_service=Mock())
        data = dict(state="ACTIVE", verification=dict(stage="VERIFIED"), factoryConfiguration=True)
        with patch("aosedge_demo_orchestrator.service_inputs.ServiceInputs") as inputs:
            inputs.return_value.prepare.return_value = data
            result = orchestrator.execute(request)
            self.assertIn("Packaged factory configuration reused", result.message)
            self.assertNotIn("Transient", result.message)
            inputs.return_value.prepare.assert_called_once_with("test", activate=True, restart_sm=True)
            data.pop("factoryConfiguration")
            self.assertIn("Transient native configuration", orchestrator.execute(request).message)

    def test_explicit_restart_is_test_only_and_is_not_the_default(self):
        default = request_from_arguments(build_parser().parse_args(["service", "runtime-activate", "test"]))
        self.assertFalse(default.restart_sm)
        explicit = request_from_arguments(build_parser().parse_args(["service", "runtime-activate", "test", "--restart-sm"]))
        self.assertTrue(explicit.restart_sm)
        self.assertIsNone(explicit.selection_error())
        from dataclasses import replace
        from aosedge_demo_orchestrator.models import VehicleTarget
        self.assertIsNotNone(replace(explicit, target=VehicleTarget.PRODUCTION).selection_error())
        self.assertIsNotNone(replace(explicit, action="runtime-prepare").selection_error())

    def test_existing_restart_is_exactly_one_command_and_same_binary(self):
        module = "aosedge_demo_orchestrator.service_activation_guest."
        before = dict(MainPID="11", ActiveState="active")
        after = dict(MainPID="22", ActiveState="active")
        binary = hashlib.sha256(b"current-sm").hexdigest()
        def content(path):
            return b"current-sm" if str(path).endswith("/exe") else b'{"stage":"VERIFIED"}'
        with patch(module + "command") as command, patch(module + "service", return_value=after), patch.object(Path, "read_bytes", content):
            result = restart_existing_sm(before, binary)
        command.assert_called_once_with(["systemctl", "restart", "aos-sm"], timeout=45)
        self.assertTrue(result["restarted"])
        self.assertEqual(binary, result["smBinarySha256"])
        self.assertEqual("11", result["previousMainPID"])
        with patch(module + "command", side_effect=subprocess.TimeoutExpired("systemctl", 45)) as command:
            with self.assertRaisesRegex(ValueError, "RESTART_UNCONFIRMED"):
                restart_existing_sm(before, binary)
        self.assertEqual(1, command.call_count)
        with patch(module + "command") as command, patch(module + "service", return_value=after), patch.object(Path, "read_bytes", return_value=b"different"):
            with self.assertRaisesRegex(ValueError, "BINARY_MISMATCH"):
                restart_existing_sm(before, binary)
        self.assertEqual(1, command.call_count)

    def setUp(self):
        self.resources = [dict(name="unrelated", devices=["untouched"], groups=["group"]),
            dict(name="kuksa", hosts=[dict(hostname="Server", ip="10.0.0.100")]),
            dict(name="kuksa-auth-client", sharedCount=4, groups=["aos-kuksa-clients"], mounts=[
                dict(source="/run/aos-kuksa-auth-compat", destination="/run/aosedge/platform/kuksa-auth", type="bind",
                    options=["rbind", "ro", "nosuid", "nodev", "noexec"]),
                dict(source="tmpfs", destination="/run/aosedge/secrets/kuksa", type="tmpfs",
                    options=["rw", "nosuid", "nodev", "noexec", "mode=0700", "size=65536"])])]

    def test_only_declared_mounts_change_and_repeat_is_idempotent(self):
        original = copy.deepcopy(self.resources)
        result = compose(self.resources)
        self.assertEqual(original, self.resources)
        self.assertEqual(original[:2], result[:2])
        self.assertEqual(original[2]["mounts"][0], result[2]["mounts"][0])
        self.assertEqual(original[2]["groups"], result[2]["groups"])
        self.assertEqual(4, result[2]["sharedCount"])
        self.assertIn("mode=1777", result[2]["mounts"][1]["options"])
        self.assertEqual(result, compose(result))
        for team, resource in zip(("brake", "tire"), result[-2:]):
            self.assertEqual(team + "-runtime-inputs", resource["name"])
            self.assertEqual("/run/aos-demo-service-inputs/" + team, resource["mounts"][0]["source"])
            self.assertEqual(["bind", "ro", "nosuid", "nodev", "noexec"], resource["mounts"][0]["options"])

    def test_factory_restart_reuses_exact_packaged_program_resources_and_hooks(self):
        module = "aosedge_demo_orchestrator.service_activation_guest."
        raw = b'def native_identity(): return "unit-test"\ndef snapshot(request): return {}\n'
        request = dict(role="test", action="service-runtime-activate", restartSm=True,
            vehicle=dict(systemUid="unit-test"), nativeSystemUid="unit-test",
            program=base64.b64encode(raw).decode(), programSha256=hashlib.sha256(raw).hexdigest())
        program = "/usr/libexec/aos-demo-service-inputs.py"
        hook_path = "/etc/systemd/system/aos-sm.service.d/40-aos-demo-service-inputs.conf"
        hook = "[Service]\nExecStartPre=/usr/bin/python3 -B " + program + " cold\nExecStartPost=/usr/bin/python3 -B " + program + " verify\n"
        resources = compose(self.resources)
        def content(path):
            text = str(path)
            if text == program:
                return raw
            if text.endswith("/etc/aos/sm.cfg"):
                return b'{}'
            if text.endswith("/etc/aos/resources.cfg"):
                return json.dumps(resources).encode()
            if text.endswith("/exe"):
                return b"factory-sm"
            self.fail("Unexpected read: " + text)
        with patch(module + "os.geteuid", return_value=0), \
                patch(module + "service", return_value=dict(MainPID="10", ActiveState="active", User="root")), \
                patch.object(Path, "is_symlink", return_value=False), patch.object(Path, "exists", return_value=False), \
                patch.object(Path, "is_file", lambda path: str(path) in (program, hook_path)), \
                patch.object(Path, "read_bytes", content), patch.object(Path, "read_text", return_value=hook) as read_text, \
                patch.object(Path, "write_bytes") as write, patch(module + "command") as command, \
                patch(module + "restart_existing_sm", return_value=dict(state="ACTIVE")) as restart:
            result = activate(request)
            self.assertTrue(result["factoryConfiguration"])
            self.assertFalse(result["transient"])
            restart.assert_called_once()
            write.assert_not_called()
            command.assert_not_called()
            restart.reset_mock()
            read_text.return_value = hook + "ExecStart=/unexpected\n"
            with self.assertRaisesRegex(ValueError, "FACTORY_HOOK_MISMATCH"):
                activate(request)
            restart.assert_not_called()
            read_text.return_value = hook
            resources.pop()
            with self.assertRaisesRegex(ValueError, "RESTART_REQUIRES_EXISTING_CONFIGURATION"):
                activate(request)
            restart.assert_not_called()

    def test_foreign_or_ambiguous_mounts_fail_without_modification(self):
        for wrong in ([*self.resources, self.resources[0]],
                [*self.resources, dict(name="brake-runtime-inputs", mounts=[])],
                self.resources[:2]):
            before = copy.deepcopy(wrong)
            with self.assertRaises(ValueError):
                compose(wrong)
            self.assertEqual(before, wrong)
        self.resources[2]["mounts"][1]["options"].append("exec")
        with self.assertRaisesRegex(ValueError, "OPTIONS_MISMATCH"):
            compose(self.resources)

    def test_native_configuration_has_no_executable_override_or_container_launcher(self):
        content = dropin_content()
        self.assertNotIn("ExecStart=", content)
        self.assertNotIn("aos_sm_app", content)
        self.assertNotIn("crun", content)
        self.assertIn("inputs.py cold", content)
        self.assertIn("inputs.py verify", content)
        self.assertIn("resources.cfg:/etc/aos/resources.cfg", content)
        request = request_from_arguments(build_parser().parse_args(["service", "runtime-activate", "test"]))
        self.assertEqual("service", request.domain)
        with self.assertRaises(ValueError):
            execute_operation(dict(domain="service", action="runtime-activate", target="test"), Mock())
