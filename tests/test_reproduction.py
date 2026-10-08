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
from reproduction import artifacts, build, cli, core, sources


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
