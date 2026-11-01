#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Official SDK signing on SSD; no model execution or Cloud publication."""
import argparse
import base64
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[2]
SERVICES=ROOT.parent/'vision-pilot-services'
BUILD=Path('/Volumes/SDV-Dev/sdv/build/vision-services')
SDK=Path('/Volumes/SDV-Dev/sdv/reproduction-current/sdv/build/builds/cloud-sdk/38de3de0019d7ddfae2f9ad3889d0aa765de6ad285965bf6f35551cda31142d8')


def require(ok,code):
    if not ok:raise ValueError(code)


def worker(role,target):
    from aos_signer.upload_config_v2.batch_configuration import UpdateBundleConfiguration
    from aos_signer.signer.signer import Signer
    sys.path.insert(0,str(ROOT/'apps/demo-orchestrator/src'))
    from aosedge_demo_orchestrator.component_worker import credential_snapshot,credential_identity
    package=runpy.run_path(str(SERVICES/'tools/aos_package.py'))
    source=BUILD/'packages-01'/role;prepared=json.loads((source/'prepared.json').read_bytes())
    require(prepared['role']==role and prepared['signing']==prepared['publication']=='NOT_RUN','VISION_SIGNING_PREPARATION_CHANGED')
    require(Path(os.environ['TMPDIR']).is_relative_to(BUILD/'.tmp'),'VISION_SIGNING_REQUIRES_OWNED_SSD_SCRATCH')
    require(not target.exists(),'VISION_SIGNED_OUTPUT_EXISTS_RECONCILE')
    secret=json.loads(sys.stdin.read(32769))
    require(set(secret)=={'credentialBase64','cloudDomain'} and secret['cloudDomain']=='aoscloud.io','VISION_SIGNING_SELECTED_ACCOUNT_REQUIRED')
    account_raw=base64.b64decode(secret.pop('credentialBase64'),validate=True);require(0<len(account_raw)<=16384,'VISION_SIGNING_CREDENTIAL_LIMIT')
    for name,pin in prepared['files'].items():
        path=source/name;raw=path.read_bytes()
        require(path.is_file() and not path.is_symlink() and len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256']
            and path.stat().st_mode&0o777==pin['mode'],'VISION_SIGNING_INPUT_CHANGED')
    old=Path.cwd()
    try:
        os.chdir(source)
        with tempfile.TemporaryDirectory(prefix='vision-signing-account-',dir=os.environ['TMPDIR']) as private_root:
            credential=Path(private_root)/'account.p12'
            with credential.open('xb') as stream:os.fchmod(stream.fileno(),0o600);stream.write(account_raw)
            del account_raw
            request=dict(credential=str(credential),role='service provider',cloudDomain=secret['cloudDomain'])
            with credential_snapshot(request) as private:
                identity=credential_identity(private);require(identity['domain']=='aoscloud.io' and identity['role']=='service provider','VISION_SIGNING_ACCOUNT_CHANGED')
                config=source/'config.yaml'
                Signer(UpdateBundleConfiguration(config),config,pkcs12_path=private['credential']).process()
                produced=source/'batch.tar.gz'
                observed=package['verify_signed'](produced,Path(private['credential']),role,prepared)
        shutil.copyfile(produced,target);target.chmod(0o444);produced.unlink()
        return dict(outcome='PASS_OFFICIAL_VISION_SERVICE_SIGNATURE',role=role,version='0.1.0',
            sourceRevision=prepared['sourceRevision'],**observed,publication='NOT_RUN')
    finally:os.chdir(old)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--worker',choices=('perception','assessment'));parser.add_argument('--target',type=Path);parser.add_argument('--config',type=Path);parser.add_argument('--selected-account',action='store_true');a=parser.parse_args()
    if a.worker:
        try:
            with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):result=worker(a.worker,a.target)
        except Exception as error:
            value=str(error);result=dict(outcome='NOT_COMPLETE',code=value if value.isupper() and len(value)<120 else type(error).__name__)
        print(json.dumps(result));return 0 if result['outcome'].startswith('PASS_') else 1
    sys.path.insert(0,str(ROOT/'scripts/distribution'));from build_scratch import directory
    require(a.config is not None and a.selected_account,'VISION_SELECTED_ACCOUNT_CONFIGURATION_REQUIRED')
    # The failed first attempt did not sign or publish: it rejected the local
    # staging credential before the SDK. Preserve that receipt, do not retry it.
    prior=json.loads((BUILD/'signed-01/result.json').read_bytes())
    require(prior['publication']=='NOT_RUN' and prior['services']['perception']['code']=='CLOUD_CERTIFICATE_DOMAIN_CHANGED'
        and not list((BUILD/'signed-01').glob('*.tar.gz')),'VISION_PRIOR_SIGNING_RECONCILE_REQUIRED')
    import remote_harness as h
    from vision_vm_campaign import configuration
    import shlex
    c=configuration(a.config)
    export='''import base64,json,pathlib,sys
step='IMPORT_BASE'
package=pathlib.Path(PACKAGE)
sys.path.insert(0,str(package/'aosedge-sdv-demo/apps/demo-orchestrator/src'))
from aosedge_demo_orchestrator import runtime_paths
from aosedge_demo_orchestrator.environment import JOURNAL
from aosedge_demo_orchestrator.status import load_configuration
native=pathlib.Path.home()/'SDV-Vision-Camera-Image-Lab-Data'
step='SELECTED_IDLE_VISION'
before=(native/JOURNAL).read_bytes();state=json.loads(before);item=state['vehicles']['test']
assert item['unitId']=='af6d074a-6ce1-49ba-b613-0476e7b6d1b5' and item['localVmId']=='89273f16-4be0-4b22-b4cb-58d08533c8bc'
assert state['source']['state']==item['runtime']['state']=='STOPPED'
with runtime_paths.installed_session(native):
 step='SELECTED_SP_PROFILE'
 config=load_configuration(native);profile=config['cloudProfiles']['service-provider'];path=pathlib.Path(profile['credential'])
 assert profile['expectedRole']=='service provider' and profile.get('cloudDomain')=='aoscloud.io'
 step='SELECTED_SP_FILE_SCOPE'
 # This is the configured producer account, not a VM/Source client identity.
 # Its existing private account file may be shared across installed profiles.
 assert path.is_absolute() and path.is_relative_to(pathlib.Path.home()) and path.suffix=='.p12'
 step='SELECTED_SP_FILE_MODE'
 assert path.is_file() and not path.is_symlink() and not path.stat().st_mode&0o077 and path.stat().st_size<=16384
 secret=base64.b64encode(path.read_bytes()).decode()
assert (native/JOURNAL).read_bytes()==before
print(json.dumps(dict(credentialBase64=secret,cloudDomain='aoscloud.io')))
'''.replace('PACKAGE',repr(c['main']['packageRoot']))
    python=c['main']['packageRoot']+'/demo-artifacts/aosedge-sdv-demo/host-runtime/python/bin/python3.12'
    # Captured only in process memory and sent to the local signer stdin. Never
    # print, put in evidence, place on argv, or copy a Source/VM identity key.
    wrapper='import json\ntry:\n exec('+repr(export)+')\nexcept Exception as error:\n print(json.dumps(dict(code="VISION_ACCOUNT_"+globals().get("step","IMPORT")+"_"+type(error).__name__)))\n'
    selected=h.remote(c['transport'],shlex.join([python,'-I','-B','-c',wrapper]),timeout=20)
    require(len(selected)<=32768,'VISION_SELECTED_ACCOUNT_LIMIT')
    value=json.loads(selected);require('code' not in value,value.get('code','VISION_ACCOUNT_UNCONFIRMED'))
    failed=json.loads((BUILD/'signed-02/result.json').read_bytes())
    require(failed['services']['perception']['code']=='ValueError' and failed['publication']=='NOT_RUN'
        and not list((BUILD/'signed-02').glob('*.tar.gz'))
        and not any((BUILD/'packages-01'/role/'batch.tar.gz').exists() for role in ('perception','assessment')),'VISION_EMPTY_SIGNING_ATTEMPT_REQUIRED')
    target=BUILD/'signed-03';require(not target.exists(),'VISION_SIGNING_ATTEMPT_EXISTS_RECONCILE');target.mkdir(mode=0o700)
    result=dict(outcome='NOT_COMPLETE',services={},publication='NOT_RUN')
    with directory(BUILD) as scratch:
        for role in ('perception','assessment'):
            path=target/('vision-'+role+'-0.1.0.tar.gz')
            environment=dict(os.environ,TMPDIR=str(scratch),PYTHONDONTWRITEBYTECODE='1')
            observed=subprocess.run([str(SDK/'bin/python3.12'),'-I','-B',str(Path(__file__)),'--worker',role,'--target',str(path)],
                capture_output=True,text=True,env=environment,input=selected,timeout=180)
            require(len(observed.stdout)<16384,'VISION_SIGNING_RESPONSE_LIMIT')
            value=json.loads(observed.stdout);result['services'][role]=value
            (target/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(value),flush=True)
            require(observed.returncode==0 and value['outcome']=='PASS_OFFICIAL_VISION_SERVICE_SIGNATURE','VISION_OFFICIAL_SIGNING_UNCONFIRMED')
    result['outcome']='PASS_TWO_INDEPENDENT_OFFICIAL_VISION_SIGNATURES';result['scratchRemoved']=True
    (target/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(outcome=result['outcome'],publication='NOT_RUN')));return 0


if __name__=='__main__':raise SystemExit(main())
