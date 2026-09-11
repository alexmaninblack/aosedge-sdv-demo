# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import contextlib
import copy
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
from urllib.parse import parse_qs, urlsplit

from aosedge_demo_orchestrator import component_worker, service_publication
from aosedge_demo_orchestrator.api import execute_operation
from aosedge_demo_orchestrator.cli import build_parser, request_from_arguments
from aosedge_demo_orchestrator.environment import EnvironmentError, atomic_json, digest
from aosedge_demo_orchestrator.service_packages import read_package
from aosedge_demo_orchestrator.unit_cloud import CloudFailure
import test_service_packages as package_fixtures
from test_services import FixtureCloud

OWNER, SERVICE = package_fixtures.OWNER, package_fixtures.SERVICE
BUNDLE = "44444444-4444-4444-8444-444444444444"
VERSION = "55555555-5555-4555-8555-555555555555"
UNIT = "66666666-6666-4666-8666-666666666666"


class PublicationCloud(FixtureCloud):
    def __init__(self):
        super().__init__()
        self.collections["services/"][0]["codename"] = "brake-health-service"
        self.collections["services/" + SERVICE + "/service-versions/"] = []
        self.collections["deployment-bundles/"] = []
        self.user["effectivePermissions"] += ["deployment_bundles_list"]

    def ready(self):
        self.collections["services/" + SERVICE + "/service-versions/"] = [dict(id=VERSION, version="8.0.0", container_state="ready")]
        self.collections["deployment-bundles/"] = [dict(id=BUNDLE, state="done", build_info=None,
            items=[dict(type="service", codename="brake-health-service", version="8.0.0")])]


