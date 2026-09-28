# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Packaged launch selection and ownership with no native external process."""
import hashlib
import json
import os
import subprocess
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from aosedge_demo_orchestrator import host_runtime as host
from aosedge_demo_orchestrator.environment import EnvironmentError, EnvironmentService
from aosedge_demo_orchestrator.source import SourceDriver
from aosedge_demo_orchestrator import source_authentication, source_cache
from aosedge_demo_orchestrator.workspace import WorkspaceService, geometry, prepare_controller


class HostTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='hl.', dir='/tmp')
        self.addCleanup(temp.cleanup)
        self.base = Path(temp.name).resolve()
        self.app = self.base / 'app'
        self.app.mkdir()
        self.root = self.base / 'demo-artifacts/aosedge-sdv-demo/host-runtime'
        self.root.mkdir(parents=True)
        self.lock = self.app / host.LOCK
        self.lock.parent.mkdir(parents=True)
        for name in host.ENTRY.values():
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'fixture')
            path.chmod(0o755)
        config = dict(controller={'autopilot': {}}, simulation={}, runtime={}, route={},
                      carla={'expected_map': 'Carla/Maps/Town10HD_Opt'})
        (self.root / host.ENTRY['config']).write_text(json.dumps(config))
        self.seal()
        self.env = EnvironmentService(self.app)
        self.vm = Mock(root=self.app, environment=self.env, children=[])
        self.driver = SourceDriver(self.vm)
        tls = self.app / 'operator-tls'
        tls.mkdir()
        for name in ('server-cert.pem', 'server-key.pem'):
            (tls / name).write_text('test fixture only, not certificate content')
        (self.app / 'workspace').mkdir()
        (self.app / 'workspace/repositories.json').write_text(json.dumps({'launcherPaths': [
            dict(id='tls', base='workspace', path='app/operator-tls')]}))
        self.screen = dict(x=0, y=39, width=2056, height=1224, desktopState='UNLOCKED')

    def seal(self, mutate=None):
        files = [dict(path=p.relative_to(self.root).as_posix(), bytes=p.stat().st_size,
                      mode=p.stat().st_mode & 0o777, sha256=hashlib.sha256(p.read_bytes()).hexdigest())
                 for p in self.root.rglob('*') if p.is_file() and p.name != host.MANIFEST]
        value = dict(schemaVersion=1, status='ASSEMBLED_HOST_LAUNCH_NOT_DISTRIBUTION_QUALIFIED', files=files)
        if mutate:
            value = mutate(value)
        raw = json.dumps(value).encode()
        (self.root / host.MANIFEST).write_bytes(raw)
        self.lock.write_text(json.dumps(dict(schemaVersion=1, contractId='aosedge-demo-portable-host-launch',
            manifest=dict(path=host.MANIFEST, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()))))

    def test_absence_is_development_but_invalid_selection_blocks(self):
        self.root.rename(self.root.with_name('not-selected'))
        self.assertIsNone(host.selected(self.app))
        self.root.symlink_to(self.root.with_name('not-selected'), target_is_directory=True)
        with self.assertRaisesRegex(EnvironmentError, 'PATH_UNSAFE'):
            host.selected(self.app)

    def test_manifest_requires_independent_pin(self):
        path = self.root / host.MANIFEST
        path.write_bytes(path.read_bytes().replace(b'fixture', b'another'))
        # Change a digest while preserving the serialized length.
        path.write_bytes(path.read_bytes().replace(b'"schemaVersion": 1', b'"schemaVersion": 2'))
        with self.assertRaisesRegex(EnvironmentError, 'MANIFEST_CHANGED'):
            host.selected(self.app)

    def test_changed_file_invalidates_in_process_hash_cache(self):
        reader = host.selected(self.app)
        path = reader.entry('presenter')
        original = path.stat().st_mtime_ns
        path.write_bytes(b'changed')
        os.utime(path, ns=(original, original))
        with self.assertRaisesRegex(EnvironmentError, 'FILE_CHANGED'):
            reader.entry('presenter')

    def test_missing_and_symlink_file_rejected(self):
        reader = host.selected(self.app)
        path = reader.entry('presenter')
        path.unlink()
        with self.assertRaisesRegex(EnvironmentError, 'FILE_UNAVAILABLE'):
            reader.entry('presenter')
        path.symlink_to(self.root / host.ENTRY['keyboard'])
        with self.assertRaisesRegex(EnvironmentError, 'PATH_UNSAFE'):
            reader.entry('presenter')

    def test_duplicate_escape_unbounded_and_wrong_modes_rejected(self):
        for change in (lambda v: dict(v, files=v['files']*2),
                       lambda v: dict(v, files=[dict(v['files'][0], path='../outside')]),
                       lambda v: dict(v, files=[dict(v['files'][0], bytes=33*2**30)]),
                       lambda v: dict(v, files=[dict(v['files'][0], mode=0o666)])):
            self.seal(change)
            with self.assertRaises(EnvironmentError):
                host.selected(self.app)

    def test_extra_importable_file_or_symlink_directory_is_not_trusted(self):
        reader = host.selected(self.app)
        extra = self.root / 'python/sitecustomize.py'
        extra.write_text('unexpected = True')
        with self.assertRaisesRegex(EnvironmentError, 'UNDECLARED_FILE'):
            reader.verify('python')
        extra.unlink()
        extra.symlink_to(self.app, target_is_directory=True)
        with self.assertRaisesRegex(EnvironmentError, 'PATH_UNSAFE'):
            reader.verify('python')

    def test_native_builds_and_editor_cache_do_not_fall_back(self):
        assets = self.driver.assets()
        self.assertNotIn('unreal-editor', assets)
        self.assertNotIn('project', assets)
        with patch('aosedge_demo_orchestrator.workspace.subprocess.run') as command:
            prepare_controller(assets, Mock())
            workspace = WorkspaceService(self.env, self.driver)
            workspace.build()
            self.assertEqual(self.root / host.ENTRY['presenter'], workspace.binary)
            self.assertTrue(source_authentication.build(self.driver)['noOp'])
            with self.assertRaisesRegex(EnvironmentError, 'EDITOR_ONLY'):
                source_cache.command(assets, self.base / 'log')
            command.assert_not_called()

    def test_geometry_and_private_callback_entry(self):
        paths = self.driver.assets()
        cmd = host.simulator_command(paths, self.screen)
        x, y, width, height = geometry(self.screen, combined=True)['carla']
        self.assertIn('-ResX=' + str(width), cmd)
        self.assertIn('-ResY=' + str(height - 32), cmd)
        self.assertIn('-WinX=' + str(x), cmd)
        self.assertIn('-WinY=' + str(y), cmd)
        self.assertIn('-ini:Game:[/Script/EngineSettings.GeneralProjectSettings]:bShouldWindowPreserveAspectRatio=False', cmd)
        self.assertNotIn('-game', cmd)
        self.assertFalse(any('.uproject' in arg for arg in cmd))
        self.assertEqual(['-I', '-B'], host.selected(self.app).cli(self.app)[1:3])

    def test_start_uses_existing_lifecycle_with_no_compiler_and_stable_repeat(self):
        state = dict(currentVehicle=None, vehicles={})
        commands = []
        self.driver.live_process = lambda cmd: 123 if cmd in commands else None
        self.driver.spawn = Mock(side_effect=lambda cmd, log, **kw: commands.append(cmd))
        self.driver.finish_start = Mock(side_effect=lambda s: s['source'])
        self.driver.ready = Mock(return_value={'fresh': True})
        def initialize(driver, value):
            value['source'] = {'trust': {'enabled': True}}
        probes = []
        def query(cmd, **kw):
            if cmd[-1] != 'screen':
                probes.append(cmd)
                if len(probes) == 1:
                    raise subprocess.TimeoutExpired(cmd, 6)
            return Mock(returncode=0, stdout=json.dumps(self.screen) if cmd[-1] == 'screen' else 'Carla/Maps/Town10HD_Opt')
        with patch.object(source_authentication, 'initialize_gateway', side_effect=initialize), \
                patch.object(source_authentication, 'runner_options', return_value=['--fixture-strict']), \
                patch.object(source_authentication, 'build') as build, \
                patch('aosedge_demo_orchestrator.source.subprocess.run', side_effect=query), \
                patch.dict(os.environ, {'PYTHONPATH': '/forbidden', 'DYLD_LIBRARY_PATH': '/forbidden'}):
            first = self.driver.start(state)
            self.assertEqual(2, self.driver.spawn.call_count)
            self.assertEqual(first, self.driver.start(state))
            self.assertEqual(2, self.driver.spawn.call_count)
            build.assert_not_called()
        self.assertEqual(2, len(probes))
        config = json.loads((self.app / first['runDirectory'] / 'input.json').read_bytes())
        self.assertEqual(88, config['route']['start_spawn_point'])
        self.assertEqual(.05, config['simulation']['fixed_delta_seconds'])
        self.assertEqual(18000, config['controller']['autopilot']['traffic_manager_port'])
        self.assertEqual(self.root / host.ENTRY['simulator'], Path(first['simulatorCommand'][0]))
        runner = first['runnerCommand']
        self.assertEqual(str(self.root / host.ENTRY['runtime']), runner[runner.index('--runtime')+1])
        callback = json.loads(runner[runner.index('--scene-command')+1])
        self.assertEqual(host.selected(self.app).cli(self.app), callback[:-3])
        for call in self.driver.spawn.call_args_list:
            self.assertNotIn('PYTHONPATH', call.kwargs['environment'])
            self.assertNotIn('DYLD_LIBRARY_PATH', call.kwargs['environment'])

    def test_bad_binary_blocks_before_any_spawn_or_gateway_enrollment(self):
        (self.root / host.ENTRY['runtime']).write_bytes(b'changed')
        with patch.object(self.driver, 'spawn') as spawn, patch.object(source_authentication, 'initialize_gateway') as enroll:
            with self.assertRaisesRegex(EnvironmentError, 'FILE_CHANGED'):
                self.driver.start({'vehicles': {}})
            spawn.assert_not_called(); enroll.assert_not_called()

    def test_missing_operator_tls_is_explicit_not_a_developer_fallback(self):
        (self.app / 'workspace/repositories.json').write_text('{"launcherPaths": []}')
        with self.assertRaisesRegex(EnvironmentError, 'SOURCE_OPERATOR_TLS_REQUIRED'):
            self.driver.assets()


if __name__ == '__main__':
    unittest.main()
