# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Run canonical build/sign/media owners with explicit source release checkpoints."""
import json
from pathlib import Path
import sys


if __name__ == '__main__':
    root, target, kit, setup, output, signer, checkpoint, release = sys.argv[1:]
    root, kit, output = Path(root), Path(kit), Path(output)
    sys.path.insert(0, str(root/'scripts/distribution'))
    sys.path.insert(0, str(root/'apps/demo-orchestrator/src'))
    if target == 'setup':
        import setup_build
        result = setup_build.build(kit, output, signing_identity=signer,
                                  input_checkpoint=checkpoint, release_checkpoint=release)
    else:
        if target != 'dmg':
            raise ValueError('Unknown media target')
        import full_dmg
        output.mkdir(mode=0o700)
        result = full_dmg.build(kit, Path(setup), output/'AosEdge-SDV-Lab-1.2.0-rc.1.dmg',
            release_checkpoint=release, progress=lambda row: print(json.dumps(row), flush=True))
    print(json.dumps({'status': result['status']}), flush=True)