class ServicePublicationTests(unittest.TestCase):
    def setUp(self):
        self.cloud = PublicationCloud()
        self.request = dict(team="brake", version="8.0.0", ownerId=OWNER, serviceId=SERVICE)

    def test_ready_needs_exact_bundle_and_ready_owned_service_version(self):
        self.cloud.ready()
        result = service_publication.snapshot(self.cloud, dict(self.request, deploymentId=BUNDLE))
        self.assertEqual("READY", result["stage"])
        self.assertEqual(VERSION, result["versionId"])
        self.assertFalse(any("units" in path for path in self.cloud.calls))
        self.assertNotIn("running", json.dumps(result).lower())
        self.cloud.collections["services/" + SERVICE + "/service-versions/"] = []
        self.assertEqual("PROCESSING", service_publication.snapshot(self.cloud, dict(self.request, deploymentId=BUNDLE))["stage"])

    def test_processing_error_unknown_and_wrong_contents_do_not_claim_ready(self):
        for state, expected in (("uploaded", "PROCESSING"), ("processing", "PROCESSING"), ("building", "PROCESSING"), ("error", "ERROR"), (None, "UNKNOWN"), ("unrecognized-new-state", "UNKNOWN")):
            with self.subTest(state=state):
                self.cloud.ready()
                self.cloud.collections["deployment-bundles/"][0]["state"] = state
                self.assertEqual(expected, service_publication.snapshot(self.cloud, dict(self.request, deploymentId=BUNDLE))["stage"])
        self.cloud.ready()
        self.cloud.collections["deployment-bundles/"][0]["items"][0]["codename"] = "tire-health-service"
        self.assertEqual("ERROR", service_publication.snapshot(self.cloud, dict(self.request, deploymentId=BUNDLE))["stage"])

    def test_lost_upload_id_is_not_adopted_by_matching_version(self):
        self.cloud.ready()
        result = service_publication.snapshot(self.cloud, self.request)
        self.assertEqual("UNCERTAIN", result["stage"])
        self.assertEqual([BUNDLE], result["candidateBundleIds"])
        self.assertIsNone(result["deploymentId"])

    def test_preflight_permits_no_vehicle_and_only_current_test_assignments(self):
        self.assertEqual(SERVICE, service_publication.snapshot(self.cloud, self.request, preflight=True)["serviceId"])
        unit = dict(id=UNIT, oem_id=OWNER, system_uid="test-uid", subjects=[])
        self.cloud.collections["services/" + SERVICE + "/units/"] = [unit]
        with self.assertRaisesRegex(CloudFailure, "NON_TEST_ASSIGNMENT"):
            service_publication.snapshot(self.cloud, self.request, preflight=True)
        self.request["test"] = dict(unitId=UNIT, systemUid="test-uid")
        self.assertEqual("CURRENT_TEST_OR_UNASSIGNED", service_publication.snapshot(self.cloud, self.request, preflight=True)["recipientScope"])
        self.cloud.collections["services/" + SERVICE + "/units/"].append(dict(unit, id=BUNDLE))
        with self.assertRaisesRegex(CloudFailure, "NON_TEST_ASSIGNMENT"):
            service_publication.snapshot(self.cloud, self.request, preflight=True)

    def test_collision_supersession_owner_change_and_pagination_fail_closed(self):
        self.cloud.ready()
        with self.assertRaisesRegex(CloudFailure, "ALREADY_PRESENT"):
            service_publication.snapshot(self.cloud, self.request, preflight=True)
        self.request["ownerId"] = BUNDLE
        with self.assertRaisesRegex(CloudFailure, "SP_BINDING"):
            service_publication.snapshot(self.cloud, self.request, preflight=True)
        self.request["ownerId"] = OWNER
        self.cloud.call = Mock(return_value=dict(items=[], total=1, offset=0))
        with self.assertRaises(CloudFailure):
            service_publication.snapshot(self.cloud, self.request, preflight=True)

    def test_mutation_worker_has_one_post_no_poll_and_truthful_uncertainty(self):
        request = dict(self.request, action="service-upload", bundle="fixture.tar.gz")
        with patch("aosedge_demo_orchestrator.service_publication.Cloud", return_value=self.cloud), \
                patch("aosedge_demo_orchestrator.component_worker.verify_service", return_value={}), \
                patch("aosedge_demo_orchestrator.service_publication.upload_bundle") as post:
            post.return_value = dict(httpStatus=201, deploymentId=BUNDLE, state="uploaded")
            result = service_publication.execute(request)
            self.assertEqual(("ACCEPTED", True), (result["stage"], result["attempted"]))
            self.assertEqual(1, post.call_count)
            self.assertEqual(1, sum(path.startswith("deployment-bundles/") for path in self.cloud.calls))
            post.side_effect = TimeoutError("must not expose raw transport")
            result = service_publication.execute(request)
            self.assertEqual(("UNCERTAIN", True), (result["stage"], result["attempted"]))
            self.cloud.ready()
            post.reset_mock()
            result = service_publication.execute(request)
            self.assertEqual(("BLOCKED", False), (result["stage"], result["attempted"]))
            post.assert_not_called()

    def test_shared_transport_uses_official_endpoint_file_field_and_one_201_response(self):
        from aosedge_demo_orchestrator.component_cloud import upload_bundle
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "deployment-bundle.tar.gz"
            path.write_bytes(b"signed-fixture")
            response = SimpleNamespace(status=201, read=lambda limit: json.dumps(dict(id=BUNDLE, state="uploaded")).encode())
            opener = Mock()
            opener.open.return_value = contextlib.nullcontext(response)
            cloud = SimpleNamespace(base="https://fixture.aoscloud.io:10000/api/v11/", opener=opener, require=Mock())
            result = upload_bundle(cloud, path, prefix="SERVICE")
            request = opener.open.call_args.args[0]
            self.assertEqual("https://fixture.aoscloud.io:10000/api/v11/deployment-bundles/upload/", request.full_url)
            self.assertEqual("POST", request.method)
            self.assertIn(b'name="file"; filename="deployment-bundle.tar.gz"', request.data)
            self.assertIn(b"signed-fixture", request.data)
            self.assertEqual(1, opener.open.call_count)
            self.assertEqual((BUNDLE, 201), (result["deploymentId"], result["httpStatus"]))

    def test_processing_failure_retains_redacted_build_info_and_never_ready(self):
        self.cloud.ready()
        bundle = self.cloud.collections["deployment-bundles/"][0]
        bundle.update(state="error", build_info="payload must be a file, not a directory")
        result = service_publication.snapshot(self.cloud, dict(self.request, deploymentId=BUNDLE))
        self.assertEqual("ERROR", result["stage"])
        self.assertEqual(bundle["build_info"], result["buildInfo"])
        bundle["build_info"] = "token=private-material"
        self.assertNotIn("private-material", json.dumps(service_publication.snapshot(self.cloud, dict(self.request, deploymentId=BUNDLE))))


