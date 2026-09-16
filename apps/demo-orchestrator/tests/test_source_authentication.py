# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
import copy
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from aosedge_demo_orchestrator import source_authentication as auth
from aosedge_demo_orchestrator.environment import EnvironmentError
from tests.test_source_trust import VEHICLE


class AuthenticationTests(unittest.TestCase):
    def setUp(self):
        self.state = dict(vehicles=dict(test=copy.deepcopy(VEHICLE)), source=dict(assignmentGeneration=2,
            trust=dict(enabled=True, profile="SELECTED_UNIT_MUTUAL_TLS", target="test",
                fingerprints=dict(vdp="a" * 64, runtime="b" * 64, dashboard="c" * 64))))
        self.driver = SimpleNamespace(root=Path("/unused"), budget=lambda n: n, vm=Mock(), guest=Mock())

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


if __name__ == "__main__":
    unittest.main()
