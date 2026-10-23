# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Private capacity-reader entry; one bounded request and no build operations."""
import json
from pathlib import Path
import sys
import signal

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from reproduction.core import LabError
from reproduction.space_probe import inspect_request


if __name__ == '__main__':
    def cancel(signum, frame):
        # Existing command owners then unwind their separately owned groups.
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, cancel)
    signal.signal(signal.SIGINT, cancel)
    def progress(event, detail):
        print(json.dumps(dict(event=event, detail=detail)), flush=True)
    try:
        raw = sys.stdin.buffer.read(8192)
        if len(raw) >= 8192:
            raise LabError('Capacity request is too large')
        result = inspect_request(json.loads(raw), progress)
        print(json.dumps({'result':result}), flush=True)
    except (Exception, KeyboardInterrupt) as error:
        reason = str(error)[:2000] if isinstance(error, LabError) else 'Capacity metadata unavailable or invalid'
        print(json.dumps({'error':reason}), flush=True)
        raise SystemExit(1)
