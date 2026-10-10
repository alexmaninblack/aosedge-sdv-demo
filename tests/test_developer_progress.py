# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Offline terminal, byte-event and readable-result tests; no product builds."""
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from developer_progress import Display
from developer_result import expose_result
from developer_bootstrap import WorkflowError
from developer_build import Owner


class Terminal(io.StringIO):
    def isatty(self):
        return True


class ProgressTests(unittest.TestCase):
    def display(self, tty=True):
        self.now = 0
        screen = Terminal() if tty else io.StringIO()
        with patch.dict(os.environ, TERM='xterm'):
            display = Display(screen, clock=lambda: self.now)
        return display, screen

    def select(self, display):
        display.event('ARTIFACT_SELECTED', {'role': 'carla-runtime', 'file': 'carla.tar.gz', 'bytes': 1000})

    def test_download_name_percentage_rate_and_resume_baseline(self):
        display, screen = self.display()
        self.select(display)
        display.event('DOWNLOAD_STARTED', {'offset': 500, 'totalBytes': 1000})
        self.now = 2
        display.event('DOWNLOAD_BYTES', 600)
        text = screen.getvalue()
        self.assertIn('CARLA simulator — carla.tar.gz', text)
        self.assertIn('60.0%', text)
        self.assertIn('50.0 B/s', text)  # Existing partial bytes never inflate speed.
        self.assertIn('~8s left', text)
        self.assertIn('\r\033[2K', text)
        self.assertNotIn('workflow-', text)

    def test_stalled_download_removes_obsolete_eta(self):
        display, screen = self.display()
        self.select(display)
        display.event('DOWNLOAD_STARTED', {'offset': 0})
        self.now = 2
        display.event('DOWNLOAD_BYTES', 200)
        self.now = 10
        display.draw()
        last = screen.getvalue().split('\r')[-1]
        self.assertIn('waiting for data', last)
        self.assertNotIn('left', last)

    def test_unknown_work_has_animation_but_no_fake_percentage(self):
        display, screen = self.display()
        display.begin('Signing Setup', 'Signing')
        self.now = 3
        display.draw()
        self.assertIn('====', screen.getvalue())
        self.assertNotIn('%', screen.getvalue())
        self.assertNotIn('left', screen.getvalue())
        display.finish(False)
        self.assertIn('Stopped', screen.getvalue())
        self.assertNotIn('Done.', screen.getvalue())

    def test_steps_count_only_verified_results_and_no_build_eta(self):
        display, screen = self.display()
        display.event('CHAIN_STARTED', 17)
        display.event('CHAIN_STEP', 'gateway')
        self.assertEqual(display.done, 0)
        display.event('CHAIN_STEP_VERIFIED', 'gateway')
        display.event('CHAIN_STEP_VERIFIED', 'gateway')
        self.assertEqual(display.done, 1)
        display.event('CHAIN_STEP', 'setup')
        self.assertIn('1/17 steps verified', screen.getvalue())
        self.assertNotIn('left', screen.getvalue())

    def test_nonterminal_is_bounded_plain_output(self):
        display, screen = self.display(False)
        self.select(display)
        display.event('DOWNLOAD_STARTED', {'offset': 0})
        for value in range(1, 1000):
            self.now += .1
            display.event('DOWNLOAD_BYTES', value)
        self.assertLess(len(screen.getvalue().splitlines()), 10)
        self.assertNotIn('\r', screen.getvalue())
        self.assertNotIn('\033', screen.getvalue())

    def test_extract_and_cached_paths(self):
        display, screen = self.display()
        self.select(display)
        display.event('ARTIFACT_REUSED', 'fixture-digest')
        self.assertIn('Reusing verified cache', screen.getvalue())
        display.event('EXTRACT_STARTED', {'role': 'factory-image', 'totalBytes': 200})
        display.event('EXTRACT_BYTES', {'role': 'factory-image', 'bytes': 100})
        display.event('EXTRACT_FINISHED', 'factory-image')
        self.assertEqual(display.done, 200)
        self.assertIn('Unpacking — Factory controller image', screen.getvalue())

    def test_invalid_artifact_name_not_printed(self):
        display, screen = self.display()
        display.event('ARTIFACT_SELECTED', {'role': 'carla-runtime', 'file': 'bad\033[2J', 'bytes': 12})
        self.assertEqual(screen.getvalue(), '')

    def test_narrow_terminal_line_does_not_wrap(self):
        display, screen = self.display()
        with patch('developer_progress.shutil.get_terminal_size', return_value=os.terminal_size((42, 24))):
            display.begin('CARLA', 'Downloading', 100)
            display.update(90)
        for line in screen.getvalue().split('\r')[1:]:
            self.assertLessEqual(len(line.removeprefix('\033[2K')), 41)


class ResultTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir='/private/tmp' if sys.platform == 'darwin' else None)
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root/'.developer-preparation').mkdir()
        self.receipt = self.root/'build/builds/chains'/('a'*64+'.json')
        self.receipt.parent.mkdir(parents=True)
        self.receipt.write_text('{}')

    def dmg(self, key='b'):
        path = self.root/'build/builds/dmg'/(key*64)/'AosEdge-SDV-Lab.dmg'
        path.parent.mkdir(parents=True)
        path.write_bytes(b'tiny fixture, not a DMG')
        return path

    def test_first_repeat_and_successor_do_not_duplicate_or_remove_bytes(self):
        first = self.dmg()
        before = first.stat()
        shown = expose_result(self.root, first, self.receipt)
        self.assertEqual(shown, str(self.root/'output'/first.name))
        self.assertEqual(Path(shown).read_bytes(), first.read_bytes())
        self.assertEqual(expose_result(self.root, first, self.receipt), shown)
        second = self.dmg('c')
        expose_result(self.root, second, self.receipt)
        self.assertEqual((self.root/'output').resolve(), second.parent)
        self.assertEqual(first.stat(), before)

    def test_foreign_files_and_links_are_preserved(self):
        dmg = self.dmg()
        output = self.root/'output'
        output.mkdir()
        with self.assertRaisesRegex(WorkflowError, 'already in use'):
            expose_result(self.root, dmg, self.receipt)
        output.rmdir()
        output.symlink_to(dmg.parent)
        with self.assertRaisesRegex(WorkflowError, 'Unowned'):
            expose_result(self.root, dmg, self.receipt)
        self.assertTrue(output.is_symlink())

    def test_crash_before_and_after_link_replacement_reconciles_intent(self):
        first, second = self.dmg(), self.dmg('c')
        expose_result(self.root, first, self.receipt)
        state = self.root/'.developer-preparation/output-link.json'
        state.write_text(json.dumps({'schemaVersion': 1, 'current': str(first.parent.relative_to(self.root)),
                                     'pending': str(second.parent.relative_to(self.root))}))
        expose_result(self.root, second, self.receipt)
        self.assertEqual((self.root/'output').resolve(), second.parent)
        state.write_text(json.dumps({'schemaVersion': 1, 'current': str(first.parent.relative_to(self.root)),
                                     'pending': str(second.parent.relative_to(self.root))}))
        (self.root/'output').unlink()
        (self.root/'output').symlink_to(second.parent.relative_to(self.root))
        expose_result(self.root, second, self.receipt)
        self.assertIsNone(json.loads(state.read_text())['pending'])

    def test_only_verified_layout_is_allowed(self):
        dmg = self.root/'random.dmg'
        dmg.write_text('fixture')
        with self.assertRaisesRegex(WorkflowError, 'outside'):
            expose_result(self.root, dmg, self.receipt)
        self.assertFalse((self.root/'output').exists())

    def test_owner_closes_progress_after_cancellation(self):
        import reproduction.cli
        screen = Terminal()
        with patch('sys.stdout', screen), patch.object(reproduction.cli, 'main', side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                Owner(self.root/'.developer-preparation')('Fixture', [])
        self.assertIn('Stopped', screen.getvalue())
        self.assertNotIn('Done.', screen.getvalue())


if __name__ == '__main__':
    unittest.main()
