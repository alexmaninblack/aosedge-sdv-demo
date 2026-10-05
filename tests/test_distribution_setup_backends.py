# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Pinned explicit image preparation; no real Docker or runtime mutations."""

from contextlib import nullcontext
import json
import os
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import test_distribution_setup as fixtures
with patch.object(fixtures.sys, 'path', [str(fixtures.fixtures.SCRIPTS), *fixtures.sys.path]):
    import setup_backends as m
    import setup_launch  # Keep the isolated request validator available standalone.

class PreparationTests(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory(); self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        (self.root / m.RECORD).parent.mkdir(parents=True, mode=0o700)
        self.archive = self.root / 'archive.tar'; self.archive.write_bytes(b'fixture')
        self.inputs = Mock(digest='a'*64)
        self.inputs.archive.return_value = self.archive
        self.inputs.candidate.side_effect = lambda team: dict(team=team, imageId=team)
        self.docker = Mock()
        self.docker.engine.return_value = 'engine-1'
        self.docker.available.side_effect = [[], ['brake','tire']]
        self.events = []

    def go(self):
        return m.prepare(SimpleNamespace(root=self.root), 'b'*64, self.inputs, self.docker, self.events.append)

    def test_empty_engine_repeat_reopened_setup_preserve_non_targets(self):
        sentinel = self.root / 'unrelated'; sentinel.write_bytes(b'keep')
        result = self.go()
        self.assertTrue(result['importAttempted'])
        self.assertEqual(2, result['imagesVerified'])
        self.assertFalse(result['runtimeChanged'] or result['cloudAccessed'] or result['demoReady'])
        prior = (self.root / m.RECORD).read_bytes()
        self.docker.available.side_effect = [['brake','tire'], ['brake','tire']]
        self.assertFalse(self.go()['importAttempted'])
        self.assertEqual(prior, (self.root / m.RECORD).read_bytes())
        self.docker.load.assert_called_once()
        self.assertFalse((self.root / m.JOURNAL).exists())
        self.assertEqual(b'keep', sentinel.read_bytes())
        self.assertNotIn(str(self.root), json.dumps(self.events))

    def test_partial_import_then_lost_response_never_reloads(self):
        self.docker.available.side_effect = [[], ['brake']]
        with self.assertRaisesRegex(ValueError, 'IMPORT_UNCONFIRMED'): self.go()
        self.docker.available.side_effect = [['brake']]
        with self.assertRaisesRegex(ValueError, 'IMPORT_UNCONFIRMED'): self.go()
        self.docker.load.assert_called_once()
        self.docker.available.side_effect = [['brake','tire'], ['brake','tire']]
        self.assertFalse(self.go()['importAttempted'])
        self.assertEqual('RECONCILED', json.loads((self.root/m.RECORD).read_text())['attempt'])

    def test_one_existing_image_loads_once(self):
        self.docker.available.side_effect = [['brake'], ['brake','tire']]
        self.assertTrue(self.go()['importAttempted']); self.docker.load.assert_called_once()

    def test_already_present_without_record_is_read_only(self):
        self.docker.available.side_effect = [['brake','tire'], ['brake','tire']]
        self.assertFalse(self.go()['importAttempted'])
        self.assertFalse((self.root/m.RECORD).exists()); self.docker.load.assert_not_called()

    def test_reconciled_predecessor_same_archive_reobserves_without_import(self):
        path = self.root/m.RECORD
        m.atomic_json(path, dict(schemaVersion=1, manifestSha256='c'*64,
            archiveSha256='a'*64, engineId='engine-1', attempt='RECONCILED'))
        self.docker.available.side_effect = [['brake','tire'], ['brake','tire']]
        self.assertFalse(self.go()['importAttempted'])
        self.docker.load.assert_not_called()
        self.assertEqual('b'*64, json.loads(path.read_text())['manifestSha256'])

    def test_predecessor_uncertain_changed_archive_or_engine_stays_blocked(self):
        path = self.root/m.RECORD
        baseline = dict(schemaVersion=1, manifestSha256='c'*64,
            archiveSha256='a'*64, engineId='engine-1', attempt='RECONCILED')
        for change, code in ((dict(attempt='ATTEMPTED'), 'RECORD_INVALID'),
                             (dict(archiveSha256='d'*64), 'RECORD_INVALID'),
                             (dict(engineId='engine-2'), 'ENGINE_CHANGED'),
                             (dict(manifestSha256='invalid'), 'RECORD_INVALID')):
            with self.subTest(change=change):
                prior = dict(baseline, **change)
                m.atomic_json(path, prior)
                with self.assertRaisesRegex(ValueError, code): self.go()
                self.assertEqual(prior, json.loads(path.read_text()))
        self.docker.load.assert_not_called()

    def test_predecessor_missing_image_loads_once_after_reconciled_attempt(self):
        path = self.root/m.RECORD
        m.atomic_json(path, dict(schemaVersion=1, manifestSha256='c'*64,
            archiveSha256='a'*64, engineId='engine-1', attempt='RECONCILED'))
        self.assertTrue(self.go()['importAttempted'])
        self.docker.load.assert_called_once()
        self.assertEqual('b'*64, json.loads(path.read_text())['manifestSha256'])

    def test_corrupt_archive_no_engine_command(self):
        self.inputs.archive.side_effect = ValueError('ARCHIVE_CHANGED')
        with self.assertRaisesRegex(ValueError, 'ARCHIVE_CHANGED'): self.go()
        self.docker.engine.assert_not_called()

    def test_engine_changes_before_dispatch_no_load(self):
        self.docker.engine.side_effect = ['engine-1','engine-2']
        with self.assertRaisesRegex(ValueError, 'ENGINE_CHANGED'): self.go()
        self.docker.load.assert_not_called()

    def test_engine_changes_after_dispatch_retains_attempt(self):
        self.docker.engine.side_effect = ['engine-1','engine-1','engine-2']
        with self.assertRaisesRegex(ValueError, 'ENGINE_CHANGED'): self.go()
        self.assertEqual('ATTEMPTED', json.loads((self.root/m.RECORD).read_text())['attempt'])

    def test_pending_or_linked_attempt_blocks(self):
        pending = self.root / (m.RECORD + '.pending')
        pending.symlink_to(self.root / 'missing')
        with self.assertRaisesRegex(ValueError, 'RECORD_PENDING'): self.go()
        self.docker.load.assert_not_called()

    def test_malformed_or_foreign_record_blocks(self):
        path = self.root/m.RECORD
        path.write_text('{}'); path.chmod(0o600)
        with self.assertRaisesRegex(ValueError, 'RECORD_INVALID'): self.go()
        self.docker.load.assert_not_called()

    def test_intent_write_failure_prevents_load(self):
        with patch.object(m, 'atomic_json', side_effect=OSError('fixture')):
            with self.assertRaises(OSError): self.go()
        self.docker.load.assert_not_called()

    def test_request_has_no_arbitrary_archive_command_or_endpoint(self):
        request = dict(action='prepare-backends', state=str(self.root))
        self.assertEqual(request, fixtures.bridge.request(json.dumps(request).encode()))
        for key in ('archive', 'command', 'endpoint', 'source'):
            with self.assertRaisesRegex(ValueError, 'REQUEST_INVALID'):
                m.request(dict(request, **{key:'untrusted'}))

    def test_changed_selection_and_retained_journal_block(self):
        with patch.object(m.runtime_paths, 'instance', return_value=(self.root, {})), \
             patch.object(m.installed_control, 'selection', return_value={'current':'c'*64}):
            with self.assertRaisesRegex(ValueError, 'LOCAL_PREPARATION_REQUIRED'):
                m.perform(dict(state=str(self.root)), 'b'*64)
        journal = self.root/m.JOURNAL; journal.parent.mkdir(parents=True); journal.write_bytes(b'keep')
        env = Mock(root=self.root); env._writer.return_value = nullcontext()
        with patch.object(m.runtime_paths, 'instance', return_value=(self.root, {})), \
             patch.object(m.installed_control, 'selection', return_value=dict(current='b'*64, storePath=str(self.root))), \
             patch.object(m.runtime_paths, 'installed_session', return_value=nullcontext()), \
             patch.object(m, 'Bundle'), patch.object(m, 'EnvironmentService', return_value=env), \
             patch.object(m, 'Docker') as docker:
            with self.assertRaisesRegex(ValueError, 'RETAINED_RUN'):
                m.perform(dict(state=str(self.root)), 'b'*64)
            docker.assert_not_called()
        self.assertEqual(b'keep', journal.read_bytes())

class DockerTests(unittest.TestCase):
    def setUp(self):
        with patch.object(m.Path, 'is_file', return_value=True): self.docker = m.Docker()

    def test_cli_is_fixed_local_clean_and_bounded(self):
        with patch.dict(os.environ, {'DOCKER_HOST':'tcp://wrong', 'SECRET':'never'}), \
             patch.object(m.subprocess, 'run', return_value=SimpleNamespace(returncode=0, stdout=b'[]')) as run:
            self.docker.read('image','ls')
            command = run.call_args.args[0]
            self.assertEqual([m.DOCKER,'--host',self.docker.endpoint,'image','ls'],command)
            self.assertEqual({'HOME','PATH','LC_ALL'},set(run.call_args.kwargs['env']))
            self.assertEqual(5,run.call_args.kwargs['timeout'])

    def test_raw_errors_are_not_exposed(self):
        with patch.object(m.subprocess, 'run', return_value=SimpleNamespace(returncode=1,stdout=b'private',stderr=b'secret')):
            with self.assertRaisesRegex(ValueError, '^SETUP_BACKENDS_ENGINE_UNAVAILABLE$'):
                self.docker.read('info')

    def test_load_timeout_is_reconciled_not_retried(self):
        with patch.object(m.subprocess, 'run', side_effect=subprocess.TimeoutExpired('private',75)) as run:
            self.docker.load(None)
            run.assert_called_once()
            self.assertEqual(75,run.call_args.kwargs['timeout'])

    def test_remote_context_rejected_before_info(self):
        with patch.object(self.docker,'read', return_value='remote') as read:
            with self.assertRaisesRegex(ValueError,'LOCAL_CONTEXT_REQUIRED'): self.docker.engine()
            read.assert_called_once()

    def test_wrong_platform_rejected(self):
        with patch.object(self.docker,'read', side_effect=['desktop-linux',json.dumps(self.docker.endpoint),json.dumps(dict(id='engine',os='linux',arch='x86_64'))]):
            with self.assertRaisesRegex(ValueError,'PLATFORM_UNSUPPORTED'): self.docker.engine()

    def test_wrong_image_identity_rejected(self):
        row = dict(imageId='sha256:'+'a'*64,team='brake',sourceRevision='b'*40)
        with patch.object(self.docker,'read', side_effect=[row['imageId'],json.dumps(dict(id=row['imageId'],os='linux',arch='amd64',labels={}))]):
            with self.assertRaisesRegex(ValueError,'IMAGE_MISMATCH'): self.docker.available([row])

    def test_untagged_archive_images_require_complete_inventory(self):
        row = dict(imageId='sha256:'+'a'*64, team='brake', sourceRevision='b'*40)
        def read(*args):
            if args[:2] == ('image', 'ls'):
                return row['imageId'] if '--all' in args else ''
            return json.dumps(dict(id=row['imageId'], os='linux', arch='arm64',
                labels={'tech.aosedge.demo.team':row['team'],
                        'org.opencontainers.image.revision':row['sourceRevision']}))
        with patch.object(self.docker, 'read', side_effect=read) as observed:
            self.assertEqual([row['imageId']], self.docker.available([row]))
            self.assertEqual(('image','ls','--all','--quiet','--no-trunc'),
                             observed.call_args_list[0].args)

if __name__ == '__main__': unittest.main()
