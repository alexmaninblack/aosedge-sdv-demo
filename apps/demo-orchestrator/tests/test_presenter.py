# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import http.client
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

    def test_no_mutation_arbitrary_paths_or_cross_origin_access(self):
        for method in ("POST", "PUT", "PATCH", "DELETE"):
            self.assertEqual(405, self.request("/api/presenter/snapshot", method)[0])
        for path in ("/api/operations", "/api/presenter/snapshot?cloud=true", "/secret.txt", "/assets/../secret.txt", "/assets/%2e%2e/secret.txt", "/assets/link.js", "/.git/config"):
            self.assertEqual(404, self.request(path)[0], path)
        self.assertEqual(403, self.request("/api/presenter/snapshot", headers={"Host": "evil.example"})[0])
        self.assertEqual(403, self.request("/api/presenter/snapshot", headers={"Origin": "https://evil.example"})[0])
        self.reader.assert_not_called()

    def test_unavailable_read_is_sanitized_and_not_a_fake_success(self):
        self.reader.side_effect = RuntimeError("secret-material")
        code, body, _ = self.request("/api/presenter/snapshot")
        self.assertEqual(503, code)
        self.assertNotIn(b"secret-material", body)

    def test_projection_uses_only_fixed_existing_democtl_read_operations(self):
        snapshot = dict(readCompletedAt="now", vehicles={"test": dict(local=dict(state="CURRENT", reason=None,
            value=dict(processState="NOT_CREATED", overlayExists=False, secret="private")))},
            source=dict(state="NOT_PREPARED", currentVehicle=None, secret="private"),
            cloud={"oem-delivery": dict(credential=dict(value=dict(present=True, secret="private")))})
        image = dict(selector="31/arm64", version="31", architecture="arm64", state="METADATA_AVAILABLE", problems=[], path="private")
        with patch.object(presenter, "execute_operation", side_effect=[dict(state="OBSERVED", status=snapshot), dict(data=dict(images=[image]))]) as execute:
            result = presenter.read_snapshot()
        self.assertEqual([dict(domain="orchestrator", action="status", target="all"), dict(domain="image", action="list")],
                         [call.args[0] for call in execute.call_args_list])
        self.assertEqual("NOT_CREATED", result["vehicles"]["test"]["process"])
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
