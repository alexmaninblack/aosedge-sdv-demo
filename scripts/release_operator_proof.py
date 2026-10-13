# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Anonymous A consumer on M1, ordinary Setup owners, then catalog promotion."""
import hashlib
import json
from pathlib import Path
import shlex
import sys
from uuid import uuid4

from release_automation import ROOT, atomic, read, require
from release_owners import command, git, sha
from release_publication import descriptor, remote_main


def project(owner, published):
    """Append-only delivery record; generate only the existing selected graph."""
    expected=descriptor(owner)
    relative='workspace/releases/'+owner.config['version']+'-presenter-preview-delivery.json'
    path=ROOT/relative
    raw=(json.dumps(expected,indent=2)+'\n').encode()
    require(not path.exists() or path.read_bytes()==raw,'IMMUTABLE_DESCRIPTOR_COLLISION')
    catalog=json.loads((ROOT/'workspace/launcher-catalog.json').read_bytes())
    catalog['catalogRevision']+=1;catalog['operatorDescriptor']=relative
    for key in ('productVersion','status','file','bytes','sha256','manifestSha256','notarized'):
        catalog['operator'][key]=expected[key]
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
                    'tests.test_drive_download_parser'],timeout=300)
    require(result.returncode==0,'CATALOG_LAUNCHER_GATE_FAILED')
    git(ROOT,'add','--',*paths)
    git(ROOT,'commit','-m','Prepare checked public Presenter preview for option A')
    intent['target']=git(ROOT,'rev-parse','HEAD');intent['launcherSha256']=sha(ROOT/'scripts/aosedge-sdv-lab.sh')
    atomic(intent_path,intent)
    git(ROOT,'push','origin','HEAD:refs/heads/codex/release-automation')
    return intent


def connection(owner):
    sys.path.insert(0,str(ROOT/'scripts/qualification'))
    import remote_harness as h
    import journey as j
    transport,_=h.configuration(Path(owner.config['remoteConfig']))
    config=j.configuration(Path(owner.config['operatorJourney']),transport['user'])
    require(config['manifestSha256']==owner.config['candidate']['manifestSha256'],'OPERATOR_PACKAGE_BINDING_CHANGED')
    return h,j,transport,config


def consumer(owner, intent):
    h,j,transport,config=connection(owner)
    from campaign import Media
    from release_automation import CampaignError
    test=read(owner.root/'qualification.json')['facts']['test']
    remote=j.Remote(transport,config)
    # Exact current desktop/read-only owner check before a costly consumer download.
    request=dict(config=config,kind='observe',args={},phase='observe',requestId=str(uuid4()),expectedRun=test)
    program=j.WORKER.read_text()+'\nREQUEST='+repr(request)+'''
with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
 worker=Worker(REQUEST)
 with worker.imports():
  worker.binding();closed=wait_for_exit(timeout=1);engine=docker_info()
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
    h.parse(run(program))
    parent='/Users/'+transport['user']+'/SDV-Qualification/operator-'+owner.config['version']
    dmg=parent+'/sdv/cache/'+descriptor(owner)['file']
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
    path=owner.root/'consumer-result.json'
    if not path.exists():return False
    return read(path).get('outcome')=='PASS' and read(path)['facts'].get('cleanupConfirmed') is True
