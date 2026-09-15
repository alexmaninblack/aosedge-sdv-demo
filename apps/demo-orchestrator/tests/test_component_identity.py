# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""First publication, per-Cloud identity, and independent baseline trust."""

import hashlib
import json
import subprocess
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from aosedge_demo_orchestrator import component_cloud, component_worker
from aosedge_demo_orchestrator.component_publication import snapshot
from aosedge_demo_orchestrator.components import COMPONENT, ComponentService, sha
from aosedge_demo_orchestrator.component_build import pack, PROFILE_BASES
from aosedge_demo_orchestrator.environment import EnvironmentError
from aosedge_demo_orchestrator.unit_cloud import Cloud, CloudFailure
from test_component_publication import FixtureCloud, OWNER, BUNDLE, RELEASE, ready

DEBUG_ID = "77777777-7777-4777-8777-777777777777"
OTHER_ID = "88888888-8888-4888-8888-888888888888"


class CatalogCloud(FixtureCloud):
    pages = Cloud.pages


class IdentityTests(unittest.TestCase):
    def setUp(self):
        self.cloud = CatalogCloud()
        self.cloud.component_rows = []
        self.request = dict(version="40.0.0", vehicles={}, verificationTest=True, purpose="upload")

    def catalog(self):
        with patch.object(component_cloud, "Cloud", return_value=self.cloud):
            return component_cloud.execute(dict(action="release-catalog"))

    def test_first_catalog_is_absent_not_failed_and_has_no_versions_request(self):
        result = self.catalog()
        self.assertEqual(dict(versions=[], componentId=None, catalogState="ABSENT", latest=None), result)
        self.assertEqual(1, len(self.cloud.calls))
        self.assertIn("components/?search=", self.cloud.calls[0])

    def test_first_upload_processing_error_and_ready_use_the_new_cloud_uuid(self):
        before = snapshot(self.cloud, self.request)
        self.assertEqual("NOT_PUBLISHED", before["publication"]["stage"])
        self.assertEqual("ABSENT", before["catalogState"])
        self.assertTrue(before["recipientCoverage"]["complete"])
        self.assertFalse(any("/versions/" in path for path in self.cloud.calls))
        self.request.update(deploymentId=BUNDLE, purpose="status")
        self.cloud.collections["deployment-bundles/"] = [dict(ready("40.0.0"), state="building")]
        self.assertEqual("PROCESSING", snapshot(self.cloud, self.request)["publication"]["stage"])
        self.cloud.collections["deployment-bundles/"][0]["state"] = "error"
        self.assertEqual("ERROR", snapshot(self.cloud, self.request)["publication"]["stage"])
        self.cloud.collections["deployment-bundles/"][0]["state"] = "done"
        self.assertEqual("PROCESSING", snapshot(self.cloud, self.request)["publication"]["stage"])
        self.cloud.component_rows = [dict(id=DEBUG_ID, codename=COMPONENT, oem_id=OWNER)]
        self.cloud.collections["components/" + DEBUG_ID + "/versions/"] = [
            dict(id=RELEASE, version="40.0.0", state="Ready", is_fake=False)]
        result = snapshot(self.cloud, self.request)
        self.assertEqual("READY", result["publication"]["stage"])
        self.assertEqual(DEBUG_ID, result["componentId"])
        self.assertEqual(["40.0.0"], self.catalog()["versions"])
        self.assertEqual([], snapshot(self.cloud, dict(self.request, version="41.0.0", deploymentId=None))["versions"])
        self.assertNotIn("c33bc994", " ".join(self.cloud.calls))

    def test_owner_and_case_insensitive_codename_select_exactly_one_identity(self):
        self.cloud.component_rows = [dict(id=OTHER_ID, codename=COMPONENT, oem_id=RELEASE),
                                     dict(id=DEBUG_ID, codename=COMPONENT.upper(), oem_id=OWNER)]
        self.assertEqual(DEBUG_ID, component_cloud.resolve_component(self.cloud)["id"])
        self.cloud.component_rows.append(dict(id=OTHER_ID, codename=COMPONENT, oem_id=OWNER))
        with self.assertRaisesRegex(CloudFailure, "IDENTITY_AMBIGUOUS"):
            self.catalog()

    def test_foreign_component_is_never_adopted_and_domains_share_no_id_cache(self):
        self.cloud.component_rows = [dict(id=OTHER_ID, codename=COMPONENT, oem_id=RELEASE)]
        self.assertIsNone(component_cloud.resolve_component(self.cloud))
        for identity in (DEBUG_ID, OTHER_ID):
            self.cloud.component_rows = [dict(id=identity, codename=COMPONENT, oem_id=OWNER)]
            self.assertEqual(identity, component_cloud.resolve_component(self.cloud)["id"])

    def test_list_permission_network_and_http_errors_are_never_empty_catalogs(self):
        for reason in ("CLOUD_HTTP_401", "CLOUD_HTTP_403", "CLOUD_HTTP_404", "CLOUD_HTTP_500", "TLS_FAILED"):
            with self.subTest(reason=reason), patch.object(self.cloud, "call", side_effect=CloudFailure(reason)):
                with self.assertRaisesRegex(CloudFailure, reason):
                    self.catalog()
        with patch.object(self.cloud, "require", side_effect=CloudFailure("OEM_PERMISSION_MISSING:components_list")), \
                patch.object(self.cloud, "call") as read:
            with self.assertRaisesRegex(CloudFailure, "PERMISSION_MISSING"):
                self.catalog()
            read.assert_not_called()

    def test_malformed_or_incomplete_collections_cannot_prove_absence(self):
        for value in (dict(offset=0, total=2, items=[]), dict(offset=0, total=1, items=[{}])):
            with self.subTest(value=value), patch.object(self.cloud, "call", return_value=value):
                with self.assertRaises(CloudFailure):
                    self.catalog()

    def test_existing_identity_missing_versions_endpoint_is_not_first_publication(self):
        self.cloud.component_rows = [dict(id=DEBUG_ID, codename=COMPONENT, oem_id=OWNER)]
        call = self.cloud.call
        def read(path):
            if "/versions/" in path:
                raise CloudFailure("CLOUD_HTTP_404")
            return call(path)
        with patch.object(self.cloud, "call", side_effect=read):
            with self.assertRaisesRegex(CloudFailure, "CLOUD_HTTP_404"):
                self.catalog()

    def test_only_fake_baseline_has_no_published_versions(self):
        self.cloud.component_rows = [dict(id=DEBUG_ID, codename=COMPONENT, oem_id=OWNER)]
        self.cloud.collections["components/" + DEBUG_ID + "/versions/"] = [dict(version="0.0.0", is_fake=True)]
        self.assertEqual(dict(versions=[], componentId=DEBUG_ID, catalogState="PRESENT", latest=None), self.catalog())

    def test_baseline_worker_never_receives_destination_private_credential(self):
        service = ComponentService(SimpleNamespace(root=Path("/fixture"), catalog=SimpleNamespace(project=Path("/fixture"))))
        config = dict(componentBaselineCertificate=Path("/source-public.pem"), cloudPython=Path("/python"),
                      cloudProfiles={"oem-delivery": dict(credential=Path("/debug-private.p12"))})
        with patch("aosedge_demo_orchestrator.status.load_configuration", return_value=config), \
                patch("aosedge_demo_orchestrator.components.subprocess.run", return_value=
                      subprocess.CompletedProcess([], 0, '{"ok":true,"data":{}}', '')) as run:
            service._worker("verify-baseline", bundle="/bundle", baselineVersion="1.0.16", expectedSha256=PROFILE_BASES["v1"][1])
        request = json.loads(run.call_args.kwargs["input"])
        self.assertEqual("/source-public.pem", request["certificate"])
        self.assertNotIn("credential", request)
        self.assertNotIn("cloudDomain", request)
        self.assertNotIn("debug-private", json.dumps(request))

    def test_sign_verify_and_upload_use_the_current_session_oem_without_fallback(self):
        service = ComponentService(SimpleNamespace(root=Path("/fixture"), catalog=SimpleNamespace(project=Path("/fixture"))))
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = dict(componentBaselineCertificate=root / "source-public.pem", cloudPython=Path("/python"))
            for name, domain in (("first", "aoscloud.io"), ("selected", "developer.aos-dev.test")):
                credential = root / (name + ".p12")
                credential.write_bytes(b"non-secret routing fixture; subprocess is mocked")
                credential.chmod(0o600)
                config["cloudProfiles"] = {"oem-delivery": dict(credential=credential, expectedRole="oem", cloudDomain=domain)}
                with patch("aosedge_demo_orchestrator.status.load_configuration", return_value=config), \
                        patch("aosedge_demo_orchestrator.components.subprocess.run", return_value=
                              subprocess.CompletedProcess([], 0, '{"ok":true,"data":{}}', '')) as run:
                    for action in ("sign", "verify", "upload"):
                        service._worker(action)
                        request = json.loads(run.call_args.kwargs["input"])
                        self.assertEqual(str(credential), request["credential"])
                        self.assertEqual(domain, request["cloudDomain"])
                        self.assertNotIn("certificate", request)
                        self.assertNotIn("source-public.pem", json.dumps(request))
                    credential.unlink()
                    run.reset_mock()
                    with self.assertRaisesRegex(EnvironmentError, "OEM_CREDENTIAL_MISSING_OR_UNSAFE"):
                        service._worker("sign")
                    run.assert_not_called()


