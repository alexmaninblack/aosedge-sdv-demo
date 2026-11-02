#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Read-only same-Vision recovery preflight; no send, VM start or catalog write."""
import argparse
import contextlib
import io
import json
from pathlib import Path
import shlex
import subprocess
import sys
import urllib.error
import urllib.request
# Explicit scenario-owned helpers also load under the isolated interpreter;
# never depend on the working directory or an ambient PYTHONPATH.
sys.path.insert(0,str(Path(__file__).resolve().parent))
import remote_harness as h

UNIT='af6d074a-6ce1-49ba-b613-0476e7b6d1b5'
ROOT='40ed2e6e-2aee-45f5-af80-3ab6928771ff'
VERSION='a7aa3468-a135-4dd4-a7d7-59bd1d46c23c'
KIND='aos-vision-vm-1.0.0-main-qemuarm64-rootfs'


def schema_fields(fields):
    return {name:{k:value[k] for k in ('type','required','read_only','min_length','max_length') if k in value}
        for name,value in fields.items()}


def sdk(tooling):
    r=json.loads(sys.stdin.read(32769));sys.path.insert(0,tooling)
    with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
        from aosedge_demo_orchestrator.unit_cloud import Cloud
        from aosedge_demo_orchestrator.component_cloud import unit_view
        cloud=Cloud(dict(credential=r['credential'],cloudDomain='aoscloud.io',ownerId=r['owner']))
        unit=cloud.unit(UNIT,nodes=True)
        h.require(unit['system_uid']==r['identity']['systemUid'] and unit['unit_sets']==[r['identity']['unitSetId']]
            and len(unit['nodes'])==1 and unit['nodes'][0]['id']==r['identity']['nodeId'],'ROOT_RECOVERY_UNIT_CHANGED')
        current=unit_view(cloud,r['identity'],strict=True,component_type=KIND)
        versions=cloud.pages('components/'+ROOT+'/versions/')
        selected=[{k:v.get(k) for k in ('id','version','state','reported_version','is_fake')} for v in versions if v['id']==VERSION]
        sends=cloud.call('units/'+UNIT+'/components/send-requests/')
        h.require(isinstance(sends,list),'ROOT_RECOVERY_SEND_SCHEMA_CHANGED')
        requests=[{k:v.get(k) for k in ('id','component_type','update_component')} for v in sends]
        path='units/'+UNIT+'/components/send-requests/'
        request=urllib.request.Request(cloud.base+path,method='OPTIONS',headers={'Accept':'application/json'})
        try:
            with cloud.opener.open(request,timeout=12) as response:
                raw=response.read(262145);h.require(len(raw)<=262144,'ROOT_RECOVERY_OPTIONS_BOUND')
                value=json.loads(raw);fields=value.get('actions',{}).get('POST',{})
                options=dict(status=response.status,allowed=response.headers.get('Allow'),fields=schema_fields(fields))
        except urllib.error.HTTPError as error:options=dict(status=error.code)
    print(json.dumps(dict(outcome='PASS_READONLY_ROOTFS_RECOVERY_PREFLIGHT',cloudMutation=False,
        vmStarted=False,unit=current,version=selected,sendRequests=requests,sendOptions=options)),flush=True)


