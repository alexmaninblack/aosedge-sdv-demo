#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Read-only exact Vision node/service preflight; no VM start or Cloud mutation."""
import argparse
import contextlib
import hashlib
import io
import json
from pathlib import Path
import re
import shlex
import subprocess
import sys

UNIT='af6d074a-6ce1-49ba-b613-0476e7b6d1b5'
NODE='84a5e7db-f694-4124-a024-0f6ee1f35bf3'
VM='89273f16-4be0-4b22-b4cb-58d08533c8bc'


def require(ok,code):
    if not ok:raise ValueError(code)


def numeric_capacity(value,inherited=False):
    if type(value) is dict:
        result={}
        for key,item in value.items():
            selected=inherited or bool(re.search('cpu|dmips|memory|ram|storage|disk',key,re.I))
            if selected:
                if type(item) in (int,float):result[key]=item
                elif type(item) in (dict,list):
                    projected=numeric_capacity(item,True)
                    if projected:result[key]=projected
            elif type(item) in (dict,list):
                projected=numeric_capacity(item)
                if projected:result[key]=projected
        return result
    if type(value) is list:return [row for item in value if (row:=numeric_capacity(item,inherited))]
    return {}


def read_step(stage,action):
    try:return action()
    except Exception as error:
        value=str(error);code=value if re.fullmatch('[A-Z][A-Z0-9_:.-]{1,100}',value) else type(error).__name__
        raise ValueError('VISION_PREFLIGHT_'+stage+'_'+code) from None


def sdk(tooling):
    sys.path.insert(0,str(tooling));request=json.loads(sys.stdin.read(65537))
    from aosedge_demo_orchestrator.unit_cloud import Cloud
    require(request['unitId']==UNIT and request['nodeId']==NODE,'VISION_PREFLIGHT_TARGET_CHANGED')
    cloud=read_step('OEM_LOGIN',lambda:Cloud(dict(credential=request['oemCredential'],cloudDomain=request['cloudDomain'],ownerId=request['oemOwner'])))
    cloud.require('units_read','units_nodes_read','units_nodes_list','subjects_list')
    unit=read_step('UNIT_READ',lambda:cloud.unit(UNIT,nodes=False))
    require(unit and unit['system_uid']==request['systemUid'] and unit['status']=='provisioned' and unit['unit_sets']==[request['unitSetId']],'VISION_PREFLIGHT_UNIT_CHANGED')
    nodes=read_step('NODE_LIST',lambda:cloud.pages('units/'+UNIT+'/nodes/'))
    require(len(nodes)==1 and nodes[0]['id']==NODE and nodes[0]['node_id']==VM.replace('-',''),'VISION_PREFLIGHT_NODE_CHANGED');node=nodes[0]
    provider=read_step('SP_LOGIN',lambda:Cloud(dict(credential=request['spCredential'],cloudDomain=request['cloudDomain'],ownerId=request['spOwner']),expected_role='service provider'))
    provider.require('services_list','services_read','services_service_versions_list')
    services={};catalog=read_step('SERVICE_LIST',lambda:provider.pages('services/'))
    for role in ('perception','assessment'):
        matches=[row for row in catalog if row.get('codename')=='vision-'+role]
        require(len(matches)<=1,'VISION_PREFLIGHT_SERVICE_AMBIGUOUS')
        versions=read_step('VERSION_LIST',lambda:provider.pages('services/'+matches[0]['id']+'/service-versions/')) if matches else []
        services[role]=dict(exists=bool(matches),versionOccupied=any(row.get('version')=='0.1.0' for row in versions))
    subjects=[row for row in read_step('SUBJECT_LIST',lambda:cloud.pages('subjects/')) if row.get('title')=='SDV Vision Pilot']
    require(len(subjects)<=1,'VISION_PREFLIGHT_SUBJECT_AMBIGUOUS')
    return dict(outcome='PASS_READ_ONLY_VISION_CLOUD_PREFLIGHT',unitPreserved=True,nodePreserved=True,online=unit['online_status']=='Online',
        nodeFieldNames=sorted(node),capacity=numeric_capacity(node),services=services,visionSubjectExists=bool(subjects),cloudMutation=False)


