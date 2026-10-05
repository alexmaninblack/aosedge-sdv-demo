# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Private one-shot enrollment engine. Tokens never enter files or diagnostics."""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import stat
from uuid import uuid4


class EnrollmentError(ValueError):
    pass


def require(ok, reason):
    if not ok:
        raise EnrollmentError('CLOUD_ENROLLMENT_' + reason)


def validate(domain, role):
    from aosedge_demo_orchestrator.cloud_connection import domain_name
    domain_name(domain)
    require(role in ('oem', 'sp'), 'ROLE_INVALID')


def directory(root, role, create=False):
    from aosedge_demo_orchestrator.runtime_paths import instance, canonical
    root, _ = instance(root)
    path = root
    for part in ('.local', 'demo-control', 'credentials', 'enrollment', role):
        path = canonical(path / part)
        if not path.exists():
            if not create:
                return path
            path.mkdir(mode=0o700)
        info = path.lstat()
        require(stat.S_ISDIR(info.st_mode) and info.st_uid == os.getuid()
                and not info.st_mode & 0o077, 'DIRECTORY_UNSAFE')
    return path


def read_private(path, limit=65536):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, 'rb') as stream:
        info = os.fstat(stream.fileno())
        require(stat.S_ISREG(info.st_mode) and info.st_uid == os.getuid()
                and info.st_nlink == 1 and not info.st_mode & 0o077
                and 0 < info.st_size <= limit, 'FILE_UNSAFE')
        raw = stream.read(limit + 1)
        after = os.fstat(stream.fileno())
        stamp = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mode, s.st_uid, s.st_nlink, s.st_mtime_ns, s.st_ctime_ns)
        require(len(raw) == info.st_size and stamp(info) == stamp(after)
                and path.lstat().st_ino == info.st_ino, 'FILE_CHANGED')
        return raw


def write_new(path, data):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    fd = os.open(path.parent, os.O_RDONLY)
    try: os.fsync(fd)
    finally: os.close(fd)


def save(path, value):
    from aosedge_demo_orchestrator.environment import atomic_json
    pending = path.with_name(path.name + '.pending')
    require(not pending.exists() and not pending.is_symlink(), 'PENDING_WRITE')
    if path.exists(): read_private(path, 32768)
    atomic_json(path, value)


def key_pair(folder):
    from cryptography import x509
    from cryptography.hazmat.primitives import serialization
    key, csr = read_private(folder/'key.pem'), read_private(folder/'request.pem')
    private_key = serialization.load_pem_private_key(key, None)
    request = x509.load_pem_x509_csr(csr)
    require(request.is_signature_valid and public(private_key.public_key()) == public(request.public_key()),
            'KEY_CSR_INVALID')
    return key, csr


def public(key):
    from cryptography.hazmat.primitives import serialization
    return key.public_bytes(serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)


def check_certificate(cert, key, domain):
    from cryptography.hazmat.primitives import serialization
    from cryptography.x509.oid import NameOID
    org = cert.subject.get_attributes_for_oid(NameOID.ORGANIZATION_NAME)
    now = datetime.now(timezone.utc)
    require(len(org) == 1 and org[0].value == domain
            and cert.not_valid_before_utc <= now < cert.not_valid_after_utc
            and public(cert.public_key()) == public(serialization.load_pem_private_key(key, None).public_key()),
            'CERTIFICATE_BINDING_INVALID')


def check_output(folder, domain):
    from cryptography.hazmat.primitives.serialization import pkcs12
    key, _ = key_pair(folder)
    data = pkcs12.load_pkcs12(read_private(folder/'client.p12'), None)
    require(data.key is not None and data.cert is not None, 'CERTIFICATE_INVALID')
    require(public(data.key.public_key()) == public(data.cert.certificate.public_key()), 'CERTIFICATE_INVALID')
    check_certificate(data.cert.certificate, key, domain)


