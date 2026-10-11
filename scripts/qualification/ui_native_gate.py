#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Record a witnessed CUA click, not perform or emulate the native action."""
import argparse
import json
import os
from pathlib import Path
import re
from uuid import UUID
import remote_harness as h

FIELDS = {'schemaVersion', 'stage', 'action', 'test', 'sessionId', 'state'}
ACTIONS = {'Safe Stop', 'Brake maneuver', 'Tire maneuver', 'Return to road', 'Autopilot'}


def validate(gate, stage, action):
    h.require(isinstance(gate, dict) and set(gate) == FIELDS and gate['schemaVersion'] == 1
              and gate['stage'] == stage and gate['action'] == action and action in ACTIONS
              and re.fullmatch('[a-z][a-z0-9-]{0,79}', stage)
              and gate['state'] == 'WAITING_FOR_UI_CLICK', 'NATIVE_GATE_MISMATCH')
    for field in ('test', 'sessionId'):
        h.require(str(UUID(gate[field])) == gate[field], 'NATIVE_GATE_ID_INVALID')
    h.require(action != 'Autopilot' or stage == 'moving-sota-autopilot', 'NATIVE_GATE_MISMATCH')
    return dict(gate, state='CLICKED_THROUGH_CUA')


def main():
    os.umask(0o077)
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--records', type=Path, required=True)
    p.add_argument('--stage', required=True)
    p.add_argument('--action', choices=sorted(ACTIONS), required=True)
    p.add_argument('--witness-cua-click', action='store_true')
    args = p.parse_args()
    root = h.unlinked(args.records)
    h.require('/.local/remote-qualification/' in str(root) and root.is_dir(), 'PRIVATE_RECORD_REQUIRED')
    info = root.stat()
    h.require(info.st_uid == os.getuid() and info.st_mode & 0o077 == 0, 'PRIVATE_RECORD_REQUIRED')
    h.require(not (root/'browser-report.json').exists(), 'UI_SCENARIO_ALREADY_TERMINAL')
    gate_path = h.unlinked(root/'native-ui-gate.json')
    gate = h.parse(gate_path.read_bytes())
    receipt = validate(gate, args.stage, args.action)
    if args.witness_cua_click:
        # Caller records this only AFTER a visible supported CUA click. A CLI
        # acknowledgement alone is not evidence that the button worked.
        target = root/'native-ui-click.json'
        h.require(not target.exists(), 'CLICK_WITNESS_ALREADY_EXISTS')
        h.atomic(target, receipt)
    print(json.dumps(gate if not args.witness_cua_click else receipt))


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError):
        print(json.dumps(dict(outcome='BLOCKED', code='NATIVE_UI_WITNESS_INVALID')))
        raise SystemExit(2)
