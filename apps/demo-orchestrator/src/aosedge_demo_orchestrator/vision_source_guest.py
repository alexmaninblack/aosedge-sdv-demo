# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Closed Vision projection for the existing Source/SM trust owner.

No Camera producer credential, VDP unit, motion command or rootfs change. The
selected-platform leaf remains an enrollment identity, not a Camera daemon key.
"""
import hashlib
import json
import os
from pathlib import Path
import ssl
import stat
import time
import re
import pwd
import grp
import socket
import struct
from uuid import UUID

PROFILE = 'aos-vision-main-qemuarm64-v1'
RUNTIME = Path('/var/aos/workdirs/sm/runtimes/systemd-slot-camera-access')
INPUTS = RUNTIME/'demo-inputs'
STORE = Path('/var/aos/iam/vehicle-state')
DROPIN = Path('/run/systemd/system/aos-sm.service.d/85-democtl-viss-mtls.conf')
CAMERA_UNIT='aos-camera-ingress.service'
CAMERA_SELECTION=Path('/run/democtl-source/camera-selection.json')
CAMERA_DROPIN=Path('/run/systemd/system/aos-camera-ingress.service.d/85-democtl-camera-mtls.conf')
CAMERA_EGRESS='democtl_vision_camera'
EXCHANGE_UNIT='aos-vision-exchange.service'
EXCHANGE_SELECTION=Path('/run/democtl-source/vision-selection.json')
EXCHANGE_DROPIN=Path('/run/systemd/system/aos-vision-exchange.service.d/85-democtl-vision-mtls.conf')
EXCHANGE_EGRESS='democtl_vision_exchange'
EXCHANGE_SCOPES=['vision-context-read','vision-assessment-publish']
EXCHANGE_ROLES=('perception-publish','perception-read','context-read','assessment-publish')


def require(ok, code):
    if not ok:
        raise ValueError('VISION_SOURCE_'+code)


def identity(request, provisioned=True):
    require(request.get('vmProfile') == PROFILE and request.get('role') == 'test', 'PROFILE_REQUIRED')
    entries = [v for v in json.loads(Path('/etc/aos/sm.cfg').read_bytes())['runtimes']
               if v['plugin'] == 'systemd-slot-component']
    require(len(entries) == 1 and entries[0]['type'] == 'aos-vision-vm-1.0.0-main-qemuarm64-camera-access'
            and entries[0]['config']['workingDir'] == str(RUNTIME)
            and entries[0]['config']['componentProfile'] == 'camera-access-v1', 'TARGET_MISMATCH')
    item = request['vehicle']
    hardware = UUID(item['localVmId']).hex
    require(Path('/etc/machine-id').read_text().strip() == hardware, 'GUEST_IDENTITY_MISMATCH')
    if provisioned:
        require(item['cloud']['identity']['nodeHardwareId'] == hardware, 'CLOUD_IDENTITY_MISMATCH')
        for key in ('unitId', 'nodeId'):
            require(str(UUID(item[key])) == item[key], 'CLOUD_IDENTITY_MISMATCH')
    return item, hardware


def read(path, mode):
    require(not any(p.is_symlink() for p in (path, *path.parents)), 'FILE_LINKED')
    info = path.stat()
    require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_uid == 0
            and stat.S_IMODE(info.st_mode) == mode and 0 < info.st_size < 16384, 'FILE_UNSAFE')
    return path.read_text()


def native_store(trust):
    """Read-only verification of the exact native Camera filesystem owner.

    Workdirs forces one SELinux context. Camera therefore has its own fixed
    loop/ext4 backend; Source must neither mount it nor accept a plain folder.
    The immutable bootstrap verifier checks backing inode, UUID and options.
    """
    parent=Path('/var/aos/workdirs')
    require(not any(p.is_symlink() for p in (RUNTIME,*RUNTIME.parents)), 'STORE_LINKED')
    mounts=[line.split()[:3] for line in Path('/proc/mounts').read_text().splitlines()]
    require(['/dev/mapper/aosvg-workdirs',str(parent),'ext4'] in mounts
            and os.path.ismount(parent), 'NATIVE_VOLUME_NOT_MOUNTED')
    info=RUNTIME.stat()
    require(stat.S_ISDIR(info.st_mode) and info.st_uid==0 and not info.st_mode&0o022
            and info.st_dev!=parent.stat().st_dev and os.path.ismount(RUNTIME), 'NATIVE_STORE_UNSAFE')
    require(trust.call(['/usr/libexec/aos-camera-access-store-check','verify']).strip()==
            'Camera Access isolated component store is ready.', 'NATIVE_STORE_IDENTITY_INVALID')


def status(trust):
    values = dict(line.split('=', 1) for line in trust.call([
        'systemctl', 'show', 'aos-sm.service', '--property=ActiveState,Result,NRestarts']).splitlines() if '=' in line)
    return dict(mutualTlsConfigured=DROPIN.is_file() and (INPUTS/'viss-update-binding').is_file(),
                platform='camera-access', updateRuntime=values, vdpInstalled=False)


def camera_egress_rules(uid,*,table=CAMERA_EGRESS):
    require(type(uid) is int and uid>0,'CAMERA_EGRESS_UID_INVALID')
    require(table in (CAMERA_EGRESS,EXCHANGE_EGRESS),'EGRESS_TABLE_INVALID')
    owner={'match':{'op':'==','left':{'meta':{'key':'skuid'}},'right':uid}}
    base=dict(family='inet',table=table,chain='output')
    return [dict(base,expr=[owner,
        {'match':{'op':'==','left':{'payload':{'protocol':'ip','field':'daddr'}},'right':'10.0.0.1'}},
        {'match':{'op':'==','left':{'payload':{'protocol':'tcp','field':'dport'}},'right':6443}},
        {'accept':None}]),dict(base,expr=[owner,{'counter':None},{'drop':None}])]


def camera_egress_observed_rule(rule):
    """Normalize only native counter values; refuse any other rule change."""
    value={k:v for k,v in rule.items() if k!='handle'}
    expressions=[]
    for expression in value.get('expr',[]):
        if 'counter' in expression:
            counter=expression['counter']
            require(set(expression)=={'counter'} and type(counter) is dict
                and set(counter)=={'packets','bytes'} and all(type(v) is int and 0<=v<2**64
                    for v in counter.values()),'CAMERA_EGRESS_COUNTER_INVALID')
            expressions.append({'counter':None})
        else:expressions.append(expression)
    return dict(value,expr=expressions)


def _egress(trust,item,enabled,*,exchange=False):
    """Existing Source packet-filter owner; no BPF/Engine/global policy change.

    Camera's UID is shared only with its AF_UNIX-only core; the exchange has
    its own distinct UID and owned table. The inet
    chain runs before Source DNAT; other UIDs and Source's own gates retain
    their original policy. Refuse unknown ownership/rules, never adopt them.
    """
    table_name=EXCHANGE_EGRESS if exchange else CAMERA_EGRESS
    uid=pwd.getpwnam('aos-vision-exchange' if exchange else 'aos-camera-access').pw_uid
    expected=camera_egress_rules(uid,table=table_name);comment=('democtl-vision-exchange:' if exchange else 'democtl-vision-camera:')+UUID(item['localVmId']).hex
    chain=dict(family='inet',table=table_name,name='output',type='filter',hook='output',prio=-250,policy='accept')
    def observed():
        tables=json.loads(trust.call(['nft','-j','list','tables']))['nftables']
        if not any(v.get('table',{}).get('name')==table_name for v in tables):return False
        data=json.loads(trust.call(['nft','-j','list','table','inet',table_name]))['nftables']
        table=[v['table'] for v in data if 'table' in v]
        chains=[{k:w for k,w in v['chain'].items() if k!='handle'} for v in data if 'chain' in v]
        rules=[camera_egress_observed_rule(v['rule']) for v in data if 'rule' in v]
        require(len(table)==1 and table[0].get('comment')==comment and chains==[chain]
            and rules==expected,'CAMERA_EGRESS_OWNER_OR_RULES_CHANGED')
        return True
    before=observed()
    if before==enabled:return dict(enforced=enabled,noOp=True)
    if enabled:
        commands=[{'add':{'table':dict(family='inet',name=table_name,comment=comment)}},
            {'add':{'chain':chain}},*[{'add':{'rule':v}} for v in expected]]
    else:commands=[{'delete':{'table':dict(family='inet',name=table_name)}}]
    trust.call(['nft','-j','-f','-'],data=json.dumps(dict(nftables=commands)))
    require(observed()==enabled,'CAMERA_EGRESS_APPLY_UNCONFIRMED')
    return dict(enforced=enabled,noOp=False)


def camera_egress(trust,item,enabled):return _egress(trust,item,enabled)


def camera_component_epoch():
    """Root Source reads only native OEM hello, never another daemon's key."""
    with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as connection:
        connection.settimeout(2);connection.connect('/run/aos-camera-access/oem/producer.sock')
        value=json.dumps(dict(schemaVersion=1,operation='hello'),separators=(',',':')).encode()
        connection.sendall(struct.pack('!I',len(value))+value);end=time.monotonic()+2
        def exact(size):
            output=bytearray()
            while len(output)<size:
                left=end-time.monotonic();require(left>0,'EXCHANGE_HELLO_TIMEOUT');connection.settimeout(left)
                part=connection.recv(size-len(output));require(part,'EXCHANGE_HELLO_TRUNCATED');output.extend(part)
            return bytes(output)
        def unique(rows):
            result={}
            for key,value in rows:
                require(key not in result,'EXCHANGE_HELLO_DUPLICATE');result[key]=value
            return result
        size=struct.unpack('!I',exact(4))[0];require(0<size<=4096,'EXCHANGE_HELLO_LIMIT')
        hello=json.loads(exact(size),object_pairs_hook=unique)
    require(type(hello) is dict,'EXCHANGE_HELLO_INVALID')
    require(set(hello)=={'schemaVersion','componentEpoch','state'} and type(hello['schemaVersion']) is int
        and hello['schemaVersion']==1 and hello['state']=='OEM_HELLO' and str(UUID(hello['componentEpoch']))==hello['componentEpoch'],'EXCHANGE_HELLO_INVALID')
    return hello['componentEpoch']


