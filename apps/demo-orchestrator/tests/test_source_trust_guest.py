# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
import copy
import json
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

from aosedge_demo_orchestrator import source_trust as trust, source_trust_guest as guest
try:
    from .test_source_trust import VEHICLE
except ImportError:  # unittest discovery with the tests directory as its root
    from test_source_trust import VEHICLE


@unittest.skipUnless(Path(trust.OPENSSL).is_file(), "OpenSSL 3 unavailable")
class TrustGuestTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        root = Path(self.stack.enter_context(tempfile.TemporaryDirectory())).resolve()
        certs = root / "certs"
        public = trust.prepare(certs, VEHICLE)
        self.inputs = root / "runtime/demo-inputs"
        self.inputs.mkdir(parents=True)
        (self.inputs / "role").write_text("test\n")
        (self.inputs / "viss-update-ca").write_text("previous public trust")
        (self.inputs / "viss-update-binding").write_text("previous public binding")
        (self.inputs / "selected.json").write_text("previous public selection")
        machine = root / "machine-id"
        machine.write_text(VEHICLE["cloud"]["identity"]["nodeHardwareId"])
        for name, value in dict(INPUTS=self.inputs, STORE=root / "private", MACHINE_ID=machine,
                SM_DROPIN=root / "sm/dropin.conf", VDP_DROPIN=root / "vdp/dropin.conf").items():
            self.stack.enter_context(patch.object(guest, name, value))
        # Real filesystem permission tests are in test_source_trust; this
        # root-only remote worker is exercised in a non-root unit harness.
        self.stack.enter_context(patch.object(guest, "safe"))
        self.calls = []
        def command(argv, data=None):
            self.calls.append(argv)
            if argv[0] == "openssl":
                return trust.openssl(argv[1:]).decode()
            if "show" in argv:
                if "Job" in argv:
                    return "\n\n".join("Id=" + unit + "\nActiveState=active\nJob=\n"
                        for unit in argv if unit.endswith(".service"))
                return "ActiveState=active\nStatusText=VDP data READY; source LIVE; reason NONE\nNRestarts=0\nMainPID=12\n"
            return ""
        self.stack.enter_context(patch.object(guest, "call", side_effect=command))
        self.request = dict(action="trust-configure", role="test", vehicle=copy.deepcopy(VEHICLE), generation=2,
            fingerprints={key: public["fingerprints"][key] for key in ("vdp", "runtime")},
            material=dict(ca=(certs / "ca.pem").read_text(),
                vdpCertificate=(certs / "vdp.pem").read_text(), vdpKey=(certs / "vdp-key.pem").read_text(),
                runtimeCertificate=(certs / "runtime.pem").read_text(), runtimeKey=(certs / "runtime-key.pem").read_text()))

    def test_first_activation_repeat_and_generation_change(self):
        first = guest.execute(self.request)
        self.assertTrue(first["smRestarted"])
        self.assertTrue(first["vdpRestarted"])
        binding = json.loads((self.inputs / "viss-update-binding").read_text())
        self.assertEqual(VEHICLE["cloud"]["identity"]["nodeHardwareId"], binding["nodeId"])
        selected = json.loads((self.inputs / "selected.json").read_text())["selectedSource"]
        self.assertEqual(VEHICLE["nodeId"], selected["nodeId"])
        second = guest.execute(self.request)
        self.assertFalse(second["smRestarted"])
        self.assertFalse(second["vdpRestarted"])
        third = guest.execute(dict(self.request, generation=3))
        self.assertFalse(third["smRestarted"])
        self.assertTrue(third["vdpRestarted"])
        self.assertEqual(1, sum("restart" in call and "aos-sm.service" in call for call in self.calls))
        self.assertFalse(any("aos-cm" in c or "aos-iam" in c for c in self.calls))

    def test_empty_factory_is_distinct_from_installed_or_failed_provider(self):
        with patch.object(guest, "call", return_value="ActiveState=inactive\n"):
            self.assertTrue(guest.status()["factoryBaseline"])
            (self.inputs.parent / "active").symlink_to("missing-slot")
            self.assertFalse(guest.status()["factoryBaseline"])
            (self.inputs.parent / "active").unlink()
            (self.inputs.parent / "state").mkdir()
            (self.inputs.parent / "state/installed.json").write_text("{}")
            self.assertFalse(guest.status()["factoryBaseline"])
        with patch.object(guest, "call", return_value="ActiveState=failed\n"):
            self.assertFalse(guest.status()["factoryBaseline"])

    def test_reboot_restores_existing_projection_without_new_identity_or_repeat_restart(self):
        guest.execute(self.request)
        before = {path: path.read_bytes() for path in guest.STORE.rglob("*") if path.is_file()}
        selected = (self.inputs / "selected.json").read_bytes()
        guest.SM_DROPIN.unlink()
        guest.VDP_DROPIN.unlink()
        self.calls.clear()
        request = {key: value for key, value in self.request.items() if key not in ("material", "generation")}
        result = guest.execute(dict(request, action="trust-restore"))
        self.assertTrue(result["mutualTlsConfigured"])
        self.assertTrue(result["smRestarted"])
        self.assertTrue(result["vdpRestarted"])
        self.assertEqual(selected, (self.inputs / "selected.json").read_bytes())
        self.assertTrue(all(path.read_bytes() == data for path, data in before.items()))
        result = guest.execute(dict(request, action="trust-restore"))
        self.assertFalse(result["smRestarted"] or result["vdpRestarted"])
        self.assertEqual(1, sum("restart" in call and "aos-sm.service" in call for call in self.calls))
        self.assertFalse(any("aos-cm" in call or "aos-iam" in call for call in self.calls))

    def test_restore_cannot_enroll_missing_or_foreign_material(self):
        guest.execute(self.request)
        request = {key: value for key, value in self.request.items() if key not in ("material", "generation")}
        request["action"] = "trust-restore"
        selected_path = self.inputs / "selected.json"
        original = selected_path.read_text()
        selected = json.loads(original)
        selected["selectedSource"]["nodeId"] = "foreign"
        selected_path.write_text(json.dumps(selected))
        self.calls.clear()
        with self.assertRaisesRegex(ValueError, "IDENTITY_MISMATCH"):
            guest.execute(request)
        self.assertEqual([], self.calls)
        selected_path.write_text(original)
        (guest.STORE / "selected-platform-unit/client-key.pem").unlink()
        with self.assertRaises(FileNotFoundError):
            guest.execute(request)
        self.assertEqual([], self.calls)

    def test_wrong_vm_is_rejected_before_crypto_or_write(self):
        self.request["vehicle"]["localVmId"] = "6fcf5a74-0b74-4ef0-a05d-44bad598ab95"
        with self.assertRaisesRegex(ValueError, "IDENTITY_MISMATCH"):
            guest.execute(self.request)
        self.assertEqual([], self.calls)

    def test_production_is_never_touched(self):
        self.request["role"] = "production"
        with self.assertRaisesRegex(ValueError, "IDENTITY_MISMATCH"):
            guest.execute(self.request)
        self.assertEqual([], self.calls)

    def test_pending_fota_does_not_restart_or_write_credentials(self):
        state = self.inputs.parent / "state"
        state.mkdir()
        (state / "transaction.json").write_text("{}")
        with self.assertRaisesRegex(ValueError, "TRANSACTION_ACTIVE"):
            guest.execute(self.request)
        self.assertFalse(guest.STORE.exists())
        self.assertEqual([], self.calls)

    def test_replacement_key_requires_explicit_reconciliation(self):
        guest.execute(self.request)
        self.calls.clear()
        self.request["material"]["vdpKey"] = "not a replacement credential"
        with self.assertRaisesRegex(ValueError, "CREDENTIAL_CONFLICT"):
            guest.execute(self.request)
        self.assertEqual([], self.calls)


if __name__ == "__main__":
    unittest.main()
