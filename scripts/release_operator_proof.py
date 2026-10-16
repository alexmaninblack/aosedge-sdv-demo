# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Anonymous A consumer on M1, ordinary Setup owners, then catalog promotion."""
import hashlib
from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
import shlex
import sys
from uuid import uuid4

from release_automation import ROOT, atomic, read, require
from release_owners import command, git, sha
from release_publication import descriptor, remote_main


def project(owner, published):
    """Project the current descriptor; immutable releases remain in receipts/Git."""
    expected=descriptor(owner)
    relative='workspace/releases/delivery.json'
    path=ROOT/relative
    raw=(json.dumps(expected,indent=2)+'\n').encode()
    catalog=json.loads((ROOT/'workspace/launcher-catalog.json').read_bytes())
    if path.exists() and path.read_bytes()!=raw:
        try:previous=json.loads(path.read_bytes())
        except (ValueError, OSError):require(False,'IMMUTABLE_DESCRIPTOR_COLLISION')
        require(catalog.get('operatorDescriptor')==relative and
                all(catalog['operator'].get(k)==previous.get(k) for k in
                    ('productVersion','status','file','bytes','sha256','manifestSha256','notarized')),
                'CURRENT_DESCRIPTOR_SELECTION_CHANGED')
        require(previous['productVersion']!=expected['productVersion'],'IMMUTABLE_DESCRIPTOR_COLLISION')
    catalog['catalogRevision']+=1;catalog['operatorDescriptor']=relative
    for key in ('productVersion','status','file','bytes','sha256','manifestSha256','notarized'):
        catalog['operator'][key]=expected[key]
    if published.get('provider')=='dropbox':
        from reproduction.dropbox_public import public_link
        catalog['operator']['downloadURL']=public_link(published['downloadURL'])
    else:
        catalog['operator']['downloadURL']='https://drive.google.com/uc?export=download&id='+published['fileId']
    return relative,raw,(json.dumps(catalog,indent=2)+'\n').encode()


def candidate_source(owner, published):
    intent_path=owner.root/'operator-intent.json'
    if intent_path.exists():
        intent=read(intent_path)
        require(intent.get('target') and git(ROOT,'rev-parse','HEAD')==intent['target'],
                'OPERATOR_COMMIT_RECONCILIATION_REQUIRED')
        require(sha(ROOT/'scripts/aosedge-sdv-lab.sh')==intent['launcherSha256'],
                'OPERATOR_LAUNCHER_CHANGED')
        return intent
    require(not git(ROOT,'status','--porcelain'),'CATALOG_WORKTREE_NOT_CLEAN')
    base=git(ROOT,'rev-parse','HEAD');require(remote_main(ROOT)==base,'MAIN_CHANGED_BEFORE_CATALOG')
    relative,raw,catalog=project(owner,published)
    paths=[relative,'workspace/launcher-catalog.json','scripts/launcher/common-macos.sh',
           'scripts/launcher/install-macos.sh','scripts/launcher/heavy-macos.sh','scripts/aosedge-sdv-lab.sh']
    intent=dict(base=base,target=None,paths=paths,launcherSha256=None)
    atomic(intent_path,intent)
    # This is mechanical projection from checked immutable delivery metadata.
    (ROOT/relative).write_bytes(raw);(ROOT/'workspace/launcher-catalog.json').write_bytes(catalog)
    result=command([sys.executable,'-B','scripts/sync-launcher-pins','--write'])
    require(result.returncode==0,'CATALOG_PROJECTION_FAILED')
    result=command([sys.executable,'-B','scripts/docs-check'])
    require(result.returncode==0,'CATALOG_DOCUMENTATION_GATE_FAILED')
    result=command([sys.executable,'-B','-m','unittest','tests.test_unified_launcher',
                    'tests.test_drive_download_parser','tests.test_dropbox_download_parser','tests.test_dropbox_public'],timeout=300)
    require(result.returncode==0,'CATALOG_LAUNCHER_GATE_FAILED')
    git(ROOT,'add','--',*paths)
    git(ROOT,'commit','-m','Prepare checked public Presenter preview for option A')
    intent['target']=git(ROOT,'rev-parse','HEAD');intent['launcherSha256']=sha(ROOT/'scripts/aosedge-sdv-lab.sh')
    atomic(intent_path,intent)
    git(ROOT,'push','origin','HEAD:refs/heads/codex/release-'+owner.config['version'])
    return intent


