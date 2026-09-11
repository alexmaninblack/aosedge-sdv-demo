# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Documented Cloud response fixtures; no credentials, VM or network access."""

import copy
import contextlib
import io
import json
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import Mock, patch

from aosedge_demo_orchestrator import cloud_observation as read
from aosedge_demo_orchestrator.api import execute_operation
from aosedge_demo_orchestrator.application import DemoOrchestrator
from aosedge_demo_orchestrator.cli import main
from aosedge_demo_orchestrator.environment import EnvironmentError
from aosedge_demo_orchestrator.unit_cloud import CloudFailure, execute
from aosedge_demo_orchestrator.units import UnitService

UNIT = "11111111-1111-4111-8111-111111111111"
SERVICE = "22222222-2222-4222-8222-222222222222"
SUBJECT = "33333333-3333-4333-8333-333333333333"
OWNER = "44444444-4444-4444-8444-444444444444"
IDENTITY = dict(unitId=UNIT, systemUid="owned-test")


def unit():
    return dict(id=UNIT, system_uid="owned-test", status="provisioned", online_status="Online",
                unit_sets=[], unit_update_components=[], nodes=[], layers=[], assigned_subjects=[], reported_subjects=[])


def service(version="3.0.0", run_state="running"):
    return dict(subject=SUBJECT, service=dict(id=SERVICE, title="Brake", service_provider_title="SP1"),
                num_instance=1, pending_num_instance=0, service_versions=dict(
                    installed_service_version_id=OWNER, installed_service_version=dict(id=OWNER, version=version),
                    pending_service_version_status="none"),
                instances=[dict(instance_id=0, version=version, run_state=run_state,
                                node=dict(node_id="main", node_type="aos-vm-main", status="provisioned"))])


def page(items, total=None):
    return dict(total=len(items) if total is None else total, offset=0, items=items)


def cloud(responses):
    value = Mock()
    def call(path, method="GET", **kwargs):
        if method != "GET" or kwargs:
            raise AssertionError("Only fixed GET requests are allowed")
        answer = responses[path]
        if isinstance(answer, Exception):
            raise answer
        return copy.deepcopy(answer)
    value.call.side_effect = call
    return value


UNIT_PATH = "units/" + UNIT + "/"
LIST_PATH = UNIT_PATH + "subjects-services/?limit=100&offset=0"
DETAIL_PATH = UNIT_PATH + "subjects-services/" + SERVICE + "/?limit=100&offset=0"
MONITOR_PATH = UNIT_PATH + "monitoring/?datetime_from=latest"


