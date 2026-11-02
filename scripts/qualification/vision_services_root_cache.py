#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Reconcile only the exact Rootfs .6 CM blob closure; preserve every original."""
import argparse
import json
from pathlib import Path
import shlex
import subprocess
import sys
import time
import traceback
import remote_harness as h


def worker(path):
    c=json.loads(path.read_bytes());records=path.parent;result=dict(outcome='NOT_COMPLETE',cleanup={},cloudMutation=False,phases=[])
    vm=native=None;retained={};began=time.monotonic()
    class AuditComplete(Exception):pass
    def phase(name,action):
        print(json.dumps(dict(stage=name,state='STARTED')),flush=True);start=time.monotonic();value=action()
        h.atomic(records/(name+'.json'),value);result['phases'].append(dict(stage=name,seconds=round(time.monotonic()-start,2)))
        print(json.dumps(dict(stage=name,state='COMPLETE')),flush=True);return value
    try:
        for name,pin in c['files'].items():h.require(h.digest(records/name)==pin,'ROOT_CACHE_TOOL_CHANGED')
        package=Path(c['main']['packageRoot']);bundle=Path(c['host']['bundle']);h.require(h.digest(package/'application-manifest.json')==c['main']['manifestSha256'],'ROOT_CACHE_BASE_CHANGED')
        sys.path.insert(0,str(package/'aosedge-sdv-demo/apps/demo-orchestrator/src'))
        import aosedge_demo_orchestrator
        from aosedge_demo_orchestrator import runtime_paths
        tooling=bundle/'Contents/Resources/tooling/aosedge-sdv-demo/apps/demo-orchestrator/src';aosedge_demo_orchestrator.__path__.insert(0,str(tooling/'aosedge_demo_orchestrator'))
        from aosedge_demo_orchestrator import vision_bootstrap as v
        from aosedge_demo_orchestrator.environment import EnvironmentService,JOURNAL
        from aosedge_demo_orchestrator.vm import VMService,access_path
        from aosedge_demo_orchestrator.guest_access import ssh_command
        from aosedge_demo_orchestrator.status import load_configuration
        from aosedge_demo_orchestrator.cloud_runtime import launch
        from aosedge_demo_orchestrator.cloud_connection import selected_domain,cloud_binding
        bootstrap=v.verify(bundle,c['main']['manifestSha256']);h.require(bootstrap.manifest_sha256==c['host']['manifestSha256'],'ROOT_CACHE_HOST_CHANGED')
        native=Path.home()/v.INSTANCE_NAME;state=json.loads((native/JOURNAL).read_bytes());item=state['vehicles']['test']
        h.require(item['unitId']=='af6d074a-6ce1-49ba-b613-0476e7b6d1b5' and item['localVmId']=='89273f16-4be0-4b22-b4cb-58d08533c8bc'
            and item['runtime']['state']==state['source']['state']=='STOPPED','ROOT_CACHE_SAME_IDLE_VISION_REQUIRED')
        retained={Path.home()/n:(Path.home()/n/JOURNAL).read_bytes() for n in v.RETAINED_INSTANCE_NAMES}
        with runtime_paths.installed_session(native):
            env=EnvironmentService(catalog=v.SignedVisionCatalog(bootstrap),vm_profile=v.VM_PROFILE);vm=VMService(env)
            phase('same-retained-vm-start',lambda:vm.execute('start','test',timeout=150))
            config=load_configuration(native);sdk,sdk_env=launch(native,config['cloudPython'],'unit_cloud.py')
            request=dict(action='status',servicesPacket=True,cloudDomain=selected_domain(state),oemOwner=cloud_binding(state)['ownerId'],
                readOnlySendReconciliation=c.get('completeIndexRepair',False),
                oemCredential=str(config['cloudProfiles']['oem-delivery']['credential']),
                permanentDelivery=dict(authorized=True,recoveryFirst=True,rootfsVersion='6.1.1-vision-camera.6',cameraVersion='0.1.2',perceptionVersion='0.1.1',assessmentVersion='0.1.1'),
                componentType='aos-vision-vm-1.0.0-main-qemuarm64-rootfs',version='6.1.1-vision-camera.6',
                deploymentId=c['deploymentId'],vehicles=dict(test={k:item[k] for k in ('unitId','systemUid','unitSetId','nodeId')}))
            request['vehicles']['test']['nodeHardwareId']=item['cloud']['identity']['nodeHardwareId']
            def cloud(action='status'):
                done=subprocess.run([sdk[0],'-I','-B',str(records/'vision_permanent_component_cloud.py'),str(tooling)],input=json.dumps(dict(request,action=action)),capture_output=True,text=True,env=sdk_env,timeout=90)
                h.require(done.returncode==0 and len(done.stdout)<262144,'ROOT_CACHE_CLOUD_UNAVAILABLE');value=json.loads(done.stdout)
                h.require(value.get('ok') is True,value.get('reason','ROOT_CACHE_CLOUD_FAILED'));return value['data']
            def guest(action):
                code=(records/'vision_services_root_cache_guest.py').read_text()+'''\ntry:
    print(json.dumps(dict(ok=True,data=run(ACTION))))
except Exception as error:
    value=str(error)
    diagnostic=dict(ok=False,code=value if value.isupper() and len(value)<180 else type(error).__name__)
    import traceback
    diagnostic['guestFailureLine']=traceback.extract_tb(error.__traceback__)[-1].lineno
    diagnostic['stage']=globals().get('STEP','unknown')
    filename=getattr(error,'filename',None)
    if isinstance(filename,str) and filename.startswith(('/var/aos/','/etc/aos/','/sys/fs/selinux/')):
        diagnostic['guestErrorPath']=filename
    if value=='ROOT_CACHE_LAYER_CHANGED' and digest(OLD/MANIFEST)==MANIFEST:
        diagnostic['verifiedOciManifest']=json.loads((OLD/MANIFEST).read_bytes())
    print(json.dumps(diagnostic))
'''.replace('ACTION',repr(action))
                done=subprocess.run(ssh_command(access_path(native,'test'),item['sshPort'],5),input='python3 -c '+shlex.quote(code)+'\n',capture_output=True,text=True,timeout=100)
                h.require(done.returncode==0 and len(done.stdout)<65536,'ROOT_CACHE_GUEST_'+action.upper()+'_FAILED')
                value=json.loads(done.stdout);h.atomic(records/('guest-'+action+'-diagnostic.json'),value)
                h.require(value.get('ok') is True,value.get('code','ROOT_CACHE_GUEST_FAILED'));return value['data']
            before=phase('cloud-rootfs-before-cache-reconciliation',cloud)
            h.require(before['publication']['stage']=='READY' and before['unit']['components']==[],'ROOT_CACHE_EXPECTED_OMISSION_REQUIRED')
            if c.get('completeIndexRepair'):h.require(before['sameComponentSendRequests']==[],'ROOT_CACHE_PREVIOUS_SEND_NOT_IDLE')
            phase('exact-native-cache-audit',lambda:guest('audit'))
            if c.get('auditOnly'):
                phase('native-committed-final-read-only',lambda:guest('native'))
                result['outcome']='PASS_READONLY_CACHE_RECONCILIATION';raise AuditComplete
            inspected=phase('original-root6-blob-closure-and-current-cache',lambda:guest('inspect'))
            h.require(inspected['missingBytes']>=130248704 and len(inspected['missing']) in (3,4,5)
                and '57cf756b0006640927d12508d146d6f8cfb72270b0bebbf03dded70cdf53ddd4' in inspected['missing']
                and '8aa022a71190f6c6b153a36f3a6840bc9d1b0e37da0352292badc36c4ae9e07c' in inspected['missing'],
                'ROOT_CACHE_EXACT_MISSING_CLOSURE_REQUIRED')
            if c.get('nativeCatalogRepair'):
                native_before=phase('native-committed-before-catalog-refresh',lambda:guest('native'))
                request['componentTitle']=before['componentTitle']
                h.atomic(records/'same-root6-send-intent.json',dict(attemptStarted=True,version='6.1.1-vision-camera.6',
                    publicationSha256='8aa022a71190f6c6b153a36f3a6840bc9d1b0e37da0352292badc36c4ae9e07c',
                    unitId=item['unitId'],uploadRepeated=False,rootfsRebuilt=False))
                result['cloudMutation']=True
                phase('normal-native-current-version-assignment',lambda:cloud('send'))
            else:phase('reconcile-only-missing-root6-blobs',lambda:guest('repair'))
            end=time.monotonic()+180;after=None
            while time.monotonic()<end:
                after=cloud();h.atomic(records/'cloud-rootfs-latest.json',after)
                if any((r.get('installed_component') or {}).get('version')=='6.1.1-vision-camera.6' and not r.get('pending_component') for r in after['unit']['components'] or []):break
                time.sleep(3)
            else:raise ValueError('ROOT_CACHE_RECONCILED_INVENTORY_STILL_MISSING')
            if c.get('nativeCatalogRepair'):
                native_after=phase('native-committed-after-catalog-refresh',lambda:guest('native'))
                h.require(native_before==native_after,'ROOT_CACHE_NATIVE_STATE_CHANGED')
            result.update(outcome='PASS_ROOT6_CLOUD_INVENTORY_AFTER_NATIVE_CATALOG_RECONCILIATION' if c.get('nativeCatalogRepair')
                    else 'PASS_ROOT6_CLOUD_INVENTORY_AFTER_EXACT_CACHE_RECONCILIATION',rootfsCloudConfirmed=True,
                exactOriginalBlobsCopied=not c.get('nativeCatalogRepair',False),originalsPreserved=True,databaseManuallyChanged=False,
                rootfsChanged=False,rootfsRebuilt=False,noUpload=True,dataPreserved=True)
    except AuditComplete:pass
    except Exception as error:
        value=str(error);result.update(code=value if value.isupper() and len(value)<180 else type(error).__name__,failureLine=traceback.extract_tb(error.__traceback__)[-1].lineno)
    finally:
        if vm is not None:
            with runtime_paths.installed_session(native):result['cleanup']['visionStopped']=vm.execute('stop','test',timeout=150)['vehicles']['test']['state']=='COMPLETED'
            result['cleanup']['sourceStopped']=json.loads((native/JOURNAL).read_bytes())['source']['state']=='STOPPED'
            result['cleanup']['retainedJournalsUnchanged']=all((p/JOURNAL).read_bytes()==raw for p,raw in retained.items())
        result['seconds']=round(time.monotonic()-began,2)
        if 'code' in result or not result['cleanup'] or not all(result['cleanup'].values()):result['outcome']='NOT_COMPLETE'
        h.atomic(records/'result.json',result);print(json.dumps(result),flush=True)
    return 0 if result['outcome'].startswith('PASS_') else 1


