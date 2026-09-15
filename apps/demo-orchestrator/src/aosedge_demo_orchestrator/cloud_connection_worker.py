# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Private, local-only certificate inspection. Never outputs key/certificate bytes."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from aosedge_demo_orchestrator.cloud_connection import inspect_certificate

if __name__ == "__main__":
    try:
        request = json.loads(sys.stdin.read(8193))
        data = inspect_certificate(request["certificate"])
        result = dict(ok=True, data=data)
    except Exception as error:
        reason = str(error)
        result = dict(ok=False, reason=reason if reason.startswith("CLOUD_") and len(reason) < 100
                      else "CLOUD_CERTIFICATE_UNREADABLE_OR_PASSWORD_REQUIRED")
    print(json.dumps(result))