def connection(owner):
    sys.path.insert(0,str(ROOT/'scripts/qualification'))
    import remote_harness as h
    import journey as j
    transport,_=h.configuration(Path(owner.config['remoteConfig']))
    config=j.configuration(Path(owner.config['operatorJourney']),transport['user'])
    require(config['manifestSha256']==owner.config['candidate']['manifestSha256'],'OPERATOR_PACKAGE_BINDING_CHANGED')
    return h,j,transport,config


@contextmanager
def display_guard(owner):
    """Temporary assertion only; never unlock a desktop or change OS policy."""
    h,j,t,c=connection(owner)
    suffix=git(ROOT,'rev-parse','HEAD')[:12]
    record='/Users/'+t['user']+'/SDV-Qualification/release-display-'+suffix+'.json'
    python=c['packageRoot']+'/demo-artifacts/aosedge-sdv-demo/host-runtime/python/bin/python3.12'
    def action(name):
        program='ACTION='+repr(name)+'\nRECORD='+repr(record)+'''
import json,os,pathlib,stat,subprocess,time,signal
p=pathlib.Path(RECORD)
assert not any(q.is_symlink() for q in (p,*p.parents)),'DISPLAY_ASSERTION_LINKED'
def stamp(pid):
 r=subprocess.run(['/bin/ps','-p',str(pid),'-o','lstart=,command='],capture_output=True,text=True,timeout=5)
 return r.stdout.strip() if r.returncode==0 else None
def saved():
 info=p.lstat()
 assert stat.S_ISREG(info.st_mode) and info.st_nlink==1 and info.st_uid==os.getuid() and stat.S_IMODE(info.st_mode)==0o600,'DISPLAY_ASSERTION_RECORD_CHANGED'
 return json.loads(p.read_bytes())
if ACTION=='start':
 if p.exists():assert stamp(saved()['pid']) is None,'DISPLAY_ASSERTION_ALREADY_ACTIVE'
 task=subprocess.Popen(['/usr/bin/caffeinate','-d','-i','-u','-t','7200'],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 value=dict(pid=task.pid,stamp=stamp(task.pid))
 assert value['stamp'] and '/usr/bin/caffeinate -d -i -u -t 7200' in value['stamp'],'DISPLAY_ASSERTION_OWNER_UNCONFIRMED'
 fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_NOFOLLOW|os.O_TRUNC,0o600)
 os.write(fd,json.dumps(value).encode());os.fsync(fd);os.close(fd)
else:
 value=saved();current=stamp(value['pid'])
 if current:
  assert current==value['stamp'],'DISPLAY_ASSERTION_OWNER_CHANGED'
  os.kill(value['pid'],signal.SIGTERM)
  deadline=time.monotonic()+5
  while stamp(value['pid']) and time.monotonic()<deadline:time.sleep(.1)
  assert stamp(value['pid']) is None,'DISPLAY_ASSERTION_CLOSE_UNCONFIRMED'
print(json.dumps(dict(displayAssertion='OWNED_TEMPORARY' if ACTION=='start' else 'CLOSED')))
'''
        return h.parse(h.remote(t,shlex.quote(python)+" -I -B - <<'RELEASE_DISPLAY_ASSERTION'\n"+
                        program+'\nRELEASE_DISPLAY_ASSERTION',timeout=20))
    action('start')
    try:yield
    finally:
        result=action('close')
        if owner.root.exists():atomic(owner.root/'display-closure.json',result)


