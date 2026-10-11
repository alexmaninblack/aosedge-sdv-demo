#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Fresh recovery experiments after a completed retained-Test UI release chain."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

import campaign
import journey as j
import remote_harness as h
from journey_plan import plan

HERE = Path(__file__).resolve().parent


def release_context(pilot, browser, events, candidate, test):
    h.require(pilot.get('outcome') == browser.get('outcome') == 'PASS'
              and pilot.get('scenario') == browser.get('scenario') == 'release-continuation'
              and pilot.get('candidate') == candidate and pilot.get('test') == test
              and pilot.get('ownersClosed') is True, 'COMPLETED_UI_CHAIN_REQUIRED')
    passed = {row['stage'] for row in browser.get('stages', []) if row.get('outcome') == 'PASS'}
    h.require({'vdp-v3', 'brake-v3', 'tire-v1', 'confirmed-stop'} <= passed,
              'COMPLETED_RELEASE_STAGES_REQUIRED')
    intents = {row['requestId']: row for row in events if row.get('state') == 'DISPATCH_INTENT'}
    context = dict(runId=test)
    for key, action, team, profile in (('vdp-v3-prepare', 'prepare', None, 'v3'),
            ('brake-v3-prepare', 'service-prepare', 'brake', 'v3'),
            ('tire-v1-prepare', 'service-prepare', 'tire', 'v1')):
        found = []
        for row in events:
            intent = intents.get(row.get('requestId'), {})
            if (row.get('productState') == 'COMPLETED' and intent.get('action') == action
                    and intent.get('team') == team and intent.get('profile') == profile):
                found.append(row.get('version'))
        h.require(len(found) == 1 and isinstance(found[0], str)
                  and re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+', found[0]), 'RELEASE_RECEIPT_REQUIRED')
        context[key] = dict(version=found[0])
    return context


def continued_context(pilot,browser,events,installed,installed_browser,candidate,test):
    from ui_pilot import settled_release_binding
    context = settled_release_binding(pilot,browser,events,candidate,test)
    h.require(installed.get('outcome') == installed_browser.get('outcome') == 'PASS'
              and installed.get('scenario') == installed_browser.get('scenario') == 'installed'
              and installed.get('candidate') == candidate and installed.get('test') == test
              and installed.get('ownersClosed') is True, 'COMPLETED_INSTALLED_CHECK_REQUIRED')
    passed = {r['stage'] for r in installed_browser.get('stages',[]) if r.get('outcome') == 'PASS'}
    h.require({'installed-details','brake-independent-reset','tire-independent-reset','confirmed-stop'} <= passed,
              'COMPLETED_INSTALLED_STAGES_REQUIRED')
    return dict(context,runId=test)


def recovery_plan(config):
    steps = [dict(id='recovery-presenter',kind='presenter-start',timeout=90)]
    steps += [dict(id='recovery-'+label,kind='presenter',args=dict(action=action),timeout=360)
              for label, action in (('controller','start-demo'), ('simulation','start-simulation'),
                                    ('connection','connect-test'))]
    steps.append(dict(id='recovery-vdp',kind='observe',args=dict(query='component'),timeout=180,
        until=dict(test='ready-vdp',actual='$sample',version='$vdp-v3-prepare.version')))
    for team in ('brake','tire'):
        key = 'brake-v3' if team == 'brake' else 'tire-v1'
        steps.append(dict(id='recovery-'+team+'-inputs',kind='observe',args=dict(query='backend',team=team),
            timeout=180,until=dict(test='receiving-inputs',actual='$sample',version='$'+key+'-prepare.version')))
    full = plan(config)
    return steps + [next(s for s in full if s['id'] == 'return-to-road')] + full[
        next(i for i,s in enumerate(full) if s['id'] == 'offline-off'):]


def main():
    os.umask(0o077)
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config',type=Path,required=True)
    p.add_argument('--journey',type=Path,required=True)
    p.add_argument('--ui-records',type=Path,required=True)
    p.add_argument('--installed-records',type=Path)
    p.add_argument('--records',type=Path,required=True)
    p.add_argument('--media-records',type=Path,required=True)
    p.add_argument('--test',required=True)
    p.add_argument('--dmg',type=Path,required=True)
    p.add_argument('--remote-dmg',required=True)
    p.add_argument('--workspace',type=Path,required=True)
    args = p.parse_args()
    transport,_ = h.configuration(args.config)
    config = j.configuration(args.journey,transport['user'])
    root = h.unlinked(args.ui_records)
    records = h.unlinked(args.records)
    h.require('/.local/remote-qualification/' in str(root)
              and '/.local/remote-qualification/' in str(records) and not records.exists(),
              'NEW_PRIVATE_RECOVERY_RECORD_REQUIRED')
    receipt = (h.parse((root/'pilot-report.json').read_bytes()),
        h.parse((root/'browser-report.json').read_bytes()),
        [json.loads(line) for line in (root/'ui-events.jsonl').read_text().splitlines()])
    if args.installed_records:
        installed = h.unlinked(args.installed_records)
        h.require('/.local/remote-qualification/' in str(installed),'PRIVATE_INSTALLED_RECORD_REQUIRED')
        context = continued_context(*receipt,h.parse((installed/'pilot-report.json').read_bytes()),
            h.parse((installed/'browser-report.json').read_bytes()),config['manifestSha256'],args.test)
    else:
        context = release_context(*receipt,config['manifestSha256'],args.test)
    media = campaign.Media(transport,config,
        campaign.media_input(args.dmg,config,args.remote_dmg,transport['user']))
    # Reuse the consumer-verified immutable media; no transfer or payload rehash.
    from ui_pilot import verified_media, observe
    media_records = h.unlinked(args.media_records)
    h.require('/.local/remote-qualification/' in str(media_records),'PRIVATE_MEDIA_RECORD_REQUIRED')
    verified = verified_media(media_records,media.media)
    h.require(verified and media.file_identity() == verified['observations']['remoteIdentity'],
              'VERIFIED_UNCHANGED_MEDIA_REQUIRED')
    initial = observe(transport,config,args.test,'closed')
    h.require('error' not in initial and initial['dataPreserved'] and initial['ownedDemoProcesses'] == 0
              and initial['ownedDemoListeners'] == 0, 'STOPPED_RETAINED_TEST_REQUIRED')
    h.require(initial.get('desktopState')=='UNLOCKED' and args.workspace.is_absolute()
              and args.workspace.is_dir(),'VISIBLE_RECOVERY_REQUIRED')
    import ui_m1
    python=config['packageRoot']+'/demo-artifacts/aosedge-sdv-demo/host-runtime/python/bin/python3.12'
    tools,_=ui_m1.prepare(transport,args.workspace,HERE.parent.parent,python)
    viewer=None;viewer_closed=False
    context['docker'] = dict(engineId=initial['dockerEngineId'])
    steps = recovery_plan(config)
    pin = hashlib.sha256(json.dumps(dict(candidate=j.identity(config,transport),context=context,
        script=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),sort_keys=True).encode()).hexdigest()
    mounted,started = not media.attached(),False
    with h.Journal(records,pin) as journal:
        runner = j.Runner(journal,j.Remote(transport,config),emit=lambda value:print(value,flush=True))
        try:
            media.mount()
            for step in steps:
                started = True
                row = runner.run_step(step,context)
                if row['outcome'] != 'PASS': break
                context[step['id']] = row['observations']['facts']
                if step['id']=='recovery-presenter':
                    viewer=ui_m1.Observer(transport,tools,records,python,args.test,initial['browserBounds'])
                    viewer.start()
        finally:
            if viewer is not None:
                try:viewer_closed=viewer.close()
                except (OSError,ValueError,subprocess.SubprocessError):viewer_closed=False
            rows = h.read_attempts(records)
            prior = j.rows_by_step(rows).get('shutdown')
            if started and not (prior and prior['outcome'] == 'PASS'):
                runner.run_step(dict(id='shutdown',kind='shutdown',timeout=120),context,
                    prior if prior and prior['outcome'] == 'UNCERTAIN' else None)
            final = observe(transport,config,args.test,'closed')
            closed = ('error' not in final and final['dataPreserved'] and final['ownedDemoProcesses'] == 0
                and final['ownedDemoListeners'] == 0 and final['dockerEngineId'] == initial['dockerEngineId'])
            h.atomic(records/'closed-owners.json',final)
            if mounted and closed:
                import shlex
                media.remote('/usr/bin/hdiutil detach '+shlex.quote(str(Path(config['setupApp']).parent))+' >/dev/null')
            result = j.report(h.read_attempts(records),steps)
            result.update(ownersClosed=closed,ownedMediaDetached=not mounted or not media.attached(),
                candidate=config['manifestSha256'],test=args.test,scope='RECOVERY_AFTER_UI_RELEASES',
                visibleObserverClosed=viewer_closed)
            h.atomic(records/'report.json',result)
    print(json.dumps(j.summary(result)),flush=True)
    return 0 if result['scriptedSequence'] == 'PASS' and closed and viewer_closed else 1


if __name__ == '__main__':
    try: raise SystemExit(main())
    except (OSError, ValueError, KeyError) as error:
        code = str(error) if re.fullmatch(r'[A-Z][A-Z0-9_]{1,100}',str(error)) else \
            'RECOVERY_PREFLIGHT_OR_RECONCILIATION_REQUIRED'
        print(json.dumps(dict(outcome='BLOCKED',code=code)))
        raise SystemExit(2)
