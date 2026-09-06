# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import contextlib
import io
import json
import socket
import subprocess
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
from urllib.error import HTTPError

from aosedge_demo_orchestrator.api import execute_operation
from aosedge_demo_orchestrator.application import DemoOrchestrator
from aosedge_demo_orchestrator.cli import main, render_human
from aosedge_demo_orchestrator.cloud import get_json, local_profile, project_unit, project_user, NoRedirect
from aosedge_demo_orchestrator.models import OperationRequest, VehicleTarget
from aosedge_demo_orchestrator.probes import guest_status, local_vehicle, owns_overlay, parse_guest, process_snapshot, qmp_status
from aosedge_demo_orchestrator.status import StatusService, has_unknown, load_configuration, observation

UID = "00000000-0000-4000-8000-000000000001"
OWNER = "00000000-0000-4000-8000-000000000002"


class StatusTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.config_path = self.root / "status.json"
        self.config = {"schemaVersion": 1, "vehicles": {"test": {"overlay": "test.qcow2"}, "production": None},
                       "cloudProfiles": {}}
        self.write_config()

    def write_config(self):
        self.config_path.write_text(json.dumps(self.config))

    def service(self):
        return StatusService(self.root, self.config_path)

    def collect(self, **kwargs):
        with patch("aosedge_demo_orchestrator.probes.process_snapshot", return_value=[]):
            return self.service().collect(**kwargs)

    def test_stopped_is_an_observation_not_ready_or_unknown(self):
        (self.root / "test.qcow2").touch()
        result = self.collect(guest=True)
        vehicle = result["vehicles"]["test"]
        self.assertEqual("STOPPED", vehicle["local"]["value"]["processState"])
        self.assertEqual("VM_NOT_RUNNING", vehicle["guest"]["reason"])
        self.assertFalse(has_unknown(result))

    def test_absent_local_disk_is_not_a_cloud_absence_claim(self):
        result = self.collect()
        self.assertEqual("NOT_CREATED", result["vehicles"]["test"]["local"]["value"]["processState"])
        self.assertEqual({}, result["cloud"])

    def test_selectors_do_not_probe_other_role(self):
        result = self.collect(target="production")
        self.assertEqual(["production"], list(result["vehicles"]))
        self.assertEqual("TARGET_NOT_CONFIGURED", result["vehicles"]["production"]["local"]["reason"])

    def test_config_invalid_preserves_state(self):
        self.config_path.write_text("{ broken")
        before = self.config_path.read_bytes()
        result = self.collect()
        self.assertEqual("CONFIG_INVALID", result["configuration"]["reason"])
        self.assertEqual(before, self.config_path.read_bytes())

    def test_explicit_missing_config_does_not_fall_back(self):
        service = StatusService(self.root, self.root / "missing.json")
        self.assertEqual("CONFIG_INVALID", service.collect()["configuration"]["reason"])

    def test_unknown_fields_and_shell_services_rejected(self):
        for change in ({"services": ["aos-sm; reboot.service"]}, {"cloudHost": "bad;host"},
                       {"sshPort": True}, {"unitId": "../units/"}, {"overlay": 4}):
            with self.subTest(change=change):
                self.config["vehicles"]["test"] = dict({"overlay": "test.qcow2"}, **change)
                self.write_config()
                self.assertEqual("CONFIG_INVALID", self.collect()["configuration"]["reason"])

    def test_configuration_is_not_written_and_no_state_created(self):
        before = sorted(str(p.relative_to(self.root)) for p in self.root.rglob("*"))
        original = self.config_path.read_bytes()
        self.collect()
        self.collect()
        self.assertEqual(before, sorted(str(p.relative_to(self.root)) for p in self.root.rglob("*")))
        self.assertEqual(original, self.config_path.read_bytes())

    def test_timeout_validation(self):
        for timeout in (0, -1, float("nan"), float("inf"), True, 31):
            with self.subTest(timeout=timeout), self.assertRaises(ValueError):
                self.collect(timeout=timeout)

    def test_profile_requires_cloud(self):
        with self.assertRaises(ValueError):
            self.collect(profile="oem-delivery")

    def test_cli_json_and_api_share_core(self):
        service = self.service()
        with patch("aosedge_demo_orchestrator.probes.process_snapshot", return_value=[]), \
             patch("aosedge_demo_orchestrator.source.SourceService.observe", return_value={"state": "NOT_PREPARED"}):
            api = execute_operation({"domain": "orchestrator", "action": "status", "target": "test"},
                                    DemoOrchestrator(service))
            output = io.StringIO()
            with patch("aosedge_demo_orchestrator.cli.StatusService", return_value=service), contextlib.redirect_stdout(output):
                code = main(["--output", "json", "status", "test"])
        cli = json.loads(output.getvalue())
        self.assertEqual(0, code)
        self.assertEqual("OBSERVED", cli["state"])
        self.assertEqual(api["status"]["vehicles"]["test"]["local"]["value"],
                         cli["status"]["vehicles"]["test"]["local"]["value"])
        self.assertIn("not demo readiness", cli["message"])

    def test_api_rejects_path_profile_and_string_flags(self):
        for extra in ({"config": "/tmp/injected"}, {"profile": "oem-delivery"},
                      {"cloud": "false"}, {"timeout": 1000}, {"shell": "reboot"}):
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                execute_operation(dict({"domain": "orchestrator", "action": "status"}, **extra),
                                  DemoOrchestrator(self.service()))

    def test_read_failure_is_partial_and_never_calls_guest(self):
        config = load_configuration(self.root, self.config_path)["vehicles"]["test"]
        value = local_vehicle(config, None, 0.2)
        with patch("aosedge_demo_orchestrator.probes.subprocess.run") as run:
            guest = guest_status(config, value, 0.2)
        run.assert_not_called()
        self.assertEqual("PROCESS_READ_FAILED", value["reason"])
        self.assertEqual("VM_IDENTITY_UNRESOLVED", guest["reason"])

    def test_cloud_failure_does_not_erase_local_results(self):
        self.config["cloudProfiles"] = {"oem-delivery": {"credential": "missing.p12", "expectedRole": "oem"}}
        self.write_config()
        result = self.collect(cloud=True)
        self.assertEqual("NOT_CREATED", result["vehicles"]["test"]["local"]["value"]["processState"])
        self.assertEqual("CREDENTIAL_MISSING_OR_UNSAFE", result["cloud"]["oem-delivery"]["access"]["reason"])
        self.assertTrue(has_unknown(result))

    def test_parallel_cloud_profiles_keep_separate_roles(self):
        self.config["cloudProfiles"] = {
            "oem-delivery": {"credential": "oem.p12", "expectedRole": "oem"},
            "service-provider": {"credential": "sp.p12", "expectedRole": "service provider"},
        }
        self.write_config()
        barrier = threading.Barrier(2)

        def fake(name, profile, vehicles, interpreter, timeout):
            barrier.wait(timeout=2)
            return {"access": observation("AOSCLOUD:" + name, {"role": profile["expectedRole"]})}
        with patch("aosedge_demo_orchestrator.cloud.cloud_status", side_effect=fake):
            result = self.collect(cloud=True)
        self.assertEqual("oem", result["cloud"]["oem-delivery"]["access"]["value"]["role"])
        self.assertEqual("service provider", result["cloud"]["service-provider"]["access"]["value"]["role"])

    def test_old_timestamps_are_not_synthesized_from_local_identity(self):
        result = self.collect()
        value = result["vehicles"]["test"]["local"]
        self.assertIsNone(value["sourceTimestamp"])
        self.assertTrue(value["readCompletedAt"].endswith("Z"))
        self.assertEqual("NOT_APPLICABLE", result["journal"]["state"])


