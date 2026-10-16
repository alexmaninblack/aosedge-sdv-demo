# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Current selection and legacy integrity parity; no builds or live operations."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

from test_release_definition import gate, ROOT
import test_release_definition as legacy_tests


class CurrentBuildDefinitionTests(unittest.TestCase):
    def setUp(self):
        self.current = gate.read_json(ROOT / gate.DEFAULT)

    def test_default_resolves_current_selection_without_restoring_old_reports(self):
        self.assertEqual(self.current['schemaVersion'], 2)
        value = gate.resolve(self.current)
        self.assertEqual(value, gate.read_json(ROOT / gate.LEGACY_DEFAULT))
        for row in self.current['historicalEvidence']:
            self.assertFalse((ROOT / row['path']).exists())

    def test_current_validation_needs_no_git_or_network_process(self):
        with patch.object(gate.subprocess, 'run', side_effect=AssertionError('No process permitted')):
            self.assertEqual(gate.resolve(self.current)['id'], 'kit028-setup042')

    def test_unknown_fields_and_qualification_shortcuts_fail(self):
        for field in ('ready', 'qualified', 'ignoreEvidence', 'skipIntegrity'):
            value = copy.deepcopy(self.current)
            value[field] = True
            with self.subTest(field=field), self.assertRaises(gate.DefinitionError):
                gate.resolve(value)

    def test_schema_version_is_not_a_boolean(self):
        self.current['schemaVersion'] = True
        with self.assertRaises(gate.DefinitionError):
            gate.resolve(self.current)

    def test_base_file_and_canonical_identity_are_independently_pinned(self):
        for field in ('sha256', 'definitionDigest'):
            value = copy.deepcopy(self.current)
            value['compatibilityBase'][field] = '0' * 64
            with self.subTest(field=field), self.assertRaises(gate.DefinitionError):
                gate.resolve(value)

    def test_missing_or_duplicate_provenance_is_rejected(self):
        self.current['historicalEvidence'].append(copy.deepcopy(self.current['historicalEvidence'][0]))
        with self.assertRaises(gate.DefinitionError):
            gate.resolve(self.current)
        self.current['historicalEvidence'] = self.current['historicalEvidence'][:2]
        with self.assertRaises(gate.DefinitionError):
            gate.resolve(self.current)

    def test_unsafe_historical_reference_fails(self):
        self.current['historicalEvidence'][0]['path'] = 'docs/../../outside.md'
        with self.assertRaises(gate.DefinitionError):
            gate.resolve(self.current)

    def test_provenance_only_uses_immutable_commit_and_hash(self):
        for field, value in [('revision', 'main'), ('sha256', 'latest')]:
            selected = copy.deepcopy(self.current)
            selected['historicalEvidence'][0][field] = value
            with self.subTest(field=field), self.assertRaises(gate.DefinitionError):
                gate.resolve(selected)

    @unittest.skipUnless((ROOT / '.git').exists(), 'Optional local Git object proof requires a checkout')
    def test_independent_local_provenance_proof(self):
        self.assertEqual(gate.verify_historical_evidence(self.current), 3)
        self.current['historicalEvidence'][0]['sha256'] = '0' * 64
        with self.assertRaisesRegex(gate.DefinitionError, 'digest mismatch'):
            gate.verify_historical_evidence(self.current)

    def test_old_v1_validation_still_requires_its_original_evidence(self):
        with self.assertRaisesRegex(gate.DefinitionError, 'Missing documentation/evidence'):
            gate.validate(gate.read_json(ROOT / gate.LEGACY_DEFAULT))

    def test_root_only_current_copy_works_without_git_or_historical_prose(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            original = gate.read_json(ROOT / gate.LEGACY_DEFAULT)
            legacy_tests.ReleaseDefinitionTests.copy_legacy_fixture(root, original)
            extras = [str(gate.DEFAULT), str(gate.CURRENT_SCHEMA), str(gate.LEGACY_DEFAULT),
                      self.current['developerSelection'], self.current['operatorSelection'],
                      *self.current['documentation']]
            selector = gate.read_json(ROOT / self.current['developerSelection'])
            catalog = gate.read_json(ROOT / self.current['operatorSelection'])
            extras.extend([selector['path'], catalog['operatorDescriptor']])
            for relative in extras:
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / relative, target)
            for row in self.current['historicalEvidence']:
                (root / row['path']).unlink()
            self.assertFalse((root / '.git').exists())
            self.assertEqual(gate.resolve(self.current, root), original)
            (root / self.current['documentation'][0]).unlink()
            with self.assertRaisesRegex(gate.DefinitionError, 'Missing current documentation'):
                gate.resolve(self.current, root)

    def test_core_keeps_compatibility_cache_and_source_identity(self):
        sys.path.insert(0, str(ROOT / 'scripts'))
        from reproduction.core import Release
        release = Release()
        self.assertEqual(release.definition, self.current)
        self.assertEqual(release.key, self.current['compatibilityBase']['definitionDigest'])
        canonical = json.dumps(release.value, sort_keys=True, separators=(',', ':')).encode()
        self.assertEqual(release.key, hashlib.sha256(canonical).hexdigest())

    def test_profile_qualification_is_not_inherited(self):
        value = gate.resolve(self.current)
        for profile in gate.PROFILES:
            self.assertTrue(any('PROFILE_NOT_QUALIFIED' in item for item in gate.readiness(value, profile)))

    def test_changed_developer_pin_is_rejected_before_plan_use(self):
        original = gate.read_json
        selected_path = ROOT / self.current['developerSelection']
        def read(path):
            value = original(path)
            if path == selected_path:
                value['sha256'] = '0' * 64
            return value
        with patch.object(gate, 'read_json', side_effect=read):
            with self.assertRaisesRegex(gate.DefinitionError, 'Developer plan pin mismatch'):
                gate.resolve(self.current)

    def test_malformed_developer_selection_fails_as_definition_error(self):
        original = gate.read_json
        selected_path = ROOT / self.current['developerSelection']
        def read(path):
            value = original(path)
            if path == selected_path:
                value['path'] = None
            return value
        with patch.object(gate, 'read_json', side_effect=read):
            with self.assertRaises(gate.DefinitionError):
                gate.resolve(self.current)

    def test_operator_descriptor_cannot_drift_from_selected_catalog(self):
        original = gate.read_json
        catalog = original(ROOT / self.current['operatorSelection'])
        descriptor = ROOT / catalog['operatorDescriptor']
        def read(path):
            value = original(path)
            if path == descriptor:
                value['sha256'] = '0' * 64
            return value
        with patch.object(gate, 'read_json', side_effect=read):
            with self.assertRaisesRegex(gate.DefinitionError, 'Operator descriptor mismatch'):
                gate.resolve(self.current)

    def test_default_chain_is_the_reviewed_current_plan_not_the_old_fallback(self):
        sys.path.insert(0, str(ROOT / 'scripts'))
        from reproduction.core import Release
        from reproduction.chain import read_plan
        selected = gate.read_json(ROOT / self.current['developerSelection'])
        self.assertEqual(read_plan(Release()), gate.read_json(ROOT / selected['path']))

    def test_explicit_compatibility_chain_remains_available(self):
        sys.path.insert(0, str(ROOT / 'scripts'))
        from reproduction.core import Release
        from reproduction import chain
        self.assertEqual(chain.read_plan(Release(), ROOT / chain.PLAN)['schemaVersion'], 1)


if __name__ == '__main__':
    unittest.main()