def receive_once(domain, token, key, csr, role):
    """No SDK CLI, system trust fallback, proxies, redirects or automatic retries."""
    import requests
    from requests.adapters import HTTPAdapter
    from aos_keys.common import ca_certificate
    from aos_keys.key_manager import pem_to_pkcs12_bytes
    from cryptography import x509
    with ca_certificate() as trust, requests.Session() as session:
        session.trust_env = False
        session.mount('https://', HTTPAdapter(max_retries=0))
        with session.post('https://' + domain + ':10000/api/v11/user-certificates/',
                          json={'csr': csr.decode('ascii')},
                          headers={'Authorization': 'Token ' + token, 'Referer': 'https://' + domain,
                                   'Content-Type': 'application/json; charset=UTF-8'},
                          verify=str(trust), timeout=(5, 30), allow_redirects=False, stream=True) as response:
            require(response.status_code != 403, 'TOKEN_REJECTED_OR_ALREADY_USED')
            require(response.status_code in (200, 201), 'RESPONSE_REQUIRES_RECONCILIATION')
            raw = bytearray()
            for block in response.iter_content(chunk_size=4096):
                require(len(raw) + len(block) <= 65536, 'RESPONSE_TOO_LARGE')
                raw.extend(block)
            def unique(pairs):
                result = {}
                for key, value in pairs:
                    require(key not in result, 'RESPONSE_INVALID')
                    result[key] = value
                return result
            payload = json.loads(raw, object_pairs_hook=unique)
            require(isinstance(payload, dict) and isinstance(payload.get('certificate'), str), 'RESPONSE_INVALID')
            pem = payload['certificate'].encode('ascii')
            certificates = x509.load_pem_x509_certificates(pem)
            require(bool(certificates), 'RESPONSE_INVALID')
            check_certificate(certificates[0], key, domain)
            return pem_to_pkcs12_bytes(key, pem, 'Aos ' + role.upper() + ' client certificate')


def load(folder, domain, role):
    path = folder/'attempt.json'
    pending = folder/'attempt.json.pending'
    require(not pending.exists() and not pending.is_symlink(), 'PENDING_WRITE')
    if not folder.exists(): return None
    require({p.name for p in folder.iterdir()} <= {'attempt.json', 'key.pem', 'request.pem', 'client.p12'}, 'FOREIGN_FILE')
    require(path.exists(), 'PARTIAL_STATE_REQUIRES_RECONCILIATION')
    value = json.loads(read_private(path, 32768))
    require(isinstance(value, dict) and set(value) == {'schemaVersion','kind','domain','role','attempts'}
            and type(value['schemaVersion']) is int and value['schemaVersion'] == 1
            and value['kind'] == 'democtl.cloud-enrollment' and value['domain'] == domain
            and value['role'] == role and isinstance(value['attempts'], list)
            and 1 <= len(value['attempts']) <= 16, 'RECORD_INVALID_OR_SCOPE_CHANGED')
    from aosedge_demo_orchestrator.status import object_id
    seen = set()
    for attempt in value['attempts']:
        require(isinstance(attempt, dict) and set(attempt) <= {'id','stage','createdAt','dispatchedAt','completedAt','reconciledAt'}
                and {'id','stage','createdAt'} <= set(attempt), 'RECORD_INVALID')
        identity = object_id(attempt['id'])
        require(identity not in seen and attempt['stage'] in ('PREPARING','PREPARED','DISPATCHING','UNCERTAIN','RECEIVED'),
                'RECORD_INVALID')
        seen.add(identity)
        require(all(isinstance(v, str) and len(v) <= 100 for v in attempt.values()), 'RECORD_INVALID')
    return value


def projected(value, state=None, accessed=False):
    last = value['attempts'][-1]
    return dict(enrollmentStage=state or last['stage'], role=value['role'], domain=value['domain'],
                attemptId=last['id'], rolesChecked=False, cloudAccessed=accessed)


