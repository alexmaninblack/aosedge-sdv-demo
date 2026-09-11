# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Native IAM transport tests; no Cloud, SSH server or real credentials."""

import io
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock, patch

from aosedge_demo_orchestrator.environment import EnvironmentError
from aosedge_demo_orchestrator.service_inputs import ServiceInputs
from aosedge_demo_orchestrator.unit_cloud import CloudFailure, execute

STUB = "aos_prov.communication.unit.v6.generated.iamanager_pb2_grpc.IAMPublicIdentityServiceStub"


@unittest.skipUnless(importlib.util.find_spec("aos_prov"), "run with the installed official Aos SDK Python")
class NativeIAMTests(unittest.TestCase):
    def test_server_authenticated_iam_tls_with_fixed_name_no_cloud_or_plaintext(self):
        request = dict(action="service-native-identity", address="unix:/tmp/democtl-native-test/iam.sock")
        resource = Mock()
        resource.joinpath.return_value.read_bytes.return_value = b"public-root-fixture"
        with patch("importlib.resources.files", return_value=resource), patch("grpc.secure_channel") as secure, patch(
                "grpc.insecure_channel") as insecure, patch("grpc.ssl_channel_credentials") as credentials, patch(
                STUB) as stub, patch("aosedge_demo_orchestrator.unit_cloud.Cloud") as cloud:
            stub.return_value.GetSystemInfo.return_value.system_id = "native-unit"
            result = execute(request)
        self.assertEqual(dict(systemUid="native-unit", source="IAM_V6_GET_SYSTEM_INFO"), result)
        credentials.assert_called_once_with(root_certificates=b"public-root-fixture")
        options = dict(secure.call_args.kwargs["options"])
        self.assertEqual("main", options["grpc.ssl_target_name_override"])
        self.assertEqual("main", options["grpc.default_authority"])
        self.assertEqual(0, options["grpc.enable_http_proxy"])
        self.assertEqual(5, stub.return_value.GetSystemInfo.call_args.kwargs["timeout"])
        resource.joinpath.assert_called_once_with("files/1rootCA.crt")
        cloud.assert_not_called()
        insecure.assert_not_called()

    def test_invalid_socket_and_native_uid_are_rejected(self):
        for address in ("main:8090", "unix:/tmp/foreign/iam.sock", "unix:/tmp/democtl-native-../../iam.sock"):
            with patch("grpc.secure_channel") as channel, self.assertRaisesRegex(CloudFailure, "SOCKET_INVALID"):
                execute(dict(action="service-native-identity", address=address))
            channel.assert_not_called()
        with patch("grpc.secure_channel"), patch(STUB) as stub:
            stub.return_value.GetSystemInfo.return_value.system_id = "untrusted\nidentity"
            with self.assertRaisesRegex(CloudFailure, "IDENTITY_INVALID"):
                execute(dict(action="service-native-identity", address="unix:/tmp/democtl-native-test/iam.sock"))

    def test_rpc_diagnostic_is_fixed_not_raw_details(self):
        import grpc

        class Failure(grpc.RpcError):
            def code(self):
                return grpc.StatusCode.UNAVAILABLE

            def details(self):
                return "Socket closed; forbidden-private-fixture"

        with patch("grpc.secure_channel"), patch(STUB) as stub:
            stub.return_value.GetSystemInfo.side_effect = Failure()
            with self.assertRaises(CloudFailure) as raised:
                execute(dict(action="service-native-identity", address="unix:/tmp/democtl-native-test/iam.sock"))
        self.assertEqual("SERVICE_NATIVE_IAM_RPC_UNAVAILABLE_SOCKET_CLOSED", str(raised.exception))


