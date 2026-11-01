#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Exact transient pending-first-install restore; no immutable guest writes."""
import argparse
import json
from pathlib import Path
import shlex
import remote_harness as h
from vision_vm_campaign import configuration

# Candidate is injected only into the existing projection's in-memory namespace.
# It cannot change persistent material or advance the native component journal.
RESTORE=r'''
def restore_initial_projection(request,trust,item,material,expected):
    require(request['action']=='trust-restore','FIRST_INSTALL_RESTORE_ONLY')
    before=first_install_state()
    persistent={path:value for path,value in expected.items() if path!=DROPIN}
    require(all(read(path,mode)==value for path,(value,mode) in persistent.items()),'FIRST_INSTALL_RESTORE_PERSISTENCE_CHANGED')
    require(not os.path.lexists(DROPIN),'FIRST_INSTALL_RESTORE_DROPIN_CONFLICT')
    validate_material(trust,item,material)
    trust.call(['systemctl','--no-block','stop','aos-sm.service'])
    try:
        deadline=time.monotonic()+20
        while True:
            values=dict(line.split('=',1) for line in trust.call([
                'systemctl','show','aos-sm.service','-p','ActiveState','-p','Job']).splitlines() if '=' in line)
            if values.get('ActiveState')=='inactive' and values.get('Job') in ('','0'):break
            require(time.monotonic()<deadline,'FIRST_INSTALL_WRITER_STOP_TIMEOUT');time.sleep(.25)
        require(first_install_state()==before,'FIRST_INSTALL_STATE_CHANGED')
        require(all(read(path,mode)==value for path,(value,mode) in persistent.items()),'FIRST_INSTALL_RESTORE_PERSISTENCE_CHANGED')
        require(not os.path.lexists(DROPIN),'FIRST_INSTALL_RESTORE_DROPIN_CONFLICT')
        value,mode=expected[DROPIN];trust.write(DROPIN,value,mode)
        require(first_install_state()==before,'FIRST_INSTALL_STATE_CHANGED')
        trust.call(['systemctl','daemon-reload'])
    except BaseException:
        # Preserve an uncertain configuration/result; never erase evidence or
        # rewrite native pending state. The native owner remains authoritative.
        trust.call(['systemctl','--no-block','start','aos-sm.service'])
        raise
    trust.activate_consumers(['aos-sm.service'])
    return dict(configured=True,noOp=False,smRestarted=True,restoredPendingFirstInstall=True,
        persistentEnrollmentUnchanged=True,transactionPreservedAtResume=True,**status(trust))
'''


