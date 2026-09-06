# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import json
import socket
import tempfile
import threading
import time
import unittest
from pathlib import Path

from aosedge_demo_orchestrator.environment import EnvironmentError
from aosedge_demo_orchestrator.guest_access import enroll_serial
from aosedge_demo_orchestrator.vm import qmp


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
            qmp(self.root / "nonexistent", "quit")

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
