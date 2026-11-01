# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
from pathlib import Path
import runpy
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]


class ImagePresetTests(unittest.TestCase):
    def test_absolute_guest_links_are_detected_without_host_resolution(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            folder=root/'etc/systemd/system/sockets.target.wants';folder.mkdir(parents=True)
            link=folder/'sshd.socket';link.symlink_to('/nonexistent-guest-root/usr/lib/systemd/system/sshd.socket')
            self.assertFalse(link.exists());self.assertTrue(link.is_symlink())
            for script in ('vision_ingress_rootfs_build.py','vision_image_preprocess_proof.py'):
                check=runpy.run_path(str(ROOT/'scripts/guest'/script))['preset_links']
                self.assertEqual(check(root,'sshd.socket'),['etc/systemd/system/sockets.target.wants/sshd.socket'])
                self.assertEqual(check(root,'aos-camera-ingress.service'),[])
                alias=root/'etc/systemd/system/sshd.socket';alias.symlink_to(link)
                self.assertEqual(check(root,'sshd.socket'),['etc/systemd/system/sockets.target.wants/sshd.socket'])
                alias.unlink()


if __name__=='__main__':unittest.main()
