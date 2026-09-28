<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Post-assembly disk retention audit

- Date: 27 September 2026.
- Status: read-only audit complete; no cleanup authorized or executed by this report.
- Owner: Demo Solution Team.
- Scope: completed SDV packaging experiments, existing warm builds and shared Docker.
- Inputs: [distribution plan](../planning/active/installable-distribution-and-reproducibility.md),
  [complete application checkpoint](../qualification/portable-application-2026-09-26.md),
  [earlier retention audit](distribution-stage1-retention-audit-2026-09-26.md),
  [standalone retention and handoff](../../../CarlaSim/Docs/standalone-retention-audit-2026-09-26.md).

This is dated operational evidence, not a runtime/architecture change, an
installer qualification or permission to delete. Only this report and its
documentation-map link were added. No process was stopped, no cache was pruned,
no Builder was started, and no Cloud, VM, image or model was changed.

## Result and measurement limits

The Data volume reported **98.33 GiB available** at the final measurement
(103,106,652 KiB). The current packaging reserve remains 90 GiB. Concurrent
running applications affect free space; the difference from yesterday is not
attributed to a specific process by this audit.

There are obsolete packages to consolidate, but their large `du` totals are
**not equivalent to reclaimable disk space**. APFS clones share extents. This
audit did not measure exclusive extents and does not promise hundreds of GiB
from deleting copied directory names. Docker cache sizes are a separate
accounting layer; deleting guest data does not guarantee equal immediate host
recovery. Measure host free space before and after each authorized batch.

The clearest non-runtime opportunity is the old Zen cache payload, about
**9.11 GiB** by allocated-block accounting. A separate old Docker service-export
pool is about **1.125 decimal GB / 1.05 GiB**, subject to the retention check below.
These are candidate sizes, not guaranteed recovered-space measurements.

## Protected current state

- Runtime processes actually use `demo-artifacts/aosedge-sdv-demo/host-runtime`:
  Test QEMU 18914, CARLA 19988, Driving Control 20208 and native Presenter 51041.
  Open files include the current Test overlay and its .39 backing. No Editor,
  Zen server, shader compiler or build process was observed in the scoped check.
- Test local identity remains `48a0e19c-857f-44b8-9b68-38b585a8278f`; Production
  remains `54d45d8f-7813-43aa-81c9-09152cbee0f7`. The journal is LOCAL_ACTIVE with
  source run `d385bdd5-af95-4d1b-a564-48f6152de50e`. This is preservation evidence,
  not fresh functional/Cloud qualification.
- Preserve all five active input groups, Factory .39, Production's .31 backing,
  both overlays, identities, credentials, ledgers, backend volumes and history.
- Preserve `/private/tmp/aosapp.dEU9Ge/Runtime Kit 004`, the final complete export.
  Its small application manifest still hashes to
  `c7f5b967ae08407b4f1ee09714a7a0cea5ba555e5076598761052b3b990187bd`.
  Its five input pins match fresh hashes of the five active small manifests.
  Large payloads were not rehashed for status. The kit has 83 application files
  and 28,111,240,862 input logical bytes, plus the catalogue's second Factory path.
  Its manifest correctly does not claim installer qualification.
- Preserve source/Git, uncommitted corrections, compact evidence and the separate
  video repository. Do not treat untracked source as disposable build output.

## First cleanup candidates

### 1. Superseded complete kits

Retire only these three exact directories, keeping their small application
manifests and useful proof references outside the directories first:

| Exact directory | `du` GiB | Why superseded |
| --- | ---: | --- |
| `/private/tmp/aosapp.dEU9Ge/Runtime Kit` | 32.74 | Initial source/native/VM checkpoint |
| `/private/tmp/aosapp.dEU9Ge/Runtime Kit 002` | 32.74 | Intermediate timeout correction |
| `/private/tmp/aosapp.dEU9Ge/Runtime Kit 003` | 32.74 | Predates final HTTP cancellation correction |

Their combined directory accounting is **98.22 GiB**, not a recovery estimate.
Keep Kit 004, `probe.py`, `offline.sb` and the parent directory. The first two
kits pin the former host/VM manifests; the third pins the current runtime but
has the previous application source. The final complete exporter can assemble
from the retained active catalogue; old complete kits are not its inputs.

The elevated open-file snapshot found no paths under the kit root. Recheck
immediately before approved removal; do not use a parent-directory or wildcard
delete. Removing these obsolete candidates does not remove the current source
checkpoint or active runtime.

### 2. Retire the old Editor-era Zen cache

Root: `Library/Application Support/Epic/UnrealEngine/Common/Zen/Data` under
the current operator's home directory. Resolve that exact home before any
authorized operation; never use the home directory itself as a cleanup target.

| Payload child | Allocated KiB |
| --- | ---: |
| `cache` | 5,963,116 |
| `cas` | 3,571,448 |
| `gc` | 12,872 |

The combined payload is **9.105 GiB**; the whole Data tree is 9.109 GiB.
The exact-tree open-file check returned no handles or diagnostics; no running
Zen/Editor consumer was found. The retained successful cook command explicitly
uses `-ddc=NoZenLocalFallback` with the standalone `filesystem-ddc` directory.
The current packaged Game does not require this old Editor cache.

Recommend retiring this stopped, obsolete cache after explicit approval and a
fresh consumer check. Use a coherent cache-store reset, not arbitrary removal
of individual database/blob files. Preserve authentication, installation,
configuration and compact logs/provenance. Verify the current runtime remains
unaffected. Returning to an Editor/default-Zen cook can recreate the cache and
require renewed resource processing; this is the explicit trade-off.

