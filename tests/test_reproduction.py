# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""R2 offline fixtures; no Cloud account, host installer or runtime is used."""
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import plistlib
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from reproduction import artifacts, build, cli, cloud, containers, core, sources


class ReleaseTests(unittest.TestCase):
    def test_profiles_select_only_needed_source_roles(self):
        release = core.Release()
        self.assertEqual(len(release.selected_sources('operator')), 0)
        self.assertEqual(len(release.selected_sources('developer')), 7)
        self.assertEqual(len(release.selected_sources('full-source')), 10)
        self.assertNotIn('unreal', release.selected_sources('developer'))

    def test_plan_is_offline_and_never_claims_qualification(self):
        with patch('reproduction.core.external_volume', side_effect=AssertionError), redirect_stdout(io.StringIO()) as output:
            self.assertEqual(cli.main(['plan']), 0)
        self.assertFalse(json.loads(output.getvalue())['qualified'])

    def test_invalidation_is_owner_and_downstream_only(self):
        release = core.Release()
        before = {row['id']: row['key'] for row in release.graph('developer')}
        release.sources['tire-health-cloud']['revision'] = 'f' * 40
        after = {row['id']: row['key'] for row in release.graph('developer')}
        self.assertEqual({name for name in before if before[name] != after[name]},
                         {'tire-backend', 'backend-export', 'application', 'setup-media'})

    def test_dependencies_precede_consumers(self):
        seen = set()
        for row in core.Release().graph('developer'):
            self.assertTrue(set(row['requires']).issubset(seen))
            seen.add(row['id'])


class StorageFixture:
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='lab-r2-')
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name).resolve()
        self.release = core.Release()
        self.volume = {'mount': str(self.base), 'uuid': 'TEST-VOLUME', 'device': self.base.stat().st_dev}
        self.patch('reproduction.core.external_volume', return_value=self.volume)
        self.patch('pathlib.Path.is_mount', lambda p: p == self.base)
        self.patch('reproduction.core.shutil.disk_usage', return_value=SimpleNamespace(free=300*core.GIB))
        self.storage = core.Storage(self.base / 'workspace', self.release, 'developer')
        self.storage.initialize()
        self.state = self.storage.state()

    def patch(self, *args, **kwargs):
        item = patch(*args, **kwargs)
        self.addCleanup(item.stop)
        return item.start()


class StorageTests(StorageFixture, unittest.TestCase):
    def test_state_repeats_and_does_not_store_credentials(self):
        before = self.storage.state_path.read_bytes()
        self.storage.initialize()
        self.assertEqual(self.storage.state_path.read_bytes(), before)
        self.assertEqual(set(self.state), {'binding', 'sources', 'artifacts', 'builds'})

    def test_all_bindings_are_enforced(self):
        for field in ('profile', 'release', 'volumeUUID'):
            value = copy.deepcopy(self.state)
            value['binding'][field] = 'different'
            core.atomic_json(self.storage.state_path, value)
            with self.assertRaisesRegex(core.LabError, 'differs'):
                self.storage.state()

    def test_unowned_nonempty_directory_preserved(self):
        path = self.base / 'foreign'
        path.mkdir()
        (path / 'keep').write_text('keep')
        foreign = core.Storage(path, self.release, 'developer')
        with self.assertRaisesRegex(core.LabError, 'unowned'):
            foreign.initialize()
        self.assertEqual((path / 'keep').read_text(), 'keep')

    def test_volume_disconnect_and_replacement_fail_closed(self):
        with patch('pathlib.Path.is_mount', return_value=False):
            with self.assertRaisesRegex(core.LabError, 'disconnected'):
                self.storage.path('cache/item')
        self.volume['device'] = -1
        with self.assertRaisesRegex(core.LabError, 'replaced'):
            self.storage.check()

    def test_space_guard_and_path_escapes(self):
        with patch('reproduction.core.shutil.disk_usage', return_value=SimpleNamespace(free=60*core.GIB)):
            with self.assertRaisesRegex(core.LabError, 'space'):
                self.storage.check(additional=1)
        for relative in ('../outside', '/outside'):
            with self.assertRaisesRegex(core.LabError, 'escapes'):
                self.storage.path(relative)

    def test_symlinks_and_hardlinks_refused(self):
        path = self.storage.root / 'file'
        path.write_text('keep')
        (self.storage.root / 'link').symlink_to(path)
        with self.assertRaisesRegex(core.LabError, 'Symlink'):
            self.storage.path('link')
        os.link(path, self.storage.root / 'hardlink')
        with self.assertRaisesRegex(core.LabError, 'regular'):
            core.regular(path)

    def test_concurrent_writer_refused(self):
        with self.storage.locked():
            with self.assertRaisesRegex(core.LabError, 'active'):
                with self.storage.locked():
                    self.fail('Second writer entered')

    def test_cache_and_temporary_environment_is_on_storage(self):
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'do-not-inherit', 'NPM_TOKEN': 'do-not-inherit'}):
            env = self.storage.environment()
        self.assertNotIn('OPENAI_API_KEY', env)
        self.assertNotIn('NPM_TOKEN', env)
        self.assertNotIn('HOME', env)
        for key in ('TMPDIR', 'npm_config_cache', 'PIP_CACHE_DIR', 'XDG_CACHE_HOME'):
            self.assertTrue(Path(env[key]).is_relative_to(self.storage.root))

    def test_status_explains_incomplete_preparation(self):
        result = cli.status(self.storage, self.state)
        self.assertEqual(result['status'], 'SOURCES_PARTIAL')
        self.assertEqual(len(result['missingSources']), 7)
        self.assertFalse(result['profileReady'])

    def test_verify_partial_and_full_profile_never_false_pass(self):
        with redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main(['verify', '--storage', str(self.storage.root)]), 2)
            self.assertEqual(cli.main(['verify', '--sources-only', '--storage', str(self.storage.root)]), 2)
            self.assertEqual(cli.main(['build', '--storage', str(self.storage.root)]), 1)


