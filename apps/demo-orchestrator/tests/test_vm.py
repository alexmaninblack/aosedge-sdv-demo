# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import json
import os
import shutil
import subprocess
import unittest
from unittest.mock import patch

import test_images_environment as fixtures
from aosedge_demo_orchestrator.api import execute_operation
from aosedge_demo_orchestrator.application import DemoOrchestrator
from aosedge_demo_orchestrator.cli import build_parser, request_from_arguments
from aosedge_demo_orchestrator.environment import EnvironmentError, JOURNAL, atomic_json, digest
from aosedge_demo_orchestrator.guest_access import ACCESS_FILES, enroll_serial
from aosedge_demo_orchestrator.status import StatusService, load_configuration
from aosedge_demo_orchestrator.vm import PROFILE, VMService, access_path


class FakeRuntime(VMService):
    """Process/guest doubles; actual factory/overlay files and lifecycle journal."""
    def __init__(self, environment):
        super().__init__(environment)
        self.running = {}
        self.spawned = []
        self.killed = []
        self.counter = 900000
        self.guest_ready = True
        self.unprovisioned = True
        self.shutdown_works = True

    def _host_profile(self):
        pass

    def _free_port(self, port, udp=False):
        pass

    def _spawn(self, command):
        self.counter += 1
        self.running[self.counter] = command
        self.spawned.append(command)
        return self.counter

    def _processes(self):
        return [(pid, " ".join(args)) for pid, args in self.running.items()]

    def kill(self, pid, signal):
        self.killed.append(pid)
        if "--owner-id" not in self.running[pid]:
            raise AssertionError("VM force kill forbidden")
        del self.running[pid]

    def guest(self, access, port, timeout=5, shutdown=False):
        if shutdown and self.shutdown_works:
            role = "test" if port == 10022 else "production"
            for pid, args in list(self.running.items()):
                if any("democtl-" + role + "-" in arg for arg in args):
                    del self.running[pid]
        return {"guestReady": self.guest_ready, "guestDnsReady": self.guest_ready,
                "unprovisioned": self.unprovisioned}


