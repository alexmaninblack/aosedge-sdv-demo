# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Current source retention, without builds, runtime or external access."""
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class CurrentSourceScopeTests(unittest.TestCase):
    def test_only_accepted_interface_contracts_remain_not_prototypes(self):
        paths = {p.name for p in (ROOT / 'docs/demo/mockups').rglob('*')
                 if p.is_file() and p.name != '.DS_Store'}
        self.assertEqual(paths, {'README.md', 'aosedge-demo-interaction-specification.md',
                                 'aosedge-demo-ui-traceability-register.md'})
        self.assertFalse((ROOT / 'tests/mockups').exists())
        for name in ('build-demo-interaction-mockup', 'build-mockup-2-10.cjs'):
            self.assertFalse((ROOT / 'scripts' / name).exists())

    def test_retained_checkpoints_are_executable_input_authorities(self):
        self.assertEqual({p.name for p in (ROOT / 'workspace/checkpoints').glob('*.json')}, {
            'demo-v1.1.json', 'factory-41-candidate.json', 'factory-41-source-20261008.json',
            'installer-kit-028-candidate.json', 'installer-kit-028-source-lock.json',
            'reproduction-services-20261008.json'})

    def test_retained_release_records_cover_current_selectors_and_adapters(self):
        self.assertEqual({p.name for p in (ROOT / 'workspace/releases').glob('*.json')}, {
            'kit028-setup042.json', 'release.schema.json',
            '1.2.0-rc.1-public-build-chain-r7.json', '1.2.0-rc.1-build-chain.json',
            '1.2.0-rc.1-packaging.json', '1.2.0-rc.1-setup.json',
            '1.2.0-rc.1-source-factory-build-chain.json',
            '1.2.0-rc.1-source-factory-delivery.json',
            '1.2.0-rc.2-presenter-preview-dropbox-delivery.json'})

    def test_current_catalog_and_developer_pin_still_resolve(self):
        catalog = json.loads((ROOT / 'workspace/launcher-catalog.json').read_bytes())
        delivery = json.loads((ROOT / catalog['operatorDescriptor']).read_bytes())
        for field in ('productVersion', 'file', 'bytes', 'sha256', 'manifestSha256'):
            self.assertEqual(delivery[field], catalog['operator'][field])
        selection = json.loads((ROOT / 'workspace/current-developer-build.json').read_bytes())
        self.assertEqual(hashlib.sha256((ROOT / selection['path']).read_bytes()).hexdigest(),
                         selection['sha256'])

    def test_closed_documentation_diaries_are_not_current_product_inputs(self):
        for name in ('docs/qualification/documentation-review-2026-10-15.md',
                     'apps/presenter-ui/tests/human/full-screen-review.md'):
            self.assertFalse((ROOT / name).exists(), name)
        for name in ('docs/development/release-reproduction-r1.md',
                     'docs/qualification/m1-live-journey-2026-10-03.md',
                     'docs/qualification/kit028-setup042-source-publication-2026-10-05.md'):
            self.assertTrue((ROOT / name).is_file(), name)


if __name__ == '__main__':
    unittest.main()