def worker(path):
    c=json.loads(path.read_bytes());records=path.parent
    for name,pin in c['files'].items():h.require(h.digest(records/name)==pin,'ROOT_RECOVERY_INPUT_CHANGED')
    package=Path(c['main']['packageRoot']);bundle=Path(c['host']['bundle'])
    h.require(h.digest(package/'application-manifest.json')==c['main']['manifestSha256'],'ROOT_RECOVERY_BASE_CHANGED')
    sys.path.insert(0,str(package/'aosedge-sdv-demo/apps/demo-orchestrator/src'))
    import aosedge_demo_orchestrator
    from aosedge_demo_orchestrator import runtime_paths
    tooling=bundle/'Contents/Resources/tooling/aosedge-sdv-demo/apps/demo-orchestrator/src'
    aosedge_demo_orchestrator.__path__.insert(0,str(tooling/'aosedge_demo_orchestrator'))
    from aosedge_demo_orchestrator import vision_bootstrap as v
    from aosedge_demo_orchestrator.environment import JOURNAL
    from aosedge_demo_orchestrator.cloud_connection import cloud_binding
    from aosedge_demo_orchestrator.cloud_runtime import launch
    from aosedge_demo_orchestrator.status import load_configuration
    verified=v.verify(bundle,c['main']['manifestSha256']);h.require(verified.manifest_sha256==c['host']['manifestSha256'],'ROOT_RECOVERY_HOST_CHANGED')
    native=Path.home()/v.INSTANCE_NAME;state=json.loads((native/JOURNAL).read_bytes());item=state['vehicles']['test']
    h.require(item['unitId']==UNIT and item['localVmId']=='89273f16-4be0-4b22-b4cb-58d08533c8bc'
        and state['source']['state']==item['runtime']['state']=='STOPPED','ROOT_RECOVERY_IDLE_SAME_VISION_REQUIRED')
    retained={Path.home()/n:(Path.home()/n/JOURNAL).read_bytes() for n in (*v.RETAINED_INSTANCE_NAMES,v.INSTANCE_NAME)}
    with runtime_paths.installed_session(native):
        config=load_configuration(native);python,env=launch(native,config['cloudPython'],'unit_cloud.py')
        request=dict(credential=str(config['cloudProfiles']['oem-delivery']['credential']),owner=cloud_binding(state)['ownerId'],
            identity={k:item[k] for k in ('unitId','systemUid','unitSetId','nodeId')})
        done=subprocess.run([python[0],'-I','-B',str(records/Path(__file__).name),'--sdk',str(tooling)],input=json.dumps(request),
            capture_output=True,text=True,env=env,timeout=90)
    h.require(done.returncode==0 and len(done.stdout)<65536,'ROOT_RECOVERY_READONLY_SDK_FAILED')
    result=json.loads(done.stdout);result['allFiveJournalsUnchanged']=all((p/JOURNAL).read_bytes()==raw for p,raw in retained.items())
    h.require(result['allFiveJournalsUnchanged'],'ROOT_RECOVERY_JOURNAL_CHANGED')
    h.atomic(records/'result.json',result);print(json.dumps(result),flush=True)


def main():
    p=argparse.ArgumentParser();p.add_argument('--config',type=Path);p.add_argument('--worker',type=Path);p.add_argument('--sdk')
    p.add_argument('--attempt',type=int,choices=(1,2),default=1);a=p.parse_args()
    if a.sdk:return sdk(a.sdk)
    if a.worker:return worker(a.worker)
    from vision_vm_campaign import configuration
    c=configuration(a.config);name='vision-rootfs-recovery-preflight-%02d'%a.attempt;local=Path(c['records'])/name;remote=Path(c['remoteRoot'])/name
    h.require(not local.exists(),'ROOT_RECOVERY_PREFLIGHT_EXISTS_RECONCILE');local.mkdir(mode=0o700)
    here=Path(__file__).parent;files=[Path(__file__).resolve(),here/'remote_harness.py',here.parent/'distribution/installation_inputs.py']
    context=dict(main=c['main'],host=json.loads((Path(c['records'])/'vision-services-host-05/result.json').read_bytes()),files={f.name:h.digest(f) for f in files})
    h.atomic(local/'context.json',context);h.remote(c['transport'],'umask 077\nmkdir '+shlex.quote(str(remote)),timeout=15)
    options=h.ssh_args(c['transport'])[1:-1];options.remove('-T');i=options.index('-b');options[i:i+2]=['-o','BindAddress='+options[i+1]]
    h.run(['/usr/bin/scp',*options,*map(str,files),str(local/'context.json'),c['transport']['user']+'@'+c['transport']['host']+':'+str(remote)+'/'],timeout=30)
    py=c['main']['packageRoot']+'/demo-artifacts/aosedge-sdv-demo/host-runtime/python/bin/python3.12'
    value=json.loads(h.remote(c['transport'],shlex.join([py,'-I','-B',str(remote/Path(__file__).name),'--worker',str(remote/'context.json')]),timeout=100))
    h.atomic(local/'result.json',value);print(json.dumps(value))


if __name__=='__main__':main()
