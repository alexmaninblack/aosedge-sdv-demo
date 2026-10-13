# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
from pathlib import Path
from types import SimpleNamespace
import json
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import release_operator_proof as operator
from release_automation import CampaignError


class ProjectionTests(unittest.TestCase):
    def test_projection_selects_new_descriptor_without_rewriting_old(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory).resolve();(root/'workspace/releases').mkdir(parents=True)
            catalog=dict(catalogRevision=1,operator={'setupBundle':'signed app'})
            (root/'workspace/launcher-catalog.json').write_text(json.dumps(catalog))
            expected=dict(productVersion='1.2.0-rc.1',status='ENGINEERING_CANDIDATE_NOT_QUALIFIED',
                file='AosEdge-SDV-Lab-1.2.0-rc.1.dmg',bytes=123,sha256='a'*64,
                manifestSha256='b'*64,notarized=False)
            owner=SimpleNamespace(config=dict(version='1.2.0-rc.1'))
            with patch.object(operator,'ROOT',root),patch.object(operator,'descriptor',return_value=expected):
                relative,raw,projected=operator.project(owner,dict(fileId='file_123456789'))
                self.assertEqual(json.loads(raw),expected)
                value=json.loads(projected)
                self.assertEqual(value['operatorDescriptor'],relative)
                self.assertEqual(value['operator']['setupBundle'],'signed app')
                self.assertIn('id=file_123456789',value['operator']['downloadURL'])
                self.assertEqual(value['operator']['notarized'],False)
                self.assertEqual((root/'workspace/launcher-catalog.json').read_text(),json.dumps(catalog))
                (root/relative).write_bytes(b'foreign immutable record')
                with self.assertRaisesRegex(CampaignError,'IMMUTABLE_DESCRIPTOR'):
                    operator.project(owner,dict(fileId='file_123456789'))
