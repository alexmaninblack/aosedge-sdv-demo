#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""One visible M1 release/views/moving/lifecycle campaign; no agent step scheduling."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from types import SimpleNamespace

import native_controls_campaign as common
import journey as j
import remote_harness as h
import ui_pilot

PHASES=('preflight','vm-access','continuous-ui','cleanup')


def execute(plan,transport,config,root):
    owner=common.Operations(plan,transport,config,root)
    stages=[];started=time.monotonic();outcome='PASS';failure=None
    def stage(name,action):
        begin=time.monotonic()
        h.atomic(root/(name+'.intent.json'),dict(startedAt=h.utc(),stage=name))
        print(json.dumps(dict(stage=name,state='STARTED')),flush=True)
        try:
            result=action()
            h.require(set(result)=={'outcome','code','facts'} and result['outcome'] in ('PASS','FAIL','BLOCKED','UNCERTAIN'),
                      'CONTINUOUS_STAGE_RESPONSE_INVALID')
        except KeyboardInterrupt:result=dict(outcome='UNCERTAIN',code='CAMPAIGN_INTERRUPTED',facts={})
        except Exception as error:
            result=dict(outcome='FAIL' if name=='cleanup' else 'BLOCKED' if name=='preflight' else 'UNCERTAIN',
                        code=common.code(error),facts={})
        value=dict(stage=name,seconds=round(time.monotonic()-begin,3),**result)
        stages.append(value);h.atomic(root/(name+'.result.json'),value)
        print(json.dumps({k:value[k] for k in ('stage','outcome','seconds','code')}),flush=True)
        return value
    def ui():
        args=SimpleNamespace(scenario='continuous-campaign',display='m1',test=plan['test'],
            cards_from_release_records=None,continue_from=None,node=None,
            config=Path(plan['config']),journey=Path(plan['journey']),records=root/'ui',
            workspace=Path(plan['workspace']),dmg=Path(plan['dmg']),remote_dmg=plan['remoteDmg'],
            media_records=Path(plan['mediaRecords']),native_build=Path(plan['nativeBuild']),
            native_run_id=plan['nativeRunId'],native_versions=plan['versions'])
        status=ui_pilot.run(args,transport,config)
        owner.ui_report=h.parse((args.records/'pilot-report.json').read_bytes())
        if status!=0:
            reason=h.parse((args.records/'failure.json').read_bytes()).get('code') if (args.records/'failure.json').exists() else 'UI_SCENARIO_FAILED'
            return dict(outcome='FAIL',code='CONTINUOUS_CAMPAIGN_NOT_QUALIFIED',facts=dict(reason=reason,
                browserStarted=(args.records/'browser-report.json').exists(),ownersClosed=owner.ui_report.get('ownersClosed')))
        browser=h.parse((args.records/'browser-report.json').read_bytes())
        required={'vdp-v1','vdp-v2','vdp-v3','brake-v1','brake-v2','brake-v3','tire-v1',
            'installed-details','brake-independent-reset','tire-independent-reset',
            'brake-moving-sota','tire-moving-sota','continuous-restart-preserved','confirmed-stop'}
        passed={r['stage'] for r in browser['stages'] if r['outcome']=='PASS'}
        ok=status==0 and owner.ui_report.get('continuousCampaign')=='PASS' and required<=passed
        return dict(outcome='PASS' if ok else 'FAIL',code='CONTINUOUS_CAMPAIGN_PASSED' if ok else 'CONTINUOUS_CAMPAIGN_NOT_QUALIFIED',
            facts=dict(requiredStagesPassed=required<=passed,browserStages=len(browser['stages']),
                       nativeRunnerClosed=owner.ui_report.get('nativeRunnerClosed'),test=plan['test']))
    try:
        for name,action in [('preflight',owner.preflight),('vm-access',owner.prepare),('continuous-ui',ui)]:
            result=stage(name,action)
            if result['outcome']!='PASS':outcome=result['outcome'];failure=result['code'];break
    finally:
        closed=stage('cleanup',owner.cleanup)
        if closed['outcome']!='PASS':outcome='FAIL';failure=closed['code']
        by_name={r['stage']:r for r in stages}
        report=dict(scenario='continuous-campaign',outcome=outcome,code=failure or 'CONTINUOUS_CAMPAIGN_PASSED',
            seconds=round(time.monotonic()-started,3),candidate=config['manifestSha256'],test=plan['test'],
            continuousCampaign='PASS' if outcome=='PASS' else 'NOT_QUALIFIED',fullE2E='NOT_COMPLETE',
            cleanupConfirmed=closed['outcome']=='PASS',agentStepScheduling=False,
            testPolicy='PRESERVE',newReleasePublication='SERIAL_UI_ONLY',
            stages=[by_name.get(p,dict(stage=p,outcome='NOT_RUN',seconds=None)) for p in PHASES])
        h.atomic(root/'campaign-report.json',report)
        print(json.dumps(report),flush=True)
    return 0 if outcome=='PASS' else 2 if outcome=='BLOCKED' else 1


def main():
    os.umask(0o077)
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--plan',type=Path,required=True)
    parser.add_argument('--display-assertion-helper',type=Path,required=True)
    args=parser.parse_args()
    plan=common.configuration(args.plan,scenario='continuous-campaign')
    h.require(plan['mode']=='retained' and plan['test'] is not None,'RETAINED_CONTINUOUS_TEST_REQUIRED')
    transport,_=h.configuration(Path(plan['config']))
    config=j.configuration(Path(plan['journey']),transport['user'])
    root=Path(plan['records']);helper=h.unlinked(args.display_assertion_helper)
    # Explicit existing qualification helper only, never a command from the plan.
    h.require(helper.name=='native_live_awake.py' and '/.local/presenter-human-friendly/' in str(helper),
              'OWNED_DISPLAY_HELPER_REQUIRED')
    suffix=plan['nativeRunId'].split('-')[-1]
    h.require(suffix.startswith('continuous'),'CONTINUOUS_RUN_ID_REQUIRED')
    source=hashlib.sha256(Path(__file__).read_bytes()+common.source_pin().encode()).hexdigest()
    pin=hashlib.sha256(json.dumps(dict(plan=plan,source=source,connection=j.identity(config,transport)),sort_keys=True).encode()).hexdigest()
    awake=False
    with h.Journal(root,pin):
        h.atomic(root/'campaign.intent.json',dict(startedAt=h.utc(),scenario=plan['scenario'],candidate=config['manifestSha256'],
            test=plan['test'],sourceSha256=source,planSha256=h.digest(args.plan)))
        try:
            subprocess.run([sys.executable,'-B',str(helper),'start',suffix],check=True,timeout=20)
            awake=True
            return execute(plan,transport,config,root)
        finally:
            if awake:subprocess.run([sys.executable,'-B',str(helper),'close',suffix],check=True,timeout=20)


if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as error:
        print(json.dumps(dict(outcome='BLOCKED',code=common.code(error))),flush=True)
        raise SystemExit(2)
