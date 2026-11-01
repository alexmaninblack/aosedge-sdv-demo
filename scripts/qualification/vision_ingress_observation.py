#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Guest read-only bounded ingress/native-consumer observation, no key reads."""
import hashlib
import json
import os
from pathlib import Path
import pwd
import grp
import socket
import struct
import subprocess


def run(args):return subprocess.check_output(args,text=True,stderr=subprocess.DEVNULL,timeout=10)


def unit(name):
    return dict(v.split('=',1) for v in run(['systemctl','show',name,'-p','ActiveState','-p','Result','-p','NRestarts','-p','MainPID','-p','ExecMainStatus']).splitlines() if '=' in v)


def health():
    def exchange(value):
        with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as s:
            s.settimeout(2);s.connect('/run/aos-camera-access/oem/producer.sock')
            raw=json.dumps(value,separators=(',',':')).encode();s.sendall(struct.pack('!I',len(raw))+raw)
            def exact(n):
                out=b''
                while len(out)<n:
                    part=s.recv(n-len(out));assert part;out+=part
                return out
            size=struct.unpack('!I',exact(4))[0];assert 0<size<=4096
            return json.loads(exact(size))
    epoch=exchange(dict(schemaVersion=1,operation='hello'))['componentEpoch']
    return exchange(dict(schemaVersion=1,operation='health',componentEpoch=epoch))


def process(pid):
    root=Path('/proc')/str(pid)
    status=dict(v.split(':',1) for v in (root/'status').read_text().splitlines() if ':' in v)
    mounts=[v.split() for v in (root/'mountinfo').read_text().splitlines()]
    camera=[v for v in mounts if v[4]=='/run/aosedge/platform/camera']
    credentials=[v for v in mounts if v[4]=='/run/credentials/aos-camera-ingress.service']
    return dict(pid=pid,uid=int(status['Uid'].split()[0]),gid=int(status['Gid'].split()[0]),
        groups=[int(v) for v in status['Groups'].split()],nnp=status['NoNewPrivs'].strip(),
        capabilities={k:status[k].strip() for k in ('CapEff','CapPrm','CapBnd','CapInh','CapAmb')},
        context=(root/'attr/current').read_text().strip().rstrip('\0'),
        readMount=bool(camera),readMountReadonly=bool(camera) and all('ro' in v[5].split(',') for v in camera),
        credentialEnvironment=any(v.startswith(b'CREDENTIALS_DIRECTORY=') for v in (root/'environ').read_bytes().split(b'\0')),
        credentialMount=bool(credentials),credentialMountReadonly=bool(credentials) and all('ro' in v[5].split(',') for v in credentials))


def observe():
    camera=unit('aos-camera-access');ingress=unit('aos-camera-ingress')
    consumers=[];consumer_errors=[]
    for path in Path('/proc').iterdir():
        if not path.name.isdecimal():continue
        try:
            if Path(os.readlink(path/'exe')).name=='vision-camera-probe':
                row=process(int(path.name));row['binarySha256']=hashlib.sha256((path/'exe').read_bytes()).hexdigest();consumers.append(row)
        except (OSError,ValueError,KeyError) as error:
            try:
                if (path/'comm').read_text().strip()=='vision-camera-p':
                    import traceback
                    frame=traceback.extract_tb(error.__traceback__)[-1]
                    consumer_errors.append(dict(pid=int(path.name),error=type(error).__name__,file=Path(frame.filename).name,line=frame.lineno))
            except OSError:pass
    messages=[];frames=[];network=[];codes=[]
    raw=run(['journalctl','-b','-n','2200','--no-pager','-o','cat'])
    assert len(raw)<2*1024**2
    for line in raw.splitlines():
        if 'CAMERA_INGRESS_' in line:
            at=line.find('CAMERA_INGRESS_');codes.append(line[at:at+120])
        for marker,target in (('{"probe":',messages),('{"ingressFrame":',frames),('{"networkProof":',network)):
            at=line.find(marker)
            if at>=0:
                try:target.append(json.JSONDecoder().raw_decode(line[at:])[0])
                except ValueError:pass
    result=dict(camera=camera,ingress=ingress,consumers=consumers,consumerErrors=consumer_errors,messages=messages[-160:],
        ingressFrames=frames[-450:],networkProofs=network[-12:],fixedCodes=codes[-12:],
        readerGid=grp.getgrnam('aos-camera-read').gr_gid,producerUid=pwd.getpwnam('aos-camera-access').pw_uid,
        enforcing=Path('/sys/fs/selinux/enforce').read_text().strip()=='1')
    tables=json.loads(run(['nft','-j','list','tables']))['nftables']
    result['egressDropPackets']=0
    if any(v.get('table',{}).get('name')=='democtl_vision_camera' for v in tables):
        nft=json.loads(run(['nft','-j','list','table','inet','democtl_vision_camera']))['nftables']
        for entry in nft:
            for expression in entry.get('rule',{}).get('expr',[]):
                if 'counter' in expression:result['egressDropPackets']+=expression['counter']['packets']
    if ingress['ActiveState']=='active' and int(ingress['MainPID'])>0:
        try:result['ingressProcess']=process(int(ingress['MainPID']))
        except OSError:pass
    if camera['ActiveState']=='active':
        result['cameraProcess']=process(int(camera['MainPID']));result['health']=health()
    return result


if __name__=='__main__':print(json.dumps(observe()))