@unittest.skipUnless(importlib.util.find_spec("cryptography"), "certificate parser test requires cryptography")
class PublicTrustTests(unittest.TestCase):
    def test_public_certificate_only_and_exact_hostname_result(self):
        import datetime
        from cryptography import x509
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.x509.oid import NameOID
        from aosedge_demo_orchestrator import service_inputs_guest as guest

        # The ephemeral key remains in memory; only a synthetic public
        # certificate reaches the parser. No Unit credential is read.
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Server")])
        now = datetime.datetime.now(datetime.timezone.utc)
        certificate = (x509.CertificateBuilder().subject_name(name).issuer_name(name)
            .public_key(key.public_key()).serial_number(x509.random_serial_number())
            .not_valid_before(now - datetime.timedelta(minutes=1)).not_valid_after(now + datetime.timedelta(days=1))
            .add_extension(x509.SubjectAlternativeName([x509.DNSName("Server")]), critical=False)
            .sign(key, hashes.SHA256()).public_bytes(serialization.Encoding.PEM))
        with patch.object(guest, "read_public", return_value=certificate) as source, patch.object(guest.subprocess, "run") as command:
            command.return_value = subprocess.CompletedProcess([], 0, b"Hostname Server does match certificate\n", b"")
            self.assertEqual(certificate, guest.trust())
            source.assert_called_with(guest.CERTIFICATE, 32768)
            self.assertEqual(["-checkhost", "Server"], command.call_args.args[0][-2:])
            # OpenSSL can return zero even when the hostname does not match.
            command.return_value = subprocess.CompletedProcess([], 0, b"Hostname Server does NOT match certificate\n", b"")
            with self.assertRaisesRegex(ValueError, "HOST_MISMATCH"):
                guest.trust()
            for invalid in (certificate + certificate, certificate + b"-----BEGIN PRIVATE KEY-----\n", b"not a certificate"):
                source.return_value = invalid
                with self.assertRaisesRegex(ValueError, "PUBLIC_CERTIFICATE_REQUIRED"):
                    guest.trust()


class IAMForwardTests(unittest.TestCase):
    def test_private_unix_forward_cleanup_success_timeout_and_denial(self):
        service = ServiceInputs(SimpleNamespace(root=Path("/fixture")))
        state = dict(vehicles=dict(test=dict(sshPort=2222)))
        for outcome in ("success", "timeout", "denied"):
            with self.subTest(outcome=outcome), tempfile.TemporaryDirectory() as directory:
                (Path(directory) / "iam.sock").touch()
                forward = MagicMock()
                forward.__enter__.return_value = forward
                forward.stderr = io.BytesIO(b"administratively prohibited: forbidden-fixture" if outcome == "denied" else b"")
                temporary = MagicMock()
                temporary.__enter__.return_value = directory
                with patch("aosedge_demo_orchestrator.service_inputs.tempfile.TemporaryDirectory", return_value=temporary), patch(
                        "aosedge_demo_orchestrator.service_inputs.load_configuration", return_value=dict(cloudPython="/sdk/python")), patch(
                        "aosedge_demo_orchestrator.service_inputs.ssh_command",
                        return_value=["ssh", "-o", "ClearAllForwardings=yes", "root@localhost", "sh", "-s"]), patch(
                        "aosedge_demo_orchestrator.service_inputs.subprocess.Popen", return_value=forward) as start, patch(
                        "aosedge_demo_orchestrator.service_inputs.subprocess.run") as worker:
                    worker.return_value = subprocess.CompletedProcess([], 0, json.dumps(dict(ok=True, data=dict(systemUid="native-unit"))), "")
                    if outcome == "timeout":
                        worker.side_effect = subprocess.TimeoutExpired("fixture", 10)
                        with self.assertRaises(subprocess.TimeoutExpired):
                            service.identity(state, "main:8090")
                    elif outcome == "denied":
                        with self.assertRaisesRegex(EnvironmentError, "SSH_FORWARDING_DENIED"):
                            service.identity(state, "main:8090")
                    else:
                        self.assertEqual("native-unit", service.identity(state, "main:8090"))
                arguments = start.call_args.args[0]
                self.assertIn(str(Path(directory) / "iam.sock") + ":127.0.0.1:8090", arguments)
                self.assertIn("ClearAllForwardings=no", arguments)
                self.assertNotIn("sh", arguments)
                forward.terminate.assert_called_once()
                forward.wait.assert_called_once_with(timeout=3)

    def test_unconfigured_endpoint_does_not_open_forward(self):
        service = ServiceInputs(SimpleNamespace(root=Path("/fixture")))
        with patch("aosedge_demo_orchestrator.service_inputs.subprocess.Popen") as forward:
            with self.assertRaisesRegex(EnvironmentError, "ENDPOINT_UNSUPPORTED"):
                service.identity({}, "external:8090")
            forward.assert_not_called()
