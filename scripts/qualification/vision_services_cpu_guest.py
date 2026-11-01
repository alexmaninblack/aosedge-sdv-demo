#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Reversible Vision-only IAM cpuInfoPath proof, never an image/Core patch.

The original private IAM configuration never leaves this VM and is not hashed
or logged. Only its exact temporary read-only bind is allowed. Restore native
owners and verify the original bytes/quota before removing owned scratch.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile
import time

CONFIG=Path('/etc/aos/iam.cfg')
UNITS=('aos-cm.service','aos-sm.service','aos-iam.service')
PROBE_SHA='a63e8640b5d9a649adda0773358710fa1ba84ebf828c9e1e7ed97f0281fcab37'


def require(ok,code):
    if not ok:raise ValueError(code)


def call(args,timeout=15):
    value=subprocess.run(args,capture_output=True,text=True,timeout=timeout)
    require(value.returncode==0,'CPU_PROOF_NATIVE_'+Path(args[0]).name.upper().replace('-','_')+'_FAILED');return value.stdout


def unit(name):
    return dict(row.split('=',1) for row in call(['systemctl','show',name,'--property=LoadState,ActiveState,MainPID,NRestarts,User']).splitlines() if '=' in row)


def stop():
    call(['systemctl','stop',*UNITS],30)
    require(all(unit(name).get('MainPID')=='0' and unit(name).get('ActiveState') in ('inactive','failed') for name in UNITS),'CPU_PROOF_OWNERS_NOT_STOPPED')


def start():
    for name in reversed(UNITS):call(['systemctl','start',name],20)
    require(all(unit(name).get('ActiveState')=='active' and int(unit(name).get('MainPID','0'))>0 for name in UNITS),'CPU_PROOF_OWNERS_NOT_STARTED')


def quota():
    matches=[]
    for proc in Path('/proc').iterdir():
        if not proc.name.isdigit():continue
        try:
            if (proc/'comm').read_text().strip()!='vision-camera-probe'[:15]:continue
            values=dict(row.split(':',1) for row in (proc/'status').read_text().splitlines() if ':' in row)
            if list(map(int,values['Uid'].split()))!=[5000]*4:continue
            require(hashlib.sha256((proc/'exe').read_bytes()).hexdigest()==PROBE_SHA,'CPU_PROOF_NATIVE_PROBE_CHANGED')
            rows=[row[3:] for row in (proc/'cgroup').read_text().splitlines() if row.startswith('0::')];require(len(rows)==1,'CPU_PROOF_CGROUP_INVALID')
            value=(Path('/sys/fs/cgroup'+rows[0])/'cpu.max').read_text().split();require(len(value)==2 and all(v.isdigit() for v in value),'CPU_PROOF_QUOTA_INVALID')
            matches.append(list(map(int,value)))
        except (FileNotFoundError,ProcessLookupError):continue
    require(len(matches)<=1,'CPU_PROOF_NATIVE_PROBE_AMBIGUOUS');return matches[0] if matches else None


def await_quota(expected):
    end=time.monotonic()+25
    while time.monotonic()<end:
        value=quota()
        if value==expected:return value
        time.sleep(.3)
    raise ValueError('CPU_PROOF_QUOTA_NOT_CONFIRMED')


