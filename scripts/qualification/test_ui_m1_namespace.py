# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
from pathlib import Path
import unittest
from ui_m1 import remote_run_directory

class Namespace(unittest.TestCase):
    def test_same_campaign_is_stable_but_repeated_ui_basename_is_isolated(self):
        root='/Users/test/SDV-Qualification/ui-tools/pin'
        first=Path('/private/campaign-one/ui');second=Path('/private/campaign-two/ui')
        self.assertEqual(remote_run_directory(root,first),remote_run_directory(root,first))
        self.assertNotEqual(remote_run_directory(root,first),remote_run_directory(root,second))
        self.assertTrue(remote_run_directory(root,first).startswith(root+'/runs/ui-'))

if __name__=='__main__':unittest.main()
