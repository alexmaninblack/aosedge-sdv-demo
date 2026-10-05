# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import json
from datetime import datetime, timedelta, timezone
import unittest
from unittest.mock import patch
import requests
from aos_keys.key_manager import generate_pair
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID
from aosedge_demo_orchestrator import cloud_enrollment as enrollment
import test_cloud_enrollment as state_fixture

TOKEN = state_fixture.TOKEN
DOMAIN = state_fixture.DOMAIN

class Response:
    def __init__(self, raw=b'', status=201):
        self.raw, self.status_code, self.closed = raw, status, False
    def __enter__(self): return self
    def __exit__(self, *a): self.closed = True
    def iter_content(self, chunk_size):
        for i in range(0, len(self.raw), chunk_size): yield self.raw[i:i+chunk_size]


class Session:
    def __init__(self, response=None, error=None):
        self.response, self.error = response, error
        self.calls, self.adapters, self.trust_env, self.closed = [], {}, True, False
    def __enter__(self): return self
    def __exit__(self, *a): self.closed = True
    def mount(self, scheme, adapter): self.adapters[scheme] = adapter
    def post(self, url, **kw):
        self.calls.append((url, kw))
        if self.error: raise self.error
        return self.response



class TransportTests(unittest.TestCase):
    def setUp(self):
        self.key, self.csr = generate_pair()
    def cert(self, domain=DOMAIN, expired=False, wrong_key=False):
        public = (ec.generate_private_key(ec.SECP256R1()).public_key() if wrong_key
                  else x509.load_pem_x509_csr(self.csr).public_key())
        ca_key = ec.generate_private_key(ec.SECP256R1())
        subject = x509.Name([x509.NameAttribute(NameOID.ORGANIZATION_NAME, domain)])
        now = datetime.now(timezone.utc)
        return (x509.CertificateBuilder().subject_name(subject).issuer_name(subject).public_key(public)
                .serial_number(x509.random_serial_number()).not_valid_before(now - timedelta(days=2))
                .not_valid_after(now + timedelta(days=-1 if expired else 2))
                .sign(ca_key, hashes.SHA256()).public_bytes(serialization.Encoding.PEM).decode())
    def session(self, **kw):
        return Session(Response(json.dumps({'certificate': self.cert(**kw)}).encode()))

    def receive(self, session):
        with patch.object(requests, "Session", return_value=session):
            return enrollment.receive_once(DOMAIN, TOKEN, self.key, self.csr, "oem")
    def test_success_one_post_fixed_trust_and_no_proxies_redirects_retries(self):
        session = self.session()
        self.assertTrue(self.receive(session))
        self.assertEqual(1, len(session.calls))
        url, call = session.calls[0]
        self.assertEqual("https://" + DOMAIN + ":10000/api/v11/user-certificates/", url)
        self.assertTrue(call["verify"].endswith("/aos_keys/files/1rootCA.crt"))
        self.assertFalse(call["allow_redirects"])
        self.assertTrue(call["stream"])
        self.assertEqual((5,30), call["timeout"])
        self.assertFalse(session.trust_env)
        self.assertEqual(0, session.adapters["https://"].max_retries.total)
        self.assertTrue(session.closed and session.response.closed)
    def test_network_and_http_failures_have_one_attempt(self):
        cases = [Session(error=error(TOKEN)) for error in (requests.exceptions.SSLError, requests.exceptions.Timeout, requests.exceptions.ConnectionError)]
        cases += [Session(Response(TOKEN.encode(), code)) for code in (301,302,307,308,400,401,403,404,409,429,500,503)]
        for session in cases:
            with self.assertRaises(Exception): self.receive(session)
            self.assertEqual(1, len(session.calls))
            self.assertTrue(session.closed)
    def test_invalid_and_oversized_responses_fail(self):
        for raw in (TOKEN.encode(), b"[]", b"{}", b'{"certificate":1}',
                    b'{"certificate":"x","certificate":"y"}', b"x"*65537):
            session = Session(Response(raw))
            with self.assertRaises(Exception): self.receive(session)
            self.assertEqual(1,len(session.calls))
    def test_wrong_key_domain_and_expired_certificate_fail(self):
        for kw in (dict(domain="foreign.example.test"), dict(wrong_key=True), dict(expired=True)):
            with self.assertRaisesRegex(ValueError, "BINDING_INVALID"): self.receive(self.session(**kw))
    def test_real_transport_failure_is_redacted_by_owner_and_blocks_replay(self):
        fixture = state_fixture.EnrollmentTests(); fixture.addCleanup = self.addCleanup; fixture.setUp()
        fixture.transport.stop()
        session = Session(error=requests.exceptions.SSLError(TOKEN))
        with patch.object(requests, "Session", return_value=session):
            result = fixture.run_action()
            self.assertEqual("RECONCILIATION_REQUIRED", result["enrollmentStage"])
            self.assertNotIn(TOKEN, json.dumps(result))
            with self.assertRaisesRegex(ValueError, "RECONCILIATION_REQUIRED"): fixture.run_action()
        self.assertEqual(1,len(session.calls))
        fixture.tearDown()

if __name__ == "__main__": unittest.main()
