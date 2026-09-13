<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Factory .33 source publication and branch cleanup

Recorded: **13 September 2026**. Status: **completed** for the seven custom
demo repositories. The user authorized committing and pushing the accumulated
work, followed by removal of temporary development branches.

## Published return point

All seven repositories are public under `alexmaninblack`, use `main` as their
default branch, and have the published annotated tag
`checkpoint/demo-20260913`. Remote tag targets and main tips were read back
before deleting any branch. Existing main histories were advanced only by
fast-forward; no force push or history rewrite was used.

| Repository | Checkpoint commit |
| --- | --- |
| `aosedge-sdv-demo` | `9ca128d8fe48ad2b03a5d2ab5613007fd848cec5` |
| `aos-vehicle-platform` | `d0c71fce8049730a61ea7a0e80e804987e7c82ce` |
| `carla-ego-runtime` | `2fc57a9bb6517d2d439d4d4c3e02b7aafad2713d` |
| `brake-health-service` | `76d80e9373c64ba815487254fe6c8820be0c22bb` |
| `brake-health-cloud` | `da7ee6b12fbc7c4a85fcd0c3d75566982e7f8f34` |
| `tire-health-service` | `fc81a37dbb68425bf659f7bbd683898d64966792` |
| `tire-health-cloud` | `76a5cd2e8f40da842f16d6ad6c955b5472f4594b` |

The Solution main also contains this subsequent documentation-only receipt;
the checkpoint tag intentionally stays at the source/qualification commit.
New commits in this publication were Solution `c7e7382` (Demo Control source
and regression tests), Solution `9ca128d` (qualification/docs/review patches),
and Platform `d0c71fc` (qualification record). Existing qualified commits in
the other repositories were promoted to main without modification.

Factory .33 remains the exact previously built image, SHA-256
`a302b2f2e2f238b361682ab8a529ec036ff260e00b2fb9a4d21db325d8d45761`,
from Platform source `f7922b02b15f6cf816f181e1bf97572b61859aea`.
A later source/documentation checkpoint does not change image provenance.

To inspect the return point in any of these repositories:

```sh
git fetch origin --tags
git show checkpoint/demo-20260913
```

Checking out a source tag does not roll back live Units, cloud releases,
credentials, databases or the monotonic release-number ledger.

## Temporary branch removal

**18 local branches and 9 remote branches were deleted.** Each branch below
has the `codex/` prefix. Merged branches remain reachable from main; the eight
non-ancestor historical tips have published `archive/20260913/<name>` tags.
Archived experiments were not merged into the current implementation.

| Repository | Removed local branches (without prefix) | Removed remote branches (without prefix) |
| --- | --- | --- |
| Solution | `demo-studio-implementation`, `bhs-v2-packet-digest-correction`, `ltvp-finalize-27`, `studio-bind-release`, `studio-cloud-observation`, `studio-test-retirement` | `demo-studio-implementation`, `ltvp-finalize-27` |
| Platform | `demo-safe-stop-clock-skew`, `ltvp-finalize-27` | `demo-safe-stop-clock-skew`, `ltvp-finalize-27` |
| Vehicle runtime | `studio-controller-startup-diagnostic`, `ltvp-traffic-manager-order` | `ltvp-traffic-manager-order` |
| Brake service | `brake-growing-window`, `imp-04-bhs-core-v3`, `studio-brake-runtime` | `studio-brake-runtime` |
| Brake backend | `imp-04-brake-cloud-window-detail`, `studio-backend-container`, `studio-test-backend` | `studio-backend-container` |
| Tire service | `studio-tire-runtime` | `studio-tire-runtime` |
| Tire backend | `studio-tire-backend` | `studio-tire-backend` |

Archive tags cover Solution's five non-main historical tips, Platform's old
`.27` branch, the runtime traffic-manager experiment, and the Brake backend
window-detail experiment. These tags preserve source history, not copies of
deleted images or compiled artifacts.

Nine historical worktrees were detached at their existing commits so the
branch pointers could be removed without changing their files. Their
directories were not deleted. In particular, six untracked C++ files in the
old Brake core-v3 worktree were preserved, not swept into the current commit.
CARLA/Unreal compatibility branches and unrelated scratch directories were
left unchanged. There is no claim that all historical worktree files have
been cleaned or published.

## Verification and publication boundaries

- 210 targeted Demo Control unit tests passed, covering CM comparison,
  isolated .31 qualification, Unit lifecycle, Test environment, component
  runtime/publication, service activation/assignment and source/connectivity.
- Documentation checks and staged/reachable-history confidential-input guards
  passed. Normal text diffs passed whitespace checks; review patch files retain
  required blank context prefixes and parse successfully with `git apply --stat`.
- Private Cloud evidence links, source locations and infrastructure identifiers
  were removed from the public diagnostic derivatives. Detailed originals
  remain owner-only outside Git. No private Cloud source was published.
- No VM image, compiled service/provider archive, runtime secret or credential
  was added. Existing UI image assets are source assets, not build outputs.
- No new live E2E, VM restart, deployment, Cloud mutation or artifact deletion
  was performed as part of this Git publication.

## Remaining work

The source-publication portion of OPEN-03 is closed; AosCore upstream review
is still open. Native service permissions/KUKSA, the Cloud stale-event defect,
remaining UI/product/visual gates and OPEN-05 machine-readable workspace/legacy
lock reconciliation remain as recorded in the
[consolidation register](factory-33-consolidation-audit-2026-09-13.md).
The exact source table above is the published return point, not a claim that
older workspace/launcher guards have been updated or fresh-clone-qualified.
