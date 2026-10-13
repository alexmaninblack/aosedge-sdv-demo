# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Fixed release adapters. No executable command is accepted from configuration."""
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import plistlib
import shutil
import signal
import subprocess
import sys
import threading
import time

from release_automation import ROOT, CampaignError, require, safe, private_file, digest


def metadata(path):
    path = safe(path)
    require(path.is_file() and path.stat().st_size < 8*2**20, 'METADATA_UNAVAILABLE')
    return json.loads(path.read_bytes())


def sha(path):
    value=hashlib.sha256()
    with safe(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(2**20),b''):value.update(chunk)
    return value.hexdigest()


def command(argv, *, cwd=ROOT, timeout=60, env=None):
    """Bound an owned process group; keep raw tool output out of release receipts."""
    process = subprocess.Popen(list(map(str, argv)), cwd=cwd, env=env,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    done = threading.Event(); started = time.monotonic()
    def heartbeat():
        while not done.wait(15):
            print(f'    {Path(str(argv[0])).name}: working ({int(time.monotonic()-started)}s)', flush=True)
    thread = threading.Thread(target=heartbeat, daemon=True); thread.start()
    try:
        out, err = process.communicate(timeout=timeout)
    except (subprocess.TimeoutExpired, KeyboardInterrupt):
        # SIGINT lets Python campaign owners execute their ordinary finally/cleanup.
        try:
            os.killpg(process.pid, signal.SIGINT)
        except ProcessLookupError:
            pass
        try:
            process.communicate(timeout=180)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL); process.communicate()
            raise CampaignError('OWNED_COMMAND_CLEANUP_UNCONFIRMED') from None
        raise CampaignError('OWNED_COMMAND_INTERRUPTED') from None
    finally:
        done.set(); thread.join()
    require(len(out)+len(err) < 32*2**20, 'COMMAND_OUTPUT_LIMIT')
    return subprocess.CompletedProcess(argv, process.returncode, out, err)


def git(repo, *args):
    result = command(['/usr/bin/git', '-C', repo, *args], timeout=40)
    require(result.returncode == 0, 'GIT_OPERATION_FAILED')
    return result.stdout.decode().strip()


