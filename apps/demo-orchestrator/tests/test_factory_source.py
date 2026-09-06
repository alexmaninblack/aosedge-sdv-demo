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
    def test_persistent_inputs_and_role_restart_once(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            marker = root / "marker"
            marker.write_text("1\n")
            inputs = root / "inputs"
            request = dict(role="test", generation=1, ca="PUBLIC_TEST_CA",
                vehicle=dict(unitId="unit", nodeId="node", cloud=dict(identity=dict(nodeHardwareId="hardware"))))
            with patch.object(guest, "FACTORY_INPUTS_MARKER", marker), patch.object(guest, "FACTORY_INPUTS", inputs), \
                    patch.object(guest, "command", return_value=SimpleNamespace(returncode=0, stdout="inactive\n")) as command:
                first = guest.configure(request)
                self.assertTrue(first["smRestarted"])
                self.assertEqual("test\n", (inputs / "role").read_text())
                self.assertEqual("hardware", json.loads((inputs / "viss-update-binding").read_text())["nodeId"])
                command.reset_mock()
                second = guest.configure(dict(request, generation=2))
                self.assertFalse(second["smRestarted"])
                self.assertEqual(1, command.call_count)
                self.assertEqual(2, json.loads((inputs / "selected.json").read_text())["selectedSource"]["assignmentGeneration"])
                self.assertFalse((root / "run").exists())
                self.assertTrue(guest.configure(dict(request, role="production"))["smRestarted"])
                self.assertEqual("production\n", (inputs / "role").read_text())
                command.reset_mock()
                with self.assertRaisesRegex(ValueError, "SOURCE_ROLE_INVALID"):
                    guest.configure(dict(request, role="invalid"))
                command.assert_not_called()
