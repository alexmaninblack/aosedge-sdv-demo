# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Closed read/recovery-marker probe; never reads keys or update-state contents."""
import gzip
import hashlib
import io
import json
from pathlib import Path
import pwd
import shlex
import shutil
import subprocess
import struct
import time

CAMERA=Path('/var/aos/workdirs/sm/runtimes/systemd-slot-camera-access')
MARKER=Path('/var/aos/workdirs/.vision-delivery-recovery-probe')


def call(args):
    return subprocess.check_output(args,text=True,stderr=subprocess.DEVNULL,timeout=12)


def snapshot():
    end=time.monotonic()+25
    while True:
        unit=dict(v.split('=',1) for v in call(['systemctl','show','aos-camera-access','-p','ActiveState','-p','Result','-p','NRestarts']).splitlines())
        if unit['ActiveState']=='active' or time.monotonic()>end:break
        time.sleep(.25)
    installed=json.loads((CAMERA/'state/installed.json').read_bytes())
    selected={k:installed[k] for k in ('version','slot','itemId','manifestDigest','runtimeId','preinstalled') if k in installed}
    assert selected and unit['ActiveState']=='active' and unit['Result']=='success' and unit['NRestarts']=='0','CAMERA_BASELINE_NOT_HEALTHY'
    assert not (CAMERA/'state/transaction.json').exists(),'CAMERA_TRANSACTION_PENDING'
    assert call(['/usr/libexec/aos-camera-access-store-check','verify']).strip()=='Camera Access isolated component store is ready.'
    root_home=Path(pwd.getpwnam('root').pw_dir)
    # Resolve only public effective SSH paths; never read private key bytes.
    options=[];defaults=Path('/etc/default/ssh')
    if defaults.exists():
        for line in defaults.read_text().splitlines():
            if line.startswith('SSHD_OPTS='):
                text=line.split('=',1)[1].strip().strip('\"\'');args=shlex.split(text)
                if '-f' in args:options=['-f',args[args.index('-f')+1]]
    effective=call([shutil.which('sshd') or '/usr/sbin/sshd','-T',*options])
    keys=[Path(v.split(' ',1)[1]).resolve() for v in effective.splitlines() if v.startswith('hostkey ')]
    assert keys and all(v.is_file() for v in keys),'SSH_PERSISTENCE_UNOBSERVABLE'
    def mount_for(path):
        rows=[v.split() for v in Path('/proc/mounts').read_text().splitlines()]
        choices=[v for v in rows if path==Path(v[1]) or Path(v[1]) in path.parents]
        row=max(choices,key=lambda v:len(v[1]))
        return row[1]
    roots=call(['findmnt','--noheadings','--output','UUID','--target',str(CAMERA)]).strip()
    assert len(roots)==36,'CAMERA_STORE_UUID_UNOBSERVABLE'
    parameters={}
    for item in shlex.split(Path('/proc/cmdline').read_text()):
        key,_,value=item.partition('=')
        if key in ('aosupdate.disk','aosupdate.device','aosupdate.path','aosupdate.selinux_module'):
            assert len(value)<200 and value.startswith(('/','sm/')),'UPDATE_PARAMETER_UNEXPECTED'
            parameters[key]=value
    return dict(machineId=Path('/etc/machine-id').read_text().strip(),
        rootfsVersion=Path('/etc/aos/version').read_text().strip(),camera=selected,
        cameraInstalledMetadataSha256=hashlib.sha256((CAMERA/'state/installed.json').read_bytes()).hexdigest(),
        cameraPayloadSha256=hashlib.sha256((CAMERA/'active/bin/camera-access').read_bytes()).hexdigest(),
        cameraStoreUuid=roots,cameraUnit=unit,provisioned=Path('/var/aos/.provisionstate').exists(),
        enforcing=Path('/sys/fs/selinux/enforce').read_text().strip()=='1',
        markerPresent=MARKER.exists(),rootHomeMount=mount_for(root_home),
        authorizedKeysPresent=(root_home/'.ssh/authorized_keys').is_file(),
        sshHostKeyMounts=sorted(set(mount_for(p) for p in keys)),updateParameters=parameters)


