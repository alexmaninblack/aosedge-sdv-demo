#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""One engineering entry: pinned DMG, signed Setup, installed journey, shutdown."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import plistlib
import re
import shlex
import subprocess
import sys

import journey as j
import remote_harness as h
from journey_plan import plan


def media_input(dmg, config, remote_dmg, user):
    dmg = h.unlinked(dmg)
    receipt = h.parse(h.unlinked(dmg.with_suffix('.receipt.json')).read_bytes())
    h.require(receipt.get('manifestSha256') == config['manifestSha256']
              and isinstance(receipt.get('dmgSha256'), str)
              and re.fullmatch('[a-f0-9]{64}', receipt['dmgSha256'])
              and type(receipt.get('dmgBytes')) is int
              and dmg.is_file() and dmg.stat().st_size == receipt['dmgBytes'], 'MEDIA_RECEIPT_MISMATCH')
    remote = Path(remote_dmg)
    home = Path('/Users') / user / 'SDV-Qualification'
    h.require(remote.is_absolute() and str(remote) == remote_dmg and '..' not in remote.parts
              and remote.is_relative_to(home) and remote.parent != home
              and remote.suffix == '.dmg' and not any(ord(c) < 32 for c in remote_dmg), 'MEDIA_TARGET_INVALID')
    return dict(path=str(dmg), remotePath=remote_dmg, bytes=receipt['dmgBytes'],
                sha256=receipt['dmgSha256'])


