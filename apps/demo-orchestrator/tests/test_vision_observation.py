# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
import copy
import unittest
from aosedge_demo_orchestrator import vision_observation as v


class VisionObservationTests(unittest.TestCase):
    def test_empty_is_explicit_unavailable_not_a_retained_success(self):
        self.assertEqual(v.observation(v.unavailable()),v.unavailable())
        value=v.unavailable();value['state']='AVAILABLE'
        with self.assertRaises(ValueError):v.observation(value)

    def test_full_ids_unknown_fields_and_valid_data_on_unavailable_fail(self):
        for change in ({'sourceId':'11111111-1111-4111-8111-111111111111'},
                {'reference':'11111111-1111-4111-8111-111111111111'}, {'reason':'11111111-1111-4111-8111-111111111111'},
                {'frame':True},{'captureAgeMs':float('nan')}):
            with self.assertRaises(ValueError):v.observation(dict(v.unavailable(),**change))

    def test_shadow_data_has_bounded_plot_not_a_new_image_association(self):
        value=dict(v.unavailable(),state='AVAILABLE',reason='CURRENT',reference='vision-'+'a'*24,frame=40,cameraFrame=42,sequence=3,
            captureAgeMs=250.,perceptionVersion='0.1.0',assessmentVersion='0.1.0',
            lead=dict(valid=True,present=False,distanceMetres=None,relativeSpeedMps=None,distanceStddevMetres=None),
            path=dict(valid=True,points=[[float(i),0.] for i in range(16)],crossTrackMetres=0.,yawRadians=0.,curvaturePerMetre=0.),
            plan=dict(valid=False,accelerationMps2=None,firstSteeringRadians=None))
        self.assertFalse(v.observation(value)['imageMatched'])
        for bad in (dict(value,imageMatched=True),dict(value,state='UNAVAILABLE')):
            with self.assertRaises(ValueError):v.observation(bad)
        bad=copy.deepcopy(value);bad['path']['points'].append([17.,0.])
        with self.assertRaises(ValueError):v.observation(bad)


if __name__=='__main__':unittest.main()
