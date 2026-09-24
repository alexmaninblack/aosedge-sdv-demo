# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Fixed Test-only VISS onboarding over pinned SSH; no Cloud credentials."""
import hashlib
import json
import os
import stat
import subprocess
import time
from pathlib import Path
from uuid import UUID

INPUTS = Path("/var/aos/workdirs/sm/runtimes/systemd-slot-component/demo-inputs")
STORE = Path("/var/aos/iam/vehicle-state")
MACHINE_ID = Path("/etc/machine-id")
OWNER = 0
SM_DROPIN = Path("/run/systemd/system/aos-sm.service.d/85-democtl-viss-mtls.conf")
VDP_DROPIN = Path("/run/systemd/system/aos-vehicle-data-provider.service.d/85-democtl-viss-mtls.conf")


def call(argv, data=None):
    result = subprocess.run(argv, input=data, text=True, capture_output=True, timeout=25)
    if result.returncode:
        raise ValueError("SOURCE_TRUST_GUEST_COMMAND_FAILED")
    return result.stdout


def activate_consumers(units, timeout=65):
    """Submit one restart transaction, then observe it; never retry a timeout.

    SM is ordered after CM. A queued endpoint restart can take longer than
    the 25-second command budget. systemctl submission is not completion.
    """
    if not units:
        return
    call(['systemctl', '--no-block', 'restart', *units])
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        raw = call(['systemctl', 'show', *units, '-p', 'Id', '-p', 'ActiveState', '-p', 'Job'])
        states = [dict(line.split('=', 1) for line in block.splitlines() if '=' in line)
                  for block in raw.strip().split('\n\n')]
        def ready(s):
            # A freshly provisioned controller has no VDP assignment yet.
            # Its condition-skipped unit is not a failed credential restore.
            empty_provider = (s.get('Id') == 'aos-vehicle-data-provider.service'
                and s.get('ActiveState') == 'inactive'
                and not os.path.lexists(INPUTS.parent / 'active')
                and not (INPUTS.parent / 'state/installed.json').exists())
            return (s.get('ActiveState') == 'active' or empty_provider) and s.get('Job') in ('', '0')
        if len(states) == len(units) and {s.get('Id') for s in states} == set(units) and all(ready(s) for s in states):
            return
        if any(s.get('ActiveState') == 'failed' and s.get('Job') in ('', '0') for s in states):
            raise ValueError('SOURCE_TRUST_CONSUMER_FAILED')
        time.sleep(.25)
    raise ValueError('SOURCE_TRUST_CONSUMER_RESTART_UNCONFIRMED')


def safe(path):
    for part in (path,) + tuple(path.parents):
        if part.is_symlink():
            raise ValueError("SOURCE_TRUST_GUEST_PATH_UNSAFE")
        if part.exists():
            st = part.stat()
            if st.st_uid != OWNER or st.st_mode & 0o022:
                raise ValueError("SOURCE_TRUST_GUEST_PATH_UNSAFE")


def write(path, data, mode=0o600):
    safe(path)
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    if path.exists():
        st = path.stat()
        if not stat.S_ISREG(st.st_mode) or st.st_nlink != 1 or stat.S_IMODE(st.st_mode) != mode:
            raise ValueError("SOURCE_TRUST_GUEST_FILE_UNSAFE")
        if path.read_text() == data:
            return False
    temporary = path.with_name(path.name + ".new")
    fd = os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, mode)
    with os.fdopen(fd, "w") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)
    return True


def status():
    result = call(["systemctl", "show", "aos-vehicle-data-provider", "--property=ActiveState,StatusText,NRestarts,MainPID"])
    values = dict(line.split("=", 1) for line in result.splitlines() if "=" in line)
    return dict(mutualTlsConfigured=SM_DROPIN.is_file() and VDP_DROPIN.is_file(),
        factoryBaseline=(values.get("ActiveState") == "inactive"
            and not os.path.lexists(INPUTS.parent / "active")
            and not (INPUTS.parent / "state/installed.json").exists()),
        vdpProcess=values.get("ActiveState"), vdpData=values.get("StatusText"), vdpRestarts=values.get("NRestarts"))


