# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Ordered-owner fixtures: no native compilation, signing or external services."""
import copy
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import test_reproduction
from test_reproduction import StorageFixture
from reproduction import chain, chain_worker, core, sources


class PlanTests(unittest.TestCase):
    def test_worker_malformed_or_missing_completion_fails_closed(self):
        for value in (b'', b'not-json', b'[]', b'{"status":"OWNER_STEP_COMPLETED"}',
                      b'{"status":"OWNER_STEP_COMPLETED","buildKey":"../escape"}'):
            with self.subTest(value=value), self.assertRaises(core.LabError):
                chain.completed_key(value)
        expected = 'f'*64
        self.assertEqual(chain.completed_key(json.dumps({'status':'OWNER_STEP_COMPLETED',
                                                       'buildKey':expected}).encode()), expected)

    def test_plan_is_complete_ordered_and_has_exact_owners(self):
        value = chain.read_plan(core.Release())
        self.assertEqual([r['id'] for r in value['steps']], list(chain.DEPENDENCIES))
        self.assertEqual(len(set(value['producers'].values())), 5)
        self.assertEqual(chain.ancestors(value, 'preparation'), {'brake-v1','brake-v2','brake-v3','tire-v1'})
        self.assertEqual(chain.ancestors(value, 'dmg'), set(chain.DEPENDENCIES)-{'dmg'})

    def test_malformed_or_different_plan_rejected(self):
        original = chain.read_plan(core.Release())
        variants = []
        for key, value in [('schemaVersion', True), ('baseDefinitionSha256', '0'*64),
                           ('repository','https://example.invalid/other.git'), ('producers', {'x':'main'}),
                           ('steps',original['steps'][:-1])]:
            changed = copy.deepcopy(original); changed[key] = value; variants.append(changed)
        for key, value in [('id','unexpected'), ('producer',[]), ('requires',['presenter']),
                           ('target','setup'), ('functionalProfile','v3'), ('python','build')]:
            changed = copy.deepcopy(original); changed['steps'][0][key] = value; variants.append(changed)
        changed = copy.deepcopy(original); changed['steps'][1] = changed['steps'][0]; variants.append(changed)
        for value in variants:
            with self.subTest(value=value), patch.object(chain, 'read_json', return_value=value):
                with self.assertRaises(core.LabError):
                    chain.read_plan(core.Release())

    def test_only_exact_ancestors_and_own_cache_visible(self):
        plan = chain.read_plan(core.Release())
        selected = {r['id']:r['id']+'-selected' for r in plan['steps']}
        state = {'builds': {selected[r['id']]:{'target':r['target']} for r in plan['steps']}}
        state['builds'].update({'foreign-signer':{'target':'setup'}, 'old-dmg':{'target':'dmg'},
                               'old-application':{'target':'application'}})
        visible = chain.visible_results(plan, plan['steps'][-1], selected, state)
        self.assertNotIn('foreign-signer', visible)
        self.assertNotIn('old-application', visible)
        self.assertIn('old-dmg', visible)
        self.assertIn('setup-selected', visible)

    def test_worker_imports_only_selected_frozen_owner(self):
        owner = Mock()
        options = dict.fromkeys(('python','node','npm','kit_inputs','docker','gateway_sdk','cmake',
                                'test_tmp_parent','signing_identity'), 'explicit')
        options['prepare_dependencies'] = False
        with patch.object(chain_worker.importlib, 'import_module', return_value=owner) as load:
            chain_worker.dispatch(None, None, 'preparation', None, options, None)
        load.assert_called_once_with('reproduction.packaging')
        owner.preparation.assert_called_once()


