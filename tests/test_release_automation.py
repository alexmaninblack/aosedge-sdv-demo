# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from release_automation import (CampaignError, STAGES, atomic, configuration,
                                execute, lease, read, safe)


class Owner:
    def __init__(self, fail=None):
        self.calls=[];self.verified=[];self.fail=fail;self.can_reconcile=False
    def stage(self,name):
        self.calls.append(name)
        if name == self.fail:
            raise CampaignError('EXPECTED_FAILURE')
        return {'receipt':name}
    def verify_saved(self,name,facts):
        if facts != {'receipt':name}:
            raise CampaignError('SAVED_RECEIPT_CHANGED')
        self.verified.append(name)
    def reconcile(self,name,previous):
        return self.can_reconcile


class CampaignTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.parent=Path(self.temp.name).resolve();self.root=self.parent/'candidate'
        self.binding={'schemaVersion':1,'source':'frozen'}
    def run_campaign(self,owner,**kw):
        return execute(self.root,self.binding,owner,emit=lambda x:None,**kw)
    def test_complete_order_and_single_submission(self):
        owner=Owner();r=self.run_campaign(owner)
        self.assertEqual(owner.calls,list(STAGES));self.assertTrue(r['complete'])
        self.assertEqual(r['outcome'],'PASS');self.assertFalse(r['agentStepScheduling'])
    def test_stop_boundary_is_partial_not_release_pass(self):
        owner=Owner();r=self.run_campaign(owner,until='qualification')
        self.assertEqual(r['outcome'],'PARTIAL');self.assertFalse(r['complete'])
        self.assertEqual(r['notRun'],list(STAGES[4:]));self.assertEqual(len(owner.calls),4)
    def test_fail_closes_later_gates(self):
        owner=Owner('artifact');r=self.run_campaign(owner)
        self.assertEqual(owner.calls,list(STAGES[:3]));self.assertEqual(r['outcome'],'BLOCKED')
        self.assertIn('publication',r['notRun'])
    def test_uncertain_main_does_not_publish(self):
        owner=Owner('main-integration');r=self.run_campaign(owner)
        self.assertEqual(r['outcome'],'UNCERTAIN');self.assertNotIn('publication',owner.calls)
    def test_resume_requires_explicit_mode(self):
        self.run_campaign(Owner(),until='freeze')
        with self.assertRaisesRegex(CampaignError,'EXISTING_CAMPAIGN'):
            self.run_campaign(Owner())
    def test_resume_revalidates_and_does_not_repeat_completed_stages(self):
        self.run_campaign(Owner(),until='artifact')
        owner=Owner();r=self.run_campaign(owner,resume=True)
        self.assertEqual(owner.verified,list(STAGES[:3]));self.assertEqual(owner.calls,list(STAGES[3:]))
        self.assertEqual(r['outcome'],'PASS')
    def test_readonly_failure_can_repeat_after_correction(self):
        self.run_campaign(Owner('source-gates'))
        owner=Owner();r=self.run_campaign(owner,resume=True)
        self.assertNotIn('freeze',owner.calls);self.assertEqual(r['outcome'],'PASS')
    def test_uncertain_mutation_cannot_blindly_repeat(self):
        self.run_campaign(Owner('publication'))
        owner=Owner()
        with self.assertRaisesRegex(CampaignError,'UNCERTAIN_MUTATION'):
            self.run_campaign(owner,resume=True)
        self.assertEqual(owner.calls,[])
    def test_rebinding_forbidden(self):
        self.run_campaign(Owner(),until='freeze');self.binding={'schemaVersion':1,'source':'changed'}
        with self.assertRaisesRegex(CampaignError,'REBINDING'):
            self.run_campaign(Owner(),resume=True)
    def test_corrupt_saved_receipt_is_not_reused(self):
        self.run_campaign(Owner(),until='freeze')
        p=self.root/'freeze.json';v=read(p);v['facts']={'receipt':'foreign'};atomic(p,v)
        with self.assertRaisesRegex(CampaignError,'SAVED_RECEIPT'):
            self.run_campaign(Owner(),resume=True)
        self.assertEqual(read(self.root/'report.json')['outcome'],'BLOCKED')
        self.assertFalse(read(self.root/'report.json')['complete'])
    def test_private_receipts_and_lease_released(self):
        self.run_campaign(Owner(),until='freeze')
        self.assertEqual((self.root/'report.json').stat().st_mode & 0o777,0o600)
        self.assertFalse(list(self.root.glob('*.pending')))
        with lease(self.root,self.binding):pass
    def test_single_writer(self):
        with lease(self.root,self.binding):
            with self.assertRaisesRegex(CampaignError,'ALREADY_ACTIVE'):
                self.run_campaign(Owner())
    def test_unknown_nonempty_directory_is_not_adopted(self):
        self.root.mkdir(mode=0o700);(self.root/'foreign').write_text('preserve')
        with self.assertRaisesRegex(CampaignError,'UNOWNED'):
            self.run_campaign(Owner())
        self.assertEqual((self.root/'foreign').read_text(),'preserve')
    def test_symlink_record_rejected(self):
        target=self.parent/'other';target.write_text('{}');os.chmod(target,0o600)
        link=self.parent/'linked';link.symlink_to(target)
        with self.assertRaises(CampaignError):read(link)
    def test_hardlink_record_rejected(self):
        target=self.parent/'other';target.write_text('{}');os.chmod(target,0o600)
        linked=self.parent/'linked';os.link(target,linked)
        with self.assertRaises(CampaignError):read(linked)
    def test_path_traversal_rejected(self):
        with self.assertRaises(CampaignError):safe(self.parent/'..'/'elsewhere')
    def test_duplicate_json_field_rejected(self):
        p=self.parent/'config';p.write_text('{"x":1,"x":2}');os.chmod(p,0o600)
        with self.assertRaisesRegex(CampaignError,'DUPLICATE'):read(p)
    def test_public_record_not_accepted_as_private(self):
        p=self.parent/'config';p.write_text('{}');os.chmod(p,0o644)
        with self.assertRaises(CampaignError):read(p)
    def test_interruption_closes_later_gates(self):
        class Interrupt(Owner):
            def stage(self,name):raise KeyboardInterrupt()
        r=self.run_campaign(Interrupt());self.assertEqual(r['outcome'],'BLOCKED')
        self.assertEqual(len(r['stages']),1)
    def test_invalid_stop_stage_rejected_before_writes(self):
        with self.assertRaises(CampaignError):self.run_campaign(Owner(),until='arbitrary-command')
        self.assertFalse(self.root.exists())


if __name__=='__main__':unittest.main()
