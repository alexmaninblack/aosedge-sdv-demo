# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
import unittest
from types import SimpleNamespace
from unittest.mock import Mock
from aosedge_demo_orchestrator.native_access import NativeVMAccess
from aosedge_demo_orchestrator.environment import EnvironmentError


class NativeAccessTests(unittest.TestCase):
    def test_keychain_reuse_has_no_dialog_and_no_public_secret(self):
        chain = Mock(read=Mock(return_value="fixture-private"))
        run, progress = Mock(), Mock()
        access = NativeVMAccess(progress, chain, run)
        self.assertEqual("fixture-private", access("test"))
        self.assertEqual("fixture-private", access("production"))
        chain.read.assert_called_once()
        run.assert_not_called()
        self.assertNotIn("fixture-private", str(progress.call_args_list))
        access.clear()
        self.assertIsNone(access.value)

    def test_save_requires_explicit_dialog_choice_and_secret_never_in_argv(self):
        for choice in ("Use once", "Save in Keychain"):
            chain = Mock(read=Mock(return_value=None))
            run = Mock(return_value=SimpleNamespace(returncode=0, stdout=choice + "\nfixture-private\n"))
            access = NativeVMAccess(keychain=chain, runner=run)
            self.assertEqual("fixture-private", access("test"))
            self.assertNotIn("fixture-private", str(run.call_args))
            self.assertEqual(choice == "Save in Keychain", chain.save.called)

    def test_cancel_stops_instead_of_hidden_terminal_fallback(self):
        chain = Mock(read=Mock(return_value=None))
        access = NativeVMAccess(keychain=chain, runner=Mock(return_value=SimpleNamespace(returncode=1)))
        with self.assertRaisesRegex(EnvironmentError, "CANCELLED"):
            access("test")
        chain.save.assert_not_called()