def main():
    p=argparse.ArgumentParser();p.add_argument('--config',type=Path);p.add_argument('--worker',type=Path)
    p.add_argument('--attempt',type=int,choices=range(1,12),default=1);p.add_argument('--audit-only',action='store_true')
    p.add_argument('--native-catalog-repair',action='store_true');a=p.parse_args()
    if a.worker:return worker(a.worker)
    from vision_vm_campaign import configuration
    c=configuration(a.config);ui=json.loads((Path(c['records'])/'vision-services-permanent-api-ui-03/result.json').read_bytes())
    h.require(ui['outcome']=='PASS_PERMANENT_VISION_HEADED_BROWSER_UI' and all(ui['cleanup'].values()),'COMPLETED_UI_AND_IDLE_TARGET_REQUIRED')
    if a.attempt>1:
        prior=json.loads((Path(c['records'])/('vision-services-root-cache-%02d'%(a.attempt-1))/'result.json').read_bytes())
        h.require(prior['outcome'] in ('NOT_COMPLETE','PASS_READONLY_CACHE_RECONCILIATION') and all(prior['cleanup'].values()),'PREVIOUS_ROOT_CACHE_ATTEMPT_NOT_IDLE')
    name='vision-services-root-cache-%02d'%a.attempt;records=Path(c['records'])/name;remote=Path(c['remoteRoot'])/name
    h.require(not records.exists(),'ROOT_CACHE_ATTEMPT_EXISTS_RECONCILE');records.mkdir(mode=0o700)
    here=Path(__file__).parent;files=[Path(__file__).resolve(),here/'vision_services_root_cache_guest.py',here/'vision_permanent_component_cloud.py',here/'remote_harness.py',here.parent/'distribution/installation_inputs.py']
    h.require(not a.native_catalog_repair or (a.attempt==9 and not a.audit_only),'EXACT_NATIVE_REPAIR_ATTEMPT_REQUIRED')
    context=dict(main=c['main'],completeIndexRepair=a.attempt==10,auditOnly=a.audit_only,nativeCatalogRepair=a.native_catalog_repair,host=json.loads((Path(c['records'])/'vision-services-host-05/result.json').read_bytes()),
        deploymentId=json.loads((Path(c['records'])/'permanent-rootfs-02/rootfs-upload.json').read_bytes())['facts']['deploymentId'],files={p.name:h.digest(p) for p in files})
    h.atomic(records/'context.json',context);h.remote(c['transport'],'umask 077\nmkdir '+shlex.quote(str(remote)),timeout=15)
    options=h.ssh_args(c['transport'])[1:-1];options.remove('-T');i=options.index('-b');options[i:i+2]=['-o','BindAddress='+options[i+1]]
    h.run(['/usr/bin/scp',*options,*map(str,files),str(records/'context.json'),c['transport']['user']+'@'+c['transport']['host']+':'+str(remote)+'/'],timeout=30)
    py=c['main']['packageRoot']+'/demo-artifacts/aosedge-sdv-demo/host-runtime/python/bin/python3.12'
    proc=subprocess.Popen(h.ssh_args(c['transport'])+[shlex.join([py,'-B',str(remote/files[0].name),'--worker',str(remote/'context.json')])],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    with (records/'progress.jsonl').open('x') as stream:
        for line in proc.stdout:h.require(stream.tell()<1024**2,'PROGRESS_LIMIT');stream.write(line);stream.flush();print(line.strip(),flush=True)
    exit_code=proc.wait(timeout=15);diagnostic=proc.stderr.read(8192)
    code='import pathlib,json;p=pathlib.Path('+repr(str(remote))+');print(json.dumps({f.name:json.loads(f.read_bytes()) for f in p.glob("*.json") if f.name!="context.json" and f.stat().st_size<2097152}))'
    for name,value in json.loads(h.remote(c['transport'],shlex.join([py,'-I','-B','-c',code]),timeout=20)).items():h.atomic(records/name,value)
    h.atomic(records/'transport.json',dict(exit=exit_code,stderrPresent=bool(diagnostic)));return exit_code


if __name__=='__main__':raise SystemExit(main())
