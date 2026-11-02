#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Retained M4 native rootfs FOTA; never edits guest rootfs or update state."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import textwrap
import time
import traceback


def require(ok,code):
    if not ok:raise ValueError(code)


def atomic(path,value):
    temporary=path.with_suffix('.pending')
    fd=os.open(temporary,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    with os.fdopen(fd,'w') as stream:json.dump(value,stream,indent=2);stream.flush();os.fsync(stream.fileno())
    os.replace(temporary,path)


def digest(path):
    value=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(4*1024**2),b''):value.update(block)
    return value.hexdigest()


def services_cache_paths_compatible(cm,sm):
    """A rootfs path change must not strand an update acquired by old Core."""
    return (cm.get('imageManager',{}).get('installPath')=='/var/aos/downloads/vision-services/cm-images'
        and sm.get('imageManager',{}).get('imagePath')=='/var/aos/downloads/vision-services/sm-images')


OBSERVE=r'''
value=run('snapshot')
match=re.fullmatch(r'VERSION="([^"\n]+)"',value['rootfsVersion']);assert match
value['rootfsVersion']=match[1]
value['bootId']=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
value['rootMount']=next(dict(source=v[0],filesystem=v[2],readOnly='ro' in v[3].split(','))
    for v in (line.split() for line in Path('/proc/mounts').read_text().splitlines()) if v[1]=='/')
work=Path('/var/aos/workdirs/sm/runtimes/rootfs')
value['updateFlags']=[name for name in ('do_update','updated','do_apply','failed') if (work/name).exists()]
value['rootfsPending']=(work/'pending_instance.json').exists()
p=work/'installed_instance.json';value['nativeInstalledVersion']=json.loads(p.read_bytes()).get('version') if p.exists() else None
value['coreActive']=all(subprocess.run(['systemctl','is-active','--quiet',name],capture_output=True,timeout=5).returncode==0
    for name in ('aos-cm','aos-iam','aos-sm'))
value['ingressShipped']=Path('/usr/libexec/aos-camera-ingress-launcher').is_file()
value['transientProofPresent']=Path('/run/vision-camera-store-proof').exists()
print(json.dumps(value))
'''


