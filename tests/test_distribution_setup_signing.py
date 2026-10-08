# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Setup code-signing build gate; no real credentials or signing in tests."""

import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import test_distribution_installation as fixtures
with patch.object(sys, 'path', [str(fixtures.SCRIPTS), *sys.path]):
    import setup_signing as signing
    import setup_build as builder

KEY = 'A' * 40
DETAILS = 'Identifier=' + signing.IDENTIFIER + '\nAuthority=Apple Development: Fixture\nTeamIdentifier=ABCDEFGHIJ\n'
REQ = 'designated => identifier "' + signing.IDENTIFIER + '" and anchor apple generic and certificate leaf[subject.OU] = "ABCDEFGHIJ"\n'


class SigningTests(unittest.TestCase):
    def test_build_environment_keeps_selected_scratch_without_ambient_secrets(self):
        with patch.object(builder.tempfile, 'gettempdir', return_value='/Volumes/BUILD/tmp'):
            env = builder.build_environment()
        self.assertEqual(env['TMPDIR'], '/Volumes/BUILD/tmp')
        self.assertEqual(set(env), {'PATH', 'HOME', 'LC_ALL', 'TMPDIR'})

    def test_successor_requires_both_independent_checkpoint_inputs(self):
        with tempfile.TemporaryDirectory() as scratch:
            for kwargs in ({'input_checkpoint': 'fixture'}, {'release_checkpoint': 'fixture'}):
                with patch.object(sys, 'path', [str(fixtures.SCRIPTS), *sys.path]), \
                        patch.object(builder, 'supported_platform'), \
                        patch.object(signing, 'select', return_value='-'), \
                        patch.object(builder, 'Bundle') as bundle:
                    with self.assertRaisesRegex(ValueError, 'CHECKPOINT_PAIR_REQUIRED'):
                        builder.build(Path(scratch)/'kit', Path(scratch)/'new', ad_hoc=True, **kwargs)
                    bundle.assert_not_called()

    def test_build_blocks_before_copy_compile_or_output_creation(self):
        import tempfile
        with tempfile.TemporaryDirectory() as scratch:
            output = Path(scratch) / 'new-output'
            with patch.object(sys, 'path', [str(fixtures.SCRIPTS), *sys.path]), \
                    patch.object(builder, 'supported_platform'), patch.object(builder, 'Bundle') as bundle:
                with self.assertRaisesRegex(ValueError, 'MODE_REQUIRED'):
                    builder.build(Path(scratch) / 'kit', output)
                with patch.object(signing, 'run', return_value='0 valid identities found'):
                    with self.assertRaisesRegex(ValueError, 'UNAVAILABLE'):
                        builder.build(Path(scratch) / 'kit', output, signing_identity=KEY)
                bundle.assert_not_called()
                self.assertFalse(output.exists())

    def test_bundle_identifier_has_one_authority(self):
        self.assertEqual(signing.IDENTIFIER, builder.bundle_info('SDVLabSetup')['CFBundleIdentifier'])

    def test_missing_or_ambiguous_mode_is_not_adhoc(self):
        with patch.object(signing, 'run') as runner:
            for args in ({}, {'identity': KEY, 'ad_hoc': True}, {'ad_hoc': 1}):
                with self.subTest(args=args), self.assertRaisesRegex(ValueError, 'MODE_REQUIRED'):
                    signing.select(**args)
            runner.assert_not_called()

    def test_explicit_adhoc_never_accesses_keychain(self):
        with patch.object(signing, 'run') as runner:
            self.assertEqual('-', signing.select(ad_hoc=True))
            runner.assert_not_called()

    def test_identity_must_be_exact_not_name_or_cli_option(self):
        with patch.object(signing, 'run') as runner:
            for identity in ('-', 'Apple Development', '--deep', 'a' * 39, '', 123):
                with self.subTest(identity=identity), self.assertRaisesRegex(ValueError, 'IDENTITY_INVALID'):
                    signing.select(identity)
            runner.assert_not_called()

    def test_exact_apple_development_identity(self):
        with patch.object(signing, 'run', return_value='  1) ' + KEY + ' "Apple Development: Fixture"\n 1 valid identities found'):
            self.assertEqual(KEY, signing.select(KEY.lower()))

    def test_missing_identity_does_not_fall_back(self):
        for observed in ('0 valid identities found', '1) ' + 'B'*40 + ' "Apple Development: Other"'):
            with patch.object(signing, 'run', return_value=observed), self.assertRaisesRegex(ValueError, 'UNAVAILABLE'):
                signing.select(KEY)

    def test_wrong_type_is_not_silently_used(self):
        for name in ('Developer ID Application: Fixture', 'Self Signed', 'Apple Distribution: Fixture'):
            with patch.object(signing, 'run', return_value='1) ' + KEY + ' "' + name + '"'), self.assertRaisesRegex(ValueError, 'DEVELOPMENT_REQUIRED'):
                signing.select(KEY)

    def test_distribution_requires_its_own_exact_certificate(self):
        for name in ('Apple Development: Fixture', 'Apple Distribution: Fixture', 'Self Signed'):
            with patch.object(signing, 'run', return_value='1) ' + KEY + ' "' + name + '"'):
                with self.assertRaisesRegex(ValueError, 'DEVELOPER_ID_REQUIRED'):
                    signing.select(KEY, distribution=True)
        with patch.object(signing, 'run', return_value='1) ' + KEY + ' "Developer ID Application: Fixture"'):
            self.assertEqual(KEY, signing.select(KEY.lower(), distribution=True))
        with patch.object(signing, 'run') as runner:
            with self.assertRaisesRegex(ValueError, 'DISTRIBUTION_MODE_INVALID'):
                signing.select(ad_hoc=True, distribution=True)
            runner.assert_not_called()

    def test_distribution_missing_identity_stops_before_output(self):
        with tempfile.TemporaryDirectory() as scratch:
            output = Path(scratch) / 'new-output'
            with patch.object(sys, 'path', [str(fixtures.SCRIPTS), *sys.path]), \
                    patch.object(builder, 'supported_platform'), patch.object(builder, 'Bundle') as bundle, \
                    patch.object(signing, 'run', return_value='0 valid identities found'):
                with self.assertRaisesRegex(ValueError, 'UNAVAILABLE'):
                    builder.build(Path(scratch)/'kit', output, developer_id_identity=KEY)
                bundle.assert_not_called()
                self.assertFalse(output.exists())

    def test_hardened_mode_never_accepts_adhoc_or_unhardened_distribution(self):
        for identity, kwargs in (('-', {'hardened': True}),
                                  (KEY, {'distribution': True}),
                                  (KEY, {'hardened': 1})):
            with patch.object(signing, 'run') as runner:
                with self.assertRaisesRegex(ValueError, 'HARDENED_MODE_INVALID'):
                    signing.sign(Path('/fixture/Setup.app'), identity, **kwargs)
                runner.assert_not_called()

    def bootstrap_fixture(self, root):
        app = root / 'Setup.app'
        python = app / 'Contents/Resources/python/bin/python3.12'
        module = app / 'Contents/Resources/python/lib/module.so'
        for path in (python, module):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(bytes.fromhex('cffaedfe') + b'fixture')
        (module.parent / 'data.txt').write_text('not native code')
        return app, python, module

    def test_native_bootstrap_excludes_data_and_rejects_link(self):
        with tempfile.TemporaryDirectory() as scratch:
            app, python, module = self.bootstrap_fixture(Path(scratch).resolve())
            self.assertEqual({python, module}, set(signing.native_bootstrap(app)))
            (module.parent / 'linked.so').symlink_to(module)
            with self.assertRaisesRegex(ValueError, 'BOOTSTRAP_LINK'):
                signing.native_bootstrap(app)

    def test_native_bootstrap_requires_real_python_code_and_private_safe_files(self):
        with tempfile.TemporaryDirectory() as scratch:
            app, python, module = self.bootstrap_fixture(Path(scratch).resolve())
            python.write_text('not a Mach-O executable')
            with self.assertRaisesRegex(ValueError, 'BOOTSTRAP_INVALID'):
                signing.native_bootstrap(app)
            module.chmod(0o666)
            with self.assertRaisesRegex(ValueError, 'INPUT_FILE_UNSAFE'):
                signing.native_bootstrap(app)

    def test_inside_out_hardening_without_permission_exceptions(self):
        for distribution in (False, True):
            prefix = 'Developer ID Application: ' if distribution else 'Apple Development: '
            details = (DETAILS.replace('Apple Development: ', prefix)
                       + 'CodeDirectory flags=0x10000(runtime)\nTimestamp=fixture\n')
            with tempfile.TemporaryDirectory() as scratch:
                app, python, module = self.bootstrap_fixture(Path(scratch).resolve())
                def output(args, code):
                    if '-dvv' in args:
                        return details
                    if '-r-' in args:
                        return REQ
                    return ''
                with patch.object(signing, 'run', side_effect=output) as runner:
                    receipt = signing.sign(app, KEY, hardened=True, distribution=distribution)
                calls = [c.args[0] for c in runner.call_args_list]
                writes = [c for c in calls if '--sign' in c]
                self.assertEqual(3, len(writes))
                self.assertEqual(str(app), writes[-1][-1])
                self.assertEqual({str(python), str(module)}, {c[-1] for c in writes[:-1]})
                for args in writes:
                    self.assertIn('runtime', args)
                    self.assertIn('--timestamp' if distribution else '--timestamp=none', args)
                    self.assertNotIn('--deep', args)
                    self.assertNotIn('--entitlements', args)
                self.assertEqual(distribution, receipt['secureTimestamp'])
                self.assertTrue(receipt['hardenedRuntime'])
                self.assertEqual(3, receipt['signedNativeFiles'])
                self.assertFalse(receipt['consentPersistenceQualified'])
                self.assertEqual('developer-id-application-unnotarized' if distribution
                                 else 'apple-development-local-only', receipt['signing'])

    def test_hardened_inspection_rejects_missing_runtime_team_authority_or_timestamp(self):
        good = DETAILS.replace('Apple Development: ', 'Developer ID Application: ') + 'flags=0x10000(runtime)\nTimestamp=fixture\n'
        for changed in (good.replace('(runtime)', ''), good.replace('ABCDEFGHIJ', 'OTHERTEAM1'),
                        good.replace('Developer ID Application: ', 'Apple Development: '),
                        good.replace('Timestamp=fixture\n', '')):
            with patch.object(signing, 'run', return_value=changed), self.assertRaises(ValueError):
                signing.inspect_hardened('/fixture/app', 'Developer ID Application: ', 'ABCDEFGHIJ', True)

    def test_verified_signed_receipt_and_commands(self):
        with patch.object(signing, 'run', side_effect=['', '', DETAILS, REQ]) as runner:
            receipt = signing.sign(Path('/fixture/Setup.app'), KEY)
            self.assertTrue(receipt['stableSigningIdentity'])
            self.assertFalse(receipt['consentPersistenceQualified'])
            self.assertEqual('ABCDEFGHIJ', receipt['teamIdentifier'])
            self.assertEqual('apple-development-local-only', receipt['signing'])
            args = runner.call_args_list[0].args[0]
            self.assertIn('--timestamp=none', args)
            self.assertNotIn('--deep', args)
            self.assertNotIn('--entitlements', args)
            self.assertNotIn(KEY, str(receipt))

    def test_adhoc_receipt_is_never_stable_or_qualified(self):
        details = 'Identifier=' + signing.IDENTIFIER + '\nSignature=adhoc\nTeamIdentifier=not set'
        with patch.object(signing, 'run', side_effect=['', '', details, '# designated => cdhash H"fixture"']):
            result = signing.sign(Path('/fixture/Setup.app'), '-')
            self.assertFalse(result['stableSigningIdentity'])
            self.assertFalse(result['consentPersistenceQualified'])

    def test_invalid_signature_fields_fail_closed(self):
        for details, req in ((DETAILS.replace(signing.IDENTIFIER, 'wrong'), REQ),
                             (DETAILS.replace('ABCDEFGHIJ', 'not set'), REQ),
                             (DETAILS.replace('Apple Development:', 'Other:'), REQ),
                             (DETAILS, 'designated => cdhash H"fixture"'),
                             (DETAILS, ''), (DETAILS, 'designated => identifier "wrong"')):
            with self.subTest(details=details, req=req), patch.object(signing, 'run', side_effect=['', '', details, req]), self.assertRaises(ValueError):
                signing.sign(Path('/fixture/Setup.app'), KEY)

    def test_failure_never_retries_signing(self):
        with patch.object(signing, 'run', side_effect=ValueError('SETUP_SIGNING_FAILED')) as runner:
            with self.assertRaisesRegex(ValueError, 'SIGNING_FAILED'):
                signing.sign(Path('/fixture/Setup.app'), KEY)
            self.assertEqual(1, runner.call_count)

    def test_subprocess_error_is_redacted(self):
        for effect in (OSError('/private/keychain/SECRET'), signing.subprocess.TimeoutExpired('SECRET', 60)):
            with patch.object(signing.subprocess, 'run', side_effect=effect), self.assertRaisesRegex(ValueError, '^FIXED_FAILURE$'):
                signing.run(['unused'], 'FIXED_FAILURE')
        with patch.object(signing.subprocess, 'run', return_value=SimpleNamespace(returncode=1, stdout='SECRET', stderr='SECRET')), self.assertRaisesRegex(ValueError, '^FIXED_FAILURE$'):
            signing.run(['unused'], 'FIXED_FAILURE')


if __name__ == '__main__':
    unittest.main()
