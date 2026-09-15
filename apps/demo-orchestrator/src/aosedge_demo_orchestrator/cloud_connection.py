# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Certificate-selected Test Cloud. No browser credential or TLS bypass."""

import json
import os
import re
import subprocess
from pathlib import Path

from .environment import EnvironmentError, JOURNAL, atomic_json
from .status import read_json

LEGACY_DOMAIN = "aoscloud.io"
CONFIG = ".local/demo-control/status.json"
DEFAULT_PROFILES = {
    "oem-delivery": {"credential": "~/.aos/security/aos-user-oem.p12", "expectedRole": "oem"},
    "service-provider": {"credential": "~/.aos/security/aos-user-sp.p12", "expectedRole": "service provider"},
}


def domain_name(value):
    if (not isinstance(value, str) or len(value) > 253 or "." not in value
            or not re.fullmatch(r"[a-z0-9.-]+", value)
            or any(not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", label)
                   for label in value.split("."))
            or all(label.isdigit() for label in value.split("."))):
        raise ValueError("CLOUD_CERTIFICATE_DOMAIN_INVALID")
    return value


def trusted_host(host, selected=None):
    host = domain_name(host)
    if selected is None:
        # Legacy profiles retain the original restriction until explicitly selected.
        if host != LEGACY_DOMAIN and not host.endswith("." + LEGACY_DOMAIN):
            raise ValueError("CLOUD_SELECTION_REQUIRED")
    elif host != domain_name(selected):
        raise ValueError("CLOUD_CERTIFICATE_DOMAIN_CHANGED")
    return host


def selected_domain(state):
    return domain_name(state.get("selectedCloudDomain", LEGACY_DOMAIN))


def cloud_scope(state, create=False):
    """Legacy Production binding/Subjects stay byte-for-byte in their old fields."""
    domain = selected_domain(state)
    context = state.get("cloudContexts", {}).get(domain, {})
    owner = (context.get("selectedOwners") or {}).get("oem")
    if owner:
        return (context.setdefault("tenants", {}).setdefault(owner, {}) if create
                else context.get("tenants", {}).get(owner, {}))
    if domain == LEGACY_DOMAIN:
        return state
    return (state.setdefault("cloudContexts", {}).setdefault(domain, {}) if create
            else state.get("cloudContexts", {}).get(domain, {}))


def bind_tenant(state, domain, owners):
    """Migrate only this OEM's binding; never move peer/legacy Production fields."""
    from copy import deepcopy
    from .status import object_id
    for value in owners.values():
        object_id(value)
    previous = cloud_scope(state)
    prior_owner = (previous.get("cloudBinding") or {}).get("ownerId")
    retained = {key: deepcopy(previous[key]) for key in ("cloudBinding", "demoSubjects")
                if key in previous and prior_owner == owners["oem"]}
    state["selectedCloudDomain"] = domain_name(domain)
    entry = state.setdefault("cloudContexts", {}).setdefault(domain, {})
    scope = entry.setdefault("tenants", {}).setdefault(owners["oem"], retained)
    entry["selectedOwners"] = dict(owners)
    return scope


def cloud_binding(state):
    return cloud_scope(state).get("cloudBinding") or {}


def cloud_subjects(state, create=False):
    scope = cloud_scope(state, create=create)
    return scope.setdefault("demoSubjects", {}) if create else scope.get("demoSubjects", {})


def cloud_request(profile):
    return {"cloudDomain": profile["cloudDomain"]} if profile.get("cloudDomain") else {}


def host_entries(domain, path=Path("/etc/hosts")):
    """Mirror only explicitly configured hosts for the selected environment."""
    import ipaddress
    names = [domain] + [prefix + "." + domain for prefix in ("api", "oem", "sp", "fleet", "admin")]
    allowed = set(names)
    entries = {}
    for line in path.read_text().splitlines():
        words = line.split("#", 1)[0].split()
        if len(words) < 2 or not allowed.intersection(words[1:]):
            continue
        address = str(ipaddress.ip_address(words[0]))
        for host in allowed.intersection(words[1:]):
            if host in entries and entries[host] != address:
                raise EnvironmentError("CLOUD_HOST_MAPPING_AMBIGUOUS")
            entries[host] = address
    return [dict(host=host, address=entries[host]) for host in names if host in entries]


