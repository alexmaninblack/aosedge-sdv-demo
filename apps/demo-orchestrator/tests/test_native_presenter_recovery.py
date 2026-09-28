# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Opt-in native WebKit regression; synthetic pages only, no demo state."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


@unittest.skipUnless(sys.platform == 'darwin' and os.environ.get('RUN_NATIVE_PRESENTER_TESTS') == '1',
                     'requires an explicitly authorized macOS WebKit/socket session')
class NativePresenterRecoveryTests(unittest.TestCase):
    def test_delayed_server_failed_refresh_and_protected_client_guards(self):
        probe = Path(__file__).parent / 'native/presenter_recovery_probe.py'
        with tempfile.TemporaryDirectory(prefix='presenter-recovery-test-') as folder:
            run = subprocess.run([sys.executable, '-B', str(probe), folder],
                                 capture_output=True, text=True, timeout=150)
            self.assertEqual(0, run.returncode, run.stdout[-4000:] + run.stderr[-4000:])
            result = json.loads((Path(folder) / 'candidate-result.json').read_text())
            self.assertEqual('PASS', result['result'])
            self.assertEqual(8, len(result['checks']))
            self.assertTrue(all(result['checks'].values()))


if __name__ == '__main__':
    unittest.main()
