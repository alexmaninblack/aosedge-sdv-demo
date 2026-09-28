# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Private SDK dispatch fixtures only: no network, SDK or operator credentials."""

import hashlib
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from aosedge_demo_orchestrator import cloud_runtime as portable
from aosedge_demo_orchestrator.environment import EnvironmentError, EnvironmentService
from aosedge_demo_orchestrator.images import ImageCatalog


class CloudRuntimeTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='cloud inputs ')
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name).resolve()
        self.root = self.base / 'demo'
        self.root.mkdir()
        self.catalog = ImageCatalog(workspace=self.base)
        self.bundle = self.catalog.project / 'cloud-runtime'
        self.bundle.mkdir(parents=True)
        self.lock = self.root / portable.LOCK
        self.lock.parent.mkdir(parents=True)
        for name in [portable.PYTHON, 'lib/python3.12/site-packages/sdk.py',
                     *('demo/scripts/host/' + n for n in portable.ADAPTERS)]:
            path = self.bundle / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'fixture-not-executable')
            path.chmod(0o755 if name == portable.PYTHON else 0o644)
        self.seal()
        self.env = EnvironmentService(self.root, catalog=self.catalog)
        self.credential = self.root / 'synthetic-credential'
        self.credential.write_text('not a certificate or secret')
        self.credential.chmod(0o600)
        self.oem = dict(expectedRole='oem', credential=self.credential)
        self.sp = dict(expectedRole='service provider', credential=self.credential)
        self.config = dict(cloudPython=Path('/missing/developer/python'),
                           cloudProfiles={'oem-delivery': self.oem, 'service-provider': self.sp})

    def seal(self, change=None):
        value = dict(schemaVersion=1, status='ASSEMBLED_NOT_INTEGRATED', operatorCredentialsCopied=False,
            files=[dict(path=str(p.relative_to(self.bundle)), bytes=p.stat().st_size,
                        sha256=hashlib.sha256(p.read_bytes()).hexdigest())
                   for p in self.bundle.rglob('*') if p.is_file() and p.name != portable.MANIFEST])
        if change:
            change(value)
        raw = json.dumps(value).encode()
        (self.bundle / portable.MANIFEST).write_bytes(raw)
        self.lock.write_text(json.dumps(dict(schemaVersion=1, contractId=portable.CONTRACT,
            manifest=dict(path=portable.MANIFEST, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()))))

    def test_absent_retains_developer_command_and_minimal_environment(self):
        self.bundle.rename(self.bundle.with_name('not-selected'))
        with patch.dict(os.environ, {portable.HINT: '/untrusted', 'PYTHONPATH': '/bad'}):
            cmd, env = portable.launch(self.root, '/developer/python', 'cloud.py')
        self.assertEqual(['/developer/python', '-I', '-B'], cmd[:3])
        self.assertEqual({'PATH': os.defpath}, env)

    def test_all_fixed_workers_share_the_same_verified_interpreter(self):
        for name in portable.WORKERS:
            cmd, env = portable.launch(self.root, '/must-not-run', name)
            self.assertEqual([str(self.bundle / portable.PYTHON), '-I', '-B'], cmd[:3])
            self.assertEqual(name, Path(cmd[3]).name)
            self.assertEqual({'PATH': os.defpath, portable.HINT: str(self.bundle)}, env)
        with self.assertRaisesRegex(EnvironmentError, 'WORKER_INVALID'):
            portable.launch(self.root, '/x', '../arbitrary.py')

    def test_full_verification_is_not_configuration_parsing(self):
        from aosedge_demo_orchestrator.status import load_configuration
        with patch.object(portable.CloudRuntime, 'verify', side_effect=AssertionError('not a status parse')):
            load_configuration(self.root)

    def test_warm_hash_rechecks_modified_files(self):
        portable.launch(self.root, '/x', 'cloud.py')
        (self.bundle / 'lib/python3.12/site-packages/sdk.py').write_bytes(b'changed')
        with self.assertRaisesRegex(EnvironmentError, 'FILE_CHANGED'):
            portable.launch(self.root, '/x', 'cloud.py')

    def test_extra_modules_links_and_writable_files_block(self):
        extra = self.bundle / 'lib/python3.12/site-packages/extra.py'
        for kind in ('file', 'link', 'directory'):
            if kind == 'file':
                extra.write_text('untrusted')
            elif kind == 'link':
                extra.symlink_to(self.root)
            else:
                extra.mkdir(mode=0o777)
                extra.chmod(0o777)
            with self.assertRaises(EnvironmentError):
                portable.launch(self.root, '/x', 'cloud.py')
            extra.rmdir() if kind == 'directory' else extra.unlink()
        (self.bundle / portable.PYTHON).chmod(0o777)
        with self.assertRaisesRegex(EnvironmentError, 'FILE_CHANGED'):
            portable.launch(self.root, '/x', 'cloud.py')

    def test_missing_interpreter_and_non_executable_block(self):
        path = self.bundle / portable.PYTHON
        path.chmod(0o644)
        with self.assertRaisesRegex(EnvironmentError, 'INTERPRETER_NOT_EXECUTABLE'):
            portable.launch(self.root, '/x', 'cloud.py')
        path.unlink()
        with self.assertRaisesRegex(EnvironmentError, 'FILE_UNAVAILABLE'):
            portable.launch(self.root, '/x', 'cloud.py')

    def test_manifest_needs_independent_pin(self):
        path = self.bundle / portable.MANIFEST
        path.write_bytes(path.read_bytes() + b' ')
        with self.assertRaises(EnvironmentError):
            portable.launch(self.root, '/x', 'cloud.py')

    def test_invalid_manifest_rows_are_bounded(self):
        for change in (lambda v: v['files'].append(v['files'][0]),
                       lambda v: v['files'][0].update(path='../outside'),
                       lambda v: v['files'][0].update(bytes=512*2**20),
                       lambda v: v.update(operatorCredentialsCopied=True)):
            self.seal(change)
            with self.assertRaises(EnvironmentError):
                portable.selected(self.root)

    def test_adapter_requires_private_identity_and_valid_closure(self):
        with patch.dict(os.environ, {portable.HINT: str(self.bundle)}):
            with self.assertRaisesRegex(EnvironmentError, 'INTERPRETER_MISMATCH'):
                portable.adapter_directory(self.root)
            with patch.object(portable.sys, 'executable', str(self.bundle / portable.PYTHON)):
                self.assertEqual(self.bundle / 'demo/scripts/host', portable.adapter_directory(self.root))
                (self.bundle / 'demo/scripts/host' / portable.ADAPTERS[0]).write_text('changed')
                with self.assertRaises(EnvironmentError):
                    portable.adapter_directory(self.root)
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(self.root / 'scripts/host', portable.adapter_directory(self.root))

    def test_unit_dispatch_preserves_request_timeout_and_local_failure_is_not_attempt(self):
        from aosedge_demo_orchestrator.units import UnitService
        service = UnitService(SimpleNamespace(environment=self.env, root=self.root, progress=lambda _: None))
        with patch('aosedge_demo_orchestrator.units.load_configuration', return_value=self.config), \
                patch('aosedge_demo_orchestrator.units.subprocess.run', return_value=Mock(
                    returncode=0, stdout='{"ok":true,"data":{"fixture":true}}')) as run:
            self.assertEqual({'fixture': True}, service._cloud('provision', identity={'fixture': True}))
            self.assertTrue(service.mutations_started)
            self.assertEqual(195, run.call_args.kwargs['timeout'])
            self.assertEqual({'action': 'provision', 'identity': {'fixture': True},
                'credential': str(self.credential)}, json.loads(run.call_args.kwargs['input']))
            self.assertEqual(str(self.bundle / portable.PYTHON), run.call_args.args[0][0])
            service.mutations_started = False
            (self.bundle / portable.PYTHON).unlink()
            run.reset_mock()
            with self.assertRaises(EnvironmentError):
                service._cloud('provision')
            self.assertFalse(service.mutations_started)
            run.assert_not_called()

    def test_native_identity_rejects_bad_inputs_before_ssh(self):
        from aosedge_demo_orchestrator.service_inputs import ServiceInputs
        (self.bundle / portable.PYTHON).unlink()
        with patch('aosedge_demo_orchestrator.service_inputs.load_configuration', return_value=self.config), \
                patch('aosedge_demo_orchestrator.service_inputs.subprocess.Popen') as popen, \
                self.assertRaises(EnvironmentError):
            ServiceInputs(self.env).identity({}, 'main:8090')
        popen.assert_not_called()

    def test_observations_report_runtime_failure_not_permission_failure(self):
        from aosedge_demo_orchestrator.cloud import cloud_status
        from aosedge_demo_orchestrator.services import ServiceCatalog
        (self.bundle / portable.PYTHON).unlink()
        with patch('subprocess.Popen') as popen, patch('subprocess.run') as run:
            result = cloud_status('oem-delivery', self.oem, {}, Path('/x'), 8, root=self.root)
            self.assertEqual('CLOUD_RUNTIME_FILE_UNAVAILABLE', result['access']['reason'])
            result = ServiceCatalog(self.env)._read('service-provider', self.sp, self.config, 'list', None)
            self.assertEqual('CLOUD_RUNTIME_FILE_UNAVAILABLE', result['authority']['reason'])
        popen.assert_not_called(); run.assert_not_called()

    def test_component_service_schema_and_certificate_dispatch(self):
        from aosedge_demo_orchestrator.components import ComponentService
        from aosedge_demo_orchestrator.service_packages import ServicePackages
        from aosedge_demo_orchestrator.cloud_connection import CloudConnection
        package = ServicePackages(self.env)
        connection = CloudConnection(self.env)
        with patch('aosedge_demo_orchestrator.status.load_configuration', return_value=self.config), \
                patch('aosedge_demo_orchestrator.service_packages.load_configuration', return_value=self.config), \
                patch.object(connection, '_configuration', return_value={'cloudPython': '/missing'}), \
                patch('subprocess.run', return_value=Mock(returncode=0,
                    stdout='{"ok":true,"data":{"state":"VALIDATED_SERVICE_CONFIG"}}')) as run:
            ComponentService(self.env)._worker('cloud-status', purpose='overview')
            self.assertEqual(30, run.call_args.kwargs['timeout'])
            package._worker('cloud-status', self.root, dict(team='brake', version='1.0.0', cloudProfile='service-provider'))
            self.assertEqual(90, run.call_args.kwargs['timeout'])
            package._validate(self.root)
            self.assertEqual(30, run.call_args.kwargs['timeout'])
            run.return_value.stdout = '{"ok":true,"data":{"domain":"example.test"}}'
            connection.inspect(self.credential)
            self.assertEqual(8, run.call_args.kwargs['timeout'])
            for call in run.call_args_list:
                self.assertEqual(str(self.bundle / portable.PYTHON), call.args[0][0])
                self.assertEqual(str(self.bundle), call.kwargs['env'][portable.HINT])


if __name__ == '__main__':
    unittest.main()
