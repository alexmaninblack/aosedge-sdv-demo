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
from uuid import UUID

PROFILE = 'aos-vision-main-qemuarm64-v1'
RUNTIME = Path('/var/aos/workdirs/sm/runtimes/systemd-slot-camera-access')
INPUTS = RUNTIME/'demo-inputs'
STORE = Path('/var/aos/iam/vehicle-state')
DROPIN = Path('/run/systemd/system/aos-sm.service.d/85-democtl-viss-mtls.conf')


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
        # No interrupted-transaction reconfiguration or credential replacement.
        require(all(read(path, mode) == value for path, (value, mode) in expected.items()), 'ACTIVE_TRANSACTION_PRESERVED')
        return dict(configured=True, noOp=True, smRestarted=False, **status(trust))
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
