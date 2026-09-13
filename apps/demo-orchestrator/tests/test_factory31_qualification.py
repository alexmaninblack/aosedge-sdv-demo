# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import io
import unittest
from pathlib import Path
from types import SimpleNamespace
from contextlib import redirect_stderr
from unittest.mock import Mock, patch

from aosedge_demo_orchestrator.cli import main
from aosedge_demo_orchestrator.environment import EnvironmentService, EnvironmentError
from aosedge_demo_orchestrator.vm import VMService
from test_connectivity import ConnectivityServiceTests


class QualificationTests(unittest.TestCase):
    def test_ports_are_isolated_and_default_context_is_unchanged(self):
        with patch("aosedge_demo_orchestrator.environment.project_root", return_value=Path("/workspace/aosedge-sdv-demo")):
            default = EnvironmentService(root="/workspace/aosedge-sdv-demo")
            control = EnvironmentService(root="/workspace/aosedge-sdv-demo-qual-31")
            self.assertFalse(default.factory31_comparison)
            self.assertEqual(10022, default.ssh_port("test"))
            self.assertEqual(10023, default.ssh_port("production"))
            self.assertTrue(control.factory31_comparison)
            self.assertEqual(11022, control.ssh_port("test"))
            control.catalog = Mock()
            control.catalog.resolve.return_value = SimpleNamespace(selector="wrong")
            with self.assertRaisesRegex(EnvironmentError, "ORIGINAL_TEST_IMAGE"):
                control.create("test", "wrong")
            with self.assertRaisesRegex(EnvironmentError, "STATE_MISMATCH"):
                VMService(control)._validate(dict(vehicles={"production": {}}), "start", ["production"])

    def test_cli_rejects_non_control_operations_before_root_creation(self):
        for argv in (["vm", "start", "production"], ["unit", "delete", "production"],
                ["component", "cm-apply", "test", "--restart-cm"], ["simulation", "start"],
                ["ui", "serve"], ["environment", "create", "--image", "wrong", "--target", "test"]):
            with self.subTest(argv=argv), patch.object(Path, "mkdir") as mkdir, redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    main(["--qualification", "factory31", *argv])
                mkdir.assert_not_called()


class IsolatedConnectivityTests(ConnectivityServiceTests):
    def test_isolated_link_control_does_not_select_carla_or_change_peer(self):
        self.source.environment.factory31_comparison = True
        self.source.environment.ssh_port.side_effect = lambda role: 11022
        self.state.update(currentVehicle=None, source={})
        self.state["vehicles"] = {"test": dict(self.state["vehicles"]["test"], sshPort=11022)}
        self.source.driver.guest.side_effect = [{"state": "ON"}, {"state": "OFF"}]
        self.assertEqual("OFF", self.service.execute("off", "test")["state"])
        self.source.vm._validate.assert_called_once_with(self.state, "start", ["test"])
        self.assertIsNone(self.state["currentVehicle"])
        self.state["source"] = {"state": "RUNNING"}
        with self.assertRaisesRegex(EnvironmentError, "SOURCE_MUST_REMAIN_DETACHED"):
            self.service.execute("off", "test")
