# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Retained bindings survive independent image builds, never changed inputs."""
import unittest
from unittest.mock import Mock

from journey_worker import retained_backend_images, retained_backend_prerequisites, launcher_prerequisites


class RetainedInputs(unittest.TestCase):
    def fixture(self):
        state={'backends':{}}
        images={};candidates={}
        for i,team in enumerate(('brake','tire'),1):
            source=str(i)*40;identity='sha256:'+str(i)*64
            row=dict(state='STOPPED',sourceRevision=source,imageId=identity,
                     mockCleanupProtocol='isolated-mock-v1')
            if team=='tire':row['privateCleanupProtocol']='tire-product-v1'
            state['backends'][team]=row
            candidates[team]={**row,'imageId':'sha256:'+str(i+2)*64}
            images[identity]=dict(Id=identity,Architecture='arm64',Os='linux',
                Config=dict(Labels={'tech.aosedge.demo.team':team,
                                   'org.opencontainers.image.revision':source}))
        owner=Mock();owner._candidate.side_effect=lambda team:candidates[team]
        owner._image.side_effect=lambda identity:images[identity]
        return state,owner,candidates,images

    def test_rebuilt_candidate_id_does_not_replace_verified_retained_binding(self):
        state,owner,_,_=self.fixture()
        self.assertEqual(retained_backend_images(state,owner),
            dict(imagesVerified=2,importAttempted=False,backendBindingsPreserved=True))
        self.assertEqual([x.args[0] for x in owner._image.call_args_list],
                         [state['backends'][t]['imageId'] for t in ('brake','tire')])
        owner.activate.assert_not_called();owner.start_stack.assert_not_called()

    def test_changed_source_or_protocol_is_not_accepted(self):
        for key,value in (('sourceRevision','f'*40),('mockCleanupProtocol','other'),
                          ('privateCleanupProtocol','other')):
            state,owner,candidates,_=self.fixture();candidates['tire'][key]=value
            with self.assertRaisesRegex(ValueError,'RETAINED_BACKEND_INPUTS_INCOMPATIBLE'):
                retained_backend_images(state,owner)

    def test_running_missing_or_changed_retained_image_is_not_accepted(self):
        state,owner,_,_=self.fixture();state['backends']['brake']['state']='RUNNING'
        with self.assertRaisesRegex(ValueError,'RETAINED_BACKEND_NOT_STOPPED'):
            retained_backend_images(state,owner)
        state,owner,_,_=self.fixture();owner._image.side_effect=ValueError('MISSING_RETAINED_IMAGE')
        with self.assertRaisesRegex(ValueError,'MISSING_RETAINED_IMAGE'):retained_backend_images(state,owner)
        state,owner,_,images=self.fixture();images[state['backends']['brake']['imageId']]['Architecture']='amd64'
        with self.assertRaisesRegex(ValueError,'RETAINED_BACKEND_IMAGE_CHANGED'):retained_backend_images(state,owner)

    def test_only_expected_candidate_absence_may_use_retained_image_proof(self):
        retained_backend_prerequisites(dict(localInstalled=True,backendsObserved=True))
        retained_backend_prerequisites(dict(localInstalled=True,backendsObserved=False,
            prerequisite='SETUP_BACKENDS_IMAGES_MISSING'))
        for row in (dict(localInstalled=False,backendsObserved=True),
                    dict(localInstalled=True,backendsObserved=False),
                    dict(localInstalled=True,backendsObserved=False,prerequisite='SETUP_BACKENDS_ENGINE_UNAVAILABLE'),
                    dict(localInstalled=True,backendsObserved=False,prerequisite='SETUP_BACKENDS_IMAGE_MISMATCH')):
            with self.assertRaisesRegex(ValueError,'RETAINED_BACKEND_PREREQUISITES_REQUIRED'):
                retained_backend_prerequisites(row)

    def test_launcher_checks_its_pin_separately_from_retained_backend_inventory(self):
        row=dict(status='SETUP_INSTALLED_OBSERVED',localInstalled=True,launcherObserved=True,
                 backendsObserved=False,prerequisite='SETUP_BACKENDS_IMAGES_MISSING')
        launcher_prerequisites(row,True)
        with self.assertRaisesRegex(ValueError,'SETUP_LAUNCHER_NOT_OBSERVED'):launcher_prerequisites(row,False)
        for key in ('localInstalled','launcherObserved'):
            with self.assertRaisesRegex(ValueError,'SETUP_LAUNCHER_NOT_OBSERVED'):
                launcher_prerequisites(dict(row,**{key:False}),True)


if __name__=='__main__':unittest.main()
