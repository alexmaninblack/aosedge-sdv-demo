# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
"""Run canonical build/sign/media owners with explicit source release checkpoints."""
import json
from pathlib import Path
import sys


def media_filename(root, checkpoint):
    """Name media from its verified source/typed seal, never a fixed release."""
    from candidate_inputs import LOCKS, pins
    pins(root, checkpoint, LOCKS)
    from developer_inputs import DeveloperInputs
    if isinstance(checkpoint, DeveloperInputs):
        version=checkpoint.value()['checkpoint']['productVersion']
    else:
        from candidate_inputs import read
        version=json.loads(read(root,checkpoint))['productVersion']
    return 'AosEdge-SDV-Lab-'+version+'.dmg'


if __name__ == '__main__':
    root, target, kit, setup, output, signer, checkpoint, release = sys.argv[1:9]
    root, kit, output = Path(root), Path(kit), Path(output)
    sys.path.insert(0, str(root/'scripts/distribution'))
    sys.path.insert(0, str(root/'apps/demo-orchestrator/src'))
    if sys.argv[9:]:
        if len(sys.argv[9:]) != 3 or sys.argv[9] != '--developer-seal':
            raise ValueError('Invalid developer result arguments')
        from developer_inputs import DeveloperInputs
        checkpoint = release = DeveloperInputs.load(sys.argv[10], sys.argv[11])
    if target == 'setup':
        import setup_build
        result = setup_build.build(kit, output, signing_identity=signer,
                                  input_checkpoint=checkpoint, release_checkpoint=release)
    else:
        if target != 'dmg':
            raise ValueError('Unknown media target')
        import full_dmg
        output.mkdir(mode=0o700)
        result = full_dmg.build(kit, Path(setup), output/media_filename(root, checkpoint),
            release_checkpoint=release, progress=lambda row: print(json.dumps(row), flush=True))
    print(json.dumps({'status': result['status']}), flush=True)
