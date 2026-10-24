# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Read failure diagnostics retain precise stages, not private error payloads."""
import json
from types import SimpleNamespace
import unittest
import journey_worker as w


class ReadFailureTests(unittest.TestCase):
    def test_fixed_owner_refusal_remains_authoritative(self):
        self.assertEqual(w.read_failure(None,ValueError('SIMULATION_NOT_READY')),
                         ('SIMULATION_NOT_READY',{}))

    def test_unknown_read_failures_expose_only_fixed_stage_and_class(self):
        worker=SimpleNamespace(_observation_stage='LOCAL_GUEST_JSON',request={'kind':'observe'})
        error=json.JSONDecodeError('private message','private stdout',1)
        self.assertEqual(w.read_failure(worker,error),('WORKER_LOCAL_GUEST_JSON_JSON',
            dict(readStage='LOCAL_GUEST_JSON',errorClass='JSON')))
        worker._observation_stage='LOCAL_CONTROLLER'
        self.assertEqual(w.read_failure(worker,KeyError('private key')),('WORKER_LOCAL_CONTROLLER_KEY',
            dict(readStage='LOCAL_CONTROLLER',errorClass='KEY')))
        self.assertNotIn('private',json.dumps(w.read_failure(worker,KeyError('private key'))))

    def test_unselected_stage_or_mutation_does_not_gain_a_read_exception(self):
        for worker in (None,SimpleNamespace(_observation_stage='private',request={'kind':'observe'}),
                       SimpleNamespace(_observation_stage='LOCAL_CONTROLLER',request={'kind':'control'})):
            self.assertEqual(w.read_failure(worker,KeyError('private')),
                             ('WORKER_OBSERVATION_UNAVAILABLE',{}))


if __name__=='__main__':unittest.main()