class ServiceReceiptTests(unittest.TestCase):
    def setUp(self):
        package_fixtures.ServicePackageTests.setUp(self)
        self.prepared = self.packages.prepare("brake", "v1")
        self.directory = Path(self.prepared["packagePath"])
        self.handle = self.prepared["releaseHandle"]
        self.bundle = self.directory / "deployment-bundle.tar.gz"

    def signed_fixture(self):
        self.bundle.write_bytes(b"fixture: signature worker is tested separately")
        receipt = dict(sha256=digest(self.bundle), signatureVerification="VERIFIED_RS256", payloadMatchesPrepared=True)
        atomic_json(self.directory / "signed.json", receipt)
        return receipt

    def test_upload_repeat_after_acceptance_only_observes_recorded_id(self):
        self.signed_fixture()
        response = dict(stage="ACCEPTED", attempted=True, httpStatus=201, deploymentId=BUNDLE)
        self.packages._worker = Mock(side_effect=[response, dict(stage="READY", deploymentId=BUNDLE)])
        result = self.packages.upload(self.handle)
        self.assertEqual("ACCEPTED", result["stage"])
        self.assertFalse(result["noOp"])
        with patch("aosedge_demo_orchestrator.service_packages.read_package", side_effect=AssertionError("Status must not read the payload")):
            result = self.packages.upload(self.handle)
        self.assertEqual("READY", result["stage"])
        self.assertTrue(result["noOp"])
        self.assertEqual(["service-upload", "service-cloud-status"], [call.args[0] for call in self.packages._worker.call_args_list])
        self.assertEqual(BUNDLE, self.packages._worker.call_args.kwargs["deploymentId"])
        self.assertFalse((self.root / ".run/demo-current/journal.json").exists())

    def test_worker_loss_preserves_intent_and_repeat_never_posts(self):
        self.signed_fixture()
        self.packages._worker = Mock(side_effect=[EnvironmentError("SERVICE_WORKER_RESPONSE_UNAVAILABLE"), dict(stage="UNCERTAIN", deploymentId=None)])
        self.assertEqual("UNCERTAIN", self.packages.upload(self.handle)["stage"])
        self.assertEqual("UNCERTAIN", self.packages.upload(self.handle)["stage"])
        self.assertEqual(["service-upload", "service-cloud-status"], [call.args[0] for call in self.packages._worker.call_args_list])
        self.assertTrue(json.loads((self.directory / "publication.json").read_text())["attempted"])

    def test_invalid_worker_response_preserves_uncertainty_and_does_not_retry(self):
        self.signed_fixture()
        self.packages._worker = Mock(return_value=None)
        result = self.packages.upload(self.handle)
        self.assertEqual("UNCERTAIN", result["stage"])
        self.assertTrue(json.loads((self.directory / "publication.json").read_text())["attempted"])

    def test_failed_preflight_can_be_explicitly_retried_without_allocating(self):
        self.signed_fixture()
        self.packages._worker = Mock(return_value=dict(stage="BLOCKED", attempted=False, reason="SERVICE_NON_TEST_ASSIGNMENT_PRESENT"))
        self.packages.upload(self.handle)
        self.packages.upload(self.handle)
        self.assertEqual(["service-upload", "service-upload"], [call.args[0] for call in self.packages._worker.call_args_list])
        self.assertEqual("8.0.0", json.loads((self.root / ".local/release-continuity.json").read_text())["versions"]["brake"])

    def test_changed_signed_or_prepared_input_does_not_start_upload(self):
        self.signed_fixture()
        self.packages._worker = Mock()
        self.bundle.write_bytes(b"changed")
        with self.assertRaisesRegex(EnvironmentError, "BUNDLE_CHANGED"):
            self.packages.upload(self.handle)
        self.packages._worker.assert_not_called()
        path = self.directory / "service/arm64/usr/bin/brake-health-service"
        path.chmod(0o644)
        with self.assertRaisesRegex(EnvironmentError, "MODE_CHANGED"):
            self.packages.sign(self.handle)
        self.assertFalse((self.directory / "publication.json").exists())

    def test_completed_sign_output_reconciles_missing_receipt_without_resigning(self):
        self.bundle.write_bytes(b"fixture")
        response = dict(sha256=digest(self.bundle), signatureVerification="VERIFIED_RS256", payloadMatchesPrepared=True)
        self.packages._worker = Mock(return_value=response)
        self.assertTrue(self.packages.sign(self.handle)["noOp"])
        self.assertEqual("service-verify", self.packages._worker.call_args.args[0])
        self.assertEqual(response, json.loads((self.directory / "signed.json").read_text()))

    def test_handle_traversal_and_extra_payload_are_rejected(self):
        for handle in ("../8.0.0", "brake/../../secret", "brake", "tire/01.0.0"):
            with self.assertRaises(EnvironmentError):
                self.packages.sign(handle)
        (self.directory / "service/arm64/extra").write_text("unexpected")
        with self.assertRaisesRegex(EnvironmentError, "CONTENT_CHANGED"):
            read_package(self.directory, "brake", "8.0.0")

    def test_cli_has_no_second_version_or_account_override_and_browser_remains_read_only(self):
        for action in ("sign", "upload", "cloud-status"):
            request = request_from_arguments(build_parser().parse_args(["service", action, self.handle]))
            self.assertEqual(self.handle, request.service_release)
            self.assertIsNone(request.component_version)
            self.assertIsNone(request.profile)
            with self.assertRaises(ValueError):
                execute_operation(dict(domain="service", action=action, service_release=self.handle), Mock())