def exchange_ready_facts(values,uid,gid,groups,context,credentials_readonly,sockets):
    """An active Type=exec unit is not proof that Python is ready or confined."""
    return (list(map(int,values.get('Uid','').split()))==[uid]*4
        and list(map(int,values.get('Gid','').split()))==[gid]*4
        and groups<=set(map(int,values.get('Groups','').split()))<=groups|{gid}
        and values.get('NoNewPrivs','').strip()=='1'
        and all(values.get(key,'').strip()=='0000000000000000' for key in ('CapEff','CapPrm','CapInh','CapBnd','CapAmb'))
        and context.rstrip('\x00\n').split(':')[2:3]==['vision_exchange_t'] and credentials_readonly
        and len(sockets)==4 and all(sockets))


def exchange_process_ready(pid):
    group_names=dict(zip(EXCHANGE_ROLES,('aos-vision-perc-pub','aos-vision-perc-read','aos-vision-context-read','aos-vision-assess-pub')))
    user=pwd.getpwnam('aos-vision-exchange');groups={grp.getgrnam(group_names[role]).gr_gid for role in EXCHANGE_ROLES}
    require(user.pw_uid>0 and user.pw_gid>0,'EXCHANGE_IDENTITY_INVALID')
    try:
        proc=Path('/proc')/str(pid);values=dict(row.split(':',1) for row in (proc/'status').read_text().splitlines() if ':' in row)
        mounts=[row.split() for row in (proc/'mountinfo').read_text().splitlines()]
        selected=[row for row in mounts if row[4]=='/run/credentials/aos-vision-exchange.service']
        readonly=len(selected)==1 and 'ro' in selected[0][5].split(',')
        listening={row[-1] for line in (proc/'net/unix').read_text().splitlines()[1:] if len(row:=line.split())>=8
            and int(row[3],16)&0x10000 and row[4]=='0001'}
        sockets=[]
        for role in EXCHANGE_ROLES:
            path=Path('/run/aos-vision-exchange')/role/'exchange.sock';info=path.lstat()
            sockets.append(stat.S_ISSOCK(info.st_mode) and info.st_uid==user.pw_uid
                and info.st_gid==grp.getgrnam(group_names[role]).gr_gid and stat.S_IMODE(info.st_mode)==0o660 and str(path) in listening)
        return exchange_ready_facts(values,user.pw_uid,user.pw_gid,groups,(proc/'attr/current').read_text(),readonly,sockets)
    except (FileNotFoundError,ProcessLookupError):return False


