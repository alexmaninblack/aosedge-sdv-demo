# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Proposal consistency only; no runtime permission or live acceptance."""
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]


class IngressProposalTests(unittest.TestCase):
    def setUp(self):
        self.value=json.loads((ROOT/'contracts/vision-vm/camera-ingress.proposal.v1.json').read_bytes())

    def test_proposal_cannot_be_mistaken_for_runtime_authorization(self):
        self.assertEqual(self.value['status'],'PROPOSED_REQUIRES_INTERFACE_AND_TRUST_SCOPE_ACCEPTANCE')
        self.assertIs(self.value['runtimeEnabled'],False)

    def test_same_vision_instance_and_two_product_vms(self):
        selected=json.loads((ROOT/'contracts/vision-vm/bootstrap.v1.json').read_bytes())
        topology=self.value['productTopology']
        self.assertEqual(topology['functionalVms'],2)
        self.assertEqual(topology['currentValidationInstance'],selected['nativeInstanceName'])
        self.assertFalse(topology['newVm'])
        self.assertFalse(topology['cloudMutationForIngress'])

    def test_read_only_vision_endpoint_and_separate_application_boundary(self):
        endpoint=self.value['hostEndpoint'];authorization=self.value['authorization']
        self.assertEqual(endpoint['method'],'GET')
        self.assertEqual(endpoint['responseType'],'multipart/x-mixed-replace')
        self.assertFalse(endpoint['queryParameters'])
        self.assertFalse(endpoint['redirects'])
        self.assertFalse(endpoint['configurableOperatorUrl'])
        self.assertFalse(authorization['motionAuthority'])
        self.assertFalse(authorization['cameraConfigurationAuthority'])
        self.assertEqual(authorization['activeMediaSessions'],1)
        self.assertIn('PLATFORM_UPDATE_RUNTIME',authorization['rejectedRoles'])

    def test_existing_frame_and_pair_limits_are_not_relaxed(self):
        capture=self.value['capture'];bounds=self.value['bounds']
        self.assertEqual((capture['width'],capture['height'],capture['horizontalFovDegrees']),(1280,720,50))
        self.assertEqual(capture['clock'].split(' with ')[0],'CARLA_WORLD_SNAPSHOT_FRAME_MATCH')
        self.assertEqual(bounds['metadataHeaderBytes'],4096)
        self.assertEqual(bounds['jpegBytes'],4*1024**2)
        self.assertEqual(bounds['cameraRetainedFrames'],2)
        self.assertEqual(bounds['cameraRetainedJpegBytes'],8*1024**2)
        self.assertEqual(bounds['pairIntervalNs'],[80000000,120000000])
        self.assertEqual(bounds['localDeliveryAgeSeconds'],1)


if __name__=='__main__':unittest.main()
