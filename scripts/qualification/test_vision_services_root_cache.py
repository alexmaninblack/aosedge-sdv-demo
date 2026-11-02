# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Frozen native cache descriptors; no guest, network or cache mutation."""
import copy
import hashlib
import json
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import patch


class RootCacheTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module=runpy.run_path(str(Path(__file__).with_name('vision_services_root_cache_guest.py')))

    def descriptor(self):
        return dict(schemaVersion=2,
            config=dict(digest='sha256:ae0b9e133e12f4b2312450cc0473844950645728712062f7978f09f21bee1da0',size=160,mediaType='application/vnd.oci.image.config.v1+json'),
            aosItemConfig=dict(digest='sha256:93716e27fd5a4af8304a4590a870ef79ebadbdc8268c4b9f14d063f2908b259c',size=176,mediaType='application/vnd.aos.item.config.v1+json'),
            layers=[dict(digest='sha256:'+self.module['LAYER'],size=130248720,mediaType='application/vnd.aos.image.component.full.v1+squashfs')])

    def test_native_decrypted_length_does_not_replace_the_signed_descriptor(self):
        spec=self.descriptor();before=copy.deepcopy(spec)
        rows=self.module['closure'](spec,547)
        self.assertEqual(spec,before);self.assertEqual(len(rows),4)
        self.assertEqual(rows[self.module['LAYER']],130248704)
        self.assertEqual(rows[spec['config']['digest'].removeprefix('sha256:')],152)
        self.assertEqual(rows[spec['aosItemConfig']['digest'].removeprefix('sha256:')],169)
        self.assertEqual(rows[self.module['MANIFEST']],547)

    def test_unknown_oci_bytes_or_missing_aos_item_config_are_refused(self):
        for field in ('config','aosItemConfig'):
            spec=self.descriptor();del spec[field]
            with self.assertRaisesRegex(ValueError,'ROOT_CACHE_.*CONFIG_CHANGED'):
                self.module['closure'](spec,547)
            spec=self.descriptor();spec[field]['digest']='sha256:'+'0'*64
            with self.assertRaises(ValueError):self.module['closure'](spec,547)

    def test_changed_layer_or_ciphertext_length_is_refused(self):
        for field,value in [('digest','sha256:'+'0'*64),('size',130248704),('mediaType','application/octet-stream')]:
            spec=self.descriptor();spec['layers'][0][field]=value
            with self.assertRaisesRegex(ValueError,'ROOT_CACHE_LAYER_CHANGED'):
                self.module['closure'](spec,547)
        spec=self.descriptor();spec['layers'].append(copy.deepcopy(spec['layers'][0]))
        with self.assertRaisesRegex(ValueError,'ROOT_CACHE_MANIFEST_CHANGED'):
            self.module['closure'](spec,547)

    def test_unknown_action_fails_before_binding_or_mutation(self):
        with self.assertRaisesRegex(ValueError,'ROOT_CACHE_OPERATION_DENIED'):
            self.module['run']('rewrite-database')

    def test_full_native_closure_must_include_the_index_blob(self):
        spec=dict(schemaVersion=2,manifests=[dict(digest='sha256:'+self.module['MANIFEST'],size=560,
            mediaType='application/vnd.oci.image.manifest.v1+json')])
        function=self.module['complete_index_closure']
        rows=self.module['closure'](self.descriptor(),547)
        with tempfile.TemporaryDirectory() as temporary,patch.dict(function.__globals__,OLD=Path(temporary)):
            with self.assertRaisesRegex(ValueError,'ROOT_CACHE_ORIGINAL_INDEX_NOT_UNIQUE'):function(rows)
            raw=json.dumps(spec).encode();pin=hashlib.sha256(raw).hexdigest();path=Path(temporary)/pin;path.write_bytes(raw)
            full=function(rows);self.assertEqual(len(full),5);self.assertEqual(full[pin],len(raw))
            self.assertNotIn(pin,rows)
            path.rename(Path(temporary)/('0'*64))
            with self.assertRaisesRegex(ValueError,'ROOT_CACHE_ORIGINAL_INDEX_INVALID'):function(rows)

    def test_an_index_cannot_smuggle_a_second_manifest(self):
        spec=dict(schemaVersion=2,manifests=[dict(digest='sha256:'+self.module['MANIFEST'],mediaType='application/vnd.oci.image.manifest.v1+json'),
            dict(digest='sha256:'+'1'*64,mediaType='application/vnd.oci.image.manifest.v1+json')])
        function=self.module['complete_index_closure'];rows=self.module['closure'](self.descriptor(),547)
        with tempfile.TemporaryDirectory() as temporary,patch.dict(function.__globals__,OLD=Path(temporary)):
            raw=json.dumps(spec).encode();(Path(temporary)/hashlib.sha256(raw).hexdigest()).write_bytes(raw)
            with self.assertRaisesRegex(ValueError,'ROOT_CACHE_ORIGINAL_INDEX_INVALID'):function(rows)


if __name__=='__main__':unittest.main()