def execute(request):
    item = request["vehicle"]
    local = str(UUID(item["localVmId"]))
    hardware = item["cloud"]["identity"]["nodeHardwareId"]
    if (request["role"] != "test" or local.replace("-", "") != hardware
            or MACHINE_ID.read_text().strip() != hardware
            or (INPUTS / "role").read_text() != "test\n"):
        raise ValueError("SOURCE_TRUST_GUEST_IDENTITY_MISMATCH")
    for key in ("unitId", "nodeId"):
        if str(UUID(item[key])) != item[key]:
            raise ValueError("SOURCE_TRUST_GUEST_IDENTITY_MISMATCH")
    if request["action"] == "trust-status":
        return status()
    if request["action"] == "trust-restore":
        # Reconstruct only previously enrolled credentials after reboot. No
        # new leaf, host secret transfer, selection or assignment is invented.
        selected_path = INPUTS / "selected.json"
        safe(selected_path)
        selected = json.loads(selected_path.read_text())["selectedSource"]
        if (selected.get("unitId") != item["unitId"] or selected.get("nodeId") != item["nodeId"]
                or selected.get("clientCertificateSha256") != request["fingerprints"]["vdp"]):
            raise ValueError("SOURCE_TRUST_GUEST_IDENTITY_MISMATCH")
        files = {"ca": INPUTS / "viss-update-ca"}
        for name, role in (("vdp", "selected-platform-unit"), ("runtime", "platform-update-runtime")):
            files[name + "Certificate"] = STORE / role / "client.pem"
            files[name + "Key"] = STORE / role / "client-key.pem"
        for name, path in files.items():
            safe(path)
            info = path.stat()
            if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1
                    or stat.S_IMODE(info.st_mode) != (0o644 if name == "ca" else 0o600)
                    or not 0 < info.st_size < 16384):
                raise ValueError("SOURCE_TRUST_GUEST_FILE_UNSAFE")
        return execute(dict(request, action="trust-configure", generation=selected["assignmentGeneration"],
            material={name: path.read_text() for name, path in files.items()}))
    if request["action"] != "trust-configure":
        raise ValueError("SOURCE_TRUST_GUEST_ACTION_INVALID")
    generation = request["generation"]
    if type(generation) is not int or not 1 <= generation < 2**63:
        raise ValueError("SOURCE_TRUST_GENERATION_INVALID")
    # Do not interrupt an in-flight FOTA slot transaction.
    if (INPUTS.parent / "state/transaction.json").exists():
        raise ValueError("SOURCE_TRUST_COMPONENT_TRANSACTION_ACTIVE")
    material = request["material"]
    expected = {"ca", "vdpCertificate", "vdpKey", "runtimeCertificate", "runtimeKey"}
    if set(material) != expected or any(not isinstance(v, str) or not 0 < len(v) < 16384 for v in material.values()):
        raise ValueError("SOURCE_TRUST_CREDENTIAL_ENVELOPE_INVALID")
    import ssl
    fingerprints = {name: hashlib.sha256(ssl.PEM_cert_to_DER_cert(material[name + "Certificate"])).hexdigest()
        for name in ("vdp", "runtime")}
    if fingerprints != request["fingerprints"]:
        raise ValueError("SOURCE_TRUST_CREDENTIAL_FINGERPRINT_MISMATCH")
    changed = False
    for name, role in (("vdp", "selected-platform-unit"), ("runtime", "platform-update-runtime")):
        base = STORE / role
        for filename, value in (("client.pem", material[name + "Certificate"]), ("client-key.pem", material[name + "Key"])):
            path = base / filename
            # Changing an enrolled leaf/key requires an explicit new onboarding.
            safe(path)
            if path.exists() and path.read_text() != value:
                raise ValueError("SOURCE_TRUST_GUEST_CREDENTIAL_CONFLICT")
            changed = write(path, value) or changed
        uri = "urn:aosedge:demo:viss-client:v1:" + role + ":" + item["unitId"] + ":" + item["nodeId"]
        san = call(["openssl", "x509", "-in", str(base / "client.pem"), "-noout", "-ext", "subjectAltName"]).splitlines()
        if len(san) != 2 or san[1].strip() != "URI:" + uri:
            raise ValueError("SOURCE_TRUST_GUEST_CERTIFICATE_IDENTITY_MISMATCH")
        if (call(["openssl", "x509", "-in", str(base / "client.pem"), "-pubkey", "-noout"])
                != call(["openssl", "pkey", "-in", str(base / "client-key.pem"), "-pubout"])):
            raise ValueError("SOURCE_TRUST_GUEST_KEY_MISMATCH")
    sm_binding = dict(schemaVersion=1, unitId=item["unitId"], nodeId=hardware,
        role="PLATFORM_UPDATE_RUNTIME", clientCertificateSha256=fingerprints["runtime"], assignmentGeneration=generation)
    vdp_binding = dict(schemaVersion=2, viss=dict(uri="wss://10.0.0.1:6443", tlsServerName="127.0.0.1"),
        selectedSource=dict(unitId=item["unitId"], nodeId=item["nodeId"], role="SELECTED_PLATFORM_UNIT",
            clientCertificateSha256=fingerprints["vdp"], assignmentGeneration=generation))
    # Existing Factory public inputs remain public; no private key enters them.
    write(INPUTS / "viss-update-ca", material["ca"], 0o644)
    write(INPUTS / "viss-update-binding", json.dumps(sm_binding, sort_keys=True), 0o644)
    vdp_changed = write(INPUTS / "selected.json", json.dumps(vdp_binding, sort_keys=True), 0o644)
    sm_text = ("[Service]\nLoadCredential=viss-update-certificate:" + str(STORE / "platform-update-runtime/client.pem")
        + "\nLoadCredential=viss-update-private-key:" + str(STORE / "platform-update-runtime/client-key.pem") + "\n")
    vdp_text = ("[Service]\nLoadCredential=viss-client-cert.pem:" + str(STORE / "selected-platform-unit/client.pem")
        + "\nLoadCredential=viss-client-key.pem:" + str(STORE / "selected-platform-unit/client-key.pem")
        + "\nLoadCredential=viss-server-ca.pem:" + str(INPUTS / "viss-update-ca")
        + "\nLoadCredential=viss-selected-source.json:" + str(INPUTS / "selected.json") + "\n")
    sm_changed = write(SM_DROPIN, sm_text, 0o644)
    vdp_changed = write(VDP_DROPIN, vdp_text, 0o644) or vdp_changed
    if sm_changed or vdp_changed:
        call(["systemctl", "daemon-reload"])
    # One credential snapshot activation. Queue both consumers before waiting
    # so CM stop ordering cannot prevent VDP from loading its credentials.
    units = (["aos-sm.service"] if sm_changed else []) + (
        ["aos-vehicle-data-provider.service"] if vdp_changed or changed else [])
    activate_consumers(units)
    return dict(configured=True, smRestarted=sm_changed, vdpRestarted=vdp_changed or changed,
        assignmentGeneration=generation, **status())


def main(request):
    try:
        print(json.dumps(dict(ok=True, data=execute(request))))
    except Exception as error:
        # Never expose OpenSSL output, input payloads or credential text.
        reason = str(error) if isinstance(error, ValueError) and str(error).startswith("SOURCE_TRUST_") else "SOURCE_TRUST_GUEST_FAILED"
        print(json.dumps(dict(ok=False, reason=reason)))