class MergeTests(unittest.TestCase):
    def fixture(self):
        row = {'target':'presenter','inputs':{'source':'one'}}
        key = core.digest(row['inputs'])
        return {'binding':{},'sources':{},'artifacts':{},'builds':{key:row}}, key

    def test_unselected_receipts_retained_and_inputs_immutable(self):
        original, key = self.fixture()
        selected = copy.deepcopy(original); selected['builds'].clear()
        row = {'target':'gateway','inputs':{'source':'two'}}; new = core.digest(row['inputs'])
        selected['builds'][new] = row
        result = chain_worker.merged_state(original, selected, core.require, core.digest)
        self.assertEqual(set(result['builds']), {key,new})
        self.assertEqual(set(original['builds']), {key})
        for section in ('binding','sources','artifacts'):
            changed = copy.deepcopy(selected); changed[section]['injected'] = True
            with self.assertRaisesRegex(core.LabError, 'non-build'):
                chain_worker.merged_state(original, changed, core.require, core.digest)
        changed = copy.deepcopy(original); changed['builds'][key]['target'] = 'setup'
        with self.assertRaisesRegex(core.LabError, 'immutable'):
            chain_worker.merged_state(original, changed, core.require, core.digest)


class ExecuteTests(StorageFixture, unittest.TestCase):
    def fixture(self):
        self.storage.environment()
        self.options = {'python':sys.executable,'ui_python':'/usr/bin/python3','signing_identity':'A'*40}
        self.args = SimpleNamespace(build_plan=None, signing_identity='A'*40, prepare_dependencies=False)
        self.patch('reproduction.chain.verify_sources')
        self.patch('reproduction.chain.preflight', return_value=self.options)
        self.prepare = self.patch('reproduction.chain.producer', return_value=self.base)
        self.verify = self.patch('reproduction.chain.verify_result')
        self.invocations, self.created = [], set()
        self.fail = None
        self.patch('reproduction.chain.run_command', side_effect=self.worker)

    def worker(self, args, **kwargs):
        request = core.read_json(args[-1]); step = request['step']
        self.invocations.append((args, request))
        if step['id'] == self.fail:
            return SimpleNamespace(returncode=1, stdout=b'{"status":"OWNER_STEP_FAILED"}', stderr=b'')
        row = {'target':step['target'], 'inputs':{'step':step['id']}}
        key = core.digest(row['inputs'])
        state = self.storage.state()
        if key not in state['builds']:
            self.created.add(key)
            state['builds'][key] = row; self.storage.save(state)
        return SimpleNamespace(returncode=0, stdout=json.dumps({'status':'OWNER_STEP_COMPLETED',
                                'buildKey':key}).encode(), stderr=b'')

    def execute(self):
        return chain.execute(self.storage, self.state, self.args, lambda *e:None)

    def test_first_repeat_no_duplicate_and_ui_interpreter_selected(self):
        self.fixture()
        first = self.execute()
        self.assertEqual(first['buildCount'], 17)
        self.assertFalse(first['profileReady']); self.assertFalse(first['published'])
        self.assertEqual(self.invocations[0][0][0], self.options['ui_python'])
        self.assertEqual(self.invocations[1][0][0], self.options['python'])
        self.created.clear()
        self.assertEqual(self.execute(), first)
        self.assertEqual(self.created, set())
        self.assertEqual(len(self.storage.state()['builds']), 17)
        self.assertFalse(list(self.storage.path('tmp').glob('chain-*.json')))

    def test_failure_preserves_completed_state_then_resumes(self):
        self.fixture(); self.fail = 'preparation'
        with self.assertRaisesRegex(core.LabError, 'preparation failed'):
            self.execute()
        self.assertEqual(len(self.storage.state()['builds']), 10)
        self.assertEqual(core.read_json(next(self.storage.path('builds/chains').glob('*.json')))['status'], 'PARTIAL')
        self.fail = None; self.created.clear()
        self.assertEqual(self.execute()['buildCount'], 17)
        self.assertEqual(len(self.created), 7)
        self.assertEqual(len(list(self.storage.path('builds/chains').glob('*.first-failure.log'))), 1)

    def test_insufficient_space_does_not_prepare_or_run(self):
        self.fixture()
        with patch('reproduction.core.shutil.disk_usage', return_value=SimpleNamespace(free=160*core.GIB)):
            with self.assertRaisesRegex(core.LabError, 'space'):
                self.execute()
        self.prepare.assert_not_called()
        self.assertEqual(self.invocations, [])


