# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Static isolation checks for the dedicated R6.1 validation VM profile."""

from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "scripts" / "r6-1-validation-vm"
LAUNCHER = ROOT / "scripts" / "aosvm"


class R61ValidationVMTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profile = PROFILE.read_text(encoding="utf-8")
        cls.launcher = LAUNCHER.read_text(encoding="utf-8")

    def test_profile_uses_a_dedicated_instance_and_storage(self) -> None:
        self.assertIn("AOSVM_INSTANCE=r6-1-validation", self.profile)
        self.assertIn('AOSVM_LOCAL_ROOT="$REPOSITORY_ROOT/.local/r6-1-validation"', self.profile)
        self.assertIn('AOSVM_BACKUP_ROOT="$STATE_ROOT/backups"', self.profile)
        self.assertIn('AOSVM_PROVISION_ATTEMPT_ROOT="$STATE_ROOT/provisioning"', self.profile)

    def test_profile_uses_nonconflicting_loopback_ports(self) -> None:
        self.assertIn("AOSVM_SSH_HOST_PORT=10024", self.profile)
        self.assertIn("AOSVM_HOST_DNS_PORT=18055", self.profile)
        self.assertIn("AOSVM_PROVISIONING_HOST_PORT=18091", self.profile)

    def test_profile_uses_a_distinct_mac_address(self) -> None:
        self.assertIn("AOSVM_MAC_ADDRESS=52:54:00:52:36:32", self.profile)
        self.assertIn("validate_mac_address", self.launcher)

    def test_launcher_accepts_only_known_instances(self) -> None:
        self.assertIn("main|r6-1-validation", self.launcher)
        self.assertIn('VM_NAME="aosvm-$AOSVM_INSTANCE"', self.launcher)


if __name__ == "__main__":
    unittest.main()
