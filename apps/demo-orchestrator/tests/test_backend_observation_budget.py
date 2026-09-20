# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Bounded local HTTP faults only; no running backend/VM/Cloud is accessed."""
import json
import http.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import threading
import time
import unittest
import subprocess
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from aosedge_demo_orchestrator.backends import BackendService, observation_connection
from aosedge_demo_orchestrator.environment import EnvironmentError


class Connection:
    instances = []
    slow_paths = set()
    def __init__(self, host, port, timeout):
        self.host, self.port, self.timeout = host, port, timeout
        self.sock = self
        self.stopped = threading.Event()
        self.closed = False
        self.instances.append(self)
    def request(self, method, path, headers):
        self.path = path
    def getresponse(self):
        self.status = 200
        return self
    def read(self, limit):
        if self.path in self.slow_paths:
            if not self.stopped.wait(12):
                raise AssertionError("Watchdog did not interrupt the read")
            raise OSError("fixture interrupted")
        if self.path.endswith("demo-mock/summary"):
            value = dict(source="DEMO_MOCK", vehicleTelemetry=False, unitSystemUid="test")
        elif self.path.endswith("demo-reset"):
            value = dict(schemaVersion=1, unitSystemUid="test", connected=False, command=None)
        elif "/function-observations?" in self.path:
            value = dict(schemaVersion=3, contractVersion="3.0.0", resourceType="FUNCTION_OBSERVATION", unitSystemUid="test", items=[], truncated=False)
        else:
            kind = next((v for k, v in {"windows": "WINDOW", "assessments": "ASSESSMENT", "events": "EVENT", "advisories": "ADVISORY"}.items() if f"/{k}?" in self.path), None)
            value = dict(unitSystemUid="test", resourceType=kind, items=[])
        return json.dumps(value).encode()
    def shutdown(self, _):
        self.stopped.set()
    def close(self):
        self.closed = True


