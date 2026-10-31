# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Offline observer protocol tests; no target or simulator is started."""
import unittest
from unittest.mock import patch
from vision_compute_worker import LoadObserver


class ObserverProtocolTests(unittest.TestCase):
    def test_full_camera_observer_protocol_and_nonmutating_close(self):
        observer=LoadObserver();value=dict(fresh=True,egoActorId=42)
        observer.phase_start('load',0,2,10)
        with patch('vision_compute_worker.time.monotonic',return_value=5):observer.sample(value)
        observer.phase_end();observer.close();observer.close()
        self.assertEqual([dict(at=5,**value)],observer.samples)
        self.assertNotIn('at',value)


if __name__=='__main__':unittest.main()
