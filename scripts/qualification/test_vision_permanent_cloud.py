# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
import unittest
from unittest.mock import patch
from urllib.parse import urlsplit, parse_qs

import vision_permanent_cloud as gate

UNIT = '4374bcb2-0613-419c-8ac9-e8458358c91c'
OTHER = '5abf6a2b-ae53-4995-a58a-91d9253057f7'
SET = '09068ddf-7bb3-4454-bbe7-e24274d30dac'
COMPONENT = '40ed2e6e-2aee-45f5-af80-3ab6928771ff'
VERSION = '691a47e5-48d9-44a2-93f2-04c1f3d67f3f'


class Cloud:
    def __init__(self, members=None, versions=None, pending=False):
        self.members = members if members is not None else [dict(id=UNIT, system_uid='current')]
        self.versions = versions or []
        self.pending, self.calls = pending, []

    def require(self, *permissions):
        pass

    def call(self, path, method='GET', **kwargs):
        assert method == 'GET' and not kwargs, 'READ_ONLY_REQUIRED'
        self.calls.append(path)
        parsed = urlsplit(path)
        if parsed.path.endswith('/send-requests/'):
            return []
        if parsed.path == 'unit-sets/':
            rows = [dict(id=SET, title='fixture', is_validation_set=True)]
        elif parsed.path == 'unit-sets/' + SET + '/units/':
            rows = self.members
        elif parsed.path == 'components/' + COMPONENT + '/versions/':
            rows = self.versions
        elif parsed.path == 'deployment-bundles/':
            rows = []
        else:
            raise AssertionError('UNEXPECTED_READ')
        return dict(items=rows, total=len(rows), offset=int(parse_qs(parsed.query)['offset'][0]))


class PermanentCloudTests(unittest.TestCase):
    def observe(self, cloud):
        request = dict(vehicles=dict(test=dict(unitId=UNIT, systemUid='current', unitSetId=SET)))
        with patch('aosedge_demo_orchestrator.component_cloud.resolve_component',
                   return_value=dict(id=COMPONENT)), patch(
                'aosedge_demo_orchestrator.component_cloud.unit_view', return_value=dict(components=[dict(
                    pending_component=dict(id=VERSION) if cloud.pending else None)])):
            return gate.inventory(cloud, request)

    def test_only_exact_current_member_passes_without_mutations(self):
        value = self.observe(Cloud())
        self.assertTrue(value['ready'])
        self.assertFalse(value['mutationAttempted'])
        self.assertTrue(value['recipientCoverage']['complete'])

    def test_foreign_verification_member_blocks_without_mutations(self):
        cloud = Cloud([dict(id=UNIT, system_uid='current'), dict(id=OTHER, system_uid='other')])
        value = self.observe(cloud)
        self.assertFalse(value['ready'])
        self.assertEqual(value['blockers'], ['COMPONENT_UNRELATED_VERIFICATION_RECIPIENT'])
        self.assertNotIn('system_uid', str(value))
        self.assertFalse(value['verificationSets'][0]['members'][1]['currentTarget'])

    def test_matching_uuid_with_changed_system_identity_is_not_adopted(self):
        value = self.observe(Cloud([dict(id=UNIT, system_uid='changed')]))
        self.assertFalse(value['ready'])
        self.assertFalse(value['verificationSets'][0]['members'][0]['currentTarget'])

    def test_version_collision_requires_reconciliation(self):
        value = self.observe(Cloud(versions=[dict(id=VERSION, version=gate.VERSIONS[gate.ROOTFS],
                                                  state='Ready', is_fake=False)]))
        self.assertFalse(value['ready'])
        self.assertIn('VISION_TARGET_VERSION_EXISTS_RECONCILE', value['blockers'])

    def test_pending_transaction_is_not_overwritten(self):
        value = self.observe(Cloud(pending=True))
        self.assertFalse(value['ready'])
        self.assertIn('VISION_PENDING_COMPONENT_RECONCILE', value['blockers'])


if __name__ == '__main__':
    unittest.main()