def main():
    context=Path(sys.argv[1]);c=json.loads(context.read_bytes());records=context.parent
    require(not (records/'result.json').exists(),'PERMANENT_ATTEMPT_EXISTS_RECONCILE')
    result=dict(scenario='VISION_RETAINED_NATIVE_ROOTFS_FOTA',outcome='NOT_COMPLETE',phases=[],cleanup={},
                cloudMutation=False,rootfsInstalled=False,cameraUpdate='NOT_RUN',nativeReadRevoke='NOT_RUN')
    began=time.monotonic();vm=None;retained={};native=None;attempted=False;confirmed=False;caffeinate=None
    services_packet=c.get('servicesPacket',False)
    require(type(services_packet) is bool,'PACKET_INVALID')
    version='6.1.1-vision-camera.6' if services_packet else '6.1.1-vision-camera.5'
    def phase(name,action):
        print(json.dumps(dict(stage=name,state='STARTED')),flush=True);start=time.monotonic();value=action()
        atomic(records/(name+'.json'),dict(seconds=round(time.monotonic()-start,2),facts=value))
        result['phases'].append(dict(stage=name,seconds=round(time.monotonic()-start,2)));atomic(records/'progress.json',result)
        print(json.dumps(dict(stage=name,state='COMPLETE')),flush=True);return value
    try:
        package=Path(c['main']['packageRoot']);bundle=Path(c['bundle'])
        require(subprocess.check_output(['/usr/sbin/sysctl','-n','hw.model'],text=True).strip()=='Mac16,8','M4_REQUIRED')
        require(digest(package/'application-manifest.json')==c['main']['manifestSha256'],'BASE_CHANGED')
        for name,pin in c['files'].items():require(digest(records/name)==pin,'DELIVERY_INPUT_CHANGED')
        payload=records/'vision-rootfs.squashfs';require(payload.stat().st_size==c['rootfs']['bytes']
            and digest(payload)==c['rootfs']['sha256'],'ROOTFS_PAYLOAD_CHANGED')
        subprocess.run(['codesign','--verify','--deep','--strict','-R',
            '=identifier "org.aosedge.sdvlab.vision.bootstrap" and anchor apple generic and certificate leaf[subject.OU] = "3NF57VKB3V"',
            str(bundle)],check=True,capture_output=True,timeout=120)
        sys.path.insert(0,str(package/'aosedge-sdv-demo/apps/demo-orchestrator/src'))
        import aosedge_demo_orchestrator
        from aosedge_demo_orchestrator import runtime_paths
        tooling=bundle/'Contents/Resources/tooling/aosedge-sdv-demo/apps/demo-orchestrator/src'
        aosedge_demo_orchestrator.__path__.insert(0,str(tooling/'aosedge_demo_orchestrator'))
        from aosedge_demo_orchestrator import vision_bootstrap as v
        from aosedge_demo_orchestrator.environment import EnvironmentService,JOURNAL
        from aosedge_demo_orchestrator.vm import VMService,access_path
        from aosedge_demo_orchestrator.units import UnitService
        from aosedge_demo_orchestrator.guest_access import ssh_command
        from aosedge_demo_orchestrator.status import load_configuration,read_json
        from aosedge_demo_orchestrator.cloud_connection import selected_domain,cloud_binding
        from aosedge_demo_orchestrator.cloud_runtime import launch
        verified=v.verify(bundle,c['main']['manifestSha256']);require(verified.manifest_sha256==c['bootstrapManifestSha256'],'BOOTSTRAP_CHANGED')
        native=Path.home()/v.INSTANCE_NAME;before=read_json(native/JOURNAL);item=before['vehicles']['test']
        require(item['runtime']['state']==before['source']['state']=='STOPPED','RETAINED_IDLE_VISION_REQUIRED')
        identity={k:item[k] for k in ('localVmId','unitId','nodeId','overlay')}
        retained={Path.home()/name:(Path.home()/name/JOURNAL).read_bytes() for name in v.RETAINED_INSTANCE_NAMES}
        recovery=Path(c['recovery'])/'checkpoint'
        require((recovery/'before-update.qcow2').is_file() and (recovery/'restore-verified.json').is_file(),'VERIFIED_RECOVERY_REQUIRED')
        binding=json.loads((recovery/'binding.json').read_bytes())
        require(all(binding['identity'][k]==value for k,value in identity.items()),'RECOVERY_IDENTITY_CHANGED')
        caffeinate=subprocess.Popen(['/usr/bin/caffeinate','-d','-i','-w',str(os.getpid())],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        with runtime_paths.installed_session(native):
            env=EnvironmentService(catalog=v.SignedVisionCatalog(verified),vm_profile=v.VM_PROFILE)
            vm=VMService(env,progress=lambda msg:print(json.dumps(dict(stage='native-owner',message=str(msg)[:110])),flush=True))
            config=load_configuration(native);sdk,sdk_env=launch(native,config['cloudPython'],'unit_cloud.py')
            request=dict(cloudDomain=selected_domain(before),oemOwner=cloud_binding(before)['ownerId'],
                oemCredential=str(config['cloudProfiles']['oem-delivery']['credential']),permanentDelivery=c['permanentDelivery'],
                servicesPacket=services_packet,componentType='aos-vision-vm-1.0.0-main-qemuarm64-rootfs',version=version,
                payload=str(payload),payloadSha256=c['rootfs']['sha256'],payloadBytes=c['rootfs']['bytes'],
                vehicles=dict(test={k:item[k] for k in ('unitId','systemUid','unitSetId','nodeId')}))
            request['vehicles']['test']['nodeHardwareId']=item['cloud']['identity']['nodeHardwareId']
            def component(action,**extra):
                done=subprocess.run([sdk[0],'-I','-B',str(records/'vision_permanent_component_cloud.py'),str(tooling)],
                    input=json.dumps(dict(request,action=action,**extra)),text=True,capture_output=True,env=sdk_env,timeout=600)
                require(done.returncode==0 and len(done.stdout)<262144,'ROOTFS_SDK_FAILED')
                value=json.loads(done.stdout)
                if not value.get('ok'):
                    atomic(records/'sdk-error.json',{k:value[k] for k in ('reason','failureFile','failureLine') if k in value})
                    raise ValueError(value.get('reason','ROOTFS_SDK_FAILED'))
                value=value['data']
                if 'publication' in value:value['publication'].pop('buildInfo',None)
                return value
            def guest():
                code=(records/'vision_delivery_guest.py').read_text()+'\nimport re\n'+OBSERVE
                wrapped='import json,traceback\ntry:\n'+textwrap.indent(code,' ')+'\nexcept Exception as error:\n print(json.dumps(dict(probeError=type(error).__name__,line=traceback.extract_tb(error.__traceback__)[-1].lineno)))\n'
                done=subprocess.run(ssh_command(access_path(native,'test'),item['sshPort'],4),
                    input="python3 - <<'READ_NATIVE_UPDATE'\n"+wrapped+"\nREAD_NATIVE_UPDATE\n",text=True,capture_output=True,timeout=40)
                require(done.returncode==0 and len(done.stdout)<65536,'NATIVE_REBOOT_OR_READ_UNAVAILABLE')
                value=json.loads(done.stdout);require('probeError' not in value,'NATIVE_UPDATE_OBSERVER_FAILED');return value
            boot=phase('retained-native-start',lambda:vm.execute('start','test',timeout=150))
            require(boot['vehicles']['test']['state']=='COMPLETED','NATIVE_START_INCOMPLETE')
            def online():
                with env._writer():return UnitService(vm)._wait(read_json(native/JOURNAL),'test',lambda x:x and x['online_status']=='Online','CLOUD_ONLINE',timeout=60)
            phase('existing-unit-online',online)
            baseline=phase('native-before-update',guest)
            require(baseline['rootfsVersion']==('6.1.1-vision-camera.5' if services_packet else '6.1.1-vision-camera.3') and not baseline['rootfsPending']
                and not baseline['updateFlags'] and baseline['enforcing'] and not baseline['transientProofPresent'],'ROOTFS_BASELINE_INVALID')
            if services_packet:
                paths_code="import json,pathlib;print(json.dumps({k:json.loads(pathlib.Path('/etc/aos/'+k+'.cfg').read_bytes()).get('imageManager',{}) for k in ('cm','sm')}))"
                paths_result=subprocess.run(ssh_command(access_path(native,'test'),item['sshPort'],4),
                    input='python3 -c '+__import__('shlex').quote(paths_code)+'\n',text=True,capture_output=True,timeout=15)
                require(paths_result.returncode==0,'ROOTFS_CACHE_PATHS_UNAVAILABLE')
                paths=json.loads(paths_result.stdout)
                atomic(records/'native-update-cache-paths.json',paths)
                require(services_cache_paths_compatible(dict(imageManager=paths['cm']),dict(imageManager=paths['sm'])),
                    'ROOTFS_NATIVE_CACHE_MIGRATION_REQUIRED_BEFORE_PUBLICATION')
                capacity_code="import json,os;print(json.dumps({p:os.statvfs(p).f_bavail*os.statvfs(p).f_frsize for p in ('/var/aos/downloads','/var/aos/workdirs')}))"
                done=subprocess.run(ssh_command(access_path(native,'test'),item['sshPort'],4),
                    input='python3 -c '+__import__('shlex').quote(capacity_code)+'\n',text=True,capture_output=True,timeout=15)
                require(done.returncode==0,'ROOTFS_CAPACITY_UNAVAILABLE')
                capacity=json.loads(done.stdout);required=2*payload.stat().st_size+32*1024**2
                require(all(v>=required for v in capacity.values()),'ROOTFS_CAPACITY_INSUFFICIENT')
                atomic(records/'rootfs-capacity.json',dict(availableBytes=capacity,requiredBytes=required))
            catalog=phase('rootfs-catalog-before',lambda:component('status'))
            require(catalog['publication']['stage']=='NOT_PUBLISHED' and not catalog['versions'],'ROOTFS_PUBLICATION_EXISTS_RECONCILE')
            request['componentTitle']=catalog['componentTitle']
            output=records/('rootfs-'+version+'.tar.gz')
            signed=phase('rootfs-oem-sign',lambda:component('sign',output=str(output)))
            intent=dict(attemptStarted=True,version=request['version'],componentType=request['componentType'],unitId=item['unitId'],
                        payloadSha256=request['payloadSha256'],bundleSha256=signed['sha256'])
            atomic(records/'rootfs-upload-intent.json',intent);attempted=True;result['cloudMutation']=True;atomic(records/'progress.json',result)
            uploaded=phase('rootfs-upload',lambda:component('upload',bundle=str(output),expectedSha256=signed['sha256']))
            request['deploymentId']=uploaded['deploymentId']
            def publication():
                end=time.monotonic()+180
                while time.monotonic()<end:
                    value=component('status')
                    if value['publication']['stage']=='READY':return value
                    require(value['publication']['stage']=='PROCESSING','ROOTFS_PUBLICATION_FAILED');time.sleep(2)
                raise ValueError('ROOTFS_PUBLICATION_TIMEOUT_RECONCILE')
            ready=phase('rootfs-publication',publication)
            auto=any((row.get(key) or {}).get('version')==request['version'] for row in ready['unit']['components'] or []
                     for key in ('pending_component','installed_component'))
            if auto:atomic(records/'rootfs-delivery-observed.json',dict(origin='EXISTING_VERIFICATION_DELIVERY',requestReplayed=False))
            else:
                atomic(records/'rootfs-send-intent.json',dict(attemptStarted=True,unitId=item['unitId'],versionId=ready['publication']['versionId']))
                phase('rootfs-send',lambda:component('send'))
            boot_ids={baseline['bootId']};trial=False;last=None
            def committed():
                nonlocal trial,last
                end=time.monotonic()+420
                while time.monotonic()<end:
                    try:last=guest()
                    except (ValueError,subprocess.TimeoutExpired):time.sleep(2);continue
                    boot_ids.add(last['bootId'])
                    trial=trial or (last['rootfsVersion']==request['version'] and last['rootMount']['filesystem']!='ext4')
                    require('failed' not in last['updateFlags'],'NATIVE_ROOTFS_TRIAL_FAILED')
                    if (last['rootfsVersion']==request['version'] and last['rootMount']==dict(source='/dev/sda3',filesystem='ext4',readOnly=True)
                        and last['nativeInstalledVersion']==request['version'] and not last['rootfsPending'] and not last['updateFlags']
                        and last['coreActive'] and last['ingressShipped']):
                        observed=component('status')
                        if any((v.get('installed_component') or {}).get('version')==request['version']
                               and not v.get('pending_component') for v in observed['unit']['components'] or []):
                            return dict(guest=last,cloud=observed,observedBootCount=len(boot_ids),trialObserved=trial)
                    time.sleep(2)
                if last:atomic(records/'native-last-observation.json',last)
                raise ValueError('NATIVE_ROOTFS_COMMIT_NOT_CONFIRMED')
            applied=phase('native-trial-and-apply',committed);after=applied['guest']
            for key in ('machineId','camera','cameraInstalledMetadataSha256','cameraPayloadSha256','cameraStoreUuid',
                        'provisioned','authorizedKeysPresent','rootHomeMount','sshHostKeyMounts'):
                require(after[key]==baseline[key],'ROOTFS_RETAINED_DATA_CHANGED')
            require(after['enforcing'] and not after['transientProofPresent'] and len(boot_ids)>1,'ROOTFS_SECURITY_OR_REBOOT_UNCONFIRMED')
            confirmed=True;result.update(outcome='PASS_RETAINED_NATIVE_ROOTFS_FOTA',rootfsInstalled=True,
                rootfsVersion=request['version'],sameVm=True,dataPreserved=True,trialObserved=trial,nativeBootCount=len(boot_ids))
    except Exception as error:
        value=str(error);location=traceback.extract_tb(error.__traceback__)[-1]
        result.update(code=value if re.fullmatch('[A-Z][A-Z0-9_:,.-]{1,160}',value) else type(error).__name__,
                      failureFile=Path(location.filename).name,failureLine=location.lineno)
    finally:
        if vm is not None:
            if attempted and not confirmed:
                result['cleanup'].update(visionStopped=False,activeUpdatePreservedForReconciliation=True)
            else:
                try:
                    with runtime_paths.installed_session(native):value=vm.execute('stop','test',timeout=150)
                    result['cleanup']['visionStopped']=value['vehicles']['test']['state']=='COMPLETED'
                except Exception:result['cleanup']['visionStopped']=False
            state=json.loads((native/JOURNAL).read_bytes())
            result['cleanup']['sameVisionIdentity']=all(state['vehicles']['test'][k]==v for k,v in identity.items())
            result['cleanup']['sourceStopped']=state['source']['state']=='STOPPED'
            result['cleanup']['retainedJournalsUnchanged']=all((p/JOURNAL).read_bytes()==raw for p,raw in retained.items())
        if caffeinate is not None:caffeinate.terminate();caffeinate.wait(timeout=5)
        result['seconds']=round(time.monotonic()-began,2)
        if not result['cleanup'] or not all(result['cleanup'].values()):result['outcome']='NOT_COMPLETE'
        atomic(records/'result.json',result);print(json.dumps(result),flush=True)
    return 0 if result['outcome']=='PASS_RETAINED_NATIVE_ROOTFS_FOTA' else 1


if __name__=='__main__':raise SystemExit(main())
