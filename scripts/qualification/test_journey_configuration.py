# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Explicit image admission does not widen Cloud, path or candidate guards."""
import json
from pathlib import Path
import tempfile
import unittest

import journey


class JourneyImageScope(unittest.TestCase):
    def configuration(self, image):
        home='/Users/operator'
        pin='a'*64
        value=dict(schemaVersion=1,manifestSha256=pin,setupSha256='b'*64,
            packageRoot=home+'/Packages/versions/'+pin,storeRoot=home+'/Packages',
            instanceRoot=home+'/Lab',setupApp='/Volumes/Review/AosEdge SDV Lab Setup.app',
            sourceRoot='/Volumes/Review/Runtime Kit',image=image,
            oemCertificate=home+'/oem.p12',spCertificate=home+'/sp.p12',
            records='/selected/.local/remote-qualification/fresh')
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary).resolve()/'journey.json'
            path.write_text(json.dumps(value));path.chmod(0o600)
            return journey.configuration(path,'operator')

    def test_explicit_built_factory42_and_previous_images_remain_admitted(self):
        for number in (39,40,41,42):
            image=f'6.1.1-maninblack.{number}/main-qemuarm64'
            self.assertEqual(self.configuration(image)['image'],image)

    def test_unknown_image_or_architecture_remains_blocked(self):
        for image in ('6.1.1-maninblack.43/main-qemuarm64',
                      '6.1.1-maninblack.42/main-qemux86',
                      '6.1.1-maninblack.42/main-qemuarm64.img'):
            with self.assertRaisesRegex(ValueError,'FACTORY_OUTSIDE_ACCEPTED_SCOPE'):
                self.configuration(image)


if __name__=='__main__':unittest.main()