def consumer_preflight(owner):
    """Read-only target check, usable before source gates or payload transfer."""
    h,j,transport,config=connection(owner)
    first_use=owner.first_use()
    test=None if first_use else read(Path(owner.config['evidence']['campaign']))['test']
    # Exact current desktop/read-only owner check before a costly consumer download.
    request=dict(config=config,kind='observe',args={},phase='observe',requestId=str(uuid4()),expectedRun=test)
    program=j.WORKER.read_text()+'\nREQUEST='+repr(request)+'''
with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
 worker=Worker(REQUEST)
 with worker.imports():
  worker.binding(allow_empty=REQUEST['expectedRun'] is None);closed=wait_for_exit(timeout=1);engine=docker_info()
  require(engine is not None and engine['runningContainers']==0,'IDLE_SHARED_DOCKER_REQUIRED')
  from aosedge_demo_orchestrator.host_runtime import selected
  runtime=selected(worker.state)
  screen=subprocess.run([str(runtime.entry('presenter')),'screen'],capture_output=True,text=True,timeout=5)
  require(screen.returncode==0 and json.loads(screen.stdout).get('desktopState')=='UNLOCKED','TARGET_DESKTOP_NOT_UNLOCKED')
print(json.dumps(dict(ownersClosed=True,desktopState='UNLOCKED',dockerEngineId=engine['engineId'])))
'''
    python=config['packageRoot']+'/demo-artifacts/aosedge-sdv-demo/host-runtime/python/bin/python3.12'
    def run(program,timeout=60,python=python):
        return h.remote(transport,shlex.quote(python)+" -I -B - <<'SDV_OPERATOR_PROOF'\n"+
                        program+'\nSDV_OPERATOR_PROOF\n',timeout=timeout)
    return h.parse(run(program))


