# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
import copy
import json
import os
import socket
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from aosedge_demo_orchestrator.environment import EnvironmentError
from aosedge_demo_orchestrator import source_trust as trust

VEHICLE = dict(unitId="42c0bf43-4eb7-44e6-8c74-f60f9959da66",
    nodeId="e78b9d9d-f613-48f0-8fbf-b3f17c6a61ca",
    localVmId="6fcf5a74-0b74-4ef0-a05d-44bad598ab94",
    cloud=dict(lifecycle="ONLINE", identity=dict(nodeHardwareId="6fcf5a740b744ef0a05d44bad598ab94")))


class TrustTests(unittest.TestCase):
    def test_cloud_node_and_native_node_are_not_conflated(self):
        value = trust.identity(VEHICLE)
        self.assertNotEqual(value["nodeId"].replace("-", ""), value["nodeHardwareId"])
        bad = copy.deepcopy(VEHICLE)
        bad["cloud"]["identity"]["nodeHardwareId"] = "0" * 32
        with self.assertRaisesRegex(EnvironmentError, "PROVISIONING_BINDING_REQUIRED"):
            trust.identity(bad)

    def test_unprovisioned_does_not_issue_placeholder(self):
        with self.assertRaises((EnvironmentError, ValueError)):
            trust.identity(dict(localVmId=VEHICLE["localVmId"]))

    @unittest.skipUnless(Path(trust.OPENSSL).is_file(), "OpenSSL 3 unavailable")
    def test_real_ca_purpose_bound_leaves_repeat_and_conflict(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "trust"
            first = trust.prepare(path, VEHICLE)
            before = {p.name: p.read_bytes() for p in path.iterdir()}
            self.assertEqual(first, trust.prepare(path, VEHICLE))
            self.assertEqual(before, {p.name: p.read_bytes() for p in path.iterdir()})
            self.assertEqual(3, len(set(first["fingerprints"].values())))
            self.assertNotIn("BEGIN", json.dumps(first))
            self.assertEqual(trust.FILES, set(before))
            for file in path.iterdir():
                self.assertEqual(0o600, file.stat().st_mode & 0o777)
            changed = dict(VEHICLE, nodeId="e78b9d9d-f613-48f0-8fbf-b3f17c6a61cb")
            with self.assertRaisesRegex(EnvironmentError, "IDENTITY_CONFLICT"):
                trust.prepare(path, changed)
            os.chmod(path / "vdp-key.pem", 0o644)
            with self.assertRaisesRegex(EnvironmentError, "FILE_UNSAFE"):
                trust.prepare(path, VEHICLE)

    def test_symlink_store_is_rejected_without_crypto_or_replacement(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            real = root / "outside"
            real.mkdir()
            (root / "trust").symlink_to(real)
            with patch.object(trust, "openssl") as crypto:
                with self.assertRaisesRegex(EnvironmentError, "FILE_UNSAFE"):
                    trust.prepare(root / "trust", VEHICLE)
            crypto.assert_not_called()

    def test_partial_store_is_never_silently_reissued(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "trust"
            path.mkdir(mode=0o700)
            with patch.object(trust, "openssl") as crypto:
                with self.assertRaisesRegex(EnvironmentError, "MATERIAL_INCOMPLETE"):
                    trust.prepare(path, VEHICLE)
            crypto.assert_not_called()

    def test_assignment_is_one_bounded_request_no_secret(self):
        with tempfile.TemporaryDirectory(dir="/tmp") as temporary:
            path = Path(temporary) / "a.sock"
            received = []
            with socket.socket(socket.AF_UNIX) as server:
                server.bind(str(path))
                path.chmod(0o600)
                server.listen(1)
                def respond():
                    with server.accept()[0] as peer:
                        with peer.makefile("rb") as stream:
                            request = json.loads(stream.readline())
                        received.append(request)
                        peer.sendall((json.dumps(dict(schemaVersion=1, requestId=request["requestId"],
                            result="ACCEPTED", state="DETACHED", assignmentGeneration=1)) + "\n").encode())
                worker = threading.Thread(target=respond)
                worker.start()
                result = trust.assignment(path, "status")
                worker.join(2)
                self.assertEqual("DETACHED", result["state"])
                self.assertEqual(1, len(received))
                self.assertEqual({"schemaVersion", "action", "requestId"}, set(received[0]))


if __name__ == "__main__":
    unittest.main()
