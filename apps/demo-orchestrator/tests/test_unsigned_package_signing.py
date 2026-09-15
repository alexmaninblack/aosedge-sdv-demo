# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Offline trust-boundary tests: real Aos signer, disposable keys, no Cloud/VM."""

import contextlib
import datetime
import io
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from aosedge_demo_orchestrator import component_worker
from aosedge_demo_orchestrator.component_build import PROFILE_BASES, pack, replay
from aosedge_demo_orchestrator.component_sources import UNSIGNED_SHA, source
from aosedge_demo_orchestrator.components import ComponentService, sha, archive_files
from aosedge_demo_orchestrator.environment import EnvironmentError, atomic_json
from aosedge_demo_orchestrator.package_artifacts import context, digest, paths, publication_path, credential_stamp
from aosedge_demo_orchestrator.service_packages import ServicePackages
from test_component_replay import inputs
import test_service_packages as service_fixtures


def credential(path, domain):
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives.serialization.pkcs12 import serialize_key_and_certificates
    from cryptography.x509.oid import NameOID
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Disposable test fixture"),
                        x509.NameAttribute(NameOID.ORGANIZATION_NAME, domain)])
    stamp = datetime.datetime.now(datetime.timezone.utc)
    cert = (x509.CertificateBuilder().subject_name(subject).issuer_name(subject).public_key(key.public_key())
        .serial_number(x509.random_serial_number()).not_valid_before(stamp - datetime.timedelta(minutes=1))
        .not_valid_after(stamp + datetime.timedelta(hours=1)).sign(key, hashes.SHA256()))
    path.write_bytes(serialize_key_and_certificates(b"fixture", key, cert, None, serialization.NoEncryption()))
    path.chmod(0o600)


class UnsignedSourceTests(unittest.TestCase):
    def test_pinned_migration_all_profiles_no_old_key_and_reusable_without_legacy_archive(self):
        for profile in PROFILE_BASES:
            with self.subTest(profile=profile), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                service = ComponentService(SimpleNamespace(catalog=SimpleNamespace(project=root)))
                version, _, module, count = PROFILE_BASES[profile]
                directory = service._directory(version)
                directory.mkdir(parents=True)
                inner = pack({"config.yaml": b"{}", "fixture": profile.encode()})
                legacy = pack({"config.yaml": b"{}", "batch.tar.gz": inner, "package.sign": b"historical signature"})
                path = directory / ("vdp-" + version + "-deployment-bundle.tar.gz")
                path.write_bytes(legacy)
                with patch.dict(PROFILE_BASES, {profile: (version, sha(legacy), module, count)}), \
                        patch.dict(UNSIGNED_SHA, {version: sha(inner)}), \
                        patch.object(service, "_inspect", return_value=({"problems": []}, {"runtime": b"unchanged"})), \
                        patch.object(service, "_worker", side_effect=AssertionError("No certificate/API worker for source migration"), create=True):
                    first, files = source(service, version, materialize=True)
                    self.assertEqual("VERIFIED_PINNED_DIGESTS", first["sourceIntegrity"])
                    canonical = service.root / ".source-profiles" / version / "package.tar.gz"
                    self.assertEqual(inner, canonical.read_bytes())
                    path.unlink()  # Disposable fixture only: canonical source is self-sufficient.
                    self.assertEqual((first, files), source(service, version, materialize=True))
                    canonical.chmod(0o600)
                    canonical.write_bytes(b"corrupt")
                    with self.assertRaisesRegex(EnvironmentError, "DIGEST"):
                        source(service, version)

    def test_unsigned_integrity_is_not_claimed_for_changed_legacy_input(self):
        with tempfile.TemporaryDirectory() as temp:
            service = ComponentService(SimpleNamespace(catalog=SimpleNamespace(project=Path(temp))))
            directory = service._directory("1.0.16")
            directory.mkdir(parents=True)
            (directory / "vdp-1.0.16-deployment-bundle.tar.gz").write_bytes(b"changed")
            with self.assertRaisesRegex(EnvironmentError, "DIGEST"):
                source(service, "1.0.16", materialize=True)
            self.assertFalse((service.root / ".source-profiles/1.0.16").exists())


@unittest.skipUnless(all(importlib.util.find_spec(name) for name in ("cryptography", "aos_signer", "jwt")),
    "Real signing fixtures require the separately installed Aos SDK Python environment")
