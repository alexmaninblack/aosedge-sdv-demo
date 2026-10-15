# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import json
import unittest
from contextlib import redirect_stderr
import io
from types import SimpleNamespace
from unittest.mock import Mock, patch

from aosedge_demo_orchestrator.api import execute_operation
from aosedge_demo_orchestrator.cli import build_parser
from aosedge_demo_orchestrator.application import DemoOrchestrator
from aosedge_demo_orchestrator.models import OperationRequest, OperationState, VehicleTarget
from aosedge_demo_orchestrator.source_guest import (
    cm_compare_factory32, cm_startup_comparison, cm_startup_projection,
    cm_idle_refresh_factory32,
)


class GuestDiagnosticCompatibilityTests(unittest.TestCase):
    """Keep fail-closed decoding of retained journals; retired host actions stay absent."""

    def test_retired_comparison_cli_is_rejected_before_any_execution(self):
        for phase in ("inspect", "build", "control", "without-patch", "restore", "startup", "refresh-build", "refresh-apply", "refresh-cache-restore"):
            with self.subTest(phase=phase), redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    build_parser().parse_args(["component", "cm-compare-" + phase, "test"])



    def test_presentation_api_never_exposes_comparison(self):
        application = Mock()
        for phase in ("inspect", "build", "control", "without-patch", "restore", "startup", "refresh-build", "refresh-apply", "refresh-cache-restore"):
            with self.assertRaisesRegex(ValueError, "retired"):
                execute_operation(dict(domain="component", action="cm-compare-" + phase, target="test"), application)
        application.execute.assert_not_called()

    def test_direct_retired_request_is_blocked_without_runtime_services(self):
        application = object.__new__(DemoOrchestrator)
        with patch("aosedge_demo_orchestrator.runtime_paths.installed", return_value=False):
            result = application.execute(OperationRequest("component", "cm-compare-control", VehicleTarget.TEST))
        self.assertEqual(result.state, OperationState.BLOCKED)
        self.assertEqual(result.message, "RETIRED_QUALIFICATION_OPERATION")

    def test_guest_rejects_wrong_target_phase_and_candidate_before_mutation(self):
        request = dict(target="test", phase="without-patch", vehicle=dict(
            localVmId="5aa1f8e4-a111-4467-a6cc-fb269c62a7a8", unitId="923b9820-999b-41bb-91db-b2a2c469e743"))
        with patch("aosedge_demo_orchestrator.source_guest.command") as command:
            for change in (dict(target="production"), dict(phase="other"), dict(sha256="untrusted")):
                with self.assertRaises(ValueError):
                    cm_compare_factory32(dict(request, **change))
            command.assert_not_called()



    def test_startup_projection_retains_flags_not_wire_payload(self):
        records = [dict(MESSAGE='(communication) Sent message: {"messageType":"unitStatus",'
            '"header":{"systemId":"","txn":"public-id"},"data":{"isDeltaInfo":false,'
            '"password":"secret-password","token":"secret-token"',
            __REALTIME_TIMESTAMP="20", _PID="41710", _SYSTEMD_UNIT="aos-cm.service"),
            dict(MESSAGE='(updatemanager) Unit status node info: id=public-node isConnected=1 token=hidden',
                 __REALTIME_TIMESTAMP="10", _PID="41710", _SYSTEMD_UNIT="aos-cm.service")]
        projected = cm_startup_projection(records)
        self.assertEqual([event["time"] for event in projected["events"]], ["10", "20"])
        wire = projected["events"][1]
        self.assertIs(wire["isDeltaInfo"], False)
        self.assertEqual(wire["systemId"], "")
        self.assertTrue(wire["wireTruncated"])
        self.assertEqual(projected["events"][0]["isConnected"], "1")
        for secret in ("secret-password", "secret-token", "hidden", "MESSAGE"):
            self.assertNotIn(secret, json.dumps(projected))

    def test_startup_projection_bounds_events_but_counts_all(self):
        record = dict(MESSAGE="(updatemanager) Send full unit status", __REALTIME_TIMESTAMP="1")
        projected = cm_startup_projection([record] * 151)
        self.assertEqual(len(projected["events"]), 150)
        self.assertTrue(projected["eventsTruncated"])
        self.assertEqual(sum(projected["counts"].values()), 151)

    def test_startup_empty_journal_is_not_successful_observation(self):
        request = dict(target="test", vehicle=dict(
            localVmId="5aa1f8e4-a111-4467-a6cc-fb269c62a7a8",
            unitId="923b9820-999b-41bb-91db-b2a2c469e743"))
        with patch("aosedge_demo_orchestrator.source_guest.command",
                   return_value=SimpleNamespace(returncode=0, stdout="")) as command:
            result = cm_startup_comparison(request)
        self.assertIs(result["mutation"], False)
        self.assertTrue(all(window["state"] == "NO_RETAINED_RECORDS"
                            for window in result["windows"].values()))
        self.assertEqual([call.args[0][:2] for call in command.call_args_list],
                         [["journalctl", "-b"], ["journalctl", "-b"], ["journalctl", "-b"], ["systemctl", "show"]])

    def test_startup_rejects_production_without_guest_commands(self):
        with patch("aosedge_demo_orchestrator.source_guest.command") as command:
            with self.assertRaisesRegex(ValueError, "CURRENT_TEST_32"):
                cm_startup_comparison(dict(target="production", vehicle={}))
            command.assert_not_called()


    def test_refresh_guest_is_pinned_before_any_command(self):
        request = dict(target="test", proof="factory32-idle-full-status", restartCm=True,
            vehicle=dict(localVmId="c7b8f9d8-68ea-4b65-b444-8b01595eb110",
                         unitId="d90798f6-a32c-40cc-8129-26a0f1343a67"))
        with patch("aosedge_demo_orchestrator.source_guest.command") as command:
            for change in (dict(target="production"), dict(restartCm=False), dict(sha256="arbitrary"),
                           dict(vehicle={}), dict(proof="other")):
                with self.assertRaises(ValueError):
                    cm_idle_refresh_factory32(dict(request, **change))
            command.assert_not_called()
