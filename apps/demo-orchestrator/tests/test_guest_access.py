# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import json
import re
import subprocess
import socket
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from aosedge_demo_orchestrator.environment import EnvironmentError
from aosedge_demo_orchestrator.guest_access import enroll_serial, read_guest
from aosedge_demo_orchestrator.vm import qmp


class CombinedStartTests(unittest.TestCase):
    def test_restore_failure_reports_only_fixed_non_secret_stage(self):
        for reported, expected in (("SOURCE_TRUST_CONSUMER_RESTART_UNCONFIRMED", "SOURCE_TRUST_CONSUMER_RESTART_UNCONFIRMED"),
                                   ("SOURCE_TRUST_unsafe /private/secret", "SOURCE_TRUST_RESTORE_UNCONFIRMED")):
            result = subprocess.CompletedProcess([], 1, stdout="DEMO_SOURCE_RESTORE_STARTED\n" +
                json.dumps(dict(ok=False, reason=reported)) + "\n", stderr="private output")
            with patch("aosedge_demo_orchestrator.guest_access.subprocess.run", return_value=result) as call:
                with self.assertRaisesRegex(EnvironmentError, "^" + expected + "$"):
                    read_guest(Path("/fixture"), 2222, factory_role="test", source_restore=dict(action="trust-restore", role="test"))
                call.assert_called_once()

    def test_reboot_restore_precedes_ready_and_uncertain_result_is_not_retried(self):
        request = dict(action="trust-restore", role="test")
        real_run = subprocess.run
        def source(path, *args, **kwargs):
            if path.name == "source_trust_guest.py":
                return "def execute(request):\n    print('RESTORED_EXISTING_IDENTITY')\n"
            return "def main(request):\n    print('{\"ok\":true,\"data\":{\"state\":\"INITIALIZED\",\"role\":\"test\"}}')\n"
        def shell(command, **kwargs):
            script = kwargs["input"]
            self.assertLess(script.index("DEMO_SOURCE_RESTORE_READY"), script.index("DEMO_GUEST_READY"))
            kwargs["input"] = re.sub(r"if timeout 2 [^\n]+; then", "if true; then", script)
            return real_run(["/bin/sh"], **kwargs)
        with patch("aosedge_demo_orchestrator.guest_access.UNPROVISIONED", "false"), \
                patch.object(Path, "read_text", source), \
                patch("aosedge_demo_orchestrator.guest_access.subprocess.run", side_effect=shell):
            self.assertTrue(read_guest(Path("/fixture"), 2222, factory_role="test", source_restore=request)["guestReady"])
        with patch("aosedge_demo_orchestrator.guest_access.subprocess.run", side_effect=subprocess.TimeoutExpired(
                "ssh", 60, output=b"DEMO_SOURCE_RESTORE_STARTED\n")) as call:
            with self.assertRaisesRegex(EnvironmentError, "SOURCE_TRUST_RESTORE_UNCONFIRMED"):
                read_guest(Path("/fixture"), 2222, factory_role="test", source_restore=request)
            call.assert_called_once()

    def test_debug_bootstrap_precedes_readiness_dns_and_role_in_one_ssh(self):
        real_run = subprocess.run
        domain = "developer.aos-dev.test"
        request = dict(domain=domain, hosts=[], vmStart=True)
        cloud_worker = "def main(request):\n    print('HOSTS_APPLIED')\n    return True\n"
        role_worker = "def main(request):\n    import json\n    print(json.dumps(dict(ok=True, data=dict(state='INITIALIZED', role=request['role']))))\n"
        def source(path, *args, **kwargs):
            return cloud_worker if path.name == "cloud_guest.py" else role_worker
        def shell(command, **kwargs):
            script = kwargs["input"]
            self.assertLess(script.index("DEMOCTL_CLOUD_PY"), script.index("DEMO_GUEST_READY"))
            self.assertLess(script.index("DEMO_CLOUD_CONFIGURATION_READY"), script.index("if timeout"))
            self.assertLess(script.index("if timeout"), script.index("DEMOCTL_ROLE_PY"))
            kwargs["input"] = re.sub(r"if timeout 2 [^\n]+; then", "if true; then", script)
            return real_run(["/bin/sh"], **kwargs)
        with patch("aosedge_demo_orchestrator.guest_access.UNPROVISIONED", "false"), \
                patch.object(Path, "read_text", source), \
                patch("aosedge_demo_orchestrator.guest_access.subprocess.run", side_effect=shell) as run:
            result = read_guest(Path("/fixture"), 2222, factory_role="test", cloud_host=domain, cloud_configuration=request)
        run.assert_called_once()
        self.assertTrue(result["guestReady"] and result["guestDnsReady"])
        self.assertEqual("INITIALIZED", result["factoryRole"]["state"])

    def test_failed_debug_bootstrap_prevents_all_following_guest_actions(self):
        real_run = subprocess.run
        domain = "developer.aos-dev.test"
        worker = "def main(request):\n    print('{\"ok\":false,\"reason\":\"CLOUD_GUEST_RUNTIME_UNSAFE\"}')\n    return False\n"
        def shell(command, **kwargs):
            result = real_run(["/bin/sh"], **kwargs)
            self.assertNotIn("DEMO_GUEST_READY", result.stdout)
            self.assertNotIn("DEMO_DNS_READY", result.stdout)
            return result
        with patch.object(Path, "read_text", return_value=worker), \
                patch("aosedge_demo_orchestrator.guest_access.subprocess.run", side_effect=shell):
            with self.assertRaisesRegex(EnvironmentError, "CLOUD_GUEST_RUNTIME_UNSAFE"):
                read_guest(Path("/fixture"), 2222, factory_role="test", cloud_host=domain,
                           cloud_configuration=dict(domain=domain))

    def test_uncertain_debug_bootstrap_is_not_retried_as_guest_boot_wait(self):
        domain = "developer.aos-dev.test"
        for response in (subprocess.TimeoutExpired("ssh", 5, output=b'DEMO_CLOUD_CONFIGURATION_STARTED\n'),
                         subprocess.CompletedProcess([], 255, 'DEMO_CLOUD_CONFIGURATION_STARTED\n', '')):
            with self.subTest(response=response), patch("aosedge_demo_orchestrator.guest_access.subprocess.run") as run:
                if isinstance(response, Exception):
                    run.side_effect = response
                else:
                    run.return_value = response
                with self.assertRaisesRegex(EnvironmentError, "CLOUD_GUEST_CONFIGURATION_UNCONFIRMED"):
                    read_guest(Path("/fixture"), 2222, factory_role="test", cloud_host=domain,
                               cloud_configuration=dict(domain=domain))

    def test_combined_shell_runs_role_only_when_dns_succeeds(self):
        real_run = subprocess.run
        worker = "def main(request):\n    import json\n    print(json.dumps(dict(ok=True, data=dict(state='INITIALIZED', role=request['role']))))\n"
        for dns in (True, False):
            def shell(command, **kwargs):
                kwargs["input"] = kwargs["input"].replace("timeout 2 busybox nslookup aoscloud.io", "true" if dns else "false")
                return real_run(["/bin/sh"], **kwargs)
            with self.subTest(dns=dns), patch("aosedge_demo_orchestrator.guest_access.UNPROVISIONED", "false"), patch.object(
                    Path, "read_text", return_value=worker), patch("aosedge_demo_orchestrator.guest_access.subprocess.run", side_effect=shell):
                result = read_guest(Path("/fixture"), 2222, factory_role="test")
                self.assertEqual(dns, result["guestDnsReady"])
                self.assertEqual(dns, "factoryRole" in result)

    def test_one_ssh_read_preserves_pinning_and_role_reconciliation(self):
        for role, state in (("test", "STAGED_BEFORE_SM"), ("test", "INITIALIZED"), ("production", "INITIALIZED")):
            with self.subTest(role=role, state=state), patch(
                    "aosedge_demo_orchestrator.guest_access.subprocess.run") as run:
                run.return_value = subprocess.CompletedProcess([], 0,
                    'DEMO_GUEST_READY\nDEMO_DNS_READY\n' + json.dumps(dict(ok=True, data=dict(state=state, role=role))), '')
                result = read_guest(Path("/fixture"), 2222, factory_role=role)
                run.assert_called_once()
                self.assertEqual(state, result["factoryRole"]["state"])
                self.assertIn("StrictHostKeyChecking=yes", run.call_args.args[0])
                self.assertIn("ControlMaster=no", run.call_args.args[0])
                script = run.call_args.kwargs["input"]
                self.assertLess(script.index("if timeout 2 busybox"), script.index("python3 - <<"))
                self.assertIn(repr(dict(action="factory-role", role=role)), script)

    def test_role_errors_or_incomplete_response_never_become_ready(self):
        for value, expected in ((dict(ok=False, reason="SOURCE_FACTORY_ROLE_CONFLICT"), "ROLE_CONFLICT"),
                (dict(ok=True, data=dict(state="INITIALIZED", role="production")), "RESPONSE_INVALID"),
                (dict(ok=True, data={}), "RESPONSE_INVALID"),
                (dict(ok=False, reason="private material /fixture"), "RESPONSE_INVALID")):
            with self.subTest(value=value), patch("aosedge_demo_orchestrator.guest_access.subprocess.run") as run:
                run.return_value = subprocess.CompletedProcess([], 0,
                    'DEMO_GUEST_READY\nDEMO_DNS_READY\n' + json.dumps(value), '')
                with self.assertRaisesRegex(EnvironmentError, expected):
                    read_guest(Path("/fixture"), 2222, factory_role="test")

    def test_dns_failure_does_not_require_role_response_or_claim_ready(self):
        with patch("aosedge_demo_orchestrator.guest_access.subprocess.run") as run:
            run.return_value = subprocess.CompletedProcess([], 0, 'DEMO_GUEST_READY\n', '')
            result = read_guest(Path("/fixture"), 2222, factory_role="test")
            self.assertTrue(result["guestReady"])
            self.assertFalse(result["guestDnsReady"])
            self.assertNotIn("factoryRole", result)

    def test_unknown_role_completion_is_not_a_boot_retry(self):
        with patch("aosedge_demo_orchestrator.guest_access.subprocess.run") as run:
            for error in (subprocess.CompletedProcess([], 1, 'DEMO_GUEST_READY\nDEMO_DNS_READY\n', ''),
                    subprocess.TimeoutExpired("ssh", 5, output=b'DEMO_GUEST_READY\nDEMO_DNS_READY\n')):
                run.side_effect = error if isinstance(error, Exception) else None
                run.return_value = error
                with self.assertRaisesRegex(EnvironmentError, "ROLE_UNCONFIRMED"):
                    read_guest(Path("/fixture"), 2222, factory_role="test")
            run.side_effect = subprocess.TimeoutExpired("ssh", 5)
            self.assertFalse(read_guest(Path("/fixture"), 2222, factory_role="test")["guestReady"])


