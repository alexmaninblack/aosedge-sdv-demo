#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""One-time, explicitly approved M1 SSH restriction; not a product dependency."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile


def rule(user, source):
    if not re.fullmatch(r'[a-z][a-z0-9_]{0,31}', user) or source != '192.168.247.1':
        raise ValueError('QUALIFICATION_PROFILE_REQUIRED')
    return (f'Match User {user} Address {source}\n'
        '    AllowTcpForwarding local\n'
        '    PermitOpen 127.0.0.1:18080\n'
        '    PermitListen none\nMatch all\n').encode()


def configure(user, source):
    wanted = rule(user, source)
    # /etc is a standard macOS alias. Use the canonical directory and still
    # reject every unexpected link rather than weakening the path guard.
    path = Path('/private/etc/ssh/sshd_config.d/sdv-presenter-qualification.conf')
    if os.getuid() != 0 or any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError('ADMIN_CANONICAL_PATH_REQUIRED')
    previous = path.read_bytes() if path.exists() else None
    if previous not in (None, wanted):
        raise ValueError('EXISTING_SSH_RULE_PRESERVED')
    created = previous is None
    if created:
        fd, name = tempfile.mkstemp(prefix='.sdv-presenter-', dir=path.parent)
        try:
            with os.fdopen(fd, 'wb') as stream:
                stream.write(wanted)
                stream.flush()
                os.fsync(stream.fileno())
            os.chmod(name, 0o644)
            os.replace(name, path)
        finally:
            if os.path.exists(name):
                os.unlink(name)
    try:
        subprocess.run(['/usr/sbin/sshd', '-t'], check=True, capture_output=True, timeout=10)
        process = subprocess.run(['/usr/sbin/sshd', '-T', '-C',
            f'user={user},host={source},addr={source}'], check=True,
            capture_output=True, text=True, timeout=10)
        values = dict(line.split(' ', 1) for line in process.stdout.splitlines())
        if not (values['allowtcpforwarding'] == 'local'
                and values['permitopen'] == '127.0.0.1:18080'
                and values['permitlisten'] == 'none'):
            raise ValueError('SSH_EFFECTIVE_SCOPE_MISMATCH')
    except Exception:
        if created:
            path.unlink()  # Only this new rule; never an existing/foreign file.
        raise
    return dict(localOnly=True, allowedDestination='127.0.0.1:18080',
                reverseForwarding=False, configurationValidated=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--user', required=True)
    parser.add_argument('--source', required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(configure(args.user, args.source)), flush=True)
    except Exception:
        print(json.dumps(dict(outcome='BLOCKED', code='SCOPED_SSH_CONFIGURATION_NOT_CONFIRMED')), flush=True)
        raise SystemExit(1)
