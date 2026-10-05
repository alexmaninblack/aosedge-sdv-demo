# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Real miniature files; synthetic authority only, no live Cloud or demo data."""
import copy
import json
import unittest
from unittest.mock import Mock, patch

from aosedge_demo_orchestrator import environment, service_assignment
from aosedge_demo_orchestrator.vm import VMService
from test_images_environment import ImagesAndCreateTests
from test_service_assignment import OWNER, USER, BRAKE, SUBJECT, TIRE, TIRE_SUBJECT


class SingleRetirementTests(unittest.TestCase):
    setUp = ImagesAndCreateTests.setUp
    create = ImagesAndCreateTests.create

    def prepared(self):
        state = self.create('test')
        state['stage'] = 'LOCAL_STOPPED'
        test = state['vehicles']['test']
        test.update(unitId=test['localVmId'], nodeId=test['localVmId'], unitSetId=test['localVmId'],
                    systemUid='synthetic-unit', cloud=dict(lifecycle='DELETED', absenceConfirmed=True),
                    runtime=dict(state='STOPPED', pid=None, everStarted=True))
        state['selectedCloudDomain'] = 'aws-stage.epmp-aos.projects.epam.com'
        subjects, operations = {}, {}
        for team, service, subject in [('brake', BRAKE, SUBJECT), ('tire', TIRE, TIRE_SUBJECT)]:
            subjects[service] = dict(ownerId=OWNER, id=subject, label=service_assignment.LABELS[team],
                isGroup=True, priority=0, createdBy=USER, create=dict(stage='CONFIRMED'))
            operations[service] = dict(ownerId=OWNER, serviceId=service, team=team, state='ASSIGNED',
                test={key: test[key] for key in ('unitId', 'systemUid', 'unitSetId')},
                steps={step: dict(stage='CONFIRMED') for step in ('bind', 'assign')})
        state['cloudContexts'] = {state['selectedCloudDomain']:
            dict(selectedOwners=dict(oem=OWNER), tenants={OWNER:
                dict(cloudBinding=dict(ownerId=OWNER), demoSubjects=subjects)})}
        state['serviceOperations'] = operations
        self.write(state)
        return state

    def write(self, state):
        environment.atomic_json(self.root / environment.JOURNAL, state)

    def test_full_finish_and_repeat_preserves_factory_config_and_ledger(self):
        state = self.prepared()
        entries = service_assignment.retirement_subjects(state)
        self.assertEqual({SUBJECT, TIRE_SUBJECT}, {v['id'] for v in entries})
        config = self.root / '.local/demo-control/status.json'
        config.parent.mkdir(parents=True)
        config.write_text('{"retained":"operator-configuration"}')
        ledger = self.root / '.local/release-continuity.json'
        ledger.write_text('{"vdp":120}')
        before = config.read_bytes(), ledger.read_bytes(), self.source.read_bytes()
        observed = []
        def check(current):
            observed.append(service_assignment.retirement_subjects(current))
            return True
        with patch.object(self.service, '_assert_unheld'):
            result = self.service.retire_test(cloud_check=check)
            self.assertEqual('REMOVED', result['outcome'])
            self.assertEqual('NO_CURRENT_ENVIRONMENT', self.service.retire_test()['outcome'])
        self.assertGreaterEqual(len(observed), 2)
        self.assertTrue(all(value == entries for value in observed))
        self.assertEqual(before, (config.read_bytes(), ledger.read_bytes(), self.source.read_bytes()))
        self.assertFalse((self.root / environment.JOURNAL).exists())
        self.assertFalse((self.root / state['vehicles']['test']['overlay']).exists())

    def test_uncertain_service_foreign_target_owner_and_steps_block_without_unlink(self):
        state = self.prepared()
        for field, value in [('state', 'UNCERTAIN'), ('ownerId', USER), ('steps', {}),
                             ('test', dict(state['serviceOperations'][BRAKE]['test'], unitId=USER))]:
            with self.subTest(field=field):
                wrong = copy.deepcopy(state)
                wrong['serviceOperations'][BRAKE][field] = value
                self.write(wrong)
                with patch.object(self.service, '_assert_unheld'), self.assertRaises(environment.EnvironmentError):
                    self.service.retire_test(cloud_check=lambda current: True)
                self.assertTrue((self.root / state['vehicles']['test']['overlay']).exists())

    def test_fresh_absence_failure_precedes_backend_cleanup(self):
        state = self.prepared()
        state['backends'] = {'synthetic': {}}
        self.write(state)
        backend = Mock(return_value=True)
        with self.assertRaisesRegex(environment.EnvironmentError, 'FRESH_CLOUD_RETIREMENT'):
            self.service.retire_test(cloud_check=lambda current: False, backend_check=backend)
        backend.assert_not_called()

    def test_interrupted_child_unlink_keeps_receipt_and_rechecks_cloud(self):
        self.prepared()
        original = self.service._unlink_owned
        def interrupt(path, identity):
            original(path, identity)
            if path.name == 'validation.qcow2':
                raise OSError('synthetic interruption')
        with patch.object(self.service, '_assert_unheld'), patch.object(self.service, '_unlink_owned', side_effect=interrupt):
            with self.assertRaises(OSError):
                self.service.retire_test(cloud_check=lambda current: True)
        self.assertTrue((self.root / environment.JOURNAL).exists())
        check = Mock(return_value=True)
        with patch.object(self.service, '_assert_unheld'):
            result = self.service.retire_test(cloud_check=check)
        self.assertEqual('REMOVED', result['outcome'])
        self.assertGreaterEqual(check.call_count, 2)

    def test_unknown_root_field_and_wrong_scope_remain_rejected(self):
        state = self.prepared()
        for edit in [dict(unknown=True), dict(stage='RETIRING_LOCAL', runtimeCleanup={}, scope='DUAL')]:
            with self.subTest(edit=edit):
                wrong = dict(state, **edit)
                self.write(wrong)
                with self.assertRaises(environment.EnvironmentError):
                    self.service.retire_test(cloud_check=lambda current: True)
                self.assertTrue((self.root / state['vehicles']['test']['overlay']).exists())

    def test_malformed_interrupted_receipt_never_reaches_cloud_or_unlink(self):
        state = self.prepared()
        state.update(stage='RETIRING_LOCAL', retirement={}, runtimeCleanup={})
        self.write(state)
        cloud = Mock(return_value=True)
        with self.assertRaises(environment.EnvironmentError):
            self.service.retire_test(cloud_check=cloud)
        cloud.assert_not_called()

    def test_full_cleanup_entry_also_validates_service_receipts(self):
        state = self.prepared()
        state['serviceOperations'][TIRE]['state'] = 'UNCERTAIN'
        self.write(state)
        with self.assertRaisesRegex(environment.EnvironmentError, 'SERVICE_RETIREMENT'):
            self.service.retire(cloud_check=lambda current: True)
        self.assertTrue((self.root / state['vehicles']['test']['overlay']).exists())

    def test_changed_cloud_authority_on_resume_preserves_remaining_files(self):
        state = self.prepared()
        original = self.service._unlink_owned
        def interrupt(path, identity):
            original(path, identity)
            if path.name == 'validation.qcow2':
                raise OSError('synthetic interruption')
        with patch.object(self.service, '_assert_unheld'), patch.object(self.service, '_unlink_owned', side_effect=interrupt):
            with self.assertRaises(OSError):
                self.service.retire_test(cloud_check=lambda current: True)
        with self.assertRaisesRegex(environment.EnvironmentError, 'FRESH_CLOUD_RETIREMENT'):
            self.service.retire_test(cloud_check=lambda current: False)
        self.assertTrue((self.root / state['factory']['path']).exists())
        self.assertTrue((self.root / environment.JOURNAL).exists())

    def dns_log(self):
        state = self.prepared()
        state['shared'] = dict(dns=dict(ownerId=state['vehicles']['test']['localVmId'], state='STOPPED', pid=None))
        self.write(state)
        path = self.root / '.run/demo-current/dns-bridge.log'
        path.write_text('synthetic bridge log')
        path.chmod(0o600)
        return state, path

    def test_owned_stopped_dns_log_is_removed(self):
        state, path = self.dns_log()
        with patch.object(self.service, '_assert_unheld'), patch.object(VMService, '_processes', return_value=[]):
            result = self.service.retire_test(cloud_check=lambda current: True)
        self.assertFalse(path.exists())
        self.assertEqual('REMOVED', result['outcome'])

    def test_unknown_dns_log_is_preserved(self):
        state, path = self.dns_log()
        state['shared'] = {}
        self.write(state)
        with self.assertRaisesRegex(environment.EnvironmentError, 'DNS_LOG_CLEANUP_OWNERSHIP'):
            self.service.retire_test(cloud_check=lambda current: True)
        self.assertTrue(path.exists())

    def test_live_dns_owner_blocks_cleanup(self):
        state, path = self.dns_log()
        with patch.object(VMService, '_processes', return_value=[(123, 'bridge --owner-id '+state['shared']['dns']['ownerId'])]):
            with self.assertRaisesRegex(environment.EnvironmentError, 'DNS_MUST_BE_STOPPED'):
                self.service.retire_test(cloud_check=lambda current: True)
        self.assertTrue(path.exists())

    def test_linked_dns_log_is_preserved(self):
        state, path = self.dns_log()
        path.unlink()
        path.symlink_to(self.source)
        with patch.object(VMService, '_processes', return_value=[]), self.assertRaises(environment.EnvironmentError):
            self.service.retire_test(cloud_check=lambda current: True)
        self.assertTrue(path.is_symlink())
        self.assertTrue(self.source.exists())


if __name__ == '__main__':
    unittest.main()
