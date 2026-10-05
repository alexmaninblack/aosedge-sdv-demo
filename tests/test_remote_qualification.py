# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import subprocess
import sys

SOURCE = Path(__file__).resolve().parents[1]/'scripts/qualification/remote_harness.py'
SPEC = importlib.util.spec_from_file_location('remote_harness', SOURCE)
h = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(h)


class HarnessTests(unittest.TestCase):
    def test_probe_rejects_duplicates_and_unknown_fields(self):
        for raw in ('arch\tarm64\narch\tarm64\n', 'secret\ttoken\n'):
            with self.assertRaises(h.Error):
                h.parse_probe(raw)

    def test_probe_rejects_missing_or_non_numeric_fields(self):
        with self.assertRaises(h.Error):
            h.parse_probe('arch\tarm64\n')
        raw = ''.join(k+'\t'+('x' if k in h.NUMERIC else 'arm64')+'\n'
                      for k in h.FIELDS)
        with self.assertRaises(h.Error):
            h.parse_probe(raw)

    def test_ssh_is_pinned_and_has_no_agent_or_forwarding(self):
        args = h.ssh_args(dict(source='192.168.247.1', key='/key', knownHosts='/hosts',
                               user='tester', host='192.168.247.2'))
        for value in ('StrictHostKeyChecking=yes', 'IdentityAgent=none',
                      'ForwardAgent=no', 'ClearAllForwardings=yes', 'BatchMode=yes'):
            self.assertIn(value, args)
        self.assertIn('/dev/null', args)

    def test_record_preserves_failure_and_unfinished_intent(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp).resolve()/'records'
            with h.Journal(p, 'a'*64) as journal:
                first = journal.begin('preflight')
                journal.finish(first, 'FAIL', 'HOST_MISMATCH')
                second = journal.begin('stage-kit')
            rows = h.read_attempts(p)
            self.assertEqual([r['outcome'] for r in rows], ['FAIL', 'UNCERTAIN'])
            self.assertTrue(h.stage_attempted(rows))
            self.assertIsNone(second['finishedAt'])

    def test_record_single_writer(self):
        with tempfile.TemporaryDirectory() as tmp:
            with h.Journal(Path(tmp).resolve()/'records', 'b'*64):
                with self.assertRaises(h.Error):
                    with h.Journal(Path(tmp).resolve()/'records', 'b'*64):
                        pass

    def test_record_rejects_candidate_rebinding_and_links(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()/'records'
            with h.Journal(root, 'a'*64):
                pass
            with self.assertRaises(h.Error):
                with h.Journal(root, 'b'*64):
                    pass
            alias = Path(tmp).resolve()/'alias'
            alias.symlink_to(root)
            with self.assertRaises(h.InstallError):
                with h.Journal(alias, 'a'*64):
                    pass

    def test_space_guard_includes_two_copies_and_reserve(self):
        self.assertEqual(h.required_bytes(7, 3), 90*2**30+17)

    def test_verify_script_checks_inventory_modes_hash_and_ownership(self):
        rows = {'kit/a b': h.Row(5, 'a'*64, 0o444)}
        script = h.verification_script('/Users/tester/SDV-Qualification/run-1', 'mark', rows)
        for check in ('shasum', '%z:%Lp', '-type l', '-user', '-type f', 'mark'):
            self.assertIn(check, script)
        self.assertIn("'kit/a b'", script)
        self.assertNotIn('rm ', script)

    def test_errors_do_not_echo_arbitrary_output(self):
        with self.assertRaisesRegex(h.Error, '^REMOTE_COMMAND_FAILED$'):
            h.run(['/bin/sh', '-c', 'echo secret >&2; exit 2'], timeout=2)

    def test_subprocess_timeout_is_bounded(self):
        with self.assertRaisesRegex(h.Error, '^COMMAND_TIMEOUT$'):
            h.run(['/bin/sleep', '2'], timeout=0.01)

    def test_status_does_not_create_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp).resolve()/'not-created'
            self.assertEqual(h.read_attempts(path), [])
            self.assertFalse(path.exists())

    def test_connection_failure_has_specific_sanitized_code(self):
        completed = subprocess.CompletedProcess(['ssh'], 255, '', 'Operation timed out: sensitive-detail')
        with patch.object(h.subprocess, 'run', return_value=completed):
            with self.assertRaisesRegex(h.Error, '^REMOTE_UNREACHABLE$'):
                h.run(['ssh'])

    def test_status_does_not_call_interrupted_transfer_pass(self):
        config = dict(runId='test', manifestSha256='a'*64)
        rows = [dict(attempt=1, command='stage-kit', outcome='UNCERTAIN')]
        result = h.summary(config, rows)
        self.assertEqual(result['unresolvedAttempts'], [1])
        self.assertEqual(result['nextStep'], 'reconcile_stage_before_any_retry')
        rows.append(dict(attempt=2, command='reconcile-stage', outcome='PASS'))
        result = h.summary(config, rows)
        self.assertEqual(result['unresolvedAttempts'], [])
        self.assertEqual(rows[0]['outcome'], 'UNCERTAIN')
        self.assertEqual(result['formalQualification'], 'NOT_RUN')

    def test_staged_status_does_not_infer_native_installation_state(self):
        config = dict(runId='test', manifestSha256='a'*64)
        rows = [dict(attempt=1, command='stage-kit', outcome='PASS')]
        result = h.summary(config, rows)
        self.assertEqual(result['nextStep'], 'consult_native_qualification_receipt')
        self.assertEqual(result['formalQualification'], 'NOT_RUN')

    @unittest.skipUnless(sys.platform == 'darwin', 'target uses macOS stat')
    def test_destination_verifier_detects_corruption_mode_extra_and_link(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            (root/'.candidate').write_text('mark')
            payload = root/'file'
            payload.write_bytes(b'hello')
            payload.chmod(0o444)
            rows = {'file': h.Row(5, h.hashlib.sha256(b'hello').hexdigest(), 0o444)}
            script = h.verification_script(str(root), 'mark', rows)
            self.assertEqual(h.run(['/bin/sh'], data=script).strip(), 'VERIFIED')
            payload.chmod(0o644)
            with self.assertRaises(h.Error):
                h.run(['/bin/sh'], data=script)
            payload.write_bytes(b'wrong')
            payload.chmod(0o444)
            with self.assertRaises(h.Error):
                h.run(['/bin/sh'], data=script)
            payload.chmod(0o644)
            payload.write_bytes(b'hello')
            payload.chmod(0o444)
            extra = root/'extra'
            extra.write_text('unlisted')
            with self.assertRaises(h.Error):
                h.run(['/bin/sh'], data=script)
            extra.unlink()
            extra.symlink_to(payload)
            with self.assertRaises(h.Error):
                h.run(['/bin/sh'], data=script)


if __name__ == '__main__':
    unittest.main()
