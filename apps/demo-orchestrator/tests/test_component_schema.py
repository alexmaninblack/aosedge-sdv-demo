# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace

from aosedge_demo_orchestrator import source_guest as guest
from aosedge_demo_orchestrator.api import execute_operation
from aosedge_demo_orchestrator.cli import main
from aosedge_demo_orchestrator.components import ComponentService
from aosedge_demo_orchestrator.environment import EnvironmentError


class SchemaTests(unittest.TestCase):
    def test_configuration_diagnostic_does_not_shadow_network_probe(self):
        for unit in (None, "current-unit"):
            request = dict(action="probe", vehicle=dict(localVmId="current-vm", unitId=unit))
            with patch.object(guest, "probe", return_value={"state": "OBSERVED"}) as probe:
                self.assertEqual({"state": "OBSERVED"}, guest.execute(request))
                if unit is None:
                    probe.assert_called_once_with(preprovision=True)
                else:
                    probe.assert_called_once_with()

    def test_advisory_diagnostic_is_read_only_and_checks_exact_types(self):
        schema = {}
        missing = guest.advisory_schema_observation(schema.get)
        self.assertEqual(4, len(missing["leaves"]))
        self.assertFalse(missing["matchesContract"])
        self.assertEqual({}, schema)
        for row in missing["leaves"]:
            schema[row["path"]] = dict(type="actuator" if row["path"].endswith("Request") else "sensor", datatype="string")
        observed = guest.advisory_schema_observation(schema.get)
        self.assertTrue(observed["matchesContract"])
        self.assertEqual("NOT_PERFORMED", observed["permissionProbe"])
        self.assertEqual("NOT_PERFORMED", observed["transportProbe"])
        schema[missing["leaves"][0]["path"]]["type"] = "sensor"
        self.assertFalse(guest.advisory_schema_observation(schema.get)["matchesContract"])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name).resolve()
        for name, file in (("VSS_BASE", "base.json"), ("VSS_TEMP", "run/vss.json"), ("VSS_DROPIN", "systemd/90-democtl-vss.conf")):
            patched = patch.object(guest, name, root / file)
            patched.start()
            self.addCleanup(patched.stop)
        self.base = {"Vehicle": dict(type="branch", description="Vehicle", children={
            "Speed": dict(type="sensor", datatype="float", unit="km/h", description="keep me")})}
        guest.VSS_BASE.write_text(json.dumps(self.base))
        self.request = dict(action="component-schema-apply", target="test",
            additionalPaths=list(guest.VSS_PROOF_PATHS), vehicle=dict(localVmId="360f228d-3aef-4919-9220-27ffeb4245b1"))

    def test_merge_adds_only_eight_slip_and_four_typed_advisory_leaves(self):
        result = guest.vss_supplement(self.base)
        self.assertNotIn("CarlaSimulation", self.base["Vehicle"]["children"])
        self.assertEqual(self.base["Vehicle"]["children"]["Speed"], result["Vehicle"]["children"]["Speed"])
        self.assertEqual(result, guest.vss_supplement(result))
        def leaves(tree, prefix=""):
            found = []
            for name, node in tree.items():
                path = prefix + name
                found.extend(leaves(node["children"], path + ".") if node["type"] == "branch" else [path])
            return found
        self.assertEqual(set(guest.VSS_PROOF_PATHS) | {"Vehicle.Speed"}, set(leaves(result)))
        for team in ("BrakeHealth", "TireHealth"):
            endpoints = result["Vehicle"]["children"]["OEM"]["children"][team]["children"]["Advisory"]["children"]
            self.assertEqual("actuator", endpoints["Request"]["type"])
            self.assertEqual("sensor", endpoints["GatewayStatus"]["type"])
            self.assertEqual("string", endpoints["Request"]["datatype"])
            endpoints["Request"]["type"] = "sensor"
            with self.assertRaisesRegex(ValueError, "LEAF_CONFLICT"):
                guest.vss_supplement(result)
            endpoints["Request"]["type"] = "actuator"

    def test_exact_owned_legacy_proof_is_removable_but_not_silently_replaced(self):
        guest.VSS_DROPIN.parent.mkdir(parents=True)
        guest.VSS_DROPIN.write_text(guest.vss_override_text(self.request["vehicle"]["localVmId"]))
        guest.VSS_TEMP.parent.mkdir(parents=True)
        guest.VSS_TEMP.write_text(json.dumps(guest.vss_supplement(self.base, advisory=False), sort_keys=True) + "\n")
        with self.assertRaisesRegex(ValueError, "CONTENT_CONFLICT"):
            guest.vss_change(self.request)
        with patch.object(guest, "vss_restart", return_value=101):
            self.assertEqual("REMOVED", guest.vss_change(dict(self.request, action="component-schema-remove"))["state"])

    def test_conflicting_schema_is_never_overwritten(self):
        self.base["Vehicle"]["children"]["CarlaSimulation"] = dict(type="sensor", datatype="float")
        with self.assertRaisesRegex(ValueError, "BRANCH_CONFLICT"):
            guest.vss_supplement(self.base)

    def test_apply_repeat_remove_and_base_bytes_unchanged(self):
        before = guest.VSS_BASE.read_bytes()
        with patch.object(guest, "command", return_value=SimpleNamespace(returncode=0, stdout="?")), \
                patch.object(guest, "vss_restart", return_value=101) as restart:
            result = guest.vss_change(self.request)
            self.assertEqual("APPLIED", result["state"])
            self.assertEqual(1, restart.call_count)
            with patch.object(guest, "execute", return_value=dict(schemaLoadedByService=True, schemaSha256=result["schemaSha256"])):
                self.assertTrue(guest.vss_change(self.request)["noOp"])
            self.assertEqual(1, restart.call_count)
            self.assertNotIn("ExecStart", guest.VSS_DROPIN.read_text())
            self.assertNotIn("LoadCredential", guest.VSS_DROPIN.read_text())
            result = guest.vss_change(dict(self.request, action="component-schema-remove"))
            self.assertEqual("REMOVED", result["state"])
            self.assertFalse(guest.VSS_DROPIN.exists())
            self.assertFalse(guest.VSS_TEMP.exists())
        self.assertEqual(before, guest.VSS_BASE.read_bytes())

    def test_failed_restart_restores_stock(self):
        with patch.object(guest, "command", return_value=SimpleNamespace(returncode=0, stdout="?")), \
                patch.object(guest, "vss_restart", side_effect=[ValueError("bad"), 101]):
            with self.assertRaisesRegex(ValueError, "BASE_RESTORED"):
                guest.vss_change(self.request)
        self.assertFalse(guest.VSS_DROPIN.exists())
        self.assertFalse(guest.VSS_TEMP.exists())

    def test_role_paths_links_and_foreign_override_rejected(self):
        for changed in (dict(target="production"), dict(additionalPaths=["Vehicle.Anything"])):
            with self.assertRaisesRegex(ValueError, "TEST_CONTRACT_ONLY"):
                guest.vss_change(dict(self.request, **changed))
        guest.VSS_DROPIN.parent.mkdir(parents=True)
        guest.VSS_DROPIN.write_text("foreign")
        with self.assertRaisesRegex(ValueError, "OWNER_CONFLICT"):
            guest.vss_change(self.request)
        guest.VSS_DROPIN.unlink()
        guest.VSS_DROPIN.symlink_to(guest.VSS_BASE)
        with self.assertRaisesRegex(ValueError, "PATH_UNSAFE"):
            guest.vss_change(self.request)

    def test_cli_api_same_operation_and_production_rejected(self):
        with patch.object(ComponentService, "schema_apply", return_value=dict(state="APPLIED")) as operation:
            result = execute_operation(dict(domain="component", action="schema-apply", target="test"))
            self.assertEqual("COMPLETED", result["state"])
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(0, main(["component", "schema-apply", "test"]))
            self.assertEqual(2, operation.call_count)
        with self.assertRaises(ValueError):
            execute_operation(dict(domain="component", action="schema-apply", target="production"))
        service = ComponentService(SimpleNamespace(catalog=SimpleNamespace(project=Path(self.temp.name))))
        with self.assertRaisesRegex(EnvironmentError, "TEST_ONLY"):
            service.schema_apply("production")


if __name__ == "__main__":
    unittest.main()
