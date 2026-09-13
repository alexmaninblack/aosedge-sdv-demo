# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import json
import unittest
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from aosedge_demo_orchestrator import source_guest as guest
from aosedge_demo_orchestrator.cli import build_parser, request_from_arguments
from aosedge_demo_orchestrator.connectivity import ConnectivityService
from aosedge_demo_orchestrator.environment import EnvironmentError

OWNER = "11111111-1111-4111-8111-111111111111"


def packet_allowed(chain, interface="eth0", address="8.8.8.8", sport=50000, dport=443, ipv6=False, incoming=False):
    for rule in guest.external_rules():
        if rule["chain"] != chain:
            continue
        match = True
        for expr in rule["expr"]:
            if "match" not in expr:
                if match:
                    return "accept" in expr
                break
            expected = expr["match"]
            left = expected["left"]
            if "meta" in left:
                key = left["meta"]["key"]
                actual = "aosbr0" if chain == "forward" and key == ("oifname" if incoming else "iifname") else interface
            else:
                payload = left["payload"]
                actual = None if ipv6 and payload["protocol"] == "ip" else (
                    address if payload["field"] in ("daddr", "saddr") else sport if payload["field"] == "sport" else dport)
            match = match and actual == expected["right"]
    return True


class ConnectivityTests(unittest.TestCase):
    def setUp(self):
        self.profile = dict(defaultRoutes=[dict(interface="enp0s2", gateway="10.0.0.1", mac="02:11:22:33:44:55")],
            maintenancePeer="10.0.0.1", maintenanceAddress="10.0.0.100", maintenancePort="22")
        mocked = patch.object(guest, "external_profile", return_value=self.profile)
        mocked.start()
        self.addCleanup(mocked.stop)

    def request(self, action):
        return dict(action="connectivity-" + action, vehicle=dict(localVmId=OWNER, mac="02:11:22:33:44:55"))

    def test_cli_current_and_explicit_recovery(self):
        for action in ("status", "on", "off"):
            request = request_from_arguments(build_parser().parse_args(["vehicle", "connectivity", action]))
            self.assertEqual("connectivity-" + action, request.action)
            self.assertIsNone(request.target)
        request = request_from_arguments(build_parser().parse_args(["vehicle", "connectivity", "on", "--target", "test"]))
        self.assertEqual("test", request.target.value)

    def test_public_traffic_and_host_backend_blocked(self):
        for chain in ("input", "output", "forward"):
            for address in ("8.8.8.8", "10.0.0.1", "10.0.0.2"):
                self.assertFalse(packet_allowed(chain, address=address))
            self.assertFalse(packet_allowed(chain, ipv6=True))
        self.assertFalse(packet_allowed("output", address="10.0.0.1", dport=18053))
        self.assertFalse(packet_allowed("output", address="10.0.0.1", dport=22))

    def test_local_interfaces_viss_and_control_preserved(self):
        for chain in ("input", "output", "forward"):
            self.assertTrue(packet_allowed(chain, interface="lo"))
            self.assertTrue(packet_allowed(chain, interface="aosbr0"))
        for port in (6443, 16443):
            self.assertTrue(packet_allowed("output", address="10.0.0.1", dport=port))
            self.assertTrue(packet_allowed("input", address="10.0.0.1", sport=port))
            self.assertTrue(packet_allowed("forward", address="10.0.0.1", dport=port))
            self.assertTrue(packet_allowed("forward", address="10.0.0.1", sport=port, incoming=True))
        self.assertFalse(packet_allowed("forward", incoming=True))
        self.assertFalse(packet_allowed("forward", incoming=True, ipv6=True))
        self.assertTrue(packet_allowed("output", address="10.0.0.1", sport=22))
        self.assertTrue(packet_allowed("input", address="10.0.0.1", dport=22))

    def test_status_and_repeated_actions_do_not_mutate(self):
        for state, action in (("ON", "status"), ("OFF", "status"), ("ON", "on"), ("OFF", "off")):
            with patch.object(guest, "external_state", return_value=state), patch.object(guest, "command") as command:
                self.assertTrue(guest.external_connectivity(self.request(action))["noOp"])
                command.assert_not_called()

    def test_off_is_one_atomic_transaction_after_supported_path(self):
        calls = []
        def run(argv, **kwargs):
            calls.append((argv, kwargs))
            return SimpleNamespace(returncode=0, stdout=json.dumps([dict(dev="eth0", gateway="10.0.0.1")]))
        with patch.object(guest, "external_state", side_effect=["ON", "OFF"]), patch.object(guest, "command", side_effect=run), patch.dict(guest.os.environ, SSH_CONNECTION="10.0.0.1 50000 10.0.0.100 22"):
            self.assertEqual("OFF", guest.external_connectivity(self.request("off"))["state"])
        self.assertEqual(1, len(calls))
        self.assertEqual(["nft", "-j", "-f", "-"], calls[0][0])
        entries = json.loads(calls[0][1]["input"])["nftables"]
        self.assertEqual(3, sum("chain" in x["add"] for x in entries))
        self.assertTrue(all("add" in x for x in entries))

    def test_off_rejects_unknown_ssh_path_without_filter_write(self):
        self.profile["maintenancePeer"] = "1.2.3.4"
        with patch.object(guest, "external_state", return_value="ON"), patch.object(guest, "command", return_value=SimpleNamespace(returncode=0, stdout='[{"dev":"eth0","gateway":"10.0.0.1"}]')) as command, patch.dict(guest.os.environ, SSH_CONNECTION="1.2.3.4 50000 10.0.0.100 22"):
            with self.assertRaisesRegex(ValueError, "LOCAL_PATH_NOT_SUPPORTED"):
                guest.external_connectivity(self.request("off"))
            command.assert_not_called()

    def test_off_rejects_wrong_mac_without_filter_write(self):
        self.profile["defaultRoutes"][0]["mac"] = "02:ff:ff:ff:ff:ff"
        with patch.object(guest, "command") as command:
            with self.assertRaisesRegex(ValueError, "LOCAL_PATH_NOT_SUPPORTED"):
                guest.external_connectivity(self.request("off"))
            command.assert_not_called()

    def test_on_deletes_only_owned_table(self):
        with patch.object(guest, "external_state", side_effect=["OFF", "ON"]), patch.object(guest, "command", return_value=SimpleNamespace(returncode=0)) as command:
            guest.external_connectivity(self.request("on"))
            self.assertEqual({"nftables": [{"delete": {"table": {"family": "inet", "name": guest.EXTERNAL_TABLE}}}]}, json.loads(command.call_args.kwargs["input"]))

    def test_foreign_or_modified_table_is_never_deleted(self):
        with patch.object(guest, "external_state", side_effect=ValueError("EXTERNAL_LINK_OWNER_OR_RULES_CONFLICT")), patch.object(guest, "command") as command:
            with self.assertRaisesRegex(ValueError, "OWNER_OR_RULES_CONFLICT"):
                guest.external_connectivity(self.request("on"))
            command.assert_not_called()

    def test_execute_routes_to_external_filter_not_source_gate(self):
        with patch.object(guest, "external_connectivity", return_value={"state": "ON"}) as operation:
            self.assertEqual({"state": "ON"}, guest.execute(self.request("status")))
            operation.assert_called_once()