class Media:
    def __init__(self, transport, config, media, emit=print):
        self.transport, self.config, self.media, self.emit = transport, config, media, emit

    def remote(self, script, timeout=60):
        with j.Progress('media-or-setup', emit=self.emit):
            return h.remote(self.transport, script, timeout=timeout)

    def file_identity(self):
        path = shlex.quote(self.media['remotePath'])
        value = self.remote('set -eu\ntest ! -L '+path+'\ntest -f '+path+
            '\ntest "$(stat -f %u:%l '+path+')" = "$(id -u):1"\n'+
            '/usr/bin/stat -f %d:%i:%z:%m:%c:%Lp '+path).strip()
        h.require(re.fullmatch('[0-9]+(?::[0-9]+){5}',value), 'MEDIA_STAT_UNAVAILABLE')
        return value

    def transfer(self, reconcile=False):
        q, path = shlex.quote, Path(self.media['remotePath'])
        # Never truncate/adopt a linked, shared or foreign target directory.
        checks = ['set -eu', 'umask 077']
        checks.extend('test ! -L '+q(str(p)) for p in (path, *path.parents))
        for parent in (path.parent.parent, path.parent):
            checks += ['if test -e '+q(str(parent))+'; then',
                'test -d '+q(str(parent)),
                'test "$(stat -f %u:%Lp '+q(str(parent))+')" = "$(id -u):700"',
                'else mkdir '+q(str(parent))+'; fi']
        checks += ['if test -e '+q(str(path))+'; then',
            'test -f '+q(str(path))+'; stat -f %z '+q(str(path)), 'else echo ABSENT; fi']
        exists = self.remote('\n'.join(checks)).strip()
        if exists == 'ABSENT':
            h.require(not reconcile, 'TRANSFER_ABSENT_AFTER_INTERRUPTION')
            h.require(h.digest(Path(self.media['path'])) == self.media['sha256'], 'LOCAL_MEDIA_CHANGED')
            options = h.ssh_args(self.transport)[1:-1]
            options.remove('-T')
            i = options.index('-b')
            options[i:i+2] = ['-o', 'BindAddress='+options[i+1]]
            self.emit('Delivering '+Path(self.media['path']).name)
            # scp provides a real byte progress meter on an interactive terminal.
            with j.Progress('media-transfer', emit=self.emit):
                value = subprocess.run(['/usr/bin/scp', *options, self.media['path'],
                    self.transport['user']+'@'+self.transport['host']+':'+q(str(path))],
                    timeout=1800, stdout=subprocess.DEVNULL if not sys.stdout.isatty() else None,
                    stderr=subprocess.PIPE)
            h.require(value.returncode == 0, 'TRANSFER_UNCONFIRMED')
        else:
            h.require(exists == str(self.media['bytes']), 'TRANSFER_SIZE_MISMATCH')
        before = self.file_identity()
        observed = self.remote('set -eu\ntest "$(stat -f %z '+q(str(path))+')" = '+
            str(self.media['bytes'])+'\n/usr/bin/shasum -a 256 '+q(str(path)), timeout=240).split()[0]
        h.require(observed == self.media['sha256'], 'TRANSFER_DIGEST_MISMATCH')
        h.require(before == self.file_identity(), 'MEDIA_CHANGED_DURING_VERIFICATION')
        return dict(bytes=self.media['bytes'], sha256=observed, remoteIdentity=before)

    def attachments(self):
        return plistlib.loads(self.remote('/usr/bin/hdiutil info -plist').encode()).get('images', [])

    def attached(self):
        mount = str(Path(self.config['setupApp']).parent)
        for image in self.attachments():
            if any(row.get('mount-point') == mount for row in image.get('system-entities', [])):
                h.require(image.get('image-path') == self.media['remotePath'], 'MOUNT_OCCUPIED_BY_OTHER_MEDIA')
                return True
        return False

    def mount(self, reconcile=False):
        if not self.attached():
            h.require(not reconcile, 'MOUNT_UNCONFIRMED')
            self.remote('/usr/bin/hdiutil attach -readonly -nobrowse -mountpoint '+
                shlex.quote(str(Path(self.config['setupApp']).parent))+' '+
                shlex.quote(self.media['remotePath'])+' >/dev/null', timeout=180)
        h.require(self.attached(), 'MOUNT_UNCONFIRMED')
        app = shlex.quote(self.config['setupApp'])
        output = self.remote('set -eu\n/usr/bin/codesign --verify --deep --strict '+app+
            '\n/usr/bin/shasum -a 256 '+shlex.quote(self.config['setupApp']+'/Contents/MacOS/SDVLabSetup')+
            '\n/bin/cat '+shlex.quote(self.config['setupApp']+'/Contents/Resources/tooling/scripts/distribution/setup_release.json'), timeout=60)
        lines = output.splitlines()
        h.require(lines[0].split()[0] == self.config['setupSha256'] and
            h.parse('\n'.join(lines[1:]))['manifestSha256'] == self.config['manifestSha256'], 'SIGNED_SETUP_PIN_MISMATCH')
        return dict(signatureVerified=True, manifestSha256=self.config['manifestSha256'])

    def setup(self, action, reconcile=False):
        resources = self.config['setupApp']+'/Contents/Resources'
        request = dict(action=action, source=self.config['sourceRoot'], store=self.config['storeRoot'],
                       state=self.config['instanceRoot'])
        # The trusted embedded helper owns verification, transactional recovery
        # and selection. No repository imports, hidden dependency or GUI launch.
        program = '''import json,sys
from pathlib import Path
sys.path.insert(0,RESOURCES+'/tooling/scripts/distribution')
sys.path.insert(0,RESOURCES+'/tooling/apps/demo-orchestrator/src')
import setup_bridge as b
try:
 b.supported_platform()
 v=b.request(json.dumps(dict(REQUEST,action='preflight')).encode())
 pin=b.release()['manifestSha256']
 p=b.perform(v,pin)
 if RECONCILE:
  store=b.Store(v['store'],p['volumeUUID'],volume_probe=b.volume_identity)
  if REQUEST['action']=='install':
   out=store.verify(pin)
  else:
   out=b.Versions(store,v['state']).status()
   b.require(out.get('current')==pin,'SELECTION_UNCONFIRMED')
 else:
  out=b.perform(b.request(json.dumps(dict(REQUEST,volumeUUID=p['volumeUUID'],revision=p['revision'])).encode()),pin)
 print(json.dumps(dict(outcome='PASS',code='SETUP_POSTCONDITION_OBSERVED',facts={k:out[k] for k in ('status','current','reused','files','logicalBytes') if k in out})))
except Exception as e:
 print(json.dumps(dict(outcome='BLOCKED',code=b.error_code(e),facts={})))
'''
        script = 'RESOURCES='+repr(resources)+'\nREQUEST='+repr(request)+'\nRECONCILE='+repr(reconcile)+'\n'+program
        output = self.remote(shlex.quote(resources+'/python/bin/python3.12')+
            " -I -B - <<'SDV_SETUP_CAMPAIGN'\n"+script+'\nSDV_SETUP_CAMPAIGN', timeout=900)
        value = h.parse(output)
        h.require(value['outcome'] == 'PASS', value['code'])
        return value['facts']


