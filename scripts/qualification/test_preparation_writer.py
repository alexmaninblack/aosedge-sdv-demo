# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
import contextlib
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch
from journey_worker import preparation_writer, visible_presenter_projection


class PreparationWriter(unittest.TestCase):
    def context(self, error=None, events=None):
        @contextlib.contextmanager
        def owner():
            if error: raise ValueError(error)
            if events is not None: events.append('acquired')
            try: yield
            finally:
                if events is not None: events.append('released')
        return owner()

    def test_busy_acquisition_waits_then_executes_body_once(self):
        events=[]
        environment=SimpleNamespace(_writer=Mock(side_effect=[self.context('CURRENT_RUN_BUSY'),self.context(events=events)]))
        with patch('journey_worker.time.sleep') as sleep:
            with preparation_writer(environment):events.append('action')
        self.assertEqual(events,['acquired','action','released'])
        self.assertEqual(environment._writer.call_count,2);sleep.assert_called_once_with(.1)

    def test_body_failure_is_never_replayed_even_when_busy(self):
        events=[];environment=SimpleNamespace(_writer=Mock(return_value=self.context(events=events)))
        with patch('journey_worker.time.sleep') as sleep:
            with self.assertRaisesRegex(ValueError,'CURRENT_RUN_BUSY'):
                with preparation_writer(environment):raise ValueError('CURRENT_RUN_BUSY')
        environment._writer.assert_called_once();sleep.assert_not_called()
        self.assertEqual(events,['acquired','released'])

    def test_acquisition_timeout_preserves_original_refusal(self):
        environment=SimpleNamespace(_writer=Mock(return_value=self.context('CURRENT_RUN_BUSY')))
        with patch('journey_worker.time.monotonic',side_effect=[0,6]),patch('journey_worker.time.sleep') as sleep:
            with self.assertRaisesRegex(ValueError,'CURRENT_RUN_BUSY'):
                with preparation_writer(environment):self.fail('action must not begin')
        environment._writer.assert_called_once();sleep.assert_not_called()

    def test_invalid_lock_never_waits_or_starts_action(self):
        environment=SimpleNamespace(_writer=Mock(return_value=self.context('JOURNAL_LOCK_INVALID')))
        with patch('journey_worker.time.sleep') as sleep:
            with self.assertRaisesRegex(ValueError,'JOURNAL_LOCK_INVALID'):
                with preparation_writer(environment):self.fail('action must not begin')
        environment._writer.assert_called_once();sleep.assert_not_called()


class VisiblePresenter(unittest.TestCase):
    def value(self):
        return dict(hostPid=42, profile='builtin-v1', display=dict(desktopState='UNLOCKED'),
            zOrder=dict(state='VERIFIED'), surfaces={name:dict(pid=42, actual=[0,0,100,100],
                expected=[0,0,100,100]) for name in ('header','browser','backdrop')})

    def test_native_surfaces_pass_without_not_yet_started_simulator(self):
        self.assertTrue(visible_presenter_projection(self.value()))

    def test_server_or_incomplete_surface_is_not_visible_acceptance(self):
        self.assertFalse(visible_presenter_projection(dict(serverReady=True)))
        value=self.value();del value['surfaces']['browser']
        self.assertFalse(visible_presenter_projection(value))

    def test_wrong_owner_geometry_order_or_locked_screen_refused(self):
        for field in ('pid','geometry','order','desktop'):
            value=self.value()
            if field=='pid':value['surfaces']['browser']['pid']=43
            if field=='geometry':value['surfaces']['browser']['actual'][0]=10
            if field=='order':value['zOrder']['state']='UNAVAILABLE'
            if field=='desktop':value['display']['desktopState']='LOCKED'
            self.assertFalse(visible_presenter_projection(value), field)


if __name__=='__main__':unittest.main()