Do **not** remove the standalone `filesystem-ddc` in the same operation.

## Candidates that still need consolidation or mapping

| Area | `du` GiB | Remaining prerequisite |
| --- | ---: | --- |
| `/private/tmp/aoshl.yj7380eu/artifacts/aosedge-sdv-demo/host-runtime` | 19.40 | Retire historical layout-reassembly inputs and preserve small manifests/proofs |
| `/private/tmp/aosedge-stage1-fixed.w9IUrj/content-profile.a38_dfdp/CarlaUnreal.app` | 19.23 | Repoint/qualify the retained host-assembly recipe before retiring its simulator input |
| `/private/tmp/aosedge-stage2-native.cir6B1` | 26.67 total | Select payload children only; this parent mixes recipe inputs, proof fixtures, manifests and logs |
| Stage 1 `source/Unreal/CarlaUnreal/Binaries/Mac/CarlaUnreal.app` | 19.23 | Prove warm re-finalization/repackage without the existing build-tree app |
| Active artifact-store `services` plus `components` | 1.92 total | Classify historical release payloads against current/rollback/profile/ledger references; not all disposable |

The historical `assemble_host_launch.py` still names the relocated simulator,
`UI Helper Candidate 002`, `Simulator Python Candidate 002`, `Portable Native
Candidate` and `OpenSSL Candidate 001`. `assemble_host_resize.py` still reads
the earlier host fixture. `package_shutdown_fix.py` reads the build-tree app's
Game executable. No such temporary-root reference was found in current runtime
source or canonical `scripts/distribution` code, but deleting all temporary
inputs now would break those retained reconstruction helpers.

Therefore consolidate recipes/evidence before retiring their exact payloads;
do not label this whole pool deletion-ready. The open-file snapshot found no
handles under the inspected temporary roots or Stage 1 build tree. Absence of
an open handle does not establish that a future build has no dependency.

Stage 2's local helper/evidence directory is only 0.34 GiB. Older qualification
directories .28/.29/.30/.31 total about 19 MiB; the CARLA `.worktrees` directory
is empty and both inspected Git repositories have only their primary checkout.
These are not major disk opportunities. No managed worktree is proposed for
manual deletion.

## Docker: updated, narrower opportunity

The existing daemon was already running; read-only inventory shows:

- Seven running containers: the two healthy demo backends and five unrelated
  Watt containers. None were restarted or stopped.
- 22 images, 3.769 decimal GB total; 291.7 MB reported reclaimable.
- Five volumes, 154.3 MB total; the only unreferenced volume is 88 bytes.
- 294 build-cache records, 11.16 GB total; `docker system df` reports 3.064 GB
  reclaimable. Buildx marks shared records separately; their sizes must not be
  added again to reclaimable physical space.
- Docker.raw occupies **14.38 GiB** of host blocks, not its roughly 926-GiB
  sparse logical maximum. Do not delete or replace this shared disk.

Non-shared reclaimable records break down into approximately 1.438 GB belonging
to the older unrelated-project group, 0.394 GB of reusable npm dependencies,
1.229 GB of 48 service export records, and 4 MB of other records. Preserve the
unrelated group and dependency layers.

The 44 service export records created before 23 September account for about
**1.125 GB**; retain at least the four latest exports dated 23 September and
the current V1/V2/V3/Tire input closure. This is a proposed selective pool:
confirm correspondence to retained build outputs and BuildKit selection
semantics before deleting exact IDs. No global `system prune`, volume deletion
or age-only prune is proposed. The former 4.14-GiB estimate from 25 September
is not a current verified opportunity and must not be reused.

## Keep the current rebuild working set

| Retained input | Current measurement | Reason |
| --- | ---: | --- |
| YoctoBuilder, including base | 79.04 GiB | Current warm Factory build; stopped, not started for this audit |
| Standalone compiler intermediates | 20.55 GiB | Avoid recompiling the Game/engine targets |
| Standalone cooked content | 18.42 GiB | Avoid another content cook |
| Standalone filesystem DDC | 12.00 GiB | Cache selected by the qualified cook |
| Unreal tree | 99.66 GiB | Required build toolchain and dependencies, not a second operational simulator |
| Original CARLA content | 80.90 GiB | About half working assets and half current Git LFS objects |

These are shared/overlapping accounting views, not an additive exclusive total.
The original project Intermediate is only 64 KiB; the old August standalone
binaries and loose staging tree were already removed. UnrealEditor remains a
headless cook tool even though ordinary demo operation now uses standalone CARLA.
The earlier LFS dry-run retained every local object; it was not repeated or
converted into permission to erase Git data.

The previous Builder cleanup already recovered approximately 27.9 GiB. Factory
.36/.37/.38 and the six historical AosCore build directories were also already
removed. Do not count any of these again. The optional historical Conan build
pool was not remeasured inside the stopped guest; it is excluded from the new
estimate. No source, warm Builder cache, current Factory, system swap or OS
cache purge is proposed.

## Recommended next action

1. Approve retirement of the three old complete kits and the stopped old Zen
   cache, with exact-path inventories, preserved small receipts and fresh
   ownership/open-file checks. Record actual free-space recovery per batch.
2. Map/select the 44 older Docker export records while preserving current
   profile inputs, dependency caches and every running/unrelated resource.
3. Consolidate the reconstruction recipes, then retire redundant relocated
   simulator/host/native payloads. Keep current catalogue and Kit 004.
4. Reassess installer disk capacity after measured recovery. Do not lower the
   90-GiB reserve or promise independent clean installation from APFS-clone
   fixture tests alone.

No deletion, commit, push, signing, build, installer implementation or live
functional test was performed by this audit.
