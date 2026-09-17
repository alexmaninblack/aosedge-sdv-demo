# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Offline certificate-selection, backend isolation and guest projection proofs."""

import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
from uuid import uuid4

from aosedge_demo_orchestrator import cloud_guest
from aosedge_demo_orchestrator.api import execute_operation
from aosedge_demo_orchestrator.cloud_connection import (
    CloudConnection, CONFIG, LEGACY_DOMAIN, cloud_binding, cloud_scope, cloud_subjects,
    configure_guest, guest_configuration, domain_name, host_entries, trusted_host)
from aosedge_demo_orchestrator.environment import EnvironmentService, EnvironmentError, JOURNAL, atomic_json
from aosedge_demo_orchestrator.presenter_operations import operation_plan, public_result
from aosedge_demo_orchestrator.status import load_configuration, read_json

DOMAIN = "developer.aos-dev.test"
OWNER = "11111111-1111-4111-8111-111111111111"


def vehicle(role, bound=False):
    return dict(localVmId=str(uuid4()), overlay=".local/demo-current/" + ("validation" if role == "test" else role) + ".qcow2",
        state="MANUFACTURED", unitId=str(uuid4()) if bound else None, nodeId=None, unitSetId=None,
        cloud={"lifecycle": "ONLINE"} if bound else None)


class SelectionTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.environment = EnvironmentService(root=self.root)
        self.connection = CloudConnection(self.environment)
        self.state = dict(schemaVersion=1, kind="democtl.current-run", stage="MANUFACTURED", factory=None,
            vehicles={"test": vehicle("test"), "production": vehicle("production", True)},
            operations=[{"class": "LOCAL_CREATE", "state": "COMPLETED"}],
            cloudBinding={"ownerId": OWNER, "sets": {"test": "old-test", "production": "old-prod"}},
            demoSubjects={"old-service": {"id": "old-subject"}})
        self.environment._directory(".run/demo-current")
        atomic_json(self.root / JOURNAL, self.state)
        self.metadata = dict(domain=DOMAIN, certificateName="oem.p12", validUntil="2036-01-01T00:00:00Z")
        self.inspector = patch.object(self.connection, "inspect", side_effect=lambda *_: dict(self.metadata))
        self.inspector.start()
        self.addCleanup(self.inspector.stop)

    def test_select_preserves_production_and_isolates_legacy_subjects_and_uuids(self):
        result = self.connection.select("/private/credential.p12", DOMAIN)
        self.assertTrue(result["applied"])
        selected = read_json(self.root / JOURNAL)
        for key in ("vehicles", "cloudBinding", "demoSubjects"):
            self.assertEqual(self.state[key], selected[key])
        self.assertEqual({}, cloud_binding(selected))
        self.assertEqual({}, cloud_subjects(selected))
        cloud_scope(selected, create=True)["cloudBinding"] = {"ownerId": "debug-owner"}
        cloud_subjects(selected, create=True)["debug-service"] = {"id": "debug-subject"}
        self.assertEqual(self.state["cloudBinding"], selected["cloudBinding"])
        self.assertEqual(self.state["demoSubjects"], selected["demoSubjects"])
        config = load_configuration(self.root)
        self.assertEqual(DOMAIN, config["cloudProfiles"]["oem-delivery"]["cloudDomain"])
        self.assertNotIn("expectedOwnerId", config["cloudProfiles"]["oem-delivery"])
        self.assertEqual(DOMAIN, config["cloudProfiles"]["service-provider"]["cloudDomain"])
        self.assertEqual(LEGACY_DOMAIN, config["vehicles"]["production"]["cloudHost"])

    def test_explicit_repeat_repairs_partial_selection_without_cloud_calls(self):
        self.state["selectedCloudDomain"] = DOMAIN
        atomic_json(self.root / JOURNAL, self.state)
        with self.assertRaisesRegex(ValueError, "reconciliation"):
            load_configuration(self.root)
        self.connection.select(expected_domain=DOMAIN)
        first = read_json(self.root / CONFIG)
        self.connection.select(expected_domain=DOMAIN)
        self.assertEqual(first, read_json(self.root / CONFIG))

    def test_domain_changed_after_preview_is_rejected_before_writes(self):
        with self.assertRaisesRegex(EnvironmentError, "CHANGED_SINCE_PREVIEW"):
            self.connection.select(expected_domain="different.example.test")
        self.assertFalse((self.root / CONFIG).exists())
        self.assertEqual(self.state, read_json(self.root / JOURNAL))

    def test_switch_bound_or_uncertain_test_is_rejected(self):
        for field, value in (("unitId", str(uuid4())), ("systemUid", "pending-sdk"), ("cloud", {"lifecycle": "PROVISIONING"})):
            state = copy.deepcopy(self.state)
            state["vehicles"]["test"][field] = value
            atomic_json(self.root / JOURNAL, state)
            with self.assertRaisesRegex(EnvironmentError, "FINISH_TEST"):
                self.connection.select(expected_domain=DOMAIN)
        state = copy.deepcopy(self.state)
        state["componentOperations"] = {"37.0.0": {"upload": {"state": "UNCERTAIN"}}}
        atomic_json(self.root / JOURNAL, state)
        with self.assertRaisesRegex(EnvironmentError, "FINISH_TEST_OPERATIONS"):
            self.connection.select(expected_domain=DOMAIN)

    def test_no_journal_selection_is_persistent_local_configuration(self):
        (self.root / JOURNAL).unlink()
        self.connection.select(expected_domain=DOMAIN)
        self.assertFalse((self.root / JOURNAL).exists())
        self.assertEqual(DOMAIN, load_configuration(self.root)["cloudConnection"]["domain"])

    def test_scope_reads_do_not_mutate_the_journal(self):
        state = {"selectedCloudDomain": DOMAIN}
        self.assertEqual({}, cloud_binding(state))
        self.assertEqual({}, cloud_subjects(state))
        self.assertEqual({"selectedCloudDomain": DOMAIN}, state)