def archive_helpers(raw):
    if raw.startswith(b'\x1f\x8b'):
        with gzip.GzipFile(fileobj=io.BytesIO(raw)) as stream:raw=stream.read(256*1024**2+1)
    assert len(raw)<=256*1024**2,'INITRAMFS_LIMIT'
    offset=0;helpers={}
    while offset+110<=len(raw):
        header=raw[offset:offset+110];assert header[:6] in (b'070701',b'070702'),'INITRAMFS_FORMAT_UNKNOWN'
        size=int(header[54:62],16);namesize=int(header[94:102],16)
        assert 0<namesize<=4096 and offset+110+namesize<=len(raw)
        name=raw[offset+110:offset+110+namesize-1].decode()
        assert not name.startswith('/') and '..' not in Path(name).parts,'INITRAMFS_UNSAFE_NAME'
        start=(offset+110+namesize+3)&~3;end=start+size;assert end<=len(raw)
        if name=='TRAILER!!!':break
        module=Path(name).name
        module={'95-aosupdate':'aosupdate','96-machineid':'machineid','05-opendisk':'opendisk','02-vardir':'vardir'}.get(module,module)
        if module in ('aosupdate','machineid','opendisk','vardir'):
            helpers[module]=hashlib.sha256(raw[start:end]).hexdigest()
        offset=(end+3)&~3
    return helpers


def boot_inventory():
    root=Path('/run/vision-delivery-boot-readonly');assert not root.exists();root.mkdir(mode=0o700)
    mounted=False
    try:
        call(['mount','-o','ro,nodev,nosuid,noexec','/dev/sda1',str(root)]);mounted=True
        files=[];images=[]
        for p in sorted(root.rglob('*')):
            if not p.is_file() or p.is_symlink():continue
            relative=p.relative_to(root).as_posix();files.append(relative)
            if 'initrd' in p.name.lower() or 'initramfs' in p.name.lower():
                assert p.stat().st_size<=128*1024**2
                raw=p.read_bytes();images.append(dict(path=relative,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),helpers=archive_helpers(raw)))
            elif p.suffix.lower()=='.efi':
                assert p.stat().st_size<=128*1024**2
                raw=p.read_bytes()
                if raw[:2]!=b'MZ':continue
                pe=struct.unpack_from('<I',raw,0x3c)[0]
                assert raw[pe:pe+4]==b'PE\0\0'
                count=struct.unpack_from('<H',raw,pe+6)[0];optional=struct.unpack_from('<H',raw,pe+20)[0]
                for n in range(count):
                    at=pe+24+optional+40*n;name=raw[at:at+8].rstrip(b'\0')
                    if name!=b'.initrd':continue
                    size,start=struct.unpack_from('<II',raw,at+16);assert start+size<=len(raw)
                    initrd=raw[start:start+size]
                    images.append(dict(path=relative+':.initrd',bytes=len(initrd),sha256=hashlib.sha256(initrd).hexdigest(),helpers=archive_helpers(initrd)))
        return dict(bootFiles=files,initramfs=images,readOnlyInspection=True,bootChanged=False)
    finally:
        if mounted:call(['umount',str(root)])
        root.rmdir()


def run(action):
    if action=='boot-inventory':return boot_inventory()
    if action=='marker-create':
        assert not MARKER.exists() and not MARKER.is_symlink(),'RECOVERY_MARKER_COLLISION'
        with MARKER.open('x') as stream:stream.write('non-secret stopped-VM recovery proof\n')
        MARKER.chmod(0o600)
        subprocess.run(['sync'],check=True,timeout=10)
        return dict(markerWritten=MARKER.is_file())
    assert action=='snapshot','DELIVERY_PROBE_ACTION_INVALID'
    return snapshot()
