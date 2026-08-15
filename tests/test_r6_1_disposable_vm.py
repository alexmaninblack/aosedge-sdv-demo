# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Safety tests for disposable R6.1 image qualification."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "r6-1-disposable-vm"


def load_helper():
    loader = importlib.machinery.SourceFileLoader("r6_1_disposable_vm", str(SCRIPT))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    if spec is None:
        raise RuntimeError("cannot create disposable VM module spec")
    module = importlib.util.module_from_spec(spec)
    sys.modules[loader.name] = module
    loader.exec_module(module)
    return module


HELPER = load_helper()


class R61DisposableVMTests(unittest.TestCase):
    def test_base_is_read_only_hashed_and_variant_scoped(self) -> None:
        original = HELPER.ARTIFACT_ROOT
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            image = root / "upstream" / "main-qemuarm64.img"
            image.parent.mkdir()
            image.write_bytes(b"r61-test-image")
            image.chmod(0o444)
            digest = HELPER.sha256(image)
            try:
                HELPER.ARTIFACT_ROOT = root
                layout = HELPER.create_layout("upstream", str(image), digest)
                self.assertEqual(layout.base, image.resolve())
                with self.assertRaisesRegex(HELPER.QualificationError, "project"):
                    HELPER.create_layout("project", str(image), digest)
                with self.assertRaisesRegex(HELPER.QualificationError, "mismatch"):
                    HELPER.create_layout("upstream", str(image), "0" * 64)

                project_image = root / "project" / "candidate.img"
                project_image.parent.mkdir()
                project_image.write_bytes(b"r61-candidate-image")
                project_image.chmod(0o444)
                candidate = HELPER.create_layout(
                    "candidate", str(project_image), HELPER.sha256(project_image)
                )
                self.assertEqual(candidate.ssh_port, 10026)
            finally:
                HELPER.ARTIFACT_ROOT = original

    def test_qemu_network_is_offline_and_host_forward_is_loopback_only(self) -> None:
        layout = HELPER.Layout(
            variant="upstream",
            base=Path("/qualified/base.img"),
            expected_sha256="0" * 64,
            overlay=Path("/qualified/upstream.qcow2"),
            pid=Path("/qualified/upstream.pid"),
            qmp=Path("/qualified/upstream.qmp"),
            serial=Path("/qualified/upstream.serial"),
            serial_log=Path("/qualified/upstream.log"),
            evidence=Path("/qualified/upstream.json"),
            ssh_port=10024,
            mac="52:54:00:52:61:20",
            vm_name="r61-qual-upstream",
        )
        command = HELPER.qemu_command(
            layout, Path("/qualified/QEMU_EFI.fd"), "/qualified/qemu"
        )
        rendered = " ".join(command)
        self.assertIn("accel=hvf", rendered)
        self.assertIn("restrict=on", rendered)
        self.assertIn("hostfwd=tcp:127.0.0.1:10024-10.0.0.100:22", rendered)
        self.assertNotIn("hostfwd=tcp:0.0.0.0", rendered)
        self.assertNotIn("8089", rendered)
        self.assertIn("format=qcow2", rendered)
        self.assertIn("-daemonize", command)

    def test_overlay_metadata_is_bound_to_the_raw_base(self) -> None:
        content = SCRIPT.read_text(encoding="utf-8")
        self.assertIn('metadata.get("format") != "qcow2"', content)
        self.assertIn('metadata.get("backing-filename-format") != "raw"', content)
        self.assertIn("backing != layout.base", content)
        self.assertIn("qualification overlay mode must be 0600", content)

    def test_reset_requires_explicit_confirmation(self) -> None:
        content = SCRIPT.read_text(encoding="utf-8")
        self.assertIn('fail("reset-overlay requires --confirm")', content)
        self.assertIn("no forced termination was used", content)
        self.assertNotIn("kill -9", content)

    def test_guest_access_reuses_strict_owned_vm_helper(self) -> None:
        guest_wrapper = (ROOT / "scripts" / "r6-1-guest").read_text(
            encoding="utf-8"
        )
        status_helper = (
            ROOT / "scripts" / "host" / "r6-1-disposable-status"
        ).read_text(encoding="utf-8")
        generic_helper = (ROOT / "scripts" / "host" / "aosvm-guest").read_text(
            encoding="utf-8"
        )
        self.assertIn("AOSVM_GUEST_STATUS_HELPER", guest_wrapper)
        self.assertIn("AOSVM_GUEST_ACCESS_ROOT", guest_wrapper)
        self.assertIn("R61_QUAL_SHA256", status_helper)
        self.assertIn('"$STATUS_HELPER" >/dev/null', generic_helper)
        self.assertIn("StrictHostKeyChecking=yes", generic_helper)

    def test_guest_gate_separates_upstream_and_empty_project_store(self) -> None:
        guest_gate = (ROOT / "scripts" / "guest" / "r6-1-bootstrap-check").read_text(
            encoding="utf-8"
        )
        self.assertIn("guest is unexpectedly provisioned", guest_gate)
        self.assertIn('crun run --bundle . "$namespace_container"', guest_gate)
        self.assertIn("required OCI namespaces do not work together", guest_gate)
        self.assertIn('"readonly": true', guest_gate)
        self.assertIn("qualified_interface=$(ip -4 route show default", guest_gate)
        self.assertNotIn("address show dev eth0", guest_gate)
        self.assertIn("upstream image contains the project runtime", guest_gate)
        self.assertIn(
            'aos-vm-1.0.0-main-qemuarm64-vehicle-data-provider', guest_gate
        )
        self.assertIn('health_status" -eq 3', guest_gate)
        self.assertIn("aos-vehicle-data-provider-health active", guest_gate)
        self.assertIn("empty project store has an active slot", guest_gate)
        self.assertIn("provider self-test does not use DynamicUser", guest_gate)
        self.assertIn("provider reload boundary is missing", guest_gate)
        self.assertIn("provider readiness is process-only", guest_gate)
        self.assertIn("vehicle integration configuration boundary is missing", guest_gate)
        self.assertIn("provider systemd unit was not loaded by PID 1", guest_gate)
        self.assertIn("provider self-test unit was not loaded by PID 1", guest_gate)
        self.assertNotIn("systemd-analyze verify", guest_gate)
        self.assertIn(
            "health controller incorrectly transitions into the payload domain",
            guest_gate,
        )
        self.assertIn("vehicle_data_provider_store_t", guest_gate)
        self.assertIn("current boot contains an SELinux AVC denial", guest_gate)


if __name__ == "__main__":
    unittest.main()
