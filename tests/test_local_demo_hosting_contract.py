# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_ROOT = ROOT / "contracts" / "local-demo-hosting"


def load(name: str) -> dict:
    return json.loads((CONTRACT_ROOT / name).read_text(encoding="utf-8"))


class LocalDemoHostingContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profile = load("local-demo-hosting-profile.v1.json")
        cls.preflight = load("fixtures/hosting-preflight.valid.json")

    def test_design_reviewed_and_no_demo_build(self) -> None:
        self.assertEqual("D4-020", self.profile["decision"])
        self.assertEqual("DESIGN_REVIEWED", self.profile["lifecycleState"])
        presentation = self.profile["presentation"]
        self.assertFalse(presentation["buildDuringDemoAllowed"])
        self.assertFalse(presentation["pullDuringDemoAllowed"])
        self.assertFalse(presentation["repackageDuringDemoAllowed"])
        self.assertIn("--no-build", presentation["requiredComposeInvocation"])
        self.assertIn("never", presentation["requiredComposeInvocation"])
        self.assertFalse(presentation["softwareDeliveryDashboardStoresAuthoritativeLifecycleState"])
        self.assertEqual("AOSCLOUD", presentation["authoritativeLifecycleStateSource"])
        self.assertEqual("NATIVE_DEMO_ORCHESTRATOR", presentation["currentRunJournalOwner"])

    def test_container_ports_volumes_and_profiles_are_distinct(self) -> None:
        containers = self.profile["containers"]
        self.assertEqual(3, len(containers))
        self.assertEqual(3, len({item["name"] for item in containers}))
        self.assertEqual(3, len({item["uiBind"] for item in containers}))
        function_products = [item for item in containers if item["id"].endswith("CLOUD")]
        self.assertEqual(2, len({item["ingestionBind"] for item in function_products}))
        self.assertEqual(2, len({item["persistentVolume"] for item in function_products}))
        self.assertEqual({"brake-sp1", "tire-sp2"}, {item["helperProfile"] for item in function_products})
        self.assertTrue(all(item["guestUrl"].startswith("http://10.0.0.1:") for item in function_products))
        self.assertTrue(all("functionalCredentialResource" not in item for item in function_products))

    def test_browser_and_containers_never_receive_protected_artifact_credentials(self) -> None:
        security = self.profile["localDemoContainerMinimumSecurityHygiene"]
        self.assertEqual("LOCAL_TRUSTED_MACOS_DEMO_ONLY", security["scope"])
        self.assertFalse(security["productionDeploymentArchitectureClaimed"])
        self.assertTrue(security["loopbackOnlyPublishedPorts"])
        self.assertFalse(security["privilegedModeAllowed"])
        self.assertFalse(security["hostNetworkAllowed"])
        self.assertFalse(security["dockerSocketMountAllowed"])
        self.assertFalse(security["broadHostFilesystemMountAllowed"])
        self.assertFalse(security["protectedP12MountAllowed"])
        self.assertFalse(security["realCredentialsEmbeddedInImagesOrFrontendAllowed"])
        self.assertFalse(security["browserReceivesCredentialOrHelperCapability"])
        self.assertTrue(security["functionDataVolumesSeparated"])
        self.assertIn("READ_ONLY_ROOT_FILESYSTEM", security["notRequiredForFirstDemo"])
        self.assertIn("PRODUCTION_GRADE_CONTAINER_SECURITY_QUALIFICATION", security["notRequiredForFirstDemo"])
        helper = self.profile["nativeHelper"]
        self.assertFalse(helper["browserAccessAllowed"])
        self.assertFalse(helper["callerMaySelectCredentialPath"])
        self.assertFalse(helper["callerMaySelectProfile"])
        self.assertTrue(helper["protectedCredentialsRemainOutsideGitDockerVmImagesAndArtifacts"])

    def test_guest_route_is_loopback_backed_and_backend_security_is_out_of_scope(self) -> None:
        route = self.profile["qemuGuestRoute"]
        self.assertTrue(route["bothVmsMayRunConcurrently"])
        self.assertTrue(route["eachVmUsesIndependentNetworkNamespace"])
        self.assertEqual("10.0.0.1", route["guestVisibleHost"])
        self.assertTrue(route["sameGuestAddressAcrossIndependentNetworksAllowed"])
        self.assertTrue(route["hostSideControlEndpointsMustBeUniquePerVm"])
        self.assertEqual("EXACTLY_ONE_VM_AT_A_TIME", route["carlaGatewayLiveSourceAssignment"])
        self.assertTrue(route["sharedFunctionalBackendsAcceptConcurrentVmClients"])
        self.assertEqual("system_uid", route["backendCorrelationField"])
        self.assertFalse(route["sourceIpIsAuthenticatedUnitIdentity"])
        self.assertTrue(route["hostBrowserAndIngestionBindsAreLoopbackOnly"])
        self.assertFalse(route["hostfwdForFunctionalIngestionRequired"])
        self.assertEqual("TO_BE_PROVEN_WITH_BOTH_VMS", route["routeQualificationState"])
        connectivity = route["vehicleExternalConnectivityControl"]
        self.assertEqual(1, connectivity["controlCount"])
        self.assertEqual("CURRENTLY_SELECTED_VEHICLE_ONLY", connectivity["scope"])
        self.assertEqual("D4-022.1_DUAL_NETWORK_QMP_EXTERNAL_LINK", connectivity["mechanismDecision"])
        self.assertTrue(connectivity["vehicleVissGatewayPlaneRemainsUp"])
        self.assertTrue(connectivity["externalCloudAndFunctionBackendPlaneChangesTogether"])
        self.assertEqual(
            {"UNIT_TO_AOSCLOUD", "BRAKE_SERVICE_TO_BACKEND", "TIRE_SERVICE_TO_BACKEND"},
            set(connectivity["disconnects"]),
        )
        self.assertIn("MAC_DASHBOARD_TO_AOSCLOUD", connectivity["preserves"])
        transport = self.profile["functionalBackendTransport"]
        self.assertEqual("ONE_CONTROLLED_DEMO_MAC", transport["trustedEnvironment"])
        self.assertEqual("HTTP_1_1", transport["protocol"])
        self.assertFalse(transport["clientAuthenticationRequired"])
        self.assertFalse(transport["perUnitCredentialLifecycleRequired"])
        self.assertFalse(transport["productionBackendSecurityClaimed"])
        self.assertTrue(transport["localRouteTrustIsNotProductionAuthentication"])
        self.assertEqual("CORRELATION_ONLY_NOT_AUTHENTICATED_IDENTITY", transport["systemUidUsage"])
        self.assertTrue(transport["separateApiNamespacePerFunctionTeam"])
        self.assertTrue(transport["crossFunctionMessageSchemaRejected"])
        self.assertTrue(transport["doesNotChangeSotaIamKuksaOrGatewaySecurity"])

    def test_native_helper_is_session_scoped_role_bound_and_non_authoritative(self) -> None:
        helper = self.profile["nativeHelper"]
        self.assertEqual("CURRENT_NON_ROOT_MACOS_USER", helper["runsAs"])
        self.assertEqual("DEMO_LAUNCHER_PROCESS_GROUP", helper["supervisor"])
        self.assertFalse(helper["launchdInstallRequired"])
        self.assertEqual("127.0.0.1:18600", helper["bind"])
        self.assertEqual("SEPARATE_MODE_0400_FILE_PER_CONTAINER_BACKEND", helper["sessionCapabilityDelivery"])
        self.assertEqual({"platform-oem", "brake-sp1", "tire-sp2"}, {item["id"] for item in helper["profiles"]})
        self.assertFalse(helper["callerMaySelectCloudUrl"])
        self.assertFalse(helper["callerMaySelectHttpMethodOrApiPath"])
        self.assertFalse(helper["callerMayRequestArbitraryShellCommand"])
        self.assertFalse(helper["storesLifecycleAuthorityState"])
        self.assertTrue(helper["publishedRequiresIndependentCloudRead"])
        self.assertEqual("UNCERTAIN", helper["ambiguousMutationState"])
        self.assertFalse(helper["blindRetryAllowed"])
        self.assertTrue(helper["terminationDeletesSessionCapabilities"])

    def test_observed_host_baseline_and_preflight_agree(self) -> None:
        baseline = self.profile["qualifiedHostCandidate"]
        for field in ("architecture", "dockerDesktopVersion", "dockerEngineVersion", "dockerComposeVersion", "qemuVersion"):
            self.assertEqual(baseline[field], self.preflight[field])
        self.assertEqual("PASS", self.preflight["result"])
        self.assertTrue(self.preflight["lanListenersAbsent"])
        self.assertEqual("26.5.2", baseline["observedMacosVersion"])
        self.assertFalse(baseline["exactMacosVersionIsUniversalGate"])
        self.assertEqual(["11.0.3", "11.1.0"], baseline["qualifiedQemuVersions"])
        policy = self.profile["hostQualificationPolicy"]
        self.assertEqual("QUALIFIED", policy["officialDemoRequires"])
        self.assertEqual("COMPATIBLE_UNQUALIFIED", policy["developmentMayUse"])
        self.assertFalse(policy["engineeringOverrideAllowedDuringOfficialPresentation"])
        self.assertFalse(policy["newVersionRequiresContainerRebuild"])

    def test_startup_shutdown_and_qualification_gates_are_explicit(self) -> None:
        startup = self.profile["startup"]
        self.assertEqual("LOCAL_DEMO_SUPPORT_STACK_ONLY", startup["scope"])
        self.assertFalse(startup["vmProvisioningOrCloudLifecycleIncluded"])
        self.assertEqual(
            ["PREFLIGHT", "NATIVE_HELPER", "CONTAINERS", "HEALTHCHECKS", "BROWSER_SURFACES"],
            startup["order"],
        )
        self.assertTrue(startup["partialStartupCleanupRequired"])
        shutdown = self.profile["shutdown"]
        self.assertFalse(shutdown["partialStartupFailureDeletesFunctionalData"])
        self.assertTrue(shutdown["persistentFunctionalVolumesRetainedUntilR0"])
        self.assertTrue(shutdown["r0UsesExactBackendCleanupBeforeVolumeReset"])
        self.assertFalse(shutdown["dockerVolumeDeletionDuringNormalShutdownAllowed"])
        self.assertFalse(shutdown["historicalDemoRunArchiveRequired"])
        self.assertFalse(shutdown["postShutdownHelperSessionCapabilitiesAndListenersRemain"])
        self.assertEqual(
            {
                "CLEAN_STARTUP",
                "SAFE_PARTIAL_STARTUP_FAILURE",
                "CONTAINER_RESTART_PRESERVES_CURRENT_DATA",
                "HELPER_LOSS_BLOCKS_PROTECTED_ACTIONS",
                "NORMAL_SHUTDOWN_RETAINS_FUNCTION_DATA",
                "R0_CLEANS_ONLY_CURRENT_DEMO_STATE",
                "NO_POST_SHUTDOWN_HELPER_CAPABILITY_OR_LISTENER",
                "BOTH_VMS_FUNCTION_BACKEND_ROUTE",
                "LAN_LISTENER_ABSENT",
            },
            set(self.profile["implementationQualificationGates"]),
        )


if __name__ == "__main__":
    unittest.main()