def operation(root, domain, role, action, token=None, reconcile_attempt=None):
    """Caller holds the existing instance writer and verified package lease."""
    from aosedge_demo_orchestrator.status import now
    validate(domain, role)
    require(action in ('status','enroll','recover'), 'ACTION_INVALID')
    folder = directory(root, role)
    value = load(folder, domain, role)
    if action != 'enroll':
        require(token is None and reconcile_attempt is None, 'REQUEST_INVALID')
        if value is None:
            return dict(enrollmentStage='NOT_STARTED', domain=domain, role=role, rolesChecked=False, cloudAccessed=False)
        if (folder/'client.p12').exists():
            check_output(folder, domain)
            if value['attempts'][-1]['stage'] != 'RECEIVED':
                if action == 'status': return projected(value, 'LOCAL_RECOVERY_AVAILABLE')
                value['attempts'][-1].update(stage='RECEIVED', completedAt=now())
                save(folder/'attempt.json', value)
            return projected(value)
        require(value['attempts'][-1]['stage'] != 'RECEIVED', 'CREDENTIAL_MISSING')
        return projected(value, 'RECONCILIATION_REQUIRED' if value['attempts'][-1]['stage'] in
                         ('DISPATCHING','UNCERTAIN','PREPARING') else None)
    require(isinstance(token, str) and 1 <= len(token) <= 4096
            and all(33 <= ord(c) <= 126 for c in token), 'TOKEN_INPUT_INVALID')
    if value is not None:
        last = value['attempts'][-1]
        if last['stage'] == 'RECEIVED':
            check_output(folder, domain)
            return projected(value)
        require(not (folder/'client.p12').exists(), 'LOCAL_RECOVERY_REQUIRED')
        require(last['stage'] != 'PREPARING', 'PARTIAL_STATE_REQUIRES_RECONCILIATION')
        key_pair(folder)
        if last['stage'] in ('DISPATCHING','UNCERTAIN'):
            require(reconcile_attempt == last['id'], 'RECONCILIATION_REQUIRED')
            require(len(value['attempts']) < 16, 'ATTEMPT_LIMIT')
            last['reconciledAt'] = now()
            value['attempts'].append(dict(id=str(uuid4()), stage='PREPARED', createdAt=now()))
            save(folder/'attempt.json', value)
        else:
            require(reconcile_attempt is None, 'RECONCILIATION_MISMATCH')
    else:
        require(reconcile_attempt is None, 'RECONCILIATION_MISMATCH')
        folder = directory(root, role, create=True)
        require(not any(folder.iterdir()), 'PARTIAL_STATE_REQUIRES_RECONCILIATION')
        value = dict(schemaVersion=1, kind='democtl.cloud-enrollment', domain=domain, role=role,
                     attempts=[dict(id=str(uuid4()), stage='PREPARING', createdAt=now())])
        save(folder/'attempt.json', value)
        from aos_keys.key_manager import generate_pair
        # The pinned official package signer uses RS256 for both OEM components
        # and SP services. The SDK's EC default authenticates but cannot sign.
        key, csr = generate_pair(use_elliptic_curves=False)
        write_new(folder/'key.pem', key)
        write_new(folder/'request.pem', csr)
        value['attempts'][-1]['stage'] = 'PREPARED'
        save(folder/'attempt.json', value)
    key, csr = key_pair(folder)
    value['attempts'][-1].update(stage='DISPATCHING', dispatchedAt=now())
    save(folder/'attempt.json', value)
    try:
        data = receive_once(domain, token, key, csr, role)
        write_new(folder/'client.p12', data)
        check_output(folder, domain)
        value['attempts'][-1].update(stage='RECEIVED', completedAt=now())
        save(folder/'attempt.json', value)
        return projected(value, accessed=True)
    except Exception:
        # Never echo transport exceptions: they can contain the Authorization header.
        value['attempts'][-1]['stage'] = 'UNCERTAIN'
        try: save(folder/'attempt.json', value)
        except Exception: pass  # DISPATCHING still blocks a replay after a failed receipt write.
        return projected(value, 'RECONCILIATION_REQUIRED', accessed=True)


def run_worker(root, domain, role, action, token=None, reconcile_attempt=None):
    import subprocess
    from .cloud_connection import CloudConnection
    from .environment import EnvironmentService
    from .cloud_runtime import launch
    env = EnvironmentService(root=root)
    with env._writer():
        CloudConnection(env).first_use_guard()
        command, environment = launch(root, '', 'cloud_enrollment.py')
        request = dict(root=str(root), domain=domain, role=role, action=action)
        if action == 'enroll': request.update(token=token, reconcileAttempt=reconcile_attempt)
        try:
            result = subprocess.run(command, input=json.dumps(request), capture_output=True,
                                    text=True, env=environment, timeout=75)
            require(result.returncode == 0 and len(result.stdout) <= 4096 and not result.stderr, 'WORKER_UNAVAILABLE')
            reply = json.loads(result.stdout)
            require(isinstance(reply, dict) and reply.get('domain') == domain and reply.get('role') == role
                    and reply.get('rolesChecked') is False
                    and reply.get('enrollmentStage') in ('NOT_STARTED','PREPARED','RECEIVED',
                        'RECONCILIATION_REQUIRED','LOCAL_RECOVERY_AVAILABLE'), 'WORKER_RESPONSE_INVALID')
            return reply
        except (subprocess.SubprocessError, OSError, json.JSONDecodeError):
            raise EnrollmentError('CLOUD_ENROLLMENT_INSPECT_ATTEMPT_BEFORE_RETRY') from None


if __name__ == '__main__':
    import resource
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    try:
        raw = sys.stdin.buffer.read(8193)
        require(len(raw) <= 8192, 'REQUEST_TOO_LARGE')
        request = json.loads(raw)
        action = request.get('action')
        keys = {'root','domain','role','action'} | ({'token','reconcileAttempt'} if action == 'enroll' else set())
        require(set(request) == keys, 'REQUEST_INVALID')
        reply = operation(request['root'], request['domain'], request['role'], action,
                          request.get('token'), request.get('reconcileAttempt'))
        print(json.dumps(reply))
    except Exception:
        # No traceback, raw response, token, key or certificate crosses IPC.
        print(json.dumps({'error':'CLOUD_ENROLLMENT_INSPECT_ATTEMPT_BEFORE_RETRY'}))
        raise SystemExit(1)
