# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

from __future__ import annotations

import importlib.machinery
import importlib.util
import json
from pathlib import Path
import stat
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
HOST_TOOLS = ROOT / "scripts" / "host"
if str(HOST_TOOLS) not in sys.path:
    sys.path.insert(0, str(HOST_TOOLS))
RUNNER = ROOT / "scripts" / "host" / "aos-prov-5-4-2-compat"
DIAGNOSTIC = ROOT / "scripts" / "host" / "aos-iam-no-cloud-diagnostic"
LOCK = ROOT / "scripts" / "host" / "aos-prov-5.4.2-source-lock.json"
ONBOARD = ROOT / "scripts" / "aosvm-macos-onboard"


def load_runner():
    loader = importlib.machinery.SourceFileLoader("aos_prov_compat_test", str(RUNNER))
    specification = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(specification)
    loader.exec_module(module)
    return module


class AosProvCompatibilityTests(unittest.TestCase):
    def test_transition_normalization_matrix_is_exact(self) -> None:
        should_normalize = load_runner().should_normalize
        baseline = {
            "operation": "finish",
            "catch_inactive": True,
            "service_is_provisioning": True,
            "status_name": "UNAVAILABLE",
            "details": "Stream removed (Socket closed)",
            "postcondition_passed": True,
        }
        self.assertTrue(should_normalize(**baseline))
        accepted = dict(baseline, operation="start", details="Socket closed")
        self.assertTrue(should_normalize(**accepted))
        for field, value in (
            ("operation", None),
            ("operation", "create-key"),
            ("catch_inactive", False),
            ("service_is_provisioning", False),
            ("status_name", "UNKNOWN"),
            ("details", "Stream removed"),
            ("details", "Socket closed by peer"),
            ("postcondition_passed", False),
        ):
            candidate = dict(baseline)
            candidate[field] = value
            self.assertFalse(should_normalize(**candidate), (field, value))

    def test_lock_is_exact_and_wrappers_do_not_edit_site_packages(self) -> None:
        payload = json.loads(LOCK.read_text(encoding="utf-8"))
        self.assertEqual("5.4.2", payload["version"])
        self.assertEqual(
            {
                "__main__.py": "d64063ae80145eb44ac3697c19cce89771f40370783f420222172f7fda61a378",
                "commands/provision_v6.py": "a1206ac0f8625f2d8625530dc9a56b741f512d17f4b68f7aecfa3c4ec8386ae2",
                "communication/unit/common/__init__.py": "a34caaf2a114b3a61204b86ebb8979708f560fd75b63bc75fae641691561824a",
                "communication/unit/v6/unit_communication_v6.py": "7bdfabaefa4332ac8f2886af5723c863e268c7669444b3ba2c59419aafd7e623",
                "main.py": "a1f40f4c27ed2c73b1a0e32605354479d8231f0ce24280fc7b4cf57937d2481f",
            },
            payload["files"],
        )
        for digest in payload["files"].values():
            self.assertRegex(digest, r"^[0-9a-f]{64}$")
        runner = RUNNER.read_text(encoding="utf-8")
        diagnostic = DIAGNOSTIC.read_text(encoding="utf-8")
        self.assertIn("sys.dont_write_bytecode = True", runner)
        self.assertNotIn("write_text", runner)
        self.assertNotIn(".ApplyCert(", diagnostic)
        self.assertNotIn("CloudAPI", diagnostic)
        self.assertNotIn(".FinishProvisioning(", diagnostic)
        self.assertIn("EXPECTED_TYPES", diagnostic)
        self.assertNotIn("site-packages", runner)
        self.assertNotIn("CreateKey", runner)
        self.assertNotIn("ApplyCert", runner)
        self.assertNotIn("Cloud", runner)
        self.assertEqual(2, runner.count("operation in {\"start\", \"finish\"}"))

    def test_official_onboarding_uses_only_the_tracked_runner(self) -> None:
        source = ONBOARD.read_text(encoding="utf-8")
        self.assertIn('"$AOS_PYTHON" "$AOS_PROV_COMPAT" provision', source)
        self.assertNotIn('"$AOS_PYTHON" -m aos_prov provision', source)
        self.assertIn("--nodes 1", source)
        self.assertIn("--check-software", source)

    def test_new_host_tools_are_private_executables(self) -> None:
        for path in (RUNNER, DIAGNOSTIC):
            self.assertFalse(path.is_symlink())
            self.assertEqual(0o755, stat.S_IMODE(path.stat().st_mode))


if __name__ == "__main__":
    unittest.main()
