# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Check current reader claims against source paths, without executing owners."""
import ast
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class DocumentationReaderModelTests(unittest.TestCase):
    def test_component_entries_delegate_complete_demo_to_the_launcher(self):
        components = [
            'aos-vehicle-platform', 'carla-ego-runtime',
            'brake-health-service', 'brake-health-cloud',
            'tire-health-service', 'tire-health-cloud',
        ]
        present = 0
        for name in components:
            path = ROOT.parent / name / 'README.md'
            if not path.is_file():
                continue
            present += 1
            with self.subTest(component=name):
                text = ' '.join(path.read_text().split())
                self.assertNotIn('Only the product repository is manually cloned', text)
                self.assertIn('https://github.com/alexmaninblack/aosedge-sdv-demo', text)
                self.assertTrue('product launcher' in text or
                                'its build prepares this component automatically' in text)
        if not present:
            self.skipTest('optional component checkouts are absent')

    def test_brake_architecture_uses_real_profile_resources_not_scaffold_rules(self):
        component = ROOT.parent / 'brake-health-service'
        if not (component / 'CMakeLists.txt').is_file():
            self.skipTest('optional Brake component checkout is absent')
        text = ' '.join((component / 'docs/architecture.md').read_text().split())
        self.assertNotIn('The R-3 scaffold requests', text)
        self.assertIn('only V3 adds the accepted Brake advisory writes', text)
        self.assertIn('v3 reuses the v2 model', text)
        self.assertIn('native IAM permissions', text)
        policy = ' '.join((component / 'docs/release-policy.md').read_text().split())
        self.assertIn('persistent model, advisory, identity-ledger and outbox state', policy)
        self.assertNotIn('The diagnostic scaffold has no persistent state', policy)

    def test_service_acceptance_points_to_candidate_bound_current_evidence(self):
        present = 0
        for name in ['brake-health-service', 'tire-health-service']:
            path = ROOT.parent / name / 'docs/advisory-demo-control.md'
            if not path.is_file():
                continue
            present += 1
            with self.subTest(component=name):
                text = ' '.join(path.read_text().split())
                self.assertIn('/blob/main/docs/qualification/current-baseline.md', text)
                self.assertNotIn('Live staging and clean Factory qualification', text)
                self.assertIn('Local tests do not qualify another candidate', text)
        if not present:
            self.skipTest('optional service checkouts are absent')

    def test_gateway_decisions_keep_strict_roles_and_motion_control_separate(self):
        component = ROOT.parent / 'carla-ego-runtime'
        if not (component / 'CMakeLists.txt').is_file():
            self.skipTest('optional Gateway component checkout is absent')
        for name in ['0007-embedded-viss-endpoint.md',
                     '0009-local-external-control-channel.md']:
            with self.subTest(decision=name):
                text = ' '.join((component / 'docs/decisions' / name).read_text().split())
                self.assertIn('mTLS', text)
                self.assertIn('advisory', text)
                self.assertNotIn('has no client authentication', text)
                self.assertNotIn('All exposed nodes are sensors or attributes', text)
        control = (component / 'docs/decisions/0009-local-external-control-channel.md').read_text()
        self.assertIn('../external-control-contract.md', control)
        self.assertIn('not a motion-control interface', control)

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