class Owners:
    def __init__(self, selected):
        self.config = selected
        self.workspace = safe(selected['workspace'])
        self.gateway = safe(selected['gateway'])
        self.candidate = safe(selected['candidate']['directory'])
        self.root = self.workspace / 'build/release-campaign' / selected['version']

    @contextmanager
    def global_lease(self, parent):
        fd = os.open(safe(parent)/'.global-lease', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        try:
            private_file(parent/'.global-lease')
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise CampaignError('ANOTHER_RELEASE_ACTIVE') from None
            yield
        finally:
            os.close(fd)

    def binding(self, *, allow_readonly_restart=False):
        self.storage()
        require(not git(ROOT, 'status', '--porcelain') and
                not git(self.gateway, 'status', '--porcelain'), 'DIRTY_CANDIDATE_SOURCE')
        current = dict(schemaVersion=1, configSha256=digest(self.config),
            source=dict(integration=git(ROOT,'rev-parse','HEAD'), gateway=git(self.gateway,'rev-parse','HEAD')),
            executorSha256=digest({p:sha(ROOT/'scripts'/p) for p in
                ('release-campaign','release_automation.py','release_owners.py',
                 'release_publication.py','release_operator_proof.py')}))
        marker=self.root/'identity.json'
        if marker.exists() and not allow_readonly_restart:
            from release_automation import read
            before=read(marker)
            if current != before:
                amendment=self.root/'operator-amendment.json'
                if amendment.exists():
                    accepted=read(amendment)
                    require(accepted['oldBinding']==before and accepted['newBinding']==current,
                            'AMENDED_SOURCE_CHANGED')
                    return before
                intent=read(self.root/'operator-intent.json')
                require(current['configSha256']==before['configSha256'] and
                    current['executorSha256']==before['executorSha256'] and
                    current['source']['gateway']==before['source']['gateway'] and
                    current['source']['integration']==intent['target'] and
                    before['source']['integration']==intent['base'], 'CAMPAIGN_REBINDING_FORBIDDEN')
                return before
        return current

    def storage(self):
        require(self.workspace.is_dir() and self.workspace.is_relative_to(Path('/Volumes'))
                and len(self.workspace.parts) >= 4, 'SELECTED_SSD_UNAVAILABLE')
        from reproduction.core import native_mountpoint
        mount = Path(native_mountpoint(self.workspace))
        probe = command(['/usr/sbin/diskutil','info','-plist',mount])
        require(probe.returncode == 0, 'STORAGE_IDENTITY_UNAVAILABLE')
        info = plistlib.loads(probe.stdout)
        require(info.get('VolumeUUID') == self.config['volumeUUID'] and
                info.get('FilesystemType') == 'apfs' and info.get('Internal') is False,
                'SELECTED_SSD_IDENTITY_CHANGED')
        require(self.candidate.is_relative_to(self.workspace) and
                self.candidate.stat().st_dev == self.workspace.stat().st_dev,
                'CANDIDATE_OUTSIDE_SELECTED_STORAGE')
        free = shutil.disk_usage(self.workspace).free
        require(free >= 60*2**30, 'SSD_RESERVE_UNAVAILABLE')
        return dict(volumeUUID=info['VolumeUUID'], freeGiB=round(free/2**30,1))

    def remote(self):
        sys.path.insert(0,str(ROOT/'scripts/qualification'))
        import remote_harness as h
        transport, _ = h.configuration(Path(self.config['remoteConfig']))
        facts = h.probe(transport)
        require(facts['internal'] == 'true' and facts['stagingHttp'] in (200,301,302,303,307,308),
                'M1_INTERNAL_STORAGE_OR_STAGING_UNAVAILABLE')
        return {k:facts[k] for k in ('arch','os','console','freeKiB','demoProcesses','busyPorts')}

    def product(self):
        sys.path.insert(0,str(ROOT/'scripts/distribution'))
        from application import export_plan
        from developer_inputs import DeveloperInputs
        app = metadata(self.candidate/'Runtime Kit/application-manifest.json')
        seal = app['packagingCheckpoint']
        require(seal['kind'] == 'developer-build-results', 'CANDIDATE_PROVENANCE_UNSUPPORTED')
        checkpoint = DeveloperInputs.load(self.candidate/'builds/developer-seals'/
            (seal['sha256']+'.json'), seal['sha256'])
        exported = export_plan(ROOT, checkpoint)
        rows = app['applicationFiles']
        require(set(exported) == {r['path'] for r in rows} and
                len(exported) == len(rows), 'APPLICATION_SOURCE_INVENTORY_CHANGED')
        require(all(hashlib.sha256(exported[r['path']]).hexdigest() == r['sha256'] and
                    len(exported[r['path']]) == r['bytes'] for r in rows),
                'APPLICATION_PRODUCT_BYTES_CHANGED')
        ui = metadata(self.candidate/'ui-build/build-receipt.json')
        require(ui.get('sourcesUnchanged') is True and
                all(sha(Path(p)) == expected for p,expected in ui['inputHashes'].items()),
                'UI_BUILD_INPUTS_CHANGED')
        return dict(applicationFiles=len(rows), uiInputs=len(ui['inputHashes']),
                    applicationManifestSha256=sha(self.candidate/'Runtime Kit/application-manifest.json'),
                    reuse='PRODUCT_INPUT_EQUIVALENCE_PROVEN')

    def freeze(self):
        return dict(storage=self.storage(), m1=self.remote(), product=self.product(),
                    source=dict(integration=git(ROOT,'rev-parse','HEAD'),gateway=git(self.gateway,'rev-parse','HEAD')))

    def source_gates(self):
        sys.path.insert(0,str(ROOT/'scripts/distribution'))
        from build_scratch import directory
        gates = [
            ('docs',[sys.executable,'-B','scripts/docs-check']),
            ('launcher-pins',[sys.executable,'-B','scripts/sync-launcher-pins','--check']),
            ('regression',[sys.executable,'-B','-m','unittest','tests.test_release_automation','tests.test_release_projection','tests.test_native_source_selection',
                'tests.test_unified_launcher','tests.test_drive_download_parser','tests.test_release_operator_amendment','tests.test_prepare_macos','tests.test_developer_catalog',
                'tests.test_developer_workflow','tests.test_developer_progress','tests.test_reader_routes',
                'tests.test_reproduction_chain','tests.test_reproduction_recipes','tests.test_reproduction_host',
                'tests.test_reproduction_delivery']),
            ('presenter-owner',[sys.executable,'-B','-m','unittest','discover','-s',
                'apps/demo-orchestrator/tests','-p','test_presenter*.py']),
            ('native-identifiers',[sys.executable,'-B',str(self.gateway/'tests/native_accessibility_test.py')]),
            ('web-types',['/opt/homebrew/bin/node','node_modules/typescript/bin/tsc','--noEmit']),
            ('web-units',['/opt/homebrew/bin/node','node_modules/vitest/vitest.mjs','run']),
        ]
        results = []
        with directory(self.workspace) as scratch:
            env = dict(os.environ, TMPDIR=str(scratch), PYTHONDONTWRITEBYTECODE='1',
                       PYTHONPATH=os.pathsep.join(map(str,(ROOT/'tests',ROOT/'scripts',
                            ROOT/'apps/demo-orchestrator/src'))))
            for name, argv in gates:
                print('    Checking '+name,flush=True)
                cwd = ROOT/'apps/presenter-ui' if name.startswith('web-') else ROOT
                start=time.monotonic(); result=command(argv,cwd=cwd,timeout=600,env=env)
                require(result.returncode == 0, 'SOURCE_GATE_'+name.upper().replace('-','_')+'_FAILED')
                results.append(dict(gate=name,seconds=round(time.monotonic()-start,3),outcome='PASS'))
        require(not git(ROOT,'status','--porcelain'),'SOURCE_GATES_CHANGED_WORKTREE')
        return dict(gates=results,source=dict(integration=git(ROOT,'rev-parse','HEAD'),
                    gateway=git(self.gateway,'rev-parse','HEAD')))

    def artifact(self):
        product = self.product()
        files = list(self.candidate.glob('*.dmg'))
        require(len(files) == 1, 'EXACT_CANDIDATE_MEDIA_REQUIRED')
        media=files[0]; receipt=metadata(media.with_suffix('.receipt.json'))
        require(receipt.get('dmgSha256') == self.config['candidate']['dmgSha256'] and
                receipt.get('manifestSha256') == self.config['candidate']['manifestSha256'] and
                receipt.get('dmgBytes') == media.stat().st_size and
                    product['applicationManifestSha256'] == receipt['manifestSha256'], 'ARTIFACT_RECEIPT_MISMATCH')
        from release_automation import read,atomic
        cache=self.root/'artifact-verification.json';identity=self.identity(media)
        verified=dict(identity=identity,sha256=receipt['dmgSha256'])
        if cache.exists():
            require(read(cache)==verified,'ARTIFACT_IDENTITY_CHANGED')
        else:
            print('    Verifying retained '+media.name+' at release freeze',flush=True)
            require(sha(media)==receipt['dmgSha256'] and self.identity(media)==identity,
                    'ARTIFACT_BYTES_CHANGED')
            atomic(cache,verified)
        return dict(product=product, dmgSha256=receipt['dmgSha256'],
                    manifestSha256=receipt['manifestSha256'], bytes=receipt['dmgBytes'],
                    identity=identity, assembly='RETAINED_CHECKED_MEDIA')

    @staticmethod
    def identity(path):
        info=safe(path).stat()
        require(info.st_nlink == 1, 'LINKED_ARTIFACT_FORBIDDEN')
        return [info.st_dev,info.st_ino,info.st_size,info.st_mtime_ns,info.st_ctime_ns]

    def qualification(self):
        self.product()
        selected=self.config['evidence']
        campaign=metadata(selected['campaign']); browser=metadata(selected['browser']); closure=metadata(selected['closure'])
        require(campaign.get('outcome') == 'PASS' and campaign.get('cleanupConfirmed') is True and
                campaign.get('candidate') == self.config['candidate']['manifestSha256'],
                'RETAINED_CAMPAIGN_NOT_APPLICABLE')
        require(len(browser['stages']) == 42 and all(r['outcome'] == 'PASS' for r in browser['stages']),
                'RETAINED_UI_MATRIX_INCOMPLETE')
        require(all(closure.get(k) == 0 for k in
                ('ownedDemoProcesses','ownedDemoListeners','ownedQualificationClients')) and
                closure.get('dataPreserved') is True and closure.get('displayAssertionClosed') is True and
                closure.get('readTransportClosed') is True, 'RETAINED_CLEANUP_UNCONFIRMED')
        sys.path.insert(0,str(ROOT/'scripts/qualification'))
        import continuous_ui_campaign as continuous
        import native_controls_campaign as common
        pin=hashlib.sha256(Path(continuous.__file__).read_bytes()+common.source_pin().encode()).hexdigest()
        require(pin == selected['sourcePin'], 'QUALIFICATION_SCENARIO_CHANGED')
        now=self.remote()
        require(now['demoProcesses'] == 0 and now['busyPorts'] == 0, 'M1_NOT_QUIESCENT')
        return dict(outcome='PASS', evidence='REUSED_EXACT_PRODUCT_AND_SCENARIO', browserStages=42,
            candidate=campaign['candidate'], test=campaign['test'], currentOwnersClosed=True,
            evidenceDigests={k:sha(Path(selected[k])) for k in ('campaign','browser','closure')},
            firstUse='NOT_RUN', fullE2E='NOT_COMPLETE')

    def stage(self, name):
        methods={'freeze':self.freeze,'source-gates':self.source_gates,
                 'artifact':self.artifact,'qualification':self.qualification}
        if name in methods:
            return methods[name]()
        from release_publication import stage
        return stage(self,name)

    def verify_saved(self, name, facts):
        self.storage(); self.product()
        if name == 'artifact':
            require(self.artifact()['identity'] == facts['identity'], 'RETAINED_MEDIA_CHANGED')
        if name == 'qualification':
            require(self.qualification()['evidenceDigests'] == facts['evidenceDigests'], 'EVIDENCE_CHANGED')
        if name in ('main-integration','publication','operator-promotion'):
            from release_publication import verify_saved
            verify_saved(self,name,facts)

    def reconcile(self, name, previous):
        from release_publication import reconcile
        return reconcile(self,name,previous)