def exchange(request,trust,item,*,start):
    """Same Source selection and credentials, four role resources, no app key."""
    require(request.get('exchangeScopes')==EXCHANGE_SCOPES,'EXCHANGE_SCOPE_REQUIRED')
    values=dict(row.split('=',1) for row in trust.call(['systemctl','show',EXCHANGE_UNIT,
        '--property=LoadState,ActiveState,MainPID']).splitlines() if '=' in row)
    require(values.get('LoadState')=='loaded','EXCHANGE_NOT_INSTALLED')
    if not start:
        trust.call(['systemctl','stop',EXCHANGE_UNIT])
        after=dict(row.split('=',1) for row in trust.call(['systemctl','show',EXCHANGE_UNIT,
            '--property=ActiveState,MainPID,Job,ControlGroup']).splitlines() if '=' in row)
        require(after.get('ActiveState') in ('inactive','failed') and after.get('MainPID')=='0' and after.get('Job','') in ('','0'),'EXCHANGE_STOP_UNCONFIRMED')
        group=after.get('ControlGroup','');require(group in ('','/system.slice/aos-vision-exchange.service'),'EXCHANGE_STOP_CGROUP_CHANGED')
        if group:
            procs=Path('/sys/fs/cgroup'+group+'/cgroup.procs');require(not procs.exists() or not procs.read_text().strip(),'EXCHANGE_STOP_PROCESS_REMAINS')
        _egress(trust,item,False,exchange=True);return dict(stopped=True)
    require(trust.call(['systemctl','is-active',CAMERA_UNIT]).strip()=='active','EXCHANGE_INGRESS_REQUIRED')
    selected=json.loads(read(INPUTS/'selected.json',0o644))['selectedSource']
    generation=request.get('generation');source=request.get('sourceId')
    require(type(generation) is int and generation>0 and selected['assignmentGeneration']==generation
        and selected['role']=='SELECTED_PLATFORM_UNIT' and selected['unitId']==item['unitId'] and selected['nodeId']==item['nodeId'],'EXCHANGE_SELECTION_MISMATCH')
    require(type(source) is str and str(UUID(source))==source,'EXCHANGE_SOURCE_INVALID')
    binding=dict(schemaVersion=1,sourceId=source,assignmentGeneration=generation,unitId=item['unitId'],nodeId=item['nodeId'],
        componentEpoch=camera_component_epoch(),scopes=EXCHANGE_SCOPES)
    text='[Service]\n'+''.join('LoadCredential='+name+':'+str(path)+'\n' for name,path in (
        ('vision-selection',EXCHANGE_SELECTION),('vision-ca',INPUTS/'viss-update-ca'),
        ('vision-certificate',STORE/'selected-platform-unit/client.pem'),('vision-private-key',STORE/'selected-platform-unit/client-key.pem')))
    expected={EXCHANGE_SELECTION:(json.dumps(binding,sort_keys=True),0o600),EXCHANGE_DROPIN:(text,0o644)}
    same=all(path.is_file() and read(path,mode)==content for path,(content,mode) in expected.items())
    require(values.get('ActiveState')=='inactive' or same,'EXCHANGE_ACTIVE_BINDING_CHANGED')
    _egress(trust,item,True,exchange=True);changed=False
    for path,(content,mode) in expected.items():changed=trust.write(path,content,mode) or changed
    if changed:trust.call(['systemctl','daemon-reload'])
    trust.call(['systemctl','start',EXCHANGE_UNIT])
    deadline=time.monotonic()+5
    while True:
        after=dict(row.split('=',1) for row in trust.call(['systemctl','show',EXCHANGE_UNIT,
            '--property=ActiveState,Result,NRestarts,MainPID']).splitlines() if '=' in row)
        pid=int(after.get('MainPID','0'))
        require(after.get('ActiveState')=='active' and after.get('Result')=='success' and after.get('NRestarts')=='0' and pid>0,'EXCHANGE_START_UNCONFIRMED')
        if exchange_process_ready(pid):return dict(started=True,noOp=same and values.get('ActiveState')=='active')
        require(time.monotonic()<deadline,'EXCHANGE_READY_UNCONFIRMED');time.sleep(.05)


