# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
import contextlib
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from aosedge_demo_orchestrator.releases import ReleaseContinuity
from aosedge_demo_orchestrator.environment import EnvironmentError
from aosedge_demo_orchestrator.cli import build_parser, request_from_arguments
from aosedge_demo_orchestrator.api import execute_operation
from unittest.mock import Mock


class ReleaseContinuityTests(unittest.TestCase):
    def test_symlinked_continuity_directory_is_not_followed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            outside = root / "other"
            outside.mkdir()
            (root / ".local").symlink_to(outside, target_is_directory=True)
            ledger = ReleaseContinuity(SimpleNamespace(root=root, _writer=contextlib.nullcontext))
            with self.assertRaisesRegex(EnvironmentError, "UNSAFE"):
                ledger.reserve("vdp")
            self.assertEqual([], list(outside.iterdir()))

    def test_api_and_cli_share_the_same_test_and_profile_selectors(self):
        app = Mock()
        for payload in (dict(domain="demo", action="plan", image="31/arm64", target="test"),
                        dict(domain="vehicle", action="initialize", target="test"),
                        dict(domain="component", action="prepare", content_profile="v3")):
            execute_operation(payload, app)
            request = app.execute.call_args.args[0]
            self.assertEqual(payload["domain"], request.domain)
            if request.domain == "component":
                self.assertIsNone(request.component_version)
                self.assertEqual("v3", request.content_profile)
            else:
                self.assertEqual("test", request.target.value)
        with self.assertRaises(ValueError):
            execute_operation(dict(domain="vehicle", action="initialize", target="production"), app)

    def test_reservations_survive_lost_run_and_never_rewind(self):
        with tempfile.TemporaryDirectory() as directory:
            env = SimpleNamespace(root=Path(directory), _writer=contextlib.nullcontext)
            ledger = ReleaseContinuity(env)
            self.assertEqual("17.0.0", ledger.reserve("vdp", ["16.9.1"]))
            ledger.remember("vdp", "12.0.0")
            self.assertEqual("18.0.0", ReleaseContinuity(env).reserve("vdp"))
            self.assertEqual("1.0.0", ledger.reserve("brake"))
            self.assertEqual("1.0.0", ledger.reserve("tire"))
            self.assertEqual({"schemaVersion", "versions"}, set(ledger.read()))
            with self.assertRaises(EnvironmentError):
                ledger.reserve("foreign")

    def test_cli_exposes_test_defaults_and_automatic_profile_release(self):
        parser = build_parser()
        for words in (["demo", "plan", "--image", "31/arm64"], ["vehicle", "initialize", "test"]):
            self.assertEqual("test", request_from_arguments(parser.parse_args(words)).target.value)
        request = request_from_arguments(parser.parse_args(["component", "prepare", "--profile", "v2"]))
        self.assertIsNone(request.component_version)
        self.assertEqual("v2", request.content_profile)
