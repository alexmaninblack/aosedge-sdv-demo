# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Private state and reference consumption; synthetic Cloud replies only."""

import copy
import json
import os
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from aosedge_demo_orchestrator import subject_first_use as subjects
from aosedge_demo_orchestrator.cloud_connection import CloudConnection, CONFIG, inspect_certificate, bind_tenant
from aosedge_demo_orchestrator.cloud_setup import CloudSetup
from aosedge_demo_orchestrator.environment import EnvironmentError, JOURNAL, atomic_json
from aosedge_demo_orchestrator.service_assignment import LABELS
import test_cloud_first_use as pair_fixture
import test_subject_first_use as subject_fixture
from aosedge_demo_orchestrator.unit_cloud import CloudFailure
from test_service_assignment import OWNER, SP, BRAKE, SUBJECT, UNIT


class ReferencePersistenceTests(unittest.TestCase):
    def setUp(self):
        self.pair = pair_fixture.PairTests(); self.pair.addCleanup = self.addCleanup; self.pair.setUp()
        self.pair.save(self.pair.preview()["selectionToken"])
        self.clouds = subject_fixture.SubjectProof(); self.clouds.setUp()
        self.clouds.cloud.pages = lambda path: [dict(id=SP)] if path == "service-providers/" else []
        self.units = SimpleNamespace(environment=self.pair.env, root=self.pair.state, _cloud=self.call)
        self.service = subjects.FirstUseSubjects(self.units)
        self.request = dict(cloudDomain="stage.example.test", spCredential=str(self.pair.sp))
        for mock in (patch.object(CloudConnection, "inspect", side_effect=inspect_certificate),
                     patch.object(CloudSetup, "_request", return_value=self.request)):
            mock.start(); self.addCleanup(mock.stop)
    def call(self, action, **values):
        try: return subjects.execute(self.clouds.cloud, self.clouds.provider, dict(values, action=action))
        except CloudFailure as error: raise EnvironmentError(str(error)) from None
    def run_action(self, reference=None, token=None):
        return self.service.perform(str(self.pair.oem), str(self.pair.sp),
            token or self.pair.preview()["selectionToken"], reference)
    def tearDown(self):
        self.assertEqual([], self.clouds.cloud.posts)
        self.assertEqual([], self.clouds.provider.posts)

    def test_inspection_saves_nothing_and_selection_is_exact_and_idempotent(self):
        path = self.pair.state/CONFIG
        before = path.read_bytes()
        result = self.run_action()
        self.assertEqual(before, path.read_bytes())
        self.assertEqual(["ELIGIBLE", "ELIGIBLE"], [r["state"] for r in result["subjects"]])
        self.assertTrue(all("reference" in r for r in result["subjects"]))
        self.run_action(self.clouds.reference())
        saved = (path.read_bytes(), path.stat().st_mtime_ns)
        self.run_action(self.clouds.reference())
        self.assertEqual(saved, (path.read_bytes(), path.stat().st_mtime_ns))
        self.run_action(self.clouds.reference("tire"))
        context = next(iter(json.loads(path.read_bytes())["cloudSetupContexts"].values()))
        self.assertEqual({"brake","tire"}, set(context["subjectReferences"]))
        self.assertFalse((self.pair.state/JOURNAL).exists())

    def test_bound_subjects_remain_blocked_and_are_never_saved(self):
        self.clouds.cloud.assigned = [dict(id=UNIT)]
        self.clouds.cloud.tire_reported = [dict(id=UNIT)]
        rows = self.run_action()["subjects"]
        self.assertEqual(["BLOCKED", "BLOCKED"], [r["state"] for r in rows])
        self.assertTrue(all("reference" not in r for r in rows))
        with self.assertRaisesRegex(ValueError, "STILL_HAS_UNITS"):
            self.run_action(self.clouds.reference())
        self.assertNotIn("subjectReferences", (self.pair.state/CONFIG).read_text())

    def test_new_recipient_and_changed_certificate_between_inspect_and_save_block(self):
        result = self.run_action()
        self.clouds.cloud.reported = [dict(id=UNIT)]
        with self.assertRaisesRegex(ValueError, "STILL_HAS_UNITS"):
            self.run_action(self.clouds.reference(), result["selectionToken"])
        self.clouds.cloud.reported = []
        os.utime(self.pair.oem, None)
        with self.assertRaisesRegex(ValueError, "CHANGED_SINCE_PREVIEW"):
            self.run_action(self.clouds.reference(), result["selectionToken"])

    def test_during_read_configuration_change_does_not_get_overwritten(self):
        original = self.units._cloud
        def changed(action, **values):
            result = original(action, **values)
            config = json.loads((self.pair.state/CONFIG).read_bytes())
            config["peerEvidence"] = True
            atomic_json(self.pair.state/CONFIG, config)
            return result
        self.units._cloud = changed
        with self.assertRaisesRegex(ValueError, "CHANGED_SINCE_PREVIEW"):
            self.run_action(self.clouds.reference())
        self.assertTrue(json.loads((self.pair.state/CONFIG).read_bytes())["peerEvidence"])

    def test_service_assignment_consumes_only_matching_reference_and_rereads(self):
        self.run_action(self.clouds.reference())
        state = {}
        scope = bind_tenant(state, "stage.example.test", dict(oem=OWNER, sp=SP))
        scope["cloudBinding"] = dict(ownerId=OWNER)
        publication = dict(team="brake", serviceProviderId=SP, publishedVersion="8.0.0")
        result = subjects.selected_reference(self.units, state, publication, BRAKE)
        self.assertEqual(SUBJECT, result["id"])
        self.assertEqual("CONFIRMED", result["create"]["stage"])
        self.assertFalse(result["create"]["attempted"])
        self.clouds.cloud.service_recipients[BRAKE] = [dict(id=UNIT)]
        with self.assertRaisesRegex(ValueError, "HAS_RECIPIENTS"):
            subjects.selected_reference(self.units, state, publication, BRAKE)
        with self.assertRaisesRegex(ValueError, "BINDING_CHANGED"):
            subjects.selected_reference(self.units, state, dict(publication, serviceProviderId=UNIT), BRAKE)

    def test_missing_or_incomplete_inventory_does_not_authorize_reuse(self):
        self.clouds.cloud.pages = lambda path: []
        with self.assertRaisesRegex(ValueError, "ASSOCIATION_REQUIRED"): self.run_action()
        self.clouds.cloud.pages = lambda path: [dict(id=SP)]
        self.clouds.cloud.subjects = []
        self.assertEqual([], self.run_action()["subjects"])
        with self.assertRaisesRegex(ValueError, "NOT_UNIQUE"):
            self.run_action(self.clouds.reference())

    def test_exact_reference_replacement_is_blocked(self):
        reference = self.clouds.reference()
        self.run_action(reference)
        replacement = dict(reference, createdBy=UNIT)
        self.clouds.cloud.subjects[1]["created_by"] = UNIT
        with self.assertRaisesRegex(ValueError, "REPLACEMENT_BLOCKED"): self.run_action(replacement)

    def test_retained_run_blocks_before_cloud(self):
        self.pair.env._directory(".run/demo-current")
        atomic_json(self.pair.state/JOURNAL, dict(kind="democtl.current-run"))
        with patch.object(self.units, "_cloud") as cloud:
            with self.assertRaisesRegex(ValueError, "RETAINED"): self.run_action()
            cloud.assert_not_called()


if __name__ == "__main__": unittest.main()
