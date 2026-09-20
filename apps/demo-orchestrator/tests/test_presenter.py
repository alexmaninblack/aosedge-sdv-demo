# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import http.client
import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from aosedge_demo_orchestrator import presenter
from aosedge_demo_orchestrator.cli import main


class PresenterTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        (self.root / "index.html").write_text("<main>Presenter</main>")
        (self.root / "assets").mkdir()
        (self.root / "assets/test.js").write_text("export {};")
        (self.root / "secret.txt").write_text("must-not-be-served")
        (self.root / "assets/link.js").symlink_to(self.root / "secret.txt")
        self.reader = Mock(return_value={"mode": "LOCAL_READ_ONLY"})
        self.server = presenter.make_server(self.root, ("127.0.0.1", 0), self.reader)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.directory.cleanup()

    def request(self, path, method="GET", headers=None):
        connection = http.client.HTTPConnection(*self.server.server_address, timeout=2)
        connection.request(method, path, headers=headers or {})
        response = connection.getresponse()
        result = response.status, response.read(), dict(response.getheaders())
        connection.close()
        return result

    def test_page_assets_and_read_only_snapshot(self):
        self.assertEqual(200, self.request("/")[0])
        self.assertEqual(200, self.request("/assets/test.js")[0])
        code, body, headers = self.request("/api/presenter/snapshot")
        self.assertEqual(200, code)
        self.assertIn(b"LOCAL_READ_ONLY", body)
        self.assertEqual("no-store", headers["Cache-Control"])
        self.assertIn("frame-ancestors 'none'", headers["Content-Security-Policy"])
        self.reader.assert_called_once_with()

    def test_sequential_manual_cloud_refresh_is_not_a_one_second_cache_hit(self):
        read = Mock(side_effect=[dict(state="CURRENT", version=1), dict(state="CURRENT", version=2)])
        server = presenter.make_server(self.root, ("127.0.0.1", 0), self.reader, platform_reader=read)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            versions = []
            for _ in range(2):
                connection = http.client.HTTPConnection(*server.server_address, timeout=2)
                connection.request("GET", "/api/presenter/platform")
                response = connection.getresponse()
                self.assertEqual(200, response.status)
                versions.append(json.loads(response.read())["version"])
                connection.close()
            self.assertEqual([1, 2], versions)
            self.assertEqual(2, read.call_count)
        finally:
            server.shutdown(); server.server_close(); thread.join()

    def test_build_identity_changes_without_cloud_reads_and_reload_requires_idle(self):
        native = Mock()
        native.call.return_value = (200, dict(sessionId="one", active=None, uncertain=False))
        first = presenter.client_state(self.root, native)
        self.assertTrue(first["canReload"])
        self.assertEqual(64, len(first["buildId"]))
        (self.root / "index.html").write_text("<main>New client</main>")
        self.assertNotEqual(first["buildId"], presenter.client_state(self.root, native)["buildId"])
        for values in (dict(active="job"), dict(uncertain=True)):
            native.call.return_value = (200, dict(sessionId="one", **values))
            self.assertFalse(presenter.client_state(self.root, native)["canReload"])
        self.assertFalse(presenter.client_state(self.root, None)["canReload"])
        code, body, _ = self.request("/api/presenter/client-state")
        self.assertEqual(200, code)
        self.assertEqual({"buildId", "sessionId", "canReload"}, set(json.loads(body)))
        self.reader.assert_not_called()

    def test_no_mutation_arbitrary_paths_or_cross_origin_access(self):
        for method in ("POST", "PUT", "PATCH", "DELETE"):
            self.assertEqual(405, self.request("/api/presenter/snapshot", method)[0])
        for path in ("/api/operations", "/api/presenter/snapshot?cloud=true", "/secret.txt", "/assets/../secret.txt", "/assets/%2e%2e/secret.txt", "/assets/link.js", "/.git/config"):
            self.assertEqual(404, self.request(path)[0], path)
        self.assertEqual(403, self.request("/api/presenter/snapshot", headers={"Host": "evil.example"})[0])
        self.assertEqual(403, self.request("/api/presenter/snapshot", headers={"Origin": "https://evil.example"})[0])
        self.reader.assert_not_called()

    def test_backend_read_is_fixed_team_only_and_uses_democtl_core(self):
        value = dict(state="OBSERVED", team="brake", source="REAL_BACKEND_HTTP", cloudAuthority=False,
            vehicleTelemetry=False, observedAt="now", observations={}, privatePath="not-public")
        with patch.object(presenter, "execute_operation", return_value=dict(data=value)) as execute:
            code, body, _ = self.request("/api/presenter/backend/brake")
        self.assertEqual(200, code)
        execute.assert_called_once()
        self.assertEqual(dict(domain="backend",action="inspect",team="brake"),execute.call_args.args[0])
        self.assertNotIn(b"privatePath",body)
        for path in ("/api/presenter/backend/production", "/api/presenter/backend/brake?target=production", "/api/presenter/backend/other"):
            self.assertEqual(404,self.request(path)[0])

    def test_backend_failure_is_not_a_fake_empty_store(self):
        with patch.object(presenter, "execute_operation", side_effect=RuntimeError("PRIVATE_FIXTURE")):
            code, body, _ = self.request("/api/presenter/backend/tire")
        self.assertEqual(503,code)
        self.assertNotIn(b"PRIVATE_FIXTURE",body)

    def test_unavailable_read_is_sanitized_and_not_a_fake_success(self):
        self.reader.side_effect = RuntimeError("secret-material")
        code, body, _ = self.request("/api/presenter/snapshot")
        self.assertEqual(503, code)

    def test_brake_window_detail_is_fixed_current_test_uuid_read(self):
        event_id = "4cba2d80-c04a-4d24-9f03-f4a85d56da13"
        with patch.object(presenter, "execute_operation", return_value=dict(state="OBSERVED", data=dict(resourceType="WINDOW_DETAIL"))) as call:
            code, body, _ = self.request("/api/presenter/backend/brake/windows/" + event_id)
            self.assertEqual(200, code)
            self.assertIn(b"WINDOW_DETAIL", body)
            self.assertEqual(dict(domain="backend", action="window-detail", team="brake", window_id=event_id), call.call_args.args[0])
            call.reset_mock()
            for path in ("/api/presenter/backend/tire/windows/" + event_id,
                    "/api/presenter/backend/brake/windows/" + event_id + "?target=production",
                    "/api/presenter/backend/brake/windows/not-an-id"):
                self.assertEqual(404, self.request(path)[0])
            call.assert_not_called()
        self.assertNotIn(b"secret-material", body)

    def test_projection_uses_only_fixed_existing_democtl_read_operations(self):
        snapshot = dict(readCompletedAt="now", vehicles={"test": dict(local=dict(state="CURRENT", reason=None,
            value=dict(processState="NOT_CREATED", overlayExists=False, secret="private")))},
            source=dict(state="NOT_PREPARED", currentVehicle=None, secret="private"),
            journal=dict(value=dict(registrationStarted=True, registrationComplete=False)),
            cloud={"oem-delivery": dict(credential=dict(value=dict(present=True, secret="private")))})
        image = dict(selector="31/arm64", version="31", architecture="arm64", state="METADATA_AVAILABLE", problems=[], path="private")
        with patch.object(presenter, "execute_operation", side_effect=[dict(state="OBSERVED", status=snapshot), dict(data=dict(images=[image])), dict(state="OBSERVED", data=dict(releases=[]))]) as execute:
            result = presenter.read_snapshot()
        self.assertEqual([dict(domain="orchestrator", action="status", target="all"), dict(domain="image", action="list"), dict(domain="service", action="releases")],
                         [call.args[0] for call in execute.call_args_list])
        self.assertEqual("NOT_CREATED", result["vehicles"]["test"]["process"])
        self.assertTrue(result["registrationStarted"])
        self.assertFalse(result["registrationComplete"])
        self.assertNotIn("private", str(result))

    def test_cli_owns_the_preview_server(self):
        with patch.object(presenter, "serve", return_value=0) as serve:
            self.assertEqual(0, main(["ui", "serve"]))
        serve.assert_called_once_with()

    def test_platform_read_uses_cli_core_and_does_not_leak_private_fields(self):
        value = dict(test=dict(online_status="Online", status="provisioned",
                id="private-unit", components=[dict(installed_component=dict(version="15.0.0", id="private"),
                pending_component=None, pending_component_status="installed")]), latestPublishedVersion="15.0.0")
        with patch.object(presenter, "execute_operation", return_value=dict(state="OBSERVED", data=value)) as execute:
            result = presenter.read_platform()
        execute.assert_called_once_with(dict(domain="component", action="cloud-status"))
        self.assertEqual("15.0.0", result["value"]["installedVersion"])
        self.assertEqual("NOT_REPORTED_BY_CLOUD", result["value"]["runtimeState"])
        self.assertEqual("NOT_REPORTED_BY_CLOUD", result["value"]["dataReadiness"])
        self.assertNotIn("private", str(result))
        self.assertNotIn("secret", str(result))

    def test_platform_failure_has_no_success_or_raw_diagnostics(self):
        with patch.object(presenter, "execute_operation", return_value=dict(state="BLOCKED", message="secret")):
            result = presenter.read_platform()
        self.assertEqual("UNAVAILABLE", result["state"])
        self.assertIsNone(result["value"])
        self.assertNotIn("secret", str(result))
