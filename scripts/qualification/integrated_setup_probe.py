#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Qualification-only invocation of trusted Setup source; never a runtime owner."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'scripts/distribution'))
sys.path.insert(0, str(ROOT/'apps/demo-orchestrator/src'))


def main():
    import setup_cloud
    from setup_bridge import error_code
    from aosedge_demo_orchestrator.environment import JOURNAL
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state', required=True)
    parser.add_argument('--pin', required=True)
    parser.add_argument('--oem', required=True)
    parser.add_argument('--sp', required=True)
    args = parser.parse_args()
    journal = Path(args.state)/JOURNAL
    before = journal.read_bytes() if journal.exists() else None
    try:
        request = setup_cloud.request(dict(action='cloud-connect', state=args.state, oem=args.oem, sp=args.sp))
        reply = setup_cloud.perform(request, args.pin)
        unchanged = before == (journal.read_bytes() if journal.exists() else None)
        result = dict(status=reply['status'], domain=reply['domain'], cloudStage=reply['cloudStage'],
                      checks=reply['checks'], journalPreserved=unchanged,
                      runtimeChanged=reply['runtimeChanged'], cloudAccessed=reply['cloudAccessed'])
        print(json.dumps(result))
        return 0 if unchanged and reply['cloudStage'] == 'READY' else 1
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps(dict(status='STOPPED', code=error_code(error),
            journalPreserved=before == (journal.read_bytes() if journal.exists() else None))))
        return 1


if __name__ == '__main__': raise SystemExit(main())
