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


def read_query(transport, config, test, query, team=None, release=None):
    """Reuse only the existing read adapter; never call its action adapters."""
    h.require(query in ('component', 'component-idle', 'service', 'backend', 'combined', 'local', 'platform', 'publication'),
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
    with contextlib.redirect_stdout(io.StringIO()):
        result = j.Remote(transport, config)(dict(id='ui-owner-read', kind='observe', args=args, timeout=45),
            'observe', dict(runId=test), str(uuid4()))
    h.require(result['outcome'] == 'PASS', 'UI_OWNER_READ_UNAVAILABLE')
    return result['facts']


def observe(transport, config, test, label):
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
    value = h.parse(h.remote(transport, command, timeout=50))
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


def run(args, transport, config):
    cards = qualified_cards(config, transport, args.test)
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
            ('ui_pilot.py','ui_m1.py','ui_native_gate.py'))).hexdigest(),
        browser=hashlib.sha256(browser_script.read_bytes()+(HERE/'ui_pilot.mjs').read_bytes()).hexdigest()),
        sort_keys=True).encode()).hexdigest()
    started, tunnel, mount_owned, bootstrap_attempted = time.monotonic(), None, False, False
    outcome, closed, detached = 'FAIL', False, False
    context = dict(runId=args.test)
    with h.Journal(records, pin) as journal:
        runner = j.Runner(journal, j.Remote(transport, config), emit=lambda value: print(value, flush=True))
        try:
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
                h.atomic(scratch/'browser-input.json', value)
                with j.Progress('real-browser-pilot', emit=lambda value: print(value, flush=True)):
                    if visible:
                        x,y,width,height=initial['browserBounds']
                        value['windowBounds']=dict(left=x,top=y,width=width,height=height)
                        h.atomic(records/'tools-pin.json',tools_pin)
                        code=ui_m1.execute(transport,m1_tools,value,records,
                            lambda label:observe(transport,config,args.test,label),
                            lambda name,team,release:read_query(transport,config,args.test,name,team,release),python)
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
    print(json.dumps(h.parse((records/'pilot-report.json').read_bytes())), flush=True)
    return 0 if outcome == 'PASS' else 1


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--journey', type=Path, required=True)
    parser.add_argument('--test', required=True)
    parser.add_argument('--observe', choices=sorted(LABELS))
    parser.add_argument('--query', choices=('component', 'component-idle', 'service', 'backend', 'combined', 'local', 'platform', 'publication'))
    parser.add_argument('--team', choices=('brake', 'tire'))
    parser.add_argument('--release')
    parser.add_argument('--scenario', choices=('pilot', 'installed', 'release-story'), default='installed')
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
    if args.query:
        print(json.dumps(read_query(transport, config, args.test, args.query, args.team, args.release)))
        return 0
    if args.observe:
        print(json.dumps(observe(transport, config, args.test, args.observe)))
        return 0
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
