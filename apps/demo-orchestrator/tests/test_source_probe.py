# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import base64
import hashlib
import json
import unittest
from unittest.mock import Mock, patch

from aosedge_demo_orchestrator.source_guest import probe


class Stream:
    def __init__(self, data):
        self.data = data
        self.sent = []
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def recv(self, length):
        chunk, self.data = self.data[:length], self.data[length:]
        return chunk
    def sendall(self, data): self.sent.append(data)


class SourceProbeTests(unittest.TestCase):
    def check(self, ids=(10, 11), protocol="VISSv3", path="Vehicle.CarlaSimulation.FrameId", safe_stop=False):
        key = base64.b64encode(b"a" * 16).decode()
        accept = base64.b64encode(hashlib.sha1((key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode()).digest()).decode()
        data = ("HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
            "Sec-WebSocket-Accept: " + accept + "\r\nSec-WebSocket-Protocol: " + protocol + "\r\n\r\n").encode()
        for index, value in enumerate(ids):
            body = json.dumps(dict(action="get", requestId="democtl",
                data=dict(path=path, dp=dict(value=str(value), ts=str(index))))).encode()
            data += bytes([0x81, 126]) + len(body).to_bytes(2, "big") + body
        stream = Stream(data)
        context = Mock()
        context.wrap_socket.return_value = stream
        with patch("aosedge_demo_orchestrator.source_guest.ssl.create_default_context", return_value=context) as tls, \
             patch("aosedge_demo_orchestrator.source_guest.socket.create_connection", return_value=stream), \
             patch("aosedge_demo_orchestrator.source_guest.os.urandom", side_effect=lambda n: b"a" * n), \
             patch("aosedge_demo_orchestrator.source_guest.time.sleep"):
            result = probe(safe_stop=safe_stop)
        self.assertEqual("127.0.0.1", context.wrap_socket.call_args.kwargs["server_hostname"])
        self.assertIn("cafile", tls.call_args.kwargs)
        self.assertIn(b"Sec-WebSocket-Protocol: VISSv3\r\n", stream.sent[0])
        return result

    def test_server_verified_two_advancing_frames(self):
        self.assertTrue(self.check()["advancingVissFrames"])

    def test_safe_stop_reports_acquisition_per_snapshot_not_final_probe_time(self):
        with patch("aosedge_demo_orchestrator.source_guest.time.time", side_effect=[10, 11, 12]):
            value = self.check(safe_stop=True)
        self.assertEqual([10000, 11000], value["snapshotAcquiredEpochMilliseconds"])
        self.assertEqual(12000, value["guestEpochMilliseconds"])
        self.assertEqual("ROOT_NETWORK_PROBE_NOT_SM_PROCESS_OBSERVATION", value["evidence"])

    def test_timestamp_change_without_frame_advance_is_not_fresh_data(self):
        self.assertEqual("VISS_FRAME_NOT_ADVANCING", self.check(ids=(10, 10))["reason"])

    def test_wrong_protocol_is_not_a_viss_connection(self):
        self.assertFalse(self.check(protocol="wrong")["serverTls"])

    def test_wrong_signal_is_not_frame_evidence(self):
        self.assertEqual("VISS_PROBE_FRAME_PATH_MISMATCH", self.check(path="Vehicle.Speed")["reason"])
