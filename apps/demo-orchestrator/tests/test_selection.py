# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Agreed CLI/API selection semantics; never start live systems in these tests."""

import contextlib
import io
import json
import unittest
from unittest.mock import Mock, patch

from aosedge_demo_orchestrator.api import execute_operation
from aosedge_demo_orchestrator.application import DemoOrchestrator
from aosedge_demo_orchestrator.cli import main
from aosedge_demo_orchestrator.models import OperationRequest, OperationState, VehicleTarget


class SelectionTests(unittest.TestCase):
    def setUp(self):
        self.vm = Mock()
        self.units = Mock()
        self.environment = Mock()
        self.source = Mock()
        def selected(role):
            return dict(requestedCurrentVehicle=role, currentVehicle=role, noOp=False,
                perUnitMtls="DEFERRED", trustProfile="LOCAL_DEMO_SERVER_TLS", vehicles={})
        self.source.prepare.side_effect = lambda target, role: selected(role)
        self.source.select.side_effect = selected
        self.app = DemoOrchestrator(vm_service=self.vm, unit_service=self.units,
                                    environment_service=self.environment, source_service=self.source)

    def tearDown(self):
        self.vm.execute.assert_not_called()
        self.units.execute.assert_not_called()
        self.environment.create.assert_not_called()
        self.environment.retire.assert_not_called()

    def test_all_preserves_one_explicit_current_role(self):
        for role in ("test", "production"):
            result = self.app.execute(OperationRequest("environment", "prepare", VehicleTarget.ALL, current=role))
            self.assertEqual(OperationState.COMPLETED, result.state)
            self.assertEqual("all", result.target)
            self.assertEqual(role, result.data["requestedCurrentVehicle"])
            self.assertEqual("DEFERRED", result.data["perUnitMtls"])

    def test_prepare_rejects_missing_or_invalid_selection(self):
        cases = [(None, "test", "PREPARE_TARGET_REQUIRED"),
                 (VehicleTarget.ALL, None, "CURRENT_VEHICLE_REQUIRED"),
                 (VehicleTarget.ALL, "all", "CURRENT_VEHICLE_MUST_BE_SINGLE_ROLE"),
                 (VehicleTarget.TEST, "production", "CURRENT_VEHICLE_NOT_IN_TARGET"),
                 (VehicleTarget.PRODUCTION, "test", "CURRENT_VEHICLE_NOT_IN_TARGET")]
        for target, current, reason in cases:
            result = self.app.execute(OperationRequest("environment", "prepare", target, current=current))
            self.assertEqual(OperationState.BLOCKED, result.state)
            self.assertEqual(reason, result.message)

    def test_select_rejects_all_and_ambiguous_arguments(self):
        for target, current in [(VehicleTarget.ALL, None), (None, None), (VehicleTarget.TEST, "production")]:
            result = self.app.execute(OperationRequest("vehicle", "select", target, current=current))
            self.assertEqual(OperationState.BLOCKED, result.state)

    def test_api_does_not_discard_current(self):
        for role in ("test", "production"):
            result = execute_operation(dict(domain="environment", action="prepare", target="all", current=role), self.app)
            self.assertEqual(role, result["data"]["requestedCurrentVehicle"])

    def test_api_rejects_missing_current_and_extra_capabilities(self):
        base = dict(domain="environment", action="prepare", target="all", current="test")
        invalid = [dict(domain="environment", action="prepare", target="all"),
                   dict(base, current="all"), dict(base, target="production")]
        for key in ("credential", "command", "socket", "force", "unitId", "image_path"):
            invalid.append(dict(base, **{key: "not-allowed"}))
        for payload in invalid:
            with self.assertRaises(ValueError):
                execute_operation(payload, self.app)

    def test_select_api_keeps_one_role(self):
        for role in ("test", "production"):
            result = execute_operation(dict(domain="vehicle", action="select", target=role), self.app)
            self.assertEqual(role, result["data"]["requestedCurrentVehicle"])
        for role in ("all", None):
            with self.assertRaises(ValueError):
                execute_operation(dict(domain="vehicle", action="select", target=role), self.app)

    def test_cli_rejects_missing_or_plural_current_before_application(self):
        for arguments in (["environment", "prepare", "--target", "all"],
                          ["environment", "prepare", "--target", "all", "--current", "all"],
                          ["vehicle", "select", "all"]):
            with patch("aosedge_demo_orchestrator.cli.DemoOrchestrator") as app, contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as error:
                    main(arguments)
                self.assertEqual(2, error.exception.code)
                app.assert_not_called()

    def test_cli_passes_valid_selection_to_source_adapter(self):
        output = io.StringIO()
        with patch("aosedge_demo_orchestrator.cli.DemoOrchestrator", return_value=self.app), contextlib.redirect_stdout(output):
            code = main(["--output", "json", "environment", "prepare", "--target", "all", "--current", "test"])
        result = json.loads(output.getvalue())
        self.assertEqual(0, code)
        self.assertEqual("COMPLETED", result["state"])
        self.assertEqual("test", result["data"]["currentVehicle"])
        self.source.prepare.assert_called_once_with("all", "test")


if __name__ == "__main__":
    unittest.main()
