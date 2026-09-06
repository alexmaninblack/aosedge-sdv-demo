# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Guest checks and explicit-user-password enrollment through owned local serial."""

import re
import os
import stat
import shlex
import socket
import subprocess
import time

from .environment import EnvironmentError

ACCESS_FILES = ("aosvm-host-ed25519", "aosvm-host-ed25519.pub", "known_hosts")
UNPROVISIONED = (
    "[ ! -e /var/aos/.provisionstate ] && [ ! -e /var/aos/iam/.usrpin ] && "
    "[ \"$(systemctl is-active aos-iam-prov.service)\" = active ] && "
    "[ \"$(systemctl is-active aos-iam.service)\" = inactive ] && "
    "[ \"$(systemctl is-active aos-sm.service)\" = inactive ] && "
    "[ \"$(systemctl is-active aos-cm.service)\" = inactive ]"
)


def ssh_command(access, port, timeout):
    known = str(access / "known_hosts").replace("\\", "\\\\").replace('"', '\\"')
    return ["ssh", "-F", "/dev/null", "-T", "-o", "BatchMode=yes", "-o", "IdentitiesOnly=yes",
            "-o", "IdentityAgent=none", "-o", "StrictHostKeyChecking=yes", "-o", "UpdateHostKeys=no",
            "-o", "GlobalKnownHostsFile=/dev/null", "-o", 'UserKnownHostsFile="' + known + '"',
            "-o", "ConnectionAttempts=1", "-o", "ConnectTimeout=" + str(max(1, int(timeout))),
            "-o", "ControlMaster=no", "-o", "ControlPath=none", "-o", "ClearAllForwardings=yes",
            "-i", str(access / ACCESS_FILES[0]), "-p", str(port), "root@127.0.0.1", "sh", "-s"]


def read_guest(access, port, timeout=5, shutdown=False):
    script = ("printf 'DEMO_GUEST_READY\\n'\nif " + UNPROVISIONED +
              "; then printf 'DEMO_UNPROVISIONED\\n'; fi\n")
    if shutdown:
        script += "sync\nsystemctl poweroff\n"
    else:
        script += "if timeout 2 busybox nslookup aoscloud.io >/dev/null 2>&1; then printf 'DEMO_DNS_READY\\n'; fi\n"
    try:
        result = subprocess.run(ssh_command(access, port, timeout), input=script,
                                capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired):
        return {"guestReady": False, "guestDnsReady": False, "unprovisioned": False}
    lines = result.stdout.splitlines()
    return {"guestReady": "DEMO_GUEST_READY" in lines and (result.returncode == 0 or shutdown),
            "guestDnsReady": "DEMO_DNS_READY" in lines,
            "unprovisioned": "DEMO_UNPROVISIONED" in lines}


