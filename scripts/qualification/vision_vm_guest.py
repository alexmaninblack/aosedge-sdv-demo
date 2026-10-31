# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Bounded guest diagnostics; no provisioning, policy edits or motion access."""
import json
import os
import stat
from pathlib import Path
import shutil
import subprocess
import tempfile
import time

STAGE='platform'
FACTS={}


def run(args, timeout=10):
    return subprocess.run(args, capture_output=True, text=True, timeout=timeout)


def check(ok, code):
    if not ok:raise ValueError(code)


def copy_dependency(source, target):
    """Preserve native file modes, especially the executable ELF interpreter."""
    source=Path(source);target=Path(target)
    shutil.copyfile(source,target)
    target.chmod(stat.S_IMODE(source.stat().st_mode))
    check(stat.S_IMODE(target.stat().st_mode)==stat.S_IMODE(source.stat().st_mode),'GUEST_FIXTURE_MODE_CHANGED')


def main():
    global STAGE
    check(os.uname().machine=='aarch64', 'GUEST_ARCH_CHANGED')
    cpus=len(os.sched_getaffinity(0))
    memory=int(next(r.split()[1] for r in Path('/proc/meminfo').read_text().splitlines() if r.startswith('MemTotal:')))
    FACTS.update(cpus=cpus,memoryKiB=memory,architecture=os.uname().machine)
    check(cpus==4 and 3700000<=memory<=4250000, 'GUEST_RESOURCES_WRONG')
    check(run(['getenforce']).stdout.strip()=='Enforcing', 'GUEST_SELINUX_NOT_ENFORCING')
    controllers=Path('/sys/fs/cgroup/cgroup.controllers').read_text().split()
    check({'cpu','memory','pids','io'}<=set(controllers), 'GUEST_CGROUP_CONTROLLERS_MISSING')
    check(run(['crun','--version']).returncode==0, 'GUEST_CRUN_UNAVAILABLE')
    check(not Path('/var/aos/.provisionstate').exists(), 'GUEST_NOT_CLEAN_FACTORY')
    STAGE='container-bundle'
    root=Path(tempfile.mkdtemp(prefix='sdv-vision-vm-', dir='/run'))
    container='sdv-vision-vm-proof'
    owned=False
    cleaned=False
    try:
        for name in ('bin','lib','usr/lib','proc','dev'):(root/'rootfs'/name).mkdir(parents=True,exist_ok=True)
        copy_dependency('/bin/busybox',root/'rootfs/bin/busybox')
        for directory in ('lib','usr/lib'):
            for name in ('libc.so.6','libm.so.6','ld-linux-aarch64.so.1'):
                copy_dependency('/'+directory+'/'+name,root/'rootfs'/directory/name)
        FACTS['loaderExecutable']=bool((root/'rootfs/lib/ld-linux-aarch64.so.1').stat().st_mode & 0o111)
        check(FACTS['loaderExecutable'],'GUEST_FIXTURE_LOADER_NOT_EXECUTABLE')
        script='echo PID=$$; echo HOST=$(/bin/busybox hostname); for ns in mnt pid ipc uts net; do echo NS-$ns=$(/bin/busybox readlink /proc/self/ns/$ns); done; if /bin/busybox pwd; then exit 42; else echo SECCOMP=blocked; fi'
        spec=dict(ociVersion='1.0.2',process=dict(terminal=False,user=dict(uid=0,gid=0),
            args=['/bin/busybox','sh','-c',script],env=['PATH=/bin'],cwd='/',noNewPrivileges=True),
            root=dict(path='rootfs',readonly=True),hostname='sdv-vision-vm-proof',
            mounts=[dict(destination='/proc',type='proc',source='proc')],
            linux=dict(namespaces=[dict(type=n) for n in ('mount','pid','ipc','uts','network')],
                seccomp=dict(defaultAction='SCMP_ACT_ALLOW',syscalls=[dict(names=['getcwd'],action='SCMP_ACT_ERRNO',errnoRet=1)])))
        (root/'config.json').write_text(json.dumps(spec))
        owned=True
        STAGE='crun-execution'
        result=run(['crun','--root',str(root/'state'),'run','--bundle',str(root),container],timeout=15)
        FACTS['crunExit']=result.returncode
        FACTS['crunDiagnostic']=[s for s in ('Permission denied','Operation not permitted','No such file','mount','seccomp','SELinux') if s.lower() in result.stderr.lower()]
        check(result.returncode==0,'GUEST_OCI_EXECUTION_FAILED')
        values=dict(line.split('=',1) for line in result.stdout.splitlines() if '=' in line)
        check(values.get('PID')=='1' and values.get('HOST')==container and values.get('SECCOMP')=='blocked','GUEST_OCI_ISOLATION_WRONG')
        check(all(values.get('NS-'+ns)!=os.readlink('/proc/self/ns/'+ns) for ns in ('mnt','pid','ipc','uts','net')), 'GUEST_NAMESPACES_NOT_ISOLATED')
        state=run(['crun','--root',str(root/'state'),'list','--format=json'])
        check(state.returncode==0 and json.loads(state.stdout)==[],'GUEST_OCI_CLEANUP_UNCONFIRMED')
        cleaned=True
    finally:
        if not owned or cleaned:shutil.rmtree(root)
    check(run(['getenforce']).stdout.strip()=='Enforcing','GUEST_POLICY_CHANGED')
    print(json.dumps(dict(architecture='aarch64',cpus=cpus,memoryKiB=memory,selinux='Enforcing',
        cgroupControllers=controllers,crunExecution=True,namespaceIsolation=True,seccompDeny=True,
        ownContainerRemoved=cleaned,unprovisioned=True,guestEpoch=time.time(),pythonVersion=list(__import__('sys').version_info[:3]),
        modelExecution='NOT_RUN',nativeAosDeployment='NOT_RUN')))


if __name__=='__main__':
    try:main()
    except Exception as error:
        reason=str(error)
        print(json.dumps(dict(outcome='FAIL',stage=STAGE,facts=FACTS,errno=getattr(error,'errno',None),
            code=reason if reason.isupper() and reason.replace('_','').isalnum() else type(error).__name__)))
        raise SystemExit(1)
