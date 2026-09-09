# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
import unittest
from unittest.mock import patch
from aosedge_demo_orchestrator.component_runtime import factory_component_support, FACTORY_REVISION
from aosedge_demo_orchestrator.environment import EnvironmentError


class FactoryCompatibilityTests(unittest.TestCase):
    def test_declaration_uses_packaged_source_schema_not_release_version_guess(self):
        paths = tuple("Vehicle.Signal" + str(number) for number in range(23))
        with patch("aosedge_demo_orchestrator.component_runtime.runpy.run_path", return_value={
                "BASE_PATHS": paths[:7], "WHEEL_PATHS": paths[7:15], "SLIP_PATHS": paths[15:]}):
            value = factory_component_support(FACTORY_REVISION)
        self.assertEqual(list(paths), value["supportedReadPaths"])
        self.assertEqual(FACTORY_REVISION, value["sourceRevision"])
        self.assertNotIn("qualified", value)

    def test_unpinned_source_and_incomplete_schema_fail_before_build(self):
        with self.assertRaisesRegex(EnvironmentError, "SOURCE_REVISION_MISMATCH"):
            factory_component_support("b" * 40)
        with patch("aosedge_demo_orchestrator.component_runtime.runpy.run_path", return_value={
                "BASE_PATHS": ("Vehicle.Speed",), "WHEEL_PATHS": (), "SLIP_PATHS": ()}):
            with self.assertRaisesRegex(EnvironmentError, "SCHEMA_DECLARATION_MISMATCH"):
                factory_component_support(FACTORY_REVISION)
