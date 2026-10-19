# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest
from unittest.mock import Mock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from release_automation import CampaignError
from release_operator_proof import allowed_amendment,retained_recovery_allowed
import release_operator_proof as operator


class AmendmentTests(unittest.TestCase):
    def test_explicit_operator_only_scope(self):
        allowed_amendment(['scripts/launcher/drive-download-macos.pl','tests/test_drive_download_parser.py'],[])
    def test_packaged_product_or_empty_scope_is_not_a_tooling_correction(self):
        for paths in ([],['apps/demo-orchestrator/src/aosedge_demo_orchestrator/vm.py'],
                      ['scripts/distribution/setup_build.py'],['workspace/repositories.json']):
            with self.assertRaises(CampaignError):allowed_amendment(paths,[])
    def test_existing_catalog_projection_is_explicit_not_arbitrary(self):
        allowed_amendment(['workspace/launcher-catalog.json'],['workspace/launcher-catalog.json'])
        with self.assertRaises(CampaignError):allowed_amendment(['workspace/foreign.json'],[])

    def test_retained_recovery_requires_exact_known_prelaunch_guard_and_closed_consumer(self):
        failed=dict(outcome='BLOCKED',facts=dict(cleanupConfirmed=True))
        stage=dict(outcome='UNCERTAIN',code='INSTALLED_CURRENT_RUN_RETAINED',facts={})
        self.assertTrue(retained_recovery_allowed(failed,stage))
        for code in ('OPERATOR_HANDOFF_UNCONFIRMED','SELECTION_STALE_REVISION',
                     'OPERATOR_PRESENTER_NOT_OBSERVED','INSTALLED_USAGE_UNKNOWN'):
            self.assertFalse(retained_recovery_allowed(failed,dict(stage,code=code)))
        for bad in (dict(outcome='BLOCKED',facts={}),dict(outcome='PASS',facts=failed['facts']),
                    dict(outcome='BLOCKED',facts=dict(cleanupConfirmed=True,presenterObserved=True))):
            self.assertFalse(retained_recovery_allowed(bad,stage))
        self.assertFalse(retained_recovery_allowed(failed,dict(stage,outcome='PASS')))
        self.assertFalse(retained_recovery_allowed(failed,dict(stage,facts=dict(launchStarted=True))))

    def proof(self,*,media_identity=None,changed=False,mounted=False,busy=False,bad_digest=False,bad_path=False):
        target='/Users/test/SDV-Qualification/operator-1.2.0-rc.3-dropbox/sdv/cache/release.dmg'
        identity='1:2:123:4:5:600'
        media=Mock()
        media.file_identity.side_effect=[identity,identity if not changed else '1:2:123:4:6:600']
        media.remote.return_value=('c' if bad_digest else 'b')*64+'  '+target
        media.attachments.return_value=[{'image-path':target}] if mounted else []
        owner=SimpleNamespace(config=dict(version='1.2.0-rc.3',delivery=dict(provider='dropbox')),
            remote=Mock(return_value=dict(demoProcesses=int(busy),busyPorts=0)))
        failed=dict(remoteDmg=target if not bad_path else '/foreign/release.dmg',launcherSha256='a'*64)
        with patch.object(operator,'connection',return_value=(None,None,dict(user='test'),{})), \
             patch.object(operator,'descriptor',return_value=dict(file='release.dmg',bytes=123,sha256='b'*64)), \
             patch.object(operator,'sha',return_value='a'*64), \
             patch.dict(sys.modules,{'campaign':SimpleNamespace(Media=Mock(return_value=media))}):
            result=operator.prove_retained_delivery(owner,failed,media_identity)
        return result,media

    def test_reconciliation_verifies_exact_bytes_once_then_reuses_unchanged_identity(self):
        result,media=self.proof()
        self.assertEqual(result['mediaIdentity'],'1:2:123:4:5:600')
        media.remote.assert_called_once()
        _,media=self.proof(media_identity=result['mediaIdentity'])
        media.remote.assert_not_called()

    def test_reconciliation_rejects_foreign_changed_mounted_or_active_delivery(self):
        for options in (dict(bad_path=True),dict(bad_digest=True),dict(changed=True),
                        dict(mounted=True),dict(busy=True),dict(media_identity='foreign')):
            with self.subTest(options=options),self.assertRaises(CampaignError):
                self.proof(**options)