class PackageSigningTests(unittest.TestCase):
    def setUp(self):
        service_fixtures.ServicePackageTests.setUp(self)
        self.domain = "first.example.test"
        self.key = self.base / "session.p12"
        credential(self.key, self.domain)
        self.config = dict(cloudPython=Path(__import__("sys").executable), cloudProfiles={
            "service-provider": dict(credential=self.key, cloudDomain=self.domain, expectedRole="service provider"),
            "oem-delivery": dict(credential=self.key, cloudDomain=self.domain, expectedRole="oem")})
        config_patch = patch("aosedge_demo_orchestrator.service_packages.load_configuration", return_value=self.config)
        config_patch.start()
        self.addCleanup(config_patch.stop)
        self.payload = self.packages.prepare("brake", "v1")
        self.directory = Path(self.payload["packagePath"])
        self.handle = self.payload["releaseHandle"]

    def test_service_real_worker_repeat_rotation_cross_cloud_and_payload_immutable(self):
        before = {name: (self.directory / name).read_bytes() for name in self.payload["files"]}
        ledger = (self.root / ".local/release-continuity.json").read_bytes()
        first = self.packages.sign(self.handle)
        self.assertEqual("VERIFIED_RS256", first["signatureVerification"])
        self.assertFalse(first["noOp"])
        self.assertTrue(self.packages.sign(self.handle)["noOp"])
        self.assertTrue(self.packages.receipts()["releases"][0]["signed"])
        credential(self.key, self.domain)  # Rotate at the same file path.
        self.assertFalse(self.packages.receipts()["releases"][0]["signed"])
        with self.assertRaisesRegex(EnvironmentError, "SIGN_FOR_SELECTED_CLOUD"):
            self.packages.upload(self.handle)
        rotated = self.packages.sign(self.handle)
        self.assertNotEqual(first["bundlePath"], rotated["bundlePath"])
        self.assertFalse(rotated["noOp"])
        self.domain = "second.example.test"
        credential(self.key, self.domain)
        self.config["cloudProfiles"]["service-provider"]["cloudDomain"] = self.domain
        other = self.packages.sign(self.handle)
        self.assertNotEqual(rotated["bundlePath"], other["bundlePath"])
        self.assertEqual(self.domain, other["cloudDomain"])
        self.assertEqual(before, {name: (self.directory / name).read_bytes() for name in before})
        self.assertEqual(ledger, (self.root / ".local/release-continuity.json").read_bytes())
        self.assertNotIn("serviceProviderId", self.payload)
        self.assertNotIn("serviceId", self.payload)

    def test_domain_mismatch_blocks_before_signing(self):
        self.config["cloudProfiles"]["service-provider"]["cloudDomain"] = "wrong.example.test"
        with self.assertRaisesRegex(EnvironmentError, "CLOUD_CERTIFICATE_DOMAIN_CHANGED"):
            self.packages.sign(self.handle)
        self.assertFalse((self.directory / ".signatures").exists())

    def test_service_publication_resolves_destination_ids_not_legacy_prepared_ids(self):
        old_id = "99999999-9999-4999-8999-999999999999"
        atomic_json(self.directory / "prepared.json", dict(self.payload, serviceId=old_id, serviceProviderId=old_id))
        self.packages.sign(self.handle)
        original = self.packages._worker
        posted = []

        def worker(action, directory, record, **values):
            if action == "service-upload":
                self.assertEqual(service_fixtures.OWNER, values["ownerId"])
                self.assertEqual(service_fixtures.SERVICE, values["serviceId"])
                self.assertEqual(self.domain, values["expectedSigningContext"]["domain"])
                posted.append(values)
                return dict(stage="ACCEPTED", attempted=True, httpStatus=201, deploymentId=service_fixtures.SERVICE)
            if action == "service-cloud-status":
                self.assertEqual(service_fixtures.OWNER, values["ownerId"])
                self.assertEqual(self.domain, values["expectedCloudDomain"])
                return dict(stage="READY", serviceId=service_fixtures.SERVICE)
            return original(action, directory, record, **values)

        with patch.object(self.packages, "_worker", side_effect=worker):
            self.assertEqual("ACCEPTED", self.packages.upload(self.handle)["stage"])
            credential(self.key, self.domain)
            self.assertTrue(self.packages.upload(self.handle)["noOp"])
        self.assertEqual(1, len(posted))
        saved = json.loads(publication_path(self.directory, self.domain, "service provider").read_text())
        self.assertEqual(service_fixtures.OWNER, saved["ownerId"])

    def test_tire_uses_same_real_signing_path_without_cloud_or_old_sp(self):
        rootfs = self.base / "tire-product/rootfs"
        binaries = {}
        for name in ("bootstrap", "service"):
            destination = rootfs / ("usr/bin/tire-health-" + name)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes((self.base / "product/rootfs/usr/bin" / ("brake-health-" + name)).read_bytes())
            destination.chmod(0o755)
            binaries[str(destination.relative_to(rootfs.parent))] = sha(destination.read_bytes())
        license_file = rootfs / "usr/share/licenses/tire-health-service/LICENSE"
        license_file.parent.mkdir(parents=True)
        license_file.write_text("Disposable fixture license")
        self.builder.return_value.execute.return_value = dict(sourceRevision="b" * 40, outputPath=str(rootfs.parent), binaries=binaries)
        prepared = self.packages.prepare("tire", "v1", without_permissions=True, demo_mocked_data=True)
        signed = self.packages.sign(prepared["releaseHandle"])
        self.assertEqual("VERIFIED_RS256", signed["signatureVerification"])
        self.assertTrue(signed["payloadMatchesPrepared"])
        self.assertTrue(self.packages.sign(prepared["releaseHandle"])["noOp"])

    def test_real_vdp_signature_uses_same_prepared_bytes_with_new_signer(self):
        base, pinned, contract = inputs("v1")
        files, record = replay("40.0.0", "v1", base, pinned, contract, {"version": "factory", "sha256": "factory"})
        service = ComponentService(self.environment)
        directory = service._directory("40.0.0")
        directory.mkdir(parents=True)
        for name, raw in files.items():
            target = directory / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
        unsigned = pack(files)
        path = directory / "aosedge-vdp-component-40.0.0-linux-arm64.unsigned.tar.gz"
        path.write_bytes(unsigned)
        atomic_json(directory / "prepared.json", dict(record, preparedSha256=sha(unsigned), files={name: sha(raw) for name, raw in files.items()}))
        with patch("aosedge_demo_orchestrator.status.load_configuration", return_value=self.config):
            first = service.sign("40.0.0")
            self.assertEqual("VERIFIED_RS256", first["signatureVerification"])
            self.assertTrue(service.sign("40.0.0")["noOp"])
            credential(self.key, self.domain)
            with self.assertRaisesRegex(EnvironmentError, "SIGN_FOR_SELECTED_CLOUD"):
                service.verify("40.0.0")
            second = service.sign("40.0.0")
            self.assertNotEqual(first["sha256"], second["sha256"])
            self.assertEqual(unsigned, path.read_bytes())
            self.assertEqual("VERIFIED_RS256", service.verify("40.0.0")["signatureVerification"])

    def test_attempt_receipt_is_cloud_scoped_not_signer_scoped(self):
        path = publication_path(self.directory, self.domain, "service provider", create=True)
        atomic_json(path, dict(attempted=True, ownerId="11111111-1111-4111-8111-111111111111", stage="UNCERTAIN"))
        credential(self.key, self.domain)
        with patch.object(self.packages, "cloud_status", return_value={"stage": "UNCERTAIN"}) as observed, \
                patch.object(self.packages, "_worker", side_effect=AssertionError("No second POST/signature required")):
            self.assertTrue(self.packages.upload(self.handle)["noOp"])
            observed.assert_called_once_with(self.handle)
        self.assertNotEqual(path, publication_path(self.directory, "second.example.test", "service provider"))

    def test_credential_snapshot_removed_and_consistent_if_original_rotates(self):
        request = dict(credential=str(self.key), cloudDomain=self.domain, role="oem")
        with component_worker.credential_snapshot(request) as snap:
            copied = Path(snap["credential"])
            old = component_worker.credential_identity(snap)
            credential(self.key, self.domain)
            self.assertEqual(old, component_worker.credential_identity(snap))
            self.assertNotEqual(old, component_worker.credential_identity(request))
        self.assertFalse(copied.exists())