class CloudInventoryTests(unittest.TestCase):
    def test_permission_denial_has_no_forbidden_endpoint_call(self):
        transport = cloud({UNIT_PATH: unit()})
        def require(permission):
            if permission == "units_subjects_services_list":
                raise CloudFailure("OEM_PERMISSION_MISSING:units_subjects_services_list")
        transport.require.side_effect = require
        result = read.inventory(transport, IDENTITY)
        self.assertEqual("FORBIDDEN", result["services"]["transport"])
        self.assertEqual(1, transport.call.call_count)

    def test_malformed_page_does_not_become_empty(self):
        for malformed in (dict(total=0, items=[]), dict(total=0, offset=False, items=[]),
                          dict(total=0, offset=0, items=[service()])):
            result = read.inventory(cloud({UNIT_PATH: unit(), LIST_PATH: malformed}), IDENTITY)
            self.assertIsNone(result["services"]["value"])
            self.assertEqual("SCHEMA_INVALID", result["services"]["transport"])

    def test_all_components_and_independent_installed_pending_are_preserved(self):
        raw = unit()
        raw["unit_update_components"] = [dict(type=name,
            installed_component=dict(id=OWNER, version="0.0.0", state="Ready", is_fake=True),
            pending_component=dict(id=SUBJECT, version="15.0.0", state="Ready", is_fake=False),
            pending_component_status="to be installed", pending_component_error="Safe stop pending")
            for name in ("rootfs", "boot", "vehicle-data-provider")]
        transport = cloud({UNIT_PATH: raw, LIST_PATH: page([])})
        result = read.inventory(transport, IDENTITY)
        self.assertFalse(result["problems"])
        self.assertEqual(3, len(result["components"]["value"]))
        component = result["components"]["value"][2]
        self.assertEqual("0.0.0", component["installed_component"]["version"])
        self.assertEqual("15.0.0", component["pending_component"]["version"])
        self.assertEqual("to be installed", component["pending_component_status"])
        self.assertEqual("NOT_REPORTED_BY_CLOUD", component["runtimeState"])
        self.assertEqual([UNIT_PATH, LIST_PATH], [call.args[0] for call in transport.call.call_args_list])
        transport.pages.assert_not_called()

    def test_missing_is_unknown_but_explicit_empty_is_current(self):
        raw = unit()
        del raw["unit_update_components"]
        result = read.inventory(cloud({UNIT_PATH: raw, LIST_PATH: page([])}), IDENTITY)
        self.assertIsNone(result["components"]["value"])
        self.assertEqual("UNKNOWN", result["components"]["state"])
        self.assertEqual([], result["services"]["value"])
        self.assertEqual("CURRENT", result["services"]["state"])

    def test_unit_read_failure_never_becomes_offline_or_absent(self):
        for code, classification in ((401, "UNAUTHENTICATED"), (403, "FORBIDDEN"), (404, "NOT_FOUND_OR_INACCESSIBLE")):
            transport = cloud({UNIT_PATH: CloudFailure("CLOUD_HTTP_" + str(code))})
            result = read.inventory(transport, IDENTITY)
            self.assertIsNone(result["unit"]["value"])
            self.assertEqual(classification, result["unit"]["transport"])
            self.assertEqual(1, transport.call.call_count)

    def test_explicit_offline_is_not_a_read_failure(self):
        raw = unit()
        raw["online_status"] = "Offline"
        result = read.inventory(cloud({UNIT_PATH: raw, LIST_PATH: page([])}), IDENTITY)
        self.assertEqual("OFFLINE", result["unit"]["value"]["connectivity"])
        self.assertEqual("CURRENT", result["unit"]["state"])

    def test_identity_change_stops_followup_reads(self):
        raw = unit()
        raw["system_uid"] = "unrelated-production"
        transport = cloud({UNIT_PATH: raw})
        result = read.inventory(transport, IDENTITY)
        self.assertEqual("CLOUD_UNIT_IDENTITY_MISMATCH", result["unit"]["reason"])
        self.assertEqual(1, transport.call.call_count)

    def test_real_instance_versions_and_detail_pages_not_first_instance_only(self):
        row = service()
        row["instances"].append(dict(instance_id=1, version="2.0.0", run_state="failed", error_exit_code=1))
        transport = cloud({UNIT_PATH: unit(), LIST_PATH: page([row]), DETAIL_PATH: page([
            dict(row, subject=dict(id=SUBJECT, label="Brake")), dict(row, subject=dict(id=OWNER))])})
        result = read.inventory(transport, IDENTITY)
        details = result["serviceDetails"][SERVICE]
        self.assertEqual(2, len(details["value"]))
        self.assertEqual([SUBJECT, OWNER], [item["subject"] for item in details["value"]])
        self.assertEqual(["3.0.0", "2.0.0"], [item["version"] for item in details["value"][0]["instances"]["value"]])
        self.assertEqual("failed", details["value"][0]["instances"]["value"][1]["run_state"])
        self.assertEqual(3, transport.call.call_count)
        self.assertIsNone(details["sourceTimestamp"])

    def test_zero_instances_and_missing_instances_are_distinct(self):
        for instances, state in (([], "CURRENT"), (None, "UNKNOWN")):
            row = service()
            row.update(num_instance=0, instances=instances)
            result = read.inventory(cloud({UNIT_PATH: unit(), LIST_PATH: page([row]), DETAIL_PATH: page([row])}), IDENTITY)
            detail = result["serviceDetails"][SERVICE]["value"][0]
            self.assertEqual(0, detail["num_instance"])
            self.assertEqual(state, detail["instances"]["state"])
            self.assertEqual(instances, detail["instances"]["value"])

    def test_incomplete_pages_are_not_claimed_complete_or_retried(self):
        transport = cloud({UNIT_PATH: unit(), LIST_PATH: page([], total=101)})
        result = read.inventory(transport, IDENTITY)
        self.assertEqual("INCOMPLETE", result["services"]["state"])
        self.assertEqual(dict(offset=0, returned=0, total=101, complete=False), result["services"]["coverage"])
        self.assertEqual(2, transport.call.call_count)

    def test_detail_failure_does_not_erase_unit_and_service_list(self):
        result = read.inventory(cloud({UNIT_PATH: unit(), LIST_PATH: page([service()]),
                                      DETAIL_PATH: CloudFailure("CLOUD_HTTP_403")}), IDENTITY)
        self.assertEqual("CURRENT", result["unit"]["state"])
        self.assertEqual("CURRENT", result["services"]["state"])
        self.assertEqual("FORBIDDEN", result["serviceDetails"][SERVICE]["transport"])

    def test_projection_excludes_arbitrary_config_and_redacts_errors(self):
        raw = unit()
        raw["secret"] = "do-not-forward"
        raw["installed_unit_config"] = dict(version="26", unit_config=dict(env=dict(PASSWORD="do-not-forward")))
        raw["unit_update_components"] = [dict(type="vdp", pending_component_error="token=do-not-forward",
            installed_component=dict(id=OWNER, version="1", metadata_info=dict(secret="do-not-forward")))]
        result = read.inventory(cloud({UNIT_PATH: raw, LIST_PATH: page([])}), IDENTITY)
        self.assertNotIn("do-not-forward", json.dumps(result))
        self.assertEqual("[REDACTED]", result["components"]["value"][0]["pending_component_error"])

    def test_detail_identity_mismatch_is_unavailable(self):
        foreign = service()
        foreign["service"]["id"] = OWNER
        result = read.inventory(cloud({UNIT_PATH: unit(), LIST_PATH: page([service()]), DETAIL_PATH: page([foreign])}), IDENTITY)
        self.assertEqual("CLOUD_SERVICE_IDENTITY_MISMATCH", result["serviceDetails"][SERVICE]["reason"])

    def test_service_detail_fanout_is_bounded(self):
        rows = [service() for _ in range(10)]
        replies = {UNIT_PATH: unit(), LIST_PATH: page(rows)}
        for index, row in enumerate(rows):
            identifier = "55555555-5555-4555-8555-" + str(index).zfill(12)
            row["service"]["id"] = identifier
            replies[UNIT_PATH + "subjects-services/" + identifier + "/?limit=100&offset=0"] = page([row])
        transport = cloud(replies)
        result = read.inventory(transport, IDENTITY)
        self.assertEqual(8, len(result["serviceDetails"]))
        self.assertEqual("CLOUD_SERVICE_DETAIL_LIMIT", result["services"]["reason"])
        self.assertEqual(10, transport.call.call_count)