class ProbeTests(unittest.TestCase):
    def test_no_qemu_is_a_valid_empty_inventory(self):
        with patch("aosedge_demo_orchestrator.probes.subprocess.run", return_value=Mock(returncode=0, stdout="1 /sbin/launchd")):
            self.assertEqual([], process_snapshot(0.2))

    def test_failed_ps_is_unknown_not_empty(self):
        with patch("aosedge_demo_orchestrator.probes.subprocess.run", side_effect=PermissionError()):
            self.assertIsNone(process_snapshot(0.2))

    def test_exact_overlay_not_substring(self):
        overlay = Path("/tmp/owned.qcow2")
        self.assertFalse(owns_overlay(["qemu-system-aarch64", "-drive", "file=/tmp/owned.qcow2.old"], overlay))
        self.assertTrue(owns_overlay(["qemu-system-aarch64", "-drive", "file=/tmp/owned.qcow2,format=qcow2"], overlay))
        self.assertTrue(owns_overlay(
            ["qemu-system-aarch64", "-drive", "file=/tmp/With", "Space/owned.qcow2,format=qcow2", "-m", "4096"],
            Path("/tmp/With Space/owned.qcow2")))

    def test_ambiguous_owner_does_not_query_qmp(self):
        with tempfile.TemporaryDirectory() as directory:
            overlay = Path(directory) / "disk.qcow2"
            overlay.touch()
            args = ["qemu-system-aarch64", "-drive", "file=" + str(overlay)]
            with patch("aosedge_demo_orchestrator.probes.qmp_status") as qmp:
                result = local_vehicle({"overlay": overlay}, [(10, args), (11, args)], 0.2)
        qmp.assert_not_called()
        self.assertEqual("AMBIGUOUS_QEMU_OWNER", result["reason"])

    def test_qmp_only_negotiates_and_queries_status(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "qmp"
            requests = []
            errors = []
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
                server.bind(str(path))
                server.listen(1)
                server.settimeout(2)

                def serve():
                    try:
                        connection, _ = server.accept()
                        with connection, connection.makefile("rb") as stream:
                            connection.sendall(b'{"QMP":{}}\r\n')
                            for index in range(2):
                                request = json.loads(stream.readline())
                                requests.append(request["execute"])
                                answer = {} if index == 0 else {"running": False, "status": "paused"}
                                connection.sendall(json.dumps({"id": request["id"], "return": answer}).encode() + b"\r\n")
                    except Exception as error:
                        errors.append(type(error).__name__)
                thread = threading.Thread(target=serve)
                thread.start()
                result = qmp_status(path, 1)
                thread.join(timeout=2)
            self.assertEqual([], errors)
            self.assertEqual(["qmp_capabilities", "query-status"], requests)
            self.assertEqual({"running": False, "status": "paused"}, result)

    def test_guest_properties_parse_independently_of_order(self):
        config = {"services": ["aos-sm.service"], "cloudHost": "aoscloud.io", "dnsPort": 18053}
        text = ("__DEMO_RELEASE__\n\"1.2.3\"\n__DEMO_SERVICES__\nActiveState=active\nSubState=running\n"
                "LoadState=loaded\nResult=success\nNRestarts=2\nId=aos-sm.service\n\n"
                "__DEMO_SYSTEMCTL_RC__=0\n__DEMO_DNS_CONFIG__\nhostDnsPort=18053\n"
                "__DEMO_DNS_RC__=0\n__DEMO_END__\n")
        result = parse_guest(text, config)
        self.assertEqual("CURRENT", result["state"])
        self.assertEqual(2, result["value"]["services"]["aos-sm.service"]["NRestarts"])
        self.assertTrue(result["value"]["dns"]["portMatches"])
        self.assertEqual("NOT_OBSERVED", result["value"]["aosCoreConnected"])

    def test_guest_security_counts_are_bounded_and_raw_values_not_returned(self):
        config = {"services": [], "cloudHost": "aoscloud.io"}
        text = ("__DEMO_RELEASE__\n1.2.3\n__DEMO_SYSTEMCTL_RC__=0\n"
                "__DEMO_SECURITY__\nselinux=Enforcing\nkernelReadExit=0\n"
                "kernelRecords=250\nkernelAvcDenials=0\nraw=SECRET_MUST_NOT_LEAK\n"
                "selinux=SECRET_MUST_NOT_LEAK\nkernelAvcDenials=-1\n__DEMO_END__\n")
        result = parse_guest(text, config)
        self.assertEqual({"source": "CURRENT_BOOT_KERNEL_JOURNAL", "selinux": "Enforcing",
                          "kernelReadExit": 0, "kernelRecords": 250, "kernelAvcDenials": 0}, result["value"]["security"])
        self.assertNotIn("SECRET", json.dumps(result))

    def test_guest_missing_security_evidence_is_not_reported_as_zero_denials(self):
        result = parse_guest("__DEMO_RELEASE__\n1.2.3\n__DEMO_SYSTEMCTL_RC__=0\n__DEMO_END__\n",
                             {"services": [], "cloudHost": "aoscloud.io"})
        self.assertEqual("NOT_OBSERVED", result["value"]["security"]["selinux"])
        self.assertNotIn("kernelAvcDenials", result["value"]["security"])

    def test_guest_timeout_and_stderr_are_redacted(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "aosvm-host-ed25519").write_text("fixture")
            (root / "aosvm-host-ed25519").chmod(0o600)
            (root / "known_hosts").write_text("fixture")
            config = {"sshPort": 10022, "accessRoot": root, "services": ["aos-sm.service"], "cloudHost": "aoscloud.io"}
            local = observation("HOST_QEMU", {"processState": "RUNNING"})
            response = Mock(returncode=255, stderr="Permission denied SECRET_MUST_NOT_LEAK", stdout="")
            with patch("aosedge_demo_orchestrator.probes.subprocess.run", return_value=response) as call:
                result = guest_status(config, local, 0.2)
            self.assertNotIn("SECRET", json.dumps(result))
            self.assertIn("StrictHostKeyChecking=yes", call.call_args.args[0])
            self.assertNotIn("shell", call.call_args.kwargs)
            self.assertEqual("SSH_AUTHENTICATION_FAILED", result["reason"])
            with patch("aosedge_demo_orchestrator.probes.subprocess.run", side_effect=subprocess.TimeoutExpired("ssh", 0.2)):
                result = guest_status(config, local, 0.2)
            self.assertEqual("SSH_TIMEOUT", result["reason"])


class CloudProjectionTests(unittest.TestCase):
    def test_user_projection_preserves_permissions_but_drops_secrets(self):
        payload = {"id": UID, "role": "oem", "oem": {"id": OWNER, "secret": "NEVER_LEAK"},
                   "effective_permissions": ["users_me", "units_read"], "token": "NEVER_LEAK",
                   "email": "private@example.test", "certificate": "NEVER_LEAK"}
        result = project_user(payload, "oem", OWNER)
        self.assertEqual(["users_me", "units_read"], result["effectivePermissions"])
        self.assertTrue(result["ownerMatches"])
        self.assertNotIn("NEVER_LEAK", json.dumps(result))
        self.assertNotIn("email", result)

    def test_sp_is_not_mistaken_for_oem(self):
        result = project_user({"id": UID, "role": "service provider", "service_provider": {"id": OWNER},
                               "effective_permissions": []}, "service provider")
        self.assertEqual(OWNER, result["ownerId"])
        self.assertTrue(result["roleMatches"])
        self.assertEqual("NOT_EVALUATED", result["mutationAuthority"])

    def test_missing_permissions_are_unknown_not_zero(self):
        self.assertIsNone(project_user({"id": UID, "role": "oem"}, "oem")["effectivePermissions"])

    def test_unit_observation_keeps_actual_state_and_ignores_unrelated_fields(self):
        payload = {"id": UID, "system_uid": "abc123", "status": "provisioned", "online_status": "Offline",
                   "unit_sets": [{"id": OWNER}], "token": "NEVER_LEAK"}
        result = project_unit(payload, {"unitId": UID, "unitSetId": OWNER})
        self.assertEqual("Offline", result["onlineStatus"])
        self.assertTrue(result["expectedMembershipPresent"])
        self.assertNotIn("NEVER_LEAK", json.dumps(result))

    def test_wrong_unit_never_becomes_a_successful_observation(self):
        with self.assertRaises(ValueError):
            project_unit({"id": OWNER}, {"unitId": UID})

    def test_http_codes_preserve_unknown_visibility_and_drop_body(self):
        for code, expected in ((401, "UNAUTHENTICATED"), (403, "FORBIDDEN"),
                               (404, "NOT_FOUND_OR_INACCESSIBLE"), (422, "SCHEMA_INVALID")):
            opener = Mock()
            opener.open.side_effect = HTTPError("https://example.test", code, "NEVER_LEAK", {}, None)
            payload, failure = get_json(opener, "https://example.test", time.monotonic() + 1, "CLOUD")
            self.assertIsNone(payload)
            self.assertEqual(expected, failure["transport"])
            self.assertNotIn("NEVER_LEAK", json.dumps(failure))
            self.assertEqual(1, opener.open.call_count)

    def test_no_redirect_of_client_credentials(self):
        self.assertIsNone(NoRedirect().redirect_request(None, None, 302, "", {}, "https://other.example"))

    def test_malformed_json_is_not_empty_success(self):
        response = Mock()
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=None)
        response.read.return_value = b"not json SECRET"
        opener = Mock()
        opener.open.return_value = response
        _, failure = get_json(opener, "https://example.test", time.monotonic() + 1, "CLOUD")
        self.assertEqual("RESPONSE_MALFORMED", failure["reason"])
        self.assertNotIn("SECRET", json.dumps(failure))


if __name__ == "__main__":
    unittest.main()
