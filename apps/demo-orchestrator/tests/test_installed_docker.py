# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Declared Docker Desktop prerequisite under the native minimal environment."""
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock, patch

from aosedge_demo_orchestrator.backends import BackendService
from aosedge_demo_orchestrator.backend_retirement import BackendRetirement
from aosedge_demo_orchestrator.environment import EnvironmentError


class InstalledDockerTests(TestCase):
    def setUp(self):
        self.service = BackendService(SimpleNamespace(root=Path('/fixture/instance'),
            catalog=SimpleNamespace(project=Path('/fixture/catalog'))))

    def test_installed_uses_declared_app_without_inherited_path(self):
        with patch('aosedge_demo_orchestrator.runtime_paths.installed', return_value=True), \
                patch('shutil.which', return_value='/Applications/Docker.app/Contents/Resources/bin/docker') as locate:
            self.service._run = Mock(return_value='observed')
            self.assertEqual('observed', self.service._docker('version', timeout=3))
            locate.assert_called_once_with('docker', path='/Applications/Docker.app/Contents/Resources/bin')
            self.service._run.assert_called_once_with(['/Applications/Docker.app/Contents/Resources/bin/docker', 'version'], 3)

    def test_missing_declared_app_blocks_without_developer_fallback_or_execution(self):
        with patch('aosedge_demo_orchestrator.runtime_paths.installed', return_value=True), \
                patch('shutil.which', return_value=None) as locate:
            self.service._run = Mock()
            with self.assertRaisesRegex(EnvironmentError, '^BACKEND_DOCKER_REQUIRED$'):
                self.service._docker('info')
            locate.assert_called_once_with('docker', path='/Applications/Docker.app/Contents/Resources/bin')
            self.service._run.assert_not_called()

    def test_developer_resolution_unchanged(self):
        with patch('aosedge_demo_orchestrator.runtime_paths.installed', return_value=False), \
                patch('shutil.which', return_value='/fixture/docker') as locate:
            self.assertEqual('/fixture/docker', self.service._docker_executable())
            locate.assert_called_once_with('docker')

    def test_admin_operation_uses_same_resolver_and_preserves_bounded_stdin(self):
        with patch.object(self.service, '_docker_executable', return_value='/fixed/docker') as locate, \
                patch('subprocess.run', return_value=Mock(returncode=0, stdout='{"status":200,"body":{}}')) as run:
            self.assertEqual({}, BackendRetirement(self.service)._private('brake', 'a' * 64, 'preview'))
            locate.assert_called_once_with()
            self.assertEqual('/fixed/docker', run.call_args.args[0][0])
            self.assertEqual('{}\n', run.call_args.kwargs['input'])
            self.assertEqual(12, run.call_args.kwargs['timeout'])
