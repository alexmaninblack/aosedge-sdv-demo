<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# Disk Usage and Warm-Build Retention Audit

- Date: 2026-09-25
- Status: Audit complete; authorized Builder cleanup completed. Other pools
  remain candidates only.
- Scope: SDV development artifacts, isolated Yocto Builder and shared Docker.
- Goal: discard superseded experiments while retaining fast current-image and
  container rebuilds before the
  [installable-distribution work](../planning/active/installable-distribution-and-reproducibility.md).

Follow-up: the [post-Stage-1 retention audit of 26 September](distribution-stage1-retention-audit-2026-09-26.md)
records new standalone CARLA candidates and fresh open-handle/Docker state.
It is an inspection only, not an additional cleanup receipt.

## Initial read-only audit and preserved state

Inspected host allocated blocks, Docker inventory/cache metadata, current VM
open files, Builder configuration and cache hard links. The existing Builder
was initially stopped, temporarily started through its standard lifecycle on
loopback SSH port 10023, inspected without compiling or cleaning, and shut down
normally. Its DNS bridge is also stopped again.

The existing Test QEMU, CARLA and Presenter process identities were unchanged.
All seven existing Docker containers remained running, including healthy Brake
and Tire backends and five containers belonging to a separate application.
This is preservation evidence, not a new functional E2E test. No Cloud action,
Factory change, Docker restart/prune, trim, VM image compaction or user-data
removal was performed. Existing uncommitted distribution-plan documents remain.

The previous
[Factory39 cleanup](../qualification/factory-39-cleanup-2026-09-24.md)
already removed obsolete .36/.37/.38 host images. They are not present as new
cleanup opportunities. Factory .39 and Production's dependent .31 remain
protected, as do their overlays, catalogs, manifests and release ledgers.

## Measurement interpretation

- Host free space was approximately 166 GiB at entry and 163 GiB at the final
  observation. No space was reclaimed by this audit; concurrent system/VM
  activity means these values are not a deletion measurement.
- Tables use GiB (2^30 bytes), unless Docker's decimal GB is stated explicitly.
- `du` measures allocated blocks, not guaranteed unique APFS storage. Sparse
  logical size, shared Docker layers, hard links and APFS sharing prevent naive
  addition of directory sizes.
- Guest file removal does not itself prove equal host free-space recovery.
  After authorized deletion, verify guest space and host allocated blocks after
  the supported discard/trim path. Do not promise the estimated total in advance.
- Some broad guest `du` reads could not enter a protected test-token directory
  and a root-owned evidence directory. Those trees are preserved. The focused
  four-cache hard-link audit completed with zero traversal errors.

## Major retained consumers

| Area | Observed allocated space | Disposition |
| --- | ---: | --- |
| Yocto Builder, including base image | 106.85 GiB | Preserve VM and current warm build; inspect internal history selectively |
| Unreal source/build tree | 99.65 GiB | Preserve for standalone simulator packaging |
| CARLA tree, including content and Git | 86.96 GiB | Preserve required content/source and qualified simulator |
| Separate video repository | 79.99 GiB | Out of this cleanup scope |
| Integration repository and local VM state | 15.50 GiB | Mostly protected Factory backings and active/persistent overlays |
| Docker virtual disk | 14.35 GiB | Shared by demo and another running application |
| Demo artifact store | 8.80 GiB | Mostly current Factory; smaller package history requires reference audit |
| Unreal shared Zen/cache | 8.19 GiB | Preserve to avoid repeated preparation/stutter |

