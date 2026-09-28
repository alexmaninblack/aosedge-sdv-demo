# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Exact script entry for isolated private Python; shared CLI, no new state root."""
from pathlib import Path
import sys

if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from aosedge_demo_orchestrator.cli import main
    raise SystemExit(main())
