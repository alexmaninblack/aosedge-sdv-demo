# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import inspect
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

from aosedge_demo_orchestrator import component_runtime as runtime
from aosedge_demo_orchestrator import factory_mainline_gates as gates


class MainlineFactoryTests(unittest.TestCase):
    def effective(self, name="aos-iamanager"):
        flags = "-DAOS_CONFIG_TYPES_FUNCTION_LEN=256"
        if name == "aos-iamanager":
            flags += " -DAOS_CONFIG_PKCS11_SESSION_POOL_MAX_SIZE=3"
        values = dict(SRCREV=gates.APP, SRCREV_default=gates.APP,
                      SRCREV_serviceupdatelib=gates.LIB, SRCREV_serviceupdateapi=gates.API,
                      BB_NO_NETWORK="1", BB_FETCH_PREMIRRORONLY="1", CXXFLAGS=flags,
                      EXTRA_OECMAKE="-DAOS_CORE_DIR=/work/service-update-deps -DFETCHCONTENT_FULLY_DISCONNECTED=ON")
        return "\n".join(('export ' if key == "CXXFLAGS" else '') + key + '="' + value + '"'
                         for key, value in values.items())

    def test_effective_exported_flags_and_matching_triplet_pass(self):
        for name in gates.MANAGERS:
            gates.check_effective(self.effective(name), name)

    def test_stale_iam_and_disabled_offline_guard_rejected(self):
        for before, after in ((gates.APP, "old"), (gates.LIB, "old"), (gates.API, "old"),
                              ('BB_NO_NETWORK="1"', 'BB_NO_NETWORK="0"'),
                              ("-DFETCHCONTENT_FULLY_DISCONNECTED=ON", "-DFETCHCONTENT_FULLY_DISCONNECTED=OFF"),
                              ("/work/service-update-deps", "/home/yocto/r61-input/ltvp-aos-core")):
            with self.subTest(before=before), self.assertRaises(ValueError):
                gates.check_effective(self.effective().replace(before, after), "aos-iamanager")

    def test_capacity_substrings_conflicting_flags_and_obsolete_allocator_rejected(self):
        valid = "-DAOS_CONFIG_TYPES_FUNCTION_LEN=256 -DAOS_CONFIG_PKCS11_SESSION_POOL_MAX_SIZE=3"
        for flags in (valid.replace("256", "2560"), valid.replace("SIZE=3", "SIZE=30"),
                      valid + " -DAOS_CONFIG_TYPES_FUNCTION_LEN=64",
                      valid + " -DAOS_CONFIG_PKCS11_SESSIONS_PER_LIB=4"):
            with self.subTest(flags=flags), self.assertRaises(ValueError):
                gates.check_flags(flags, "aos-iamanager")

    def report(self, path, count, skipped=0, disabled=0):
        root = ET.Element("testsuites", tests=str(count + disabled), failures="0", disabled=str(disabled))
        suite = ET.SubElement(root, "testsuite", skipped=str(skipped))
        for index in range(count):
            case = ET.SubElement(suite, "testcase", name=str(index), status="run")
            if index < skipped:
                ET.SubElement(case, "skipped")
        for name in ("DISABLED_PopulateHostDevices", "DISABLED_PopulateHostDevicesSymlink")[:disabled]:
            ET.SubElement(suite, "testcase", name=name, status="notrun")
        ET.ElementTree(root).write(path)

    def test_skip_and_upstream_disabled_are_not_passes(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "result.xml"
            self.report(path, 83, skipped=2)
            self.assertEqual(gates.check_gtest(path, 83, skipped=2), dict(passed=81, skipped=2, disabled=0))
            self.report(path, 42, disabled=2)
            self.assertEqual(gates.check_gtest(path, 42, disabled=2), dict(passed=42, skipped=0, disabled=2))

    def test_partial_failed_or_unexpectedly_skipped_report_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "result.xml"
            self.report(path, 3)
            for old, new in (('tests="3"', 'tests="2"'), ('failures="0"', 'failures="1"'),
                             ('skipped="0"', 'skipped="1"')):
                self.report(path, 3)
                path.write_text(path.read_text().replace(old, new))
                with self.assertRaises(ValueError):
                    gates.check_gtest(path, 3)

    def test_existing_evidence_cannot_be_blindly_retried(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(FileExistsError):
                gates.NativeGates(Path("/unused"), Path(temporary))

    def test_successor_pin_and_gate_order_preserve_factory36(self):
        self.assertEqual(runtime.FACTORY_RELEASES["6.1.1-maninblack.37"],
                         "77d99770a3d9476736da55c3e2196396899bc563")
        self.assertEqual(runtime.FACTORY_RELEASES["6.1.1-maninblack.36"],
                         "a0f88d8fc47d5e84df874883cb01872e25516fd5")
        source = inspect.getsource(runtime.build_factory)
        self.assertLess(source.index('" preflight --conf "'), source.index('"-c compile "'))
        self.assertLess(source.index('" native --root "'), source.index('"package the managers'))
        self.assertLess(source.index('" package --root "'), source.index('flags + "aos-image-vm"'))
        self.assertIn('state="BUILT_NOT_LIVE_QUALIFIED"', source)

    def test_dirty_tooling_is_rejected_before_export_or_remote_mutation(self):
        with patch.object(runtime.subprocess, "check_output", return_value=b" M file\n"), \
             patch.object(runtime.subprocess, "run") as run:
            with self.assertRaisesRegex(runtime.EnvironmentError, "COMMITTED_QUALIFICATION"):
                runtime.stage_mainline_factory_gates([], lambda *args: self.fail("unexpected remote"), "/build", "/source")
            run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
