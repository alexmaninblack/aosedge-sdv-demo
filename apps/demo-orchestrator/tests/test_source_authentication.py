# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
import copy
import contextlib
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from aosedge_demo_orchestrator import source_authentication as auth
from aosedge_demo_orchestrator.environment import EnvironmentError
try:
    from .test_source_trust import VEHICLE
except ImportError:  # unittest discovery with the tests directory as its root
    from test_source_trust import VEHICLE


class AuthenticationTests(unittest.TestCase):
    def setUp(self):
        self.state = dict(vehicles=dict(test=copy.deepcopy(VEHICLE)), source=dict(assignmentGeneration=2,
            trust=dict(enabled=True, profile="SELECTED_UNIT_MUTUAL_TLS", target="test",
                fingerprints=dict(vdp="a" * 64, runtime="b" * 64, dashboard="c" * 64))))
        self.driver = SimpleNamespace(root=Path("/unused"), budget=lambda n: n, vm=Mock(), guest=Mock(), progress=Mock())

    def test_legacy_or_absent_source_never_enables_strict_implicitly(self):
        for state in ({}, {"source": None}, {"source": {}}, {"source": {"trust": {"enabled": False}}}):
            self.assertFalse(auth.enabled(state))

    def test_lost_detach_response_is_reconciled_without_second_mutation(self):
        self.state["source"]["trust"]["pending"] = dict(action="detach", generation=2)
        with patch.object(auth, "observe", return_value=dict(state="DETACHED", assignmentGeneration=3)), \
                patch.object(auth.trust, "assignment") as mutation:
            auth.detach(self.driver, self.state)
        mutation.assert_not_called()
        self.assertEqual(3, self.state["source"]["assignmentGeneration"])
        self.assertNotIn("pending", self.state["source"]["trust"])

    def test_detach_requires_exact_owner_before_mutation(self):
        other = dict(auth.selection(self.state), nodeId="00000000-0000-4000-8000-000000000001")
        with patch.object(auth, "observe", return_value=dict(state="SELECTED", assignmentGeneration=2, selectedSource=other)), \
                patch.object(auth.trust, "assignment") as mutation:
            with self.assertRaisesRegex(EnvironmentError, "OWNER_CONFLICT"):
                auth.detach(self.driver, self.state)
        mutation.assert_not_called()

    def test_detach_requires_selected_role_sessions_to_close(self):
        first = dict(state="SELECTED", assignmentGeneration=2, selectedSource=auth.selection(self.state))
        second = dict(state="DETACHED", assignmentGeneration=3,
            activeRoleCounts=dict(selectedPlatformUnit=1, platformUpdateRuntime=0))
        with patch.object(auth, "observe", side_effect=[first, second]), \
                patch.object(auth.trust, "assignment", return_value=dict(result="ACCEPTED")) as mutation:
            with self.assertRaisesRegex(EnvironmentError, "SESSIONS_REMAIN"):
                auth.detach(self.driver, self.state)
        mutation.assert_called_once()
        self.assertEqual("detach", self.state["source"]["trust"]["pending"]["action"])

    def test_live_read_requires_identity_generation_role_and_provider(self):
        current = dict(state="SELECTED", assignmentGeneration=2, selectedSource=auth.selection(self.state),
            activeRoleCounts=dict(selectedPlatformUnit=1))
        self.driver.guest.return_value = dict(mutualTlsConfigured=True, vdpProcess="active",
            vdpData="VDP data READY; source LIVE; reason NONE", vdpRestarts="0")
        with patch.object(auth, "observe", return_value=current):
            self.assertTrue(auth.connection(self.driver, self.state, "test")["mutualTls"])
            current["assignmentGeneration"] = 1
            self.assertFalse(auth.connection(self.driver, self.state, "test")["mutualTls"])
            current["assignmentGeneration"] = 2
            current["activeRoleCounts"]["selectedPlatformUnit"] = 0
            self.assertFalse(auth.connection(self.driver, self.state, "test")["mutualTls"])
            current["activeRoleCounts"]["selectedPlatformUnit"] = 1
            self.driver.guest.return_value["vdpProcess"] = "failed"
            self.assertFalse(auth.connection(self.driver, self.state, "test")["mutualTls"])

    def test_factory_baseline_requires_actual_authenticated_read_not_provider(self):
        current = dict(state="SELECTED", assignmentGeneration=2, selectedSource=auth.selection(self.state),
            activeRoleCounts=dict(selectedPlatformUnit=0))
        status = dict(factoryBaseline=True, mutualTlsConfigured=True, vdpProcess="inactive", vdpData="")
        with patch.object(auth, "observe", return_value=current):
            self.driver.guest.side_effect = [status, dict(serverTls=True, mutualTls=True, advancingVissFrames=True)]
            result = auth.connection(self.driver, self.state, "test")
            self.assertTrue(result["factoryBaseline"])
            self.assertTrue(result["serverTls"])
            self.assertEqual("GUEST_UPDATE_IDENTITY_MUTUAL_TLS_READ_NOT_VDP_PROCESS", result["evidence"])
            self.driver.guest.side_effect = [status, dict(serverTls=False, mutualTls=False)]
            self.assertFalse(auth.connection(self.driver, self.state, "test")["serverTls"])

    def test_manual_handoff_is_bound_to_exact_identity_and_pending_receipt(self):
        record = dict(state="PENDING", unitId=VEHICLE["unitId"], nodeId=VEHICLE["nodeId"])
        self.state["source"]["trust"]["onboarding"] = record
        self.assertTrue(auth.onboarding_manual(self.state))
        record["state"] = "COMPLETE"
        self.assertFalse(auth.onboarding_manual(self.state))
        record.update(state="PENDING", nodeId="different")
        self.assertFalse(auth.onboarding_manual(self.state))

    def test_resume_manual_requires_exact_owned_restore_phase(self):
        self.state["source"]["trust"]["onboarding"] = dict(state="COMPLETE", unitId=VEHICLE["unitId"], nodeId=VEHICLE["nodeId"])
        self.state["demoLifecycle"] = dict(action="resume", target="test", state="IN_PROGRESS",
            phase="restore-test-connection", retainedConnection="test", simulationWasRunning=True)
        self.assertTrue(auth.onboarding_manual(self.state))
        for key, value in (("action", "create"), ("target", "production"), ("state", "PARTIAL"),
                ("phase", "start-test"), ("retainedConnection", None), ("simulationWasRunning", False)):
            changed = copy.deepcopy(self.state)
            changed["demoLifecycle"][key] = value
            self.assertFalse(auth.onboarding_manual(changed))
        self.state["source"]["trust"]["onboarding"]["nodeId"] = "foreign"
        self.assertFalse(auth.onboarding_manual(self.state))

    def test_provision_enrolls_gateway_without_restarting_simulator_or_ui(self):
        self.state.update(currentVehicle=None)
        self.state["source"].update(runId="run", runDirectory="run", runnerCommand=["runner"], assignmentGeneration=0)
        self.state["source"]["trust"]["fingerprints"] = dict(dashboard="c" * 64)
        self.driver.ready = Mock()
        self.driver.assets = Mock(return_value={"ca": Path("/unused/ca.pem")})
        self.driver.operation = contextlib.nullcontext
        service = Mock(root=Path("/unused"), driver=self.driver)
        service.environment._writer.side_effect = contextlib.nullcontext
        service.select.return_value = {}
        public = dict(fingerprints=dict(dashboard="c" * 64, vdp="a" * 64, runtime="b" * 64))
        with patch.object(auth, "read_json", side_effect=lambda *a: self.state), \
                patch.object(auth, "build") as build, patch.object(auth.trust, "prepare", return_value=public), \
                patch.object(auth.subprocess, "run", return_value=SimpleNamespace(returncode=1, stdout=b"certificate required", stderr=b"")) as probe:
            auth.authenticate(service, "test", provisioning=True)
            service.select.assert_called_once_with("test", initial_manual=True)
            self.assertEqual("COMPLETE", self.state["source"]["trust"]["onboarding"]["state"])
            auth.authenticate(service, "test", provisioning=True)
            self.assertEqual(2, service.select.call_count)
            probe.assert_called_once()
        service.simulation.assert_not_called()
        service.cloud.assert_not_called()
        build.assert_not_called()
        self.assertEqual("run", self.state["source"]["runId"])

    def test_legacy_running_source_is_not_silently_restarted(self):
        self.state.update(currentVehicle=None)
        self.state["source"]["trust"] = {}
        self.state["source"].update(runnerCommand=["runner"], runDirectory="run")
        service = Mock(root=Path("/unused"), driver=self.driver)
        service.environment._writer.side_effect = contextlib.nullcontext
        self.driver.operation = contextlib.nullcontext
        with patch.object(auth, "read_json", return_value=self.state), patch.object(auth, "build") as build, \
                patch.object(auth.trust, "prepare") as issue:
            with self.assertRaisesRegex(EnvironmentError, "EXPLICIT_RESTART"):
                auth.authenticate(service, "test", provisioning=True)
        build.assert_not_called()
        issue.assert_not_called()
        service.simulation.assert_not_called()
        service.select.assert_not_called()


if __name__ == "__main__":
    unittest.main()
