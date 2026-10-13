# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
import tempfile
import unittest
from pathlib import Path
from native_ui_build import control_prefix


class NativeBuildGuards(unittest.TestCase):
    def test_fixture_uses_exact_control_prefix_without_production_launch(self):
        with tempfile.TemporaryDirectory() as root:
            p=Path(root)/'source.swift'
            p.write_text('production-control\nfinal class TelemetryView: NSView {\nproduction-launch')
            self.assertEqual(control_prefix(p),'production-control\n')
            for text in ('missing', 'final class TelemetryView: NSView {\nfinal class TelemetryView: NSView {'):
                p.write_text(text)
                with self.assertRaisesRegex(ValueError,'CONTROL_SOURCE_BOUNDARY_INVALID'): control_prefix(p)


if __name__=='__main__': unittest.main()
