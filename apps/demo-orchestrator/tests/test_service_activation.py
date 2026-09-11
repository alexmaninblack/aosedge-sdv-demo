# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import copy
import json
from pathlib import Path
import unittest
from unittest.mock import Mock

from aosedge_demo_orchestrator.service_activation_guest import compose, dropin_content
from aosedge_demo_orchestrator.api import execute_operation
from aosedge_demo_orchestrator.cli import build_parser, request_from_arguments


class NativeActivationTests(unittest.TestCase):
    def setUp(self):
        self.resources = [dict(name="unrelated", devices=["untouched"], groups=["group"]),
            dict(name="kuksa", hosts=[dict(hostname="Server", ip="10.0.0.100")]),
            dict(name="kuksa-auth-client", sharedCount=4, groups=["aos-kuksa-clients"], mounts=[
                dict(source="/run/aos-kuksa-auth-compat", destination="/run/aosedge/platform/kuksa-auth", type="bind",
                    options=["rbind", "ro", "nosuid", "nodev", "noexec"]),
                dict(source="tmpfs", destination="/run/aosedge/secrets/kuksa", type="tmpfs",
                    options=["rw", "nosuid", "nodev", "noexec", "mode=0700", "size=65536"])])]

    def test_only_declared_mounts_change_and_repeat_is_idempotent(self):
        original = copy.deepcopy(self.resources)
        result = compose(self.resources)
        self.assertEqual(original, self.resources)
        self.assertEqual(original[:2], result[:2])
        self.assertEqual(original[2]["mounts"][0], result[2]["mounts"][0])
        self.assertEqual(original[2]["groups"], result[2]["groups"])
        self.assertEqual(4, result[2]["sharedCount"])
        self.assertIn("mode=1777", result[2]["mounts"][1]["options"])
        self.assertEqual(result, compose(result))
        for team, resource in zip(("brake", "tire"), result[-2:]):
            self.assertEqual(team + "-runtime-inputs", resource["name"])
            self.assertEqual("/run/aos-demo-service-inputs/" + team, resource["mounts"][0]["source"])
            self.assertEqual(["bind", "ro", "nosuid", "nodev", "noexec"], resource["mounts"][0]["options"])

    def test_foreign_or_ambiguous_mounts_fail_without_modification(self):
        for wrong in ([*self.resources, self.resources[0]],
                [*self.resources, dict(name="brake-runtime-inputs", mounts=[])],
                self.resources[:2]):
            before = copy.deepcopy(wrong)
            with self.assertRaises(ValueError):
                compose(wrong)
            self.assertEqual(before, wrong)
        self.resources[2]["mounts"][1]["options"].append("exec")
        with self.assertRaisesRegex(ValueError, "OPTIONS_MISMATCH"):
            compose(self.resources)

    def test_native_configuration_has_no_executable_override_or_container_launcher(self):
        content = dropin_content()
        self.assertNotIn("ExecStart=", content)
        self.assertNotIn("aos_sm_app", content)
        self.assertNotIn("crun", content)
        self.assertIn("inputs.py cold", content)
        self.assertIn("inputs.py verify", content)
        self.assertIn("resources.cfg:/etc/aos/resources.cfg", content)
        request = request_from_arguments(build_parser().parse_args(["service", "runtime-activate", "test"]))
        self.assertEqual("service", request.domain)
        with self.assertRaises(ValueError):
            execute_operation(dict(domain="service", action="runtime-activate", target="test"), Mock())
