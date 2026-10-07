# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""R1 offline contract proof. No simulator, Cloud, SDK or network is used."""

import copy
import hashlib
import importlib.machinery
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/validate-release-definition'
loader = importlib.machinery.SourceFileLoader('release_definition', str(SCRIPT))
spec = importlib.util.spec_from_loader(loader.name, loader)
gate = importlib.util.module_from_spec(spec)
loader.exec_module(gate)


class ReleaseDefinitionTests(unittest.TestCase):
    def setUp(self):
        self.value = gate.read_json(ROOT / gate.DEFAULT)

    def rejects(self, match):
        with self.assertRaisesRegex(gate.DefinitionError, match):
            gate.validate(self.value)

    def test_real_definition_passes_without_sibling_or_runtime_inputs(self):
        self.assertEqual(gate.validate(self.value)['id'], 'kit028-setup042')

    def test_unknown_field_fails(self):
        self.value['ready'] = True
        self.rejects('unknown field')

    def test_missing_field_fails(self):
        del self.value['profiles']
        self.rejects('missing required')

    def test_boolean_is_not_an_integer(self):
        self.value['inputs'][0]['bytes'] = True
        self.rejects('invalid type')

    def test_changed_authority_fails(self):
        self.value['authorities'][0]['sha256'] = '0' * 64
        self.rejects('Authority digest mismatch')

    def test_missing_authority_binding_fails(self):
        self.value['authorities'].pop(0)
        self.rejects('Missing required authority')

    def test_duplicate_sources_fail(self):
        self.value['sources'].append(copy.deepcopy(self.value['sources'][0]))
        self.rejects('duplicate id')

    def test_missing_source_role_fails(self):
        self.value['sources'].pop(1)
        self.rejects('Incomplete source roles')

    def test_branch_instead_of_commit_fails(self):
        self.value['sources'][0]['revision'] = 'main'
        self.rejects('invalid format')

    def test_wrong_source_revision_fails(self):
        self.value['sources'][0]['revision'] = 'a' * 40
        self.rejects('revision mismatch')

    def test_wrong_integration_repository_fails(self):
        self.value['sources'][0]['repository'] = 'https://github.com/example/other.git'
        self.rejects('wrong integration repository')

    def test_restricted_source_cannot_be_marked_public(self):
        row = next(s for s in self.value['sources'] if s['id'] == 'unreal-engine')
        row['access'] = 'public-git'
        self.rejects('access boundary mismatch')

    def test_historical_candidate_not_given_new_product_version(self):
        self.value['productVersion'] = '1.2.0'
        self.rejects('no assigned product version')

    def test_build_revision_cannot_be_rewritten(self):
        self.value['sources'][0]['buildRevision'] = self.value['sources'][0]['revision']
        self.rejects('original build revision mismatch')

    def test_duplicate_source_indices_fail(self):
        self.value['sources'][1]['sourceLockIndex'] = 0
        self.rejects('duplicate reference')

    def test_factory_tools_cannot_be_application_role(self):
        self.value['sources'][0]['id'], self.value['sources'][1]['id'] = 'factory-tools', 'integration'
        self.rejects('build revision mismatch|application source role|Factory tools role')

    def test_missing_manifest_group_fails(self):
        self.value['inputs'].pop()
        self.rejects('Incomplete input manifest')

    def test_manifest_digest_mismatch_fails(self):
        self.value['inputs'][0]['sha256'] = 'b' * 64
        self.rejects('input manifest mismatch')

    def test_manifest_cannot_use_other_groups_lock(self):
        self.value['inputs'][0]['lock'] = self.value['inputs'][1]['lock']
        self.rejects('wrong manifest authority')

    def test_artifact_mismatch_fails(self):
        self.value['artifacts']['dmg']['bytes'] += 1
        self.rejects('Artifact identity mismatch')

    def test_no_retroactive_clean_build(self):
        self.value['application']['originalBuildHadUncommittedSources'] = False
        self.rejects('Original provenance')

    def test_unsupported_profile_fails(self):
        self.value['profiles'][0]['id'] = 'automatic'
        self.rejects('unsupported value')
        with self.assertRaisesRegex(gate.DefinitionError, 'Unsupported profile'):
            gate.readiness(gate.read_json(ROOT / gate.DEFAULT), 'automatic')

    def test_missing_profile_dependency_fails(self):
        self.value['profiles'][1]['components'].pop()
        self.rejects('incomplete profile closure')

    def test_duplicate_dependency_fails(self):
        row = next(c for c in self.value['components'] if c['id'] == 'factory')
        row['requires'].append(row['requires'][0])
        self.rejects('duplicate reference')

    def test_unknown_dependency_fails(self):
        self.value['components'][0]['requires'] = ['ghost-input']
        self.rejects('unknown requires')

    def test_dependency_cycle_fails(self):
        self.value['components'][0]['requires'] = ['carla']
        self.rejects('Dependency cycle')

    def test_missing_component_fails(self):
        self.value['components'].pop()
        self.rejects('Incomplete component closure')

    def test_operator_cannot_build_unreal(self):
        self.value['components'][0]['actions']['operator'] = 'build'
        self.rejects('operator must not build')

    def test_wrong_toolchain_pin_fails(self):
        self.value['toolchains'][0]['identity'] = '20.0.0'
        self.rejects('toolchain mismatch')

    def test_all_profiles_are_explicitly_blocked(self):
        for profile in gate.PROFILES:
            with self.subTest(profile=profile):
                pending = gate.readiness(self.value, profile)
                self.assertTrue(any('PROFILE_NOT_QUALIFIED' in item for item in pending))
                self.assertGreater(len(pending), 1)

    def test_candidate_cannot_be_promoted_by_deleting_gates(self):
        self.value['gates'] = []
        self.rejects('missing entries')
        self.assertIn('PROFILE_NOT_QUALIFIED', gate.readiness(self.value, 'operator')[-1])

    def test_publication_and_qualification_flags_fail_closed(self):
        for field in ('status', 'distribution', 'profiles'):
            with self.subTest(field=field):
                self.setUp()
                if field == 'status':
                    self.value[field] = 'stable'
                elif field == 'distribution':
                    self.value[field]['approved'] = True
                else:
                    self.value[field][0]['claim'] = 'qualified'
                self.rejects('unsupported value|wrong constant')

    def test_unpublished_url_rejected(self):
        self.value['distribution']['locator'] = 'https://example.invalid/binary'
        self.rejects('must not advertise')

    def test_traversal_rejected(self):
        self.value['inputs'][0]['kitPath'] = '../outside'
        self.rejects('invalid format')

    def test_missing_optional_kit_is_error(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(gate.DefinitionError, 'unavailable'):
                gate.verify_kit(self.value, Path(temporary))

    def kit_fixture(self, kit):
        value = copy.deepcopy(self.value)
        pins = {i['id']: {k: i[k] for k in ('path', 'bytes', 'sha256')} for i in value['inputs']}
        payloads = {i['id']: {'id': i['id']} for i in value['inputs']}
        payloads['vm-runtime'] = {'hostManifest': pins['host-runtime']}
        for row in value['inputs']:
            data = (json.dumps(payloads[row['id']]) + '\n').encode()
            path = kit / row['kitPath']
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            row.update(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
            pins[row['id']] = {k: row[k] for k in ('path', 'bytes', 'sha256')}
        # Rebind VM to fixture host metadata, not the real manifest.
        vm = next(row for row in value['inputs'] if row['id'] == 'vm-runtime')
        data = json.dumps({'hostManifest': pins['host-runtime']}).encode()
        (kit / vm['kitPath']).write_bytes(data)
        vm.update(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
        pins['vm-runtime'] = {k: vm[k] for k in ('path', 'bytes', 'sha256')}
        data = json.dumps({'inputs': pins, 'inputLogicalBytes': value['application']['inputLogicalBytes']}).encode()
        (kit / value['application']['kitPath']).write_bytes(data)
        value['application'].update(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
        return value

    def test_metadata_fixture_matches_then_detects_corruption(self):
        with tempfile.TemporaryDirectory() as temporary:
            kit = Path(temporary)
            value = self.kit_fixture(kit)
            self.assertEqual(gate.verify_kit(value, kit), 6)
            (kit / value['inputs'][0]['kitPath']).write_text('{}')
            with self.assertRaisesRegex(gate.DefinitionError, 'digest/size mismatch'):
                gate.verify_kit(value, kit)

    def test_duplicate_json_keys_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'duplicate.json'
            path.write_text('{"x": 1, "x": 2}')
            with self.assertRaisesRegex(gate.DefinitionError, 'Duplicate JSON key'):
                gate.read_json(path)

    def test_symlink_escape_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'outside').symlink_to(ROOT / gate.DEFAULT)
            with self.assertRaisesRegex(gate.DefinitionError, 'escapes root'):
                gate.safe_path(root, 'outside')

    def test_new_schema_keyword_requires_implementation(self):
        with self.assertRaisesRegex(gate.DefinitionError, 'unsupported schema keyword'):
            gate.schema_check('anything', {'type': 'string', 'format': 'email'})

    def test_unknown_cli_profile_and_readiness_exit_codes(self):
        for profile, code in [('developer', 2), ('other', 1)]:
            with self.subTest(profile=profile):
                result = subprocess.run([sys.executable, '-B', str(SCRIPT), '--profile', profile],
                                        capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode, code, result.stderr)

    def source_fixture(self, workspace):
        repository = workspace / 'aosedge-sdv-demo'
        repository.mkdir()
        value = copy.deepcopy(self.value)
        value['sources'] = value['sources'][:2]
        value['components'] = [{'recipes': [
            {'source': 'integration', 'path': 'scripts/distribution/application.py'},
            {'source': 'factory-tools', 'path': 'scripts/guest/r6-1-yocto-build'},
        ]}]
        def metadata(repo, *args):
            self.assertEqual(repo, repository)
            if args == ('rev-parse', '--show-toplevel'):
                return str(repository)
            if args[0] == 'rev-parse':
                return self.value['baselineTag']['commit']
            self.assertEqual(args[:2], ('cat-file', '-t'))
            return 'blob' if ':' in args[-1] else 'commit'
        return value, metadata

    def test_optional_source_check_accepts_exact_objects_without_branch_requirement(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            value, metadata = self.source_fixture(workspace)
            with patch.object(gate, 'git_metadata', side_effect=metadata) as git:
                self.assertEqual(gate.verify_sources(value, workspace), (2, 2))
            for call in git.call_args_list:
                self.assertNotIn('HEAD', call.args)
                self.assertNotIn('checkout', call.args)

    def test_optional_source_check_rejects_wrong_baseline_tag(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            value, metadata = self.source_fixture(workspace)
            value['baselineTag']['commit'] = 'a' * 40
            with patch.object(gate, 'git_metadata', side_effect=metadata):
                with self.assertRaisesRegex(gate.DefinitionError, 'Baseline tag commit mismatch'):
                    gate.verify_sources(value, workspace)

    def test_optional_source_check_rejects_parent_repository(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            value, _ = self.source_fixture(workspace)
            with patch.object(gate, 'git_metadata', return_value=str(workspace)):
                with self.assertRaisesRegex(gate.DefinitionError, 'wrong checkout root'):
                    gate.verify_sources(value, workspace)

    def test_optional_source_check_rejects_directory_recipe(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            value, metadata = self.source_fixture(workspace)
            def directory_recipe(repo, *args):
                result = metadata(repo, *args)
                return 'tree' if result == 'blob' else result
            with patch.object(gate, 'git_metadata', side_effect=directory_recipe):
                with self.assertRaisesRegex(gate.DefinitionError, 'recipe is not a file'):
                    gate.verify_sources(value, workspace)

    def test_git_inspection_disables_lazy_fetch_and_inherited_repository_override(self):
        with tempfile.TemporaryDirectory() as temporary:
            with patch.dict(gate.os.environ, {'GIT_DIR': 'foreign-repo', 'GIT_CONFIG_COUNT': '1'}):
                with patch.object(gate.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, 'commit\n', '')) as run:
                    self.assertEqual(gate.git_metadata(Path(temporary), 'cat-file', '-t', 'a' * 40), 'commit')
            arguments = run.call_args.kwargs
            self.assertNotIn('GIT_DIR', arguments['env'])
            self.assertNotIn('GIT_CONFIG_COUNT', arguments['env'])
            self.assertEqual(arguments['env']['GIT_NO_LAZY_FETCH'], '1')
            self.assertEqual(arguments['env']['GIT_TERMINAL_PROMPT'], '0')
            self.assertEqual(arguments['timeout'], 10)

    def test_git_inspection_reports_missing_object_without_echoing_stderr(self):
        with tempfile.TemporaryDirectory() as temporary:
            with patch.object(gate.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1, '', 'raw response')):
                with self.assertRaisesRegex(gate.DefinitionError, 'local Git object unavailable') as failure:
                    gate.git_metadata(Path(temporary), 'cat-file', '-t', 'a' * 40)
            self.assertNotIn('raw response', str(failure.exception))

    def test_git_inspection_reports_timeout(self):
        with tempfile.TemporaryDirectory() as temporary:
            with patch.object(gate.subprocess, 'run', side_effect=subprocess.TimeoutExpired('git', 10)):
                with self.assertRaisesRegex(gate.DefinitionError, 'inspection unavailable'):
                    gate.git_metadata(Path(temporary), 'cat-file', '-t', 'a' * 40)

    def test_root_only_copy_passes_and_ci_pin_drift_fails(self):
        paths = {row['path'] for row in self.value['authorities']}
        paths.update(self.value['evidence'])
        paths.update(v for k, v in self.value['documentation'].items() if k != 'version')
        paths.update(t['evidence'] for t in self.value['toolchains'])
        paths.update(r['path'] for c in self.value['components'] for r in c['recipes'] if r['source'] == 'integration')
        paths.update([str(gate.SCHEMA), '.github/workflows/repository-boundaries.yml'])
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for relative in paths:
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / relative, target)
            gate.validate(self.value, root)
            path = root / '.github/workflows/repository-boundaries.yml'
            pin = next(s['revision'] for s in self.value['sources'] if s['id'] == 'vehicle-gateway')
            path.write_text(path.read_text().replace(pin, 'c' * 40))
            with self.assertRaisesRegex(gate.DefinitionError, 'CI checkout pin mismatch'):
                gate.validate(self.value, root)


if __name__ == '__main__':
    unittest.main()
