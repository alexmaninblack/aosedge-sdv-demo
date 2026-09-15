# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Public Test Cloud configuration projected onto an unchanged Factory image.

Executed in the guest. Runtime bind mounts disappear at reboot and are
recreated by democtl vm start. No credential, base-file edit or TLS bypass.
"""

import json
import os
from pathlib import Path
import subprocess


def apply(request):
    from urllib.parse import urlsplit
    domain = request["domain"]
    # Even a mistakenly routed production request must not write guest files.
    if domain == "aoscloud.io":
        return dict(domain=domain, configured=False, changed=False, cmRestarted=False,
                    hostsProjected=0, factoryUnchanged=True)
    url = "https://" + domain + ":9000/sd/v7/"
    if urlsplit(url).hostname != domain or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789.-" for c in domain):
        raise ValueError("CLOUD_GUEST_DOMAIN_INVALID")
    root = Path("/run/democtl-cloud")
    target = Path("/etc/aos/cm.cfg")
    original = target.read_text()
    config = json.loads(original)
    changed = config.get("serviceDiscoveryUrl") != url
    cm_active = subprocess.run(["systemctl", "is-active", "--quiet", "aos-cm.service"]).returncode == 0
    # Provisioning must not change the endpoint of an already running CM.
    if changed and cm_active and not request.get("vmStart"):
        raise ValueError("CLOUD_GUEST_ACTIVE_CM_REQUIRES_VM_START")
    if changed and Path("/var/aos/.provisionstate").exists() and not request.get("vmStart"):
        raise ValueError("CLOUD_GUEST_ALREADY_PROVISIONED")
    root.mkdir(mode=0o700, exist_ok=True)
    if root.is_symlink() or root.stat().st_uid != 0:
        raise ValueError("CLOUD_GUEST_RUNTIME_UNSAFE")

    def bind(content, name, destination):
        path = root / name
        temporary = root / (name + ".new")
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644)
        with os.fdopen(fd, "w") as stream:
            stream.write(content)
        try:
            subprocess.run(["chcon", "--reference=" + str(destination), str(temporary)], check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            os.replace(temporary, path)
            subprocess.run(["mount", "--bind", str(path), str(destination)], check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["mount", "-o", "remount,bind,ro", str(destination)], check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        finally:
            if temporary.exists():
                temporary.unlink()

    entries = request.get("hosts", [])
    if entries:
        hosts = Path("/etc/hosts")
        before = hosts.read_text()
        names = {entry["host"] for entry in entries}
        lines = []
        for line in before.splitlines():
            words = line.split("#", 1)[0].split()
            if len(words) > 1 and names.intersection(words[1:]):
                remaining = [name for name in words[1:] if name not in names]
                if remaining:
                    lines.append(words[0] + " " + " ".join(remaining))
            else:
                lines.append(line)
        addresses = {}
        for entry in entries:
            addresses.setdefault(entry["address"], []).append(entry["host"])
        after = "\n".join(lines + [address + " " + " ".join(names)
                                   for address, names in addresses.items()]) + "\n"
        if before != after:
            bind(after, "hosts", hosts)
    if changed:
        config["serviceDiscoveryUrl"] = url
        bind(json.dumps(config, indent=2) + "\n", "cm.cfg", target)
        if cm_active:
            subprocess.run(["systemctl", "restart", "aos-cm.service"], check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    import socket
    socket.getaddrinfo(domain, 9000, type=socket.SOCK_STREAM)
    return dict(domain=domain, configured=True, changed=changed, cmRestarted=bool(changed and cm_active),
                hostsProjected=len(entries), serviceDiscoveryUrl=url, factoryUnchanged=True)


def main(request):
    try:
        print(json.dumps(dict(ok=True, data=apply(request))))
        return True
    except Exception as error:
        reason = str(error)
        print(json.dumps(dict(ok=False, reason=reason if reason.startswith("CLOUD_GUEST_") and len(reason) < 100
                             else "CLOUD_GUEST_CONFIGURATION_FAILED_" + type(error).__name__)))
        return False
