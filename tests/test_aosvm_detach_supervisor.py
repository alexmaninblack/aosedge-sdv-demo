# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

from __future__ import annotations

import os
from pathlib import Path
import pty
import signal
import stat
import subprocess
import tempfile
import time
import unittest
from unittest import mock
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader


ROOT = Path(__file__).resolve().parents[1]
DETACHER = ROOT / "scripts" / "host" / "aosvm-detach-supervisor"


class AosVMDetachSupervisorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(
            prefix="aosvm-detacher-", dir="/private/tmp"
        )
        self.root = Path(self.temporary.name)
        self.log = self.root / "supervisor.log"
        self.log.touch(mode=0o600)
        (self.root / "scripts").mkdir()
        self.worker = self.root / "scripts" / "aosvm"
        self.worker.write_text(
            "#!/bin/sh\n"
            "[ \"$1\" = _supervise ] && { [ \"$2\" = normal ] || "
            "[ \"$2\" = provisioning ]; } || exit 64\n"
            "/bin/sh -c 'printf \"%s:%s\\n\" \"$$\" \"$PPID\" > child.meta; "
            "trap \"exit 0\" TERM INT; while :; do sleep 1; done' & child=$!\n"
            "trap 'kill \"$child\" 2>/dev/null || true; wait \"$child\" "
            "2>/dev/null || true; exit 0' TERM INT\n"
            "wait \"$child\"\n",
            encoding="utf-8",
        )
        self.worker.chmod(0o755)
        self.pids: list[int] = []

    def tearDown(self) -> None:
        for pid in self.pids:
            try:
                os.killpg(pid, signal.SIGTERM)
            except ProcessLookupError:
                continue
            deadline = time.monotonic() + 3
            while time.monotonic() < deadline:
                try:
                    os.kill(pid, 0)
                except ProcessLookupError:
                    break
                time.sleep(0.05)
        self.temporary.cleanup()

    def _command(self) -> list[str]:
        return [
            str(DETACHER),
            "--log",
            str(self.log),
            "--cwd",
            str(self.root),
            "--",
            str(self.worker),
            "_supervise",
            "normal",
        ]

    def _child_meta(self) -> tuple[int, int]:
        path = self.root / "child.meta"
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            if path.is_file():
                child, parent = path.read_text(encoding="utf-8").strip().split(":")
                return int(child), int(parent)
            time.sleep(0.05)
        self.fail("fake QEMU child PID was not published")

    def _remember(self, pid_text: str) -> int:
        self.assertRegex(pid_text, r"^[1-9][0-9]*\n$")
        pid = int(pid_text)
        self.pids.append(pid)
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            try:
                if os.getsid(pid) == pid:
                    self.assertEqual(pid, os.getpgid(pid))
                    return pid
            except ProcessLookupError:
                pass
            time.sleep(0.05)
        self.fail("detached supervisor did not become a session leader")

    def test_non_pty_parent_exit_leaves_owned_session_alive(self) -> None:
        result = subprocess.run(
            self._command(), check=True, capture_output=True, text=True
        )
        self.assertEqual("", result.stderr)
        pid = self._remember(result.stdout)
        child, parent = self._child_meta()
        os.kill(pid, 0)
        self.assertEqual(pid, parent)
        os.kill(child, 0)
        self.assertEqual(0o600, stat.S_IMODE(self.log.stat().st_mode))

    def test_pty_teardown_does_not_hang_up_detached_session(self) -> None:
        master, slave = pty.openpty()
        try:
            parent = subprocess.Popen(
                self._command(), stdout=slave, stderr=slave, close_fds=True
            )
            os.close(slave)
            slave = -1
            output = os.read(master, 128).decode("utf-8")
            os.close(master)
            master = -1
            self.assertEqual(0, parent.wait(timeout=3))
        finally:
            if slave >= 0:
                os.close(slave)
            if master >= 0:
                os.close(master)
        pid = self._remember(output.replace("\r\n", "\n"))
        child, parent = self._child_meta()
        os.kill(pid, 0)
        os.kill(child, 0)
        self.assertEqual(pid, parent)

    def test_controlled_supervisor_stop_leaves_no_child_orphan(self) -> None:
        result = subprocess.run(
            self._command(), check=True, capture_output=True, text=True
        )
        pid = self._remember(result.stdout)
        child, parent = self._child_meta()
        self.assertEqual(pid, parent)
        os.kill(pid, signal.SIGTERM)
        deadline = time.monotonic() + 4
        while time.monotonic() < deadline:
            supervisor_alive = True
            child_alive = True
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                supervisor_alive = False
            try:
                os.kill(child, 0)
            except ProcessLookupError:
                child_alive = False
            if not supervisor_alive and not child_alive:
                break
            time.sleep(0.05)
        else:
            self.fail("controlled stop left the supervisor or fake QEMU alive")

    def test_symlink_hardlink_and_mode_changes_fail_closed(self) -> None:
        symlink = self.root / "worker-link"
        symlink.symlink_to(self.worker)
        command = self._command()
        command[-3] = str(symlink)
        result = subprocess.run(command, check=False, capture_output=True, text=True)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("regular non-symlink", result.stderr)

        hardlink = self.root / "worker-hardlink"
        os.link(self.worker, hardlink)
        result = subprocess.run(
            self._command(), check=False, capture_output=True, text=True
        )
        self.assertNotEqual(0, result.returncode)
        self.assertIn("exactly one hard link", result.stderr)
        hardlink.unlink()

        self.worker.chmod(0o700)
        result = subprocess.run(
            self._command(), check=False, capture_output=True, text=True
        )
        self.assertNotEqual(0, result.returncode)
        self.assertIn("mode must be 0755", result.stderr)

    def test_invalid_log_cwd_owner_and_argv_fail_closed(self) -> None:
        log_link = self.root / "log-link"
        log_link.symlink_to(self.log)
        command = self._command()
        command[2] = str(log_link)
        result = subprocess.run(command, check=False, capture_output=True, text=True)
        self.assertNotEqual(0, result.returncode)

        log_hardlink = self.root / "log-hardlink"
        os.link(self.log, log_hardlink)
        result = subprocess.run(
            self._command(), check=False, capture_output=True, text=True
        )
        self.assertNotEqual(0, result.returncode)
        log_hardlink.unlink()

        self.log.chmod(0o644)
        result = subprocess.run(
            self._command(), check=False, capture_output=True, text=True
        )
        self.assertNotEqual(0, result.returncode)
        self.log.chmod(0o600)

        cwd_link = self.root.parent / f"{self.root.name}-link"
        cwd_link.symlink_to(self.root)
        command = self._command()
        command[4] = str(cwd_link)
        result = subprocess.run(command, check=False, capture_output=True, text=True)
        cwd_link.unlink()
        self.assertNotEqual(0, result.returncode)

        linked_parent = self.root.parent / f"{self.root.name}-parent-link"
        linked_parent.symlink_to(self.root.parent)
        linked_cwd = linked_parent / self.root.name
        linked_worker = linked_cwd / "scripts" / "aosvm"
        command = self._command()
        command[4] = str(linked_cwd)
        command[-3] = str(linked_worker)
        result = subprocess.run(command, check=False, capture_output=True, text=True)
        linked_parent.unlink()
        self.assertNotEqual(0, result.returncode)
        self.assertIn("noncanonical components", result.stderr)

        command = self._command()
        command[-2] = "status"
        result = subprocess.run(command, check=False, capture_output=True, text=True)
        self.assertNotEqual(0, result.returncode)
        command = self._command()
        command[-1] = "invalid"
        result = subprocess.run(command, check=False, capture_output=True, text=True)
        self.assertNotEqual(0, result.returncode)

        loader = SourceFileLoader("aosvm_detacher_test", str(DETACHER))
        spec = spec_from_loader(loader.name, loader)
        self.assertIsNotNone(spec)
        module = module_from_spec(spec)
        loader.exec_module(module)
        with mock.patch.object(module.os, "getuid", return_value=os.getuid() + 1):
            with self.assertRaises(SystemExit):
                module.regular_owned_file(self.worker, 0o755, "supervisor")

    def test_helper_is_private_tracked_executable(self) -> None:
        self.assertFalse(DETACHER.is_symlink())
        self.assertEqual(0o755, stat.S_IMODE(DETACHER.stat().st_mode))

    def test_launcher_uses_detacher_and_polls_nonchild_cleanup(self) -> None:
        launcher = (ROOT / "scripts" / "aosvm").read_text(encoding="utf-8")
        start = launcher.index("start_background()")
        end = launcher.index("\nsupervise_vm()", start)
        background = launcher[start:end]
        self.assertIn('"$DETACH_SUPERVISOR_HELPER"', background)
        self.assertNotIn("nohup", background)
        cleanup_start = launcher.index("cleanup_background_start()")
        cleanup_end = launcher.index("\nread_pid_file()", cleanup_start)
        cleanup = launcher[cleanup_start:cleanup_end]
        self.assertIn("wait_for_process_exit", cleanup)
        self.assertNotIn('wait "$BACKGROUND_START_PID"', cleanup)


if __name__ == "__main__":
    unittest.main()