def installation(media, journal, emit=print):
    """One attempt per action; interruption uses read-only reconciliation."""
    actions = [('media-transfer', media.transfer), ('media-mount', media.mount),
               ('setup-install', lambda reconcile=False: media.setup('install', reconcile)),
               ('setup-prepare', lambda reconcile=False: media.setup('prepare', reconcile))]
    for name, action in actions:
        rows = h.read_attempts(journal.root)
        prior = next((r for r in reversed(rows) if r['command'] == name), None)
        if prior and prior['outcome'] == 'PASS':
            try:
                if name == 'media-transfer':
                    h.require(media.file_identity() == prior['observations'].get('remoteIdentity'),
                              'VERIFIED_MEDIA_CHANGED')
                # Mounts are ephemeral; reattach only this verified DMG when
                # absent. Never displace another image.
                if name == 'media-mount':
                    media.mount()
            except (OSError, ValueError, subprocess.SubprocessError) as error:
                row = journal.begin('verify-'+name)
                code = str(error) if isinstance(error,(h.Error,h.InstallError)) else 'MEDIA_RECHECK_UNAVAILABLE'
                journal.finish(row, 'BLOCKED', code)
                emit(name+': '+code)
                return False
            continue
        if prior and prior['outcome'] != 'UNCERTAIN':
            return False
        row = journal.begin(name)
        row['campaignSourceSha256'] = j.source_pin()
        h.atomic(journal.root/('attempt-%04d.json' % row['attempt']), row)
        emit(name+': '+('reconciling' if prior else 'started'))
        try:
            facts = action(reconcile=prior is not None)
            journal.finish(row, 'PASS', 'POSTCONDITION_OBSERVED', facts)
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            code = str(error) if isinstance(error, (h.Error, h.InstallError)) and re.fullmatch(
                '[A-Z][A-Z0-9_]{1,100}', str(error)) else 'MEDIA_OR_SETUP_UNCONFIRMED'
            journal.finish(row, 'UNCERTAIN', code)
            emit(name+': '+code)
            return False
        emit(name+': PASS')
    return True


def installation_report(root, success):
    rows = h.read_attempts(root)
    latest = {r['command']:r for r in rows}
    value = dict(installation='PASS' if success else 'NOT_COMPLETE', nativeAcceptance='NOT_RUN',
                 fullE2E='NOT_COMPLETE', candidateBound=True,
                 steps=[dict(step=r['command'], outcome=r['outcome'], code=r['code'],
                             seconds=r.get('durationSeconds')) for r in latest.values()])
    h.atomic(root/'report.json', value)
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--journey', type=Path, required=True)
    parser.add_argument('--dmg', type=Path, required=True)
    parser.add_argument('--remote-dmg', required=True)
    parser.add_argument('--until')
    parser.add_argument('--resume-partial-create', action='store_true')
    args = parser.parse_args()
    transport, _ = h.configuration(args.config)
    config = j.configuration(args.journey, transport['user'])
    media = media_input(args.dmg, config, args.remote_dmg, transport['user'])
    pin = hashlib.sha256(json.dumps(dict(media=media, journey=j.identity(config, transport)), sort_keys=True).encode()).hexdigest()
    records = Path(config['records']+'-installation')
    probe = h.probe(transport)
    h.require(probe['console'] == transport['user'] and probe['internal'] == 'true', 'TARGET_LOGIN_OR_STORAGE_REQUIRED')
    h.require(probe['memoryBytes'] >= 16*2**30 and probe['freeKiB']*1024 >= 90*2**30+media['bytes'],
              'TARGET_CAPACITY_REQUIRED')
    if not j.read_records(config, transport):
        h.require(probe['demoProcesses'] == 0 and probe['busyPorts'] == 0, 'EXISTING_RUNTIME_CONFLICT')
    client = Media(transport, config, media, emit=lambda value: print(value, flush=True))
    with h.Journal(records, pin) as journal:
        installed = False
        try:
            installed = installation(client, journal, emit=lambda value: print(value, flush=True))
        finally:
            installation_report(records, installed)
        if not installed:
            return 2
    # Delegate the whole run, including its guaranteed ordinary cleanup/report,
    # to the existing runner rather than composing another runtime lifecycle.
    argv = ['journey.py', '--config', str(args.config), '--journey', str(args.journey), 'run']
    if args.until: argv += ['--until', args.until]
    if args.resume_partial_create: argv += ['--resume-partial-create']
    old = sys.argv
    try:
        sys.argv = argv
        j.main()
    finally:
        sys.argv = old
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError, subprocess.SubprocessError):
        print(json.dumps(dict(outcome='BLOCKED', code='CAMPAIGN_PREFLIGHT_OR_RECONCILIATION_REQUIRED')))
        raise SystemExit(2)