def camera(request,trust,item):
    """The existing Source owner projects selection, never invents credentials.

    Stop is idempotent even on the retained pre-ingress image. Start requires
    the new internal OEM unit (a reversible /run unit in the accepted proof).
    """
    action=request['action']
    scopes=request.get('exchangeScopes',[]);require(scopes in ([],EXCHANGE_SCOPES),'EXCHANGE_SCOPE_INVALID')
    if action=='camera-stop' and scopes:exchange(request,trust,item,start=False)
    values=dict(line.split('=',1) for line in trust.call(['systemctl','show',CAMERA_UNIT,
        '--property=LoadState,ActiveState,Result,NRestarts,MainPID']).splitlines() if '=' in line)
    if action=='camera-stop':
        if values.get('LoadState')=='not-found':
            require(values.get('ActiveState') in ('inactive','failed') and values.get('MainPID')=='0','CAMERA_STOP_UNCONFIRMED')
            camera_egress(trust,item,False)
            return dict(stopped=True,noOp=True)
        trust.call(['systemctl','stop',CAMERA_UNIT])
        after=dict(line.split('=',1) for line in trust.call(['systemctl','show',CAMERA_UNIT,
            '--property=ActiveState,MainPID,Job,ControlGroup']).splitlines() if '=' in line)
        require(after.get('ActiveState') in ('inactive','failed') and after.get('MainPID')=='0'
            and after.get('Job','') in ('','0'),'CAMERA_STOP_UNCONFIRMED')
        group=after.get('ControlGroup','')
        require(group in ('','/system.slice/aos-camera-ingress.service'),'CAMERA_STOP_CGROUP_CHANGED')
        if group:
            procs=Path('/sys/fs/cgroup'+group+'/cgroup.procs')
            require(not procs.exists() or not procs.read_text().strip(),'CAMERA_STOP_PROCESS_REMAINS')
        camera_egress(trust,item,False)
        return dict(stopped=True,noOp=values.get('ActiveState')=='inactive')
    require(action=='camera-start','CAMERA_ACTION_INVALID')
    require(values.get('LoadState')=='loaded','CAMERA_INGRESS_NOT_INSTALLED')
    native_store(trust)
    active=trust.call(['systemctl','is-active','aos-camera-access.service']).strip()
    require(active=='active','CAMERA_COMPONENT_NOT_ACTIVE')
    selected=json.loads(read(INPUTS/'selected.json',0o644))['selectedSource']
    generation=request.get('generation');source_id=request.get('sourceId')
    require(type(generation) is int and 0<generation<2**63 and selected['assignmentGeneration']==generation
        and selected['role']=='SELECTED_PLATFORM_UNIT' and selected['unitId']==item['unitId']
        and selected['nodeId']==item['nodeId'],'CAMERA_SELECTION_MISMATCH')
    require(type(source_id) is str and str(UUID(source_id))==source_id,'CAMERA_SOURCE_INVALID')
    # Require both original enrolled files, without logging or replacing them.
    for name in ('client.pem','client-key.pem'):read(STORE/'selected-platform-unit'/name,0o600)
    read(INPUTS/'viss-update-ca',0o644)
    binding=dict(schemaVersion=1,sourceId=source_id,assignmentGeneration=generation,
        unitId=item['unitId'],nodeId=item['nodeId'],scope='VISION_CAMERA_READ')
    text='[Service]\n'+''.join('LoadCredential='+name+':'+str(path)+'\n' for name,path in (
        ('camera-selection',CAMERA_SELECTION),('camera-ca',INPUTS/'viss-update-ca'),
        ('camera-certificate',STORE/'selected-platform-unit/client.pem'),
        ('camera-private-key',STORE/'selected-platform-unit/client-key.pem')))
    expected={CAMERA_SELECTION:(json.dumps(binding,sort_keys=True),0o600),CAMERA_DROPIN:(text,0o644)}
    same=all(path.is_file() and read(path,mode)==value for path,(value,mode) in expected.items())
    require(values.get('ActiveState')=='inactive' or same,'CAMERA_ACTIVE_BINDING_CHANGED')
    camera_egress(trust,item,True)
    changed=False
    for path,(value,mode) in expected.items():changed=trust.write(path,value,mode) or changed
    if changed:trust.call(['systemctl','daemon-reload'])
    trust.call(['systemctl','start',CAMERA_UNIT])
    after=dict(line.split('=',1) for line in trust.call(['systemctl','show',CAMERA_UNIT,
        '--property=ActiveState,Result,NRestarts,MainPID']).splitlines() if '=' in line)
    require(after.get('ActiveState')=='active' and after.get('Result')=='success'
        and after.get('NRestarts')=='0' and int(after.get('MainPID','0'))>0,'CAMERA_INGRESS_START_UNCONFIRMED')
    if scopes:exchange(request,trust,item,start=True)
    return dict(started=True,noOp=same and values.get('ActiveState')=='active',credentials='SOURCE_OWNED_SYSTEMD_PROJECTION')


