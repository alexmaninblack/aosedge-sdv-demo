# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
import copy
import unittest
from types import SimpleNamespace
import vision_model_probe as p


def sequence():
    return dict(kind='vision-camera-sequence',camera='forward-rgb-720p-fov50',source='source-generation',frames=[
        dict(frame=20+i*2,simulationTime=1+i*.1,file=str(20+i*2)+'.jpg',sha256='a'*64) for i in range(4)])


class ModelSequenceTests(unittest.TestCase):
    def test_exact_upstream_dynamic_batch_is_not_an_arbitrary_shape_override(self):
        spec=SimpleNamespace(type='tensor(float)',shape=['batch_size',3,512,1024])
        self.assertTrue(p.valid_input_shapes([spec]))
        self.assertFalse(p.valid_input_shapes([]))
        for shape in ([1,3,512,1024],['other',3,512,1024],['batch_size',3,720,1280]):
            self.assertFalse(p.valid_input_shapes([SimpleNamespace(type='tensor(float)',shape=shape)]))

    def test_real_ordered_pair_metadata(self):self.assertEqual(4,len(p.validate_sequence(sequence())))

    def test_gaps_and_duplicate_frames_are_not_faked_as_valid_pairs(self):
        for key,value in (('frame',20),('simulationTime',2.0)):
            data=sequence();data['frames'][1][key]=value
            with self.assertRaisesRegex(ValueError,'FRAME_PAIR_INTERVAL_INVALID|FRAME_FILE_INVALID'):p.validate_sequence(data)

    def test_only_the_bounded_declared_camera_sequence_is_accepted(self):
        for key,value in (('camera','unknown'),('kind','random-tensors'),('source',None),('frames',[])):
            data=sequence();data[key]=value
            with self.assertRaises(ValueError):p.validate_sequence(data)

    def test_file_traversal_rejected(self):
        data=sequence();data['frames'][0]['file']='../foreign.jpg'
        with self.assertRaisesRegex(ValueError,'FRAME_FILE_INVALID'):p.validate_sequence(data)

    def test_tensor_cost_only_preserves_irregular_source_timing_without_qualifying_pairs(self):
        data=sequence();data['frames'][1]['simulationTime']=1.05
        with self.assertRaisesRegex(ValueError,'FRAME_PAIR_INTERVAL_INVALID'):p.validate_sequence(data)
        self.assertEqual(1.05,p.validate_sequence(data,tensor_timing_only=True)[1]['simulationTime'])
        for value in (float('nan'),float('inf'),.5,2.):
            bad=copy.deepcopy(data);bad['frames'][1]['simulationTime']=value
            with self.assertRaises(ValueError):p.validate_sequence(bad,tensor_timing_only=True)

    def test_replay_preserves_the_recorded_source_not_the_new_load_source(self):
        data=sequence()
        replay=p.replay_manifest('new-live-source',data['frames'],data)
        self.assertEqual('source-generation',replay['source'])
        self.assertEqual(data['frames'],replay['frames'])
        with self.assertRaisesRegex(ValueError,'RETAINED_FRAME_METADATA_CHANGED'):
            p.replay_manifest('new-live-source',data['frames'][:-1],data)


if __name__=='__main__':unittest.main()