class MonitoringTests(unittest.TestCase):
    def test_dmips_raw_units_zero_and_source_time(self):
        sample = dict(time="2026-09-10T00:00:00Z", value=0, system_uid="owned-test", nodeId="main", instance=0)
        metrics = {key: [] for key in read.METRICS}
        metrics.update(cpu=[sample], ram=[dict(sample, value=1024)], usedDisk=[dict(sample, value=None)])
        transport = cloud({UNIT_PATH: unit(), MONITOR_PATH: [metrics]})
        result = read.monitoring(transport, IDENTITY)["monitoring"]["value"]
        self.assertEqual("DMIPS", result["cpu"]["unit"])
        self.assertEqual(0, result["cpu"]["value"][0]["value"])
        self.assertEqual(sample["time"], result["cpu"]["value"][0]["sourceTimestamp"])
        self.assertIsNone(result["ram"]["unit"])
        self.assertEqual(1024, result["ram"]["value"][0]["value"])
        self.assertIsNone(result["usedDisk"]["value"][0]["value"])
        self.assertEqual("UNKNOWN", result["usedDisk"]["value"][0]["state"])
        self.assertEqual([UNIT_PATH, MONITOR_PATH], [call.args[0] for call in transport.call.call_args_list])

    def test_no_samples_missing_field_and_denied_are_different(self):
        empty = read.monitoring(cloud({UNIT_PATH: unit(), MONITOR_PATH: []}), IDENTITY)
        missing = read.monitoring(cloud({UNIT_PATH: unit(), MONITOR_PATH: [{}]}), IDENTITY)
        denied = read.monitoring(cloud({UNIT_PATH: unit(), MONITOR_PATH: CloudFailure("CLOUD_HTTP_403")}), IDENTITY)
        self.assertEqual([], empty["monitoring"]["value"]["cpu"]["value"])
        self.assertIsNone(missing["monitoring"]["value"]["cpu"]["value"])
        self.assertIsNone(denied["monitoring"]["value"])
        self.assertEqual("FORBIDDEN", denied["monitoring"]["transport"])

    def test_foreign_uid_and_non_numeric_value_rejected(self):
        for sample in (dict(time="x", value=1, system_uid="unrelated"), dict(time="x", value=True)):
            result = read.monitoring(cloud({UNIT_PATH: unit(), MONITOR_PATH: [dict(cpu=[sample])]}), IDENTITY)
            self.assertEqual("UNKNOWN", result["monitoring"]["state"])
            self.assertIsNone(result["monitoring"]["value"])