def first_install_state():
    """Read-only, closed native wait. No enrollment or slot repair authority."""
    raw=read(RUNTIME/'state/transaction.json',0o600);value=json.loads(raw)
    fields={'schemaVersion','operation','phase','candidateSlot','candidateItemId','candidateSubjectId',
        'candidateInstance','candidateVersion','candidateManifestDigest','candidateRuntimeId','candidatePreinstalled','hasPrevious'}
    require(set(value)==fields and value['schemaVersion']==2 and value['operation']=='install-or-replace'
        and value['phase']=='waiting-for-safe-stop' and value['hasPrevious'] is False
        and value['candidateSlot'] in ('a','b') and value['candidateVersion']=='0.1.0'
        and type(value['candidateInstance']) is int and value['candidateInstance']>=0
        and type(value['candidatePreinstalled']) is bool
        and re.fullmatch('sha256:[a-f0-9]{64}',value['candidateManifestDigest']), 'FIRST_INSTALL_STATE_REQUIRED')
    for name in ('candidateItemId','candidateSubjectId','candidateRuntimeId'):
        require(str(UUID(value[name]))==value[name],'FIRST_INSTALL_IDENTITY_INVALID')
    require(not os.path.lexists(RUNTIME/'active') and not os.path.lexists(RUNTIME/'state/installed.json'),
        'FIRST_INSTALL_PREVIOUS_DEPLOYMENT')
    candidate=RUNTIME/'slots'/value['candidateSlot']/'.aos-instance.json'
    # Native SealPayload removes owner-write from the original 0600 record.
    meta=read(candidate,0o400);record=json.loads(meta)
    require(record.get('schemaVersion')==1 and record.get('slot')==value['candidateSlot']
        and all(record.get(k)==value['candidate'+k] for k in
            ('ItemId','SubjectId','Instance','Version','ManifestDigest','RuntimeId','Preinstalled')),
        'FIRST_INSTALL_CANDIDATE_CHANGED')
    return raw,meta