class ProducerTests(StorageFixture, unittest.TestCase):
    def fixture(self):
        source = test_reproduction.SourceTests.fixture(self)
        self.upstream = Path(source['repository'])
        sources.git(self.upstream, ['remote','add','origin','https://example.invalid/root.git'], self.storage.environment())
        self.patch('reproduction.chain.ROOT', self.upstream)
        self.plan = {'repository':'https://example.invalid/root.git'}
        self.revision = source['revision']
        return self.storage.path('sources/build-tools/'+self.revision)

    def prepare(self):
        return chain.producer(self.storage, self.plan, self.revision, False, lambda *e:None)

    def test_exact_local_object_first_repeat_and_dirty_preserved(self):
        path = self.fixture()
        self.assertEqual(self.prepare(), path)
        self.assertEqual(self.prepare(), path)
        self.assertNotIn('ref:', (path/'.git/HEAD').read_text())
        (path/'file').write_text('user change')
        with self.assertRaisesRegex(core.LabError, 'Dirty'):
            self.prepare()
        self.assertEqual((path/'file').read_text(), 'user change')

    def test_collision_and_linked_git_never_overwritten(self):
        path = self.fixture(); path.mkdir(parents=True); (path/'keep').write_text('keep')
        with self.assertRaisesRegex(core.LabError, 'Unowned'):
            self.prepare()
        core.atomic_json(path.with_suffix('.json'), {'repository':self.plan['repository'],'revision':self.revision})
        (path/'.git').symlink_to(self.upstream/'.git')
        with self.assertRaisesRegex(core.LabError, 'Symlink'):
            self.prepare()
        self.assertEqual((path/'keep').read_text(), 'keep')

    def test_missing_object_requires_explicit_acquisition(self):
        self.fixture(); self.revision = '0'*40
        with self.assertRaisesRegex(core.LabError, 'prepare-dependencies'):
            self.prepare()


class PreflightTests(StorageFixture, unittest.TestCase):
    def options(self):
        values = dict.fromkeys(('python','ui_python','node','npm','cmake','docker'), Path(sys.executable))
        values.update(kit_inputs=self.base, gateway_sdk=self.base, test_tmp_parent=self.base,
            signing_identity='a'*40, resume=False, functional_profile=None, prepare_dependencies=False)
        return SimpleNamespace(**values)

    def test_explicit_signer_required_before_owner_work(self):
        args = self.options(); args.signing_identity = None
        with self.assertRaisesRegex(core.LabError, 'explicit authorized'):
            chain.preflight(self.storage, args)

    def test_foreign_disk_and_unavailable_tool_block(self):
        args = self.options()
        with patch.object(chain, 'external_volume', return_value={'uuid':'OTHER'}):
            with self.assertRaisesRegex(core.LabError, 'bound SSD'):
                chain.preflight(self.storage, args)
        with patch.object(chain, 'external_volume', return_value=self.volume), patch.object(chain.gateway, 'temporary_parent'):
            args.node = self.base/'missing'
            with self.assertRaisesRegex(core.LabError, 'node'):
                chain.preflight(self.storage, args)

    def test_venv_interpreter_not_resolved_away(self):
        args = self.options(); link = self.base/'venv-python'; link.symlink_to(sys.executable); args.python = link
        with patch.object(chain, 'external_volume', return_value=self.volume), patch.object(chain.gateway, 'temporary_parent'):
            result = chain.preflight(self.storage, args)
        self.assertEqual(result['python'], str(link))
        self.assertEqual(result['signing_identity'], 'A'*40)


if __name__ == '__main__':
    unittest.main()
