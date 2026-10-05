# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import json
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import subprocess
from aosedge_demo_orchestrator import cloud_enrollment as enrollment, cloud_runtime
from aosedge_demo_orchestrator.environment import EnvironmentError, JOURNAL, atomic_json
import test_cloud_first_use as fixture


class EnrollmentOwnerTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixture.PairTests(); self.fixture.addCleanup = self.addCleanup; self.fixture.setUp()
        self.root = self.fixture.state
        self.command = ["/fixture/private-python", "-I", "-B", "/fixture/cloud_enrollment.py"]
        self.env = {"PATH":"/usr/bin:/bin", "AOSEDGE_CLOUD_RUNTIME":"/fixture"}
        mock = patch.object(cloud_runtime, "launch", return_value=(self.command,self.env))
        self.launch = mock.start(); self.addCleanup(mock.stop)
        self.reply = dict(domain="stage.example.test", role="oem", rolesChecked=False,
            enrollmentStage="NOT_STARTED", cloudAccessed=False)
    def run_action(self, action="status"):
        return enrollment.run_worker(self.root, "stage.example.test", "oem", action,
            "synthetic-private-token" if action=="enroll" else None)
    def test_success_and_secure_stdin_without_token_in_arguments_or_environment(self):
        with patch.object(subprocess,"run",return_value=SimpleNamespace(returncode=0,stdout=json.dumps(self.reply),stderr="")) as run:
            self.run_action("enroll")
        args, kwargs = run.call_args
        self.assertEqual((self.command,),args)
        self.assertEqual(self.env,kwargs["env"])
        self.assertNotIn("synthetic-private-token",json.dumps([args,kwargs["env"]]))
        self.assertEqual("synthetic-private-token",json.loads(kwargs["input"])["token"])
        self.assertEqual(75,kwargs["timeout"])
        self.assertFalse((self.root/JOURNAL).exists())
    def test_foreign_writer_blocks_before_launch(self):
        with self.fixture.env._writer(), self.assertRaisesRegex(EnvironmentError,"BUSY"):
            self.run_action()
        self.launch.assert_not_called()
    def test_retained_journal_blocks_before_launch(self):
        self.fixture.env._directory(".run/demo-current")
        atomic_json(self.root/JOURNAL,dict(kind="democtl.current-run"))
        with self.assertRaisesRegex(EnvironmentError,"RETAINED"): self.run_action()
        self.launch.assert_not_called()
    def test_timeout_is_not_replayed(self):
        with patch.object(subprocess,"run",side_effect=subprocess.TimeoutExpired("fixture",75)) as run:
            with self.assertRaisesRegex(ValueError,"INSPECT_ATTEMPT_BEFORE_RETRY"): self.run_action("enroll")
        self.assertEqual(1,run.call_count)
    def test_nonzero_stderr_oversize_or_wrong_scope_is_not_success(self):
        for reply in (SimpleNamespace(returncode=1,stdout="secret",stderr=""),
                      SimpleNamespace(returncode=0,stdout="x"*4097,stderr=""),
                      SimpleNamespace(returncode=0,stdout=json.dumps(self.reply),stderr="secret"),
                      SimpleNamespace(returncode=0,stdout=json.dumps(dict(self.reply,role="sp")),stderr="")):
            with patch.object(subprocess,"run",return_value=reply),self.assertRaises(ValueError) as caught: self.run_action()
            self.assertNotIn("secret",str(caught.exception))


if __name__ == "__main__": unittest.main()