def consumer(owner, intent):
    h,j,transport,config=connection(owner)
    from campaign import Media
    from release_automation import CampaignError
    test=read(owner.root/'qualification.json')['facts']['test']
    remote=j.Remote(transport,config)
    consumer_preflight(owner)
    python=config['packageRoot']+'/demo-artifacts/aosedge-sdv-demo/host-runtime/python/bin/python3.12'
    def run(program,timeout=60,python=python):
        return h.remote(transport,shlex.quote(python)+" -I -B - <<'SDV_OPERATOR_PROOF'\n"+
                        program+'\nSDV_OPERATOR_PROOF\n',timeout=timeout)
    attempt=intent.get('consumerAttempt',1)
    require(type(attempt) is int and 1<=attempt<=9,'CONSUMER_ATTEMPT_INVALID')
    parent='/Users/'+transport['user']+'/SDV-Qualification/operator-'+owner.config['version']
    if owner.config['delivery'].get('provider')=='dropbox':parent+='-dropbox'
    if attempt>1:parent+='-attempt-'+str(attempt)
    dmg=parent+'/sdv/cache/'+descriptor(owner)['file']
    # A previous verified transfer is expendable, not the installed package or
    # Test. Reclaim only that exact same-byte, unmounted, idle media when needed.
    prior=read(Path(owner.config['operatorJourney']).parent/'campaign-plan.json')
    from campaign import media_input
    previous=media_input(next(owner.candidate.glob('*.dmg')),config,prior['remoteDmg'],transport['user'])
    capacity='OLD='+repr(previous)+'\nNEW='+repr(dmg)+'''
import hashlib,json,os,pathlib,plistlib,shutil,stat,subprocess
reserve=90*2**30+OLD['bytes']+2**30
deleted=False
if shutil.disk_usage(pathlib.Path.home()).free < reserve:
 path=pathlib.Path(OLD['remotePath'])
 assert str(path)!=NEW and path.suffix=='.dmg' and path.exists(),'OPERATOR_TARGET_CAPACITY_REQUIRED'
 assert not any(p.is_symlink() for p in (path,*path.parents)),'OLD_MEDIA_LINKED'
 before=path.stat()
 assert stat.S_ISREG(before.st_mode) and before.st_uid==os.getuid() and before.st_nlink==1 and before.st_size==OLD['bytes'],'OLD_MEDIA_IDENTITY_CHANGED'
 images=plistlib.loads(subprocess.check_output(['/usr/bin/hdiutil','info','-plist']))['images']
 assert not any(image.get('image-path')==str(path) for image in images),'OLD_MEDIA_STILL_MOUNTED'
 handles=subprocess.run(['/usr/sbin/lsof','-t','--',str(path)],capture_output=True,text=True,timeout=10)
 assert handles.returncode==1 and not handles.stdout and not handles.stderr,'OLD_MEDIA_HANDLES_UNCONFIRMED'
 digest=hashlib.sha256()
 with path.open('rb') as stream:
  for chunk in iter(lambda:stream.read(2**20),b''):digest.update(chunk)
 assert digest.hexdigest()==OLD['sha256'] and path.stat()==before,'OLD_MEDIA_BYTES_CHANGED'
 subprocess.run(['/bin/rm','--',str(path)],check=True,timeout=10)
 deleted=True
assert shutil.disk_usage(pathlib.Path.home()).free>=reserve,'OPERATOR_TARGET_CAPACITY_REQUIRED'
print(json.dumps(dict(oldTransferRemoved=deleted,bytesReclaimed=OLD['bytes'] if deleted else 0)))
'''
    reclaimed=h.parse(run(capacity,timeout=180))
    marker=owner.root/'consumer-launcher.intent.json'
    if marker.exists():
        # Never repeat an uncertain graphical handoff. Read its persisted output,
        # file and actual mounted signed Setup; recovery is observation only.
        raise CampaignError('OPERATOR_CONSUMER_RECONCILIATION_REQUIRED')
    atomic(marker,dict(launcherSha256=intent['launcherSha256'],source=intent['target'],remoteDmg=dmg))
    launcher=parent+'/aosedge-sdv-lab.sh'
    url='https://raw.githubusercontent.com/alexmaninblack/aosedge-sdv-demo/'+intent['target']+'/scripts/aosedge-sdv-lab.sh'
    script='set -eu\numask 077\n'
    script+='test ! -e '+shlex.quote(parent)+'\nmkdir -m 700 '+shlex.quote(parent)+'\n'
    script+='/usr/bin/curl --disable --fail --proto "=https" --tlsv1.2 --connect-timeout 15 --max-time 60 --silent --show-error -o '+shlex.quote(launcher)+' '+shlex.quote(url)+'\n'
    script+='test "$(/usr/bin/shasum -a 256 '+shlex.quote(launcher)+' | /usr/bin/awk \'{print $1}\')" = '+intent['launcherSha256']+'\n'
    script+='printf "yes\\n" | /bin/bash '+shlex.quote(launcher)+' --route A --parent '+shlex.quote(parent)+' --state-dir '+shlex.quote(parent+'/launcher-state')+'\n'
    mounted=False;opened=False;setup_path=None;failure=None;facts={}
    try:
        print('    M1 anonymous A download → checksum/signature → visible Setup',flush=True)
        with j.Progress('anonymous-operator-download',emit=lambda value:print(value,flush=True)):
            output=h.remote(transport,script,timeout=1900)
        require('SETUP HANDOFF REQUESTED' in output,'OPERATOR_HANDOFF_UNCONFIRMED')
        inspect='import plistlib,subprocess,json\nDMG='+repr(dmg)+'''
images=plistlib.loads(subprocess.check_output(['/usr/bin/hdiutil','info','-plist']))['images']
matches=[row['mount-point'] for image in images if image.get('image-path')==DMG for row in image['system-entities'] if row.get('mount-point')]
assert len(matches)==1,'OPERATOR_MEDIA_MOUNT_UNCONFIRMED'
print(json.dumps(dict(mount=matches[0])))
'''
        mount=h.parse(run(inspect))['mount'];mounted=True
        setup_path=mount+'/AosEdge SDV Lab Setup.app'
        config=dict(config,setupApp=setup_path,sourceRoot=mount+'/Runtime Kit')
        media=Media(transport,config,dict(remotePath=dmg),emit=lambda value:print(value,flush=True))
        # Launcher itself performed full consumer SHA and codesign verification.
        # Bind to the exact signed executable and installed manifest again here.
        media.mount(reconcile=True)
        installed=media.setup('install');prepared=media.setup('prepare')
        resources=setup_path+'/Contents/Resources'
        launch='RESOURCES='+repr(resources)+'\nSTATE='+repr(config['instanceRoot'])+'''
import json,sys
sys.path.insert(0,RESOURCES+'/tooling/scripts/distribution')
sys.path.insert(0,RESOURCES+'/tooling/apps/demo-orchestrator/src')
import setup_bridge as b
value=b.perform(b.request(json.dumps(dict(action='launch',state=STATE)).encode()),b.release()['manifestSha256'])
print(json.dumps(value))
'''
        opened=True
        opened_facts=h.parse(run(launch,timeout=150,python=resources+'/python/bin/python3.12'))
        require(opened_facts.get('presenterObserved') is True,'OPERATOR_PRESENTER_NOT_OBSERVED')
        facts=dict(anonymousDownload=True,checksumAndSignature=True,setupHandoff=True,
            installed=True,installedReused=installed.get('reused'),presenterObserved=True,
            testPreserved=test,nativeSetupClicks='NOT_RUN',cleanFirstUse='NOT_RUN',
            fullE2E='NOT_COMPLETE',enginePolicy='PRESERVED',launcherSha256=intent['launcherSha256'])
        facts['mediaCleanup']=reclaimed
    except BaseException as error:failure=error
    finally:
        try:
            if not mounted:
                # A lost handoff response may still have opened the signed app.
                # Observe that exact image before any cleanup, never rerun A.
                inspect='import plistlib,subprocess,json\nDMG='+repr(dmg)+'''
images=plistlib.loads(subprocess.check_output(['/usr/bin/hdiutil','info','-plist']))['images']
matches=[row['mount-point'] for image in images if image.get('image-path')==DMG for row in image['system-entities'] if row.get('mount-point')]
assert len(matches)<=1,'OPERATOR_MEDIA_AMBIGUOUS'
print(json.dumps(dict(mount=matches[0] if matches else None)))
'''
                mount=h.parse(run(inspect))['mount']
                if mount:
                    mounted=True;setup_path=mount+'/AosEdge SDV Lab Setup.app'
            if opened:
                closed=j.Remote(transport,config)(dict(id='operator-close',kind='shutdown',timeout=90),
                        'execute',dict(runId=test),str(uuid4()))
                require(closed['outcome']=='PASS','OPERATOR_OWNER_CLOSE_UNCONFIRMED')
            if setup_path:
                q=shlex.quote
                quit_script='APP='+repr(setup_path)+'''
import json,subprocess,time
def owned():
 return [row for row in subprocess.check_output(['/bin/ps','-axo','comm='],text=True).splitlines() if row.startswith(APP+'/Contents/MacOS/')]
if owned():
 subprocess.run(['/usr/bin/osascript','-e','tell application "'+APP+'" to quit'],check=True,timeout=10)
 deadline=time.monotonic()+10
 while owned() and time.monotonic()<deadline:time.sleep(.1)
assert not owned(),'OPERATOR_SETUP_CLOSE_UNCONFIRMED'
print(json.dumps(dict(setupClosed=True)))
'''
                h.parse(run(quit_script))
            if mounted:
                h.remote(transport,'/usr/bin/hdiutil detach '+shlex.quote(str(Path(setup_path).parent))+' >/dev/null',timeout=30)
            now=owner.remote()
            require(now['demoProcesses']==0 and now['busyPorts']==0,'OPERATOR_FINAL_OWNERS_NOT_CLOSED')
            facts['cleanupConfirmed']=True
        except BaseException as cleanup_error:failure=cleanup_error
        atomic(owner.root/'consumer-result.json',dict(outcome='PASS' if failure is None else 'BLOCKED',facts=facts))
    if failure is not None:raise failure
    return facts