class VolumeProbeTests(unittest.TestCase):
    def test_probe_uses_mount_not_child_directory(self):
        with tempfile.TemporaryDirectory(prefix='lab-volume-') as temporary:
            mount = Path(temporary).resolve()
            child = mount / 'child'
            child.mkdir()
            info = {'Internal': False, 'WritableVolume': True, 'VolumeUUID': 'X', 'MountPoint': str(mount)}
            with patch('reproduction.core.platform.system', return_value='Darwin'), \
                 patch('reproduction.core.platform.machine', return_value='arm64'), \
                 patch('pathlib.Path.is_mount', lambda p: p == mount), \
                 patch('reproduction.core.subprocess.run', return_value=SimpleNamespace(returncode=0, stdout=plistlib.dumps(info))) as run:
                self.assertEqual(core.external_volume(child)['uuid'], 'X')
                self.assertEqual(run.call_args.args[0][-1], str(mount))

    def test_unsupported_host_does_not_invoke_diskutil(self):
        with patch('reproduction.core.platform.system', return_value='Linux'), patch('reproduction.core.subprocess.run') as run:
            with self.assertRaisesRegex(core.LabError, 'Apple Silicon'):
                core.external_volume(Path('/path'))
            run.assert_not_called()

    def test_internal_disk_is_rejected(self):
        with patch('reproduction.core.platform.system', return_value='Darwin'), \
             patch('reproduction.core.platform.machine', return_value='arm64'), \
             patch('reproduction.core.subprocess.run', return_value=SimpleNamespace(returncode=0, stdout=plistlib.dumps({
                 'Internal': True, 'WritableVolume': True, 'VolumeUUID': 'X', 'MountPoint': '/'}))):
            with self.assertRaisesRegex(core.LabError, 'external'):
                core.external_volume(Path('/'))