class ConnectivityServiceTests(unittest.TestCase):
    def setUp(self):
        self.state = dict(currentVehicle="test", source=dict(state="RUNNING"), vehicles={
            role: dict(localVmId=OWNER, sshPort=port, runtime=dict(state="RUNNING"))
            for role, port in (("test", 10022), ("production", 10023))})
        self.source = Mock()
        self.source.environment.root = Path("/unused-connectivity-test")
        self.source.environment.factory31_comparison = False
        self.source.environment.ssh_port.side_effect = lambda role: 10022 if role == "test" else 10023
        self.source.environment._writer.side_effect = nullcontext
        self.source.driver.operation.side_effect = lambda **kwargs: nullcontext()
        self.service = ConnectivityService(self.source)
        reader = patch("aosedge_demo_orchestrator.connectivity.read_json", return_value=self.state)
        reader.start()
        self.addCleanup(reader.stop)

    def test_off_never_touches_non_current_vm(self):
        with self.assertRaisesRegex(EnvironmentError, "REQUIRES_CURRENT_VEHICLE"):
            self.service.execute("off", "production")
        self.source.driver.guest.assert_not_called()
        self.source.vm._save.assert_not_called()

    def test_status_is_single_read_without_writer_or_save(self):
        self.source.driver.guest.return_value = dict(state="OFF")
        self.assertEqual("OFF", self.service.execute("status")["state"])
        self.source.driver.guest.assert_called_once_with(self.state, "test", "connectivity-status")
        self.source.environment._writer.assert_not_called()
        self.source.vm._save.assert_not_called()

    def test_explicit_restore_after_simulation_stop(self):
        self.state.update(currentVehicle=None, source=dict(state="STOPPED"))
        self.source.driver.guest.side_effect = [dict(state="OFF"), dict(state="ON")]
        self.assertEqual("ON", self.service.execute("on", "test")["state"])
        self.assertEqual(["connectivity-status", "connectivity-on"],
            [call.args[2] for call in self.source.driver.guest.call_args_list])
        self.assertNotIn("externalConnectivity", self.state["vehicles"]["production"]["runtime"])

    def test_failed_mutation_is_uncertain_without_retry(self):
        self.source.driver.guest.side_effect = [dict(state="ON"), EnvironmentError("LOST_REPLY")]
        with self.assertRaisesRegex(EnvironmentError, "LOST_REPLY"):
            self.service.execute("off")
        self.assertEqual(2, self.source.driver.guest.call_count)
        self.assertEqual("UNCERTAIN", self.state["vehicles"]["test"]["runtime"]["externalConnectivity"]["state"])


if __name__ == "__main__":
    unittest.main()
