# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Small filesystem fixtures only; no compiler, download, signing or runtime."""
import json
import ast
import os
from pathlib import Path
import subprocess
import signal
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts/distribution'))
import build_scratch as scratch


class ScratchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.anchor = Path(self.temp.name).resolve()
        self.env = patch.dict(os.environ)
        self.env.start()
        self.addCleanup(self.env.stop)
        os.environ.pop('SDV_SCRATCH_ROOT', None)

    def runs(self):
        return [p for p in (self.anchor/'.tmp').iterdir() if p.is_dir()]

    def test_success_and_failure_remove_scratch_preserve_cache_output_and_log(self):
        for name in ('cache', 'output.dmg', 'report.json'):
            (self.anchor/name).write_text('keep')
        for fail in (False, True):
            try:
                with scratch.directory(self.anchor) as work:
                    (work/'large-copy').write_bytes(b'fixture')
                    self.assertTrue(work.is_relative_to(self.anchor/'.tmp'))
                    if fail:
                        raise RuntimeError('fixture')
            except RuntimeError:
                self.assertTrue(fail)
            self.assertFalse(work.exists())
            self.assertEqual(self.runs(), [])
        for name in ('cache', 'output.dmg', 'report.json'):
            self.assertEqual((self.anchor/name).read_text(), 'keep')

    def test_nested_or_active_run_is_not_reaped(self):
        with scratch.directory(self.anchor) as outer:
            with scratch.directory(self.anchor) as inner:
                self.assertNotEqual(outer, inner)
                self.assertTrue(outer.exists())
            self.assertTrue(outer.exists())

    def test_killed_owner_recovered_on_next_invocation(self):
        code = ('import os,sys; from pathlib import Path; '
                'sys.path.insert(0,sys.argv[1]); import build_scratch as s; '
                'c=s.directory(Path(sys.argv[2])); p=c.__enter__(); '
                '(p/"partial").write_bytes(b"fixture"); os._exit(9)')
        result = subprocess.run([sys.executable, '-B', '-c', code,
                                 str(ROOT/'scripts/distribution'), str(self.anchor)])
        self.assertEqual(result.returncode, 9)
        self.assertEqual(len(self.runs()), 1)
        with self.assertWarns(UserWarning), scratch.directory(self.anchor):
            self.assertEqual(len(self.runs()), 1)
        self.assertEqual(self.runs(), [])

    def test_normal_termination_unwinds_scratch(self):
        sentinel = self.anchor/'started'
        code = ('import sys,time; from pathlib import Path; '
                'sys.path.insert(0,sys.argv[1]); import build_scratch as s\n'
                'with s.directory(Path(sys.argv[2])) as p:\n'
                ' Path(sys.argv[3]).write_text(str(p))\n'
                ' time.sleep(20)\n')
        process = subprocess.Popen([sys.executable, '-B', '-c', code,
            str(ROOT/'scripts/distribution'), str(self.anchor), str(sentinel)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            for _ in range(100):
                if sentinel.exists():
                    break
                time.sleep(.01)
            self.assertTrue(sentinel.exists())
            process.send_signal(signal.SIGTERM)
            process.communicate(timeout=5)
            self.assertNotEqual(process.returncode, 0)
            self.assertEqual(self.runs(), [])
        finally:
            if process.poll() is None:
                process.kill()
                process.communicate(timeout=5)

    def test_build_owners_use_managed_scratch(self):
        paths = list((ROOT/'scripts/reproduction').glob('*.py'))
        paths += [ROOT/'scripts/distribution'/name for name in (
            'full_dmg.py', 'native_bundle.py', 'setup_build.py', 'vm_inputs.py')]
        for path in paths:
            tree = ast.parse(path.read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                    self.assertNotIn(node.func.attr, ('mkdtemp', 'TemporaryDirectory'), str(path))

    def test_busy_abandoned_run_is_preserved(self):
        with scratch.directory(self.anchor) as active:
            metadata = active.parent/'.run.json'
            value = json.loads(metadata.read_bytes())
            value['pid'] = 99999999
            metadata.write_text(json.dumps(value))
            with patch.object(scratch, 'alive', return_value=False), patch.object(scratch, 'idle', return_value=False):
                with scratch.directory(self.anchor):
                    self.assertTrue(active.exists())

    def test_foreign_and_unmarked_paths_are_preserved(self):
        root = self.anchor/'.tmp'
        root.mkdir(mode=0o700)
        (root/'keep').write_text('foreign')
        with self.assertRaises(scratch.ScratchError):
            with scratch.directory(self.anchor):
                pass
        self.assertEqual((root/'keep').read_text(), 'foreign')

    def test_foreign_child_in_owned_root_is_not_removed(self):
        root = scratch.root_for(self.anchor)
        foreign = root/'run-abcdefgh'
        foreign.mkdir(mode=0o700)
        (foreign/'keep').write_text('foreign')
        with scratch.directory(self.anchor):
            pass
        self.assertTrue((foreign/'keep').exists())

    def test_linked_root_rejected_and_inner_link_target_preserved(self):
        other = self.anchor/'other'
        other.mkdir()
        (other/'keep').write_text('safe')
        (self.anchor/'.tmp').symlink_to(other)
        with self.assertRaises(scratch.ScratchError):
            with scratch.directory(self.anchor):
                pass
        (self.anchor/'.tmp').unlink()
        with scratch.directory(self.anchor) as work:
            (work/'link').symlink_to(other)
        self.assertEqual((other/'keep').read_text(), 'safe')

    def test_compact_socket_path_keeps_original_nine_byte_suffix(self):
        with scratch.directory(self.anchor, compact=True) as work:
            self.assertEqual(work.parent, self.anchor/'.tmp')
            self.assertEqual(len(work.name), 9)
        self.assertFalse(work.exists())

    def test_explicit_workspace_root_is_shared_by_packagers(self):
        nested = self.anchor/'outputs'
        nested.mkdir()
        os.environ['SDV_SCRATCH_ROOT'] = str(self.anchor/'.tmp')
        with scratch.directory(nested) as work:
            self.assertTrue(work.is_relative_to(self.anchor/'.tmp'))
        self.assertFalse((nested/'.tmp').exists())

    def test_replaced_root_is_preserved_not_deleted(self):
        context = scratch.directory(self.anchor)
        work = context.__enter__()
        root = self.anchor/'.tmp'
        root.rename(self.anchor/'old-scratch')
        root.mkdir(mode=0o700)
        (root/'keep').write_text('new')
        with self.assertRaises(scratch.ScratchError):
            context.__exit__(None, None, None)
        self.assertEqual((root/'keep').read_text(), 'new')


if __name__ == '__main__':
    unittest.main()
