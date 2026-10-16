# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Check current reader claims against source paths, without executing owners."""
import ast
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class DocumentationReaderModelTests(unittest.TestCase):
    def test_preparation_reference_names_the_actual_default_inputs(self):
        tree = ast.parse((ROOT / 'scripts/distribution/vehicle_inputs.py').read_text())
        defaults = {
            node.targets[0].id: ast.literal_eval(node.value)
            for node in tree.body
            if isinstance(node, ast.Assign) and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id in {
                'DEFAULT_FACTORY_CHECKPOINT', 'DEFAULT_SERVICE_CHECKPOINT',
                'VEHICLE_BUILD_INPUTS',
            }
        }
        self.assertEqual(len(defaults), 3)
        reference = (ROOT / 'contracts/portable-preparation-inputs/README.md').read_text()
        for name, path in defaults.items():
            with self.subTest(default=name):
                self.assertTrue((ROOT / path).is_file())
                self.assertIn(Path(path).name, reference)

    def test_gateway_fixture_guide_references_existing_entries(self):
        gateway = ROOT.parent / 'carla-ego-runtime'
        if not (gateway / 'CMakeLists.txt').is_file():
            self.skipTest('optional Gateway sibling checkout is absent')
        guide = (gateway / 'docs/standalone-fixtures.md').read_text()
        entries = set(re.findall(r'`((?:tools|config)/[^`\s]+)`', guide))
        self.assertGreaterEqual(len(entries), 7)
        for entry in entries:
            with self.subTest(entry=entry):
                self.assertTrue((gateway / entry).is_file(), entry)

    def test_component_status_does_not_repeat_retired_missing_artifact_claim(self):
        document = (ROOT / 'docs/requirements/components/vehicle-data-platform.md').read_text()
        self.assertNotIn('no v1/v2/v3 prepared artifact exists', document)
        self.assertNotIn('Cloud publication and live FOTA qualification are absent', document)
        self.assertIn('../../qualification/current-baseline.md', document)
        self.assertIn('../../../workspace/inputs/runtime-inputs.lock.json', document)
        self.assertIn('complete negative/recovery acceptance matrix', document)


if __name__ == '__main__':
    unittest.main()
