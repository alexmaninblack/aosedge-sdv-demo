# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
import ctypes
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock,patch

import vision_delivery_guest as guest
import vision_recovery_worker as recovery


def entry(name,body):
    fields=[1,0o100644,0,0,1,0,len(body),0,0,0,0,len(name)+1,0]
    raw=b'070701'+''.join('%08x'%v for v in fields).encode()+name.encode()+b'\0'
    raw+=b'\0'*((-len(raw))%4);raw+=body;raw+=b'\0'*((-len(raw))%4)
    return raw


class RecoveryTests(unittest.TestCase):
    def test_atomic_swap_has_no_overwrite_fallback(self):
        swap=Mock(return_value=0)
        with patch.object(recovery.ctypes,'CDLL',return_value=SimpleNamespace(renameatx_np=swap)):
            recovery.swap(Path('/owned/disk'),Path('/owned/replacement'))
        swap.assert_called_once_with(-2,b'/owned/disk',-2,b'/owned/replacement',2)
        swap.return_value=-1
        with patch.object(recovery.ctypes,'CDLL',return_value=SimpleNamespace(renameatx_np=swap)),patch.object(recovery.ctypes,'get_errno',return_value=5),patch.object(recovery.os,'replace') as replace:
            with self.assertRaises(OSError):recovery.swap(Path('/owned/disk'),Path('/owned/replacement'))
            replace.assert_not_called()

    def test_cpio_read_only_helper_selection_and_unsafe_name_denial(self):
        raw=entry('init.d/95-aosupdate',b'non-secret source fixture')+entry('TRAILER!!!',b'')
        values=guest.archive_helpers(raw)
        self.assertEqual(set(values),{'aosupdate'});self.assertEqual(len(values['aosupdate']),64)
        for name in ('../aosupdate','/etc/aosupdate'):
            with self.assertRaises(AssertionError):guest.archive_helpers(entry(name,b'fixture'))
        with self.assertRaises(AssertionError):guest.archive_helpers(b'not cpio'*20)


if __name__=='__main__':unittest.main()
