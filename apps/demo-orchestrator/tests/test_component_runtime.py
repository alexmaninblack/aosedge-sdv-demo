# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import unittest
import subprocess
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from aosedge_demo_orchestrator.api import execute_operation
from aosedge_demo_orchestrator.cli import build_parser, request_from_arguments
from aosedge_demo_orchestrator.component_runtime import apply_test, build, builder, build_factory, FACTORY_VERSION, FACTORY_REVISION
from aosedge_demo_orchestrator.environment import EnvironmentError
from aosedge_demo_orchestrator.source_guest import execute


class RuntimeProofBoundaryTests(unittest.TestCase):
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
            for proof in ("stop-start", "factory-placeholder"):
                with self.assertRaises(ValueError):
                    execute(dict(action="component-sm-apply", proof=proof, target="test", vehicle={"localVmId": "another-vm"}))
            command.assert_not_called()
