# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import contextlib
import io
import json
import unittest
from unittest.mock import patch

from aosedge_demo_orchestrator.api import execute_operation
from aosedge_demo_orchestrator.cli import build_parser, main
from aosedge_demo_orchestrator.environment import EnvironmentError


class DemoCtlBoilerplateTests(unittest.TestCase):
    def test_composite_initialization_reaches_the_same_source_service(self):
        from aosedge_demo_orchestrator.application import DemoOrchestrator
        from aosedge_demo_orchestrator.models import OperationRequest, VehicleTarget, OperationState
        from unittest.mock import Mock
        source = Mock(initialize_test=Mock(return_value=dict(currentVehicle="test")))
        result = DemoOrchestrator(source_service=source).execute(OperationRequest("vehicle", "initialize", VehicleTarget.TEST))
        self.assertEqual(OperationState.COMPLETED, result.state)
        source.initialize_test.assert_called_once()
    def test_command_tree_accepts_each_vehicle_selector(self) -> None:
        parser = build_parser()
        for target in ("test", "production", "all"):
            arguments = parser.parse_args(["vm", "start", target])
            self.assertEqual(target, arguments.target)

    def test_status_is_read_only(self) -> None:
        output = io.StringIO()
        with contextlib.redirect_stdout(output), patch(
            "aosedge_demo_orchestrator.probes.process_snapshot", return_value=[]
        ), patch("aosedge_demo_orchestrator.source.SourceService.observe", return_value={"state": "NOT_PREPARED"}):
            exit_code = main(["--output", "json", "status"])
        result = json.loads(output.getvalue())
        self.assertEqual(0, exit_code)
        self.assertEqual("OBSERVED", result["state"])
        self.assertEqual("orchestrator.status", result["operation"])

    def test_unit_cli_preserves_blocked_result_without_external_call(self) -> None:
        output = io.StringIO()
        with contextlib.redirect_stdout(output), patch(
            "aosedge_demo_orchestrator.units.UnitService.execute", side_effect=EnvironmentError("FIXTURE_BLOCKED")
        ):
            exit_code = main(["--output", "json", "unit", "provision", "test"])
        result = json.loads(output.getvalue())
        self.assertEqual(1, exit_code)
        self.assertEqual("BLOCKED", result["state"])
        self.assertEqual("test", result["target"])
        self.assertEqual("FIXTURE_BLOCKED", result["message"])

    def test_api_adapter_uses_the_same_application_boundary(self) -> None:
        with patch("aosedge_demo_orchestrator.units.UnitService.execute", return_value={
            "vehicles": {"production": {"state": "COMPLETED", "lifecycle": "DELETED"}}
        }) as unit:
            result = execute_operation({"domain": "unit", "action": "delete", "target": "production"})
        self.assertEqual("COMPLETED", result["state"])
        unit.assert_called_once_with("delete", "production")
        for field in ("unitId", "credential", "password", "force", "unitSetId"):
            with self.assertRaises(ValueError):
                execute_operation(dict(domain="unit", action="delete", target="test", **{field: "not-allowed"}))

    def test_interrupt_preserves_state_and_has_no_traceback(self):
        output = io.StringIO()
        with patch("aosedge_demo_orchestrator.units.UnitService.execute", side_effect=KeyboardInterrupt), contextlib.redirect_stderr(output):
            code = main(["unit", "deprovision", "production"])
        self.assertEqual(130, code)
        self.assertIn("state retained", output.getvalue())
        self.assertNotIn("Traceback", output.getvalue())


if __name__ == "__main__":
    unittest.main()
