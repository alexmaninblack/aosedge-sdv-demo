# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock,patch
import continuous_ui_campaign as campaign

def result(outcome='PASS',code='UNIT_CHECK_PASSED'):
    return dict(outcome=outcome,code=code,facts={})

class ContinuousEntry(unittest.TestCase):
    def test_preflight_refusal_never_starts_ui_or_publishes_and_still_closes(self):
        ops=SimpleNamespace(preflight=Mock(return_value=result('BLOCKED','TARGET_DESKTOP_NOT_UNLOCKED')),
                            prepare=Mock(),cleanup=Mock(return_value=result()))
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            with patch.object(campaign.common,'Operations',return_value=ops),patch.object(campaign.ui_pilot,'run') as ui,patch('builtins.print'):
                status=campaign.execute({'test':'test'},{},{'manifestSha256':'a'*64},root)
            self.assertEqual(status,2);ops.prepare.assert_not_called();ui.assert_not_called();ops.cleanup.assert_called_once()
            report=json.loads((root/'campaign-report.json').read_bytes())
            self.assertEqual(report['continuousCampaign'],'NOT_QUALIFIED');self.assertTrue(report['cleanupConfirmed'])
            self.assertEqual(report['fullE2E'],'NOT_COMPLETE')

    def test_uncertain_access_is_not_replayed_or_followed_by_ui(self):
        ops=SimpleNamespace(preflight=Mock(return_value=result()),prepare=Mock(return_value=result('UNCERTAIN','INPUT_UNCONFIRMED')),
                            cleanup=Mock(return_value=result()))
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            with patch.object(campaign.common,'Operations',return_value=ops),patch.object(campaign.ui_pilot,'run') as ui,patch('builtins.print'):
                self.assertEqual(campaign.execute({'test':'test'},{},{'manifestSha256':'a'*64},root),1)
            ops.prepare.assert_called_once();ui.assert_not_called();ops.cleanup.assert_called_once()

if __name__=='__main__':unittest.main()
