# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Contract tests for the thin successor Testing Vehicle launcher profile."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "scripts" / "successor-testing-vm"
LAUNCHER = ROOT / "scripts" / "aosvm"
ONBOARD = ROOT / "scripts" / "aosvm-macos-onboard"
NETWORK_COMPAT = ROOT / "scripts" / "guest" / "aosvm-apply-qemu-network-compat"
MANIFEST_HELPER = ROOT / "scripts" / "host" / "aosvm-successor-manifest"
PHASE13_GATE = ROOT / "tests" / "host" / "aosvm-phase13-stopped-gate"


class SuccessorTestingVMTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(
            prefix="aosvm-successor-testing-", dir="/private/tmp"
        )
        self.root = Path(self.temporary.name)
        self.image = self.root / "successor-testing.img"
        with self.image.open("wb") as stream:
            stream.truncate(8 * 1024 * 1024)
        self.image.chmod(0o444)
        info = json.loads(
            subprocess.run(
                ["qemu-img", "info", "--output=json", str(self.image)],
                check=True,
                capture_output=True,
                text=True,
            ).stdout
        )
        self.payload = {
            "schema": 1,
            "kind": "aosedge.successor-testing-launcher.v1",
            "vehicleRole": "Testing Vehicle",
            "image": {
                "path": str(self.image),
                "format": "raw",
                "version": "6.1.2-demo.1",
                "sizeBytes": self.image.stat().st_size,
                "virtualSizeBytes": info["virtual-size"],
                "sha256": self._sha256(self.image),
            },
        }
        self.manifest = self.root / "successor-testing-manifest.json"
        self._write_manifest()

    def tearDown(self) -> None:
        self.image.chmod(0o600)
        if self.manifest.exists():
            self.manifest.chmod(0o600)
        self.temporary.cleanup()

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def _write_manifest(self) -> None:
        if self.manifest.exists():
            self.manifest.chmod(0o600)
        self.manifest.write_text(
            json.dumps(self.payload, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        self.manifest.chmod(0o444)

    def _run_profile(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment["HOME"] = str(self.root / "home")
        return subprocess.run(
            [str(PROFILE), "--manifest", str(self.manifest), *arguments],
            check=False,
            capture_output=True,
            text=True,
            env=environment,
        )

    def _successor_state_root(self) -> Path:
        return (
            self.root
            / "home"
            / "Library"
            / "Application Support"
            / "CarlaAosEdge"
            / "AosVM"
            / "successor-testing"
        )

    def test_validate_binds_exact_manifest_image_digest_and_version(self) -> None:
        result = self._run_profile("validate")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("Successor Testing Vehicle selection is valid.", result.stdout)
        self.assertIn(str(self.manifest), result.stdout)
        self.assertIn(str(self.image), result.stdout)
        self.assertIn("Image format: raw", result.stdout)
        self.assertIn("Image version: 6.1.2-demo.1", result.stdout)
        self.assertIn(self.payload["image"]["sha256"], result.stdout)
        self.assertIn("No VM, network, Cloud, provisioning", result.stdout)
        self.assertFalse(self._successor_state_root().exists())

    def test_manifest_path_must_be_absolute(self) -> None:
        result = subprocess.run(
            [str(PROFILE), "--manifest", self.manifest.name, "validate"],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(0, result.returncode)
        self.assertIn("manifest path must be absolute", result.stderr)

    def test_changed_digest_is_rejected_without_state(self) -> None:
        self.payload["image"]["sha256"] = "0" * 64
        self._write_manifest()
        result = self._run_profile("validate")
        self.assertNotEqual(0, result.returncode)
        self.assertIn("SHA-256 does not match manifest", result.stderr)
        self.assertFalse(self._successor_state_root().exists())

    def test_mutable_image_is_rejected(self) -> None:
        self.image.chmod(0o644)
        result = self._run_profile("validate")
        self.assertNotEqual(0, result.returncode)
        self.assertIn("successor image must be read-only", result.stderr)

    def test_unknown_manifest_property_is_rejected(self) -> None:
        self.payload["unexpected"] = True
        self._write_manifest()
        result = self._run_profile("validate")
        self.assertNotEqual(0, result.returncode)
        self.assertIn("missing or unknown top-level properties", result.stderr)

    def test_wrong_vehicle_role_is_rejected(self) -> None:
        self.payload["vehicleRole"] = "Production Vehicle"
        self._write_manifest()
        result = self._run_profile("validate")
        self.assertNotEqual(0, result.returncode)
        self.assertIn("vehicleRole must be Testing Vehicle", result.stderr)

    def test_direct_successor_launcher_use_is_rejected(self) -> None:
        environment = os.environ.copy()
        environment["AOSVM_INSTANCE"] = "successor-testing"
        result = subprocess.run(
            [str(LAUNCHER), "status"],
            check=False,
            capture_output=True,
            text=True,
            env=environment,
        )
        self.assertNotEqual(0, result.returncode)
        self.assertIn("must be selected through scripts/successor-testing-vm", result.stderr)

    def test_profile_isolated_ports_mac_and_state_roots_are_exact(self) -> None:
        source = PROFILE.read_text(encoding="utf-8")
        self.assertIn("AOSVM_INSTANCE=successor-testing", source)
        self.assertIn("AOSVM_MAC_ADDRESS=52:54:00:53:54:30", source)
        self.assertIn("AOSVM_SSH_HOST_PORT=10030", source)
        self.assertIn("AOSVM_HOST_DNS_PORT=18056", source)
        self.assertIn("AOSVM_PROVISIONING_HOST_PORT=18092", source)
        self.assertIn('AOSVM_LOCAL_ROOT="$REPOSITORY_ROOT/.local/successor-testing"', source)
        self.assertIn('AOSVM_RUN_ROOT="/private/tmp/aosvm-successor-testing-runtime"', source)
        self.assertIn('AOSVM_BACKUP_ROOT="$STATE_ROOT/backups"', source)
        self.assertIn('AOSVM_PROVISION_ATTEMPT_ROOT="$STATE_ROOT/provisioning"', source)

    def test_profile_dns_port_is_applied_to_the_guest_overlay(self) -> None:
        onboard = ONBOARD.read_text(encoding="utf-8")
        network_compat = NETWORK_COMPAT.read_text(encoding="utf-8")
        self.assertIn(
            "GUEST_DNS_BRIDGE_PORT=${AOSVM_HOST_DNS_PORT:-18053}", onboard
        )
        self.assertIn(
            'aosvm-apply-qemu-network-compat "$GUEST_DNS_BRIDGE_PORT"', onboard
        )
        self.assertIn("host_dns_port=${1:-18053}", network_compat)
        self.assertIn(
            "expected_upstream=server=10.0.0.1#$host_dns_port", network_compat
        )

    def test_phase13_gate_accepts_only_manifest_validated_successor_inputs(self) -> None:
        gate = PHASE13_GATE.read_text(encoding="utf-8")
        self.assertIn("successor-testing)", gate)
        self.assertIn('AOSVM_SUCCESSOR_PROFILE_VALIDATED:-0', gate)
        self.assertIn('successor_image_format" = raw', gate)
        self.assertIn("'Successor Testing Vehicle image'", gate)
        self.assertIn("expected_backing_format=raw", gate)

    def test_profile_reuses_existing_lifecycle_and_not_offline_harness(self) -> None:
        profile = PROFILE.read_text(encoding="utf-8")
        onboard = ONBOARD.read_text(encoding="utf-8")
        launcher = LAUNCHER.read_text(encoding="utf-8")
        self.assertIn('exec "$SCRIPT_DIR/aosvm-macos-onboard" "$@"', profile)
        self.assertNotIn("r6-1-disposable-vm", profile)
        self.assertIn('"$AOSVM" checkpoint-pre-provision', onboard)
        self.assertIn('"$AOSVM" seal-provisioned', onboard)
        self.assertIn("automatic retry is blocked", onboard)
        self.assertIn("restrict=off", launcher)
        self.assertIn("Normal AosVM mode unexpectedly exposes the provisioning port", launcher)

    def test_new_files_are_private_executables(self) -> None:
        for path in (PROFILE, MANIFEST_HELPER):
            self.assertEqual(0o755, stat.S_IMODE(path.stat().st_mode), path)
            self.assertFalse(path.is_symlink(), path)


if __name__ == "__main__":
    if shutil.which("qemu-img") is None:
        raise SystemExit("qemu-img is required")
    unittest.main()