class SourceTests(StorageFixture, unittest.TestCase):
    def fixture(self):
        upstream = self.base / 'upstream'
        upstream.mkdir()
        env = self.storage.environment()
        sources.git(upstream, ['init', '--quiet'], env)
        (upstream / 'file').write_text('original')
        sources.git(upstream, ['add', 'file'], env)
        sources.git(upstream, ['-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'fixture'], env)
        commit = sources.git(upstream, ['rev-parse', 'HEAD'], env)
        selected = {'fixture': {'repository': str(upstream), 'revision': commit, 'access': 'public-git'}}
        selected_patch = patch.object(self.release, 'selected_sources', return_value=selected)
        selected_patch.start()
        self.addCleanup(selected_patch.stop)
        return selected['fixture']

    def test_first_prepare_detached_and_idempotent_repeat(self):
        self.fixture()
        events = []
        sources.prepare_sources(self.storage, self.state, lambda *e: events.append(e))
        path = self.storage.root / 'sources/fixture'
        first = (path / '.git/HEAD').read_text()
        events.clear()
        sources.prepare_sources(self.storage, self.state, lambda *e: events.append(e))
        self.assertNotIn('ref:', first)
        self.assertEqual(first, (path / '.git/HEAD').read_text())
        self.assertFalse(any(event[0] == 'FETCH_SOURCE' for event in events))
        self.assertEqual(sources.verify_sources(self.storage, self.state), 1)

    def test_dirty_checkout_never_reset(self):
        self.fixture()
        sources.prepare_sources(self.storage, self.state, lambda *e: None)
        path = self.storage.root / 'sources/fixture/file'
        path.write_text('user change')
        with self.assertRaisesRegex(core.LabError, 'Dirty'):
            sources.prepare_sources(self.storage, self.state, lambda *e: None)
        self.assertEqual(path.read_text(), 'user change')

    def test_wrong_remote_and_revision_refused(self):
        source = self.fixture()
        sources.prepare_sources(self.storage, self.state, lambda *e: None)
        path = self.storage.root / 'sources/fixture'
        with self.assertRaisesRegex(core.LabError, 'revision'):
            sources.check_source(path, {**source, 'revision': '0'*40}, self.storage.environment())
        with self.assertRaisesRegex(core.LabError, 'remote'):
            sources.check_source(path, {**source, 'repository': '/different'}, self.storage.environment())

    def test_resume_after_init_before_remote(self):
        source = self.fixture()
        path = self.storage.root / 'sources/fixture'
        path.mkdir(parents=True)
        core.atomic_json(path.with_suffix('.json'), {key: source[key] for key in ('repository', 'revision')})
        sources.git(path, ['init', '--quiet'], self.storage.environment())
        sources.prepare_sources(self.storage, self.state, lambda *e: None)
        self.assertEqual(sources.verify_sources(self.storage, self.state), 1)

    def test_collision_preserved(self):
        self.fixture()
        path = self.storage.root / 'sources/fixture'
        path.mkdir(parents=True)
        (path / 'keep').write_text('keep')
        with self.assertRaisesRegex(core.LabError, 'collision'):
            sources.prepare_sources(self.storage, self.state, lambda *e: None)
        self.assertEqual((path / 'keep').read_text(), 'keep')


class FakeDrive:
    def __init__(self, data):
        self.data, self.offsets, self.reads = data, [], 0
        self.info = {'id': 'test-file-identifier', 'parents': ['test-folder-identifier'], 'size': str(len(data)),
                     'sha256Checksum': hashlib.sha256(data).hexdigest(), 'version': '1',
                     'trashed': False, 'capabilities': {'canDownload': True}}
        self.ignore_range = False
        self.change = False

    def metadata(self, _):
        self.reads += 1
        return {**self.info, 'version': '2' if self.change and self.reads > 1 else '1'}

    def content(self, _, offset):
        self.offsets.append(offset)
        response = io.BytesIO(self.data[offset:])
        response.status = 200 if self.ignore_range else 206
        response.headers = {'Content-Range': f'bytes {offset}-{len(self.data)-1}/{len(self.data)}',
                            'Content-Length': str(len(self.data)-offset)}
        return response


class ArtifactTests(StorageFixture, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.data = b'fixture-artifact-payload'
        self.expected = {'bytes': len(self.data), 'sha256': hashlib.sha256(self.data).hexdigest()}
        self.drive = FakeDrive(self.data)

    def download(self):
        return artifacts.download(self.storage, self.drive, self.drive.info['id'],
                                  'test-folder-identifier', self.expected)

    def partial(self, content):
        path = self.storage.path('cache/sha256/' + self.expected['sha256']).with_suffix('.part')
        path.parent.mkdir(parents=True)
        path.write_bytes(content)
        return path

    def test_download_verified_then_reused_without_network_or_rehash(self):
        path = self.download()
        self.assertEqual(path.read_bytes(), self.data)
        with patch.object(self.drive, 'metadata', side_effect=AssertionError), patch('reproduction.artifacts.sha256', side_effect=AssertionError):
            self.assertEqual(self.download(), path)

    def test_resume_uses_exact_remaining_range(self):
        self.partial(self.data[:5])
        self.assertEqual(self.download().read_bytes(), self.data)
        self.assertEqual(self.drive.offsets, [5])

    def test_ignored_range_keeps_partial_unchanged(self):
        path = self.partial(self.data[:5])
        self.drive.ignore_range = True
        with self.assertRaisesRegex(core.LabError, 'ignored resume'):
            self.download()
        self.assertEqual(path.read_bytes(), self.data[:5])

    def test_wrong_folder_and_access_prevent_content_read(self):
        self.drive.info['parents'] = ['different-folder']
        with self.assertRaisesRegex(core.LabError, 'folder'):
            self.download()
        self.drive.info['parents'] = ['test-folder-identifier']
        self.drive.info['capabilities']['canDownload'] = False
        with self.assertRaisesRegex(core.LabError, 'not permitted'):
            self.download()
        self.assertFalse(self.drive.offsets)

    def test_digest_failure_is_not_promoted(self):
        self.partial(b'x' * len(self.data))
        with self.assertRaisesRegex(core.LabError, 'digest differs'):
            self.download()
        self.assertFalse(self.storage.path('cache/sha256/' + self.expected['sha256']).exists())

    def test_metadata_change_is_not_promoted(self):
        self.drive.change = True
        with self.assertRaisesRegex(core.LabError, 'changed during'):
            self.download()

    def test_cache_mutation_is_detected(self):
        path = self.download()
        path.write_bytes(b'x' * len(self.data))
        with self.assertRaisesRegex(core.LabError, 'digest differs'):
            self.download()

    def test_binding_cannot_override_identity_or_embed_credentials(self):
        binding = {'schemaVersion': 1, 'releaseDigest': self.release.key,
                   'folderId': 'test-folder-identifier', 'files': {'dmg': {'fileId': 'test-file-identifier'}}}
        _, folder, expected = artifacts.binding_entry(binding, self.release, 'dmg')
        self.assertEqual(folder, binding['folderId'])
        self.assertEqual(expected, self.release.value['artifacts']['dmg'])
        binding['files']['dmg']['token'] = 'forbidden'
        with self.assertRaisesRegex(core.LabError, 'credentials'):
            artifacts.binding_entry(binding, self.release, 'dmg')

    def test_redirect_and_tokens_not_exposed(self):
        token = 'private-fixture-token'
        with self.assertRaisesRegex(core.LabError, 'credentials were not forwarded'):
            artifacts.NoRedirect().redirect_request(None)
        client = artifacts.Drive(token)
        with patch.object(client._opener, 'open', side_effect=OSError(token)):
            with self.assertRaises(core.LabError) as error:
                client.metadata('test-file-identifier')
        self.assertNotIn(token, str(error.exception))


class BuildTests(StorageFixture, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.patch('reproduction.build.verify_sources', return_value=7)
        self.patch('reproduction.build.check_source')
        self.integration = self.storage.root / 'sources/integration'
        web = self.integration / 'apps/presenter-ui'
        web.mkdir(parents=True)
        core.atomic_json(web / 'package.json', {'engines': {'node': '26.0.0', 'npm': '11.12.1'}})
        core.atomic_json(web / 'package-lock.json', {})
        owner = self.integration / 'scripts/distribution/ui_build.py'
        owner.parent.mkdir(parents=True)
        owner.write_text('# owner recipe fixture\n')
        for name in ('integration', 'vehicle-gateway'):
            self.state['sources'][name] = {key: self.release.sources[name][key] for key in ('repository', 'revision')}
        self.commands = []
        self.patch('reproduction.build.command', side_effect=self.command)

    def command(self, args, env, cwd, timeout=15):
        args = list(map(str, args))
        self.commands.append(args)
        if args[1:] == ['--version']:
            return 'v26.0.0' if args[0] == str(Path(sys.executable).resolve()) else '11.12.1'
        if args[1:] == ['swiftc', '--version']:
            return 'Swift fixture'
        if '--show-sdk-version' in args:
            return '26.0'
        if '--output' in args:
            output = Path(args[args.index('--output') + 1])
            (output / 'native').mkdir(parents=True)
            (output / 'native/Presenter').write_bytes(b'fixture-output')
            (output / 'web').mkdir()
            core.atomic_json(output / 'build-receipt.json', {
                'status': 'BUILT_NOT_RUNTIME_QUALIFIED', 'sourcesUnchanged': True,
                'files': [{'path': 'native/Presenter', 'bytes': 14,
                           'sha256': hashlib.sha256(b'fixture-output').hexdigest()}]})
        return ''

    def invoke(self, dependencies=True):
        return build.presenter(self.storage, self.state, sys.executable, '/usr/bin/true', dependencies, lambda *e: None)

    def test_build_delegates_to_owner_and_reuses_output(self):
        key = self.invoke()
        owner_calls = [args for args in self.commands if '--output' in args]
        self.assertEqual(len(owner_calls), 1)
        self.assertEqual(owner_calls[0][2], str(self.integration / 'scripts/distribution/ui_build.py'))
        self.commands.clear()
        self.assertEqual(self.invoke(dependencies=False), key)
        self.assertFalse(any('--output' in args or 'ci' in args for args in self.commands))

    def test_completed_owner_build_reconciles_without_duplicate(self):
        key = self.invoke()
        self.state['builds'].clear()
        self.commands.clear()
        self.assertEqual(self.invoke(dependencies=False), key)
        self.assertFalse(any('--output' in args or 'ci' in args for args in self.commands))

    def test_dependency_acquisition_requires_explicit_flag(self):
        with self.assertRaisesRegex(core.LabError, 'prepare-dependencies'):
            self.invoke(dependencies=False)
        self.assertFalse(any('ci' in args for args in self.commands))

    def test_changed_outputs_not_reused(self):
        key = self.invoke()
        (self.storage.root / 'builds/presenter' / key / 'native/Presenter').write_bytes(b'corrupt')
        with self.assertRaisesRegex(core.LabError, 'changed'):
            self.invoke()

    def test_corrupt_receipt_cannot_escape_output(self):
        key = self.invoke()
        output = self.storage.root / 'builds/presenter' / key
        receipt = core.read_json(output / 'build-receipt.json')
        receipt['files'][0]['path'] = '../../outside'
        core.atomic_json(output / 'build-receipt.json', receipt)
        with self.assertRaisesRegex(core.LabError, 'path'):
            build.verify_output(output)


class PublicWheelTests(StorageFixture, unittest.TestCase):
    def test_public_wheel_resumes_and_uses_no_auth(self):
        data = b'fixture-wheel'
        row = {'file': 'fixture-1-py3-none-any.whl', 'bytes': len(data),
               'sha256': hashlib.sha256(data).hexdigest(),
               'url': 'https://files.pythonhosted.org/packages/x/fixture-1-py3-none-any.whl'}
        part = self.storage.path('cache/sha256/' + row['sha256']).with_suffix('.part')
        part.parent.mkdir(parents=True)
        part.write_bytes(data[:3])
        response = io.BytesIO(data[3:])
        response.status = 206
        response.headers = {'Content-Range': f'bytes 3-{len(data)-1}/{len(data)}'}
        with patch('reproduction.artifacts.urllib.request.OpenerDirector.open', return_value=response) as opened:
            path = artifacts.public_wheel(self.storage, row)
        request = opened.call_args.args[0]
        self.assertNotIn('Authorization', request.headers)
        self.assertEqual(request.headers['Range'], 'bytes=3-')
        self.assertEqual(path.read_bytes(), data)
        with patch('reproduction.artifacts.urllib.request.build_opener', side_effect=AssertionError):
            self.assertEqual(artifacts.public_wheel(self.storage, row), path)

    def test_public_transport_rejects_other_hosts_and_query_tokens(self):
        row = {'file': 'x.whl', 'bytes': 1, 'sha256': 'a'*64}
        for url in ('http://files.pythonhosted.org/packages/x.whl',
                    'https://evil.invalid/packages/x.whl',
                    'https://files.pythonhosted.org/packages/x.whl?token=secret',
                    'https://user:secret@files.pythonhosted.org/packages/x.whl'):
            with self.assertRaisesRegex(core.LabError, 'Invalid pinned'):
                artifacts.public_wheel(self.storage, {**row, 'url': url})


class CloudBuildTests(StorageFixture, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.patch('reproduction.cloud.verify_sources', return_value=7)
        self.patch('reproduction.cloud.external_volume', return_value=self.volume)
        self.integration = self.storage.root / 'sources/integration'
        owner = self.integration / 'scripts/distribution/cloud_worker.py'
        owner.parent.mkdir(parents=True)
        owner.write_text('# canonical owner fixture')
        (self.integration / 'workspace').mkdir()
        self.wheel_data = b'wheel fixture'
        self.wheel = {'name': 'fixture', 'file': 'fixture-1-py3-none-any.whl', 'bytes': len(self.wheel_data),
                      'sha256': hashlib.sha256(self.wheel_data).hexdigest(),
                      'url': 'https://files.pythonhosted.org/packages/x/fixture-1-py3-none-any.whl'}
        core.atomic_json(self.integration / 'workspace/cloud-worker-wheels.lock.json', {
            'python': '3.12', 'platform': 'macOS-arm64', 'packages': [self.wheel]})
        self.state['sources']['integration'] = {k: self.release.sources['integration'][k] for k in ('repository', 'revision')}
        self.kit = self.base / 'kit'
        self.python_source = self.kit / 'host/python'
        (self.python_source / 'bin').mkdir(parents=True)
        (self.python_source / 'bin/python3.12').write_bytes(b'python fixture')
        (self.python_source / 'bin/python3.12').chmod(0o755)
        row = self.row(self.python_source, 'bin/python3.12')
        core.atomic_json(self.python_source / cloud.BASE_MANIFEST, {
            'versionFamily': '3.12', 'sitePackagesCopied': False,
            'developmentCustomizationHooksCopied': False, 'files': [row]})
        subrow = self.row(self.python_source, cloud.BASE_MANIFEST)
        host_path = self.python_source.parent / 'host.json'
        core.atomic_json(host_path, {'files': [{**r, 'path': 'python/' + r['path']} for r in (row, subrow)]})
        self.release.value['inputs'] = [{'id': 'host-runtime', 'kitPath': 'host/host.json',
            'bytes': host_path.stat().st_size, 'sha256': artifacts.sha256(host_path)}]
        self.commands = []
        self.patch('reproduction.cloud.command', side_effect=self.command)
        self.downloads = self.patch('reproduction.cloud.public_wheel', side_effect=self.download)

    def row(self, root, name):
        path = root / name
        return {'path': name, 'bytes': path.stat().st_size, 'sha256': artifacts.sha256(path),
                'mode': path.stat().st_mode & 0o777}

    def download(self, storage, row, progress):
        path = storage.path('cache/sha256/' + row['sha256'])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(self.wheel_data)
        return path

    def command(self, args, env, cwd, timeout=15):
        self.commands.append(list(map(str, args)))
        if '-c' in args:
            return json.dumps({'python': '3.12.14', 'packaging': '26.3', 'machine': 'arm64'})
        output = args[args.index('--output') + 1]
        output.mkdir()
        (output / 'worker').write_bytes(b'fixture-output')
        base = args[args.index('--base') + 1]
        lock = args[args.index('--lock') + 1]
        core.atomic_json(output / cloud.OUTPUT_MANIFEST, {
            'status': 'ASSEMBLED_NOT_INTEGRATED', 'packageCount': 1,
            'wheelLockSha256': artifacts.sha256(lock),
            'baseManifestSha256': artifacts.sha256(base / cloud.BASE_MANIFEST),
            'operatorCredentialsCopied': False, 'runtimeSelectorsChanged': False,
            'externalDistributionApproved': False, 'files': [self.row(output, 'worker')]})
        return ''

    def invoke(self, dependencies=True):
        return cloud.assemble(self.storage, self.state, self.kit, sys.executable, dependencies, lambda *e: None)

    def test_owner_first_build_and_repeat_without_download_or_assembly(self):
        key = self.invoke()
        self.commands.clear()
        self.downloads.reset_mock()
        self.assertEqual(self.invoke(False), key)
        self.downloads.assert_not_called()
        self.assertFalse(any('--output' in a for a in self.commands))
        self.assertEqual(self.state['builds'][key]['target'], 'cloud-sdk')

    def test_completed_owner_receipt_recovers_missing_outer_state(self):
        key = self.invoke()
        self.state['builds'].clear()
        self.commands.clear()
        self.assertEqual(self.invoke(False), key)
        self.assertFalse(any('--output' in a for a in self.commands))

    def test_no_acquisition_without_explicit_flag(self):
        with self.assertRaisesRegex(core.LabError, 'prepare-dependencies'):
            self.invoke(False)
        self.downloads.assert_not_called()

    def test_wrong_host_manifest_rejected_before_acquisition(self):
        (self.python_source.parent / 'host.json').write_text('{}')
        with self.assertRaisesRegex(core.LabError, 'digest differs'):
            self.invoke()
        self.downloads.assert_not_called()

    def test_kit_extra_packages_never_enter_python_base(self):
        (self.python_source / 'not-selected').write_text('must not copy')
        self.invoke()
        self.assertFalse(any(self.storage.root.glob('inputs/python-base/*/not-selected')))

    def test_extra_output_and_mode_changes_refused(self):
        key = self.invoke()
        output = self.storage.root / 'builds/cloud-sdk' / key
        (output / 'extra').write_text('foreign')
        with self.assertRaisesRegex(core.LabError, 'inventory differs'):
            self.invoke()
        (output / 'extra').unlink()
        (output / 'worker').chmod(0o777)
        with self.assertRaisesRegex(core.LabError, 'mode differs'):
            self.invoke()

    def test_corrupt_base_and_path_escape_rejected(self):
        (self.python_source / 'bin/python3.12').write_bytes(b'corrupt')
        with self.assertRaisesRegex(core.LabError, 'digest differs'):
            self.invoke()
        with self.assertRaisesRegex(core.LabError, 'path'):
            cloud.relative('../escape')

    def test_kit_on_other_volume_is_rejected(self):
        with patch('reproduction.cloud.external_volume', return_value={'uuid': 'OTHER'}):
            with self.assertRaisesRegex(core.LabError, 'selected external'):
                self.invoke()

    def test_declared_venv_entry_point_is_not_dereferenced(self):
        python = self.base / 'venv/bin/python3'
        python.parent.mkdir(parents=True)
        python.symlink_to(sys.executable)
        cloud.assemble(self.storage, self.state, self.kit, python, True, lambda *e: None)
        self.assertTrue(all(args[0] == str(python) for args in self.commands))


class BackendBuildTests(StorageFixture, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.patch('reproduction.containers.verify_sources', return_value=7)
        self.client = self.patch('reproduction.containers.Desktop').return_value
        self.client.version = 'fixture-engine'
        self.client.run.side_effect = self.build_image
        for role, _ in containers.TARGETS.values():
            root = self.storage.root / 'sources' / role
            root.mkdir(parents=True)
            (root / 'Dockerfile').write_text('# owner Dockerfile fixture')
            self.state['sources'][role] = {k: self.release.sources[role][k] for k in ('repository', 'revision')}

    def build_image(self, args, timeout=30):
        self.assertNotIn('run', args)
        self.assertNotIn('--push', args)
        self.assertNotIn('--tag', args)
        self.assertIn('linux/arm64', args)
        Path(args[args.index('--iidfile') + 1]).write_text('sha256:' + 'a'*64)
        return ''

    def invoke(self, target='brake-backend', dependencies=True):
        return containers.assemble(self.storage, self.state, target, sys.executable, dependencies, lambda *e: None)

    def test_each_backend_build_uses_owner_then_reuses_exact_image(self):
        for target in containers.TARGETS:
            key = self.invoke(target)
            self.client.run.reset_mock()
            self.assertEqual(self.invoke(target, False), key)
            self.client.run.assert_not_called()
            self.client.image.assert_called_with('sha256:' + 'a'*64,
                self.state['builds'][key]['inputs']['source']['revision'], target.split('-')[0])

    def test_first_build_requires_explicit_network_preparation(self):
        with self.assertRaisesRegex(core.LabError, 'prepare-dependencies'):
            self.invoke(dependencies=False)
        self.client.run.assert_not_called()

    def test_complete_iid_recovers_without_rebuild(self):
        key = self.invoke()
        self.state['builds'].clear()
        (self.storage.root / 'builds/brake-backend' / key / 'build-receipt.json').unlink()
        self.client.run.reset_mock()
        self.assertEqual(self.invoke(dependencies=False), key)
        self.client.run.assert_not_called()

    def test_changed_image_receipt_rejected(self):
        key = self.invoke()
        (self.storage.root / 'builds/brake-backend' / key / 'image-id').write_text('sha256:' + 'b'*64)
        with self.assertRaisesRegex(core.LabError, 'differs'):
            self.invoke()

    def test_missing_image_not_silently_rebuilt(self):
        self.invoke()
        self.client.run.reset_mock()
        self.client.image.side_effect = core.LabError('Image unavailable')
        with self.assertRaisesRegex(core.LabError, 'unavailable'):
            self.invoke()
        self.client.run.assert_not_called()

    def export_fixture(self):
        self.state['sources']['integration'] = {k: self.release.sources['integration'][k] for k in ('repository', 'revision')}
        owner = self.storage.root / 'sources/integration/scripts/distribution/backend_archive.py'
        owner.parent.mkdir(parents=True)
        owner.write_text('# existing archive owner fixture')
        self.exports = []
        def run(args, timeout=30):
            if args[:2] == ['image', 'save']:
                self.exports.append(args)
                Path(args[args.index('--output') + 1]).write_bytes(b'archive-fixture')
                return ''
            return self.build_image(args, timeout)
        self.client.run.side_effect = run
        def verify(args, env, cwd, timeout=30):
            archive = args[args.index('--archive') + 1]
            expected = core.read_json(args[args.index('--inventory') + 1])['backendImages']
            core.atomic_json(args[args.index('--receipt') + 1], {
                'status': 'OFFLINE_INTEGRITY_VERIFIED_NOT_CLEAN_ENGINE_QUALIFIED',
                'operatorDataIncluded': False, 'externalDistributionApproved': False,
                'archiveBytes': archive.stat().st_size, 'archiveSha256': artifacts.sha256(archive),
                'images': [{'team': r['team'], 'imageId': r['localImageId'], 'source': r['source']} for r in expected]})
            return ''
        return self.patch('reproduction.containers.command', side_effect=verify)

    def export(self):
        return containers.export(self.storage, self.state, sys.executable, True, lambda *e: None, sys.executable)

    def test_export_uses_owner_and_reuses_without_save_or_rehash(self):
        verifier = self.export_fixture()
        key = self.export()
        self.assertEqual(len(self.exports), 1)
        self.assertEqual(verifier.call_count, 1)
        verifier.reset_mock()
        self.exports.clear()
        self.assertEqual(self.export(), key)
        self.assertFalse(self.exports)
        verifier.assert_not_called()

    def test_export_corruption_and_extra_file_refused(self):
        self.export_fixture()
        key = self.export()
        output = self.storage.root / 'builds/backend-export' / key
        (output / 'images.tar').write_bytes(b'x' * len(b'archive-fixture'))
        with self.assertRaisesRegex(core.LabError, 'digest differs'):
            self.export()

    def test_export_recovers_owner_success_without_duplicate_save(self):
        self.export_fixture()
        key = self.export()
        del self.state['builds'][key]
        (self.storage.root / 'builds/backend-export' / key / 'build-receipt.json').unlink()
        self.exports.clear()
        self.assertEqual(self.export(), key)
        self.assertFalse(self.exports)


class DockerStorageTests(StorageFixture, unittest.TestCase):
    def test_internal_or_unconfigured_docker_is_blocked_before_build(self):
        for setting in ({}, {'DataFolder': str(self.base / 'internal')}):
            with patch.object(self.storage, 'environment', return_value={}), \
                 patch('reproduction.containers.command', return_value='unix:///local/docker.sock'), \
                 patch('reproduction.containers.stat.S_ISSOCK', return_value=True), \
                 patch('reproduction.containers.Path.stat', return_value=SimpleNamespace(st_mode=0)), \
                 patch('reproduction.containers.Path.resolve', return_value=Path(sys.executable)), \
                 patch('reproduction.containers.regular', side_effect=lambda p: p), \
                 patch('reproduction.containers.read_json', return_value=setting), \
                 patch('reproduction.containers.external_volume', side_effect=core.LabError('Internal disk')):
                with self.assertRaisesRegex(core.LabError, 'Internal disk' if setting else 'Move Docker disk'):
                    containers.Desktop(self.storage, sys.executable)

    def test_remote_engine_refused(self):
        with patch('reproduction.containers.command', return_value='tcp://remote.invalid:2376'):
            with self.assertRaisesRegex(core.LabError, 'local Docker'):
                containers.Desktop(self.storage, sys.executable)


class CommandTests(unittest.TestCase):
    def test_timeout_stops_owned_command(self):
        with self.assertRaisesRegex(core.LabError, 'timed out'):
            core.run_command([sys.executable, '-B', '-c', 'import time; time.sleep(30)'],
                             env=os.environ.copy(), timeout=0.05)

    def test_stderr_is_not_disclosed_as_exception(self):
        with self.assertRaises(core.LabError) as error:
            build.command([sys.executable, '-c', 'import sys; sys.stderr.write("secret"); sys.exit(1)'],
                          os.environ.copy(), ROOT)
        self.assertNotIn('secret', str(error.exception))


if __name__ == '__main__':
    unittest.main()
