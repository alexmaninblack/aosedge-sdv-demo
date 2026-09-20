# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
import unittest
from test_cloud_observation import cloud, unit, UNIT_PATH, IDENTITY, SERVICE, SUBJECT
from aosedge_demo_orchestrator.cloud_observation import monitoring_history, unavailable
from aosedge_demo_orchestrator.unit_cloud import CloudFailure

PATH = UNIT_PATH + "monitoring/dashboard/"


class HistoryTests(unittest.TestCase):
    def read(self, row):
        return monitoring_history(cloud({UNIT_PATH: unit(), PATH: row}), IDENTITY)["history"]

    def test_fixed_request_authority_and_denial(self):
        transport = cloud({UNIT_PATH: unit()})
        def require(permission):
            if permission == "units_monitoring_dashboard":
                raise CloudFailure("OEM_PERMISSION_MISSING:units_monitoring_dashboard")
        transport.require.side_effect = require
        result = monitoring_history(transport, IDENTITY)
        self.assertEqual("FORBIDDEN", result["history"]["transport"])
        self.assertEqual(1, transport.call.call_count)
        self.assertIn("history", unavailable(IDENTITY, "monitoring-history", "OFFLINE"))

    def test_both_service_shapes_zero_null_decimal_and_instant_dedup(self):
        points = [["2026-09-20T10:01:00+01:00", 1.5], ["2026-09-20T09:00:00Z", 0],
                  ["2026-09-20T09:01:00Z", 1.5], ["2026-09-20T09:02:00Z", None]]
        service = dict(serviceId=SERVICE, subjectId=SUBJECT, instance="0", cpu=points, ram=[])
        for services in ([service], {"opaque-key": service}):
            result = self.read([{"node-a": dict(cpu=points, ram=[], services=services)}])
            self.assertEqual("CURRENT", result["state"])
            rows = result["value"]["series"]
            self.assertEqual(4, len(rows))
            self.assertEqual(3, len(rows[0]["points"]))
            self.assertEqual(0, rows[0]["points"][0][1])
            self.assertEqual(0, rows[2]["instance"])
            self.assertEqual("DMIPS", rows[0]["unit"])
            self.assertEqual("bytes", rows[1]["unit"])
            self.assertEqual("CLOUD_OEM_RAM_BYTES", rows[1]["unitEvidence"])

    def test_conflicting_points_are_gaps_not_arbitrary_values(self):
        result = self.read([{"node": {"cpu": [["2026-09-20T00:00:00Z", 1], ["2026-09-20T00:00:00Z", 2]]}}])
        self.assertEqual("INCOMPLETE", result["value"]["series"][0]["state"])
        self.assertIsNone(result["value"]["series"][0]["points"][0][1])

    def test_empty_missing_malformed_bounds_foreign_and_unzoned(self):
        self.assertEqual([], self.read([])["value"]["series"])
        self.assertEqual("UNKNOWN", self.read([{"node": {}}])["value"]["series"][0]["state"])
        for raw in ({}, [{"node": {"cpu": [["not-time", 1]]}}],
                    [{"node": {"cpu": [["2026-09-20T00:00:00", 1]]}}],
                    [{"node": {"cpu": [["2026-09-20T00:00:00Z", True]]}}],
                    [{"node": {"cpu": [["2026-09-20T00:00:00Z", float("nan")]]}}],
                    [{"node": {"cpu": [None] * 1001}}], [{"node": {"system_uid": "foreign"}}],
                    [{"node": {"services": [dict(serviceId=SERVICE, subjectId=SUBJECT, instance=True)]}}]):
            with self.subTest(raw=str(raw)[:60]):
                self.assertIsNone(self.read(raw)["value"])
