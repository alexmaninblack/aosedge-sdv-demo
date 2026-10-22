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


def metadata_only_media_change(before, after):
    """A mount can update ctime/xattrs; content-bearing identity must stay fixed."""
    first, second = before.split(':'), after.split(':')
    return (len(first) == len(second) == 6 and all(v.isdigit() for v in first+second)
            and first != second and all(first[i] == second[i] for i in (0,1,2,3,5)))


def consumer_space_required(receipt, media_cached, candidate_present):
    logical, compressed = receipt.get('logicalBytes'), receipt.get('dmgBytes')
    h.require(type(logical) is int and 0 < logical <= 48*2**30
              and type(compressed) is int and compressed > 0
              and type(media_cached) is type(candidate_present) is bool, 'MEDIA_CAPACITY_RECEIPT_INVALID')
    return 90*2**30 + (0 if candidate_present else logical) + (0 if media_cached else compressed)


def receipt_only(path):
    return path.name.endswith('.receipt.json')


def media_receipt_path(path):
    return path if receipt_only(path) else path.with_suffix('.receipt.json')


def media_input(dmg, config, remote_dmg, user):
    dmg = h.unlinked(dmg)
    receipt = h.parse(h.unlinked(media_receipt_path(dmg)).read_bytes())
    h.require(receipt.get('manifestSha256') == config['manifestSha256']
              and isinstance(receipt.get('dmgSha256'), str)
              and re.fullmatch('[a-f0-9]{64}', receipt['dmgSha256'])
              and type(receipt.get('dmgBytes')) is int
              and receipt['dmgBytes'] > 0
              and (receipt_only(dmg) or dmg.is_file() and dmg.stat().st_size == receipt['dmgBytes']),
              'MEDIA_RECEIPT_MISMATCH')
    remote = Path(remote_dmg)
    home = Path('/Users') / user / 'SDV-Qualification'
    h.require(remote.is_absolute() and str(remote) == remote_dmg and '..' not in remote.parts
              and remote.is_relative_to(home) and remote.parent != home
              and remote.suffix == '.dmg' and not any(ord(c) < 32 for c in remote_dmg), 'MEDIA_TARGET_INVALID')
    return dict(path=None if receipt_only(dmg) else str(dmg), remotePath=remote_dmg, bytes=receipt['dmgBytes'],
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

    def allocation(self):
        """Presence controls only the capacity estimate; normal owners still verify bytes."""
        file, candidate = shlex.quote(self.media['remotePath']), shlex.quote(self.config['packageRoot'])
        script = ('set -eu\nmedia=false\ncandidate=false\ntest ! -L '+file+'\ntest ! -L '+candidate+
            '\nif test -e '+file+'; then test -f '+file+'; test "$(stat -f %z '+file+')" = '+str(self.media['bytes'])+
            '; media=true; fi\nif test -e '+candidate+'; then test -d '+candidate+'; candidate=true; fi\n'+
            'printf \'{"mediaCached":%s,"candidatePresent":%s}\\n\' "$media" "$candidate"\n')
        return h.parse(self.remote(script, timeout=10))

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
            h.require(self.media['path'] is not None, 'CONSUMER_MEDIA_MISSING')
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

    def capacity_preflight(self):
        """Prove the failed capacity guard had no installation effect before a new attempt."""
        resources = self.config['setupApp']+'/Contents/Resources'
        request = dict(action='preflight', source=self.config['sourceRoot'], store=self.config['storeRoot'],
                       state=self.config['instanceRoot'])
        program = 'RESOURCES='+repr(resources)+'\nREQUEST='+repr(request)+'\nPIN='+repr(self.config['manifestSha256'])+'''
import json,sys
from pathlib import Path
sys.path.insert(0,RESOURCES+'/tooling/scripts/distribution')
sys.path.insert(0,RESOURCES+'/tooling/apps/demo-orchestrator/src')
import setup_bridge as b
v=b.request(json.dumps(REQUEST).encode());p=b.perform(v,PIN)
store=b.Store(v['store'],p['volumeUUID'],volume_probe=b.volume_identity)
for relative in ('versions/'+PIN,'staging/'+PIN,'receipts/'+PIN+'.json'):
 path=store.root/relative
 b.require(not path.exists() and not path.is_symlink(),'INSTALL_CAPACITY_RECOVERY_HAS_EFFECTS')
from aosedge_demo_orchestrator.installed_control import quiescent
quiescent(Path(v['state']),store.root)
bundle=store.plan(Path(v['source']),PIN)
print(json.dumps(dict(installationEffectsAbsent=True,capacityNowSufficient=True,logicalBytes=bundle.total_bytes)))
'''
        return h.parse(self.remote(shlex.quote(resources+'/python/bin/python3.12')+
            " -I -B - <<'SDV_CAPACITY_PREFLIGHT'\n"+program+'\nSDV_CAPACITY_PREFLIGHT',timeout=60))


def installation(media, journal, emit=print, resume_capacity=False):
    """One attempt per action; interruption uses read-only reconciliation."""
    actions = [('media-transfer', media.transfer), ('media-mount', media.mount),
               ('setup-install', lambda reconcile=False: media.setup('install', reconcile)),
               ('setup-prepare', lambda reconcile=False: media.setup('prepare', reconcile))]
    for name, action in actions:
        rows = h.read_attempts(journal.root)
        prior = next((r for r in reversed(rows) if r['command'] == name), None)
        if (resume_capacity and name == 'setup-install' and prior
                and prior['outcome'] == 'UNCERTAIN' and prior.get('code') == 'INSTALL_SPACE_INSUFFICIENT'):
            proof = journal.begin('reconcile-install-capacity-preflight')
            try:
                facts = media.capacity_preflight()
                h.require(facts.get('installationEffectsAbsent') is True and facts.get('capacityNowSufficient') is True,
                          'INSTALL_CAPACITY_RECOVERY_UNCONFIRMED')
            except (OSError, ValueError, subprocess.SubprocessError):
                journal.finish(proof, 'BLOCKED', 'INSTALL_CAPACITY_RECOVERY_UNCONFIRMED')
                return False
            journal.finish(proof, 'PASS', 'INSTALL_CAPACITY_PREFLIGHT_NO_EFFECT', facts)
            prior = None  # Explicit new attempt only after the no-effect proof; retain the original record.
        if prior and prior['outcome'] == 'PASS':
            try:
                if name == 'media-transfer':
                    current = media.file_identity()
                    original = prior['observations'].get('remoteIdentity')
                    if current != original:
                        h.require(isinstance(original,str) and metadata_only_media_change(original,current),
                                  'VERIFIED_MEDIA_CHANGED')
                        proof = journal.begin('media-transfer')
                        facts = media.transfer(reconcile=True)  # Existing file only; never a second copy.
                        journal.finish(proof,'PASS','EXISTING_MEDIA_DIGEST_REVERIFIED',
                                       dict(facts,payloadCopied=False))
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
    parser.add_argument('--dmg', type=Path, required=True,
                        help='Local DMG, or explicit .receipt.json for media already on M1; absent consumer media never falls back')
    parser.add_argument('--remote-dmg', required=True)
    parser.add_argument('--until')
    parser.add_argument('--resume-partial-create', action='store_true')
    parser.add_argument('--resume-capacity-preflight', action='store_true',
                        help='Explicitly resume a proven no-effect installer capacity failure')
    args = parser.parse_args()
    transport, _ = h.configuration(args.config)
    config = j.configuration(args.journey, transport['user'])
    media = media_input(args.dmg, config, args.remote_dmg, transport['user'])
    pin = hashlib.sha256(json.dumps(dict(media=media, journey=j.identity(config, transport)), sort_keys=True).encode()).hexdigest()
    records = Path(config['records']+'-installation')
    probe = h.probe(transport, cloud_domain=j.cloud_scope(config)[0])
    h.require(probe['console'] == transport['user'] and probe['internal'] == 'true', 'TARGET_LOGIN_OR_STORAGE_REQUIRED')
    client = Media(transport, config, media, emit=lambda value: print(value, flush=True))
    allocation = client.allocation()
    receipt = h.parse(media_receipt_path(args.dmg).read_bytes())
    needed = consumer_space_required(receipt, allocation['mediaCached'], allocation['candidatePresent'])
    h.require(probe['memoryBytes'] >= 16*2**30 and probe['freeKiB']*1024 >= needed,
              'TARGET_CAPACITY_REQUIRED')
    if not j.read_records(config, transport):
        h.require(probe['demoProcesses'] == 0 and probe['busyPorts'] == 0, 'EXISTING_RUNTIME_CONFLICT')
    with h.Journal(records, pin) as journal:
        installed = False
        try:
            installed = installation(client, journal, emit=lambda value: print(value, flush=True),
                                     resume_capacity=args.resume_capacity_preflight)
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
