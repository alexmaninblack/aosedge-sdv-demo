# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Synthetic credentials only; no real keys, network or running instance."""

from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import NameOID

from aosedge_demo_orchestrator import runtime_paths
from aosedge_demo_orchestrator.cloud_connection import CloudConnection, CONFIG, inspect_certificate
from aosedge_demo_orchestrator.environment import EnvironmentService, JOURNAL, atomic_json
from aosedge_demo_orchestrator.cloud_setup import inspect_setup
from test_cloud_setup import CloudFixture, REQUEST, SP


def certificate(path, domain='stage.example.test', expired=False, encrypted=False, use_ec=False):
    key = (ec.generate_private_key(ec.SECP256R1()) if use_ec else
           rsa.generate_private_key(public_exponent=65537, key_size=2048))
    name = x509.Name([x509.NameAttribute(NameOID.ORGANIZATION_NAME, domain)])
    now = datetime.now(timezone.utc)
    cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key())
            .serial_number(x509.random_serial_number()).not_valid_before(now - timedelta(days=2))
            .not_valid_after(now + timedelta(days=-1 if expired else 2)).sign(key, hashes.SHA256()))
    encryption = serialization.BestAvailableEncryption(b'synthetic-only') if encrypted else serialization.NoEncryption()
    path.write_bytes(pkcs12.serialize_key_and_certificates(b'fixture', key, cert, None, encryption))
    path.chmod(0o600)


class PairTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='pair.', dir='/tmp')
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.state = self.root / 'state'
        identity = runtime_paths.create_instance(self.state)['instanceId']
        atomic_json(self.state / 'installation.json', dict(current='0'*64, revision=1))
        context = patch.object(runtime_paths, '_active', runtime_paths.Layout(self.state, self.root, self.root, identity))
        context.start(); self.addCleanup(context.stop)
        self.env = EnvironmentService(root=self.state)
        self.connection = CloudConnection(self.env)
        self.oem, self.sp = self.root/'oem.p12', self.root/'sp.p12'
        certificate(self.oem); certificate(self.sp)
        # Exercise cryptographic parsing locally, no SDK subprocess/network.
        inspector = patch.object(self.connection, 'inspect', side_effect=inspect_certificate)
        inspector.start(); self.addCleanup(inspector.stop)

    def preview(self): return self.connection.inspect_pair(str(self.oem), str(self.sp))

    def save(self, token): return self.connection.select_pair(str(self.oem), str(self.sp), token)

    def test_preview_save_and_idempotent_repeat(self):
        result = self.preview()
        self.assertFalse((self.state/CONFIG).exists())
        self.assertFalse(result['rolesChecked'])
        saved = self.save(result['selectionToken'])
        path = self.state/CONFIG
        before, modified = path.read_bytes(), path.stat().st_mtime_ns
        self.save(saved['selectionToken'])
        self.assertEqual((before, modified), (path.read_bytes(), path.stat().st_mtime_ns))
        self.assertFalse((self.state/JOURNAL).exists())
        self.assertEqual(0o600, path.stat().st_mode & 0o777)
        self.assertEqual(str(self.sp), json.loads(before)['cloudProfiles']['service-provider']['credential'])
        self.assertNotIn(str(self.root), json.dumps(saved))

    def test_mismatch_expired_encrypted_and_same_file_rejected(self):
        for kwargs in (dict(domain='different.example.test'), dict(expired=True), dict(encrypted=True)):
            certificate(self.sp, **kwargs)
            with self.assertRaises(ValueError): self.preview()
        with self.assertRaisesRegex(ValueError, 'DISTINCT'):
            self.connection.inspect_pair(str(self.oem), str(self.oem))
        self.assertFalse((self.state/CONFIG).exists())

    def test_authentication_only_ec_certificate_is_not_a_usable_demo_pair(self):
        for path in (self.oem, self.sp):
            certificate(path, use_ec=True)
            before = path.read_bytes()
            with self.assertRaisesRegex(ValueError, 'CLOUD_PACKAGE_SIGNING_RSA_KEY_REQUIRED'):
                self.preview()
            self.assertEqual(before, path.read_bytes())
            self.assertFalse((self.state/CONFIG).exists())
            self.assertFalse((self.state/JOURNAL).exists())
            certificate(path)

    def test_changed_file_config_or_selection_rejects_save(self):
        for mutation in ('file', 'config', 'selection'):
            token = self.preview()['selectionToken']
            if mutation == 'file': certificate(self.sp)
            elif mutation == 'config':
                self.env._directory('.local/demo-control')
                atomic_json(self.state/CONFIG, dict(schemaVersion=1, cloudSetupContexts={}))
            else: atomic_json(self.state/'installation.json', dict(current='0'*64, revision=2))
            with self.assertRaisesRegex(ValueError, 'CHANGED_SINCE_PREVIEW'): self.save(token)

    def test_changed_during_inspection_is_rejected(self):
        def changed(path):
            result = inspect_certificate(path)
            if Path(path) == self.sp: os.utime(self.oem, None)
            return result
        with patch.object(self.connection, 'inspect', side_effect=changed), self.assertRaisesRegex(ValueError, 'CHANGED_SINCE_PREVIEW'):
            self.preview()

    def test_private_unlinked_single_link_files_only(self):
        self.oem.chmod(0o644)
        with self.assertRaisesRegex(ValueError, 'PRIVATE'): self.preview()
        self.oem.chmod(0o600)
        link = self.root/'hardlink'; os.link(self.oem, link)
        with self.assertRaisesRegex(ValueError, 'PRIVATE'): self.preview()
        link.unlink(); link.symlink_to(self.oem)
        with self.assertRaisesRegex(ValueError, 'LINKED'):
            self.connection.inspect_pair(str(link), str(self.sp))
        with self.assertRaisesRegex(ValueError, 'PATH_INVALID'):
            self.connection.inspect_pair('oem.p12', str(self.sp))

    def test_retained_pending_and_developer_mode_block(self):
        self.env._directory('.run/demo-current')
        for name in (JOURNAL, JOURNAL+'.pending', CONFIG+'.pending'):
            path = self.state/name; path.parent.mkdir(exist_ok=True, mode=0o700)
            path.write_text('{}'); path.chmod(0o600)
            with self.assertRaises(ValueError): self.preview()
            self.assertEqual('{}', path.read_text()); path.unlink()
        with patch.object(runtime_paths, '_active', None), self.assertRaisesRegex(ValueError, 'INSTALLED_INSTANCE_REQUIRED'):
            self.preview()

    def connect_report(self, stage='READY'):
        return dict(domain='stage.example.test', stage=stage,
                    owners={'oem': '11111111-1111-4111-8111-111111111111',
                            'sp': '22222222-2222-4222-8222-222222222222'},
                    checks=[dict(key=k, state='READY') for k in
                            ('oem', 'sp', 'association', 'componentDelivery', 'serviceDelivery')])

    def connect(self, authenticate):
        return self.connection.connect_pair(str(self.oem), str(self.sp), authenticate)

    def retained(self):
        report = self.connect_report()
        self.save(self.preview()['selectionToken'])
        data = json.loads((self.state/CONFIG).read_bytes())
        data['cloudProfiles']['service-provider']['credential'] = str(self.root/'missing.p12')
        data['cloudConnection']['domain'] = report['domain']
        atomic_json(self.state/CONFIG, data)
        self.env._directory('.run/demo-current')
        atomic_json(self.state/JOURNAL, dict(schemaVersion=1, kind='democtl.current-run', stage='LOCAL_ACTIVE',
            selectedCloudDomain=report['domain'], vehicles={'test': {'unitId':'33333333-3333-4333-8333-333333333333'}},
            cloudContexts={report['domain']: {'cloudBinding': {'ownerId': report['owners']['oem']}}},
            componentOperations={}, serviceOperations={}))
        return report

    def test_connect_authenticates_before_save_and_repeat_is_idempotent(self):
        def authenticate(*args):
            self.assertFalse((self.state/CONFIG).exists())
            return self.connect_report()
        self.connect(authenticate)
        before = (self.state/CONFIG).read_bytes()
        self.connect(lambda *args: self.connect_report())
        self.assertEqual(before, (self.state/CONFIG).read_bytes())
        self.assertFalse((self.state/JOURNAL).exists())

    def test_retained_missing_sp_repair_preserves_journal_and_ledger(self):
        report = self.retained()
        journal = (self.state/JOURNAL).read_bytes()
        sentinel = self.state/'ledger'; sentinel.write_bytes(b'keep')
        self.connect(lambda *args: report)
        self.assertEqual(journal, (self.state/JOURNAL).read_bytes())
        self.assertEqual(b'keep', sentinel.read_bytes())
        self.assertEqual(str(self.sp), json.loads((self.state/CONFIG).read_bytes())['cloudProfiles']['service-provider']['credential'])
        # Original fresh-only operations remain forbidden.
        with self.assertRaisesRegex(ValueError, 'CURRENT_RUN_RETAINED'): self.preview()
        self.connect(lambda *args: report)
        self.assertEqual(journal, (self.state/JOURNAL).read_bytes())

    def test_wrong_owner_or_unassociated_pair_never_saved(self):
        self.retained()
        before = (self.state/CONFIG).read_bytes()
        report = self.connect_report(); report['owners']['oem'] = report['owners']['sp']
        with self.assertRaisesRegex(ValueError, 'OWNER_CHANGED'): self.connect(lambda *args: report)
        report = self.connect_report(); report['checks'][2]['state'] = 'BLOCKED'
        with self.assertRaisesRegex(ValueError, 'AUTHENTICATION_REQUIRED'): self.connect(lambda *args: report)
        self.assertEqual(before, (self.state/CONFIG).read_bytes())

    def test_changed_journal_during_authentication_never_saved(self):
        report = self.retained(); before = (self.state/CONFIG).read_bytes()
        def changed(*args):
            data = json.loads((self.state/JOURNAL).read_bytes()); data['sentinel'] = 'change'
            atomic_json(self.state/JOURNAL, data)
            return report
        with self.assertRaisesRegex(ValueError, 'CHANGED_SINCE_PREVIEW'): self.connect(changed)
        self.assertEqual(before, (self.state/CONFIG).read_bytes())

    def test_known_verification_response_is_not_retirement_or_uncertainty(self):
        report = self.retained()
        path = self.state/JOURNAL; state = json.loads(path.read_bytes())
        record = dict(deploymentId='33333333-3333-4333-8333-333333333333', publication={'stage':'ACCEPTED'},
                      upload=dict(attemptStarted=True, state='RESPONDED', response=dict(httpStatus=201,
                                  deploymentId='33333333-3333-4333-8333-333333333333')))
        state['componentOperations'] = {'140.0.0':record}; atomic_json(path, state)
        before = path.read_bytes()
        self.connect(lambda *args: report)
        self.assertEqual(before, path.read_bytes())
        for change in (dict(state='UNCERTAIN'), dict(response={})):
            state['componentOperations']['140.0.0']['upload'].update(change); atomic_json(path, state)
            with self.assertRaisesRegex(ValueError, 'RECONCILIATION_REQUIRED'): self.connect(lambda *args: report)