def enroll_serial(serial, access, port, deadline, password, progress=None):
    """The caller supplies the password explicitly; no credential discovery."""
    progress = progress or (lambda stage: None)
    if not isinstance(password, str) or any(c in password for c in "\r\n\x00"):
        raise EnvironmentError("CONSOLE_PASSWORD_REQUIRED")
    if access.is_symlink() or not access.is_dir() or access.stat().st_uid != os.getuid():
        raise EnvironmentError("SSH_ACCESS_PATH_INVALID")
    for name in ACCESS_FILES:
        path = access / name
        if path.exists() or path.is_symlink():
            info = path.lstat()
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_uid != os.getuid():
                raise EnvironmentError("SSH_ACCESS_PATH_INVALID")
    private = access / ACCESS_FILES[0]
    if not private.exists():
        subprocess.run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C", "democtl-local-access",
                        "-f", str(private)], capture_output=True, check=True, timeout=10)
    for path in (private, access / ACCESS_FILES[1]):
        if path.is_symlink() or not path.is_file():
            raise EnvironmentError("SSH_ACCESS_PATH_INVALID")
        path.chmod(0o600)
    public = (access / ACCESS_FILES[1]).read_text().strip()
    if not re.fullmatch(r"ssh-ed25519 [A-Za-z0-9+/=]+ democtl-local-access", public):
        raise EnvironmentError("SSH_PUBLIC_KEY_INVALID")
    with socket.socket(socket.AF_UNIX) as connection:
        connection.settimeout(1)
        connection.connect(str(serial))
        connection.sendall(b"\r")
        buffer = ""
        authenticated = False
        sent_password = False
        stage = "CONSOLE_PROMPT"
        progress("waiting for console prompt")
        next_progress = time.monotonic() + 5
        next_prompt_request = time.monotonic() + 2
        while time.monotonic() < deadline:
            if stage == "CONSOLE_PROMPT" and time.monotonic() >= next_prompt_request:
                connection.sendall(b"\r")
                next_prompt_request = time.monotonic() + 2
            if time.monotonic() >= next_progress:
                progress("waiting: " + stage)
                next_progress = time.monotonic() + 5
            try:
                chunk = connection.recv(8192)
            except socket.timeout:
                # QMP becomes running before getty opens the UART. Its first
                # Enter can therefore be lost during boot. Request the prompt
                # again only before login; never resubmit a username/password.
                continue
            if not chunk:
                break
            buffer = (buffer + chunk.decode("utf-8", "replace"))[-32768:]
            if re.search(r"login: *$", buffer):
                if stage != "CONSOLE_PROMPT":
                    raise EnvironmentError("GUEST_CONSOLE_AUTHENTICATION_FAILED")
                connection.sendall(b"root\r")
                stage = "PASSWORD_PROMPT"
                progress("console login received; waiting for password prompt")
                buffer = ""
            elif re.search(r"[Pp]assword: *$", buffer):
                if sent_password:
                    raise EnvironmentError("GUEST_CONSOLE_AUTHENTICATION_FAILED")
                connection.sendall(password.encode() + b"\r")
                sent_password = True
                stage = "SHELL_PROMPT"
                progress("console credentials submitted; waiting for shell")
                buffer = ""
            elif re.search(r"(?:^|[\r\n])[^\r\n]*# *$", buffer):
                authenticated = True
                break
        if not authenticated:
            raise EnvironmentError("GUEST_CONSOLE_NOT_READY_" + stage)
        progress("console authenticated; installing SSH public key")
        command = (
            "stty -echo; umask 077; h=$(awk -F: '$1 == \"root\" {print $6}' /etc/passwd); "
            "test -d \"$h\" && printf '\\nDEMO_ENROLL_STAGE=HOME\\n' && "
            "test ! -L \"$h/.ssh\" && mkdir -p \"$h/.ssh\" && chmod 700 \"$h/.ssh\" && "
            "printf '\\nDEMO_ENROLL_STAGE=DIRECTORY\\n' && "
            "test ! -L \"$h/.ssh/authorized_keys\" && touch \"$h/.ssh/authorized_keys\" && "
            "chmod 600 \"$h/.ssh/authorized_keys\" && (grep -qxF " + shlex.quote(public) +
            " \"$h/.ssh/authorized_keys\" || printf '%s\\n' " + shlex.quote(public) +
            " >> \"$h/.ssh/authorized_keys\") && printf '\\nDEMO_ENROLL_STAGE=KEY\\n' && "
            "restorecon -RF \"$h\" && printf '\\nDEMO_ENROLL_STAGE=LABEL\\n' && "
            r"""f=$(awk '/^SSHD_OPTS=/ {gsub(/["\047]/,""); sub(/^SSHD_OPTS=/,""); for(i=1;i<NF;i++) if($i=="-f"){print $(i+1);exit}}' /etc/default/ssh 2>/dev/null); """
            "if test -n \"$f\"; then c=$(sshd -T -f \"$f\" 2>&1); else c=$(sshd -T 2>&1); fi; rc=$?; "
            "printf '\\nDEMO_SSHD_CONFIG_EXIT=%s\\n' \"$rc\"; "
            "test \"$rc\" = 0 && p=$(printf '%s\\n' \"$c\" | awk '$1 == \"hostkey\" {print $2; exit}') && "
            "test -n \"$p\" && printf '\\nDEMO_ENROLL_STAGE=HOST_KEY_PATH\\n' && "
            "printf '\\nDEMO_HOSTKEY_BEGIN\\n' && cat \"$p.pub\" && "
            "printf '\\nDEMO_HOSTKEY_END\\n'; r=$?; printf '\\nDEMO_ENROLL_RESULT=%s\\n' \"$r\"; stty echo\r"
        )
        connection.sendall(command.encode())
        buffer = ""
        last_stage = "SHELL"
        while time.monotonic() < deadline:
            try:
                chunk = connection.recv(8192)
            except socket.timeout:
                continue
            if not chunk:
                break
            buffer = (buffer + chunk.decode("utf-8", "replace"))[-32768:]
            config_result = re.search(r"(?:^|[\r\n])DEMO_SSHD_CONFIG_EXIT=([0-9]{1,3})\r?\n", buffer)
            if config_result and config_result[1] != "0":
                raise EnvironmentError("SSH_EFFECTIVE_CONFIG_FAILED_EXIT_" + config_result[1])
            stages = re.findall(r"(?:^|[\r\n])DEMO_ENROLL_STAGE=(HOME|DIRECTORY|KEY|LABEL|HOST_KEY_PATH)\r?\n", buffer)
            if stages and stages[-1] != last_stage:
                last_stage = stages[-1]
                progress("SSH setup completed stage: " + last_stage)
            result = re.search(r"(?:^|[\r\n])DEMO_ENROLL_RESULT=([0-9]{1,3})\r?\n", buffer)
            if result and result[1] != "0":
                raise EnvironmentError("SSH_ENROLLMENT_FAILED_AFTER_" + last_stage + "_EXIT_" + result[1])
            match = re.search(r"\r?\nDEMO_HOSTKEY_BEGIN\r?\n((?:ssh-ed25519|ssh-rsa|ecdsa-sha2-nistp(?:256|384|521)) [A-Za-z0-9+/=]+)(?: [^\r\n]*)?\r?\n", buffer)
            if match and "\nDEMO_HOSTKEY_END" in buffer:
                known = access / "known_hosts"
                line = "[127.0.0.1]:" + str(port) + " " + match.group(1) + "\n"
                if known.exists():
                    if known.is_symlink() or known.read_text() != line:
                        raise EnvironmentError("SSH_HOST_IDENTITY_CHANGED")
                else:
                    with known.open("x") as stream:
                        stream.write(line)
                    known.chmod(0o600)
                return
        raise EnvironmentError("SSH_CONSOLE_ENROLLMENT_INCOMPLETE")