class BaselineSignatureTests(unittest.TestCase):
    def setUp(self):
        try:
            import jwt
            from cryptography import x509
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import rsa
            from cryptography.x509.oid import NameOID
        except ImportError:
            self.skipTest("Run cryptographic fixtures with the installed Aos Python runtime")
        self.jwt = jwt
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.certificate = self.root / "original-public.pem"
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        def cert(sign_key):
            name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "offline-test-only")])
            return (x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(sign_key.public_key())
                .serial_number(x509.random_serial_number()).not_valid_before(datetime.now(timezone.utc) - timedelta(days=1))
                .not_valid_after(datetime.now(timezone.utc) + timedelta(days=1)).sign(sign_key, hashes.SHA256())
                .public_bytes(serialization.Encoding.PEM))
        self.certificate.write_bytes(cert(key))
        self.other_certificate = cert(rsa.generate_private_key(public_exponent=65537, key_size=2048))
        config = b'{"schemaVersion":2}'
        batch = pack({"config.yaml": config, "payload": b"offline fixture"})
        data = [dict(name=name, size=len(raw), hash=hashlib.sha3_512(raw).hexdigest())
                for name, raw in (("batch.tar.gz", batch), ("config.yaml", config))]
        signature = jwt.encode(dict(data=data), key, algorithm="RS256").encode()
        self.bundle = self.root / "bundle.tar.gz"
        self.bundle.write_bytes(pack({"batch.tar.gz": batch, "config.yaml": config, "package.sign": signature}))
        self.digest = sha(self.bundle.read_bytes())
        self.pins = patch("aosedge_demo_orchestrator.component_build.PROFILE_BASES", {"v1": ("1.0.16", self.digest, "unused", 7)})
        self.pins.start()
        self.addCleanup(self.pins.stop)
        self.request = dict(action="verify-baseline", bundle=str(self.bundle), certificate=str(self.certificate),
                            baselineVersion="1.0.16", expectedSha256=self.digest)

    def test_original_signature_and_exact_frozen_bytes_are_both_verified(self):
        result = component_worker.execute(self.request)
        self.assertEqual("VERIFIED_RS256", result["signatureVerification"])
        self.assertEqual("PINNED_BASELINE_AND_ORIGINAL_OEM_CERTIFICATE", result["verificationTrust"])

    def test_another_oem_key_does_not_verify_the_original_baseline(self):
        self.certificate.write_bytes(self.other_certificate)
        with self.assertRaises(self.jwt.InvalidSignatureError):
            component_worker.execute(self.request)

    def test_tampered_or_unpinned_bundles_are_rejected_before_signature_use(self):
        with self.assertRaisesRegex(EnvironmentError, "BASELINE_NOT_PINNED"):
            component_worker.execute(dict(self.request, expectedSha256="0" * 64))
        self.bundle.write_bytes(self.bundle.read_bytes() + b"changed")
        with self.assertRaisesRegex(EnvironmentError, "SIGNED_DIGEST_CHANGED"):
            component_worker.execute(self.request)


if __name__ == "__main__":
    unittest.main()
