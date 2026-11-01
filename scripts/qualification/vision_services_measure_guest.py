#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Ephemeral nonroot closure measurement on the retained Vision guest only.

This is deliberately not an Aos/native-resource or live-camera proof. Native
allocation, policy and end-to-end acceptance remain separate required gates.
"""
import hashlib
import contextlib
import json
import os
import pwd
from pathlib import Path,PurePosixPath
import shutil
import subprocess
import tarfile
import tempfile
import time

BASE=Path('/var/aos/workdirs/vision-services-measure-inputs')


def require(ok,code):
    if not ok:raise ValueError(code)


def digest(path):
    result=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(4*1024**2),b''):result.update(block)
    return result.hexdigest()


def extract(archive,manifest,root):
    expected={row['path']:row for row in manifest['files']};seen=set()
    require(len(expected)==manifest['count']<10000,'MANIFEST_FILE_SET_INVALID')
    with tarfile.open(archive) as source:
        for row in source:
            relative=PurePosixPath(row.name)
            require(row.isfile() and not relative.is_absolute() and '..' not in relative.parts and row.name not in seen and row.name in expected,'CLOSURE_MEMBER_UNSAFE')
            pin=expected[row.name];require(row.size==pin['bytes'],'CLOSURE_MEMBER_SIZE_CHANGED');seen.add(row.name)
            target=root/relative;target.parent.mkdir(parents=True,exist_ok=True)
            with source.extractfile(row) as stream,target.open('xb') as output:shutil.copyfileobj(stream,output)
            require(digest(target)==pin['sha256'],'CLOSURE_MEMBER_DIGEST_CHANGED');target.chmod(0o555 if row.mode&0o111 else 0o444)
    require(seen==set(expected),'CLOSURE_MEMBER_MISSING')


def run(request):
    require(Path('/etc/machine-id').read_text().strip()=='89273f164be04b22b4cb58d08533c8bc','SAME_VISION_VM_REQUIRED')
    require(subprocess.check_output(['getenforce'],text=True).strip()=='Enforcing','ENFORCING_REQUIRED')
    account=pwd.getpwnam('nobody');require(account.pw_uid==account.pw_gid==65534,'MEASUREMENT_UNPRIVILEGED_ACCOUNT_CHANGED')
    require(not BASE.is_symlink() and BASE.is_dir(),'MEASUREMENT_STORAGE_INVALID')
    require(set(request)=={'artifacts','probeSha256'} and set(request['artifacts'])=={'perception','assessment'},'MEASUREMENT_REQUEST_INVALID')
    probe=BASE/('runtime_measurement-'+request['probeSha256'][:16]+'.py');require(digest(probe)==request['probeSha256'],'MEASUREMENT_SOURCE_CHANGED')
    for role,pin in request['artifacts'].items():
        require(set(pin)=={'bytes','sha256','manifestSha256'},'MEASUREMENT_PIN_INVALID')
        archive=BASE/(role+'-rootfs.tar.gz');manifest=BASE/(role+'-closure.json')
        require(archive.stat().st_size==pin['bytes'] and digest(archive)==pin['sha256'] and digest(manifest)==pin['manifestSha256'],'MEASUREMENT_INPUT_CHANGED')
    # The retained native workdirs LV is deliberately small. Measurement must
    # not consume or resize it. The temporary, unprovisioned runtime root uses
    # RAM-backed /run; this is runtime execution, not a compilation/build input.
    runtime=Path('/run/aos-vision-services-measure');runtime.mkdir(mode=0o755,exist_ok=True)
    require(not runtime.is_symlink() and runtime.stat().st_uid==0 and not runtime.stat().st_mode&0o022,'MEASUREMENT_SCRATCH_INVALID')
    scratch=runtime/'.tmp';scratch.mkdir(mode=0o755,exist_ok=True)
    require(not scratch.is_symlink() and shutil.disk_usage(scratch).free>=512*1024**2,'MEASUREMENT_TMPFS_CAPACITY')
    memory=int(next(row.split()[1] for row in Path('/proc/meminfo').read_text().splitlines() if row.startswith('MemAvailable:')))*1024
    require(memory>=2*1024**3,'MEASUREMENT_MEMORY_CAPACITY')
    started=time.monotonic();result=dict(outcome='NOT_COMPLETE',roles={},nativeAos='NOT_RUN',liveCamera='NOT_RUN',policyChanged=False,cleanup={})
    active=None;workspace=None;units={}
    def stop_owned(unit):
        subprocess.run(['systemctl','stop',unit],capture_output=True,timeout=10)
        state=subprocess.run(['systemctl','show',unit,'--property=MainPID,ActiveState'],capture_output=True,text=True,timeout=5)
        require('MainPID=0' in state.stdout and ('ActiveState=inactive' in state.stdout or 'ActiveState=failed' in state.stdout),'MEASUREMENT_STOP_UNCONFIRMED')
        subprocess.run(['systemctl','reset-failed',unit],capture_output=True,timeout=5)
    def quiesce():
        nonlocal active
        if active:stop_owned(active);active=None
    try:
        with contextlib.ExitStack() as lifecycle:
            temporary=lifecycle.enter_context(tempfile.TemporaryDirectory(prefix='closure-',dir=scratch))
            workspace=Path(temporary);workspace.chmod(0o755)
            # LIFO: prove the owned unit stopped before deleting its root.
            lifecycle.callback(quiesce)
            for role,pin in request['artifacts'].items():
                root=workspace/role;root.mkdir(mode=0o755)
                manifest=json.loads((BASE/(role+'-closure.json')).read_bytes());require(manifest['licenseNoticesIncluded'],'LICENSE_CLOSURE_REQUIRED')
                extract(BASE/(role+'-rootfs.tar.gz'),manifest,root)
                shutil.copyfile(probe,root/'probe.py');(root/'probe.py').chmod(0o444)
                for folder in ('proc','sys','dev','run','tmp','etc'): (root/folder).mkdir(mode=0o755,exist_ok=True)
                unit='aos-vision-closure-measure-'+role
                state=subprocess.run(['systemctl','show',unit,'--property=LoadState','--value'],capture_output=True,text=True,timeout=5)
                require(state.stdout.strip()=='not-found','MEASUREMENT_UNIT_OTHER_OWNER')
                properties=dict(User='nobody',Group='65534',RootDirectory=str(root),MountAPIVFS='yes',NoNewPrivileges='yes',
                    CapabilityBoundingSet='',AmbientCapabilities='',PrivateNetwork='yes',PrivateTmp='yes',PrivateDevices='yes',ProtectSystem='strict',
                    ProtectHome='yes',ProtectKernelTunables='yes',ProtectKernelModules='yes',ProtectKernelLogs='yes',ProtectControlGroups='yes',
                    RestrictSUIDSGID='yes',LockPersonality='yes',RestrictAddressFamilies='AF_UNIX',SocketBindDeny='any',
                    CPUAccounting='yes',MemoryAccounting='yes',CPUQuota='300%',MemoryMax='1536M' if role=='perception' else '256M',
                    TasksMax='64',RuntimeMaxSec='75s',TimeoutStopSec='5s',UMask='0077',WorkingDirectory='/')
                # This guest supports normal Source-owned /run units, while
                # its transient D-Bus/FD-passing start rejected systemd-run.
                # Keep exactly the same isolation, no policy/capability change.
                output=workspace/(role+'.stdout');error=workspace/(role+'.stderr')
                unitfile=Path('/run/systemd/system')/(unit+'.service');require(not unitfile.exists() and not unitfile.is_symlink(),'MEASUREMENT_UNIT_FILE_CONFLICT')
                text='[Unit]\nDescription=Isolated Vision closure measurement\n[Service]\nType=exec\n'+''.join(key+'='+value+'\n' for key,value in properties.items())
                text+='Environment=OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 LANG=C.UTF-8 PATH=/usr/bin\n'
                text+='StandardOutput=file:'+str(output)+'\nStandardError=file:'+str(error)+'\nExecStart=/usr/bin/python3.12 -I -B /probe.py '+role+'\n'
                unitfile.write_text(text);unitfile.chmod(0o644);units[unit]=(unitfile,text)
                subprocess.run(['systemctl','daemon-reload'],check=True,capture_output=True,timeout=10)
                active=unit;execution=subprocess.run(['systemctl','start',unit],capture_output=True,text=True,timeout=15)
                end=time.monotonic()+80
                while execution.returncode==0:
                    status=subprocess.check_output(['systemctl','show',unit,'--property=ActiveState','--value'],text=True,timeout=5).strip()
                    if status in ('inactive','failed'):break
                    require(time.monotonic()<end,'MEASUREMENT_EXECUTION_TIMEOUT');time.sleep(.2)
                details=subprocess.run(['systemctl','show',unit,'--property=Result,ExecMainStatus,MemoryPeak,CPUUsageNSec'],capture_output=True,text=True,timeout=5)
                stdout=output.read_text()[-8192:] if output.exists() else ''
                stderr=error.read_text()[-8192:] if error.exists() else ''
                if execution.returncode or 'Result=success\n' not in details.stdout or 'ExecMainStatus=0\n' not in details.stdout:
                    # This fresh root has no credentials. Keep bounded loader /
                    # Python diagnostics, not a system-wide journal or process list.
                    avc=subprocess.run(['ausearch','-m','AVC,USER_AVC','-ts','recent'],capture_output=True,text=True,timeout=5)
                    scoped=[line for line in avc.stdout.splitlines() if any(word in line for word in ('aos-vision-closure','probe.py','python3.12','closure-measure'))]
                    result['roles'][role]=dict(exit=execution.returncode,stdout=stdout,stderr=stderr,startError=execution.stderr[-2048:],unit=details.stdout[-4096:],scopedAvc=scoped[-20:])
                    raise ValueError('ISOLATED_CLOSURE_EXECUTION_FAILED')
                observed=json.loads(stdout);require(observed['outcome']=='PASS_SYNTHETIC_ARM64_CLOSURE_MEASUREMENT','MEASUREMENT_UNCONFIRMED')
                result['roles'][role]=observed
                stop_owned(unit);active=None
            result['outcome']='PASS_ISOLATED_ARM64_CLOSURE_MEASUREMENTS'
        result['cleanup']['scratchRemoved']=not workspace.exists()
    except Exception as error:result['code']=str(error) if str(error).isupper() else type(error).__name__
    finally:
        if active:
            stop_owned(active)
        for unit,(unitfile,text) in units.items():
            require(unitfile.is_file() and not unitfile.is_symlink() and unitfile.read_text()==text,'MEASUREMENT_UNIT_OWNER_CHANGED');unitfile.unlink()
        if units:subprocess.run(['systemctl','daemon-reload'],check=True,capture_output=True,timeout=10)
        result['cleanup']['measurementProcessesStopped']=all(subprocess.run(['systemctl','is-active','--quiet','aos-vision-closure-measure-'+role]).returncode!=0 for role in request['artifacts'])
        result['cleanup']['scratchRemoved']=workspace is None or not workspace.exists()
        result['cleanup']['temporaryUnitsRemoved']=all(not path.exists() for path,_ in units.values())
        result['nativeStorage']=dict(workdirsFreeBytes=shutil.disk_usage(BASE).free,runtimeTmpfs=True,vmMemoryIncreased=False,volumesChanged=False)
        result['seconds']=round(time.monotonic()-started,2)
    return result
