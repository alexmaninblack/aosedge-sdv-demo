# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import json
import unittest
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from aosedge_demo_orchestrator import presenter


class PresenterStopTests(unittest.TestCase):
    def run_stop(self, *, cwd="/fixture/apps/demo-orchestrator", active=None, absolute=False, user=501):
        def command(arguments, **_):
            if arguments[0] == "/bin/ps":
                script = "/fixture/apps/demo-orchestrator/.venv/bin/democtl" if absolute else ".venv/bin/democtl"
                return SimpleNamespace(stdout=f"{user} /fixed/Python {script} ui serve", returncode=0)
            if "-d" in arguments:
                self.assertIn("-a", arguments)  # No accidental all-process cwd scan.
                return SimpleNamespace(stdout=f"p123\nfcwd\nn{cwd}\n", returncode=0)
            return SimpleNamespace(stdout="123\n", returncode=0)
        opener = Mock()
        opener.open.return_value = BytesIO(json.dumps(dict(sessionId="fixture", active=active, uncertain=False)).encode())
        with patch.object(presenter, "project_root", return_value=Path("/fixture")), \
                patch("subprocess.run", side_effect=command), patch("urllib.request.build_opener", return_value=opener), \
                patch("os.getuid", return_value=501), patch("os.kill") as kill:
            result = presenter.stop()
        return result, kill

    def test_relative_command_requires_canonical_process_cwd(self):
        result, kill = self.run_stop()
        self.assertEqual(0, result)
        kill.assert_called_once()

    def test_foreign_relative_cwd_is_never_signalled(self):
        result, kill = self.run_stop(cwd="/unrelated")
        self.assertEqual(1, result)
        kill.assert_not_called()

    def test_busy_or_foreign_user_is_never_signalled(self):
        for values in (dict(active="running"), dict(user=502)):
            with self.subTest(values=values):
                result, kill = self.run_stop(**values)
                self.assertEqual(1, result)
                kill.assert_not_called()

    def test_canonical_absolute_command_remains_supported(self):
        result, kill = self.run_stop(absolute=True)
        self.assertEqual(0, result)
        kill.assert_called_once()