class VMTests(unittest.TestCase):
    def setUp(self):
        support = fixtures.ImagesAndCreateTests()
        with patch("tempfile.tempdir", "/private/tmp"):
            support.setUp()
        self.addCleanup(support.doCleanups)
        self.support = support
        self.environment = support.service
        self.root = support.root
        state = support.create()
        self.runtime = FakeRuntime(self.environment)
        for role, item in state["vehicles"].items():
            access = access_path(self.root, role)
            access.mkdir(mode=0o700)
            for name in ACCESS_FILES:
                path = access / name
                path.write_text("fixture-material-not-a-real-key")
                path.chmod(0o600)
            item["runtime"] = {"profile": PROFILE, "state": "STOPPED", "everStarted": False,
                               "accessCreated": True, "stopProof": None}
        atomic_json(self.root / JOURNAL, state)
        for name, replacement in (("qmp", lambda *args: {"status": "running"}),
                                  ("read_guest", self.runtime.guest), ("os.kill", self.runtime.kill)):
            handle = patch("aosedge_demo_orchestrator.vm." + name, replacement)
            handle.start()
            self.addCleanup(handle.stop)

    def state(self):
        return json.loads((self.root / JOURNAL).read_text())

    def test_start_both_repeat_stop_one_and_last_dns_owner(self):
        result = self.runtime.execute("start", "all", 1)
        self.assertTrue(all(item["state"] == "COMPLETED" for item in result["vehicles"].values()))
        self.assertEqual(3, len(self.runtime.spawned))
        self.runtime.execute("start", "all", 1)
        self.assertEqual(3, len(self.runtime.spawned))
        self.runtime.execute("stop", "test", 1)
        self.assertEqual(2, len(self.runtime.running))
        self.assertEqual([], self.runtime.killed)
        self.runtime.execute("stop", "production", 1)
        self.assertEqual({}, self.runtime.running)
        self.assertEqual(1, len(self.runtime.killed))
        self.assertEqual("LOCAL_STOPPED", self.state()["stage"])
        self.assertTrue(self.state()["vehicles"]["test"]["runtime"]["stopProof"]["unprovisioned"])

    def test_isolated_test_reuses_exact_bridge_and_cannot_stop_its_owner(self):
        owner_root = self.root.parent / "aosedge-sdv-demo"
        consumer_root = self.root.parent / "aosedge-sdv-demo-qual-fixture"
        consumer_root.mkdir()
        state = self.state()
        state.update(scope="SINGLE_ROLE_ENGINEERING", vehicles={"test": state["vehicles"]["test"]})
        identity = "11111111-1111-4111-8111-111111111111"
        for root in (owner_root, consumer_root):
            script = root / "scripts/host/aosvm-dns-bridge"
            script.parent.mkdir(parents=True)
            script.write_text("exact-fixture-script")
        (owner_root / JOURNAL).parent.mkdir(parents=True)
        atomic_json(owner_root / JOURNAL, dict(kind="democtl.current-run", shared=dict(dns=dict(
            ownerId=identity, state="RUNNING", pid=54321))))
        self.runtime.root = self.runtime.assets = consumer_root
        with patch.object(self.runtime, "_owned_pid", return_value=54321), \
                patch.object(self.runtime, "_save"), patch.object(self.runtime, "_spawn") as spawn:
            self.runtime._start_dns(state)
            self.assertEqual("EXTERNAL_DEPENDENCY", state["shared"]["dns"]["ownership"])
            self.runtime._stop_dns(state)
            spawn.assert_not_called()
            self.assertEqual([], self.runtime.killed)
            (owner_root / "scripts/host/aosvm-dns-bridge").write_text("different-script")
            with self.assertRaisesRegex(EnvironmentError, "DNS_OWNER_NOT_PROVEN"):
                self.runtime._start_dns(state)

    def test_started_guest_data_can_be_retired_with_exact_stop_proof(self):
        self.runtime.execute("start", "all", 1)
        qemu_io = shutil.which("qemu-io")
        if not qemu_io:
            self.skipTest("qemu-io needed for written-overlay proof")
        overlay = self.root / self.state()["vehicles"]["test"]["overlay"]
        subprocess.run([qemu_io, "-f", "qcow2", "-c", "write -P 0x55 0 512", str(overlay)],
                       capture_output=True, check=True, timeout=5)
        self.runtime.execute("stop", "all", 1)
        result = self.environment.retire()
        self.assertFalse((self.root / JOURNAL).exists())
        self.assertFalse(access_path(self.root, "test").exists())
        self.assertEqual(self.support.sha, digest(self.support.source))
        self.assertFalse(result["cloudActions"])

    def test_provisioned_or_unknown_guest_never_gets_local_delete_proof(self):
        self.runtime.execute("start", "all", 1)
        self.runtime.unprovisioned = False
        self.runtime.execute("stop", "all", 1)
        with self.assertRaisesRegex(EnvironmentError, "STOPPED_UNPROVISIONED_PROOF_REQUIRED"):
            self.environment.retire()
        self.assertTrue((self.root / JOURNAL).exists())

    def test_changed_stopped_disk_invalidates_proof(self):
        self.runtime.execute("start", "all", 1)
        self.runtime.execute("stop", "all", 1)
        state = self.state()
        state["vehicles"]["test"]["runtime"]["stopProof"]["overlaySha256"] = "0" * 64
        atomic_json(self.root / JOURNAL, state)
        with self.assertRaisesRegex(EnvironmentError, "STOPPED_UNPROVISIONED_PROOF_REQUIRED"):
            self.environment.retire()

    def test_stop_current_vehicle_is_blocked_before_shutdown(self):
        self.runtime.execute("start", "all", 1)
        state = self.state()
        state["currentVehicle"] = "test"
        atomic_json(self.root / JOURNAL, state)
        with self.assertRaisesRegex(EnvironmentError, "PARK_OR_DETACH"):
            self.runtime.execute("stop", "all", 1)
        self.assertEqual(3, len(self.runtime.running))

    def test_stop_timeout_never_kills_a_vm_or_its_dns(self):
        self.runtime.execute("start", "test", 1)
        self.runtime.shutdown_works = False
        result = self.runtime.execute("stop", "test", 0.02)
        self.assertEqual("VM_STOP_TIMEOUT_NO_FORCE_USED", result["vehicles"]["test"]["reason"])
        self.assertEqual([], self.runtime.killed)
        self.assertEqual(2, len(self.runtime.running))

    def test_owner_mismatch_blocks_without_adopting_process(self):
        self.runtime.execute("start", "test", 1)
        for pid, command in self.runtime.running.items():
            if "-machine" in command:
                self.runtime.running[pid] = command + ["-S"]
        result = self.runtime.execute("start", "test", 1)
        self.assertEqual("BLOCKED", result["vehicles"]["test"]["state"])
        self.assertEqual(2, len(self.runtime.spawned))

    def test_status_binds_generated_access_not_legacy_credentials(self):
        self.runtime.execute("start", "test", 1)
        config = load_configuration(self.root)
        self.assertEqual(access_path(self.root, "test"), config["vehicles"]["test"]["accessRoot"])
        self.assertEqual(18053, config["vehicles"]["test"]["dnsPort"])
        self.assertNotIn("unitId", config["vehicles"]["test"])
        self.assertNotIn("fixture-material", (self.root / JOURNAL).read_text())

    def test_missing_explicit_password_never_searches_credentials(self):
        with self.assertRaisesRegex(EnvironmentError, "CONSOLE_PASSWORD_REQUIRED"):
            enroll_serial(self.root / "serial", self.root / "access", 10022, 1, None)
        self.assertFalse((self.root / "access").exists())

    def test_unresolved_other_role_is_not_forgotten(self):
        self.runtime.execute("start", "test", 1)
        self.runtime.shutdown_works = False
        self.runtime.execute("stop", "test", 0.02)
        before = self.state()["operations"]
        with self.assertRaisesRegex(EnvironmentError, "PREVIOUS_TARGETS_REQUIRE_RECONCILIATION"):
            self.runtime.execute("start", "production", 1)
        self.assertEqual(before, self.state()["operations"])
        self.runtime.shutdown_works = True
        self.runtime.execute("stop", "all", 1)
        self.assertEqual(1, len(self.state()["operations"]))

    def test_dns_failure_preserves_stopped_vm_result(self):
        self.runtime.execute("start", "test", 1)
        with patch.object(self.runtime, "_stop_dns", side_effect=EnvironmentError("DNS_STOP_TIMEOUT")):
            result = self.runtime.execute("stop", "test", 1)
        self.assertEqual("COMPLETED", result["vehicles"]["test"]["state"])
        self.assertEqual("DNS_STOP_TIMEOUT", result["infrastructure"]["reason"])
        self.assertEqual("UNCERTAIN", self.state()["operations"][-1]["state"])

    def test_cli_and_api_use_one_vm_core_and_api_has_no_password_or_path(self):
        request = request_from_arguments(build_parser().parse_args(["vm", "start", "all", "--timeout", "20"]))
        self.assertEqual(20, request.timeout)
        app = DemoOrchestrator(environment_service=self.environment, vm_service=self.runtime)
        result = execute_operation({"domain": "vm", "action": "start", "target": "all"}, app)
        self.assertEqual("COMPLETED", result["state"])
        with self.assertRaises(ValueError):
            execute_operation({"domain": "vm", "action": "start", "target": "test", "password": "not-accepted"}, app)


if __name__ == "__main__":
    unittest.main()
