# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""A human-facing directory shortcut; immutable build receipts remain authority."""
import os
from pathlib import Path
import re
import tempfile

from developer_bootstrap import safe, read, save, require
from reproduction.core import regular


def target_ok(value):
    return isinstance(value, str) and re.fullmatch(r'build/builds/dmg/[a-f0-9]{64}', value)


def expose_result(root, dmg, receipt):
    root = safe(root)
    dmg, receipt = regular(Path(dmg)), regular(Path(receipt))
    require(dmg.parent.parent == root/'build/builds/dmg'
            and re.fullmatch(r'[a-f0-9]{64}', dmg.parent.name)
            and dmg.suffix == '.dmg'
            and receipt.parent == root/'build/builds/chains', 'Result is outside the verified build layout.')
    target = str(dmg.parent.relative_to(root))
    state_path = root/'.developer-preparation/output-link.json'
    link = root/'output'  # This exact presentation-only link is the sole exception to safe().
    prior = read(state_path) if state_path.exists() else None
    allowed = set()
    if prior is not None:
        require(set(prior) == {'schemaVersion', 'current', 'pending'} and prior['schemaVersion'] == 1,
                'Output shortcut metadata differs; existing files preserved.')
        for value in (prior['current'], prior['pending']):
            require(value is None or target_ok(value), 'Invalid output shortcut metadata; preserved.')
            if value:
                allowed.add(value)
    old = None
    if os.path.lexists(link):
        require(link.is_symlink() and link.lstat().st_uid == os.getuid(),
                'The output path is already in use; existing files preserved.')
        old = os.readlink(link)
        require(old in allowed, 'Unowned output shortcut; existing files preserved.')
    if old == target:
        save(state_path, dict(schemaVersion=1, current=target, pending=None))
        return str(link/dmg.name)
    # Intent before atomic replacement permits recovery after either crash window.
    save(state_path, dict(schemaVersion=1, current=old, pending=target))
    fd, temporary = tempfile.mkstemp(prefix='.output-link-', dir=state_path.parent)
    os.close(fd)
    os.unlink(temporary)
    try:
        os.symlink(target, temporary)
        # Do not replace a path that changed after the ownership check.
        require((old is None and not os.path.lexists(link)) or
                (link.is_symlink() and os.readlink(link) == old), 'Output shortcut changed; preserved.')
        os.replace(temporary, link)
        save(state_path, dict(schemaVersion=1, current=target, pending=None))
    finally:
        if os.path.islink(temporary):
            os.unlink(temporary)
    return str(link/dmg.name)