class PermissionTests(unittest.TestCase):
    def delivery_report(self, *, sp_denied=None, oem_denied=None, occupied=False):
        from test_cloud_setup import SET, OTHER, FLEET
        cloud, sp = CloudFixture(), CloudFixture()
        sp.user = {'ownerId': SP}
        cloud.denied, sp.denied = oem_denied, sp_denied
        if occupied:
            cloud.sets.append(dict(id=SET, title='Test Vehicles', fleet=FLEET,
                                   is_validation_set=True, allow_unknown_components=False))
            cloud.members = [dict(id=OTHER)]
        with patch('aosedge_demo_orchestrator.cloud_connection.inspect_certificate', return_value={}), \
                patch.object(sp, 'pages', wraps=sp.pages) as sp_pages:
            result = inspect_setup(cloud, dict(REQUEST, firstUse=True), sp_factory=lambda *a, **k: sp)
        sp_pages.assert_not_called()
        self.assertEqual([], cloud.posts)
        self.assertEqual([], sp.posts)
        return {v['key']: v for v in result['checks']}

    def test_sp_does_not_need_oem_provider_discovery_and_repeat_is_read_only(self):
        for _ in range(2):
            rows = self.delivery_report(sp_denied='service_providers_list')
            self.assertEqual('READY', rows['serviceDelivery']['state'])
            self.assertEqual('READY', rows['association']['state'])

    def test_oem_provider_discovery_is_still_required_for_association(self):
        rows = self.delivery_report(oem_denied='service_providers_list')
        self.assertEqual('BLOCKED', rows['association']['state'])
        self.assertEqual('READY', rows['serviceDelivery']['state'])

    def test_each_required_sp_delivery_permission_fails_closed(self):
        for permission in ('services_list', 'services_read', 'services_create',
                           'services_service_versions_list', 'services_versions_read', 'services_units_list',
                           'deployment_bundles_create', 'deployment_bundles_list'):
            with self.subTest(permission=permission):
                rows = self.delivery_report(sp_denied=permission)
                self.assertEqual('BLOCKED', rows['serviceDelivery']['state'])
                self.assertEqual('READY', rows['association']['state'])

    def test_role_correct_permissions_do_not_bypass_occupied_test_set(self):
        rows = self.delivery_report(sp_denied='service_providers_list', occupied=True)
        self.assertEqual('READY', rows['serviceDelivery']['state'])
        self.assertEqual('CONFLICT', rows['testSet']['state'])
        self.assertEqual('TEST_UNIT_SET_HAS_OTHER_UNITS', rows['testSet']['detail'])

    def test_first_use_read_only_delivery_checks(self):
        cloud, sp = CloudFixture(), CloudFixture()
        sp.user = {'ownerId': SP}
        with patch('aosedge_demo_orchestrator.cloud_connection.inspect_certificate', return_value={}):
            for denied, target, key in ((None, sp, 'serviceDelivery'), ('services_create', sp, 'serviceDelivery'),
                                       ('deployment_bundles_create', cloud, 'componentDelivery')):
                target.denied = denied
                result = inspect_setup(cloud, dict(REQUEST, firstUse=True), sp_factory=lambda *a, **k: sp)
                row = next(v for v in result['checks'] if v['key'] == key)
                self.assertEqual('BLOCKED' if denied else 'READY', row['state'])
                self.assertEqual([], cloud.posts); self.assertEqual([], sp.posts)
                target.denied = None