class ContractTests(unittest.TestCase):
    def test_host_is_certificate_derived_and_pinned_for_oem_and_sp(self):
        self.assertEqual(DOMAIN, trusted_host(DOMAIN, DOMAIN))
        for host in ("aoscloud.io", "sp.developer.aos-dev.test"):
            with self.assertRaisesRegex(ValueError, "DOMAIN_CHANGED"):
                trusted_host(host, DOMAIN)
        with self.assertRaisesRegex(ValueError, "SELECTION_REQUIRED"):
            trusted_host(DOMAIN)
        self.assertEqual(LEGACY_DOMAIN, trusted_host(LEGACY_DOMAIN))

    def test_no_url_port_ip_path_or_command_injection_in_domain(self):
        for value in ("https://example.test", "example.test:10000", "127.0.0.1", "example.test/a", "bad;example.test", "localhost", "a..test", "-x.test", "*.example.test"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                domain_name(value)

    def test_browser_can_only_reference_a_native_preview(self):
        payload = dict(action="cloud-select", requestId=str(uuid4()), sessionId="session", selectionId=str(uuid4()))
        _, plan = operation_plan(payload)
        self.assertEqual("select", plan[0]["action"])
        for key in ("certificate", "cloudDomain", "apiUrl"):
            with self.assertRaises(ValueError):
                operation_plan(dict(payload, **{key: "/private/key.p12"}))
        with self.assertRaises(ValueError):
            execute_operation(dict(domain="cloud", action="select", certificate="/private/key.p12"), Mock())

    def test_public_receipt_does_not_expose_private_path_or_key(self):
        value = public_result(dict(operation="cloud.inspect", state="OBSERVED", message="ok",
            data=dict(domain=DOMAIN, certificateName="oem.p12", certificate="/private/key.p12", key="secret", pem="secret")))
        self.assertEqual({"domain": DOMAIN, "certificateName": "oem.p12"}, value["facts"])
        self.assertNotIn("secret", json.dumps(value))

    def test_only_selected_cloud_hosts_are_mirrored_and_conflicts_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "hosts"
            path.write_text("127.0.0.1 localhost\n192.0.2.42 " + DOMAIN + " api." + DOMAIN + " unrelated.test\n")
            self.assertEqual(2, len(host_entries(DOMAIN, path)))
            with path.open("a") as stream:
                stream.write("192.0.2.9 " + DOMAIN + "\n")
            with self.assertRaisesRegex(EnvironmentError, "AMBIGUOUS"):
                host_entries(DOMAIN, path)

    def test_unselected_and_production_guests_are_not_touched(self):
        vm = Mock()
        with patch("aosedge_demo_orchestrator.cloud_connection.host_entries") as hosts, \
                patch("aosedge_demo_orchestrator.status.load_configuration") as config, \
                patch("aosedge_demo_orchestrator.cloud_connection.subprocess.run") as run:
            self.assertIsNone(configure_guest(vm, {}, "test"))
            self.assertIsNone(configure_guest(vm, {"selectedCloudDomain": DOMAIN}, "production"))
            self.assertIsNone(configure_guest(vm, {"selectedCloudDomain": LEGACY_DOMAIN}, "test", vm_start=True))
            hosts.assert_not_called()
            config.assert_not_called()
            run.assert_not_called()
        vm.progress.assert_not_called()

    def test_debug_requires_all_six_hosts_before_guest_execution(self):
        entries = [dict(host=(prefix + "." if prefix else "") + DOMAIN, address="192.0.2.42")
                   for prefix in ("", "api", "oem", "sp", "fleet", "admin")]
        with patch("aosedge_demo_orchestrator.status.load_configuration", return_value={"cloudConnection": {"domain": DOMAIN}}), \
                patch("aosedge_demo_orchestrator.cloud_connection.host_entries", return_value=entries) as hosts:
            self.assertEqual(entries, guest_configuration(Mock(), {"selectedCloudDomain": DOMAIN}, "test")["hosts"])
            hosts.return_value = entries[:-1]
            with self.assertRaisesRegex(EnvironmentError, "HOST_MAPPING_INCOMPLETE"):
                guest_configuration(Mock(), {"selectedCloudDomain": DOMAIN}, "test")

    def test_hosts_resolution_is_not_misreported_as_a_failed_dns_bridge(self):
        from aosedge_demo_orchestrator.probes import host_dns
        with patch("aosedge_demo_orchestrator.cloud_connection.host_entries", return_value=[{"host": DOMAIN}]), \
                patch("socket.socket") as socket:
            result = host_dns(dict(cloudHost=DOMAIN, dnsPort=18053), 1)
        self.assertEqual("NOT_APPLICABLE", result["state"])
        self.assertEqual("HOSTS_MAPPING_USED_NOT_DNS", result["reason"])
        socket.assert_not_called()

    def test_cloud_status_never_sends_the_retained_production_uuid_to_debug(self):
        from aosedge_demo_orchestrator.cloud import cloud_status
        credential = Mock(is_file=Mock(return_value=True), is_symlink=Mock(return_value=False),
                          stat=Mock(return_value=SimpleNamespace(st_mode=0o600)))
        profile = dict(credential=credential, expectedRole="oem", cloudDomain=DOMAIN)
        process = Mock(returncode=0, communicate=Mock(return_value=(json.dumps({"access": {}, "certificate": {}, "units": {}}), "")))
        with patch("aosedge_demo_orchestrator.cloud.subprocess.Popen", return_value=process):
            cloud_status("oem-delivery", profile, {"test": {"unitId": "debug-test", "cloudHost": DOMAIN},
                "production": {"unitId": "retained-production", "cloudHost": LEGACY_DOMAIN}}, Mock(is_file=Mock(return_value=True)), 1)
        request = json.loads(process.communicate.call_args.args[0])
        self.assertEqual(DOMAIN, request["cloudDomain"])
        self.assertEqual({"test": {"unitId": "debug-test"}}, request["vehicles"])


class GuestProjectionTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.cfg = self.root / "etc/aos/cm.cfg"
        self.cfg.parent.mkdir(parents=True)
        self.original = dict(serviceDiscoveryUrl="https://aoscloud.io:9000/sd/v7/", caCert="/packaged/AosRootCA.crt", unrelated=17)
        self.cfg.write_text(json.dumps(self.original))
        (self.root / "etc/hosts").write_text("127.0.0.1 localhost\n192.0.2.1 unrelated.test\n")
        (self.root / "run").mkdir()
        self.calls = []
        self.active = False
        self.request = dict(domain=DOMAIN, hosts=[dict(host=DOMAIN, address="192.0.2.42")])

    def run_projection(self, **extra):
        path_type = Path
        def mapped(value):
            return self.root / value.lstrip("/")
        original_stat = Path.stat
        def stat(path, *args, **kwargs):
            if path == self.root / "run/democtl-cloud":
                return SimpleNamespace(st_uid=0, st_mode=original_stat(path, *args, **kwargs).st_mode)
            return original_stat(path, *args, **kwargs)
        def run(args, **kwargs):
            self.calls.append(args)
            if args[:3] == ["systemctl", "is-active", "--quiet"]:
                return SimpleNamespace(returncode=0 if self.active else 3)
            if args[:2] == ["mount", "--bind"]:
                shutil.copyfile(args[2], args[3])  # Simulated mount, fixture only.
            return SimpleNamespace(returncode=0)
        with patch.object(cloud_guest, "Path", side_effect=mapped), patch.object(path_type, "stat", stat), \
                patch.object(cloud_guest.subprocess, "run", side_effect=run), patch("socket.getaddrinfo", return_value=[]):
            return cloud_guest.apply(dict(self.request, **extra))

    def test_first_apply_repeat_and_reboot_preserve_config_and_ca(self):
        first = self.run_projection()
        self.assertTrue(first["changed"])
        self.assertFalse(first["cmRestarted"])
        expected = dict(self.original, serviceDiscoveryUrl="https://" + DOMAIN + ":9000/sd/v7/")
        self.assertEqual(expected, json.loads(self.cfg.read_text()))
        hosts = (self.root / "etc/hosts").read_text()
        self.assertIn("unrelated.test", hosts)
        self.assertIn(DOMAIN, hosts)
        self.calls.clear()
        self.assertFalse(self.run_projection()["changed"])
        self.assertFalse(any(call[0] == "mount" for call in self.calls))
        # An unchanged Factory boots again; host start reprojects the same selection.
        self.cfg.write_text(json.dumps(self.original))
        self.active = True
        restarted = self.run_projection(vmStart=True)
        self.assertFalse(restarted["cmRestarted"])
        self.assertTrue(restarted["cmRestartRequested"])
        self.assertEqual(1, self.calls.count(["systemctl", "--no-block", "restart", "aos-cm.service"]))
        self.assertFalse(self.run_projection(vmStart=True)["cmRestartRequested"])
        self.assertEqual(1, self.calls.count(["systemctl", "--no-block", "restart", "aos-cm.service"]))

    def test_provision_does_not_repoint_an_active_or_provisioned_guest(self):
        self.active = True
        with self.assertRaisesRegex(ValueError, "ACTIVE_CM"):
            self.run_projection()
        self.assertEqual(self.original, json.loads(self.cfg.read_text()))
        self.active = False
        path = self.root / "var/aos/.provisionstate"
        path.parent.mkdir(parents=True)
        path.touch()
        with self.assertRaisesRegex(ValueError, "ALREADY_PROVISIONED"):
            self.run_projection()

    def test_production_projection_has_no_file_process_or_dns_actions(self):
        with patch.object(cloud_guest, "Path") as path, patch.object(cloud_guest.subprocess, "run") as run, \
                patch("socket.getaddrinfo") as dns:
            self.assertFalse(cloud_guest.apply(dict(domain=LEGACY_DOMAIN, hosts=self.request["hosts"]))["configured"])
            path.assert_not_called()
            run.assert_not_called()
            dns.assert_not_called()

    def test_hosts_are_one_line_and_precede_endpoint_change_and_restart(self):
        self.request["hosts"] = [dict(host=(prefix + "." if prefix else "") + DOMAIN, address="192.0.2.42")
                                 for prefix in ("", "api", "oem", "sp", "fleet", "admin")]
        self.active = True
        self.run_projection(vmStart=True)
        lines = (self.root / "etc/hosts").read_text().splitlines()
        self.assertEqual(["192.0.2.42 " + " ".join(entry["host"] for entry in self.request["hosts"])],
                         [line for line in lines if DOMAIN in line])
        actions = [call for call in self.calls if call[:2] in (["mount", "--bind"], ["systemctl", "--no-block"])]
        self.assertEqual(str(self.root / "etc/hosts"), actions[0][-1])
        self.assertEqual(str(self.cfg), actions[1][-1])
        self.assertEqual(["systemctl", "--no-block", "restart", "aos-cm.service"], actions[2])


if __name__ == "__main__":
    unittest.main()