def host(context):
    c=json.loads(context.read_bytes());records=context.parent;result=dict(outcome='NOT_COMPLETE',cloudMutation=False)
    native=None;before=None;retained={}
    try:
        package=Path(c['packageRoot']);bundle=Path(c['bundle'])
        require(hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==c['workerSha256'],'VISION_PREFLIGHT_WORKER_CHANGED')
        require(subprocess.check_output(['/usr/sbin/sysctl','-n','hw.model'],text=True).strip()=='Mac16,8','M4_REQUIRED')
        require(hashlib.sha256((package/'application-manifest.json').read_bytes()).hexdigest()==c['baseManifest'],'VISION_PREFLIGHT_BASE_CHANGED')
        sys.path.insert(0,str(package/'aosedge-sdv-demo/apps/demo-orchestrator/src'))
        import aosedge_demo_orchestrator
        from aosedge_demo_orchestrator import runtime_paths
        tooling=bundle/'Contents/Resources/tooling/aosedge-sdv-demo/apps/demo-orchestrator/src'
        aosedge_demo_orchestrator.__path__.insert(0,str(tooling/'aosedge_demo_orchestrator'))
        from aosedge_demo_orchestrator import vision_bootstrap as v
        from aosedge_demo_orchestrator.environment import JOURNAL
        from aosedge_demo_orchestrator.status import load_configuration
        from aosedge_demo_orchestrator.cloud_connection import selected_domain,cloud_binding
        from aosedge_demo_orchestrator.cloud_runtime import launch
        verified=v.verify(bundle,c['baseManifest']);require(verified.manifest_sha256==c['bootstrapManifest'],'VISION_PREFLIGHT_BOOTSTRAP_CHANGED')
        native=Path.home()/v.INSTANCE_NAME;before=(native/JOURNAL).read_bytes();state=json.loads(before);item=state['vehicles']['test']
        retained={Path.home()/name:(Path.home()/name/JOURNAL).read_bytes() for name in v.RETAINED_INSTANCE_NAMES}
        require(item['unitId']==UNIT and item['nodeId']==NODE and item['localVmId']==VM and item['runtime']['state']==state['source']['state']=='STOPPED','VISION_PREFLIGHT_SAME_IDLE_TARGET_REQUIRED')
        with runtime_paths.installed_session(native):
            configuration=load_configuration(native);command,environment=launch(native,configuration['cloudPython'],'unit_cloud.py')
            request=dict(unitId=UNIT,nodeId=NODE,systemUid=item['systemUid'],unitSetId=item['unitSetId'],cloudDomain=selected_domain(state),
                oemOwner=cloud_binding(state)['ownerId'],spOwner=configuration['cloudProfiles']['service-provider']['expectedOwnerId'],
                oemCredential=str(configuration['cloudProfiles']['oem-delivery']['credential']),spCredential=str(configuration['cloudProfiles']['service-provider']['credential']))
            observed=subprocess.run([command[0],'-I','-B',str(Path(__file__)),'--sdk',str(tooling)],input=json.dumps(request),capture_output=True,text=True,env=environment,timeout=75)
            require(observed.returncode==0 and len(observed.stdout)<65536,'VISION_PREFLIGHT_SDK_UNAVAILABLE')
            value=json.loads(observed.stdout);require(value.get('ok') is True,value.get('reason','VISION_PREFLIGHT_SDK_FAILED'))
            result.update(value['data'])
        result['journalsUnchanged']=(native/JOURNAL).read_bytes()==before and all((path/JOURNAL).read_bytes()==raw for path,raw in retained.items())
        require(result['journalsUnchanged'],'VISION_PREFLIGHT_STATE_CHANGED')
    except Exception as error:
        result['outcome']='NOT_COMPLETE';value=str(error);result['code']=value if re.fullmatch('[A-Z][A-Z0-9_:.-]{1,160}',value) else type(error).__name__
    finally:
        if native is not None and before is not None:
            result['journalsUnchanged']=(native/JOURNAL).read_bytes()==before and all((path/JOURNAL).read_bytes()==raw for path,raw in retained.items())
    (records/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
    return 0  # Typed result carries success/failure; transport stays collectable.


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--config',type=Path);parser.add_argument('--host',type=Path);parser.add_argument('--sdk',type=Path);parser.add_argument('--node-list-diagnostic',action='store_true');args=parser.parse_args()
    if args.sdk:
        try:
            with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):value=sdk(args.sdk)
            result=dict(ok=True,data=value)
        except Exception as error:
            value=str(error);result=dict(ok=False,reason=value if re.fullmatch('[A-Z][A-Z0-9_:.-]{1,160}',value) else type(error).__name__)
        print(json.dumps(result));return 0
    if args.host:return host(args.host)
    import remote_harness as h
    from vision_vm_campaign import configuration
    c=configuration(args.config);t=c['transport'];name='vision-services-cloud-preflight-02' if args.node_list_diagnostic else 'vision-services-cloud-preflight-01';records=Path(c['records'])/name;remote=Path(c['remoteRoot'])/name
    if args.node_list_diagnostic:
        previous=json.loads((Path(c['records'])/'vision-services-cloud-preflight-01/result.json').read_bytes())
        require(previous['code']=='CLOUD_HTTP_500' and not previous['cloudMutation'],'VISION_PREFLIGHT_DIAGNOSTIC_SCOPE_REQUIRED')
    require(not records.exists(),'VISION_PREFLIGHT_EXISTS_RECONCILE');records.mkdir(mode=0o700)
    source=Path(__file__).resolve();context=dict(packageRoot=c['main']['packageRoot'],baseManifest=c['main']['manifestSha256'],workerSha256=h.digest(source),
        bundle=str(Path(c['remoteRoot'])/'vision-fresh-accept-11/AosEdge Vision Bootstrap 0.5.0.bundle'),bootstrapManifest='e10d77b648b664a8ae5cbe895c428d0ee37578f516c0a62b467161e055118a1c')
    h.atomic(records/'context.json',context);h.remote(t,'umask 077\nmkdir '+shlex.quote(str(remote)),timeout=10)
    options=h.ssh_args(t)[1:-1];options.remove('-T');i=options.index('-b');options[i:i+2]=['-o','BindAddress='+options[i+1]]
    h.run(['/usr/bin/scp',*options,str(source),str(records/'context.json'),t['user']+'@'+t['host']+':'+str(remote)+'/'],timeout=15)
    python=c['main']['packageRoot']+'/demo-artifacts/aosedge-sdv-demo/host-runtime/python/bin/python3.12'
    output=h.remote(t,shlex.join([python,'-I','-B',str(remote/source.name),'--host',str(remote/'context.json')]),timeout=90)
    result=json.loads(output);h.atomic(records/'result.json',result);print(json.dumps(result),flush=True)
    return 0 if result['outcome'].startswith('PASS_') else 1


if __name__=='__main__':raise SystemExit(main())
