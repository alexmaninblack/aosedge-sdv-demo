# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import ast
import inspect
import unittest

from aosedge_demo_orchestrator import component_runtime as runtime


class Factory36BuildTests(unittest.TestCase):
    def test_successor_has_exact_source_without_replacing_factory35(self):
        self.assertEqual(runtime.FACTORY_RELEASES["6.1.1-maninblack.35"],
                         "bb691efcbf19f1bebd74fd2ef3ae9ff0aee2bf74")
        self.assertEqual(runtime.FACTORY_RELEASES["6.1.1-maninblack.36"],
                         "a0f88d8fc47d5e84df874883cb01872e25516fd5")

    def test_successor_inherits_every_factory35_package_gate(self):
        tree = ast.parse(inspect.getsource(runtime.build_factory))
        groups = [node for node in ast.walk(tree) if isinstance(node, ast.Tuple)
                  and any(isinstance(value, ast.Constant) and value.value == "35" for value in node.elts)]
        self.assertGreaterEqual(len(groups), 6)
        for group in groups:
            self.assertIn("36", [value.value for value in group.elts])

    def test_storage_native_suite_is_a_pre_image_gate(self):
        source = inspect.getsource(runtime.build_factory)
        self.assertIn('expected_cm_tests = 45 if suffix == "36" else 19', source)
        self.assertIn("CMStorage*.*:MissingImageAndExpiry/*", source)
        self.assertLess(source.index("FACTORY_CM_STARTUP_REGRESSIONS_INCOMPLETE"),
                        source.index('flags + "aos-image-vm"'))
        self.assertIn('state="BUILT_NOT_LIVE_QUALIFIED"', source)


if __name__ == "__main__":
    unittest.main()