def promote(owner):
    published=read(owner.root/'publication.json')['facts']
    intent=candidate_source(owner,published)
    proof=owner.root/'consumer-result.json'
    if proof.exists():
        saved=read(proof);require(saved['outcome']=='PASS','OPERATOR_CONSUMER_RECONCILIATION_REQUIRED')
        facts=saved['facts'];require(facts.get('cleanupConfirmed') and
            facts.get('launcherSha256')==intent['launcherSha256'],'OPERATOR_PROOF_CHANGED')
    else:facts=consumer(owner,intent)
    require(remote_main(ROOT) in (intent['base'],intent['target']),'MAIN_CHANGED_BEFORE_PROMOTION')
    if remote_main(ROOT)!=intent['target']:
        git(ROOT,'push','origin',intent['target']+':refs/heads/main')
    require(remote_main(ROOT)==intent['target'],'OPERATOR_PROMOTION_UNCONFIRMED')
    tag='sdv-lab-v'+owner.config['version']
    refs=git(ROOT,'ls-remote','origin','refs/tags/'+tag,'refs/tags/'+tag+'^{}').splitlines()
    if not refs:
        require(not git(ROOT,'tag','--list',tag),'LOCAL_RELEASE_TAG_COLLISION')
        git(ROOT,'tag','-a',tag,intent['target'],'-m',
            'Engineering preview; M1 A consumer checked. Gateway '+git(owner.gateway,'rev-parse','HEAD'))
        git(ROOT,'push','origin','refs/tags/'+tag)
    refs=git(ROOT,'ls-remote','origin','refs/tags/'+tag+'^{}').splitlines()
    require(len(refs)==1 and refs[0].split()[0]==intent['target'],'RELEASE_TAG_UNCONFIRMED')
    return dict(main=intent['target'],tag=tag,consumer=facts,launcherSha256=intent['launcherSha256'])


