# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Native bridge qualification with tiny non-executable package fixtures."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import test_distribution_installation as fixtures
with patch.object(sys, 'path', [str(fixtures.SCRIPTS), *sys.path]):
    import setup_bridge as bridge
    import setup_build as builder
    from version_management import control


class SetupTests(unittest.TestCase):
    def setUp(self):
        fixture = fixtures.InstallationTests()
        fixture.addCleanup = self.addCleanup
        fixture.setUp()
        self.f = fixture
        fixture.manifest['installedStateContract'] = control.CONTRACT
        fixture.rewrite_manifest()
        directory = tempfile.TemporaryDirectory(prefix='setup.', dir='/tmp')
        self.addCleanup(directory.cleanup)
        self.state = Path(directory.name).resolve() / 'state'
        for module, name, value in ((bridge, 'supported_platform', None),
                                    (bridge, 'internal_volume', None),
                                    (bridge, 'volume_identity', fixtures.UUID),
                                    (control, 'unused', None)):
            mock = patch.object(module, name, return_value=value)
            mock.start(); self.addCleanup(mock.stop)

    def req(self, action='preflight', **changes):
        value = dict(action=action, source=str(self.f.source), store=str(self.f.target), state=str(self.state))
        if action != 'preflight':
            value.update(volumeUUID=fixtures.UUID, revision=0)
        value.update(changes)
        return bridge.request(json.dumps(value).encode())

    def run_action(self, action='preflight', **changes):
        return bridge.perform(self.req(action, **changes), self.f.pin)

    def test_preflight_is_read_only_and_not_full_verification(self):
        result = self.run_action()
        self.assertEqual('PREFLIGHT_PASSED', result['status'])
        self.assertFalse(result['payloadDigestsVerified'])
        self.assertEqual(0, result['revision'])
        self.assertFalse(self.f.target.exists())
        self.assertFalse(self.state.exists())

    def test_install_then_prepare_and_repeat_are_separate(self):
        result = self.run_action('install')
        self.assertEqual('INSTALLED_NOT_ACTIVATED', result['status'])
        self.assertFalse(self.state.exists())
        self.assertTrue(self.run_action('install')['reused'])
        selected = self.run_action('prepare')
        self.assertEqual('SELECTED_NOT_STARTED', selected['status'])
        self.assertFalse(selected['demoReady'])
        self.assertFalse(selected['cloudAccessed'])
        self.assertFalse(selected['dockerEngineChecked'])
        before = {p: p.read_bytes() for p in self.state.rglob('*') if p.is_file()}
        preflight = self.run_action()
        self.assertEqual(1, preflight['revision'])
        self.assertEqual(before, {p: p.read_bytes() for p in self.state.rglob('*') if p.is_file()})
        self.assertTrue(self.run_action('prepare', revision=1)['reused'])
        self.assertEqual(before, {p: p.read_bytes() for p in self.state.rglob('*') if p.is_file()})

    def test_stale_prepare_keeps_selection(self):
        self.run_action('install'); self.run_action('prepare')
        before = (self.state / control.RECORD).read_bytes()
        with self.assertRaisesRegex(ValueError, 'STALE_REVISION'):
            self.run_action('prepare')
        self.assertEqual(before, (self.state / control.RECORD).read_bytes())

    def test_retained_run_is_not_deleted_to_unblock(self):
        self.run_action('install'); self.run_action('prepare')
        path = self.state / '.run/demo-current'
        path.mkdir(); (path / 'journal.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'CURRENT_RUN_RETAINED'):
            self.run_action('prepare', revision=1)
        self.assertEqual('{}', (path / 'journal.json').read_text())

    def test_wrong_volume_and_corruption_do_not_create_state(self):
        with self.assertRaisesRegex(ValueError, 'VOLUME_CHANGED'):
            self.run_action('install', volumeUUID=fixtures.OTHER)
        self.assertFalse(self.f.target.exists())
        path = self.f.source / 'aosedge-sdv-demo/LICENSE'
        path.chmod(0o644); raw = path.read_bytes(); path.write_bytes(b'X' + raw[1:])
        with self.assertRaisesRegex(ValueError, 'TRANSFER_MISMATCH'):
            self.run_action('install')
        self.assertFalse(self.state.exists())

    def test_prepare_before_install_has_no_state_side_effect(self):
        with self.assertRaisesRegex(ValueError, 'STORE_MISSING'):
            self.run_action('prepare')
        self.assertFalse(self.state.exists())

    def test_missing_receipt_does_not_create_state(self):
        self.run_action('install')
        (self.f.target / 'receipts' / (self.f.pin + '.json')).unlink()
        with self.assertRaises(OSError):
            self.run_action('prepare')
        self.assertFalse(self.state.exists())

    def test_foreign_state_is_preserved(self):
        self.state.mkdir(mode=0o700)
        keep = self.state / 'keep'; keep.write_text('unrelated')
        with self.assertRaises(OSError):
            self.run_action()
        self.assertEqual('unrelated', keep.read_text())
        self.assertFalse(self.f.target.exists())

    def test_missing_parent_long_path_and_internal_rule(self):
        with self.assertRaisesRegex(ValueError, 'PARENT_MISSING'):
            self.run_action(state=str(self.state / 'missing'))
        with self.assertRaisesRegex(ValueError, 'SOCKET_PATH_TOO_LONG'):
            self.run_action(state=str(self.state.with_name('a' * 100)))
        with patch.object(bridge, 'internal_volume', side_effect=ValueError('SETUP_STATE_INTERNAL_REQUIRED')):
            with self.assertRaisesRegex(ValueError, 'INTERNAL_REQUIRED'):
                self.run_action('install')
        self.assertFalse(self.f.target.exists())

    def test_invalid_protocol_and_paths(self):
        for raw in (b'[]', b'{}', b'{', b'{"action":"preflight","action":"install"}', b' ' * (bridge.LIMIT + 1)):
            with self.subTest(raw=raw[:60]), self.assertRaises(ValueError):
                bridge.request(raw)
        for changes in ({'unexpected': True}, {'source': 'relative'}, {'action': 'launch'},
                        {'state': str(self.f.source)}, {'state': str(self.f.target / 'data')},
                        {'source': str(self.f.source / '..')}, {'state': '/a\nb'}, {'pin': '0' * 64},
                        {'state': '//' + str(self.state).lstrip('/')}, {'state': str(self.state) + '/'}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.req(**changes)
        link = self.state.with_name('link'); link.symlink_to(self.f.source)
        with self.assertRaisesRegex(ValueError, 'PATH_HAS_LINK'):
            self.req(source=str(link))
        for revision in (True, -1, 2**53, '1'):
            with self.assertRaisesRegex(ValueError, 'REVISION_INVALID'):
                self.req('install', revision=revision)

    def test_source_pin_independent_and_incompatible_kit(self):
        with self.assertRaisesRegex(ValueError, 'MANIFEST_MISMATCH'):
            bridge.perform(self.req(), '0' * 64)
        self.f.manifest['installedStateContract'] = 'unsupported'; self.f.rewrite_manifest()
        with self.assertRaisesRegex(ValueError, 'COMPATIBILITY_UNSUPPORTED'):
            self.run_action()
        self.assertFalse(self.f.target.exists())

    def test_progress_is_bounded_and_never_emits_paths(self):
        events = []
        # Test throttling independently of filesystem/host scheduling delays.
        with patch.object(bridge.time, 'monotonic', return_value=1.0):
            bridge.perform(self.req('install'), self.f.pin, events.append)
        self.assertLess(len(events), 10)
        self.assertEqual('COPY_VERIFIED', events[-1]['stage'])
        self.assertEqual(events[-1]['bytes'], events[-1]['totalBytes'])
        self.assertNotIn(str(self.f.root), json.dumps(events))

    def test_error_redaction_and_process_protocol(self):
        for error in (OSError('/private/secret'), ValueError('token: sensitive'), RuntimeError('SECRET')):
            self.assertEqual('SETUP_OPERATION_FAILED', bridge.error_code(error))
        result = subprocess.run([sys.executable, '-I', '-B', str(fixtures.SCRIPTS / 'setup_bridge.py')],
                                input=b'{"secret":"do-not-echo"}', capture_output=True, timeout=20)
        self.assertEqual(1, result.returncode)
        self.assertEqual(b'', result.stderr)
        self.assertNotIn(b'do-not-echo', result.stdout)
        self.assertEqual('error', json.loads(result.stdout)['kind'])


class PlatformTests(unittest.TestCase):
    def test_supported_and_unsupported_platforms(self):
        for system, machine, version, allowed in (('darwin', 'arm64', '26.0', True),
                ('darwin', 'x86_64', '26.0', False), ('darwin', 'arm64', '15.7', False),
                ('linux', 'arm64', '', False)):
            with patch.object(bridge.sys, 'platform', system), patch.object(bridge.platform, 'machine', return_value=machine), \
                    patch.object(bridge.platform, 'mac_ver', return_value=(version, (), '')):
                if allowed:
                    bridge.supported_platform()
                else:
                    with self.assertRaisesRegex(ValueError, 'PLATFORM_UNSUPPORTED'):
                        bridge.supported_platform()

    def test_internal_volume_probe_rejects_external_disk(self):
        import plistlib
        from types import SimpleNamespace
        responses = [SimpleNamespace(returncode=0, stdout=b'Filesystem\n/dev/disk3s5 1 2 3\n'),
                     SimpleNamespace(returncode=0, stdout=plistlib.dumps({'Internal': False}))]
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(bridge.subprocess, 'run', side_effect=responses):
            with self.assertRaisesRegex(ValueError, 'INTERNAL_REQUIRED'):
                bridge.internal_volume(Path(directory))


class BootstrapTests(unittest.TestCase):
    def test_native_busy_state_hides_completed_step_guidance(self):
        source = (builder.HERE / 'native/Setup.swift').read_text()
        refresh = source.split('    private func refresh() {', 1)[1].split('\n    }', 1)[0]
        self.assertIn('next.isHidden = busy', refresh)
        self.assertIn('guard busy else { return true }', source)
        self.assertIn('You can close this setup window; the Presenter stays open.', source)

    def test_removable_storage_purpose_is_explicit_without_broad_entitlements(self):
        info = builder.bundle_info('SDVLabSetup')
        self.assertIn('selected', info['NSRemovableVolumesUsageDescription'])
        self.assertIn('external drive', info['NSRemovableVolumesUsageDescription'])
        self.assertNotIn('NSSystemAdministrationUsageDescription', info)
        self.assertEqual('SDVLabSetup', info['CFBundleExecutable'])

    def setUp(self):
        import hashlib
        from types import SimpleNamespace
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name).resolve()
        self.source = self.root / 'kit'; self.source.mkdir()
        self.target = self.root / 'python'
        rows = {}
        for leaf in ['bin/python3.12'] + ['lib/fixture' + str(n) for n in range(11)]:
            name = builder.PYTHON + leaf
            path = self.source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'bootstrap fixture, never executed')
            path.chmod(0o555 if leaf.startswith('bin/') else 0o444)
            rows[name] = SimpleNamespace(size=path.stat().st_size, mode=path.stat().st_mode & 0o777,
                                        sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        self.bundle = SimpleNamespace(root=self.source, rows=rows, unchanged=lambda name: None)

    def test_bootstrap_copy_is_only_pinned_subtree(self):
        (self.source / 'unrelated').write_text('must not be copied')
        self.assertEqual(12, builder.copy_python(self.bundle, self.target))
        self.assertFalse((self.target / 'unrelated').exists())
        self.assertEqual(0o555, (self.target / 'bin/python3.12').stat().st_mode & 0o777)

    def test_changed_bootstrap_is_rejected_before_execution(self):
        path = self.source / builder.PYTHON / 'bin/python3.12'
        path.chmod(0o755); path.write_bytes(b'altered')
        with self.assertRaisesRegex(ValueError, 'BOOTSTRAP_DIGEST_MISMATCH'):
            builder.copy_python(self.bundle, self.target)
        self.assertFalse((self.target / 'bin/python3.12').exists())

    def test_missing_bootstrap_executable_is_rejected(self):
        del self.bundle.rows[builder.PYTHON + 'bin/python3.12']
        with self.assertRaisesRegex(ValueError, 'BOOTSTRAP_MISSING'):
            builder.python_files(self.bundle)