def guest_configuration(vm, state, role, *, vm_start=False):
    """Debug-only preparation; production keeps the unchanged guest start path."""
    from .status import load_configuration
    if role != "test" or selected_domain(state) == LEGACY_DOMAIN:
        return None
    config = load_configuration(vm.root)
    domain = selected_domain(state)
    if (config.get("cloudConnection") or {}).get("domain") != domain:
        raise EnvironmentError("CLOUD_SELECTION_RECONCILIATION_REQUIRED")
    entries = host_entries(domain)
    if domain.endswith(".test") and len(entries) != 6:
        raise EnvironmentError("CLOUD_DEBUG_HOST_MAPPING_INCOMPLETE")
    return dict(domain=domain, hosts=entries, vmStart=vm_start)


def configure_guest(vm, state, role, *, vm_start=False):
    """Provision preparation; vm start embeds the same payload in its first SSH."""
    request = guest_configuration(vm, state, role, vm_start=vm_start)
    if request is None:
        return None
    from .guest_access import ssh_command
    from .vm import access_path
    from . import cloud_guest
    script = "python3 - <<'DEMOCTL_CLOUD_PY'\n" + Path(cloud_guest.__file__).read_text() + "\nmain(" + repr(request) + ")\nDEMOCTL_CLOUD_PY\n"
    vm.progress("test: applying certificate-selected Cloud endpoint and host mappings; Factory image unchanged")
    try:
        result = subprocess.run(ssh_command(access_path(vm.root, role), state["vehicles"][role]["sshPort"], 10),
            input=script, capture_output=True, text=True, timeout=15)
        if result.returncode or len(result.stdout) > 8192:
            raise ValueError()
        value = json.loads(result.stdout)
        if not value.get("ok"):
            raise EnvironmentError(value.get("reason", "CLOUD_GUEST_CONFIGURATION_FAILED"))
        return value["data"]
    except EnvironmentError:
        raise
    except (OSError, ValueError, subprocess.SubprocessError):
        raise EnvironmentError("CLOUD_GUEST_CONFIGURATION_UNAVAILABLE") from None


def inspect_certificate(path):
    """Runs in the installed Aos Python process; returns public metadata only."""
    from datetime import datetime, timezone
    from cryptography.hazmat.primitives.serialization.pkcs12 import load_key_and_certificates
    from cryptography.x509.oid import NameOID
    path = Path(path).expanduser()
    if path.is_symlink() or not path.is_file() or path.stat().st_mode & 0o077 or path.stat().st_size > 1024 * 1024:
        raise ValueError("CLOUD_CREDENTIAL_MISSING_OR_UNSAFE")
    key, cert, _ = load_key_and_certificates(path.read_bytes(), None)
    if key is None or cert is None:
        raise ValueError("CLOUD_CLIENT_CERTIFICATE_REQUIRED")
    domains = cert.subject.get_attributes_for_oid(NameOID.ORGANIZATION_NAME)
    if len(domains) != 1:
        raise ValueError("CLOUD_CERTIFICATE_DOMAIN_AMBIGUOUS")
    domain = domain_name(domains[0].value)
    starts, ends = cert.not_valid_before_utc, cert.not_valid_after_utc
    if not starts <= datetime.now(timezone.utc) <= ends:
        raise ValueError("CLOUD_CERTIFICATE_TIME_INVALID")
    return dict(domain=domain, validUntil=ends.isoformat(), certificateName=path.name,
        apiUrl="https://" + domain + ":10000/api/v11/",
        serviceDiscoveryUrl="https://" + domain + ":9000/sd/v7/", trust="PACKAGED_AOS_CA")


