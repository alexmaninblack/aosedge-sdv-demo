# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Capacity protocol/deadlines with tiny disposable subprocesses, no Docker."""
import json
import os
from pathlib import Path
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from reproduction import space_probe as probe
from reproduction.core import LabError


class CapacityProbeTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root=Path(temporary.name).resolve()
        self.worker=self.root/'worker.py'
        self.args=SimpleNamespace(storage=self.root/'uncreated', manifest=None,
            profile='operator', target='all', build_plan=None, cache_from=None, docker=None)

    def run_probe(self, body, deadline=2):
        self.worker.write_text('import json,sys,time\n'+body)
        return probe.probe(self.args, lambda event, detail:self.events.append((event,detail)),
                           deadline=deadline, worker=self.worker)

    def test_complete_checked_and_blocked_results_preserve_verdict(self):
        for fits,complete in ((True,True),(False,True),(True,False)):
            self.events=[]
            value=dict(status='SPACE_REPORT',fitsCheckedPools=fits,storagePreflightComplete=complete)
            result=self.run_probe("print(json.dumps({'event':'SPACE_STAGE','detail':'docker'}),flush=True)\n"
                +"print(json.dumps({'result':"+repr(value)+"}),flush=True)\n")
            self.assertEqual(result['fitsCheckedPools'],fits)
            self.assertEqual(result['storagePreflightComplete'],complete)
            self.assertEqual(self.events,[('SPACE_STAGE','docker')])
            self.assertFalse(self.args.storage.exists())

    def test_timeout_reports_last_stage_and_stops_reader(self):
        self.events=[]; pid=self.root/'reader.pid'
        started=time.monotonic()
        with self.assertRaisesRegex(LabError,'deadline exceeded at inventory-sources'):
            self.run_probe("import os\nfrom pathlib import Path\nPath("+repr(str(pid))+").write_text(str(os.getpid()))\n"
                +"print(json.dumps({'event':'SPACE_STAGE','detail':'inventory-sources'}),flush=True)\ntime.sleep(30)\n", .3)
        self.assertLess(time.monotonic()-started,3)
        with self.assertRaises(ProcessLookupError):os.kill(int(pid.read_text()),0)
        self.assertFalse(self.args.storage.exists())

    def test_success_payload_without_successful_exit_is_not_pass(self):
        self.events=[]
        value=dict(status='SPACE_REPORT',fitsCheckedPools=True,storagePreflightComplete=True)
        with self.assertRaisesRegex(LabError,'did not complete'):
            self.run_probe("print(json.dumps({'result':"+repr(value)+"}),flush=True)\nsys.exit(1)\n")

    def test_partial_or_malformed_output_and_missing_result_fail_closed(self):
        for body in ("print('not json')\n", "sys.stdout.write('{')\n", "pass\n",
                     "print(json.dumps({'event':'SPACE_STAGE','detail':'foreign'}))\n",
                     "print(json.dumps({'result':{'status':'SPACE_REPORT','fitsCheckedPools':1}}))\n"):
            self.events=[]
            with self.subTest(body=body), self.assertRaises(LabError):self.run_probe(body)

    def test_worker_failure_is_not_a_capacity_result(self):
        self.events=[]
        with self.assertRaisesRegex(LabError,'fixed failure'):
            self.run_probe("print(json.dumps({'error':'fixed failure'}),flush=True)\nsys.exit(1)\n")

    def test_payload_followed_by_hang_cannot_pass(self):
        self.events=[]
        value=dict(status='SPACE_REPORT',fitsCheckedPools=True,storagePreflightComplete=True)
        with self.assertRaisesRegex(LabError,'deadline exceeded'):
            self.run_probe("print(json.dumps({'result':"+repr(value)+"}),flush=True)\ntime.sleep(30)\n", .3)

    def test_exited_reader_with_child_holding_pipe_is_bounded_and_cleaned(self):
        import subprocess
        self.events=[]; child_pid=self.root/'child.pid'
        body="import subprocess\nfrom pathlib import Path\n"
        body+="child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)'])\n"
        body+="Path("+repr(str(child_pid))+").write_text(str(child.pid))\n"
        body+="print(json.dumps({'event':'SPACE_STAGE','detail':'docker'}),flush=True)\n"
        with self.assertRaisesRegex(LabError,'deadline exceeded at docker'):
            self.run_probe(body,.4)
        status=subprocess.run(['/bin/ps','-p',child_pid.read_text(),'-o','stat='],capture_output=True,text=True)
        self.assertTrue(status.returncode != 0 or status.stdout.strip().startswith('Z'))

    def test_output_limit_fails_without_a_capacity_verdict(self):
        self.events=[]
        with self.assertRaisesRegex(LabError,'output exceeded'):
            self.run_probe("print('x'*"+str(probe.LIMIT+1)+",flush=True)\n")

    def test_request_rejects_unknown_fields_before_storage_access(self):
        with self.assertRaisesRegex(LabError,'Invalid capacity request'):
            probe.inspect_request({'unexpected':True},lambda *args:None)