class LocalProtocolTests(unittest.TestCase):
    """Local protocol fixtures only: no real VM, account or guest credentials."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir="/private/tmp")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.access = self.root / "access"
        self.access.mkdir(mode=0o700)

    def server(self, exchange):
        endpoint = self.root / "console.sock"
        server = socket.socket(socket.AF_UNIX)
        server.bind(str(endpoint))
        server.listen(1)
        server.settimeout(3)
        errors = []

        def run():
            try:
                with server, server.accept()[0] as connection:
                    connection.settimeout(3)
                    exchange(connection)
            except Exception as error:
                errors.append(error)

        worker = threading.Thread(target=run, daemon=True)
        worker.start()

        def finish():
            worker.join(4)
            self.assertFalse(worker.is_alive(), "fixture server did not finish")
            self.assertEqual([], errors)

        self.addCleanup(finish)
        return endpoint

    def test_qmp_handshake_ignores_events_and_requests_only_powerdown(self):
        commands = []

        def exchange(connection):
            connection.sendall(b'{"QMP":{"version":{}}}\n')
            with connection.makefile("rb") as reader:
                for _ in range(2):
                    command = json.loads(reader.readline())
                    commands.append(command["execute"])
                    connection.sendall(b'{"event":"RESUME"}\n')
                    connection.sendall((json.dumps({"return": {}, "id": command["id"]}) + "\n").encode())

        self.assertEqual({}, qmp(self.server(exchange), "system_powerdown"))
        self.assertEqual(["qmp_capabilities", "system_powerdown"], commands)
        with self.assertRaisesRegex(EnvironmentError, "QMP_COMMAND_NOT_ALLOWED"):
            qmp(self.root / "nonexistent", "system_reset")

    def test_explicit_fixture_password_enrolls_and_pins_console_host_key(self):
        password = "explicit-test-fixture-password"
        public_host = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIFixtureOnly"

        def exchange(connection):
            self.assertEqual(b"\r", connection.recv(8192))
            connection.sendall(b"fixture login: ")
            self.assertEqual(b"root\r", connection.recv(8192))
            connection.sendall(b"Password: ")
            self.assertEqual(password.encode() + b"\r", connection.recv(8192))
            connection.sendall(b"\r\nroot@fixture:~# ")
            command = connection.recv(16384).decode()
            self.assertIn("authorized_keys", command)
            self.assertIn("SSHD_OPTS", command)
            self.assertIn("sshd -T -f", command)
            self.assertNotIn("cat /etc/ssh/ssh_host_ed25519_key.pub", command)
            self.assertNotIn(password, command)
            connection.sendall(("\r\nDEMO_HOSTKEY_BEGIN\r\n" + public_host +
                                " fixture\r\n\r\nDEMO_HOSTKEY_END\r\n").encode())

        enroll_serial(self.server(exchange), self.access, 10022, time.monotonic() + 5, password)
        self.assertEqual("[127.0.0.1]:10022 " + public_host + "\n", (self.access / "known_hosts").read_text())
        for path in self.access.iterdir():
            self.assertNotIn(password, path.read_text())
            self.assertEqual(0o600, path.stat().st_mode & 0o777)

    def test_bad_explicit_password_is_not_retried(self):
        def exchange(connection):
            connection.recv(8192)
            connection.sendall(b"Password: ")
            self.assertEqual(b"fixture-wrong\r", connection.recv(8192))
            connection.sendall(b"\r\nLogin incorrect\r\nfixture login: ")
            self.assertEqual(b"", connection.recv(8192))

        with self.assertRaisesRegex(EnvironmentError, "GUEST_CONSOLE_AUTHENTICATION_FAILED"):
            enroll_serial(self.server(exchange), self.access, 10022, time.monotonic() + 5, "fixture-wrong")
        self.assertFalse((self.access / "known_hosts").exists())


if __name__ == "__main__":
    unittest.main()
