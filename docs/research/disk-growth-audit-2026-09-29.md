<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Internal Disk Growth Audit — 29 September 2026

- Status: Read-only audit complete in the measured scope; no cleanup or migration performed
- Version: 1.0
- Prepared: 2026-09-29
- Owner: Demo Solution Team
- Source base: `22ee79e0e21709de34803c6db20047847138eba0`, existing work preserved
- Previous inventory: [25 September retention audit](disk-usage-retention-audit-2026-09-25.md)
- Current installer checkpoint: [29 September consolidation](../qualification/installer-consolidation-2026-09-29.md)

## Finding

The operator's recollection of more than 200 GB free is supported by the
recorded **190.25 GiB (approximately 204.3 decimal GB)** after Builder cleanup
on 25 September. The current internal APFS container reports approximately
**95.3 GB / 88.7 GiB unallocated**. The decline is approximately 101.5 GiB,
not a GB-versus-GiB display difference.

Most of the decline predates the latest small native-installer signing changes:
free space was already about 104.5 GiB after the 26 September standalone work
and cleanup. The largest directly identified new retained project working set
is the standalone CARLA workspace, 72.13 GiB by allocated-block directory
accounting, including compiler outputs, cooked resources, DDC and a built Game.
Other new preparation/runtime fixtures, video work and ordinary system activity
also exist. **The evidence does not support an exact exclusive-byte allocation
of the entire decline to individual folders.** APFS clones and missing historic
whole-disk inventories prevent that claim.

Deleting three superseded kit directory names was not a solution to the larger
capacity problem: their 98.22 GiB directory-accounting total shared almost all
payload with retained copies. The already-authorized earlier cleanup increased
free space by only 27.96 MiB. No deletion was made during this new audit.

## Recorded free-space chronology

