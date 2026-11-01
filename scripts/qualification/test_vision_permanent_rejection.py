# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
import copy
from pathlib import Path
import tempfile
import unittest
import vision_permanent_cloud as gate


class Cloud:
    user=dict(ownerId='fixture-owner')
    def __init__(self,changed=False,lost=False):
        self.writes=[];self.lost=lost
        self.value=dict(id=gate.FAILED_BATCH,oem_id=self.user['ownerId'],architectures=['arm64'],
            state='Waiting_validation',approval_states={},update_items=[dict(identity_id=gate.FAILED_COMPONENT,
                codename=gate.ROOTFS,version='6.1.1-vision-camera.9' if changed else '6.1.1-vision-camera.4')])
    def require(self,*values):pass
    def call(self,path,method='GET',data=None):
        assert path=='verification-batch/'+gate.FAILED_BATCH+'/'
        if method=='PATCH':
            assert data==[dict(architecture='arm64',is_approved=False)]
            self.writes.append(copy.deepcopy(data));self.value['approval_states']=dict(arm64=dict(is_approved=False))
            if self.lost:raise OSError('fixture lost response')
        else:assert method=='GET' and data is None
        return copy.deepcopy(self.value)


class RejectionTests(unittest.TestCase):
    def request(self,folder):
        return dict(operationDirectory=str(folder),vehicles=dict(test=dict(unitId=gate.CURRENT_UNIT)),
            rejectFailedRootfs=dict(authorized=True,batchId=gate.FAILED_BATCH,
                failedVersion='6.1.1-vision-camera.4',successorVersion=gate.VERSIONS[gate.ROOTFS]))
    def test_exact_one_patch_and_reconcile_without_replay(self):
        for lost in (False,True):
            with tempfile.TemporaryDirectory() as temporary:
                cloud=Cloud(lost=lost);r=self.request(Path(temporary))
                self.assertTrue(gate.reject_failed_rootfs(cloud,r)['confirmed'])
                self.assertTrue(gate.reject_failed_rootfs(cloud,r)['resumed'])
                self.assertEqual(len(cloud.writes),1)
    def test_changed_batch_is_read_only_failure(self):
        with tempfile.TemporaryDirectory() as temporary:
            cloud=Cloud(changed=True)
            with self.assertRaisesRegex(Exception,'BATCH_CHANGED'):gate.reject_failed_rootfs(cloud,self.request(Path(temporary)))
            self.assertEqual(cloud.writes,[])
    def test_unconfirmed_intent_never_replays(self):
        with tempfile.TemporaryDirectory() as temporary:
            cloud=Cloud();r=self.request(Path(temporary));gate.reject_failed_rootfs(cloud,r)
            cloud.value['approval_states']={}
            with self.assertRaisesRegex(Exception,'UNCERTAIN_NO_REPLAY'):gate.reject_failed_rootfs(cloud,r)
            self.assertEqual(len(cloud.writes),1)


if __name__=='__main__':unittest.main()
