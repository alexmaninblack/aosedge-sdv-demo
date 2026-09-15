# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import json
import tempfile
import threading
import unittest
from collections import Counter
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from aosedge_demo_orchestrator import presenter
from aosedge_demo_orchestrator.environment import JOURNAL


class StudioReadPerformanceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        root = Path(self.directory.name)
        path = root / JOURNAL
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(dict(vehicles=dict(test=dict(localVmId="run-test")),
            componentOperations={"1.0.0": dict(deploymentId="bundle")})))
        self.application = SimpleNamespace(environment_service=SimpleNamespace(root=root))
        with patch("aosedge_demo_orchestrator.application.DemoOrchestrator", return_value=self.application):
            self.reader = presenter.StudioCloudReader()
        self.addCleanup(self.reader.pool.shutdown)
        self.calls = Counter()
        self.barrier = None
        self.component_stage = "PROCESSING"
        self.service_stage = "PROCESSING"

    def execute(self, request, application):
        self.assertIs(self.application, application)
        key = request["domain"] + "." + request["action"]
        self.calls[key] += 1
        if key == "service.releases":
            return dict(state="OBSERVED", data=dict(releases=[dict(runId="run-test", submitted=True,
                releaseHandle="brake/2.0.0", preparedAt="now", publication=dict(stage="PROCESSING"))]))
        if self.barrier:
            self.barrier.wait(timeout=1)
        if key == "component.cloud-status":
            return dict(data=dict(publication=dict(stage=self.component_stage, deploymentId="bundle")))
        if key == "service.cloud-status":
            return dict(data=dict(stage=self.service_stage, serviceId="service"))
        self.assertEqual("unit.cloud-status", key)
        self.assertEqual("test", request["target"])
        return dict(data=dict(unit=dict(state="CURRENT", value=dict(connectivity="ONLINE")),
            components=dict(value=[]), readCompletedAt="now"))

    def test_independent_cloud_reads_overlap_and_each_is_requested_once(self):
        self.barrier = threading.Barrier(3)
        with patch.object(presenter, "execute_operation", side_effect=self.execute):
            result = self.reader()
        self.assertEqual("CURRENT", result["state"])
        self.assertEqual("ONLINE", result["value"]["online"])
        self.assertEqual("PROCESSING", result["publication"]["stage"])
        self.assertEqual("PROCESSING", result["serviceReleases"][0]["publication"]["stage"])
        self.assertEqual({"service.releases": 1, "component.cloud-status": 1,
            "service.cloud-status": 1, "unit.cloud-status": 1}, self.calls)

    def test_terminal_component_error_is_not_repolled_on_every_inventory_refresh(self):
        self.component_stage = "ERROR"
        with patch.object(presenter, "execute_operation", side_effect=self.execute):
            first, second = self.reader(), self.reader()
        self.assertEqual("ERROR", first["publication"]["stage"])
        self.assertEqual("ERROR", second["publication"]["stage"])
        self.assertEqual(1, self.calls["component.cloud-status"])
        self.assertEqual(2, self.calls["unit.cloud-status"])

    def test_slow_publication_does_not_block_unit_or_duplicate_reads(self):
        released = threading.Event()
        self.addCleanup(released.set)
        original = self.execute
        def execute(request, application):
            if request["domain"] == "component":
                released.wait(2)
            return original(request, application)
        with patch.object(presenter, "execute_operation", side_effect=execute):
            first = self.reader()
            self.assertEqual("ONLINE", first["value"]["online"])
            self.assertIsNone(first["publication"])
            future = self.reader.publication_reads["component"][1]
            second = self.reader()
            self.assertIs(future, self.reader.publication_reads["component"][1])
            self.assertEqual("ONLINE", second["value"]["online"])
            released.set()
            future.result(timeout=1)
            third = self.reader()
            self.assertEqual("PROCESSING", third["publication"]["stage"])
            self.assertEqual(1, self.calls["component.cloud-status"])

    def test_publication_failure_does_not_turn_current_unit_offline(self):
        self.service_stage = "UNKNOWN"
        self.component_stage = "ERROR"
        with patch.object(presenter, "execute_operation", side_effect=self.execute):
            result = self.reader()
        self.assertEqual("ONLINE", result["value"]["online"])
        self.assertEqual("UNKNOWN", result["serviceReleases"][0]["publication"]["stage"])
        self.assertEqual("ERROR", result["publication"]["stage"])