def verify_saved(owner,facts):
    require(remote_main(ROOT)==facts['main'] and sha(ROOT/'scripts/aosedge-sdv-lab.sh')==facts['launcherSha256'],
            'OPERATOR_MAIN_OR_LAUNCHER_CHANGED')
    now=owner.remote();require(now['demoProcesses']==0 and now['busyPorts']==0,'OPERATOR_OWNERS_NOT_CLOSED')


def reconcile(owner,previous):
    amendment=owner.root/'operator-amendment.json'
    if amendment.exists() and not (owner.root/'consumer-launcher.intent.json').exists():
        value=read(amendment)
        prove_no_handoff(owner,value['failedConsumerIntent'])
        return True
    path=owner.root/'consumer-result.json'
    if not path.exists():return False
    return read(path).get('outcome')=='PASS' and read(path)['facts'].get('cleanupConfirmed') is True


AMEND_PATHS=frozenset(('scripts/launcher/drive-download-macos.pl','scripts/launcher/install-macos.sh',
    'scripts/aosedge-sdv-lab.sh','scripts/launcher/common-macos.sh','scripts/launcher/heavy-macos.sh',
    'scripts/release_automation.py','scripts/release_owners.py','scripts/release_operator_proof.py',
    'tests/test_drive_download_parser.py','tests/test_unified_launcher.py',
    'tests/test_release_automation.py','tests/test_release_operator_amendment.py',
    'docs/development/release-campaign.md'))


def allowed_amendment(paths,projection_paths):
    require(bool(paths) and set(paths)<=AMEND_PATHS|set(projection_paths),'OPERATOR_AMEND_SCOPE_INVALID')


def prove_no_handoff(owner,failed):
    """Absence of any media bytes + no mounted image/owners is affirmative evidence."""
    h,j,t,c=connection(owner)
    path=Path(failed['remoteDmg'])
    parent=Path('/Users')/t['user']/'SDV-Qualification'
    require(path.is_relative_to(parent) and path.suffix=='.dmg' and '..' not in path.parts,
            'FAILED_CONSUMER_SCOPE_INVALID')
    script='DMG='+repr(str(path))+'''
import json,pathlib,plistlib,subprocess
p=pathlib.Path(DMG)
assert not any(q.is_symlink() for q in (p,*p.parents)),'FAILED_CONSUMER_LINKED'
assert not p.exists() and not pathlib.Path(DMG+'.part').exists(),'CONSUMER_BYTES_OR_HANDOFF_UNCERTAIN'
images=plistlib.loads(subprocess.check_output(['/usr/bin/hdiutil','info','-plist']))['images']
assert not any(i.get('image-path')==DMG for i in images),'CONSUMER_MEDIA_STILL_ATTACHED'
print(json.dumps(dict(noMediaBytes=True,noMountedImage=True)))
'''
    python=c['packageRoot']+'/demo-artifacts/aosedge-sdv-demo/host-runtime/python/bin/python3.12'
    facts=h.parse(h.remote(t,shlex.quote(python)+" -I -B - <<'NO_HANDOFF_PROOF'\n"+script+'\nNO_HANDOFF_PROOF',timeout=20))
    now=owner.remote();require(now['demoProcesses']==0 and now['busyPorts']==0,'FAILED_CONSUMER_OWNERS_NOT_CLOSED')
    return dict(facts,ownersClosed=True)