def run(projection,canonical=False,writer=False):
    require(Path('/etc/machine-id').read_text().strip()=='89273f164be04b22b4cb58d08533c8bc','CPU_PROOF_SAME_VISION_VM_REQUIRED')
    require(call(['getenforce']).strip()=='Enforcing','CPU_PROOF_ENFORCING_REQUIRED')
    before={name:unit(name) for name in UNITS}
    require(all(v.get('LoadState')=='loaded' and v.get('ActiveState')=='active' and int(v.get('MainPID','0'))>0 for v in before.values()),'CPU_PROOF_HEALTHY_BASELINE_REQUIRED')
    require(before['aos-iam.service']['User'] in ('','root','0'),'CPU_PROOF_IAM_IDENTITY_CHANGED')
    info=CONFIG.lstat();require(stat.S_ISREG(info.st_mode) and info.st_uid==0 and not info.st_mode&0o022,'CPU_PROOF_CONFIG_UNSAFE')
    require(not os.path.ismount(CONFIG),'CPU_PROOF_CONFIG_OTHER_MOUNT')
    original=CONFIG.read_bytes();document=json.loads(original)
    require(type(document.get('nodeInfo')) is dict,'CPU_PROOF_NODE_CONFIG_INVALID')
    node=document['nodeInfo'];require(node.get('maxDmips',node.get('maxDMIPS'))==10000,'CPU_PROOF_NODE_BUDGET_CHANGED')
    require(not any(key.lower()=='cpuinfopath' for key in node),'CPU_PROOF_CUSTOM_CPUINFO_EXISTS')
    original_quota=await_quota([10000,100000])
    text,topology=projection['current']()
    if canonical:text=projection['canonical_profile']()
    # Core uses package IDs only to group records; its public CPUInfo carries
    # counts, not those kernel IDs. The fixed one-package model uses ordinal 0
    # even where sysfs identifies the same package with another numeric ID.
    identities={cpu:((0,cpu) if canonical else (
        int((Path('/sys/devices/system/cpu')/('cpu'+str(cpu))/'topology/physical_package_id').read_text()),
        int((Path('/sys/devices/system/cpu')/('cpu'+str(cpu))/'topology/core_id').read_text()))) for cpu in topology['online']}
    require(projection['project'](text,set(topology['online']),identities)[0]==text,'CPU_PROOF_PROJECTION_NOT_IDEMPOTENT')
    workspace=Path(tempfile.mkdtemp(prefix='aos-vision-cpu-',dir='/run'));workspace.chmod(0o700)
    result=dict(outcome='NOT_COMPLETE',topology=topology,originalNativeQuota=original_quota,coreSourceChanged=False,
        vmResourcesChanged=False,dmipsBudgetChanged=False,nativeCapacityMayRefresh=True,cleanup={})
    bound=False;owners_stopped=False;restored=False;started=time.monotonic()
    dropin=Path('/run/systemd/system/aos-iam.service.d/36-vision-cpuinfo-proof.conf');dropin_text=None
    try:
        projected=workspace/'cpuinfo';projected.write_text(text);projected.chmod(0o644)
        node['cpuInfoPath']=str(projected);candidate=workspace/'iam.cfg';candidate.write_text(json.dumps(document));candidate.chmod(stat.S_IMODE(info.st_mode))
        # Reuse the corresponding existing read-only object types; no policy
        # permissions or modes are widened and only these new files are labelled.
        call(['chcon','--reference=/etc/aos',str(workspace)])
        call(['chcon','--reference=/etc/aos/iam.cfg',str(candidate)])
        call(['chcon','--reference=/etc/aos/iam.cfg' if canonical else '--reference=/proc/cpuinfo',str(projected)])
        if canonical or writer:
            require(not dropin.exists() and not dropin.is_symlink(),'CPU_PROOF_DROPIN_OTHER_OWNER')
            guard=workspace/'guard.py'
            # The production guard is executed by the actual IAM ExecStartPre
            # owner; only its candidate file path differs before the image exists.
            operation='write_profile' if writer else 'check_profile'
            guard_code='import json,pathlib\nprojection={};exec('+repr(projection['__proofSource'])+',projection)\ntry:\n projection['+repr(operation)+'](pathlib.Path('+repr(str(projected))+'))\n result=dict(ok=True)\nexcept Exception as error:\n value=str(error);result=dict(ok=False,code=value if value.isupper() else type(error).__name__)\npathlib.Path('+repr(str(workspace/'guard-result.json'))+').write_text(json.dumps(result))\nif not result["ok"]:raise SystemExit(1)\n'
            guard.write_text(guard_code);guard.chmod(0o444)
            call(['chcon','--reference=/usr/libexec/aos-demo-service-inputs.py',str(guard)])
            dropin.parent.mkdir(mode=0o755,parents=True,exist_ok=True)
            require(not dropin.parent.is_symlink() and dropin.parent.stat().st_uid==0 and not dropin.parent.stat().st_mode&0o022,'CPU_PROOF_DROPIN_DIRECTORY_UNSAFE')
            dropin_text='[Service]\nExecStartPre=/usr/bin/python3 -I -B '+str(guard)+'\n'
            dropin.write_text(dropin_text);dropin.chmod(0o644)
            call(['systemctl','daemon-reload'])
        owners_stopped=True;stop()
        call(['mount','--bind',str(candidate),str(CONFIG)]);bound=True
        call(['mount','-o','remount,bind,ro',str(CONFIG)])
        require(CONFIG.stat().st_ino==candidate.stat().st_ino and CONFIG.read_bytes()==candidate.read_bytes(),'CPU_PROOF_BIND_NOT_CONFIRMED')
        start();owners_stopped=False
        result['projectedNativeQuota']=await_quota([40000,100000])
        result['canonicalProfileAndNativeStartupGuard']=canonical
        result['actualProfileWriterInNativeIAM']=writer
        result['ownersRestartCountZero']=all(unit(name).get('NRestarts')=='0' for name in UNITS)
        require(result['ownersRestartCountZero'],'CPU_PROOF_NATIVE_RESTART_LOOP')
        require(call(['getenforce']).strip()=='Enforcing','CPU_PROOF_POLICY_CHANGED')
        result['outcome']='PASS_TRANSIENT_FOUR_CPU_NATIVE_QUOTA_MAPPING'
    except Exception as error:
        value=str(error);result['code']=value if value.isupper() else type(error).__name__
        # Only fixed owner/result diagnostics; no config, keys, environment,
        # credentials or a broad system journal is emitted.
        result['owners']={name:{key:value for key,value in unit(name).items() if key in ('LoadState','ActiveState','MainPID','NRestarts')} for name in UNITS}
        if (workspace/'guard-result.json').is_file():result['guard']=json.loads((workspace/'guard-result.json').read_bytes())
    finally:
        try:
            if bound:
                owners_stopped=True;stop()
                require(CONFIG.stat().st_ino==candidate.stat().st_ino and CONFIG.read_bytes()==candidate.read_bytes(),'CPU_PROOF_BIND_OWNER_CHANGED')
                call(['umount',str(CONFIG)]);bound=False
            require(CONFIG.read_bytes()==original and not os.path.ismount(CONFIG),'CPU_PROOF_CONFIG_RESTORE_FAILED')
            if dropin_text is not None:
                require(dropin.is_file() and not dropin.is_symlink() and dropin.read_text()==dropin_text,'CPU_PROOF_DROPIN_OWNER_CHANGED')
                dropin.unlink();call(['systemctl','daemon-reload'])
            if owners_stopped:start();owners_stopped=False
            result['restoredNativeQuota']=await_quota([10000,100000]);restored=True
            result['cleanup'].update(originalConfigRestored=True,nativeOwnersHealthy=True,nativeQuotaRestored=True,selinuxEnforcing=call(['getenforce']).strip()=='Enforcing')
            if canonical or writer:result['cleanup']['startupGuardDropinRemoved']=not dropin.exists()
        except Exception as error:
            result['cleanup']['restorationConfirmed']=False;result['restoreCode']=str(error) if str(error).isupper() else type(error).__name__
        if restored:
            require(workspace.parent==Path('/run') and workspace.name.startswith('aos-vision-cpu-') and not workspace.is_symlink(),'CPU_PROOF_SCRATCH_OWNER_CHANGED')
            shutil.rmtree(workspace);result['cleanup']['scratchRemoved']=not workspace.exists()
        result['seconds']=round(time.monotonic()-started,2)
    return result