class ObservationBudgetTests(unittest.TestCase):
    def setUp(self):
        Connection.instances = []
        Connection.slow_paths = set()

    def full_path(self, action="inspect", docker_duration=2, foreign=False):
        """Actual ownership/execute path; simulated subprocess and HTTP latency."""
        clock, timeouts = [0.0], []
        owner = "11111111-1111-4111-8111-111111111111"
        image = "sha256:" + "a" * 64
        state = dict(kind="democtl.current-run", vehicles=dict(test=dict(systemUid="test")),
            operations=[dict(id=owner, **{"class": "LOCAL_CREATE"}, state="COMPLETED")],
            backends=dict(brake=dict(imageId=image)))
        service = BackendService.__new__(BackendService)
        service.root = Path("/unused-fixture-environment")
        container = dict(State=dict(Running=True), Image=image,
            Config=dict(Labels={"tech.aosedge.demo.owner": "foreign" if foreign else owner,
                "tech.aosedge.demo.team": "brake"}))
        def run(args, *, timeout, **kwargs):
            timeouts.append(timeout)
            clock[0] += min(docker_duration, timeout)
            if docker_duration > timeout:
                raise subprocess.TimeoutExpired(args, timeout)
            return SimpleNamespace(returncode=0, stderr="", stdout="abc" if args[2] == "ls" else json.dumps([container]))
        class Response(Connection):
            def read(self, limit):
                clock[0] += min(2, self.timeout)
                if self.timeout < 2:
                    raise TimeoutError("fixture timeout")
                return super().read(limit)
        with patch("aosedge_demo_orchestrator.backends.read_json", return_value=state), \
             patch("aosedge_demo_orchestrator.backends.shutil.which", return_value="/fixture/docker"), \
             patch("aosedge_demo_orchestrator.backends.subprocess.run", side_effect=run), \
             patch("aosedge_demo_orchestrator.backends.time.monotonic", side_effect=lambda: clock[0]), \
             patch("aosedge_demo_orchestrator.backends.http.client.HTTPConnection", Response):
            try:
                result = service.execute(action, "brake", window_id="4cba2d80-c04a-4d24-9f03-f4a85d56da13")
            except EnvironmentError as error:
                result = error
        return clock[0], timeouts, result

    def test_whole_observation_budget_includes_docker_preflight(self):
        elapsed, timeouts, result = self.full_path()
        self.assertEqual([10, 8], timeouts)
        self.assertEqual(10, elapsed)
        self.assertEqual("PARTIAL", result["state"])
        self.assertEqual("BACKEND_READ_BUDGET_EXHAUSTED", result["observations"]["functionObservations"]["reason"])

    def test_slow_preflight_fails_closed_before_http_without_retry(self):
        elapsed, timeouts, result = self.full_path(docker_duration=7)
        self.assertEqual([10, 3], timeouts)
        self.assertEqual(10, elapsed)
        self.assertIsInstance(result, EnvironmentError)
        self.assertEqual([], Connection.instances)

    def test_window_preflight_shares_shorter_budget_and_keeps_ownership_check(self):
        elapsed, timeouts, result = self.full_path("window-detail", docker_duration=4)
        self.assertEqual([6, 2], timeouts)
        self.assertEqual(6, elapsed)
        self.assertIsInstance(result, EnvironmentError)
        self.assertEqual([], Connection.instances)
        _, _, result = self.full_path(foreign=True)
        self.assertIn("FOREIGN_CONTAINER", str(result))
        self.assertEqual([], Connection.instances)

    def test_window_detail_stream_uses_whole_exchange_watchdog(self):
        event = "4cba2d80-c04a-4d24-9f03-f4a85d56da13"
        Connection.slow_paths = {"/api/v1/brake/units/test/windows/" + event}
        start = time.monotonic()
        with patch("aosedge_demo_orchestrator.backends.http.client.HTTPConnection", Connection), \
             patch("aosedge_demo_orchestrator.backends.BACKEND_WINDOW_BUDGET", .1, create=True):
            with self.assertRaises(EnvironmentError):
                BackendService.__new__(BackendService)._window_detail("test", event)
        self.assertLess(time.monotonic() - start, .75)
        self.assertTrue(all(c.closed for c in Connection.instances))

    def test_selective_slow_history_preserves_later_function_and_reset(self):
        Connection.slow_paths = {"/api/v1/brake/units/test/events?limit=10"}
        start = time.monotonic()
        with patch("aosedge_demo_orchestrator.backends.http.client.HTTPConnection", Connection):
            result = BackendService.__new__(BackendService)._product_observation("brake", "test")
        elapsed = time.monotonic() - start
        self.assertLess(elapsed, 5)
        self.assertEqual("PARTIAL", result["state"])
        self.assertEqual("UNAVAILABLE", result["observations"]["events"]["state"])
        for name in ("assessments", "functionObservations", "demoReset"):
            self.assertEqual("OBSERVED", result["observations"][name]["state"])
        self.assertTrue(all(c.closed for c in Connection.instances))

    def test_many_slow_resources_respect_aggregate_deadline_without_retries(self):
        Connection.slow_paths = {"/health/ready", "/health/context", "/api/v1/brake/demo-mock/summary", "/api/v1/brake/units/test/windows?limit=10"}
        start = time.monotonic()
        with patch("aosedge_demo_orchestrator.backends.http.client.HTTPConnection", Connection):
            result = BackendService.__new__(BackendService)._product_observation("brake", "test")
        elapsed = time.monotonic() - start
        self.assertLess(elapsed, 12)  # Browser deadline remains 15 seconds.
        self.assertEqual(4, len(Connection.instances))
        self.assertEqual("BACKEND_READ_BUDGET_EXHAUSTED", result["observations"]["demoReset"]["reason"])
        self.assertTrue(all(c.closed for c in Connection.instances))

    def test_expired_budget_makes_no_request_and_watchdog_is_cancelled_on_success(self):
        with patch("aosedge_demo_orchestrator.backends.http.client.HTTPConnection", Connection):
            with self.assertRaises(TimeoutError):
                with observation_connection(18091, time.monotonic() - 1):
                    self.fail("expired")
            self.assertEqual([], Connection.instances)
            with observation_connection(18091, time.monotonic() + .05) as (connection, active_socket):
                active_socket[0] = connection.sock
            self.assertFalse(connection.stopped.wait(.1))
            self.assertTrue(connection.closed)

    def test_watchdog_interrupts_real_stream_even_when_socket_timeout_keeps_resetting(self):
        stop = threading.Event()
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass
            def do_GET(self):
                self.send_response(200)
                self.send_header("Content-Length", "1000")
                self.end_headers()
                try:
                    for _ in range(1000):
                        if stop.wait(.01):
                            break
                        self.wfile.write(b"x")
                        self.wfile.flush()
                except OSError:
                    pass
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        original = http.client.HTTPConnection
        def fixture_connection(host, port, timeout):
            self.assertEqual((host, port), ("127.0.0.1", 18091))
            return original("127.0.0.1", server.server_port, timeout=timeout)
        try:
            start = time.monotonic()
            with patch("aosedge_demo_orchestrator.backends.http.client.HTTPConnection", fixture_connection):
                with observation_connection(18091, start + .15) as (connection, active_socket):
                    connection.request("GET", "/")
                    active_socket[0] = connection.sock
                    raw = connection.getresponse().read(262145)
            self.assertLess(time.monotonic() - start, .75)
            self.assertLess(len(raw), 1000)
        finally:
            stop.set()
            server.shutdown()
            server.server_close()
            worker.join(1)
