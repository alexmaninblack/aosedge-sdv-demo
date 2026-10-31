# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
from pathlib import Path
import stat
import tempfile
import unittest

import vision_vm_guest as g


class GuestFixtureTests(unittest.TestCase):
    def test_elf_loader_and_library_modes_are_preserved(self):
        with tempfile.TemporaryDirectory() as root:
            root=Path(root)
            for mode in (0o755,0o644,0o555):
                source=root/('source-'+str(mode));target=root/('target-'+str(mode))
                source.write_bytes(b'fixture ELF bytes');source.chmod(mode)
                g.copy_dependency(source,target)
                self.assertEqual(source.read_bytes(),target.read_bytes())
                self.assertEqual(mode,stat.S_IMODE(target.stat().st_mode))


if __name__=='__main__':unittest.main()
