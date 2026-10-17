# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Check current reader claims against source paths, without executing owners."""
import ast
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class DocumentationReaderModelTests(unittest.TestCase):
    def test_cloud_first_use_explains_role_emails_and_real_certificate_limits(self):
        guide = ' '.join((ROOT / 'docs/getting-started/installed-preview-cloud-first-use.md').read_text().split())
        for term in ('id="new-cloud-access"', 'two welcome emails',
                     'OEM issuance token', 'Service Provider issuance token',
                     'Copy **only that token**', 'Do not run the email',
                     'unencrypted `.p12`', 'RSA package-signing',
                     'not your email password', 'cannot approve your registration'):
            self.assertIn(term, guide)
        for url in ('https://aoscloud.io/',
                    'https://aws-stage.epmp-aos.projects.epam.com/',
                    'https://docs.aosedge.tech/docs/how-to/register-your-users/create-first-account'):
            self.assertIn(url, guide)
        native = (ROOT / 'scripts/distribution/native/Setup.swift').read_text()
        self.assertIn('OEM issuance token', native)
        self.assertIn('Service Provider issuance token', native)
        self.assertIn('CLOUD_PACKAGE_SIGNING_RSA_KEY_REQUIRED', native)
        self.assertIn('unencrypted PKCS#12', native)

    def test_vm_password_is_a_scoped_public_development_default(self):
        helper = (ROOT / 'scripts/host/aosvm-expect-password').read_text()
        public_default = re.search(r'^set password "([^"\n]+)"$', helper, re.M).group(1)
        guide = ' '.join((ROOT / 'docs/getting-started/installed-preview-cloud-first-use.md').read_text().split())
        self.assertIn('`' + public_default + '`', guide)
        for text in ('public test password', 'not your Mac, Apple or Aos Cloud password',
                     'Save in Keychain', 'different/custom image',
                     'not suitable for a real vehicle'):
            self.assertIn(text, guide)

    def test_first_drive_uses_actual_controls_and_separates_quick_preparation(self):
        guide = ' '.join((ROOT / 'docs/operations/current-demo-workflow.md').read_text().split())
        studio = (ROOT / 'apps/presenter-ui/src/app/StudioWorkspace.tsx').read_text()
        for label in ('Full story', 'Quick preparation', 'Create controller',
                      'Start simulator', 'Sign & publish', 'Provision to Test',
                      'Connect in Manual', 'Assign to Test', 'Refresh publication',
                      'Refresh Cloud state', 'Continue preparation'):
            with self.subTest(label=label):
                self.assertIn(label, guide)
                self.assertIn(label, studio)
        self.assertIn('Expected result / next step', guide)
        self.assertIn('No manual certificate or Gateway configuration is needed', guide)
        self.assertIn('Do not also repeat Full story', guide)
        self.assertIn('only after the preceding version has installed', guide)
        native = ROOT.parent / 'carla-ego-runtime/tools/KeyboardControl.swift'
        if native.is_file():
            for label in ('BRAKE MANEUVER', 'TIRE MANEUVER'):
                self.assertIn(label, native.read_text())
                self.assertIn(label, guide)

    def test_own_dmg_installation_does_not_reenter_published_route_a(self):
        guide = ' '.join((ROOT / 'docs/getting-started/reproduce-demo.md').read_text().split())
        for text in ('id="install-your-build"', 'double-click that DMG',
                     'AosEdge SDV Lab Setup',
                     'Do **not** return to route A', 'exact checksum',
                     'Do not change the public catalog'):
            self.assertIn(text, guide)
        install = (ROOT / 'scripts/launcher/install-macos.sh').read_text()
        self.assertIn('size=$(route_field operator.bytes)', install)
        self.assertIn('digest=$(route_field operator.sha256)', install)
        self.assertIn('DMG checksum differs', install)
        first_use = (ROOT / 'docs/getting-started/installed-preview-cloud-first-use.md').read_text()
        self.assertIn('reproduce-demo.md#install-your-build', first_use)

    def test_source_changes_are_not_claimed_as_an_arbitrary_b_working_tree_build(self):
        contribution = ' '.join((ROOT / 'CONTRIBUTING.md').read_text().split())
        for text in ('id="from-a-source-change-to-your-own-installer"',
                     'git clone https://github.com/alexmaninblack/aosedge-sdv-demo.git',
                     'frozen build inputs', 'nativeSources', 'producers',
                     'repository-map.json', 'successor cache namespace',
                     'no downloaded-launcher option to build arbitrary dirty working trees'):
            self.assertIn(text, contribution)
        readme = ' '.join((ROOT / 'README.md').read_text().split())
        self.assertIn('reproduce the selected project build', readme)
        self.assertNotIn('You want to change project components or build an installer', readme)
        bootstrap = (ROOT / 'scripts/developer_bootstrap.py').read_text()
        self.assertIn('Existing source has local changes', bootstrap)

    def test_fresh_source_selection_keeps_old_receipts_and_caches(self):
        guide = ' '.join((ROOT / 'docs/getting-started/unified-macos-launcher.md').read_text().split())
        for text in ('id="start-a-new-build-selection"', '**new empty parent folder**',
                     '--route B --parent', 'Keep the prior workspace, caches and outputs intact',
                     'Do not edit `root-source.json`'):
            self.assertIn(text, guide)
        build = (ROOT / 'docs/getting-started/reproduce-demo.md').read_text()
        self.assertIn('unified-macos-launcher.md#start-a-new-build-selection', build)

    def test_resource_and_signing_guidance_does_not_claim_a_cold_build_peak(self):
        guide = ' '.join((ROOT / 'docs/getting-started/macos-developer-tools.md').read_text().split())
        for text in ('id="apple-signing-access"', 'Settings → Accounts',
                     'Manage Certificates', 'private key',
                     'id="capacity-planning"', 'not a 90 GiB total allowance',
                     'not a measured cold-build upper bound',
                     'no established universal RAM minimum',
                     "Docker's backing disk"):
            self.assertIn(text, guide)

    def test_contributor_and_fresh_parent_commands_parse_without_running_them(self):
        for relative in ('CONTRIBUTING.md',
                         'docs/getting-started/unified-macos-launcher.md'):
            blocks = re.findall(r'```sh\n(.*?)```', (ROOT / relative).read_text(), re.S)
            self.assertTrue(blocks)
            for block in blocks:
                with self.subTest(document=relative, block=block):
                    result = subprocess.run(['/bin/sh', '-n'], input=block,
                                            text=True, capture_output=True, timeout=5)
                    self.assertEqual(result.returncode, 0, result.stderr)

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