Docker.raw has a logical size of about 926.3 GiB, but occupies only 14.35 GiB
of host blocks. Do not report its logical maximum as current consumption, delete
the file, or reduce its size as a cleanup shortcut. Docker documents this
[logical-versus-actual distinction](https://docs.docker.com/desktop/troubleshoot-and-support/faqs/macfaqs/).

## Yocto Builder: exact active dependencies

The guest root filesystem reports approximately 105 GiB used and 109 GiB free.
No BitBake/compiler/build process was found during the audit.

Active configuration is under
`/home/yocto/r61-build/project/yocto/build-main/conf/`:

- `moulin.conf` selects `/home/yocto/yocto-cache/downloads` and
  `/home/yocto/yocto-cache/sstate-cache`, machine `qemuarm64`, distro `aos-core`.
- `auto.conf` retains `BB_NO_NETWORK = "1"`.
- `bblayers.conf` selects the platform layer at
  `aos-vehicle-platform-793b1fc035d2b7c123f9a4161788955f389bb81d`.
- No reference to either historical candidate root below was found in the
  current configuration or inspected shallow layer symlinks. This is not an
  exhaustive proof that no historical script can refer to them.

Preserve the canonical downloads (12.60 GiB), canonical sstate (16.49 GiB),
current work/sysroots/stamps, selected layers and tools. Their directory sizes
overlap other trees through hard links and must not be summed as unique storage.

### Candidate A — superseded isolated cache copies

Four exact candidate directories:

1. `/home/yocto/kac-compile-bdc72ab-e4f692f9/downloads`
2. `/home/yocto/kac-compile-bdc72ab-e4f692f9/sstate-cache`
3. `/home/yocto/build/wp-p1-platform-kuksa-row2-scope-001/downloads`
4. `/home/yocto/build/wp-p1-platform-kuksa-row2-scope-001/sstate-cache`

Keep the parent evidence directories. These are historical diagnostic caches,
not the current build's configured downloads/sstate.

The read-only inode audit counted candidate references against `st_nlink`:

| Measurement across the four candidates | Bytes | GiB |
| --- | ---: | ---: |
| File blocks whose last links are within these candidates | 22,714,458,112 | 21.15 |
| File blocks still linked outside these candidates | 29,553,037,312 | 27.52 |
| Candidate directory blocks, separately measured | 56,160,256 | 0.05 |

Consequently, removing the candidates would not recover their apparent sum of
about 49 GiB. The file-block estimate is **21.15 GiB**, plus small directory
overhead. External hard links retain their data. Before deletion, recheck
exact paths, active references, stopped owners and open handles; preserve the
canonical cache paths and compact experiment evidence.

The metadata-only audit helper used on this date is
`/private/tmp/sdv-retention-hardlink-audit-20260925.py`; it performed no writes
inside the guest and reported no traversal errors. Its temporary availability
is not required to interpret the recorded results.

### Candidate B — accumulated recipe-parse cache

`/home/yocto/r61-build/project/yocto/build-main/tmp/cache` occupies 6.67 GiB,
predominantly 33 `bb_cache.dat.*` variants, typically about 208 MiB each.
Keeping all entries dated 23–24 September leaves about 0.81 GiB and identifies
approximately **5.86 GiB** of earlier candidates.

This is metadata parsing cache, not sstate or compiled work. Before pruning,
identify the cache signature used by the retained configuration and confirm
that it is in the keep set; date alone is not proof of obsolescence. A removed
parse variant may require reparsing, not a full compiler rebuild. Do not delete
the whole `tmp` directory or change active build configuration for this cleanup.

### Candidate C — historical event logs

`/home/yocto/r61-build/project/yocto/build-main/tmp/log/eventlog` occupies
1.09 GiB. Keeping the 23–24 September logs leaves roughly 0.26 GiB; earlier
files total approximately **0.82 GiB**. Confirm retained compact qualification
evidence before removing the exact older raw logs. Keep current failures and
all source/manifests/provenance receipts.

### Optional, separate trade-off — Conan build directories

`/home/yocto/r61-work/.conan2` occupies 11.43 GiB. Build-only subdirectories
under `p/b/<package-id>/b` total **7.15 GiB**; compiled package directories
under `p/b/<package-id>/p` are distinct and must remain.

Do not delete the Conan cache wholesale. Before considering build-directory
cleanup, identify current consumers, verify corresponding binary packages are
valid and retain the source/export data needed by the next build. Removing
intermediate objects can slow a future rebuild of a dependency. This option is
not included in the first, warm-build-preserving cleanup recommendation.

### Small or protected Builder items

Only Factory .31 and .39 image outputs were found at the inspected project
level. Each has a logical size of 6.52 GiB but only about 0.55 GiB allocated
inside the guest. Preserve both; deleting them offers little compared with the
obsolete caches. Superseded layer checkouts are mostly only a few MiB each:
they are housekeeping, not the primary disk-pressure solution.

## Docker: preserve useful layers, not every experiment

Observed Docker accounting:

- 22 images; seven referenced by the seven running containers.
- 3.769 GB image storage, of which Docker reports only 291.7 MB reclaimable.
- 302 build-cache records: 11.16 GB total, 10.17 GB reported reclaimable.
- Five volumes, four referenced; total volume data 121.8 MB. The sole unlinked
  volume is 88 bytes and is not a meaningful cleanup target.

Old backend tags share almost all their approximately 363 MB displayed image
size. Removing many such tags will not recover that size for each tag.
Preserve active image IDs `48f633748d22` (Brake) and `5dddd12060c3` (Tire), their
data volumes, current build inputs and the unrelated application's resources.

A description-based classification found 116 non-shared reclaimable
service-source/build cache records totalling about 4.87 GB. The most recent
group, used about 45 hours earlier, accounts for 0.423 GB; older groups total
about **4.44 GB / 4.14 GiB**. This is a candidate pool, not an approved deletion
list: map parent chains and required V1/V2/V3 build inputs before choosing
records. Keep current source/build records and reusable compiler, gRPC,
protobuf, OpenSSL, base-image and package-manager dependency layers.

At least 1.44 GB of other non-shared cache was last used four months ago and
includes the unrelated application's dependency builds. Age alone does not
authorize deleting it. Global `docker system prune -a --volumes` is not the
proposed operation. Docker supports selective
[build-cache retention policies](https://docs.docker.com/build/cache/garbage-collection/);
a project-specific keep set must precede any policy change on this shared host.

## Host diagnostics and demo package history

- Six completed build directories below
  `/private/tmp/aos-mainline-migration-20260923.A2qEwO` remain candidates:
  `app-build`, `lib-build`, `cm-build`, `cm-lock-build`, `openssl-build`,
  `gtest-1.14-build`. Their recorded total is about **2.12 GiB**. A fresh open-file
  check still found the Docker virtualization file service holding `app-build`
  objects/directories. Do not delete while held. A coordinated Docker restart
  could interrupt both the demo and the unrelated application; none was done.
- VDP component artifacts total 0.59 GiB and Brake/Tire service artifacts
  1.34 GiB, including retained build exports. Some are historical, but preserve
  `.source-profiles`, current functional-version build inputs, current installed
  packages and release-allocation records. The entire 1.93 GiB is not disposable.
  Resolve active and rollback references before selecting obsolete releases.
- Only one registered worktree per repository was observed across the eight
  inspected demo/component/engine repositories. The small remaining
  qualification directories are not a hidden set of large Git worktrees.
- Preserve Unreal/CARLA source, content Git, required binaries and shader/Zen
  caches during the upcoming standalone-package proof. Do not trade a small
  immediate saving for another large engine rebuild or missing assets.

## Recommended cleanup order and retention rule

1. Authorize the exact deletion inventory after a fresh dependency/open-handle
   check. Preserve the failing/current runtime state and baseline first.
2. Remove only the four historical cache trees, retaining their compact parent
   evidence and the canonical downloads/sstate.
3. Retain the active parse signature and latest useful logs; remove verified
   superseded metadata variants and redundant raw event logs.
4. Return freed guest ranges through the existing supported discard/trim path,
   then measure actual host-space recovery. Stop the Builder normally afterward.
5. Map and prune only superseded demo Docker build records. Keep dependency
   layers and all active/unrelated resources; do not delete volumes.
6. Schedule held host diagnostics separately if a Docker restart is required.
   Leave optional Conan reduction for a distinct, explicitly accepted trade-off.
7. Verify image/backing relationships, current configurations and offline build
   input availability, then run a bounded incremental check when authorized.

The first Builder pool is approximately **27.8 GiB of file blocks** (about
28 GiB with directory overhead). The Docker pool may add up to about 4.1 GiB
after dependency mapping; held host diagnostics add about 2.1 GiB only after
their owners release them. These are estimates, not recovered-space claims.
Conan's optional 7.15 GiB and unresolved artifact history are excluded.

Steady-state policy: retain one current warm Builder/configuration, canonical
downloads/sstate, current dependency toolchains, necessary functional-profile
inputs, accepted Factory/Production backing chains and compact evidence. Keep
temporary experiment caches only while their investigation is active; retire
their exact paths after evidence consolidation and reference checks. The
[Yocto disk-space guidance](https://docs.yoctoproject.org/dev-manual/disk-space.html)
distinguishes work cleanup from sstate management; neither broad `rm_work`
activation nor age-only pruning of the current shared cache is proposed here.

Reading this audit does not authorize the remaining candidate pools. Follow the
[rapid-debug and retention policy](../governance/rapid-development-and-debugging.md)
for exact authorization, dependency order, open-handle checks and completion
receipts. Preserve the existing minimum free-space build guard; a successful
cleanup does not itself qualify a new image or distribution.

## Authorized Builder cleanup — completed 25 September

After the audit, the operator approved the recommended approximately 28 GiB
Builder cleanup. This execution was limited to candidates A–C above. Docker,
host diagnostic builds, Conan, video assets, current images and active demo
state were not cleanup targets. This is an operational retention receipt, not
a product/architecture change or a new qualification baseline.

### Exact removals and retained inputs

- Removed all four historical cache directories listed in candidate A, but
  retained their parent directories, source and compact evidence.
- Removed 29 superseded regular `bb_cache.dat.<hash>` files, with 6,295,420,928
  allocated bytes (5.86 GiB). Preserved the four variants from 23–24 September
  and the current variant proved by the offline parse check. The original
  last-build variant `8bd6106e…c99a` is still retained; the check's current
  variant is `beb5c064…3b05`.
- Removed 50 individually inventoried event logs dated before 23 September,
  with 884,494,336 allocated bytes (0.82 GiB). Preserved all logs from
  23 September onward, including both cleanup-time parse checks.
- Preserved canonical downloads and sstate, current compiled work, sysroots,
  stamps, layer checkouts, Factory .31/.39 outputs and existing qualification
  evidence. Canonical cache allocated sizes remain exactly 13,207,572 KiB
  and 17,287,344 KiB respectively.

The fresh hard-link audit reproduced candidate A's 22,714,458,112 exclusive
file bytes plus 56,160,256 directory bytes. Its 29,553,037,312 externally linked
bytes were **not** counted as recovered: those other links retain their data.
Across A–C, the exclusive allocated-block estimate removed is **27.89 GiB**.

Before deletion, all exact paths and file identities were frozen in a manifest.
The checks found no active build process, nested target mount, or open handle.
Each of the 83 targets has a flushed `ATTEMPTED` followed by `REMOVED` record;
post-read reconciliation found every target absent. No broad prune or
whole-build-directory removal was used.

### Verification and measured recovery

| Measurement | Before | After |
| --- | ---: | ---: |
| Builder qcow2 allocated host blocks | 106.30 GiB | 78.38 GiB |
| Mac filesystem available space | 162.36 GiB | 190.25 GiB |
| Guest available space immediately around deletion/checks | 108.52 GiB | 136.41 GiB |

The Builder's host allocation decreased by **27.91 GiB**. Mac free space
increased by **27.88 GiB** over the observation interval; concurrent system and
demo activity prevents exact byte-for-byte attribution. The qcow2 logical
file size remains 185,233,571,840 bytes: sparse logical size is not disk usage.

The existing `discard=unmap` path was retained. A normal `fstrim /` reported
143,114,850,304 bytes of free ranges submitted. That includes already-free
ranges and is **not** an additional 133 GiB reclaimed by this cleanup.

Verification passed:

- An offline parse-only check before pruning completed 3,162 recipes with zero
  errors, identifying the cache used by the current invocation. The same check
  after pruning loaded **5,250 entries from the retained dependency cache**.
  Neither check compiled targets, fetched sources, or built a new image.
- The four build-configuration hashes are unchanged from before parsing;
  `BB_NO_NETWORK = "1"` remains set.
- Canonical-cache metadata inventories, Factory .31/.39 identity/size/mtime,
  compact qualification evidence and non-target experiment siblings match the
  pre-deletion snapshot. All retained cache variants and raw logs from the
  deletion manifest are unchanged.
- CARLA, Test QEMU and Presenter retained the same process identities. All
  seven Docker containers stayed running; both demo backends remained healthy.
  This proves preservation at those boundaries, not a fresh functional E2E.
- Builder and its DNS bridge were shut down normally and are **STOPPED** again.

Exact guest manifest, per-target journal and verification receipts:
`/home/yocto/r61-build/cleanup-warm-builder-20260925-p38drset`.
The host helper/evidence workspace is
`/private/tmp/sdv-builder-cleanup-20260925.bsyuNP`.

The deleted caches/logs were removed directly, not moved to Trash. Build caches
can be regenerated from retained inputs; the deleted historical raw event logs
cannot be restored through the application. Their retained compact evidence,
the current warm build, and Test/Production state are unaffected. The remaining
Docker, held host-build and optional Conan candidates require their separate
dependency/ownership checks and are not included in this completed cleanup.