class CloudConnection:
    def __init__(self, environment):
        self.environment = environment
        self.root = environment.root

    def _configuration(self):
        path = self.root / CONFIG
        return read_json(path) if path.exists() else {"schemaVersion": 1}

    def credential(self):
        data = self._configuration()
        value = data.get("cloudProfiles", DEFAULT_PROFILES).get("oem-delivery", {}).get("credential")
        if not value:
            raise EnvironmentError("OEM_DELIVERY_PROFILE_REQUIRED")
        path = Path(value).expanduser()
        return path if path.is_absolute() else self.root / path

    def inspect(self, certificate=None):
        data = self._configuration()
        path = Path(certificate).expanduser() if certificate else self.credential()
        if not path.is_absolute():
            path = self.root / path
        interpreter = str(Path(data.get("cloudPython", "~/.aos/venv/bin/python3")).expanduser())
        try:
            result = subprocess.run([interpreter, "-I", "-B", str(Path(__file__).with_name("cloud_connection_worker.py"))],
                input=json.dumps({"certificate": str(path)}), capture_output=True, text=True,
                timeout=8, env={"PATH": os.defpath})
            if result.returncode or len(result.stdout) > 8192:
                raise ValueError()
            value = json.loads(result.stdout)
            if not value.get("ok"):
                raise EnvironmentError(value.get("reason", "CLOUD_CERTIFICATE_UNAVAILABLE"))
            metadata = value["data"]
            domain_name(metadata["domain"])
            metadata["selectedDomain"] = data.get("cloudConnection", {}).get("domain", LEGACY_DOMAIN)
            metadata["applied"] = data.get("cloudConnection", {}).get("domain") == metadata["domain"]
            return metadata
        except EnvironmentError:
            raise
        except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
            raise EnvironmentError("CLOUD_CERTIFICATE_UNAVAILABLE") from None

    def select(self, certificate=None, expected_domain=None):
        with self.environment._writer():
            metadata = self.inspect(certificate)
            domain = metadata["domain"]
            if expected_domain is not None and domain != domain_name(expected_domain):
                raise EnvironmentError("CLOUD_CERTIFICATE_CHANGED_SINCE_PREVIEW")
            journal = self.root / JOURNAL
            state = read_json(journal) if journal.exists() else None
            if state and (state.get("schemaVersion") != 1 or state.get("kind") != "democtl.current-run"
                    or state.get("stage") not in ("MANUFACTURED", "LOCAL_ACTIVE", "LOCAL_STOPPED")):
                raise EnvironmentError("CLOUD_SELECTION_REQUIRES_STABLE_LOCAL_RUN")
            data = self._configuration()
            old_domain = data.get("cloudConnection", {}).get("domain", LEGACY_DOMAIN)
            if state and domain != selected_domain(state):
                test = state.get("vehicles", {}).get("test", {})
                if any(test.get(key) for key in ("unitId", "nodeId", "systemUid", "unitSetId", "cloud")):
                    raise EnvironmentError("CLOUD_SWITCH_REQUIRES_FINISH_TEST")
                published = any(set(record) - {"prepare", "signed"}
                                for record in state.get("componentOperations", {}).values())
                if (len(state.get("operations", [])) > 1 or published
                        or state.get("serviceOperations") or state.get("source", {}).get("operation")):
                    raise EnvironmentError("CLOUD_SWITCH_REQUIRES_FINISH_TEST_OPERATIONS")
            path = Path(certificate).expanduser() if certificate else self.credential()
            if not path.is_absolute():
                path = self.root / path
            profiles = data.setdefault("cloudProfiles", {k: dict(v) for k, v in DEFAULT_PROFILES.items()})
            profile = profiles.setdefault("oem-delivery", dict(DEFAULT_PROFILES["oem-delivery"]))
            profile.update(credential=str(path), expectedRole="oem")
            if domain != old_domain:
                profile.pop("expectedOwnerId", None)
                for entry in profiles.values():
                    if entry.get("expectedRole") == "service provider":
                        entry.pop("expectedOwnerId", None)
            previous_connection = data.get("cloudConnection", {})
            data["cloudConnection"] = {"domain": domain, "source": "OEM_CERTIFICATE_ORGANIZATION"}
            if old_domain == domain and previous_connection.get("owners"):
                data["cloudConnection"]["owners"] = previous_connection["owners"]
            # Journal first: an interrupted pair fails closed in load_configuration.
            # Repeating this explicit selection repairs the same pair without any
            # Cloud calls, credential copies or VM changes.
            if state:
                state["selectedCloudDomain"] = domain
                atomic_json(journal, state)
            destination = self.environment._directory(".local/demo-control") / "status.json"
            atomic_json(destination, data)
            return dict(metadata, applied=True, selectedDomain=domain, productionPreserved=True,
                guestConfiguration=("FACTORY_UNCHANGED" if domain == LEGACY_DOMAIN
                                    else "APPLIED_BEFORE_PROVISION_OR_ON_VM_START"))