def main():
    p=argparse.ArgumentParser();p.add_argument('--config',type=Path,required=True);args=p.parse_args();c=configuration(args.config)
    records=Path(c['records'])/'vision-first-restore-proof-01';h.require(not records.exists(),'RESTORE_PROOF_EXISTS_RECONCILE');records.mkdir(mode=0o700)
    python=c['main']['packageRoot']+'/demo-artifacts/aosedge-sdv-demo/host-runtime/python/bin/python3.12'
    code=r'''import json,sys,pathlib,subprocess
main=MAIN;bundle=pathlib.Path(BUNDLE)
subprocess.run(['codesign','--verify','--deep','--strict',str(bundle)],check=True,capture_output=True)
sys.path.insert(0,main['packageRoot']+'/aosedge-sdv-demo/apps/demo-orchestrator/src')
import aosedge_demo_orchestrator
from aosedge_demo_orchestrator import runtime_paths
aosedge_demo_orchestrator.__path__.insert(0,str(bundle/'Contents/Resources/tooling/aosedge-sdv-demo/apps/demo-orchestrator/src/aosedge_demo_orchestrator'))
from aosedge_demo_orchestrator import vision_bootstrap as v,vision_source_guest as projection,source_guest,source_trust_guest
from aosedge_demo_orchestrator.environment import EnvironmentService,JOURNAL
from aosedge_demo_orchestrator.vm import VMService,access_path
from aosedge_demo_orchestrator.guest_access import ssh_command
from aosedge_demo_orchestrator.status import read_json
verified=v.verify(bundle,main['manifestSha256']);native=pathlib.Path.home()/v.INSTANCE_NAME
retained={pathlib.Path.home()/n:(pathlib.Path.home()/n/JOURNAL).read_bytes() for n in v.RETAINED_INSTANCE_NAMES};result={}
with runtime_paths.installed_session(native):
 env=EnvironmentService(catalog=v.SignedVisionCatalog(verified),vm_profile=v.VM_PROFILE);vm=VMService(env)
 try:
  boot=vm.execute('start','test',timeout=150);assert boot['vehicles']['test'].get('reason')=='SOURCE_TRUST_RESTORE_UNCONFIRMED'
  state=read_json(native/JOURNAL);item=state['vehicles']['test'];trust=state['source']['trust']
  request=dict(action='trust-restore',role='test',vmProfile=v.VM_PROFILE,
   vehicle={**{k:item[k] for k in ('localVmId','unitId','nodeId')},'cloud':{'identity':{'nodeHardwareId':item['cloud']['identity']['nodeHardwareId']}}},
   fingerprints={k:trust['fingerprints'][k] for k in ('vdp','runtime')})
  own=pathlib.Path(projection.__file__).read_text()
  marker="        return initial_projection(request,trust,item,material,expected)"
  assert own.count(marker)==1
  own=own.replace(marker,"        if action=='trust-restore':return restore_initial_projection(request,trust,item,material,expected)\n"+marker)+RESTORE
  # Normal trusted helper code and the one exact candidate function live only
  # in this SSH Python process. No guest module/file/policy is replaced.
  script='import types,json\ntrust=types.ModuleType("trust_owner")\nexec('+repr(pathlib.Path(source_trust_guest.__file__).read_text())+',trust.__dict__)\nvision=types.ModuleType("vision_projection")\nexec('+repr(own)+',vision.__dict__)\nrequest='+repr(request)+'\n'
  script+="before=vision.first_install_state()\ntry:\n value=vision.execute(request,trust)\n assert vision.first_install_state()==before\n print(json.dumps(dict(outcome='PASS_TRANSIENT_PENDING_FIRST_RESTORE',facts=value,transactionUnchanged=True,immutableGuestFilesChanged=False)))\nexcept Exception as e:\n print(json.dumps(dict(outcome='NOT_COMPLETE',code=str(e) if isinstance(e,ValueError) and str(e).startswith('VISION_SOURCE_') else type(e).__name__)))\n"
  done=subprocess.run(ssh_command(access_path(native,'test'),item['sshPort'],5),input="python3 - <<'RESTORE'\n"+script+"\nRESTORE\n",capture_output=True,text=True,timeout=65)
  assert done.returncode==0 and len(done.stdout)<8192
  result.update(json.loads(done.stdout))
 finally:
  stopped=vm.execute('stop','test',timeout=150);result['cleanup']=dict(vmStopped=stopped['vehicles']['test']['state']=='COMPLETED',retainedJournalsUnchanged=all((p/JOURNAL).read_bytes()==raw for p,raw in retained.items()))
print(json.dumps(result))
'''.replace('MAIN',repr(c['main'])).replace('BUNDLE',repr(str(Path(c['remoteRoot'])/'signed-bootstrap-04/AosEdge Vision Bootstrap 0.5.0.bundle')))
    # Substitute the candidate token only, not heredoc/diagnostic text.
    code=code.replace('+RESTORE\n','+'+repr(RESTORE)+'\n')
    value=json.loads(h.remote(c['transport'],shlex.quote(python)+' -I -B -c '+shlex.quote(code),timeout=240))
    h.atomic(records/'result.json',value);print(json.dumps(value,indent=2))


if __name__=='__main__':main()
