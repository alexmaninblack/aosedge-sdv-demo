#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""One bounded real-browser pilot against an already qualified installed Test."""
import argparse
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shlex
import socket
import subprocess
import sys
import time
from uuid import UUID, uuid4

import campaign
import journey as j
import remote_harness as h
from build_scratch import directory

HERE = Path(__file__).resolve().parent
LABELS = {'before', 'running', 'connected', 'cancelled', 'stopped', 'closed'}


def read_query(transport, config, test, query, team=None, release=None, channel=None):
    """Reuse only the existing read adapter; never call its action adapters."""
    h.require(query in ('component', 'component-idle', 'service', 'backend', 'combined', 'local', 'platform', 'publication', 'exercise'),
              'QUERY_NOT_ALLOWED')
    args = dict(query=query)
    h.require((query in ('service','backend')) == (team is not None), 'QUERY_TEAM_REQUIRED')
    h.require((query == 'publication') == (release is not None), 'QUERY_RELEASE_REQUIRED')
    if team is not None:
        h.require(team in ('brake', 'tire') and query in ('service', 'backend'), 'QUERY_TEAM_INVALID')
        args['team'] = team
    if release is not None:
        h.require(query == 'publication' and re.fullmatch(r'(brake|tire)/[0-9]+\.[0-9]+\.[0-9]+', release),
                  'QUERY_RELEASE_INVALID')
        args['release'] = release
    if channel is None:
        with contextlib.redirect_stdout(io.StringIO()):
            result = j.Remote(transport, config)(dict(id='ui-owner-read', kind='observe', args=args, timeout=45),
                'observe', dict(runId=test), str(uuid4()))
    else:
        payload=dict(config=config,kind='observe',phase='observe',args=args,
                     expectedRun=test,requestId=str(uuid4()),prepared={})
        script=j.WORKER.read_text()+'\nmain('+repr(json.dumps(payload))+')\n'
        python=config['packageRoot']+'/demo-artifacts/aosedge-sdv-demo/host-runtime/python/bin/python3.12'
        result=h.parse(channel.remote(shlex.quote(python)+" -I -B - <<'SDV_FRESH_OWNER_READ'\n"+
            script+'\nSDV_FRESH_OWNER_READ\n',timeout=65))
        h.require(isinstance(result,dict) and set(result)=={'outcome','code','facts'}
            and isinstance(result['facts'],dict) and len(json.dumps(result))<=512*1024,'WORKER_RESPONSE_INVALID')
    h.require(result['outcome'] == 'PASS', 'UI_OWNER_READ_UNAVAILABLE')
    return result['facts']


def observe(transport, config, test, label, channel=None):
    """Read independent owners; never perform an action or persist a raw response."""
    h.require(label in LABELS, 'OBSERVATION_LABEL_INVALID')
    payload = dict(config=config, kind='observe', args=dict(query='snapshot'),
                   phase='observe', requestId=str(uuid4()), expectedRun=test)
    program = j.WORKER.read_text() + '\nREQUEST=' + repr(payload) + '\nLABEL=' + repr(label) + '''
answer=None
try:
 with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
  worker=Worker(REQUEST)
  with worker.imports():
   state=worker.binding()
   from aosedge_demo_orchestrator.backends import BackendService
   from aosedge_demo_orchestrator.environment import JOURNAL
   engine=docker_info()
   require(engine is not None,'DOCKER_ENGINE_UNAVAILABLE')
   if LABEL=='closed':
    from aosedge_demo_orchestrator.host_runtime import selected
    binary=selected(worker.state).entry('presenter')
    screen=subprocess.run([str(binary),'screen'],capture_output=True,text=True,timeout=5)
    screen_value=json.loads(screen.stdout) if screen.returncode==0 else {}
    desktop=screen_value.get('desktopState','UNKNOWN')
    from aosedge_demo_orchestrator.workspace import geometry
    browser_bounds=geometry(screen_value,combined=True)['browser'] if desktop=='UNLOCKED' else None
    answer=dict(wait_for_exit(),dockerEngineId=engine['engineId'],
     dataPreserved=(worker.state/JOURNAL).is_file(),desktopState=desktop,browserBounds=browser_bounds)
   else:
    worker.idle()
    snapshot=exchange('snapshot')
    source=worker.app.source_service.observe()
    vehicle=state['vehicles']['test']
    teams=BackendService(worker.app.environment_service).observe_stack()['teams']
    answer=dict(candidate=worker.pin,
     identity={key:vehicle.get(key) for key in ('localVmId','unitId','nodeId','systemUid')},
     controller=snapshot['vehicles']['test'].get('process'),source=source.get('state'),
     currentVehicle=state.get('currentVehicle'),selectedVehicle=source.get('selectedVehicle'),
     backends={team:teams[team]['state'] for team in ('brake','tire')},
     dockerEngineId=engine['engineId'],dataPreserved=(worker.state/JOURNAL).is_file())
    if LABEL in ('connected','cancelled'):
     answer['control']=worker.local(require_teams=False)['controller']
except Exception as error:
 code=fixed_code(str(error)) or 'OBSERVATION_UNAVAILABLE'
 answer=dict(error=code)
print(json.dumps(answer),flush=True)
'''
    python = config['packageRoot'] + '/demo-artifacts/aosedge-sdv-demo/host-runtime/python/bin/python3.12'
    command = shlex.quote(python) + " -I -B - <<'SDV_UI_PILOT_READ'\n" + program + '\nSDV_UI_PILOT_READ\n'
    value = h.parse(channel.remote(command,timeout=50) if channel else h.remote(transport, command, timeout=50))
    h.require(isinstance(value, dict) and len(json.dumps(value)) < 16384, 'OBSERVATION_RESPONSE_INVALID')
    return value


