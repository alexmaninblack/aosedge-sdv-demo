#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""M4-only signed-bootstrap manufacture/provision scenario, normal owners only."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import stat
import subprocess
import sys
import time


def require(ok, code):
    if not ok:
        raise ValueError(code)


def atomic(path, value):
    tmp=path.with_suffix('.pending')
    with tmp.open('x') as stream:
        os.fchmod(stream.fileno(),0o600)
        json.dump(value,stream,indent=2);stream.flush();os.fsync(stream.fileno())
    os.replace(tmp,path)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--context',type=Path,required=True)
    a=parser.parse_args()
    require(a.context.stat().st_uid==os.getuid() and stat.S_IMODE(a.context.stat().st_mode)==0o600,'PRIVATE_CONTEXT_REQUIRED')
    c=json.loads(a.context.read_bytes());records=a.context.parent
    require(not (records/'result.json').exists(),'SCENARIO_ATTEMPT_EXISTS_RECONCILE')
    console=json.loads(sys.stdin.read(8193))
    require(set(console)=={'password'} and isinstance(console['password'],str)
            and 0<len(console['password'])<1024 and not any(v in console['password'] for v in '\r\n\x00'),'CONSOLE_INPUT_INVALID')
    package=Path(c['main']['packageRoot']);bundle=Path(c['bundle'])
    require(subprocess.check_output(['/usr/sbin/sysctl','-n','hw.model'],text=True).strip()=='Mac16,8','M4_REQUIRED')
    require(hashlib.sha256((package/'application-manifest.json').read_bytes()).hexdigest()==c['main']['manifestSha256'],'BASE_PROGRAM_CHANGED')
    requirement='identifier "org.aosedge.sdvlab.vision.bootstrap" and anchor apple generic and certificate leaf[subject.OU] = "3NF57VKB3V"'
    subprocess.run(['/usr/bin/codesign','--verify','--deep','--strict','-R','='+requirement,str(bundle)],check=True,capture_output=True,timeout=120)
    # Do not import any bundle code until its OS signature has been verified.
    sys.path.insert(0,str(package/'aosedge-sdv-demo/apps/demo-orchestrator/src'))
    import aosedge_demo_orchestrator
    from aosedge_demo_orchestrator import runtime_paths,installed_control
    require(runtime_paths.CODE_ROOT==package/'aosedge-sdv-demo','BASE_RUNTIME_OWNER_CHANGED')
    tooling=bundle/'Contents/Resources/tooling/aosedge-sdv-demo/apps/demo-orchestrator/src/aosedge_demo_orchestrator'
    aosedge_demo_orchestrator.__path__.insert(0,str(tooling))
    from aosedge_demo_orchestrator import vision_bootstrap as v
    from aosedge_demo_orchestrator.environment import EnvironmentService,JOURNAL
    from aosedge_demo_orchestrator.vm import VMService,access_path
    from aosedge_demo_orchestrator.units import UnitService
    from aosedge_demo_orchestrator.cloud_setup import CloudSetup
    from aosedge_demo_orchestrator.cloud_connection import CloudConnection
    from aosedge_demo_orchestrator.status import load_configuration,read_json
    from aosedge_demo_orchestrator.guest_access import ssh_command
    verified=v.verify(bundle,c['main']['manifestSha256'])
    require(verified.manifest_sha256==c['bootstrapManifestSha256'],'BOOTSTRAP_SELECTION_CHANGED')
    home=Path.home();native=home/v.INSTANCE_NAME
    require(native.stat().st_dev==home.stat().st_dev if native.exists() else native.parent==home,'NATIVE_INTERNAL_STORAGE_REQUIRED')
    retained=[home/name for name in ('SDV-Lab-Data','SDV-Vision-Lab-Data','SDV-Vision-Native-Lab-Data')]
    before={root:(root/JOURNAL).read_bytes() for root in retained}
    for raw in before.values():
        state=json.loads(raw)
        require(all(i.get('runtime',{}).get('state')=='STOPPED' for i in state['vehicles'].values()),'RETAINED_VM_MUST_BE_STOPPED')
    for port in (10022,12022,2000,18080,16443,18053):
        with socket.socket() as sock:
            sock.settimeout(.2);require(sock.connect_ex(('127.0.0.1',port))!=0,'CONFLICTING_RUNTIME_OWNER')
    result=dict(scenario='VISION_SIGNED_BOOTSTRAP_M4',outcome='NOT_COMPLETE',phases=[],
        bootstrapManifestSha256=verified.manifest_sha256,nativeActivation='NOT_RUN',aosConsumer='NOT_RUN',
        fullVisionE2E='NOT_RUN',cleanup={},carlaRebuilt=False,retainedDataPolicy='PRESERVE')
    started=time.monotonic();runtime=None;own_started=False
    def phase(name, action):
        print(json.dumps(dict(stage=name,state='STARTED')),flush=True);begin=time.monotonic()
        value=action()
        atomic(records/(name+'.json'),dict(seconds=round(time.monotonic()-begin,2),facts=value))
        result['phases'].append(dict(stage=name,seconds=round(time.monotonic()-begin,2),state='COMPLETE'))
        atomic(records/'progress.json',result)
        print(json.dumps(dict(stage=name,state='COMPLETE')),flush=True)
        return value
    try:
        sys.path.insert(0,str(Path(c['main']['setupApp'])/'Contents/Resources/tooling/scripts/distribution'))
        from installation import Store
        from version_management import Versions
        _,old_id=runtime_paths.instance(retained[0])
        selection=installed_control.selection(retained[0],old_id)
        store=Store(Path(selection['storePath']),selection['volumeUUID'])
        require(not native.exists(),'NATIVE_INSTANCE_EXISTS_RECONCILE')
        phase('instance',lambda:runtime_paths.create_instance(native))
        phase('base-selection',lambda:Versions(store,native).change('select',0,c['main']['manifestSha256']))
        # Read only certificate references, not keys or the old configuration.
        with runtime_paths.installed_session(retained[0]):
            config=load_configuration(retained[0])
            pair=[str(config['cloudProfiles'][name]['credential']) for name in ('oem-delivery','service-provider')]
        with runtime_paths.installed_session(native):
            catalog=v.SignedVisionCatalog(verified)
            env=EnvironmentService(catalog=catalog,vm_profile=v.VM_PROFILE)
            runtime=VMService(env,password_provider=lambda role:console['password'] if role=='test' else None,
                              progress=lambda message:print(json.dumps(dict(stage='native-owner',state=str(message)[:110])),flush=True))
            units=UnitService(runtime)
            connection=CloudConnection(env)
            preview=connection.inspect_pair(*pair)
            phase('certificate-selection',lambda:connection.select_pair(*pair,preview['selectionToken']))
            setup=CloudSetup(units)
            report=phase('cloud-preflight',lambda:setup.check(first_use=True))
            require(report['stage'] in ('MISSING','READY'),'VISION_CLOUD_PREFLIGHT_BLOCKED')
            report=phase('cloud-prepare',setup.prepare)
            require(report['stage']=='READY','VISION_CLOUD_PREPARATION_INCOMPLETE')
            phase('manufacture',lambda:env.create('test',selector=v.SELECTOR))
            own_started=True
            boot=phase('native-boot',lambda:runtime.execute('start','test',timeout=150))
            require(boot['vehicles']['test']['state']=='COMPLETED','VISION_BOOT_INCOMPLETE')
            console.clear();runtime.password_provider=None
            phase('native-time',runtime.sync_time)
            provision=phase('native-provision',lambda:units.execute('provision','test'))
            state=read_json(native/JOURNAL);item=state['vehicles']['test']
            require(item.get('unitId') and item.get('nodeId') and item['cloud']['identity']['model']=='aos-vision-vm','VISION_NATIVE_IDENTITY_NOT_CONFIRMED')
            cmd=ssh_command(access_path(native,'test'),item['sshPort'],5)
            script='''set -eu
test "$(getenforce)" = Enforcing
python3 -c "import pwd,grp;assert pwd.getpwnam('aos-camera-access').pw_uid>0;assert grp.getgrnam('aos-camera-read').gr_gid>0"
systemctl is-active --quiet aos-sm
test ! -e /usr/libexec/aos-vehicle-data-provider-launcher
test ! -e /var/aos/workdirs/sm/runtimes/systemd-slot-component/active
printf 'VISION_NATIVE_BOOTSTRAP_CONFIRMED\\n'
'''
            p=subprocess.run(cmd,input=script,text=True,capture_output=True,timeout=15)
            require(p.returncode==0 and p.stdout.strip()=='VISION_NATIVE_BOOTSTRAP_CONFIRMED','VISION_NATIVE_BOOTSTRAP_NOT_CONFIRMED')
            result.update(outcome='PASS_BOOTSTRAP_PROVISION_ONLY',nativeUnitCreated=True,
                          nativeActivation='NOT_RUN',aosConsumer='NOT_RUN')
    except Exception as error:
        value=str(error)
        result['code']=value if re.fullmatch('[A-Z][A-Z0-9_:.-]{1,150}',value) else type(error).__name__
    finally:
        console.clear()
        if runtime is not None and own_started:
            try:
                with runtime_paths.installed_session(native):
                    stopped=runtime.execute('stop','test',timeout=150)
                result['cleanup']['nativeVmStopped']=stopped['vehicles']['test']['state']=='COMPLETED'
            except Exception as error:
                result['cleanup']['nativeVmStopped']=False
                result['cleanup']['code']=type(error).__name__
        else:
            result['cleanup']['nativeVmStopped']=True
        result['cleanup']['retainedJournalsUnchanged']=all((root/JOURNAL).read_bytes()==raw for root,raw in before.items())
        released=True
        for port in (12022,2000,18080,16443,18053):
            with socket.socket() as sock:
                sock.settimeout(.2);released &= sock.connect_ex(('127.0.0.1',port))!=0
        result['cleanup']['listenersReleased']=released
        result['seconds']=round(time.monotonic()-started,2)
        if not all(result['cleanup'].values()):result['outcome']='CLEANUP_INCOMPLETE'
        atomic(records/'result.json',result)
        print(json.dumps(result),flush=True)
    return 0 if result['outcome']=='PASS_BOOTSTRAP_PROVISION_ONLY' else 1


if __name__=='__main__':raise SystemExit(main())