def amend(owner):
    """Re-gate an operator-only correction; confirmed publication is never repeated."""
    fd=os.open(owner.root/'.lease',os.O_RDWR|os.O_NOFOLLOW)
    try:
        try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise RuntimeError('RELEASE_ALREADY_ACTIVE') from None
        old=read(owner.root/'identity.json')
        require(all(read(owner.root/(name+'.json'))['outcome']=='PASS' for name in
                ('freeze','source-gates','artifact','qualification','main-integration','publication')),
                'AMEND_REQUIRES_CONFIRMED_PUBLICATION')
        failed=read(owner.root/'consumer-result.json')
        require(failed['outcome']=='BLOCKED' and failed['facts'].get('cleanupConfirmed') is True,
                'AMEND_REQUIRES_CLOSED_FAILED_CONSUMER')
        intent=read(owner.root/'operator-intent.json')
        previous_attempt=intent.get('consumerAttempt',1)
        require(type(previous_attempt) is int and 1<=previous_attempt<9,'CONSUMER_ATTEMPTS_EXHAUSTED')
        require(remote_main(ROOT)==intent['base'],'MAIN_CHANGED_BEFORE_AMENDMENT')
        current=owner.binding(allow_readonly_restart=True)
        require(current['configSha256']==old['configSha256'] and
            current['source']['gateway']==old['source']['gateway'],'AMEND_SELECTION_CHANGED')
        paths=git(ROOT,'diff','--name-only',old['source']['integration'],current['source']['integration']).splitlines()
        allowed_amendment(paths,intent['paths'])
        failed_intent=read(owner.root/'consumer-launcher.intent.json')
        observed=prove_no_handoff(owner,failed_intent)
        owner.product();owner.artifact()
        from release_publication import verify_saved
        verify_saved(owner,'publication',read(owner.root/'publication.json')['facts'])
        print('    Re-gating operator-only tooling correction; published media retained',flush=True)
        gates=owner.source_gates()
        require(owner.binding(allow_readonly_restart=True)==current,'AMENDED_SOURCE_CHANGED_DURING_GATES')
        amendment=dict(oldBinding=old,newBinding=current,sourceGates=gates,
            failedConsumerIntent=failed_intent,noHandoff=observed,
            previousConsumerResult=failed,previousOperatorStage=read(owner.root/'operator-promotion.json'))
        intent=dict(intent,target=current['source']['integration'],
                    launcherSha256=sha(ROOT/'scripts/aosedge-sdv-lab.sh'),consumerAttempt=previous_attempt+1)
        atomic(owner.root/'operator-intent.json',intent)
        for name in ('consumer-result.json','consumer-launcher.intent.json'):
            path=owner.root/name;archive=owner.root/(name+'.attempt-'+str(previous_attempt))
            require(not archive.exists(),'CONSUMER_ARCHIVE_COLLISION');path.rename(archive)
        prior_amendment=owner.root/'operator-amendment.json'
        if prior_amendment.exists():
            archive=owner.root/('operator-amendment.json.attempt-'+str(previous_attempt))
            require(not archive.exists(),'AMENDMENT_ARCHIVE_COLLISION');prior_amendment.rename(archive)
        atomic(owner.root/'operator-amendment.json',amendment)
    finally:os.close(fd)
