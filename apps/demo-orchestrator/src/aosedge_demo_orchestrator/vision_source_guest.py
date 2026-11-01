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


def camera_egress_rules(uid):
    require(type(uid) is int and uid>0,'CAMERA_EGRESS_UID_INVALID')
    owner={'match':{'op':'==','left':{'meta':{'key':'skuid'}},'right':uid}}
    base=dict(family='inet',table=CAMERA_EGRESS,chain='output')
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


def camera_egress(trust,item,enabled):
    """Existing Source packet-filter owner; no BPF/Engine/global policy change.

    UID is shared only with Camera core (which is AF_UNIX-only). The inet
    chain runs before Source DNAT; other UIDs and Source's own gates retain
    their original policy. Refuse unknown ownership/rules, never adopt them.
    """
    uid=pwd.getpwnam('aos-camera-access').pw_uid
    expected=camera_egress_rules(uid);comment='democtl-vision-camera:'+UUID(item['localVmId']).hex
    chain=dict(family='inet',table=CAMERA_EGRESS,name='output',type='filter',hook='output',prio=-250,policy='accept')
    def observed():
        tables=json.loads(trust.call(['nft','-j','list','tables']))['nftables']
        if not any(v.get('table',{}).get('name')==CAMERA_EGRESS for v in tables):return False
        data=json.loads(trust.call(['nft','-j','list','table','inet',CAMERA_EGRESS]))['nftables']
        table=[v['table'] for v in data if 'table' in v]
        chains=[{k:w for k,w in v['chain'].items() if k!='handle'} for v in data if 'chain' in v]
        rules=[camera_egress_observed_rule(v['rule']) for v in data if 'rule' in v]
        require(len(table)==1 and table[0].get('comment')==comment and chains==[chain]
            and rules==expected,'CAMERA_EGRESS_OWNER_OR_RULES_CHANGED')
        return True
    before=observed()
    if before==enabled:return dict(enforced=enabled,noOp=True)
    if enabled:
        commands=[{'add':{'table':dict(family='inet',name=CAMERA_EGRESS,comment=comment)}},
            {'add':{'chain':chain}},*[{'add':{'rule':v}} for v in expected]]
    else:commands=[{'delete':{'table':dict(family='inet',name=CAMERA_EGRESS)}}]
    trust.call(['nft','-j','-f','-'],data=json.dumps(dict(nftables=commands)))
    require(observed()==enabled,'CAMERA_EGRESS_APPLY_UNCONFIRMED')
    return dict(enforced=enabled,noOp=False)


def camera(request,trust,item):
    """The existing Source owner projects selection, never invents credentials.

    Stop is idempotent even on the retained pre-ingress image. Start requires
    the new internal OEM unit (a reversible /run unit in the accepted proof).
    """
    action=request['action']
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
            require(all(read(path, mode) == value for path, (value, mode) in expected.items()), 'ACTIVE_TRANSACTION_PRESERVED')
            return dict(configured=True, noOp=True, smRestarted=False, **status(trust))
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