@unittest.skipUnless(importlib.util.find_spec("aos_signer"), "run with the installed official Aos signer Python")
class OfficialSigningTests(unittest.TestCase):
    def setUp(self):
        ServiceReceiptTests.setUp(self)

    def test_real_signature_with_ephemeral_key_and_exact_payload_no_cloud(self):
        import datetime
        from cryptography import x509
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives.serialization.pkcs12 import serialize_key_and_certificates
        from cryptography.x509.oid import NameOID
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Offline Demo Control fixture")])
        now = datetime.datetime.now(datetime.timezone.utc)
        certificate = (x509.CertificateBuilder().subject_name(subject).issuer_name(subject).public_key(key.public_key())
            .serial_number(x509.random_serial_number()).not_valid_before(now - datetime.timedelta(minutes=1))
            .not_valid_after(now + datetime.timedelta(hours=1)).sign(key, hashes.SHA256()))
        credential = self.base / "fixture.p12"
        credential.write_bytes(serialize_key_and_certificates(b"fixture", key, certificate, None, serialization.NoEncryption()))
        credential.chmod(0o600)
        request = dict(action="service-sign", directory=str(self.directory), bundle=str(self.bundle),
            team="brake", version="8.0.0", ownerId=OWNER, credential=str(credential))
        with patch("aosedge_demo_orchestrator.unit_cloud.Cloud") as authority, contextlib.redirect_stdout(io.StringIO()):
            result = component_worker.execute(request)
        self.assertEqual("VERIFIED_RS256", result["signatureVerification"])
        self.assertTrue(result["payloadMatchesPrepared"])
        authority.assert_called_once_with(request, expected_role="service provider")
        self.assertEqual("CONFIGURED_SP_SIGNING_CERTIFICATE", result["verificationTrust"])
        verified = component_worker.execute(dict(request, action="service-verify", expectedSha256=result["sha256"]))
        self.assertEqual(result, verified)
        with self.assertRaisesRegex(EnvironmentError, "DIGEST_CHANGED"):
            component_worker.execute(dict(request, action="service-verify", expectedSha256="0" * 64))
        with self.assertRaisesRegex(EnvironmentError, "SIGN_OUTPUT_EXISTS"), \
                patch("aosedge_demo_orchestrator.unit_cloud.Cloud"):
            component_worker.execute(request)


if __name__ == "__main__":
    unittest.main()