def validate_material(trust,item,material):
    """Validate both exact leaves/keys before the first persistent write."""
    for name,role in (('vdp','selected-platform-unit'),('runtime','platform-update-runtime')):
        san=trust.call(['openssl','x509','-noout','-ext','subjectAltName'],data=material[name+'Certificate']).splitlines()
        require(len(san)==2 and san[1].strip()=='URI:urn:aosedge:demo:viss-client:v1:'+role+':'+item['unitId']+':'+item['nodeId'],
            'CERTIFICATE_IDENTITY_INVALID')
        require(trust.call(['openssl','x509','-pubkey','-noout'],data=material[name+'Certificate'])==
            trust.call(['openssl','pkey','-pubout'],data=material[name+'Key']),'KEY_MISMATCH')


def initial_projection(request,trust,item,material,expected):
    """Quiesce one native writer, retain its exact first wait, then resume it."""
    require(request['action']=='trust-configure','FIRST_INSTALL_CONFIGURE_ONLY')
    before=first_install_state()
    require(all(not os.path.lexists(path) for path in expected),'FIRST_INSTALL_PARTIAL_ENROLLMENT')
    validate_material(trust,item,material)
    trust.call(['systemctl','--no-block','stop','aos-sm.service'])
    stopped=False;created=[]
    try:
        deadline=time.monotonic()+20
        while True:
            values=dict(line.split('=',1) for line in trust.call([
                'systemctl','show','aos-sm.service','-p','ActiveState','-p','Job']).splitlines() if '=' in line)
            if values.get('ActiveState')=='inactive' and values.get('Job') in ('','0'):
                stopped=True;break
            require(time.monotonic()<deadline,'FIRST_INSTALL_WRITER_STOP_TIMEOUT');time.sleep(.25)
        require(first_install_state()==before,'FIRST_INSTALL_STATE_CHANGED')
        require(all(not os.path.lexists(path) for path in expected),'FIRST_INSTALL_PARTIAL_ENROLLMENT')
        for path,(value,mode) in expected.items():
            trust.write(path,value,mode);created.append(path)
        require(first_install_state()==before,'FIRST_INSTALL_STATE_CHANGED')
        trust.call(['systemctl','daemon-reload'])
    except BaseException:
        # Only newly created, still-exact files may be rolled back. A crash
        # leaves partial state fail-closed; never overwrite it on another run.
        try:
            if stopped and first_install_state()==before:
                for path in reversed(created):
                    value,mode=expected[path]
                    require(read(path,mode)==value,'FIRST_INSTALL_ROLLBACK_CHANGED')
                    path.unlink()
                trust.call(['systemctl','daemon-reload'])
        finally:
            trust.call(['systemctl','--no-block','start','aos-sm.service'])
        raise
    trust.activate_consumers(['aos-sm.service'])
    return dict(configured=True,noOp=False,smRestarted=True,firstEnrollment=True,
        transactionPreservedAtResume=True,**status(trust))


def restore_initial_projection(request,trust,item,material,expected):
    """Restore only the volatile SM binding for an exact first native wait."""
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
        # Keep an uncertain result for reconciliation; never rewrite native
        # pending state or erase an independently changed configuration.
        trust.call(['systemctl','--no-block','start','aos-sm.service'])
        raise
    trust.activate_consumers(['aos-sm.service'])
    return dict(configured=True,noOp=False,smRestarted=True,restoredPendingFirstInstall=True,
        persistentEnrollmentUnchanged=True,transactionPreservedAtResume=True,**status(trust))