def forward_args(transport):
    args = h.ssh_args(transport)
    # The only forwarding exception is this loopback-only, same-port tunnel.
    # Keep product Host/Origin checks unchanged and SSH agent forwarding off.
    args[args.index('ClearAllForwardings=yes')] = 'ClearAllForwardings=no'
    args[-1:-1] = ['-N', '-L', '127.0.0.1:18080:127.0.0.1:18080',
                    '-o', 'ExitOnForwardFailure=yes']
    return args


def start_tunnel(transport):
    process = subprocess.Popen(forward_args(transport), stdin=subprocess.DEVNULL,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        deadline = time.monotonic() + 12
        while process.poll() is None:
            try:
                with socket.create_connection(('127.0.0.1', 18080), timeout=.3):
                    return process
            except (ConnectionRefusedError, TimeoutError):
                h.require(time.monotonic() < deadline, 'TUNNEL_NOT_READY')
                time.sleep(.1)
        raise h.Error('TUNNEL_NOT_READY')
    except BaseException:
        stop_tunnel(process)
        raise


def stop_tunnel(process):
    if process and process.poll() is None:
        process.terminate()
        process.wait(timeout=10)


def qualified_cards(config, transport, test):
    context = j.context_from(j.read_records(config, transport))
    h.require(context.get('runId') == test, 'QUALIFIED_TEST_BINDING_REQUIRED')
    rows = j.rows_by_step(j.read_records(config, transport))
    names = {'vdp-v3-ready': 'Vehicle Data Platform installed details',
             'brake-v3-ready': 'Brake service details', 'tire-v1-ready': 'Tire service details'}
    result = {}
    for step, name in names.items():
        h.require(rows.get(step, {}).get('outcome') == 'PASS', 'QUALIFIED_CARDS_REQUIRED')
        facts = context[step]
        version = facts['activeVersion'] if step.startswith('vdp') else facts['instances'][0]['version']
        h.require(isinstance(version, str) and re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+', version),
                  'QUALIFIED_VERSION_INVALID')
        result[name] = ('v1' if step.startswith('tire') else 'v3') + ' · ' + version
    return result


def verified_media(records, media):
    return next((r for r in reversed(h.read_attempts(records))
        if r['command'] in ('media-transfer', 'media-consumer-reverification')
        and r['outcome'] == 'PASS'
        and r['observations'].get('sha256') == media['sha256']
        and r['observations'].get('bytes') == media['bytes']), None)


def continuation_binding(report, events, candidate, test):
    """Pin the one completed prepare-only experiment; never invent a release."""
    h.require(report.get('outcome') == 'PASS' and report.get('scenario') == 'vdp-transition'
              and report.get('candidate') == candidate and report.get('test') == test
              and report.get('ownersClosed') is True, 'CONTINUATION_RECEIPT_REQUIRED')
    rows = [row for row in events if row.get('state') == 'VDP_V2_PREPARATION_CONFIRMED']
    h.require(len(rows) == 1 and rows[0].get('publication') == 'NOT_REQUESTED'
              and re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+', rows[0].get('version', '')),
              'CONTINUATION_PREPARED_VERSION_REQUIRED')
    return dict(preparedV2=rows[0]['version'])


def settled_release_binding(report, browser, events, candidate, test):
    """Resume only after completed releases and a closed native-witness timeout."""
    h.require(report.get('scenario') == browser.get('scenario') == 'release-continuation'
              and report.get('candidate') == candidate and report.get('test') == test
              and report.get('ownersClosed') is True, 'SETTLED_RELEASE_BINDING_REQUIRED')
    passed = {r['stage'] for r in browser.get('stages', []) if r.get('outcome') == 'PASS'}
    h.require({'vdp-v2','brake-v2','vdp-v3','brake-v3','tire-v1'} <= passed,
              'SETTLED_RELEASE_STAGES_REQUIRED')
    failures = [r for r in browser.get('stages', []) if r.get('outcome') != 'PASS']
    h.require(report.get('outcome') == browser.get('outcome') == 'FAIL'
              and len(failures) == 1 and failures[0].get('stage') == 'return-to-road'
              and failures[0].get('code') == 'NATIVE_UI_BROKER_UNAVAILABLE',
              'NATIVE_WITNESS_TIMEOUT_REQUIRED')
    intents = {r['requestId']:r for r in events if r.get('state') == 'DISPATCH_INTENT'}
    result = {}
    for key,action,team,profile in (('vdp-v3-prepare','prepare',None,'v3'),
            ('brake-v3-prepare','service-prepare','brake','v3'),
            ('tire-v1-prepare','service-prepare','tire','v1')):
        found = [r.get('version') for r in events if r.get('productState') == 'COMPLETED'
            and intents.get(r.get('requestId'),{}).get('action') == action
            and intents.get(r.get('requestId'),{}).get('team') == team
            and intents.get(r.get('requestId'),{}).get('profile') == profile]
        h.require(len(found) == 1 and isinstance(found[0],str)
                  and re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+',found[0]), 'RELEASE_RECEIPT_REQUIRED')
        result[key] = dict(version=found[0])
    return result


def completed_release_binding(report, browser, events, candidate, test):
    """Bind a subsequent experiment to a fully passed same-candidate story."""
    h.require(report.get('scenario') == browser.get('scenario') == 'release-story'
              and report.get('outcome') == browser.get('outcome') == 'PASS'
              and report.get('candidate') == candidate and report.get('test') == test
              and report.get('ownersClosed') is True, 'COMPLETED_RELEASE_BINDING_REQUIRED')
    stages = browser.get('stages', [])
    h.require(stages and all(row.get('outcome') == 'PASS' for row in stages)
              and {'vdp-v1','brake-v1','vdp-v2','brake-v2','vdp-v3','brake-v3',
                   'tire-v1','return-to-road','confirmed-stop'} <= {row.get('stage') for row in stages},
              'COMPLETED_RELEASE_STAGES_REQUIRED')
    return release_receipts(events)


def interrupted_tire_binding(report, browser, events, candidate, test):
    """Keep the failed story intact; bind only its settled releases for fresh reads."""
    h.require(report.get('scenario') == browser.get('scenario') == 'release-story'
              and report.get('outcome') == browser.get('outcome') == 'FAIL'
              and report.get('candidate') == candidate and report.get('test') == test
              and report.get('ownersClosed') is True, 'INTERRUPTED_TIRE_BINDING_REQUIRED')
    stages = browser.get('stages', [])
    passed = {row.get('stage') for row in stages if row.get('outcome') == 'PASS'}
    failures = [row for row in stages if row.get('outcome') != 'PASS']
    h.require({'vdp-v1','brake-v1','vdp-v2','brake-v2','vdp-v3','brake-v3'} <= passed
              and len(failures) == 1 and failures[0].get('stage') == 'tire-v1'
              and failures[0].get('code') == 'NATIVE_UI_BROKER_UNAVAILABLE',
              'INTERRUPTED_TIRE_STAGES_REQUIRED')
    waits = [row for row in events if row.get('state') == 'WAITING_FOR_NATIVE_UI'
             and row.get('stage') == 'tire-v1-maneuver' and row.get('action') == 'Tire maneuver']
    h.require(len(waits) == 1, 'TIRE_INSTALL_GATE_REQUIRED')
    receipt = release_receipts(events)
    handle = 'tire/' + receipt['tire-v1-prepare']['version']
    intents = [row for row in events if row.get('state') == 'DISPATCH_INTENT'
               and row.get('action') == 'service-publish' and row.get('release') == handle]
    h.require(len(intents) == 1 and any(row.get('requestId') == intents[0]['requestId']
              and row.get('productState') == 'COMPLETED' and row.get('releaseHandle') == handle
              for row in events), 'TIRE_PUBLICATION_RECEIPT_REQUIRED')
    return receipt


def release_receipts(events):
    intents = {row['requestId']:row for row in events if row.get('state') == 'DISPATCH_INTENT'}
    result = {}
    for key,action,team,profile in (('vdp-v3-prepare','prepare',None,'v3'),
            ('brake-v3-prepare','service-prepare','brake','v3'),
            ('tire-v1-prepare','service-prepare','tire','v1')):
        found = [row.get('version') for row in events if row.get('productState') == 'COMPLETED'
            and intents.get(row.get('requestId'),{}).get('action') == action
            and intents.get(row.get('requestId'),{}).get('team') == team
            and intents.get(row.get('requestId'),{}).get('profile') == profile]
        h.require(len(found) == 1 and isinstance(found[0],str)
                  and re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+',found[0]), 'RELEASE_RECEIPT_REQUIRED')
        result[key] = dict(version=found[0])
    return result


def run(args, transport, config):
    cards = {} if args.scenario in ('native-controls','continuous-campaign','restart-check') else qualified_cards(config, transport, args.test)
    if args.cards_from_release_records:
        prior = h.unlinked(args.cards_from_release_records)
        h.require('/.local/remote-qualification/' in str(prior), 'PRIVATE_RELEASE_RECORD_REQUIRED')
        report = h.parse((prior/'pilot-report.json').read_bytes())
        bind = (completed_release_binding if report.get('outcome') == 'PASS' else interrupted_tire_binding) \
            if report.get('scenario') == 'release-story' else settled_release_binding
        receipt = bind(report, h.parse((prior/'browser-report.json').read_bytes()),
            [json.loads(line) for line in (prior/'ui-events.jsonl').read_text().splitlines()],
            config['manifestSha256'],args.test)
        for name,key,profile in (('Vehicle Data Platform installed details','vdp-v3-prepare','v3'),
                ('Brake service details','brake-v3-prepare','v3'),('Tire service details','tire-v1-prepare','v1')):
            cards[name] = profile+' · '+receipt[key]['version']
    continuation = None
    if args.scenario == 'release-continuation':
        prior = h.unlinked(args.continue_from)
        h.require('/.local/remote-qualification/' in str(prior), 'PRIVATE_CONTINUATION_RECORD_REQUIRED')
        continuation = continuation_binding(h.parse((prior/'pilot-report.json').read_bytes()),
            [json.loads(line) for line in (prior/'ui-events.jsonl').read_text().splitlines()],
            config['manifestSha256'], args.test)
    records = h.unlinked(args.records)
    h.require('/.local/remote-qualification/' in str(records) and not records.exists(),
              'NEW_PRIVATE_RECORD_REQUIRED')
    h.require(args.workspace.is_absolute() and args.workspace.is_dir(), 'SCRATCH_WORKSPACE_REQUIRED')
    # A port conflict is not permission to stop an unrelated local application.
    visible = args.display == 'm1'
    if not visible:
        with socket.socket() as reservation:
            reservation.bind(('127.0.0.1', 18080))
    probe = h.probe(transport)
    h.require(probe['console'] == transport['user'] and probe['demoProcesses'] == 0
              and probe['busyPorts'] == 0, 'IDLE_TARGET_REQUIRED')
    h.require((visible or args.node is not None and args.node.is_file())
              and (HERE.parent.parent/'apps/presenter-ui/node_modules/@playwright/test').is_dir(),
              'EXISTING_DEVELOPMENT_BROWSER_TOOLS_REQUIRED')
    media = campaign.Media(transport, config,
        campaign.media_input(args.dmg, config, args.remote_dmg, transport['user']),
        emit=lambda value: print(value, flush=True))
    verified = verified_media(Path(config['records']+'-installation'), media.media)
    if args.media_records:
        prior = h.unlinked(args.media_records)
        h.require('/.local/remote-qualification/' in str(prior), 'PRIVATE_MEDIA_RECORD_REQUIRED')
        verified = verified_media(prior, media.media) or verified
    h.require(verified is not None, 'VERIFIED_MEDIA_REQUIRED')
    changed_media = media.file_identity() != verified['observations']['remoteIdentity']
    initial = observe(transport, config, args.test, 'closed')
    h.require('error' not in initial and initial['dataPreserved'], 'PRESERVED_STOPPED_TEST_REQUIRED')
    h.require(initial.get('desktopState') == 'UNLOCKED', 'TARGET_DESKTOP_NOT_UNLOCKED')
    scenario = getattr(args, 'scenario', 'pilot')
    h.require(not visible or scenario != 'pilot', 'VISIBLE_SCENARIO_REQUIRED')
    m1_tools=None
    python=config['packageRoot']+'/demo-artifacts/aosedge-sdv-demo/host-runtime/python/bin/python3.12'
    if visible:
        import ui_m1
        m1_tools,tools_pin=ui_m1.prepare(transport,args.workspace,HERE.parent.parent,python)
    browser_script = HERE / ('ui_pilot.mjs' if scenario == 'pilot' else 'ui_journey.mjs')
    pin = hashlib.sha256(json.dumps(dict(candidate=config['manifestSha256'], test=args.test,
        connection=j.identity(config, transport), scenario=scenario,display=args.display,
        runner=hashlib.sha256(b''.join((HERE/name).read_bytes() for name in
            ('ui_pilot.py','ui_m1.py','ui_native_gate.py','native_ui_live.py','ui_read_transport.py'))).hexdigest(),
        ownerReader=j.source_pin(),
        nativeBuild=h.digest(args.native_build/'build-receipt.json') if args.native_build else None,
        browser=hashlib.sha256(browser_script.read_bytes()+(HERE/'ui_pilot.mjs').read_bytes()
            +(HERE/'ui_read_broker.mjs').read_bytes()).hexdigest()),
        sort_keys=True).encode()).hexdigest()
    started, tunnel, mount_owned, bootstrap_attempted = time.monotonic(), None, False, False
    native = None
    native_closed = True
    outcome, closed, detached = 'FAIL', False, False
    context = dict(runId=args.test)
    with h.Journal(records, pin) as journal:
        runner = j.Runner(journal, j.Remote(transport, config), emit=lambda value: print(value, flush=True))
        try:
            if scenario in ('native-controls','continuous-campaign'):
                from native_ui_live import Live
                native = Live(transport,config,args.test,args.native_build,records,args.native_run_id,scenario=scenario)
            if changed_media:
                # A changed consumer identity invalidates the cached digest,
                # not the product. Verify this existing copy once; no transfer.
                row = journal.begin('media-consumer-reverification')
                facts = media.transfer(reconcile=True)
                journal.finish(row, 'PASS', 'EXISTING_MEDIA_DIGEST_CONFIRMED', facts)
            mount_owned = not media.attached()
            row = journal.begin('media-mount-existing-candidate')
            facts = media.mount()
            journal.finish(row, 'PASS', 'SIGNED_MEDIA_BOUND', facts)
            bootstrap_attempted = True
            boot = runner.run_step(dict(id='browser-bootstrap', kind='presenter-start', timeout=90), context)
            h.require(boot['outcome'] == 'PASS', 'PRESENTER_BOOTSTRAP_UNCONFIRMED')
            if not visible: tunnel = start_tunnel(transport)
            with directory(args.workspace) as scratch:
                value = dict(repository=str(HERE.parent.parent), records=str(records), python=sys.executable,
                    helper=str(Path(__file__).resolve()), config=str(args.config.resolve()),
                    journey=str(args.journey.resolve()), test=args.test, cards=cards, scenario=scenario)
                if native is not None: value['nativeRunner'] = True
                if getattr(args,'native_versions',None) is not None:
                    h.require(scenario in ('native-controls','continuous-campaign'),'NATIVE_VERSION_SCOPE_INVALID')
                    value['nativeVersions']=args.native_versions
                if continuation: value['continuation'] = continuation
                h.atomic(scratch/'browser-input.json', value)
                with j.Progress('real-browser-pilot', emit=lambda value: print(value, flush=True)):
                    if visible:
                        x,y,width,height=initial['browserBounds']
                        value['windowBounds']=dict(left=x,top=y,width=width,height=height)
                        h.atomic(records/'tools-pin.json',tools_pin)
                        from ui_read_transport import ReadTransport
                        channel=ReadTransport(transport,scratch)
                        try:
                            with channel:
                                code=ui_m1.execute(transport,m1_tools,value,records,
                                    lambda label:observe(transport,config,args.test,label,channel=channel),
                                    lambda name,team,release:read_query(transport,config,args.test,name,team,release,channel=channel),python,native=native)
                        finally:h.atomic(records/'read-transport-report.json',channel.report())
                    else:
                        child=subprocess.run([str(args.node),str(browser_script),str(scratch/'browser-input.json')],
                            env=dict(os.environ,TMPDIR=str(scratch)),timeout=700 if scenario=='pilot' else 3600,
                            stderr=subprocess.PIPE)
                        code=child.returncode
                h.require(code == 0, 'UI_PILOT_CHECK_FAILED')
            outcome = 'PASS'
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            code = str(error) if re.fullmatch(r'[A-Z][A-Z0-9_]{1,100}', str(error)) else 'PILOT_TRANSPORT_OR_PREREQUISITE'
            h.atomic(records/'failure.json', dict(code=code))
            print(code, flush=True)
        finally:
            if native is not None:
                try: native_closed = native.close()
                except (OSError,ValueError,subprocess.SubprocessError):
                    native_closed = False
                    outcome = 'FAIL'
                    print('NATIVE_RUNNER_CLEANUP_UNCONFIRMED',flush=True)
            try:
                stop_tunnel(tunnel)
                if bootstrap_attempted:
                    step = dict(id='browser-cleanup', kind='shutdown', timeout=120)
                    stop = runner.run_step(step, context)
                    if stop['outcome'] == 'UNCERTAIN':
                        stop = runner.run_step(step, context, previous=stop)  # Read-only resolution, never replay.
                    h.require(stop['outcome'] == 'PASS', 'PILOT_CLEANUP_UNCONFIRMED')
                final = observe(transport, config, args.test, 'closed')
                h.require('error' not in final and final['dataPreserved'] and
                    final['dockerEngineId'] == initial['dockerEngineId'] and
                    final['ownedDemoProcesses'] == 0 and final['ownedDemoListeners'] == 0,
                    'PILOT_EXIT_UNCONFIRMED')
                h.atomic(records/'closed-owners.json', final)
                closed = True
                if mount_owned:
                    # No forced detach. Setup/window owners must already be gone.
                    count = media.remote("/bin/ps -axo comm= | /usr/bin/awk '/SDVLabSetup$/ {n++} END {print n+0}'").strip()
                    h.require(count == '0', 'SETUP_STILL_OPEN')
                    row = journal.begin('media-detach-owned-candidate')
                    media.remote('/usr/bin/hdiutil detach '+shlex.quote(str(Path(config['setupApp']).parent))+' >/dev/null')
                    h.require(not media.attached(), 'MEDIA_DETACH_UNCONFIRMED')
                    journal.finish(row, 'PASS', 'OWNED_MEDIA_DETACHED')
                detached = not mount_owned or not media.attached()
            except (OSError, ValueError, subprocess.SubprocessError):
                outcome = 'FAIL'
                print('PILOT_CLEANUP_UNCONFIRMED — preserve records for reconciliation', flush=True)
            h.atomic(records/'pilot-report.json', dict(outcome=outcome,
                seconds=round(time.monotonic()-started, 3), candidate=config['manifestSha256'], test=args.test,
                browserPilot=outcome, nativeAcceptance='NOT_RUN', fullE2E='NOT_COMPLETE',
                scenario=scenario,
                browserLocation='M1_VISIBLE' if visible else 'DEVELOPMENT_MAC_HEADLESS',
                ownersClosed=closed, tunnelClosed=tunnel is None or tunnel.poll() is not None,
                ownedMediaDetached=detached, dockerPolicy='PRESERVED'))
            report=h.parse((records/'pilot-report.json').read_bytes())
            report['nativeRunnerClosed']=native_closed
            report['nativeControls']='PASS' if scenario=='native-controls' and outcome=='PASS' and native_closed else 'NOT_QUALIFIED'
            report['continuousCampaign']='PASS' if scenario=='continuous-campaign' and outcome=='PASS' and native_closed and closed else 'NOT_QUALIFIED'
            h.atomic(records/'pilot-report.json',report)
    print(json.dumps(h.parse((records/'pilot-report.json').read_bytes())), flush=True)
    return 0 if outcome == 'PASS' else 1


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--journey', type=Path, required=True)
    parser.add_argument('--test', required=True)
    parser.add_argument('--observe', choices=sorted(LABELS))
    parser.add_argument('--query', choices=('component', 'component-idle', 'service', 'backend', 'combined', 'local', 'platform', 'publication', 'exercise'))
    parser.add_argument('--team', choices=('brake', 'tire'))
    parser.add_argument('--release')
    parser.add_argument('--scenario', choices=('pilot', 'installed', 'release-story', 'vdp-transition', 'release-continuation', 'tire-review', 'road-return', 'moving-sota', 'native-controls','continuous-campaign','restart-check'), default='installed')
    parser.add_argument('--native-build',type=Path,help='Verified separate signed native qualification build')
    parser.add_argument('--native-run-id',default='native-ui-live-20261012')
    parser.add_argument('--continue-from', type=Path, help='Completed same-candidate prepare-only records')
    parser.add_argument('--cards-from-release-records', type=Path,
                        help='Passed release story or exact native-witness-interrupted continuation records')
    parser.add_argument('--display',choices=('m1','background'),default='m1')
    parser.add_argument('--dmg', type=Path)
    parser.add_argument('--remote-dmg')
    parser.add_argument('--records', type=Path)
    parser.add_argument('--media-records', type=Path,
                        help='Optional previous private consumer digest verification; identity must still match')
    parser.add_argument('--workspace', type=Path)
    parser.add_argument('--node', type=Path)
    args = parser.parse_args()
    h.require(str(UUID(args.test)) == args.test, 'TEST_UUID_INVALID')
    transport, _ = h.configuration(args.config)
    config = j.configuration(args.journey, transport['user'])
    h.require((args.scenario == 'release-continuation') == (args.continue_from is not None),
              'CONTINUATION_RECORD_BOUNDARY')
    h.require(not args.cards_from_release_records or args.scenario in ('installed','tire-review','road-return','moving-sota'), 'INSTALLED_CARD_RECORD_BOUNDARY')
    h.require(args.scenario not in ('tire-review','road-return','moving-sota') or args.cards_from_release_records is not None,
              'ROAD_RETURN_RELEASE_RECORD_REQUIRED')
    if args.query:
        print(json.dumps(read_query(transport, config, args.test, args.query, args.team, args.release)))
        return 0
    if args.observe:
        print(json.dumps(observe(transport, config, args.test, args.observe)))
        return 0
    h.require((args.scenario in ('native-controls','continuous-campaign'))==(args.native_build is not None)
              and (not args.native_build or args.display=='m1'), 'NATIVE_RUNNER_SCOPE_INVALID')
    h.require(all((args.dmg, args.remote_dmg, args.records, args.workspace))
              and (args.display=='m1' or args.node), 'PILOT_INPUT_REQUIRED')
    return run(args, transport, config)


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        code = str(error) if re.fullmatch(r'[A-Z][A-Z0-9_]{1,100}', str(error)) else 'PILOT_PREFLIGHT_UNAVAILABLE'
        print(json.dumps(dict(outcome='BLOCKED', code=code)))
        raise SystemExit(2)
