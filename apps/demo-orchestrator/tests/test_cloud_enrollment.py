# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from aosedge_demo_orchestrator import runtime_paths
from aos_keys.key_manager import pem_to_pkcs12_bytes
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from cryptography.x509.oid import NameOID
from aosedge_demo_orchestrator import cloud_enrollment as enrollment
DOMAIN='fixture.example.test'
TOKEN='fixture-token-not-a-real-credential'


class EnrollmentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='enrollment-proof.', dir='/tmp')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()/'state'
        runtime_paths.create_instance(self.root)
        self.calls=[]
        self.transport = patch.object(enrollment, 'receive_once', side_effect=self.issue)
        self.transport.start(); self.addCleanup(self.transport.stop)
    def issue(self, domain, token, key, csr, role):
        self.calls.append((domain,role))
        self.assertEqual(TOKEN, token)
        state=json.loads((self.folder(role)/'attempt.json').read_bytes())
        self.assertEqual('DISPATCHING', state['attempts'][-1]['stage'])
        self.assertNotIn(TOKEN, json.dumps(state))
        certkey=ec.generate_private_key(ec.SECP256R1())
        name=x509.Name([x509.NameAttribute(NameOID.ORGANIZATION_NAME, domain)])
        now=datetime.now(timezone.utc)
        cert=(x509.CertificateBuilder().subject_name(name).issuer_name(name)
              .public_key(x509.load_pem_x509_csr(csr).public_key()).serial_number(x509.random_serial_number())
              .not_valid_before(now-timedelta(days=1)).not_valid_after(now+timedelta(days=1))
              .sign(certkey,hashes.SHA256()).public_bytes(serialization.Encoding.PEM))
        return pem_to_pkcs12_bytes(key,cert,'fixture')
    def folder(self, role='oem'): return self.root/'.local/demo-control/credentials/enrollment'/role
    def run_action(self, action='enroll',role='oem',**kw):
        return enrollment.operation(self.root, DOMAIN, role, action, TOKEN if action=='enroll' else None, **kw)
    def tearDown(self):
        self.assertFalse((self.root/'.run/demo-current/journal.json').exists())
        for path in self.root.rglob('*'):
            if path.is_file() and not path.is_symlink():
                self.assertNotIn(TOKEN.encode(),path.read_bytes())
    def test_status_is_read_only(self):
        before=list(self.root.rglob('*'))
        self.assertEqual('NOT_STARTED',self.run_action('status')['enrollmentStage'])
        self.assertEqual(before,list(self.root.rglob('*')))
        self.assertEqual([],self.calls)
    def test_first_repeat_restart_and_separate_roles(self):
        for role in ('oem','sp'):
            first=self.run_action(role=role)
            self.assertTrue(first['cloudAccessed'])
            first = dict(first, cloudAccessed=False)
            self.assertEqual('RECEIVED',first['enrollmentStage'])
            files={p:p.read_bytes() for p in self.folder(role).iterdir()}
            self.assertEqual(first,self.run_action(role=role))
            self.assertEqual(first,self.run_action('status',role))
            self.assertEqual(first,self.run_action('recover',role))
            self.assertEqual(files,{p:p.read_bytes() for p in self.folder(role).iterdir()})
            self.assertTrue(all(p.stat().st_mode & 0o777 == 0o600 for p in files))
        self.assertEqual(2,len(self.calls))
    def test_both_enrolled_roles_sign_with_the_real_official_rs256_signer(self):
        from aos_signer.signer.signer import Signer
        from cryptography.hazmat.primitives.serialization import pkcs12
        import jwt
        with patch('socket.socket.connect', side_effect=AssertionError('No network in fixture')):
            for role in ('oem','sp'):
                self.run_action(role=role)
                folder = self.folder(role)
                key, cert, _ = pkcs12.load_key_and_certificates((folder/'client.p12').read_bytes(), None)
                self.assertIsInstance(key, rsa.RSAPrivateKey)
                self.assertGreaterEqual(key.key_size, 2048)
                self.assertIsInstance(x509.load_pem_x509_csr((folder/'request.pem').read_bytes()).public_key(), rsa.RSAPublicKey)
                with tempfile.TemporaryDirectory() as temporary:
                    stage = Path(temporary)
                    (stage/'config.yaml').write_text('{}')
                    (stage/'batch.tar.gz').write_bytes(b'offline fixture')
                    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                        Signer(None, stage/'config.yaml', str(folder/'client.p12'))._sign_file(temporary, str(stage/'batch.tar.gz'))
                    result = jwt.decode((stage/'package.sign').read_bytes(), cert.public_key(), algorithms=['RS256'])
                    self.assertEqual(2, len(result['data']))
    def test_completed_legacy_ec_attempt_is_preserved_without_rotation(self):
        from aos_keys.key_manager import generate_pair
        with patch('aos_keys.key_manager.generate_pair', return_value=generate_pair(use_elliptic_curves=True)):
            self.run_action()
        before = {p:p.read_bytes() for p in self.folder().iterdir()}
        for action in ('status','recover','enroll'):
            self.assertEqual('RECEIVED', self.run_action(action)['enrollmentStage'])
        self.assertEqual(before, {p:p.read_bytes() for p in self.folder().iterdir()})
        self.assertEqual(1, len(self.calls))
    def test_timeout_preserves_key_and_never_replays(self):
        output=io.StringIO()
        with patch.object(enrollment,'receive_once',side_effect=TimeoutError(TOKEN)) as transport, \
                redirect_stdout(output),redirect_stderr(output):
            first=self.run_action()
            key=(self.folder()/'key.pem').read_bytes()
            self.assertEqual('RECONCILIATION_REQUIRED',first['enrollmentStage'])
            self.assertTrue(first['cloudAccessed'])
            first = dict(first, cloudAccessed=False)
            self.assertEqual(first,self.run_action('status'))
            self.assertEqual(first,self.run_action('recover'))
            with self.assertRaisesRegex(ValueError,'RECONCILIATION_REQUIRED'): self.run_action()
            with self.assertRaisesRegex(ValueError,'RECONCILIATION_REQUIRED'):
                self.run_action(reconcile_attempt='00000000-0000-4000-8000-000000000000')
            self.assertEqual(key,(self.folder()/'key.pem').read_bytes())
            self.assertEqual(1,transport.call_count)
        self.assertEqual('',output.getvalue())
    def test_explicit_reconciled_replacement_preserves_old_attempt_and_key(self):
        with patch.object(enrollment,'receive_once',side_effect=TimeoutError()): first=self.run_action()
        key=(self.folder()/'key.pem').read_bytes()
        last=self.run_action(reconcile_attempt=first['attemptId'])
        self.assertEqual('RECEIVED',last['enrollmentStage'])
        self.assertNotEqual(first['attemptId'],last['attemptId'])
        self.assertEqual(key,(self.folder()/'key.pem').read_bytes())
        record=json.loads((self.folder()/'attempt.json').read_bytes())
        self.assertEqual(2,len(record['attempts']))
        self.assertIn('reconciledAt',record['attempts'][0])
    def test_crash_after_dispatch_intent_blocks_after_restart(self):
        with patch.object(enrollment,'receive_once',side_effect=SystemExit(2)),self.assertRaises(SystemExit):
            self.run_action()
        self.assertEqual('RECONCILIATION_REQUIRED',self.run_action('status')['enrollmentStage'])
        with self.assertRaisesRegex(ValueError,'RECONCILIATION_REQUIRED'): self.run_action()
        self.assertEqual([],self.calls)
    def test_crash_after_key_only_preserves_partial_state(self):
        original=enrollment.write_new
        def interrupt(path,data):
            if path.name=='request.pem': raise SystemExit(2)
            return original(path,data)
        with patch.object(enrollment,'write_new',side_effect=interrupt),self.assertRaises(SystemExit): self.run_action()
        key=(self.folder()/'key.pem').read_bytes()
        with self.assertRaisesRegex(ValueError,'PARTIAL_STATE'): self.run_action()
        self.assertEqual(key,(self.folder()/'key.pem').read_bytes())
        self.assertEqual([],self.calls)
    def test_crash_after_prepared_but_before_intent_is_safe_to_submit(self):
        original=enrollment.save
        def interrupt(path,record):
            if record['attempts'][-1]['stage']=='DISPATCHING': raise SystemExit(2)
            return original(path,record)
        with patch.object(enrollment,'save',side_effect=interrupt),self.assertRaises(SystemExit): self.run_action()
        self.assertEqual('PREPARED',self.run_action('status')['enrollmentStage'])
        self.assertEqual('RECEIVED',self.run_action()['enrollmentStage'])
        self.assertEqual(1,len(self.calls))
    def test_crash_after_credential_write_recovers_without_network(self):
        original=enrollment.save
        def interrupt(path,record):
            if record['attempts'][-1]['stage']=='RECEIVED': raise SystemExit(2)
            return original(path,record)
        with patch.object(enrollment,'save',side_effect=interrupt),self.assertRaises(SystemExit): self.run_action()
        self.assertEqual('LOCAL_RECOVERY_AVAILABLE',self.run_action('status')['enrollmentStage'])
        with self.assertRaisesRegex(ValueError,'LOCAL_RECOVERY_REQUIRED'): self.run_action()
        self.assertEqual('RECEIVED',self.run_action('recover')['enrollmentStage'])
        self.assertEqual(1,len(self.calls))
    def test_invalid_token_role_domain_do_not_create_attempt(self):
        for domain,role,token in ((DOMAIN,'admin',TOKEN),('127.0.0.1','oem',TOKEN),(DOMAIN,'oem','a\nb')):
            with self.assertRaises(ValueError): enrollment.operation(self.root,domain,role,'enroll',token)
        self.assertFalse((self.root/'.local/demo-control/credentials/enrollment').exists())
    def test_changed_domain_never_rotates_or_reissues(self):
        self.run_action()
        with self.assertRaisesRegex(ValueError,'SCOPE_CHANGED'):
            enrollment.operation(self.root,'other.example.test','oem','enroll',TOKEN)
        self.assertEqual(1,len(self.calls))
    def test_unsafe_links_modes_and_pending_record_block(self):
        self.run_action()
        cert=self.folder()/'client.p12'
        cert.chmod(0o644)
        with self.assertRaisesRegex(ValueError,'UNSAFE'): self.run_action('status')
        cert.chmod(0o600)
        link=self.root/'hardlink'; os.link(cert,link)
        with self.assertRaisesRegex(ValueError,'UNSAFE'): self.run_action('status')
        link.unlink()
        (self.folder()/'attempt.json.pending').write_text('{}')
        with self.assertRaisesRegex(ValueError,'PENDING'): self.run_action('status')
        self.assertEqual(1,len(self.calls))
    def test_malformed_cert_response_blocks_and_preserves_key(self):
        with patch.object(enrollment,'receive_once',return_value=b'bad-p12') as transport:
            self.assertEqual('RECONCILIATION_REQUIRED',self.run_action()['enrollmentStage'])
            with self.assertRaises(ValueError): self.run_action('recover')
            self.assertEqual(1,transport.call_count)
    def test_transport_observes_durable_intent(self):
        self.run_action()
        self.assertEqual(1,len(self.calls))


if __name__=='__main__': unittest.main(verbosity=2)
