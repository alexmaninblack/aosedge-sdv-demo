# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Recipe selection and invalidation; no package, compiler or runtime starts."""
import ast
from pathlib import Path
import shutil
import subprocess
import unittest
from unittest.mock import patch

from test_reproduction import StorageFixture
from reproduction import core, packaging, recipes


def constant(path, name):
    tree = ast.parse(path.read_bytes())
    return ast.literal_eval(next(node.value for node in tree.body if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == name for target in node.targets)))


class RecipeTests(StorageFixture, unittest.TestCase):
    def roots(self):
        # Works in the root-only Git archive as well as a maintained checkout.
        roots = ('scripts/reproduction', 'scripts/distribution', recipes.APP,
                 'contracts', 'workspace/releases', 'workspace/checkpoints')
        tracked = {p.relative_to(core.ROOT).as_posix() for name in roots
                   for p in (core.ROOT/name).rglob('*') if p.is_file()}
        tracked.update(('LICENSE', 'scripts/validate-release-definition', 'scripts/host/aosvm-dns-bridge',
                        'workspace/gateway-build-sdk.lock.json',
                        'workspace/repositories.json', 'workspace/distribution-stage0-inventory.json',
                        'config/aosvm-single-node-unitconfig.json'))
        return tracked

    def selections(self):
        tracked = self.roots()
        return {target: set(recipes.paths(core.ROOT, tracked, target)) for target in recipes.ENTRIES}

    def test_all_targets_have_explicit_regular_input_closure(self):
        for target, paths in self.selections().items():
            with self.subTest(target=target):
                self.assertTrue(paths)
                for name in paths:
                    self.assertTrue(core.regular(core.ROOT/name).is_file())
                self.assertFalse(any(name.endswith('.md') for name in paths))
                self.assertNotIn('scripts/distribution/installed_state_probe.py', paths)
                self.assertIn('scripts/reproduction/recipes.py', paths)

    def test_setup_native_change_does_not_invalidate_other_producers(self):
        selections = self.selections()
        self.assertEqual({target for target, names in selections.items()
                          if 'scripts/distribution/native/Setup.swift' in names}, {'setup'})
        self.assertEqual({target for target, names in selections.items()
                          if 'scripts/distribution/full_dmg.py' in names}, {'dmg'})
        # An updated Setup still reaches DMG through its existing upstream key.
        before = core.digest({'setup': 'old', 'producerTrees': sorted(selections['dmg'])})
        self.assertNotEqual(before, core.digest({'setup': 'new', 'producerTrees': sorted(selections['dmg'])}))

    def test_vm_dns_and_application_configuration_are_not_missed(self):
        selections = self.selections()
        self.assertEqual({target for target, names in selections.items()
                          if 'scripts/host/aosvm-dns-bridge' in names}, {'vm-runtime'})
        for name in ('workspace/repositories.json', 'config/aosvm-single-node-unitconfig.json'):
            self.assertEqual({target for target, names in selections.items() if name in names},
                             {'application', 'setup'})

    def test_owner_data_lists_cannot_drift_silently(self):
        dist = core.ROOT/recipes.DIST
        self.assertEqual(tuple(constant(dist/'vehicle_inputs.py', 'CONTRACTS')), recipes.CONTRACTS)
        for module in ('application', 'candidate_inputs'):
            self.assertEqual(tuple(constant(dist/(module+'.py'), 'LOCKS').values()), recipes.LOCKS)
        selected = self.selections()['setup']
        self.assertTrue({recipes.DIST+'/'+name for name in constant(dist/'setup_build.py', 'HELPERS')}
                        <= selected)
        # Application non-Python export names must remain the reviewed expression.
        tree = ast.parse((dist/'application.py').read_bytes())
        node = next(n.value for n in tree.body if isinstance(n, ast.Assign)
                    and any(isinstance(t, ast.Name) and t.id == 'EXTRA' for t in n.targets))
        expected = ast.parse("('LICENSE', 'workspace/repositories.json', 'config/aosvm-single-node-unitconfig.json', "
            "'contracts/qm-advisory-profile/advisory-readiness.v1.json', "
            "*('contracts/' + name for name in CONTRACTS), *('contracts/' + name for name in LOCKS.values()))",
            mode='eval').body
        self.assertEqual(ast.dump(node), ast.dump(expected))

    def test_deferred_relative_import_and_initializer_are_included_without_execution(self):
        files = {
            recipes.DIST+'/start.py': 'raise RuntimeError("must not execute")\n'
                                    'def later():\n from aosedge_demo_orchestrator import leaf\n',
            recipes.APP+'/__init__.py': 'from . import common\n',
            recipes.APP+'/leaf.py': 'from .common import value\n',
            recipes.APP+'/common.py': 'value = 1\n',
        }
        for name, raw in files.items():
            path = self.base/name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(raw)
        self.assertEqual(recipes.local_closure(self.base, files, ['start']), set(files))
        (self.base/(recipes.APP+'/leaf.py')).write_text('from .missing import value\n')
        with self.assertRaisesRegex(core.LabError, 'Local recipe import is missing'):
            recipes.local_closure(self.base, files, ['start'])

    def test_missing_file_unknown_target_and_symlink_fail(self):
        tracked = self.roots()
        tracked.remove('scripts/host/aosvm-dns-bridge')
        with self.assertRaisesRegex(core.LabError, 'missing or untracked'):
            recipes.paths(core.ROOT, tracked, 'vm-runtime')
        with self.assertRaisesRegex(core.LabError, 'Unknown packaging'):
            recipes.paths(core.ROOT, tracked, 'unknown')
        directory = self.base/recipes.DIST
        directory.mkdir(parents=True)
        (directory/'linked.py').symlink_to(core.ROOT/'scripts/distribution/native_bundle.py')
        with self.assertRaisesRegex(core.LabError, 'Symlink'):
            recipes.local_closure(self.base, {recipes.DIST+'/linked.py'}, ['linked'])

    def test_fingerprint_selects_file_content_and_mode_not_unrelated_revision(self):
        name = 'scripts/host/aosvm-dns-bridge'
        listing = '100755 blob '+ 'a'*40 + '\t'+name+'\0'
        with patch('reproduction.packaging.git', side_effect=['', 'b'*40, listing]), \
                patch('reproduction.recipes.paths', return_value=[name]) as selected:
            identity, revision = packaging.producer(self.storage, 'vm-runtime')
        self.assertEqual(identity, {name: {'mode': '100755', 'blob': 'a'*40}})
        self.assertEqual(revision, 'b'*40)
        self.assertEqual(selected.call_args.args[-1], 'vm-runtime')
        with patch('reproduction.packaging.git', side_effect=['', 'c'*40, listing]), \
                patch('reproduction.recipes.paths', return_value=[name]):
            self.assertEqual(packaging.producer(self.storage, 'vm-runtime')[0], identity)
        for mode in ('100644', '120000'):
            with patch('reproduction.packaging.git', side_effect=['', 'c'*40, listing.replace('100755', mode)]), \
                    patch('reproduction.recipes.paths', return_value=[name]):
                if mode == '120000':
                    with self.assertRaisesRegex(core.LabError, 'linked or non-file'):
                        packaging.producer(self.storage, 'vm-runtime')
                else:
                    self.assertNotEqual(packaging.producer(self.storage, 'vm-runtime')[0], identity)

    def test_real_git_changes_have_only_selected_recipe_effects(self):
        checkout = self.base/'source'
        checkout.mkdir()
        for name in set().union(*self.selections().values()):
            target = checkout/name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(core.ROOT/name, target)
        env = self.storage.environment()
        def git(*args):
            subprocess.run(['git', '-C', str(checkout), *args], check=True,
                           capture_output=True, env=env, timeout=30)
        def commit():
            git('add', '.')
            git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                '-c', 'commit.gpgsign=false', 'commit', '-qm', 'fixture')
        git('init', '-q'); commit()
        def identities():
            return {target: packaging.producer(self.storage, target)[0] for target in recipes.ENTRIES}
        with patch('reproduction.packaging.ROOT', checkout):
            before = identities()
            (checkout/'README.md').write_text('Only documentation\n'); commit()
            self.assertEqual(before, identities())
            with (checkout/'scripts/distribution/native/Setup.swift').open('a') as stream:
                stream.write('\n// Fixture-only recipe change\n')
            commit()
            after = identities()
            self.assertEqual({name for name in before if before[name] != after[name]}, {'setup'})
            before = after
            with (checkout/'scripts/host/aosvm-dns-bridge').open('a') as stream:
                stream.write('\n# Fixture-only content change\n')
            commit()
            after = identities()
            self.assertEqual({name for name in before if before[name] != after[name]}, {'vm-runtime'})
            before = after
            with (checkout/'scripts/distribution/native_bundle.py').open('a') as stream:
                stream.write('\n# Shared validator change\n')
            commit()
            after = identities()
            self.assertEqual({name for name in before if before[name] != after[name]}, set(recipes.ENTRIES))


if __name__ == '__main__':
    unittest.main()
