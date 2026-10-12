#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Prepare or execute the signed native fixture on the dedicated M1 only."""
import argparse
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys

import remote_harness as h
import journey as j

HERE=Path(__file__).resolve().parent


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=('prepare','run'))
    p.add_argument('--config',type=Path,required=True)
    p.add_argument('--journey',type=Path,required=True)
    p.add_argument('--build',type=Path,required=True)
    p.add_argument('--run-id',default='native-ui-pilot-20261012')
    a=p.parse_args();os.umask(0o077)
    t,_=h.configuration(a.config);c=j.configuration(a.journey,t['user'])
    h.require(re.fullmatch(r'native-ui-pilot-\d{8}(?:-[a-z0-9]+)?',a.run_id),'NATIVE_RUN_ID_INVALID')
    root='/Users/'+t['user']+'/SDV-Qualification/'+a.run_id
    python=c['packageRoot']+'/demo-artifacts/aosedge-sdv-demo/host-runtime/python/bin/python3.12'
    if a.action=='prepare':
        build=h.unlinked(a.build.resolve(strict=True));receipt=h.parse((build/'build-receipt.json').read_bytes())
        h.require(receipt['status']=='BUILT_NOT_UI_QUALIFIED' and receipt['artifact']=='NATIVE_QUALIFICATION_PILOT','PILOT_BUILD_INVALID')
        program='import os,pathlib,subprocess; os.umask(0o077); r=pathlib.Path('+repr(root)+'); '+\
            'names=subprocess.run(["/bin/ps","-axo","comm="],check=True,capture_output=True,text=True).stdout.splitlines(); '+\
            'assert not any(n.startswith(str(r)+"/") for n in names),"PILOT_PROCESS_ACTIVE"; '+\
            'r.mkdir(mode=0o700,exist_ok=True); (r/"requests").mkdir(mode=0o700,exist_ok=True); '+\
            'assert not (r/"runner-status.json").exists(),"PREPARATION_ALREADY_DISPATCHED"'
        h.remote(t,shlex.quote(python)+' -I -B -c '+shlex.quote(program),timeout=15)
        shell=shlex.join(h.ssh_args(t)[:-1])
        files=[build/row['app'] for row in receipt['apps']]+[build/'build-receipt.json',HERE/'native_ui_worker.py']
        subprocess.run(['/usr/bin/rsync','-rpt','-e',shell,*map(str,files),t['user']+'@'+t['host']+':'+shlex.quote(root+'/')],check=True,capture_output=True,timeout=40)
        verify='import sys,pathlib; sys.path.insert(0,'+repr(root)+'); import native_ui_worker as n; '+\
            'n.verify(pathlib.Path('+repr(root)+')); print("SIGNED_PILOT_VERIFIED")'
        print(h.remote(t,shlex.quote(python)+' -I -B -c '+shlex.quote(verify),timeout=30).strip())
        command=shlex.join(['/usr/bin/open','-a',root+'/Native UI Runner.app','--args',root])
        print(h.remote(t,command+'\n',timeout=15).strip())
        program='import pathlib,json,time; p=pathlib.Path('+repr(root+'/runner-status.json')+'); end=time.monotonic()+8; '+\
            '\nwhile not p.exists() and time.monotonic()<end: time.sleep(.05)\nassert p.exists(),"RUNNER_NOT_OBSERVED"\nprint(p.read_text())'
        print(h.remote(t,shlex.quote(python)+' -I -B -c '+shlex.quote(program),timeout=12).strip())
    else:
        records=Path('.local/remote-qualification')/('m1-'+a.run_id)
        h.require(not records.exists(),'NATIVE_RECORDS_ALREADY_EXIST')
        guard='import pathlib; r=pathlib.Path('+repr(root)+'); '+\
            'assert not (r/"campaign.intent").exists() and not (r/"pilot-report.json").exists(),"CAMPAIGN_REPLAY_FORBIDDEN"'
        h.remote(t,shlex.quote(python)+' -I -B -c '+shlex.quote(guard),timeout=10)
        command=shlex.join([python,'-I','-B',root+'/native_ui_worker.py',root])
        # The worker retains FAIL and performs normal cleanup before its exit.
        try: raw=h.remote(t,command+'\n',timeout=60)
        except h.Error:
            # Read-only reconciliation, never replay a possibly executed campaign.
            raw=h.remote(t,'/bin/cat '+shlex.quote(root+'/pilot-report.json')+'\n',timeout=10)
        report=json.loads(raw);print(json.dumps(report))
        records.mkdir(mode=0o700)
        shell=shlex.join(h.ssh_args(t)[:-1])
        subprocess.run(['/usr/bin/rsync','-rpt','--include=*.json','--include=*.jsonl','--exclude=*',
            '-e',shell,t['user']+'@'+t['host']+':'+shlex.quote(root+'/'),str(records)+'/'],check=True,capture_output=True,timeout=30)
        return 0 if report.get('outcome')=='PASS' else 1
    return 0


if __name__=='__main__': raise SystemExit(main())
