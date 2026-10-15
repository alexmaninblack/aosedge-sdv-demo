# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""First-use acceptance is additive; a green legacy UI report cannot fill it."""
from pathlib import Path
import copy
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from release_automation import CampaignError
from release_owners import Owners


class FirstUseTests(unittest.TestCase):
    def fixture(self):
        owner=object.__new__(Owners)
        owner.candidate=Path('/private/candidate')
        owner.config=dict(evidence=dict(firstUse='/private/report.json'),candidate=dict(manifestSha256='a'*64))
        value=dict(outcome='PASS',code='FIRST_USE_ACCEPTED',candidate='a'*64,
            tokensPersisted=False,workingKeysCopied=False,stages=[
                dict(stage='retire-and-park',status='PASS',facts={}),
                dict(stage='native-launch',status='PASS',facts=dict(nativeSource='b'*64,setupSha256='d'*64)),
                dict(stage='native-first-use',status='PASS',facts={}),
                dict(stage='independent-effects',status='PASS',facts=dict(newOemAndSpCertificates=True,
                    noTestCreated=True,cloudStage='READY',presenterObserved=True,domain='aoscloud.io')),
                dict(stage='closure',status='PASS',facts=dict(ownedDemoProcesses=0,
                    ownedDemoListeners=0,mediaDetached=True))])
        return owner,value

    def metadata(self,value):
        return lambda path: dict(binarySha256='d'*64) if str(path).endswith('build-receipt.json') else value

    def test_absent_gate_remains_absent(self):
        owner,_=self.fixture();owner.config['evidence']={}
        self.assertIsNone(owner.first_use())

    def test_complete_exact_evidence_accepted(self):
        owner,value=self.fixture()
        with patch('release_owners.metadata',side_effect=self.metadata(value)),patch('release_owners.sha',return_value='b'*64):
            self.assertEqual(owner.first_use()['candidate'],'a'*64)

    def test_partial_wrong_candidate_secrets_and_unclosed_owners_rejected(self):
        owner,base=self.fixture()
        for change in ('partial','candidate','secrets','cleanup','not-new','setup'):
            value=copy.deepcopy(base)
            if change=='partial':value['stages'].pop(2)
            if change=='candidate':value['candidate']='f'*64
            if change=='secrets':value['tokensPersisted']=True
            if change=='cleanup':value['stages'][-1]['facts']['ownedDemoProcesses']=1
            if change=='not-new':value['stages'][-2]['facts']['newOemAndSpCertificates']=False
            if change=='setup':value['stages'][1]['facts']['setupSha256']='f'*64
            with self.subTest(change=change),patch('release_owners.metadata',side_effect=self.metadata(value)),patch('release_owners.sha',return_value='b'*64):
                with self.assertRaises(CampaignError):owner.first_use()

    def test_changed_native_scenario_rejected(self):
        owner,value=self.fixture()
        with patch('release_owners.metadata',side_effect=self.metadata(value)),patch('release_owners.sha',return_value='c'*64):
            with self.assertRaisesRegex(CampaignError,'SOURCE_CHANGED'):owner.first_use()