def resume_initial_projection(request,trust,item,material,expected):
    require(request['action'] in ('trust-configure','trust-restore'),'FIRST_INSTALL_RESUME_ONLY')
    before=first_install_state()
    selected=INPUTS/'selected.json';binding=INPUTS/'viss-update-binding'
    old={path:read(path,0o644) for path in (selected,binding)}
    previous_selected=json.loads(old[selected]);previous_binding=json.loads(old[binding])
    next_selected=json.loads(expected[selected][0]);next_binding=json.loads(expected[binding][0])
    previous_generation=previous_selected['selectedSource']['assignmentGeneration']
    generation=next_selected['selectedSource']['assignmentGeneration']
    require(type(previous_generation) is int and type(generation) is int
        and 1<=previous_generation<=generation<2**63
        and previous_binding['assignmentGeneration']==previous_generation,'FIRST_INSTALL_RESUME_GENERATION_INVALID')
    previous_selected['selectedSource']['assignmentGeneration']=generation
    previous_binding['assignmentGeneration']=generation
    require(previous_selected==next_selected and previous_binding==next_binding,'FIRST_INSTALL_RESUME_IDENTITY_CHANGED')
    persistent={path:value for path,value in expected.items() if path not in (DROPIN,selected,binding)}
    require(all(read(path,mode)==value for path,(value,mode) in persistent.items()),'FIRST_INSTALL_RESUME_ENROLLMENT_CHANGED')
    present=os.path.lexists(DROPIN)
    require(not present or read(DROPIN,0o644)==expected[DROPIN][0],'FIRST_INSTALL_RESUME_DROPIN_CONFLICT')
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
        require(all(read(path,mode)==value for path,(value,mode) in persistent.items())
            and all(read(path,0o644)==value for path,value in old.items()),'FIRST_INSTALL_RESUME_INPUT_CHANGED')
        require(os.path.lexists(DROPIN)==present and (not present or read(DROPIN,0o644)==expected[DROPIN][0]),'FIRST_INSTALL_RESUME_DROPIN_CONFLICT')
        for path in (selected,binding,DROPIN):
            value,mode=expected[path];trust.write(path,value,mode)
        require(first_install_state()==before,'FIRST_INSTALL_STATE_CHANGED')
        trust.call(['systemctl','daemon-reload'])
    except BaseException:
        trust.call(['systemctl','--no-block','start','aos-sm.service'])
        raise
    trust.activate_consumers(['aos-sm.service'])
    return dict(configured=True,noOp=False,smRestarted=True,resumedPendingFirstInstall=True,
        persistentEnrollmentUnchanged=True,transactionPreservedAtResume=True,**status(trust))


