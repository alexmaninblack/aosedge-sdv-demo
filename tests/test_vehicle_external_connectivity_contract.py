# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "contracts" / "vehicle-external-connectivity" / "vehicle-external-connectivity-profile.v1.json"


class VehicleExternalConnectivityContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profile = json.loads(PROFILE.read_text(encoding="utf-8"))

    def test_accepted_subdecisions_do_not_accept_the_package(self) -> None:
        self.assertEqual("D4-022", self.profile["decision"])
        self.assertEqual("DESIGN_REVIEWED", self.profile["lifecycleState"])
        self.assertEqual(
            {"D4-022.1", "D4-022.2", "D4-022.3", "D4-022.4"},
            {item["id"] for item in self.profile["acceptedSubdecisions"]},
        )

    def test_only_selected_vehicle_external_plane_is_controlled(self) -> None:
        target = self.profile["target"]
        self.assertEqual("CURRENTLY_SELECTED_VEHICLE_ROLE_FROM_CURRENT_RUN_JOURNAL", target["selector"])
        self.assertEqual({"VALIDATION", "PRODUCTION"}, set(target["allowedRoles"]))
        self.assertFalse(target["otherRunningVmAffected"])
        planes = self.profile["networkPlanes"]
        self.assertFalse(planes["vehicle"]["defaultRouteAllowed"])
        self.assertFalse(planes["vehicle"]["cloudDnsAllowed"])
        self.assertTrue(planes["vehicle"]["remainsUpDuringExternalConnectivityFault"])
        self.assertTrue(planes["external"]["ownsDefaultRouteAndDns"])
        self.assertTrue(planes["external"]["qmpLinkControlAllowed"])

    def test_native_helper_uses_exact_qmp_operation_without_firewall_or_aoscore_change(self) -> None:
        control = self.profile["controlMechanism"]
        self.assertEqual("QMP_SET_LINK_EXTERNAL_NET_ONLY", control["operation"])
        self.assertEqual("NATIVE_HELPER_FIXED_ALLOWLIST_OPERATION", control["caller"])
        self.assertTrue(control["qmpSocketSelectedFromCurrentJournal"])
        self.assertFalse(control["browserReceivesQmpSocketOrArbitraryCommand"])
        self.assertTrue(control["qmpAndSerialRemainOutOfBand"])
        self.assertFalse(control["macosFirewallRuleRequired"])
        self.assertFalse(control["guestFirewallMutationRequired"])
        impact = self.profile["implementationImpact"]
        self.assertFalse(impact["upstreamAosCoreSourceChangeRequired"])
        self.assertTrue(impact["oemDemoFactoryImageNetworkConfigurationChangeRequired"])
        self.assertTrue(impact["qemuLauncherChangeRequired"])
        self.assertTrue(impact["preSopOemConfiguration"])

    def test_ui_success_requires_complete_independent_probe_sets(self) -> None:
        ui = self.profile["uiAndProbeStateMachine"]
        self.assertEqual(
            {"ONLINE", "TRANSITIONING", "OFFLINE", "RECOVERING", "FAILED_PARTIAL"},
            set(ui["states"]),
        )
        self.assertTrue(ui["singleVisibleControl"])
        self.assertFalse(ui["perChannelControlsExposed"])
        self.assertTrue(ui["buttonDisabledDuringTransitionOrRecovery"])
        self.assertFalse(ui["singleProbeMayDeclareSuccess"])
        self.assertIn("SELECTED_UNIT_AOSCLOUD_OFFLINE", ui["offlineRequires"])
        self.assertIn("SAME_EVENT_REACHED_LOCAL_VISS_KUKSA_ANALYTICS", ui["offlineRequires"])
        self.assertIn("OTHER_VM_EXTERNAL_LINK_AND_CLOUD_STATE_UNCHANGED", ui["offlineRequires"])
        self.assertIn("NO_FABRICATED_CURRENT_RESULT", ui["functionDashboardOfflinePresentation"])
        self.assertIn("SAME_UNIT_UUID_AND_SYSTEM_UID_AOSCLOUD_ONLINE", ui["recoveredOnlineRequires"])
        self.assertIn("NO_REPROVISION_REINSTALL_OR_SERVICE_RESTART", ui["recoveredOnlineRequires"])
        self.assertEqual("FAILED_PARTIAL", ui["anyMismatchState"])
        self.assertEqual("PRODUCTION", ui["normativePresentationRole"])

    def test_transition_is_desired_state_idempotent_and_restart_safe(self) -> None:
        transition = self.profile["transitionAndRecovery"]
        self.assertEqual("SET_EXACT_DESIRED_STATE_NEVER_TOGGLE", transition["commandSemantics"])
        self.assertEqual("PROBE_THEN_IDEMPOTENT_NO_OP", transition["sameDesiredStateRequest"])
        self.assertTrue(transition["intentJournaledBeforeQmp"])
        self.assertIn("LAST_CONFIRMED_STATE", transition["intentJournalFields"])
        self.assertIn("DESIRED_STATE", transition["intentJournalFields"])
        self.assertFalse(transition["lostQmpResponse"]["treatedAsSuccess"])
        self.assertFalse(transition["lostQmpResponse"]["automaticBlindRetryAllowed"])
        self.assertTrue(transition["lostQmpResponse"]["reconcileAllAcceptedProbesFirst"])
        self.assertFalse(
            transition["restartDuringTransition"]["mutationBeforeJournalAndProbeReconciliationAllowed"]
        )

    def test_compensation_and_recovery_fail_closed(self) -> None:
        transition = self.profile["transitionAndRecovery"]
        self.assertEqual("LAST_CONFIRMED_STATE", transition["compensation"]["target"])
        self.assertTrue(transition["compensation"]["sameExactSelectorRequired"])
        self.assertEqual(
            "FAILED_PARTIAL",
            transition["compensation"]["failedOrUnprovenCompensationState"],
        )
        self.assertTrue(transition["recovery"]["sameUnitAndInstalledGraphRequired"])
        self.assertEqual("BOUNDED_IDEMPOTENT", transition["recovery"]["queuedMessageSynchronization"])
        self.assertFalse(transition["timeouts"]["unboundedWaitAllowed"])
        self.assertEqual(5, transition["timeouts"]["qmpAcknowledgementSeconds"])
        self.assertEqual("FAILED_PARTIAL", transition["timeouts"]["timeoutState"])

    def test_qemu_capability_does_not_invent_a_link_query(self) -> None:
        evidence = self.profile["transitionAndRecovery"]["qemuCapabilityEvidence"]
        self.assertTrue(evidence["setLinkSupported"])
        self.assertFalse(evidence["dedicatedQueryNetdevSupported"])
        self.assertFalse(evidence["queryRxFilterReportsLinkState"])
        self.assertFalse(evidence["singleQemuQueryMayDeclareSuccess"])

    def test_live_qualification_covers_both_roles_and_keeps_acceptance_open(self) -> None:
        qualification = self.profile["qualificationPlan"]
        self.assertTrue(qualification["designPlanAccepted"])
        self.assertEqual(
            "OPEN_GATE_AFTER_IMPLEMENTATION",
            qualification["implementationAndLiveEvidenceState"],
        )
        self.assertEqual(2, qualification["liveCyclesPerRole"])
        self.assertEqual({"VALIDATION", "PRODUCTION"}, set(qualification["liveRoles"]))
        self.assertIn(
            "NEW_DETERMINISTIC_CARLA_EVENT_AFTER_DISCONNECT",
            qualification["eachOfflineCycleRequires"],
        )
        self.assertIn(
            "NO_REPROVISION_REINSTALL_OR_SERVICE_RESTART",
            qualification["eachRestoreCycleRequires"],
        )
        self.assertIn("LOST_QMP_RESPONSE", qualification["controlledNegativeCases"])
        self.assertIn(
            "FAILED_OR_UNPROVEN_COMPENSATION",
            qualification["controlledNegativeCases"],
        )
        self.assertFalse(qualification["boundQualification"]["audiencePerformanceKpi"])
        self.assertFalse(qualification["boundQualification"]["unboundedWaitAllowed"])
        self.assertEqual("ONE_SANITIZED_QUALIFICATION_RECORD", qualification["retainedEvidence"])
        self.assertFalse(qualification["ordinaryDemoRunHistoryRetained"])


if __name__ == "__main__":
    unittest.main()
