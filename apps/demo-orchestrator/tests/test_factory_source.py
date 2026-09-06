# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import json
import tempfile
import unittest
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
                guest.initialize_factory_role(dict(request, role="production"))
                self.assertEqual("production\n", (inputs / "role").read_text())
