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

                bootstrap_image = (
                    root
                    / "bootstrap-6.1.1-maninblack.10"
                    / "main-qemuarm64.img"
                )
                bootstrap_image.parent.mkdir()
                bootstrap_image.write_bytes(b"r61-bootstrap-image")
                bootstrap_image.chmod(0o444)
                bootstrap = HELPER.create_layout(
                    "bootstrap",
                    str(bootstrap_image),
                    HELPER.sha256(bootstrap_image),
                )
                self.assertEqual(bootstrap.ssh_port, 10027)

                legacy_bootstrap_image = (
                    root
                    / "bootstrap-6.1.1-maninblack.3"
                    / "main-qemuarm64.img"
                )
                legacy_bootstrap_image.parent.mkdir()
                legacy_bootstrap_image.write_bytes(b"r61-legacy-bootstrap-image")
                legacy_bootstrap_image.chmod(0o444)
                legacy = HELPER.create_layout(
                    "bootstrap",
                    str(legacy_bootstrap_image),
                    HELPER.sha256(legacy_bootstrap_image),
                )
                self.assertEqual(legacy.ssh_port, 10027)

                store = HELPER.create_layout(
                    "store",
                    str(bootstrap_image),
                    HELPER.sha256(bootstrap_image),
                )
                self.assertEqual(store.ssh_port, 10029)
                self.assertEqual(
                    HELPER.LOCAL_ROOT / "store-workdirs.qcow2", store.data_disk
                )
            finally:
                HELPER.ARTIFACT_ROOT = original

    def test_qemu_network_is_offline_and_host_forward_is_loopback_only(self) -> None:
        layout = HELPER.Layout(
            variant="upstream",
            base=Path("/qualified/base.img"),
            expected_sha256="0" * 64,
            overlay=Path("/qualified/upstream.qcow2"),
            data_disk=None,
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

    def test_store_fixture_has_exact_private_secondary_disk(self) -> None:
        layout = HELPER.Layout(
            variant="store",
            base=Path("/qualified/base.img"),
            expected_sha256="0" * 64,
            overlay=Path("/qualified/store.qcow2"),
            data_disk=Path("/qualified/store-workdirs.qcow2"),
            pid=Path("/qualified/store.pid"),
            qmp=Path("/qualified/store.qmp"),
            serial=Path("/qualified/store.serial"),
            serial_log=Path("/qualified/store.log"),
            evidence=Path("/qualified/store.json"),
            ssh_port=10029,
            mac="52:54:00:52:61:24",
            vm_name="r61-qual-store",
        )
        rendered = " ".join(
            HELPER.qemu_command(
                layout, Path("/qualified/QEMU_EFI.fd"), "/qualified/qemu"
            )
        )
        self.assertIn("store-workdirs.qcow2", rendered)
        self.assertIn("virtio-blk-pci,drive=r61store", rendered)
        self.assertIn("serial=r61-store-fixture", rendered)
        self.assertIn("format=qcow2", rendered)
        self.assertNotIn("snapshot=on", rendered)

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

    def test_restart_artifacts_are_rotated_without_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = root / "bootstrap-boot.json"
            evidence.write_text("first\n", encoding="utf-8")
            first = HELPER.rotate_previous_artifact(evidence)
            self.assertEqual(root / "bootstrap-boot-1.json", first)
            self.assertEqual("first\n", first.read_text(encoding="utf-8"))
            evidence.write_text("second\n", encoding="utf-8")
            second = HELPER.rotate_previous_artifact(evidence)
            self.assertEqual(root / "bootstrap-boot-2.json", second)
            self.assertEqual("second\n", second.read_text(encoding="utf-8"))

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
        self.assertIn("expected_rootfs_version=6.1.1-maninblack.10", guest_gate)
        self.assertIn("validation) expected_rootfs_version=6.1.1-maninblack.10", guest_gate)
        self.assertIn("store-side-load) expected_rootfs_version=6.1.1-maninblack.9", guest_gate)
        self.assertIn("validation guest is not provisioned", guest_gate)
        self.assertIn("AosCore runtime service is not active", guest_gate)
        self.assertIn("Aos rootfs component version marker is incorrect", guest_gate)
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
        self.assertIn("dedicated non-login provider account is missing", guest_gate)
        self.assertIn("provider launcher capability boundary is incorrect", guest_gate)
        self.assertIn(
            "provider self-test does not use the bounded privilege-drop launcher",
            guest_gate,
        )
        self.assertIn("transition-suppressing DynamicUser", guest_gate)
        self.assertIn("applies no_new_privs before the launcher", guest_gate)
        self.assertIn("provider reload boundary is missing", guest_gate)
        self.assertIn("provider readiness is process-only", guest_gate)
        self.assertIn("vehicle integration configuration boundary is missing", guest_gate)
        self.assertIn("provider systemd unit was not loaded by PID 1", guest_gate)
        self.assertIn("provider self-test unit was not loaded by PID 1", guest_gate)
        self.assertIn(
            "vehicle_data_provider_store_admin_exec_t", guest_gate
        )
        self.assertIn(
            "vehicle_data_provider_store_prepare_exec_t", guest_gate
        )
        self.assertNotIn("systemd-analyze verify", guest_gate)
        self.assertIn(
            "health controller incorrectly transitions into the payload domain",
            guest_gate,
        )
        self.assertIn("vehicle_data_provider_store_t", guest_gate)
        self.assertIn(
            "/usr/lib/systemd/system/"
            "aos-vehicle-data-provider-store-attach.service",
            guest_gate,
        )
        self.assertIn("current boot contains an SELinux AVC denial", guest_gate)
        self.assertIn("current boot contains a systemd ordering cycle", guest_gate)

    def test_store_fixture_is_bounded_persistent_and_fail_closed(self) -> None:
        fixture = (
            ROOT / "scripts" / "guest" / "r6-1-store-fixture"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "aos-vehicle-data-provider-store-attach.service", fixture
        )
        self.assertIn("fixture_serial=r61-store-fixture", fixture)
        self.assertIn("fixture_sectors=4194304", fixture)
        self.assertIn("fixture_device=/dev/vda", fixture)
        self.assertIn("What=/dev/vda", fixture)
        self.assertIn('/sys/class/block/$fixture_block/serial', fixture)
        self.assertNotIn("/sys/class/block/sdb/device/serial", fixture)
        self.assertIn("findmnt -rn -M / -o SOURCE", fixture)
        self.assertIn("first-generation data disk is not blank", fixture)
        self.assertIn("context=system_u:object_r:aos_var_run_t:s0", fixture)
        self.assertIn("aos-vehicle-data-provider-store-check", fixture)
        self.assertIn("/run/aos-vehicle-data-provider-store/loop", fixture)
        self.assertIn("store backing is not fully allocated", fixture)
        self.assertIn("r6-1-store-fixture-v1", fixture)
        self.assertIn('gate_variant=${2:-store}', fixture)
        self.assertIn('security_mode=${3:-enforcing}', fixture)
        self.assertIn('store|store-side-load)', fixture)
        self.assertIn(
            "probe_unit=aos-vehicle-data-provider-selftest@a.service", fixture
        )
        self.assertIn('systemctl start "$probe_unit"', fixture)
        self.assertIn("PROBE_SECURITY_MODEL=PASS", fixture)
        self.assertIn("NON_ROOT_IDENTITY=PASS", fixture)
        self.assertNotIn("uid=$(id -u)", fixture)
        self.assertIn("PROBE_SIBLING_ACCESS=ALLOWED_FOR_DISCOVERY", fixture)
        self.assertIn("PROBE_SIBLING_ACCESS=DENIED", fixture)
        self.assertIn("provider payload did not prove a non-root", fixture)
        self.assertNotIn("id -Z", fixture)
        self.assertNotIn("/proc/self", fixture)
        self.assertNotIn(
            "probe_output=$(/usr/libexec/aos-vehicle-data-provider-launcher",
            fixture,
        )
        self.assertIn("PROVIDER_SIBLING_ACCESS=%s", fixture)
        self.assertNotIn("/dev/sda ", fixture)
        self.assertNotIn("mkfs.ext4 -q -F -m 0 -L r61-workdirs /dev/sda", fixture)

    def test_security_side_load_is_disposable_pinned_and_domain_scoped(self) -> None:
        helper = (
            ROOT / "scripts" / "guest" / "r6-1-security-side-load"
        ).read_text(encoding="utf-8")
        self.assertIn("VERSION_ID=6.1.1-maninblack.9", helper)
        self.assertIn(
            "55dc2e826d639f8434785f54a3dd69e51beef89d6e9c07229718bed72952a071",
            helper,
        )
        self.assertIn(
            "a1efd6434642210a09a80170a19830b63a6601871d1c32ef7e6f1fd4e3cba2e1",
            helper,
        )
        self.assertIn("semanage permissive -a \"$domain\"", helper)
        self.assertIn("semanage permissive -d \"$domain\"", helper)
        self.assertNotIn("setenforce 0", helper)
        self.assertNotIn("semodule -DB", helper)


if __name__ == "__main__":
    unittest.main()
