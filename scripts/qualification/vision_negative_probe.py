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
    if not root.exists():
        root.mkdir(mode=0o755)
        subprocess.run(['chcon','--reference=/var/aos/workdirs/sm/runtimes/systemd-slot-camera-access',str(root)],check=True,capture_output=True)
        marker.write_text(json.dumps(pins,sort_keys=True));marker.chmod(0o600)
        for name,raw in files.items():
            path=root/name;path.write_bytes(base64.b64decode(raw));path.chmod(0o555)
            reference='/usr/libexec/aos-camera-ingress-launcher' if name=='boundary' else '/usr/libexec/aos-camera-access-launcher'
            subprocess.run(['chcon','--reference='+reference,str(path)],check=True,capture_output=True)
    assert not root.is_symlink() and root.stat().st_uid==0 and json.loads(marker.read_bytes())==pins
    assert {p.name for p in root.iterdir()}=={'.owner.json','boundary','core-deny'}
    assert all(not (root/name).is_symlink() and hashlib.sha256((root/name).read_bytes()).hexdigest()==pin for name,pin in pins.items())
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
        command += [str(root/name),str(uid),str(gid)]
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
            execLabel=subprocess.check_output(['ls','-Zd',str(root/name)],text=True).split()[0])
    with audit.open('rb') as stream:stream.seek(cursor);raw=stream.read(1048577)
    assert len(raw)<=1048576
    return dict(probes=results,identityOnly=identity_only,scopedAvcs=[line[:1600] for line in raw.decode(errors='replace').splitlines()
        if 'avc:' in line and ('camera_ingress' in line or 'camera_access_t' in line)])


if __name__=='__main__':print(json.dumps(probe(FILES,IDENTITY_ONLY)))
