#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Run Presenter browser fixtures on M1 only, against isolated compiled web bytes.

No installed payload, Test, Docker or Cloud changes. The static server and
browser are scenario-owned. Private M1 review files are retained after closure.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import time

import remote_harness as h

REPO = Path(__file__).resolve().parents[2]


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--tools-root', required=True)
    parser.add_argument('--records', type=Path, required=True)
    args = parser.parse_args()
    config, _ = h.configuration(args.config)
    user_root = '/Users/' + config['user']
    h.require(re.fullmatch(re.escape(user_root) + r'/SDV-Qualification/ui-tools/[a-f0-9]{20}', args.tools_root), 'FIXTURE_TOOLS_ROOT_INVALID')
    records = h.unlinked(args.records)
    h.require('/.local/remote-qualification/' in str(records) and not records.exists(), 'NEW_PRIVATE_RECORDS_REQUIRED')
    records.mkdir(parents=True, mode=0o700)
    web = REPO / 'apps/presenter-ui'
    paths = sorted(p for folder in ('dist', 'tests/browser') for p in (web / folder).rglob('*') if p.is_file())
    paths += [web / 'tests/unit/backendFixture.ts']
    h.require((web / 'dist/index.html') in paths and all(not p.is_symlink() for p in paths), 'COMPILED_WEB_REQUIRED')
    inventory = {str(p.relative_to(web)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    pin = hashlib.sha256(json.dumps(inventory, sort_keys=True).encode() + Path(__file__).read_bytes()).hexdigest()
    target = config['remoteRoot'] + '/presenter-fixtures-' + pin[:12]
    payload = dict(target=target, tools=args.tools_root, inventory=inventory)
    shell = shlex.join(h.ssh_args(config)[:-1])
    h.remote(config, 'umask 077; test ! -e ' + shlex.quote(target) + '; /bin/mkdir -m 700 ' + shlex.quote(target), timeout=15)
    for name in ('dist', 'tests'):
        # Transfer no developer dependency cache or installed application.
        subprocess.run(['/usr/bin/rsync', '-rlt', '-e', shell,
            '--exclude=unit/*', '--include=unit/backendFixture.ts',
            str(web / name), config['user'] + '@' + config['host'] + ':' + shlex.quote(target + '/')], check=True, timeout=90)
    # Unit fixture data only; type imports are erased by the browser-test loader.
    h.remote(config, '/bin/mkdir -p ' + shlex.quote(target + '/tests/unit'), timeout=10)
    subprocess.run(['/usr/bin/rsync', '-t', '-e', shell, str(web / 'tests/unit/backendFixture.ts'),
        config['user'] + '@' + config['host'] + ':' + shlex.quote(target + '/tests/unit/backendFixture.ts')], check=True, timeout=20)
    program = 'INPUT=' + repr(payload) + '\n' + r'''
import hashlib,json,os,pathlib,signal,subprocess,time
p=pathlib.Path(INPUT['target']);tools=pathlib.Path(INPUT['tools'])
assert p.is_dir() and p.stat().st_uid==os.getuid()
assert all(hashlib.sha256((p/name).read_bytes()).hexdigest()==digest for name,digest in INPUT['inventory'].items())
assert (tools/'tools.json').is_file()
subprocess.run(['/usr/bin/codesign','--verify','--deep','--strict',str(tools/'Google Chrome.app')],check=True,capture_output=True,timeout=40)
occupied=subprocess.run(['/usr/sbin/lsof','-nP','-iTCP:18070','-sTCP:LISTEN'],capture_output=True,timeout=10)
assert occupied.returncode==1 and not occupied.stdout,'FIXTURE_PORT_OCCUPIED'
def browser_pids():
 rows=subprocess.check_output(['/bin/ps','-axo','pid=,command='],text=True).splitlines()
 return {int(row.strip().split(None,1)[0]) for row in rows if str(tools/'Google Chrome.app/Contents/') in row}
previous_browsers=browser_pids()
(p/'node_modules').symlink_to(tools/'node_modules',target_is_directory=True)
# No hostname/reverse-DNS discovery in a loopback-only fixture server.
(p/'fixture-server.py').write_text("import functools,http.server,socketserver\nclass Server(socketserver.ThreadingTCPServer):\n allow_reuse_address=True\n daemon_threads=True\nwith Server(('127.0.0.1',18070),functools.partial(http.server.SimpleHTTPRequestHandler,directory='dist')) as server:\n server.serve_forever()\n")
configuration="""import {defineConfig} from '@playwright/test';
export default defineConfig({testDir:'./tests/browser',outputDir:'test-results',workers:2,retries:0,timeout:30000,globalTimeout:600000,
 reporter:[['line'],['json',{outputFile:'browser-results.json'}]],
 use:{baseURL:'http://127.0.0.1:18070',viewport:{width:1440,height:900},trace:'off',
 launchOptions:{executablePath:CHROME}},
 webServer:{command:'/opt/homebrew/bin/python3.12 -I -B fixture-server.py',url:'http://127.0.0.1:18070',reuseExistingServer:false,timeout:15000,stdout:'pipe',stderr:'pipe'}});""".replace('CHROME',json.dumps(str(tools/'Google Chrome.app/Contents/MacOS/Google Chrome')))
(p/'playwright.config.mjs').write_text(configuration)
started=time.monotonic()
with (p/'browser-process.log').open('xb') as log:
 child=subprocess.Popen([str(tools/'node'),str(tools/'node_modules/@playwright/test/cli.js'),'test','--config',str(p/'playwright.config.mjs')],cwd=p,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 try: exit_code=child.wait(timeout=660)
 except subprocess.TimeoutExpired:
  os.killpg(child.pid,signal.SIGINT)
  try: child.wait(timeout=20)
  except subprocess.TimeoutExpired:
   os.killpg(child.pid,signal.SIGTERM);child.wait(timeout=10)
  exit_code=124
closed=subprocess.run(['/usr/sbin/lsof','-nP','-iTCP:18070','-sTCP:LISTEN'],capture_output=True,timeout=10)
summary=dict(exitCode=exit_code,seconds=round(time.monotonic()-started,3),fixtureOnly=True,installedPayloadChanged=False,serverClosed=closed.returncode==1 and not closed.stdout,browserOwnersClosed=not (browser_pids()-previous_browsers))
(p/'fixture-report.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary))
'''
    started = time.monotonic()
    result = json.loads(h.remote(config, '/opt/homebrew/bin/python3.12 -I -B - <<\'FIXTURE\'\n' + program + '\nFIXTURE\n', timeout=960))
    for name in ('fixture-report.json', 'browser-results.json', 'browser-process.log', 'test-results'):
        subprocess.run(['/usr/bin/rsync', '-rlt', '-e', shell,
            config['user'] + '@' + config['host'] + ':' + shlex.quote(target + '/' + name), str(records) + '/'], check=True, timeout=90)
    h.atomic(records / 'campaign-report.json', dict(result, target=target, inputSha256=pin, secondsIncludingTransfer=round(time.monotonic()-started, 3)))
    print(json.dumps(result), flush=True)
    return 0 if result['exitCode'] == 0 and result['serverClosed'] and result['browserOwnersClosed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
