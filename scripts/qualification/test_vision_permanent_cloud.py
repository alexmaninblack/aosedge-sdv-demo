# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
import unittest
import copy
import tempfile
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


class FlagMigrationTests(unittest.TestCase):
    class Account:
        def __init__(self, lose_response=False):
            self.values = {k:dict(id=k,title=v[0],is_validation_set=True,fleet='retained',
                                allow_unknown_components=False,update_strategy='MinimizeRestarts')
                           for k,v in gate.RETIRED_VERIFICATION.items()}
            self.writes = []
            self.lose_response = lose_response

        def require(self, *permissions): pass

        def pages(self, path):
            key = path.split('/')[1]
            return [dict(id=gate.RETIRED_VERIFICATION[key][1])]

        def call(self, path, method='GET', body=None):
            key = path.split('/')[1]
            if method != 'GET':
                assert method == 'PATCH' and body == dict(is_validation_set=False)
                self.writes.append((key,copy.deepcopy(body)))
                self.values[key].update(body)
                if self.lose_response: raise TimeoutError()
            return copy.deepcopy(self.values[key])

    def request(self, directory):
        return dict(operationDirectory=directory,retireVerification=dict(
            authorized=True,flagOnly=True,setIds=list(gate.RETIRED_VERIFICATION)))

    def test_exact_two_flags_only_and_lost_response_is_read_not_replay(self):
        for lost in (False,True):
            cloud = self.Account(lost)
            with tempfile.TemporaryDirectory() as directory:
                result = gate.retire_verification(cloud,self.request(directory))
            self.assertEqual(len(result),2)
            self.assertEqual(len(cloud.writes),2)
            self.assertTrue(all(v['responseReconciled']==lost and v['membersUnchanged'] for v in result))

    def test_existing_intent_prevents_replaying_a_mutation(self):
        cloud = self.Account()
        with tempfile.TemporaryDirectory() as directory:
            request = self.request(directory)
            from pathlib import Path
            (Path(directory)/('verification-'+next(iter(gate.RETIRED_VERIFICATION))+'-intent.json')).touch()
            with self.assertRaises(FileExistsError): gate.retire_verification(cloud,request)
        self.assertEqual(cloud.writes,[])

    def test_changed_scope_blocks_before_either_write(self):
        cloud = self.Account()
        list(cloud.values.values())[1]['title'] = 'foreign'
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(Exception):gate.retire_verification(cloud,self.request(directory))
        self.assertEqual(cloud.writes,[])


if __name__ == '__main__':
    unittest.main()
