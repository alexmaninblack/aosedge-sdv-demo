# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Guest-only closed negative probe; no policy, credential or rootfs mutation."""
import base64
import hashlib
import json
from pathlib import Path
import pwd
import grp
import subprocess


def probe(files,identity_only):
    root=Path('/run/vision-permanent-acceptance')
    pins={name:hashlib.sha256(base64.b64decode(raw)).hexdigest() for name,raw in files.items()}
    assert set(pins)=={'boundary','core-deny'}
    marker=root/'.owner.json'
    executable=root/'exec'
    if not root.exists():
        root.mkdir(mode=0o755)
        subprocess.run(['chcon','--reference=/var/aos/workdirs/sm/runtimes/systemd-slot-camera-access',str(root)],check=True,capture_output=True)
        marker.write_text(json.dumps(pins,sort_keys=True));marker.chmod(0o600)
        executable.mkdir(mode=0o755)
        # /run itself remains nosuid. Only this owned, size-bounded exec view
        # permits the same SELinux entry as /usr/libexec. All files are pinned,
        # root-owned 0555; no set-ID bits, file caps or policy grants are added.
        subprocess.run(['mount','-t','tmpfs','-o','size=4m,mode=0755,nodev,exec,suid','tmpfs',str(executable)],check=True,capture_output=True)
        subprocess.run(['chcon','--reference=/var/aos/workdirs/sm/runtimes/systemd-slot-camera-access',str(executable)],check=True,capture_output=True)
        for name,raw in files.items():
            path=executable/name;path.write_bytes(base64.b64decode(raw));path.chmod(0o555)
            reference='/usr/libexec/aos-camera-ingress-launcher' if name=='boundary' else '/usr/libexec/aos-camera-access-launcher'
            subprocess.run(['chcon','--reference='+reference,str(path)],check=True,capture_output=True)
    assert not root.is_symlink() and root.stat().st_uid==0 and json.loads(marker.read_bytes())==pins
    assert {p.name for p in root.iterdir()}=={'.owner.json','exec'} and executable.is_mount() and not executable.is_symlink()
    mount=next(row.split() for row in Path('/proc/mounts').read_text().splitlines() if row.split()[1]==str(executable))
    assert mount[2]=='tmpfs' and 'nodev' in mount[3].split(',') and not {'nosuid','noexec'}&set(mount[3].split(','))
    assert all(not (executable/name).is_symlink() and (executable/name).stat().st_uid==0
        and (executable/name).stat().st_mode&0o7777==0o555 and hashlib.sha256((executable/name).read_bytes()).hexdigest()==pin for name,pin in pins.items())
    uid=pwd.getpwnam('aos-camera-access').pw_uid;gid=grp.getgrnam('aos-camera-read').gr_gid
    audit=Path('/var/log/audit/audit.log');cursor=audit.stat().st_size
    results={}
    for name in ('boundary','core-deny'):
        unit='vision-permanent-'+('identity-' if identity_only else '')+name
        command=['systemd-run','--quiet','--wait','--unit='+unit,'-p','User=aos-camera-access','-p','Group=aos-camera-read','-p','CapabilityBoundingSet=','-p','AmbientCapabilities=']
        if name=='core-deny' and not identity_only:
            pid=subprocess.check_output(['systemctl','show','aos-camera-ingress','--value','-p','MainPID'],text=True).strip()
            assert pid.isdecimal() and int(pid)>0
            source='/proc/'+pid+'/root/run/credentials/aos-camera-ingress.service'
            assert Path(source,'camera-private-key').is_file()
            command+=['-p','BindReadOnlyPaths='+source+':/run/credentials/aos-camera-ingress.service']
        command += [str(executable/name),str(uid),str(gid)]
        if identity_only:command.append('--identity-only')
        done=subprocess.run(command,text=True,capture_output=True,timeout=20)
        raw=subprocess.check_output(['journalctl','-u',unit,'-n','40','--no-pager','-o','cat'],text=True)
        messages=[]
        for line in raw.splitlines():
            if line.startswith('{'):
                try:messages.append(json.loads(line))
                except ValueError:pass
        status=subprocess.run(['systemctl','show',unit,'-p','Result','-p','ExecMainCode','-p','ExecMainStatus','-p','NoNewPrivileges','-p','SELinuxContext','-p','User','-p','Group'],text=True,capture_output=True)
        results[name]=dict(exit=done.returncode,messages=messages,stderrPresent=bool(done.stderr),
            unit=dict(row.split('=',1) for row in status.stdout.splitlines() if '=' in row),
            execLabel=subprocess.check_output(['ls','-Zd',str(executable/name)],text=True).split()[0])
    with audit.open('rb') as stream:stream.seek(cursor);raw=stream.read(1048577)
    assert len(raw)<=1048576
    return dict(probes=results,identityOnly=identity_only,privateExecMount=True,systemRunMountUnchanged=True,scopedAvcs=[line[:1600] for line in raw.decode(errors='replace').splitlines()
        if 'avc:' in line and ('camera_ingress' in line or 'camera_access_t' in line)])


def cleanup(files):
    root=Path('/run/vision-permanent-acceptance');executable=root/'exec'
    for unit in ('vision-permanent-boundary','vision-permanent-core-deny','vision-permanent-identity-boundary','vision-permanent-identity-core-deny'):
        stopped=subprocess.run(['systemctl','stop',unit],capture_output=True)
        state=subprocess.run(['systemctl','show',unit,'-p','LoadState','-p','MainPID','-p','ActiveState'],capture_output=True,text=True)
        values=dict(row.split('=',1) for row in state.stdout.splitlines() if '=' in row)
        assert values.get('LoadState')=='not-found' or (state.returncode==0 and values.get('MainPID')=='0' and values.get('ActiveState') in ('inactive','failed'))
        subprocess.run(['systemctl','reset-failed',unit],capture_output=True)
    if root.exists():
        assert not root.is_symlink() and root.stat().st_uid==0
        pins={name:hashlib.sha256(base64.b64decode(raw)).hexdigest() for name,raw in files.items()}
        assert json.loads((root/'.owner.json').read_bytes())==pins and {p.name for p in root.iterdir()}=={'.owner.json','exec'}
        if executable.is_mount():subprocess.run(['umount',str(executable)],check=True,capture_output=True)
        assert not executable.is_mount() and not any(executable.iterdir())
        executable.rmdir();(root/'.owner.json').unlink();root.rmdir()
    return dict(temporaryFixturesRemoved=not root.exists(),transientExecUnmounted=not executable.is_mount(),fixtureUnitsStopped=True)


if __name__=='__main__':print(json.dumps(cleanup(FILES) if CLEANUP else probe(FILES,IDENTITY_ONLY)))
