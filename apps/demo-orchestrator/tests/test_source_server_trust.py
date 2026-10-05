# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Real local crypto/loopback fixtures; no operator keys, Cloud or live VM."""
from datetime import datetime, timedelta, timezone
from contextlib import nullcontext
import json
import os
from pathlib import Path
import socket
import ssl
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import Mock, patch

from aosedge_demo_orchestrator import runtime_paths as paths, source_trust as crypto
from aosedge_demo_orchestrator.environment import EnvironmentError
from aosedge_demo_orchestrator.source import SourceDriver, SourceService
from aosedge_demo_orchestrator import source_server_trust as target

REPO = paths.CODE_ROOT


class GatewayServerTrustTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='gst.', dir='/private/tmp')
        self.addCleanup(temp.cleanup)
        self.base = Path(temp.name)
        self.root = self.base/'instance'
        self.identity = paths.create_instance(self.root)['instanceId']
        self.layout = paths.Layout(self.root, REPO, REPO.parent/'demo-artifacts', self.identity)
        active = patch.object(paths, '_active', self.layout)
        active.start(); self.addCleanup(active.stop)
        self.directory = self.root/target.RELATIVE

    def prepare(self, state=None):
        return target.prepare(self.root, state or {})

    def contents(self):
        return {p.name: (p.read_bytes(), p.stat().st_mtime_ns, p.stat().st_ino)
                for p in self.directory.iterdir()}

    def test_first_create_repeat_read_and_redaction(self):
        with self.assertRaisesRegex(EnvironmentError, 'SOURCE_OPERATOR_TLS_REQUIRED'):
            target.inspect(self.root)
        self.assertTrue(self.directory.parent.is_dir())
        self.assertEqual(0o700, self.directory.parent.stat().st_mode & 0o777)
        self.assertFalse(self.directory.exists())
        result = self.prepare()
        self.assertFalse(result['reused'])
        before = self.contents()
        self.assertEqual(set(before), target.FILES)
        self.assertTrue(self.prepare({'source': {'state': 'STOPPED'}})['reused'])
        self.assertTrue(before == self.contents(), 'Repeat changed server identity')
        self.assertEqual('VERIFIED', target.inspect(self.root)['state'])
        self.assertNotIn('BEGIN', json.dumps(result))
        self.assertNotIn(self.identity, json.dumps(result))
        self.assertEqual(0o700, self.directory.stat().st_mode & 0o777)
        for path in self.directory.iterdir():
            self.assertEqual(0o600, path.stat().st_mode & 0o777)

    def test_missing_member_does_not_regenerate(self):
        self.prepare(); (self.directory/'server-key.pem').unlink()
        with patch.object(crypto, 'openssl') as command:
            with self.assertRaisesRegex(EnvironmentError, 'MATERIAL_INCOMPLETE'):
                self.prepare()
        command.assert_not_called()

    def test_retained_source_without_material_cannot_rotate(self):
        with patch.object(crypto, 'openssl') as command:
            with self.assertRaisesRegex(EnvironmentError, 'RETAINED_SOURCE_TRUST_MISSING'):
                self.prepare({'source': {'state':'STOPPED'}})
        command.assert_not_called()
        self.assertFalse(self.directory.exists())

    def test_explicit_start_initializes_before_driver_and_assets_stay_read_only(self):
        vm=Mock(root=self.root)
        vm.environment.root=self.root
        vm.environment._writer=nullcontext
        driver=Mock(); driver.operation=nullcontext
        service=SourceService(vm,Mock(),driver)
        state=dict(vehicles={'test':{}},currentVehicle=None)
        def start(observed):
            self.assertIs(observed,state)
            self.assertEqual('VERIFIED',target.inspect(self.root)['state'])
            return dict(runId='fixture-run')
        driver.start.side_effect=start
        with patch('aosedge_demo_orchestrator.source.read_json',return_value=state), \
                patch.object(service,'_detach',return_value={'test':{'gate':'BLOCKED'}}):
            self.assertEqual('RUNNING', service.simulation('start',target='test')['state'])
        before=self.contents()
        self.assertEqual(self.directory, SourceDriver(vm).assets()['tls'])
        self.assertTrue(before == self.contents(), 'Read-only assets changed trust')
        (self.directory/'server-key.pem').unlink(); driver.start.reset_mock()
        with patch('aosedge_demo_orchestrator.source.read_json',return_value=state):
            with self.assertRaisesRegex(EnvironmentError,'MATERIAL_INCOMPLETE'):
                service.simulation('start',target='test')
        driver.start.assert_not_called()

    def test_partial_foreign_and_extra_material_preserved(self):
        self.directory.mkdir(mode=0o700)
        for extra in (None, 'foreign'):
            if extra:
                (self.directory/extra).write_text('preserve')
            with self.assertRaisesRegex(EnvironmentError, 'MATERIAL_INCOMPLETE'):
                self.prepare()
        self.assertEqual('preserve', (self.directory/'foreign').read_text())

    def test_existing_stage_blocks_without_retry(self):
        stage=self.directory.parent/'.gateway-tls.pending'; stage.mkdir(mode=0o700)
        (stage/'keep').write_text('preserve')
        with self.assertRaisesRegex(EnvironmentError, 'RECONCILIATION_REQUIRED'):
            self.prepare()
        self.assertEqual('preserve', (stage/'keep').read_text())

    def test_generation_failure_retains_private_stage(self):
        with patch.object(crypto, 'openssl', side_effect=EnvironmentError('FIXTURE_CRYPTO_FAILURE')):
            with self.assertRaisesRegex(EnvironmentError, 'FIXTURE_CRYPTO_FAILURE'):
                self.prepare()
        self.assertFalse(self.directory.exists())
        self.assertEqual(0o700, (self.directory.parent/'.gateway-tls.pending').stat().st_mode & 0o777)
        with self.assertRaisesRegex(EnvironmentError, 'RECONCILIATION_REQUIRED'):
            self.prepare()

    def test_exclusive_publication_never_overwrites_even_empty_destination(self):
        stage=self.directory.parent/'.test-stage'; stage.mkdir(mode=0o700)
        self.directory.mkdir(mode=0o700)
        with self.assertRaisesRegex(EnvironmentError, 'PUBLICATION_CONFLICT'):
            target.publish(stage, self.directory)
        self.assertTrue(stage.is_dir() and self.directory.is_dir())

    def test_wrong_marker_or_certificate_instance_is_refused(self):
        self.prepare()
        descriptor=self.directory/'identity.json'
        value=json.loads(descriptor.read_text()); original=descriptor.read_bytes()
        value['instanceId']='00000000-0000-4000-8000-000000000000'
        descriptor.write_text(json.dumps(value))
        with self.assertRaisesRegex(EnvironmentError, 'INSTANCE_CONFLICT'):
            self.prepare()
        descriptor.write_bytes(original)
        expected=dict(value)
        with self.assertRaisesRegex(EnvironmentError, 'INSTANCE_CONFLICT'):
            target.inspect_directory(self.directory, expected)
        descriptor.write_text(json.dumps(expected))
        with self.assertRaisesRegex(EnvironmentError, 'CERTIFICATE_IDENTITY_INVALID'):
            target.inspect_directory(self.directory, expected)

    def test_key_mismatch_refused_without_replacement(self):
        self.prepare()
        key=self.directory/'server-key.pem'
        crypto.openssl(['genpkey','-algorithm','RSA','-pkeyopt','rsa_keygen_bits:2048','-out',key])
        before=self.contents()
        with self.assertRaisesRegex(EnvironmentError,'KEY_MISMATCH'):
            self.prepare()
        self.assertTrue(before == self.contents(), 'Invalid pair was changed')

    def test_read_from_new_process_preserves_identity(self):
        self.prepare(); before=self.contents()
        code='''import sys, importlib.util
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from aosedge_demo_orchestrator import runtime_paths as p
r=Path(sys.argv[2]); root, identity=p.instance(r)
repo=Path(sys.argv[1]).parents[2]
p._active=p.Layout(root,repo,repo.parent/'demo-artifacts',identity)
spec=importlib.util.spec_from_file_location('proof_server',sys.argv[3])
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
assert m.inspect(root)['state']=='VERIFIED'
print('VERIFIED_NO_CHANGE')
'''
        result=subprocess.run([sys.executable,'-I','-B','-c',code,
            str(REPO/'apps/demo-orchestrator/src'),str(self.root),str(Path(target.__file__).resolve())],
            capture_output=True,text=True,timeout=15)
        self.assertEqual(0,result.returncode,'New-process verifier failed')
        self.assertEqual('VERIFIED_NO_CHANGE',result.stdout.strip())
        self.assertTrue(before == self.contents(), 'Process restart changed identity')

    def test_links_and_nonprivate_modes_are_refused(self):
        self.prepare()
        key=self.directory/'server-key.pem'; original=key.read_bytes()
        key.chmod(0o644)
        with self.assertRaisesRegex(EnvironmentError, 'MATERIAL_INVALID'):
            target.inspect(self.root)
        key.chmod(0o600)
        link=self.base/'key-link'; os.link(key, link)
        with self.assertRaisesRegex(EnvironmentError, 'MATERIAL_INVALID'):
            target.inspect(self.root)
        link.unlink()
        key.rename(self.base/'outside-key'); key.symlink_to(self.base/'outside-key')
        with self.assertRaisesRegex(EnvironmentError, 'MATERIAL_INVALID'):
            target.inspect(self.root)
        self.assertTrue(original == (self.base/'outside-key').read_bytes(), 'Outside key was changed')

    def test_linked_parent_never_receives_key(self):
        outside=self.base/'outside'; outside.mkdir(mode=0o700)
        self.directory.parent.rmdir()  # Empty fixture parent only, to inject a hostile link.
        self.directory.parent.symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(EnvironmentError, 'INITIALIZATION_FAILED'):
            self.prepare()
        self.assertEqual([], list(outside.iterdir()))

    def test_malformed_and_oversized_certificate_are_refused(self):
        self.prepare()
        cert=self.directory/'server-cert.pem'
        for raw in (b'invalid private fixture', b'x'*16385):
            cert.write_bytes(raw)
            with self.assertRaises(EnvironmentError) as observed:
                target.inspect(self.root)
            self.assertNotIn('private fixture', str(observed.exception))
            self.assertNotIn(str(self.root), str(observed.exception))

    def test_expiry_wrong_purpose_and_signature_rejected(self):
        from cryptography import x509
        from cryptography.hazmat.primitives import serialization, hashes
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.x509.oid import ExtendedKeyUsageOID
        self.prepare()
        cert=self.directory/'server-cert.pem'; key=self.directory/'server-key.pem'
        original=x509.load_pem_x509_certificate(cert.read_bytes())
        private=serialization.load_pem_private_key(key.read_bytes(), password=None)
        now=datetime.now(timezone.utc)
        for case in ('expired','purpose','signature'):
            builder=(x509.CertificateBuilder().subject_name(original.subject).issuer_name(original.issuer)
                .public_key(private.public_key()).serial_number(x509.random_serial_number())
                .not_valid_before(now-timedelta(days=2))
                .not_valid_after(now+timedelta(days=-1 if case=='expired' else 1)))
            for extension in original.extensions:
                val = (x509.ExtendedKeyUsage([ExtendedKeyUsageOID.CLIENT_AUTH])
                       if case=='purpose' and isinstance(extension.value,x509.ExtendedKeyUsage) else extension.value)
                builder=builder.add_extension(val, extension.critical)
            signer=rsa.generate_private_key(public_exponent=65537,key_size=2048) if case=='signature' else private
            cert.write_bytes(builder.sign(signer,hashes.SHA256()).public_bytes(serialization.Encoding.PEM))
            with self.subTest(case=case), self.assertRaises(EnvironmentError):
                target.inspect(self.root)

    def handshake(self, anchor, name):
        server=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        server.load_cert_chain(self.directory/'server-cert.pem', self.directory/'server-key.pem')
        client=ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT); client.load_verify_locations(cafile=str(anchor))
        listener=socket.socket(); listener.bind(('127.0.0.1',0)); listener.listen(); listener.settimeout(3)
        received=[]
        def accept():
            try:
                raw,_=listener.accept(); raw.settimeout(3)
                with server.wrap_socket(raw,server_side=True) as stream:
                    stream.sendall(b'local-proof')
            except (ssl.SSLError,OSError):
                pass
        worker=threading.Thread(target=accept); worker.start()
        try:
            with socket.create_connection(listener.getsockname(),timeout=3) as raw:
                with client.wrap_socket(raw,server_hostname=name) as stream:
                    received.append(stream.recv(64))
        finally:
            worker.join(4); listener.close()
        self.assertEqual([b'local-proof'],received)

    def test_real_tls_correct_anchor_wrong_name_and_wrong_anchor(self):
        self.prepare()
        self.handshake(self.directory/'server-cert.pem','localhost')
        self.handshake(self.directory/'server-cert.pem','127.0.0.1')
        with self.assertRaises(ssl.SSLCertVerificationError):
            self.handshake(self.directory/'server-cert.pem','wrong.example.test')
        second=self.base/'other'; identity=paths.create_instance(second)['instanceId']
        with patch.object(paths,'_active',paths.Layout(second,REPO,REPO.parent/'demo-artifacts',identity)):
            target.prepare(second,{})
        other=second/target.RELATIVE/'server-cert.pem'
        self.assertTrue(other.read_bytes() != (self.directory/'server-cert.pem').read_bytes())
        with self.assertRaises(ssl.SSLCertVerificationError):
            self.handshake(other,'localhost')


if __name__ == '__main__':
    unittest.main()
