#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Read-only OEM recipient/version gate before the one Vision rootfs build."""
import argparse
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import sys
import remote_harness as h


def worker(path):
    c=json.loads(path.read_bytes());records=path.parent;package=Path(c['main']['packageRoot']);bundle=Path(c['host']['bundle'])
    h.require(hashlib.sha256((package/'application-manifest.json').read_bytes()).hexdigest()==c['main']['manifestSha256'],'VISION_BASE_CHANGED')
    for name,pin in c['files'].items():h.require(h.digest(records/name)==pin,'VISION_PREFLIGHT_TOOL_CHANGED')
    sys.path.insert(0,str(package/'aosedge-sdv-demo/apps/demo-orchestrator/src'))
    import aosedge_demo_orchestrator
    from aosedge_demo_orchestrator import runtime_paths
    tooling=bundle/'Contents/Resources/tooling/aosedge-sdv-demo/apps/demo-orchestrator/src'
    aosedge_demo_orchestrator.__path__.insert(0,str(tooling/'aosedge_demo_orchestrator'))
    from aosedge_demo_orchestrator import vision_bootstrap as v
    from aosedge_demo_orchestrator.environment import JOURNAL
    from aosedge_demo_orchestrator.status import load_configuration
    from aosedge_demo_orchestrator.cloud_runtime import launch
    from aosedge_demo_orchestrator.cloud_connection import selected_domain,cloud_binding
    verified=v.verify(bundle,c['main']['manifestSha256']);h.require(verified.manifest_sha256==c['host']['manifestSha256'],'VISION_HOST_CHANGED')
    native=Path.home()/v.INSTANCE_NAME;before=(native/JOURNAL).read_bytes();state=json.loads(before);item=state['vehicles']['test'];result={}
    h.require(item['unitId']=='af6d074a-6ce1-49ba-b613-0476e7b6d1b5' and item['localVmId']=='89273f16-4be0-4b22-b4cb-58d08533c8bc'
        and item['runtime']['state']==state['source']['state']=='STOPPED','VISION_IDLE_TARGET_REQUIRED')
    if c.get('bootInventory') is True:
        from aosedge_demo_orchestrator.environment import EnvironmentService
        from aosedge_demo_orchestrator.vm import VMService,access_path
        from aosedge_demo_orchestrator.guest_access import ssh_command
        retained={Path.home()/name:(Path.home()/name/JOURNAL).read_bytes() for name in v.RETAINED_INSTANCE_NAMES}
        vm=None
        try:
            with runtime_paths.installed_session(native):
                env=EnvironmentService(catalog=v.SignedVisionCatalog(verified),vm_profile=v.VM_PROFILE);vm=VMService(env)
                started=vm.execute('start','test',timeout=150)
                h.require(started['vehicles']['test']['state']=='COMPLETED','VISION_BOOT_START_FAILED')
                code=(records/'vision_delivery_guest.py').read_text()+"\nprint(json.dumps(boot_inventory()))\n"
                done=subprocess.run(ssh_command(access_path(native,'test'),item['sshPort'],4),
                    input="python3 - <<'READ_BOOT'\n"+code+"\nREAD_BOOT\n",capture_output=True,text=True,timeout=45)
                h.require(done.returncode==0,'VISION_BOOT_INVENTORY_FAILED');inventory=json.loads(done.stdout)
                h.atomic(records/'boot-inventory.json',inventory)
                images=inventory['initramfs'];pin=c['installedBootPin']
                h.require(len(images)==1 and images[0]['sha256']==pin['initramfsSha256']
                    and images[0]['helpers']==pin['helpers'] and inventory['bootChanged'] is False,'VISION_INSTALLED_BOOT_CHANGED')
                output=dict(pin,currentBootRechecked=True,cloudMutation=False)
        finally:
            if vm is not None:
                with runtime_paths.installed_session(native):stopped=vm.execute('stop','test',timeout=150)
                h.require(stopped['vehicles']['test']['state']=='COMPLETED','VISION_BOOT_STOP_FAILED')
            h.require(all((p/JOURNAL).read_bytes()==raw for p,raw in retained.items()),'VISION_RETAINED_JOURNALS_CHANGED')
        output['cleanup']=dict(visionStopped=True,retainedJournalsUnchanged=True)
        h.atomic(records/'result.json',output);print(json.dumps(output));return 0
    with runtime_paths.installed_session(native):
        config=load_configuration(native);sdk,environment=launch(native,config['cloudPython'],'unit_cloud.py')
        request=dict(action='preflight',servicesPacket=True,cloudDomain=selected_domain(state),oemOwner=cloud_binding(state)['ownerId'],
            oemCredential=str(config['cloudProfiles']['oem-delivery']['credential']),vehicles=dict(test={k:item[k] for k in ('unitId','systemUid','unitSetId','nodeId')}),
            permanentDelivery=dict(authorized=True,recoveryFirst=True,rootfsVersion='6.1.1-vision-camera.6',cameraVersion='0.1.2',perceptionVersion='0.1.1',assessmentVersion='0.1.1'))
        request['vehicles']['test']['nodeHardwareId']=item['cloud']['identity']['nodeHardwareId']
        for kind,version in (('rootfs','6.1.1-vision-camera.6'),('camera-access','0.1.2')):
            done=subprocess.run([sdk[0],'-I','-B',str(records/'vision_permanent_component_cloud.py'),str(tooling)],input=json.dumps(dict(request,
                componentType='aos-vision-vm-1.0.0-main-qemuarm64-'+kind,version=version)),capture_output=True,text=True,env=environment,timeout=90)
            h.require(done.returncode==0 and len(done.stdout)<262144,'VISION_PLATFORM_PREFLIGHT_UNAVAILABLE');value=json.loads(done.stdout)
            h.require(value.get('ok') is True,value.get('reason','VISION_PLATFORM_PREFLIGHT_FAILED'));result[kind]=value['data']
    h.require((native/JOURNAL).read_bytes()==before,'VISION_PREFLIGHT_JOURNAL_CHANGED')
    output=dict(outcome='PASS_VISION_SERVICES_PLATFORM_RECIPIENTS_AND_VERSIONS',components=result,cloudMutation=False,vmStarted=False,journalUnchanged=True)
    h.atomic(records/'result.json',output);print(json.dumps(output));return 0


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--config',type=Path);parser.add_argument('--worker',type=Path)
    parser.add_argument('--boot-inventory',action='store_true');parser.add_argument('--boot-case',type=int,choices=(1,2),default=1);args=parser.parse_args()
    if args.worker:return worker(args.worker)
    from vision_vm_campaign import configuration
    c=configuration(args.config);name=('vision-services-boot-%02d'%args.boot_case) if args.boot_inventory else 'vision-services-platform-preflight-01';records=Path(c['records'])/name;remote=Path(c['remoteRoot'])/name
    h.require(not records.exists(),'VISION_PLATFORM_PREFLIGHT_EXISTS_RECONCILE')
    for n,outcome in (('vision-services-recovery-01','PASS_SAME_VM_CHECKPOINT_RECOVERY'),('vision-services-native-live-17','PASS_NATIVE_COMMUNICATION_CACHE_PATH_AND_RETAINED_SUCCESSORS')):
        value=json.loads((Path(c['records'])/n/'result.json').read_bytes());h.require(value['outcome']==outcome and all(value['cleanup'].values()),'VISION_PLATFORM_SOURCE_AND_RECOVERY_REQUIRED')
    records.mkdir(mode=0o700);source=Path(__file__).resolve();files=[source,source.with_name('vision_permanent_component_cloud.py'),source.with_name('remote_harness.py')]
    # remote_harness imports the pure complete-kit parser, not product owners.
    files.append(source.parent.parent/'distribution/installation_inputs.py')
    if args.boot_inventory:files.append(source.with_name('vision_delivery_guest.py'))
    context=dict(main=c['main'],host=json.loads((Path(c['records'])/'vision-services-host-03/result.json').read_bytes()),files={p.name:h.digest(p) for p in files})
    if args.boot_inventory:context.update(bootInventory=True,installedBootPin=json.loads(Path('/Volumes/SDV-Dev/sdv/build/vision-ingress/native-primitives-01/boot-compatibility.json').read_bytes()))
    h.atomic(records/'context.json',context);h.remote(c['transport'],'umask 077\nmkdir '+shlex.quote(str(remote)),timeout=15)
    options=h.ssh_args(c['transport'])[1:-1];options.remove('-T');index=options.index('-b');options[index:index+2]=['-o','BindAddress='+options[index+1]]
    h.run(['/usr/bin/scp',*options,*map(str,files),str(records/'context.json'),c['transport']['user']+'@'+c['transport']['host']+':'+str(remote)+'/'],timeout=30)
    python=c['main']['packageRoot']+'/demo-artifacts/aosedge-sdv-demo/host-runtime/python/bin/python3.12'
    done=h.remote(c['transport'],shlex.join([python,'-B',str(remote/source.name),'--worker',str(remote/'context.json')]),timeout=200)
    value=json.loads(done);h.atomic(records/'result.json',value);print(json.dumps(value));return 0


if __name__=='__main__':raise SystemExit(main())
