# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import copy
import unittest
from unittest.mock import patch
from aosedge_demo_orchestrator.subject_first_use import inspect_reference, execute
from aosedge_demo_orchestrator.service_assignment import LABELS
from aosedge_demo_orchestrator.unit_cloud import CloudFailure
from test_service_assignment import AssignmentCloud, OWNER, SP, USER, BRAKE, TIRE, SUBJECT, TIRE_SUBJECT, UNIT

class SubjectProof(unittest.TestCase):
    def setUp(self):
        self.cloud, self.provider = AssignmentCloud(), AssignmentCloud()
        self.provider.user = dict(role='service provider', ownerId=SP, userId=USER)
        self.cloud.subjects.append(copy.deepcopy(self.cloud.subject_created))
        self.cloud.subjects.append(dict(self.cloud.subject_created, id=TIRE_SUBJECT, label=LABELS['tire']))
        self.cloud.services = [dict(service=dict(id=BRAKE))]
        self.cloud.tire_services = [dict(service=dict(id=TIRE))]
    def reference(self, team='brake'):
        return dict(team=team, ownerId=OWNER, serviceProviderId=SP, createdBy=USER,
                    id=SUBJECT if team == 'brake' else TIRE_SUBJECT, serviceId=BRAKE if team == 'brake' else TIRE)
    def observe(self, reference=None):
        return inspect_reference(self.cloud, self.provider, reference or self.reference())
    def tearDown(self):
        self.assertEqual([], self.cloud.posts)
        self.assertEqual([], self.provider.posts)
    def test_first_and_repeat_observe_both_without_adopting(self):
        before = copy.deepcopy(self.cloud.__dict__)
        for _ in range(2):
            for team in LABELS:
                result = self.observe(self.reference(team))
                self.assertFalse(result['adopted'])
                self.assertEqual('EXACT_UNBOUND_REFERENCE_OBSERVED', result['status'])
        after = copy.deepcopy(self.cloud.__dict__)
        after['reads'] = before['reads']
        self.assertEqual(before, after)
    def test_label_without_exact_identity_is_never_enough(self):
        with self.assertRaisesRegex(CloudFailure, 'EXACT_REFERENCE_REQUIRED'):
            self.observe({'team':'brake', 'label':LABELS['brake']})
    def test_missing_or_duplicate_same_label_is_blocked(self):
        self.cloud.subjects.append(dict(self.cloud.subject_created, id=UNIT))
        with self.assertRaises(CloudFailure): self.observe()
        self.cloud.subjects = []
        with self.assertRaises(CloudFailure): self.observe()
    def test_changed_authority_or_creator_is_blocked(self):
        for key in ('ownerId', 'serviceProviderId', 'createdBy', 'id', 'serviceId'):
            with self.subTest(key=key), self.assertRaises((CloudFailure, StopIteration, KeyError)):
                self.observe(dict(self.reference(), **{key: UNIT}))
    def test_wrong_subject_type_priority_or_protection_is_blocked(self):
        subject = self.cloud.subjects[1]
        for key, value in (('is_group',False), ('priority',1), ('is_protected',True)):
            old = subject[key]; subject[key] = value
            with self.assertRaises(CloudFailure): self.observe()
            subject[key] = old
    def test_desired_and_reported_units_both_block_even_when_parked(self):
        for field in ('assigned', 'reported'):
            setattr(self.cloud, field, [dict(id=UNIT)])
            with self.assertRaisesRegex(CloudFailure, 'STILL_HAS_UNITS'): self.observe()
            setattr(self.cloud, field, [])
    def test_service_recipient_on_different_subject_blocks(self):
        self.cloud.service_recipients[BRAKE] = [dict(id=UNIT)]
        with self.assertRaisesRegex(CloudFailure, 'HAS_RECIPIENTS'): self.observe()
    def test_missing_extra_or_peer_service_blocks(self):
        for rows in ([], [dict(service=dict(id=TIRE))], [dict(service=dict(id=BRAKE)),dict(service=dict(id=TIRE))]):
            self.cloud.services = rows
            with self.assertRaisesRegex(CloudFailure, 'SERVICES_CHANGED'): self.observe()
    def test_permission_denials_are_not_absence(self):
        for permission in ('subjects_list','subjects_read','subjects_units_list','subjects_units_reported',
                           'subjects_services_list','services_read','services_units_list'):
            self.cloud.denied = {permission}
            with self.assertRaises(CloudFailure): self.observe()
        self.cloud.denied = set(); self.provider.denied = {'services_read'}
        with self.assertRaises(CloudFailure): self.observe()
    def test_changed_remote_state_is_reread_before_any_future_save(self):
        self.observe()
        self.cloud.assigned = [dict(id=UNIT)]
        with self.assertRaises(CloudFailure): self.observe()
    def test_incomplete_inventory_is_not_absence(self):
        original = self.cloud.call
        def broken(path, **kw):
            value = original(path, **kw)
            if path.startswith('subjects/?'): value['total'] += 1
            return value
        with patch.object(self.cloud, 'call', side_effect=broken), self.assertRaisesRegex(CloudFailure, 'INCOMPLETE'):
            self.observe()


if __name__ == '__main__': unittest.main(verbosity=2)
