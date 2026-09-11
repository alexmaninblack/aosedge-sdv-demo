# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from aosedge_demo_orchestrator import presenter
from aosedge_demo_orchestrator.components import COMPONENT
from aosedge_demo_orchestrator.environment import JOURNAL


class StudioCloudReaderTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.path = self.root / JOURNAL
        self.path.parent.mkdir(parents=True)
        self.journal = dict(vehicles=dict(test=dict(localVmId="vm-a", unitId="unit-a")))
        self.write()
        self.reader = presenter.StudioCloudReader.__new__(presenter.StudioCloudReader)
        self.reader.application = SimpleNamespace(environment_service=SimpleNamespace(root=self.root))

    def write(self):
        self.path.write_text(json.dumps(self.journal))

    def inventory(self, state="CURRENT"):
        return dict(state="OBSERVED", data=dict(unitId="unit-a", readCompletedAt="now",
            unit=dict(state="CURRENT", value=dict(connectivity="ONLINE", status="provisioned")),
            components=dict(state=state, value=[dict(reported_component_id="cloud-component-uuid", type=COMPONENT,
                installed_component=dict(version="18.0.0"), pending_component=None)]),
            services=dict(state="CURRENT", value=[])))

    def test_uses_cloud_component_type_and_preserves_section_freshness(self):
        with patch.object(presenter, "execute_operation", return_value=self.inventory("STALE")) as call:
            result = self.reader()
        self.assertEqual("vm-a:unit-a", result["bindingKey"])
        self.assertEqual("18.0.0", result["value"]["installedVersion"])
        self.assertEqual("STALE", result["value"]["inventory"]["components"]["state"])
        self.assertEqual("NOT_REPORTED_BY_CLOUD", result["value"]["runtimeState"])
        self.assertEqual(dict(domain="unit", action="cloud-status", target="test"), call.call_args.args[0])

    def test_ready_publication_is_selected_by_receipt_and_does_not_repeat_release_scan(self):
        self.journal["componentOperations"] = {"19.0.0": dict(deploymentId="bundle-a")}
        self.write()
        publication = dict(stage="READY", deploymentId="bundle-a", versionState="ready", secret="not-public")
        with patch.object(presenter, "execute_operation", side_effect=[dict(data=dict(publication=publication)), self.inventory(), self.inventory()]) as call:
            first, second = self.reader(), self.reader()
        self.assertEqual(3, call.call_count)
        self.assertEqual("19.0.0", first["publication"]["version"])
        self.assertNotIn("secret", first["publication"])
        self.assertEqual(first["publication"], second["publication"])
        self.assertEqual("18.0.0", first["value"]["installedVersion"])

    def test_preprovision_publication_is_visible_without_inventing_unit_installation(self):
        self.journal = dict(vehicles=dict(test=dict(localVmId="vm-b")), componentOperations={"19.0.0": dict(deploymentId="bundle-a")})
        self.write()
        with patch.object(presenter, "execute_operation", side_effect=[dict(data=dict(publication=dict(stage="PROCESSING"))), dict(state="BLOCKED")]):
            result = self.reader()
        self.assertEqual("vm-b:none", result["bindingKey"])
        self.assertIsNone(result["value"])
        self.assertEqual("PROCESSING", result["publication"]["stage"])

    def test_monitoring_is_fixed_test_cloud_operation(self):
        with patch.object(presenter, "execute_operation", return_value=dict(data=dict(unitId="unit-a"))) as call:
            self.assertEqual(dict(unitId="unit-a"), self.reader.monitoring())
        self.assertEqual(dict(domain="unit", action="monitoring", target="test"), call.call_args.args[0])

    def test_service_details_own_runtime_and_missing_details_are_not_absence(self):
        self.journal["serviceOperations"] = {"brake-id":dict(team="brake",test=dict(unitId="unit-a"))}
        self.write()
        result = self.inventory()
        result["data"]["services"]["value"] = [dict(service=dict(id="brake-id"))]
        row = dict(service=dict(id="brake-id"),service_versions=dict(installed_service_version=dict(version="7.0.0")),instances=dict(state="CURRENT",value=[]))
        result["data"]["serviceDetails"] = {"brake-id":dict(state="CURRENT",value=[row])}
        with patch.object(presenter,"execute_operation",return_value=result):
            data=self.reader()["value"]["inventory"]
        self.assertEqual([row],data["services"]["value"])
        self.assertEqual({"brake":"brake-id"},data["teamServiceIds"])
        result["data"]["serviceDetails"]["brake-id"] = dict(state="UNAVAILABLE",value=None)
        with patch.object(presenter,"execute_operation",return_value=result):
            data=self.reader()["value"]["inventory"]
        self.assertEqual("INCOMPLETE",data["services"]["state"])
        self.assertIsNone(data["services"]["value"])

    def test_older_profile_receipts_remain_visible_and_new_run_prunes_them(self):
        self.journal["componentOperations"] = {
            "19.0.0": dict(deploymentId="bundle-a"),
            "20.0.0": dict(deploymentId="bundle-b"),
        }
        self.write()
        ready = dict(data=dict(publication=dict(stage="READY")))
        with patch.object(presenter, "execute_operation", side_effect=[
            ready, self.inventory(), ready, self.inventory(), self.inventory(),
        ]) as call:
            self.reader()
            second = self.reader()
            self.assertEqual({"19.0.0", "20.0.0"}, {row["version"] for row in second["publications"]})
            self.assertEqual("20.0.0", second["publication"]["version"])
            self.journal = dict(vehicles=dict(test=dict(localVmId="vm-new")))
            self.write()
            final = self.reader()
        self.assertEqual([], final["publications"])
        self.assertIsNone(final["publication"])
        self.assertEqual("vm-new:none", final["bindingKey"])
        self.assertEqual(["20.0.0", "19.0.0"], [
            row.args[0]["component_version"] for row in call.call_args_list
            if row.args[0]["domain"] == "component"
        ])
