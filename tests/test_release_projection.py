# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
from pathlib import Path
from types import SimpleNamespace
import json
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import release_operator_proof as operator
import release_publication as publication
from release_automation import CampaignError


class ProjectionTests(unittest.TestCase):
    def source_selection(self, paths, ancestor=0, product_error=None):
        root=Path('/fixture');selected='a'*40;current='b'*40
        owner=SimpleNamespace(gateway=root/'gateway',product=Mock(side_effect=product_error))
        plan=dict(schemaVersion=3,nativeSources={'vehicle-gateway':{'revision':selected}})
        def git(repo,*args):
            return current if args==('rev-parse','HEAD') else '\n'.join(paths)
        with patch.object(publication,'ROOT',root),patch('developer_build.selected_plan',return_value=root/'plan.json'), \
             patch('reproduction.chain.read_plan',return_value=plan),patch.object(publication,'git',side_effect=git), \
             patch.object(publication,'sha',return_value='c'*64), \
             patch.object(publication,'command',return_value=SimpleNamespace(returncode=ancestor)):
            result=publication.active_sources(owner)
        return result,owner

    def test_gateway_documentation_descendant_keeps_b_plan_and_requires_product_equivalence(self):
        result,owner=self.source_selection(['README.md','docs/architecture.md'])
        self.assertEqual(result['nativeSources']['vehicle-gateway']['revision'],'a'*40)
        self.assertEqual(result['gatewayHead'],'b'*40)
        self.assertTrue(result['gatewayDocumentationAdvance'])
        owner.product.assert_called_once_with()

    def test_gateway_source_or_foreign_history_cannot_use_documentation_exception(self):
        for paths,ancestor in [(['tools/KeyboardControl.swift'],0),(['src/main.cpp'],0),
                               (['LICENSE'],0),(['docs/data.json'],0),(['docs/guide.md'],1),([],0)]:
            with self.assertRaisesRegex(CampaignError,'GATEWAY_PRODUCT_SOURCE_CHANGED'):
                self.source_selection(paths,ancestor)

    def test_documentation_only_advance_never_waives_changed_product_bytes(self):
        with self.assertRaisesRegex(CampaignError,'APPLICATION_PRODUCT_BYTES_CHANGED'):
            self.source_selection(['docs/architecture.md'],product_error=CampaignError('APPLICATION_PRODUCT_BYTES_CHANGED'))

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

    def test_stable_descriptor_path_and_same_version_collision(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory).resolve();(root/'workspace/releases').mkdir(parents=True)
            old=dict(productVersion='1.2.0-rc.2',status='ENGINEERING_CANDIDATE_NOT_QUALIFIED',
                     file='current.dmg',bytes=123,sha256='a'*64,manifestSha256='b'*64,notarized=False)
            path=root/'workspace/releases/delivery.json';path.write_text(json.dumps(old))
            catalog=dict(catalogRevision=1,operatorDescriptor='workspace/releases/delivery.json',operator=old)
            (root/'workspace/launcher-catalog.json').write_text(json.dumps(catalog))
            owner=SimpleNamespace(config=dict(version='1.2.0-rc.2'))
            with patch.object(operator,'ROOT',root),patch.object(operator,'descriptor',return_value={**old,'sha256':'c'*64}):
                with self.assertRaisesRegex(CampaignError,'IMMUTABLE_DESCRIPTOR'):operator.project(owner,dict(fileId='file_123456789'))
            with patch.object(operator,'ROOT',root),patch.object(operator,'descriptor',return_value={**old,'productVersion':'1.2.0-rc.3'}):
                relative,_,_=operator.project(owner,dict(fileId='file_123456789'))
                self.assertEqual(relative,'workspace/releases/delivery.json')
            self.assertEqual(json.loads(path.read_text()),old)
