# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
import tempfile
import json
import unittest
from pathlib import Path
from aosedge_demo_orchestrator.backend_context import project_context, sync_context, CONTEXT
from aosedge_demo_orchestrator.environment import EnvironmentService, EnvironmentError


def vehicle(uid):
    return dict(systemUid=uid, unitId="unit-" + uid, nodeId="node-" + uid, cloud=dict(lifecycle="ONLINE"))


class BackendContextTests(unittest.TestCase):
    def test_projection_is_only_owned_identity_not_runtime_or_cloud_state(self):
        state = dict(vehicles=dict(test=vehicle("test-uid")))
        value = project_context(state)
        self.assertEqual({"schemaVersion", "contractVersion", "source", "testUnit"}, set(value))
        self.assertEqual("VALIDATION", value["testUnit"]["unitRole"])
        state["vehicles"]["production"] = vehicle("prod-uid")
        self.assertEqual("PRODUCTION", project_context(state)["productionUnit"]["unitRole"])
        state["vehicles"]["production"]["systemUid"] = "test-uid"
        with self.assertRaises(EnvironmentError):
            project_context(state)

    def test_no_test_or_partial_sdk_does_not_create_a_context(self):
        for vehicles in ({}, dict(test={}), dict(production=vehicle("prod")),
                         dict(test=dict(systemUid="partial", unitId="unit"))):
            with self.assertRaises(EnvironmentError):
                project_context(dict(vehicles=vehicles))

    def test_retiring_uid_stays_until_explicit_cleanup_and_no_silent_rebind(self):
        with tempfile.TemporaryDirectory() as directory:
            env = EnvironmentService(Path(directory))
            state = dict(vehicles=dict(test=vehicle("test-uid")))
            self.assertEqual("BOUND", sync_context(env, state)["state"])
            original = (env.root / CONTEXT).read_bytes()
            state["vehicles"]["test"]["cloud"]["lifecycle"] = "DELETED"
            self.assertEqual("UNCHANGED", sync_context(env, state)["state"])
            state["vehicles"]["test"] = vehicle("replacement")
            with self.assertRaisesRegex(EnvironmentError, "CLEANUP_REQUIRED"):
                sync_context(env, state)
            self.assertEqual(original, (env.root / CONTEXT).read_bytes())

    def test_dual_role_can_add_production_without_changing_the_test(self):
        with tempfile.TemporaryDirectory() as directory:
            env = EnvironmentService(Path(directory))
            state = dict(vehicles=dict(test=vehicle("test-uid")))
            sync_context(env, state)
            state["vehicles"]["production"] = vehicle("prod-uid")
            self.assertEqual("BOUND", sync_context(env, state)["state"])
            state["vehicles"].pop("production")
            with self.assertRaisesRegex(EnvironmentError, "CLEANUP_REQUIRED"):
                sync_context(env, state)

    def test_invalid_previous_context_is_not_silently_adopted(self):
        with tempfile.TemporaryDirectory() as directory:
            env = EnvironmentService(Path(directory))
            state = dict(vehicles=dict(test=vehicle("test-uid")))
            sync_context(env, state)
            path = env.root / CONTEXT
            malformed = json.loads(path.read_text())
            malformed["source"] = "UNTRUSTED_SOURCE"
            path.chmod(0o600)
            path.write_text(json.dumps(malformed))
            state["vehicles"]["production"] = vehicle("prod-uid")
            with self.assertRaisesRegex(EnvironmentError, "CLEANUP_REQUIRED"):
                sync_context(env, state)

    def test_only_nonsecret_export_is_readable_by_container_uid(self):
        with tempfile.TemporaryDirectory() as directory:
            env = EnvironmentService(Path(directory))
            sync_context(env, dict(vehicles=dict(test=vehicle("test-uid"))))
            path = env.root / CONTEXT
            self.assertEqual(0o444, path.stat().st_mode & 0o777)
            self.assertEqual(0o755, path.parent.stat().st_mode & 0o777)
            self.assertEqual(0o700, (env.root / ".run/demo-current").stat().st_mode & 0o777)
            self.assertEqual({"contractVersion", "schemaVersion", "source", "testUnit"}, set(json.loads(path.read_text())))
