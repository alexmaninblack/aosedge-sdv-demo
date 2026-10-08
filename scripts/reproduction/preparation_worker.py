# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Invoke the root release's existing producer without runtime initialization."""
import json
from pathlib import Path
import sys


if __name__ == '__main__':
    integration, platform, artifacts, output = map(Path, sys.argv[1:5])
    sys.path.insert(0, str(integration / 'scripts/distribution'))
    sys.path.insert(0, str(integration / 'apps/demo-orchestrator/src'))
    from vehicle_inputs import assemble
    from aosedge_demo_orchestrator.components import ComponentService
    from aosedge_demo_orchestrator import component_build
    from aosedge_demo_orchestrator.service_packages import product_files
    value = assemble(integration, platform, artifacts, artifacts / 'firmware/QEMU_EFI.fd', output,
        (ComponentService.__new__(ComponentService), component_build, product_files),
        factory_checkpoint=sys.argv[5], service_checkpoint=sys.argv[6])
    print(json.dumps({'status': value['status'], 'files': len(value['files'])}))
