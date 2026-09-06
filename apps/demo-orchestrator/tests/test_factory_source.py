# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import json
import tempfile
import unittest
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from aosedge_demo_orchestrator import source_guest as guest


class FactorySourceTests(unittest.TestCase):
    def test_role_is_initialized_before_provisioning_and_source_never_restarts_sm(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            marker = root / "marker"
            marker.write_text("1\n")
            inputs = root / "inputs"
            request = dict(role="test", generation=1, ca="PUBLIC_TEST_CA",
                vehicle=dict(unitId="unit", nodeId="node", cloud=dict(identity=dict(nodeHardwareId="hardware"))))
            with patch.object(guest, "FACTORY_INPUTS_MARKER", marker), patch.object(guest, "FACTORY_INPUTS", inputs), \
                    patch.object(guest, "FACTORY_ROLE_DROPIN", root / "role.conf"), \
                    patch.object(guest.os.path, "ismount", return_value=True), \
                    patch.object(guest, "command", return_value=SimpleNamespace(returncode=0, stdout="inactive\n")) as command:
                with self.assertRaisesRegex(ValueError, "SOURCE_FACTORY_ROLE_NOT_INITIALIZED"):
                    guest.configure(request)
                command.assert_not_called()
                self.assertFalse(guest.initialize_factory_role(request)["noOp"])
                command.reset_mock()
                first = guest.configure(request)
                self.assertFalse(first["smRestarted"])
                self.assertEqual("test\n", (inputs / "role").read_text())
                self.assertEqual("hardware", json.loads((inputs / "viss-update-binding").read_text())["nodeId"])
                command.reset_mock()
                second = guest.configure(dict(request, generation=2))
                self.assertFalse(second["smRestarted"])
                self.assertEqual(1, command.call_count)
                self.assertEqual(2, json.loads((inputs / "selected.json").read_text())["selectedSource"]["assignmentGeneration"])
                self.assertFalse((root / "run").exists())
                self.assertTrue(guest.initialize_factory_role(request)["noOp"])
                with self.assertRaisesRegex(ValueError, "SOURCE_FACTORY_ROLE_CONFLICT"):
                    guest.initialize_factory_role(dict(request, role="production"))
                command.reset_mock()
                with self.assertRaisesRegex(ValueError, "SOURCE_ROLE_INVALID"):
                    guest.configure(dict(request, role="invalid"))
                command.assert_not_called()
                (inputs / "role").unlink()
                command.return_value.stdout = "active\n"
                with self.assertRaisesRegex(ValueError, "SOURCE_FACTORY_ROLE_REQUIRES_UNPROVISIONED_VM"):
                    guest.initialize_factory_role(request)
                self.assertFalse((inputs / "role").exists())
                command.return_value.stdout = "inactive\n"
                (root / "role.conf").unlink()  # a fresh staged role, not a switch of the existing assignment
                guest.initialize_factory_role(dict(request, role="production"))
                self.assertEqual("production\n", (inputs / "role").read_text())

    def test_unmounted_role_is_written_by_sm_start_only_after_real_store_mount(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            marker = root / "marker"
            marker.write_text("1\n")
            inputs, dropin = root / "store/demo-inputs", root / "sm/role.conf"
            with patch.object(guest, "FACTORY_INPUTS_MARKER", marker), \
                    patch.object(guest, "FACTORY_INPUTS", inputs), \
                    patch.object(guest, "FACTORY_ROLE_DROPIN", dropin), \
                    patch.object(guest.os.path, "ismount", return_value=False), \
                    patch.object(guest, "command", return_value=SimpleNamespace(returncode=0, stdout="inactive\n")) as calls:
                for role in ("test", "production"):
                    if dropin.exists():
                        dropin.unlink()
                    result = guest.initialize_factory_role(dict(role=role))
                    self.assertEqual("STAGED_BEFORE_SM", result["state"])
                    self.assertFalse(inputs.exists())
                    script = dropin.read_text().split("ExecStartPre=/usr/bin/python3 -c '", 1)[1].rsplit("'", 1)[0]
                    # A missing mount fails before creating any shadow files.
                    result = subprocess.run([sys.executable, "-c", "import os; os.path.ismount=lambda p: False; " + script], capture_output=True)
                    self.assertNotEqual(0, result.returncode)
                    self.assertFalse(inputs.exists())
                    # The native SM start sequence now has the actual store.
                    result = subprocess.run([sys.executable, "-c", "import os; os.path.ismount=lambda p: True; " + script], capture_output=True)
                    self.assertEqual(0, result.returncode, result.stderr)
                    self.assertEqual(role + "\n", (inputs / "role").read_text())
                    self.assertEqual(0, subprocess.run([sys.executable, "-c", "import os; os.path.ismount=lambda p: True; " + script], capture_output=True).returncode)
                    (inputs / "role").write_text("conflicting-role\n")
                    self.assertNotEqual(0, subprocess.run([sys.executable, "-c", "import os; os.path.ismount=lambda p: True; " + script], capture_output=True).returncode)
                    (inputs / "role").unlink()
                    inputs.rmdir()
                self.assertFalse(any("start" in call.args[0] or "restart" in call.args[0] for call in calls.call_args_list))