def execute(request, trust, source=None):
    action = request['action']
    item, hardware = identity(request, provisioned=action not in ('factory-role', 'configure') or bool(request['vehicle'].get('unitId')))
    if action == 'factory-role':
        return dict(state='INITIALIZED', role='test', profile=PROFILE, noOp=True)
    if action == 'configure':
        # Server trust before provisioning belongs in the established transient
        # Source directory. It grants no authenticated role or native Safe Stop.
        require(isinstance(request.get('ca'), str) and 0 < len(request['ca']) < 16384, 'CA_INVALID')
        trust.write(Path('/run/democtl-source/ca.pem'), request['ca'], 0o644)
        return dict(configured=True, preProvision=not bool(item.get('unitId')),
                    smRestarted=False, runtimeBinding='DEFERRED_UNTIL_MUTUAL_TLS')
    if action in ('probe', 'trust-probe'):
        require(source is not None, 'PROBE_OWNER_REQUIRED')
        return source.probe(preprovision=not bool(item.get('unitId')),
                            mutual_tls=action == 'trust-probe', vision=True)
    if action == 'trust-status':
        return status(trust)
    if action in ('camera-start','camera-stop'):
        return camera(request,trust,item)
    require(action in ('trust-configure', 'trust-restore'), 'ACTION_UNSUPPORTED')
    native_store(trust)
    files = {'ca': INPUTS/'viss-update-ca'}
    for name, role in (('vdp', 'selected-platform-unit'), ('runtime', 'platform-update-runtime')):
        files[name+'Certificate'] = STORE/role/'client.pem'
        files[name+'Key'] = STORE/role/'client-key.pem'
    if action == 'trust-restore':
        selected = json.loads(read(INPUTS/'selected.json', 0o644))['selectedSource']
        require(selected['unitId'] == item['unitId'] and selected['nodeId'] == item['nodeId'], 'RESTORE_IDENTITY_CHANGED')
        generation = selected['assignmentGeneration']
        material = {name: read(path, 0o644 if name == 'ca' else 0o600) for name, path in files.items()}
    else:
        material = request['material']
        generation = request['generation']
    require(type(generation) is int and 1 <= generation < 2**63, 'GENERATION_INVALID')
    require(set(material) == set(files) and all(isinstance(v, str) and 0 < len(v) < 16384 for v in material.values()), 'MATERIAL_INVALID')
    fingerprints = {name: hashlib.sha256(ssl.PEM_cert_to_DER_cert(material[name+'Certificate'])).hexdigest()
                    for name in ('vdp', 'runtime')}
    require(fingerprints == request['fingerprints'], 'FINGERPRINT_CHANGED')
    binding = dict(schemaVersion=1, unitId=item['unitId'], nodeId=hardware, role='PLATFORM_UPDATE_RUNTIME',
                   clientCertificateSha256=fingerprints['runtime'], assignmentGeneration=generation)
    selected = dict(schemaVersion=2, viss=dict(uri='wss://10.0.0.1:6443', tlsServerName='127.0.0.1'),
                    selectedSource=dict(unitId=item['unitId'], nodeId=item['nodeId'], role='SELECTED_PLATFORM_UNIT',
                                        clientCertificateSha256=fingerprints['vdp'], assignmentGeneration=generation))
    text = '[Service]\n'+''.join('LoadCredential='+name+':'+str(path)+'\n' for name, path in (
        ('viss-update-ca', files['ca']), ('viss-update-binding', INPUTS/'viss-update-binding'),
        ('viss-update-certificate', files['runtimeCertificate']), ('viss-update-private-key', files['runtimeKey'])))
    expected = {**{path: (material[name], 0o644 if name == 'ca' else 0o600) for name, path in files.items()},
                INPUTS/'viss-update-binding': (json.dumps(binding, sort_keys=True), 0o644),
                INPUTS/'selected.json': (json.dumps(selected, sort_keys=True), 0o644), DROPIN: (text, 0o644)}
    transaction = RUNTIME/'state/transaction.json'
    if transaction.exists() or transaction.is_symlink():
        if all(path.is_file() and not path.is_symlink() for path in expected):
            if all(read(path,mode)==value for path,(value,mode) in expected.items()):
                return dict(configured=True,noOp=True,smRestarted=False,**status(trust))
            return resume_initial_projection(request,trust,item,material,expected)
        if all(path.is_file() and not path.is_symlink() for path in expected if path!=DROPIN):
            if action=='trust-restore':return restore_initial_projection(request,trust,item,material,expected)
            return resume_initial_projection(request,trust,item,material,expected)
        return initial_projection(request,trust,item,material,expected)
    changed = False
    for name, path in files.items():
        if name != 'ca' and path.exists():
            require(read(path, 0o600) == material[name], 'ENROLLMENT_CONFLICT')
        changed = trust.write(path, material[name], 0o644 if name == 'ca' else 0o600) or changed
    for name, role in (('vdp', 'selected-platform-unit'), ('runtime', 'platform-update-runtime')):
        certificate, key = files[name+'Certificate'], files[name+'Key']
        san = trust.call(['openssl', 'x509', '-in', str(certificate), '-noout', '-ext', 'subjectAltName']).splitlines()
        require(len(san) == 2 and san[1].strip() == 'URI:urn:aosedge:demo:viss-client:v1:'+role+':'+item['unitId']+':'+item['nodeId'], 'CERTIFICATE_IDENTITY_INVALID')
        require(trust.call(['openssl', 'x509', '-in', str(certificate), '-pubkey', '-noout']) ==
                trust.call(['openssl', 'pkey', '-in', str(key), '-pubout']), 'KEY_MISMATCH')
    for path in (INPUTS/'viss-update-binding', INPUTS/'selected.json', DROPIN):
        value, mode = expected[path]
        changed = trust.write(path, value, mode) or changed
    if changed:
        trust.call(['systemctl', 'daemon-reload'])
        trust.activate_consumers(['aos-sm.service'])
    return dict(configured=True, noOp=not changed, smRestarted=changed, **status(trust))


def script(request, *, source_code, trust_code):
    """Package-local scripts, isolated namespaces; no import/path override in guest."""
    own = Path(__file__).read_text()
    return ('import types,json\n'
            'source=types.ModuleType("source_owner")\nexec('+repr(source_code)+',source.__dict__)\n'
            'trust=types.ModuleType("trust_owner")\nexec('+repr(trust_code)+',trust.__dict__)\n'
            'vision=types.ModuleType("vision_projection")\nexec('+repr(own)+',vision.__dict__)\n'
            'request='+repr(request)+'\n'
            'try:\n value=vision.execute(request,trust,source)\n print(json.dumps(dict(ok=True,data=value)))\n'
            'except Exception as error:\n'
            ' reason=str(error) if isinstance(error,ValueError) and str(error).startswith("VISION_SOURCE_") else "VISION_SOURCE_FAILED"\n'
            ' print(json.dumps(dict(ok=False,reason=reason)))\n raise SystemExit(1)\n')
