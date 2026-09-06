# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from aosedge_demo_orchestrator.source_guest import clock_status


class ClockObservationTests(unittest.TestCase):
    def test_native_clock_observation_is_read_only_and_bounded(self):
        answer = SimpleNamespace(returncode=0, stdout="NTP=yes\nNTPSynchronized=yes\n"
            "ServerName=time3.google.com\nNTPMessage={ PacketCount=9, Jitter=2.840ms }\n"
            "Unrelated=SECRET_FIXTURE\nServerName=" + "x" * 2100 + "\n", stderr="SECRET_FIXTURE")
        with patch("aosedge_demo_orchestrator.source_guest.command", return_value=answer) as command, \
             patch("aosedge_demo_orchestrator.source_guest.time.time", return_value=100.5):
            result = clock_status()
        self.assertEqual(100500, result["guestEpochMilliseconds"])
        self.assertEqual(3, command.call_count)
        self.assertEqual(["show", "show-timesync", "show"], [call.args[0][1] for call in command.call_args_list])
        self.assertEqual(4, len(result["synchronization"]["fields"]))
        self.assertNotIn("SECRET_FIXTURE", json.dumps(result))
        self.assertNotIn("x" * 2100, json.dumps(result))

    def test_missing_tool_or_failed_read_is_not_synchronized(self):
        with patch("aosedge_demo_orchestrator.source_guest.command", side_effect=[
            FileNotFoundError(), SimpleNamespace(returncode=1, stdout=""),
            SimpleNamespace(returncode=0, stdout="LoadState=not-found\nActiveState=inactive\n")]):
            result = clock_status()
        self.assertEqual("TOOL_NOT_INSTALLED", result["settings"]["state"])
        self.assertEqual(1, result["synchronization"]["exitCode"])
        self.assertEqual([], result["synchronization"]["fields"])


if __name__ == "__main__":
    unittest.main()