| Observation | Free GiB | Evidence / interpretation |
| --- | ---: | --- |
| 25 September, after selective Builder cleanup | 190.25 | Actual before/after retention receipt; approximately 204.3 GB |
| 26 September, before first post-Stage-1 cleanup | 98.94 | Different-time observation, not the cleanup baseline |
| 26 September, after that authorized cleanup | 104.52 | [Post-Stage-1 receipt](distribution-stage1-retention-audit-2026-09-26.md#authorized-cleanup) |
| 27 September, post-assembly audit | 98.33 | [Recorded audit](distribution-stage2-retention-audit-2026-09-27.md) |
| 28 September, after old Zen data moved off internal storage | 90.51 | This already includes approximately 9.10 GiB recovered; [closure receipt](../qualification/distribution-stage2-closure-2026-09-28.md) |
| 29 September, after the three old kits were removed | 88.78 | [Exact cleanup receipt](../qualification/installer-consolidation-2026-09-29.md#authorized-cleanup-result) |
| This read-only audit | Approximately 88.7 | Concurrent applications continue to change free space |

The difference from 190.25 to 104.52 GiB is 85.73 GiB. This establishes the main
time interval of the decline, not a claim that every byte in that interval was
written by CARLA. The further decline from 104.52 to about 88.7 GiB is roughly
15.8 GiB, despite intervening cleanup. Therefore new gross writes were larger
than that net decline. Repeated Setup previews are on the external Work volume
and are each small, not internal 30-GiB copies.

## Current project allocation and comparison

All following GiB values are `du` allocated-block accounting. Rows may share
APFS extents; parent and child values must not be added as independent usage.
Project and named build-directory traversals completed without errors.

| Area, relative to the workspace unless noted | 25 September recorded GiB | Current GiB | Interpretation |
| --- | ---: | ---: | --- |
| `CarlaSim` | 86.96 | 158.58 | Approximately +71.62; contains the new 72.13-GiB Stage 1 working set |
| `UnrealEngine5_carla` | 99.65 | 99.66 | Essentially unchanged; source/toolchain, not another new 100-GiB copy |
| `demo-artifacts` | 8.80 | 35.02 | New portable host/preparation exports; clone overlap with other pools |
| Integration repo plus internal installed state | 15.50 for earlier repo/state | 7.93 repo + 7.61 installed instance | Roughly stable combined accounting; protected identities/backings remain |
| `aosedge-sdv-lab-video` | 79.99 | 120.83 | +40.84 directory accounting; largely new cloned proof workspace, not proved physical growth |
| `aosedge-executive-pitch` | No comparable recorded baseline | 12.69 | Includes 6.67 archive and 5.37 output; cannot assign all to this iteration |
| Yocto Builder, under Application Support | 78.38 overlay after cleanup, plus base | 79.04 including base | Stable retained warm Builder, not a repeat 28-GiB cache accumulation |
| Docker virtual disk | 14.35 | 14.31 file / 14.35 container directory | No material growth; 926-GiB logical capacity is not allocation |

### Standalone CARLA working set

Under `CarlaSim/Build-distribution-stage1-20260925`:

| Component | Current GiB | Retention meaning |
| --- | ---: | --- |
| `source/Unreal/CarlaUnreal/Intermediate` | 20.55 | Warm compiled objects |
| `cooked` | 18.42 | Completed asset cook |
| `filesystem-ddc` | 12.00 | Selected standalone shader/resource cache |
| `source/Unreal/CarlaUnreal/Binaries` | 19.68 | Includes a 19.23-GiB Game app; related clones also exist elsewhere |
| Other source, docs, metadata and evidence | About 1.48 | Not all disposable; source snapshot alone includes about 1.15 GiB of docs |
| Entire workspace | 72.13 | New since Stage 0, created on 25 September |

The approximately 50.96 GiB of compiler/cook/DDC data is intentionally retained
for warm rebuilds. It is **not needed to execute the installed demo**. Keeping
the runtime on SSD did not move these development inputs off the internal disk.
Deleting this working set would incur another compile/cook/resource preparation;
moving it instead requires a verified build-path change, not an unreviewed move
or a replacement of immutable runtime pins.

### Remaining temporary packaging families

The measured `/private/tmp` tree totals approximately 98.35 GiB, dominated by:

| Retained path | Directory-accounting GiB |
| --- | ---: |
| `aosapp.dEU9Ge/Runtime Kit 004` | 32.74 |
| `aosedge-stage2-native.cir6B1` | 26.67 |
| `aoshl.yj7380eu` | 19.48 |
| `aosedge-stage1-fixed.w9IUrj` | 19.23 |

These are not 98 GiB of independently reclaimable data. The native family
contains a 19.40-GiB host correction and a 6.79-GiB preparation-selector proof,
plus small runtime dependencies. Historical assembly helpers still reference
some of these inputs. The [previous retention audit](distribution-stage2-retention-audit-2026-09-27.md)
already requires recipe consolidation before their retirement. Deleting one
more cloned Game may again release almost nothing while breaking a build recipe.

### Video and pitch storage

The separate video project has an existing, explicit 27 September retention
proposal. This audit only read its organization/verification/cleanup documents
and file metadata; it did not modify video source, media, or Git.

- Completed organization test jobs: **33.26 GiB** directory/logical accounting.
  The principal restored picture workspace is 31.17 GiB, created 27 September.
  Its documented implementation uses native clone-copy requests. Compact proof
  is already retained outside those jobs; they are candidates for a separately
  authorized exact cleanup, not a promise of 33 GiB recovered.
- Original captures: **22.70 GiB**; frozen editable baseline: **24.84 GiB**.
  Protected production inputs, not deletion candidates by age/version alone.
- Recovery archive `recovery/v21-editable-2026-09-24.tar`:
  **26,668,154,880 logical/allocated bytes, approximately 24.84 GiB**. Created
  24 September, so it predates the initial 200-GB-free observation. It is a
  potential relocation candidate, not the cause of this iteration's increase.
  Preserve the archive; moving a verified copy to SSD is distinct from deleting
  the only recovery backup. Actual recovered internal space must be measured.
- Voice runtime/model support: **5.42 GiB** under the old `voice-pilot` name.
  Existing video documentation explicitly treats this as a protected dependency,
  not a disposable experiment; moving its Python environment blindly can break
  embedded paths.
- The pitch project has **6.67 GiB** of archives and **5.37 GiB** of outputs.
  Its current input closure has not been audited for deletion; size alone does
  not authorize clearing either directory.

## System, application and SSD cross-checks

- Internal APFS container: capacity **994.61 decimal GB**, in use **899.34 GB**,
  unallocated **95.27 GB** at one aligned observation. Data consumed about
  870.66 GB, System 12.63 GB, Preboot 7.72 GB, Recovery 1.64 GB and the separate
  VM volume 6.44 GB. System swap reported 6,144 MiB allocated, about 4,734 MiB
  used. Neither is evidence of an unexplained 100-GiB swap leak.
- Time Machine local snapshot listing was empty; the Data APFS volume had no
  snapshots. The booted System volume had one sealed OS-update snapshot. No
  large Data snapshot-retention pool was found and no snapshot was deleted.
- Docker's running daemon reports 22 images / 3.769 decimal GB, 5 volumes /
  68.71 MB, and 11.16 GB build cache with 3.064 GB reclaimable. Its accounting
  is a separate layer, not additive to `Docker.raw`. Five unrelated application
  containers are running; the two demo containers are stopped. No engine or
  container was started, stopped or pruned.
- User Library reports 230.16 GiB, including the already-counted Builder,
  approximately 61.06 GiB of locally stored iCloud documents, 12.68 GiB of
  CloudStorage, 15.23 GiB of caches and other application data. There is no
  historic like-for-like baseline for attributing their growth. Personal cloud
  files were not read or modified.
- Claude support data reports 13.99 GiB, including its own VM bundle (9.84 GiB)
  and local sessions. Its large image creation dates precede this iteration;
  current file size alone cannot prove recent expansion. No application state
  is a cleanup target in this audit.
- User application caches include Google 6.57 GiB and Codex 2.88 GiB. The latter
  is almost entirely two Sparkle installation directories. These are possible
  application-managed maintenance items only after checking the current updater
  and rollback dependencies, not an instruction to remove live app files.
- Work SSD physically consumes about **47.9 decimal GB including APFS overhead**
  and has approximately **602.1 GB / 560.8 GiB free**. Its project directory
  totals 469.28 GiB by `du` because packages and installed test copies are cloned.
  This is an independent demonstration that summing visible kit sizes badly
  overstates actual storage. SSD bytes are not charged to the internal disk.
- Clean SSD remains essentially empty and reserved for native clean-system
  qualification; it is not treated as another scratch pool.

## Recommended capacity plan — proposal only

This was the audit-time proposal. The operator subsequently accepted it;
see [authorized execution and measured recovery](../qualification/storage-consolidation-2026-09-29.md).
The audit observations below remain a dated record, not current storage locations.

1. **Restore meaningful headroom, not merely the missing 1.3 GiB.** Subject to
   explicit authorization, preserve/verify the single 24.84-GiB video recovery
   archive on Work and update its recovery location before removing the exact
   internal original. Verify privacy/retention requirements and no active
   consumer. This avoids sacrificing warm build caches or original media.
2. **Consolidate the whole runtime-copy family.** Establish one accepted runtime
   input on Work and one reproducible recipe; map historical consumers before
   retiring their exact internal clones. Judge success by measured physical
   space, not removed folder sizes. Keep the retained Test's selected kit intact.
3. **Choose where warm rebuilds live.** The approximately 51-GiB standalone
   compiler/cook/DDC set can remain for speed, or undergo a separately qualified
   move to Work. Do not delete it as if it were an obsolete Editor experiment.
4. **Coordinate video housekeeping separately.** Its five already-inventoried
   completed jobs can be retired after exact approval/checks. Preserve current
   media, baseline, voices, model support and private recovery material.
5. **Add a capacity checkpoint per packaging stage.** Record APFS free bytes
   before/after and retained-versus-disposable inputs; retire complete families
   after consumer closure. The existing 90-GiB engineering guard is unchanged
   and is not a claimed end-user installer minimum.

There is no approval in this audit for moving or deleting any of those items.
The installer build remains deferred while reviewing capacity; the VDP timeout
investigation remains user-deferred too.

## Evidence and limitations

Generated size inventories are retained under
`CarlaSim/Build-distribution-stage2-20260926/disk-audit-20260929/` (ignored,
local evidence). `du` never followed another filesystem. Named project,
standalone, artifact, video, pitch and Work scans completed without errors.
Broad internal/home/Library/private scans encountered protected paths (490
permission-denied diagnostics in the top Data traversal). No extra OS access
was requested or bypassed. Those category totals are partial as to denied data;
the APFS container free/used measurement is authoritative for overall capacity.

No global pre-iteration file/extent snapshot exists. File birth/modification
dates are supporting chronology, not proof of when every shared physical extent
was allocated. No large immutable payload was rehashed merely for this audit.
No compilation, runtime restart, VM/Cloud mutation, deletion, migration,
commit, push or tag change was performed. Only audit helpers/evidence and these
documentation updates were created.
