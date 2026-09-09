# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Pure safety/regression tests. No host VM or Cloud access."""

import copy
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

from aosedge_demo_orchestrator.environment import EnvironmentError
from aosedge_demo_orchestrator.units import UnitService
from aosedge_demo_orchestrator.probes import classify_cloud_log, provisioning_forward_states
from aosedge_demo_orchestrator import unit_cloud

TEST = "11111111-1111-4111-8111-111111111111"
PROD = "22222222-2222-4222-8222-222222222222"
UNIT = "33333333-3333-4333-8333-333333333333"
NODE = "44444444-4444-4444-8444-444444444444"


class UnitSafetyTests(unittest.TestCase):
    def test_connected_initial_test_can_provision_but_not_retire(self):
        import contextlib
        self.service.environment._writer = contextlib.nullcontext
        self.service.root = Path("/unused-test-root")
        self.state.update(currentVehicle="test", source=dict(lastConnectionConfirmation=dict(role="test", serverTls=True, initialManual=True)))
        self.service._cloud = Mock(return_value=self.inventory)
        self.service._provision = Mock(return_value={"lifecycle": "ONLINE"})
        self.state["vehicles"]["test"]["unitId"] = None
        with patch("aosedge_demo_orchestrator.units.read_json", return_value=self.state):
            self.service.execute("provision", "test")
            self.service._provision.assert_called_once()
            self.service.vm._validate.assert_called_with(self.state, "start", ["test"])
            self.service._cloud.reset_mock()
            for action in ("deprovision", "delete"):
                with self.assertRaisesRegex(EnvironmentError, "DETACHED_SOURCE"):
                    self.service.execute(action, "test")
            self.service._cloud.assert_not_called()

    def setUp(self):
        self.service = UnitService(Mock())
        self.service.vm._save = Mock()
        self.service._cloud = Mock(side_effect=AssertionError("Unexpected Cloud call"))
        self.inventory = {"ownerId": UNIT, "sets": [
            {"id": TEST, "title": "Test Vehicles", "is_validation_set": True, "fleet": NODE, "members": []},
            {"id": PROD, "title": "Production Vehicles", "is_validation_set": False, "fleet": NODE, "members": []}]}
        self.state = {"vehicles": {"test": {"localVmId": TEST, "unitId": UNIT, "nodeId": NODE,
            "systemUid": "hardware-identity", "unitSetId": TEST, "cloud": {"lifecycle": "ONLINE"}}},
            "operations": [{"class": "LOCAL_CREATE", "state": "COMPLETED"}]}

    def test_roles_must_be_unique_disjoint_and_correct_types(self):
        self.assertEqual(TEST, self.service._bindings({}, self.inventory)["test"]["id"])
        for mutation in ("type", "duplicate", "fleet"):
            inventory = copy.deepcopy(self.inventory)
            if mutation == "type":
                inventory["sets"][0]["is_validation_set"] = False
            elif mutation == "duplicate":
                inventory["sets"].append(copy.deepcopy(inventory["sets"][0]))
            else:
                inventory["sets"][1]["fleet"] = UNIT
            with self.assertRaises(EnvironmentError):
                self.service._bindings({}, inventory)

    def test_online_poll_reuses_client_and_known_uuid_without_node_or_inventory_reads(self):
        cloud = Mock()
        cloud.unit.side_effect = [dict(system_uid="uid", status="provisioned", online_status=value)
                                  for value in ("Offline", "Online")]
        request = dict(action="wait", unitId=UNIT, systemUid="uid", unitSetId=TEST,
                       needNodes=False, label="CLOUD_ONLINE")
        with patch.object(unit_cloud, "Cloud", return_value=cloud) as constructor, \
                patch.object(unit_cloud.time, "sleep"):
            result = unit_cloud.execute(request)
        constructor.assert_called_once_with(request)
        self.assertEqual("Online", result["unit"]["online_status"])
        self.assertEqual(2, cloud.unit.call_count)
        self.assertTrue(all(call.kwargs == {"nodes": False} for call in cloud.unit.call_args_list))
        cloud.pages.assert_not_called()
        cloud.inventory.assert_not_called()

    def test_unknown_uuid_is_resolved_once_and_nodes_are_reused_within_wait(self):
        cloud = Mock()
        cloud.pages.return_value = [dict(id=UNIT, system_uid="uid")]
        cloud.unit.side_effect = [dict(system_uid="uid", status="provisioned", online_status="Offline", nodes=[dict(id=NODE)]),
                                  dict(system_uid="uid", status="provisioned", online_status="Online")]
        with patch.object(unit_cloud, "Cloud", return_value=cloud), patch.object(unit_cloud.time, "sleep"):
            result = unit_cloud.execute(dict(action="wait", systemUid="uid", needNodes=True, label="CLOUD_ONLINE"))
        cloud.pages.assert_called_once()
        self.assertEqual([True, False], [call.kwargs["nodes"] for call in cloud.unit.call_args_list])
        self.assertEqual(NODE, result["unit"]["nodes"][0]["id"])

    def test_inventory_limits_membership_reads_to_role_sets_and_can_skip_units(self):
        cloud = unit_cloud.Cloud.__new__(unit_cloud.Cloud)
        cloud.user = dict(ownerId=UNIT)
        cloud.require = Mock()
        cloud.pages = Mock(side_effect=[self.inventory["sets"] + [dict(id=NODE, title="Other Fleet")], [], []])
        result = cloud.inventory(include_units=False)
        self.assertEqual(2, len(result["sets"]))
        self.assertEqual(["unit-sets/", "unit-sets/" + TEST + "/units/", "unit-sets/" + PROD + "/units/"],
                         [call.args[0] for call in cloud.pages.call_args_list])

    def test_pinned_set_identity_survives_display_title_change(self):
        state = {"cloudBinding": {"ownerId": UNIT, "sets": {"test": TEST, "production": PROD}}}
        self.inventory["sets"][0]["title"] = "Renamed Test Display"
        self.assertEqual(TEST, self.service._bindings(state, self.inventory)["test"]["id"])
        state["cloudBinding"]["ownerId"] = NODE
        with self.assertRaisesRegex(EnvironmentError, "OEM_OWNER_CHANGED"):
            self.service._bindings(state, self.inventory)

    def test_delete_before_deprovision_does_not_call_cloud(self):
        with self.assertRaisesRegex(EnvironmentError, "UNIT_DEPROVISION_REQUIRED"):
            self.service._delete(self.state, "test", {})
        self.service._cloud.assert_not_called()

    def test_unassign_requires_stopped_test(self):
        with self.assertRaisesRegex(EnvironmentError, "STOPPED_TEST"):
            self.service._unassign(self.state, "test", {})
        self.service._cloud.assert_not_called()

    def test_unassign_preserves_identity_disk_and_other_memberships(self):
        item = self.state["vehicles"]["test"]
        item["runtime"] = {"state": "STOPPED"}
        before = dict(id=UNIT, system_uid="hardware-identity", status="provisioned", unit_sets=[TEST, NODE])
        after = dict(before, unit_sets=[NODE])
        self.service._cloud = Mock(side_effect=[{"unit": before}, {"httpStatus": 204}])
        self.service._wait = Mock(return_value=after)
        sets = self.service._bindings({}, self.inventory)
        result = self.service._unassign(self.state, "test", sets)
        self.assertTrue(result["localDiskRetained"])
        self.assertTrue(result["otherMembershipsUnchanged"])
        self.assertEqual(UNIT, item["unitId"])
        self.assertEqual("ONLINE", item["cloud"]["lifecycle"])
        self.assertEqual(["read", "remove"], [call.args[0] for call in self.service._cloud.call_args_list])
        self.service._cloud = Mock(return_value={"unit": after})
        self.assertTrue(self.service._unassign(self.state, "test", sets)["noOp"])
        self.assertEqual(["read"], [call.args[0] for call in self.service._cloud.call_args_list])

    def test_partial_sdk_identity_is_not_never_provisioned(self):
        self.state["vehicles"]["test"]["unitId"] = None
        with self.assertRaisesRegex(EnvironmentError, "PARTIAL_PROVISIONING"):
            self.service._delete(self.state, "test", {})

    def test_uncertain_delete_reconciles_without_repeating_mutation(self):
        self.state["vehicles"]["test"]["cloud"]["lifecycle"] = "DEPROVISIONED"
        self.state["operations"].append({"class": "UNIT_LIFECYCLE", "step": "DELETE_UNIT", "target": ["test"]})
        self.service._cloud = Mock(side_effect=[{"unit": None}, {"absent": True}])
        self.service._reconcile(self.state)
        self.assertEqual("DELETED", self.state["vehicles"]["test"]["cloud"]["lifecycle"])
        self.assertEqual(["find", "absence"], [call.args[0] for call in self.service._cloud.call_args_list])
        self.assertEqual(1, len(self.state["operations"]))

    def test_uncertain_sdk_failure_never_retries_sdk(self):
        self.state["operations"].append({"class": "UNIT_LIFECYCLE", "step": "SDK_PROVISION", "target": ["test"]})
        self.service._cloud = Mock(return_value={"unit": None})
        with self.assertRaisesRegex(EnvironmentError, "NO_RETRY"):
            self.service._reconcile(self.state)
        self.assertEqual(["find"], [call.args[0] for call in self.service._cloud.call_args_list])
        self.assertEqual(2, len(self.state["operations"]))

    def test_deprovision_stops_vm_without_reconnecting_or_reading_probe_logs(self):
        item = self.state["vehicles"]["test"]
        item["runtime"] = {"state": "RUNNING"}
        # Old journals must not resume the removed probe either.
        item["cloud"].update(credentialProbeIntent=True, oldIdentityRejected=False)
        self.service._live = Mock()
        self.service._stop_cm = Mock()
        self.service._guest_script = Mock(side_effect=AssertionError("No reconnect or probe logs"))
        self.service._wait = Mock(side_effect=[{"status": "provisioned", "online_status": "Offline"},
                                               {"status": "new", "online_status": "Offline"}])
        self.service._cloud = Mock(return_value={})
        def stopped(*args):
            item["runtime"]["state"] = "STOPPED"
            return {"state": "COMPLETED"}
        self.service.vm._stop.side_effect = stopped
        result = self.service._deprovision(self.state, "test", {})
        self.assertEqual("DEPROVISIONED", result["lifecycle"])
        self.assertNotIn("oldIdentityRejected", result)
        self.assertFalse(item["cloud"]["oldIdentityRejected"])
        self.service._guest_script.assert_not_called()
        self.service._stop_cm.assert_called_once_with(self.state, "test")
        self.assertEqual(["deprovision"], [call.args[0] for call in self.service._cloud.call_args_list])
        self.assertEqual(1, len(self.state["operations"]))

    def test_local_cleanup_rechecks_identity_and_role_sets_without_mutation(self):
        self.state["vehicles"]["test"]["cloud"]["lifecycle"] = "DELETED"
        self.state["cloudBinding"] = {"ownerId": UNIT, "sets": {"test": TEST, "production": PROD}}
        inventory = copy.deepcopy(self.inventory)
        inventory["units"] = []
        self.service._cloud = Mock(return_value={"absent": True, "inventory": inventory})
        self.assertTrue(self.service.confirm_retired(self.state))
        self.assertEqual(["absence"], [call.args[0] for call in self.service._cloud.call_args_list])
        inventory["units"] = [{"id": NODE, "system_uid": "hardware-identity"}]
        with self.assertRaisesRegex(EnvironmentError, "FRESH_CLOUD_RETIREMENT_CHECK_FAILED"):
            self.service.confirm_retired(self.state)
        inventory["units"] = []
        inventory["sets"][1]["members"] = [{"id": NODE}]
        with self.assertRaisesRegex(EnvironmentError, "FRESH_CLOUD_RETIREMENT_CHECK_FAILED"):
            self.service.confirm_retired(self.state)

    def test_diagnostics_exclude_credentials_and_raw_discovery_payload(self):
        text = 'error token=NEVER_LEAK\nerror password=NEVER_LEAK\nReceived discovery response: content={"systemId":"NEVER_LEAK"}\nConnect failed https://private.example/secret\nSent message: connected message={"data":"NEVER_LEAK"}'
        value = str(classify_cloud_log(text))
        for forbidden in ("NEVER_LEAK", "private.example", "systemId"):
            self.assertNotIn(forbidden, value)

    def test_test_retirement_preserves_production_membership_and_full_journal_on_upload_reconcile(self):
        self.state["vehicles"]["test"]["cloud"]["lifecycle"] = "DELETED"
        self.state["vehicles"]["production"] = dict(unitId=NODE, nodeId=PROD,
            systemUid="production-hardware", cloud=dict(lifecycle="ONLINE"), runtime=dict(pid=123, state="RUNNING"))
        self.state["cloudBinding"] = dict(ownerId=UNIT, sets=dict(test=TEST, production=PROD))
        self.state["shared"] = dict(dns=dict(pid=555, state="RUNNING"))
        self.state["demoLifecycle"] = dict(action="retire", target="test")
        record = dict(deploymentId=TEST, publicationPath="VERIFICATION_TEST", ownerId=UNIT,
            upload=dict(attemptStarted=True, state="RESPONDED", response=dict(httpStatus=201, deploymentId=TEST)))
        self.state["componentOperations"] = {"16.0.0": record}
        inventory = copy.deepcopy(self.inventory)
        inventory["units"] = [dict(id=NODE, system_uid="production-hardware")]
        inventory["sets"][1]["members"] = [dict(id=NODE)]
        entries = [dict(version="16.0.0", deploymentId=TEST, verificationTest=True)]
        self.service._cloud = Mock(side_effect=[dict(absent=True, inventory=inventory), dict(confirmedUploads=entries)])
        before = copy.deepcopy(self.state)
        self.assertTrue(self.service.confirm_test_retired(self.state))
        self.assertEqual(before["vehicles"]["production"], self.state["vehicles"]["production"])
        self.assertEqual(before["shared"], self.state["shared"])
        self.assertEqual(before["demoLifecycle"], self.state["demoLifecycle"])
        self.service.vm._save.assert_called_once_with(self.state)
        self.service._cloud.assert_any_call("absence", unitId=UNIT, nodeId=NODE)
        self.assertEqual("CONFIRMED", record["upload"]["state"])

    def test_retire_reconciles_known_upload_without_replaying_or_reading_deleted_unit(self):
        self.state["cloudBinding"] = {"ownerId": UNIT}
        self.state["vehicles"] = {}
        record = dict(deploymentId=TEST, batchId=PROD,
            upload=dict(attemptStarted=True, state="RESPONDED", response=dict(httpStatus=201, deploymentId=TEST)),
            approve=dict(state="CONFIRMED", response=dict(batchId=PROD)))
        self.state["componentOperations"] = {"12.0.0": record}
        entries = [dict(version="12.0.0", deploymentId=TEST, batchId=PROD)]
        self.service._cloud = Mock(return_value={"confirmedUploads": entries})
        self.assertTrue(self.service.confirm_retired(self.state))
        self.service._cloud.assert_called_once_with("reconcile-uploads", uploads=entries)
        self.assertEqual("PUBLICATION_ONLY", record["upload"]["reconciliationScope"])
        self.assertEqual("CONFIRMED", record["upload"]["state"])
        self.service.vm._save.assert_called_once_with(self.state)
        self.service._cloud.reset_mock()
        self.assertTrue(self.service.confirm_retired(self.state))
        self.service._cloud.assert_not_called()

    def test_retire_upload_missing_identity_or_proof_stays_unresolved(self):
        self.state.update(vehicles={}, cloudBinding={"ownerId": UNIT})
        original = dict(deploymentId=TEST, batchId=PROD,
            upload=dict(attemptStarted=True, state="RESPONDED", response=dict(httpStatus=201, deploymentId=TEST)),
            approve=dict(state="CONFIRMED", response=dict(batchId=PROD)))
        for failure in ("missing", "mismatch", "uncertain", "approval", "unavailable", "wrong-proof"):
            with self.subTest(failure=failure):
                record = copy.deepcopy(original)
                if failure == "missing":
                    record.pop("deploymentId")
                elif failure == "mismatch":
                    record["upload"]["response"]["deploymentId"] = NODE
                elif failure == "uncertain":
                    record["upload"]["state"] = "UNCERTAIN"
                elif failure == "approval":
                    record["approve"]["state"] = "RESPONDED"
                self.state["componentOperations"] = {"12.0.0": record}
                self.service._cloud = Mock(side_effect=EnvironmentError("CLOUD_UNAVAILABLE")) if failure == "unavailable" else Mock(return_value={"confirmedUploads": []})
                before = copy.deepcopy(self.state)
                with self.assertRaises(EnvironmentError):
                    self.service.confirm_retired(self.state)
                self.assertEqual(before, self.state)
                self.service.vm._save.assert_not_called()
                if failure not in ("unavailable", "wrong-proof"):
                    self.service._cloud.assert_not_called()

    def test_retire_verification_upload_has_no_approval_dependency(self):
        self.state.update(vehicles={}, cloudBinding={"ownerId": UNIT})
        record = dict(deploymentId=TEST, publicationPath="VERIFICATION_TEST", ownerId=UNIT,
            upload=dict(attemptStarted=True, state="RESPONDED", response=dict(httpStatus=201, deploymentId=TEST)))
        self.state["componentOperations"] = {"16.0.0": record}
        entries = [dict(version="16.0.0", deploymentId=TEST, verificationTest=True)]
        self.service._cloud = Mock(return_value=dict(confirmedUploads=entries))
        self.assertTrue(self.service.confirm_retired(self.state))
        self.service._cloud.assert_called_once_with("reconcile-uploads", uploads=entries)
        self.assertEqual("CONFIRMED", record["upload"]["state"])
        self.assertNotIn("approve", record)
        record["ownerId"] = NODE
        record["upload"]["state"] = "RESPONDED"
        with self.assertRaisesRegex(EnvironmentError, "PUBLICATION_OWNER_CHANGED"):
            self.service.confirm_retired(self.state)

    def test_upload_reconciliation_worker_is_read_only_exact_and_owner_scoped(self):
        from aosedge_demo_orchestrator.component_cloud import COMPONENT, COMPONENT_ID
        entry = dict(version="12.0.0", deploymentId=TEST, batchId=PROD)
        bundle = dict(id=TEST, state="done", items=[dict(codename=COMPONENT, version="12.0.0")])
        batch = dict(id=PROD, oem_id=UNIT, architectures=["arm64"],
            update_items=[dict(identity_id=COMPONENT_ID, codename=COMPONENT, version="12.0.0")])
        for failure in (None, "missing", "duplicate", "state", "component", "version", "owner", "batch"):
            with self.subTest(failure=failure):
                bundles, detail = [copy.deepcopy(bundle)], copy.deepcopy(batch)
                if failure == "missing":
                    bundles = []
                elif failure == "duplicate":
                    bundles *= 2
                elif failure == "state":
                    bundles[0]["state"] = "error"
                elif failure in ("component", "version"):
                    bundles[0]["items"][0]["codename" if failure == "component" else "version"] = "wrong"
                elif failure == "owner":
                    detail["oem_id"] = NODE
                elif failure == "batch":
                    detail["id"] = NODE
                cloud = Mock(user={"ownerId": UNIT})
                cloud.pages.return_value, cloud.call.return_value = bundles, detail
                with patch.object(unit_cloud, "Cloud", return_value=cloud):
                    if failure:
                        with self.assertRaises(unit_cloud.CloudFailure):
                            unit_cloud.execute(dict(action="reconcile-uploads", uploads=[entry]))
                    else:
                        self.assertEqual({"confirmedUploads": [entry]}, unit_cloud.execute(dict(action="reconcile-uploads", uploads=[entry])))
                cloud.pages.assert_called_once_with("deployment-bundles/")
                for call in cloud.call.call_args_list:
                    self.assertEqual(("verification-batch/" + PROD + "/",), call.args)
                    self.assertEqual({}, call.kwargs)  # GET only; never POST/DELETE.
                cloud.unit.assert_not_called()
                cloud.inventory.assert_not_called()

    def test_forward_removal_allows_draining_connection_but_not_listener(self):
        self.service._live = Mock()
        self.service.vm._paths.return_value = ["fixture.qmp"]
        for label in ("CLOSE_WAIT", "TIME_WAIT", "ESTABLISHED"):
            table = "  TCP[" + label + "]  10 127.0.0.1 18089 10.0.0.100 8089 0 0\n"
            self.assertEqual([label], provisioning_forward_states(table, 18089))
            with patch("aosedge_demo_orchestrator.units.qmp", side_effect=["host forwarding rule removed", table]):
                self.service._forward(self.state, "test", False)
        table = " TCP[HOST_FORWARD] 10 127.0.0.1 18089 10.0.0.100 8089 0 0\n"
        with patch("aosedge_demo_orchestrator.units.qmp", side_effect=["removed", table]), self.assertRaisesRegex(EnvironmentError, "POSTCONDITION"):
            self.service._forward(self.state, "test", False)

    def test_runtime_abort_diagnostics_keep_fixed_signal_and_termination(self):
        value = classify_cloud_log("terminate called without an active exception\naos-cm.service: Main process exited, code=dumped, status=6/ABRT\naos-cm.service: Failed with result 'core-dump'.")
        self.assertEqual([("dumped", "6/ABRT")], value["serviceExits"])
        self.assertEqual(1, value["RUNTIME_TERMINATION"])
        self.assertTrue(any("terminate called" in line for line in value["redactedConnectionEvents"]))

    def test_payload_embedded_abort_is_not_a_local_process_exit(self):
        from aosedge_demo_orchestrator.probes import classify_start_context
        text = ('Received message: content={"log":"aos-cm.service: Main process exited, code=dumped, status=6/ABRT; '
                'GRPC_CALL_ERROR_TOO_MANY_OPERATIONS; assertion failed: false; terminate called without an active exception"}\n')
        log = classify_cloud_log(text)
        context = classify_start_context(text)
        self.assertEqual([], log["serviceExits"])
        self.assertNotIn("RUNTIME_TERMINATION", log)
        self.assertEqual(1, log["payloadRecordsExcluded"])
        self.assertEqual([], context["grpcCallErrors"])
        self.assertFalse(context["assertionFailedFalse"])
        self.assertFalse(context["terminationWithoutException"])
        mixed = classify_cloud_log(text + "aos-cm.service: Main process exited, code=dumped, status=6/ABRT\n")
        self.assertEqual([("dumped", "6/ABRT")], mixed["serviceExits"])
        self.assertEqual([{"embeddedPayload": False, "systemdCmExitLine": True}], mixed["serviceExitContexts"])

    def test_start_context_projects_only_stage_and_stack_symbol(self):
        from aosedge_demo_orchestrator.probes import classify_start_context
        text = "[ 12.250] vm aos-cm[23]: (iamclient) Get certificate: key=SECRET (iamclient.cpp:42)\n/usr/bin/aos-cm(_ZN3aos2cm3AppEv+0x4)[0xabcdef]\n/var/secret/user-file(+0xa)[0x123]\nterminate called without an active exception\n"
        value = classify_start_context(text)
        self.assertTrue(value["terminationWithoutException"])
        self.assertEqual([{"module": "aos-cm", "symbolOffset": "_ZN3aos2cm3AppEv+0x4"}], value["frames"])
        self.assertEqual("Get certificate", value["stages"][0]["stage"])
        self.assertEqual(12.25, value["stages"][0]["bootSeconds"])
        for secret in ("SECRET", "user-file", "/usr/bin", "0xabcdef"):
            self.assertNotIn(secret, str(value))
        payload = classify_start_context('message={"value":"(iamclient) Get PRIVATESECRET: /usr/bin/aos_cm_app(SECRET+0xa)[0x123]"}')
        self.assertEqual([], payload["stages"])
        self.assertEqual([], payload["frames"])

    def test_start_context_keeps_grpc_api_misuse_without_payload(self):
        from aosedge_demo_orchestrator.probes import classify_start_context
        value = classify_start_context("call_op_set.h:975 API misuse of type GRPC_CALL_ERROR_TOO_MANY_OPERATIONS observed\ncall_op_set.h:977 assertion failed: false\n/usr/bin/aos_cm_app(+0xb20)[0xabc]\n")
        self.assertEqual(["GRPC_CALL_ERROR_TOO_MANY_OPERATIONS"], value["grpcCallErrors"])
        self.assertTrue(value["assertionFailedFalse"])
        self.assertEqual(["call_op_set.h:975", "call_op_set.h:977"], value["grpcAssertionLocations"])
        self.assertEqual("aos_cm_app", value["frames"][0]["module"])

    def test_delete_uses_cloud_deprovision_proof_not_old_identity_flag(self):
        item = self.state["vehicles"]["test"]
        item.update(runtime={"state": "STOPPED"}, overlay=".local/demo-current/validation.qcow2")
        item["cloud"]["lifecycle"] = "DEPROVISIONED"
        self.state["cloudBinding"] = {"ownerId": UNIT, "sets": {"test": TEST, "production": PROD}}
        self.service.root = Path("/fixture")
        self.service._cloud = Mock(side_effect=[
            {"unit": {"status": "new", "online_status": "Offline", "unit_sets": []}}, {},
            {"absent": True, "inventory": self.inventory}])
        result = self.service._delete(self.state, "test", {})
        self.assertEqual("DELETED", result["lifecycle"])
        self.assertEqual(["read", "delete", "absence"], [call.args[0] for call in self.service._cloud.call_args_list])
        self.assertNotIn("oldIdentityRejected", item["cloud"])


if __name__ == "__main__":
    unittest.main()
