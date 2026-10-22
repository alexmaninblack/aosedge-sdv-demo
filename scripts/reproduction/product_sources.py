# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Read-only current-product owner check; no fetching, execution or receipt edits."""
import os
import re
import subprocess

from .core import LabError, no_links, read_json, require
from . import recipes


def tree(root, revision):
    require(revision == 'HEAD' or re.fullmatch('[a-f0-9]{40}', revision), 'Invalid product owner revision')
    env = {k:v for k,v in os.environ.items() if not k.startswith('GIT_')}
    env.update(GIT_NO_LAZY_FETCH='1', GIT_TERMINAL_PROMPT='0', GIT_OPTIONAL_LOCKS='0',
               GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull)
    try:
        result = subprocess.run(['git', '-C', str(root), 'ls-tree', '-r', '-z', revision],
                                capture_output=True, env=env, timeout=20)
    except (OSError, subprocess.TimeoutExpired):
        raise LabError('Current product owner objects unavailable; no fetch or build started') from None
    require(result.returncode == 0 and len(result.stdout) <= 8*2**20,
            'Current product owner objects unavailable; use the complete selected source checkout')
    rows = {}
    for raw in result.stdout.decode().split('\0'):
        if not raw: continue
        metadata, name = raw.split('\t', 1)
        mode, kind, oid = metadata.split()
        require(name not in rows, 'Duplicate product source path')
        rows[name] = (mode, kind, oid)
    return rows


def compare(current, selected, names):
    require(bool(names) and all(name in current and current[name][1] == 'blob'
                and current[name][0] in ('100644', '100755')
                and selected.get(name) == current[name] for name in names),
            'Selected application/Setup owner differs from current product inputs; review a successor build plan')


def check(root, plan_path):
    root = no_links(root)
    plan = read_json(plan_path)
    current = tree(root, 'HEAD')
    checked = {}
    for role, targets in (('application', ('application',)), ('media', ('setup', 'dmg'))):
        revision = plan['producers'][role]
        selected = tree(root, revision)
        names = set().union(*(recipes.paths(root, current, target) for target in targets))
        compare(current, selected, names)
        checked[role] = dict(revision=revision, verifiedFiles=len(names))
    return checked