class ObservationIntegrationTests(unittest.TestCase):
    def test_failed_list_retains_details_but_confirmed_removal_does_not(self):
        previous = read.inventory(cloud({UNIT_PATH: unit(), LIST_PATH: page([service()]), DETAIL_PATH: page([service()])}), IDENTITY)
        failure = read.inventory(cloud({UNIT_PATH: unit(), LIST_PATH: CloudFailure("CLOUD_HTTP_403")}), IDENTITY)
        merged = read.retain_last_known(failure, previous)
        self.assertEqual("STALE", merged["serviceDetails"][SERVICE]["state"])
        self.assertEqual("3.0.0", merged["serviceDetails"][SERVICE]["value"][0]["instances"]["value"][0]["version"])
        removed = read.inventory(cloud({UNIT_PATH: unit(), LIST_PATH: page([])}), IDENTITY)
        self.assertEqual({}, read.retain_last_known(removed, previous)["serviceDetails"])

    def test_failed_refresh_retains_last_known_only_for_exact_unit(self):
        previous = read.inventory(cloud({UNIT_PATH: unit(), LIST_PATH: page([])}), IDENTITY)
        current = read.unavailable(IDENTITY, "cloud-status", "CLOUD_HTTP_403")
        merged = read.retain_last_known(current, previous)
        self.assertEqual("STALE", merged["unit"]["state"])
        self.assertEqual("Online", merged["unit"]["value"]["online_status"])
        self.assertEqual("FORBIDDEN", merged["unit"]["transport"])
        self.assertEqual(previous["unit"]["readCompletedAt"], merged["unit"]["lastKnownReadCompletedAt"])
        current["systemUid"] = "replacement"
        self.assertIsNone(read.retain_last_known(current, previous)["unit"]["value"])

    def test_shared_inflight_read_does_not_start_second_request(self):
        shared = read.SharedCloudObserver()
        started, release = threading.Event(), threading.Event()
        def fetch():
            started.set()
            self.assertTrue(release.wait(2))
            return read.inventory(cloud({UNIT_PATH: unit(), LIST_PATH: page([])}), IDENTITY)
        fetch = Mock(side_effect=fetch)
        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(shared.read, "unit", fetch)
            self.assertTrue(started.wait(2))
            # Signal when the second caller reaches the shared Future result.
            future = shared.in_flight["unit"]
            waiting = threading.Event()
            original = future.result
            def wait():
                waiting.set()
                return original()
            with patch.object(future, "result", side_effect=wait):
                second = pool.submit(shared.read, "unit", fetch)
                self.assertTrue(waiting.wait(2))
                release.set()
                self.assertEqual(first.result(), second.result())
        fetch.assert_called_once()

    def test_unit_service_reads_journal_identity_without_vm_checks(self):
        vm = Mock(root=Path("/unused"))
        unit_service = UnitService(vm)
        unit_service._cloud = Mock(return_value=read.unavailable(IDENTITY, "cloud-status", "CLOUD_HTTP_403"))
        journal = dict(cloudBinding=dict(ownerId=OWNER), vehicles=dict(test=IDENTITY,
            production=dict(unitId="never-read", systemUid="never-read")))
        with patch("aosedge_demo_orchestrator.units.read_json", return_value=journal):
            unit_service.observe("cloud-status", "test")
        unit_service._cloud.assert_called_once_with("observe", observation="cloud-status", ownerId=OWNER, **IDENTITY)
        vm._validate.assert_not_called()
        vm.execute.assert_not_called()

    def test_missing_binding_and_wrong_target_do_not_call_cloud(self):
        service_instance = UnitService(Mock(root=Path("/unused")))
        service_instance._cloud = Mock()
        with patch("aosedge_demo_orchestrator.units.read_json", return_value=dict(vehicles={})), self.assertRaises(EnvironmentError):
            service_instance.observe("monitoring", "test")
        with self.assertRaises(EnvironmentError):
            service_instance.observe("monitoring", "production")
        service_instance._cloud.assert_not_called()

    def test_cli_and_api_share_result_and_reject_injected_capabilities(self):
        data = read.inventory(cloud({UNIT_PATH: unit(), LIST_PATH: page([])}), IDENTITY)
        output = io.StringIO()
        with patch.object(UnitService, "observe", return_value=data) as observe, contextlib.redirect_stdout(output):
            code = main(["--output", "json", "unit", "cloud-status", "test"])
        self.assertEqual(0, code)
        self.assertEqual("OBSERVED", json.loads(output.getvalue())["state"])
        observe.assert_called_once_with("cloud-status", "test")
        app = DemoOrchestrator(unit_service=Mock(observe=Mock(return_value=data)))
        result = execute_operation(dict(domain="unit", action="monitoring", target="test"), app)
        self.assertEqual(data, result["data"])
        for extra in (dict(target="production"), dict(guest=True), dict(unitId=UNIT), dict(credential="secret"), dict(path="/")):
            request = dict(domain="unit", action="monitoring", target="test")
            request.update(extra)
            with self.assertRaises(ValueError):
                execute_operation(request, app)

    def test_worker_dispatch_is_fixed_read_only(self):
        transport = cloud({UNIT_PATH: unit(), LIST_PATH: page([])})
        with patch("aosedge_demo_orchestrator.unit_cloud.Cloud", return_value=transport):
            result = execute(dict(action="observe", observation="cloud-status", **IDENTITY))
        self.assertEqual("AOS_CLOUD_ONLY", result["source"])
        transport.pages.assert_not_called()

    def test_human_cli_prints_observation_without_lifecycle_vehicle_shape(self):
        data = read.unavailable(IDENTITY, "monitoring", "CLOUD_HTTP_403")
        output = io.StringIO()
        with patch.object(UnitService, "observe", return_value=data), contextlib.redirect_stdout(output):
            code = main(["unit", "monitoring", "test"])
        self.assertEqual(1, code)
        self.assertIn("FORBIDDEN", output.getvalue())


if __name__ == "__main__":
    unittest.main()
